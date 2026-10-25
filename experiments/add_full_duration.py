"""Add 'mkco_full_dur': MKCO-full selected by estimated execution time.

Candidates per circuit: {two-qubit KAK blocks + 1q rewrite, 1q rewrite only}
x {Max-k-Cut reordering for depth, for two-qubit depth}.  The candidate with
the lowest estimated duration (ECR 533 ns, sx/x 36 ns, rz virtual) is kept.
Verification as in add_full.py."""
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
from run_ibm127 import duration_ns, metrics                  # noqa: E402


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
        pre = {"kak+1q": full_rewrite(c)[0], "1q-only": rewrite_single_qubit(c)[0]}
        best = None
        for label, src in pre.items():
            for metric in ("depth", "2q"):
                opt, rep = optimize(src, metric=metric, time_limit=60)
                key = (duration_ns(opt), opt.depth())
                if best is None or key < best[0]:
                    best = (key, label, metric, src, opt, rep)
        _, label, metric, src, opt, rep = best
        m = metrics(opt, adj)
        ok, fid = statevector_check(c, opt)
        rev = sum(1 for g in opt.gates if len(g.qubits) == 2 and g.qubits not in native[name])
        m.update({"time_s": round(time.time() - t, 2), "chosen": f"{label}, reorder for {metric}",
                  "lower_bound": rep["lower_bound"], "certified_optimal": rep["certified_optimal"],
                  "reversed_ecr": rev,
                  "verification": {"audit_of_reordering": audit_reordering(src, src.gates, opt.gates),
                                   "statevector": None if ok is None else {"ok": bool(ok), "min_fidelity": fid}}})
        r["methods"]["mkco_full_dur"] = m
        open(os.path.join(outdir, f"{name}__mkco_full_dur.qasm"), "w").write(opt.to_qasm())
        q = r["methods"]["qiskit_o3"]
        print(f"{name}: [{label}, {metric}] duration {m['duration_ns']/1000:.1f}us (O3 {q['duration_ns']/1000:.1f}) "
              f"depth {m['depth']} (O3 {q['depth']}) 2q {m['depth_2q']} (O3 {q['depth_2q']}) ECR {m['ecr']} "
              f"(O3 {q['ecr']}) sv {ok}", flush=True)
        json.dump(res, open(path, "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
