"""Gera o prompt do "auditor cetico" (para colar no ChatGPT) a partir de resultados/*.csv.

So numeros agregados entram no texto: nenhum dado de aluno. Saida: auditoria/prompt_auditor.md
"""
import json
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
R = RAIZ / "resultados"


CURTO = {
    "ECT2101": "Pré-Cálculo", "ECT2102": "Vetores e Geom. Analítica", "ECT2103": "Cálculo I",
    "ECT2104": "Química Geral", "ECT2105": "Leitura e Escrita I", "ECT2106": "Ciência, Tecnologia e Sociedade",
    "ECT2201": "Cálculo II", "ECT2203": "Lógica de Programação", "ECT2204": "Física Clássica I",
    "ECT2205": "Leitura e Escrita II", "ECT2206": "Gestão e Economia da CT&I",
    "ECT2207": "Probabilidade e Estatística", "ECT2302": "Metodologia Científica",
    "ECT2303": "Linguagem de Programação", "ECT2305": "Leitura em Inglês",
}


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

    def rot(df):
        return df["disciplina"].map(CURTO) + " dado " + df["dado_par"].map(CURTO)

    def fp(x):  # p-valor legivel: arredondar para 0 apaga a informacao
        return "<0,001" if x < 0.001 else f"{x:.3f}".replace(".", ",")

    ph["par"], pp["par"], reg["par"] = rot(ph), rot(pp), rot(reg)
    for df_, col in ((ph, "q_bh"), (pp, "q_bh"), (reg, "p_regressao"), (reg, "q_bh_regressao")):
        df_[col + "_t"] = df_[col].map(fp)
    disc["disciplina"] = disc["codigo"].map(CURTO)
    pos = int((ph.passa_bh & (ph.dif_risco_pp > 0)).sum())
    neg = int((ph.passa_bh & (ph.dif_risco_pp < 0)).sum())
    top_ph = ph[ph.passa_bh].sort_values("dif_risco_pp", key=abs, ascending=False).head(10)
    top_pp = pp[pp.passa_bh].sort_values("dif_risco_pp", key=abs, ascending=False).head(8)

    texto = f"""# Prompt para o auditor cético (colar no ChatGPT)

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

Detalhes que importam para a sua crítica:
- A unidade de análise é a linha aluno-semestre-disciplina. O mesmo aluno aparece em várias linhas
  (outros semestres, outras disciplinas, repetições da mesma disciplina). As taxas são por
  tentativa, não por aluno: quem repete uma disciplina conta de novo.
- "Cursou B junto" = tem matrícula efetiva em B no mesmo semestre, inclusive se depois trancou B.
- "Carga do semestre" = número de disciplinas distintas de graduação com matrícula efetiva do aluno
  no semestre (todas, não só as 15), contando as que ele depois trancou. É medida no fim do
  semestre, não na matrícula. A curva por carga considera só as linhas das 15 disciplinas.
- "Desempenho anterior" = média das notas finais de todas as disciplinas concluídas em semestres
  anteriores; só existe a partir do segundo semestre observado.
- Reprovação inclui REPROVADO, por faltas, por nota, por média e combinações. Trancamento e
  desistência não entram como reprovação nem como aprovação.
- Regra de publicação definida antes de ver os resultados: serão mostrados até 4 pares distintos,
  escolhidos entre os que passam na correção e mantêm a direção na regressão, ordenados pelo
  tamanho do efeito. Os 12 candidatos da regressão também foram escolhidos pelo tamanho do efeito.
- Os intervalos de confiança por bootstrap e o teste de Mantel-Haenszel tratam as linhas como
  independentes; só a regressão agrupa por aluno.

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
{md(disc, ["codigo", "disciplina", "n_concluidas", "reprovacao_pct", "reprov_ic_inf", "reprov_ic_sup", "desistencia_pct"], ["código", "disciplina", "tentativas concluídas", "reprov %", "IC inf", "IC sup", "desist %"])}

### Pares com histórico: 10 maiores efeitos entre os que passam na correção
Leitura: "A dado B" é a reprovação em A de quem cursou B no mesmo semestre (n com par) contra quem
cursou A sem B. A coluna q BH é o p-valor depois da correção.
{md(top_ph, ["par", "n_com_par", "reprov_com_par_pct", "reprov_sem_par_pct", "dif_risco_pp", "ic_inf_pp", "ic_sup_pp", "q_bh_t"], ["par", "n com par", "reprov com %", "reprov sem %", "dif pp", "IC inf", "IC sup", "q BH"], 1)}

### Primeiro semestre (sem histórico): 8 maiores efeitos entre os que passam
{md(top_pp, ["par", "n_com_par", "reprov_com_par_pct", "reprov_sem_par_pct", "dif_risco_pp", "ic_inf_pp", "ic_sup_pp", "q_bh_t"], ["par", "n com par", "reprov com %", "reprov sem %", "dif pp", "IC inf", "IC sup", "q BH"], 1)}

### Verificação por regressão (candidatos de risco)
{md(reg, ["par", "n_com_par", "dif_risco_mh_pp", "odds_ratio_regressao", "or_ic_inf", "or_ic_sup", "p_regressao_t", "q_bh_regressao_t", "mantem_apos_bh"], ["par", "n com par", "dif MH pp", "OR regressão", "IC inf", "IC sup", "p", "q BH", "mantém após BH"], 2)}

### Reprovação e desistência por número de disciplinas no semestre (todos os alunos)
"disciplinas" é a carga definida acima. A coluna padronizada ajusta pela mistura das 15 disciplinas.
{md(curva, ["desfecho", "disciplinas_no_semestre", "n", "taxa_pct", "ic_inf", "ic_sup", "taxa_padronizada_pct"], ["desfecho", "disciplinas", "n", "taxa %", "IC inf", "IC sup", "padronizada %"])}

## O que eu quero de você
1. Os 5 problemas mais graves de validade (confundimento, seleção, viés de sobrevivência, causalidade
   reversa, definição das variáveis, unidade de análise, dependência entre linhas), em ordem de gravidade.
2. Para cada um: por que invalida ou enfraquece qual afirmação, e que checagem simples eu faria com
   os dados que tenho (matrículas, notas, faltas, semestre, curso, tentativa).
3. Quais conclusões eu poderia sustentar com honestidade e quais devo cortar ou reformular.
4. Qualquer erro no uso de intervalo de confiança, correção para múltiplas comparações ou testes.
5. Dado que escolhi os candidatos e os pares publicados pelo tamanho do efeito, quanto isso infla
   o que vou mostrar (maldição do vencedor)? Há controle de regressão que eu errei, por exemplo
   controlar por uma variável que é consequência de cursar B junto?
6. Que linguagem posso usar na tela e no README: o que posso afirmar como associação e o que não
   posso afirmar como causa.
Não reescreva o trabalho. Critique.
"""
    saida = RAIZ / "auditoria"
    saida.mkdir(exist_ok=True)
    (saida / "prompt_auditor.md").write_text(texto, encoding="utf-8")
    print(f"{len(texto)} caracteres")


if __name__ == "__main__":
    sys.exit(main())
