import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import analisar_formulario as af  # noqa: E402


def _df(n=6):
    d = {t: ["Sim"] * n for t in af.PERGUNTAS.values()}
    d[af.PERGUNTAS["mudaria"]] = ["4"] * (n - 1) + ["2"]
    d["O que faltou?"] = ["texto livre que não deve sair"] * n
    return pd.DataFrame(d)


def test_resume_so_contagens_sem_texto_livre():
    out, n = af.resumir(_df())
    assert n == 6
    assert set(out["pergunta"]) == set(af.PERGUNTAS)
    assert "texto livre" not in out.to_string()
    m = out[(out["pergunta"] == "mudaria") & (out["resposta"] == "4")].iloc[0]
    assert m["n"] == 5 and m["pct"] == pytest.approx(83.3, abs=0.1)


def test_coluna_ausente_gera_erro_claro():
    with pytest.raises(KeyError):
        af.resumir(pd.DataFrame({"outra": [1]}))
