"""Run benchmark outputs on IBM Quantum hardware (or locally on a fake backend).

Submit (needs an IBM Quantum account saved beforehand with
QiskitRuntimeService.save_account(...); this script never handles tokens):

    python experiments/run_ibm_hardware.py submit            # backend auto, small circuits, 5 methods
    python experiments/run_ibm_hardware.py submit --backend ibm_brisbane \\
        --circuits mult_8 hubbard_8 hhl_8 --methods original qiskit_o3 mkco mkco_alap mkco_noise

    python experiments/run_ibm_hardware.py status     # job state
    python experiments/run_ibm_hardware.py collect    # scores, once the job is done

Local dry run with the ibm_brisbane noise model (no account needed; tests the
pipeline only, without ALAP delays, so idle noise is not modelled):

    python experiments/run_ibm_hardware.py submit --fake --circuits mult_8

All circuits go into one Sampler job, so every method sees the same
calibration.  Placement: the benchmarks are native to ibm_brisbane.  On a
backend that has every coupler they use, they keep their physical qubits;
otherwise (or with --placement best) all methods of a circuit are moved to the
same best-calibrated copy of their interaction graph on the backend.  ECRs
against the backend's direction are re-oriented with mkco.blocks.make_native,
the same treatment for every method.  Circuits are scheduled ALAP
(optimization_level=0, so nothing else changes) and measure their active
qubits.  Score: Hellinger fidelity between the counts and the ideal output
distribution, with a bootstrap 95% interval; the model predictions (ESP and
state-aware ESP from the backend's live calibration) are stored alongside.
Files: results/hardware/jobs.json and results/hardware/results.json.
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


def active_qubits(c):
    return sorted({q for g in c.gates if g.kind != "barrier" for q in g.qubits})


def best_placement(circuits, backend, max_tries=200000):
    """Map the union interaction graph of `circuits` onto the backend's coupling
    graph (subgraph monomorphism), minimising summed 2q and readout errors."""
    import networkx as nx
    from networkx.algorithms import isomorphism
    from mkco.noise import Calibration
    cal = Calibration(backend)
    h = nx.Graph()
    for c in circuits:
        h.add_nodes_from(active_qubits(c))
        h.add_edges_from(tuple(sorted(g.qubits)) for g in c.gates if len(g.qubits) == 2)
    dev = nx.Graph()
    dev.add_nodes_from(range(backend.num_qubits))
    err2 = {}
    for (op, qs), e in cal.err.items():
        if len(qs) == 2:
            k = tuple(sorted(qs))
            err2[k] = min(err2.get(k, 1.0), e)
            dev.add_edge(*k)
    best, best_cost = None, None
    gm = isomorphism.GraphMatcher(dev, h)
    for i, m in enumerate(gm.subgraph_monomorphisms_iter()):
        if i >= max_tries:
            break
        phi = {v: k for k, v in m.items()}          # circuit qubit -> device qubit
        cost = sum(err2.get(tuple(sorted((phi[a], phi[b]))), 1.0) for a, b in h.edges())
        cost += sum(cal.ro[phi[q]] for q in h.nodes())
        if best_cost is None or cost < best_cost:
            best, best_cost = phi, cost
    return best


def relabel(c, phi, n):
    from mkco.circuit import Circuit, Gate
    out = Circuit(n)
    out.name = c.name
    out.gates = [Gate(g.name, [phi[q] for q in g.qubits], g.params, g.clbits, g.cond, g.kind)
                 for g in c.gates]
    return out


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


def ideal_distribution(c):
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import ECRGate, RZGate, SXGate, XGate
    from qiskit.quantum_info import Statevector
    active = active_qubits(c)
    pos = {q: i for i, q in enumerate(active)}
    qc = QuantumCircuit(len(active))
    for g in c.gates:
        if g.kind == "barrier":
            continue
        op = (RZGate(g.params[0]) if g.name in ("rz", "p", "u1") else SXGate() if g.name == "sx"
              else XGate() if g.name == "x" else ECRGate())
        qc.append(op, [pos[q] for q in g.qubits])
    return np.abs(Statevector(qc).data) ** 2


def hellinger(counts, p, k, rng=None, boot=0):
    shots = sum(counts.values())
    q = np.zeros(2 ** k)
    for bits, n in counts.items():
        q[int(bits, 2)] += n
    val = float(np.sum(np.sqrt(p * q / shots)) ** 2)
    if not boot:
        return val, None
    rng = rng or np.random.default_rng(0)
    samples = [float(np.sum(np.sqrt(p * rng.multinomial(shots, q / shots) / shots)) ** 2)
               for _ in range(boot)]
    return val, [float(np.percentile(samples, 2.5)), float(np.percentile(samples, 97.5))]


def get_backend(a):
    if a.fake:
        from qiskit_ibm_runtime.fake_provider import FakeBrisbane
        return FakeBrisbane(), None
    from qiskit_ibm_runtime import QiskitRuntimeService
    service = QiskitRuntimeService()
    if a.backend != "auto":
        return service.backend(a.backend), service
    # auto: ibm_brisbane (the benchmarks are native to it), else another 127-qubit
    # ECR Eagle (same heavy-hex couplers), else the least busy device
    live = service.backends(operational=True, simulator=False)
    names = {b.name: b for b in live}
    if "ibm_brisbane" in names:
        return names["ibm_brisbane"], service
    eagles = [b for b in live if b.num_qubits == 127 and "ecr" in b.operation_names]
    if eagles:
        return min(eagles, key=lambda b: b.status().pending_jobs), service
    return service.least_busy(operational=True, simulator=False), service


def submit(a):
    from qiskit import transpile
    from qiskit_ibm_runtime import SamplerV2

    from mkco.noise import Calibration, esp, state_aware_esp
    backend, _ = get_backend(a)
    cal = Calibration(backend)
    native = {tuple(e) for e in backend.coupling_map.get_edges()}
    undirected = {tuple(sorted(e)) for e in native}
    pubs, recs = [], []
    for name in a.circuits:
        circs = {m: method_circuit(name, m) for m in a.methods}
        pairs = {tuple(sorted(g.qubits)) for c in circs.values() for g in c.gates if len(g.qubits) == 2}
        fits = backend.num_qubits >= circs["original"].num_qubits and pairs <= undirected
        if a.placement == "native" and fits:
            phi = {q: q for c in circs.values() for q in active_qubits(c)}
        else:
            phi = best_placement(list(circs.values()), backend)
            if phi is None:
                raise RuntimeError(f"{name}: no placement on {backend.name}")
        for m, c in circs.items():
            c = relabel(c, phi, backend.num_qubits)
            flipped = 0
            if any(len(g.qubits) == 2 and g.qubits not in native for g in c.gates) and "ecr" in backend.operation_names:
                from mkco.blocks import make_native
                c, flipped = make_native(c, native)
            act = active_qubits(c)
            p_ideal = ideal_distribution(c)          # same bit order as the measured qubits
            qc = transpile(to_qiskit(c, act), backend=backend, optimization_level=0,
                           initial_layout=list(range(backend.num_qubits)),
                           # local dry runs skip scheduling: Aer rejects the snapshot's
                           # T2 > 2*T1 qubits once delays carry relaxation noise
                           scheduling_method=None if a.fake else "alap", seed_transpiler=0)
            s = state_aware_esp(c, cal) if "ecr" in backend.operation_names else None
            recs.append({"circuit": name, "method": m, "pub": len(pubs), "active": act,
                         "placement": {str(k): v for k, v in phi.items()}, "ecr_flipped": flipped,
                         "two_qubit_gates": sum(1 for g in c.gates if len(g.qubits) == 2),
                         "depth": c.depth(),
                         "model": {"esp": esp(c, cal)["esp"] if "ecr" in backend.operation_names else None,
                                   "sesp": None if s is None else s["sesp"]},
                         "ideal": p_ideal.tolist()})
            pubs.append(qc)
            print(name, m, "pub", len(pubs) - 1, "active", act, "flipped", flipped, flush=True)
    order = np.random.default_rng(a.seed).permutation(len(pubs))       # interleave methods
    job = SamplerV2(mode=backend).run([pubs[i] for i in order], shots=a.shots)
    pos = {int(i): k for k, i in enumerate(order)}
    for r in recs:
        r["pub"] = pos[r["pub"]]
    meta = {"backend": backend.name, "job_id": job.job_id(), "shots": a.shots, "fake": bool(a.fake),
            "submitted": time.strftime("%Y-%m-%d %H:%M:%S"), "options": "SamplerV2 defaults "
            "(no dynamical decoupling, no twirling)", "records": recs}
    os.makedirs(HDIR, exist_ok=True)
    json.dump(meta, open(os.path.join(HDIR, "jobs_fake.json" if a.fake else "jobs.json"), "w"), indent=1)
    print("job", job.job_id(), "on", backend.name, flush=True)
    if a.fake:
        collect(a, job=job)


def status(a):
    meta = json.load(open(os.path.join(HDIR, "jobs.json")))
    from qiskit_ibm_runtime import QiskitRuntimeService
    job = QiskitRuntimeService().job(meta["job_id"])
    print(meta["backend"], meta["job_id"], job.status())


def collect(a, job=None):
    fn = "jobs_fake.json" if a.fake else "jobs.json"
    meta = json.load(open(os.path.join(HDIR, fn)))
    if job is None:
        from qiskit_ibm_runtime import QiskitRuntimeService
        job = QiskitRuntimeService().job(meta["job_id"])
    res = job.result()
    rows = []
    rng = np.random.default_rng(1)
    for r in meta["records"]:
        counts = res[r["pub"]].data.c.get_counts()
        k = len(r["active"])
        p = np.asarray(r["ideal"])
        h, ci = hellinger(counts, p, k, rng, boot=1000)
        rows.append({"circuit": r["circuit"], "method": r["method"], "backend": meta["backend"],
                     "job_id": meta["job_id"], "shots": meta["shots"], "hellinger_fidelity": h,
                     "ci95": ci, "uniform_baseline": float(np.sum(np.sqrt(p / len(p))) ** 2),
                     "model": r["model"], "two_qubit_gates": r["two_qubit_gates"], "depth": r["depth"],
                     "ecr_flipped": r["ecr_flipped"]})
        print(rows[-1]["circuit"], rows[-1]["method"], round(h, 4), [round(x, 4) for x in ci], flush=True)
    out = {"backend": meta["backend"], "job_id": meta["job_id"], "submitted": meta["submitted"],
           "options": meta["options"], "rows": rows}
    json.dump(out, open(os.path.join(HDIR, "results_fake.json" if a.fake else "results.json"), "w"), indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["submit", "status", "collect"])
    ap.add_argument("--backend", default="auto",
                    help="backend name, or auto: ibm_brisbane > 127-qubit Eagle > least busy")
    ap.add_argument("--fake", action="store_true", help="run locally on FakeBrisbane")
    ap.add_argument("--circuits", nargs="+", default=["mult_8", "hubbard_8", "hhl_8"])
    ap.add_argument("--methods", nargs="+",
                    default=["original", "qiskit_o3", "mkco", "mkco_alap", "mkco_noise"])
    ap.add_argument("--placement", choices=["native", "best"], default="native")
    ap.add_argument("--shots", type=int, default=8192)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    {"submit": submit, "status": status, "collect": collect}[a.cmd](a)


if __name__ == "__main__":
    main()
