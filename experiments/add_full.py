"""Add 'mkco_full': two-qubit block (KAK) resynthesis + single-qubit rewrite,
iterated to a fixed point, then MKCO Max-k-Cut reordering.

Verification: state-vector check against the original (<= 20 active qubits),
numerical check of every replaced block / fused chain inside the passes, and
the commutation audit of the reordering step."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from mkco.blocks import full_rewrite                         # noqa: E402
from mkco.crosstalk import adjacent_couplers, coupler_edges  # noqa: E402
from mkco.optimize import optimize                           # noqa: E402
from mkco.qasm import load_qasm                              # noqa: E402
from mkco.resynth import rewrite_single_qubit                # noqa: E402
from mkco.verify import audit_reordering, statevector_check  # noqa: E402
from run_ibm127 import metrics                               # noqa: E402


def main(bdir="benchmarks/ibm127", outdir="results/ibm127"):
    path = os.path.join(outdir, "results.json")
    res = json.load(open(path))
    files = {os.path.splitext(f)[0]: os.path.join(bdir, f) for f in os.listdir(bdir)}
    circs = {n: load_qasm(p) for n, p in files.items()}
    adj = adjacent_couplers(coupler_edges(circs.values()))
    native = {n: {g.qubits for g in c.gates if len(g.qubits) == 2} for n, c in circs.items()}
    for name, r in res.items():
        c = circs[name]
        t = time.time()
        rw, st = full_rewrite(c)
        opt, rep = optimize(rw, metric="depth", time_limit=60)
        # never worse than rewrite-only: keep the shallower of the two pipelines
        rw1, _ = rewrite_single_qubit(c)
        opt1, rep1 = optimize(rw1, metric="depth", time_limit=60)
        chosen = "full"
        if (opt1.depth(), opt1.size()) < (opt.depth(), opt.size()):
            rw, opt, rep, chosen = rw1, opt1, rep1, "rewrite-only"
        tt = time.time() - t
        m = metrics(opt, adj)
        ok, fid = statevector_check(c, opt)
        rev = sum(1 for g in opt.gates if len(g.qubits) == 2 and g.qubits not in native[name])
        m.update({"time_s": round(tt, 2), "lower_bound": rep["lower_bound"], "chosen": chosen,
                  "certified_optimal": rep["certified_optimal"], "reversed_ecr": rev,
                  "rewrite": {"gates_before": st["gates_before"], "gates_after": st["gates_after"],
                              "rounds": len(st["rounds"])},
                  "verification": {"audit_of_reordering": audit_reordering(rw, rw.gates, opt.gates),
                                   "statevector": None if ok is None else {"ok": bool(ok), "min_fidelity": fid}}})
        r["methods"]["mkco_full"] = m
        open(os.path.join(outdir, f"{name}__mkco_full.qasm"), "w").write(opt.to_qasm())
        print(f"{name}: mkco_full depth {m['depth']} [{chosen}] (cert {rep['certified_optimal']}), ECR {m['ecr']} "
              f"(reversed {rev}), 2q {m['depth_2q']}, sv {ok}, {tt:.0f}s | rewrite {r['methods']['mkco_rewrite']['depth']}",
              flush=True)
        json.dump(res, open(path, "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
