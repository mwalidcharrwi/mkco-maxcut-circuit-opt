"""Szegedy theta-plus certificates for the instances that are still open after
the clique/Jackson and theta bounds (E1 and E3, including the 200-gate ones the
theta run skipped).  Writes results/structured/theta_plus.json."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mkco import generators as gen                 # noqa: E402
from mkco.coloring import conflict_graph           # noqa: E402
from mkco.depmodel import DepModel                 # noqa: E402
from mkco.sdp_bounds import theta_bound            # noqa: E402

D = "results/structured"


def main():
    closed = {(r["experiment"], r["m"], r["n"], r["seed"])
              for r in json.load(open(os.path.join(D, "theta.json")))
              if r["mkco_certified_by_theta"]}
    jobs = []
    for exp, fn in (("e1", "e1.json"), ("e3", "e3.json")):
        for r in json.load(open(os.path.join(D, fn))):
            m, n = r.get("m", 10), r.get("n", r.get("gates"))
            if r["mkco"] <= r["lb"] or (exp, m, n, r["seed"]) in closed:
                continue
            c = (gen.random_commuting_mcz(m, n, seed=r["seed"]) if exp == "e1"
                 else gen.random_commuting_ccz(10, n, seed=r["seed"]))
            jobs.append((exp, m, n, r, c))
    jobs.sort(key=lambda j: j[4].size())
    theta = {(r["experiment"], r["m"], r["n"], r["seed"]): r
             for r in json.load(open(os.path.join(D, "theta.json")))}
    out = []
    for exp, m, n, r, c in jobs:
        g = conflict_graph(DepModel(c))
        t = time.time()
        bound, val, raw = theta_bound(g, plus=True, return_raw=True)
        prev = theta.get((exp, m, n, r["seed"]))
        row = {"experiment": exp, "m": m, "n": n, "seed": r["seed"],
               "clique_jackson_lb": r["lb"], "theta": prev["theta"] if prev else None,
               "theta_plus": val, "theta_plus_solver": raw, "theta_plus_lb": bound,
               "lb": max(bound, r["lb"]), "dsatur": r["dsatur"], "jk": r["jk"],
               "mkco": r["mkco"], "time_s": time.time() - t}
        row["mkco_certified"] = row["mkco"] == row["lb"]
        out.append(row)
        print(row, flush=True)
        json.dump(out, open(os.path.join(D, "theta_plus.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
