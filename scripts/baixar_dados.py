"""Baixa os dados abertos da UFRN usados no Termometro do Semestre.

Fonte: https://dados.ufrn.br (CKAN). Os links vem da API, nao sao digitados a mao.
Saida: dados/brutos/<conjunto>/ (ignorado pelo Git) e dados/manifesto_download.json
(versionado: URL, tamanho e SHA-256 de cada arquivo, para a coleta ser reproduzivel).

Uso: python -I scripts/baixar_dados.py
"""
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
BRUTOS = RAIZ / "dados" / "brutos"
API = "https://dados.ufrn.br/api/3/action/package_show?id="
ANOS = ("2015", "2016", "2017", "2018", "2019")

# conjunto -> funcao que decide se o recurso entra
CONJUNTOS = {
    "matriculas-componentes": lambda r: any(a in r["name"] for a in ANOS),
    "turmas": lambda r: any(a in r["name"] for a in ANOS),
    "discentes": lambda r: any(a in r["name"] for a in ANOS),
    "componentes-curriculares": lambda r: "Presenciais" in r["name"]
    or "Dicion" in r["name"],
}


def get_json(url):
    with urllib.request.urlopen(url, timeout=60) as resp:
        return json.load(resp)


def baixar(url, destino):
    h = hashlib.sha256()
    tamanho = 0
    with urllib.request.urlopen(url, timeout=120) as resp, open(destino, "wb") as f:
        while chunk := resp.read(1 << 20):
            f.write(chunk)
            h.update(chunk)
            tamanho += len(chunk)
    return tamanho, h.hexdigest()


def main():
    manifesto = []
    for conjunto, filtro in CONJUNTOS.items():
        pacote = get_json(API + conjunto)["result"]
        pasta = BRUTOS / conjunto
        pasta.mkdir(parents=True, exist_ok=True)
        for r in pacote["resources"]:
            if not filtro(r):
                continue
            nome = re.sub(r"[^\w.\-]", "_", r["url"].rsplit("/", 1)[-1])
            destino = pasta / nome
            print(f"[{conjunto}] {nome} ...", flush=True)
            tamanho, sha = baixar(r["url"], destino)
            manifesto.append(
                {
                    "conjunto": conjunto,
                    "recurso": r["name"],
                    "arquivo": f"{conjunto}/{nome}",
                    "url": r["url"],
                    "bytes": tamanho,
                    "sha256": sha,
                }
            )
            print(f"    {tamanho / 1e6:.1f} MB", flush=True)
    saida = RAIZ / "dados" / "manifesto_download.json"
    saida.write_text(json.dumps(manifesto, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(manifesto)} arquivos. Manifesto em {saida}")


if __name__ == "__main__":
    sys.exit(main())
