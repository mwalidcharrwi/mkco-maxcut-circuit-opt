"""Re-run the Qiskit O3 baseline for benchmarks where the directed coupling map
made Qiskit fail (its re-synthesis produced ECRs it could not re-orient).
The retry uses a bidirectional coupling map, which can only help Qiskit
(reverse ECRs would cost extra single-qubit gates on hardware)."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from mkco.optimize import optimize                         # noqa: E402
from mkco.qasm import load_qasm, parse_qasm                # noqa: E402
from mkco.crosstalk import adjacent_couplers, coupler_edges  # noqa: E402
from mkco.verify import audit_reordering                   # noqa: E402
from run_ibm127 import metrics                             # noqa: E402


def qiskit_o3_bidirectional(path):
    from qiskit import qasm2, transpile
    from qiskit.transpiler import CouplingMap
    qc = qasm2.load(path, custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS)
    edges = set()
    for i in qc.data:
        if i.operation.num_qubits == 2:
            a, b = (qc.find_bit(q).index for q in i.qubits)
            edges.update({(a, b), (b, a)})
    cm = CouplingMap(sorted(edges))
    for q in range(qc.num_qubits):
        if q not in cm.physical_qubits:
            cm.add_physical_qubit(q)
    t = time.time()
    out = transpile(qc, basis_gates=["rz", "sx", "x", "ecr"], coupling_map=cm,
                    initial_layout=list(range(qc.num_qubits)), optimization_level=3,
                    seed_transpiler=0)
    return parse_qasm(qasm2.dumps(out)), time.time() - t


def main(bdir="benchmarks/ibm127", outdir="results/ibm127"):
    path = os.path.join(outdir, "results.json")
    res = json.load(open(path))
    files = {os.path.splitext(f)[0]: os.path.join(bdir, f) for f in os.listdir(bdir)}
    adj = adjacent_couplers(coupler_edges(load_qasm(p) for p in files.values()))
    for name, r in res.items():
        if "error" not in r["methods"].get("qiskit_o3", {}):
            continue
        print("retrying Qiskit O3 (bidirectional) for", name, flush=True)
        q3, tq = qiskit_o3_bidirectional(files[name])
        m = metrics(q3, adj)
        m.update({"time_s": round(tq, 2), "coupling": "bidirectional (retry)"})
        r["methods"]["qiskit_o3"] = m
        open(os.path.join(outdir, f"{name}__qiskit_o3.qasm"), "w").write(q3.to_qasm())
        t = time.time()
        qm, rep = optimize(q3, metric="depth", time_limit=60)
        m2 = metrics(qm, adj)
        m2.update({"time_s": round(time.time() - t, 2), "lower_bound": rep["lower_bound"],
                   "certified_optimal": rep["certified_optimal"],
                   "verification": {"audit": audit_reordering(q3, q3.gates, qm.gates)}})
        r["methods"]["qiskit_o3+mkco"] = m2
        open(os.path.join(outdir, f"{name}__qiskit_o3+mkco.qasm"), "w").write(qm.to_qasm())
        print(name, "O3", m["depth"], "O3+MKCO", m2["depth"], flush=True)
        json.dump(res, open(path, "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
