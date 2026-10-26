"""Depth budget vs crosstalk trade-off (Pareto) with the weighted Max-k-Cut.

For each circuit and each extra 2q-layer budget s, minimise crosstalk-prone
ECR pairs subject to 2q-depth <= k* + s.  Writes results/ibm127/pareto.json.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from mkco.crosstalk import (adjacent_couplers, coupler_edges, crosstalk_pairs,  # noqa: E402
                            optimize_crosstalk)
from mkco.qasm import load_qasm                                                 # noqa: E402
from mkco.verify import audit_reordering                                       # noqa: E402
from run_ibm127 import duration_ns                                             # noqa: E402

CIRCUITS = ["mult_8", "add_17", "qae_17", "qft_16", "hubbard_8", "hhl_8"]
SLACK_PCT = [0, 1, 2, 5, 10, 20]


def main(bdir="benchmarks/ibm127", out="results/ibm127/pareto.json"):
    files = {os.path.splitext(f)[0]: os.path.join(bdir, f) for f in os.listdir(bdir)}
    circs = {n: load_qasm(p) for n, p in files.items()}
    adj = adjacent_couplers(coupler_edges(circs.values()))
    rows = []
    for name in [n for n in CIRCUITS if n in circs] or sorted(circs):   # set 2: all its circuits
        c = circs[name]
        k_star = c.depth("2q")
        for pct in SLACK_PCT:
            extra = int(round(k_star * pct / 100))
            t = time.time()
            xt, st = optimize_crosstalk(c, adj, time_limit=20, extra_layers=extra)
            row = {"circuit": name, "slack_pct": pct, "extra_layers": extra,
                   "depth_2q": xt.depth("2q", barrier_sync=True),
                   "xt_pairs": crosstalk_pairs(xt, adj),
                   "xt_pairs_original": crosstalk_pairs(c, adj),
                   "duration_ns": duration_ns(xt), "duration_ns_original": duration_ns(c),
                   "audit_ok": audit_reordering(c, c.gates, xt.gates)["ok"],
                   "time_s": round(time.time() - t, 1)}
            rows.append(row)
            print(row, flush=True)
            json.dump(rows, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
