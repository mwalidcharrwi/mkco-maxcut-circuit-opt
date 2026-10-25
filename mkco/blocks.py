"""Two-qubit block resynthesis (optional rewrite step, needs Qiskit).

A *block* is a maximal stretch of gates that act only on one qubit pair
{a, b} and are contiguous on both wires (no other gate touches a or b in
between).  Each block is replaced by a single 4x4 unitary that is
re-synthesised by the KAK / Weyl decomposition into at most three native
ECRs (or CXs, for CX-native circuits) plus single-qubit ZSX gates.  We call Qiskit's TwoQubitBasisDecomposer
for the numerical KAK step; collecting the blocks, keeping the native ECR
direction, the cost test and the verification are ours.

A replacement is kept only when it lowers (two-qubit gates, physical
single-qubit gates, total gates), every ECR it emits has the same direction
as the ECRs it replaces (so the result stays executable on the device), and
its unitary matches the block's product up to global phase.
"""
from __future__ import annotations

import numpy as np

from .circuit import Gate
from .sim import apply_matrix

VIRTUAL = {"rz", "p", "u1"}


def _block_unitary(circuit, gates, a, b):
    st = np.eye(4, dtype=complex).reshape(2, 2, 4)
    pos = {a: 0, b: 1}
    for g in gates:
        st = apply_matrix(st, circuit.gate_unitary(g), [pos[q] for q in g.qubits])
    return st.reshape(4, 4)


def _equal_up_to_phase(x, y, tol=1e-7):
    idx = np.unravel_index(np.argmax(np.abs(y)), y.shape)
    if abs(y[idx]) < 1e-12:
        return False
    ph = x[idx] / y[idx]
    return abs(abs(ph) - 1) < 1e-6 and np.allclose(x, ph * y, atol=tol)


def _cost(gates):
    two = sum(1 for g in gates if len(g.qubits) == 2)
    phys = sum(1 for g in gates if len(g.qubits) == 1 and g.name not in VIRTUAL)
    return (two, phys, len(gates))


def _local_depth(gates):
    level = {}
    for g in gates:
        lv = max(level.get(q, 0) for q in g.qubits) + 1
        for q in g.qubits:
            level[q] = lv
    return max(level.values(), default=0)


def _better(new, old, objective):
    """Acceptance test.  'depth': fewer ECRs, or as many ECRs and a shallower block.
    'count': lexicographically fewer (ECRs, physical 1q gates, gates)."""
    cn, co = _cost(new), _cost(old)
    if objective == "count":
        return cn < co
    if cn[0] != co[0]:
        return cn[0] < co[0]
    return _local_depth(new) < _local_depth(old)


def collect_blocks(circuit):
    """Return blocks as lists of gate indices (each block has >= 1 two-qubit gate)."""
    gates = circuit.gates
    nq = circuit.num_qubits
    open_block = {}          # qubit -> block id
    pending = {}             # qubit -> 1q gate indices since its last multi-qubit gate
    blocks = []              # block id -> {"pair": (a, b), "idx": [...], "open": bool}

    def close(bid):
        if bid is None or not blocks[bid]["open"]:
            return
        blocks[bid]["open"] = False
        for q in blocks[bid]["pair"]:
            if open_block.get(q) == bid:
                del open_block[q]

    for i, g in enumerate(gates):
        plain = g.kind == "gate" and g.cond is None
        if plain and len(g.qubits) == 1:
            q = g.qubits[0]
            bid = open_block.get(q)
            if bid is not None:
                blocks[bid]["idx"].append(i)
            else:
                pending.setdefault(q, []).append(i)
            continue
        if plain and len(g.qubits) == 2:
            a, b = g.qubits
            ba, bb = open_block.get(a), open_block.get(b)
            if ba is not None and ba == bb:
                blocks[ba]["idx"].append(i)
                continue
            close(ba)
            close(bb)
            idx = pending.pop(a, []) + pending.pop(b, []) + [i]
            blocks.append({"pair": (a, b), "idx": sorted(idx), "open": True})
            open_block[a] = open_block[b] = len(blocks) - 1
            continue
        # anything else (>= 3 qubits, measure, reset, barrier, conditional) ends blocks
        for w in g.wires(nq):
            if w < nq:
                close(open_block.get(w))
                pending.pop(w, None)
    return [blk for blk in blocks]


def regroup_pairs(circuit):
    """Commutation-aware block formation (returns an equivalent circuit, n_moved).

    A legal reordering (a linear extension of the run order of DepModel, so
    docs/THEORY.md Lemma 2 applies) that keeps the gates of one qubit pair
    together whenever commutation allows it.  Kahn's algorithm emits, among the
    ready gates, first those that would extend a block that is still open
    (a 1q gate on one of its qubits, or a 2q gate on exactly its pair), and
    otherwise the ready gate that came first in the input.  Gates that the input
    order separated by commuting gates (e.g. ECRs sharing a control, whose
    control axis is X) then fall into the same block for KAK resynthesis.
    Barriers are respected: each barrier-free segment is regrouped on its own.
    """
    import heapq

    from .coloring import split_barriers
    from .depmodel import DepModel
    from .schedule import verify_order

    out, moved = [], 0
    for kind, payload in split_barriers(circuit):
        if kind == "barrier":
            out.append(payload)
            continue
        sub = circuit.copy_with_gates(payload)
        m = DepModel(sub, "depth")
        gates = sub.gates
        n = m.n
        plain = [g.kind == "gate" and g.cond is None and len(g.qubits) <= 2 for g in gates]
        left = [len(mem) for mem in m.run_members]
        nxt_run = np.full(m.num_runs, -1, dtype=np.int64)
        waiting = np.zeros(n, dtype=np.int64)
        for w, rs in enumerate(m.wire_runs):
            for i in range(len(rs) - 1):
                nxt_run[rs[i]] = rs[i + 1]
            for r in rs[1:]:
                for gi in m.run_members[r]:
                    waiting[gi] += 1
        open_pair = {}
        ready_on = {}
        heap, cand = [], []
        done = np.zeros(n, dtype=bool)

        def fits(gi):
            g = gates[gi]
            if not plain[gi]:
                return False
            if len(g.qubits) == 1:
                return g.qubits[0] in open_pair
            a, b = g.qubits
            return open_pair.get(a) == open_pair.get(b) == frozenset((a, b))

        def make_ready(gi):
            heapq.heappush(heap, gi)
            for q in gates[gi].qubits:
                ready_on.setdefault(q, set()).add(gi)
            if fits(gi):
                heapq.heappush(cand, gi)

        for gi in range(n):
            if waiting[gi] == 0:
                make_ready(gi)
        order = []
        while len(order) < n:
            gi = -1
            while cand:
                x = heapq.heappop(cand)
                if not done[x] and fits(x):
                    gi = x
                    break
            if gi < 0:
                while done[heap[0]]:
                    heapq.heappop(heap)
                gi = heapq.heappop(heap)
            done[gi] = True
            order.append(gi)
            g = gates[gi]
            for q in g.qubits:
                ready_on[q].discard(gi)
            qs = g.qubits
            if plain[gi] and len(qs) == 2:
                pair = frozenset(qs)
                if not (open_pair.get(qs[0]) == open_pair.get(qs[1]) == pair):
                    for q in qs:
                        old = open_pair.pop(q, None)
                        if old is not None:
                            for o in old:
                                open_pair.pop(o, None)
                    for q in qs:
                        open_pair[q] = pair
                    for q in qs:
                        for x in ready_on.get(q, ()):
                            if fits(x):
                                heapq.heappush(cand, x)
            elif not (plain[gi] and len(qs) == 1):
                for w in g.wires(sub.num_qubits):
                    old = open_pair.pop(w, None)
                    if old is not None:
                        for o in old:
                            open_pair.pop(o, None)
            for r in m.gate_runs[gi]:
                left[r] -= 1
                if left[r] == 0 and nxt_run[r] >= 0:
                    for x in m.run_members[nxt_run[r]]:
                        waiting[x] -= 1
                        if waiting[x] == 0:
                            make_ready(x)
        ok, msg = verify_order(m, order)
        if not ok:
            raise AssertionError(f"regrouping is not a legal reordering: {msg}")
        moved += sum(1 for i, gi in enumerate(order) if gi != i)
        out.extend(gates[gi] for gi in order)
    return circuit.copy_with_gates(out), moved


def regroup_both_ways(circuit):
    """regroup_pairs forward, then on the reversed circuit (pulls block members
    from both sides; the reverse of a legal reordering of the reversed circuit is
    a legal reordering of the circuit, since commutation is symmetric)."""
    c, m1 = regroup_pairs(circuit)
    r, m2 = regroup_pairs(c.copy_with_gates(list(reversed(c.gates))))
    return r.copy_with_gates(list(reversed(r.gates))), m1 + m2


def resynthesize_blocks(circuit, min_two_qubit=1, objective="depth", directed=True):
    """One pass over all blocks.  Returns (circuit, stats).

    directed=False (symmetric couplers, e.g. CX-level routing studies) accepts
    blocks with both gate directions and either output direction."""
    try:
        from qiskit.circuit.library import CXGate, ECRGate
        from qiskit.synthesis import TwoQubitBasisDecomposer
    except ImportError as e:            # optional dependency
        raise ImportError("two-qubit block resynthesis needs qiskit") from e
    names = {g.name for g in circuit.gates if len(g.qubits) == 2}
    if names <= {"ecr"}:
        kak, basis_gate = ECRGate(), "ecr"
    elif names <= {"cx"}:
        kak, basis_gate = CXGate(), "cx"
    else:
        # only ECR- or CX-native circuits are handled; others pass through
        return circuit, {"blocks": 0, "replaced": 0, "skipped_basis": sorted(names)}
    decomposer = TwoQubitBasisDecomposer(kak, euler_basis="ZSX")
    gates = circuit.gates
    replace, drop = {}, set()
    stats = {"blocks": 0, "replaced": 0, "ecr_removed": 0}
    for blk in collect_blocks(circuit):
        idx = blk["idx"]
        members = [gates[i] for i in idx]
        twos = [g for g in members if len(g.qubits) == 2]
        if len(twos) < min_two_qubit or len(members) < 2:
            continue
        stats["blocks"] += 1
        dirs = {g.qubits for g in twos}
        if len(dirs) != 1 and directed:
            continue                    # mixed ECR directions: leave as is
        c, t = twos[0].qubits
        u = _block_unitary(circuit, members, c, t)            # basis |c t>, c most significant
        # Qiskit is little-endian; put c on Qiskit qubit 0 so that ecr(0, 1) = ecr(c, t)
        uq = u.reshape(2, 2, 2, 2).transpose(1, 0, 3, 2).reshape(4, 4)
        qc = decomposer(uq, approximate=False)
        qmap = {0: c, 1: t}
        new, ok = [], True
        for inst in qc.data:
            qs = [qmap[qc.find_bit(q).index] for q in inst.qubits]
            name = inst.operation.name
            if name == basis_gate:
                if directed and tuple(qs) != (c, t):
                    ok = False
                    break
                new.append(Gate(basis_gate, qs))
            elif name in ("rz", "sx", "x"):
                new.append(Gate(name, qs, [float(p) for p in inst.operation.params]))
            else:
                ok = False
                break
        if not ok or not _better(new, members, objective):
            continue
        if not _equal_up_to_phase(_block_unitary(circuit, new, c, t), u):
            # Qiskit's Weyl decomposition snaps blocks that are very close to a
            # cheaper class (e.g. a controlled phase of angle 5e-5 -> identity)
            # even with approximate=False; such inexact results are rejected.
            stats["rejected_inexact"] = stats.get("rejected_inexact", 0) + 1
            continue
        replace[idx[-1]] = new
        drop.update(idx[:-1])
        stats["replaced"] += 1
        stats["ecr_removed"] += len(twos) - sum(1 for g in new if len(g.qubits) == 2)
    out = []
    for i, g in enumerate(gates):
        if i in drop:
            continue
        out.extend(replace.get(i, [g]))
    return circuit.copy_with_gates(out), stats


def make_native(circuit, native_pairs):
    """Re-orient two-qubit gates that run against the device's native direction.

    Each gate on (a, b) with (b, a) native is replaced by an exact
    decomposition into one native ECR(b, a) plus single-qubit ZSX gates (the
    gate is locally equivalent to an ECR).  Returns (circuit, n_flipped).
    """
    from qiskit.circuit.library import ECRGate
    from qiskit.synthesis import TwoQubitBasisDecomposer
    decomposer = TwoQubitBasisDecomposer(ECRGate(), euler_basis="ZSX")
    native_pairs = set(native_pairs)
    out, flipped = [], 0
    for g in circuit.gates:
        if not (g.kind == "gate" and len(g.qubits) == 2) or g.qubits in native_pairs:
            out.append(g)
            continue
        a, b = g.qubits
        if (b, a) not in native_pairs:
            out.append(g)                 # not a device edge at all; leave untouched
            continue
        c, t = b, a
        u = _block_unitary(circuit, [g], c, t)
        uq = u.reshape(2, 2, 2, 2).transpose(1, 0, 3, 2).reshape(4, 4)
        qc = decomposer(uq, approximate=False)
        qmap = {0: c, 1: t}
        new = []
        for inst in qc.data:
            qs = [qmap[qc.find_bit(q).index] for q in inst.qubits]
            name = inst.operation.name
            new.append(Gate("ecr", qs) if name == "ecr" else
                       Gate(name, qs, [float(p) for p in inst.operation.params]))
        if any(len(x.qubits) == 2 and x.qubits != (c, t) for x in new):
            raise AssertionError("re-orientation produced a non-native ECR")
        if not _equal_up_to_phase(_block_unitary(circuit, new, c, t), u):
            raise AssertionError("re-orientation produced a wrong unitary")
        out.extend(new)
        flipped += 1
    return circuit.copy_with_gates(out), flipped


def full_rewrite(circuit, rounds=3, objective="depth", regroup=False, directed=True):
    """Block resynthesis + single-qubit rewrite, iterated to a fixed point.

    regroup=True first applies the commutation-aware block formation of
    regroup_both_ways in every round."""
    from .resynth import rewrite_single_qubit
    cur = circuit
    log = []
    for _ in range(rounds):
        before = (sum(1 for g in cur.gates if len(g.qubits) == 2), cur.size())
        if regroup:
            cur, _ = regroup_both_ways(cur)
        cur, bs = resynthesize_blocks(cur, objective=objective, directed=directed)
        cur, rs = rewrite_single_qubit(cur)
        log.append({"blocks": bs, "single_qubit": rs})
        after = (sum(1 for g in cur.gates if len(g.qubits) == 2), cur.size())
        if after >= before:
            break
    return cur, {"rounds": log, "gates_before": circuit.size(), "gates_after": cur.size()}
