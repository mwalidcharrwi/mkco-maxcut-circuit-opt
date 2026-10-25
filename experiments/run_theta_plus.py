"""Szegedy theta-plus certificates for the instances that are still open after
the clique/Jackson and theta bounds (E1 and E3, including the 200-gate ones the
theta run skipped).  Writes results/structured/theta_plus.json.

Usage: python experiments/run_theta_plus.py [--solver CLARABEL|SCS] [--min-gates N]
       [--workers K]

Clarabel (interior point) is used up to 150 gates.  At 200 gates it needs
about an hour and 6 GB per instance, so those are solved with SCS (first
order, less accurate).  Either way the bound comes from the repaired, exactly
feasible point, so it is valid whatever the solver's accuracy; a less
accurate solver can only make it weaker.  Already computed instances are kept.
"""
import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mkco import generators as gen                 # noqa: E402
from mkco.coloring import conflict_graph           # noqa: E402
from mkco.depmodel import DepModel                 # noqa: E402
from mkco.sdp_bounds import theta_bound            # noqa: E402

D = "results/structured"
OUT = os.path.join(D, "theta_plus.json")


def _key(r):
    return (r["experiment"], r["m"], r["n"], r["seed"])


def solve(job):
    exp, m, n, r, solver = job
    c = (gen.random_commuting_mcz(m, n, seed=r["seed"]) if exp == "e1"
         else gen.random_commuting_ccz(10, n, seed=r["seed"]))
    g = conflict_graph(DepModel(c))
    t = time.time()
    if solver == "SCS":
        import cvxpy as cp
        bound, val, raw = theta_bound(g, solver=cp.SCS, plus=True, return_raw=True,
                                      eps=1e-7, max_iters=200000)
    else:
        bound, val, raw = theta_bound(g, plus=True, return_raw=True)
    return {"experiment": exp, "m": m, "n": n, "seed": r["seed"],
            "clique_jackson_lb": r["lb"], "theta_plus": val, "theta_plus_solver": raw,
            "theta_plus_lb": bound, "lb": max(bound, r["lb"]), "dsatur": r["dsatur"], "jk": r["jk"],
            "mkco": r["mkco"], "solver": solver, "time_s": time.time() - t,
            "mkco_certified": r["mkco"] == max(bound, r["lb"])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solver", default="CLARABEL", choices=["CLARABEL", "SCS"])
    ap.add_argument("--min-gates", type=int, default=0)
    ap.add_argument("--workers", type=int, default=1)
    a = ap.parse_args()
    theta = {_key(r): r for r in json.load(open(os.path.join(D, "theta.json")))}
    closed = {k for k, r in theta.items() if r["mkco_certified_by_theta"]}
    done = {_key(r): r for r in json.load(open(OUT))} if os.path.exists(OUT) else {}
    jobs = []
    for exp, fn in (("e1", "e1.json"), ("e3", "e3.json")):
        for r in json.load(open(os.path.join(D, fn))):
            m, n = r.get("m", 10), r.get("n", r.get("gates"))
            k = (exp, m, n, r["seed"])
            if r["mkco"] <= r["lb"] or k in closed or k in done or n < a.min_gates:
                continue
            jobs.append((exp, m, n, r, a.solver))
    jobs.sort(key=lambda j: j[2])
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for row in ex.map(solve, jobs):
            prev = theta.get(_key(row))
            row["theta"] = prev["theta"] if prev else None
            done[_key(row)] = row
            print(row, flush=True)
            json.dump(sorted(done.values(), key=lambda r: (r["n"], r["experiment"], r["m"], r["seed"])),
                      open(OUT, "w"), indent=1)


if __name__ == "__main__":
    main()
