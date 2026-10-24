"""Crosstalk-aware layering: soft conflicts in the weighted Max-k-Cut.

Two-qubit gates that run in the same layer on *neighbouring* couplers (couplers
that share no qubit but are joined by a hardware edge) suffer spectator /
ZZ crosstalk on fixed-frequency transmon devices such as IBM Eagle (Murali et
al., ASPLOS 2020; Ding et al., MICRO 2020).  Graph colouring can only forbid
or allow such pairs.  In the Max-k-Cut formulation they are simply soft edges
with weight w < 1: we keep the 2q-depth at its certified optimum (hard edges
must all be cut) and minimise the number of crosstalk-prone pairs (soft edges
left uncut).  The chosen layering is locked in with minimal "anchor"
barriers, so a hardware scheduler that retimes gates ASAP reproduces it.
"""
from __future__ import annotations

import numpy as np

from .circuit import Gate
from .coloring import split_barriers
from .depmodel import DepModel
from .maxkcut import MaxKCutState, compact, used_layers
from .schedule import emit_order, list_schedule


def coupler_edges(circuits):
    """Undirected hardware edges inferred from the 2q gates of the given circuits."""
    edges = set()
    for c in circuits:
        for g in c.gates:
            if g.kind == "gate" and len(g.qubits) == 2:
                edges.add(tuple(sorted(g.qubits)))
    return edges


def adjacent_couplers(edges):
    """Pairs of disjoint couplers joined by a hardware edge -> list of (e1, e2)."""
    nbr = {}
    for a, b in edges:
        nbr.setdefault(a, set()).add(b)
        nbr.setdefault(b, set()).add(a)
    el = sorted(edges)
    out = []
    for i, e1 in enumerate(el):
        for e2 in el[i + 1:]:
            if set(e1) & set(e2):
                continue
            if any(y in nbr.get(x, ()) for x in e1 for y in e2):
                out.append((e1, e2))
    return out


def asap_2q_layers(circuit, barrier_sync=True):
    """ASAP layer of every 2q gate (1q gates take no time, barriers synchronise)."""
    level = {}
    layers = []
    for g in circuit.gates:
        if g.kind == "barrier":
            if barrier_sync and g.qubits:
                lv = max(level.get(q, 0) for q in g.qubits)
                for q in g.qubits:
                    level[q] = lv
            continue
        lv = max((level.get(q, 0) for q in g.qubits), default=0)
        if len(g.qubits) >= 2:
            layers.append((lv, tuple(sorted(g.qubits))))
            lv += 1
        for q in g.qubits:
            level[q] = lv
    return layers


def crosstalk_pairs(circuit, adj, barrier_sync=True):
    """Number of same-layer 2q gate pairs on neighbouring couplers."""
    adjset = set()
    for e1, e2 in adj:
        adjset.add((e1, e2))
        adjset.add((e2, e1))
    by_layer = {}
    for lv, e in asap_2q_layers(circuit, barrier_sync):
        by_layer.setdefault(lv, []).append(e)
    total = 0
    for es in by_layer.values():
        for i in range(len(es)):
            for j in range(i + 1, len(es)):
                if (es[i], es[j]) in adjset:
                    total += 1
    return total


def _anchor_emit(circuit, model, slots, gates):
    """Emit `gates` in slot order, adding barriers so that ASAP retiming keeps each
    2q gate in its assigned layer.  Before the gates of layer s are emitted every
    layer-(s-1) gate ends exactly at level s, so a barrier joining a gate that
    could start early with any layer-(s-1) gate ("anchor") delays it to s and
    touches nothing else.  Barriers are added only where needed."""
    order, s_all = emit_order(model, slots, return_slots=True)
    level = {}
    out = []
    prev_layer = []          # qubit tuples of the unit gates of layer s-1
    i = 0
    n = len(order)
    while i < n:
        s = s_all[order[i]]
        j = i
        while j < n and s_all[order[j]] == s:
            j += 1
        block = order[i:j]
        zero = [g for g in block if model.dur[g] == 0]
        unit = [g for g in block if model.dur[g] == 1]
        for g in zero:
            out.append(gates[g])
        if prev_layer:
            anchor = prev_layer[0]
            for g in unit:
                lv = max((level.get(q, 0) for q in gates[g].qubits), default=0)
                if lv < s:
                    qs = sorted(set(gates[g].qubits) | set(anchor))
                    out.append(Gate("barrier", qs, (), kind="barrier"))
                    for q in qs:
                        level[q] = max(level.get(q, 0), s)
        for g in unit:
            out.append(gates[g])
            for q in gates[g].qubits:
                level[q] = s + 1
        if unit:
            prev_layer = [gates[g].qubits for g in unit]
        i = j
    return out


def optimize_crosstalk(circuit, adj, weight=0.1, time_limit=30.0, seed=0, max_iter=200000):
    """Keep the optimal 2q-depth, minimise neighbouring-coupler pairs per layer.

    Returns (circuit_with_anchor_barriers, stats).
    """
    import time
    t0 = time.time()
    out = []
    stats = {"segments": []}
    for kind, payload in split_barriers(circuit):
        if kind == "barrier":
            out.append(payload)
            continue
        sub = circuit.copy_with_gates(payload)
        model = DepModel(sub, "2q")
        nu = len(model.unit)
        if nu == 0:
            out.extend(payload)
            continue
        base = compact(list_schedule(model))
        k = used_layers(base)
        # soft resources: one per neighbouring coupler pair
        cid = {}
        for r, (e1, e2) in enumerate(adj):
            cid.setdefault(e1, []).append(r)
            cid.setdefault(e2, []).append(r)
        n_soft = len(adj)
        soft_res = [cid.get(tuple(sorted(payload[g].qubits)), []) for g in model.unit]
        st = MaxKCutState(model, k, soft={"num": n_soft, "weight": np.full(n_soft, weight),
                                          "res": soft_res}, seed=seed)
        st.load_slots(base)
        before = st.phi_soft / weight
        st.tabu_search(max_iter=max_iter, deadline=t0 + time_limit, soft_phase=True,
                       stall_limit=max(5000, 20 * nu))
        if st.phi_hard > 0:
            st.reset_to(base)
        after = st.phi_soft / weight
        out.extend(_anchor_emit(sub, model, st.slot, payload))
        stats["segments"].append({"layers": k, "xt_pairs_model_before": before,
                                  "xt_pairs_model_after": after,
                                  "iterations": getattr(st, "iterations", 0)})
    stats["time"] = time.time() - t0
    return circuit.copy_with_gates(out), stats
