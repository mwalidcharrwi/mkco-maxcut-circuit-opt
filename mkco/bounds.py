"""Certified lower bounds on the layer count of any reordering."""
from __future__ import annotations

import heapq

import networkx as nx
import numpy as np


def jackson_wire_bound(model, caps=None):
    """Max over wires of the optimal makespan of the gates on that wire.

    Every wire is a (capacity-c) machine; gate j has release head(j) and tail
    tail(j) from the dependency DAG.  For unit jobs with integer releases the
    largest-tail-first rule is optimal (Jackson 1955 / Horn 1974), so the value
    is a valid lower bound on the depth of every equivalent circuit.  It
    dominates both the critical path and the paper's max-load bound (Eq. 2).
    """
    nu = len(model.unit)
    if nu == 0:
        return 0
    caps = np.ones(model.num_wires, dtype=np.int64) if caps is None else np.asarray(caps)
    by_wire = {}
    for i, g in enumerate(model.unit):
        for w in model.wires[g]:
            by_wire.setdefault(w, []).append(i)
    head, tail = model.head, model.tail
    best = model.critical_path
    for w, jobs in by_wire.items():
        c = int(caps[w])
        jobs = sorted(jobs, key=lambda j: head[j])
        heap = []
        t = 0
        k = 0
        val = 0
        n = len(jobs)
        done = 0
        while done < n:
            if not heap and k < n and head[jobs[k]] > t:
                t = int(head[jobs[k]])
            while k < n and head[jobs[k]] <= t:
                heapq.heappush(heap, -int(tail[jobs[k]]))
                k += 1
            for _ in range(c):
                if not heap:
                    break
                q = -heapq.heappop(heap)
                val = max(val, t + 1 + q)
                done += 1
            t += 1
        best = max(best, val)
    return int(best)


def clique_bound(graph, exact_limit=120):
    """Size of a clique in the conflict graph (exact for small graphs)."""
    if graph.number_of_nodes() == 0:
        return 0
    if graph.number_of_nodes() <= exact_limit:
        return max(len(c) for c in nx.find_cliques(graph))
    return len(nx.algorithms.approximation.max_clique(graph))


def paper_bound(model):
    """Eq. (2) of Lee et al.: maximum number of gates on one qubit."""
    load = model.load_per_wire()
    return int(load.max()) if len(load) else 0


def lower_bound(model, caps=None, graph=None):
    lb = jackson_wire_bound(model, caps)
    if graph is not None and caps is None:
        lb = max(lb, clique_bound(graph))
    return lb
