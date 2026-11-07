"""Checagens pedidas pela auditoria (Opus sem contexto): o par e so atraso no curso?

Para os candidatos de risco (resultados/pares_regressao.csv):
 1. Quanto de "cursou B junto" e repeticao de B / de A (atraso no fluxo)?
 2. O efeito sobrevive quando B e A estao na 1a vez (sem repeticao)?
 3. Trancamento de A e reprovacao por faltas: mudam com B?
 4. Sobreviventes: A e B na 1a vez, IC por aluno inteiro e regressao sem a carga.
Saida agregada: resultados/checagens_auditoria.csv. Uso: python -I scripts/checagens_auditoria.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analise as an  # noqa: E402

R = an.SAIDA


def rd_cluster_boot(ra, n_rep=1000):
    """IC 95% da diferenca de risco de Mantel-Haenszel reamostrando ALUNOS inteiros."""
    y = ra["reprovou"].to_numpy(float)
    e = ra["expo"].to_numpy(float)
    f = ra["faixa"].to_numpy(int)
    ids = pd.factorize(ra["aluno"])[0]
    n_al = ids.max() + 1

    def rd(w):
        num = den = 0.0
        for k in np.unique(f):
            m = f == k
            n1, n0 = (w[m] * e[m]).sum(), (w[m] * (1 - e[m])).sum()
            if n1 == 0 or n0 == 0:
                continue
            a, c = (w[m] * e[m] * y[m]).sum(), (w[m] * (1 - e[m]) * y[m]).sum()
            N = n1 + n0
            num += (a * n0 - c * n1) / N
            den += n1 * n0 / N
        return num / den if den else np.nan

    pontual = rd(np.ones(len(y)))
    boots = [rd(np.bincount(an.RNG.integers(0, n_al, n_al), minlength=n_al)[ids].astype(float)) for _ in range(n_rep)]
    lo, hi = np.nanpercentile(boots, [2.5, 97.5])
    return 100 * pontual, 100 * lo, 100 * hi


def sobreviventes(com_hist, nomes, B_any, out):
    """Candidatos que sobram quando A e B estao na 1a vez e ha pelo menos 100 alunos nos dois bracos."""
    import duckdb
    import statsmodels.formula.api as smf

    con = duckdb.connect(str(an.DB), read_only=True)
    pri = con.execute("SELECT aluno, MIN(semestre_idx) AS primeiro_idx FROM tentativas WHERE efetiva GROUP BY 1").df()
    con.close()
    com_hist = com_hist.merge(pri, on="aluno", how="left")
    com_hist["sem_desde_entrada"] = (com_hist["semestre_idx"] - com_hist["primeiro_idx"]).astype(float)

    regra = out[(out["limpo_n_com_par"] >= 100) & (out["limpo_n_sem_par"] >= 100) & (out["limpo_ic_inf"] > 0)]
    linhas = []
    for _, c in regra.iterrows():
        A, Bc = c["disciplina"], c["dado_par"]
        ra = com_hist[(com_hist["cod"] == A) & com_hist["concluiu"]].copy()
        idx = pd.MultiIndex.from_frame(ra[["aluno", "semestre_idx"]])
        bval = B_any[Bc].reindex(idx).to_numpy()
        ra["expo"] = (~pd.isna(bval)).astype(int)
        ra["b_repete"] = np.where(pd.isna(bval), False, bval.astype(object) == True)  # noqa: E712
        limpo = ra[(~ra["repeticao"]) & ((ra["expo"] == 0) | (~ra["b_repete"]))].copy()
        pont, lo, hi = rd_cluster_boot(limpo)
        # desfecho composto: reprovou OU trancou/desistiu, sobre todas as matriculas efetivas de A
        tod = com_hist[(com_hist["cod"] == A) & (com_hist["concluiu"] | com_hist["desistiu"])].copy()
        i2 = pd.MultiIndex.from_frame(tod[["aluno", "semestre_idx"]])
        b2 = B_any[Bc].reindex(i2).to_numpy()
        tod["expo"] = (~pd.isna(b2)).astype(int)
        tod["b_repete"] = np.where(pd.isna(b2), False, b2.astype(object) == True)  # noqa: E712
        tod = tod[(~tod["repeticao"]) & ((tod["expo"] == 0) | (~tod["b_repete"]))].copy()
        tod["reprovou"] = ((tod["reprovou"] == 1) | tod["desistiu"]).astype(int)
        comp = an.comparar(tod, tod["expo"], tod["faixa"])
        for col in ("desemp", "semestre_idx", "reprovou"):
            limpo[col] = limpo[col].astype(float)
        limpo["aluno_id"] = pd.factorize(limpo["aluno"])[0]
        m = smf.logit("reprovou ~ expo + desemp + C(grupo) + C(semestre_idx) + sem_desde_entrada", data=limpo).fit(
            disp=0, cov_type="cluster", cov_kwds={"groups": limpo["aluno_id"]}
        )
        ic = m.conf_int().loc["expo"]
        linhas.append(
            {
                "disciplina": A, "nome": nomes[A], "dado_par": Bc, "nome_par": nomes[Bc],
                "n_com_par": int(limpo["expo"].sum()), "n_sem_par": int((1 - limpo["expo"]).sum()),
                "dif_MH_pp": pont, "ic_cluster_inf": lo, "ic_cluster_sup": hi,
                "composto_dif_MH_pp": comp["dif_risco_pp"], "composto_ic_inf": comp["ic_inf_pp"],
                "composto_ic_sup": comp["ic_sup_pp"],
                "or_sem_carga": float(np.exp(m.params["expo"])), "or_ic_inf": float(np.exp(ic[0])),
                "or_ic_sup": float(np.exp(ic[1])), "p": float(m.pvalues["expo"]),
            }
        )
    res = pd.DataFrame(linhas)
    res.round(3).to_csv(R / "sobreviventes_auditoria.csv", index=False)
    print("\nSobreviventes (A e B na 1a vez, IC por aluno, regressao sem carga):")
    print(res[["nome", "nome_par", "n_com_par", "n_sem_par", "dif_MH_pp", "ic_cluster_inf", "ic_cluster_sup", "or_sem_carga", "or_ic_inf", "or_ic_sup", "p"]].round(3).to_string(index=False))


def main():
    df, nomes = an.carregar()
    # primeira vez em que o aluno aparece em cada disciplina (matricula efetiva observada)
    prim = df.groupby(["aluno", "cod"])["semestre_idx"].min().rename("prim_cod")
    df = df.join(prim, on=["aluno", "cod"])
    df["repeticao"] = df["semestre_idx"] > df["prim_cod"]

    cal = df[df["calouro"]]
    com_hist = cal[cal["desemp"].notna()].copy()
    ua = com_hist[["aluno", "semestre_idx", "desemp"]].drop_duplicates()
    cortes = ua["desemp"].quantile([1 / 3, 2 / 3]).to_numpy()
    com_hist["faixa"] = np.digitize(com_hist["desemp"], cortes)

    # B por (aluno, semestre): matricula efetiva e se e repeticao
    b = com_hist[["aluno", "semestre_idx", "cod", "repeticao"]].drop_duplicates(["aluno", "semestre_idx", "cod"])
    B_any = b.pivot(index=["aluno", "semestre_idx"], columns="cod", values="repeticao")  # NaN = nao cursou

    cand = pd.read_csv(R / "pares_regressao.csv")
    linhas = []
    for _, c in cand.iterrows():
        A, Bc = c["disciplina"], c["dado_par"]
        ra = com_hist[(com_hist["cod"] == A) & com_hist["concluiu"]].copy()
        idx = pd.MultiIndex.from_frame(ra[["aluno", "semestre_idx"]])
        bval = B_any[Bc].reindex(idx).to_numpy() if Bc in B_any.columns else np.full(len(ra), np.nan)
        ra["expo"] = (~pd.isna(bval)).astype(int)
        ra["b_repete"] = np.where(pd.isna(bval), False, bval.astype(object) == True)  # noqa: E712

        com, sem = ra[ra["expo"] == 1], ra[ra["expo"] == 0]
        base = an.comparar(ra, ra["expo"], ra["faixa"])
        # so "na primeira vez": A nao e repeticao e, entre os expostos, B tambem nao
        limpo = ra[(~ra["repeticao"]) & ((ra["expo"] == 0) | (~ra["b_repete"]))]
        rl = an.comparar(limpo, limpo["expo"], limpo["faixa"])
        # A e B ambas na 1a vez, tambem nos nao expostos? (A na 1a vez ja esta no filtro)

        # desistencia e falta (todas as matriculas efetivas de A, nao so as concluidas)
        todas = com_hist[com_hist["cod"] == A].copy()
        idx2 = pd.MultiIndex.from_frame(todas[["aluno", "semestre_idx"]])
        todas["expo"] = B_any[Bc].reindex(idx2).notna().to_numpy().astype(int)
        rep = ra[ra["reprovou"] == 1]
        falta = rep["situacao"].str.contains("FALTA", na=False)

        linhas.append(
            {
                "disciplina": A, "nome": nomes[A], "dado_par": Bc, "nome_par": nomes[Bc],
                "n_com_par": len(com), "pct_B_repeticao_entre_expostos": 100 * com["b_repete"].mean(),
                "pct_A_repeticao_com_par": 100 * com["repeticao"].mean(),
                "pct_A_repeticao_sem_par": 100 * sem["repeticao"].mean(),
                "dif_MH_pp": base["dif_risco_pp"], "dif_MH_ic_inf": base["ic_inf_pp"], "dif_MH_ic_sup": base["ic_sup_pp"],
                "limpo_n_com_par": rl["n_com_par"] if rl else np.nan,
                "limpo_n_sem_par": rl["n_sem_par"] if rl else np.nan,
                "limpo_dif_MH_pp": rl["dif_risco_pp"] if rl else np.nan,
                "limpo_ic_inf": rl["ic_inf_pp"] if rl else np.nan, "limpo_ic_sup": rl["ic_sup_pp"] if rl else np.nan,
                "limpo_p_cmh": rl["p_cmh"] if rl else np.nan,
                "desist_A_com_par_pct": 100 * todas.loc[todas["expo"] == 1, "desistiu"].mean(),
                "desist_A_sem_par_pct": 100 * todas.loc[todas["expo"] == 0, "desistiu"].mean(),
                "pct_reprov_por_falta_com_par": 100 * falta[rep.index.isin(com.index)].mean(),
                "pct_reprov_por_falta_sem_par": 100 * falta[rep.index.isin(sem.index)].mean(),
            }
        )
    out = pd.DataFrame(linhas)
    out.round(3).to_csv(R / "checagens_auditoria.csv", index=False)
    sobreviventes(com_hist, nomes, B_any, out)

    pd.set_option("display.width", 250, "display.max_columns", 40)
    cols = ["nome", "nome_par", "n_com_par", "pct_B_repeticao_entre_expostos", "pct_A_repeticao_com_par",
            "pct_A_repeticao_sem_par", "dif_MH_pp", "limpo_n_com_par", "limpo_n_sem_par", "limpo_dif_MH_pp",
            "limpo_ic_inf", "limpo_ic_sup"]
    print(out[cols].round(1).to_string(index=False))
    print()
    print(out[["nome", "nome_par", "desist_A_com_par_pct", "desist_A_sem_par_pct",
               "pct_reprov_por_falta_com_par", "pct_reprov_por_falta_sem_par"]].round(1).to_string(index=False))


if __name__ == "__main__":
    sys.exit(main())
