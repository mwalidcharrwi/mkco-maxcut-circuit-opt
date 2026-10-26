"""Build the paper package: key tables from the result files, the results
digest (from digest_template.md), and copies of figures and supplements.

Run from the repository root:  python paper/build_package.py
Then (optional) zip:           the script also writes paper/mkco_paper_package.zip
"""
import csv
import json
import os
import shutil
import zipfile

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
P = os.path.join(ROOT, "paper")
T = os.path.join(P, "tables")
ORDER = ["mult_8", "add_17", "qae_17", "qft_16", "hubbard_8", "hhl_8", "heisenberg_32", "grover_10",
         "hubbard_18", "tfim_8", "heisenberg_8", "qpe_8", "tfim_7_40"]
SETS = (("results/ibm127", "set 1"), ("results/ibm127_set2", "set 2"))


def load(p):
    return json.load(open(os.path.join(ROOT, p)))


def pct(a, b):
    return f"{100 * (a - b) / b:+.1f}%"


def write_csv(name, rows):
    with open(os.path.join(T, name), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


# ------------------------------------------------------------------ tables
def table_ibm():
    rows = []
    for d, tag in SETS:
        for n, r in load(f"{d}/results_recomputed.json").items():
            M = r["methods"]
            o = M["original"]
            rows.append({
                "set": tag, "circuit": n, "active_qubits": r["qubits_active"], "gates": o["gates"], "ecr": o["ecr"],
                "depth_original": o["depth"], "depth_lee2026": M["lee2026"]["depth"],
                "depth_jk2026": M["jk2026"]["depth"], "depth_mkco": M["mkco"]["depth"],
                "depth_lower_bound": M["mkco"]["lower_bound"], "mkco_certified": M["mkco"]["certified_optimal"],
                "depth2q_original": o["depth_2q"], "depth2q_jk2026": M["jk2026_2q"]["depth_2q"],
                "depth2q_mkco": M["mkco_2q"]["depth_2q"], "depth2q_lower_bound": M["mkco_2q"]["lower_bound"],
                "mkco_2q_certified": M["mkco_2q"]["certified_optimal"],
                "xt_pairs_original": o["xt_pairs"], "xt_pairs_mkco_xt": M["mkco_xt"]["xt_pairs"],
                "depth_mkco_rewrite": M["mkco_rewrite"]["depth"], "depth_mkco_full": M["mkco_full"]["depth"],
                "duration_us_original": round(o["duration_ns"] / 1000, 2),
                "duration_us_mkco_full_dur": round(M["mkco_full_dur"]["duration_ns"] / 1000, 2),
                "ecr_mkco_full_dur": M["mkco_full_dur"]["ecr"],
                "runtime_s_lee2026": M["lee2026"]["time_s"], "runtime_s_jk2026": M["jk2026"]["time_s"],
                "runtime_s_mkco": M["mkco"]["time_s"]})
    rows.sort(key=lambda r: ORDER.index(r["circuit"]))
    write_csv("ibm127_all.csv", rows)
    L = ["| Set | Circuit | Qubits | Gates | Depth: input | Lee'26 | JK'26 | **MKCO** | Proven LB | "
         "2q-depth: input → MKCO (LB) | Crosstalk pairs: input → MKCO-XT | MKCO-full depth (vs input) | "
         "Est. time µs: input → MKCO-full (vs input) |",
         "|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|"]
    for r in rows:
        xo, xx = r["xt_pairs_original"], r["xt_pairs_mkco_xt"]
        L.append(f"| {r['set']} | {r['circuit']} | {r['active_qubits']} | {r['gates']:,} | {r['depth_original']:,} | "
                 f"{r['depth_lee2026']:,} | {r['depth_jk2026']:,} | **{r['depth_mkco']:,}**"
                 f"{' ✓' if r['mkco_certified'] else ''} | {r['depth_lower_bound']:,} | "
                 f"{r['depth2q_original']:,} → {r['depth2q_mkco']:,} ({r['depth2q_lower_bound']:,}) | "
                 f"{xo:,} → {xx:,} ({pct(xx, xo) if xo else '–'}) | "
                 f"{r['depth_mkco_full']:,} ({pct(r['depth_mkco_full'], r['depth_original'])}) | "
                 f"{r['duration_us_original']:,.2f} → {r['duration_us_mkco_full_dur']:,.2f} "
                 f"({pct(r['duration_us_mkco_full_dur'], r['duration_us_original'])}) |")
    L.append("\n✓ = certified optimal: the depth equals the proven lower bound, so no commutation-equivalent "
             "reordering is shallower. Every 2q-depth result is also certified optimal (13/13).")
    return "\n".join(L)


def table_paper_settings():
    e1, e2, e3, e4 = (load(f"results/structured/{e}.json") for e in ("e1", "e2", "e3", "e4"))
    th = load("results/structured/theta.json") + load("results/structured/theta_plus.json")
    lb = {(r["m"], r["n"], r["seed"]): r["lb"] for r in e1}
    for r in th:
        if r["experiment"] == "e1":
            k = (r["m"], r["n"], r["seed"])
            lb[k] = max(lb[k], r["lb"])
    opt1 = {k: sum(1 for r in e1 if r[k] == lb[(r["m"], r["n"], r["seed"])]) for k in ("dsatur", "jk", "mkco")}
    ex1 = {k: sum(r[k] - lb[(r["m"], r["n"], r["seed"])] for r in e1) / len(e1) for k in ("dsatur", "jk", "mkco")}
    best2 = {r["n"]: r.get("proven_optimum") or r["lb"] for r in e2}
    opt2 = {k: sum(1 for r in e2 if r[k] == best2[r["n"]]) for k in ("dsatur", "jk", "mkco")}
    opt3 = {k: sum(1 for r in e3 if r[k] == r["lb"]) for k in ("dsatur", "jk", "mkco")}
    opt4 = {k: sum(1 for r in e4 if r[k] == r["lb"]) for k in ("dsatur", "jk", "mkco")}
    ex4 = {k: sum(r[k] - r["lb"] for r in e4) / len(e4) for k in ("dsatur", "jk", "mkco")}
    e6 = load("results/structured/e6.json")
    best6 = min(e6, key=lambda r: r["mkco_total"] / r["baseline_total"])
    L = ["| Setting (Lee et al.) | Instances | Lee et al. (DSatur) | Jain & Kumar | **MKCO** | Note |",
         "|---|---:|---:|---:|---:|---|",
         f"| E1 random multi-controlled-Z (§4.3), m=10/20/30, n=50–200 | 60 | {opt1['dsatur']}/60 | {opt1['jk']}/60 | "
         f"**{opt1['mkco']}/60** | mean layers above best proven bound: DSatur {ex1['dsatur']:.2f}, JK {ex1['jk']:.1f}, "
         f"MKCO {ex1['mkco']:.2f} |",
         f"| E2 F₂ⁿ multiplier Toffoli-depth (§5.1), n = 2…64 | 34 sizes | {opt2['dsatur']}/34 | {opt2['jk']}/34 | "
         f"**{opt2['mkco']}/34** | optimum = 2n−1 for n ≥ 6; n ≤ 5 proven by exhaustive search |",
         f"| E3 random CCZ on 10 qubits (App. C) | 50 | {opt3['dsatur']}/50 | {opt3['jk']}/50 | **{opt3['mkco']}/50** | "
         f"MKCO strictly better than DSatur on {sum(1 for r in e3 if r['mkco'] < r['dsatur'])} |",
         f"| E4 commuting RZZ / QAOA layers (edge colouring) | 18 | {opt4['dsatur']}/18 | {opt4['jk']}/18 | "
         f"**{opt4['mkco']}/18** | reaching Vizing's bound Δ; mean excess DSatur {ex4['dsatur']:.1f}, JK {ex4['jk']:.1f}, "
         f"MKCO {ex4['mkco']:.2f} |",
         f"| E6 ancilla fan-out (§5.2, capacitated Max-k-Cut) | {len(e6)} | – | – | up to "
         f"**{100 * (1 - best6['mkco_total'] / best6['baseline_total']):.0f}%** shallower | vs round-robin copies + DSatur "
         f"({best6['case']}, c={best6['copies']}: {best6['baseline_total']} → {best6['mkco_total']}) |"]
    L.append("\nCounts are instances where the method meets the best proven lower bound (clique / Jackson, "
             "Lovász θ, Szegedy θ⁺, or exhaustive search).")
    return "\n".join(L)


def table_tdepth():
    rows = [r for r in load("results/structured/tdepth.json")]
    L = ["| Circuit | Kind | Qubits | Input | MKCO-T | PyZX (full) | **PyZX + MKCO-T** | PyZX gain from MKCO-T |",
         "|---|---|---:|---:|---:|---:|---:|---:|"]
    for r in rows:
        c = lambda k: (f"{r[k]['count']} / {r[k]['depth_nc']}" + (" ✓" if r[k].get("certified_optimal") else "")) if k in r else "–"  # noqa: E731
        gain = (f"{100 * (r['pyzx_full+mkco_t']['depth_nc'] - r['pyzx_full']['depth_nc']) / r['pyzx_full']['depth_nc']:+.0f}%"
                if "pyzx_full" in r else "–")
        L.append(f"| {r['circuit']} | {r['kind']} | {r['qubits']} | {c('original')} | {c('mkco_t')} | {c('pyzx_full')} | "
                 f"**{c('pyzx_full+mkco_t')}** | {gain} |")
    L.append("\nCells: count / depth of the counted gates (T-like rotations or Toffolis); ✓ = certified optimal "
             "for that gate set. PyZX: full_reduce + extract_circuit + basic_optimization.")
    return "\n".join(L)


def table_routing():
    rows = load("results/structured/routing.json")
    L = ["| Logical circuit | Qubits | Qiskit L3 (SABRE) CNOTs / depth | **MKCO-route** CNOTs / depth | CNOTs vs Qiskit | "
         "Depth vs Qiskit | Ablation (DAG front) CNOTs / depth |",
         "|---|---:|---|---|---:|---:|---|"]
    for r in rows:
        q, m, a = r["qiskit_o3"], r["mkco_route"], r["sabre_dag"]
        L.append(f"| {r['circuit']} | {r['qubits']} | {q['cx']} / {q['depth']} | **{m['cx']} / {m['depth']}** | "
                 f"{pct(m['cx'], q['cx'])} | {pct(m['depth'], q['depth'])} | {a['cx']} / {a['depth']} |")
    L.append("\nUntranspiled logical circuits routed onto IBM Eagle's 127-qubit heavy-hex graph (CNOT level). "
             "Every MKCO-route output passes the exact unroute and coupling checks.")
    return "\n".join(L)


def table_regroup():
    rg = load("results/structured/regroup.json")["logical"]
    L = ["| Logical circuit | Input CNOTs | Plain block KAK | **Regroup + KAK** | Qiskit L3 | Qiskit L3 + regroup + KAK |",
         "|---|---:|---:|---:|---:|---:|"]
    for r in rg:
        f = lambda k: f"{r[k]['cx']} / {r[k]['depth']}"  # noqa: E731
        L.append(f"| {r['circuit']} | {r['cx_in']} | {f('kak')} | **{f('regroup_kak')}** | {f('qiskit_o3')} | "
                 f"{f('o3+regroup_kak')} |")
    L.append("\nCells: CNOTs / depth after MKCO layering.")
    return "\n".join(L)


def table_noise():
    L = ["| Set | Circuit | Device | Score (10× lower noise) | Input | JK'26 | MKCO (depth only) | MKCO-ALAP | MKCO-full | "
         "**Noise-aware MKCO** (picks) |", "|---|---|---|---|---:|---:|---:|---:|---:|---|"]
    for d, tag in SETS:
        nz = load(f"{d}/noise.json")["circuits"]
        for n in [x for x in ORDER if x in nz]:
            cr = nz[n]
            ms = cr["methods"]
            if cr["simulated"]:
                key, g = "density-matrix fidelity", (lambda r: r["sim_scale0.1"]["state_fidelity"])
            elif ms["original"]["sesp_scale0.1"] is not None:
                key, g = "state-aware ESP", (lambda r: r["sesp_scale0.1"])
            else:
                key, g = "ESP", (lambda r: r["esp_scale0.1"])
            fmt = lambda v: f"{v:.4f}" if v >= 1e-3 else f"{v:.2e}"  # noqa: E731
            L.append(f"| {tag} | {n} | {cr.get('backend', 'fake_brisbane')} | {key} | {fmt(g(ms['original']))} | "
                     f"{fmt(g(ms['jk2026']))} | {fmt(g(ms['mkco']))} | {fmt(g(ms['mkco_alap']))} | "
                     f"{fmt(g(ms['mkco_full']))} | **{fmt(g(ms['mkco_noise']))}** ({ms['mkco_noise']['selected']}) |")
    return "\n".join(L)


def table_noisy_backend():
    import glob
    rows = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "results/hardware/noisy_backend_scale0.1_*_results.json"))):
        for r in json.load(open(f))["rows"]:
            rows[(r["circuit"], r["method"])] = r
    circs = [c for c in ORDER if any(k[0] == c for k in rows)]
    meths = ["original", "mkco", "mkco_alap", "mkco_full", "mkco_full_alap", "mkco_noise"]
    L = ["| Circuit | " + " | ".join(meths) + " |", "|---|" + "---:|" * len(meths)]
    for c in circs:
        cells = []
        for m in meths:
            r = rows.get((c, m))
            cells.append("–" if r is None else f"{r['hellinger_fidelity']:.3f} [{r['ci95'][0]:.3f}, {r['ci95'][1]:.3f}]")
        L.append(f"| {c} | " + " | ".join(cells) + " |")
    L.append("\nAer with the device noise model (NoiseModel.from_backend of the circuit's calibration snapshot), "
             "Qiskit ALAP scheduling, 10× lower noise; Hellinger fidelity of the counts vs the ideal output "
             "[bootstrap 95% interval]; 32,768 shots (512 for add_17 / qae_17).")
    return "\n".join(L)


def table_runtime():
    L = ["| Circuit | Gates | Lee'26 (s) | JK'26 (s) | **MKCO depth (s)** | MKCO 2q-depth (s) | MKCO-full, incl. KAK (s) |",
         "|---|---:|---:|---:|---:|---:|---:|"]
    rows = []
    for d, _ in SETS:
        for n, r in load(f"{d}/results_recomputed.json").items():
            M = r["methods"]
            rows.append((n, M["original"]["gates"], M["lee2026"]["time_s"], M["jk2026"]["time_s"], M["mkco"]["time_s"],
                         M["mkco_2q"]["time_s"], M["mkco_full"]["time_s"]))
    for n, g, *t in sorted(rows, key=lambda r: r[1]):
        L.append(f"| {n} | {g:,} | {t[0]:.2f} | {t[1]:.2f} | **{t[2]:.2f}** | {t[3]:.2f} | {t[4]:.2f} |")
    L.append("\nSingle-process Python on a laptop, other jobs sharing the machine: indicative only. MKCO stops as soon "
             "as the certified bound is met, which happens on every IBM circuit.")
    return "\n".join(L)


TABLES = {"ibm": table_ibm, "paper_settings": table_paper_settings, "tdepth": table_tdepth,
          "routing": table_routing, "regroup": table_regroup, "noise": table_noise,
          "noisy_backend": table_noisy_backend, "runtime": table_runtime}


def main():
    os.makedirs(T, exist_ok=True)
    rendered = {}
    for name, fn in TABLES.items():
        rendered[name] = fn()
        open(os.path.join(T, f"key_{name}.md"), "w").write(rendered[name] + "\n")
    # full generated tables, as produced by the pipeline
    for src, dst in (("results/ibm127/tables.md", "full_ibm127_set1.md"),
                     ("results/ibm127_set2/tables.md", "full_ibm127_set2.md"),
                     ("results/structured/tables.md", "full_paper_settings_E1-E7.md"),
                     ("results/structured/tables_ext.md", "full_extensions_E8-E11.md")):
        shutil.copy(os.path.join(ROOT, src), os.path.join(T, dst))
    # digest
    text = open(os.path.join(P, "digest_template.md")).read()
    for name, body in rendered.items():
        text = text.replace("{{table:" + name + "}}", body)
    assert "{{table:" not in text, "unfilled table placeholder"
    open(os.path.join(P, "RESULTS_DIGEST.md"), "w").write(text)
    # figures and supplements
    fig = os.path.join(P, "figures")
    for f in os.listdir(os.path.join(ROOT, "docs/figures")):
        shutil.copy(os.path.join(ROOT, "docs/figures", f), os.path.join(fig, f))
    sup = os.path.join(P, "supplement")
    os.makedirs(sup, exist_ok=True)
    for f in ("REPORT.md", "THEORY.md", "RELATED_WORK.md"):
        shutil.copy(os.path.join(ROOT, "docs", f), os.path.join(sup, f))
    # zip for upload
    zpath = os.path.join(P, "mkco_paper_package.zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for base in ("README.md", "PAPER_PROMPT.md", "RESULTS_DIGEST.md"):
            z.write(os.path.join(P, base), os.path.join("mkco_paper_package", base))
        for sub in ("figures", "tables", "supplement"):
            for f in sorted(os.listdir(os.path.join(P, sub))):
                z.write(os.path.join(P, sub, f), os.path.join("mkco_paper_package", sub, f))
    print("wrote", os.path.relpath(os.path.join(P, "RESULTS_DIGEST.md"), ROOT), "and", os.path.relpath(zpath, ROOT))


if __name__ == "__main__":
    main()
