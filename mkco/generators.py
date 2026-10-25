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


# ------------------------------------------------- fault-tolerant benchmarks
def decompose_toffoli(circuit):
    """Replace ccx / ccz by the standard 7-T Clifford+T circuit (Nielsen & Chuang Fig. 4.9)."""
    out = circuit.copy_with_gates([])
    for g in circuit.gates:
        if g.name in ("ccx", "toffoli", "ccz") and g.kind == "gate" and g.cond is None:
            a, b, t = g.qubits
            if g.name != "ccz":
                out.add("h", [t])
            for name, qs in (("cx", [b, t]), ("tdg", [t]), ("cx", [a, t]), ("t", [t]),
                             ("cx", [b, t]), ("tdg", [t]), ("cx", [a, t]), ("t", [b]),
                             ("t", [t])):
                out.add(name, qs)
            if g.name != "ccz":
                out.add("h", [t])
            for name, qs in (("cx", [a, b]), ("t", [a]), ("tdg", [b]), ("cx", [a, b])):
                out.add(name, qs)
        else:
            out.gates.append(g)
    out.name = (circuit.name or "circuit") + "_ct"
    return out


def cuccaro_adder(n):
    """Cuccaro et al. ripple-carry adder: |c0, a, b, z> -> |c0, a, a+b, z ^ carry>."""
    c = Circuit(2 * n + 2)
    c0, z = 0, 2 * n + 1
    a = [1 + 2 * i for i in range(n)]
    b = [2 + 2 * i for i in range(n)]

    def maj(x, y, w):
        c.add("cx", [w, y]).add("cx", [w, x]).add("ccx", [x, y, w])

    def uma(x, y, w):
        c.add("ccx", [x, y, w]).add("cx", [w, x]).add("cx", [x, y])

    maj(c0, b[0], a[0])
    for i in range(1, n):
        maj(a[i - 1], b[i], a[i])
    c.add("cx", [a[n - 1], z])
    for i in range(n - 1, 0, -1):
        uma(a[i - 1], b[i], a[i])
    uma(c0, b[0], a[0])
    c.name = f"cuccaro_{n}"
    return c


def mcx_vchain(n):
    """n-controlled X with n-2 clean ancillas (Barenco et al. V-chain, compute/uncompute)."""
    ctrl = list(range(n))
    anc = list(range(n, 2 * n - 2))
    tgt = 2 * n - 2
    c = Circuit(2 * n - 1)
    chain = [("ccx", [ctrl[0], ctrl[1], anc[0]])]
    for i in range(2, n - 1):
        chain.append(("ccx", [ctrl[i], anc[i - 2], anc[i - 1]]))
    for name, qs in chain:
        c.add(name, qs)
    c.add("ccx", [ctrl[n - 1], anc[n - 3], tgt])
    for name, qs in reversed(chain):
        c.add(name, qs)
    c.name = f"mcx_vchain_{n}"
    return c


_TRINOMIAL = {2: 1, 3: 1, 4: 1, 5: 2, 6: 1, 7: 1, 9: 4, 10: 3, 11: 2, 12: 3, 14: 5, 15: 1}


def gf2_multiplier(n):
    """F_{2^n} multiplier c ^= a*b mod (x^n + x^k + 1) with an ancilla register
    for the high-degree terms: Toffolis (phase 1), CNOT reduction, Toffolis
    (phase 3), then phase 1 again to clean the ancillas."""
    k = _TRINOMIAL[n]
    a, b = list(range(n)), list(range(n, 2 * n))
    cc = list(range(2 * n, 3 * n))
    e = list(range(3 * n, 4 * n - 1))
    c = Circuit(4 * n - 1)
    phase1 = [(a[i], b[j], e[i + j - n]) for i in range(n) for j in range(n) if i + j >= n]
    for x, y, t in phase1:
        c.add("ccx", [x, y, t])
    for d in range(n - 1):                       # x^(n+d) mod P as a set of low powers
        terms = {d, d + k}
        while max(terms) >= n:
            hi = max(terms)
            terms ^= {hi, hi - n, hi - n + k}
        for p in sorted(terms):
            c.add("cx", [e[d], cc[p]])
    for i in range(n):
        for j in range(n - i):
            c.add("ccx", [a[i], b[j], cc[i + j]])
    for x, y, t in reversed(phase1):
        c.add("ccx", [x, y, t])
    c.name = f"gf2_mult_{n}"
    return c


def t_phase_polynomial(nq, nterms, seed=0, max_w=4):
    """Random Clifford+T phase polynomial: CNOT parity ladders with T / T^dag / S rotations."""
    rng = np.random.default_rng(seed)
    c = Circuit(nq)
    for q in range(nq):
        c.add("h", [q])
    for _ in range(nterms):
        w = int(rng.integers(2, max_w + 1))
        qs = [int(x) for x in rng.choice(nq, w, replace=False)]
        tgt = qs[-1]
        for q in qs[:-1]:
            c.add("cx", [q, tgt])
        c.add(["t", "tdg", "t", "s"][int(rng.integers(4))], [tgt])
        for q in reversed(qs[:-1]):
            c.add("cx", [q, tgt])
    for q in range(nq):
        c.add("h", [q])
    c.name = f"tpoly_n{nq}_t{nterms}_s{seed}"
    return c
