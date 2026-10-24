"""Core correctness tests.  Run:  python tests/test_core.py   (or pytest)."""
import itertools
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mkco import generators as gen                       # noqa: E402
from mkco import gates as G                              # noqa: E402
from mkco.bounds import jackson_wire_bound               # noqa: E402
from mkco.circuit import Circuit                         # noqa: E402
from mkco.crosstalk import (adjacent_couplers, coupler_edges, crosstalk_pairs,  # noqa: E402
                            optimize_crosstalk)
from mkco.depmodel import DepModel                       # noqa: E402
from mkco.hmc import IsingSplit                          # noqa: E402
from mkco.jk import jain_kumar                           # noqa: E402
from mkco.merge import merge_rotations                   # noqa: E402
from mkco.optimize import optimize                       # noqa: E402
from mkco.qasm import parse_qasm                         # noqa: E402
from mkco.resynth import rewrite_single_qubit, synth_zsx   # noqa: E402
from mkco.sim import apply_matrix, equivalent            # noqa: E402
from mkco.verify import audit_reordering                 # noqa: E402

ONE_Q = [("rz", (0.3,)), ("rx", (0.4,)), ("ry", (0.5,)), ("h", ()), ("sx", ()), ("x", ()),
         ("t", ()), ("s", ()), ("u3", (0.1, 0.2, 0.3))]
TWO_Q = [("cx", ()), ("cz", ()), ("rzz", (0.2,)), ("rxx", (0.3,)), ("crx", (0.4,)),
         ("ch", ()), ("swap", ()), ("ecr", ()), ("cp", (0.6,))]


def _embed(name, params, qubits, n=3):
    dim = 2 ** n
    st = np.eye(dim, dtype=complex).reshape((2,) * n + (dim,))
    nq = len(qubits)
    st = apply_matrix(st, G.gate_matrix(name, params, nq), qubits)
    return st.reshape(dim, dim)


def test_axis_rule_is_sound():
    """Lemma 1: same axis on every shared qubit  =>  the gates commute."""
    gates = [(n, p, (q,)) for n, p in ONE_Q for q in range(3)]
    gates += [(n, p, qs) for n, p in TWO_Q for qs in itertools.permutations(range(3), 2)]
    checked = 0
    for (n1, p1, q1), (n2, p2, q2) in itertools.combinations(gates, 2):
        shared = set(q1) & set(q2)
        if not shared:
            continue
        a1 = dict(zip(q1, G.library_axes(n1, p1, len(q1))))
        a2 = dict(zip(q2, G.library_axes(n2, p2, len(q2))))
        if all(G.axes_compatible(a1[q], a2[q]) for q in shared):
            u, v = _embed(n1, p1, q1), _embed(n2, p2, q2)
            assert np.allclose(u @ v, v @ u, atol=1e-9), (n1, q1, n2, q2)
            checked += 1
    assert checked > 50


def test_reordering_is_equivalent_on_random_circuits():
    for seed in range(6):
        for c in (gen.random_clifford_t(6, 150, seed=seed), gen.phase_polynomial(6, 15, seed=seed),
                  gen.qaoa_maxcut(8, 2, seed=seed, decompose=True)):
            opt, rep = optimize(c, time_limit=1.0, seed=seed)
            ok, _ = equivalent(c, opt)
            assert ok
            assert audit_reordering(c, c.gates, opt.gates)["ok"]
            assert opt.depth() <= c.depth()
            assert rep["after"] >= rep["lower_bound"]
            assert jk_ok(c)


def jk_ok(c):
    j = jain_kumar(c)
    return equivalent(c, j)[0]


def test_lower_bound_never_exceeds_exact_optimum():
    try:
        import ortools  # noqa: F401
    except ImportError:          # optional dependency: skip quietly
        return
    from mkco.exact import cpsat_schedule
    from mkco.schedule import list_schedule
    from mkco.maxkcut import used_layers
    for seed in range(3):
        c = gen.random_clifford_t(5, 60, seed=seed)
        m = DepModel(c)
        lb = jackson_wire_bound(m)
        s = list_schedule(m)
        sol, status, _ = cpsat_schedule(m, used_layers(s), time_limit=20)
        assert status == "optimal" and used_layers(sol) >= lb


def test_merge_preserves_semantics():
    c = Circuit(3)
    for q in range(3):
        c.add("rz", [q], (0.3,)).add("rz", [q], (0.4,)).add("sx", [q]).add("sx", [q])
    c.add("ecr", [0, 1]).add("sx", [1]).add("x", [1]).add("rz", [2], (1.0,))
    m, st = merge_rotations(c)
    assert m.size() < c.size()
    assert equivalent(c, m)[0]


def test_zsx_synthesis_is_exact():
    from scipy.stats import unitary_group
    from mkco.resynth import _equal_up_to_phase, _seq_matrix
    for seed in range(200):
        u = unitary_group.rvs(2, random_state=seed)
        assert _equal_up_to_phase(_seq_matrix(synth_zsx(u)), u)
    assert [n for n, _ in synth_zsx(G.gate_matrix("x", ()))] == ["x"]


def test_rewrite_preserves_semantics():
    for seed in range(4):
        c = Circuit(4)
        rng = np.random.default_rng(seed)
        for _ in range(120):
            if rng.random() < 0.3:
                a, b = (int(x) for x in rng.choice(4, 2, replace=False))
                c.add("ecr", [a, b])
            else:
                q = int(rng.integers(4))
                name = ["rz", "sx", "x"][int(rng.integers(3))]
                c.add(name, [q], (float(rng.uniform(-3, 3)),) if name == "rz" else ())
        rw, st = rewrite_single_qubit(c)
        assert rw.size() <= c.size()
        assert equivalent(c, rw)[0]
        opt, _ = optimize(rw, time_limit=1.0)
        assert equivalent(c, opt)[0]


def test_ising_expansion_matches_energy():
    c = gen.random_clifford_t(5, 40, seed=1)
    m = DepModel(c)
    sp = IsingSplit(m, list(range(len(m.unit))), 9, m.unit_resources())
    h, J, off = sp.ising()
    rng = np.random.default_rng(0)
    for _ in range(10):
        z = rng.choice([-1.0, 1.0], sp.n)
        e = off + h @ z + sum(v * z[a] * z[b] for (a, b), v in J.items())
        assert abs(sp.energy(z) - e) < 1e-6


def test_crosstalk_mode_keeps_2q_depth_and_semantics():
    src = open(os.path.join(os.path.dirname(__file__), "..", "benchmarks", "ibm127",
                            "mult_8.qasm")).read() if os.path.exists(os.path.join(
                                os.path.dirname(__file__), "..", "benchmarks", "ibm127",
                                "mult_8.qasm")) else None
    if src is None:
        return
    c = parse_qasm(src)
    adj = adjacent_couplers(coupler_edges([c]))
    xt, _ = optimize_crosstalk(c, adj, time_limit=3)
    assert xt.depth("2q", barrier_sync=True) <= c.depth("2q")
    assert crosstalk_pairs(xt, adj) <= crosstalk_pairs(c, adj)
    assert audit_reordering(c, c.gates, xt.gates)["ok"]


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
