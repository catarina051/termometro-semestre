"""Graficos estaticos para o README (docs/img/*.png), a partir de dados/termometro.json.

Uma cor por serie (paleta categorica validada), barras finas, rotulos diretos, sem eixo duplo.
Uso: python -I scripts/gerar_graficos.py
"""
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "docs" / "img"
AZUL, LARANJA, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, MUDO, GRADE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
SUPERFICIE = "#fcfcfb"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRADE, "axes.labelcolor": INK2,
    "xtick.color": MUDO, "ytick.color": INK2, "figure.facecolor": SUPERFICIE, "axes.facecolor": SUPERFICIE,
})


def pt(x, n=1):
    return f"{x:.{n}f}".replace(".", ",")


def limpar(ax):
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(GRADE)
    ax.grid(axis="x", color=GRADE, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)


def grafico_disciplinas(j):
    d = sorted(j["disciplinas"], key=lambda x: x["reprovacao_pct"])
    fig, ax = plt.subplots(figsize=(9, 6.2))
    y = range(len(d))
    ax.barh(y, [x["reprovacao_pct"] for x in d], height=0.5, color=AZUL, zorder=2, label="Reprovação (entre as concluídas)")
    for i, x in enumerate(d):
        lo, hi = x["reprovacao_ic"]
        ax.plot([lo, hi], [i, i], color=INK, linewidth=1.4, zorder=3)
        ax.text(hi + 1.2, i, f"{pt(x['reprovacao_pct'])}%", va="center", fontsize=9, color=INK)
    ax.scatter([x["desistencia_pct"] for x in d], y, marker="D", s=34, color=LARANJA, zorder=4, edgecolor=SUPERFICIE, linewidth=1.2,
               label="Desistência (trancou ou desistiu)")
    ax.set_yticks(list(y))
    ax.set_yticklabels([x["nome"] for x in d])
    ax.set_xlim(0, 80)
    ax.set_xlabel("% das tentativas (a linha preta é o intervalo de confiança de 95%)")
    limpar(ax)
    ax.legend(loc="lower right", frameon=False, fontsize=9)
    ax.set_title("Reprovação e desistência por disciplina (UFRN, 2015.1 a 2019.2)", loc="left", fontsize=11, color=INK, pad=12)
    fig.tight_layout()
    fig.savefig(SAIDA / "reprovacao_por_disciplina.png", dpi=160)
    plt.close(fig)


def grafico_curva(j):
    ordem = ["1", "2", "3", "4", "5", "6", "7", "8", "9+"]
    fig, ax = plt.subplots(figsize=(9, 5))
    series = [("nao_aprovacao", "Reprovação ou desistência", AQUA), ("reprovacao", "Reprovação (só concluídas)", AZUL),
              ("desistencia", "Desistência", LARANJA)]
    for chave, rotulo, cor in series:
        pts = {p["disciplinas_no_semestre"]: p for p in j["curva_carga"][chave]}
        xs = range(len(ordem))
        ys = [pts[o]["taxa_pct"] for o in ordem]
        lo = [pts[o]["ic"][0] for o in ordem]
        hi = [pts[o]["ic"][1] for o in ordem]
        ax.fill_between(xs, lo, hi, color=cor, alpha=0.15, linewidth=0)
        ax.plot(xs, ys, color=cor, linewidth=2, marker="o", markersize=6, markeredgecolor=SUPERFICIE, markeredgewidth=1.5, label=rotulo)
        ax.text(len(ordem) - 1 + 0.12, ys[-1], f"{pt(ys[-1])}%", color=INK, va="center", fontsize=9)
    ax.set_xticks(range(len(ordem)))
    ax.set_xticklabels(ordem)
    ax.set_xlabel("Disciplinas no semestre (contando as que o aluno depois trancou)")
    ax.set_ylabel("% das matrículas")
    ax.set_ylim(0, 90)
    ax.set_xlim(-0.3, len(ordem) - 0.3 + 0.5)
    limpar(ax)
    ax.grid(axis="y", color=GRADE, linewidth=0.8)
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper center", frameon=False, ncol=3, fontsize=9)
    ax.set_title("A carga do semestre tem forma de U quando se soma reprovação e desistência", loc="left", fontsize=11, color=INK, pad=12)
    fig.tight_layout()
    fig.savefig(SAIDA / "curva_carga.png", dpi=160)
    plt.close(fig)


def grafico_repeticao(j):
    c = sorted(j["pares"]["candidatos"], key=lambda x: x["pct_repetindo_a_outra"])
    fig, ax = plt.subplots(figsize=(9, 5.6))
    y = range(len(c))
    ax.barh(y, [x["pct_repetindo_a_outra"] for x in c], height=0.5, color=AZUL, zorder=2)
    for i, x in enumerate(c):
        ax.text(x["pct_repetindo_a_outra"] + 1, i, f"{pt(x['pct_repetindo_a_outra'])}%", va="center", fontsize=9, color=INK)
    ax.set_yticks(list(y))
    ax.set_yticklabels([f"{x['nome']} (junto com {x['nome_par']})" for x in c], fontsize=8.5)
    ax.set_xlim(0, 112)
    ax.set_xlabel("% dos alunos que repetiam a segunda disciplina")
    limpar(ax)
    n_forte = sum(x["pct_repetindo_a_outra"] > 90 for x in c)
    fig.suptitle(f"Em {n_forte} dos {len(c)} maiores 'pares de risco', mais de 90% dos alunos repetem uma das disciplinas",
                 x=0.01, ha="left", fontsize=11, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(SAIDA / "pares_sao_repetencia.png", dpi=160)
    plt.close(fig)


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    j = json.loads((RAIZ / "dados" / "termometro.json").read_text(encoding="utf-8"))
    grafico_disciplinas(j)
    grafico_curva(j)
    grafico_repeticao(j)
    print([p.name for p in sorted(SAIDA.glob("*.png"))])


if __name__ == "__main__":
    sys.exit(main())
