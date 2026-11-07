"""Conta quantas sugestoes de mapeamento UFRN -> CEFET a Catarina aceitou sem correcao.

Preencha a coluna `decisao_catarina` de dados/mapeamento_ufrn_cefet.csv com uma de:
  aceito     - concordo com a sugestao como esta
  corrigido  - concordo em parte; escreva a correcao em `correcao_catarina`
  recusado   - nao ha equivalencia; escreva o motivo em `correcao_catarina`
Uso: python -I scripts/contar_revisao.py
"""
import sys
from pathlib import Path

import pandas as pd

ARQ = Path(__file__).resolve().parent.parent / "dados" / "mapeamento_ufrn_cefet.csv"
VALIDAS = {"aceito", "corrigido", "recusado"}


def contar(df):
    d = df["decisao_catarina"].fillna("").str.strip().str.lower()
    invalidas = sorted(set(d) - VALIDAS - {""})
    if invalidas:
        raise ValueError(f"decisao_catarina com valor invalido: {invalidas}")
    return {
        "total": len(df),
        "aceito": int((d == "aceito").sum()),
        "corrigido": int((d == "corrigido").sum()),
        "recusado": int((d == "recusado").sum()),
        "pendente": int((d == "").sum()),
    }


def main():
    r = contar(pd.read_csv(ARQ, dtype=str))
    print(r)
    if r["pendente"] == 0:
        print(f"Aceitas sem correção: {r['aceito']} de {r['total']}")


if __name__ == "__main__":
    sys.exit(main())
