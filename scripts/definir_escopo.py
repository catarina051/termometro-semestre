"""Fixa o escopo do Termometro e grava dois CSV versionados.

Decisoes da Catarina (ver DIARIO.md):
- Cursos: Ciencias e Tecnologia (BC&T) + Engenharias + Computacao.
- Disciplinas: as 15 mais cursadas nesse escopo (lista A), so presenciais, matriculas efetivas.

Saida:
- dados/cursos_escopo.csv       id_curso, grupo, nome_fonte
- dados/disciplinas_escopo.csv  posicao, codigo, nome, tentativas, alunos, calouros

Uso: python -I scripts/definir_escopo.py   (depois de construir_tentativas.py)
"""
import csv
import sys
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parent.parent
DB = RAIZ / "dados" / "termometro.duckdb"
DISCENTES = (RAIZ / "dados" / "brutos" / "discentes").as_posix()

N_DISCIPLINAS = 15

# Os CSV da UFRN chegam com acentos perdidos; os nomes de exibicao sao restaurados a mao.
NOMES = {
    "ECT2102": "Vetores e Geometria Analítica",
    "ECT2103": "Cálculo I",
    "ECT2101": "Pré-Cálculo",
    "ECT2104": "Química Geral",
    "ECT2106": "Ciência, Tecnologia e Sociedade",
    "ECT2105": "Práticas de Leitura e Escrita I",
    "ECT2206": "Gestão e Economia da Ciência, Tecnologia e Inovação",
    "ECT2205": "Práticas de Leitura e Escrita II",
    "ECT2302": "Metodologia Científica e Tecnológica",
    "ECT2204": "Introdução à Física Clássica I",
    "ECT2203": "Lógica de Programação",
    "ECT2201": "Cálculo II",
    "ECT2305": "Prática de Leitura em Inglês",
    "ECT2303": "Linguagem de Programação",
    "ECT2207": "Probabilidade e Estatística",
}

CURSOS_SQL = f"""
CREATE OR REPLACE TEMP TABLE cursos_escopo AS
SELECT * FROM (
    SELECT id_curso,
           CASE WHEN nome LIKE 'CI%NCIAS E TECNOLOGIA' THEN 'BCT'
                WHEN nome LIKE 'ENGENHARIA%' THEN 'ENG'
                WHEN nome LIKE 'TECNOLOGIA DA INFORMA%' OR nome LIKE '%COMPUTA%'
                     OR nome LIKE 'SISTEMAS DE INFORMA%' THEN 'COMP' END AS grupo,
           nome AS nome_fonte
    FROM (SELECT id_curso, ANY_VALUE(nome_curso) AS nome
          FROM read_csv('{DISCENTES}/*.csv', delim=';', header=true, all_varchar=true,
                        union_by_name=true)
          WHERE nivel_ensino LIKE 'GRADUA%' GROUP BY 1)
) WHERE grupo IS NOT NULL;
"""


def main():
    con = duckdb.connect(str(DB))
    con.execute(CURSOS_SQL)
    cursos = con.execute("SELECT id_curso, grupo, nome_fonte FROM cursos_escopo ORDER BY 2, 3").fetchall()
    # cursos que tem tentativas na tabela
    com_dados = {r[0] for r in con.execute("SELECT DISTINCT id_curso FROM tentativas").fetchall()}
    cursos = [c for c in cursos if c[0] in com_dados]

    top = con.execute(
        f"""SELECT t.codigo_disciplina, COUNT(*) AS tentativas,
                   COUNT(DISTINCT t.aluno) AS alunos,
                   COUNT(DISTINCT t.aluno) FILTER (WHERE t.coorte_calouro) AS calouros
            FROM tentativas t JOIN cursos_escopo c USING (id_curso)
            WHERE t.efetiva AND NOT t.a_distancia AND t.codigo_disciplina IS NOT NULL
            GROUP BY 1 ORDER BY 2 DESC LIMIT {N_DISCIPLINAS}"""
    ).fetchall()
    con.close()

    faltando = [t[0] for t in top if t[0] not in NOMES]
    if faltando:
        raise SystemExit(f"Falta nome de exibicao para: {faltando}")

    with open(RAIZ / "dados" / "cursos_escopo.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["id_curso", "grupo", "nome_fonte"])
        w.writerows(cursos)
    with open(RAIZ / "dados" / "disciplinas_escopo.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["posicao", "codigo", "nome", "tentativas", "alunos", "calouros"])
        for i, (cod, tent, alu, cal) in enumerate(top, 1):
            w.writerow([i, cod, NOMES[cod], tent, alu, cal])
    print(f"{len(cursos)} cursos, {len(top)} disciplinas")
    for i, (cod, tent, alu, cal) in enumerate(top, 1):
        print(f"{i:2d} {cod} {NOMES[cod]}: {tent} tentativas, {alu} alunos, {cal} calouros")


if __name__ == "__main__":
    sys.exit(main())
