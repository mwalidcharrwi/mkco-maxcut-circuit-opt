"""E8: non-Clifford depth with free Cliffords (T-depth and Toffoli-depth).

Methods per circuit
  original          the input
  mkco_depth        MKCO minimising the total depth (T-depth only incidental)
  mkco_t            MKCO non-Clifford mode: rotation merging + layering of the
                    counted gates on the reduced mixed graph (mkco.nonclifford)
  pyzx_full         PyZX full_reduce + extract_circuit + basic_optimization
  pyzx_teleport     PyZX teleport_reduce (T-count reduction, structure kept)
  pyzx_*+mkco_t     MKCO non-Clifford mode applied to PyZX's output

T-depth counts single-qubit Z rotations by odd multiples of pi/4 (t, tdg,
rz(pi/4), ...); Toffoli-depth counts Toffoli-class gates.  lower_bound is the
certified bound of mkco_t for its own (merged) input.  Every output with <= 20
active qubits is checked against the input by state-vector simulation.

Writes results/structured/tdepth.json.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mkco import generators as gen                                   # noqa: E402
from mkco.nonclifford import counted_count, counted_depth, optimize_nonclifford  # noqa: E402
from mkco.optimize import optimize                                   # noqa: E402
from mkco.qasm import parse_qasm                                     # noqa: E402
from mkco.verify import statevector_check                            # noqa: E402

OUT = "results/structured/tdepth.json"


def n2q(c):
    return sum(1 for g in c.gates if len(g.qubits) == 2)


def pyzx(c, mode):
    import pyzx as zx
    zc = zx.Circuit.from_qasm(c.to_qasm())
    g = zc.to_graph()
    if mode == "full":
        zx.full_reduce(g)
        oc = zx.extract_circuit(g.copy())
    else:
        oc = zx.Circuit.from_graph(zx.teleport_reduce(g))
    oc = zx.optimize.basic_optimization(oc.to_basic_gates())
    return parse_qasm(oc.to_qasm())


def record(ref, c, kind, t, extra=None):
    ok, _ = statevector_check(ref, c)
    m = {"count": counted_count(c, kind), "depth_nc": counted_depth(c, kind), "cx": n2q(c),
         "depth": c.depth(), "statevector_ok": None if ok is None else bool(ok),
         "time_s": round(t, 2)}
    m.update(extra or {})
    return m


def t_cases():
    cs = []
    for n in (4, 8, 16):
        cs.append(gen.decompose_toffoli(gen.cuccaro_adder(n)))
    for n in (5, 8, 12):
        cs.append(gen.decompose_toffoli(gen.mcx_vchain(n)))
    for n in (3, 4, 5, 6, 7):
        cs.append(gen.decompose_toffoli(gen.gf2_multiplier(n)))
    for n, t in ((8, 40), (12, 80), (16, 120)):
        cs.append(gen.t_phase_polynomial(n, t, seed=0))
    for n, g in ((8, 400), (10, 800), (12, 1200)):
        cs.append(gen.random_clifford_t(n, g, seed=0))
    return cs


def toffoli_cases():
    cs = [gen.cuccaro_adder(n) for n in (8, 16, 32)]
    cs += [gen.mcx_vchain(n) for n in (8, 16)]
    cs += [gen.gf2_multiplier(n) for n in (4, 5, 6, 7, 9, 10, 11, 12)]
    return cs


def run_case(c, kind, use_pyzx, tl=10.0):
    row = {"circuit": c.name, "qubits": c.num_qubits, "kind": kind}
    row["original"] = record(c, c, kind, 0.0)
    t = time.time()
    d, _ = optimize(c, metric="depth", time_limit=tl)
    row["mkco_depth"] = record(c, d, kind, time.time() - t)
    t = time.time()
    o, rep = optimize_nonclifford(c, kind=kind, time_limit=tl)
    row["mkco_t"] = record(c, o, kind, time.time() - t,
                           {"lower_bound": rep["lower_bound"],
                            "certified_optimal": rep["certified_optimal"]})
    if use_pyzx:
        for mode in ("full", "teleport"):
            t = time.time()
            p = pyzx(c, mode)
            tp = time.time() - t
            row[f"pyzx_{mode}"] = record(c, p, kind, tp)
            t = time.time()
            po, prep = optimize_nonclifford(p, kind=kind, time_limit=tl)
            row[f"pyzx_{mode}+mkco_t"] = record(c, po, kind, tp + time.time() - t,
                                                {"lower_bound": prep["lower_bound"],
                                                 "certified_optimal": prep["certified_optimal"]})
    return row


def main():
    rows = []
    for c in t_cases():
        rows.append(run_case(c, "t", use_pyzx=True))
        r = rows[-1]
        print(r["circuit"], {k: (v["count"], v["depth_nc"]) for k, v in r.items() if isinstance(v, dict)},
              flush=True)
        json.dump(rows, open(OUT, "w"), indent=1)
    for c in toffoli_cases():
        rows.append(run_case(c, "toffoli", use_pyzx=False))
        r = rows[-1]
        print(r["circuit"], {k: (v["count"], v["depth_nc"]) for k, v in r.items() if isinstance(v, dict)},
              flush=True)
        json.dump(rows, open(OUT, "w"), indent=1)


if __name__ == "__main__":
    main()
