"""Commutation-aware qubit routing (SWAP insertion) on a coupling graph.

A SABRE-style router (Li, Ding & Xie, ASPLOS 2019) whose *front layer* is
taken from the trace order of DepModel instead of the gate DAG: a gate is
ready as soon as the previous run on each of its wires has been executed, so
every mutually commuting gate (a whole QAOA cost layer, all controlled phases
of a QFT stage that share a control, ...) competes for execution at once and
the router may execute them in any order.  Routing and layering therefore
use the same commutation structure; the routed circuit is then layered by
MKCO as usual.

Correctness is checked exactly by `unroute`: tracking the layout through the
inserted SWAPs maps every routed gate back to its logical qubits, and the
resulting logical gate sequence must be a linear extension of the input's
trace order (docs/THEORY.md, Lemma 2), i.e. an equivalent circuit up to the
final qubit permutation.
"""
from __future__ import annotations

import networkx as nx
import numpy as np

from .circuit import Circuit, Gate
from .depmodel import DepModel
from .schedule import verify_order


class _Ready:
    """Kahn-style readiness over the run order of a DepModel."""

    def __init__(self, model):
        self.m = model
        self.left = [len(mem) for mem in model.run_members]
        self.next_run = np.full(model.num_runs, -1, dtype=np.int64)
        self.waiting = np.zeros(model.n, dtype=np.int64)
        for rs in model.wire_runs:
            for i in range(len(rs) - 1):
                self.next_run[rs[i]] = rs[i + 1]
            for r in rs[1:]:
                for gi in model.run_members[r]:
                    self.waiting[gi] += 1
        self.ready = {i for i in range(model.n) if self.waiting[i] == 0}

    def done(self, gi):
        self.ready.discard(gi)
        new = []
        for r in self.m.gate_runs[gi]:
            self.left[r] -= 1
            if self.left[r] == 0 and self.next_run[r] >= 0:
                for x in self.m.run_members[self.next_run[r]]:
                    self.waiting[x] -= 1
                    if self.waiting[x] == 0:
                        self.ready.add(x)
                        new.append(x)
        return new


class _DagReady:
    """Readiness over the plain gate DAG (every gate waits for the previous gate
    on each of its wires): the front layer of standard SABRE."""

    def __init__(self, model):
        n = model.n
        self.succ = [[] for _ in range(n)]
        self.waiting = np.zeros(n, dtype=np.int64)
        last = {}
        for i, ws in enumerate(model.wires):
            for w in ws:
                if w in last:
                    self.succ[last[w]].append(i)
                    self.waiting[i] += 1
                last[w] = i
        self.ready = {i for i in range(n) if self.waiting[i] == 0}

    def done(self, gi):
        self.ready.discard(gi)
        new = []
        for x in self.succ[gi]:
            self.waiting[x] -= 1
            if self.waiting[x] == 0:
                self.ready.add(x)
                new.append(x)
        return new


def _distance_matrix(graph, n):
    d = np.full((n, n), 10 ** 6, dtype=np.int64)
    for s, lens in nx.all_pairs_shortest_path_length(graph):
        for t, v in lens.items():
            d[s, t] = v
    return d


def route_once(circuit, graph, layout, seed=0, lookahead=20, w_ext=0.5, decay_delta=0.001,
               decay_reset=5, record=True, front_mode="mean"):
    """Route `circuit` (logical) on `graph` (physical, nodes 0..N-1) from `layout`.

    layout[l] = physical qubit of logical qubit l.  Returns (gates, final_layout,
    n_swaps) where gates are on physical qubits (SWAPs named 'swap').
    """
    rng = np.random.default_rng(seed)
    nphys = graph.number_of_nodes()
    dist = graph.graph.setdefault("_dist", _distance_matrix(graph, nphys))
    l2p = list(layout)
    p2l = [-1] * nphys
    for l, p in enumerate(l2p):
        p2l[p] = l
    gates = circuit.gates
    for g in gates:
        if len(g.qubits) > 2:
            raise ValueError("route: decompose gates on more than two qubits first")
    model = DepModel(circuit, "depth")
    rd = _DagReady(model) if front_mode == "dag" else _Ready(model)
    out = []
    decay = np.ones(nphys)
    since_reset = 0
    n_swaps = 0
    executed = 0
    stall = 0
    two = [len(g.qubits) == 2 for g in gates]
    pending_2q = [i for i in range(model.n) if two[i]]
    ptr = 0
    done_flag = np.zeros(model.n, dtype=bool)

    level = np.zeros(nphys, dtype=np.int64)     # ASAP layer of each physical qubit

    def phys(g):
        return [l2p[q] for q in g.qubits]

    def emit(gi):
        nonlocal executed
        g = gates[gi]
        ps = phys(g)
        lv = max(level[p] for p in ps) + 1
        for p in ps:
            level[p] = lv
        if record:
            out.append(Gate(g.name, ps, g.params, g.clbits, g.cond, g.kind))
        done_flag[gi] = True
        executed += 1
        rd.done(gi)

    while executed < model.n:
        progressed = True
        while progressed:
            progressed = False
            for gi in sorted(rd.ready):
                if not two[gi]:
                    emit(gi)
                    progressed = True
                else:
                    a, b = phys(gates[gi])
                    if dist[a, b] == 1:
                        emit(gi)
                        progressed = True
        if executed >= model.n:
            break
        front = [gi for gi in rd.ready if two[gi]]
        if stall > 10 * nphys:                       # release valve: walk one gate along a path
            gi = min(front)
            a, b = phys(gates[gi])
            path = nx.shortest_path(graph, a, b)
            for x, y in zip(path[:-2], path[1:-1]):
                level[x] = level[y] = max(level[x], level[y]) + 3
                _apply_swap(x, y, l2p, p2l, out, record)
                n_swaps += 1
            stall = 0
            continue
        while ptr < len(pending_2q) and done_flag[pending_2q[ptr]]:
            ptr += 1
        fset = set(front)
        ext = []
        k = ptr
        while k < len(pending_2q) and len(ext) < lookahead:
            gi = pending_2q[k]
            if not done_flag[gi] and gi not in fset:
                ext.append(gi)
            k += 1
        fq = [tuple(gates[gi].qubits) for gi in front]
        eq = [tuple(gates[gi].qubits) for gi in ext]
        cands = set()
        for la, lb in fq:
            for p in (l2p[la], l2p[lb]):
                for nb in graph.neighbors(p):
                    cands.add((min(p, nb), max(p, nb)))
        best, best_score = [], None
        for x, y in cands:
            lx, ly = p2l[x], p2l[y]

            def pos(l):
                if l == lx:
                    return y
                if l == ly:
                    return x
                return l2p[l]

            if front_mode == "nearest":
                # commuting front gates that share a qubit run one after another:
                # count only each qubit's nearest one
                near = {}
                for a, b in fq:
                    dd = dist[pos(a), pos(b)]
                    for q in (a, b):
                        if dd < near.get(q, 1 << 30):
                            near[q] = dd
                f = sum(near.values()) / len(near)
            else:
                f = sum(dist[pos(a), pos(b)] for a, b in fq) / len(fq)
            e = (sum(dist[pos(a), pos(b)] for a, b in eq) / len(eq)) if eq else 0.0
            score = max(decay[x], decay[y]) * (f + w_ext * e)
            if best_score is None or score < best_score - 1e-12:
                best, best_score = [(x, y)], score
            elif abs(score - best_score) <= 1e-12:
                best.append((x, y))
        # depth-aware tie-break: among equally good SWAPs prefer the most idle pair
        lo = min(max(level[x], level[y]) for x, y in best)
        best = [(x, y) for x, y in best if max(level[x], level[y]) == lo]
        x, y = best[int(rng.integers(len(best)))]
        lv = max(level[x], level[y]) + 3            # a SWAP is three CNOTs deep
        level[x] = level[y] = lv
        _apply_swap(x, y, l2p, p2l, out, record)
        n_swaps += 1
        stall += 1
        decay[x] += decay_delta
        decay[y] += decay_delta
        since_reset += 1
        if since_reset >= decay_reset:
            decay[:] = 1.0
            since_reset = 0
        if any(dist[l2p[a], l2p[b]] == 1 for a, b in fq):
            stall = 0
    return out, l2p, n_swaps


def _apply_swap(x, y, l2p, p2l, out, record):
    if record:
        out.append(Gate("swap", [x, y]))
    lx, ly = p2l[x], p2l[y]
    p2l[x], p2l[y] = ly, lx
    if lx >= 0:
        l2p[lx] = y
    if ly >= 0:
        l2p[ly] = x


def _random_layout(graph, n, rng):
    nodes = list(graph.nodes())
    start = nodes[int(rng.integers(len(nodes)))]
    region = list(nx.bfs_tree(graph, start).nodes())[:n]
    rng.shuffle(region)
    return region


def route(circuit, graph, trials=8, iterations=3, seed=0, cost=None,
          modes=("nearest", "mean"), **kw):
    """Bidirectional SABRE layout search + commutation-aware routing.

    Trials cycle through the front-layer definitions in `modes`:
      nearest  commutation-aware front, each qubit's nearest front gate scored
      mean     commutation-aware front, all front gates scored (SABRE's mean)
      dag      the plain gate-DAG front of standard SABRE (ablation)
    cost(routed_circuit, n_swaps) selects the best trial (default: fewest SWAPs).
    Returns (physical circuit on graph.number_of_nodes() qubits, report).
    """
    rng = np.random.default_rng(seed)
    n = circuit.num_qubits
    nphys = graph.number_of_nodes()
    if n > nphys:
        raise ValueError("circuit has more qubits than the device")
    rev = circuit.copy_with_gates(list(reversed(circuit.gates)))
    best = None
    for trial in range(trials):
        mode = modes[trial % len(modes)]
        layout = _random_layout(graph, n, rng)
        for it in range(iterations):
            _, fin, _ = route_once(circuit, graph, layout, seed=seed + trial, record=False,
                                   front_mode=mode, **kw)
            _, layout, _ = route_once(rev, graph, fin, seed=seed + trial, record=False,
                                      front_mode=mode, **kw)
        gates, fin, ns = route_once(circuit, graph, layout, seed=seed + trial, front_mode=mode, **kw)
        cand = Circuit(nphys)
        cand.gates = gates
        val = ns if cost is None else cost(cand, ns)
        if best is None or val < best[4]:
            best = (gates, list(layout), ns, list(fin), val, mode)
    gates, init, ns, fin, _, mode = best
    out = Circuit(nphys)
    out.gates = gates
    out.name = (circuit.name or "circuit") + "__routed"
    report = {"swaps": ns, "initial_layout": init, "final_layout": fin, "front_mode": mode}
    return out, report


def unroute(circuit, routed, initial_layout):
    """Map a routed circuit back to logical gates and check it is a legal reordering.

    Returns (ok, message, final_layout).
    """
    nphys = routed.num_qubits
    p2l = [-1] * nphys
    for l, p in enumerate(initial_layout):
        p2l[p] = l
    logical = []
    graph_ok = True
    for g in routed.gates:
        if g.name == "swap":
            x, y = g.qubits
            p2l[x], p2l[y] = p2l[y], p2l[x]
            continue
        qs = [p2l[p] for p in g.qubits]
        if any(q < 0 for q in qs):
            return False, f"gate {g} acts on an unmapped physical qubit", None
        logical.append((g.name, tuple(qs), tuple(round(p, 12) for p in g.params)))
    model = DepModel(circuit, "depth")
    pool = {}
    for i, g in enumerate(circuit.gates):
        pool.setdefault((g.name, tuple(g.qubits), tuple(round(p, 12) for p in g.params)), []).append(i)
    for v in pool.values():
        v.reverse()
    order = []
    for key in logical:
        lst = pool.get(key)
        if not lst:
            return False, f"routed gate {key} has no counterpart", None
        order.append(lst.pop())
    ok, msg = verify_order(model, order)
    fin = [None] * circuit.num_qubits
    for p, l in enumerate(p2l):
        if l >= 0:
            fin[l] = p
    return ok and graph_ok, msg, fin


def check_coupling(routed, graph):
    """Every two-qubit gate of the routed circuit acts on a coupled pair."""
    return all(graph.has_edge(*g.qubits) for g in routed.gates if len(g.qubits) == 2)
