"""Non-Clifford depth with free Clifford gates (T-depth, Toffoli-depth, rotation depth).

In fault-tolerant execution the expensive layers are the ones that contain
non-Clifford gates; Clifford gates are cheap.  The non-Clifford depth of a
circuit is its ASAP depth when counted gates take one step and every other
gate takes none but still synchronises the wires it touches (the usual
definition of T-depth; Circuit.depth with a 0/1 weight).  Minimising it over
all commutation-equivalent reorderings is the mixed-graph colouring of
Theorem 1 restricted to the counted gates (docs/THEORY.md, Proposition 10):

  arcs   u -> v   counted u before counted v in the trace order
  edges  u -- v   counted u, v share a qubit and are incomparable

The mixed graph is built as a *surrogate circuit* that the unchanged MKCO
engine can solve (layering, Max-k-Cut search, certified Jackson bound).  The
counted gates keep their real qubits and per-qubit axes.  Every pair (u, v)
joined by a path whose interior gates are all free gets a private virtual
wire, on which u and v have non-commuting axes; the transitive closure of
these pairs is the whole trace order on the counted gates.  The layers are
then mapped back: each free gate goes right after the last layer of its
counted ancestors, which is a linear extension of the trace order.
"""
from __future__ import annotations

import math

from .circuit import Circuit, Gate
from .depmodel import DepModel
from .schedule import verify_order

_QUARTER = math.pi / 4


def _z_angle(g):
    """Rotation angle of a diagonal single-qubit gate (up to global phase), else None."""
    if g.kind != "gate" or len(g.qubits) != 1:
        return None
    fixed = {"t": _QUARTER, "tdg": -_QUARTER, "s": 2 * _QUARTER, "sdg": -2 * _QUARTER,
             "z": 4 * _QUARTER}
    if g.name in fixed:
        return fixed[g.name]
    if g.name in ("rz", "p", "u1"):
        return g.params[0]
    return None


def _multiple_of(angle, step, tol=1e-9):
    k = angle / step
    return abs(k - round(k)) < tol, int(round(k))


def is_t_like(g):
    """Single-qubit Z rotation by an odd multiple of pi/4 (t, tdg, rz(pi/4), ...)."""
    a = _z_angle(g)
    if a is None:
        return False
    ok, k = _multiple_of(a, _QUARTER)
    return ok and k % 2 == 1


def is_non_clifford_rotation(g):
    """Single-qubit Z rotation whose angle is not a multiple of pi/2."""
    a = _z_angle(g)
    if a is None:
        return False
    return not _multiple_of(a, 2 * _QUARTER)[0]


def counted_predicate(kind):
    """Gate -> bool for the counted gates of a non-Clifford depth metric."""
    if callable(kind):
        return kind
    if kind == "t":
        return is_t_like
    if kind == "toffoli":
        from .gates import TOFFOLI_CLASS
        return lambda g: g.kind == "gate" and g.name in TOFFOLI_CLASS
    if kind == "rotation":
        return is_non_clifford_rotation
    raise ValueError(f"unknown non-Clifford metric {kind!r}")


def counted_depth(circuit, kind="t"):
    pred = counted_predicate(kind)
    return circuit.depth(lambda g: 1 if pred(g) else 0)


def counted_count(circuit, kind="t"):
    pred = counted_predicate(kind)
    return sum(1 for g in circuit.gates if pred(g))


class SurrogateCircuit(Circuit):
    """Circuit whose gate axes are given explicitly (used for the reduced mixed graph)."""

    def __init__(self, num_qubits, axes):
        super().__init__(num_qubits)
        self.axes_by_id = axes

    def copy_with_gates(self, gates):
        c = SurrogateCircuit(self.num_qubits, self.axes_by_id)
        c.name = self.name
        c.gates = list(gates)
        return c

    def gate_axes(self, g):
        return self.axes_by_id[id(g)]


def build_surrogate(circuit, pred):
    """Return (surrogate, counted gate indices, frontier pairs, full DepModel)."""
    m = DepModel(circuit, "depth")
    gates = circuit.gates
    counted = [i for i, g in enumerate(gates) if pred(g)]
    is_counted = set(counted)
    prev_run = {}
    for rs in m.wire_runs:
        for k in range(1, len(rs)):
            prev_run[rs[k]] = rs[k - 1]
    out = [None] * m.n              # counted gates reachable through free-only paths, or {i}
    run_front = {}
    pairs = []
    for i in range(m.n):
        front = set()
        for r in m.gate_runs[i]:
            p = prev_run.get(r)
            if p is None:
                continue
            f = run_front.get(p)
            if f is None:
                f = set()
                for x in m.run_members[p]:
                    f |= out[x]
                run_front[p] = f
            front |= f
        if i in is_counted:
            pairs.extend((u, i) for u in sorted(front))
            out[i] = {i}
        else:
            out[i] = front
    nq = circuit.num_qubits
    axes, sgates = {}, []
    extra = {i: [] for i in counted}
    for k, (u, v) in enumerate(pairs):
        w = nq + k
        extra[u].append((w, "X"))
        extra[v].append((w, "Z"))
    for i in counted:
        g = gates[i]
        if g.kind != "gate" or g.cond is not None or g.clbits:
            raise ValueError("counted gates must be plain unitary gates")
        ax = list(circuit.gate_axes(g))
        qs = list(g.qubits)
        for w, a in extra[i]:
            qs.append(w)
            ax.append(a)
        sg = Gate("nc", qs)
        axes[id(sg)] = tuple(ax)
        sgates.append(sg)
    sur = SurrogateCircuit(nq + len(pairs), axes)
    sur.gates = sgates
    sur.name = (circuit.name or "circuit") + "__noncliff"
    return sur, counted, pairs, m


def _layers_of(sur_gates, num_wires):
    level = {}
    out = []
    for g in sur_gates:
        lv = max((level.get(w, 0) for w in g.qubits), default=0)
        out.append(lv)
        for w in g.qubits:
            level[w] = lv + 1
    return out


def emit_with_layers(circuit, model, layer_of):
    """Order all gates: counted gate c in slot 2*layer(c), free gate f in slot
    2*gap(f)+1 where gap(f) is the last layer among its counted ancestors."""
    prev_run = {}
    for rs in model.wire_runs:
        for k in range(1, len(rs)):
            prev_run[rs[k]] = rs[k - 1]
    val = [0] * model.n
    key = [0] * model.n
    run_val = {}
    for i in range(model.n):
        gap = -1
        for r in model.gate_runs[i]:
            p = prev_run.get(r)
            if p is None:
                continue
            v = run_val.get(p)
            if v is None:
                v = max(val[x] for x in model.run_members[p])
                run_val[p] = v
            gap = max(gap, v)
        if i in layer_of:
            if layer_of[i] <= gap:
                raise AssertionError("layering violates the trace order")
            val[i] = layer_of[i]
            key[i] = 2 * layer_of[i]
        else:
            val[i] = gap
            key[i] = 2 * gap + 1
    return sorted(range(model.n), key=lambda i: (key[i], i))


def optimize_nonclifford(circuit, kind="t", time_limit=10.0, seed=0, merge=True):
    """Minimise the non-Clifford depth by reordering (and optionally rotation merging).

    Returns (circuit, report).  report['lower_bound'] is a certified bound on the
    counted depth of every commutation-equivalent reordering of the (merged)
    circuit, so after == lower_bound proves optimality for that circuit.
    """
    from .coloring import split_barriers
    from .optimize import optimize

    pred = counted_predicate(kind)
    before = counted_depth(circuit, pred)
    cnt_before = counted_count(circuit, pred)
    stats = {}
    cur = circuit
    if merge:
        from .merge import merge_rotations
        cur, stats["merge"] = merge_rotations(circuit)
    out, lbs, segs = [], [], 0
    for kindseg, payload in split_barriers(cur):
        if kindseg == "barrier":
            out.append(payload)
            continue
        segs += 1
        sub = cur.copy_with_gates(payload)
        sur, counted, pairs, model = build_surrogate(sub, pred)
        if not counted:
            out.extend(payload)
            lbs.append(0)
            continue
        opt, rep = optimize(sur, metric="depth", time_limit=time_limit, seed=seed)
        index = {id(g): counted[k] for k, g in enumerate(sur.gates)}
        lv = _layers_of(opt.gates, sur.num_qubits)
        layer_of = {index[id(g)]: lv[k] for k, g in enumerate(opt.gates)}
        order = emit_with_layers(sub, model, layer_of)
        ok, msg = verify_order(model, order)
        if not ok:
            raise RuntimeError(f"structural verification failed: {msg}")
        out.extend(payload[i] for i in order)
        lbs.append(rep["lower_bound"])
        stats.setdefault("segments", []).append(
            {"counted": len(counted), "frontier_pairs": len(pairs), "layers": rep["after"],
             "lower_bound": rep["lower_bound"], "certified": rep["certified_optimal"]})
    res = cur.copy_with_gates(out)
    after = counted_depth(res, pred)
    if after > counted_depth(cur, pred):
        res, after = cur, counted_depth(cur, pred)
    lower = max(lbs) if lbs else 0
    report = {"kind": kind if isinstance(kind, str) else "custom", "before": before,
              "after": after, "count_before": cnt_before, "count_after": counted_count(res, pred),
              "lower_bound": lower, "certified_optimal": bool(segs == 1 and after == lower),
              **stats}
    return res, report
