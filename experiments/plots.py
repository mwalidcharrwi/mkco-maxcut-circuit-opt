"""Static figures for the report (needs matplotlib; reads JSON results only).

Palette: reference categorical slots in fixed order (blue, orange, aqua,
yellow, magenta, green).  Charts with more than three series are line charts
(adjacent-pair rule) with direct end labels; every figure has a table in
docs/REPORT.md, which also covers the low-contrast slots (relief rule).
"""
import json
import os
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100",
                                              "#e87ba4", "#008300")
SERIES = [BLUE, ORANGE, AQUA, YELLOW, MAGENTA, GREEN]
OUT = "docs/figures"
ORDER = ["mult_8", "add_17", "qae_17", "qft_16", "hubbard_8", "hhl_8", "heisenberg_32",
         "grover_10", "hubbard_18"]


def style(ax, title, ylabel, xlabel=None):
    ax.set_facecolor(SURFACE)
    ax.figure.set_facecolor(SURFACE)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=9)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    if title:
        ax.set_title(title, color=INK, fontsize=12, loc="left", pad=12)
    ax.set_ylabel(ylabel, color=INK2, fontsize=10)
    if xlabel:
        ax.set_xlabel(xlabel, color=INK2, fontsize=10)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, name), dpi=160)
    plt.close(fig)


def load(p):
    return json.load(open(p)) if os.path.exists(p) else None


def grouped_bars(ax, names, series, w=0.26):
    k = len(series)
    for j, (label, vals, col) in enumerate(series):
        xs = [i + (j - (k - 1) / 2) * w for i in range(len(names))]
        ax.bar(xs, vals, width=w, color=col, edgecolor=SURFACE, linewidth=2, label=label)
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, fontsize=8.5, color=INK2)


# --------------------------------------------------------------- IBM figures
def fig_depth(res):
    names = [n for n in ORDER if n in res]
    pct = lambda n, k: 100 * (res[n]["methods"]["original"]["depth"] - res[n]["methods"][k]["depth"]) \
        / res[n]["methods"]["original"]["depth"]  # noqa: E731
    fig, ax = plt.subplots(figsize=(10, 4.2))
    grouped_bars(ax, names, [("Lee et al. 2026 (colouring)", [pct(n, "lee2026") for n in names], ORANGE),
                             ("Jain & Kumar 2026 (MIS + beam)", [pct(n, "jk2026") for n in names], AQUA),
                             ("MKCO (ours)", [pct(n, "mkco") for n in names], BLUE)])
    w = 0.26
    for i, n in enumerate(names):
        m = res[n]["methods"]
        lbv = 100 * (m["original"]["depth"] - m["mkco"]["lower_bound"]) / m["original"]["depth"]
        ax.plot([i - 1.5 * w, i + 1.5 * w], [lbv, lbv], color=INK, linewidth=1.2)
    style(ax, "Depth reduction vs. transpiled input (reorder-only; black line = certified optimum)",
          "depth reduction (%)")
    ax.set_ylim(0, 6.2)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2, loc="upper left", ncol=3)
    ax.text(len(names) - 0.5, 5.75, "Lee et al.: 0% on every circuit", ha="right", fontsize=9, color=INK2)
    save(fig, "ibm127_depth.png")


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
    save(fig, "ibm127_crosstalk.png")


def fig_rewrite(res):
    names = [n for n in ORDER if n in res and "mkco_full" in res[n]["methods"]]
    if not names:
        return
    pct = lambda n, k: 100 * (res[n]["methods"]["original"]["depth"] - res[n]["methods"][k]["depth"]) \
        / res[n]["methods"]["original"]["depth"]  # noqa: E731
    fig, ax = plt.subplots(figsize=(10, 4.4))
    grouped_bars(ax, names, [("MKCO (reorder only, certified optimal)", [pct(n, "mkco") for n in names], AQUA),
                             ("MKCO-rewrite (1q resynthesis + reorder)", [pct(n, "mkco_rewrite") for n in names], ORANGE),
                             ("MKCO-full (+ 2q KAK blocks)", [pct(n, "mkco_full") for n in names], BLUE)])
    ax.axhline(0, color=INK2, linewidth=0.8)
    style(ax, "Depth reduction vs the transpiled input (Qiskit level 3), higher is better",
          "depth reduction (%)")
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2, loc="upper left")
    save(fig, "ibm127_rewrite.png")


def fig_duration(res):
    names = [n for n in ORDER if n in res and "mkco_full_dur" in res[n]["methods"]]
    if not names:
        return
    pct = lambda n, k: 100 * (res[n]["methods"]["original"]["duration_ns"] -  # noqa: E731
                              res[n]["methods"][k]["duration_ns"]) / res[n]["methods"]["original"]["duration_ns"]
    fig, ax = plt.subplots(figsize=(10, 4.2))
    grouped_bars(ax, names, [("MKCO-full, depth objective", [pct(n, "mkco_full") for n in names], AQUA),
                             ("MKCO-full, duration objective", [pct(n, "mkco_full_dur") for n in names], BLUE)],
                 w=0.36)
    ax.axhline(0, color=INK2, linewidth=0.8)
    style(ax, "Estimated execution time saved vs the transpiled input (ECR 533 ns, sx/x 36 ns, rz virtual)",
          "time saved (%)")
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2, loc="upper left")
    save(fig, "ibm127_duration.png")


def fig_pareto(rows):
    by = defaultdict(list)
    for r in rows:
        by[r["circuit"]].append(r)
    fig, ax = plt.subplots(figsize=(10, 4.6))
    for col, (name, rs) in zip(SERIES, by.items()):
        rs.sort(key=lambda r: (r["depth_2q"], r["xt_pairs"]))
        k0 = min(r["depth_2q"] for r in rs)
        base = rs[0]["xt_pairs_original"]
        front, best = [], None          # non-dominated points (time-limited search can be non-monotone)
        for r in rs:
            if best is None or r["xt_pairs"] < best:
                front.append(r)
                best = r["xt_pairs"]
        xs = [100 * (r["depth_2q"] - k0) / k0 for r in front]
        ys = [100 * (base - r["xt_pairs"]) / base for r in front]
        ax.plot(xs, ys, color=col, linewidth=2, marker="o", markersize=6, markeredgecolor=SURFACE,
                markeredgewidth=1.5, label=name)
        ax.text(xs[-1] + 0.15, ys[-1], name, color=INK2, fontsize=8.5, va="center")
    style(ax, "Depth budget vs crosstalk: weighted Max-k-Cut Pareto fronts (non-dominated points)",
          "crosstalk-prone ECR pairs removed (%)", "extra two-qubit depth over the certified optimum (%)")
    ax.legend(frameon=False, fontsize=8.5, labelcolor=INK2, loc="lower right", ncol=2)
    save(fig, "pareto_crosstalk.png")


def fig_runtime(res):
    names = [n for n in ORDER if n in res]
    gates = [res[n]["methods"]["original"]["gates"] for n in names]
    fig, ax = plt.subplots(figsize=(10, 4))
    for label, key, col, mk in (("Lee et al. (block colouring)", "lee2026", ORANGE, "o"),
                                ("Jain & Kumar", "jk2026", AQUA, "s"),
                                ("MKCO (certified)", "mkco", BLUE, "D")):
        ts = [max(res[n]["methods"][key]["time_s"], 0.05) for n in names]
        ax.plot(gates, ts, color=col, linewidth=2, marker=mk, markersize=6, markeredgecolor=SURFACE,
                markeredgewidth=1.5, label=label)
    ax.set_xscale("log")
    ax.set_yscale("log")
    style(ax, "Runtime vs circuit size (reorder-only, depth mode)", "seconds", "gates")
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2, loc="upper left")
    save(fig, "runtime_scaling.png")


# --------------------------------------------------------- structured figures
def fig_gf2(rows):
    rows = [r for r in rows if r["n"] <= 32]
    ns = [r["n"] for r in rows]
    fig, ax = plt.subplots(figsize=(10, 3.8))
    for label, key, col, mk in (("DSatur (Lee et al.)", "dsatur", ORANGE, "o"),
                                ("Jain & Kumar", "jk", AQUA, "s"),
                                ("MKCO (ours)", "mkco", BLUE, "D")):
        ax.plot(ns, [r[key] - r["lb"] for r in rows], color=col, linewidth=2, marker=mk,
                markersize=6, markeredgecolor=SURFACE, markeredgewidth=1.5, label=label)
    ax.set_yticks(range(0, 4))
    style(ax, "F(2^n) multiplier: Toffoli-depth above the proven optimum (0 = optimal)",
          "excess Toffoli layers", "n (field F_{2^n})")
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2)
    save(fig, "gf2_multiplier.png")


def fig_e1(rows, theta):
    lbx = {}
    for t in theta or []:                       # theta and theta-plus certificates
        if t["experiment"] == "e1":
            k = (t["m"], t["n"], t["seed"])
            lbx[k] = max(lbx.get(k, 0), t["lb"])
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), sharey=True)
    for ax, m in zip(axes, (10, 20, 30)):
        g = defaultdict(list)
        for r in rows:
            if r["m"] == m:
                lb = lbx.get((r["m"], r["n"], r["seed"]), r["lb"])
                g[r["n"]].append((r["dsatur"] - lb, r["jk"] - lb, r["mkco"] - lb))
        ns = sorted(g)
        for j, (label, col, mk) in enumerate((("DSatur (Lee)", ORANGE, "o"), ("Jain & Kumar", AQUA, "s"),
                                               ("MKCO", BLUE, "D"))):
            ax.plot(ns, [sum(x[j] for x in g[n]) / len(g[n]) for n in ns], color=col, linewidth=2,
                    marker=mk, markersize=6, markeredgecolor=SURFACE, markeredgewidth=1.5, label=label)
        style(ax, f"m = {m} qubits", "mean layers above certified LB" if m == 10 else "", "gates n")
    axes[0].legend(frameon=False, fontsize=9, labelcolor=INK2)
    fig.suptitle("Random multi-controlled-Z circuits (Lee et al. Sec. 4.3 setting)", x=0.01, ha="left",
                 color=INK, fontsize=12)
    save(fig, "e1_random_mcz.png")


def fig_e3(rows):
    g = defaultdict(list)
    for r in rows:
        g[r["gates"]].append(r)
    ns = sorted(g)
    fig, ax = plt.subplots(figsize=(10, 3.8))
    for label, key, col, mk in (("DSatur (Lee)", "dsatur", ORANGE, "o"), ("Jain & Kumar", "jk", AQUA, "s"),
                                ("MKCO", "mkco", BLUE, "D")):
        ax.plot(ns, [sum(r[key] - r["lb"] for r in g[n]) / len(g[n]) for n in ns], color=col,
                linewidth=2, marker=mk, markersize=6, markeredgecolor=SURFACE, markeredgewidth=1.5,
                label=label)
    style(ax, "Random CCZ circuits on 10 qubits (Lee et al. App. C): layers above certified LB",
          "mean excess layers", "CCZ gates")
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2)
    save(fig, "e3_ccz.png")


def fig_e4(rows):
    g = defaultdict(list)
    for r in rows:
        g[(r["qubits"], r["degree"])].append(r)
    keys = sorted(g)
    names = [f"n={q}, d={d}" for q, d in keys]
    fig, ax = plt.subplots(figsize=(10, 3.8))
    grouped_bars(ax, names, [(lbl, [sum(r[k] - r["lb"] for r in g[c]) / len(g[c]) for c in keys], col)
                             for lbl, k, col in (("DSatur (Lee)", "dsatur", ORANGE),
                                                 ("Jain & Kumar", "jk", AQUA), ("MKCO", "mkco", BLUE))])
    style(ax, "Commuting RZZ layers (QAOA cost layer): layers above the degree bound (0 = optimal)",
          "mean excess layers")
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2, loc="upper left")
    save(fig, "e4_rzz.png")


def fig_e6(rows):
    cases = ["mcz_m20_n120", "ccz_m10_n80", "draper_16_core"]
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    for ax, case in zip(axes, cases):
        rs = sorted([r for r in rows if r["case"] == case], key=lambda r: r["qubits"])
        q = [r["qubits"] for r in rs]
        ax.plot(q, [r["baseline_total"] for r in rs], color=ORANGE, linewidth=2, marker="o",
                markersize=6, markeredgecolor=SURFACE, markeredgewidth=1.5, label="fixed split + DSatur")
        ax.plot(q, [r["mkco_total"] for r in rs], color=BLUE, linewidth=2, marker="D",
                markersize=6, markeredgecolor=SURFACE, markeredgewidth=1.5, label="capacitated Max-k-Cut")
        style(ax, case, "depth incl. fan-out" if case == cases[0] else "", "total qubits")
    axes[0].legend(frameon=False, fontsize=9, labelcolor=INK2)
    fig.suptitle("Depth/qubit trade-offs by ancilla fan-out (Lee et al. Sec. 5.2 made precise)", x=0.01,
                 ha="left", color=INK, fontsize=12)
    save(fig, "e6_fanout.png")


def fig_tdepth(rows):
    rows = [r for r in rows if r["kind"] == "t" and "pyzx_full" in r]
    if not rows:
        return
    names = [r["circuit"].replace("_ct", "").replace("rand_cliffT", "cliffT") for r in rows]
    fig, ax = plt.subplots(figsize=(11, 4.4))
    grouped_bars(ax, names, [("MKCO-T on the input", [r["mkco_t"]["depth_nc"] for r in rows], AQUA),
                             ("PyZX (full_reduce + extract)", [r["pyzx_full"]["depth_nc"] for r in rows], ORANGE),
                             ("PyZX + MKCO-T (certified)", [r["pyzx_full+mkco_t"]["depth_nc"] for r in rows], BLUE)])
    ax.set_xticklabels(names, fontsize=8, color=INK2, rotation=35, ha="right")
    style(ax, "T-depth with free Cliffords (lower is better)", "T-depth")
    top = max(max(r["mkco_t"]["depth_nc"], r["pyzx_full"]["depth_nc"]) for r in rows)
    ax.set_ylim(0, top * 1.28)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2, loc="upper left", ncol=3)
    save(fig, "tdepth.png")


def fig_routing(rows):
    if not rows:
        return
    names = [r["circuit"].replace("_d3", "").replace("trotter_reg3", "trotter") for r in rows]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.2), sharey=False)
    for ax, key, title in ((axes[0], "cx", "CNOTs vs Qiskit O3 (%)"), (axes[1], "depth", "depth vs Qiskit O3 (%)")):
        pct = lambda r, m: 100 * (r[m][key] - r["qiskit_o3"][key]) / r["qiskit_o3"][key]  # noqa: E731
        series = [("MKCO-route (commutation-aware front)", [pct(r, "mkco_route") for r in rows], BLUE)]
        if all("sabre_dag" in r for r in rows):
            series.append(("ablation: same router, DAG front", [pct(r, "sabre_dag") for r in rows], AQUA))
        grouped_bars(ax, names, series, w=0.36)
        ax.set_xticklabels(names, fontsize=8, color=INK2, rotation=40, ha="right")
        ax.axhline(0, color=INK2, linewidth=0.8)
        style(ax, title, "change (%) — below 0 is better")
    axes[0].legend(frameon=False, fontsize=8.5, labelcolor=INK2, loc="upper left")
    fig.suptitle("Routing on the 127-qubit heavy-hex device", x=0.01, ha="left", color=INK, fontsize=12)
    save(fig, "routing.png")


def fig_noise(nz):
    if not nz:
        return
    pts = {"ESP (state-blind)": [], "state-aware ESP": []}
    for name, cr in nz["circuits"].items():
        if not cr["simulated"]:
            continue
        ms = cr["methods"]
        f0 = ms["original"]["sim_scale0.1"]["state_fidelity"]
        e0 = ms["original"]["esp_scale0.1"]
        s0 = ms["original"]["sesp_scale0.1"]
        for m, r in ms.items():
            if m in ("original", "mkco_noise") or "sim_scale0.1" not in r:
                continue
            x = r["sim_scale0.1"]["state_fidelity"] / f0
            pts["ESP (state-blind)"].append((x, r["esp_scale0.1"] / e0))
            pts["state-aware ESP"].append((x, r["sesp_scale0.1"] / s0))
    if not pts["state-aware ESP"]:
        return
    fig, ax = plt.subplots(figsize=(6.4, 5.2))
    xs = [p[0] for v in pts.values() for p in v]
    lo, hi = min(xs + [p[1] for v in pts.values() for p in v]) - 0.01, max(xs + [p[1] for v in pts.values() for p in v]) + 0.01
    ax.plot([lo, hi], [lo, hi], color=GRID, linewidth=1.5, zorder=1)
    for (label, v), col in zip(pts.items(), (ORANGE, BLUE)):
        ax.scatter([p[0] for p in v], [p[1] for p in v], s=46, color=col, edgecolor=SURFACE,
                   linewidth=1.5, label=label, zorder=3)
    style(ax, "Predicted vs simulated fidelity, relative to the input order",
          "predicted / predicted(input)", "density-matrix fidelity / fidelity(input)")
    ax.legend(frameon=False, fontsize=9, labelcolor=INK2, loc="upper left")
    save(fig, "noise_validation.png")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    res = load("results/ibm127/results_recomputed.json")
    if res:
        fig_depth(res)
        fig_xt(res)
        fig_rewrite(res)
        fig_duration(res)
        fig_runtime(res)
    pareto = load("results/ibm127/pareto.json")
    if pareto:
        fig_pareto(pareto)
    S = "results/structured"
    if load(f"{S}/e2.json"):
        fig_gf2(load(f"{S}/e2.json"))
    if load(f"{S}/e1.json"):
        fig_e1(load(f"{S}/e1.json"), (load(f"{S}/theta.json") or []) + (load(f"{S}/theta_plus.json") or []))
    if load(f"{S}/e3.json"):
        fig_e3(load(f"{S}/e3.json"))
    if load(f"{S}/e4.json"):
        fig_e4(load(f"{S}/e4.json"))
    if load(f"{S}/e6.json"):
        fig_e6(load(f"{S}/e6.json"))
    if load(f"{S}/tdepth.json"):
        fig_tdepth(load(f"{S}/tdepth.json"))
    if load(f"{S}/routing.json"):
        fig_routing(load(f"{S}/routing.json"))
    fig_noise(load("results/ibm127/noise.json"))
    print("figures written to", OUT, sorted(os.listdir(OUT)))
