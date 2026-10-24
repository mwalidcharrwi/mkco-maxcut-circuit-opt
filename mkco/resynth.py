"""Single-qubit resynthesis (optional rewrite mode).

Pure reordering is certified optimal on the IBM benchmarks, but transpiled
circuits contain long single-qubit chains (rz sx rz sx rz ...) that only a
rewrite can shorten.  This module

1. fuses every maximal run of consecutive single-qubit gates of a wire (no
   other gate on that wire in between) into one 2x2 unitary, and
2. re-synthesises it with the fewest gates of the circuit's basis: ZSX
   (rz, sx, x) when available, otherwise one u3.

A replacement is made only when it lowers (physical gates, total gates), and
each one is checked numerically against the product it replaces.  Combined
with the run-based same-axis merge of `merge.py` (which gathers rotations
across commuting two-qubit gates) and iterated to a fixed point, this is the
`rewrite` pre-pass of MKCO; the Max-k-Cut reordering then runs on the result.
"""
from __future__ import annotations

import cmath
import math

import numpy as np

from .circuit import Gate
from .gates import gate_matrix
from .merge import merge_rotations

TWO_PI = 2 * math.pi
VIRTUAL = {"rz", "p", "u1"}


def _wrap(a):
    a = math.fmod(a, TWO_PI)
    if a > math.pi:
        a -= TWO_PI
    elif a <= -math.pi:
        a += TWO_PI
    return a


def _zero(a, tol=1e-10):
    return abs(_wrap(a)) < tol


def zyz_angles(u):
    """(theta, phi, lam) with u = e^{i g} Rz(phi) Ry(theta) Rz(lam)."""
    det = np.linalg.det(u)
    v = u / cmath.sqrt(det)
    theta = 2 * math.atan2(abs(v[1, 0]), abs(v[0, 0]))
    if abs(v[0, 0]) < 1e-12:          # theta = pi: only phi - lam is defined
        s = 2 * cmath.phase(v[1, 0])
        return theta, s, 0.0
    if abs(v[1, 0]) < 1e-12:          # theta = 0: only phi + lam is defined
        return theta, 2 * cmath.phase(v[1, 1]), 0.0
    psum = 2 * cmath.phase(v[1, 1])
    pdif = 2 * cmath.phase(v[1, 0])
    return theta, (psum + pdif) / 2, (psum - pdif) / 2


def _seq_matrix(seq):
    m = np.eye(2, dtype=complex)
    for name, params in seq:
        m = gate_matrix(name, params, 1) @ m
    return m


def _equal_up_to_phase(a, b, tol=1e-8):
    idx = np.unravel_index(np.argmax(np.abs(b)), b.shape)
    if abs(b[idx]) < 1e-12:
        return False
    ph = a[idx] / b[idx]
    return abs(abs(ph) - 1) < 1e-6 and np.allclose(a, ph * b, atol=tol)


def _clean(seq):
    out = []
    for name, params in seq:
        if name in VIRTUAL and _zero(params[0]):
            continue
        if name in VIRTUAL:
            params = (_wrap(params[0]),)
        out.append((name, params))
    return out


def synth_zsx(u):
    """Shortest (rz, sx, x) sequence (time order) equal to u up to phase."""
    theta, phi, lam = zyz_angles(u)
    cands = []
    if abs(theta) < 1e-9:
        cands.append([("rz", (phi + lam,))])
    if abs(theta - math.pi / 2) < 1e-9:
        cands.append([("rz", (lam - math.pi / 2,)), ("sx", ()), ("rz", (phi + math.pi / 2,))])
    if abs(theta - math.pi) < 1e-9:
        cands.append([("rz", (lam + math.pi,)), ("x", ()), ("rz", (phi,))])
        cands.append([("rz", (lam,)), ("x", ()), ("rz", (phi + math.pi,))])
    cands.append([("rz", (lam,)), ("sx", ()), ("rz", (theta + math.pi,)), ("sx", ()),
                  ("rz", (phi + math.pi,))])
    best = None
    for c in cands:
        c = _clean(c)
        if _equal_up_to_phase(_seq_matrix(c), u):
            if best is None or _cost(c) < _cost(best):
                best = c
    if best is None:
        raise AssertionError("ZSX synthesis failed")
    return best


def synth_u3(u):
    theta, phi, lam = zyz_angles(u)
    if abs(theta) < 1e-9 and _zero(phi + lam):
        return []
    seq = [("u3", (theta, _wrap(phi), _wrap(lam)))]
    if not _equal_up_to_phase(_seq_matrix(seq), u):
        raise AssertionError("u3 synthesis failed")
    return seq


def _cost(seq):
    phys = sum(1 for n, _ in seq if n not in VIRTUAL)
    return (phys, len(seq))


def fuse_single_qubit(circuit):
    """One pass of adjacent single-qubit fusion.  Returns (circuit, n_replaced_groups)."""
    names = {g.name for g in circuit.gates}
    synth = synth_zsx if {"rz", "sx"} <= names else synth_u3   # keep the circuit's basis
    gates = circuit.gates
    nq = circuit.num_qubits
    pending = {}                  # qubit -> list of indices of the current 1q chain
    groups = []

    def close(q):
        idx = pending.pop(q, None)
        if idx and len(idx) >= 2:
            groups.append(idx)

    for i, g in enumerate(gates):
        one = (g.kind == "gate" and len(g.qubits) == 1 and g.cond is None
               and g.name not in circuit.custom)
        if one:
            pending.setdefault(g.qubits[0], []).append(i)
        else:
            for w in g.wires(nq):
                if w < nq:
                    close(w)
    for q in list(pending):
        close(q)
    replace, drop = {}, set()
    for idx in groups:
        seq_in = [(gates[i].name, gates[i].params) for i in idx]
        u = _seq_matrix(seq_in)
        new = synth(u)
        if _cost(new) >= _cost(seq_in):
            continue
        if not _equal_up_to_phase(_seq_matrix(new) if new else np.eye(2), u):
            raise AssertionError("fusion produced a wrong unitary")
        q = gates[idx[0]].qubits[0]
        replace[idx[-1]] = [Gate(n, [q], p) for n, p in new]
        drop.update(idx[:-1])
    out = []
    for i, g in enumerate(gates):
        if i in drop:
            continue
        out.extend(replace.get(i, [g]))
    return circuit.copy_with_gates(out), len(replace)


def rewrite_single_qubit(circuit, max_rounds=8):
    """Fixed point of (same-axis run merge, adjacent 1q fusion)."""
    stats = {"rounds": 0, "fused_groups": 0, "merged_groups": 0}
    cur = circuit
    for _ in range(max_rounds):
        before = cur.size()
        cur, ms = merge_rotations(cur)
        cur, nf = fuse_single_qubit(cur)
        stats["rounds"] += 1
        stats["merged_groups"] += ms["groups_merged"]
        stats["fused_groups"] += nf
        if cur.size() >= before:
            break
    stats["gates_before"] = circuit.size()
    stats["gates_after"] = cur.size()
    return cur, stats
