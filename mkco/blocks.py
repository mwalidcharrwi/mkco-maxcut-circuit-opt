"""Two-qubit block resynthesis (optional rewrite step, needs Qiskit).

A *block* is a maximal stretch of gates that act only on one qubit pair
{a, b} and are contiguous on both wires (no other gate touches a or b in
between).  Each block is replaced by a single 4x4 unitary that is
re-synthesised by the KAK / Weyl decomposition into at most three native
ECRs plus single-qubit ZSX gates.  We call Qiskit's TwoQubitBasisDecomposer
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


def resynthesize_blocks(circuit, min_two_qubit=1, objective="depth"):
    """One pass over all blocks.  Returns (circuit, stats)."""
    try:
        from qiskit.circuit.library import ECRGate
        from qiskit.synthesis import TwoQubitBasisDecomposer
    except ImportError as e:            # optional dependency
        raise ImportError("two-qubit block resynthesis needs qiskit") from e
    names = {g.name for g in circuit.gates if len(g.qubits) == 2}
    if not names <= {"ecr"}:
        # only ECR-native circuits are handled (the IBM benchmarks); others pass through
        return circuit, {"blocks": 0, "replaced": 0, "skipped_basis": sorted(names)}
    decomposer = TwoQubitBasisDecomposer(ECRGate(), euler_basis="ZSX")
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
        if len(dirs) != 1:
            continue                    # mixed ECR directions: leave as is
        c, t = next(iter(dirs))
        u = _block_unitary(circuit, members, c, t)            # basis |c t>, c most significant
        # Qiskit is little-endian; put c on Qiskit qubit 0 so that ecr(0, 1) = ecr(c, t)
        uq = u.reshape(2, 2, 2, 2).transpose(1, 0, 3, 2).reshape(4, 4)
        qc = decomposer(uq)
        qmap = {0: c, 1: t}
        new, ok = [], True
        for inst in qc.data:
            qs = [qmap[qc.find_bit(q).index] for q in inst.qubits]
            name = inst.operation.name
            if name == "ecr":
                if tuple(qs) != (c, t):
                    ok = False
                    break
                new.append(Gate("ecr", qs))
            elif name in ("rz", "sx", "x"):
                new.append(Gate(name, qs, [float(p) for p in inst.operation.params]))
            else:
                ok = False
                break
        if not ok or not _better(new, members, objective):
            continue
        if not _equal_up_to_phase(_block_unitary(circuit, new, c, t), u):
            raise AssertionError("block resynthesis produced a wrong unitary")
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
        qc = decomposer(uq)
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


def full_rewrite(circuit, rounds=3, objective="depth"):
    """Block resynthesis + single-qubit rewrite, iterated to a fixed point."""
    from .resynth import rewrite_single_qubit
    cur = circuit
    log = []
    for _ in range(rounds):
        before = (sum(1 for g in cur.gates if len(g.qubits) == 2), cur.size())
        cur, bs = resynthesize_blocks(cur, objective=objective)
        cur, rs = rewrite_single_qubit(cur)
        log.append({"blocks": bs, "single_qubit": rs})
        after = (sum(1 for g in cur.gates if len(g.qubits) == 2), cur.size())
        if after >= before:
            break
    return cur, {"rounds": log, "gates_before": circuit.size(), "gates_after": cur.size()}
