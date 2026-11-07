"""Constroi a tabela `tentativas` (DuckDB) a partir dos CSV brutos da UFRN.

Uma linha por (aluno, turma) de GRADUACAO, 2015.1 a 2019.2.
Saida: dados/termometro.duckdb (ignorado pelo Git; os numeros agregados vao para JSON depois).

Uso: python -I scripts/construir_tentativas.py

Decisoes de metodo (ver DIARIO.md):
- Populacao hibrida: todas as linhas valem para taxas e curva por carga;
  `coorte_calouro` marca quem foi visto entrando (1o semestre observado >= 2015.2),
  e so essa coorte tem `numero_tentativa` e `desempenho_anterior` confiaveis.
- `resultado` (APROVADO / REPROVADO / OUTRO): REPROVADO e qualquer situacao que comece com
  "REPROVADO"; CANCELADO, EXCLUIDA, INDEFERIDO etc. nao sao reprovacao.
- `desistiu` (TRANCADO ou DESISTENCIA) e uma coluna a parte, pedida pela Catarina.
"""
import sys
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parent.parent
BRUTOS = (RAIZ / "dados" / "brutos").as_posix()
DB = RAIZ / "dados" / "termometro.duckdb"

LER = "delim=';', quote='\"', header=true, all_varchar=true, union_by_name=true"

SQL = f"""
CREATE OR REPLACE TABLE tentativas AS
WITH
mat AS (
    SELECT id_turma, discente AS aluno, id_curso, descricao,
           TRY_CAST(REPLACE(NULLIF(media_final, ''), ',', '.') AS DOUBLE) AS nota,
           TRY_CAST(NULLIF(numero_total_faltas, '') AS DOUBLE) AS faltas
    FROM read_csv('{BRUTOS}/matriculas-componentes/*.csv', {LER})
),
-- Uma matricula vira varias linhas (uma por unidade) e, as vezes, uma linha extra
-- EXCLUIDA/INDEFERIDO de um pedido anterior. Fica a linha de maior prioridade.
prio AS (
    SELECT *,
        CASE
            WHEN descricao LIKE 'APROVADO%' OR descricao LIKE 'REPROVADO%'
                 OR descricao IN ('CUMPRIU', 'DISPENSADO') THEN 3
            WHEN descricao IN ('TRANCADO', 'DESISTENCIA', 'MATRICULADO',
                               'CANCELADO', 'TRANSFERIDO', 'INCORPORADO') THEN 2
            ELSE 1  -- EXCLUIDA, INDEFERIDO, AGUARDANDO DEFERIMENTO, EM ESPERA
        END AS p
    FROM mat
),
melhor AS (
    SELECT id_turma, aluno, MAX(p) AS p FROM prio GROUP BY 1, 2
),
-- entre as linhas de maior prioridade, a situacao mais frequente (desempate: ordem alfabetica)
situacao AS (
    SELECT pr.id_turma, pr.aluno,
           ANY_VALUE(pr.id_curso) AS id_curso,
           MIN(pr.descricao) AS situacao,
           MAX(pr.nota) AS nota,
           MAX(pr.faltas) AS faltas,
           COUNT(DISTINCT pr.descricao) AS n_situacoes_empate
    FROM prio pr JOIN melhor m ON pr.id_turma = m.id_turma AND pr.aluno = m.aluno AND pr.p = m.p
    GROUP BY 1, 2
),
turma AS (
    -- os CSV de turmas repetem turmas entre semestres (148.761 linhas, 89.594 turmas)
    SELECT DISTINCT id_turma, CAST(ano AS INT) AS ano, CAST(periodo AS INT) AS periodo,
           id_componente_curricular, distancia = 'true' AS a_distancia
    FROM read_csv('{BRUTOS}/turmas/*.csv', {LER})
    WHERE nivel_ensino LIKE 'GRADUA%'
),
comp AS (
    SELECT id_componente, codigo, nome
    FROM read_csv(['{BRUTOS}/componentes-curriculares/componentes-curriculares-presenciais.csv',
                   '{BRUTOS}/componentes-curriculares/componentes-curriculares-semi-presenciais.csv',
                   '{BRUTOS}/componentes-curriculares/componentes-curriculares-ead.csv'],
                  {LER}, ignore_errors=true)
    QUALIFY ROW_NUMBER() OVER (PARTITION BY id_componente ORDER BY id_componente) = 1
),
base AS (
    SELECT s.aluno, s.id_curso, s.id_turma,
           t.ano, t.periodo, t.ano * 2 + (t.periodo - 1) AS semestre_idx,
           t.ano || '.' || t.periodo AS semestre,
           t.a_distancia,
           c.codigo AS codigo_disciplina, c.nome AS nome_disciplina,
           s.situacao, s.nota, s.faltas,
           CASE WHEN s.situacao LIKE 'APROVADO%' OR s.situacao = 'CUMPRIU' THEN 'APROVADO'
                WHEN s.situacao LIKE 'REPROVADO%' THEN 'REPROVADO'
                ELSE 'OUTRO' END AS resultado,
           -- desistencia: o aluno chegou a se matricular e saiu (trancou ou desistiu).
           -- Fica separada de `resultado`: nao e reprovacao nem aprovacao.
           s.situacao IN ('TRANCADO', 'DESISTENCIA') AS desistiu,
           -- conta na carga do semestre: matricula que existiu de fato
           s.situacao NOT IN ('CANCELADO', 'EXCLUIDA', 'INDEFERIDO', 'AGUARDANDO DEFERIMENTO',
                              'EM ESPERA', 'DISPENSADO', 'TRANSFERIDO', 'INCORPORADO') AS efetiva
    FROM situacao s
    JOIN turma t ON t.id_turma = s.id_turma
    LEFT JOIN comp c ON c.id_componente = t.id_componente_curricular
),
primeiro AS (
    SELECT aluno, MIN(semestre_idx) AS primeiro_idx FROM base WHERE efetiva GROUP BY 1
)
SELECT b.aluno, b.id_curso, b.id_turma, b.codigo_disciplina, b.nome_disciplina,
       b.semestre, b.semestre_idx, b.a_distancia,
       b.situacao, b.resultado, b.desistiu, b.nota, b.faltas, b.efetiva,
       -- carga do semestre: disciplinas distintas com matricula efetiva
       COUNT(DISTINCT CASE WHEN b.efetiva THEN b.codigo_disciplina END)
           OVER (PARTITION BY b.aluno, b.semestre_idx) AS disciplinas_no_semestre,
       -- so conta tentativas que terminaram em aprovacao ou reprovacao
       CASE WHEN b.resultado IN ('APROVADO', 'REPROVADO') THEN
           ROW_NUMBER() OVER (PARTITION BY b.aluno, b.codigo_disciplina,
                                           b.resultado IN ('APROVADO', 'REPROVADO')
                              ORDER BY b.semestre_idx, b.id_turma)
       END AS numero_tentativa,
       -- media das notas finais de semestres anteriores (so semestres estritamente antes)
       AVG(CASE WHEN b.efetiva AND b.resultado IN ('APROVADO', 'REPROVADO') THEN b.nota END)
           OVER (PARTITION BY b.aluno ORDER BY b.semestre_idx
                 RANGE BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS desempenho_anterior,
       p.primeiro_idx IS NOT NULL AND p.primeiro_idx >= 2015 * 2 + 1 AS coorte_calouro
FROM base b
LEFT JOIN primeiro p USING (aluno)
WHERE b.semestre_idx BETWEEN 2015 * 2 AND 2019 * 2 + 1;
"""


def main():
    con = duckdb.connect(str(DB))
    con.execute(SQL)
    total, alunos, turmas = con.execute(
        "SELECT COUNT(*), COUNT(DISTINCT aluno), COUNT(DISTINCT id_turma) FROM tentativas"
    ).fetchone()
    print(f"tentativas: {total:,} linhas, {alunos:,} alunos, {turmas:,} turmas")
    cal = con.execute(
        "SELECT COUNT(DISTINCT aluno) FROM tentativas WHERE coorte_calouro"
    ).fetchone()[0]
    print(f"coorte_calouro: {cal:,} alunos")
    con.close()


if __name__ == "__main__":
    sys.exit(main())
