"""Exporta dados/termometro.json: tudo que a tela precisa, so agregados (nenhum dado de aluno).

A tela le este arquivo; o LLM da rota /api/explicar recebe trechos dele e nunca calcula.
O mapeamento UFRN -> CEFET so aparece para linhas que a Catarina revisou (aceito/corrigido).

Uso: python -I scripts/exportar_json.py   (depois de analise, checagens, validacao, gerar_achados)
"""
import json
import re
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
R = RAIZ / "resultados"


def num(x, casas=2):
    return None if pd.isna(x) else round(float(x), casas)


def parse_achados(texto):
    achados = []
    for bloco in re.split(r"\n(?=## )", texto):  # cada secao "## ..." e um bloco; so os achados interessam
        m = re.match(r"## Achado (\d+)\.\s*(.+)", bloco)
        if not m:
            continue

        def campo(rotulo, seguinte):
            r = re.search(rf"- \*\*{rotulo}:?\*\*\s*(.*?)(?=\n- \*\*{seguinte}|\Z)", bloco, re.S)
            return r.group(1).strip() if r else None

        achados.append(
            {
                "id": int(m.group(1)),
                "titulo": m.group(2).strip(),
                "numero": campo("Número", "E daí\\?"),
                "e_dai": campo("E daí\\?", "Limitação"),
                "limitacao": campo("Limitação", "XXXX"),
            }
        )
    return achados


def main():
    meta = json.loads((R / "metodo.json").read_text(encoding="utf-8"))
    disc = pd.read_csv(R / "disciplinas.csv")
    curva = pd.read_csv(R / "curva_carga.csv", dtype={"disciplinas_no_semestre": str})
    chk = pd.read_csv(R / "checagens_auditoria.csv")
    sob = pd.read_csv(R / "sobreviventes_auditoria.csv")
    vres = pd.read_csv(R / "validacao_resumo.csv").set_index("procedimento")
    vpar = pd.read_csv(R / "validacao_por_par.csv")
    mapa = pd.read_csv(RAIZ / "dados" / "mapeamento_ufrn_cefet.csv").set_index("ufrn_codigo")

    disciplinas = []
    for _, d in disc.iterrows():
        mp = mapa.loc[d["codigo"]]
        decisao = (mp["decisao_catarina"] if isinstance(mp["decisao_catarina"], str) else "").strip().lower()
        cefet = None
        if decisao in ("aceito", "corrigido") and isinstance(mp["cefet_codigo"], str):
            cefet = {
                "codigo": mp["cefet_codigo"], "nome": mp["cefet_nome"], "cursos": mp["cefet_cursos"],
                "cobertura": mp["cobertura"], "correcao": mp["correcao_catarina"] if isinstance(mp["correcao_catarina"], str) else None,
            }
        disciplinas.append(
            {
                "codigo": d["codigo"], "nome": d["disciplina"], "tentativas_concluidas": int(d["n_concluidas"]),
                "reprovacao_pct": num(d["reprovacao_pct"]), "reprovacao_ic": [num(d["reprov_ic_inf"]), num(d["reprov_ic_sup"])],
                "desistencia_pct": num(d["desistencia_pct"]), "desistencia_ic": [num(d["desist_ic_inf"]), num(d["desist_ic_sup"])],
                "mapeamento_status": decisao or "pendente", "cefet": cefet,
            }
        )

    curva_json = {}
    for desf, g in curva.groupby("desfecho"):
        curva_json[desf] = [
            {"disciplinas_no_semestre": r["disciplinas_no_semestre"], "n": int(r["n"]), "taxa_pct": num(r["taxa_pct"]),
             "ic": [num(r["ic_inf"]), num(r["ic_sup"])], "taxa_padronizada_pct": num(r["taxa_padronizada_pct"])}
            for _, r in g.iterrows()
        ]

    candidatos = [
        {
            "disciplina": r["disciplina"], "nome": r["nome"], "cursada_junto_com": r["dado_par"], "nome_par": r["nome_par"],
            "alunos_com_par": int(r["n_com_par"]), "pct_repetindo_a_outra": num(r["pct_B_repeticao_entre_expostos"], 1),
            "dif_mh_pp": num(r["dif_MH_pp"], 1),
            "alunos_com_par_na_primeira_vez": None if pd.isna(r["limpo_n_com_par"]) else int(r["limpo_n_com_par"]),
        }
        for _, r in chk.iterrows()
    ]
    sobreviventes = []
    for _, s in sob.iterrows():
        v = vpar[(vpar["procedimento"] == "revisado") & (vpar["disciplina"] == s["disciplina"]) & (vpar["dado_par"] == s["dado_par"])]
        sobreviventes.append(
            {
                "disciplina": s["disciplina"], "nome": s["nome"], "cursada_junto_com": s["dado_par"], "nome_par": s["nome_par"],
                "alunos_com_par": int(s["n_com_par"]), "alunos_sem_par": int(s["n_sem_par"]),
                "dif_pp": num(s["dif_MH_pp"], 1), "ic": [num(s["ic_cluster_inf"], 1), num(s["ic_cluster_sup"], 1)],
                "odds_ratio_sem_carga": num(s["or_sem_carga"]), "or_ic": [num(s["or_ic_inf"]), num(s["or_ic_sup"])],
                "p_regressao": num(s["p"], 4),
                "divisoes_escolhido": None if v.empty else int(v.iloc[0]["vezes_finalista"]),
                "pct_confirma_na_validacao": None if v.empty else num(v.iloc[0]["pct_confirma"], 0),
            }
        )

    saida = {
        "versao": 1,
        "fonte": {
            "instituicao": "UFRN", "origem": "dados.ufrn.br (dados abertos)", "periodo": "2015.1 a 2019.2",
            "nivel": "graduação presencial", "grupos_de_curso": ["Ciências e Tecnologia", "Engenharias", "Computação"],
        },
        "populacao": {
            "linhas_analisadas": meta["linhas_total"], "linhas_calouros": meta["linhas_calouros"],
            "definicao_calouro": "aluno cuja primeira matrícula efetiva observada é de 2015.2 ou depois",
        },
        "avisos": {
            "unidade": "As taxas são por tentativa de matrícula, não por aluno: quem repete conta de novo.",
            "causalidade": "Associação observada. Não indica que cursar uma disciplina cause reprovação em outra.",
            "etico": (RAIZ / "dados" / "aviso_etico.txt").read_text(encoding="utf-8").strip(),  # decisao da Catarina (opcao C)
        },
        "disciplinas": disciplinas,
        "curva_carga": curva_json,
        "pares": {"candidatos": candidatos, "sobreviventes": sobreviventes},
        "validacao": {
            k: {"divisoes": int(v["divisoes"]), "efeito_descoberta_pp": num(v["efeito_descoberta_medio_pp"], 1),
                "efeito_validacao_pp": num(v["efeito_validacao_medio_pp"], 1), "inflacao_pp": num(v["inflacao_media_pp"], 1),
                "pct_confirma": num(v["pct_confirma_na_validacao"], 0)}
            for k, v in vres.iterrows()
        },
        "achados": parse_achados((RAIZ / "achados" / "ACHADOS.md").read_text(encoding="utf-8")),
    }
    destino = RAIZ / "dados" / "termometro.json"
    destino.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{destino.name}: {destino.stat().st_size / 1024:.1f} KB, {len(saida['disciplinas'])} disciplinas, {len(saida['achados'])} achados")


if __name__ == "__main__":
    sys.exit(main())
