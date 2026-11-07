"""Validacao por divisao de alunos: o que e escolhido pelo maior efeito se repete em outros alunos?

Em cada divisao (alunos sorteados em duas metades, semente fixa):
 1. DESCOBERTA (metade 1): roda a selecao inteira, como no trabalho original
    (todos os pares, Benjamini-Hochberg, so efeito positivo) e escolhe ate 4 finalistas.
 2. VALIDACAO (metade 2): estima so os finalistas, sem escolher de novo.
Dois procedimentos de selecao sao comparados:
 - ORIGINAL: os 4 maiores efeitos positivos que passam no BH (como estava planejado);
 - REVISADO: igual, mas exige que A e B estejam na 1a vez e pelo menos 50 alunos nos dois
   bracos (equivale a 100 no total) com IC inferior > 0, tudo medido na descoberta.
O suporte minimo e 50 em cada metade (= 100 no total). Faixas de desempenho anterior (tercis)
usam os cortes da amostra toda: a covariavel nao depende do desfecho.

Saida: resultados/validacao_divisoes.csv e resultados/validacao_resumo.csv (so agregados).
Uso: python -I scripts/validacao.py [n_divisoes]
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analise as an  # noqa: E402

R = an.SAIDA
SEMENTE = 20261108
N_FINALISTAS = 4
SUPORTE_METADE = 50


def preparar():
    df, nomes = an.carregar()
    prim = df.groupby(["aluno", "cod"])["semestre_idx"].min().rename("prim_cod")
    df = df.join(prim, on=["aluno", "cod"])
    df["repeticao"] = df["semestre_idx"] > df["prim_cod"]
    cal = df[df["calouro"]]
    ch = cal[cal["desemp"].notna()].copy()
    ua = ch[["aluno", "semestre_idx", "desemp"]].drop_duplicates()
    cortes = ua["desemp"].quantile([1 / 3, 2 / 3]).to_numpy()
    ch["faixa"] = np.digitize(ch["desemp"], cortes)
    b = ch[["aluno", "semestre_idx", "cod", "repeticao"]].drop_duplicates(["aluno", "semestre_idx", "cod"])
    B_rep = b.pivot(index=["aluno", "semestre_idx"], columns="cod", values="repeticao")
    return ch, nomes, B_rep


def estimar(rows, Bc, B_rep, limpo):
    idx = pd.MultiIndex.from_frame(rows[["aluno", "semestre_idx"]])
    bval = B_rep[Bc].reindex(idx).to_numpy() if Bc in B_rep.columns else np.full(len(rows), np.nan)
    r = rows.assign(expo=(~pd.isna(bval)).astype(int), b_rep=np.where(pd.isna(bval), False, bval.astype(object) == True))  # noqa: E712
    if limpo:
        r = r[(~r["repeticao"]) & ((r["expo"] == 0) | (~r["b_rep"]))]
    if r.empty:
        return None
    return an.comparar(r, r["expo"], r["faixa"])


def main(n_div=40):
    an.N_BOOT = 300
    an.SUPORTE_MIN = SUPORTE_METADE
    ch, nomes, B_rep = preparar()
    alunos = ch["aluno"].unique()
    rng = np.random.default_rng(SEMENTE)
    linhas = []
    for s in range(n_div):
        perm = rng.permutation(alunos)
        desc = set(perm[: len(perm) // 2])
        D = ch[ch["aluno"].isin(desc)]
        V = ch[~ch["aluno"].isin(desc)]
        tab, _ = an.pares(D, nomes, "faixa", "descoberta")
        cand = tab[tab["passa_bh"] & (tab["dif_risco_pp"] > 0)].sort_values("dif_risco_pp", ascending=False)

        # procedimento ORIGINAL: 4 maiores efeitos positivos que passam no BH
        orig = cand.head(N_FINALISTAS)[["disciplina", "dado_par", "dif_risco_pp"]].values.tolist()
        # procedimento REVISADO: filtra por 1a vez e suporte nos dois bracos, medido na descoberta
        rev = []
        for _, c in cand.iterrows():
            ra = D[(D["cod"] == c["disciplina"]) & D["concluiu"]]
            e = estimar(ra, c["dado_par"], B_rep, True)
            if e and e["n_com_par"] >= SUPORTE_METADE and e["n_sem_par"] >= SUPORTE_METADE and e["ic_inf_pp"] > 0:
                rev.append([c["disciplina"], c["dado_par"], e["dif_risco_pp"]])
        rev = sorted(rev, key=lambda x: -x[2])[:N_FINALISTAS]

        for proc, fin, limpo in (("original", orig, False), ("revisado", rev, True)):
            for A, Bc, dif_d in fin:
                rv = V[(V["cod"] == A) & V["concluiu"]]
                e = estimar(rv, Bc, B_rep, limpo)
                if e is None:
                    continue
                linhas.append(
                    {
                        "divisao": s, "procedimento": proc, "disciplina": A, "nome": nomes[A],
                        "dado_par": Bc, "nome_par": nomes[Bc], "dif_descoberta_pp": dif_d,
                        "dif_validacao_pp": e["dif_risco_pp"], "val_ic_inf": e["ic_inf_pp"], "val_ic_sup": e["ic_sup_pp"],
                        "val_n_com_par": e["n_com_par"], "val_n_sem_par": e["n_sem_par"],
                        "confirma": bool(e["dif_risco_pp"] > 0 and e["ic_inf_pp"] > 0),
                    }
                )
        print(f"divisao {s + 1}/{n_div}: candidatos {len(cand)}, finalistas original {len(orig)}, revisado {len(rev)}", flush=True)

    out = pd.DataFrame(linhas)
    out.round(3).to_csv(R / "validacao_divisoes.csv", index=False)
    resumo = []
    for proc, g in out.groupby("procedimento"):
        resumo.append(
            {
                "procedimento": proc, "divisoes": n_div, "finalistas_estimados": len(g),
                "efeito_descoberta_medio_pp": g["dif_descoberta_pp"].mean(),
                "efeito_validacao_medio_pp": g["dif_validacao_pp"].mean(),
                "inflacao_media_pp": (g["dif_descoberta_pp"] - g["dif_validacao_pp"]).mean(),
                "pct_confirma_na_validacao": 100 * g["confirma"].mean(),
                "pct_sinal_positivo": 100 * (g["dif_validacao_pp"] > 0).mean(),
            }
        )
    pd.DataFrame(resumo).round(2).to_csv(R / "validacao_resumo.csv", index=False)
    por_par = (
        out.groupby(["procedimento", "disciplina", "nome", "dado_par", "nome_par"])
        .agg(vezes_finalista=("divisao", "count"), efeito_descoberta_pp=("dif_descoberta_pp", "mean"),
             efeito_validacao_pp=("dif_validacao_pp", "mean"), pct_confirma=("confirma", lambda x: 100 * x.mean()))
        .reset_index().sort_values(["procedimento", "vezes_finalista"], ascending=[True, False])
    )
    por_par.round(2).to_csv(R / "validacao_por_par.csv", index=False)
    pd.set_option("display.width", 250, "display.max_columns", 30)
    print(pd.DataFrame(resumo).round(2).to_string(index=False))
    print(por_par.groupby("procedimento").head(6).round(1).to_string(index=False))


if __name__ == "__main__":
    sys.exit(main(int(sys.argv[1]) if len(sys.argv) > 1 else 40))
