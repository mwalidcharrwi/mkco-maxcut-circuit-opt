"""Run-based commutative rotation merging (optional pre-pass).

Inside one run of a wire every gate commutes on that wire, so all
single-qubit members of the run can be gathered at the position of the first
one and multiplied together (the same idea as rotation merging in Nam et al.
2018 and Qiskit's CommutativeCancellation, expressed on our run structure).
The product is re-synthesised with the fewest gates of the circuit's own
basis; a group is only replaced when that strictly reduces its gate count, and
every replacement is checked numerically against the product it replaces.
"""
from __future__ import annotations

import cmath
import math

import numpy as np

from .circuit import Gate
from .depmodel import DepModel
from .gates import gate_matrix

_TWO_PI = 2 * math.pi


def _angle_mod(t):
    t = math.fmod(t, _TWO_PI)
    if t < 0:
        t += _TWO_PI
    if abs(t - _TWO_PI) < 1e-9:
        t = 0.0
    return t


def _equal_up_to_phase(a, b, tol=1e-8):
    idx = np.unravel_index(np.argmax(np.abs(b)), b.shape)
    ph = a[idx] / b[idx]
    return abs(abs(ph) - 1) < 1e-6 and np.allclose(a, ph * b, atol=tol)


def _synth(u, axis, basis):
    """Fewest gates of `basis` equal to 1q unitary u (with the given axis), or None."""
    if abs(u[0, 0]) > 1e-9 and np.allclose(u / u[0, 0], np.eye(2), atol=1e-9):
        return []
    if axis == "Z":
        theta = _angle_mod(cmath.phase(u[1, 1] / u[0, 0]))
        for name in ("rz", "p", "u1"):
            if name in basis:
                return [(name, (theta if theta <= math.pi else theta - _TWO_PI,))]
        return None
    if axis == "X":
        # u = e^{i phi} rx(theta): u[0,0] = e^{i phi} cos(theta/2), u[0,1] = -i e^{i phi} sin(theta/2)
        ref = u[0, 0] if abs(u[0, 0]) > 1e-9 else 1j * u[0, 1]
        ph = ref / abs(ref)
        c = (u[0, 0] / ph).real
        s = (1j * u[0, 1] / ph).real
        theta = _angle_mod(2 * math.atan2(s, c))
        cands = {0.0: []}
        if "sx" in basis:
            cands[math.pi / 2] = [("sx", ())]
        if "x" in basis:
            cands[math.pi] = [("x", ())]
        if "sxdg" in basis:
            cands[3 * math.pi / 2] = [("sxdg", ())]
        elif "sx" in basis and "x" in basis:
            cands[3 * math.pi / 2] = [("x", ()), ("sx", ())]
        for t, seq in cands.items():
            if abs(theta - t) < 1e-9:
                return seq
        if "rx" in basis:
            return [("rx", (theta,))]
        return None
    return None


def merge_rotations(circuit, max_rounds=6):
    """Return (new_circuit, stats).  Only plain single-qubit library gates merge."""
    basis = {g.name for g in circuit.gates}
    gates = list(circuit.gates)
    stats = {"rounds": 0, "groups_merged": 0, "gates_removed": 0}
    for _ in range(max_rounds):
        c = circuit.copy_with_gates(gates)
        segs, cur = [], []
        for g in gates:                 # barriers split runs
            if g.kind == "barrier":
                segs.append(cur)
                segs.append([g])
                cur = []
            else:
                cur.append(g)
        segs.append(cur)
        new_gates = []
        changed = False
        for seg in segs:
            if len(seg) == 1 and seg[0].kind == "barrier":
                new_gates.extend(seg)
                continue
            if not seg:
                continue
            sub = circuit.copy_with_gates(seg)
            m = DepModel(sub, "depth")
            drop = set()
            replace = {}
            for r in range(m.num_runs):
                if m.run_wire[r] >= circuit.num_qubits:
                    continue
                axis = m.run_axis[r]
                ones = [g for g in m.run_members[r]
                        if seg[g].kind == "gate" and len(seg[g].qubits) == 1
                        and seg[g].cond is None and seg[g].name not in circuit.custom]
                if len(ones) < 2 and not (ones and axis == "I"):
                    continue
                u = np.eye(2, dtype=complex)
                for g in ones:          # order is irrelevant (they commute) but keep it
                    u = gate_matrix(seg[g].name, seg[g].params, 1) @ u
                ax = axis if axis in ("Z", "X") else None
                if ax is None:
                    # pure-identity runs or other axes: drop exact identities only
                    if abs(u[0, 0]) > 1e-9 and np.allclose(u / u[0, 0], np.eye(2), atol=1e-9):
                        seq = []
                    else:
                        continue
                else:
                    seq = _synth(u, ax, basis)
                if seq is None or len(seq) >= len(ones):
                    continue
                v = np.eye(2, dtype=complex)
                for name, params in seq:
                    v = gate_matrix(name, params, 1) @ v
                if not _equal_up_to_phase(v, u):
                    raise AssertionError("rotation merge produced a wrong unitary")
                q = seg[ones[0]].qubits[0]
                replace[ones[0]] = [Gate(n, [q], p) for n, p in seq]
                drop.update(ones[1:])
                stats["groups_merged"] += 1
                stats["gates_removed"] += len(ones) - len(seq)
                changed = True
            for i, g in enumerate(seg):
                if i in drop:
                    continue
                if i in replace:
                    new_gates.extend(replace[i])
                else:
                    new_gates.append(g)
        gates = new_gates
        stats["rounds"] += 1
        if not changed:
            break
    return circuit.copy_with_gates(gates), stats
