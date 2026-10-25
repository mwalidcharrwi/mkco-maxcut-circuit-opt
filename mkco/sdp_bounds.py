"""SDP lower bound on the depth of commuting circuits (optional, needs cvxpy).

Lovasz sandwich theorem: omega(G) <= theta(complement of G) <= chi(G).  The
theta number of the complement of the conflict graph is therefore a lower
bound on the depth of every ordering of a commuting circuit (Theorem 1 with no
precedence arcs; docs/THEORY.md, Proposition 9).  It can be strictly stronger
than the maximum clique, and it is the dual of the Karger-Motwani-Sudan strict
vector colouring.

    theta(complement G) = max <J, X>  s.t.  X psd, tr X = 1,
                                            X_ij = 0 for every non-adjacent pair ij of G

The SDP is solved numerically (Clarabel interior point), so the solver's
optimum is not itself a proof.  The bound is taken from a *repaired* solution
instead: the zero pattern is imposed exactly, the diagonal is shifted by the
most negative eigenvalue (which keeps the zeros) and the matrix is rescaled to
trace 1.  The result is a feasible point, so its objective is <= theta <= chi
whatever the solver's accuracy; only the eigenvalue and the sum carry
floating-point error, covered by a 1e-7 margin.
"""
from __future__ import annotations

import math

import numpy as np


def repair(x, adj, plus=False, margin=1e-9):
    """Return a feasible point of the theta (or theta-plus) SDP close to x.

    theta: X_ij = 0 on non-adjacent pairs.  theta-plus: X_ij <= 0 there, so
    only positive entries are cut to zero.  The diagonal shift keeps those
    entries and the positive rescaling keeps their sign.
    """
    n = len(adj)
    y = (np.asarray(x, dtype=float) + np.asarray(x, dtype=float).T) / 2
    off = (adj == 0) & ~np.eye(n, dtype=bool)
    y[off] = np.minimum(y[off], 0.0) if plus else 0.0
    lam = float(np.linalg.eigvalsh(y)[0])
    if lam < margin:
        y += (margin - lam) * np.eye(n)
    return y / np.trace(y)


def core_nodes(graph, k):
    """Vertices of the (k-1)-core: the only ones that matter for chi >= k.

    A vertex with fewer than k-1 neighbours can always take a free colour in
    any (k-1)-colouring of the rest, so chi(G) >= k iff chi(core) >= k.  Any
    induced subgraph gives a valid bound anyway; the core is just smaller.
    """
    import networkx as nx
    return list(nx.k_core(graph, k - 1).nodes()) if k > 1 else list(graph.nodes())


def theta_bound(graph, solver=None, return_raw=False, plus=False, nodes=None, **solver_opts):
    """Return (depth lower bound, certified value) for a networkx conflict graph.

    plus=True computes Szegedy's theta-plus, which is >= theta and still <= chi
    (docs/THEORY.md, Proposition 9).  `nodes` restricts the bound to an induced
    subgraph (e.g. core_nodes).  With return_raw=True the solver's own optimum is
    returned as a third value.
    """
    import cvxpy as cp
    import networkx as nx

    if nodes is not None:
        graph = graph.subgraph(nodes)
    n = graph.number_of_nodes()
    if n == 0:
        return (0, 0.0, 0.0) if return_raw else (0, 0.0)
    a = nx.to_numpy_array(graph, nodelist=list(graph.nodes()))
    ii, jj = np.nonzero(np.triu(1 - a, k=1))      # non-adjacent pairs i < j only
    X = cp.Variable((n, n), symmetric=True)
    cons = [X >> 0, cp.trace(X) == 1]
    if len(ii):
        cons.append(X[ii, jj] <= 0 if plus else X[ii, jj] == 0)
    prob = cp.Problem(cp.Maximize(cp.sum(X)), cons)
    prob.solve(solver=solver or cp.CLARABEL, **solver_opts)
    raw = float(prob.value)
    val = float(repair(X.value, a, plus=plus).sum())
    bound = max(1, int(math.ceil(val - 1e-7)))
    return (bound, val, raw) if return_raw else (bound, val)
