"""Figures made for the paper package (paper/figures), in addition to docs/figures.

  fig1_framework        workflow of the MKCO framework
  fig2_example          worked example: circuit -> mixed graph -> optimal layering
  fig3_certified        share of instances solved to proven optimality, per method
  fig4_ibm_overview     depth reduction on all 13 IBM-127 benchmarks
  fig5_noise_selection  fidelity of MKCO orders relative to the input (noise-aware selection)
  fig6_crosstalk_budget crosstalk pairs removed under a two-qubit-depth budget, both IBM sets
  fig7_capabilities     capability matrix vs Lee et al. and Jain & Kumar
  fig8_theory_map       dependency map of the lemmas, theorems and propositions

Run from the repository root:  python paper/make_figures.py
"""
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "experiments"))

from plots import AQUA, BLUE, GREEN, GRID, INK, INK2, MAGENTA, ORANGE, SURFACE, YELLOW, grouped_bars, style  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "figures")


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=200, facecolor=SURFACE)
    fig.savefig(os.path.join(OUT, name + ".pdf"), facecolor=SURFACE)
    plt.close(fig)


# ---------------------------------------------------------------- Figure 1
def box(ax, x, y, w, h, title, body="", fc="#ffffff", ec=GRID, title_color=INK, lw=1.2, fs=8.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h - 0.13, title, ha="center", va="top", fontsize=fs + 0.6,
            color=title_color, weight="bold")
    if body:
        ax.text(x + w / 2, y + h - 0.47, body, ha="center", va="top", fontsize=fs, color=INK2,
                linespacing=1.35)


def arrow(ax, p, q, color=INK2, style="-|>", ls="-", lw=1.4, rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=12, color=color,
                                 lw=lw, linestyle=ls, connectionstyle=f"arc3,rad={rad}"))


def fig_framework():
    fig, ax = plt.subplots(figsize=(15.5, 8.0))
    fig.set_facecolor(SURFACE)
    ax.set_xlim(0, 15.5)
    ax.set_ylim(0.2, 8.4)
    ax.axis("off")
    tint = {"core": "#e9f1fb", "bound": "#e8f6ef", "opt": "#fdf0e9", "ext": "#fbf3df", "noise": "#fbeaf1"}
    y, h = 3.4, 2.15
    cols = [(0.15, 1.75), (2.2, 2.45), (4.95, 2.75), (8.0, 3.65), (11.95, 1.95), (14.2, 1.2)]
    (x0, w0), (x1, w1), (x2, w2), (x3, w3), (x4, w4), (x5, w5) = cols
    box(ax, x0, y, w0, h, "Input", "OpenQASM 2.0\ntranspiled (IBM-127)\nor logical", fc="#ffffff")
    box(ax, x1, y, w1, h, "① Commutation\n    analysis",
        "\nper-qubit commutation\naxes → runs of mutually\ncommuting gates per wire\n(Lemmas 1–2)",
        fc=tint["core"], ec=BLUE)
    box(ax, x2, y, w2, h, "② Mixed graph",
        "precedence arcs between runs\n+ conflict edges within runs\nmin depth = mixed chromatic\nnumber (Thm 1); O(Σ arity)",
        fc=tint["core"], ec=BLUE)
    box(ax, x3, y, w3, h, "③ Weighted Max-k-Cut engine",
        "k layers exist ⇔ the cut keeps\nevery hard edge (Thm 2)\nwarm starts: list scheduling, DSatur\ntabu k-descent · window LNS\nhierarchical Max-Cut: SA, GW-SDP, QAOA\n(Thm 4, Prop 6)",
        fc=tint["core"], ec=BLUE)
    box(ax, x4, y, w4, h, "④ Emit + verify", "linear extension\ncommutation audit\nstate-vector check\n(≤ 20 qubits)",
        fc=tint["core"], ec=BLUE)
    box(ax, x5, y, w5, h, "Output", "layered\ncircuit\n+ optimality\ncertificate", fc="#ffffff")
    for (xa, wa), (xb, _) in zip(cols, cols[1:]):
        arrow(ax, (xa + wa, y + h / 2), (xb, y + h / 2), color=BLUE)
    # bounds (bottom)
    box(ax, x2, 0.55, 6.7, 1.55, "Certified lower bounds",
        "run-serialised Jackson bound (Thm 7) · clique bound\nLovász θ / Szegedy θ⁺ SDP with exact feasible repair (Prop 9)\nlayers = bound  ⇒  provably optimal",
        fc=tint["bound"], ec=GREEN)
    arrow(ax, (x2 + 1.3, y), (x2 + 1.3, 2.1), color=GREEN)
    arrow(ax, (x2 + 6.7, 1.45), (x4 + w4 / 2, y), color=GREEN, rad=0.3)
    ax.text(x4 + 0.35, 2.15, "certificate", fontsize=8.5, color=GREEN, ha="center")
    # top row
    top, th = 6.05, 1.55
    box(ax, 0.15, top, 4.5, th, "Optional gate rewriting (pre-pass)",
        "1q ZSX resynthesis + run-based rotation merging\n2q KAK blocks in native ECR direction (exact check)\ncommutation-aware block formation (regroup)",
        fc=tint["ext"], ec=YELLOW)
    arrow(ax, (2.4, top), (x1 + w1 / 2, y + h), color=YELLOW)
    box(ax, x3, top, w3, th, "Objectives & hardware terms",
        "depth · 2q-depth · estimated duration\nnon-Clifford depth: T / Toffoli (Prop 10)\nsoft edges: crosstalk · depth budget k* + s\ncapacities: ancilla fan-out",
        fc=tint["opt"], ec=ORANGE)
    arrow(ax, (x3 + w3 / 2, top), (x3 + w3 / 2, y + h), color=ORANGE)
    box(ax, x4 - 0.15, top, 15.35 - x4 + 0.15, th, "Device-level modules",
        "routing: SABRE with trace-order\nfront, exact unroute check (Prop 11)\nnoise-aware selection: state-aware\nESP from calibration (Prop 12)",
        fc=tint["noise"], ec=MAGENTA)
    arrow(ax, (x4 + w4 / 2, top), (x4 + w4 / 2, y + h), color=MAGENTA)
    ax.text(0.15, 8.25, "MKCO: quantum circuit optimisation by precedence-constrained weighted Max-k-Cut",
            fontsize=13, color=INK, weight="bold", va="top")
    save(fig, "fig1_framework")


# ---------------------------------------------------------------- Figure 2
EXAMPLE = [("cx", (3, 1)), ("cx", (1, 2)), ("cx", (0, 2)), ("cz", (0, 1)), ("h", (2,)),
           ("cx", (0, 3)), ("rz", (3,))]
INPUT_LAYER = [0, 1, 2, 3, 3, 4, 5]          # ASAP layers of the input order (depth 6)
OPT_LAYER = [0, 1, 0, 2, 2, 1, 2]            # MKCO layering (depth 3, certified optimal)
LAYER_COL = [BLUE, ORANGE, AQUA]


def _place(layers):
    """x position per gate: gates of one layer whose qubit spans overlap get side-by-side slots."""
    xs, width = [], {}
    used = {}
    for (nm, qs), lay in zip(EXAMPLE, layers):
        lo, hi = min(qs), max(qs)
        slot = 0
        while any(not (hi < a or lo > b) for a, b in used.get((lay, slot), [])):
            slot += 1
        used.setdefault((lay, slot), []).append((lo, hi))
        width[lay] = max(width.get(lay, 0), slot)
        xs.append((lay, slot))
    starts, x = {}, 0.0
    for lay in sorted(width):
        starts[lay] = x
        x += 1.0 + 0.55 * width[lay]
    return [starts[lay] + 0.55 * slot for lay, slot in xs], starts, x


def draw_circuit(ax, layers, colours, title, bands=False):
    xs, starts, end = _place(layers)
    if bands:
        for lay, x0 in starts.items():
            w = (max(x for x, la in zip(xs, layers) if la == lay) - x0) + 0.8
            ax.add_patch(FancyBboxPatch((x0 - 0.4, -0.55), w, 4.05, boxstyle="round,pad=0.0,rounding_size=0.1",
                                        fc=LAYER_COL[lay], alpha=0.07, ec="none", zorder=0))
            ax.text(x0 - 0.4 + w / 2, 3.75, f"layer {lay + 1}", ha="center", fontsize=8.5, color=INK2)
    for q in range(4):
        ax.plot([-0.6, end - 0.4], [q, q], color=GRID, lw=1.4, zorder=1)
        ax.text(-0.85, q, f"q{q}", ha="right", va="center", fontsize=9, color=INK2)
    for i, ((nm, qs), x) in enumerate(zip(EXAMPLE, xs)):
        col = colours[i]
        if nm in ("cx", "cz"):
            a, b = qs
            ax.plot([x, x], [a, b], color=col, lw=2, zorder=2)
            ax.scatter([x], [a], s=55, color=col, zorder=3)
            if nm == "cx":
                ax.scatter([x], [b], s=260, facecolor=SURFACE, edgecolor=col, lw=2, zorder=3)
                ax.plot([x - 0.13, x + 0.13], [b, b], color=col, lw=1.6, zorder=4)
                ax.plot([x, x], [b - 0.17, b + 0.17], color=col, lw=1.6, zorder=4)
            else:
                ax.scatter([x], [b], s=55, color=col, zorder=3)
        else:
            q = qs[0]
            ax.add_patch(FancyBboxPatch((x - 0.27, q - 0.24), 0.54, 0.48, boxstyle="round,pad=0.01",
                                        fc=SURFACE, ec=col, lw=2, zorder=3))
            ax.text(x, q, "H" if nm == "h" else "Rz", ha="center", va="center", fontsize=8.5, color=INK, zorder=4)
        top = min(qs)
        ax.text(x, top - 0.38, f"g{i + 1}", ha="center", fontsize=8, color=INK2, zorder=5)
    ax.set_xlim(-1.2, end)
    ax.set_ylim(4.1, -0.8)
    ax.axis("off")
    ax.set_title(title, fontsize=10.5, color=INK, loc="left")


def fig_example():
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 4.6), gridspec_kw={"width_ratios": [1.35, 1.05, 1.15]})
    fig.set_facecolor(SURFACE)
    draw_circuit(axes[0], INPUT_LAYER, [INK2] * 7, "(a) Input order: depth 6\n(Lee et al.'s block colouring: still 6)")
    ax = axes[1]
    pos = {0: (0.0, 1.0), 1: (1.0, 2.0), 2: (1.0, 0.0), 3: (2.0, 1.0), 4: (2.0, 2.6), 5: (1.0, -1.0), 6: (2.0, -1.0)}
    arcs = [(0, 1), (0, 3), (0, 5), (1, 4), (2, 4), (5, 6)]
    edges = [(1, 3), (1, 2), (2, 3), (2, 5), (3, 5)]
    for a, b in edges:
        ax.plot([pos[a][0], pos[b][0]], [pos[a][1], pos[b][1]], color=ORANGE, lw=1.8, ls="--", zorder=1)
    for a, b in arcs:
        ax.add_patch(FancyArrowPatch(pos[a], pos[b], arrowstyle="-|>", mutation_scale=13, color=INK2, lw=1.4,
                                     shrinkA=13, shrinkB=13, zorder=2))
    for i, (x, y) in pos.items():
        ax.scatter([x], [y], s=650, color=LAYER_COL[OPT_LAYER[i]], zorder=3, edgecolor=SURFACE, lw=2)
        ax.text(x, y, f"g{i + 1}", ha="center", va="center", fontsize=9, color="white", weight="bold", zorder=4)
    ax.plot([], [], color=INK2, lw=1.4, label="precedence arc (order kept)")
    ax.plot([], [], color=ORANGE, lw=1.8, ls="--", label="conflict edge (commute, share a qubit)")
    ax.legend(frameon=False, fontsize=8, labelcolor=INK2, loc="lower center", bbox_to_anchor=(0.5, -0.22), ncol=1)
    ax.set_xlim(-0.6, 2.6)
    ax.set_ylim(-1.6, 3.2)
    ax.axis("off")
    ax.set_title("(b) Mixed graph from commutation runs;\ncolours = layers of a 3-colouring", fontsize=10.5, color=INK, loc="left")
    draw_circuit(axes[2], OPT_LAYER, [LAYER_COL[x] for x in OPT_LAYER],
                 "(c) MKCO layering: depth 3\n(= lower bound: certified optimal)", bands=True)
    fig.tight_layout()
    save(fig, "fig2_example")


# ---------------------------------------------------------------- Figure 3
def fig_certified():
    groups = ["Random multi-\ncontrolled-Z\n(60)", "F₂ⁿ multiplier\n(34 sizes)", "Random CCZ\n(50)",
              "RZZ / QAOA\nlayers (18)", "IBM-127\nset 1 (9)", "IBM-127\nset 2 (4)"]
    lee = [42 / 60, 24 / 34, 20 / 50, 0 / 18, 0 / 9, 0 / 4]
    jk = [0 / 60, 7 / 34, 17 / 50, 0 / 18, 0 / 9, 0 / 4]
    mk = [48 / 60, 34 / 34, 49 / 50, 14 / 18, 9 / 9, 4 / 4]
    fig, ax = plt.subplots(figsize=(11, 4.4))
    grouped_bars(ax, groups, [("Lee et al. 2026 (DSatur / block colouring)", [100 * v for v in lee], ORANGE),
                              ("Jain & Kumar 2026", [100 * v for v in jk], AQUA),
                              ("MKCO (ours)", [100 * v for v in mk], BLUE)])
    for i, v in enumerate(mk):
        ax.text(i + 0.26, 100 * v + 1.5, f"{100 * v:.0f}%", ha="center", fontsize=8, color=INK)
    ax.set_ylim(0, 128)
    ax.set_yticks([0, 20, 40, 60, 80, 100])
    style(ax, "Instances solved to proven optimality (higher is better)",
          "share of instances (%)")
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2, loc="upper left", ncol=3)
    ax.text(0.99, -0.27, "IBM sets: only MKCO issues a proof (Lee and JK reach no / equal depth without a certificate). "
            "RZZ: reaching the degree bound Δ.", transform=ax.transAxes, ha="right", fontsize=7.5, color=INK2)
    fig.tight_layout()
    save(fig, "fig3_certified")


# ---------------------------------------------------------------- Figure 4
def fig_ibm_overview():
    rows = []
    for d in ("results/ibm127", "results/ibm127_set2"):
        res = json.load(open(os.path.join(d, "results_recomputed.json")))
        for n, r in res.items():
            M = r["methods"]
            o = M["original"]["depth"]
            rows.append((n, *(100 * (o - M[k]["depth"]) / o for k in ("lee2026", "jk2026", "mkco", "mkco_full"))))
    rows.sort(key=lambda r: r[4])
    names = [r[0] for r in rows]
    fig, ax = plt.subplots(figsize=(13, 4.6))
    grouped_bars(ax, names, [("Lee et al. 2026", [r[1] for r in rows], ORANGE),
                             ("Jain & Kumar 2026", [r[2] for r in rows], AQUA),
                             ("MKCO reorder (certified optimal)", [r[3] for r in rows], BLUE),
                             ("MKCO-full (+ gate rewriting)", [r[4] for r in rows], YELLOW)], w=0.2)
    ax.set_xticklabels(names, fontsize=8, color=INK2, rotation=30, ha="right")
    ax.set_yscale("symlog", linthresh=5)
    ax.set_yticks([0, 1, 2, 3, 5, 10, 20, 50])
    ax.set_yticklabels(["0", "1", "2", "3", "5", "10", "20", "50"])
    style(ax, "Depth reduction vs the transpiled input on all 13 IBM-127 benchmarks (higher is better)",
          "depth reduction (%, symlog)")
    ax.legend(frameon=False, fontsize=8.5, labelcolor=INK2, loc="upper left", ncol=4)
    fig.tight_layout()
    save(fig, "fig4_ibm_overview")


# ---------------------------------------------------------------- Figure 5
def fig_noise_selection():
    rows = []
    for d in ("results/ibm127", "results/ibm127_set2"):
        nz = json.load(open(os.path.join(d, "noise.json")))["circuits"]
        for n, cr in nz.items():
            if not cr["simulated"]:
                continue
            ms = cr["methods"]
            f = lambda m: ms[m]["sim_scale0.1"]["state_fidelity"]  # noqa: E731
            base = f("original")
            rows.append((n, *(100 * (f(m) / base - 1) for m in ("mkco", "mkco_alap", "mkco_noise"))))
    names = [r[0] for r in rows]
    fig, ax = plt.subplots(figsize=(11, 4.4))
    grouped_bars(ax, names, [("MKCO, depth only", [r[1] for r in rows], ORANGE),
                             ("MKCO, ALAP placement", [r[2] for r in rows], AQUA),
                             ("MKCO, noise-aware selection", [r[3] for r in rows], BLUE)])
    ax.axhline(0, color=INK2, linewidth=0.9)
    style(ax, "Simulated state fidelity relative to the input order (10x lower noise, device calibration)",
          "fidelity change (%)")
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2, loc="upper left")
    ax.text(0.99, -0.16, "Exact density-matrix simulation; idle noise depends on the state a qubit waits in. "
            "Noise-aware selection never falls below the input.", transform=ax.transAxes, ha="right",
            fontsize=7.5, color=INK2)
    fig.tight_layout()
    save(fig, "fig5_noise_selection")


# ---------------------------------------------------------------- Figure 6
def fig_pareto_budget():
    rows = []
    for d in ("results/ibm127", "results/ibm127_set2"):
        by = {}
        for r in json.load(open(os.path.join(d, "pareto.json"))):
            by.setdefault(r["circuit"], {})[r["slack_pct"]] = 100 * (1 - r["xt_pairs"] / r["xt_pairs_original"])
        rows += [(n, v[0], v[10], v[20]) for n, v in by.items()]
    names = [r[0] for r in rows]
    fig, ax = plt.subplots(figsize=(12, 4.4))
    grouped_bars(ax, names, [("at the optimal 2q-depth", [r[1] for r in rows], "#9ec5f2"),
                             ("2q-depth budget +10%", [r[2] for r in rows], BLUE),
                             ("2q-depth budget +20%", [r[3] for r in rows], "#174a8b")])
    for i, r in enumerate(rows):
        ax.text(i + 0.26, r[3] + 1.2, f"{r[3]:.0f}", ha="center", fontsize=7.5, color=INK)
        if r[1] == 0:
            ax.text(i - 0.26, 0.8, "0", ha="center", fontsize=7.5, color=INK2)
    ax.set_xticklabels(names, fontsize=8.5, color=INK2, rotation=20, ha="right")
    ax.set_ylim(0, 78)
    style(ax, "Crosstalk-prone ECR pairs removed by weighted Max-k-Cut under a depth budget (higher is better)",
          "pairs removed vs input (%)")
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2, loc="upper right", ncol=3)
    ax.text(0.99, -0.3, "k = k* + slack, k* = certified optimal two-qubit depth; same-layer ECRs on neighbouring "
            "couplers count as one crosstalk-prone pair. 10 IBM-127 circuits with a Pareto study.",
            transform=ax.transAxes, ha="right", fontsize=7.5, color=INK2)
    fig.tight_layout()
    save(fig, "fig6_crosstalk_budget")


# ---------------------------------------------------------------- Figure 7
CAPABILITIES = [
    ("Commuting circuits", "yes", "yes", "yes"),
    ("Non-commuting circuits", "no", "yes", "yes"),
    ("Exact reduction for general circuits", "no", "no", "yes (Thm 1)"),
    ("Certified lower bound / optimality proof", "partial (Eq. 2)", "no", "yes (Thm 7, Prop 9)"),
    ("Depth budget and soft constraints (crosstalk)", "no", "no", "yes (Thm 2)"),
    ("Capacities (ancilla fan-out)", "heuristic", "no", "yes (capacitated cut)"),
    ("Quantum-native solver path (Ising)", "no", "no", "yes (Thm 4, Prop 6)"),
    ("Memory without an O(n²) conflict graph", "no", "no", "yes"),
    ("Independent equivalence audit", "no", "no", "yes"),
    ("Non-Clifford depth with free Cliffords", "partial (commuting)", "no", "yes (Prop 10)"),
    ("Commutation-aware routing", "no", "no", "yes (Prop 11)"),
    ("State-aware idle-noise scoring", "no", "no", "yes (Prop 12)"),
]


def fig_capabilities():
    cols = ["Lee et al. 2026", "Jain & Kumar 2026", "MKCO (ours)"]
    fig, ax = plt.subplots(figsize=(11, 5.6))
    fig.set_facecolor(SURFACE)
    n = len(CAPABILITIES)
    ax.set_xlim(0, 11)
    ax.set_ylim(-0.2, n + 1.1)
    ax.axis("off")
    x0, cw = 4.4, 2.15
    fill = {"yes": "#dbe9fa", "partial": "#fbefd0", "heuristic": "#fbefd0", "no": SURFACE}
    for j, c in enumerate(cols):
        ax.text(x0 + j * cw + cw / 2, n + 0.45, c, ha="center", va="center", fontsize=10, color=INK,
                weight="bold")
    for i, (cap, *cells) in enumerate(CAPABILITIES):
        y = n - 1 - i
        ax.text(0.05, y + 0.45, cap, ha="left", va="center", fontsize=9.2, color=INK)
        for j, v in enumerate(cells):
            kind = v.split()[0]
            ax.add_patch(FancyBboxPatch((x0 + j * cw + 0.06, y + 0.08), cw - 0.12, 0.74,
                                        boxstyle="round,pad=0,rounding_size=0.06", fc=fill[kind], ec=GRID, lw=0.8))
            label = {"yes": "✓", "no": "–"}.get(kind, kind)
            rest = v[len(kind):].strip()
            text = label + (" " + rest if rest else "")
            ax.text(x0 + j * cw + cw / 2, y + 0.45, text, ha="center", va="center", fontsize=8.6,
                    color=INK if kind != "no" else INK2)
    ax.set_title("Capabilities compared with the graph-colouring line of work", fontsize=12, color=INK, loc="left")
    fig.tight_layout()
    save(fig, "fig7_capabilities")


# ---------------------------------------------------------------- Figure 8
def fig_theory_map():
    fig, ax = plt.subplots(figsize=(16, 7.2))
    fig.set_facecolor(SURFACE)
    ax.set_xlim(0, 15.8)
    ax.set_ylim(0.1, 7.6)
    ax.axis("off")
    tint = {"core": "#e9f1fb", "solve": "#fdf0e9", "cert": "#e8f6ef", "ext": "#fbf3df", "noise": "#fbeaf1",
            "audit": "#f1f0ed"}
    H = 1.35
    main = {"L1": (0.2, "Lemma 1 · axis rule", "gates commute when they share\na Bloch axis on every common qubit"),
            "L2": (3.4, "Lemma 2 · trace order", "runs per wire give ≺; every linear\nextension is equivalent"),
            "T1": (6.6, "Theorem 1 · exact reduction", "minimum depth = mixed chromatic\nnumber χ(M) of arcs ≺ + edges"),
            "T2": (9.8, "Theorem 2 · Max-k-Cut", "k layers exist ⇔ the precedence-\nconstrained weighted cut is total")}
    ym = 3.2
    for k, (x, t, b) in main.items():
        box(ax, x, ym, 2.75, H, t, b, fc=tint["core"], fs=8.2)
    for a, b in (("L1", "L2"), ("L2", "T1"), ("T1", "T2")):
        arrow(ax, (main[a][0] + 2.75, ym + H / 2), (main[b][0], ym + H / 2))
    solve = [(6.6, "Prop 3 · repair", "near-feasible cut ⇒\nnear-optimal depth"),
             (8.95, "Thm 4 · Cor 5", "bisection = per-wire\nload balancing (Ising)"),
             (11.3, "Prop 6 · log encoding", "n⌈log₂K⌉ spins:\nQAOA / annealer ready"),
             (13.65, "Prop 8 · windows", "isolated small\nMax-k-Cuts (LNS)")]
    ys = 5.85
    for x, t, b in solve:
        box(ax, x, ys, 2.05, H, t, b, fc=tint["solve"], fs=8.0)
        arrow(ax, (main["T2"][0] + 1.375, ym + H), (x + 1.025, ys), lw=1.1)
    low = [(0.2, "Corollary · audit", "check only inverted pairs:\n[A, B] = 0 numerically", "audit", "L2"),
           (2.8, "Prop 11 · routing", "front layer from runs;\nexact unroute check", "ext", "L2"),
           (5.4, "Prop 10 · T-depth", "counted depth with free\nCliffords = mixed colouring", "ext", "L2"),
           (8.0, "Theorem 7 · bound", "run-serialised Jackson\nbound ⇒ certificate", "cert", "T1"),
           (10.6, "Prop 9 · θ and θ⁺", "SDP bound with exact,\nsolver-independent repair", "cert", "T1"),
           (13.2, "Prop 12 · idle noise", "fidelity loss depends on\nthe state a qubit waits in", "noise", None)]
    yl = 0.45
    for x, t, b, kind, src in low:
        box(ax, x, yl, 2.4, H, t, b, fc=tint[kind], fs=8.0)
        if src:
            arrow(ax, (main[src][0] + 1.375, ym), (x + 1.2, yl + H), lw=1.1)
    arrow(ax, (main["T1"][0] + 1.375, ym), (5.4 + 1.2, yl + H), lw=1.1)
    ax.text(13.2 + 1.2, yl + H + 0.18, "scores the emitted schedule", ha="center", fontsize=7.8, color=INK2,
            style="italic")
    for i, (kind, label) in enumerate((("core", "core reduction"), ("solve", "solvers"), ("cert", "certificates"),
                                       ("ext", "extensions"), ("noise", "noise"), ("audit", "verification"))):
        x, y = 0.25 + (i % 3) * 1.95, 6.55 - (i // 3) * 0.45
        ax.add_patch(FancyBboxPatch((x, y), 0.3, 0.26, boxstyle="round,pad=0,rounding_size=0.05",
                                    fc=tint[kind], ec=GRID))
        ax.text(x + 0.4, y + 0.13, label, va="center", fontsize=8.5, color=INK2)
    ax.text(0.2, 7.3, "Dependency map of the theory", fontsize=12, color=INK, va="center")
    ax.text(0.2, 6.98, "statements and proofs: supplement/THEORY.md", fontsize=8.5, color=INK2, va="center")
    fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
    save(fig, "fig8_theory_map")


if __name__ == "__main__":
    fig_framework()
    fig_example()
    fig_certified()
    fig_ibm_overview()
    fig_noise_selection()
    fig_pareto_budget()
    fig_capabilities()
    fig_theory_map()
    print("figures written to", OUT, sorted(os.listdir(OUT)))
