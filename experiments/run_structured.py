"""Commuting-circuit experiments: the settings of Lee et al. plus structured layers.

E1  random commuting multi-controlled-Z circuits (Lee et al., Sec. 4.3 / Fig. 1)
E2  F_{2^n} multiplication, Toffoli-depth of phases 1+3 (Lee et al., Sec. 5.1 / Fig. 2)
E3  random CCZ circuits, m = 10 (Lee et al., Appendix C)
E4  commuting two-qubit layers: RZZ on random d-regular graphs (QAOA cost layers)
E5  hierarchical Max-Cut with exact / QAOA sub-solvers (quantum-ready backend)

Every number is the depth of a commuting circuit; LB is a certified lower
bound (max of the Jackson wire bound and an exact maximum clique).
"""
from __future__ import annotations

import json
import os
import sys
import time

import networkx as nx
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mkco import generators as gen                                   # noqa: E402
from mkco.bounds import jackson_wire_bound                           # noqa: E402
from mkco.circuit import Circuit                                     # noqa: E402
from mkco.coloring import (coloring_to_slots, conflict_graph, dsatur,  # noqa: E402
                           exact_coloring)
from mkco.depmodel import DepModel                                   # noqa: E402
from mkco.jk import jain_kumar_schedule                              # noqa: E402
from mkco.maxkcut import compact, kdescent, used_layers              # noqa: E402


def exact_clique(graph, time_limit=20.0):
    try:
        from ortools.sat.python import cp_model
    except ImportError:
        return max(len(c) for c in nx.find_cliques(graph))
    n = graph.number_of_nodes()
    m = cp_model.CpModel()
    x = [m.NewBoolVar(f"x{i}") for i in range(n)]
    for u, v in nx.complement(graph).edges():
        m.AddBoolOr([x[u].Not(), x[v].Not()])
    m.Maximize(sum(x))
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = time_limit
    s.parameters.num_workers = 2
    s.Solve(m)
    return int(s.ObjectiveValue())     # a clique found = valid lower bound


def solve_all(c, tl=10.0, exact_limit=None):
    m = DepModel(c)
    g = conflict_graph(m)
    t = time.time(); ds = compact(coloring_to_slots(m, dsatur(g))); t_ds = time.time() - t
    t = time.time(); jk = compact(jain_kumar_schedule(m, beam=3)); t_jk = time.time() - t
    lb = max(jackson_wire_bound(m), exact_clique(g))
    t = time.time(); mk, _ = kdescent(m, ds, lb, time_limit=tl); t_mk = time.time() - t
    row = {"n": len(m.unit), "lb": lb, "dsatur": used_layers(ds), "jk": used_layers(jk),
           "mkco": used_layers(mk), "t_dsatur": t_ds, "t_jk": t_jk, "t_mkco": t_mk}
    if exact_limit and len(m.unit) <= exact_limit:
        t = time.time(); col, proven = exact_coloring(g, time_limit=tl)
        row["backtracking"] = max(col.values()) + 1
        row["backtracking_proven"] = proven
        row["t_backtracking"] = time.time() - t
    return row


def e1(seeds=5, tl=10.0):
    out = []
    for m_ in (10, 20, 30):
        for n in (50, 100, 150, 200):
            for s in range(seeds):
                r = solve_all(gen.random_commuting_mcz(m_, n, seed=s), tl, exact_limit=50)
                r.update({"m": m_, "seed": s})
                out.append(r)
                print("E1", r, flush=True)
    return out


def e2(ns=tuple(range(2, 33)) + (40, 48, 64), tl=10.0):
    out = []
    for n in ns:
        p1, p3 = gen.gf2_mult_phases(n)
        a, b = solve_all(p1, tl, exact_limit=40), solve_all(p3, tl, exact_limit=40)
        r = {"n": n, "bound_2n_minus_1": 2 * n - 1}
        for k in ("lb", "dsatur", "jk", "mkco"):
            r[k] = a[k] + b[k]
        out.append(r)
        print("E2", r, flush=True)
    return out


def e3(seeds=5, tl=10.0):
    out = []
    for n in range(10, 101, 10):
        for s in range(seeds):
            r = solve_all(gen.random_commuting_ccz(10, n, seed=s), tl, exact_limit=50)
            r.update({"gates": n, "seed": s})
            out.append(r)
            print("E3", r, flush=True)
    return out


def e4(tl=10.0):
    out = []
    for nq, d in ((30, 5), (30, 9), (50, 15), (50, 25), (100, 15), (100, 31)):
        for s in range(3):
            g = nx.random_regular_graph(d, nq, seed=s)
            c = Circuit(nq)
            for u, v in g.edges():
                c.add("rzz", [u, v], (0.3,))
            r = solve_all(c, tl)
            r.update({"qubits": nq, "degree": d, "seed": s})
            out.append(r)
            print("E4", r, flush=True)
    return out


def e5():
    """HMC with the exact and QAOA backends on small commuting instances."""
    from mkco.hmc import hmc_assign, legalize
    out = []
    cases = [("gf2_4_phase3", gen.gf2_mult_phases(4)[1]),
             ("gf2_5_phase3", gen.gf2_mult_phases(5)[1]),
             ("draper_6_core", gen.draper_adder(6, with_qft=False)),
             ("ccz_m8_n16", gen.random_commuting_ccz(8, 16, seed=1))]
    for name, c in cases:
        m = DepModel(c)
        lb = jackson_wire_bound(m)
        for backend in ("exact", "qaoa"):
            t = time.time()
            slots, info = hmc_assign(m, lb, backend=backend, seed=0, qaoa_limit=16, p=3)
            s = legalize(m, slots)
            row = {"case": name, "backend": backend, "n_gates": len(m.unit), "lb": lb,
                   "layers": used_layers(s), "spins_log_encoding": len(m.unit) * int(np.ceil(np.log2(max(lb, 2)))),
                   "spins_one_hot": len(m.unit) * lb, "time": time.time() - t,
                   "qaoa": info.get("qaoa", [])}
            out.append(row)
            print("E5", {k: v for k, v in row.items() if k != "qaoa"},
                  "| QAOA nodes optimal:", sum(q["best_sampled_is_optimal"] for q in row["qaoa"]),
                  "/", len(row["qaoa"]), flush=True)
    return out


def e6(tl=10.0):
    """Ancilla fan-out (Lee et al. Sec. 5.2) as capacitated Max-k-Cut vs a fixed split."""
    from mkco.fanout import fanout_parallelize
    out = []
    cases = [("draper_8_core", gen.draper_adder(8, with_qft=False), 16),
             ("draper_16_core", gen.draper_adder(16, with_qft=False), 32),
             ("ccz_m10_n80", gen.random_commuting_ccz(10, 80, seed=1), 10),
             ("ccz_m16_n150", gen.random_commuting_ccz(16, 150, seed=2), 16),
             ("mcz_m20_n120", gen.random_commuting_mcz(20, 120, seed=3), 20)]
    for name, c, nq in cases:
        for copies in (1, 2, 3, 4):
            caps = {q: copies for q in range(nq)}
            b, bi = fanout_parallelize(c, caps, time_limit=tl, baseline=True)
            m, mi = fanout_parallelize(c, caps, time_limit=tl)
            row = {"case": name, "copies": copies, "qubits": mi["qubits"],
                   "baseline_core": bi["core_depth"], "baseline_total": bi["total_depth"],
                   "mkco_core": mi["core_depth"], "mkco_total": mi["total_depth"]}
            out.append(row)
            print("E6", row, flush=True)
    return out


if __name__ == "__main__":
    os.makedirs("results/structured", exist_ok=True)
    which = sys.argv[1:] or ["e1", "e2", "e3", "e4", "e5", "e6"]
    for w in which:
        res = globals()[w]()
        with open(f"results/structured/{w}.json", "w") as fh:
            json.dump(res, fh, indent=1, default=float)
