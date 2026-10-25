"""Run benchmark outputs on IBM Quantum hardware (or locally on a fake backend).

Submit (needs an IBM Quantum account saved beforehand with
QiskitRuntimeService.save_account(...); this script never handles tokens):

    python experiments/run_ibm_hardware.py submit --backend ibm_brisbane \
        --circuits mult_8 hubbard_8 --methods original qiskit_o3 mkco mkco_alap mkco_noise

Collect the results once the jobs are done:

    python experiments/run_ibm_hardware.py collect

Local dry run with the ibm_brisbane noise model (no account needed):

    python experiments/run_ibm_hardware.py submit --fake --circuits mult_8

The benchmarks are native to ibm_brisbane.  On another backend every method's
circuit is re-oriented with mkco.blocks.make_native (same treatment for all
methods) and transpiled with optimization_level=0 and the trivial layout, so
the compared circuits stay as they are.  Each job measures the active qubits;
the score is the Hellinger fidelity between the measured counts and the ideal
output distribution (state-vector simulation of the original circuit).
Job ids go to results/hardware/jobs.json, scores to results/hardware/results.json.
"""
import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mkco.optimize import optimize                           # noqa: E402
from mkco.qasm import load_qasm                              # noqa: E402

RDIR = "results/ibm127"
HDIR = "results/hardware"


def method_circuit(name, method):
    path = os.path.join(RDIR, f"{name}__{method}.qasm")
    if os.path.exists(path):
        return load_qasm(path)
    if method == "mkco_noise":
        sel = json.load(open(os.path.join(RDIR, "noise.json")))["circuits"][name]["methods"]
        return method_circuit(name, sel["mkco_noise"]["selected"])
    if method.endswith("_alap"):
        base = method_circuit(name, "original" if method == "mkco_alap" else method[:-5])
        rev = base.copy_with_gates(list(reversed(base.gates)))
        out, _ = optimize(rev, metric="depth", time_limit=30)
        return base.copy_with_gates(list(reversed(out.gates)))
    raise FileNotFoundError(path)


def to_qiskit(c, active):
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import ECRGate, RZGate, SXGate, XGate
    qc = QuantumCircuit(c.num_qubits, len(active))
    for g in c.gates:
        if g.kind == "barrier":
            qc.barrier(list(g.qubits))
        elif g.name in ("rz", "p", "u1"):
            qc.append(RZGate(g.params[0]), list(g.qubits))
        elif g.name == "sx":
            qc.append(SXGate(), list(g.qubits))
        elif g.name == "x":
            qc.append(XGate(), list(g.qubits))
        elif len(g.qubits) == 2:
            qc.append(ECRGate(), list(g.qubits))
        else:
            raise ValueError(f"unsupported gate {g}")
    qc.measure(active, list(range(len(active))))
    return qc


def ideal_distribution(c, active):
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import ECRGate, RZGate, SXGate, XGate
    pos = {q: i for i, q in enumerate(active)}
    qc = QuantumCircuit(len(active))
    for g in c.gates:
        if g.kind == "barrier":
            continue
        qs = [pos[q] for q in g.qubits]
        op = (RZGate(g.params[0]) if g.name in ("rz", "p", "u1") else SXGate() if g.name == "sx"
              else XGate() if g.name == "x" else ECRGate())
        qc.append(op, qs)
    from qiskit.quantum_info import Statevector
    return np.abs(Statevector(qc).data) ** 2


def hellinger(counts, p, k):
    shots = sum(counts.values())
    q = np.zeros(2 ** k)
    for bits, n in counts.items():
        q[int(bits, 2)] += n / shots
    return float(np.sum(np.sqrt(p * q)) ** 2)


def submit(a):
    from qiskit import transpile
    from qiskit_ibm_runtime import SamplerV2
    if a.fake:
        from qiskit_ibm_runtime.fake_provider import FakeBrisbane
        backend = FakeBrisbane()
    else:
        from qiskit_ibm_runtime import QiskitRuntimeService
        backend = QiskitRuntimeService().backend(a.backend)
    native = {tuple(e) for e in backend.coupling_map.get_edges()}
    jobs = []
    for name in a.circuits:
        for m in a.methods:
            c = method_circuit(name, m)
            if any(len(g.qubits) == 2 and g.qubits not in native for g in c.gates):
                from mkco.blocks import make_native
                c, _ = make_native(c, native)
            active = sorted({q for g in c.gates if g.kind != "barrier" for q in g.qubits})
            qc = transpile(to_qiskit(c, active), backend=backend, optimization_level=0,
                           initial_layout=list(range(c.num_qubits)), seed_transpiler=0)
            job = SamplerV2(mode=backend).run([qc], shots=a.shots)
            rec = {"circuit": name, "method": m, "backend": backend.name, "job_id": job.job_id(),
                   "active": active, "shots": a.shots, "submitted": time.time()}
            if a.fake:                                     # local mode: results are ready
                rec["counts"] = job.result()[0].data.c.get_counts()
            jobs.append(rec)
            print(name, m, rec["job_id"], flush=True)
    os.makedirs(HDIR, exist_ok=True)
    json.dump(jobs, open(os.path.join(HDIR, "jobs.json"), "w"), indent=1)
    if a.fake:
        collect(a)


def collect(a):
    jobs = json.load(open(os.path.join(HDIR, "jobs.json")))
    service = None
    rows = []
    for rec in jobs:
        counts = rec.get("counts")
        if counts is None:
            if service is None:
                from qiskit_ibm_runtime import QiskitRuntimeService
                service = QiskitRuntimeService()
            counts = service.job(rec["job_id"]).result()[0].data.c.get_counts()
        c0 = method_circuit(rec["circuit"], "original")
        active0 = sorted({q for g in c0.gates if g.kind != "barrier" for q in g.qubits})
        p = ideal_distribution(c0, active0)
        k = len(rec["active"])
        rows.append({k2: rec[k2] for k2 in ("circuit", "method", "backend", "job_id", "shots")} |
                    {"hellinger_fidelity": hellinger(counts, p, k)})
        print(rows[-1], flush=True)
    json.dump(rows, open(os.path.join(HDIR, "results.json"), "w"), indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["submit", "collect"])
    ap.add_argument("--backend", default="ibm_brisbane")
    ap.add_argument("--fake", action="store_true", help="run locally on FakeBrisbane")
    ap.add_argument("--circuits", nargs="+", default=["mult_8"])
    ap.add_argument("--methods", nargs="+",
                    default=["original", "qiskit_o3", "mkco", "mkco_alap", "mkco_noise"])
    ap.add_argument("--shots", type=int, default=8192)
    a = ap.parse_args()
    submit(a) if a.cmd == "submit" else collect(a)


if __name__ == "__main__":
    main()
