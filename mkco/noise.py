"""Calibration-based fidelity estimates and noisy simulation (optional, needs qiskit-aer).

The input is a device calibration (per-gate errors and durations, T1, T2,
readout errors), e.g. the ibm_brisbane snapshot shipped with
qiskit-ibm-runtime's FakeBrisbane, on which the IBM-127 benchmarks are native.

Schedule.  Gates are placed as late as possible (ALAP) with their calibrated
durations; barriers synchronise the qubits they span.  A qubit's idle time is
the time between its first gate and the final measurement during which no
gate acts on it.

ESP (estimated success probability, Nishio et al. 2020, extended with idling):
    prod_gates (1 - e_g) * prod_qubits F_idle(t_q) * prod_qubits (1 - e_ro,q)
with F_idle(t) = (3 + exp(-t/T1) + 2 exp(-t/T2)) / 6, the average fidelity of
the thermal-relaxation channel for time t.  An optional crosstalk factor
multiplies (1 - e_xt) for every pair of ECRs that overlap in time on
neighbouring couplers.

Noisy simulation.  The scheduled circuit is simulated exactly as a density
matrix: every gate is followed by a depolarizing channel with the calibrated
average infidelity, every idle gap by a thermal-relaxation channel, and
readout errors are applied to the final distribution.  `scale` multiplies all
error rates and divides T1 and T2 (scale = 0.1 models a 10x better device).
"""
from __future__ import annotations

import math

import numpy as np

VIRTUAL = {"rz", "p", "u1"}


class Calibration:
    def __init__(self, backend):
        tg = backend.target
        self.name = backend.name
        self.err, self.dur = {}, {}
        for op in ("ecr", "cx", "cz", "sx", "x", "rz", "id"):
            if op not in tg.operation_names:
                continue
            for qargs, props in tg[op].items():
                if props is None:
                    continue
                self.err[(op, tuple(qargs))] = props.error or 0.0
                self.dur[(op, tuple(qargs))] = props.duration or 0.0
        n = backend.num_qubits
        self.t1 = np.array([backend.qubit_properties(q).t1 for q in range(n)])
        self.t2 = np.array([backend.qubit_properties(q).t2 for q in range(n)])
        self.t2 = np.minimum(self.t2, 2 * self.t1)
        self.ro = np.array([tg["measure"][(q,)].error for q in range(n)])
        two = [v for (op, q), v in self.err.items() if len(q) == 2 and v < 0.5]
        self.median_2q = float(np.median(two)) if two else 0.0
        self.broken = {k for k, v in self.err.items() if v >= 0.5}

    def gate(self, g):
        """(error, duration) of a gate instance; arity-based fallback for unknown names."""
        name = g.name if g.name not in VIRTUAL else "rz"
        key = (name, tuple(g.qubits))
        if key in self.err:
            return self.err[key], self.dur[key]
        if len(g.qubits) == 2:                   # e.g. Qiskit-renamed ECRs (ecr_<id>)
            for op in ("ecr", "cx", "cz"):
                if (op, tuple(g.qubits)) in self.err:
                    return self.err[(op, tuple(g.qubits))], self.dur[(op, tuple(g.qubits))]
        if len(g.qubits) == 1:
            return self.err.get(("sx", tuple(g.qubits)), 0.0), self.dur.get(("sx", tuple(g.qubits)), 0.0)
        raise KeyError(f"no calibration for {g}")


def alap_schedule(circuit, cal):
    """Start times (seconds) of every gate under ALAP; barriers synchronise.

    Returns (starts, total_time); starts[i] is None for barriers."""
    gates = circuit.gates
    n = len(gates)
    durs = [0.0 if g.kind == "barrier" else cal.gate(g)[1] for g in gates]
    tail = {}                                     # time from a qubit's next op to the end
    rev_start = [0.0] * n
    for i in range(n - 1, -1, -1):
        g = gates[i]
        t = max((tail.get(q, 0.0) for q in g.qubits), default=0.0)
        if g.kind == "barrier":
            for q in g.qubits:
                tail[q] = t
            rev_start[i] = None
            continue
        rev_start[i] = t + durs[i]
        for q in g.qubits:
            tail[q] = t + durs[i]
    total = max(tail.values(), default=0.0)
    starts = [None if s is None else total - s for s in rev_start]
    return starts, total, durs


def idle_times(circuit, starts, total, durs):
    first, busy = {}, {}
    for g, s, d in zip(circuit.gates, starts, durs):
        if s is None:
            continue
        for q in g.qubits:
            first[q] = min(first.get(q, math.inf), s)
            busy[q] = busy.get(q, 0.0) + d
    return {q: max(0.0, total - first[q] - busy[q]) for q in first}


def _f_idle(t, t1, t2):
    return (3 + math.exp(-t / t1) + 2 * math.exp(-t / t2)) / 6


def esp(circuit, cal, scale=1.0, xt_adjacent=None, xt_error=None):
    """Estimated success probability; returns a dict of its factors."""
    starts, total, durs = alap_schedule(circuit, cal)
    log_g, broken = 0.0, 0
    for g in circuit.gates:
        if g.kind == "barrier":
            continue
        e, _ = cal.gate(g)
        if e >= 0.5:
            broken += 1
            e = cal.median_2q
        log_g += math.log(max(1e-300, 1 - scale * e))
    idle = idle_times(circuit, starts, total, durs)
    log_i = sum(math.log(_f_idle(t, cal.t1[q] / scale, cal.t2[q] / scale)) for q, t in idle.items())
    log_r = sum(math.log(1 - scale * cal.ro[q]) for q in idle)
    log_x, pairs = 0.0, 0
    if xt_adjacent is not None:
        ivs = [(s, s + d, tuple(sorted(g.qubits))) for g, s, d in zip(circuit.gates, starts, durs)
               if s is not None and len(g.qubits) == 2]
        ivs.sort()
        active = []
        for s, e, c in ivs:
            active = [x for x in active if x[1] > s + 1e-15]
            pairs += sum(1 for x in active if frozenset((x[2], c)) in xt_adjacent)
            active.append((s, e, c))
        log_x = pairs * math.log(1 - scale * (xt_error if xt_error is not None else cal.median_2q))
    return {"esp": math.exp(log_g + log_i + log_r + log_x), "log_gates": log_g, "log_idle": log_i,
            "log_readout": log_r, "log_crosstalk": log_x, "xt_pairs_overlapping": pairs,
            "duration_us": total * 1e6, "idle_us": sum(idle.values()) * 1e6,
            "broken_gates": broken}


def noisy_density_matrix(circuit, cal, scale=1.0):
    """Exact noisy simulation of the scheduled circuit on its active qubits.

    Returns (rho as numpy array, ideal statevector, active qubits) with qubit
    order = sorted active physical qubits, little-endian as in Qiskit."""
    from qiskit import QuantumCircuit
    from qiskit.circuit.library import ECRGate
    from qiskit.quantum_info import Statevector
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import depolarizing_error, thermal_relaxation_error

    active = sorted({q for g in circuit.gates for q in g.qubits if g.kind != "barrier"})
    pos = {q: i for i, q in enumerate(active)}
    k = len(active)
    starts, total, durs = alap_schedule(circuit, cal)
    order = sorted((s, i) for i, s in enumerate(starts) if s is not None)
    noisy = QuantumCircuit(k)
    ideal = QuantumCircuit(k)
    free = {}
    for s, i in order:
        g = circuit.gates[i]
        qs = [pos[q] for q in g.qubits]
        for q, p in zip(g.qubits, qs):
            gap = s - free.get(q, s)
            if gap > 1e-12:
                noisy.append(thermal_relaxation_error(cal.t1[q] / scale, cal.t2[q] / scale, gap)
                             .to_instruction(), [p])
        inst = _qiskit_gate(g, ECRGate)
        noisy.append(inst, qs)
        ideal.append(inst, qs)
        e, _ = cal.gate(g)
        if e >= 0.5:
            e = cal.median_2q
        r = min(scale * e, 0.75)
        if r > 0:
            d = 2 ** len(qs)
            noisy.append(depolarizing_error(min(r * d / (d - 1), 1.0), len(qs)).to_instruction(), qs)
        for q in g.qubits:
            free[q] = s + durs[i]
    for q in active:
        gap = total - free.get(q, total)
        if gap > 1e-12:
            noisy.append(thermal_relaxation_error(cal.t1[q] / scale, cal.t2[q] / scale, gap)
                         .to_instruction(), [pos[q]])
    noisy.save_density_matrix()
    sim = AerSimulator(method="density_matrix")
    rho = np.asarray(sim.run(noisy).result().data()["density_matrix"])
    psi = np.asarray(Statevector(ideal).data)
    return rho, psi, active


def _qiskit_gate(g, ECRGate):
    from qiskit.circuit.library import RZGate, SXGate, XGate
    if g.name in ("rz", "p", "u1"):
        return RZGate(g.params[0])
    if g.name == "sx":
        return SXGate()
    if g.name == "x":
        return XGate()
    if len(g.qubits) == 2:
        return ECRGate()
    raise ValueError(f"unsupported gate for noisy simulation: {g}")


def readout_distribution(rho, active, cal, scale=1.0):
    """Measured distribution of a density matrix with symmetric per-qubit readout errors."""
    p = np.real(np.diag(rho)).clip(0)
    k = len(active)
    p = p.reshape([2] * k)
    for i, q in enumerate(active):
        e = scale * cal.ro[q]
        m = np.array([[1 - e, e], [e, 1 - e]])
        axis = k - 1 - i                         # little-endian: qubit i is the last-but-i axis
        p = np.moveaxis(np.tensordot(m, p, axes=([1], [axis])), 0, axis)
    return p.reshape(-1)


def fidelities(rho, psi, active, cal, scale=1.0):
    state = float(np.real(np.conj(psi) @ rho @ psi))
    p = readout_distribution(rho, active, cal, scale)
    q = np.abs(psi) ** 2
    hell = float(np.sum(np.sqrt(p * q)) ** 2)
    return {"state_fidelity": state, "hellinger_fidelity": hell,
            "uniform_hellinger": float(np.sum(np.sqrt(q / len(q))) ** 2)}


def state_aware_esp(circuit, cal, scale=1.0, max_qubits=22):
    """ESP whose idle factors depend on the state of the idling qubit.

    The ideal state is simulated along the ALAP schedule.  An idle gap of
    length t on qubit q costs, to first order (pure-state fidelity),
        gamma * (P1 - |<sigma->|^2)  +  p_phi * (1 - <Z>^2)
    with gamma = 1 - exp(-t/T1) (amplitude damping) and
    p_phi = (1 - exp(-t/T_phi)) / 2, 1/T_phi = 1/T2 - 1/(2 T1) (dephasing).
    A qubit waiting in |0> loses nothing, one waiting in an equal
    superposition dephases fully.  Returns None above max_qubits.
    """
    from .sim import apply_matrix
    active = sorted({q for g in circuit.gates for q in g.qubits if g.kind != "barrier"})
    k = len(active)
    if k > max_qubits:
        return None
    pos = {q: i for i, q in enumerate(active)}
    starts, total, durs = alap_schedule(circuit, cal)
    order = sorted((s, i) for i, s in enumerate(starts) if s is not None)
    psi = np.zeros((2,) * k, dtype=complex)
    psi[(0,) * k] = 1.0
    log_g = log_i = 0.0
    free = {}

    def idle_loss(q, t):
        ax = pos[q]
        a0, a1 = np.take(psi, 0, axis=ax), np.take(psi, 1, axis=ax)
        p1 = float(np.vdot(a1, a1).real)
        sm = complex(np.vdot(a0, a1))
        z = 1 - 2 * p1
        t1, t2 = cal.t1[q] / scale, cal.t2[q] / scale
        gamma = 1 - math.exp(-t / t1)
        rphi = max(0.0, 1 / t2 - 1 / (2 * t1))
        pphi = (1 - math.exp(-t * rphi)) / 2
        return gamma * max(0.0, p1 - abs(sm) ** 2) + pphi * (1 - z * z)

    for s, i in order:
        g = circuit.gates[i]
        for q in g.qubits:
            if q in free and s - free[q] > 1e-12:
                log_i += math.log(max(1e-300, 1 - idle_loss(q, s - free[q])))
        e, _ = cal.gate(g)
        if e >= 0.5:
            e = cal.median_2q
        log_g += math.log(max(1e-300, 1 - scale * e))
        psi = apply_matrix(psi, circuit.gate_unitary(g), [pos[q] for q in g.qubits])
        for q in g.qubits:
            free[q] = s + durs[i]
    for q in active:
        if q in free and total - free[q] > 1e-12:
            log_i += math.log(max(1e-300, 1 - idle_loss(q, total - free[q])))
    log_r = sum(math.log(1 - scale * cal.ro[q]) for q in active)
    return {"sesp": math.exp(log_g + log_i + log_r), "sesp_no_readout": math.exp(log_g + log_i),
            "log_gates": log_g, "log_idle": log_i, "log_readout": log_r}
