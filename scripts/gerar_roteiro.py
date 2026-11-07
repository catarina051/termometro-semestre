"""Gera video/roteiro.md (video de 2 min) a partir de dados/termometro.json. Numeros vem do arquivo.

O roteiro e um rascunho para a Catarina falar com as proprias palavras.
Uso: python -I scripts/gerar_roteiro.py
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def f(x, n=1):
    return f"{x:.{n}f}".replace(".", ",")


def main():
    j = json.loads((RAIZ / "dados" / "termometro.json").read_text(encoding="utf-8"))
    cl = next(d for d in j["disciplinas"] if d["codigo"] == "ECT2103")
    n = f"{j['populacao']['linhas_analisadas']:,}".replace(",", ".")
    cand = j["pares"]["candidatos"]
    n_forte = sum(c["pct_repetindo_a_outra"] > 90 for c in cand)
    lei = next(c for c in cand if c["disciplina"] == "ECT2205" and c["cursada_junto_com"] == "ECT2106")
    s = next(x for x in j["pares"]["sobreviventes"] if x["cursada_junto_com"] == "ECT2205")
    rev = j["validacao"]["revisado"]
    na = {p["disciplinas_no_semestre"]: p for p in j["curva_carga"]["nao_aprovacao"]}

    texto = f"""# Roteiro do vídeo (2 minutos)

Rascunho para você falar com as suas palavras. Meta: 2 minutos, em torno de 300 palavras faladas.
Grave a tela do app só no trecho 3 (1:25 a 1:45); no resto, câmera ou slides simples.

## 0:00 a 0:15 · O gancho
"Quando eu monto a grade, eu decido no escuro. Em Cálculo I, {f(cl['reprovacao_pct'])}% das tentativas na UFRN terminaram em reprovação. Mas será que juntar Cálculo com outra disciplina piora isso? Fui descobrir com dados."

## 0:15 a 0:45 · Como eu fiz
"Usei dados abertos da UFRN: {n} matrículas de 2015 a 2019. Eu defini o escopo e o método; uma IA calculou e duas outras me criticaram. A regra: o modelo de linguagem só explica número pronto, nunca calcula."

## 0:45 a 1:25 · O que eu achei
"Primeiro, o que parecia a grande descoberta: {n_forte} das {len(cand)} combinações 'perigosas' eram, na verdade, aluno atrasado. Na combinação de maior efeito, {f(lei['pct_repetindo_a_outra'], 0)}% dos alunos estavam repetindo uma das duas disciplinas.
Depois da limpeza, sobrou só Probabilidade e Estatística, com cerca de {f(s['dif_pp'], 0)} pontos percentuais a mais de reprovação quando cursada junto com Leitura e Escrita II. Em alunos que não usei para escolher o par, o efeito médio caiu de {f(rev['efeito_descoberta_pp'])} para {f(rev['efeito_validacao_pp'])} pontos. Por isso é hipótese, não recomendação.
E a carga do semestre faz um U: {f(na['1']['taxa_pct'], 0)}% de reprovação ou desistência com 1 disciplina, {f(na['7']['taxa_pct'], 0)}% com 7 e {f(na['9+']['taxa_pct'], 0)}% com 9 ou mais."

## 1:25 a 1:45 · A tela (gravar o app)
"Na tela, cada disciplina mostra reprovação e desistência com intervalo de confiança. O botão de explicar pede a uma IA um texto simples, e o servidor descarta qualquer resposta com número que não estava nos dados."

## 1:45 a 2:00 · O que aprendi e o próximo passo
"O resultado mais empolgante era o mais enganoso, e quem me mostrou isso foi a crítica. O próximo passo é levar essas taxas para o simulador de grade do GradMent."

## Antes de gravar
- Confira cada número falado no `dados/termometro.json`.
- Se mudar a ordem ou cortar trechos, mantenha: o que decidi, o que a IA fez, o que a crítica mudou.
"""
    (RAIZ / "video").mkdir(exist_ok=True)
    (RAIZ / "video" / "roteiro.md").write_text(texto, encoding="utf-8")
    import re
    falado = " ".join(re.findall(r'^"(.*?)"$', texto, re.S | re.M))
    palavras = len(falado.split())
    print(f"~{palavras} palavras faladas (~{palavras / 150:.1f} min a 150 palavras por minuto)")


if __name__ == "__main__":
    sys.exit(main())
