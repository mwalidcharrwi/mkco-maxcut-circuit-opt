"""Top-level MKCO pipeline: Max-k-Cut circuit optimisation."""
from __future__ import annotations

import time

from .bounds import clique_bound, jackson_wire_bound
from .circuit import metric_weight
from .coloring import (coloring_to_slots, conflict_graph, dsatur, exact_coloring,
                       split_barriers)
from .depmodel import DepModel
from .maxkcut import compact, kdescent, used_layers
from .schedule import asap_slots_of_order, emit_order, list_schedule, slots_valid, verify_order

_OTHER = {"depth": "2q", "2q": "depth"}


class SegmentResult:
    def __init__(self, gates, layers, lb, source, stats):
        self.gates = gates
        self.layers = layers
        self.lb = lb
        self.source = source
        self.stats = stats


def _secondary(circuit, gates, model, slots, metric):
    """Value of the other depth metric for a candidate layering (tie-breaker)."""
    order = emit_order(model, slots)
    return circuit.copy_with_gates([gates[i] for i in order]).depth(_OTHER[metric])


def optimize_segment(circuit, gates, metric, time_limit, seed=0, use_hmc=False,
                     hmc_backend="sa", log=None, exact_small=False):
    sub = circuit.copy_with_gates(gates)
    model = DepModel(sub, metric)
    nu = len(model.unit)
    if nu == 0:
        return SegmentResult(gates, 0, 0, "empty", {})
    t_start = time.time()
    other_w = metric_weight(_OTHER[metric])
    candidates = {
        "original": asap_slots_of_order(model),
        "list_tail": list_schedule(model, priority="tail"),
        "list_load": list_schedule(model, priority="load"),
        "list_lex": list_schedule(model, priority="tail",
                                  secondary=model.weighted_tails(other_w)),
    }
    commuting = model.is_commuting()
    graph = None
    if commuting and nu <= 3000:
        graph = conflict_graph(model)
        candidates["dsatur"] = coloring_to_slots(model, dsatur(graph))
    lb = jackson_wire_bound(model)
    if graph is not None and nu <= 400:
        lb = max(lb, clique_bound(graph))
    stats = {"n_unit": nu, "commuting": commuting, "lb": lb,
             "critical_path": model.critical_path}
    for name in candidates:
        candidates[name] = compact(candidates[name])
        stats[f"layers_{name}"] = used_layers(candidates[name])

    def key(name, s):
        return (used_layers(s), _secondary(sub, gates, model, s, metric), name != "original")

    best_name = min(candidates, key=lambda n: key(n, candidates[n]))
    best = candidates[best_name]
    if use_hmc and used_layers(best) > lb:
        from .hmc import hmc_schedule
        hs, hstats = hmc_schedule(model, lb, used_layers(best) - 1, backend=hmc_backend,
                                  time_limit=0.4 * time_limit, seed=seed)
        stats["hmc"] = hstats
        if hs is not None and slots_valid(model, hs) and used_layers(hs) < used_layers(best):
            best, best_name = compact(hs), "hmc"
    remaining = time_limit - (time.time() - t_start)
    if used_layers(best) > lb and remaining > 0:
        if commuting:   # Max-k-Cut tabu k-descent
            slots, kstats = kdescent(model, best, lb, time_limit=remaining, seed=seed, log=log)
            stats["kdescent"] = kstats
            name = "maxkcut"
        else:           # window-compression LNS, each window a Max-k-Cut sub-problem
            from .lns import lns
            slots, kstats = lns(model, best, lb, time_limit=remaining, seed=seed, log=log)
            stats["lns"] = kstats
            name = "maxkcut_lns"
        if used_layers(slots) < used_layers(best):
            best, best_name = slots, name
    if exact_small and commuting and graph is not None and nu <= 80 and used_layers(best) > lb:
        colr, proven = exact_coloring(graph, time_limit=time_limit)
        s = compact(coloring_to_slots(model, colr))
        stats["exact_proven"] = proven
        if used_layers(s) < used_layers(best):
            best, best_name = s, "exact"
    if not slots_valid(model, best):
        raise RuntimeError("internal error: invalid layering")
    order = emit_order(model, best)
    ok, msg = verify_order(model, order)
    if not ok:
        raise RuntimeError(f"structural verification failed: {msg}")
    stats["source"] = best_name
    stats["layers"] = used_layers(best)
    stats["time"] = time.time() - t_start
    return SegmentResult([gates[i] for i in order], used_layers(best), lb, best_name, stats)


def optimize(circuit, metric="depth", time_limit=10.0, seed=0, use_hmc=False,
             hmc_backend="sa", log=None, exact_small=False, alap=False):
    """Reorder `circuit` (commutation-preserving) to minimise depth or 2q-depth.

    Returns (optimized_circuit, report).  The output is never worse than the
    input in the chosen metric (ties broken by the other depth metric).  When
    the circuit has no barriers the report's `lower_bound` is a certified
    bound on every commutation-equivalent reordering, so `after ==
    lower_bound` proves optimality.

    alap=True layers the reversed circuit and reverses the result, so gates are
    placed as late as possible.  The depth and the bound are the same; on
    hardware this keeps qubits in |0> longer before their first gates, which
    matters under state-dependent idle noise (mkco.noise).
    """
    if alap:
        rev = circuit.copy_with_gates(list(reversed(circuit.gates)))
        out, rep = optimize(rev, metric, time_limit, seed, use_hmc, hmc_backend, log, exact_small)
        rep["alap"] = True
        return out.copy_with_gates(list(reversed(out.gates))), rep
    t0 = time.time()
    segs = split_barriers(circuit)
    total = sum(len(p) for k, p in segs if k == "gates") or 1
    out, seg_reports = [], []
    for kind, payload in segs:
        if kind == "barrier":
            out.append(payload)
            continue
        share = max(0.5, time_limit * len(payload) / total)
        res = optimize_segment(circuit, payload, metric, share, seed=seed, use_hmc=use_hmc,
                               hmc_backend=hmc_backend, log=log, exact_small=exact_small)
        out.extend(res.gates)
        seg_reports.append(res.stats)
    opt = circuit.copy_with_gates(out)
    mname = "depth" if metric == "depth" else "2q"
    before = (circuit.depth(mname), circuit.depth(_OTHER[mname]))
    after = (opt.depth(mname), opt.depth(_OTHER[mname]))
    if after > before:
        opt, after = circuit.copy_with_gates(list(circuit.gates)), before
    single = sum(1 for k, _ in segs if k == "gates") == 1 and not any(
        k == "barrier" for k, _ in segs)
    lbs = [s.get("lb", 0) for s in seg_reports]
    lower = max(lbs) if lbs else 0
    report = {
        "metric": metric,
        "before": before[0],
        "after": after[0],
        "before_other": before[1],
        "after_other": after[1],
        "lower_bound": lower,
        "certified_optimal": bool(single and after[0] == lower),
        "segments": seg_reports,
        "time": time.time() - t0,
    }
    return opt, report
