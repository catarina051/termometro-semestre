"""Testes do dados/termometro.json (o que a tela e o LLM recebem)."""
import json
import re
from pathlib import Path

import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parent.parent
ARQ = RAIZ / "dados" / "termometro.json"
pytestmark = pytest.mark.skipif(not ARQ.exists(), reason="rode scripts/exportar_json.py")


@pytest.fixture(scope="module")
def j():
    return json.loads(ARQ.read_text(encoding="utf-8"))


def test_estrutura_e_quantidades(j):
    assert len(j["disciplinas"]) == 15
    assert len(j["achados"]) == 4
    assert set(j["curva_carga"]) == {"reprovacao", "desistencia", "nao_aprovacao"}
    assert all(a["numero"] and a["e_dai"] and a["limitacao"] for a in j["achados"])


def test_numeros_batem_com_os_csv(j):
    d = pd.read_csv(RAIZ / "resultados" / "disciplinas.csv").set_index("codigo")
    for x in j["disciplinas"]:
        assert x["reprovacao_pct"] == pytest.approx(d.loc[x["codigo"], "reprovacao_pct"], abs=0.006)
        assert x["tentativas_concluidas"] == d.loc[x["codigo"], "n_concluidas"]
        lo, hi = x["reprovacao_ic"]
        assert lo <= x["reprovacao_pct"] <= hi


def test_sem_dados_pessoais_nem_celulas_pequenas(j):
    txt = json.dumps(j, ensure_ascii=False).lower()
    for proibido in ("matricula", "discente", "\"aluno\"", "nome_discente", "@"):
        assert proibido not in txt
    assert all(c["alunos_com_par"] >= 100 for c in j["pares"]["candidatos"])
    assert all(s["alunos_com_par"] >= 100 and s["alunos_sem_par"] >= 100 for s in j["pares"]["sobreviventes"])
    assert all(p["n"] >= 100 for g in j["curva_carga"].values() for p in g)


def test_mapeamento_so_aparece_depois_da_revisao(j):
    for x in j["disciplinas"]:
        if x["mapeamento_status"] == "pendente":
            assert x["cefet"] is None
    assert isinstance(j["avisos"]["etico"], str) and "não classifica alunos" in j["avisos"]["etico"]


def test_achados_sem_linguagem_de_recomendacao(j):
    texto = " ".join(" ".join(filter(None, [a["titulo"], a["numero"], a["e_dai"], a["limitacao"]])) for a in j["achados"]).lower()
    assert not re.search(r"\b(evite|recomend[ae]mos|você deve)\b", texto)
