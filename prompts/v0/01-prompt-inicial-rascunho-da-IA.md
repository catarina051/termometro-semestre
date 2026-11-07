# 01 · Prompt inicial (rascunho escrito pela IA; a Catarina edita e envia)

> Anexe `dados/termometro.json` ao enviar este prompt.

Crie uma página única em Next.js (App Router), TypeScript, Tailwind e shadcn/ui, em português do Brasil, chamada **Termômetro do Semestre**. Ela mostra, com dados abertos da UFRN de 2015 a 2019, como a reprovação se distribui nas disciplinas do ciclo básico de engenharias e computação. Público: estudante de graduação planejando o semestre. Tom: claro, honesto, sem alarmismo.

## Dados

Importe o arquivo anexo com `import dados from "@/dados/termometro.json"` e tipe os campos. **Não calcule nada na tela**: só formate números (vírgula decimal, "%" e "pp" para pontos percentuais). Campos principais: `fonte`, `populacao`, `avisos` (`unidade`, `causalidade`, `etico`), `disciplinas` (15 itens com `reprovacao_pct`, `reprovacao_ic`, `desistencia_pct`, `desistencia_ic`, `mapeamento_status`, `cefet`), `curva_carga` (`reprovacao`, `desistencia`, `nao_aprovacao`), `pares` (`candidatos`, `sobreviventes`), `validacao`, `achados` (4 itens com `titulo`, `numero`, `e_dai`, `limitacao`).

## Layout (mobile primeiro, depois desktop)

1. **Cabeçalho**: título, uma frase de contexto e a fonte (`fonte`), mais "N matrículas analisadas" vindo de `populacao.linhas_analisadas`.
2. **Faixa de aviso** logo abaixo, sempre visível: `avisos.unidade` e `avisos.causalidade`. Se `avisos.etico` não for nulo, mostre também.
3. **Seção "Disciplinas"**: gráfico de barras horizontais (Recharts) ordenado por reprovação, com a barra do intervalo de confiança de 95% e um segundo marcador para desistência. Ao clicar numa disciplina, abra um cartão com os números dela e o botão **"Explicar em linguagem simples"**, que faz `POST /api/explicar` com `{ topico: "disciplina", numeros: {...campos da disciplina} }` e mostra a resposta (com estado de carregamento e de erro). Se `cefet` não for nulo, mostre "Equivalente no CEFET-MG: ..." com a cobertura.
4. **Seção "Carga do semestre"**: gráfico de linha com intervalo de confiança, com abas (Tabs) para "Reprovação", "Desistência" e "Reprovação ou desistência". Legenda abaixo: quem cursa 1 ou 2 disciplinas costuma ser aluno irregular, então a curva não diz que mais disciplinas reprovam menos.
5. **Seção "Combinações de disciplinas"**: título honesto, algo como "Cursar duas disciplinas juntas costuma significar estar atrasado". Mostre `candidatos` como barras com `pct_repetindo_a_outra` e, abaixo, a tabela de `sobreviventes` com `dif_pp`, intervalo e `pct_confirma_na_validacao`, precedida de um aviso de que é hipótese e não recomendação.
6. **Seção "Achados"**: 4 itens em Accordion, cada um com o número, o "e daí?" e a limitação, nessa ordem.
7. **Rodapé**: fonte dos dados, link para o repositório no GitHub e o texto de `avisos.etico` (se for nulo, deixe um espaço reservado discreto; o texto final será decidido depois).

## Estilo

Componentes shadcn (Card, Tabs, Accordion, Badge, Button, Tooltip, Skeleton). Paleta neutra com uma cor de destaque; não use só vermelho e verde para diferenciar (acessibilidade para daltonismo). Contraste AA. Funciona em 360 px de largura sem rolagem horizontal. Tema claro e escuro.

## Restrições

- Nenhuma frase do tipo "evite", "recomendamos" ou "você deve". Só descrever o que os dados mostram.
- Sem login, sem banco de dados, sem dados de alunos.
- Não invente números: tudo vem do JSON.
- O botão de explicar só envia números que já estão no JSON.
