# MKCO — Quantum Circuit Optimization by Max-k-Cut

MKCO reorders (and optionally rewrites) the gates of a quantum circuit to
minimize its depth, its two-qubit depth, or crosstalk-prone parallelism.
Reordering uses only legal commutations, and every result comes with a
**certified lower bound**. MKCO starts from Lee, Jeong & Kim's result
(*Quantum* 2026) that layering a *commuting* circuit is graph colouring, and
generalizes it:

* **Any circuit, not only commuting ones.** Depth minimization equals colouring
  a mixed graph (precedence arcs + conflict edges) built from per-qubit
  commutation axes ([docs/THEORY.md](docs/THEORY.md), Theorem 1).
* **Max-k-Cut core.** A depth-k circuit exists iff a precedence-constrained
  weighted Max-k-Cut cuts every hard edge (Theorem 2). The same objective takes
  depth budgets, soft edges (crosstalk) and capacities (ancilla fan-out).
* **Certified and verified.** A Jackson-type lower bound (Theorem 7) proves when
  an output is optimal. Every output is checked by an independent commutation
  audit, plus state-vector simulation when it has ≤ 20 active qubits.
* **Quantum-ready.** Hierarchical Max-Cut turns layering into
  log₂(depth) Ising problems with n spins each, solvable by
  Goemans–Williamson SDP, annealing or QAOA (Theorem 4, Proposition 6).

## Headline results
Full tables in [docs/REPORT.md](docs/REPORT.md) and
[results/ibm127/tables.md](results/ibm127/tables.md).

- **9 IBM-127-transpiled benchmarks (rz/sx/x/ecr, up to 358k gates).**
  - **Reordering only:** MKCO is certified optimal on 9/9. Lee et al. gains
    nothing on any circuit; Jain & Kumar ties on depth but cannot certify it.
  - **Crosstalk mode:** 2–26% fewer neighbouring-coupler ECR pairs at the
    optimal two-qubit depth.
  - **Gate-rewriting modes vs Qiskit O3** (Qiskit run on a device Target with
    native ECR directions; every output is executable):
    - MKCO-full is shallower on **9/9** circuits (−3.4% to −25.5%;
      heisenberg_32: 3,011 vs 4,039, hubbard_18: 72,992 vs 84,761).
    - Selected by estimated execution time, MKCO-full is also faster than
      Qiskit on 9/9 (see the hardware-time table in the report).
  - **Depth budgets:** with 20% two-qubit-depth slack, the weighted Max-k-Cut
    removes 39–65% of crosstalk-prone pairs (Pareto fronts in the report).
- **Second benchmark set** (heisenberg_8, qpe_8, tfim_8, tfim_7_40, with measurements; report
  Section 5.1):
  - **Certified optimal depth:** on 4/4 circuits, for both total depth and two-qubit depth.
  - **vs Qiskit O3:** MKCO-full is 0.5–3.0% shallower; Qiskit removes at most one layer.
  - **Crosstalk:** a 20% two-qubit-depth budget removes 34–38% of crosstalk-prone pairs.
  - **Noisy simulation:** on qpe_8, every MKCO order beats the input and Qiskit O3 (+3–4%),
    as the noise model predicted.
- **Extensions** (report Section 7):
  - **T-depth with free Cliffords:** on top of PyZX, 10–69% lower T-depth
    (mean 41%) on 17 Clifford+T circuits, all certified optimal; Toffoli-depth
    of GF(2ⁿ) multipliers −53% to −64%.
  - **Commutation-aware routing on IBM's 127-qubit heavy-hex:** on QAOA,
    3.8–21.9% fewer CNOTs than Qiskit O3 and up to 55% less depth. Each output
    is proven correct by an exact `unroute` check. QFT remains Qiskit's case.
  - **Noise study with ibm_brisbane calibration data:** a depth-optimal
    reordering can lose fidelity, because qubits may idle in superposition. A
    state-aware success estimate predicts this (97% pairwise agreement with
    density-matrix simulation vs 66% for the usual ESP) and picks the output.
    The picked output beats Qiskit O3 on all 9 benchmarks under the model.
  - **Commutation-aware block formation** gives KAK larger blocks: fewer CNOTs
    on 17 of 19 logical circuits.
- **The paper's own settings:**
  - F₂ⁿ multiplier: optimal at all 34 sizes (DSatur 24/34).
  - Random multi-controlled-Z circuits: 48/60 certified optimal (DSatur 42/60), using the
    clique/Jackson and Lovász-θ / θ⁺ bounds.
  - Random CCZ circuits: 49/50 (DSatur 20/50).
  - QAOA-style RZZ layers: 14/18 reach the degree bound (DSatur 0/18).
  - Lovász-θ / θ⁺ SDP certificates are solver-independent (repaired feasible points).

## Real hardware
`experiments/run_ibm_hardware.py` submits chosen outputs to an IBM Quantum
backend and scores the counts by Hellinger fidelity against the ideal output.
It needs your own account, saved beforehand with
`QiskitRuntimeService.save_account(...)`; the script never handles tokens.
`submit --fake [--noise-scale 0.1]` runs the same pipeline on a noisy
simulated backend (Aer + the ibm_brisbane calibration snapshot). The results
are in report Table 12: the state-aware estimate ordered every resolved pair
of methods correctly (13/13), while the usual ESP got 4/13.

## Layout
```
mkco/
  gates.py        gate library, unitaries, per-qubit commutation axes
  circuit.py      IR, depth metrics (incl. weighted / barrier-synchronised), QASM export
  qasm.py         OpenQASM 2.0 parser (custom gates kept as composites)
  depmodel.py     runs, mixed graph, heads/tails (O(Σ arity) memory)
  schedule.py     list scheduling, serial SGS, emission, structural verification
  maxkcut.py      precedence-constrained weighted Max-k-Cut engine (tabu, k-descent)
  lns.py          window-compression LNS for general circuits (+ forward/backward justification)
  hmc.py          hierarchical Max-Cut: Ising splits, SA / Burer–Monteiro-GW / QAOA / exact
  crosstalk.py    crosstalk-aware layering (soft edges) with anchor barriers
  resynth.py      rewrite mode: single-qubit ZSX resynthesis + rotation merging
  blocks.py       two-qubit block (KAK) resynthesis (native direction), commutation-aware
                  block formation (regroup), ECR re-orientation
  merge.py        run-based same-axis rotation merging
  fanout.py       ancilla fan-out depth/qubit trade-offs (capacitated Max-k-Cut)
  bounds.py       certified lower bounds (run-serialised Jackson)
  sdp_bounds.py   Lovász-theta / Szegedy theta-plus SDP bounds, solver-independent (needs cvxpy)
  nonclifford.py  T-depth / Toffoli-depth with free Cliffords (reduced mixed graph, surrogate circuit)
  route.py        commutation-aware SABRE-style routing + exact `unroute` check
  noise.py        calibration-based ESP, state-aware ESP, density-matrix noisy simulation
  coloring.py     Lee et al. baseline (DSatur / backtracking / block-wise extension)
  jk.py           Jain & Kumar baseline (mixed-graph independent sets + beam search)
  verify.py       independent commutation audit, state-vector check
  exact.py        optional CP-SAT reference solver (needs ortools)
benchmarks/ibm127/  the 9 IBM-127-transpiled input circuits
benchmarks/devices/  IBM Eagle 127-qubit coupling map (heavy-hex)
experiments/      run_ibm127.py, run_qiskit.py, add_merge.py, add_rewrite.py, add_full.py,
                  add_full_duration.py, run_blocks.py, run_pareto.py, run_theta.py,
                  run_theta_plus.py, run_structured.py, run_tdepth.py, run_routing.py,
                  run_regroup.py, run_noise.py, run_ibm_hardware.py, summarize_*.py, plots.py
tests/            test_core.py, test_gates_vs_qiskit.py, test_extensions.py
docs/             REPORT.md (full report), THEORY.md, RELATED_WORK.md, figures/
results/          JSON, tables and logs (optimized QASM outputs are regenerated, not committed)
```

## Install and use
```bash
pip install -e .              # core: numpy, scipy, networkx
pip install -e ".[dev]"       # + qiskit, ortools, cvxpy, matplotlib, pytest
pip install -e ".[noise,zx]"  # + qiskit-aer, qiskit-ibm-runtime (noise study, IBM runs), pyzx
```

```bash
python -m mkco opt in.qasm out.qasm --metric depth --time 30   # reorder, certify, verify
python -m mkco opt in.qasm out.qasm --metric 2q                 # two-qubit depth
python -m mkco opt in.qasm out.qasm --rewrite                   # 1q resynthesis + reorder
python -m mkco opt in.qasm out.qasm --full                      # + 2q KAK blocks (needs qiskit)
python -m mkco opt in.qasm out.qasm --xt                        # crosstalk-aware layering
python -m mkco opt in.qasm out.qasm --alap                      # same depth, gates as late as possible
python -m mkco opt in.qasm out.qasm --nc t                      # T-depth with free Cliffords (or toffoli)
python -m mkco route logical.qasm routed.qasm                   # route onto IBM Eagle heavy-hex
```

```python
from mkco import load_qasm, optimize
c = load_qasm("in.qasm")
opt, report = optimize(c, metric="depth", time_limit=30)
print(report["before"], "->", report["after"], "certified:", report["certified_optimal"])
```

## Reproduce
```bash
python experiments/run_ibm127.py benchmarks/ibm127
python experiments/run_qiskit.py && python experiments/add_merge.py && python experiments/add_rewrite.py
python experiments/add_full.py && python experiments/add_full_duration.py
python experiments/run_blocks.py && python experiments/run_pareto.py
python experiments/summarize_ibm127.py
python experiments/run_structured.py && python experiments/run_theta.py && python experiments/summarize_structured.py
python experiments/run_theta_plus.py && python experiments/run_tdepth.py
python experiments/run_routing.py && python experiments/run_regroup.py && python experiments/run_noise.py
python experiments/summarize_ibm127.py && python experiments/summarize_structured.py
python experiments/run_set2.py                       # second benchmark set -> results/ibm127_set2
python experiments/plots.py && python docs/build_report.py
pytest -q
```

## License
MIT (see [LICENSE](LICENSE)).
