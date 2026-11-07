# Prompt para o auditor cético (colar no Gemini)

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
| código   | disciplina                                          |    n |   reprov % |   IC inf |   IC sup |   desist % |
|:---------|:----------------------------------------------------|-----:|-----------:|---------:|---------:|-----------:|
| ECT2103  | Cálculo I                                           | 7442 |       65.5 |     64.4 |     66.6 |       13.1 |
| ECT2102  | Vetores e Geometria Analítica                       | 7603 |       64.4 |     63.3 |     65.4 |       11.4 |
| ECT2101  | Pré-Cálculo                                         | 6696 |       54.7 |     53.5 |     55.9 |        9   |
| ECT2201  | Cálculo II                                          | 3758 |       54.3 |     52.7 |     55.8 |        6.8 |
| ECT2204  | Introdução à Física Clássica I                      | 4378 |       50.4 |     48.9 |     51.8 |        5.9 |
| ECT2104  | Química Geral                                       | 5925 |       48   |     46.7 |     49.3 |       12.9 |
| ECT2207  | Probabilidade e Estatística                         | 3401 |       45.2 |     43.6 |     46.9 |        4.4 |
| ECT2303  | Linguagem de Programação                            | 3364 |       45.2 |     43.5 |     46.9 |        7.5 |
| ECT2203  | Lógica de Programação                               | 4152 |       39.7 |     38.2 |     41.2 |        6.5 |
| ECT2106  | Ciência, Tecnologia e Sociedade                     | 5958 |       28.2 |     27.1 |     29.4 |        9.4 |
| ECT2205  | Práticas de Leitura e Escrita II                    | 4635 |       27.3 |     26   |     28.6 |        4.3 |
| ECT2206  | Gestão e Economia da Ciência, Tecnologia e Inovação | 4787 |       26   |     24.8 |     27.2 |        7.6 |
| ECT2302  | Metodologia Científica e Tecnológica                | 4536 |       19.6 |     18.4 |     20.7 |        6.2 |
| ECT2105  | Práticas de Leitura e Escrita I                     | 5391 |       18.7 |     17.7 |     19.8 |        8.6 |
| ECT2305  | Prática de Leitura em Inglês                        | 3534 |       12.1 |     11.1 |     13.2 |        5.6 |

### Pares com histórico: 10 maiores efeitos entre os que passam na correção
| par                  |   n com par |   reprov com % |   reprov sem % |   dif pp |   IC inf |   IC sup |   q BH |
|:---------------------|------------:|---------------:|---------------:|---------:|---------:|---------:|-------:|
| ECT2102 dado ECT2204 |         480 |         41.042 |         73.355 |  -20.406 |  -25.424 |  -14.98  |  0     |
| ECT2101 dado ECT2204 |         223 |         22.87  |         61.116 |  -18.75  |  -25.659 |  -11.505 |  0     |
| ECT2205 dado ECT2106 |         242 |         57.025 |         25.753 |   17.984 |   11.553 |   24.405 |  0     |
| ECT2104 dado ECT2204 |         107 |         28.972 |         56.711 |  -17.964 |  -26.929 |   -9.299 |  0.004 |
| ECT2101 dado ECT2207 |         118 |         18.644 |         58.423 |  -17.052 |  -25.046 |   -8.926 |  0.002 |
| ECT2204 dado ECT2102 |         475 |         72.421 |         46.21  |   16.856 |   12.11  |   21.338 |  0     |
| ECT2207 dado ECT2102 |         271 |         67.159 |         41.385 |   16.855 |   10.961 |   22.804 |  0     |
| ECT2102 dado ECT2207 |         279 |         40.502 |         69.762 |  -16.335 |  -22.408 |   -9.766 |  0     |
| ECT2303 dado ECT2103 |         195 |         69.231 |         39.366 |   16.184 |    9.177 |   23.053 |  0     |
| ECT2207 dado ECT2101 |         114 |         65.79  |         43.527 |   16.116 |    8.18  |   24.342 |  0.004 |

### Primeiro semestre (sem histórico): 8 maiores efeitos entre os que passam
| par                  |   n com par |   reprov com % |   reprov sem % |   dif pp |   IC inf |   IC sup |   q BH |
|:---------------------|------------:|---------------:|---------------:|---------:|---------:|---------:|-------:|
| ECT2105 dado ECT2106 |        4543 |         17.477 |         45     |  -27.523 |  -43.096 |  -12.456 |  0     |
| ECT2105 dado ECT2104 |        4441 |         17.046 |         38.732 |  -21.687 |  -30.137 |  -13.319 |  0     |
| ECT2101 dado ECT2106 |        4230 |         55.556 |         76.316 |  -20.76  |  -30.018 |  -11.171 |  0.003 |
| ECT2106 dado ECT2104 |        4513 |         25.305 |         43.498 |  -18.193 |  -24.876 |  -11.644 |  0     |
| ECT2101 dado ECT2104 |        4187 |         55.457 |         72.269 |  -16.812 |  -24.356 |   -8.412 |  0.003 |
| ECT2102 dado ECT2106 |        4307 |         63.478 |         79.13  |  -16.508 |  -23.712 |   -8.758 |  0.003 |
| ECT2101 dado ECT2105 |        4188 |         55.492 |         71.186 |  -15.695 |  -23.752 |   -7.636 |  0.004 |
| ECT2103 dado ECT2101 |        3948 |         65.603 |         76.923 |  -11.32  |  -16.599 |   -5.761 |  0.002 |

### Verificação por regressão (candidatos de risco)
| par                  |   n com par |   dif simples pp |   OR regressão |   IC inf |   IC sup |     p | direção mantida   |
|:---------------------|------------:|-----------------:|---------------:|---------:|---------:|------:|:------------------|
| ECT2205 dado ECT2106 |         242 |           17.984 |          1.793 |    1.318 |    2.439 | 0     | True              |
| ECT2204 dado ECT2102 |         475 |           16.856 |          1.768 |    1.361 |    2.296 | 0     | True              |
| ECT2207 dado ECT2102 |         271 |           16.855 |          1.776 |    1.295 |    2.436 | 0     | True              |
| ECT2303 dado ECT2103 |         195 |           16.184 |          1.474 |    1.022 |    2.127 | 0.038 | True              |
| ECT2207 dado ECT2101 |         114 |           16.116 |          1.416 |    0.918 |    2.184 | 0.115 | False             |
| ECT2204 dado ECT2101 |         216 |           15.579 |          1.512 |    1.061 |    2.153 | 0.022 | True              |
| ECT2207 dado ECT2205 |         854 |           14.345 |          2.421 |    1.872 |    3.13  | 0     | True              |
| ECT2207 dado ECT2204 |        1291 |           13.129 |          1.707 |    1.359 |    2.143 | 0     | True              |
| ECT2207 dado ECT2203 |         840 |           11.824 |          1.857 |    1.441 |    2.394 | 0     | True              |
| ECT2303 dado ECT2102 |         188 |            9.749 |          1.03  |    0.717 |    1.479 | 0.872 | False             |
| ECT2101 dado ECT2104 |         229 |            9.151 |          1.415 |    0.982 |    2.039 | 0.063 | False             |
| ECT2103 dado ECT2106 |         208 |            8.25  |          1.082 |    0.731 |    1.599 | 0.694 | False             |

### Reprovação e desistência por número de disciplinas no semestre (todos os alunos)
Colunas "padronizada" ajustam pela mistura de disciplinas.
| desfecho    | disciplinas   |     n |   taxa % |   IC inf |   IC sup |   padronizada % |
|:------------|:--------------|------:|---------:|---------:|---------:|----------------:|
| reprovacao  | 1             |   300 |     59   |     53.4 |     64.4 |            63.6 |
| reprovacao  | 2             |  1131 |     60.3 |     57.4 |     63.1 |            62.5 |
| reprovacao  | 3             |  3096 |     54   |     52.2 |     55.8 |            55.1 |
| reprovacao  | 4             |  6875 |     53.2 |     52   |     54.4 |            53   |
| reprovacao  | 5             | 11540 |     45.9 |     45   |     46.8 |            46.7 |
| reprovacao  | 6             | 37687 |     42   |     41.5 |     42.5 |            39.9 |
| reprovacao  | 7             | 10568 |     30   |     29.1 |     30.8 |            35.5 |
| reprovacao  | 8             |  3164 |     27.7 |     26.2 |     29.3 |            35.1 |
| reprovacao  | 9+            |  1199 |     31.7 |     29.1 |     34.4 |            34.2 |
| desistencia | 1             |   529 |     43.3 |     39.1 |     47.5 |            46   |
| desistencia | 2             |  1364 |     17.1 |     15.2 |     19.2 |            17.5 |
| desistencia | 3             |  3433 |      9.8 |      8.9 |     10.9 |            10.4 |
| desistencia | 4             |  7362 |      6.6 |      6.1 |      7.2 |             7   |
| desistencia | 5             | 12494 |      7.6 |      7.2 |      8.1 |             8.7 |
| desistencia | 6             | 40208 |      6.3 |      6   |      6.5 |             5.9 |
| desistencia | 7             | 11321 |      6.6 |      6.2 |      7.1 |            10.5 |
| desistencia | 8             |  3662 |     13.6 |     12.5 |     14.8 |            22.7 |
| desistencia | 9+            |  2317 |     48.2 |     46.2 |     50.3 |            47.4 |

## O que eu quero de você
1. Os 5 problemas mais graves de validade (confundimento, seleção, viés de sobrevivência, causalidade
   reversa, definição das variáveis, unidade de análise, dependência entre linhas), em ordem de gravidade.
2. Para cada um: por que invalida ou enfraquece qual afirmação, e que checagem simples eu faria com
   os dados que tenho (matrículas, notas, faltas, semestre, curso, tentativa).
3. Quais conclusões eu poderia sustentar com honestidade e quais devo cortar ou reformular.
4. Qualquer erro no uso de intervalo de confiança, correção para múltiplas comparações ou testes.
Não reescreva o trabalho. Critique.
