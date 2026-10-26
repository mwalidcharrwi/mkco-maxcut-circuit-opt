# MKCO — results digest for the paper

This digest is the single source of truth for drafting the paper. Every number
in it is generated from the result files of the repository
(`paper/build_package.py`); the full tables are in `tables/`, the figures in
`figures/`, and the complete report, proofs and related-work notes in
`supplement/`.

**Working title options**
1. *Certified Quantum Circuit Depth Optimization by Precedence-Constrained Max-k-Cut*
2. *Beyond Graph Colouring: Provably Optimal Commutation-Aware Layering of Quantum Circuits via Max-k-Cut*
3. *MKCO: Max-k-Cut Circuit Optimization with Optimality Certificates and Hardware-Aware Objectives*

**Author.** Mohammad Walid Charrwi (affiliation to be filled in).
**Code.** `mkco` Python package, MIT licence, 23 unit tests, every experiment
reproducible from one script each (supplement/REPORT.md §10).

---

## 1. One-paragraph summary

Lee, Jeong and Kim (*Quantum*, 2026) showed that minimising the depth of a
circuit whose gates all commute is graph colouring. Real circuits do not
commute, and colouring gives neither a proof of optimality nor a way to trade
depth against hardware effects. **MKCO** generalises the reduction to
*arbitrary* circuits: per-qubit commutation axes, computed exactly from the gate
unitaries, group the gates of each wire into runs; the runs define a trace
order, and the minimum depth over all equivalent reorderings is exactly the
chromatic number of a **mixed graph** (precedence arcs + conflict edges). We
recast that colouring as a **precedence-constrained weighted Max-k-Cut**,
which (i) admits depth budgets, soft constraints (crosstalk) and capacities
(ancilla fan-out), (ii) decomposes into Ising problems that a QAOA or annealer
can solve with `n⌈log₂k⌉` spins, and (iii) comes with **certified lower bounds**
(a run-serialised Jackson bound, plus Lovász θ / Szegedy θ⁺ SDP bounds made
solver-independent by an exact repair). On the base paper's own benchmarks MKCO
proves optimality far more often than the colouring baselines (e.g. 34/34 vs
24/34 multiplier sizes, 49/50 vs 20/50 random CCZ circuits). On 13 circuits
already transpiled by Qiskit at optimisation level 3 for IBM's 127-qubit
devices, every MKCO result is **certified optimal** for depth and two-qubit
depth, while Lee et al.'s method gains nothing; with gate rewriting MKCO is
0.5–57.8% shallower than the transpiled input. The same machinery extends to
T-depth with free Cliffords (−10% to −69% after PyZX), commutation-aware
routing (up to 21.9% fewer CNOTs than Qiskit's level-3 SABRE on QAOA), and a
state-aware idle-noise model that correctly predicts which reordering is more
faithful on a noisy simulated backend.

## 2. Problem and gap

Depth minimisation by reordering: given a gate sequence, find a
commutation-equivalent sequence of minimum depth (or two-qubit depth, duration,
T-depth, …) and *prove* that nothing shorter exists.

What the base paper leaves open (its own stated limitations, see
supplement/RELATED_WORK.md):
1. **Commuting circuits only.** Non-commuting circuits must be cut into
   commuting blocks that are coloured separately, so no gate can cross a block
   boundary. After transpilation such blocks are short: on all 13 IBM circuits
   the block-wise method gains **nothing**.
2. **No optimality guarantee.** DSatur is a heuristic; how far it is from
   optimal on large instances is stated as open.
3. **Hardware constraints open.** Connectivity, crosstalk, gate sets are
   flagged as "highly nontrivial".
4. **Ancilla parallelisation unspecified** and an explicit `O(n²)` conflict
   graph.

The direct follow-up (Jain & Kumar, NeurIPS 2026 WiML poster) handles
non-commuting circuits with a mixed graph and a learned independent-set
heuristic, but gives no bounds, no hardware terms and no code (we
re-implemented it from the description).

## 3. Contributions (claims, each with its evidence)

| # | Contribution | Evidence |
|---|---|---|
| C1 | **Exact reduction for general circuits.** Per-qubit commutation axes from the unitaries (Lemma 1), runs and trace order (Lemma 2); minimum depth over all equivalent reorderings = mixed chromatic number (Thm 1). `O(Σ arity)` memory, no quadratic graph. | THEORY §1–2; Fig. 2; IBM results (Lee'26 gains nothing; MKCO certified on 13/13) |
| C2 | **Max-k-Cut formulation** (Thm 2): depth budgets, weighted soft constraints (crosstalk), capacities (ancilla fan-out); near-feasible cuts give near-optimal circuits (Prop 3). | Tables 9 (Pareto), E6; Fig. 6 |
| C3 | **Certified lower bounds**: run-serialised Jackson bound for any circuit (Thm 7) and θ / θ⁺ SDP bounds with an exact, solver-independent repair (Prop 9). | E1/E7/E7b; all 13 IBM circuits certified; Fig. 3 |
| C4 | **Solver engine**: vectorised tabu Max-k-Cut with k-descent, window large-neighbourhood search with isolated windows (Prop 8), hierarchical Max-Cut = per-wire load balancing (Thm 4, Cor 5) with a log-encoded Ising form (Prop 6) solved by SA / Goemans–Williamson / QAOA. | E1–E5 (QAOA solves 21/21 sub-problems) |
| C5 | **Hardware-aware objectives**: two-qubit depth, crosstalk-prone pairs at fixed or budgeted depth, estimated duration, ALAP placement. | IBM Tables 2, 3, 5, 9; Fig. 6 |
| C6 | **Composition with gate rewriting**: single-qubit ZSX resynthesis + run merging, native-direction two-qubit KAK with an exact check (rejects Qiskit's silent inexact snaps), commutation-aware block formation before KAK. | IBM Table 4 (MKCO-full); E11 (17/19) |
| C7 | **Non-Clifford depth with free Cliffords** (Prop 10) via a surrogate circuit that the unchanged engine solves with certificates. | E8: −10% to −69% T-depth after PyZX, 17/17 certified |
| C8 | **Commutation-aware routing** (Prop 11) with an exact unroute check. | E9: QAOA −3.8% to −21.9% CNOTs, up to −55% depth vs Qiskit L3 |
| C9 | **State-aware idle-noise model** (Prop 12) and noise-aware selection among MKCO outputs. | E10: 95% vs 70% pairwise agreement; Aer noisy backend 7/7 vs 3/7 (set 1), Fig. 5 |
| C10 | **Verification and reproducibility**: independent commutation audit of every inverted pair, state-vector checks (≤ 20 qubits), open code with tests. | IBM Table 7; supplement |

## 4. The framework (for the "Proposed work" section)

**Figure 1** (`figures/fig1_framework`) is the workflow:
1. **Commutation analysis.** For each (gate, qubit) solve the null space of
   the commutators of the unitary with X, Y, Z on that qubit → axis Z, X, Y, a
   general direction, I or none (Lemma 1, checked exhaustively on all library
   gate pairs).
2. **Mixed graph.** Consecutive same-axis gates on a wire form a run; runs are
   ordered along the wire → precedence arcs; gates that share a wire conflict
   → edges (implicit, via a gate × wire incidence matrix).
3. **Weighted Max-k-Cut engine.** Warm starts (input ASAP, commutation-aware
   list schedules, DSatur for commuting segments) → improvement only while
   depth > LB: tabu Max-k-Cut with k-descent on commuting segments, window LNS
   on general circuits, optional hierarchical Max-Cut (SA / GW-SDP / QAOA /
   exact). Objective variants: depth, two-qubit depth, crosstalk (soft edges
   w = 0.1, anchor barriers), capacities, duration, ALAP.
4. **Emit + verify.** Zero-duration gates are placed between layers; the
   output is re-checked structurally, audited pairwise for commutation and
   (≤ 20 qubits) simulated. The input order is always a candidate (never
   worse).
5. **Certificates.** Jackson bound (any circuit) and θ / θ⁺ (commuting
   circuits); `depth = LB` ⇒ certified optimal.

Optional modules around the core: gate rewriting (ZSX, merging, KAK,
regrouping), non-Clifford depth, routing, and the noise model.

**Figure 2** (`figures/fig2_example`) is a worked 4-qubit, 7-gate example:
(a) the input has depth 6, and Lee et al.'s block colouring cannot improve it
because no commuting block spans the circuit; (b) the commutation runs give a
mixed graph with 6 arcs and 5 conflict edges; (c) a 3-colouring gives depth 3,
which equals the critical-path bound, so it is certified optimal.

**Figure 8** (`figures/fig8_theory_map`) shows how the formal results depend
on each other. **Figure 7** (`figures/fig7_capabilities`) is the capability
matrix against the two prior works (use it in Related Work or the
Introduction).

**Why Max-k-Cut rather than colouring.** Colouring asks a yes/no question per
k; Max-k-Cut asks how much can be separated, with weights. This gives the
search moves of the best colouring heuristics (TabuCol-style), weights for
hard and soft conflicts in one objective, capacities, and an Ising structure
(one bisection = per-wire load balancing) that maps to quantum solvers.

## 5. Formal results (statements; proofs in supplement/THEORY.md)

- **Lemma 1 (axis rule).** If, on every shared qubit q, both gates commute
  with the same Pauli direction n_q·σ (or one acts trivially), the gates
  commute.
- **Lemma 2 (trace equivalence).** Runs per wire define a partial order ≺;
  every linear extension of ≺ implements the input unitary; ≺ is stored in
  O(Σ_g |supp g|).
- **Corollary (independent audit).** A reordering is correct iff every
  inverted pair that shares a qubit commutes — checked numerically, without the
  axis machinery.
- **Theorem 1.** Minimum depth over equivalent reorderings = mixed chromatic
  number χ(M) of (gates, ≺ arcs, conflict edges). With ≺ empty this is Lee et
  al.'s reduction.
- **Theorem 2.** Φ_k(ℓ) = Σ_{t,q} C(occ[t,q], 2) = w(E) − Cut_k(ℓ); a k-layer
  circuit exists iff the precedence-constrained weighted Max-k-Cut cuts all of
  w(E).
- **Proposition 3 (repair bound).** Splitting each layer's monochromatic graph
  H_t gives depth ≤ k + Σ_t (½ + √(2|E(H_t)|+¼) − 1).
- **Theorem 4.** Σ_{u<v} w(u,v) z_u z_v = ½ Σ_q (S_q² − n_q): a bisection is a
  Max-Cut = per-wire load balancing (Ising with local fields for unequal
  halves). **Corollary 5**: conditions under which hierarchical Max-Cut is
  optimal (recovers König's edge-colouring theorem).
- **Proposition 6.** A K-layering of n gates needs n⌈log₂K⌉ spins over
  ⌈log₂K⌉ Ising sub-problems (one-hot: nK binaries + penalties).
- **Theorem 7.** LB = max(max_g head+tail+1, max_q J_q), J_q a single-machine
  (Jackson) makespan per wire; dominates the critical path and Lee et al.'s
  Eq. (2). depth = LB ⇒ certified optimal.
- **Proposition 8 (window isolation).** Compressing a window of layers is
  feasible iff its gates alone admit a (b−a)-colouring: an isolated small
  Max-k-Cut (basis of the LNS).
- **Proposition 9.** For commuting circuits depth ≥ χ(G) ≥ ϑ⁺(Ḡ) ≥ ϑ(Ḡ) ≥
  ω(G); a numerical SDP solution is repaired into an exactly feasible point,
  so ⌈⟨J,X⟩ − ε⌉ is a bound independent of solver accuracy.
- **Proposition 10.** Minimum counted (T / Toffoli) depth with free Cliffords
  = chromatic number of a mixed graph on the counted gates; solved through a
  surrogate circuit with virtual wires, with the Theorem 7 certificate.
- **Proposition 11.** A routed circuit whose un-routed logical sequence is a
  linear extension of ≺ implements the input up to the final permutation.
- **Proposition 12.** To first order, idling for time t costs fidelity
  γ(P₁ − |⟨σ⁻⟩|²) + p(1 − ⟨Z⟩²): it depends on the state the qubit waits in,
  so equal-depth reorderings can differ in fidelity.

## 6. Experimental setup

**Benchmarks**
- **IBM-127 set 1** (9 circuits; Qiskit optimisation level 3 for IBM Eagle
  127-qubit devices, basis ECR / RZ / SX / X, native ECR directions match the
  ibm_brisbane snapshot): mult_8, add_17, qae_17, qft_16, hubbard_8, hhl_8,
  heisenberg_32, grover_10, hubbard_18 — 1.9k to 358k gates, 8–32 active
  qubits.
- **IBM-127 set 2** (4 circuits, also level-3 transpiled, end in
  measurements): tfim_8, heisenberg_8, qpe_8 (ibm_brisbane), tfim_7_40
  (ibm_cusco). (The set's grover_10 is byte-identical to set 1.)
- **Base-paper settings** (Lee et al.): random multi-controlled-Z circuits
  (§4.3; m = 10/20/30 qubits, 50–200 gates, 60 instances), F₂ⁿ multiplier
  Toffoli layers (§5.1; n = 2…64), random CCZ on 10 qubits (App. C, 50
  instances), commuting RZZ / QAOA cost layers on random regular graphs (18),
  ancilla fan-out (§5.2, 20 settings).
- **Extension benchmarks**: 17 Clifford+T circuits (T-depth) and 13
  Toffoli-level circuits incl. 8 GF(2ⁿ) multipliers (E8), 13 untranspiled logical circuits for routing (E9: QAOA, Trotter, QFT,
  phase polynomial, random Clifford+T), 19 logical circuits for block
  formation (E11).

**Baselines**
- Lee et al. 2026: DSatur / backtracking on commuting blocks (block-wise for
  non-commuting circuits), as in the paper.
- Jain & Kumar 2026: re-implementation (mixed graph, repeated independent-set
  extraction with beam search).
- PyZX 0.10.7 (full_reduce + extract + basic_optimization) for T-depth.
- Qiskit 2.6.1 transpiler at optimisation level 3 (SabreLayout + SabreSwap +
  optimisation loop) **only for the untranspiled logical circuits** (routing
  E9, block formation E11). It is *not* a baseline on the IBM benchmarks,
  which are already its level-3 output; there the reference is the input
  itself.

**Metrics.** Depth, two-qubit (ECR) depth, crosstalk-prone pairs (two ECRs in
the same layer on neighbouring couplers), estimated duration (ECR 533 ns, sx/x
36 ns, rz virtual), ECR count, T-/Toffoli-depth, CNOTs after routing, proven
lower bound and certified-optimal count, runtime. Noise: ESP (state-blind),
state-aware ESP (Prop 12), exact density-matrix state fidelity (≤ 8 qubits),
Hellinger fidelity of sampled counts on Aer with `NoiseModel.from_backend`
(32,768 shots; bootstrap 95% intervals). "Scale 0.1" = all error rates ×0.1
and T1/T2 ×10 (a near-term device), scale 1 = the calibration snapshot.

**Verification.** Every reordered output passes an exact pairwise commutation
audit of all inverted pairs; outputs with ≤ 20 active qubits are also checked
by state-vector simulation (rewritten outputs against the input unitary).

**Environment.** Python, single process, laptop; qiskit 2.6.1, qiskit-aer
0.18, qiskit-ibm-runtime 0.51 (fake backends), pyzx 0.10.7, cvxpy 1.9.3 with
Clarabel / SCS. No real-hardware runs (no IBM account was available); the
submission script exists.

## 7. Results by research question

### RQ1 — Does MKCO find and *prove* optimal depths? (Fig. 3)

{{table:paper_settings}}

- **SDP certificates (E7, E7b).** θ closes the gap on 6 of 15 instances that
  the clique/Jackson bound left open; θ⁺ closes one more of the 14 remaining
  (a 200-gate instance, 95.03 → 96 = MKCO). Without SDP: MKCO 41/60 vs DSatur
  36/60 certified on E1; with them 48/60 vs 42/60.
- **E5 hierarchical Max-Cut.** QAOA solves 21/21 Ising sub-problems optimally
  on four structured cases; the log encoding needs 20–64 spins where one-hot
  needs 40–176.
- **IBM circuits.** All 13 are certified optimal for depth and for two-qubit
  depth (next table).

### RQ2 — Gains on circuits already transpiled at Qiskit level 3 (Fig. 4)

{{table:ibm}}

- **Reorder-only.** Lee et al.'s block colouring gains nothing on any of the
  13 circuits. MKCO lowers depth on 12/13 (up to −5.2%; grover_10:
  −2,282 layers) and proves heisenberg_32 already optimal; hubbard_18 had only
  7 layers of headroom out of 136,644. Jain & Kumar reach the same depths (any
  sound commutation-aware layering does on these instances) but cannot certify
  them, and in depth mode raise add_17's two-qubit depth by 2.
- **Two-qubit depth.** Certified optimal on 13/13; hubbard_8 (−1) and
  hubbard_18 (−3) improve, the rest were already optimal.
- **With gate rewriting (MKCO-full).** Shallower than the transpiled input on
  all 13 (set 1: −1.9% to −57.8%; set 2: −0.5% to −3.1%) and faster in
  estimated time on all 13 (−0.1% to −17.7%). Large gains come from KAK on
  Trotter-type circuits: heisenberg_32 7,143 → 3,011 (60 fewer ECRs);
  hubbard_18 136,644 → 72,992 (3,505 fewer ECRs, −17.7% time). All outputs use
  the native ECR direction.

### RQ3 — Hardware-aware objectives: crosstalk and depth budgets (Fig. 6)

- **At the certified-optimal two-qubit depth**, the weighted Max-k-Cut
  removes 1.8–25.9% of crosstalk-prone ECR pairs on set 1 (mean −14.2%) and
  13.6% on qpe_8; the other set-2 circuits have no slack at the optimum.
- **With a depth budget** k = k* + slack: −21% to −44% of pairs at +10%
  two-qubit depth and −39% to −65% at +20% on set 1; −34% to −38% at +20% on
  set 2 (full curves: tables/full_ibm127_set1.md, Table 9).
- Anchor barriers keep the two-qubit depth optimal but cost 0.8–7.6% total
  depth (0.0–0.9% estimated duration).

### RQ4 — Fault-tolerant cost: T-depth and Toffoli-depth (E8)

{{table:tdepth}}

- On its own, MKCO-T lowers the T-depth of the GF(2ⁿ) multipliers by 39–44%
  and of T phase polynomials by 23–30%; it is certified optimal on 14 of 17
  T-depth instances. Ripple-carry adders are proven to admit no improvement.
- After PyZX, MKCO-T cuts T-depth by a further **10–69% (mean 41%)** on all
  17, every result certified optimal (gf2_mult_7: 74 → 23).
- Toffoli-depth of the multipliers drops 53–64% (gf2_mult_12: 64 → 23).
- Plain depth-minimising MKCO is worse on T-depth (cuccaro_16: 144 vs 128):
  the counted objective matters.

### RQ5 — Routing and block formation on logical circuits (E9, E11)

{{table:routing}}

- **QAOA** (whole cost layers commute): 3.8–21.9% fewer CNOTs than Qiskit's
  level-3 SABRE on all 7 and up to 55% shallower (qaoa_n64_p1: 638 vs 726
  CNOTs, depth 80 vs 177).
- **Trotter**: −2.9% CNOTs and 7.9% shallower at n = 16; +0.2% CNOTs and
  25% shallower at n = 32.
- **QFT is Qiskit's case** (+11% / +25% CNOTs); the ablation shows our SABRE
  base is weaker than Qiskit's tuned implementation there.
- **Ablation**: the plain DAG front needs more CNOTs on 13/13, so the gain is
  the commutation-aware front. **Composition**: MKCO's post-routing passes
  lower the depth of Qiskit's output on 13/13 at equal or fewer CNOTs.

{{table:regroup}}

- Commutation-aware block formation removes CNOTs on 17/19 circuits relative
  to plain block KAK and never adds any; on par with Qiskit L3 in CNOTs and
  shallower after layering on Trotter, QAOA and random circuits. On the
  already-transpiled IBM circuits only hubbard_8 gains (4 ECRs).
- Qiskit's KAK decomposer snaps near-identity blocks to inexact circuits even
  with `approximate=False` (a controlled phase of 5·10⁻⁵ in QFT-20); MKCO's
  exact check rejects them.

### RQ6 — Does depth translate into fidelity? (Fig. 5)

**Noise model with device calibration (E10).** Each circuit is scored with
its own device snapshot (ibm_brisbane; ibm_cusco for tfim_7_40) at 10× lower
noise:

{{table:noise}}

- **Depth is not fidelity.** All reorderings have the same gate noise; the
  differences come from idling, mainly dephasing of qubits that wait in
  superposition. A depth-optimal order can be less faithful (mult_8: −4.4%)
  or more (hhl_8: +12%; qpe_8: +4.3%).
- **State-aware ESP (Prop 12) sees this; the usual ESP does not.** It orders
  method pairs as the density-matrix simulation does in 95% of cases on set 1
  (84% at calibrated noise) vs 70% (57%) for the state-blind ESP; set 2: 90%
  (78%) vs 80% (64%).
- **Noise-aware selection** (`mkco_noise`: best state-aware ESP among MKCO's
  orders, their ALAP variants and the input) never scores below the input,
  above it on 8/9 set-1 circuits, and at least as high as Jain & Kumar on
  every circuit.

**Independent check on a noisy simulated backend (Aer + `NoiseModel.from_backend`,
no shared code with the model).** Hellinger fidelity at 10× lower noise:

{{table:noisy_backend}}

- On the method pairs that sampling separates, set 1: density-matrix model
  7/7, state-aware ESP 7/7, state-blind ESP 3/7 (worse than chance — it
  rewards shorter orders); at calibrated noise 4/4, 4/4, 2/4. Set 2: all
  three predictors 4/4 (×0.1) and 6/6 (×1).
- qpe_8 is the clearest case: every MKCO order 0.701–0.707 vs input 0.679,
  separated intervals, as predicted (+4%).
- The 17-qubit circuits (512 shots) have intervals of ±0.03, wider than the
  predicted 1–2% differences; qae_17's measured order matches the prediction
  but the intervals overlap.
- Crosstalk mode does **not** carry over to a timing model: under ESP_xt it
  beats plain MKCO only on hubbard_18 (×24). A duration-aware crosstalk
  objective is future work.

### RQ7 — Runtime

{{table:runtime}}

MKCO is faster than our runs of Lee et al. on every circuit and comparable to
Jain & Kumar (faster on 8 of 13, at most 2.3× slower); it handles 358k gates in about 20 s for the reordering
(MKCO-full with KAK resynthesis: about 6 min). Runtime scaling on the
structured sets is in `figures/runtime_scaling.png`.

## 8. Figures

New figures for the paper (`figures/*.pdf` vector, `*.png` 200 dpi):

| File | Suggested caption | Section |
|---|---|---|
| fig1_framework | The MKCO framework: commutation analysis → mixed graph → weighted Max-k-Cut engine → emission and verification, with certified lower bounds, optional gate rewriting, hardware objectives and device-level modules. | Proposed work |
| fig2_example | Worked example. (a) Input order, depth 6; block colouring cannot improve it. (b) Mixed graph from commutation runs (arcs = precedence, edges = conflicts); colours = layers. (c) MKCO layering, depth 3 = lower bound, certified optimal. | Proposed work |
| fig3_certified | Share of instances solved to proven optimality per method on the base paper's settings and the IBM sets. | Results RQ1 |
| fig4_ibm_overview | Depth reduction vs the transpiled input on the 13 IBM-127 circuits (symlog): Lee et al., Jain & Kumar, MKCO reorder (certified), MKCO-full. | Results RQ2 |
| fig5_noise_selection | Simulated state fidelity of MKCO orders relative to the input (10× lower noise, device calibration): depth-only, ALAP, noise-aware selection. | Results RQ6 |
| fig6_crosstalk_budget | Crosstalk-prone ECR pairs removed at the optimal two-qubit depth and with +10% / +20% depth budgets. | Results RQ3 |
| fig7_capabilities | Capability matrix vs Lee et al. and Jain & Kumar. | Intro / Related work |
| fig8_theory_map | Dependency map of the formal results. | Theory |

Existing report figures (also in `figures/`): `e1_random_mcz`, `gf2_multiplier`,
`e3_ccz`, `e4_rzz`, `e6_fanout`, `ibm127_depth`, `ibm127_crosstalk`,
`ibm127_rewrite`, `ibm127_duration`, `pareto_crosstalk`, `runtime_scaling`,
`tdepth`, `routing`, `noise_validation`.

## 9. Limitations and negative results (must appear in the paper)

- **The IBM benchmarks are easy for reordering.** Commutation-aware list
  scheduling already meets the bound, so JK and MKCO reach equal depths; MKCO's
  distinctive value there is the proof, the hardware objectives and the
  rewrite modes. Max-k-Cut search matters on the structured commuting sets
  (E1–E4).
- **Jain & Kumar re-implemented** from the description (no public code).
- **Crosstalk proxy** (neighbouring couplers, same layer) does not survive a
  timing model (E10).
- **Depth-only optimisation can lower fidelity** (mult_8 −4.4%); the
  noise-aware selection is the fix.
- **Simulation only.** All noise results use calibration snapshots and Aer;
  no real hardware. Noise model: depolarising gate errors, thermal relaxation,
  readout; no crosstalk, leakage, coherent errors or dynamical decoupling.
- **Routing**: CNOT level, symmetric couplers, one Qiskit seed; QFT is worse
  than Qiskit (+11–25% CNOTs).
- **T-depth**: PyZX is a T-count optimiser; MKCO-T composes with it but is not
  compared with re-synthesis T-depth methods (T-par, TODD).
- **SDP bounds** are for commuting circuits only and costly beyond ~200 gates.
- **Runtimes** are indicative (laptop, shared machine).

## 10. Claims → evidence map

| Claim in the paper | Where the evidence is |
|---|---|
| MKCO generalises colouring to any circuit, exactly | Thm 1; Fig. 2; IBM table (Lee gains 0/13) |
| MKCO proves optimality where colouring cannot | Fig. 3; paper-settings table; IBM table (13/13 ✓) |
| Max-k-Cut enables hardware trade-offs colouring cannot express | Fig. 6; IBM Table 9 |
| Gains on top of Qiskit level-3 output | IBM table (MKCO-full on 13/13) |
| Extends to fault-tolerant cost | T-depth table (17/17 ✓ after PyZX) |
| Commutation-aware routing helps commuting workloads | routing table (QAOA 7/7); ablation 13/13 |
| Depth ≠ fidelity; the state-aware model predicts it | noise tables; Aer 7/7 vs 3/7 |
| Every output is verified | IBM Table 7; audit + state vector |

## 11. Key references (full notes: supplement/RELATED_WORK.md)

- Lee, Jeong, Kim. Quantum Circuit Optimization by Graph Coloring. *Quantum*
  (2026), arXiv:2501.14447 — the base paper.
- Jain, Kumar. Quantum Circuit Depth Optimization using Graph Coloring.
  NeurIPS 2026 WiML poster — direct follow-up.
- Brélaz 1979 (DSatur); Hertz & de Werra 1987 (TabuCol); Galinier & Hao 1999
  (HEA); Frieze & Jerrum 1997 (Max-k-Cut SDP); Goemans & Williamson 1995;
  Burer & Monteiro 2003; Lovász 1979 (θ); Szegedy 1994 (θ⁺); Jackson 1955
  (scheduling rule); Mazurkiewicz traces; König's edge-colouring theorem;
  Vizing's theorem.
- Farhi, Goldstone, Gutmann 2014 (QAOA); Lucas 2014 (Ising formulations).
- Li, Ding, Xie 2019 (SABRE); Qiskit; Kissinger & van de Wetering (PyZX);
  Amy, Maslov, Mosca (T-par); Heyfron & Campbell (TODD); Maslov et al. (F₂ⁿ
  multiplier); Draper (QFT adder); Cuccaro et al. (ripple-carry adder);
  Murali et al. 2020 (crosstalk-aware scheduling); Vidal & Dawson / Shende et
  al. (KAK two-qubit synthesis).

Verify every bibliographic detail (venue, year, pages) before submission; the
list above is from study notes.
