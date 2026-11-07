"""Monta achados/ACHADOS.md a partir de resultados/*.csv (todo numero vem de arquivo).

Formato de cada achado: achado -> numero -> "e dai?" -> limitacao.
Uso: python -I scripts/gerar_achados.py   (depois de analise, checagens e validacao)
"""
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
R = RAIZ / "resultados"


def f(x, n=1):
    return f"{x:.{n}f}".replace(".", ",")


def milhar(n):
    return f"{int(n):,}".replace(",", ".")


def main():
    disc = pd.read_csv(R / "disciplinas.csv").set_index("codigo")
    chk = pd.read_csv(R / "checagens_auditoria.csv")
    sob = pd.read_csv(R / "sobreviventes_auditoria.csv")
    vpar = pd.read_csv(R / "validacao_por_par.csv")
    vres = pd.read_csv(R / "validacao_resumo.csv").set_index("procedimento")
    curva = pd.read_csv(R / "curva_carga.csv", dtype={"disciplinas_no_semestre": str})
    meta = pd.read_json(R / "metodo.json", typ="series")

    cl, vet, ing = disc.loc["ECT2103"], disc.loc["ECT2102"], disc.loc["ECT2305"]
    pre = disc.loc["ECT2101"]

    # --- achado 2: "cursou junto" e repeticao
    forte = chk[chk["pct_B_repeticao_entre_expostos"] > 90]
    max_limpo = int(forte["limpo_n_com_par"].fillna(0).max())
    zero_limpo = int(forte["limpo_n_com_par"].isna().sum())
    lei = chk[(chk["disciplina"] == "ECT2205") & (chk["dado_par"] == "ECT2106")].iloc[0]
    fis = chk[(chk["disciplina"] == "ECT2204") & (chk["dado_par"] == "ECT2102")].iloc[0]

    # --- achado 3: Probabilidade e Estatistica
    def vp(b):
        return vpar[(vpar["procedimento"] == "revisado") & (vpar["disciplina"] == "ECT2207") & (vpar["dado_par"] == b)].iloc[0]

    linhas3 = []
    for b in ("ECT2205", "ECT2203", "ECT2204"):
        s = sob[(sob["disciplina"] == "ECT2207") & (sob["dado_par"] == b)].iloc[0]
        v = vp(b)
        linhas3.append(
            f"| {s['nome_par']} | {int(s['n_com_par'])} / {int(s['n_sem_par'])} | +{f(s['dif_MH_pp'])} "
            f"({f(s['ic_cluster_inf'])} a {f(s['ic_cluster_sup'])}) | {f(s['or_sem_carga'], 2)} "
            f"({f(s['or_ic_inf'], 2)} a {f(s['or_ic_sup'], 2)}) | {int(v['vezes_finalista'])} de 100 | {f(v['pct_confirma'], 0)}% |"
        )
    rev, ori = vres.loc["revisado"], vres.loc["original"]

    # --- achado 4: curva
    def c(desf, faixa):
        return curva[(curva["desfecho"] == desf) & (curva["disciplinas_no_semestre"] == faixa)].iloc[0]

    na1, na7, na9 = c("nao_aprovacao", "1"), c("nao_aprovacao", "7"), c("nao_aprovacao", "9+")
    ds9 = c("desistencia", "9+")
    rp1, rp8 = c("reprovacao", "1"), c("reprovacao", "8")

    texto = f"""# Achados do Termômetro do Semestre

Rascunho da IA para revisão da Catarina. Todo número abaixo vem de `resultados/*.csv`, gerados
por `scripts/`. Dados: matrículas de graduação da UFRN, 2015.1 a 2019.2, cursos de Ciências e
Tecnologia, Engenharias e Computação, 15 disciplinas mais cursadas. As taxas são **por
tentativa**, não por aluno: quem repete uma disciplina conta de novo.

## Achado 1. O ciclo básico concentra a reprovação em três disciplinas de entrada

- **Número:** {milhar(cl['n_concluidas'])} tentativas concluídas em {cl['disciplina']}: {f(cl['reprovacao_pct'])}% terminaram em reprovação (IC 95% {f(cl['reprov_ic_inf'])} a {f(cl['reprov_ic_sup'])}). {vet['disciplina']}: {f(vet['reprovacao_pct'])}%. {pre['disciplina']}: {f(pre['reprovacao_pct'])}%. No extremo oposto, {ing['disciplina']}: {f(ing['reprovacao_pct'])}%. A desistência (trancamento ou desistência formal) também é maior nas de entrada: {f(cl['desistencia_pct'])}% em {cl['disciplina']}.
- **E daí?** Quem planeja o primeiro semestre enfrenta o maior risco em Cálculo I, Vetores e Pré-Cálculo, e não na carga de leitura ou de gestão. Um simulador de grade deveria mostrar essa diferença entre disciplinas antes de qualquer conversa sobre combinações.
- **Limitação:** a taxa é por tentativa e inclui repetentes. Não vale ler "{f(cl['reprovacao_pct'], 0)}% dos alunos reprovam em {cl['disciplina']}". Os dados descrevem a UFRN em 2015 a 2019; o CEFET não está neles, e o mapeamento entre as duas instituições é uma etapa à parte.

## Achado 2. "Cursar duas disciplinas juntas" costuma significar "estar atrasado"

- **Número:** em {len(forte)} dos {len(chk)} maiores candidatos a "par de risco", entre {f(forte['pct_B_repeticao_entre_expostos'].min(), 0)}% e {f(forte['pct_B_repeticao_entre_expostos'].max(), 0)}% dos alunos que cursaram a segunda disciplina junto estavam **repetindo** essa segunda disciplina. Em {lei['nome']} dado {lei['nome_par']}, o par com o maior efeito aparente, eram {f(lei['pct_B_repeticao_entre_expostos'])}%. Em {fis['nome']} dado {fis['nome_par']}, {f(fis['pct_B_repeticao_entre_expostos'])}%. Refazendo as comparações só com alunos na primeira vez, esses {len(forte)} pares ficam com no máximo {max_limpo} alunos no grupo com o par (em {zero_limpo} deles, nenhum), longe dos 100 exigidos para concluir.
- **E daí?** Um "par perigoso" medido sem separar repetência mostra o perfil do aluno atrasado, não o efeito da combinação. Qualquer ferramenta que oriente a escolha de combinações com esse tipo de número erra o alvo.
- **Limitação:** a repetição só é observada a partir de 2015.1, e a "primeira vez" de um aluno que já cursava antes é desconhecida. O vínculo entre matrículas e data de ingresso não existe nos dados abertos.

## Achado 3. Só Probabilidade e Estatística mantém um sinal depois das checagens

- **Número:** entre os 12 candidatos de risco, só ficaram comparações com Probabilidade e Estatística como disciplina de interesse (A e B na primeira vez, pelo menos 100 alunos nos dois grupos, IC por aluno acima de zero). Nelas, alunos que a cursaram no mesmo semestre de outra disciplina (ambas na primeira vez, calouros com histórico) reprovaram mais do que alunos que a cursaram sem ela:

| Cursada junto com | Alunos com / sem a outra | Diferença em pontos percentuais (IC 95%) | OR da regressão sem carga (IC 95%) | Escolhida na descoberta | Confirmada na validação |
| --- | --- | --- | --- | --- | --- |
{chr(10).join(linhas3)}

  Nas {int(rev['divisoes'])} divisões aleatórias de alunos, o efeito médio dos finalistas caiu de {f(rev['efeito_descoberta_medio_pp'])} pp na metade de descoberta para {f(rev['efeito_validacao_medio_pp'])} pp na de validação (inflação média de {f(rev['inflacao_media_pp'])} pp, cerca de {f(100 * rev['inflacao_media_pp'] / rev['efeito_descoberta_medio_pp'], 0)}%).
- **E daí?** É uma hipótese concreta para investigar (oferta, horários, curso), não uma recomendação de grade.
- **Limitação:** é associação, não causa. {sob.loc[sob['dado_par'] == 'ECT2204', 'nome_par'].iloc[0]} não se sustenta na regressão (p = {f(float(sob.loc[sob['dado_par'] == 'ECT2204', 'p'].iloc[0]), 3)}). "Leitura e Escrita II" é uma disciplina de formação geral, improvável como causa direta, o que sugere perfil de curso ou de trajetória ainda não controlado. A validação com divisão de alunos mede a inflação por seleção, **não** elimina confundimento: o procedimento original, sem o filtro de repetência, "confirma" em {f(ori['pct_confirma_na_validacao'], 0)}% das validações justamente porque o artefato da repetência se repete em qualquer metade dos alunos.

## Achado 4. A carga do semestre tem forma de U quando se junta reprovação e desistência

- **Número:** considerando reprovação ou desistência sobre todas as matrículas, a taxa é {f(na1['taxa_pct'])}% com 1 disciplina no semestre, {f(na7['taxa_pct'])}% com 7 e {f(na9['taxa_pct'])}% com 9 ou mais. Olhando só a reprovação entre os que concluíram, ela cai de {f(rp1['taxa_pct'])}% (1 disciplina) para {f(rp8['taxa_pct'])}% (8), o que esconde que {f(ds9['taxa_pct'])}% das matrículas com 9 ou mais disciplinas terminam em trancamento ou desistência.
- **E daí?** Cargas muito baixas ou muito altas se associam a não concluir, não a aprender mais ou menos. Mostrar só reprovação passaria a mensagem errada de que "mais disciplinas reprova menos".
- **Limitação:** a carga é medida no fim do semestre e conta disciplinas depois trancadas; quem cursa uma ou duas disciplinas é, em geral, um aluno irregular. Não dá para dizer que alterar a carga muda o resultado.

## Como a IA foi usada e conferida (resumo para o README, a reescrever na voz da Catarina)

- Claude fez os cálculos; um agente Opus sem contexto e o ChatGPT fizeram a crítica independente; a Catarina decidiu população, cursos, disciplinas, método, suporte mínimo e correção.
- A crítica mudou o resultado: {meta['comparacoes_testadas_com_historico']} comparações com histórico entraram no Benjamini-Hochberg e {meta['passam_bh_com_historico']} passaram, mas após separar repetência sobraram 3. A tabela do primeiro semestre foi descartada (o grupo sem a segunda disciplina tinha de 40 a 223 alunos).
- Erros da IA já corrigidos: coluna "direção mantida" que aplicava p < 0,05, rótulo "diferença simples" que era a de Mantel-Haenszel e controle de carga que incluía a própria disciplina em estudo. Detalhes no `DIARIO.md`.
"""
    saida = RAIZ / "achados"
    saida.mkdir(exist_ok=True)
    (saida / "ACHADOS.md").write_text(texto, encoding="utf-8")
    print(f"{len(texto)} caracteres")


if __name__ == "__main__":
    sys.exit(main())
