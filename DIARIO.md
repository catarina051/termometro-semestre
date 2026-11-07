# DIARIO — Termômetro do Semestre

Registro de autoria deste repositório: o que a Catarina decidiu e fez, e o que a IA fez.
Uma entrada por sessão de trabalho.

## 2026-11-07 · [começo: 13:45] h
**Catarina decidiu:** criar o repositório separado `termometro-semestre`, público, com o mesmo stack do front do GradMent (Next.js, Tailwind e shadcn), publicado na Vercel.
**Catarina fez:** [PREENCHER]
**A IA fez:** criou a estrutura inicial da pasta (`dados/`, `prompts/v0/`, `src/`), este diário, o README provisório e o `.gitignore`. Escreveu `scripts/baixar_dados.py`, que baixou 28 arquivos da UFRN (790 MB: matrículas, turmas e discentes de 2015 a 2019, mais os componentes curriculares presenciais e o dicionário). Conferiu as chaves entre as tabelas e registrou em `dados/CHAVES.md`.
**Onde a IA errou e como foi corrigido:** assumi que o hash de aluno das matrículas seria o MD5 da matrícula, para ligar com a tabela de discentes. Testei e não é (0 acertos em 500, mais 4 variantes). Em vez de insistir, registrei que a ligação não existe e que o curso do aluno vem das próprias matrículas.
**Aprendizado:** [PREENCHER]
