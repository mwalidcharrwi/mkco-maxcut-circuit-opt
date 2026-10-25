"""SDP lower bound on the depth of commuting circuits (optional, needs cvxpy).

Lovasz sandwich theorem: omega(G) <= theta(complement of G) <= chi(G).  The
theta number of the complement of the conflict graph is therefore a lower
bound on the depth of every ordering of a commuting circuit (Theorem 1 with no
precedence arcs).  It can be strictly stronger than the maximum clique, and it
is the dual of the Karger-Motwani-Sudan strict vector colouring.

    theta(complement G) = max <J, X>  s.t.  X psd, tr X = 1,
                                            X_ij = 0 for every non-adjacent pair ij of G

The SDP is solved numerically (Clarabel interior point); the bound is rounded
with a safety margin, ceil(value - 1e-4), and the raw value is returned too.
"""
from __future__ import annotations

import math

import numpy as np


def theta_bound(graph, solver=None, eps=1e-4):
    """Return (depth lower bound, raw theta value) for a networkx conflict graph."""
    import cvxpy as cp
    import networkx as nx

    n = graph.number_of_nodes()
    if n == 0:
        return 0, 0.0
    a = nx.to_numpy_array(graph, nodelist=list(graph.nodes()))
    ii, jj = np.nonzero(np.triu(1 - a, k=1))      # non-adjacent pairs i < j only
    X = cp.Variable((n, n), symmetric=True)
    cons = [X >> 0, cp.trace(X) == 1]
    if len(ii):
        cons.append(X[ii, jj] == 0)
    prob = cp.Problem(cp.Maximize(cp.sum(X)), cons)
    prob.solve(solver=solver or cp.CLARABEL)
    val = float(prob.value)
    return int(math.ceil(val - eps)), val
