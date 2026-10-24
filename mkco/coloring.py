"""Baselines from Lee, Jeong & Kim, "Quantum circuit optimization by graph
coloring" (Quantum 2026): explicit conflict graph (their Algorithm 1), DSatur
and exact backtracking colouring, ToCircuit (Algorithm 2), and the natural
extension of their method to general circuits (colour every maximal block of
mutually commuting gates separately)."""
from __future__ import annotations

import time

import networkx as nx
import numpy as np

from .depmodel import DepModel
from .gates import axes_compatible
from .schedule import emit_order


def conflict_graph(model):
    """Algorithm 1 (ConstructGraph): vertices = unit gates, edge = not parallelisable."""
    g = nx.Graph()
    nu = len(model.unit)
    g.add_nodes_from(range(nu))
    by_wire = {}
    for i, gate in enumerate(model.unit):
        for w in model.wires[gate]:
            by_wire.setdefault(w, []).append(i)
    for members in by_wire.values():
        for a in range(len(members)):
            for b in range(a + 1, len(members)):
                g.add_edge(members[a], members[b])
    return g


def dsatur(graph):
    """DSatur colouring (Brelaz 1979) via networkx; returns {node: colour}."""
    if graph.number_of_nodes() == 0:
        return {}
    return nx.coloring.greedy_color(graph, strategy="DSATUR")


def exact_coloring(graph, time_limit=10.0, ub_coloring=None):
    """DSatur-based branch and bound (exact backtracking colouring).

    Returns (coloring, proven_optimal).  Falls back to the best colouring found
    when the time limit is hit.
    """
    nodes = list(graph.nodes())
    n = len(nodes)
    if n == 0:
        return {}, True
    idx = {v: i for i, v in enumerate(nodes)}
    adj = [set(idx[u] for u in graph.neighbors(v)) for v in nodes]
    best = ub_coloring or dsatur(graph)
    best_k = max(best.values()) + 1
    best_col = [best[v] for v in nodes]
    clique = nx.algorithms.approximation.max_clique(graph)
    lb = len(clique)
    if best_k == lb:
        return best, True
    deadline = time.time() + time_limit
    col = [-1] * n
    # neighbour colour counts for saturation
    sat = [dict() for _ in range(n)]
    # pre-colour the clique (symmetry breaking)
    order_clique = [idx[v] for v in clique]
    state = {"best_k": best_k, "best_col": best_col, "timeout": False}

    def assign(v, c):
        col[v] = c
        for u in adj[v]:
            sat[u][c] = sat[u].get(c, 0) + 1

    def unassign(v, c):
        col[v] = -1
        for u in adj[v]:
            sat[u][c] -= 1
            if sat[u][c] == 0:
                del sat[u][c]

    for c, v in enumerate(order_clique):
        assign(v, c)
    n_col = len(order_clique)

    def rec(colored, k_used):
        if state["timeout"]:
            return
        if time.time() > deadline:
            state["timeout"] = True
            return
        if colored == n:
            if k_used < state["best_k"]:
                state["best_k"] = k_used
                state["best_col"] = list(col)
            return
        # pick uncoloured vertex with max saturation, tie -> max degree
        v, bs, bd = -1, -1, -1
        for u in range(n):
            if col[u] < 0:
                s = len(sat[u])
                d = len(adj[u])
                if s > bs or (s == bs and d > bd):
                    v, bs, bd = u, s, d
        for c in range(min(k_used + 1, state["best_k"] - 1)):
            if c in sat[v]:
                continue
            assign(v, c)
            rec(colored + 1, max(k_used, c + 1))
            unassign(v, c)
            if state["best_k"] == lb or state["timeout"]:
                return

    rec(n_col, n_col)
    coloring = {nodes[i]: state["best_col"][i] for i in range(n)}
    return coloring, not state["timeout"]


def coloring_to_slots(model, coloring):
    """Algorithm 2 (ToCircuit): sort gates by colour."""
    return np.array([coloring[i] for i in range(len(model.unit))], dtype=np.int64)


def commuting_blocks(circuit):
    """Split a gate list into maximal consecutive blocks of mutually commuting gates."""
    blocks, cur, block_axis = [], [], {}
    nq = circuit.num_qubits
    for g in circuit.gates:
        ws = g.wires(nq)
        ax = list(circuit.gate_axes(g)) + [None] * (len(ws) - len(g.qubits))
        ok = all(a is not None for a in ax) and all(
            w not in block_axis or axes_compatible(block_axis[w], a) for w, a in zip(ws, ax))
        if not ok and cur:
            blocks.append(cur)
            cur, block_axis = [], {}
        cur.append(g)
        if any(a is None for a in ax):
            blocks.append(cur)
            cur, block_axis = [], {}
            continue
        for w, a in zip(ws, ax):
            if w not in block_axis or block_axis[w] == "I":
                block_axis[w] = a
    if cur:
        blocks.append(cur)
    return blocks


def paper_blockwise(circuit, metric="depth", solver="dsatur", time_limit=5.0):
    """Lee et al.'s colouring method applied to every commuting block in turn."""
    out = []
    for seg in split_barriers(circuit):
        if seg[0] == "barrier":
            out.append(seg[1])
            continue
        sub = circuit.copy_with_gates(seg[1])
        for block in commuting_blocks(sub):
            bc = circuit.copy_with_gates(block)
            m = DepModel(bc, metric)
            gph = conflict_graph(m)
            if solver == "dsatur":
                colr = dsatur(gph)
            else:
                colr, _ = exact_coloring(gph, time_limit=time_limit)
            order = emit_order(m, coloring_to_slots(m, colr))
            out.extend(block[i] for i in order)
    return circuit.copy_with_gates(out)


def split_barriers(circuit):
    """Yield ('gates', [..]) and ('barrier', gate) segments."""
    segs, cur = [], []
    for g in circuit.gates:
        if g.kind == "barrier":
            if cur:
                segs.append(("gates", cur))
                cur = []
            segs.append(("barrier", g))
        else:
            cur.append(g)
    if cur:
        segs.append(("gates", cur))
    return segs
