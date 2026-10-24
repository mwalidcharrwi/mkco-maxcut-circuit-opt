"""Cross-check every library gate matrix against Qiskit (up to global phase)."""
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
pytest.importorskip("qiskit")
from qiskit import QuantumCircuit
from qiskit.quantum_info import Operator
from mkco import gates as G
from mkco.qasm import parse_qasm


def equal_up_to_phase(a, b, tol=1e-8):
    idx = np.unravel_index(np.argmax(np.abs(b)), b.shape)
    if abs(b[idx]) < 1e-12:
        return False
    ph = a[idx] / b[idx]
    return abs(abs(ph) - 1) < tol and np.allclose(a, ph * b, atol=tol)


CASES = [("id", ()), ("x", ()), ("y", ()), ("z", ()), ("h", ()), ("s", ()), ("sdg", ()),
         ("t", ()), ("tdg", ()), ("sx", ()), ("sxdg", ()), ("rx", (0.3,)), ("ry", (0.4,)),
         ("rz", (0.5,)), ("u1", (0.6,)), ("p", (0.7,)), ("u2", (0.1, 0.2)),
         ("u3", (0.1, 0.2, 0.3)), ("u", (0.3, 0.2, 0.1)), ("cx", ()), ("cy", ()), ("cz", ()),
         ("ch", ()), ("swap", ()), ("crx", (0.3,)), ("cry", (0.3,)), ("crz", (0.3,)),
         ("cu1", (0.3,)), ("cp", (0.3,)), ("cu3", (0.1, 0.2, 0.3)), ("csx", ()),
         ("rxx", (0.3,)), ("ryy", (0.3,)), ("rzz", (0.3,)), ("rzx", (0.3,)),
         ("ccx", ()), ("cswap", ()), ("rccx", ()), ("c3x", ()), ("c3sqrtx", ()),
         ("rc3x", ()), ("c4x", ()), ("cu", (0.1, 0.2, 0.3, 0.4)), ("ecr", ()), ("dcx", ()),
         ("iswap", ()), ("cs", ()), ("csdg", ()), ("ccz", ())]


def qiskit_matrix(name, params, nq):
    qc = QuantumCircuit(nq)
    p = "" if not params else "(" + ",".join(repr(x) for x in params) + ")"
    src = f'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[{nq}];\n{name}{p} ' + \
        ",".join(f"q[{i}]" for i in range(nq)) + ";\n"
    from qiskit import qasm2
    custom = list(qasm2.LEGACY_CUSTOM_INSTRUCTIONS)
    qc = qasm2.loads(src, custom_instructions=custom)
    m = Operator(qc).data
    # qiskit is little-endian: reverse qubit order to compare with ours
    t = m.reshape([2] * (2 * nq))
    perm = list(range(nq))[::-1] + [nq + i for i in range(nq)][::-1]
    return t.transpose(perm).reshape(2 ** nq, 2 ** nq)


def test_all():
    bad = []
    for name, params in CASES:
        nq, _ = G.library_arity(name)
        ours = G.gate_matrix(name, params, nq)
        try:
            ref = qiskit_matrix(name, params, nq)
        except Exception as e:  # gate unknown to qiskit's qasm2 legacy set
            print(f"skip {name}: {type(e).__name__}: {e}")
            continue
        ok = equal_up_to_phase(ours, ref)
        print(f"{name:8s} {'ok' if ok else 'MISMATCH'}")
        if not ok:
            bad.append(name)
    assert not bad, bad


if __name__ == "__main__":
    test_all()


def test_extra_library():
    from qiskit import QuantumCircuit
    from qiskit.circuit import library as L
    extra = {"ryy": L.RYYGate(0.3), "rzx": L.RZXGate(0.3), "ecr": L.ECRGate(),
             "dcx": L.DCXGate(), "iswap": L.iSwapGate(), "cs": L.CSGate(),
             "csdg": L.CSdgGate(), "ccz": L.CCZGate()}
    params = {"ryy": (0.3,), "rzx": (0.3,)}
    bad = []
    for name, gate in extra.items():
        nq = gate.num_qubits
        qc = QuantumCircuit(nq)
        qc.append(gate, list(range(nq)))
        m = Operator(qc).data.reshape([2] * (2 * nq))
        perm = list(range(nq))[::-1] + [nq + i for i in range(nq)][::-1]
        ref = m.transpose(perm).reshape(2 ** nq, 2 ** nq)
        ok = equal_up_to_phase(G.gate_matrix(name, params.get(name, ()), nq), ref)
        print(f"{name:8s} {'ok' if ok else 'MISMATCH'}")
        if not ok:
            bad.append(name)
    assert not bad, bad


if __name__ == "__main__":
    test_extra_library()
