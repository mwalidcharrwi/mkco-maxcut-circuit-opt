"""Re-implementation of the Jain & Kumar (NeurIPS 2026 WiML) baseline.

Their method models a circuit as a mixed graph (directed dependency arcs,
undirected arcs between commuting gates that share a qubit), repeatedly takes
the executable subgraph (gates with in-degree 0), extracts a large independent
set from it as the next colour class (layer), and guides the choices with a
beam search.  Their code is not public; this version follows the published
description: candidate independent sets are built greedily under several
orderings and the beam keeps the states with the best lower-bound estimate
(layers so far + remaining critical path / wire load).
"""
from __future__ import annotations

import numpy as np


class _State:
    __slots__ = ("blocking", "remaining", "ready", "wire_left", "layers", "parent", "chosen",
                 "done")

    def copy(self):
        s = _State()
        s.blocking = self.blocking.copy()
        s.remaining = self.remaining.copy()
        s.ready = set(self.ready)
        s.wire_left = self.wire_left.copy()
        s.layers = self.layers
        s.parent = self
        s.chosen = None
        s.done = self.done
        return s


def _independent_sets(ready, res, order_keys, k):
    """Up to k distinct maximal wire-disjoint subsets of `ready`."""
    out, seen = [], set()
    for key in order_keys:
        used = set()
        pick = []
        for i in sorted(ready, key=key):
            ws = res[i]
            if any(w in used for w in ws):
                continue
            used.update(ws)
            pick.append(i)
        t = tuple(sorted(pick))
        if t not in seen:
            seen.add(t)
            out.append(pick)
        if len(out) >= k:
            break
    return out


def jain_kumar_schedule(model, beam=3, cands=3, seed=0):
    """Return unit-gate slots produced by beam-searched independent-set layering."""
    rng = np.random.default_rng(seed)
    nu = len(model.unit)
    if nu == 0:
        return np.zeros(0, dtype=np.int64)
    res = model.unit_resources()
    tail = model.tail
    uidx = model.unit_index
    nxt = model.next_unit_run
    gate_runs = [model.gate_runs[g] for g in model.unit]
    run_members = [[uidx[g] for g in mem] for mem in model.run_unit_members]

    s0 = _State()
    s0.blocking = np.array([len(p) for p in model.preds], dtype=np.int32)
    s0.remaining = np.array([len(m) for m in run_members], dtype=np.int32)
    s0.ready = {i for i in range(nu) if s0.blocking[i] == 0}
    s0.wire_left = model.load_per_wire().astype(np.int32)
    s0.layers = 0
    s0.parent = None
    s0.chosen = None
    s0.done = 0

    deg_cache = {}

    def degree_in_ready(i, ready):
        c = 0
        ws = res[i]
        for j in ready:
            if j != i and any(w in ws for w in res[j]):
                c += 1
        return c

    def expand(st, pick):
        ch = st.copy() if beam > 1 else st
        ch.chosen = pick
        ch.layers = st.layers + 1
        newly = []
        for i in pick:
            ch.ready.discard(i)
            for w in res[i]:
                ch.wire_left[w] -= 1
            for r in gate_runs[i]:
                ch.remaining[r] -= 1
                if ch.remaining[r] == 0 and nxt[r] >= 0:
                    for j in run_members[nxt[r]]:
                        ch.blocking[j] -= 1
                        if ch.blocking[j] == 0:
                            newly.append(j)
        ch.ready.update(newly)
        ch.done = st.done + len(pick)
        return ch

    def bound(st):
        mt = max((tail[i] for i in st.ready), default=-1) + 1
        return st.layers + max(mt, int(st.wire_left.max()) if st.done < nu else 0)

    frontier = [s0]
    history = []                 # for beam == 1 keep the chosen layers directly
    while True:
        if all(st.done == nu for st in frontier):
            break
        children = []
        for st in frontier:
            if st.done == nu:
                children.append(st)
                continue
            ready = st.ready
            keys = [lambda i: (-tail[i], i)]
            if beam > 1:
                rnd = {i: rng.random() for i in ready}
                keys += [lambda i: (degree_in_ready(i, ready), -tail[i]),
                         lambda i: rnd[i]]
            sets = _independent_sets(ready, res, keys, cands if beam > 1 else 1)
            for pick in sets:
                children.append(expand(st, pick))
                if beam == 1:
                    history.append(pick)
        if beam == 1:
            frontier = children[:1]
            continue
        children.sort(key=lambda s: (bound(s), -s.done))
        frontier = children[:beam]
    best = min(frontier, key=lambda s: s.layers)
    slots = np.full(nu, -1, dtype=np.int64)
    if beam == 1:
        for t, pick in enumerate(history):
            for i in pick:
                slots[i] = t
    else:
        layers = []
        st = best
        while st is not None and st.chosen is not None:
            layers.append(st.chosen)
            st = st.parent
        for t, pick in enumerate(reversed(layers)):
            for i in pick:
                slots[i] = t
    del deg_cache
    return slots


def jain_kumar(circuit, metric="depth", beam=None, seed=0):
    """Apply the JK baseline segment by segment (barriers kept)."""
    from .coloring import split_barriers
    from .depmodel import DepModel
    from .schedule import emit_order, verify_order
    out = []
    for kind, payload in split_barriers(circuit):
        if kind == "barrier":
            out.append(payload)
            continue
        sub = circuit.copy_with_gates(payload)
        m = DepModel(sub, metric)
        b = beam if beam is not None else (3 if len(m.unit) <= 25000 else 1)
        slots = jain_kumar_schedule(m, beam=b, seed=seed)
        order = emit_order(m, slots)
        ok, msg = verify_order(m, order)
        if not ok:
            raise RuntimeError(msg)
        out.extend(payload[i] for i in order)
    return circuit.copy_with_gates(out)
