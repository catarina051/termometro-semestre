# Chaves de ligação entre as tabelas (UFRN, 2015 a 2019)

Conferido em 2026-11-07 com DuckDB sobre os arquivos baixados por `scripts/baixar_dados.py`
(o manifesto com URL, tamanho e SHA-256 está em `manifesto_download.json`).

## Cadeia de ligação que funciona

```
matriculas-componentes.id_turma
   -> turmas.id_turma                                   (0 turmas faltando)
turmas.id_componente_curricular
   -> componentes-curriculares-presenciais.id_componente (397 turmas de graduação sem componente)
matriculas-componentes.id_curso  (1 curso por aluno)    -> nome do curso via discentes.id_curso
```

- O semestre **não** é coluna das matrículas: vem de `turmas.ano` e `turmas.periodo` (e do nome do arquivo).
- Os nomes de campo do dicionário não coincidem com os dos arquivos (ex.: `id_componente` nos componentes, `id_componente_curricular` nas turmas), como o Plano de Dados Abertos já avisava.

## O que NÃO liga

- `matriculas-componentes.discente` é um hash de 32 caracteres. `discentes.matricula` é o número real.
  Testei MD5 da matrícula (com e sem `\n`), do nome, de matrícula+nome e de matrícula+curso: **0 acertos em 500**.
  Não dá para juntar matrículas com a tabela de discentes. Consequência: não sei quando cada aluno ingressou.
- Cada aluno tem exatamente 1 `id_curso` nas matrículas, então o curso do aluno vem das próprias matrículas.

## Números de sanidade (contagens, não dados pessoais)

| Item | Valor |
| --- | --- |
| Linhas de matrícula (2015.1 a 2019.2) | 7.034.153 |
| Alunos distintos (hash) | 128.221 |
| Turmas distintas com matrícula | 83.875 |
| Turmas (todas as linhas) / distintas | 148.761 / 89.594 |
| Componentes presenciais | 44.520 |
| Discentes ingressantes 2015-2019 / matrículas distintas | 96.474 / 96.473 (1 duplicada) |
| Cursos distintos nas matrículas / em comum com discentes | 614 / 501 |

## Cuidados para o pipeline

1. Uma matrícula vira várias linhas (uma por `unidade`/nota). Antes de contar, reduzir a 1 linha por `(id_turma, discente)`.
2. Valores de `descricao` incluem situações que não são aprovação nem reprovação (CANCELADO, EXCLUIDA, TRANCADO, INDEFERIDO, DESISTENCIA, MATRICULADO etc.). A regra do que conta como "reprovou" é decisão de método.
3. Alunos que entraram antes de 2015.1 têm histórico cortado no início da janela. Sem a data de ingresso, a "tentativa número N" só vale a partir de 2015.1.
4. Os arquivos de `discentes` têm o nome do aluno. Ficam só em `dados/brutos/` (ignorado pelo Git) e não entram no pipeline.
