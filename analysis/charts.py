"""Token Clock: charts for the README. Usage: python charts.py <moves.csv> <out_dir>"""
import sys, pandas as pd, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
df = pd.read_csv(sys.argv[1]); s = df[df.set == "series"]; OUT = sys.argv[2]
COL = {"gpt-6.1-sol": "#2a78d6", "claude-sonnet-5-5": "#eb6834"}; ORDER = ["gpt-6.1-sol", "claude-sonnet-5-5"]
NAME = {"gpt-6.1-sol": "GPT-6.1 Sol", "claude-sonnet-5-5": "Claude Sonnet 5.5"}
INK, SEC, MUT, GRID, AX, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": AX, "text.color": INK})

def base(title, sub, w=9, h=5):
    f, a = plt.subplots(figsize=(w, h), dpi=160); f.patch.set_facecolor(SURF); a.set_facecolor(SURF)
    for sp in ["top", "right", "left"]: a.spines[sp].set_visible(False)
    a.tick_params(colors=MUT, length=0); a.yaxis.grid(True, color=GRID, lw=0.8); a.set_axisbelow(True)
    f.text(0.06, 0.95, title, fontsize=14, fontweight="bold", va="top"); f.text(0.06, 0.885, sub, fontsize=10.5, color=SEC, va="top")
    f.subplots_adjust(top=0.78, left=0.09, right=0.97, bottom=0.14); return f, a

CLS = ["best", "good", "inaccuracy", "mistake", "blunder"]
f, a = base("The best moves were the cheapest ones", "Median output tokens per move, by engine-judged move quality. Series of 11 games, n under each bar.")
for i, m in enumerate(ORDER):
    x = s[s.model == m]
    for j, c in enumerate(CLS):
        v = x[x.cls == c].output_tokens; 
        if not len(v): continue
        px = j + (i - 0.5) * 0.36
        a.bar(px, v.median(), width=0.32, color=COL[m], label=NAME[m] if j == 0 else None)
        a.text(px, v.median(), f"{v.median():,.0f}", ha="center", va="bottom", fontsize=9.5, color=INK)
        a.text(px, 0, f"n={len(v)}", ha="center", va="top", fontsize=8, color=MUT, transform=a.get_xaxis_transform(), clip_on=False)
a.set_xticks(range(5)); a.set_xticklabels([c.capitalize() for c in CLS]); a.tick_params(axis="x", pad=14)
a.set_ylabel("Output tokens (median)", color=SEC); a.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, borderaxespad=0)
f.savefig(f"{OUT}/tokens_by_move_quality.png", facecolor=SURF); plt.close(f)

g = s.groupby(["game", "model"]).cpl.mean().unstack()
f, a = base("Average centipawn loss, game by game", "Lower is better. Each game is one pair of dots. Series of 11 games, both models on reasoning effort high.")
xs = np.arange(len(g))
for k in xs: a.plot([k, k], [g.iloc[k].min(), g.iloc[k].max()], color=AX, lw=1.2, zorder=1)
for m in ORDER: a.scatter(xs, g[m], s=70, color=COL[m], edgecolor=SURF, linewidth=2, zorder=2, label=NAME[m])
a.set_xticks(xs); a.set_xticklabels([str(int(x[1:])) for x in g.index]); a.set_xlabel("Game", color=SEC); a.set_ylabel("ACPL", color=SEC)
a.set_ylim(0, 100); a.legend(frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, borderaxespad=0)
f.savefig(f"{OUT}/acpl_per_game.png", facecolor=SURF); plt.close(f)
print("charts ok")
