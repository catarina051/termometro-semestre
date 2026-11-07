# Prompt para o auditor cético (colar no ChatGPT)

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
anterior (média das notas finais dos semestres anteriores; cortes: 4.28 e 5.65).
Efeito = diferença de risco de Mantel-Haenszel em pontos percentuais; IC 95% por bootstrap
paramétrico dentro de cada faixa (2000 réplicas); p-valor do teste de
Cochran-Mantel-Haenszel. Suporte mínimo: 100 alunos com o par. Correção:
Benjamini-Hochberg a 5%. Calouros no primeiro semestre não têm desempenho anterior e foram
analisados à parte, estratificando por grupo de curso (BC&T / Engenharias / Computação).
Verificação: regressão logística nos candidatos de risco, com desempenho anterior, número da
tentativa (1, 2, 3+), carga do semestre, grupo de curso e semestre do calendário como controles;
erro padrão agrupado por aluno.

Contagens: 147 comparações com histórico (48 passam na correção: 22 com
risco maior com o par, 26 com risco menor); 50 comparações no primeiro semestre
(14 passam).

## Resultados
### Reprovação e desistência por disciplina (todos os alunos, %)
| código   | disciplina                      |   tentativas concluídas |   reprov % |   IC inf |   IC sup |   desist % |
|:---------|:--------------------------------|------------------------:|-----------:|---------:|---------:|-----------:|
| ECT2103  | Cálculo I                       |                    7442 |       65.5 |     64.4 |     66.6 |       13.1 |
| ECT2102  | Vetores e Geom. Analítica       |                    7603 |       64.4 |     63.3 |     65.4 |       11.4 |
| ECT2101  | Pré-Cálculo                     |                    6696 |       54.7 |     53.5 |     55.9 |        9   |
| ECT2201  | Cálculo II                      |                    3758 |       54.3 |     52.7 |     55.8 |        6.8 |
| ECT2204  | Física Clássica I               |                    4378 |       50.4 |     48.9 |     51.8 |        5.9 |
| ECT2104  | Química Geral                   |                    5925 |       48   |     46.7 |     49.3 |       12.9 |
| ECT2207  | Probabilidade e Estatística     |                    3401 |       45.2 |     43.6 |     46.9 |        4.4 |
| ECT2303  | Linguagem de Programação        |                    3364 |       45.2 |     43.5 |     46.9 |        7.5 |
| ECT2203  | Lógica de Programação           |                    4152 |       39.7 |     38.2 |     41.2 |        6.5 |
| ECT2106  | Ciência, Tecnologia e Sociedade |                    5958 |       28.2 |     27.1 |     29.4 |        9.4 |
| ECT2205  | Leitura e Escrita II            |                    4635 |       27.3 |     26   |     28.6 |        4.3 |
| ECT2206  | Gestão e Economia da CT&I       |                    4787 |       26   |     24.8 |     27.2 |        7.6 |
| ECT2302  | Metodologia Científica          |                    4536 |       19.6 |     18.4 |     20.7 |        6.2 |
| ECT2105  | Leitura e Escrita I             |                    5391 |       18.7 |     17.7 |     19.8 |        8.6 |
| ECT2305  | Leitura em Inglês               |                    3534 |       12.1 |     11.1 |     13.2 |        5.6 |

### Pares com histórico: 10 maiores efeitos entre os que passam na correção
Leitura: "A dado B" é a reprovação em A de quem cursou B no mesmo semestre (n com par) contra quem
cursou A sem B. A coluna q BH é o p-valor depois da correção.
| par                                                        |   n com par |   reprov com % |   reprov sem % |   dif pp |   IC inf |   IC sup | q BH   |
|:-----------------------------------------------------------|------------:|---------------:|---------------:|---------:|---------:|---------:|:-------|
| Vetores e Geom. Analítica dado Física Clássica I           |         480 |           41   |           73.4 |    -20.4 |    -25.4 |    -15   | <0,001 |
| Pré-Cálculo dado Física Clássica I                         |         223 |           22.9 |           61.1 |    -18.8 |    -25.7 |    -11.5 | <0,001 |
| Leitura e Escrita II dado Ciência, Tecnologia e Sociedade  |         242 |           57   |           25.8 |     18   |     11.6 |     24.4 | <0,001 |
| Química Geral dado Física Clássica I                       |         107 |           29   |           56.7 |    -18   |    -26.9 |     -9.3 | 0,004  |
| Pré-Cálculo dado Probabilidade e Estatística               |         118 |           18.6 |           58.4 |    -17.1 |    -25   |     -8.9 | 0,002  |
| Física Clássica I dado Vetores e Geom. Analítica           |         475 |           72.4 |           46.2 |     16.9 |     12.1 |     21.3 | <0,001 |
| Probabilidade e Estatística dado Vetores e Geom. Analítica |         271 |           67.2 |           41.4 |     16.9 |     11   |     22.8 | <0,001 |
| Vetores e Geom. Analítica dado Probabilidade e Estatística |         279 |           40.5 |           69.8 |    -16.3 |    -22.4 |     -9.8 | <0,001 |
| Linguagem de Programação dado Cálculo I                    |         195 |           69.2 |           39.4 |     16.2 |      9.2 |     23.1 | <0,001 |
| Probabilidade e Estatística dado Pré-Cálculo               |         114 |           65.8 |           43.5 |     16.1 |      8.2 |     24.3 | 0,004  |

### Primeiro semestre (sem histórico): 8 maiores efeitos entre os que passam
| par                                                            |   n com par |   reprov com % |   reprov sem % |   dif pp |   IC inf |   IC sup | q BH   |
|:---------------------------------------------------------------|------------:|---------------:|---------------:|---------:|---------:|---------:|:-------|
| Leitura e Escrita I dado Ciência, Tecnologia e Sociedade       |        4543 |           17.5 |           45   |    -27.5 |    -43.1 |    -12.5 | <0,001 |
| Leitura e Escrita I dado Química Geral                         |        4441 |           17   |           38.7 |    -21.7 |    -30.1 |    -13.3 | <0,001 |
| Pré-Cálculo dado Ciência, Tecnologia e Sociedade               |        4230 |           55.6 |           76.3 |    -20.8 |    -30   |    -11.2 | 0,003  |
| Ciência, Tecnologia e Sociedade dado Química Geral             |        4513 |           25.3 |           43.5 |    -18.2 |    -24.9 |    -11.6 | <0,001 |
| Pré-Cálculo dado Química Geral                                 |        4187 |           55.5 |           72.3 |    -16.8 |    -24.4 |     -8.4 | 0,003  |
| Vetores e Geom. Analítica dado Ciência, Tecnologia e Sociedade |        4307 |           63.5 |           79.1 |    -16.5 |    -23.7 |     -8.8 | 0,003  |
| Pré-Cálculo dado Leitura e Escrita I                           |        4188 |           55.5 |           71.2 |    -15.7 |    -23.8 |     -7.6 | 0,004  |
| Cálculo I dado Pré-Cálculo                                     |        3948 |           65.6 |           76.9 |    -11.3 |    -16.6 |     -5.8 | 0,002  |

### Verificação por regressão (candidatos de risco)
| par                                                        |   n com par |   dif MH pp |   OR regressão |   IC inf |   IC sup | p      | q BH   | mantém após BH   |
|:-----------------------------------------------------------|------------:|------------:|---------------:|---------:|---------:|:-------|:-------|:-----------------|
| Leitura e Escrita II dado Ciência, Tecnologia e Sociedade  |         242 |       17.98 |           1.79 |     1.32 |     2.44 | <0,001 | <0,001 | True             |
| Física Clássica I dado Vetores e Geom. Analítica           |         475 |       16.86 |           1.77 |     1.36 |     2.3  | <0,001 | <0,001 | True             |
| Probabilidade e Estatística dado Vetores e Geom. Analítica |         271 |       16.85 |           1.78 |     1.3  |     2.44 | <0,001 | <0,001 | True             |
| Linguagem de Programação dado Cálculo I                    |         195 |       16.18 |           1.47 |     1.02 |     2.13 | 0,038  | 0,057  | False            |
| Probabilidade e Estatística dado Pré-Cálculo               |         114 |       16.12 |           1.42 |     0.92 |     2.18 | 0,115  | 0,139  | False            |
| Física Clássica I dado Pré-Cálculo                         |         216 |       15.58 |           1.51 |     1.06 |     2.15 | 0,022  | 0,038  | True             |
| Probabilidade e Estatística dado Leitura e Escrita II      |         854 |       14.35 |           2.42 |     1.87 |     3.13 | <0,001 | <0,001 | True             |
| Probabilidade e Estatística dado Física Clássica I         |        1291 |       13.13 |           1.71 |     1.36 |     2.14 | <0,001 | <0,001 | True             |
| Probabilidade e Estatística dado Lógica de Programação     |         840 |       11.82 |           1.86 |     1.44 |     2.39 | <0,001 | <0,001 | True             |
| Linguagem de Programação dado Vetores e Geom. Analítica    |         188 |        9.75 |           1.03 |     0.72 |     1.48 | 0,872  | 0,872  | False            |
| Pré-Cálculo dado Química Geral                             |         229 |        9.15 |           1.41 |     0.98 |     2.04 | 0,063  | 0,084  | False            |
| Cálculo I dado Ciência, Tecnologia e Sociedade             |         208 |        8.25 |           1.08 |     0.73 |     1.6  | 0,695  | 0,758  | False            |

### Reprovação e desistência por número de disciplinas no semestre (todos os alunos)
"disciplinas" é a carga definida acima. A coluna padronizada ajusta pela mistura das 15 disciplinas.
| desfecho      | disciplinas   |     n |   taxa % |   IC inf |   IC sup |   padronizada % |
|:--------------|:--------------|------:|---------:|---------:|---------:|----------------:|
| reprovacao    | 1             |   300 |     59   |     53.4 |     64.4 |            63.6 |
| reprovacao    | 2             |  1131 |     60.3 |     57.4 |     63.1 |            62.5 |
| reprovacao    | 3             |  3096 |     54   |     52.2 |     55.8 |            55.1 |
| reprovacao    | 4             |  6875 |     53.2 |     52   |     54.4 |            53   |
| reprovacao    | 5             | 11540 |     45.9 |     45   |     46.8 |            46.7 |
| reprovacao    | 6             | 37687 |     42   |     41.5 |     42.5 |            39.9 |
| reprovacao    | 7             | 10568 |     30   |     29.1 |     30.8 |            35.5 |
| reprovacao    | 8             |  3164 |     27.7 |     26.2 |     29.3 |            35.1 |
| reprovacao    | 9+            |  1199 |     31.7 |     29.1 |     34.4 |            34.2 |
| desistencia   | 1             |   529 |     43.3 |     39.1 |     47.5 |            46   |
| desistencia   | 2             |  1364 |     17.1 |     15.2 |     19.2 |            17.5 |
| desistencia   | 3             |  3433 |      9.8 |      8.9 |     10.9 |            10.4 |
| desistencia   | 4             |  7362 |      6.6 |      6.1 |      7.2 |             7   |
| desistencia   | 5             | 12494 |      7.6 |      7.2 |      8.1 |             8.7 |
| desistencia   | 6             | 40208 |      6.3 |      6   |      6.5 |             5.9 |
| desistencia   | 7             | 11321 |      6.6 |      6.2 |      7.1 |            10.5 |
| desistencia   | 8             |  3662 |     13.6 |     12.5 |     14.8 |            22.7 |
| desistencia   | 9+            |  2317 |     48.2 |     46.2 |     50.3 |            47.4 |
| nao_aprovacao | 1             |   529 |     76.8 |     73   |     80.2 |            78.6 |
| nao_aprovacao | 2             |  1364 |     67.1 |     64.5 |     69.5 |            68.9 |
| nao_aprovacao | 3             |  3433 |     58.5 |     56.9 |     60.2 |            59.5 |
| nao_aprovacao | 4             |  7362 |     56.3 |     55.2 |     57.4 |            56.2 |
| nao_aprovacao | 5             | 12494 |     50   |     49.1 |     50.9 |            51.2 |
| nao_aprovacao | 6             | 40208 |     45.6 |     45.2 |     46.1 |            43.2 |
| nao_aprovacao | 7             | 11321 |     34.6 |     33.8 |     35.5 |            42   |
| nao_aprovacao | 8             |  3662 |     37.6 |     36   |     39.1 |            48.9 |
| nao_aprovacao | 9+            |  2317 |     64.6 |     62.7 |     66.6 |            65.4 |

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
