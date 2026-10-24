"""Circuit intermediate representation, metrics and OpenQASM 2.0 export."""
from __future__ import annotations

from collections import Counter
from functools import lru_cache

import numpy as np

from . import gates as G


class Gate:
    """One instruction.  kind is 'gate', 'measure', 'reset' or 'barrier'."""
    __slots__ = ("name", "qubits", "params", "clbits", "cond", "kind")

    def __init__(self, name, qubits, params=(), clbits=(), cond=None, kind="gate"):
        self.name = name
        self.qubits = tuple(qubits)
        self.params = tuple(float(p) for p in params)
        self.clbits = tuple(clbits)
        self.cond = cond            # None or (creg_name, value, clbit_indices)
        self.kind = kind

    def wires(self, num_qubits):
        """Qubit wires followed by classical wires (offset by num_qubits)."""
        w = list(self.qubits)
        cl = set(self.clbits)
        if self.cond is not None:
            cl.update(self.cond[2])
        w.extend(num_qubits + c for c in sorted(cl))
        return w

    def __repr__(self):
        p = f"({', '.join(f'{x:.4g}' for x in self.params)})" if self.params else ""
        return f"{self.name}{p} {list(self.qubits)}"


class CustomGateDef:
    """A user `gate` definition from an OpenQASM file."""

    def __init__(self, name, param_names, qarg_names, body, text, circuit):
        self.name = name
        self.param_names = list(param_names)
        self.qarg_names = list(qarg_names)
        self.body = body            # list of (gate_name, [param_ast], [qarg_name])
        self.text = text            # original source text, re-emitted on export
        self._circuit = circuit
        self._cache = {}

    @property
    def num_qubits(self):
        return len(self.qarg_names)

    def expand(self, params, qubits):
        """Inline the body into library gates acting on the given global qubits."""
        from .qasm import eval_expr
        env = dict(zip(self.param_names, params))
        qmap = dict(zip(self.qarg_names, qubits))
        out = []
        for gname, pexprs, qargs in self.body:
            pv = [eval_expr(e, env) for e in pexprs]
            qv = [qmap[a] for a in qargs]
            if gname in self._circuit.custom:
                out.extend(self._circuit.custom[gname].expand(pv, qv))
            else:
                out.append(Gate(gname, qv, pv))
        return out

    def unitary(self, params):
        key = tuple(round(p, 12) for p in params)
        if key not in self._cache:
            from .sim import apply_matrix
            k = self.num_qubits
            dim = 2 ** k
            st = np.eye(dim, dtype=complex).reshape((2,) * k + (dim,))
            for g in self.expand(params, list(range(k))):
                st = apply_matrix(st, G.gate_matrix(g.name, g.params, len(g.qubits)), g.qubits)
            self._cache[key] = st.reshape(dim, dim)
        return self._cache[key]


class Circuit:
    def __init__(self, num_qubits, num_clbits=0, qregs=None, cregs=None):
        self.num_qubits = num_qubits
        self.num_clbits = num_clbits
        self.qregs = qregs if qregs is not None else [("q", num_qubits)]
        self.cregs = cregs if cregs is not None else ([("c", num_clbits)] if num_clbits else [])
        self.gates: list[Gate] = []
        self.custom: dict[str, CustomGateDef] = {}
        self.custom_order: list[str] = []
        self.name = ""

    # ------------------------------------------------------------------ build
    def add(self, name, qubits, params=(), **kw):
        self.gates.append(Gate(name, qubits, params, **kw))
        return self

    def copy_with_gates(self, gates):
        c = Circuit(self.num_qubits, self.num_clbits, list(self.qregs), list(self.cregs))
        c.custom = self.custom
        c.custom_order = self.custom_order
        c.name = self.name
        c.gates = list(gates)
        return c

    # ------------------------------------------------------------- semantics
    def gate_unitary(self, g):
        if g.name in self.custom:
            return self.custom[g.name].unitary(g.params)
        return G.gate_matrix(g.name, g.params, len(g.qubits))

    def gate_axes(self, g):
        """Per-qubit commutation axes (see gates.py)."""
        if g.kind != "gate":
            return tuple([None] * len(g.qubits))
        if g.name in self.custom:
            d = self.custom[g.name]
            if d.num_qubits > 8:
                return tuple([None] * len(g.qubits))
            return _custom_axes(d, tuple(round(p, 12) for p in g.params))
        return G.library_axes(g.name, tuple(round(p, 12) for p in g.params), len(g.qubits))

    # ---------------------------------------------------------------- metrics
    def depth(self, weight=None, barrier_sync=False):
        """ASAP depth.  `weight(gate)` gives each gate's duration (default 1).

        Zero-weight gates still synchronise the wires they touch, which is the
        standard definition for T-depth / Toffoli-depth / 2q-depth.  Barriers
        are ignored (as in Qiskit's QuantumCircuit.depth) unless `barrier_sync`
        is set, in which case they synchronise the qubits they span, as a
        hardware scheduler does.
        """
        wf = metric_weight(weight)
        level = {}
        best = 0
        nq = self.num_qubits
        for g in self.gates:
            if g.kind == "barrier":
                if barrier_sync and g.qubits:
                    lv = max(level.get(q, 0) for q in g.qubits)
                    for q in g.qubits:
                        level[q] = lv
                continue
            ws = g.wires(nq)
            lv = max((level.get(w, 0) for w in ws), default=0) + wf(g)
            for w in ws:
                level[w] = lv
            if lv > best:
                best = lv
        return best

    def count_ops(self):
        return Counter(g.name for g in self.gates)

    def size(self):
        return sum(1 for g in self.gates if g.kind != "barrier")

    def metrics(self):
        return {
            "qubits": self.num_qubits,
            "gates": self.size(),
            "depth": self.depth("depth"),
            "depth_2q": self.depth("2q"),
            "t_depth": self.depth("t"),
            "toffoli_depth": self.depth("toffoli"),
        }

    # ----------------------------------------------------------------- export
    def _wire_names(self):
        qn, cn = [], []
        for name, size in self.qregs:
            qn.extend(f"{name}[{i}]" for i in range(size))
        for name, size in self.cregs:
            cn.extend(f"{name}[{i}]" for i in range(size))
        return qn, cn

    def to_qasm(self):
        qn, cn = self._wire_names()
        lines = ["OPENQASM 2.0;", 'include "qelib1.inc";']
        for name in self.custom_order:
            lines.append(self.custom[name].text.strip())
        for name, size in self.qregs:
            lines.append(f"qreg {name}[{size}];")
        for name, size in self.cregs:
            lines.append(f"creg {name}[{size}];")
        for g in self.gates:
            pre = f"if({g.cond[0]}=={g.cond[1]}) " if g.cond is not None else ""
            if g.kind == "measure":
                lines.append(f"{pre}measure {qn[g.qubits[0]]} -> {cn[g.clbits[0]]};")
            elif g.kind == "reset":
                lines.append(f"{pre}reset {qn[g.qubits[0]]};")
            elif g.kind == "barrier":
                lines.append(f"barrier {','.join(qn[q] for q in g.qubits)};")
            else:
                p = f"({','.join(_fmt(x) for x in g.params)})" if g.params else ""
                lines.append(f"{pre}{g.name}{p} {','.join(qn[q] for q in g.qubits)};")
        return "\n".join(lines) + "\n"


def _fmt(x):
    return repr(float(x))


@lru_cache(maxsize=4096)
def _custom_axes_impl(defn_id, params):
    d = _DEF_REGISTRY[defn_id]
    return G.axes_from_unitary(d.unitary(params))


_DEF_REGISTRY: dict[int, CustomGateDef] = {}


def _custom_axes(d, params):
    _DEF_REGISTRY[id(d)] = d
    return _custom_axes_impl(id(d), params)


def metric_weight(weight):
    """Turn a metric name (or callable) into a gate -> duration function."""
    if weight is None or weight == "depth":
        return lambda g: 1
    if callable(weight):
        return weight
    if weight == "2q":
        return lambda g: 1 if len(g.qubits) >= 2 else 0
    if weight == "t":
        return lambda g: 1 if g.name in G.T_CLASS else 0
    if weight == "toffoli":
        return lambda g: 1 if g.name in G.TOFFOLI_CLASS else 0
    raise ValueError(f"unknown metric {weight!r}")
