"""Commutation-aware dependency model (the mixed graph of a circuit).

For every wire (qubit or classical bit) the gates touching it are grouped into
*runs*: maximal consecutive stretches whose members all commute on that wire
(same commutation axis).  Gates in consecutive runs of a wire do not commute
and must keep their relative order; gates inside a run may be reordered
freely as far as this wire is concerned.  The resulting partial order is
exactly the Mazurkiewicz-trace order of the circuit under the pairwise
commutation relation of mkco.gates (docs/THEORY.md, Lemma 2), and it is
stored in O(sum of gate arities) memory: no quadratic edge list is built.

Gates carry a duration in {0, 1}.  Unit gates are the ones being layered;
zero-duration gates (1q gates, and final measurements, when the metric is
the two-qubit depth) are placed afterwards between the layers.
"""
from __future__ import annotations

import numpy as np

from .gates import axes_compatible


def _run_completion(times):
    """Earliest completion of unit jobs with release dates on one machine."""
    t = 0
    for r in sorted(times):
        t = (r if r > t else t) + 1
    return t


class DepModel:
    def __init__(self, circuit, metric="depth"):
        self.circuit = circuit
        gates = circuit.gates
        if any(g.kind == "barrier" for g in gates):
            raise ValueError("split the circuit at barriers before building a DepModel")
        nq = circuit.num_qubits
        self.num_wires = nq + circuit.num_clbits
        self.n = len(gates)
        self.wires = [g.wires(nq) for g in gates]
        if metric == "depth":
            self.dur = np.ones(self.n, dtype=np.int8)
        elif metric == "2q":
            # Unit gates are the multi-qubit gates (as in Circuit.depth("2q") and
            # Qiskit).  Measurements (qubit + clbit) count as unit only when some gate
            # is classically conditioned, since a zero-duration gate must not carry a
            # dependency between unit gates on different wires.
            classical = any(g.cond is not None for g in gates)
            self.dur = np.array([1 if (len(w) >= 2 if classical else len(g.qubits) >= 2) else 0
                                 for g, w in zip(gates, self.wires)], dtype=np.int8)
        else:
            raise ValueError("DepModel metric must be 'depth' or '2q'")

        # axis of every gate on every wire it touches
        self.axes = []
        for g, ws in zip(gates, self.wires):
            ax = list(circuit.gate_axes(g))
            ax.extend([None] * (len(ws) - len(ax)))
            if g.cond is not None:          # conditional gates: be conservative on qubits too
                ax = [a if a == "I" else a for a in ax]
            self.axes.append(ax)

        # ---------------------------------------------------------------- runs
        run_wire, run_axis, run_members = [], [], []
        wire_runs = [[] for _ in range(self.num_wires)]
        cur = [-1] * self.num_wires
        self.gate_runs = []                 # per gate: run id per wire (aligned with self.wires)
        for gi, (ws, ax) in enumerate(zip(self.wires, self.axes)):
            rids = []
            for w, a in zip(ws, ax):
                r = cur[w]
                join = False
                if r >= 0:
                    ra = run_axis[r]
                    if a == "I":
                        join = True
                    elif ra == "I" and a is not None:
                        join = True
                        run_axis[r] = a
                    elif ra is not None and a is not None and axes_compatible(ra, a):
                        join = True
                if not join:
                    r = len(run_wire)
                    run_wire.append(w)
                    run_axis.append(a)
                    run_members.append([])
                    wire_runs[w].append(r)
                    cur[w] = r
                run_members[r].append(gi)
                rids.append(r)
            self.gate_runs.append(rids)
        self.num_runs = len(run_wire)
        self.run_wire = run_wire
        self.run_axis = run_axis
        self.run_members = run_members
        self.wire_runs = wire_runs
        self.run_pos = np.zeros(self.num_runs, dtype=np.int64)
        for w, rs in enumerate(wire_runs):
            for i, r in enumerate(rs):
                self.run_pos[r] = i

        # ------------------------------------------------------ unit structure
        self.unit = [i for i in range(self.n) if self.dur[i] == 1]
        self.unit_index = {g: i for i, g in enumerate(self.unit)}
        self.run_unit_members = [[g for g in mem if self.dur[g] == 1] for mem in run_members]
        prev_unit_run = np.full(self.num_runs, -1, dtype=np.int64)
        next_unit_run = np.full(self.num_runs, -1, dtype=np.int64)
        for w, rs in enumerate(wire_runs):
            last = -1
            for r in rs:
                prev_unit_run[r] = last
                if self.run_unit_members[r]:
                    last = r
            nxt = -1
            for r in reversed(rs):
                next_unit_run[r] = nxt
                if self.run_unit_members[r]:
                    nxt = r
        self.prev_unit_run = prev_unit_run
        self.next_unit_run = next_unit_run
        self.unit_runs = [r for r in range(self.num_runs) if self.run_unit_members[r]]

        # per unit gate: predecessor / successor unit runs (one per wire)
        self.preds = []
        self.succs = []
        for g in self.unit:
            self.preds.append([int(prev_unit_run[r]) for r in self.gate_runs[g] if prev_unit_run[r] >= 0])
            self.succs.append([int(next_unit_run[r]) for r in self.gate_runs[g] if next_unit_run[r] >= 0])

        self._compute_heads_tails()

    # ------------------------------------------------------------------------
    def _compute_heads_tails(self):
        """Earliest start (head) and minimal remaining layers (tail) of every unit gate.

        A whole predecessor run must finish before a gate can start, and the
        members of a run share its wire, so they occupy distinct layers.  The
        earliest completion of a run is therefore a single-machine schedule of
        its members with release dates = their heads (Jackson's rule), which is
        what `_run_completion` computes.  Tails are the mirror image.
        """
        nu = len(self.unit)
        head = np.zeros(nu, dtype=np.int64)
        tail = np.zeros(nu, dtype=np.int64)
        uidx = self.unit_index
        done_head = {}
        for i, g in enumerate(self.unit):
            h = 0
            for p in self.preds[i]:
                c = done_head.get(p)
                if c is None:
                    c = _run_completion([head[uidx[x]] for x in self.run_unit_members[p]])
                    done_head[p] = c
                if c > h:
                    h = c
            head[i] = h
        done_tail = {}
        for i in range(nu - 1, -1, -1):
            t = 0
            for s in self.succs[i]:
                c = done_tail.get(s)
                if c is None:
                    c = _run_completion([tail[uidx[x]] for x in self.run_unit_members[s]])
                    done_tail[s] = c
                if c > t:
                    t = c
            tail[i] = t
        self.head = head
        self.tail = tail
        self.critical_path = int((head + tail).max() + 1) if nu else 0

    def weighted_tails(self, weight):
        """Longest weighted path after each unit gate (weight(gate) per gate).

        Used as a secondary scheduling priority, e.g. remaining 2q-depth when
        the primary objective is the total depth."""
        nu = len(self.unit)
        gates = self.circuit.gates
        w = np.array([weight(gates[g]) for g in self.unit], dtype=float)
        out = np.zeros(nu)
        run_best = {}
        uidx = self.unit_index
        for i in range(nu - 1, -1, -1):
            t = 0.0
            for s in self.succs[i]:
                b = run_best.get(s)
                if b is None:
                    b = max(out[uidx[x]] + w[uidx[x]] for x in self.run_unit_members[s])
                    run_best[s] = b
                if b > t:
                    t = b
            out[i] = t
        return out

    def is_commuting(self):
        """True if every pair of gates commutes (no precedence at all)."""
        return all(p < 0 for p in self.prev_unit_run) and all(
            len(rs) <= 1 for rs in self.wire_runs)

    def unit_resources(self):
        return [self.wires[g] for g in self.unit]

    def load_per_wire(self):
        load = np.zeros(self.num_wires, dtype=np.int64)
        for g in self.unit:
            for w in self.wires[g]:
                load[w] += 1
        return load
