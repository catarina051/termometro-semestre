"""Testes dos resultados agregados em resultados/ (versionados, sem dados de aluno)."""
from pathlib import Path

import pandas as pd
import pytest

R = Path(__file__).resolve().parent.parent / "resultados"
pytestmark = pytest.mark.skipif(not (R / "metodo.json").exists(), reason="rode scripts/analise.py")


def ler(nome):
    return pd.read_csv(R / nome)


@pytest.mark.parametrize("arq", ["pares_com_historico.csv", "pares_primeiro_semestre.csv"])
def test_pares_respeitam_suporte_e_correcao(arq):
    p = ler(arq)
    assert (p["n_com_par"] >= 100).all()                     # suporte minimo decidido
    assert (p["q_bh"] >= p["p_cmh"] - 1e-9).all()            # BH nunca diminui o p-valor
    assert (p["passa_bh"] == (p["q_bh"] < 0.05)).all()
    assert (p["ic_inf_pp"] <= p["dif_risco_pp"] + 1e-6).all() and (p["dif_risco_pp"] <= p["ic_sup_pp"] + 1e-6).all()
    assert ((p["disciplina"] != p["dado_par"])).all()


def test_taxas_por_disciplina_dentro_do_ic():
    d = ler("disciplinas.csv")
    assert len(d) == 15
    assert ((d["reprov_ic_inf"] <= d["reprovacao_pct"]) & (d["reprovacao_pct"] <= d["reprov_ic_sup"])).all()
    assert ((d["desist_ic_inf"] <= d["desistencia_pct"]) & (d["desistencia_pct"] <= d["desist_ic_sup"])).all()


def test_nenhum_dado_de_aluno_nos_resultados():
    proibidas = {"aluno", "matricula", "discente", "nome_discente"}
    for arq in R.glob("*.csv"):
        assert not (set(pd.read_csv(arq, nrows=1).columns) & proibidas), arq.name


def test_regressao_so_para_candidatos_que_passaram_na_correcao():
    reg, ph = ler("pares_regressao.csv"), ler("pares_com_historico.csv")
    ok = ph[ph["passa_bh"] & (ph["dif_risco_pp"] > 0)][["disciplina", "dado_par"]]
    juntos = reg.merge(ok, on=["disciplina", "dado_par"])
    assert len(juntos) == len(reg) > 0
    assert (reg["q_bh_regressao"] >= reg["p_regressao"] - 1e-9).all()
    assert (reg["mantem_apos_bh"] == ((reg["odds_ratio_regressao"] > 1) & (reg["q_bh_regressao"] < 0.05))).all()


def test_curva_cobre_todas_as_faixas_de_carga():
    c = ler("curva_carga.csv")
    assert set(c["desfecho"]) == {"reprovacao", "desistencia", "nao_aprovacao"}
    assert c.groupby("desfecho")["disciplinas_no_semestre"].nunique().eq(9).all()


def test_checagens_da_auditoria():
    chk = ler("checagens_auditoria.csv")
    assert len(chk) == 12
    # nos candidatos de risco mais fortes, quase todo "cursou B junto" e B repetido (atraso no fluxo)
    assert (chk["pct_B_repeticao_entre_expostos"] > 90).sum() >= 5
    sob = ler("sobreviventes_auditoria.csv")
    assert len(sob) >= 1
    assert (sob["n_com_par"] >= 100).all() and (sob["n_sem_par"] >= 100).all()
    assert (sob["ic_cluster_inf"] > 0).all()  # a regra de entrada exige IC por aluno acima de zero


def test_validacao_por_divisao_de_alunos():
    res = ler("validacao_resumo.csv").set_index("procedimento")
    assert set(res.index) == {"original", "revisado"}
    assert (res["divisoes"] == 100).all()
    # a escolha pelo maior efeito infla: descoberta > validacao nos dois procedimentos
    assert (res["inflacao_media_pp"] > 0).all()
    div = ler("validacao_divisoes.csv")
    assert (div["val_n_com_par"] > 0).all() and (div["val_n_sem_par"] > 0).all()
    assert div.groupby(["divisao", "procedimento"]).size().max() <= 4  # ate 4 finalistas


def test_achados_gerados_dos_arquivos():
    txt = (R.parent / "achados" / "ACHADOS.md").read_text(encoding="utf-8")
    assert txt.count("## Achado ") == 4
    for proibido in ("[PREENCHER]", "[A MEDIR]", "nan", "None"):
        assert proibido not in txt
    # nenhuma frase de recomendacao ou causalidade solta
    assert "evite" not in txt.lower() and "aumenta o risco" not in txt.lower()
