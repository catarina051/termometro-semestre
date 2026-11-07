"""Gera o prompt do "auditor cetico" (para colar no Gemini) a partir de resultados/*.csv.

So numeros agregados entram no texto: nenhum dado de aluno. Saida: auditoria/prompt_auditor_gemini.md
"""
import json
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
R = RAIZ / "resultados"


def md(df, cols, nomes=None, casas=1):
    d = df[cols].copy()
    for c in d.columns:
        if d[c].dtype.kind == "f":
            d[c] = d[c].round(casas)
    d.columns = nomes or cols
    return d.to_markdown(index=False)


def main():
    meta = json.loads((R / "metodo.json").read_text(encoding="utf-8"))
    disc = pd.read_csv(R / "disciplinas.csv")
    ph = pd.read_csv(R / "pares_com_historico.csv")
    pp = pd.read_csv(R / "pares_primeiro_semestre.csv")
    reg = pd.read_csv(R / "pares_regressao.csv")
    curva = pd.read_csv(R / "curva_carga.csv")

    ph["par"] = ph["disciplina"] + " dado " + ph["dado_par"]
    pp["par"] = pp["disciplina"] + " dado " + pp["dado_par"]
    reg["par"] = reg["disciplina"] + " dado " + reg["dado_par"]
    pos = int((ph.passa_bh & (ph.dif_risco_pp > 0)).sum())
    neg = int((ph.passa_bh & (ph.dif_risco_pp < 0)).sum())
    top_ph = ph[ph.passa_bh].sort_values("dif_risco_pp", key=abs, ascending=False).head(10)
    top_pp = pp[pp.passa_bh].sort_values("dif_risco_pp", key=abs, ascending=False).head(8)

    texto = f"""# Prompt para o auditor cético (colar no Gemini)

Você é um estatístico cético e rigoroso, revisor de um trabalho de uma estudante de graduação.
Seu papel é procurar falhas, não elogiar. Responda em português, de forma direta.

## O que foi feito
Dados abertos da UFRN (matrículas em componentes, turmas, componentes curriculares), semestres
2015.1 a 2019.2, graduação presencial. Escopo: cursos de Ciências e Tecnologia (BC&T), Engenharias
e Computação, e as 15 disciplinas mais cursadas nesse escopo (nove de exatas e programação; seis de
formação geral: leitura e escrita, inglês, metodologia, gestão, ciência e sociedade). Cada linha é uma matrícula
(aluno, turma) com situação final. Reprovação = situação que começa com "REPROVADO", entre as
matrículas que terminaram em aprovação ou reprovação. Desistência = TRANCADO ou DESISTENCIA.

Limitação dos dados: o identificador de aluno nas matrículas é um hash que não liga à tabela de
discentes, então não existe data de ingresso. "Calouro" = aluno cujo primeiro semestre com
matrícula efetiva é 2015.2 ou depois (visto entrando). Quem já estava no curso em 2015.1 tem
histórico cortado e fica fora das análises que dependem de histórico.

Populações: taxas por disciplina e curva por carga usam todos os alunos. Pares de risco usam só
calouros.

## Método dos pares de risco
"A dado B": entre calouros que cursaram A (matrícula concluída), compara a reprovação de quem
cursou B no mesmo semestre contra quem cursou A sem B. Estratificado por tercil de desempenho
anterior (média das notas finais dos semestres anteriores; cortes: {meta["cortes_desempenho_anterior_tercis"][0]:.2f} e {meta["cortes_desempenho_anterior_tercis"][1]:.2f}).
Efeito = diferença de risco de Mantel-Haenszel em pontos percentuais; IC 95% por bootstrap
paramétrico dentro de cada faixa ({meta["bootstrap"]} réplicas); p-valor do teste de
Cochran-Mantel-Haenszel. Suporte mínimo: {meta["suporte_minimo"]} alunos com o par. Correção:
Benjamini-Hochberg a {int(meta["alfa_bh"] * 100)}%. Calouros no primeiro semestre não têm desempenho anterior e foram
analisados à parte, estratificando por grupo de curso (BC&T / Engenharias / Computação).
Verificação: regressão logística nos candidatos de risco, com desempenho anterior, número da
tentativa (1, 2, 3+), carga do semestre, grupo de curso e semestre do calendário como controles;
erro padrão agrupado por aluno.

Contagens: {meta["comparacoes_testadas_com_historico"]} comparações com histórico ({meta["passam_bh_com_historico"]} passam na correção: {pos} com
risco maior com o par, {neg} com risco menor); {meta["comparacoes_testadas_primeiro_semestre"]} comparações no primeiro semestre
({meta["passam_bh_primeiro_semestre"]} passam).

## Resultados
### Reprovação e desistência por disciplina (todos os alunos, %)
{md(disc, ["codigo", "disciplina", "n_concluidas", "reprovacao_pct", "reprov_ic_inf", "reprov_ic_sup", "desistencia_pct"], ["código", "disciplina", "n", "reprov %", "IC inf", "IC sup", "desist %"])}

### Pares com histórico: 10 maiores efeitos entre os que passam na correção
{md(top_ph, ["par", "n_com_par", "reprov_com_par_pct", "reprov_sem_par_pct", "dif_risco_pp", "ic_inf_pp", "ic_sup_pp", "q_bh"], ["par", "n com par", "reprov com %", "reprov sem %", "dif pp", "IC inf", "IC sup", "q BH"], 3)}

### Primeiro semestre (sem histórico): 8 maiores efeitos entre os que passam
{md(top_pp, ["par", "n_com_par", "reprov_com_par_pct", "reprov_sem_par_pct", "dif_risco_pp", "ic_inf_pp", "ic_sup_pp", "q_bh"], ["par", "n com par", "reprov com %", "reprov sem %", "dif pp", "IC inf", "IC sup", "q BH"], 3)}

### Verificação por regressão (candidatos de risco)
{md(reg, ["par", "n_com_par", "dif_risco_simples_pp", "odds_ratio_regressao", "or_ic_inf", "or_ic_sup", "p_regressao", "direcao_mantida"], ["par", "n com par", "dif simples pp", "OR regressão", "IC inf", "IC sup", "p", "direção mantida"], 3)}

### Reprovação e desistência por número de disciplinas no semestre (todos os alunos)
Colunas "padronizada" ajustam pela mistura de disciplinas.
{md(curva, ["desfecho", "disciplinas_no_semestre", "n", "taxa_pct", "ic_inf", "ic_sup", "taxa_padronizada_pct"], ["desfecho", "disciplinas", "n", "taxa %", "IC inf", "IC sup", "padronizada %"])}

## O que eu quero de você
1. Os 5 problemas mais graves de validade (confundimento, seleção, viés de sobrevivência, causalidade
   reversa, definição das variáveis, unidade de análise, dependência entre linhas), em ordem de gravidade.
2. Para cada um: por que invalida ou enfraquece qual afirmação, e que checagem simples eu faria com
   os dados que tenho (matrículas, notas, faltas, semestre, curso, tentativa).
3. Quais conclusões eu poderia sustentar com honestidade e quais devo cortar ou reformular.
4. Qualquer erro no uso de intervalo de confiança, correção para múltiplas comparações ou testes.
Não reescreva o trabalho. Critique.
"""
    saida = RAIZ / "auditoria"
    saida.mkdir(exist_ok=True)
    (saida / "prompt_auditor_gemini.md").write_text(texto, encoding="utf-8")
    print(f"{len(texto)} caracteres")


if __name__ == "__main__":
    sys.exit(main())
