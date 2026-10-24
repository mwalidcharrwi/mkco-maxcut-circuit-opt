"""Exact reference solver (optional, needs `ortools`): CP-SAT model of the
mixed-graph layering problem.  Used only to measure optimality gaps of the
heuristics on small instances; MKCO itself does not depend on it."""
from __future__ import annotations

import numpy as np


def cpsat_schedule(model, ub, lb=0, time_limit=30.0, hint=None, caps=None, workers=8):
    """Minimise the number of layers.  Returns (slots, status, best_bound)."""
    from ortools.sat.python import cp_model

    nu = len(model.unit)
    K = int(ub)
    est = model.head
    tail = model.tail
    m = cp_model.CpModel()
    s = [m.NewIntVar(int(est[i]), int(K - 1 - tail[i]), f"s{i}") for i in range(nu)]
    span = m.NewIntVar(max(lb, model.critical_path), K, "span")
    for i in range(nu):
        m.Add(s[i] + 1 <= span)
    # precedence through run summaries
    rmax, rmin = {}, {}
    for r in model.unit_runs:
        mem = [model.unit_index[g] for g in model.run_unit_members[r]]
        if model.next_unit_run[r] >= 0:
            v = m.NewIntVar(0, K, f"M{r}")
            m.AddMaxEquality(v, [s[i] for i in mem])
            rmax[r] = v
        if model.prev_unit_run[r] >= 0:
            v = m.NewIntVar(0, K, f"m{r}")
            m.AddMinEquality(v, [s[i] for i in mem])
            rmin[r] = v
    for r in model.unit_runs:
        q = model.next_unit_run[r]
        if q >= 0:
            m.Add(rmin[q] >= rmax[r] + 1)
    # conflicts: gates on a wire occupy distinct layers
    by_wire = {}
    for i, g in enumerate(model.unit):
        for w in model.wires[g]:
            by_wire.setdefault(w, []).append(i)
    for w, mem in by_wire.items():
        if len(mem) > 1:
            if caps is None or caps[w] == 1:
                m.AddAllDifferent([s[i] for i in mem])
    if hint is not None:
        for i in range(nu):
            m.AddHint(s[i], int(hint[i]))
    m.Minimize(span)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = workers
    st = solver.Solve(m)
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        slots = np.array([solver.Value(v) for v in s], dtype=np.int64)
        return slots, ("optimal" if st == cp_model.OPTIMAL else "feasible"), int(solver.BestObjectiveBound())
    return None, solver.StatusName(st), int(solver.BestObjectiveBound())
