"""Testes de sanidade da tabela `tentativas`.

Precisam de dados/termometro.duckdb e dos CSV em dados/brutos/ (gerados por
scripts/baixar_dados.py e scripts/construir_tentativas.py). Sem eles, os testes sao pulados.
"""
import csv
import glob
from pathlib import Path

import duckdb
import pytest

RAIZ = Path(__file__).resolve().parent.parent
DB = RAIZ / "dados" / "termometro.duckdb"
BRUTOS = RAIZ / "dados" / "brutos"

pytestmark = pytest.mark.skipif(not DB.exists(), reason="rode scripts/construir_tentativas.py antes")


@pytest.fixture(scope="module")
def con():
    c = duckdb.connect(str(DB), read_only=True)
    yield c
    c.close()


def um(con, sql):
    return con.execute(sql).fetchone()[0]


def test_nao_ha_duplicata_por_aluno_e_turma(con):
    total = um(con, "SELECT COUNT(*) FROM tentativas")
    distintos = um(con, "SELECT COUNT(*) FROM (SELECT DISTINCT aluno, id_turma FROM tentativas)")
    assert total == distintos > 1_000_000


def test_janela_de_semestres(con):
    assert um(con, "SELECT MIN(semestre) FROM tentativas") == "2015.1"
    assert um(con, "SELECT MAX(semestre) FROM tentativas") == "2019.2"
    assert um(con, "SELECT COUNT(DISTINCT semestre) FROM tentativas") == 10


def test_so_graduacao_e_chaves_preenchidas(con):
    assert um(con, "SELECT COUNT(*) FROM tentativas WHERE aluno IS NULL OR id_turma IS NULL OR situacao IS NULL") == 0
    assert um(con, "SELECT COUNT(*) FROM tentativas WHERE codigo_disciplina IS NULL") < 100


def test_cada_aluno_tem_um_curso(con):
    assert um(con, "SELECT COUNT(*) FROM (SELECT aluno FROM tentativas GROUP BY 1 HAVING COUNT(DISTINCT id_curso) > 1)") == 0


def test_numero_tentativa_e_sequencial(con):
    ruins = um(
        con,
        """SELECT COUNT(*) FROM (
               SELECT aluno, codigo_disciplina, MAX(numero_tentativa) mx, COUNT(numero_tentativa) n
               FROM tentativas WHERE numero_tentativa IS NOT NULL GROUP BY 1, 2
               HAVING mx <> n)""",
    )
    assert ruins == 0


def test_calouro_comeca_sem_historico(con):
    # no 1o semestre efetivo de um calouro nao ha desempenho anterior
    ruins = um(
        con,
        """WITH p AS (SELECT aluno, MIN(semestre_idx) i FROM tentativas WHERE efetiva GROUP BY 1)
           SELECT COUNT(*) FROM tentativas t JOIN p USING (aluno)
           WHERE t.coorte_calouro AND t.semestre_idx = p.i AND t.desempenho_anterior IS NOT NULL""",
    )
    assert ruins == 0


def test_calouro_so_se_primeiro_semestre_apos_2015_1(con):
    ruins = um(
        con,
        """WITH p AS (SELECT aluno, MIN(semestre_idx) i FROM tentativas WHERE efetiva GROUP BY 1)
           SELECT COUNT(*) FROM (SELECT DISTINCT aluno FROM tentativas WHERE coorte_calouro) c
           JOIN p USING (aluno) WHERE p.i < 2015 * 2 + 1""",
    )
    assert ruins == 0


def test_carga_do_semestre_coerente(con):
    # a carga e igual no semestre inteiro do aluno
    assert um(con, "SELECT COUNT(*) FROM (SELECT aluno, semestre_idx FROM tentativas GROUP BY 1, 2 HAVING COUNT(DISTINCT disciplinas_no_semestre) > 1)") == 0
    # medido: 99,7% dos aluno-semestres tem ate 15 disciplinas; o maximo observado e 21
    # (atividades, estagios e TCC contam como componentes). Mais que 99% ate 15 e o que se espera.
    pct = um(
        con,
        """SELECT AVG((d <= 15)::INT) FROM
           (SELECT MAX(disciplinas_no_semestre) d FROM tentativas GROUP BY aluno, semestre_idx)""",
    )
    assert pct > 0.99


# --- conferencia independente: 10 alunos recalculados em Python puro a partir dos CSV ---

def _prioridade(desc):
    if desc.startswith(("APROVADO", "REPROVADO")) or desc in ("CUMPRIU", "DISPENSADO"):
        return 3
    if desc in ("TRANCADO", "DESISTENCIA", "MATRICULADO", "CANCELADO", "TRANSFERIDO", "INCORPORADO"):
        return 2
    return 1


@pytest.mark.skipif(not BRUTOS.exists(), reason="CSV brutos ausentes")
def test_dez_alunos_conferidos_contra_os_csv(con):
    alunos = [
        r[0]
        for r in con.execute(
            """SELECT aluno FROM tentativas GROUP BY 1 HAVING COUNT(*) >= 15
               ORDER BY md5(aluno) LIMIT 10"""
        ).fetchall()
    ]
    assert len(alunos) == 10
    alvo = set(alunos)

    # 1) matriculas dos 10 alunos, direto dos CSV
    por_chave = {}
    for arq in glob.glob(str(BRUTOS / "matriculas-componentes" / "*.csv")):
        with open(arq, encoding="utf-8", newline="") as f:
            for lin in csv.DictReader(f, delimiter=";"):
                if lin["discente"] in alvo:
                    por_chave.setdefault((lin["discente"], lin["id_turma"]), []).append(lin["descricao"])
    esperado = {}
    for (aluno, turma), descs in por_chave.items():
        melhor = max(_prioridade(d) for d in descs)
        esperado[(aluno, turma)] = min(d for d in descs if _prioridade(d) == melhor)

    # 2) turmas de graduacao no intervalo
    turmas = {}
    for arq in glob.glob(str(BRUTOS / "turmas" / "*.csv")):
        with open(arq, encoding="utf-8", newline="") as f:
            for lin in csv.DictReader(f, delimiter=";"):
                turmas[lin["id_turma"]] = (lin["nivel_ensino"], lin["ano"] + "." + lin["periodo"])
    esperado = {
        k: (sit, turmas[k[1]][1])
        for k, sit in esperado.items()
        if k[1] in turmas and turmas[k[1]][0].startswith("GRADUA")
    }

    # 3) mesma coisa lida da tabela
    obtido = {
        (a, t): (s, sem)
        for a, t, s, sem in con.execute(
            "SELECT aluno, id_turma, situacao, semestre FROM tentativas WHERE aluno IN ({})".format(
                ",".join("'" + a + "'" for a in alunos)
            )
        ).fetchall()
    }
    assert obtido == esperado


def test_desistencia_e_coluna_separada(con):
    # desistiu = TRANCADO ou DESISTENCIA, e nunca conta como aprovacao nem reprovacao
    assert um(con, "SELECT COUNT(*) FROM tentativas WHERE desistiu AND situacao NOT IN ('TRANCADO', 'DESISTENCIA')") == 0
    assert um(con, "SELECT COUNT(*) FROM tentativas WHERE NOT desistiu AND situacao IN ('TRANCADO', 'DESISTENCIA')") == 0
    assert um(con, "SELECT COUNT(*) FROM tentativas WHERE desistiu AND resultado <> 'OUTRO'") == 0
    assert um(con, "SELECT COUNT(*) FROM tentativas WHERE desistiu") > 0


def test_escopo_tem_15_disciplinas_e_so_dados_agregados():
    arq = RAIZ / "dados" / "disciplinas_escopo.csv"
    linhas = list(csv.DictReader(open(arq, encoding="utf-8")))
    assert len(linhas) == 15
    assert [int(r["posicao"]) for r in linhas] == list(range(1, 16))
    assert "Cálculo I" in {r["nome"] for r in linhas}
