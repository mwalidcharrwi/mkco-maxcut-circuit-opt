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
  - **Rewrite mode** (ZSX single-qubit resynthesis + Max-k-Cut reordering):
    shallower than Qiskit O3 on 8/9 (heisenberg_32: 3,011 vs 3,538). As a
    post-pass after Qiskit O3 it gives the best result on the other one.
- **The paper's own settings:**
  - F₂ⁿ multiplier: optimal at all 34 sizes (DSatur 24/34).
  - Random multi-controlled-Z circuits: 41/60 certified optimal (DSatur 36/60).
  - Random CCZ circuits: 49/50 (DSatur 20/50).
  - QAOA-style RZZ layers: 14/18 reach the degree bound (DSatur 0/18).

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
  merge.py        run-based same-axis rotation merging
  fanout.py       ancilla fan-out depth/qubit trade-offs (capacitated Max-k-Cut)
  bounds.py       certified lower bounds
  coloring.py     Lee et al. baseline (DSatur / backtracking / block-wise extension)
  jk.py           Jain & Kumar baseline (mixed-graph independent sets + beam search)
  verify.py       independent commutation audit, state-vector check
  exact.py        optional CP-SAT reference solver (needs ortools)
benchmarks/ibm127/  the 9 IBM-127-transpiled input circuits
experiments/      run_ibm127.py, fill_qiskit.py, add_merge.py, add_rewrite.py,
                  summarize_ibm127.py, run_structured.py, summarize_structured.py, plots.py
tests/            test_core.py, test_gates_vs_qiskit.py
docs/             REPORT.md (full report), THEORY.md, RELATED_WORK.md, figures/
results/          JSON, tables and logs (optimized QASM outputs are regenerated, not committed)
```

## Install and use
```bash
pip install -e .              # core: numpy, scipy, networkx
pip install -e ".[dev]"       # + qiskit, ortools, matplotlib, pytest
```

```bash
python -m mkco opt in.qasm out.qasm --metric depth --time 30   # reorder, certify, verify
python -m mkco opt in.qasm out.qasm --metric 2q                 # two-qubit depth
python -m mkco opt in.qasm out.qasm --rewrite                   # 1q resynthesis + reorder
python -m mkco opt in.qasm out.qasm --xt                        # crosstalk-aware layering
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
python experiments/fill_qiskit.py && python experiments/add_merge.py && python experiments/add_rewrite.py
python experiments/summarize_ibm127.py
python experiments/run_structured.py && python experiments/summarize_structured.py
python experiments/plots.py && python docs/build_report.py
pytest -q
```
