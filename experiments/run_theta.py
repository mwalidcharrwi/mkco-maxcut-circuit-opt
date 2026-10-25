"""Lovasz-theta certificates for commuting instances that the clique/Jackson
bound left uncertified (E1 and E3).  Writes results/structured/theta.json."""
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
    out = []
    jobs = []
    for r in json.load(open(os.path.join(D, "e1.json"))):
        if r["mkco"] > r["lb"]:
            jobs.append(("e1", r, gen.random_commuting_mcz(r["m"], r["n"], seed=r["seed"])))
    for r in json.load(open(os.path.join(D, "e3.json"))):
        if r["mkco"] > r["lb"]:
            jobs.append(("e3", r, gen.random_commuting_ccz(10, r["gates"], seed=r["seed"])))
    jobs.sort(key=lambda j: j[2].size())
    for exp, r, c in jobs:
        g = conflict_graph(DepModel(c))
        t = time.time()
        bound, val = theta_bound(g)
        row = {"experiment": exp, "m": r.get("m", 10), "n": r.get("n", r.get("gates")),
               "seed": r["seed"], "clique_jackson_lb": r["lb"], "theta": val,
               "theta_lb": bound, "lb": max(bound, r["lb"]), "dsatur": r["dsatur"],
               "jk": r["jk"], "mkco": r["mkco"], "time_s": time.time() - t}
        row["mkco_certified_by_theta"] = row["mkco"] == row["lb"]
        out.append(row)
        print(row, flush=True)
        json.dump(out, open(os.path.join(D, "theta.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
