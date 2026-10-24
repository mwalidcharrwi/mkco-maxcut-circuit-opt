"""Depth/qubit trade-offs by ancilla fan-out = capacitated Max-k-Cut.

Lee et al. (Sec. 5.2) lower the depth of commuting circuits with extra qubits
but leave the algorithm unspecified.  For a wire q on which every gate is
block-diagonal in the computational basis (axis Z: controls, phases, CZ/CP
ends, ...), CNOT fan-out copies q into c_q - 1 fresh ancillas, any Z-axis gate
may act on any copy (on span{|b...b>} the copies are indistinguishable), and
the copies are uncomputed at the end.  Layering then becomes the Max-k-Cut of
Theorem 2 with *capacities*: at most c_q gates per layer on wire q.  The copy
used by each gate is decided per layer after layering, which is strictly more
flexible than fixing a gate-to-copy split beforehand.
"""
from __future__ import annotations

import math

import numpy as np

from .circuit import Circuit, Gate
from .coloring import coloring_to_slots, conflict_graph, dsatur
from .depmodel import DepModel
from .maxkcut import compact, kdescent, used_layers
from .schedule import list_schedule


def _fanout_layers(src, copies):
    """CNOT doubling tree copying `src` into `copies`; returns list of layers."""
    have = [src]
    todo = list(copies)
    layers = []
    while todo:
        layer = []
        for h in list(have):
            if not todo:
                break
            t = todo.pop(0)
            layer.append((h, t))
            have.append(t)
        layers.append(layer)
    return layers


def capacity_lower_bound(model, caps):
    load = model.load_per_wire()
    return int(max(math.ceil(load[w] / caps[w]) for w in range(len(load)) if load[w]))


def fanout_parallelize(circuit, caps, time_limit=10.0, seed=0, baseline=False):
    """Return (new_circuit, info).  `caps` maps qubit -> number of copies (>= 1).

    baseline=True reproduces a fixed, round-robin gate-to-copy split followed by
    DSatur colouring (a natural reading of the extra-qubit heuristic).
    """
    model = DepModel(circuit)
    if not model.is_commuting():
        raise ValueError("fan-out parallelisation needs a commuting circuit")
    nq = circuit.num_qubits
    cap = np.ones(model.num_wires, dtype=np.int64)
    for q, c in caps.items():
        if c > 1:
            axes = {circuit.gate_axes(g)[g.qubits.index(q)] for g in circuit.gates if q in g.qubits}
            if not axes <= {"Z", "I"}:
                raise ValueError(f"qubit {q} is not diagonal for every gate; cannot fan out")
            cap[q] = c
    # ancilla allocation
    anc = {}
    nxt = nq
    for q in range(nq):
        if cap[q] > 1:
            anc[q] = list(range(nxt, nxt + cap[q] - 1))
            nxt += cap[q] - 1
    if baseline:
        # fixed split: k-th gate on q uses copy k mod c, then colour the remapped circuit
        cnt = {}
        remapped = []
        for g in circuit.gates:
            qs = []
            for q in g.qubits:
                if cap[q] > 1:
                    k = cnt.get(q, 0)
                    cnt[q] = k + 1
                    j = k % cap[q]
                    qs.append(q if j == 0 else anc[q][j - 1])
                else:
                    qs.append(q)
            remapped.append(Gate(g.name, qs, g.params))
        tmp = Circuit(nxt)
        tmp.custom = circuit.custom
        tmp.gates = remapped
        m2 = DepModel(tmp)
        slots = compact(coloring_to_slots(m2, dsatur(conflict_graph(m2))))
        layer_gates = {}
        for i, g in enumerate(m2.unit):
            layer_gates.setdefault(int(slots[i]), []).append(remapped[g])
        core_depth = used_layers(slots)
    else:
        # warm starts: capacity-aware list schedule, and DSatur on the uncapacitated
        # conflict graph (always feasible because every capacity is >= 1)
        cands = [compact(list_schedule(model, caps=cap)),
                 compact(coloring_to_slots(model, dsatur(conflict_graph(model))))]
        init = min(cands, key=used_layers)
        lb = capacity_lower_bound(model, cap)
        slots, _ = kdescent(model, init, lb, time_limit=time_limit, caps=cap, seed=seed)
        core_depth = used_layers(slots)
        layer_gates = {}
        for i, g in enumerate(model.unit):
            layer_gates.setdefault(int(slots[i]), []).append(circuit.gates[g])
        # per layer, give each gate on a fanned-out wire a distinct copy
        for t, gs in layer_gates.items():
            used = {}
            new = []
            for g in gs:
                qs = []
                for q in g.qubits:
                    if cap[q] > 1:
                        j = used.get(q, 0)
                        used[q] = j + 1
                        qs.append(q if j == 0 else anc[q][j - 1])
                    else:
                        qs.append(q)
                new.append(Gate(g.name, qs, g.params))
            layer_gates[t] = new
    out = Circuit(nxt, qregs=list(circuit.qregs) + ([("anc", nxt - nq)] if nxt > nq else []))
    out.custom, out.custom_order = circuit.custom, circuit.custom_order
    fan = []
    for q, cs in anc.items():
        for li, layer in enumerate(_fanout_layers(q, cs)):
            while len(fan) <= li:
                fan.append([])
            fan[li].extend(layer)
    for layer in fan:
        for a, b in layer:
            out.add("cx", [a, b])
    for t in sorted(layer_gates):
        out.gates.extend(layer_gates[t])
    for layer in reversed(fan):
        for a, b in layer:
            out.add("cx", [a, b])
    info = {"core_depth": core_depth, "fanout_layers": 2 * len(fan),
            "total_depth": out.depth(), "qubits": int(np.count_nonzero(
                np.bincount([q for g in out.gates for q in g.qubits], minlength=nxt))),
            "ancillas": nxt - nq}
    return out, info
