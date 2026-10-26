"""Commutation-aware ("run-aware") two-qubit block resynthesis.

Plain block KAK only sees blocks that are contiguous in the given gate order.
regroup_both_ways first applies a legal reordering that keeps gates of one
qubit pair together wherever commutation allows, so KAK sees larger blocks.

Part 1, logical (untranspiled) circuits (CX basis, all-to-all):
  kak            block KAK + 1q rewrite, iterated (plain blocks)
  regroup_kak    the same with commutation-aware block formation
  qiskit_o3      Qiskit O3, basis {cx, rz, sx, x}, no coupling map (a baseline
                 here because these circuits are not transpiled yet)
  o3+regroup_kak our pass applied to Qiskit's output
  every result is then layered by MKCO; depth and 2q-gate count are reported.
Part 2, the IBM-127 benchmarks (already transpiled at level 3): ECRs removed
by plain vs regrouped block KAK.

Writes results/structured/regroup.json.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mkco import generators as gen                       # noqa: E402
from mkco.blocks import full_rewrite, regroup_both_ways, resynthesize_blocks  # noqa: E402
from mkco.optimize import optimize                       # noqa: E402
from mkco.qasm import load_qasm, parse_qasm              # noqa: E402
from mkco.verify import statevector_check                # noqa: E402

OUT = "results/structured/regroup.json"


def n2q(c):
    return sum(1 for g in c.gates if len(g.qubits) == 2)


def qiskit_o3(c):
    from qiskit import qasm2, transpile
    qc = qasm2.loads(c.to_qasm(), custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS)
    out = transpile(qc, basis_gates=["cx", "rz", "sx", "x"], optimization_level=3, seed_transpiler=0)
    return parse_qasm(qasm2.dumps(out))


def layered(c):
    o, rep = optimize(c, metric="depth", time_limit=10)
    return o, {"cx": n2q(o), "depth": o.depth(), "depth_2q": o.depth("2q"),
               "certified_optimal": rep["certified_optimal"]}


def logical_cases():
    cs = []
    for n, t in ((8, 40), (10, 60), (12, 80), (16, 120), (20, 160)):
        for s in range(2):
            cs.append(gen.phase_polynomial(n, t, seed=s))
    for n in (10, 12, 16):
        cs.append(gen.trotter_ising(n, 4, seed=0, graph="reg3"))
        cs.append(gen.qaoa_maxcut(n, p=2, decompose=True, seed=0))
    for s in range(3):
        cs.append(gen.random_clifford_t(10, 400, seed=s))
    return cs


def ibm_rows(bdir, rdir):
    """ECRs removed by plain vs regrouped block KAK on the (already transpiled) inputs."""
    for f in sorted(os.listdir(bdir)):
        name = os.path.splitext(f)[0]
        row = {"circuit": name}
        for tag, path in (("input", os.path.join(bdir, f)),):
            if not os.path.exists(path):
                continue
            c = load_qasm(path)
            _, s0 = resynthesize_blocks(c)
            rg, moved = regroup_both_ways(c)
            _, s1 = resynthesize_blocks(rg)
            row[tag] = {"ecr": n2q(c), "plain_ecr_removed": s0["ecr_removed"],
                        "regroup_ecr_removed": s1["ecr_removed"], "gates_moved": moved}
        yield row


def main():
    rows = {"logical": [], "ibm127": []}
    for c in logical_cases():
        row = {"circuit": c.name, "qubits": c.num_qubits, "cx_in": n2q(c)}
        t = time.time()
        a, _ = full_rewrite(c, regroup=False)
        b, _ = full_rewrite(c, regroup=True)
        q = qiskit_o3(c)
        qb, _ = full_rewrite(q, regroup=True)
        for name, x in (("kak", a), ("regroup_kak", b), ("qiskit_o3", q), ("o3+regroup_kak", qb)):
            o, m = layered(x)
            ok, fid = statevector_check(c, o)
            m["statevector_ok"] = None if ok is None else bool(ok)
            row[name] = m
        row["time_s"] = round(time.time() - t, 1)
        rows["logical"].append(row)
        print(row, flush=True)
        json.dump(rows, open(OUT, "w"), indent=1)
    for row in ibm_rows("benchmarks/ibm127", "results/ibm127"):
        rows["ibm127"].append(row)
        print(row, flush=True)
        json.dump(rows, open(OUT, "w"), indent=1)


if __name__ == "__main__":
    main()
