# DIARIO — Termômetro do Semestre

Registro de autoria deste repositório: o que a Catarina decidiu e fez, e o que a IA fez.
Uma entrada por sessão de trabalho.

## 2026-11-07 · [começo: 13:45] h
**Catarina decidiu:** criar o repositório separado `termometro-semestre`, público, com o mesmo stack do front do GradMent (Next.js, Tailwind e shadcn), publicado na Vercel.
**Catarina decidiu (população de análise):** como não há ligação entre matrículas e discentes, não se sabe a data de ingresso. Opções apresentadas: (1) todos os alunos com a janela como está; (2) só quem aparece pela primeira vez em 2015.2 ou depois (40.941 de 71.565 alunos de graduação); (3) híbrida. Escolha: **(3)**. Taxas de reprovação por disciplina e curva por carga usam todos os alunos; tentativa, desempenho anterior e pares de risco usam só quem foi visto entrando (primeiro semestre observado em 2015.2 ou depois).
**Catarina fez:** [PREENCHER]
**A IA fez:** criou a estrutura inicial da pasta (`dados/`, `prompts/v0/`, `src/`), este diário, o README provisório e o `.gitignore`. Escreveu `scripts/baixar_dados.py`, que baixou 28 arquivos da UFRN (790 MB: matrículas, turmas e discentes de 2015 a 2019, mais os componentes curriculares presenciais e o dicionário). Conferiu as chaves entre as tabelas e registrou em `dados/CHAVES.md`.
**A IA fez (pipeline):** `scripts/construir_tentativas.py` gera a tabela `tentativas` em DuckDB (1.596.446 linhas, 71.565 alunos de graduação, 2015.1 a 2019.2). `tests/test_tentativas.py` tem 9 testes, incluindo a conferência de 10 alunos recalculados em Python puro direto dos CSV; os 9 passam. Com a regra de "visto entrando" aplicada sobre matrículas efetivas, a coorte de calouros ficou em 39.124 alunos (a contagem de 40.941 que mostrei antes usava qualquer linha, inclusive canceladas).
**Onde a IA errou e como foi corrigido:** (1) o join com as turmas multiplicou as linhas: deu 2,34 milhões de "tentativas" quando todo o arquivo de matrículas tem 2,04 milhões de pares aluno-turma. Percebi pela contagem, vi que os CSV de turmas se repetem e usei `DISTINCT`; caiu para 1,60 milhão. (2) Escrevi um teste com limite de 20 disciplinas por semestre sem ter olhado os dados; o máximo real é 21. Medi a distribuição (99,7% até 15) e troquei o limite por esse critério. (3) assumi que o hash de aluno das matrículas seria o MD5 da matrícula, para ligar com a tabela de discentes. Testei e não é (0 acertos em 500, mais 4 variantes). Em vez de insistir, registrei que a ligação não existe e que o curso do aluno vem das próprias matrículas.
**Aprendizado:** [PREENCHER]
