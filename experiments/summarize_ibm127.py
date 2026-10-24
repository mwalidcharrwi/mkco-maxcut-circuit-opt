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

    A("\n### Table 4 - Gate-rewriting class: MKCO rewrite mode vs Qiskit O3, and their composition\n")
    A("Depth (lower is better). MKCO-rewrite = single-qubit ZSX resynthesis + run merging, then Max-k-Cut "
      "reordering; every MKCO result is certified optimal for the gate list it reorders.\n")
    A("| Circuit | Original | MKCO (reorder) | **MKCO-rewrite** | Qiskit O3 | O3 + MKCO | **O3 + MKCO-rewrite** | Best | Who wins |")
    A("|---|---:|---:|---:|---:|---:|---:|---:|---|")
    for n in names:
        M = res[n]["methods"]
        q = M.get("qiskit_o3", {})
        row = {k: M.get(k, {}).get("depth") for k in ("original", "mkco", "mkco_rewrite", "qiskit_o3",
                                                       "qiskit_o3+mkco", "qiskit_o3+mkco_rewrite")}
        vals = {k: v for k, v in row.items() if v is not None}
        best = min(vals.values())
        who = ("MKCO-rewrite" if row.get("mkco_rewrite") == best else
               "O3 + MKCO" if best in (row.get("qiskit_o3+mkco"), row.get("qiskit_o3+mkco_rewrite")) else
               "Qiskit O3" if row.get("qiskit_o3") == best else "MKCO")
        mark = "†" if "retry" in str(q.get("coupling", "")) else ""
        f = lambda k: "" if row.get(k) is None else str(row[k])  # noqa: E731
        A(f"| {n}{mark} | {f('original')} | {f('mkco')} | **{f('mkco_rewrite')}** | {f('qiskit_o3')} | "
          f"{f('qiskit_o3+mkco')} | **{f('qiskit_o3+mkco_rewrite')}** | {best} | {who} |")
    A("\n| Circuit | 2q-depth MKCO-rewrite | 2q-depth Qiskit O3 | gates MKCO-rewrite | gates Qiskit O3 | "
      "duration MKCO-rewrite (us) | duration Qiskit O3 (us) | duration O3+MKCO-rewrite (us) |")
    A("|---|---:|---:|---:|---:|---:|---:|---:|")
    for n in names:
        M = res[n]["methods"]
        a, q, b = M.get("mkco_rewrite", {}), M.get("qiskit_o3", {}), M.get("qiskit_o3+mkco_rewrite", {})
        if not a or "depth" not in q:
            continue
        A(f"| {n} | {a['depth_2q']} | {q['depth_2q']} | {a['gates']} | {q['gates']} | "
          f"{a['duration_ns'] / 1000:.2f} | {q['duration_ns'] / 1000:.2f} | "
          f"{b.get('duration_ns', float('nan')) / 1000:.2f} |")
    A("\n† Qiskit could not re-orient the ECRs it re-synthesised on the native (directed) coupling "
      "map, so it was re-run with a bidirectional map (favourable to Qiskit).\n")
    A("\n### Table 5 - Estimated execution time (us; ECR 533 ns, sx/x 36 ns, rz virtual)\n")
    A("| Circuit | Original | Lee'26 | JK'26 | MKCO (depth) | MKCO (2q) | MKCO-XT |")
    A("|---|---:|---:|---:|---:|---:|---:|")
    for n in names:
        M = res[n]["methods"]
        vals = [M[k]["duration_ns"] / 1000 for k in ("original", "lee2026", "jk2026", "mkco",
                                                    "mkco_2q", "mkco_xt")]
        A(f"| {n} | " + " | ".join(f"{v:.2f}" for v in vals) + " |")

    A("\n### Table 6 - Runtime (s)\n")
    A("| Circuit | Lee'26 | JK'26 | MKCO | MKCO-2q | MKCO-XT | Qiskit O3 | MKCO after O3 |")
    A("|---|---:|---:|---:|---:|---:|---:|---:|")
    for n in names:
        M = res[n]["methods"]
        g = lambda k: M.get(k, {}).get("time_s", float("nan"))  # noqa: E731
        A(f"| {n} | {g('lee2026'):.1f} | {g('jk2026'):.1f} | {g('mkco'):.1f} | {g('mkco_2q'):.1f} | "
          f"{g('mkco_xt'):.1f} | {g('qiskit_o3'):.1f} | {g('qiskit_o3+mkco'):.1f} |")

    A("\n### Table 7 - Verification of every reordered output\n")
    A("| Circuit | Active qubits | Commutation audit (all reorderings) | Inverted pairs checked (MKCO) | "
      "State-vector check (MKCO) | State-vector check (MKCO-rewrite, vs original) |")
    A("|---|---:|:---:|---:|:---:|:---:|")

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
        A(f"| {n} | {res[n]['qubits_active']} | {sum(audits)}/{len(audits)} pass | "
          f"{M['mkco']['verification']['audit'].get('inverted_pairs')} | "
          f"{sv_text(M['mkco']['verification'].get('statevector'))} | "
          f"{sv_text(rw.get('statevector')) if rw else '-'} |")

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
    main()
