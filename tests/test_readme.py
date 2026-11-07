import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TXT = (RAIZ / "README.md").read_text(encoding="utf-8")


def test_sem_texto_provisorio():
    for proibido in ("[PREENCHER]", "[A MEDIR]", "[a gravar]", "TODO", "nan"):
        assert proibido not in TXT


def test_imagens_e_links_locais_existem():
    for alvo in re.findall(r"\]\(([^)#]+)\)", TXT):
        if alvo.startswith("http"):
            continue
        assert (RAIZ / alvo).exists(), alvo


def test_voz_e_aviso_sem_ia_em_primeira_pessoa():
    assert "eu, Claude" not in TXT and "Claude" not in TXT
    assert "não afirmo" in TXT.lower()
    assert "evite" not in TXT.lower()


def test_numeros_chave_vem_do_json():
    import json
    j = json.loads((RAIZ / "dados" / "termometro.json").read_text(encoding="utf-8"))
    assert f"{j['populacao']['linhas_analisadas']:,}".replace(",", ".") in TXT
    cl = next(d for d in j["disciplinas"] if d["codigo"] == "ECT2103")
    assert f"{cl['reprovacao_pct']:.1f}".replace(".", ",") in TXT
