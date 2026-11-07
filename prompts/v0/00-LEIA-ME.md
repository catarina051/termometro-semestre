# Prompts do v0

Esta pasta guarda **todos** os prompts usados no v0, na ordem, porque eles são a prova do vibe coding.

## Como usar

1. Abra o v0 e anexe `dados/termometro.json` (ou cole o conteúdo) junto com o prompt `01`.
2. O `01-prompt-inicial-rascunho-da-IA.md` é só um ponto de partida escrito pela IA. **Edite como quiser antes de enviar**: o que você mudar é decisão sua e fica registrado.
3. A cada iteração no v0, salve aqui um arquivo novo: `02-...md`, `03-...md`, com o texto exato que você enviou.
   No topo de cada arquivo, escreva em 2 linhas: *o que pedi* e *o que o v0 errou ou eu não gostei*.
4. Ao terminar, anote no `DIARIO.md` quantas iterações foram e o que o v0 errou.

## Regras que valem para qualquer iteração

- A tela só lê o JSON. Nada de calcular taxa, intervalo ou média no código da tela.
- Nenhuma frase que recomende evitar ou escolher uma combinação de disciplinas.
- Nenhum dado de aluno. O JSON só tem agregados.

## Como foi na prática (07/11/2026)

O `01-prompt-enviado.md` é o prompt final, com o visual do GradMent e os dados por URL em vez de anexo. Ele foi enviado ao v0 pelo Claude, no navegador integrado, a pedido da Catarina, que depois publicou o site. O v0 gerou o app numa única geração, sem iterações no v0; as mudanças seguintes (rota `/api/explicar`, validação de tipos, README) foram feitas com o Claude Code no repositório do app.
