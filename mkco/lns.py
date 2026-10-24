"""Large-neighbourhood search for general (non-commuting) circuits.

Window compression: take the gates W currently in layers [a, b] and ask for a
re-layering of W into layers [a, b-1] (everything after b shifts down by one).
Because every dependency chain between two gates of W runs through layers
[a, b], the sub-problem is an *isolated* precedence-constrained Max-k-Cut with
k = b - a (docs/THEORY.md, Proposition 8).  Windows are small, so any Max-k-Cut
backend works on them -- tabu search, exhaustive enumeration, or QAOA.

Justification (forward/backward passes) moves gates as early / late as their
neighbours allow; it often frees layers on its own and changes which gates
share a window, which keeps the LNS from stalling.
"""
from __future__ import annotations

import time

import numpy as np

from .maxkcut import compact, used_layers


def _occupied(occ, t, ws, caps):
    for w in ws:
        if occ.get((t, w), 0) >= caps[w]:
            return True
    return False


def justify(model, slots, direction, caps=None):
    """Serial re-placement of every gate as early ('left') or late ('right') as possible."""
    nu = len(model.unit)
    if nu == 0:
        return slots
    caps = np.ones(model.num_wires, dtype=np.int64) if caps is None else caps
    res = model.unit_resources()
    occ = {}
    new = np.zeros(nu, dtype=np.int64)
    placed = np.zeros(nu, dtype=bool)
    if direction == "left":
        run_max = np.full(model.num_runs, -(1 << 60), dtype=np.int64)
        for i in sorted(range(nu), key=lambda i: (slots[i], i)):
            lo = 0
            for p in model.preds[i]:
                lo = max(lo, run_max[p] + 1)
            t = lo
            while _occupied(occ, t, res[i], caps):
                t += 1
            new[i] = t
            for w in res[i]:
                occ[(t, w)] = occ.get((t, w), 0) + 1
            for r in model.gate_runs[model.unit[i]]:
                run_max[r] = max(run_max[r], t)
    else:
        top = int(slots.max())
        run_min = np.full(model.num_runs, 1 << 60, dtype=np.int64)
        for i in sorted(range(nu), key=lambda i: (-slots[i], -i)):
            hi = top
            for q in model.succs[i]:
                hi = min(hi, run_min[q] - 1)
            t = hi
            while _occupied(occ, t, res[i], caps):
                t -= 1
            new[i] = t
            for w in res[i]:
                occ[(t, w)] = occ.get((t, w), 0) + 1
            for r in model.gate_runs[model.unit[i]]:
                run_min[r] = min(run_min[r], t)
    del placed
    return compact(new - new.min())


def fbi(model, slots, caps=None, max_rounds=20):
    """Forward-backward improvement: alternate justifications until no gain."""
    best = compact(slots)
    for _ in range(max_rounds):
        s = justify(model, justify(model, best, "right", caps), "left", caps)
        if used_layers(s) < used_layers(best):
            best = s
        else:
            # keep the left-justified version even without gain (normal form)
            return s if used_layers(s) == used_layers(best) else best
    return best


# ---------------------------------------------------------------------------
# window sub-problem: exact Max-k-Cut feasibility by depth-first search
# ---------------------------------------------------------------------------

def _window_instance(model, slots, a, b):
    W = [i for i in range(len(slots)) if a <= slots[i] <= b]
    W.sort(key=lambda i: (slots[i], i))
    inW = {i: j for j, i in enumerate(W)}
    # internal predecessor lists (via runs) restricted to W
    preds = []
    for i in W:
        ps = []
        for p in model.preds[i]:
            for g in model.run_unit_members[p]:
                j = inW.get(model.unit_index[g])
                if j is not None:
                    ps.append(j)
        preds.append(sorted(set(ps)))
    succs = [[] for _ in W]
    for j, ps in enumerate(preds):
        for p in ps:
            succs[p].append(j)
    n = len(W)
    head = [0] * n
    for j in range(n):
        for p in preds[j]:
            head[j] = max(head[j], head[p] + 1)
    tail = [0] * n
    for j in range(n - 1, -1, -1):
        for s in succs[j]:
            tail[j] = max(tail[j], tail[s] + 1)
    res = [model.wires[model.unit[i]] for i in W]
    return W, preds, succs, head, tail, res


def window_lower_bound(n, preds, head, tail, res):
    """Jackson bound inside the window (per wire) and the internal critical path."""
    lb = max((head[j] + tail[j] + 1 for j in range(n)), default=0)
    by_wire = {}
    for j in range(n):
        for w in res[j]:
            by_wire.setdefault(w, []).append(j)
    for jobs in by_wire.values():
        jobs.sort(key=lambda j: head[j])
        import heapq
        heap, t, k, val, done = [], 0, 0, 0, 0
        while done < len(jobs):
            if not heap and k < len(jobs) and head[jobs[k]] > t:
                t = head[jobs[k]]
            while k < len(jobs) and head[jobs[k]] <= t:
                heapq.heappush(heap, -tail[jobs[k]])
                k += 1
            q = -heapq.heappop(heap)
            val = max(val, t + 1 + q)
            done += 1
            t += 1
        lb = max(lb, val)
    return lb


def solve_window_exact(n, preds, head, tail, res, k, node_limit=20000, caps=None):
    """Exhaustive Max-k-Cut feasibility (all conflicts cut, all arcs forward) by DFS.

    Returns a list of slots in [0, k-1] or None.
    """
    # sorting on head gives a topological order (head[p] < head[j] for p -> j)
    order = sorted(range(n), key=lambda j: (head[j], -tail[j]))
    slot = [-1] * n
    occ = {}
    nodes = [0]

    def dfs(idx):
        if idx == n:
            return True
        nodes[0] += 1
        if nodes[0] > node_limit:
            return False
        j = order[idx]
        lo = head[j]
        for p in preds[j]:
            lo = max(lo, slot[p] + 1)
        hi = k - 1 - tail[j]
        for t in range(lo, hi + 1):
            if any(occ.get((t, w), 0) >= (1 if caps is None else caps[w]) for w in res[j]):
                continue
            slot[j] = t
            for w in res[j]:
                occ[(t, w)] = occ.get((t, w), 0) + 1
            if dfs(idx + 1):
                return True
            for w in res[j]:
                occ[(t, w)] -= 1
            slot[j] = -1
            if nodes[0] > node_limit:
                return False
        return False

    ok = dfs(0)
    return slot if ok else None


def solve_window_tabu(model, slots, a, b, W, seed=0, max_iter=4000):
    """Max-k-Cut tabu search on the window (soft precedence, fixed outside gates)."""
    from .maxkcut import MaxKCutState
    D = used_layers(slots)
    k = D - 1
    base = slots.copy()
    base[base > b] -= 1
    st = MaxKCutState(model, k, seed=seed)
    Wset = set(W)
    fixed = [i for i in range(len(slots)) if i not in Wset]
    for i in fixed:
        st._place(i, int(base[i]))
    Wl, preds, succs, head, tail, res = _window_instance(model, slots, a, b)
    for j, i in enumerate(Wl):
        st.est[i] = a + head[j]
        st.lst[i] = b - 1 - tail[j]
        if st.est[i] > st.lst[i]:
            return None
    # greedy init in topological order
    for j, i in enumerate(Wl):
        lo = st.est[i]
        for p in model.preds[i]:
            lo = max(lo, st.run_max[p] + 1)
        hi = max(lo, st.lst[i])
        r = st.res[i]
        sub = st.occ[lo:hi + 1][:, r]
        add = np.maximum(0, sub - st.res_cap[i] + 1).sum(axis=1)
        st._place(i, lo + int(np.argmin(add)))
    st.recompute_precedence()
    st.movable = Wset
    ok = st.tabu_search(max_iter=max_iter)
    if ok:
        return st.slot.copy()
    return None


def compress_window(model, slots, a, L, node_limit=20000, use_tabu=True, seed=0):
    """Try to re-layer the window [a, a+L-1] into L-1 layers. Returns new slots or None."""
    D = used_layers(slots)
    b = min(a + L - 1, D - 1)
    if b - a < 1:
        return None
    W, preds, succs, head, tail, res = _window_instance(model, slots, a, b)
    n = len(W)
    k = b - a
    if window_lower_bound(n, preds, head, tail, res) > k:
        return None
    sol = solve_window_exact(n, preds, head, tail, res, k, node_limit=node_limit)
    if sol is None and use_tabu:
        out = solve_window_tabu(model, slots, a, b, W, seed=seed)
        if out is not None:
            return compact(out)
        return None
    if sol is None:
        return None
    new = slots.copy()
    new[new > b] -= 1
    for j, i in enumerate(W):
        new[i] = a + sol[j]
    return compact(new)


def lns(model, slots, lb, time_limit=10.0, sizes=(4, 6, 8, 12, 16, 24), seed=0,
        node_limit=20000, log=None):
    """Window-compression LNS with FBI justification between sweeps."""
    t0 = time.time()
    rng = np.random.default_rng(seed)
    best = fbi(model, compact(slots))
    stats = {"start": used_layers(compact(slots)), "after_fbi": used_layers(best),
             "compressions": 0, "sweeps": 0}
    improved = True
    while improved and time.time() - t0 < time_limit and used_layers(best) > lb:
        improved = False
        for L in sizes:
            D = used_layers(best)
            if L > D:
                break
            starts = list(range(0, D - 1, max(1, L // 2)))
            rng.shuffle(starts)
            for a in starts:
                if time.time() - t0 > time_limit or used_layers(best) <= lb:
                    break
                new = compress_window(model, best, a, L, node_limit=node_limit,
                                      seed=int(rng.integers(1 << 30)))
                if new is not None and used_layers(new) < used_layers(best):
                    best = new
                    stats["compressions"] += 1
                    improved = True
            stats["sweeps"] += 1
            if improved:
                break
        if improved:
            best = fbi(model, best)
        if log:
            log(f"  lns sweep: layers={used_layers(best)}")
    stats["final"] = used_layers(best)
    stats["time"] = time.time() - t0
    return best, stats
