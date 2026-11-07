"""Analise do Termometro: reprovacao por disciplina, pares de risco e curva por carga.

Metodo (decidido pela Catarina, ver DIARIO.md):
- Taxas por disciplina e curva por carga: TODOS os alunos (populacao hibrida).
- Pares de risco: so a coorte de calouros. "A dado B" = reprovacao em A de quem cursou B no
  mesmo semestre contra quem cursou A sem B. Comparacao estratificada por faixa (tercil) de
  desempenho anterior; efeito = diferenca de risco de Mantel-Haenszel (pontos percentuais),
  IC 95% por bootstrap dentro de cada faixa, p-valor pelo teste de Cochran-Mantel-Haenszel.
- Primeiro semestre (sem desempenho anterior): analise a parte, estratificada por grupo de curso.
- Suporte minimo: 100 alunos com o par. Correcao: Benjamini-Hochberg a 5%, por familia de testes.

Saida (so numeros agregados) em resultados/. Uso: python -I scripts/analise.py
"""
import json
import sys
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportion_confint
from statsmodels.stats.contingency_tables import StratifiedTable

RAIZ = Path(__file__).resolve().parent.parent
DB = RAIZ / "dados" / "termometro.duckdb"
SAIDA = RAIZ / "resultados"

SUPORTE_MIN = 100
ALFA = 0.05
N_BOOT = 2000
SEED = 20261107
RNG = np.random.default_rng(SEED)


def carregar():
    con = duckdb.connect(str(DB), read_only=True)
    df = con.execute(
        f"""SELECT t.aluno, t.semestre_idx, t.codigo_disciplina AS cod, t.resultado, t.situacao, t.desistiu,
                   t.desempenho_anterior AS desemp, t.numero_tentativa AS tentativa,
                   t.disciplinas_no_semestre AS carga, t.coorte_calouro AS calouro, c.grupo
            FROM tentativas t
            JOIN read_csv('{(RAIZ / "dados" / "cursos_escopo.csv").as_posix()}') c USING (id_curso)
            JOIN read_csv('{(RAIZ / "dados" / "disciplinas_escopo.csv").as_posix()}') d
                 ON d.codigo = t.codigo_disciplina
            WHERE t.efetiva AND NOT t.a_distancia"""
    ).df()
    con.close()
    nomes = pd.read_csv(RAIZ / "dados" / "disciplinas_escopo.csv").set_index("codigo")["nome"].to_dict()
    df["reprovou"] = (df["resultado"] == "REPROVADO").astype(int)
    df["concluiu"] = df["resultado"].isin(["APROVADO", "REPROVADO"])
    return df, nomes


def wilson(k, n):
    lo, hi = proportion_confint(k, n, alpha=0.05, method="wilson")
    return 100 * lo, 100 * hi


# ---------------------------------------------------------------- por disciplina
def tabela_disciplinas(df, nomes):
    linhas = []
    for cod, g in df.groupby("cod"):
        ar = g[g["concluiu"]]
        k, n = int(ar["reprovou"].sum()), len(ar)
        lo, hi = wilson(k, n)
        kd, nd = int(g["desistiu"].sum()), int((g["concluiu"] | g["desistiu"]).sum())
        dlo, dhi = wilson(kd, nd)
        linhas.append(
            {
                "codigo": cod, "disciplina": nomes[cod],
                "n_concluidas": n, "reprovacao_pct": 100 * k / n, "reprov_ic_inf": lo, "reprov_ic_sup": hi,
                "n_matriculas": nd, "desistencia_pct": 100 * kd / nd, "desist_ic_inf": dlo, "desist_ic_sup": dhi,
            }
        )
    return pd.DataFrame(linhas).sort_values("reprovacao_pct", ascending=False)


# ---------------------------------------------------------------- pares
def rd_mh(a, n1, c, n0):
    """Diferenca de risco de Mantel-Haenszel (expostos - nao expostos); vetores por faixa."""
    N = n1 + n0
    return np.sum((a * n0 - c * n1) / N) / np.sum(n1 * n0 / N)


def rd_boot(a, n1, c, n0):
    p1, p0 = a / n1, c / n0
    A = RNG.binomial(n1.astype(int), p1, size=(N_BOOT, len(n1)))
    C = RNG.binomial(n0.astype(int), p0, size=(N_BOOT, len(n1)))
    N = n1 + n0
    num = ((A * n0 - C * n1) / N).sum(axis=1)
    den = (n1 * n0 / N).sum()
    d = num / den
    return np.percentile(d, [2.5, 97.5])


def comparar(a_rows, expo, estrato):
    """a_rows: linhas de A (concluidas). expo: serie 0/1 'cursou B junto'. estrato: serie."""
    t = pd.DataFrame({"y": a_rows["reprovou"].values, "e": expo.values, "s": estrato.values})
    g = t.groupby(["s", "e"])["y"].agg(["sum", "count"]).unstack("e")
    if ("sum", 1) not in g.columns or ("sum", 0) not in g.columns:
        return None  # um dos grupos ficou vazio
    g = g.dropna()
    if g.empty:
        return None
    a, n1 = g[("sum", 1)].to_numpy(float), g[("count", 1)].to_numpy(float)
    c, n0 = g[("sum", 0)].to_numpy(float), g[("count", 0)].to_numpy(float)
    ok = (n1 > 0) & (n0 > 0)
    a, n1, c, n0 = a[ok], n1[ok], c[ok], n0[ok]
    if len(a) == 0:
        return None
    tabelas = [np.array([[x, m - x], [y_, k - y_]]) for x, m, y_, k in zip(a, n1, c, n0)]
    try:
        st = StratifiedTable(tabelas)
        p = st.test_null_odds(correction=True).pvalue
        or_mh = st.oddsratio_pooled
    except Exception:
        p, or_mh = np.nan, np.nan
    lo, hi = rd_boot(a, n1, c, n0)
    return {
        "n_com_par": int(n1.sum()), "n_sem_par": int(n0.sum()),
        "reprov_com_par_pct": 100 * a.sum() / n1.sum(), "reprov_sem_par_pct": 100 * c.sum() / n0.sum(),
        "dif_risco_pp": 100 * rd_mh(a, n1, c, n0), "ic_inf_pp": 100 * lo, "ic_sup_pp": 100 * hi,
        "odds_ratio_mh": or_mh, "p_cmh": p, "n_estratos": int(len(a)),
    }


def pares(df_cal, nomes, estrato_col, rotulo_familia):
    """df_cal: linhas de calouros ja filtradas pela familia. Retorna tabela de comparacoes."""
    base = df_cal[["aluno", "semestre_idx", "cod"]].drop_duplicates()
    base["v"] = 1
    M = base.pivot_table(index=["aluno", "semestre_idx"], columns="cod", values="v", aggfunc="max", fill_value=0)
    saida, sem_suporte = [], 0
    for A in sorted(nomes):
        ra = df_cal[(df_cal["cod"] == A) & df_cal["concluiu"]]
        if ra.empty:
            continue
        idx = pd.MultiIndex.from_frame(ra[["aluno", "semestre_idx"]])
        for B in sorted(nomes):
            if B == A or B not in M.columns:
                continue
            expo = pd.Series(M[B].reindex(idx).fillna(0).to_numpy(), index=ra.index)
            if expo.sum() < SUPORTE_MIN:
                sem_suporte += 1
                continue
            r = comparar(ra, expo, ra[estrato_col])
            if r is None:
                continue
            r.update({"familia": rotulo_familia, "disciplina": A, "nome": nomes[A], "dado_par": B, "nome_par": nomes[B]})
            saida.append(r)
    out = pd.DataFrame(saida)
    if not out.empty:
        ok = out["p_cmh"].notna()
        q = np.full(len(out), np.nan)
        q[ok.to_numpy()] = multipletests(out.loc[ok, "p_cmh"], alpha=ALFA, method="fdr_bh")[1]
        out["q_bh"] = q
        out["passa_bh"] = out["q_bh"] < ALFA
        out = out.sort_values("q_bh")
    return out, sem_suporte


# ---------------------------------------------------------------- curva por carga
def curva_carga(df):
    d = df[df["concluiu"] | df["desistiu"]].copy()
    d["faixa_carga"] = d["carga"].clip(upper=9)
    linhas = []
    pesos = d.groupby("cod").size() / len(d)
    d["nao_aprovou"] = ((d["reprovou"] == 1) | d["desistiu"]).astype(int)
    for desfecho, marca, base_ in (
        ("reprovacao", d["reprovou"], d[d["concluiu"]]),
        ("desistencia", d["desistiu"].astype(int), d),
        # reprovou OU trancou/desistiu, sobre todas as matriculas: junta os dois desfechos
        ("nao_aprovacao", d["nao_aprovou"], d),
    ):
        b = base_.copy()
        b["y"] = {"reprovacao": b["reprovou"], "desistencia": b["desistiu"].astype(int),
                  "nao_aprovacao": b["nao_aprovou"]}[desfecho]
        for f, g in b.groupby("faixa_carga"):
            n, k = len(g), int(g["y"].sum())
            lo, hi = wilson(k, n)
            # padronizada pela mistura de disciplinas (pesos fixos = peso de cada disciplina no total)
            cel = g.groupby("cod")["y"].agg(["sum", "count"])
            cel = cel[cel["count"] >= 10]
            w = pesos.reindex(cel.index)
            w = w / w.sum()
            padr = float((w * cel["sum"] / cel["count"]).sum())
            boots = []
            for _ in range(500):
                kk = RNG.binomial(cel["count"].to_numpy().astype(int), (cel["sum"] / cel["count"]).to_numpy())
                boots.append(float((w.to_numpy() * kk / cel["count"].to_numpy()).sum()))
            plo, phi = np.percentile(boots, [2.5, 97.5])
            linhas.append(
                {
                    "desfecho": desfecho, "disciplinas_no_semestre": f"{int(f)}{'+' if f >= 9 else ''}",
                    "n": n, "taxa_pct": 100 * k / n, "ic_inf": lo, "ic_sup": hi,
                    "taxa_padronizada_pct": 100 * padr, "padr_ic_inf": 100 * plo, "padr_ic_sup": 100 * phi,
                }
            )
    return pd.DataFrame(linhas)


def verificar_regressao(com_hist, nomes, tabela, n_max=12):
    """Metodo B: regressao logistica com controles, so para os candidatos de risco (efeito > 0
    que passou no Benjamini-Hochberg). Controles: desempenho anterior, numero da tentativa
    (1, 2, 3+), carga do semestre, grupo de curso e semestre do calendario. Erro padrao
    robusto agrupado por aluno."""
    import statsmodels.formula.api as smf

    cand = tabela[tabela["passa_bh"] & (tabela["dif_risco_pp"] > 0)].sort_values("dif_risco_pp", ascending=False).head(n_max)
    base = com_hist[["aluno", "semestre_idx", "cod"]].drop_duplicates()
    base["v"] = 1
    M = base.pivot_table(index=["aluno", "semestre_idx"], columns="cod", values="v", aggfunc="max", fill_value=0)
    linhas = []
    for _, r in cand.iterrows():
        ra = com_hist[(com_hist["cod"] == r["disciplina"]) & com_hist["concluiu"]].copy()
        idx = pd.MultiIndex.from_frame(ra[["aluno", "semestre_idx"]])
        ra["expo"] = M[r["dado_par"]].reindex(idx).fillna(0).to_numpy()
        ra["tent"] = ra["tentativa"].astype(float).clip(upper=3)
        for col in ("carga", "desemp", "semestre_idx", "reprovou"):
            ra[col] = ra[col].astype(float)
        ra["aluno_id"] = pd.factorize(ra["aluno"])[0]
        m = smf.logit("reprovou ~ expo + desemp + C(tent) + carga + C(grupo) + C(semestre_idx)", data=ra).fit(
            disp=0, cov_type="cluster", cov_kwds={"groups": ra["aluno_id"]}
        )
        b, ic, p = m.params["expo"], m.conf_int().loc["expo"], m.pvalues["expo"]
        linhas.append(
            {
                "disciplina": r["disciplina"], "nome": r["nome"], "dado_par": r["dado_par"], "nome_par": r["nome_par"],
                "n": int(len(ra)), "n_com_par": int(ra["expo"].sum()),
                "dif_risco_mh_pp": r["dif_risco_pp"], "odds_ratio_mh": r["odds_ratio_mh"],
                "odds_ratio_regressao": float(np.exp(b)), "or_ic_inf": float(np.exp(ic[0])), "or_ic_sup": float(np.exp(ic[1])),
                "p_regressao": float(p),
            }
        )
    out = pd.DataFrame(linhas)
    # Benjamini-Hochberg tambem aqui: "p < 0,05" solto nao serve para 12 regressoes
    out["q_bh_regressao"] = multipletests(out["p_regressao"], alpha=ALFA, method="fdr_bh")[1]
    out["mantem_apos_bh"] = (out["odds_ratio_regressao"] > 1) & (out["q_bh_regressao"] < ALFA)
    return out


def main():
    SAIDA.mkdir(exist_ok=True)
    df, nomes = carregar()

    disc = tabela_disciplinas(df, nomes)
    disc.round(2).to_csv(SAIDA / "disciplinas.csv", index=False)

    cal = df[df["calouro"]].copy()
    # faixas de desempenho anterior: tercis no nivel aluno-semestre, so quem tem historico
    com_hist = cal[cal["desemp"].notna()].copy()
    ua = com_hist[["aluno", "semestre_idx", "desemp"]].drop_duplicates()
    cortes = ua["desemp"].quantile([1 / 3, 2 / 3]).to_numpy()
    com_hist["faixa"] = np.digitize(com_hist["desemp"], cortes)  # 0 baixa, 1 media, 2 alta
    p_hist, sem_sup_h = pares(com_hist, nomes, "faixa", "com_historico")
    p_hist.round(4).to_csv(SAIDA / "pares_com_historico.csv", index=False)

    reg = verificar_regressao(com_hist, nomes, p_hist)
    reg.round(4).to_csv(SAIDA / "pares_regressao.csv", index=False)

    primeiro = cal[cal["desemp"].isna()].copy()
    p_prim, sem_sup_p = pares(primeiro, nomes, "grupo", "primeiro_semestre")
    p_prim.round(4).to_csv(SAIDA / "pares_primeiro_semestre.csv", index=False)

    curva = curva_carga(df)
    curva.round(2).to_csv(SAIDA / "curva_carga.csv", index=False)

    meta = {
        "semente": SEED, "suporte_minimo": SUPORTE_MIN, "alfa_bh": ALFA, "bootstrap": N_BOOT,
        "cortes_desempenho_anterior_tercis": [float(x) for x in cortes],
        "linhas_total": int(len(df)), "linhas_calouros": int(len(cal)),
        "linhas_calouros_com_historico": int(len(com_hist)), "linhas_calouros_primeiro_semestre": int(len(primeiro)),
        "comparacoes_testadas_com_historico": int(len(p_hist)), "sem_suporte_com_historico": sem_sup_h,
        "passam_bh_com_historico": int(p_hist["passa_bh"].sum()) if not p_hist.empty else 0,
        "comparacoes_testadas_primeiro_semestre": int(len(p_prim)), "sem_suporte_primeiro_semestre": sem_sup_p,
        "passam_bh_primeiro_semestre": int(p_prim["passa_bh"].sum()) if not p_prim.empty else 0,
    }
    (SAIDA / "metodo.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(meta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    sys.exit(main())
