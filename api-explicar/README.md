# Rota `/api/explicar`

Recebe **números já calculados** e devolve uma explicação em linguagem simples feita pelo Gemini.
O modelo nunca calcula: se a explicação trouxer qualquer número que não esteja nos dados enviados,
ela é descartada (uma nova tentativa; depois, erro).

## Como colocar no app

1. Copie `explicar.mjs` e `route.ts` para `app/api/explicar/` do app Next.js.
2. Na Vercel (Settings → Environment Variables), crie `GEMINI_API_KEY` com a sua chave gratuita do
   Google AI Studio. Opcional: `GEMINI_MODEL` (padrão `gemini-2.5-flash`; se o Google trocar o nome do
   modelo gratuito, é só mudar aqui). **A chave nunca vai para o Git.**
3. Para testar localmente, crie `.env.local` com a mesma variável (o `.gitignore` já ignora).

## Contrato

```http
POST /api/explicar
{ "topico": "disciplina" | "carga" | "achado" | "par",
  "numeros": { "nome": "Cálculo I", "reprovacao_pct": 65.49, "reprovacao_ic": [64.41, 66.56] } }
```

Resposta 200: `{ "explicacao": "...", "aviso": "Explicação gerada por IA ..." }`.
Erros: 400 (entrada inválida), 429 (mais de 10 consultas por minuto por IP), 500 (sem chave),
502 (Gemini falhou ou a explicação inventou números).

## Defesas

- Entrada com formato fixo; textos só com letras, números e pontuação simples (sem `<`, `{`, crases).
- Os dados vão entre `<dados>` e a instrução de sistema manda ignorar ordens que apareçam ali.
- Verificação de saída: todo número do texto precisa existir nos dados (vírgula ou ponto valem).
- Chave só no cabeçalho `x-goog-api-key`, nunca na URL nem no prompt.
- Cache de 1 hora e limite por IP, em memória. Em ambiente serverless isso vale por instância, então
  é uma proteção de cota, não uma garantia.

## Testes

```bash
node --test api-explicar/explicar.test.mjs
```

Os testes usam um Gemini falso. **A chamada real ao Gemini não foi testada**: depende da sua chave.
