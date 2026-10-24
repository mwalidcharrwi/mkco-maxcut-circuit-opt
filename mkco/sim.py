"""Small dense state-vector simulator used for equivalence checking."""
from __future__ import annotations

import numpy as np


def apply_matrix(state, m, qubits):
    """Apply a k-qubit matrix to tensor `state` (qubit axes first, batch axes last)."""
    k = len(qubits)
    t = np.asarray(m).reshape((2,) * (2 * k))
    out = np.tensordot(t, state, axes=(list(range(k, 2 * k)), list(qubits)))
    return np.moveaxis(out, list(range(k)), list(qubits))


def _apply_mcx(state, qubits):
    *ctrl, tgt = qubits
    idx = [slice(None)] * state.ndim
    for c in ctrl:
        idx[c] = 1
    sub = state[tuple(idx)]
    # the target axis index inside `sub` shifts left by the number of controls before it
    t_axis = tgt - sum(1 for c in ctrl if c < tgt)
    flipped = np.flip(sub, axis=t_axis).copy()
    state = state.copy()
    state[tuple(idx)] = flipped
    return state


def _apply_phase_all_ones(state, qubits, ph):
    idx = [slice(None)] * state.ndim
    for c in qubits:
        idx[c] = 1
    state = state.copy()
    state[tuple(idx)] *= ph
    return state


def apply_gate(state, gate, circuit):
    """Apply one Gate of `circuit` to the state tensor."""
    name, qs = gate.name, gate.qubits
    if name in ("mcx", "c3x", "c4x", "ccx", "toffoli") and len(qs) >= 3:
        return _apply_mcx(state, qs)
    if name in ("mcz", "ccz") and len(qs) >= 3:
        return _apply_phase_all_ones(state, qs, -1.0)
    if name in ("mcphase", "mcp", "mcu1") and len(qs) >= 3:
        return _apply_phase_all_ones(state, qs, np.exp(1j * gate.params[0]))
    return apply_matrix(state, circuit.gate_unitary(gate), qs)


def random_states(n, batch, seed=0):
    rng = np.random.default_rng(seed)
    v = rng.normal(size=(2 ** n, batch)) + 1j * rng.normal(size=(2 ** n, batch))
    v /= np.linalg.norm(v, axis=0, keepdims=True)
    return v.reshape((2,) * n + (batch,))


def run_unitary_part(circuit, state):
    for g in circuit.gates:
        if g.kind != "gate":
            continue
        if g.cond is not None:
            raise ValueError("classically-controlled gates cannot be simulated here")
        state = apply_gate(state, g, circuit)
    return state


def equivalent(c1, c2, batch=3, seed=1, max_qubits=20, tol=1e-7):
    """Check c1 == c2 (up to global phase) on random input states.

    Measurements, resets and barriers are ignored, so call this only on circuits
    whose non-unitary operations are terminal.  Returns (ok, min_fidelity) or
    (None, None) when the circuit is too large to simulate.
    """
    n = max(c1.num_qubits, c2.num_qubits)
    if n > max_qubits:
        return None, None
    s0 = random_states(n, batch, seed)
    a = run_unitary_part(c1, s0.copy()).reshape(2 ** n, batch)
    b = run_unitary_part(c2, s0.copy()).reshape(2 ** n, batch)
    overlaps = np.einsum("ij,ij->j", a.conj(), b)
    # same global phase for every input state is required for unitary equality
    phases = overlaps / np.abs(overlaps)
    fid = float(np.min(np.abs(overlaps)))
    phase_ok = bool(np.allclose(phases, phases[0], atol=1e-6))
    return (fid > 1 - tol and phase_ok), fid
