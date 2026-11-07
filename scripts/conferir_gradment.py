"""Confere se a ordem de dificuldade das disciplinas mapeadas no GradMent aponta na mesma
direcao da UFRN. So agregados: a entrada sao consultas exportadas da producao (privado/, fora do Git).

Cada disciplina da UFRN (mapeamento aceito ou corrigido pela Catarina) e comparada com a taxa do
GradMent nas disciplinas do CEFET equivalentes. Publica so disciplinas com 10 ou mais tentativas.

Entradas (a versao 2 tem prioridade):
- privado/gradment_consulta3_v2.md : reprovacao correta (situacao REP/REPMF entre as concluidas).
- privado/gradment_consulta3.md    : versao 1, com passou = 0 (INCLUI disciplinas em andamento).
  Resultados da v1 sao gravados com definicao "nao_aprovada_inclui_em_andamento" e NAO vao para o README.

Saida: resultados/gradment_vs_ufrn.csv e resultados/gradment_vs_ufrn_resumo.json
Uso: python -I scripts/conferir_gradment.py
"""
import json
import sys
from pathlib import Path

import pandas as pd
from scipy.stats import spearmanr
from statsmodels.stats.proportion import proportion_confint

RAIZ = Path(__file__).resolve().parent.parent
V1 = RAIZ / "privado" / "gradment_consulta3.md"
V2 = RAIZ / "privado" / "gradment_consulta3_v2.md"
MIN_TENTATIVAS = 10
DEF_V2 = "reprovacao_REP_REPMF_entre_concluidas"
DEF_V1 = "nao_aprovada_inclui_em_andamento"


def ler_md(caminho, inteiros):
    linhas = [l.strip() for l in caminho.read_text(encoding="utf-8").splitlines() if l.strip().startswith("|")]
    cab = [c.strip() for c in linhas[0].strip("|").split("|")]
    df = pd.DataFrame([[c.strip() for c in l.strip("|").split("|")] for l in linhas[2:]], columns=cab)
    for c in inteiros:
        df[c] = df[c].astype(int)
    return df


def carregar():
    """Devolve (tabela por codigo com colunas tentativas e fracassos, definicao)."""
    if V2.exists():
        g = ler_md(V2, ["concluidas", "reprovadas", "trancadas", "em_andamento", "linhas"])
        t = g.set_index("cefet_codigo")[["concluidas", "reprovadas"]].rename(columns={"concluidas": "tentativas", "reprovadas": "fracassos"})
        return t, DEF_V2
    g = ler_md(V1, ["curso_id", "tentativas", "aprovadas", "nao_aprovadas", "alunos_distintos"])
    t = g.groupby("cefet_codigo").agg(tentativas=("tentativas", "sum"), fracassos=("nao_aprovadas", "sum"))
    return t, DEF_V1


def main():
    por_codigo, definicao = carregar()
    mapa = pd.read_csv(RAIZ / "dados" / "mapeamento_ufrn_cefet.csv", dtype=str)
    mapa = mapa[mapa["decisao_catarina"].isin(["aceito", "corrigido"]) & mapa["cefet_codigo"].notna()]
    disc = pd.read_csv(RAIZ / "resultados" / "disciplinas.csv").set_index("codigo")

    linhas = []
    for _, m in mapa.iterrows():
        codigos = [c.strip() for c in m["cefet_codigo"].split(";")]
        sub = por_codigo.reindex(codigos).dropna()
        tent = int(sub["tentativas"].sum()) if len(sub) else 0
        if tent < MIN_TENTATIVAS:
            continue
        k = int(sub["fracassos"].sum())
        lo, hi = proportion_confint(k, tent, alpha=0.05, method="wilson")
        linhas.append(
            {
                "ufrn_codigo": m["ufrn_codigo"], "ufrn_nome": m["ufrn_nome"],
                "ufrn_reprovacao_pct": round(float(disc.loc[m["ufrn_codigo"], "reprovacao_pct"]), 1),
                "cefet_codigos": "; ".join(codigos), "gradment_tentativas": tent,
                "gradment_taxa_pct": round(100 * k / tent, 1),
                "gradment_ic_inf": round(100 * lo, 1), "gradment_ic_sup": round(100 * hi, 1),
            }
        )
    df = pd.DataFrame(linhas)
    rho, p = spearmanr(df["ufrn_reprovacao_pct"], df["gradment_taxa_pct"])
    resumo = {
        "definicao": definicao,
        "n_pares": int(len(df)), "n_codigos_cefet_distintos": int(df["cefet_codigos"].nunique()),
        "spearman_rho": round(float(rho), 2), "spearman_p": round(float(p), 4),
        "min_tentativas_publicadas": MIN_TENTATIVAS,
        "ressalvas": [
            "UFRN: reprovacao por tentativa concluida, 2015 a 2019. GradMent: amostra pequena de alunos reais",
            "duas disciplinas da UFRN (Pre-Calculo e Calculo I) compartilham o mesmo equivalente do CEFET",
        ] + (["a taxa do GradMent conta disciplinas em andamento, trancadas e canceladas como nao aprovadas"] if definicao == DEF_V1 else []),
    }
    # so a definicao correta vai para resultados/ (publico); a v1 fica em privado/ (fora do Git)
    destino = RAIZ / ("resultados" if definicao == DEF_V2 else "privado")
    df.to_csv(destino / "gradment_vs_ufrn.csv", index=False)
    (destino / "gradment_vs_ufrn_resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"definicao: {definicao}; {resumo['n_pares']} pares; Spearman {resumo['spearman_rho']} (p = {resumo['spearman_p']})")


if __name__ == "__main__":
    sys.exit(main())
