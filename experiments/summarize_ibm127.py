"""Build comparison tables (markdown + CSV) from results/ibm127/results.json.

Durations are recomputed from the saved QASM outputs with the arity-based
model (ECR 533.33 ns, sx/x 35.56 ns, rz virtual).
"""
from __future__ import annotations

import csv
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from mkco.qasm import load_qasm                      # noqa: E402
from run_ibm127 import duration_ns                    # noqa: E402

ORDER = ["mult_8", "add_17", "qae_17", "qft_16", "hubbard_8", "hhl_8", "heisenberg_32",
         "grover_10", "hubbard_18"]


def pct(a, b):
    return 100.0 * (b - a) / a if a else 0.0


def main(outdir="results/ibm127"):
    res = json.load(open(os.path.join(outdir, "results.json")))
    names = [n for n in ORDER if n in res] + [n for n in res if n not in ORDER]
    for n in names:
        for key, m in res[n]["methods"].items():
            p = os.path.join(outdir, f"{n}__{key}.qasm")
            if "depth" in m and os.path.exists(p):
                m["duration_ns"] = duration_ns(load_qasm(p), sync=True)
    lines = []
    A = lines.append

    A("### Table 1 - Total depth, reorder-only methods (lower is better)\n")
    A("| Circuit | Gates | Original | Lee'26 (colouring) | JK'26 (MIS+beam) | **MKCO** | Certified LB | MKCO optimal? | MKCO vs original |")
    A("|---|---:|---:|---:|---:|---:|---:|:---:|---:|")
    rows_csv = []
    for n in names:
        M = res[n]["methods"]
        o, l, j, k = (M[x]["depth"] for x in ("original", "lee2026", "jk2026", "mkco"))
        lb = M["mkco"].get("lower_bound")
        A(f"| {n} | {M['original']['gates']} | {o} | {l} | {j} | **{k}** | {lb} | "
          f"{'yes' if M['mkco'].get('certified_optimal') else 'no'} | {pct(o, k):+.2f}% |")
        rows_csv.append({"circuit": n, "metric": "depth", "original": o, "lee2026": l,
                         "jk2026": j, "mkco": k, "lower_bound": lb})

    A("\n### Table 2 - Two-qubit (ECR) depth, reorder-only methods optimising 2q-depth\n")
    A("| Circuit | Original | Lee'26 | JK'26 | **MKCO** | Certified LB | MKCO optimal? |")
    A("|---|---:|---:|---:|---:|---:|:---:|")
    for n in names:
        M = res[n]["methods"]
        o = M["original"]["depth_2q"]
        l, j, k = (M[x]["depth_2q"] for x in ("lee2026_2q", "jk2026_2q", "mkco_2q"))
        lb = M["mkco_2q"].get("lower_bound")
        A(f"| {n} | {o} | {l} | {j} | **{k}** | {lb} | "
          f"{'yes' if M['mkco_2q'].get('certified_optimal') else 'no'} |")
        rows_csv.append({"circuit": n, "metric": "depth_2q", "original": o, "lee2026": l,
                         "jk2026": j, "mkco": k, "lower_bound": lb})

    A("\n### Table 3 - Crosstalk-prone ECR pairs (same layer, neighbouring couplers) at optimal 2q-depth\n")
    A("| Circuit | Original | Lee'26 | JK'26 | MKCO (2q mode) | **MKCO-XT** | Reduction vs best baseline | 2q-depth orig -> XT | Total depth orig -> XT |")
    A("|---|---:|---:|---:|---:|---:|---:|---|---|")
    for n in names:
        M = res[n]["methods"]
        o = M["original"]["xt_pairs"]
        l, j, k2 = M["lee2026_2q"]["xt_pairs"], M["jk2026_2q"]["xt_pairs"], M["mkco_2q"]["xt_pairs"]
        x = M["mkco_xt"]["xt_pairs"]
        best = min(o, l, j, k2)
        A(f"| {n} | {o} | {l} | {j} | {k2} | **{x}** | {pct(best, x):+.1f}% | "
          f"{M['original']['depth_2q']} -> {M['mkco_xt']['depth_2q']} | "
          f"{M['original']['depth']} -> {M['mkco_xt']['depth']} |")
        rows_csv.append({"circuit": n, "metric": "xt_pairs", "original": o, "lee2026": l,
                         "jk2026": j, "mkco": x, "lower_bound": ""})

    A("\n### Table 4 - Gate-rewriting class: MKCO rewrite modes vs Qiskit O3 (device target), and composition\n")
    A("Depth (lower is better). Qiskit O3 runs on a Target with ECRs only on the native directed edges, so "
      "every output below is executable on the device (0 reversed ECRs). MKCO-rewrite = single-qubit ZSX "
      "resynthesis + run merging + Max-k-Cut reordering; MKCO-full adds two-qubit KAK block resynthesis. "
      "Every MKCO result is certified optimal for the gate list it reorders.\n")
    A("| Circuit | Original | MKCO (reorder) | MKCO-rewrite | **MKCO-full** | Qiskit O3 | O3 + MKCO | O3 + MKCO-rewrite | Best | MKCO-full vs Qiskit O3 |")
    A("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for n in names:
        M = res[n]["methods"]
        row = {k: M.get(k, {}).get("depth") for k in ("original", "mkco", "mkco_rewrite", "mkco_full",
                                                       "qiskit_o3", "qiskit_o3+mkco", "qiskit_o3+mkco_rewrite")}
        best = min(v for v in row.values() if v is not None)
        f = lambda k: "" if row.get(k) is None else (f"**{row[k]}**" if row[k] == best else str(row[k]))  # noqa: E731
        gain = ("" if row.get("mkco_full") is None or row.get("qiskit_o3") is None else
                f"{100 * (row['mkco_full'] - row['qiskit_o3']) / row['qiskit_o3']:+.1f}%")
        A(f"| {n} | {row['original']} | {f('mkco')} | {f('mkco_rewrite')} | {f('mkco_full')} | {f('qiskit_o3')} | "
          f"{f('qiskit_o3+mkco')} | {f('qiskit_o3+mkco_rewrite')} | {best} | {gain} |")
    A("\n**Hardware-time view.** MKCO-full (duration objective) keeps, per circuit, the candidate with the "
      "lowest estimated execution time among {KAK + 1q rewrite, 1q rewrite} x {reorder for depth, for 2q-depth}.\n")
    A("| Circuit | est. duration original (us) | Qiskit O3 (us) | MKCO-full, depth obj. (us) | **MKCO-full, duration obj. (us)** | "
      "vs Qiskit | 2q-depth Qiskit / MKCO-dur | ECRs Qiskit / MKCO-dur | depth Qiskit / MKCO-dur | reversed ECRs |")
    A("|---|---:|---:|---:|---:|---:|---|---|---|---|")
    for n in names:
        M = res[n]["methods"]
        q, a, d = M.get("qiskit_o3", {}), M.get("mkco_full", {}), M.get("mkco_full_dur", {})
        if not d or "depth" not in q:
            continue
        A(f"| {n} | {M['original']['duration_ns'] / 1000:.2f} | {q['duration_ns'] / 1000:.2f} | "
          f"{a['duration_ns'] / 1000:.2f} | **{d['duration_ns'] / 1000:.2f}** | "
          f"{100 * (d['duration_ns'] - q['duration_ns']) / q['duration_ns']:+.1f}% | "
          f"{q['depth_2q']} / {d['depth_2q']} | {q['ecr']} / {d['ecr']} | {q['depth']} / {d['depth']} | "
          f"{q.get('reversed_ecr', '-')} / {d.get('reversed_ecr', '-')} |")
    A("\n### Table 5 - Estimated execution time (us; ECR 533 ns, sx/x 36 ns, rz virtual)\n")
    A("| Circuit | Original | Lee'26 | JK'26 | MKCO (depth) | MKCO (2q) | MKCO-XT |")
    A("|---|---:|---:|---:|---:|---:|---:|")
    for n in names:
        M = res[n]["methods"]
        vals = [M[k]["duration_ns"] / 1000 for k in ("original", "lee2026", "jk2026", "mkco",
                                                    "mkco_2q", "mkco_xt")]
        A(f"| {n} | " + " | ".join(f"{v:.2f}" for v in vals) + " |")

    A("\n### Table 6 - Runtime (s)\n")
    A("| Circuit | Lee'26 | JK'26 | MKCO | MKCO-2q | MKCO-XT | MKCO-full | Qiskit O3 (target) | MKCO after O3 |")
    A("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for n in names:
        M = res[n]["methods"]
        g = lambda k: M.get(k, {}).get("time_s", float("nan"))  # noqa: E731
        A(f"| {n} | {g('lee2026'):.1f} | {g('jk2026'):.1f} | {g('mkco'):.1f} | {g('mkco_2q'):.1f} | "
          f"{g('mkco_xt'):.1f} | {g('mkco_full'):.1f} | {g('qiskit_o3'):.1f} | {g('qiskit_o3+mkco'):.1f} |")

    A("\n### Table 7 - Verification of every reordered output\n")
    A("| Circuit | Active qubits | Commutation audit (all reorderings) | Inverted pairs checked (MKCO) | "
      "State-vector check (MKCO) | State-vector (MKCO-rewrite, vs original) | State-vector (MKCO-full dur., vs original) |")
    A("|---|---:|:---:|---:|:---:|:---:|:---:|")

    def sv_text(v):
        if v is None:
            return "n/a (>20 qubits)"
        return f"pass (F={v['min_fidelity']:.10f})" if v["ok"] else "FAIL"

    for n in names:
        M = res[n]["methods"]
        audits = [m["verification"]["audit"]["ok"] for m in M.values()
                  if "verification" in m and "audit" in m["verification"]]
        audits += [m["verification"]["audit_of_reordering"]["ok"] for m in M.values()
                   if "verification" in m and "audit_of_reordering" in m["verification"]]
        rw = M.get("mkco_rewrite", {}).get("verification", {})
        fu = M.get("mkco_full_dur", M.get("mkco_full", {})).get("verification", {})
        A(f"| {n} | {res[n]['qubits_active']} | {sum(audits)}/{len(audits)} pass | "
          f"{M['mkco']['verification']['audit'].get('inverted_pairs')} | "
          f"{sv_text(M['mkco']['verification'].get('statevector'))} | "
          f"{sv_text(rw.get('statevector')) if rw else '-'} | {sv_text(fu.get('statevector')) if fu else '-'} |")

    blocks = os.path.join(outdir, "blocks.json")
    if os.path.exists(blocks):
        A("\n### Table 8 - Two-qubit block (KAK) resynthesis: blocks that become cheaper in native ECRs\n")
        A("| Circuit | two-qubit blocks | cheaper after KAK | ECRs removed |")
        A("|---|---:|---:|---:|")
        for b in json.load(open(blocks)):
            A(f"| {b['circuit']} | {b['blocks_with_2q']} | {b['cheaper_after_kak']} | {b['ecr_removed']} |")
    pareto = os.path.join(outdir, "pareto.json")
    if os.path.exists(pareto):
        A("\n### Table 9 - Depth budget vs crosstalk (weighted Max-k-Cut with k = k* + slack)\n")
        A("| Circuit | slack (% of k*) | 2q-depth | crosstalk-prone pairs | vs original | est. duration (us) |")
        A("|---|---:|---:|---:|---:|---:|")
        for r in json.load(open(pareto)):
            A(f"| {r['circuit']} | {r['slack_pct']} | {r['depth_2q']} | {r['xt_pairs']} | "
              f"{100 * (r['xt_pairs'] - r['xt_pairs_original']) / r['xt_pairs_original']:+.1f}% | "
              f"{r['duration_ns'] / 1000:.2f} |")
    noise = os.path.join(outdir, "noise.json")
    if os.path.exists(noise):
        nz = json.load(open(noise))
        show = ["original", "qiskit_o3", "mkco", "mkco_alap", "mkco_full", "mkco_full_alap",
                "mkco_noise"]
        A(f"\n### Table 10 - Noise study with device calibration snapshots ({nz['backend']})\n")
        A("ESP = estimated success probability (state-blind, ALAP idling); sESP = state-aware "
          "ESP (idle gaps weighted by the idling qubit's state, <= 22 active qubits); "
          "sim = exact density-matrix state fidelity (<= 8 active qubits). Scale 0.1 = all "
          "error rates x0.1 and T1, T2 x10. mkco_noise = the MKCO candidate with the best sESP "
          "(ESP for larger circuits), the input included.\n")
        A("| Circuit | score | " + " | ".join(show) + " | mkco_noise picks |")
        A("|---|---|" + "---:|" * len(show) + "---|")

        def fmt(v):
            return "–" if v is None else (f"{v:.3g}" if v >= 1e-3 else f"{v:.2e}")

        for name, cr in nz["circuits"].items():
            if name not in res:
                continue
            ms = cr["methods"]
            pick = ms["mkco_noise"]["selected"]
            rows_ = [("ESP", "esp"), ("ESP_xt", "esp_xt"), ("ESP x0.1", "esp_scale0.1"), ("sESP", "sesp_scale1.0"),
                     ("sESP x0.1", "sesp_scale0.1")]
            if cr["simulated"]:
                rows_ += [("sim F", ("sim_scale1.0", "state_fidelity")),
                          ("sim F x0.1", ("sim_scale0.1", "state_fidelity"))]
            for label, key in rows_:
                vals = []
                for m in show:
                    r = ms.get(m, {})
                    v = r.get(key[0], {}).get(key[1]) if isinstance(key, tuple) else r.get(key)
                    vals.append(v)
                best = max((v for v in vals if v is not None), default=None)
                cells = [("**" + fmt(v) + "**") if v is not None and v == best else fmt(v) for v in vals]
                A(f"| {name} | {label} | " + " | ".join(cells) + f" | {pick if label == 'ESP' else ''} |")
    rg = os.path.join(outdir, "regroup.json")
    if not os.path.exists(rg):
        rg = "results/structured/regroup.json"
    if os.path.exists(rg) and any(r["circuit"] in res for r in json.load(open(rg))["ibm127"]):
        A("\n### Table 11 - ECRs removed by block KAK, plain vs commutation-aware block formation\n")
        A("| Circuit | input ECRs | plain KAK | regrouped KAK | Qiskit O3 ECRs | plain KAK on O3 | regrouped KAK on O3 |")
        A("|---|---:|---:|---:|---:|---:|---:|")
        for r in [r for r in json.load(open(rg))["ibm127"] if r["circuit"] in res]:
            i, q = r.get("input", {}), r.get("qiskit_o3", {})
            A(f"| {r['circuit']} | {i.get('ecr', '–')} | {i.get('plain_ecr_removed', '–')} | "
              f"{i.get('regroup_ecr_removed', '–')} | {q.get('ecr', '–')} | {q.get('plain_ecr_removed', '–')} | "
              f"{q.get('regroup_ecr_removed', '–')} |")
    import glob
    import itertools
    hw_rows, hw_model = {}, {}
    for sc in ("1", "0.1"):
        for f in sorted(glob.glob(f"results/hardware/noisy_backend_scale{sc}_*_results.json")):
            for r in json.load(open(f))["rows"]:
                if r["circuit"] in res:
                    hw_rows.setdefault(sc, {})[(r["circuit"], r["method"])] = r
            for r in json.load(open(f.replace("_results.json", "_jobs.json")))["records"]:
                if r["circuit"] in res:
                    hw_model.setdefault(sc, {})[(r["circuit"], r["method"])] = r["model"]
    if hw_rows and os.path.exists(noise):
        nzc = json.load(open(noise))["circuits"]
        shots = sorted({r["shots"] for rows_ in hw_rows.values() for r in rows_.values()})
        A("\n### Table 12 - Noisy simulated backend: Aer + the circuits' device calibrations, sampled counts\n")
        A(f"Hellinger fidelity of {' or '.join(map(str, shots))} shots against the ideal output "
          "[bootstrap 95% interval]. Noise model: Aer's NoiseModel.from_backend (independent of "
          "mkco.noise); Qiskit's ALAP scheduling; methods interleaved in one job per run. mkco_noise "
          "is the same circuit as the method it selects (a repeat measurement). Predictions at "
          "scale 0.1: mkco.noise density-matrix Hellinger fidelity (<= 8 qubits) and state-aware ESP. "
          "The 17-qubit circuits are run at scale 0.1 only (at scale 1 they are at the noise floor).\n")
        A("| Circuit | method | scale 1 | scale 0.1 | predicted (DM, x0.1) | sESP x0.1 |")
        A("|---|---|---:|---:|---:|---:|")
        keys = sorted({k for rows_ in hw_rows.values() for k in rows_},
                      key=lambda k: (ORDER.index(k[0]) if k[0] in ORDER else 99, k[1] != "original", k[1]))

        def cell(r):
            return "–" if r is None else f"{r['hellinger_fidelity']:.4f} [{r['ci95'][0]:.4f}, {r['ci95'][1]:.4f}]"

        for (c, m) in keys:
            mm = nzc[c]["methods"].get(m, {})
            pred = mm.get("sim_scale0.1", {}).get("hellinger_fidelity")
            ses = mm.get("sesp_scale0.1")
            pick = f" (= {nzc[c]['methods']['mkco_noise']['selected']})" if m == "mkco_noise" else ""
            A(f"| {c} | {m}{pick} | {cell(hw_rows.get('1', {}).get((c, m)))} | "
              f"{cell(hw_rows.get('0.1', {}).get((c, m)))} | {'–' if pred is None else f'{pred:.4f}'} | "
              f"{'–' if ses is None else f'{ses:.4f}'} |")
        for sc, tag in (("1", "1.0"), ("0.1", "0.1")):
            rb, model = hw_rows.get(sc, {}), hw_model.get(sc, {})
            agree = {"density-matrix model": [0, 0], "state-aware ESP": [0, 0], "ESP": [0, 0]}
            for c in sorted({k[0] for k in rb}):
                sel = nzc[c]["methods"]["mkco_noise"]["selected"]
                # mkco_noise is a repeat of its selected circuit: count it only when that one is absent
                ms = [m for (cc, m) in rb if cc == c and not (m == "mkco_noise" and (c, sel) in rb)]
                for a, b in itertools.combinations(ms, 2):
                    ra, rr = rb[(c, a)], rb[(c, b)]
                    if not (ra["ci95"][1] < rr["ci95"][0] or rr["ci95"][1] < ra["ci95"][0]):
                        continue
                    truth = ra["hellinger_fidelity"] > rr["hellinger_fidelity"]
                    dm = nzc[c]["methods"]
                    preds = {"state-aware ESP": (model[(c, a)]["sesp"], model[(c, b)]["sesp"]),
                             "ESP": (model[(c, a)]["esp"], model[(c, b)]["esp"])}
                    if f"sim_scale{tag}" in dm[a]:
                        preds["density-matrix model"] = (dm[a][f"sim_scale{tag}"]["hellinger_fidelity"],
                                                         dm[b][f"sim_scale{tag}"]["hellinger_fidelity"])
                    for k, (x, y) in preds.items():
                        agree[k][1] += 1
                        agree[k][0] += x != y and (x > y) == truth
            if rb:
                A(f"\nScale {sc}: on the method pairs that sampling separates (non-overlapping intervals), the "
                  "predictions order " + ", ".join(f"{k} {a}/{n}" for k, (a, n) in agree.items() if n) +
                  " correctly.")

    md = "\n".join(lines) + "\n"
    with open(os.path.join(outdir, "tables.md"), "w") as fh:
        fh.write(md)
    with open(os.path.join(outdir, "summary.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows_csv[0]))
        w.writeheader()
        w.writerows(rows_csv)
    with open(os.path.join(outdir, "results_recomputed.json"), "w") as fh:
        json.dump(res, fh, indent=1, default=float)
    print(md)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results/ibm127")
