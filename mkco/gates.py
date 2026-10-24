"""Gate library: unitaries and per-qubit commutation axes.

Matrix convention: a gate applied to qubits (q0, q1, ..., q_{k-1}) has a
2^k x 2^k matrix in the basis |b0 b1 ... b_{k-1}> where b0 (the first listed
qubit) is the most significant bit.  For controlled gates the controls are
listed first, as in OpenQASM 2.0.

Commutation axes
----------------
For every qubit a gate touches we compute an *axis*: the Bloch direction n
such that the gate commutes with the single-qubit Pauli operator n.sigma on
that qubit.  Two gates that share qubits commute whenever they have the same
axis on every shared qubit (proof in docs/THEORY.md, Lemma 1).  Axis values:

    'Z', 'X', 'Y'      -- the gate is block-diagonal in that Pauli basis
    (nx, ny, nz)       -- any other direction (e.g. 'H' axis for h / ch)
    'I'                -- the gate acts as identity on that qubit
    None               -- no axis: the gate is ordered against everything
"""
from __future__ import annotations

import cmath
import math
from functools import lru_cache

import numpy as np

SQ2 = 1.0 / math.sqrt(2.0)
I2 = np.eye(2, dtype=complex)
PX = np.array([[0, 1], [1, 0]], dtype=complex)
PY = np.array([[0, -1j], [1j, 0]], dtype=complex)
PZ = np.array([[1, 0], [0, -1]], dtype=complex)
PH = SQ2 * np.array([[1, 1], [1, -1]], dtype=complex)


def u3(theta, phi, lam):
    c, s = math.cos(theta / 2), math.sin(theta / 2)
    return np.array([[c, -cmath.exp(1j * lam) * s],
                     [cmath.exp(1j * phi) * s, cmath.exp(1j * (phi + lam)) * c]], dtype=complex)


def rx(t):
    c, s = math.cos(t / 2), math.sin(t / 2)
    return np.array([[c, -1j * s], [-1j * s, c]], dtype=complex)


def ry(t):
    c, s = math.cos(t / 2), math.sin(t / 2)
    return np.array([[c, -s], [s, c]], dtype=complex)


def rz(t):
    return np.diag([cmath.exp(-0.5j * t), cmath.exp(0.5j * t)])


def phase(lam):
    return np.diag([1.0, cmath.exp(1j * lam)]).astype(complex)


def r_gate(theta, phi):
    n = math.cos(phi) * PX + math.sin(phi) * PY
    return math.cos(theta / 2) * I2 - 1j * math.sin(theta / 2) * n


def controlled(u, nctrl=1):
    d = u.shape[0]
    m = np.eye((2 ** nctrl) * d, dtype=complex)
    m[-d:, -d:] = u
    return m


def kron(*ms):
    out = np.array([[1.0 + 0j]])
    for m in ms:
        out = np.kron(out, m)
    return out


def expm_pauli(theta, p):
    """exp(-i theta/2 P) for a Hermitian involution P."""
    return math.cos(theta / 2) * np.eye(p.shape[0]) - 1j * math.sin(theta / 2) * p


SX = 0.5 * np.array([[1 + 1j, 1 - 1j], [1 - 1j, 1 + 1j]], dtype=complex)
SWAP = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]], dtype=complex)
ISWAP = np.array([[1, 0, 0, 0], [0, 0, 1j, 0], [0, 1j, 0, 0], [0, 0, 0, 1]], dtype=complex)
CX = controlled(PX)
CX_REV = np.array([[1, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0]], dtype=complex)


def _seq_unitary(nq, seq):
    """Compose a gate sequence [(name, params, qubits), ...] into a unitary."""
    from .sim import apply_matrix
    dim = 2 ** nq
    state = np.eye(dim, dtype=complex).reshape((2,) * nq + (dim,))
    for name, params, qs in seq:
        state = apply_matrix(state, gate_matrix(name, params, len(qs)), qs)
    return state.reshape(dim, dim)


_P4 = math.pi / 4
_RCCX_SEQ = [("u2", (0, math.pi), (2,)), ("u1", (_P4,), (2,)), ("cx", (), (1, 2)),
             ("u1", (-_P4,), (2,)), ("cx", (), (0, 2)), ("u1", (_P4,), (2,)),
             ("cx", (), (1, 2)), ("u1", (-_P4,), (2,)), ("u2", (0, math.pi), (2,))]
_RC3X_SEQ = [("u2", (0, math.pi), (3,)), ("u1", (_P4,), (3,)), ("cx", (), (2, 3)),
             ("u1", (-_P4,), (3,)), ("u2", (0, math.pi), (3,)), ("cx", (), (0, 3)),
             ("u1", (_P4,), (3,)), ("cx", (), (1, 3)), ("u1", (-_P4,), (3,)),
             ("cx", (), (0, 3)), ("u1", (_P4,), (3,)), ("cx", (), (1, 3)),
             ("u1", (-_P4,), (3,)), ("u2", (0, math.pi), (3,)), ("u1", (_P4,), (3,)),
             ("cx", (), (2, 3)), ("u1", (-_P4,), (3,)), ("u2", (0, math.pi), (3,))]

# name -> (num_qubits or None for variable, num_params, matrix builder)
_FIXED = {
    "id": (1, 0, lambda: I2), "u0": (1, 1, lambda g: I2), "x": (1, 0, lambda: PX),
    "y": (1, 0, lambda: PY), "z": (1, 0, lambda: PZ), "h": (1, 0, lambda: PH),
    "s": (1, 0, lambda: phase(math.pi / 2)), "sdg": (1, 0, lambda: phase(-math.pi / 2)),
    "t": (1, 0, lambda: phase(math.pi / 4)), "tdg": (1, 0, lambda: phase(-math.pi / 4)),
    "sx": (1, 0, lambda: SX), "sxdg": (1, 0, lambda: SX.conj().T),
    "rx": (1, 1, rx), "ry": (1, 1, ry), "rz": (1, 1, rz), "u1": (1, 1, phase), "p": (1, 1, phase),
    "u2": (1, 2, lambda p, l: u3(math.pi / 2, p, l)), "u3": (1, 3, u3), "u": (1, 3, u3),
    "U": (1, 3, u3), "r": (1, 2, r_gate),
    "cx": (2, 0, lambda: CX), "CX": (2, 0, lambda: CX), "cnot": (2, 0, lambda: CX),
    "cy": (2, 0, lambda: controlled(PY)), "cz": (2, 0, lambda: controlled(PZ)),
    "ch": (2, 0, lambda: controlled(PH)), "swap": (2, 0, lambda: SWAP),
    "iswap": (2, 0, lambda: ISWAP),
    "crx": (2, 1, lambda t: controlled(rx(t))), "cry": (2, 1, lambda t: controlled(ry(t))),
    "crz": (2, 1, lambda t: controlled(rz(t))), "cu1": (2, 1, lambda l: controlled(phase(l))),
    "cp": (2, 1, lambda l: controlled(phase(l))), "cphase": (2, 1, lambda l: controlled(phase(l))),
    "cu3": (2, 3, lambda t, p, l: controlled(u3(t, p, l))),
    "cu": (2, 4, lambda t, p, l, g: controlled(cmath.exp(1j * g) * u3(t, p, l))),
    "csx": (2, 0, lambda: controlled(SX)), "cs": (2, 0, lambda: controlled(phase(math.pi / 2))),
    "csdg": (2, 0, lambda: controlled(phase(-math.pi / 2))),
    "rxx": (2, 1, lambda t: expm_pauli(t, kron(PX, PX))),
    "ryy": (2, 1, lambda t: expm_pauli(t, kron(PY, PY))),
    "rzz": (2, 1, lambda t: expm_pauli(t, kron(PZ, PZ))),
    "rzx": (2, 1, lambda t: expm_pauli(t, kron(PZ, PX))),
    "ecr": (2, 0, lambda: SQ2 * (kron(PX, I2) - kron(PY, PX))),
    "dcx": (2, 0, lambda: CX_REV @ CX),
    "ccx": (3, 0, lambda: controlled(PX, 2)), "toffoli": (3, 0, lambda: controlled(PX, 2)),
    "ccz": (3, 0, lambda: controlled(PZ, 2)),
    "cswap": (3, 0, lambda: controlled(SWAP)), "fredkin": (3, 0, lambda: controlled(SWAP)),
    "rccx": (3, 0, lambda: _seq_unitary(3, _RCCX_SEQ)),
    "c3x": (4, 0, lambda: controlled(PX, 3)), "c3sqrtx": (4, 0, lambda: controlled(SX, 3)),
    "rc3x": (4, 0, lambda: _seq_unitary(4, _RC3X_SEQ)),
    "rcccx": (4, 0, lambda: _seq_unitary(4, _RC3X_SEQ)),
    "c4x": (5, 0, lambda: controlled(PX, 4)),
}

# variable-arity multi-controlled families: controls first, target last
_VARIABLE = {"mcx": 0, "mcz": 0, "mcphase": 1, "mcp": 1, "mcu1": 1}

# gates whose names identify "Toffoli-class" operations (used by Toffoli-depth)
TOFFOLI_CLASS = {"ccx", "toffoli", "ccz", "c3x", "c4x", "mcx", "mcz", "rccx", "rc3x",
                 "rcccx", "c3sqrtx", "cswap", "fredkin"}
T_CLASS = {"t", "tdg"}

NON_UNITARY = {"measure", "reset", "barrier"}


def is_library_gate(name):
    return name in _FIXED or name in _VARIABLE


def library_arity(name):
    if name in _FIXED:
        return _FIXED[name][0], _FIXED[name][1]
    if name in _VARIABLE:
        return None, _VARIABLE[name]
    raise KeyError(name)


def gate_matrix(name, params=(), nq=None):
    """Unitary of a library gate (see module docstring for the qubit order)."""
    return _gate_matrix_cached(name, tuple(round(float(p), 15) for p in params), nq)


@lru_cache(maxsize=4096)
def _gate_matrix_cached(name, params, nq):
    if name in _FIXED:
        k, npar, fn = _FIXED[name]
        if name == "u0":
            return I2
        m = fn(*params) if npar else fn()
        return np.asarray(m, dtype=complex)
    if name in _VARIABLE:
        if nq is None:
            raise ValueError(f"{name} needs an explicit qubit count")
        dim = 2 ** nq
        if name == "mcx":
            return controlled(PX, nq - 1)
        if name == "mcz":
            d = np.ones(dim, dtype=complex)
            d[-1] = -1
            return np.diag(d)
        d = np.ones(dim, dtype=complex)
        d[-1] = cmath.exp(1j * params[0])
        return np.diag(d)
    raise KeyError(f"unknown gate '{name}'")


# ---------------------------------------------------------------------------
# commutation axes
# ---------------------------------------------------------------------------

def _canon_axis(n, tol=1e-7):
    n = np.asarray(n, dtype=float)
    n = n / np.linalg.norm(n)
    for i in range(3):
        if abs(n[i]) > tol:
            if n[i] < 0:
                n = -n
            break
    if abs(n[0] - 1) < tol:
        return "X"
    if abs(n[1] - 1) < tol:
        return "Y"
    if abs(n[2] - 1) < tol:
        return "Z"
    return tuple(round(float(v), 6) for v in n)


def axes_from_unitary(u, tol=1e-8):
    """Per-qubit commutation axis of an arbitrary k-qubit unitary."""
    dim = u.shape[0]
    k = int(round(math.log2(dim)))
    out = []
    for j in range(k):
        cols = []
        for p in (PX, PY, PZ):
            pj = kron(*([I2] * j + [p] + [I2] * (k - j - 1)))
            c = u @ pj - pj @ u
            cols.append(np.concatenate([c.real.ravel(), c.imag.ravel()]))
        a = np.stack(cols, axis=1)
        s, vt = np.linalg.svd(a, full_matrices=True)[1:]
        scale = max(1.0, np.abs(u).max())
        null = [vt[i] for i in range(3) if (s[i] if i < len(s) else 0.0) < tol * scale * 10]
        if len(null) >= 2:
            out.append("I")
        elif len(null) == 1:
            out.append(_canon_axis(null[0]))
        else:
            out.append(None)
    return tuple(out)


@lru_cache(maxsize=8192)
def library_axes(name, params, nq):
    if name in ("mcx", "c3x", "c4x", "ccx", "toffoli", "cx", "CX", "cnot"):
        return tuple(["Z"] * (nq - 1) + ["X"])
    if name in ("mcz", "mcphase", "mcp", "mcu1", "ccz", "cz", "cp", "cu1", "cphase"):
        return tuple(["Z"] * nq)
    if nq > 8:
        return tuple([None] * nq)
    return axes_from_unitary(gate_matrix(name, params, nq))


def axes_compatible(a, b):
    """True if two gates with axes a and b on a shared qubit commute there."""
    if a == "I" or b == "I":
        return True
    return a is not None and a == b
