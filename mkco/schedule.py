"""Layer assignments: list scheduling, emission and structural verification."""
from __future__ import annotations

import heapq

import numpy as np


def list_schedule(model, caps=None, rng=None, noise=0.0, priority="tail", secondary=None):
    """Commutation-aware greedy layering (strong baseline / warm start).

    At every layer the ready unit gates (all predecessor runs finished) are
    packed greedily by priority: longest remaining chain first, then the
    gate's total wire load.  Returns slots for model.unit (same order).
    """
    nu = len(model.unit)
    if nu == 0:
        return np.zeros(0, dtype=np.int64)
    caps = np.ones(model.num_wires, dtype=np.int64) if caps is None else np.asarray(caps)
    load = model.load_per_wire()
    res = model.unit_resources()
    gload = np.array([load[r].sum() for r in res], dtype=float)
    if priority == "tail":
        key = -(model.tail * 1e6 + gload)
        if secondary is not None:     # lexicographic: tail, then secondary tail, then load
            key = -(model.tail * 1e12 + np.asarray(secondary) * 1e6 + gload)
    elif priority == "load":
        key = -(gload * 1e6 + model.tail)
    else:
        raise ValueError(priority)
    if noise and rng is not None:
        key = key + noise * rng.random(nu) * 1e6
    blocking = np.array([len(p) for p in model.preds], dtype=np.int64)
    remaining = np.array([len(m) for m in model.run_unit_members], dtype=np.int64)
    slots = np.full(nu, -1, dtype=np.int64)
    ready = [(key[i], i) for i in range(nu) if blocking[i] == 0]
    heapq.heapify(ready)
    t = 0
    done = 0
    uidx = model.unit_index
    while done < nu:
        used = {}
        placed = []
        deferred = []
        while ready:
            k_, i = heapq.heappop(ready)
            ok = True
            for w in res[i]:
                if used.get(w, 0) >= caps[w]:
                    ok = False
                    break
            if ok:
                for w in res[i]:
                    used[w] = used.get(w, 0) + 1
                slots[i] = t
                placed.append(i)
            else:
                deferred.append((k_, i))
        for item in deferred:
            heapq.heappush(ready, item)
        done += len(placed)
        newly = []
        for i in placed:
            for r in model.gate_runs[model.unit[i]]:
                remaining[r] -= 1
                if remaining[r] == 0:
                    nr = model.next_unit_run[r]
                    if nr >= 0:
                        for g2 in model.run_unit_members[nr]:
                            j = uidx[g2]
                            blocking[j] -= 1
                            if blocking[j] == 0:
                                newly.append(j)
        for j in newly:
            heapq.heappush(ready, (key[j], j))
        t += 1
        if not placed and not ready:
            raise RuntimeError("list scheduler stalled (cyclic dependencies?)")
    return slots


def serial_sgs(model, priority, caps=None):
    """Serial schedule generation: repeatedly take the eligible gate (all
    predecessor runs placed) with the smallest priority and put it in the
    earliest layer where its predecessors are finished and its wires are free.
    Always returns a valid layering, whatever the priorities are."""
    nu = len(model.unit)
    if nu == 0:
        return np.zeros(0, dtype=np.int64)
    caps = np.ones(model.num_wires, dtype=np.int64) if caps is None else np.asarray(caps)
    res = model.unit_resources()
    blocking = np.array([len(p) for p in model.preds], dtype=np.int64)
    remaining = np.array([len(m) for m in model.run_unit_members], dtype=np.int64)
    run_max = np.full(model.num_runs, -1, dtype=np.int64)
    occ = {}
    slots = np.full(nu, -1, dtype=np.int64)
    heap = [(float(priority[i]), i) for i in range(nu) if blocking[i] == 0]
    heapq.heapify(heap)
    uidx = model.unit_index
    while heap:
        _, i = heapq.heappop(heap)
        t = 0
        for p in model.preds[i]:
            t = max(t, run_max[p] + 1)
        while any(occ.get((t, w), 0) >= caps[w] for w in res[i]):
            t += 1
        slots[i] = t
        for w in res[i]:
            occ[(t, w)] = occ.get((t, w), 0) + 1
        for r in model.gate_runs[model.unit[i]]:
            if t > run_max[r]:
                run_max[r] = t
            remaining[r] -= 1
            if remaining[r] == 0:
                nr = model.next_unit_run[r]
                if nr >= 0:
                    for g2 in model.run_unit_members[nr]:
                        j = uidx[g2]
                        blocking[j] -= 1
                        if blocking[j] == 0:
                            heapq.heappush(heap, (float(priority[j]), j))
    if (slots < 0).any():
        raise RuntimeError("serial SGS did not place every gate")
    return slots


def asap_slots_of_order(model):
    """Slots of the ASAP layering of the original gate order (original depth)."""
    level = {}
    slots = np.zeros(len(model.unit), dtype=np.int64)
    for i, g in enumerate(model.unit):
        ws = model.wires[g]
        s = max((level.get(w, 0) for w in ws), default=0)
        slots[i] = s
        for w in ws:
            level[w] = s + 1
    return slots


def emit_order(model, slots, return_slots=False):
    """Order of all gates (indices into circuit.gates) for a unit-slot assignment.

    Zero-duration gates go right after the last unit gate of their preceding
    unit run on their wire; ties are broken so that the original relative
    order of non-commuting gates is preserved (docs/THEORY.md, Sec. 2).
    """
    n = model.n
    s_all = np.zeros(n, dtype=np.int64)
    run_max = np.full(model.num_runs, -1, dtype=np.int64)
    for i, g in enumerate(model.unit):
        s_all[g] = slots[i]
        for r in model.gate_runs[g]:
            if slots[i] > run_max[r]:
                run_max[r] = slots[i]
    for g in range(n):
        if model.dur[g] == 0:
            s = 0
            for r in model.gate_runs[g]:
                p = model.prev_unit_run[r]
                if p >= 0:
                    s = max(s, run_max[p] + 1)
            s_all[g] = s
    keys = sorted(range(n), key=lambda g: (s_all[g], model.dur[g], g))
    if return_slots:
        return keys, s_all
    return keys


def verify_order(model, order):
    """Exact check that `order` is a linear extension of the dependency order.

    For every wire the run index of successive gates must never decrease.
    Returns (ok, message).
    """
    if sorted(order) != list(range(model.n)):
        return False, "order is not a permutation of the gates"
    last = np.full(model.num_wires, -1, dtype=np.int64)
    for pos, g in enumerate(order):
        for w, r in zip(model.wires[g], model.gate_runs[g]):
            rp = model.run_pos[r]
            if rp < last[w]:
                return False, f"gate {g} moved across a non-commuting gate on wire {w}"
            last[w] = rp
    return True, "ok"


def slots_valid(model, slots, caps=None):
    """Check precedence (strict) and per-layer wire capacities of a slot vector."""
    caps = np.ones(model.num_wires, dtype=np.int64) if caps is None else np.asarray(caps)
    occ = {}
    for i, g in enumerate(model.unit):
        for w in model.wires[g]:
            key = (int(slots[i]), w)
            occ[key] = occ.get(key, 0) + 1
            if occ[key] > caps[w]:
                return False
    run_min = {}
    run_max = {}
    for i, g in enumerate(model.unit):
        for r in model.gate_runs[g]:
            run_min[r] = min(run_min.get(r, 1 << 60), slots[i])
            run_max[r] = max(run_max.get(r, -1), slots[i])
    for r in run_max:
        nr = model.next_unit_run[r]
        if nr >= 0 and run_min[nr] <= run_max[r]:
            return False
    return True
