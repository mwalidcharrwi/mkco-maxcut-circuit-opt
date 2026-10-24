"""Static figures for the report (needs matplotlib; reads JSON results only).

Palette: reference categorical slots 1-3 (blue, orange, aqua), validated
all-pairs for three series in light mode; every figure has a table in
docs/REPORT.md (relief rule for the low-contrast aqua slot).
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
OUT = "docs/figures"
ORDER = ["mult_8", "add_17", "qae_17", "qft_16", "hubbard_8", "hhl_8", "heisenberg_32",
         "grover_10", "hubbard_18"]


def style(ax, title, ylabel):
    ax.set_facecolor(SURFACE)
    ax.figure.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=9)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.set_title(title, color=INK, fontsize=12, loc="left", pad=12)
    ax.set_ylabel(ylabel, color=INK2, fontsize=10)


def fig_depth(res):
    names = [n for n in ORDER if n in res]
    series = [("Lee et al. 2026 (colouring)", "lee2026", ORANGE),
              ("Jain & Kumar 2026 (MIS + beam)", "jk2026", AQUA),
              ("MKCO (ours)", "mkco", BLUE)]
    fig, ax = plt.subplots(figsize=(10, 4.2))
    w = 0.26
    for k, (label, key, col) in enumerate(series):
        vals = [100 * (res[n]["methods"]["original"]["depth"] - res[n]["methods"][key]["depth"])
                / res[n]["methods"]["original"]["depth"] for n in names]
        xs = [i + (k - 1) * w for i in range(len(names))]
        ax.bar(xs, vals, width=w, color=col, edgecolor=SURFACE, linewidth=2, label=label)
    for i, n in enumerate(names):
        m = res[n]["methods"]
        lbv = 100 * (m["original"]["depth"] - m["mkco"]["lower_bound"]) / m["original"]["depth"]
        ax.plot([i - 1.5 * w, i + 1.5 * w], [lbv, lbv], color=INK, linewidth=1.2)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, rotation=0, fontsize=8.5, color=INK2)
    style(ax, "Depth reduction vs. transpiled input (reorder-only; black line = certified optimum)",
          "depth reduction (%)")
    ax.set_ylim(0, max(6.2, ax.get_ylim()[1]))
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2, loc="upper left", ncol=3)
    ax.text(len(names) - 0.5, 5.75, "Lee et al.: 0% on every circuit", ha="right", fontsize=9, color=INK2)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "ibm127_depth.png"), dpi=160)


def fig_xt(res):
    names = [n for n in ORDER if n in res]
    vals = []
    for n in names:
        m = res[n]["methods"]
        best = min(m[k]["xt_pairs"] for k in ("original", "lee2026_2q", "jk2026_2q", "mkco_2q"))
        vals.append(100 * (best - m["mkco_xt"]["xt_pairs"]) / best if best else 0)
    fig, ax = plt.subplots(figsize=(10, 3.8))
    bars = ax.bar(range(len(names)), vals, width=0.55, color=BLUE, edgecolor=SURFACE, linewidth=2)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.5, f"{v:.0f}%", ha="center", va="bottom",
                fontsize=9, color=INK)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, fontsize=8.5, color=INK2)
    style(ax, "Fewer crosstalk-prone ECR pairs at unchanged optimal 2q-depth (MKCO-XT vs best baseline)",
          "reduction (%)")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "ibm127_crosstalk.png"), dpi=160)


def fig_gf2(rows):
    rows = [r for r in rows if r["n"] <= 32]
    ns = [r["n"] for r in rows]
    fig, ax = plt.subplots(figsize=(10, 3.8))
    for label, key, col, mk in (("DSatur (Lee et al.)", "dsatur", ORANGE, "o"),
                                ("Jain & Kumar", "jk", AQUA, "s"),
                                ("MKCO (ours)", "mkco", BLUE, "D")):
        ax.plot(ns, [r[key] - r["lb"] for r in rows], color=col, linewidth=2, marker=mk,
                markersize=6, markeredgecolor=SURFACE, markeredgewidth=1.5, label=label)
    ax.set_xlabel("n (field F_{2^n})", color=INK2, fontsize=10)
    ax.set_yticks(range(0, 4))
    style(ax, "F(2^n) multiplier: Toffoli-depth above the proven optimum (0 = optimal)",
          "excess Toffoli layers")
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "gf2_multiplier.png"), dpi=160)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    p = "results/ibm127/results_recomputed.json"
    if os.path.exists(p):
        res = json.load(open(p))
        fig_depth(res)
        fig_xt(res)
    p = "results/structured/e2.json"
    if os.path.exists(p):
        fig_gf2(json.load(open(p)))
    print("figures written to", OUT)
