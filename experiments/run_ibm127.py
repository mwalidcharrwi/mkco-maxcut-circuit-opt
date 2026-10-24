"""Benchmark MKCO against related work on IBM-127-transpiled circuits.

Methods
  original        the transpiled circuit as given
  lee2026         Lee, Jeong & Kim (Quantum 2026): DSatur colouring of every
                  maximal block of mutually commuting gates
  jk2026          Jain & Kumar (NeurIPS 2026 WiML): independent-set layering of
                  the mixed graph with beam search (our re-implementation)
  mkco            ours: precedence-constrained Max-k-Cut layering (+ certified bound)
  mkco_xt         ours: crosstalk-aware weighted Max-k-Cut at optimal 2q-depth
  qiskit_o3       Qiskit transpile, optimization_level=3 (gate re-synthesis)
  qiskit_o3+mkco  ours applied to Qiskit's output

Usage: python experiments/run_ibm127.py [benchmark_dir] [--quick]
"""
from __future__ import annotations

import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mkco.coloring import paper_blockwise                       # noqa: E402
from mkco.crosstalk import (adjacent_couplers, coupler_edges,    # noqa: E402
                            crosstalk_pairs, optimize_crosstalk)
from mkco.jk import jain_kumar                                   # noqa: E402
from mkco.optimize import optimize                               # noqa: E402
from mkco.qasm import load_qasm, parse_qasm                      # noqa: E402
from mkco.verify import audit_reordering, statevector_check      # noqa: E402

# nominal IBM Eagle gate durations (ns): rz is virtual, sx/x 35.56 ns, ECR 533.33 ns.
# Classified by arity because Qiskit's exporter renames ECRs (ecr_<id>).
VIRTUAL_1Q = {"rz", "p", "u1"}


def gate_duration(g):
    if len(g.qubits) >= 2:
        return 533.33
    return 0.0 if g.name in VIRTUAL_1Q else 35.56


def duration_ns(c, sync=True):
    return round(c.depth(gate_duration, barrier_sync=sync), 1)


def metrics(c, adj, sync=False):
    return {"depth": c.depth("depth", barrier_sync=sync),
            "depth_2q": c.depth("2q", barrier_sync=sync),
            "gates": c.size(),
            "ecr": sum(1 for g in c.gates if len(g.qubits) == 2 and g.kind == "gate"),
            "xt_pairs": crosstalk_pairs(c, adj),
            "duration_ns": duration_ns(c, sync=True)}


def verify(orig, new, check_sim=True):
    out = {"audit": audit_reordering(orig, orig.gates, new.gates)}
    if check_sim:
        ok, fid = statevector_check(orig, new)
        out["statevector"] = None if ok is None else {"ok": bool(ok), "min_fidelity": fid}
    return out


def qiskit_o3(path):
    from qiskit import qasm2, transpile
    from qiskit.transpiler import CouplingMap
    qc = qasm2.load(path, custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS)
    edges = sorted({(qc.find_bit(i.qubits[0]).index, qc.find_bit(i.qubits[1]).index)
                    for i in qc.data if i.operation.num_qubits == 2})
    cm = CouplingMap(edges)
    for q in range(qc.num_qubits):
        if q not in cm.physical_qubits:
            cm.add_physical_qubit(q)
    t = time.time()
    out = transpile(qc, basis_gates=["rz", "sx", "x", "ecr"], coupling_map=cm,
                    initial_layout=list(range(qc.num_qubits)), optimization_level=3,
                    seed_transpiler=0)
    return parse_qasm(qasm2.dumps(out)), time.time() - t


def run(bdir, outdir, quick=False):
    os.makedirs(outdir, exist_ok=True)
    files = sorted((os.path.join(bdir, f) for f in os.listdir(bdir) if f.endswith(".qasm")),
                   key=os.path.getsize)
    circuits = {f: load_qasm(f) for f in files}
    adj = adjacent_couplers(coupler_edges(circuits.values()))
    results_path = os.path.join(outdir, "results.json")
    results = json.load(open(results_path)) if os.path.exists(results_path) else {}
    for f in files:
        c = circuits[f]
        name = c.name
        if name in results and not quick:
            print(f"skip {name} (done)")
            continue
        n_active = len({q for g in c.gates for q in g.qubits})
        sim_ok = n_active <= 20
        big = c.size() > 40000
        tl = 20 if quick else (60 if big else 30)
        r = {"qubits_active": n_active, "methods": {}}
        print(f"== {name}: {c.size()} gates, {n_active} active qubits", flush=True)

        def record(key, circ, t, extra=None, sync=False, ver=None):
            m = metrics(circ, adj, sync=sync)
            m["time_s"] = round(t, 2)
            if extra:
                m.update(extra)
            if ver is not None:
                m["verification"] = ver
            r["methods"][key] = m
            print(f"   {key:16s} depth={m['depth']:7d} 2q={m['depth_2q']:6d} xt={m['xt_pairs']:5d} "
                  f"dur={m['duration_ns']:10.1f}ns gates={m['gates']:6d} t={t:.1f}s", flush=True)
            with open(os.path.join(outdir, f"{name}__{key}.qasm"), "w") as fh:
                fh.write(circ.to_qasm())

        record("original", c, 0.0)
        for metric, tag in (("depth", ""), ("2q", "_2q")):
            t = time.time(); lee = paper_blockwise(c, metric=metric); tt = time.time() - t
            record("lee2026" + tag, lee, tt, ver=verify(c, lee, sim_ok and metric == "depth"))
            t = time.time(); jk = jain_kumar(c, metric=metric); tt = time.time() - t
            record("jk2026" + tag, jk, tt, extra={"beam": 3 if c.size() <= 25000 else 1},
                   ver=verify(c, jk, sim_ok and metric == "depth"))
            t = time.time(); opt, rep = optimize(c, metric=metric, time_limit=tl); tt = time.time() - t
            record("mkco" + tag, opt, tt, extra={"lower_bound": rep["lower_bound"],
                                                 "certified_optimal": rep["certified_optimal"],
                                                 "source": [s.get("source") for s in rep["segments"]]},
                   ver=verify(c, opt, sim_ok))
        t = time.time(); xt, st = optimize_crosstalk(c, adj, time_limit=tl); tt = time.time() - t
        record("mkco_xt", xt, tt, extra={"model": st["segments"]}, sync=True,
               ver=verify(c, xt, sim_ok))
        try:
            q3, tq = qiskit_o3(f)
            record("qiskit_o3", q3, tq)
            t = time.time(); qm, rep = optimize(q3, metric="depth", time_limit=tl); tt = time.time() - t
            record("qiskit_o3+mkco", qm, tt, extra={"lower_bound": rep["lower_bound"],
                                                    "certified_optimal": rep["certified_optimal"]},
                   ver=verify(q3, qm, False))
        except Exception as e:  # keep the benchmark going if Qiskit fails on a file
            r["methods"]["qiskit_o3"] = {"error": repr(e)}
            print("   qiskit failed:", e, flush=True)
        results[name] = r
        with open(results_path, "w") as fh:
            json.dump(results, fh, indent=1, default=float)
    return results


if __name__ == "__main__":
    bdir = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "benchmarks/ibm127"
    run(bdir, "results/ibm127", quick="--quick" in sys.argv)
