"""Gera README.md a partir de dados/termometro.json (todo numero vem do arquivo).

O README esta na voz da Catarina. O papel de cada IA em cada etapa fica no DIARIO.md.
Uso: python -I scripts/gerar_readme.py
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def f(x, n=1):
    return f"{x:.{n}f}".replace(".", ",")


def cap(t):
    return t[0].upper() + t[1:] if t else t


def milhar(n):
    return f"{int(n):,}".replace(",", ".")


def main():
    j = json.loads((RAIZ / "dados" / "termometro.json").read_text(encoding="utf-8"))
    n_linhas = milhar(j["populacao"]["linhas_analisadas"])
    cand = j["pares"]["candidatos"]
    n_forte = sum(c["pct_repetindo_a_outra"] > 90 for c in cand)
    rev = j["validacao"]["revisado"]
    achados = "\n\n".join(
        f"### {a['id']}. {a['titulo']}\n\n**Número.** {cap(a['numero'])}\n\n**E daí?** {cap(a['e_dai'])}\n\n**Limitação.** {cap(a['limitacao'])}"
        for a in j["achados"]
    )
    graf = {
        1: "![Reprovação e desistência por disciplina](docs/img/reprovacao_por_disciplina.png)",
        2: "![Pares de risco que são repetência](docs/img/pares_sao_repetencia.png)",
        4: "![Curva da carga do semestre](docs/img/curva_carga.png)",
    }
    for i, g in graf.items():
        achados = achados.replace(f"### {i}. ", f"### {i}. ", 1)
        marcador = f"### {i}. "
        pos = achados.index(marcador)
        fim = achados.find("\n\n### ", pos + 1)
        fim = len(achados) if fim == -1 else fim
        achados = achados[:fim] + f"\n\n{g}" + achados[fim:]

    texto = f"""# Termômetro do Semestre

**Resultado em uma linha:** analisei {n_linhas} matrículas de graduação da UFRN (2015 a 2019) e vi que {n_forte} das {len(cand)} combinações de disciplinas que pareciam perigosas eram, na verdade, alunos atrasados repetindo uma delas; o sinal que sobrevive às checagens é pequeno e vem de uma única disciplina, Probabilidade e Estatística.

## O problema

Montar a grade do semestre é decidir no escuro: ninguém mostra ao aluno quais disciplinas do ciclo básico mais reprovam, nem se juntar duas delas muda alguma coisa. Usei os dados abertos da UFRN para olhar isso nas engenharias, na computação e no bacharelado de Ciências e Tecnologia, com as 15 disciplinas mais cursadas.

Uma regra que mantive o tempo todo: o modelo de linguagem só **explica** números já calculados; ele nunca calcula.

## Achados

Todo número abaixo vem de `resultados/*.csv`, gerados pelos scripts da pasta `scripts/`. As taxas são **por tentativa de matrícula**, não por aluno: quem repete uma disciplina conta de novo.

{achados}

## Como conferi o trabalho

- Separei o que **decidi** (população, cursos, disciplinas, método, suporte mínimo, correção para múltiplas comparações, o mapeamento para o CEFET) do que a IA calculou. O registro, com as opções que me foram apresentadas, está no [DIARIO.md](DIARIO.md).
- Pedi a crítica a dois revisores independentes: um modelo da OpenAI e um agente de outro modelo, sem contexto. Eles apontaram erros no trabalho (por exemplo, um indicador de "direção mantida" que na verdade testava significância). O que cada crítica mudou está no diário.
- Validei por divisão de alunos, repetida {rev["divisoes"]} vezes: escolho os pares numa metade e estimo na outra. O efeito dos finalistas cai de {f(rev["efeito_descoberta_pp"])} para {f(rev["efeito_validacao_pp"])} pontos percentuais, o que mede quanto a escolha pelo maior efeito infla o resultado.
- Os testes automáticos conferem, entre outras coisas, que o suporte mínimo foi respeitado, que nenhum dado de aluno entra nos resultados e que 10 alunos recalculados por um código independente, direto dos arquivos brutos, batem com a tabela.

## O que eu não afirmo

- Não afirmo que cursar uma disciplina cause reprovação em outra, nem recomendo combinações de matrícula.
- Não afirmo que a taxa vale para outra universidade. O mapeamento para as disciplinas do CEFET-MG, que revisei linha a linha, serve para a próxima etapa, não prova que os resultados se repetem lá.
- A identificação de calouro é aproximada: os dados abertos não ligam a matrícula à data de ingresso.

## Como reproduzir

```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
python -I scripts/baixar_dados.py          # baixa os dados abertos da UFRN (cerca de 800 MB)
python -I scripts/construir_tentativas.py  # tabela de tentativas em DuckDB
python -I scripts/definir_escopo.py
python -I scripts/analise.py
python -I scripts/checagens_auditoria.py
python -I scripts/validacao.py
python -I scripts/gerar_achados.py
python -I scripts/exportar_json.py
pytest -q tests
```

## Estrutura

- `dados/`: manifesto do download, escopo, mapeamento UFRN → CEFET e o `termometro.json` que alimenta a tela.
- `scripts/`: coleta, pipeline, análise, validação e exportação.
- `resultados/`: tabelas agregadas (sem dados de alunos).
- `achados/`: o texto dos achados, gerado dos resultados.
- `auditoria/`: o prompt enviado ao revisor cético.
- `api-explicar/`: rota que pede ao Gemini uma explicação em linguagem simples e descarta qualquer resposta com número que não estava nos dados.
- `prompts/v0/`: os prompts usados no v0 para a tela.

## Próximo passo

Integrar ao simulador de grade do GradMent, mostrando junto de cada disciplina a taxa de reprovação, a de desistência e o equivalente no CEFET-MG.
"""
    (RAIZ / "README.md").write_text(texto, encoding="utf-8")
    print(f"{len(texto)} caracteres")


if __name__ == "__main__":
    sys.exit(main())
