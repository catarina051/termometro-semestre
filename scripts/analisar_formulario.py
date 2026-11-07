"""Resume as respostas do formulario de colegas (CSV exportado). So contagens.

Uso: python -I scripts/analisar_formulario.py respostas.csv
Saida: resultados/formulario_colegas.csv (nao grava texto livre)
"""
import sys
from pathlib import Path

import pandas as pd

PERGUNTAS = {
    "sabia": "Já sabia quais disciplinas do ciclo básico reprovam mais?",
    "mudaria": "O Termômetro mudaria algo na forma como você monta sua grade?",
    "entendeu_taxa": "Entendi o que a taxa de reprovação mostra",
    "entendeu_nao_recomenda": "Entendi por que o Termômetro não recomenda combinações de disciplinas",
    "usaria": "Você usaria isso dentro de um simulador de grade?",
}
MIN_RESPOSTAS = 5


def resumir(df):
    n = len(df)
    linhas = []
    for chave, titulo in PERGUNTAS.items():
        if titulo not in df.columns:
            raise KeyError(f"coluna ausente no CSV: {titulo!r}")
        cont = df[titulo].dropna().astype(str).str.strip().value_counts()
        for resposta, qtd in cont.items():
            linhas.append({"pergunta": chave, "resposta": resposta, "n": int(qtd), "pct": round(100 * qtd / n, 1)})
    return pd.DataFrame(linhas), n


def main(caminho):
    df = pd.read_csv(caminho)
    out, n = resumir(df)
    destino = Path(__file__).resolve().parent.parent / "resultados" / "formulario_colegas.csv"
    out.to_csv(destino, index=False)
    print(f"{n} respostas" + ("" if n >= MIN_RESPOSTAS else f" (menos de {MIN_RESPOSTAS}: chamar de 'teste informal')"))
    print(out.to_string(index=False))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
