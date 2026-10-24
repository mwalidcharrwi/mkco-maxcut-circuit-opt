"""Independent equivalence checks for reordered circuits.

`audit_reordering` does not use the run/axis machinery of the optimiser.  By
the characterisation of Mazurkiewicz traces, two orderings of the same gates
implement the same unitary whenever every pair of gates whose relative order
differs commutes (sufficient condition; pairs on disjoint qubits always do).
The audit enumerates exactly those pairs that share a qubit, and checks
[A, B] = 0 numerically on the union of their qubits.  It is exact and works
for any number of qubits.

`statevector_check` simulates both circuits on random input states after
relabelling to the active qubits (feasible up to ~20 active qubits).
"""
from __future__ import annotations

import bisect

import numpy as np

from .circuit import Circuit, Gate
from .sim import apply_matrix, equivalent


def _pair_unitaries(circuit, a, b):
    qs = sorted(set(a.qubits) | set(b.qubits))
    pos = {q: i for i, q in enumerate(qs)}
    n = len(qs)
    dim = 2 ** n

    def full(g):
        st = np.eye(dim, dtype=complex).reshape((2,) * n + (dim,))
        st = apply_matrix(st, circuit.gate_unitary(g), [pos[q] for q in g.qubits])
        return st.reshape(dim, dim)

    return full(a), full(b)


def _signature(a, b):
    qs = sorted(set(a.qubits) | set(b.qubits))
    pos = {q: i for i, q in enumerate(qs)}
    return (a.name, tuple(round(p, 12) for p in a.params), tuple(pos[q] for q in a.qubits),
            b.name, tuple(round(p, 12) for p in b.params), tuple(pos[q] for q in b.qubits))


def audit_reordering(circuit, original_gates, new_gates, max_pairs=20_000_000, tol=1e-9):
    """Return dict(ok, inverted_pairs, distinct_pair_types, failures)."""
    orig = [g for g in original_gates if g.kind != "barrier"]
    new = [g for g in new_gates if g.kind != "barrier"]
    idx = {id(g): i for i, g in enumerate(orig)}
    if len(new) != len(orig) or any(id(g) not in idx for g in new) or \
            len({id(g) for g in new}) != len(new):
        return {"ok": False, "reason": "not a permutation of the original gates"}
    seq_by_wire = {}
    for g in new:
        for w in g.wires(circuit.num_qubits):
            seq_by_wire.setdefault(w, []).append(idx[id(g)])
    pairs = set()
    for seq in seq_by_wire.values():
        seen = []
        for x in seq:
            k = bisect.bisect_right(seen, x)
            for y in seen[k:]:          # y was originally after x but now precedes it
                pairs.add((x, y))
            if len(pairs) > max_pairs:
                return {"ok": None, "reason": "too many inverted pairs to audit"}
            seen.insert(k, x)
    cache = {}
    failures = 0
    for x, y in pairs:
        a, b = orig[x], orig[y]
        if a.kind != "gate" or b.kind != "gate" or a.cond is not None or b.cond is not None:
            failures += 1
            continue
        sig = _signature(a, b)
        ok = cache.get(sig)
        if ok is None:
            ua, ub = _pair_unitaries(circuit, a, b)
            ok = bool(np.allclose(ua @ ub, ub @ ua, atol=tol))
            cache[sig] = ok
        if not ok:
            failures += 1
    return {"ok": failures == 0, "inverted_pairs": len(pairs),
            "distinct_pair_types": len(cache), "failures": failures}


def active_relabel(circuit, gates=None, qubits=None):
    """Copy of the circuit on its active qubits only (for simulation)."""
    gates = circuit.gates if gates is None else gates
    if qubits is None:
        qubits = sorted({q for g in gates for q in g.qubits})
    mp = {q: i for i, q in enumerate(qubits)}
    c = Circuit(len(qubits))
    c.custom, c.custom_order = circuit.custom, circuit.custom_order
    c.gates = [Gate(g.name, [mp[q] for q in g.qubits], g.params, kind=g.kind)
               for g in gates if g.kind == "gate"]
    return c


def statevector_check(circuit_a, circuit_b, max_qubits=20, batch=2, seed=7):
    qubits = sorted({q for g in circuit_a.gates for q in g.qubits} |
                    {q for g in circuit_b.gates for q in g.qubits})
    if len(qubits) > max_qubits:
        return None, None
    a = active_relabel(circuit_a, qubits=qubits)
    b = active_relabel(circuit_b, qubits=qubits)
    return equivalent(a, b, batch=batch, seed=seed, max_qubits=max_qubits)
