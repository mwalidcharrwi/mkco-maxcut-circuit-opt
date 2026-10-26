"""Add the rewrite-mode methods to results/ibm127/results.json.

  mkco_rewrite            single-qubit resynthesis (ZSX) + run merging, then MKCO reordering

Verification: state-vector simulation against the *original* circuit when it
has <= 20 active qubits; every fused group is checked numerically inside the
rewrite, and the reordering step is audited against the rewritten circuit.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from mkco.crosstalk import adjacent_couplers, coupler_edges  # noqa: E402
from mkco.optimize import optimize                           # noqa: E402
from mkco.qasm import load_qasm                              # noqa: E402
from mkco.resynth import rewrite_single_qubit                # noqa: E402
from mkco.verify import audit_reordering, statevector_check  # noqa: E402
from run_ibm127 import metrics                               # noqa: E402


def run_one(src, reference, adj, tl=60):
    t = time.time()
    rw, st = rewrite_single_qubit(src)
    opt, rep = optimize(rw, metric="depth", time_limit=tl)
    tt = time.time() - t
    m = metrics(opt, adj)
    ok, fid = statevector_check(reference, opt)
    m.update({"time_s": round(tt, 2), "lower_bound": rep["lower_bound"],
              "certified_optimal": rep["certified_optimal"], "rewrite": st,
              "verification": {"audit_of_reordering": audit_reordering(rw, rw.gates, opt.gates),
                               "statevector": None if ok is None else {"ok": bool(ok), "min_fidelity": fid}}})
    return opt, m


def main(bdir="benchmarks/ibm127", outdir="results/ibm127"):
    path = os.path.join(outdir, "results.json")
    res = json.load(open(path))
    files = {os.path.splitext(f)[0]: os.path.join(bdir, f) for f in os.listdir(bdir)}
    circs = {n: load_qasm(p) for n, p in files.items()}
    adj = adjacent_couplers(coupler_edges(circs.values()))
    for name, r in res.items():
        c = circs[name]
        opt, m = run_one(c, c, adj)
        r["methods"]["mkco_rewrite"] = m
        open(os.path.join(outdir, f"{name}__mkco_rewrite.qasm"), "w").write(opt.to_qasm())
        print(f"{name}: mkco_rewrite {m['depth']} (sv {m['verification']['statevector']})", flush=True)
        json.dump(res, open(path, "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
