"""E9: commutation-aware routing + layering on the 127-qubit heavy-hex device.

Logical circuits are mapped onto IBM Eagle's coupling graph
(benchmarks/devices/ibm_eagle_127.json, from Qiskit's FakeSherbrooke) at CNOT
level with symmetric couplers, the usual setting of routing studies.

Methods
  qiskit_o3       Qiskit transpile, optimization_level=3 (SabreLayout + SabreSwap
                  + its optimisation loop), basis {cx, rz, sx, x}
  mkco_route      ours: bidirectional SABRE-style layout search with the
                  commutation-aware front layer (mkco.route); each trial is
                  layered by MKCO, unrolled to the basis, re-synthesised (block
                  KAK, undirected) and layered again; the trial with the
                  smallest CNOTs + depth is kept
  sabre_dag       ablation: our router with the plain gate-DAG front layer of
                  standard SABRE, same trials and post-routing passes
  qiskit_o3+mkco  the same post-routing passes applied to Qiskit's output

Verification of mkco_route: `unroute` proves the routed circuit is a legal
reordering of the input up to the final qubit permutation (any size), every
two-qubit gate is checked to act on a coupler, and the post-routing passes
are checked as usual (numerical block checks, structural reordering checks,
state-vector check when <= 20 qubits are active).

Writes results/structured/routing.json.
"""
import json
import os
import sys
import time

import networkx as nx

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mkco import generators as gen                       # noqa: E402
from mkco.blocks import full_rewrite                     # noqa: E402
from mkco.circuit import Circuit                         # noqa: E402
from mkco.optimize import optimize                       # noqa: E402
from mkco.qasm import parse_qasm                         # noqa: E402
from mkco.route import check_coupling, route, unroute    # noqa: E402
from mkco.verify import statevector_check                # noqa: E402

OUT = "results/structured/routing.json"
BASIS = ["cx", "rz", "sx", "x"]


def device():
    d = json.load(open("benchmarks/devices/ibm_eagle_127.json"))
    g = nx.Graph()
    g.add_nodes_from(range(d["num_qubits"]))
    g.add_edges_from(tuple(e) for e in d["coupling"])
    return g


def n2q(c):
    return sum(1 for g in c.gates if len(g.qubits) == 2)


def _qc(c):
    from qiskit import qasm2
    return qasm2.loads(c.to_qasm(), custom_instructions=qasm2.LEGACY_CUSTOM_INSTRUCTIONS)


def to_basis(c):
    from qiskit import qasm2, transpile
    return parse_qasm(qasm2.dumps(transpile(_qc(c), basis_gates=BASIS, optimization_level=0)))


def qiskit_o3(c, graph):
    from qiskit import qasm2, transpile
    from qiskit.transpiler import CouplingMap
    edges = [list(e) for e in graph.edges()] + [[b, a] for a, b in graph.edges()]
    out = transpile(_qc(c), coupling_map=CouplingMap(edges), basis_gates=BASIS,
                    optimization_level=3, seed_transpiler=0)
    return parse_qasm(qasm2.dumps(out))


def layer(c, tl):
    return optimize(c, metric="depth", time_limit=tl)[0]


def post(routed, tl=10.0, kak=True):
    v = layer(to_basis(layer(routed, tl)), tl)
    if kak:
        v = layer(full_rewrite(v, regroup=False, directed=False)[0], tl)
    return v


def metrics(c, t):
    return {"cx": n2q(c), "depth": c.depth(), "depth_2q": c.depth("2q"), "time_s": round(t, 1)}


def qft(n):
    c = Circuit(n)
    gen.qft_gates(c, list(range(n)))
    c.name = f"qft_{n}"
    return c


def cases():
    cs = []
    for n, p in ((16, 1), (16, 2), (32, 1), (32, 2), (64, 1), (64, 2)):
        cs.append(gen.qaoa_maxcut(n, p=p, seed=0))
    cs.append(gen.qaoa_maxcut(32, p=1, degree=4, seed=0))
    for n in (16, 32):
        cs.append(gen.trotter_ising(n, 3, seed=0, graph="reg3"))
    for n in (12, 20):
        cs.append(qft(n))
    cs.append(gen.phase_polynomial(16, 60, seed=0))
    cs.append(gen.random_clifford_t(16, 600, seed=0))
    return cs


def main(trials=16):
    g = device()
    rows = []
    for c in cases():
        row = {"circuit": c.name, "qubits": c.num_qubits, "cx_logical": n2q(to_basis(c))}
        t = time.time()
        q = qiskit_o3(c, g)
        row["qiskit_o3"] = metrics(q, time.time() - t)
        for tag, modes in (("mkco_route", ("nearest", "mean")), ("sabre_dag", ("dag",))):
            t = time.time()
            r, rep = route(c, g, trials=trials, iterations=3, modes=modes,
                           cost=lambda rc, ns: (lambda v: n2q(v) + v.depth())(post(rc, 1.0, kak=False)))
            ok, msg, _ = unroute(c, r, rep["initial_layout"])
            v = post(r)
            sv, _ = statevector_check(to_basis(r), v)
            m = metrics(v, time.time() - t)
            m.update({"swaps": rep["swaps"], "front_mode": rep["front_mode"], "unroute_ok": bool(ok),
                      "coupling_ok": check_coupling(v, g),
                      "post_statevector_ok": None if sv is None else bool(sv)})
            row[tag] = m
        t = time.time()
        qp = post(q)
        sq, _ = statevector_check(q, qp)
        m = metrics(qp, time.time() - t + row["qiskit_o3"]["time_s"])
        m.update({"coupling_ok": check_coupling(qp, g), "post_statevector_ok": None if sq is None else bool(sq)})
        row["qiskit_o3+mkco"] = m
        rows.append(row)
        print({k: (v if not isinstance(v, dict) else (v["cx"], v["depth"])) for k, v in row.items()},
              f"unroute {ok} ({msg})", flush=True)
        json.dump(rows, open(OUT, "w"), indent=1)


if __name__ == "__main__":
    main()
