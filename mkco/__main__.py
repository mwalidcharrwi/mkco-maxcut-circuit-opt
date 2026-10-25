"""MKCO command line.

  python -m mkco opt   IN.qasm OUT.qasm [--metric depth|2q] [--time 30] [--full|--rewrite|--merge] [--xt]
  python -m mkco bench FILES_OR_DIRS... [--metric depth|2q] [--time 30] [--csv out.csv]

`opt` reorders a circuit (commutation-preserving) and prints the certified
lower bound; `--full` first re-synthesises two-qubit blocks (KAK, native ECR
direction, needs qiskit) and then does `--rewrite`; `--rewrite` re-synthesises
single-qubit chains (ZSX) and fuses
same-axis rotations across commuting gates; `--merge` does only the latter;
`--xt` keeps the optimal 2q-depth and minimises crosstalk-prone ECR pairs on
neighbouring couplers (coupling graph inferred from the circuit).
For the full related-work comparison use experiments/run_ibm127.py.
"""
import argparse
import csv
import glob
import os
import time

from .coloring import paper_blockwise
from .optimize import optimize
from .qasm import load_qasm
from .verify import audit_reordering, statevector_check


def main(argv=None):
    ap = argparse.ArgumentParser(prog="mkco")
    ap.add_argument("cmd", choices=["opt", "bench"])
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--time", type=float, default=30.0)
    ap.add_argument("--metric", default="depth", choices=["depth", "2q"])
    ap.add_argument("--merge", action="store_true", help="fuse same-axis rotations first")
    ap.add_argument("--full", action="store_true",
                    help="two-qubit block (KAK) + single-qubit resynthesis before reordering")
    ap.add_argument("--rewrite", action="store_true",
                    help="single-qubit ZSX resynthesis + rotation merging before reordering")
    ap.add_argument("--xt", action="store_true", help="crosstalk-aware layering")
    ap.add_argument("--hmc", action="store_true", help="add hierarchical Max-Cut warm starts")
    ap.add_argument("--csv", default="results/bench.csv")
    a = ap.parse_args(argv)
    if a.cmd == "opt":
        c = load_qasm(a.paths[0])
        src = c
        if a.full:
            from .blocks import full_rewrite
            from .resynth import rewrite_single_qubit
            full, st = full_rewrite(c)
            only1q, _ = rewrite_single_qubit(c)
            # keep whichever pre-pass reorders to the shallower circuit (never worse)
            d_full = optimize(full, metric=a.metric, time_limit=a.time / 2)[0].depth()
            d_1q = optimize(only1q, metric=a.metric, time_limit=a.time / 2)[0].depth()
            src = full if d_full <= d_1q else only1q
            print(f"full rewrite: {st['gates_before']} -> {st['gates_after']} gates; "
                  f"kept {'block+1q' if src is full else '1q-only'} pre-pass "
                  f"(depth {min(d_full, d_1q)} vs {max(d_full, d_1q)})")
        elif a.rewrite:
            from .resynth import rewrite_single_qubit
            src, st = rewrite_single_qubit(c)
            print(f"rewrite: {st['gates_before']} -> {st['gates_after']} gates "
                  f"({st['fused_groups']} fused chains, {st['merged_groups']} merged groups)")
        elif a.merge:
            from .merge import merge_rotations
            src, st = merge_rotations(c)
            print(f"merged {st['groups_merged']} rotation groups, removed {st['gates_removed']} gates")
        if a.xt:
            from .crosstalk import (adjacent_couplers, coupler_edges, crosstalk_pairs,
                                    optimize_crosstalk)
            adj = adjacent_couplers(coupler_edges([src]))
            out, _ = optimize_crosstalk(src, adj, time_limit=a.time)
            print(f"crosstalk pairs {crosstalk_pairs(src, adj)} -> {crosstalk_pairs(out, adj)}; "
                  f"2q depth {src.depth('2q')} -> {out.depth('2q', barrier_sync=True)}")
        else:
            out, rep = optimize(src, metric=a.metric, time_limit=a.time, use_hmc=a.hmc)
            cert = " (certified optimal)" if rep["certified_optimal"] else ""
            print(f"{a.metric}: {rep['before']} -> {rep['after']}, lower bound "
                  f"{rep['lower_bound']}{cert}; {rep['time']:.1f}s")
        audit = audit_reordering(src, src.gates, out.gates)      # the reordering step
        print(f"commutation audit: {'pass' if audit['ok'] else 'FAIL'} "
              f"({audit.get('inverted_pairs')} reordered pairs checked)")
        ok, fid = statevector_check(c, out)
        if ok is not None:
            print(f"state-vector check: {'pass' if ok else 'FAIL'} (min fidelity {fid:.12f})")
        with open(a.paths[1], "w") as fh:
            fh.write(out.to_qasm())
        return
    files = []
    for p in a.paths:
        files += sorted(glob.glob(os.path.join(p, "*.qasm"))) if os.path.isdir(p) else [p]
    mname = "depth" if a.metric == "depth" else "2q"
    rows = []
    for f in files:
        c = load_qasm(f)
        t = time.time()
        paper = paper_blockwise(c, metric=a.metric)
        opt, rep = optimize(c, metric=a.metric, time_limit=a.time, use_hmc=a.hmc)
        audit = audit_reordering(c, c.gates, opt.gates)
        row = {"circuit": c.name, "gates": c.size(), "original": c.depth(mname),
               "lee2026": paper.depth(mname), "mkco": opt.depth(mname),
               "lower_bound": rep["lower_bound"], "certified_optimal": rep["certified_optimal"],
               "audit_ok": audit["ok"], "seconds": round(time.time() - t, 2)}
        rows.append(row)
        print(row, flush=True)
    os.makedirs(os.path.dirname(a.csv) or ".", exist_ok=True)
    with open(a.csv, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
