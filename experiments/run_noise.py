"""E10: hardware-oriented validation with the ibm_brisbane calibration snapshot.

The 9 IBM-127 benchmarks are native to ibm_brisbane (all 78 ECR directions
match qiskit-ibm-runtime's FakeBrisbane), so every method's output can be
scored with that device's calibrated gate errors, gate durations, T1, T2 and
readout errors (mkco.noise).

Scores
  esp         estimated success probability with ALAP idling (state-blind)
  esp_xt      esp with an extra ECR error for every pair of ECRs that overlap
              in time on neighbouring couplers (crosstalk sensitivity)
  sesp        state-aware ESP: idle gaps weighted by the idling qubit's ideal
              state (<= 22 active qubits)
  sim_*       exact density-matrix simulation of the scheduled circuit
              (<= 8 active qubits): state fidelity and Hellinger fidelity of the
              measured distribution, at calibrated noise (scale 1) and at 10x
              lower noise (scale 0.1)

Methods: the stored outputs of run_ibm127.py / add_*.py, plus
  mkco_alap, mkco_full_alap   the same layerings placed as late as possible
  mkco_noise                  the candidate with the best sesp (esp when the
                              circuit is too large) among original, mkco,
                              mkco_alap, mkco_full, mkco_full_alap, mkco_full_dur

Real-hardware runs need an IBM Quantum account: experiments/run_ibm_hardware.py.
Usage: python experiments/run_noise.py [results_dir]   (default results/ibm127)
Each circuit is scored on the calibration snapshot on which all its ECRs are
native (ibm_brisbane for set 1; ibm_brisbane or ibm_cusco for set 2).
Writes <results_dir>/noise.json.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mkco.crosstalk import adjacent_couplers                 # noqa: E402
from mkco.noise import (Calibration, esp, fidelities,       # noqa: E402
                        matching_backend, noisy_density_matrix, state_aware_esp)
from mkco.optimize import optimize                           # noqa: E402
from mkco.qasm import load_qasm                              # noqa: E402

STORED = ["original", "lee2026", "jk2026", "mkco", "mkco_xt", "mkco_rewrite", "mkco_full",
          "mkco_full_dur"]
CANDIDATES = ["original", "mkco", "mkco_alap", "mkco_full", "mkco_full_alap", "mkco_full_dur"]
SIM_MAX_QUBITS = 8


def alap(c, tl=30.0):
    rev = c.copy_with_gates(list(reversed(c.gates)))
    out, _ = optimize(rev, metric="depth", time_limit=tl)
    return c.copy_with_gates(list(reversed(out.gates)))


def score(c, cal, adj, simulate):
    e1 = esp(c, cal)
    rec = {"esp": e1["esp"], "esp_xt": esp(c, cal, xt_adjacent=adj)["esp"],
           "esp_scale0.1": esp(c, cal, scale=0.1)["esp"], "depth": c.depth(),
           "ecr": sum(1 for g in c.gates if len(g.qubits) == 2),
           "duration_us": e1["duration_us"], "idle_us": e1["idle_us"],
           "broken_gates": e1["broken_gates"]}
    for scale in (1.0, 0.1):
        s = state_aware_esp(c, cal, scale)
        rec[f"sesp_scale{scale}"] = None if s is None else s["sesp"]
    if simulate:
        for scale in (1.0, 0.1):
            rho, psi, act = noisy_density_matrix(c, cal, scale)
            rec[f"sim_scale{scale}"] = fidelities(rho, psi, act, cal, scale)
    return rec


def device(circuit):
    """Calibration snapshot on which the circuit is native (ibm_brisbane for set 1)."""
    from qiskit_ibm_runtime.fake_provider import FakeBrisbane
    be = matching_backend(circuit) or FakeBrisbane()
    cal = Calibration(be)
    edges = {tuple(sorted(e)) for e in be.coupling_map.get_edges()}
    return cal, {frozenset(p) for p in adjacent_couplers(edges)}


def main(rdir="results/ibm127"):
    path = os.path.join(rdir, "noise.json")
    names = sorted({f.split("__")[0] for f in os.listdir(rdir) if f.endswith("__original.qasm")},
                   key=lambda n: os.path.getsize(os.path.join(rdir, f"{n}__original.qasm")))
    out = json.load(open(path)) if os.path.exists(path) else {"circuits": {}}
    for name in names:
        if name in out["circuits"]:
            continue
        circs = {m: load_qasm(os.path.join(rdir, f"{name}__{m}.qasm")) for m in STORED
                 if os.path.exists(os.path.join(rdir, f"{name}__{m}.qasm"))}
        cal, adj = device(circs["original"])
        circs["mkco_alap"] = alap(circs["original"])
        circs["mkco_full_alap"] = alap(circs["mkco_full"])
        active = {q for g in circs["original"].gates for q in g.qubits}
        simulate = len(active) <= SIM_MAX_QUBITS
        row = {}
        for m, c in circs.items():
            t = time.time()
            row[m] = score(c, cal, adj, simulate)
            row[m]["time_s"] = round(time.time() - t, 1)
            print(name, m, {k: (round(v, 5) if isinstance(v, float) else v) for k, v in row[m].items()
                            if k in ("esp", "sesp_scale1.0", "sesp_scale0.1", "duration_us")},
                  {k: round(v["state_fidelity"], 5) for k, v in row[m].items() if k.startswith("sim_")},
                  flush=True)
        key = "sesp_scale1.0" if row["original"]["sesp_scale1.0"] is not None else "esp"
        pick = max(CANDIDATES, key=lambda m: (row[m][key], m == "original"))
        row["mkco_noise"] = dict(row[pick], selected=pick, selected_by=key)
        out["circuits"][name] = {"active_qubits": len(active), "simulated": simulate,
                                 "backend": cal.name, "median_ecr_error": cal.median_2q,
                                 "methods": row}
        out["backend"] = ", ".join(sorted({c.get("backend", out.get("backend", ""))
                                           for c in out["circuits"].values()}))
        json.dump(out, open(path, "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results/ibm127")
