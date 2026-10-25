"""Tests for the extensions: theta-plus, non-Clifford depth, regrouped KAK,
commutation-aware routing and the state-aware idle-noise score."""
import math
import os
import sys

import networkx as nx
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mkco import generators as gen                       # noqa: E402
from mkco.circuit import Circuit                         # noqa: E402
from mkco.nonclifford import counted_depth, optimize_nonclifford  # noqa: E402
from mkco.route import check_coupling, route, unroute    # noqa: E402
from mkco.verify import statevector_check                # noqa: E402


def test_theta_plus_between_theta_and_chi():
    pytest.importorskip("cvxpy")
    from mkco.coloring import conflict_graph, exact_coloring
    from mkco.depmodel import DepModel
    from mkco.sdp_bounds import theta_bound
    b, v = theta_bound(nx.cycle_graph(5), plus=True)
    assert b == 3 and v <= math.sqrt(5) + 1e-6
    for seed in range(2):
        g = conflict_graph(DepModel(gen.random_commuting_ccz(8, 20, seed=seed)))
        col, proven = exact_coloring(g, time_limit=30)
        b0, v0 = theta_bound(g)
        b1, v1 = theta_bound(g, plus=True)
        assert proven and v1 >= v0 - 1e-5 and b1 <= max(col.values()) + 1


@pytest.mark.parametrize("kind,circ", [
    ("t", lambda: gen.decompose_toffoli(gen.gf2_multiplier(3))),
    ("t", lambda: gen.random_clifford_t(6, 150, seed=3)),
    ("toffoli", lambda: gen.gf2_multiplier(3)),
])
def test_nonclifford_depth_is_equivalent_and_certified(kind, circ):
    c = circ()
    out, rep = optimize_nonclifford(c, kind=kind, time_limit=3)
    ok, _ = statevector_check(c, out)
    assert ok
    assert rep["after"] == counted_depth(out, kind) <= rep["before"]
    assert rep["lower_bound"] <= rep["after"]


def test_nonclifford_parallelises_independent_t_gates():
    c = Circuit(3)
    for q in range(3):                  # T gates behind a CNOT ladder that only looks sequential
        c.add("h", [q])
    c.add("t", [0]).add("cx", [1, 2]).add("t", [1]).add("t", [2])
    out, rep = optimize_nonclifford(c, kind="t", time_limit=2, merge=False)
    assert rep["after"] == rep["lower_bound"] == 1 and rep["certified_optimal"]


def test_regroup_is_legal_and_never_worse():
    pytest.importorskip("qiskit")
    from mkco.blocks import full_rewrite, regroup_both_ways
    c = gen.phase_polynomial(6, 30, seed=1)
    r, _ = regroup_both_ways(c)
    assert statevector_check(c, r)[0]
    a, _ = full_rewrite(c, regroup=False)
    b, _ = full_rewrite(c, regroup=True)
    n2 = lambda x: sum(1 for g in x.gates if len(g.qubits) == 2)  # noqa: E731
    assert statevector_check(c, b)[0] and n2(b) <= n2(a)


def _routed_statevector_ok(c, r, init, fin):
    """Simulate both and compare after undoing the final layout."""
    from mkco.sim import apply_gate
    n = c.num_qubits
    rng = np.random.default_rng(0)
    psi = rng.normal(size=2 ** n) + 1j * rng.normal(size=2 ** n)
    psi /= np.linalg.norm(psi)
    st = psi.reshape((2,) * n)
    for g in c.gates:
        st = apply_gate(st, g, c)
    active = sorted({q for g in r.gates for q in g.qubits} | set(init))
    pos = {p: i for i, p in enumerate(active)}
    k = len(active)
    full = np.zeros((2,) * k, dtype=complex)
    # embed logical qubit l at physical init[l], others in |0>
    idx = np.indices((2,) * n).reshape(n, -1)
    for col in range(idx.shape[1]):
        bits = [0] * k
        for l in range(n):
            bits[pos[init[l]]] = idx[l, col]
        full[tuple(bits)] = psi.reshape(-1)[col]
    sub = Circuit(k)
    for g in r.gates:
        sub.add(g.name, [pos[p] for p in g.qubits], g.params)
    for g in sub.gates:
        full = apply_gate(full, g, sub)
    out = np.zeros(2 ** n, dtype=complex)
    for col in range(idx.shape[1]):
        bits = [0] * k
        for l in range(n):
            bits[pos[fin[l]]] = idx[l, col]
        out[col] = full[tuple(bits)]
    return abs(np.vdot(out, st.reshape(-1))) > 1 - 1e-9


def test_routing_is_exactly_checked():
    g = nx.grid_2d_graph(3, 3)
    g = nx.convert_node_labels_to_integers(g)
    c = gen.qaoa_maxcut(6, p=1, seed=2)
    r, rep = route(c, g, trials=2, iterations=1)
    ok, msg, fin = unroute(c, r, rep["initial_layout"])
    assert ok, msg
    assert check_coupling(r, g)
    assert _routed_statevector_ok(c, r, rep["initial_layout"], fin)


class _ToyCal:
    """Duck-typed calibration: error-free gates, 'id' and 'cz' take 1 us."""
    def __init__(self, n):
        self.t1 = np.full(n, 100e-6)
        self.t2 = np.full(n, 80e-6)
        self.ro = np.zeros(n)
        self.median_2q = 0.0

    def gate(self, g):
        return (0.0, 1e-6) if g.name in ("id", "cz") else (0.0, 0.0)


def test_state_aware_esp_sees_the_idling_state():
    from mkco.noise import esp, state_aware_esp
    cal = _ToyCal(3)

    def build(h0_first):
        c = Circuit(3)
        if h0_first:
            c.add("h", [0])
        c.add("h", [1]).add("cz", [0, 1])
        for _ in range(3):                  # pins cz(0,1) early: qubit 0 then idles
            c.add("id", [1])
        c.add("h", [2]).add("cz", [0, 2])
        if not h0_first:
            c.add("h", [0])
        return c

    ground, plus = build(False), build(True)
    assert esp(ground, cal)["esp"] == pytest.approx(esp(plus, cal)["esp"])   # state-blind
    a = state_aware_esp(ground, cal)["sesp"]
    b = state_aware_esp(plus, cal)["sesp"]
    assert a == pytest.approx(1.0) and b < a


def test_alap_layering_keeps_depth_and_bound():
    from mkco.optimize import optimize
    c = gen.random_clifford_t(6, 120, seed=5)
    a, ra = optimize(c, time_limit=2)
    b, rb = optimize(c, time_limit=2, alap=True)
    assert statevector_check(c, b)[0]
    assert b.depth() == a.depth() and rb["lower_bound"] == ra["lower_bound"]
