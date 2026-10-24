"""Add the 'mkco_merge' method (run-based rotation merging + MKCO reordering).

Merging changes gates, so equivalence is checked by state-vector simulation
when the circuit has <= 20 active qubits; every merge group is also checked
numerically inside merge_rotations, and the reordering step is audited
against the merged circuit."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from mkco.crosstalk import adjacent_couplers, coupler_edges  # noqa: E402
from mkco.merge import merge_rotations                       # noqa: E402
from mkco.optimize import optimize                           # noqa: E402
from mkco.qasm import load_qasm                              # noqa: E402
from mkco.verify import audit_reordering, statevector_check  # noqa: E402
from run_ibm127 import metrics                               # noqa: E402


def main(bdir="benchmarks/ibm127", outdir="results/ibm127"):
    path = os.path.join(outdir, "results.json")
    res = json.load(open(path))
    files = {os.path.splitext(f)[0]: os.path.join(bdir, f) for f in os.listdir(bdir)}
    circs = {n: load_qasm(p) for n, p in files.items()}
    adj = adjacent_couplers(coupler_edges(circs.values()))
    for name, r in res.items():
        c = circs[name]
        t = time.time()
        merged, st = merge_rotations(c)
        opt, rep = optimize(merged, metric="depth", time_limit=60)
        tt = time.time() - t
        m = metrics(opt, adj)
        ok, fid = statevector_check(c, opt)
        m.update({"time_s": round(tt, 2), "lower_bound": rep["lower_bound"],
                  "certified_optimal": rep["certified_optimal"], "merge": st,
                  "verification": {"audit_of_reordering": audit_reordering(merged, merged.gates, opt.gates),
                                   "statevector": None if ok is None else {"ok": bool(ok), "min_fidelity": fid}}})
        r["methods"]["mkco_merge"] = m
        open(os.path.join(outdir, f"{name}__mkco_merge.qasm"), "w").write(opt.to_qasm())
        print(name, "depth", c.depth(), "->", m["depth"], "sv", ok, flush=True)
    json.dump(res, open(path, "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
