"""Qiskit O3 baseline on a proper device Target, plus MKCO applied after it.

Setup (fair to Qiskit): the QASM files are loaded with `ecr` mapped to Qiskit's
ECRGate, and transpilation uses a Target whose ECRs exist only on the native
directed edges of the circuit (rz/sx/x on every qubit), trivial layout,
optimization_level=3.  Qiskit's synthesis then emits only native-direction
ECRs, so its outputs are executable as they stand (checked below).

Records, per circuit:
  qiskit_o3                Qiskit's output
  qiskit_o3+mkco           MKCO reordering of Qiskit's output
  qiskit_o3+mkco_rewrite   MKCO rewrite mode (1q resynthesis + reordering) of Qiskit's output
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from mkco.crosstalk import adjacent_couplers, coupler_edges  # noqa: E402
from mkco.optimize import optimize                           # noqa: E402
from mkco.qasm import load_qasm, parse_qasm                  # noqa: E402
from mkco.resynth import rewrite_single_qubit                # noqa: E402
from mkco.verify import audit_reordering, statevector_check  # noqa: E402
from run_ibm127 import metrics                               # noqa: E402


def device_target(qc):
    from qiskit.circuit import Measure, Parameter
    from qiskit.circuit.library import ECRGate, RZGate, SXGate, XGate
    from qiskit.transpiler import Target
    native = sorted({(qc.find_bit(i.qubits[0]).index, qc.find_bit(i.qubits[1]).index)
                     for i in qc.data if i.operation.num_qubits == 2})
    tg = Target(num_qubits=qc.num_qubits)
    every = {(q,): None for q in range(qc.num_qubits)}
    tg.add_instruction(RZGate(Parameter("theta")), dict(every))
    tg.add_instruction(SXGate(), dict(every))
    tg.add_instruction(XGate(), dict(every))
    tg.add_instruction(ECRGate(), {e: None for e in native})
    tg.add_instruction(Measure(), dict(every))           # set-2 circuits end in measurements
    return tg, set(native)


def qiskit_o3(path):
    from qiskit import qasm2, transpile
    from qiskit.circuit.library import ECRGate, RZXGate
    custom = list(qasm2.LEGACY_CUSTOM_INSTRUCTIONS) + [
        qasm2.CustomInstruction("ecr", 0, 2, ECRGate, builtin=False),
        qasm2.CustomInstruction("rzx", 1, 2, RZXGate, builtin=False)]
    qc = qasm2.load(path, custom_instructions=custom)
    tg, native = device_target(qc)
    t = time.time()
    out = transpile(qc, target=tg, initial_layout=list(range(qc.num_qubits)),
                    optimization_level=3, seed_transpiler=0)
    tt = time.time() - t
    c = parse_qasm(qasm2.dumps(out))
    reversed_ecr = sum(1 for g in c.gates if len(g.qubits) == 2 and g.qubits not in native)
    return c, tt, reversed_ecr


def main(bdir="benchmarks/ibm127", outdir="results/ibm127"):
    path = os.path.join(outdir, "results.json")
    res = json.load(open(path))
    files = {os.path.splitext(f)[0]: os.path.join(bdir, f) for f in os.listdir(bdir)}
    circs = {n: load_qasm(p) for n, p in files.items()}
    adj = adjacent_couplers(coupler_edges(circs.values()))
    for name, r in res.items():
        orig = circs[name]
        q3, tq, rev = qiskit_o3(files[name])
        m = metrics(q3, adj)
        ok, fid = statevector_check(orig, q3)
        m.update({"time_s": round(tq, 2), "reversed_ecr": rev, "target": "native directed ECR edges",
                  "verification": {"statevector": None if ok is None else {"ok": bool(ok), "min_fidelity": fid}}})
        r["methods"]["qiskit_o3"] = m
        open(os.path.join(outdir, f"{name}__qiskit_o3.qasm"), "w").write(q3.to_qasm())
        # MKCO reordering after Qiskit
        t = time.time()
        qm, rep = optimize(q3, metric="depth", time_limit=60)
        m2 = metrics(qm, adj)
        m2.update({"time_s": round(time.time() - t, 2), "lower_bound": rep["lower_bound"],
                   "certified_optimal": rep["certified_optimal"],
                   "verification": {"audit": audit_reordering(q3, q3.gates, qm.gates)}})
        r["methods"]["qiskit_o3+mkco"] = m2
        open(os.path.join(outdir, f"{name}__qiskit_o3+mkco.qasm"), "w").write(qm.to_qasm())
        # MKCO rewrite mode after Qiskit
        t = time.time()
        rw, st = rewrite_single_qubit(q3)
        qr, rep2 = optimize(rw, metric="depth", time_limit=60)
        m3 = metrics(qr, adj)
        ok3, fid3 = statevector_check(orig, qr)
        m3.update({"time_s": round(time.time() - t, 2), "lower_bound": rep2["lower_bound"],
                   "certified_optimal": rep2["certified_optimal"], "rewrite": st,
                   "verification": {"audit_of_reordering": audit_reordering(rw, rw.gates, qr.gates),
                                    "statevector": None if ok3 is None else {"ok": bool(ok3), "min_fidelity": fid3}}})
        r["methods"]["qiskit_o3+mkco_rewrite"] = m3
        open(os.path.join(outdir, f"{name}__qiskit_o3+mkco_rewrite.qasm"), "w").write(qr.to_qasm())
        print(f"{name}: O3 {m['depth']} (reversed ECR {rev}, {tq:.0f}s, sv {ok}) | O3+MKCO {m2['depth']} | "
              f"O3+MKCO-rewrite {m3['depth']} (sv {ok3}) | MKCO-rewrite "
              f"{r['methods'].get('mkco_rewrite', {}).get('depth', '-')}",
              flush=True)
        json.dump(res, open(path, "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
