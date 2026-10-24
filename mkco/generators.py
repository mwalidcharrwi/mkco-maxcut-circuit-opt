"""Circuit generators used in the experiments."""
from __future__ import annotations

import math

import networkx as nx
import numpy as np

from .circuit import Circuit


def random_commuting_mcz(m, n, seed=0, min_size=3, max_size=None):
    """Lee et al. Sec. 4.3: n multi-controlled Z gates on m qubits, each on a
    random subset of between 3 and floor(m/2) qubits."""
    rng = np.random.default_rng(seed)
    max_size = max_size or m // 2
    c = Circuit(m)
    for _ in range(n):
        k = int(rng.integers(min_size, max_size + 1))
        qs = sorted(rng.choice(m, size=k, replace=False).tolist())
        c.add("ccz" if k == 3 else "mcz", qs)
    c.name = f"rand_mcz_m{m}_n{n}_s{seed}"
    return c


def random_commuting_ccz(m, n, seed=0):
    """Appendix C setting: n CCZ gates on m qubits."""
    return random_commuting_mcz(m, n, seed, 3, 3)


def gf2_mult_phases(n):
    """Toffoli phases of Maslov et al.'s F_{2^n} multiplier (Lee et al. Sec. 5.1).

    Registers: a = q[0..n-1], b = q[n..2n-1], c = q[2n..3n-1].
    Phase 1 computes the high-degree terms e_k = sum_{i+j=n+k} a_i b_j,
    Phase 3 adds the low-degree terms d_k = sum_{i+j=k} a_i b_j.
    Both phases consist of mutually commuting Toffoli gates.
    """
    a = list(range(n))
    b = list(range(n, 2 * n))
    c = list(range(2 * n, 3 * n))
    p1 = Circuit(3 * n, qregs=[("a", n), ("b", n), ("c", n)])
    p3 = Circuit(3 * n, qregs=[("a", n), ("b", n), ("c", n)])
    for k in range(n, 2 * n - 1):
        for i in range(n):
            j = k - i
            if 0 <= j < n:
                p1.add("ccx", [a[i], b[j], c[k - n]])
    for k in range(n):
        for i in range(k + 1):
            p3.add("ccx", [a[i], b[k - i], c[k]])
    p1.name, p3.name = f"gf2_{n}_phase1", f"gf2_{n}_phase3"
    return p1, p3


def qft_gates(c, qs, inverse=False, do_swaps=False):
    n = len(qs)
    seq = []
    for j in range(n):
        seq.append(("h", [qs[j]], ()))
        for k in range(j + 1, n):
            seq.append(("cp", [qs[k], qs[j]], (math.pi / 2 ** (k - j),)))
    if inverse:
        seq = [(nm, q, tuple(-x for x in p)) for nm, q, p in reversed(seq)]
    for nm, q, p in seq:
        c.add(nm, q, p)


def draper_adder(n, with_qft=True):
    """|a>|b> -> |a>|a+b mod 2^n> (Draper 2000).  The conditional rotations
    between the two QFTs commute (Lee et al. Sec. 5.2)."""
    a = list(range(n))
    b = list(range(n, 2 * n))
    c = Circuit(2 * n, qregs=[("a", n), ("b", n)])
    if with_qft:
        qft_gates(c, b)
    for j in range(n):          # b_j holds phase 2*pi*b/2^(n-j) after QFT
        for i in range(n - j):
            c.add("cp", [a[i], b[j]], (math.pi / 2 ** (n - j - 1 - i),))
    if with_qft:
        qft_gates(c, b, inverse=True)
    c.name = f"draper_{n}" + ("" if with_qft else "_core")
    return c


def qaoa_maxcut(nq, p=1, degree=3, seed=0, decompose=False):
    g = nx.random_regular_graph(degree, nq, seed=seed)
    rng = np.random.default_rng(seed)
    c = Circuit(nq)
    for q in range(nq):
        c.add("h", [q])
    edges = list(g.edges())
    for layer in range(p):
        gamma, beta = rng.uniform(0, math.pi, 2)
        rng.shuffle(edges)
        for u, v in edges:
            if decompose:
                c.add("cx", [u, v]).add("rz", [v], (2 * gamma,)).add("cx", [u, v])
            else:
                c.add("rzz", [u, v], (2 * gamma,))
        for q in range(nq):
            c.add("rx", [q], (2 * beta,))
    c.name = f"qaoa_n{nq}_p{p}_d{degree}" + ("_cx" if decompose else "")
    return c


def random_clifford_t(nq, ngates, seed=0, p2=0.4):
    rng = np.random.default_rng(seed)
    c = Circuit(nq)
    names = ["h", "s", "t", "tdg", "x", "z"]
    for _ in range(ngates):
        if rng.random() < p2:
            u, v = rng.choice(nq, 2, replace=False)
            c.add("cx", [int(u), int(v)])
        else:
            c.add(names[rng.integers(len(names))], [int(rng.integers(nq))])
    c.name = f"rand_cliffT_n{nq}_g{ngates}_s{seed}"
    return c


def trotter_ising(nq, steps=3, seed=0, graph="ring"):
    rng = np.random.default_rng(seed)
    if graph == "ring":
        edges = [(i, (i + 1) % nq) for i in range(nq)]
    else:
        edges = list(nx.random_regular_graph(3, nq, seed=seed).edges())
    c = Circuit(nq)
    for _ in range(steps):
        order = list(edges)
        rng.shuffle(order)
        for u, v in order:
            c.add("cx", [u, v]).add("rz", [v], (0.3,)).add("cx", [u, v])
        for q in range(nq):
            c.add("rx", [q], (0.2,))
    c.name = f"trotter_{graph}_n{nq}_s{steps}"
    return c


def phase_polynomial(nq, nterms, seed=0, max_w=4):
    """Random diagonal circuit of multi-qubit Z-rotations, each realised as a
    CNOT parity ladder + Rz (a typical non-commuting gate-level structure)."""
    rng = np.random.default_rng(seed)
    c = Circuit(nq)
    for _ in range(nterms):
        w = int(rng.integers(2, max_w + 1))
        qs = [int(x) for x in rng.choice(nq, w, replace=False)]
        tgt = qs[-1]
        for q in qs[:-1]:
            c.add("cx", [q, tgt])
        c.add("rz", [tgt], (float(rng.uniform(0, 2 * math.pi)),))
        for q in reversed(qs[:-1]):
            c.add("cx", [q, tgt])
    c.name = f"phasepoly_n{nq}_t{nterms}_s{seed}"
    return c
