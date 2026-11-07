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
    gm_arq = RAIZ / "resultados" / "gradment_vs_ufrn_resumo.json"
    gm = json.loads(gm_arq.read_text(encoding="utf-8")) if gm_arq.exists() else None
    bloco_gm = ""
    if gm and gm.get("definicao") == "reprovacao_REP_REPMF_entre_concluidas":
        import csv
        linhas_gm = list(csv.DictReader(open(RAIZ / "resultados" / "gradment_vs_ufrn.csv", encoding="utf-8")))
        taxas = [float(r["gradment_taxa_pct"]) for r in linhas_gm if float(r["gradment_taxa_pct"]) > 0]
        n_zero = sum(float(r["gradment_taxa_pct"]) == 0 for r in linhas_gm)
        bloco_gm = f"""
## Conferência com alunos reais do GradMent

Rodei consultas somente de leitura, com agregados, no banco de produção do GradMent e comparei a ordem de dificuldade. Nas {gm["n_pares"]} disciplinas da UFRN que têm equivalente no CEFET-MG (pelo mapeamento que revisei) e pelo menos {gm["min_tentativas_publicadas"]} matrículas concluídas no GradMent, a correlação de Spearman entre a reprovação da UFRN e a do GradMent é **ρ = {f(gm["spearman_rho"], 2)}** (p = {f(gm["spearman_p"], 4)}). No GradMent, "reprovou" é a situação REP ou REPMF entre as disciplinas concluídas.

Boa parte dessa correlação vem do contraste entre exatas e formação geral: {n_zero} das {gm["n_pares"]} disciplinas (as equivalentes de Ciência, Tecnologia e Sociedade, de Metodologia e de Inglês) não tiveram nenhuma reprovação no GradMent. Só entre as {gm["spearman_so_com_reprovacao_n"]} disciplinas com alguma reprovação a correlação cai para **ρ = {f(gm["spearman_so_com_reprovacao_rho"], 2)}** (p = {f(gm["spearman_so_com_reprovacao_p"], 2)}), o que não é distinguível de acaso com tão poucos alunos. Ou seja: a direção geral bate, a ordem fina entre as disciplinas de exatas não se confirma. As taxas do GradMent ({f(min(taxas), 0)}% a {f(max(taxas), 0)}% nessas {gm["spearman_so_com_reprovacao_n"]}) são menores que as da UFRN, e isso confere direção, não taxa. A tabela está em [`resultados/gradment_vs_ufrn.csv`](resultados/gradment_vs_ufrn.csv).

Ressalvas: é uma amostra pequena de alunos reais, de quem enviou o histórico; e Pré-Cálculo e Cálculo I compartilham o mesmo equivalente.
"""
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

## A tela

O site [termometro-psi.vercel.app](https://termometro-psi.vercel.app) mostra estes resultados: as 15 disciplinas com reprovação e desistência e seus intervalos, a curva da carga do semestre, as combinações de disciplinas e os achados. Foi feito com vibe coding no v0, com o mesmo visual do front do GradMent, e o código está em [termometro-semestre-app](https://github.com/catarina051/termometro-semestre-app). O prompt está em [`prompts/v0/01-prompt-enviado.md`](prompts/v0/01-prompt-enviado.md): ele manda buscar os dados por URL deste repositório, proíbe número inventado e frase de recomendação, e define o visual. Os números da tela foram conferidos, por script, contra o `dados/termometro.json`: a reprovação e a desistência das 15 disciplinas batem. O botão "Explicar" chama uma rota que pede ao Gemini um texto simples e descarta qualquer resposta com número que não estava nos dados.

## Como conferi o trabalho

- Separei o que **decidi** (população, cursos, disciplinas, método, suporte mínimo, correção para múltiplas comparações, o mapeamento para o CEFET) do que a IA calculou. O registro, com as opções que me foram apresentadas, está no [DIARIO.md](DIARIO.md).
- Pedi a crítica a dois revisores independentes: um modelo da OpenAI e um agente de outro modelo, sem contexto. Eles apontaram erros no trabalho (por exemplo, um indicador de "direção mantida" que na verdade testava significância). O que cada crítica mudou está no diário.
- Validei por divisão de alunos, repetida {rev["divisoes"]} vezes: escolho os pares numa metade e estimo na outra. O efeito dos finalistas cai de {f(rev["efeito_descoberta_pp"])} para {f(rev["efeito_validacao_pp"])} pontos percentuais, o que mede quanto a escolha pelo maior efeito infla o resultado.
- Os testes automáticos conferem, entre outras coisas, que o suporte mínimo foi respeitado, que nenhum dado de aluno entra nos resultados e que 10 alunos recalculados por um código independente, direto dos arquivos brutos, batem com a tabela.
{bloco_gm}
## O que eu não afirmo

> {j['avisos']['etico']}

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
