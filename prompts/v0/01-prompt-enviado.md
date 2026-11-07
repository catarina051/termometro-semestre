# 01 · Prompt enviado ao v0 (versão final, com o visual do GradMent)

Enviado pela IA no navegador integrado, a pedido da Catarina, que decidiu o visual (o mesmo do front do GradMent) e a regra de buscar os dados por URL em vez de anexar o arquivo. O rascunho anterior está em `01-prompt-inicial-rascunho-da-IA.md`. Texto exatamente como enviado:

```
Crie um app de página única em Next.js (App Router) + TypeScript + Tailwind + shadcn/ui + Recharts, em português do Brasil, chamado "Termômetro do Semestre". Ele mostra, com dados abertos da UFRN de 2015 a 2019, como a reprovação e a desistência se distribuem nas 15 disciplinas mais cursadas do ciclo básico de Engenharias, Computação e Ciências e Tecnologia. Público: estudante de graduação planejando o semestre. Tom: claro, honesto, sem alarmismo.

DADOS
Os dados reais ficam em https://raw.githubusercontent.com/catarina051/termometro-semestre/main/dados/termometro.json . Busque com fetch num Server Component (next: { revalidate: 3600 }), tipe tudo em TypeScript a partir da amostra abaixo e NÃO invente nenhum número nem use dados de exemplo no lugar dos reais. Não calcule nada na tela: só formate (vírgula decimal, "%" e "pp" para pontos percentuais). Se o fetch falhar, mostre um estado de erro claro, sem quebrar a página. Campos: `fonte`, `populacao`, `avisos` (`unidade`, `causalidade`, `etico`), `disciplinas` (15 itens), `curva_carga` (`reprovacao`, `desistencia`, `nao_aprovacao`), `pares` (`candidatos`, `sobreviventes`), `validacao`, `achados` (4 itens com `titulo`, `numero`, `e_dai`, `limitacao`). Em `disciplinas`, `cefet` é null quando não há equivalente no CEFET-MG; nesse caso não mostre a linha do CEFET.

ESTILO: o mesmo visual do front do GradMent (planejador de grade que eu construí)
- Fundo da página #F4F7F1 (verde-acinzentado bem claro); cartões #FCFDF9; cor primária um verde escuro, oklch(0.48 0.16 142) (aprox. #058239), com texto branco sobre ele; bordas e campos oklch(0.91 0.005 145); texto principal oklch(0.15 0.02 260); texto secundário oklch(0.48 0.02 145).
- Fonte Inter para tudo; números grandes e em negrito nos destaques.
- Cantos bem arredondados (raio de 1.225rem nos cartões e 9999px nos botões e nas abas), sombras suaves (0 4px 8px -1px rgb(0 0 0 / 0.10)).
- Barra lateral esquerda flutuante e arredondada, com o nome "Termômetro" em verde e itens de navegação por âncora (Disciplinas, Carga do semestre, Combinações, Achados); o item ativo é uma pílula verde escura com texto branco. No celular, vira uma barra no topo.
- Um cartão de destaque verde escuro, com cantos arredondados, no topo, com o número grande de "matrículas analisadas" (populacao.linhas_analisadas) e uma frase de contexto, como o cartão do curso atual do GradMent.
- Tema claro e escuro, com os tons de verde acima ajustados no escuro. Contraste AA. Funciona em 360 px sem rolagem horizontal. Não use só vermelho e verde para diferenciar séries (use também forma, rótulo ou textura).

LAYOUT (nesta ordem)
1. Cartão de destaque verde (acima) e, logo abaixo, uma faixa de aviso sempre visível com `avisos.unidade` e `avisos.causalidade`.
2. "Disciplinas": gráfico de barras horizontais (Recharts) ordenado por reprovação, com o intervalo de confiança de 95% e um segundo marcador para desistência. Ao clicar numa disciplina, abra um cartão com os números dela e o botão "Explicar em linguagem simples", que faz POST /api/explicar com { "topico": "disciplina", "numeros": { ...campos da disciplina que não são objetos aninhados... } } e mostra a resposta (estado de carregamento e de erro). Não crie a rota /api/explicar: ela já existe no projeto; só chame. Se `cefet` não for null, mostre "Equivalente no CEFET-MG: ..." com a cobertura.
3. "Carga do semestre": gráfico de linha com o intervalo de confiança e abas (Tabs) para "Reprovação", "Desistência" e "Reprovação ou desistência". Legenda abaixo: quem cursa 1 ou 2 disciplinas costuma ser aluno irregular, então a curva não diz que mais disciplinas reprovam menos.
4. "Combinações de disciplinas": título honesto, como "Cursar duas disciplinas juntas costuma significar estar atrasado". Mostre `candidatos` como barras com `pct_repetindo_a_outra` e, abaixo, a tabela de `sobreviventes` com `dif_pp`, o intervalo e `pct_confirma_na_validacao`, precedida de um aviso de que é hipótese e não recomendação.
5. "Achados": 4 itens em Accordion, cada um com o número, o "e daí?" e a limitação, nessa ordem.
6. Rodapé: fonte dos dados, link para https://github.com/catarina051/termometro-semestre e o texto de `avisos.etico`, sempre visível e sem encurtar.

RESTRIÇÕES
- Nenhuma frase do tipo "evite", "recomendamos" ou "você deve". Só descrever o que os dados mostram.
- Sem login, sem banco de dados, sem dados de alunos.
- Não invente números: tudo vem do JSON. O botão de explicar só envia números que já estão no JSON.

AMOSTRA DO FORMATO (truncada: o arquivo real tem 15 disciplinas, 12 candidatos, 3 sobreviventes e 4 achados)
{
 "fonte": {
  "instituicao": "UFRN",
  "origem": "dados.ufrn.br (dados abertos)",
  "periodo": "2015.1 a 2019.2",
  "nivel": "graduação presencial",
  "grupos_de_curso": [
   "Ciências e Tecnologia",
   "Engenharias",
   "Computação"
  ]
 },
 "populacao": {
  "linhas_analisadas": 82690,
  "linhas_calouros": 64749,
  "definicao_calouro": "aluno cuja primeira matrícula efetiva observada é de 2015.2 ou depois"
 },
 "avisos": {
  "unidade": "As taxas são por tentativa de matrícula, não por aluno: quem repete conta de novo.",
  "causalidade": "Associação observada. Não indica que cursar uma disciplina cause reprovação em outra.",
  "etico": "Dados históricos agregados da UFRN (2015 a 2019). As taxas são por tentativa de matrícula. Os resultados mostram associações, não causas, e não são previsão individual nem recomendação de grade. Este projeto não classifica alunos nem estima a chance de evasão de ninguém."
 },
 "disciplinas": [
  {
   "codigo": "ECT2103",
   "nome": "Cálculo I",
   "tentativas_concluidas": 7442,
   "reprovacao_pct": 65.49,
   "reprovacao_ic": [
    64.41,
    66.56
   ],
   "desistencia_pct": 13.08,
   "desistencia_ic": [
    12.38,
    13.81
   ],
   "mapeamento_status": "aceito",
   "cefet": {
    "codigo": "CFVR0",
    "nome": "Cálculo com Funções de Uma Variável Real",
    "cursos": "Computação; Controle e Automação",
    "cobertura": "alta",
    "correcao": null
   }
  }
 ],
 "curva_carga": {
  "desistencia": [
   {
    "disciplinas_no_semestre": "1",
    "n": 529,
    "taxa_pct": 43.29,
    "ic": [
     39.13,
     47.54
    ],
    "taxa_padronizada_pct": 46.05
   },
   {
    "disciplinas_no_semestre": "2",
    "n": 1364,
    "taxa_pct": 17.08,
    "ic": [
     15.18,
     19.17
    ],
    "taxa_padronizada_pct": 17.51
   }
  ],
  "nao_aprovacao": [
   {
    "disciplinas_no_semestre": "1",
    "n": 529,
    "taxa_pct": 76.75,
    "ic": [
     72.96,
     80.15
    ],
    "taxa_padronizada_pct": 78.56
   },
   {
    "disciplinas_no_semestre": "2",
    "n": 1364,
    "taxa_pct": 67.08,
    "ic": [
     64.54,
     69.52
    ],
    "taxa_padronizada_pct": 68.87
   }
  ],
  "reprovacao": [
   {
    "disciplinas_no_semestre": "1",
    "n": 300,
    "taxa_pct": 59.0,
    "ic": [
     53.35,
     64.42
    ],
    "taxa_padronizada_pct": 63.62
   },
   {
    "disciplinas_no_semestre": "2",
    "n": 1131,
    "taxa_pct": 60.3,
    "ic": [
     57.42,
     63.11
    ],
    "taxa_padronizada_pct": 62.51
   }
  ]
 },
 "pares": {
  "candidatos": [
   {
    "disciplina": "ECT2205",
    "nome": "Práticas de Leitura e Escrita II",
    "cursada_junto_com": "ECT2106",
    "nome_par": "Ciência, Tecnologia e Sociedade",
    "alunos_com_par": 242,
    "pct_repetindo_a_outra": 97.9,
    "dif_mh_pp": 18.0,
    "alunos_com_par_na_primeira_vez": 5
   }
  ],
  "sobreviventes": [
   {
    "disciplina": "ECT2207",
    "nome": "Probabilidade e Estatística",
    "cursada_junto_com": "ECT2205",
    "nome_par": "Práticas de Leitura e Escrita II",
    "alunos_com_par": 778,
    "alunos_sem_par": 768,
    "dif_pp": 11.1,
    "ic": [
     6.4,
     15.5
    ],
    "odds_ratio_sem_carga": 1.93,
    "or_ic": [
     1.35,
     2.74
    ],
    "p_regressao": 0.0,
    "divisoes_escolhido": 95,
    "pct_confirma_na_validacao": 95.0
   }
  ]
 },
 "validacao": {
  "original": {
   "divisoes": 100,
   "efeito_descoberta_pp": 18.5,
   "efeito_validacao_pp": 14.1,
   "inflacao_pp": 4.4,
   "pct_confirma": 90.0
  },
  "revisado": {
   "divisoes": 100,
   "efeito_descoberta_pp": 10.3,
   "efeito_validacao_pp": 7.6,
   "inflacao_pp": 2.7,
   "pct_confirma": 58.0
  }
 },
 "achados": [
  {
   "id": 1,
   "titulo": "O ciclo básico concentra a reprovação em três disciplinas de entrada",
   "numero": "7.442 tentativas concluídas em Cálculo I: 65,5% terminaram em reprovação (IC 95% 64,4 a 66…",
   "e_dai": "Quem planeja o primeiro semestre enfrenta o maior risco em Cálculo I, Vetores e Pré-Cálcul…",
   "limitacao": "a taxa é por tentativa e inclui repetentes. Não vale ler \"65% dos alunos reprovam em Cálcu…"
  }
 ]
}
```
