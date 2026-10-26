# Quantum Circuit Optimization by Max-k-Cut (MKCO)

**Extending Lee, Jeong & Kim, "Quantum Circuit Optimization by Graph Coloring" (*Quantum*, 2026).**
Report, code and benchmark results.

## 1. Summary

Lee et al. proved that minimizing the depth of a circuit made only of
mutually commuting gates is graph colouring, and solved it with DSatur.
MKCO turns that reduction into a **Max-k-Cut framework** that:

1. **Covers every circuit, not only commuting ones.** Per-qubit commutation
   axes give a linear-size mixed graph (precedence arcs + conflict edges).
   Minimum depth over all commutation-equivalent reorderings is exactly its
   mixed chromatic number (Theorem 1).
2. **Solves layering as precedence-constrained weighted Max-k-Cut.** A depth-k
   circuit exists iff the cut contains every hard edge (Theorem 2). The same
   objective handles three things colouring cannot: depth budgets, soft
   hardware penalties (crosstalk), and capacities (ancilla fan-out).
3. **Shows that Max-Cut on the conflict multigraph is per-qubit load balancing**
   (Theorem 4). Recursive Max-Cut therefore meets the max-load bound whenever
   balanced splits exist. It also gives a qubit-efficient Ising/QUBO
   encoding, n·⌈log₂ depth⌉ spins, for QAOA, annealers or Goemans–Williamson
   SDP (Proposition 6).
4. **Certifies its answers.** A run-serialised Jackson lower bound (Theorem 7),
   plus a Lovász-θ SDP bound for commuting circuits, proves optimality. An
   independent commutation audit, plus state-vector simulation for ≤ 20 active
   qubits, verifies every output.
5. **Goes beyond reordering when asked.** Optional single-qubit (ZSX) and
   two-qubit (KAK, native ECR direction) resynthesis feed the same Max-k-Cut
   layering. On the already-transpiled benchmarks this lowers depth by up to
   58% and estimated execution time by up to 18%. Commutation-aware block formation lets KAK see
   blocks that commuting gates had split (E11).
6. **Optimises fault-tolerant depth.** T-depth and Toffoli-depth with free
   Clifford gates reduce to a mixed-graph colouring on the non-Clifford gates
   (Proposition 10), solved by the same engine with a certified bound. On top
   of PyZX it lowers T-depth by 41% on average (E8).
7. **Routes with the same commutation structure.** A SABRE-style router whose
   front layer is the trace-order front, followed by Max-k-Cut layering. It is
   proven correct per output (Proposition 11) and evaluated against Qiskit's
   SABRE routing on logical circuits for IBM's 127-qubit heavy-hex device (E9).
8. **Is checked against device noise.** Scoring with the ibm_brisbane
   calibration shows that a depth-optimal reordering can be *less* faithful,
   because qubits may idle in superposition for longer. A state-aware success
   estimate (Proposition 12) predicts this, matching density-matrix
   simulation, and picks the output (E10). A script for real IBM runs is
   included.

**Comparison against the related work.** Lee et al. 2026 and Jain & Kumar 2026
are run on identical inputs:
- rows 1–6: the 9 provided IBM-127-transpiled benchmarks (rz/sx/x/ecr,
  1.9k–358k gates);
- rows 7–11: the paper's own experimental settings and structured commuting
  circuits;
- rows 12–15: the extensions (fault-tolerant depth, routing, block formation,
  noise), each against an established tool.

| Question | Lee et al. 2026 | Jain & Kumar 2026 | **MKCO (ours)** |
|---|---|---|---|
| Total depth, reorder-only (9 circuits) | no gain on any circuit | same depths as MKCO, uncertified | −1.9% to −5.2% on 7 circuits; **certified optimal on 9/9** |
| Two-qubit depth | already optimal or no gain | optimal on 9/9 (uncertified) | **certified optimal on 9/9** |
| Crosstalk-prone ECR pairs at optimal 2q-depth | cannot express | cannot express | **−1.8% to −25.9%** (mean −14.2%) |
| Gate rewriting vs the transpiled input (Qiskit level 3) | – | – | MKCO-full **shallower on 9/9** (−1.9% to −57.8%) and **faster (est. time) on 9/9** (−0.1% to −17.7%); all outputs native-direction |
| Depth budget vs crosstalk (Pareto) | cannot express | cannot express | −21% to −44% pairs at +10% 2q-depth; −39% to −65% at +20% |
| F₂ⁿ multiplier (paper §5.1), n = 2…64 | optimal at 24/34 sizes | 7/34 | **34/34 (proven)** |
| Random multi-controlled-Z (paper §4.3), 60 circuits | 42/60 certified optimal (36 by clique/Jackson, 6 more by θ/θ⁺) | 0/60 | **48/60** (41 + 7 more by θ/θ⁺); never worse than DSatur |
| Random CCZ (paper App. C), 50 circuits | 20/50 certified optimal | 17/50 | **49/50** |
| RZZ/QAOA layers (edge colouring), 18 circuits | 0/18 reach Δ | 0/18 | **14/18 reach Δ (optimal)** |
| Second IBM-127 set (4 circuits with measurements, Section 5.1) | no gain | ties, uncertified | depth and 2q-depth **certified optimal 4/4**; MKCO-full −0.5% to −3.1% vs the input; noisy simulation: qpe_8 +3–4% fidelity vs the input |
| Ancilla fan-out (paper §5.2) | heuristic not specified | – | up to **−24%** vs fixed copy split |
| T-depth with free Cliffords, after PyZX (17 Clifford+T circuits, E8) | – | – | **−10% to −69%** (mean −41%) vs PyZX alone; 17/17 certified optimal |
| Toffoli-depth, GF(2ⁿ) multipliers n = 4–12 (E8) | commuting parts only | – | **−53% to −64%** vs input; 6/8 certified |
| Routing logical circuits on the 127-qubit heavy-hex device vs Qiskit's SABRE at level 3 (13 circuits, E9) | – | – | QAOA (7): **−3.8% to −21.9% CNOTs, up to −55% depth**; Trotter shallower; QFT worse (+11–25% CNOTs) |
| Block formation before KAK (19 logical circuits, E11) | – | – | fewer CNOTs than plain block KAK on **17/19**, never more |
| Noise with ibm_brisbane calibration (9 circuits, E10) | – | – | state-aware ESP orders method pairs like density-matrix simulation in **95%** of cases (state-blind ESP 70%); `mkco_noise` never below the input, above it on 8/9 |

Every reordered output was independently verified: an exact pairwise
commutation audit, plus state-vector simulation for ≤ 20 active qubits.


## 2. What the base paper leaves open (and what MKCO does about it)

| Open point in Lee et al. | MKCO |
|---|---|
| Only commuting circuits (§6) | Exact reduction for arbitrary circuits via a mixed graph (Thm 1); O(Σ arity) memory |
| Hardware restrictions "highly nontrivial" (§6) | Hardware penalties become weighted soft edges of the Max-k-Cut (Thm 2); crosstalk mode on IBM heavy-hex |
| DSatur vs exact gap "open for further experiment" (§4.3) | Answered: on the paper's random circuits DSatur is within 0–0.8 layers of the maximum clique for m ≥ 20 qubits but 4.6–5.2 layers above the bound at m = 10, n ≥ 150, where MKCO cuts the gap by more than half; on structured circuits (F₂ⁿ multiplier, CCZ, RZZ layers) MKCO closes DSatur's gap to the certified bound |
| DSatur misses 2n−1 for some n < 20 (fn. 2) | MKCO is optimal for every n = 2…64 (bound 2n−1 for n ≥ 6, exhaustive proof for n ≤ 5); DSatur is sub-optimal at 10 sizes |
| Extra-qubit parallelisation algorithm not given (§5.2) | Capacitated Max-k-Cut (wire capacity = number of fan-out copies), implemented and verified (E6): up to 24% shallower than a fixed copy split |
| No optimality certificate beyond Eq. (2) | Stronger certified bound (Thm 7); optimality proven on every IBM benchmark |

## 3. The MKCO framework

Full statements and proofs are in [THEORY.md](THEORY.md); related work is in
[RELATED_WORK.md](RELATED_WORK.md).

### 3.1 Pipeline
```
QASM ──► commutation axes per (gate, qubit)  [Lemma 1, exact from unitaries]
     ──► runs per wire → mixed graph M = (gates, precedence arcs, conflict edges)   [Lemma 2, O(Σ arity)]
     ──► certified lower bound LB  (run-serialised Jackson bound)                    [Thm 7]
     ──► warm starts: original ASAP, commutation-aware list schedules, DSatur (commuting)
     ──► Max-k-Cut improvement (only while depth > LB):
           commuting segments: vectorised tabu Max-k-Cut with k-descent (TabuCol-style)
           general circuits:   window LNS, each window an isolated Max-k-Cut      [Prop 8]
           optional:           hierarchical Max-Cut (SA / GW-SDP / QAOA / exact)    [Thm 4]
     ──► emission (zero-duration gates placed between layers) → structural certificate
     ──► independent commutation audit (+ state-vector check ≤ 20 qubits)
Modes:  depth | 2q-depth | crosstalk (soft edges + anchor barriers) | fan-out capacities
Optional pre-passes (gate-rewriting class), each verified numerically block by block:
  rewrite: single-qubit ZSX resynthesis + run-based rotation merging, to a fixed point
  full:    + two-qubit KAK block resynthesis in the native ECR direction (keeps the better)
Bounds:  run-serialised Jackson bound (any circuit) + Lovász theta SDP (commuting circuits)
```

### 3.2 Why Max-k-Cut and not just colouring
Colouring asks one yes/no question per k: can every conflict be separated?
Max-k-Cut asks *how much* can be separated, with weights. This gives:
- **Search.** The strongest colouring heuristics (TabuCol, HEA) are Max-k-Cut
  local searches. MKCO's engine evaluates all moves of all conflicting gates
  with one matrix product (`A_C · Mᵀ`) over a gate × wire incidence matrix,
  never materialising the O(n²) conflict graph.
- **Weights.** Hard edges (shared qubits) and soft edges (crosstalk, `w = 0.1`)
  live in one objective. With *k* fixed at the certified optimum, the search
  can only spend slack on soft edges.
- **Capacities.** A fanned-out wire with `c` copies holds `c` gates per layer.
- **Ising structure.** One bisection is a Max-Cut that equals per-qubit load
  balancing (Thm 4). It is solvable by Goemans–Williamson rounding of a
  Burer–Monteiro SDP, by annealing, or by QAOA, with `n·⌈log₂k⌉` spins for
  the whole layering.

### 3.3 Correctness guarantees
1. **Soundness.** Only gates that provably commute are swapped. The rule is
   checked against exact matrices for every gate pair in the library.
2. **Never worse.** The original order is always a candidate, ties are broken
   by the secondary metric, and the result is checked before it is returned.
3. **Two independent verifications** of every output (Section 4).
4. **Optimality certificate** whenever `depth = LB`.

## 4. Experimental setup

**Benchmarks.** The 9 provided circuits, already transpiled for a 127-qubit
IBM Eagle device:
- basis `rz, sx, x, ecr`;
- ECR declared as a custom `gate`, kept as one instruction; its commutation axes
  come from its exact unitary: target ≡ X axis, control has none;
- 8–32 active qubits, 1,898–357,535 gates, no measurements or barriers.

**Metrics.**
- *Depth*: Qiskit's `QuantumCircuit.depth()`. MKCO's metric matches Qiskit on
  every input.
- *Two-qubit depth*: ECR layers; single-qubit gates count as zero.
- *Crosstalk-prone pairs*: two ECRs in the same two-qubit layer on couplers
  that share no qubit but are joined by a hardware edge (the spectator/ZZ
  crosstalk proxy of Murali et al. 2020). The coupling graph is inferred from
  the ECR pairs used across the 9 files (78 couplers, 107 neighbouring pairs).
- *Estimated duration*: ASAP with nominal Eagle durations — ECR 533 ns,
  sx/x 36 ns, rz virtual.

**Methods.** Every method sees the same input file. The inputs are already
Qiskit's output at optimization level 3, so re-running Qiskit's optimiser on
them is not a baseline; the gate-rewriting modes are compared with the input.
- `lee2026`: Lee et al.'s DSatur colouring (networkx implementation), applied
  to every maximal block of mutually commuting gates. This is the extension
  their conclusion suggests ("divide a noncommuting circuit into many commuting
  parts").
- `jk2026`: Jain & Kumar's independent-set layering of the mixed graph with
  beam search (width 3; width 1 above 25k gates). This is a re-implementation;
  their code is not public.
- `mkco`: our pipeline: list-scheduling warm starts, then precedence-constrained
  Max-k-Cut (tabu k-descent for commuting segments, window-compression LNS for
  general ones), stopping as soon as the certified bound is met.
- `mkco_xt`: our crosstalk mode. Optimal two-qubit depth with weighted soft
  edges (w = 0.1), and anchor barriers so an ASAP hardware scheduler reproduces
  the layering.
- `mkco_rewrite`: our rewrite mode. Each maximal chain of single-qubit gates
  is re-synthesised in the device basis (rz/sx/x) by ZSX Euler decomposition,
  same-axis rotations are merged across commuting two-qubit gates, and the
  result is reordered by MKCO.
- `mkco_full`: two-qubit block (KAK) resynthesis into native-direction ECRs
  plus the rewrite mode, iterated to a fixed point, then Max-k-Cut reordering.
  The numerical KAK step uses Qiskit's `TwoQubitBasisDecomposer`. Block
  collection, the native-direction constraint, the acceptance rule (fewer
  ECRs, or equal ECRs and a shallower block) and verification are ours. It
  keeps the shallower of this pipeline and rewrite-only, so it is never worse.

**Verification.** Every reordered output passes two independent checks:
1. the structural certificate (a linear extension of the dependency order);
2. the commutation audit (every pair whose order changed commutes, checked on
   exact matrices).

Outputs with at most 20 active qubits are additionally checked by state-vector
simulation on random inputs (global phase compared). A negative control — one
illegal swap — fails both the audit and the simulation.

**Extensions (Section 7).**
- *T-depth / Toffoli-depth (E8).* Generated circuits (`mkco.generators`):
  - Cuccaro ripple-carry adders;
  - Barenco V-chain multi-controlled X;
  - GF(2ⁿ) multipliers (trinomial reduction, ancilla register for the high
    terms);
  - random T phase polynomials;
  - random Clifford+T.

  Toffolis are decomposed with the 7-T circuit of Nielsen & Chuang. PyZX
  0.10.7 runs `full_reduce` + `extract_circuit` + `basic_optimization`
  (respectively `teleport_reduce`).
- *Routing (E9).* IBM Eagle heavy-hex coupling graph (127 qubits, 144
  couplers; `benchmarks/devices/ibm_eagle_127.json`, from FakeSherbrooke;
  the same graph as ibm_brisbane), symmetric CNOTs.
  - Qiskit: `transpile(..., coupling_map, basis_gates=[cx, rz, sx, x],
    optimization_level=3, seed_transpiler=0)`.
  - MKCO-route: 16 trials (8 per front scoring), 3 bidirectional layout
    iterations each.
- *Block formation (E11).* Logical circuits in the CX basis, all-to-all. Qiskit
  O3 with `basis_gates=[cx, rz, sx, x]`.
- *Noise (E10).* Calibration snapshot of ibm_brisbane (FakeBrisbane,
  qiskit-ibm-runtime 0.51): median ECR error 0.77%, ECR 660–780 ns, sx 60 ns,
  median T1 232 µs, T2 150 µs, median readout error 2%. Density matrices
  are computed with qiskit-aer 0.18.

**Machine.** Laptop, Intel Core i7-1068NG7 (4 cores / 8 threads, 2.3 GHz), 16 GB, Python 3.13, single
process.

## 5. Results on the IBM-127 benchmarks

![Depth reduction](figures/ibm127_depth.png)

**Reorder-only depth (Table 1).**
- **Lee et al.** gains nothing on any of the 9 circuits. After transpilation,
  maximal blocks of mutually commuting gates are short, and colouring each block
  separately cannot move a gate across a block boundary.
- **MKCO** reorders across the whole circuit. Depth drops by 2.9–5.2% on 7
  circuits (grover_10: −2,282 layers), and the result equals the certified
  lower bound on **all 9**. These depths are therefore *provably optimal*:
  no reordering method, present or future, can do better on these inputs.
- **heisenberg_32** is proven to be already optimal as transpiled.
- **hubbard_18** had only 7 layers of headroom out of 136,644.
- **Jain & Kumar** (our re-implementation) reaches the same depths, as any
  sound commutation-aware layering must once the instance is this easy. It
  cannot certify them, and in depth mode it raises the 2q-depth of add_17 by 2.

**Two-qubit depth (Table 2).** In 2q mode MKCO is certified optimal on 9/9.
Seven circuits were already optimal as transpiled; hubbard_8 (−1) and
hubbard_18 (−3) improve.

![Crosstalk](figures/ibm127_crosstalk.png)

**Crosstalk at optimal 2q-depth (Table 3): the Max-Cut-only capability.**
- No colouring-based method can express "prefer not to run these two ECRs
  together". All three baselines leave the crosstalk-prone pair count where
  the transpiler put it.
- With the 2q-depth pinned at its certified optimum, the weighted Max-k-Cut
  spends the available slack on soft edges. It removes **1.8–25.9%** of
  neighbouring-coupler ECR pairs (mean 14.2%; hubbard_18: −1,897 pairs, −25.9%).
- The cost: the anchor barriers that lock the layering add 0.8–7.6% total
  depth, but only 0.0–0.9% estimated duration, because ECRs dominate execution
  time.

![Rewriting](figures/ibm127_rewrite.png)

**Gate rewriting (Table 4).** The inputs are already Qiskit's output at
optimization level 3, so the reference is the input itself; re-running
Qiskit O3 on them would not be a meaningful baseline.
- **MKCO-full is shallower than the input on all 9 circuits** (−1.9% to
  −57.8%). Every MKCO result is certified optimal for the gate list it
  reorders.
  - The two Hamiltonian-simulation circuits gain most: heisenberg_32
    7,143 → 3,011 (−57.8%), hubbard_18 136,644 → 72,992 (−46.6%).
  - Their transpiled rz/sx chains collapse under single-qubit resynthesis.
    MKCO's run-based merging then gathers same-axis rotations *across*
    commuting ECRs, which the level-3 transpiler's adjacent-gate passes did
    not do.
- On the other 7 circuits rewriting adds little to reordering (at most 27
  layers).

![Execution time](figures/ibm127_duration.png)

**Hardware time.** Total depth counts virtual rz layers, so the
hardware-relevant figure is estimated execution time.
- Selecting among MKCO's candidates by estimated duration, MKCO-full is
  **faster than the input on all 9 circuits**: −0.1% to −1.1% on 7, −9.0% on
  heisenberg_32 and −17.7% on hubbard_18.
- On hubbard_18 it also lowers two-qubit depth (21,769 → 18,795) and the ECR
  count (33,958 → 30,453, −10.3%).
- Depth- and duration-optimal choices differ on hubbard_18. The 1q-only
  pre-pass gives the smallest total depth (72,992). KAK block resynthesis
  gives the fewest ECRs and the shortest time.

**Two-qubit block (KAK) resynthesis (Table 8).**
- The transpiled circuits are already ECR-optimal block by block on 7 of 9
  benchmarks (0–58 cheaper blocks).
- On heisenberg_32 and hubbard_18, KAK finds 1,073 and 4,856 cheaper blocks.
  On hubbard_18 it removes 3,505 ECRs.
- *Locally* cheaper blocks are not automatically better globally. On
  heisenberg_32 the KAK branch is 33% deeper than 1q-only (3,998 vs 3,011),
  because generic KAK output pins single-qubit layers on both wires and
  destroys the cross-block merging the run model exploits. MKCO therefore
  evaluates both branches after Max-k-Cut reordering and keeps the better one.

![Pareto](figures/pareto_crosstalk.png)

**Depth budget vs crosstalk (Table 9).** This is Theorem 2's depth-budget
form in action. The certified-optimal layering is stretched
order-preservingly to k* + s layers, and the weighted Max-k-Cut spends the
slack on soft edges.
- With s = 0 (no depth cost), crosstalk-prone pairs fall 2–26%.
- With 10% slack they fall 21–44%; with 20% slack, 39–65%.
- Estimated execution time grows by 1–19% along these fronts. The fronts let
  a user choose the operating point that fits their device's crosstalk to
  coherence ratio.
- The search is time-limited, so a few measured points are dominated; the
  figure plots the non-dominated ones and Table 9 lists all of them.

**Correctness (Table 7).** All reordered outputs (117 audits) pass the independent
commutation audit (14,222 reordered gate pairs checked on grover_10 alone).
Every MKCO output with ≤ 20 active qubits also matches the input under
state-vector simulation (fidelity 1 to 10 digits, global phase consistent).

![Runtime](figures/runtime_scaling.png)

**Runtime (Table 6).** Reorder-only MKCO runs in 0.1–20 s, faster than
block-wise colouring on every circuit and comparable to Jain & Kumar.
- The crosstalk mode uses its time budget (30–60 s).
- MKCO-full evaluates two pre-pass branches and takes up to 6 minutes on the
  358k-gate hubbard_18.

### Table 1 - Total depth, reorder-only methods (lower is better)

| Circuit | Gates | Original | Lee'26 (colouring) | JK'26 (MIS+beam) | **MKCO** | Certified LB | MKCO optimal? | MKCO vs original |
|---|---:|---:|---:|---:|---:|---:|:---:|---:|
| mult_8 | 1898 | 1138 | 1138 | 1102 | **1102** | 1102 | yes | -3.16% |
| add_17 | 2812 | 1003 | 1003 | 964 | **964** | 964 | yes | -3.89% |
| qae_17 | 3033 | 1066 | 1066 | 1035 | **1035** | 1035 | yes | -2.91% |
| qft_16 | 3444 | 1009 | 1009 | 980 | **980** | 980 | yes | -2.87% |
| hubbard_8 | 8125 | 4400 | 4400 | 4268 | **4268** | 4268 | yes | -3.00% |
| hhl_8 | 18165 | 10641 | 10641 | 10434 | **10434** | 10434 | yes | -1.95% |
| heisenberg_32 | 58848 | 7143 | 7143 | 7143 | **7143** | 7143 | yes | +0.00% |
| grover_10 | 93235 | 43923 | 43923 | 41641 | **41641** | 41641 | yes | -5.20% |
| hubbard_18 | 357535 | 136644 | 136644 | 136637 | **136637** | 136637 | yes | -0.01% |

### Table 2 - Two-qubit (ECR) depth, reorder-only methods optimising 2q-depth

| Circuit | Original | Lee'26 | JK'26 | **MKCO** | Certified LB | MKCO optimal? |
|---|---:|---:|---:|---:|---:|:---:|
| mult_8 | 276 | 276 | 276 | **276** | 276 | yes |
| add_17 | 253 | 253 | 253 | **253** | 253 | yes |
| qae_17 | 274 | 274 | 274 | **274** | 274 | yes |
| qft_16 | 260 | 260 | 260 | **260** | 260 | yes |
| hubbard_8 | 1111 | 1111 | 1110 | **1110** | 1110 | yes |
| hhl_8 | 2319 | 2319 | 2319 | **2319** | 2319 | yes |
| heisenberg_32 | 881 | 881 | 881 | **881** | 881 | yes |
| grover_10 | 10895 | 10895 | 10895 | **10895** | 10895 | yes |
| hubbard_18 | 21769 | 21769 | 21766 | **21766** | 21766 | yes |

### Table 3 - Crosstalk-prone ECR pairs (same layer, neighbouring couplers) at optimal 2q-depth

| Circuit | Original | Lee'26 | JK'26 | MKCO (2q mode) | **MKCO-XT** | Reduction vs best baseline | 2q-depth orig -> XT | Total depth orig -> XT |
|---|---:|---:|---:|---:|---:|---:|---|---|
| mult_8 | 31 | 31 | 31 | 31 | **23** | -25.8% | 276 -> 276 | 1138 -> 1154 |
| add_17 | 151 | 151 | 151 | 151 | **144** | -4.6% | 253 -> 253 | 1003 -> 1019 |
| qae_17 | 165 | 165 | 165 | 165 | **138** | -16.4% | 274 -> 274 | 1066 -> 1075 |
| qft_16 | 210 | 210 | 210 | 210 | **195** | -7.1% | 260 -> 260 | 1009 -> 1027 |
| hubbard_8 | 166 | 166 | 167 | 167 | **130** | -21.7% | 1111 -> 1110 | 4400 -> 4415 |
| hhl_8 | 56 | 56 | 56 | 56 | **55** | -1.8% | 2319 -> 2319 | 10641 -> 10658 |
| heisenberg_32 | 1234 | 1234 | 1234 | 1234 | **1087** | -11.9% | 881 -> 881 | 7143 -> 7687 |
| grover_10 | 4431 | 4431 | 4431 | 4431 | **3870** | -12.7% | 10895 -> 10895 | 43923 -> 45858 |
| hubbard_18 | 7332 | 7332 | 7336 | 7334 | **5435** | -25.9% | 21769 -> 21766 | 136644 -> 137968 |

### Table 4 - Gate-rewriting modes: depth

Depth (lower is better). The inputs are already transpiled by Qiskit at optimization level 3, so the reference is the input itself; Lee'26 and JK'26 are reorder-only. MKCO-rewrite = single-qubit ZSX resynthesis + run merging + Max-k-Cut reordering; MKCO-full adds two-qubit KAK block resynthesis in the native ECR direction. Every MKCO result is certified optimal for the gate list it reorders.

| Circuit | Original | Lee'26 | JK'26 | MKCO (reorder) | MKCO-rewrite | **MKCO-full** | MKCO-full vs original |
|---|---:|---:|---:|---:|---:|---:|---:|
| mult_8 | 1138 | 1138 | **1102** | **1102** | **1102** | **1102** | -3.2% |
| add_17 | 1003 | 1003 | **964** | **964** | **964** | **964** | -3.9% |
| qae_17 | 1066 | 1066 | 1035 | 1035 | **1030** | **1030** | -3.4% |
| qft_16 | 1009 | 1009 | **980** | **980** | **980** | **980** | -2.9% |
| hubbard_8 | 4400 | 4400 | 4268 | 4268 | 4251 | **4241** | -3.6% |
| hhl_8 | 10641 | 10641 | **10434** | **10434** | **10434** | **10434** | -1.9% |
| heisenberg_32 | 7143 | 7143 | 7143 | 7143 | **3011** | **3011** | -57.8% |
| grover_10 | 43923 | 43923 | 41641 | 41641 | **41631** | **41631** | -5.2% |
| hubbard_18 | 136644 | 136644 | 136637 | 136637 | **72992** | **72992** | -46.6% |

**Hardware-time view.** MKCO-full (duration objective) keeps, per circuit, the candidate with the lowest estimated execution time among {KAK + 1q rewrite, 1q rewrite} x {reorder for depth, for 2q-depth}.

| Circuit | est. duration original (us) | MKCO-full, depth obj. (us) | **MKCO-full, duration obj. (us)** | vs original | 2q-depth orig / MKCO-dur | ECRs orig / MKCO-dur | depth orig / MKCO-dur | reversed ECRs |
|---|---:|---:|---:|---:|---|---|---|---|
| mult_8 | 159.89 | 158.69 | **158.69** | -0.8% | 276 / 276 | 311 / 311 | 1138 / 1102 | 0 |
| add_17 | 145.60 | 145.42 | **145.42** | -0.1% | 253 / 255 | 499 / 499 | 1003 / 964 | 0 |
| qae_17 | 157.37 | 156.44 | **156.44** | -0.6% | 274 / 274 | 541 / 541 | 1066 / 1030 | 0 |
| qft_16 | 149.12 | 148.23 | **148.23** | -0.6% | 260 / 260 | 614 / 614 | 1009 / 980 | 0 |
| hubbard_8 | 638.05 | 633.96 | **633.96** | -0.6% | 1111 / 1111 | 1344 / 1344 | 4400 / 4241 | 0 |
| hhl_8 | 1365.41 | 1359.51 | **1359.51** | -0.4% | 2319 / 2319 | 2377 / 2377 | 10641 / 10434 | 0 |
| heisenberg_32 | 549.16 | 499.95 | **499.95** | -9.0% | 881 / 881 | 3942 / 3942 | 7143 / 3011 | 0 |
| grover_10 | 6292.61 | 6220.96 | **6220.96** | -1.1% | 10895 / 10895 | 16397 / 16397 | 43923 / 41631 | 0 |
| hubbard_18 | 13230.21 | 12313.54 | **10891.42** | -17.7% | 21769 / 18795 | 33958 / 30453 | 136644 / 80677 | 0 |

### Table 5 - Estimated execution time (us; ECR 533 ns, sx/x 36 ns, rz virtual)

| Circuit | Original | Lee'26 | JK'26 | MKCO (depth) | MKCO (2q) | MKCO-XT |
|---|---:|---:|---:|---:|---:|---:|
| mult_8 | 159.89 | 159.89 | 158.69 | 158.69 | 159.89 | 160.39 |
| add_17 | 145.60 | 145.60 | 145.42 | 145.42 | 145.56 | 145.74 |
| qae_17 | 157.37 | 157.37 | 156.52 | 156.52 | 157.37 | 157.51 |
| qft_16 | 149.12 | 149.12 | 148.23 | 148.23 | 149.08 | 149.37 |
| hubbard_8 | 638.05 | 638.05 | 634.95 | 634.95 | 637.12 | 637.55 |
| hhl_8 | 1365.41 | 1365.41 | 1359.51 | 1359.51 | 1365.41 | 1365.77 |
| heisenberg_32 | 549.16 | 549.16 | 549.16 | 549.16 | 549.16 | 552.58 |
| grover_10 | 6292.61 | 6292.61 | 6221.17 | 6221.17 | 6292.61 | 6347.09 |
| hubbard_18 | 13230.21 | 13230.21 | 13228.79 | 13187.43 | 13228.57 | 13256.92 |

### Table 6 - Runtime (s)

| Circuit | Lee'26 | JK'26 | MKCO | MKCO-2q | MKCO-XT | MKCO-full |
|---|---:|---:|---:|---:|---:|---:|
| mult_8 | 0.3 | 0.2 | 0.1 | 0.1 | 4.4 | 3.7 |
| add_17 | 0.5 | 0.2 | 0.2 | 0.2 | 23.6 | 1.3 |
| qae_17 | 0.5 | 0.2 | 0.2 | 0.1 | 21.0 | 3.6 |
| qft_16 | 0.5 | 0.2 | 0.2 | 0.1 | 30.1 | 7.5 |
| hubbard_8 | 1.3 | 1.3 | 0.7 | 0.3 | 30.2 | 17.1 |
| hhl_8 | 2.8 | 6.2 | 1.1 | 0.7 | 30.1 | 14.5 |
| heisenberg_32 | 8.4 | 1.6 | 3.6 | 1.9 | 60.5 | 49.5 |
| grover_10 | 14.3 | 3.1 | 5.7 | 3.7 | 60.9 | 90.5 |
| hubbard_18 | 44.0 | 11.0 | 19.9 | 11.8 | 62.5 | 378.1 |

### Table 7 - Verification of every reordered output

| Circuit | Active qubits | Commutation audit (all reorderings) | Inverted pairs checked (MKCO) | State-vector check (MKCO) | State-vector (MKCO-rewrite, vs original) | State-vector (MKCO-full dur., vs original) |
|---|---:|:---:|---:|:---:|:---:|:---:|
| mult_8 | 8 | 11/11 pass | 75 | pass (F=1.0000000000) | pass (F=1.0000000000) | pass (F=1.0000000000) |
| add_17 | 17 | 11/11 pass | 129 | pass (F=1.0000000000) | pass (F=1.0000000000) | pass (F=1.0000000000) |
| qae_17 | 17 | 11/11 pass | 142 | pass (F=1.0000000000) | pass (F=1.0000000000) | pass (F=1.0000000000) |
| qft_16 | 16 | 11/11 pass | 166 | pass (F=1.0000000000) | pass (F=1.0000000000) | pass (F=1.0000000000) |
| hubbard_8 | 8 | 11/11 pass | 260 | pass (F=1.0000000000) | pass (F=1.0000000000) | pass (F=1.0000000000) |
| hhl_8 | 8 | 11/11 pass | 333 | pass (F=1.0000000000) | pass (F=1.0000000000) | pass (F=1.0000000000) |
| heisenberg_32 | 32 | 11/11 pass | 0 | n/a (>20 qubits) | n/a (>20 qubits) | n/a (>20 qubits) |
| grover_10 | 10 | 11/11 pass | 14222 | pass (F=1.0000000000) | pass (F=1.0000000000) | pass (F=1.0000000000) |
| hubbard_18 | 31 | 11/11 pass | 2654 | n/a (>20 qubits) | n/a (>20 qubits) | n/a (>20 qubits) |

### Table 8 - Two-qubit block (KAK) resynthesis: blocks that become cheaper in native ECRs

| Circuit | two-qubit blocks | cheaper after KAK | ECRs removed |
|---|---:|---:|---:|
| mult_8 | 151 | 0 | 0 |
| add_17 | 198 | 0 | 0 |
| qae_17 | 213 | 0 | 0 |
| qft_16 | 237 | 0 | 0 |
| hubbard_8 | 695 | 1 | 0 |
| hhl_8 | 1433 | 1 | 0 |
| heisenberg_32 | 1594 | 1073 | 60 |
| grover_10 | 8387 | 58 | 0 |
| hubbard_18 | 12823 | 4856 | 3505 |

### Table 9 - Depth budget vs crosstalk (weighted Max-k-Cut with k = k* + slack)

| Circuit | slack (% of k*) | 2q-depth | crosstalk-prone pairs | vs original | est. duration (us) |
|---|---:|---:|---:|---:|---:|
| mult_8 | 0 | 276 | 23 | -25.8% | 160.39 |
| mult_8 | 1 | 278 | 21 | -32.3% | 161.67 |
| mult_8 | 2 | 278 | 22 | -29.0% | 161.57 |
| mult_8 | 5 | 277 | 24 | -22.6% | 161.00 |
| mult_8 | 10 | 283 | 19 | -38.7% | 164.37 |
| mult_8 | 20 | 291 | 11 | -64.5% | 168.96 |
| add_17 | 0 | 253 | 144 | -4.6% | 145.74 |
| add_17 | 1 | 256 | 141 | -6.6% | 147.41 |
| add_17 | 2 | 257 | 140 | -7.3% | 147.95 |
| add_17 | 5 | 261 | 128 | -15.2% | 150.51 |
| add_17 | 10 | 270 | 117 | -22.5% | 155.66 |
| add_17 | 20 | 288 | 87 | -42.4% | 165.65 |
| qae_17 | 0 | 274 | 138 | -16.4% | 157.51 |
| qae_17 | 1 | 276 | 133 | -19.4% | 158.76 |
| qae_17 | 2 | 277 | 131 | -20.6% | 159.29 |
| qae_17 | 5 | 282 | 124 | -24.8% | 162.10 |
| qae_17 | 10 | 289 | 113 | -31.5% | 166.04 |
| qae_17 | 20 | 307 | 85 | -48.5% | 176.46 |
| qft_16 | 0 | 260 | 195 | -7.1% | 149.37 |
| qft_16 | 1 | 262 | 193 | -8.1% | 150.36 |
| qft_16 | 2 | 264 | 185 | -11.9% | 151.50 |
| qft_16 | 5 | 269 | 173 | -17.6% | 154.74 |
| qft_16 | 10 | 281 | 162 | -22.9% | 161.53 |
| qft_16 | 20 | 309 | 102 | -51.4% | 177.53 |
| hubbard_8 | 0 | 1110 | 130 | -21.7% | 637.55 |
| hubbard_8 | 1 | 1113 | 127 | -23.5% | 639.47 |
| hubbard_8 | 2 | 1121 | 120 | -27.7% | 643.77 |
| hubbard_8 | 5 | 1123 | 119 | -28.3% | 645.12 |
| hubbard_8 | 10 | 1153 | 93 | -44.0% | 662.22 |
| hubbard_8 | 20 | 1189 | 58 | -65.1% | 683.27 |
| hhl_8 | 0 | 2319 | 55 | -1.8% | 1365.77 |
| hhl_8 | 1 | 2320 | 54 | -3.6% | 1366.30 |
| hhl_8 | 2 | 2323 | 51 | -8.9% | 1368.01 |
| hhl_8 | 5 | 2323 | 51 | -8.9% | 1367.97 |
| hhl_8 | 10 | 2330 | 44 | -21.4% | 1372.24 |
| hhl_8 | 20 | 2339 | 34 | -39.3% | 1377.32 |

### Table 10 - Noise study with device calibration snapshots (fake_brisbane)

ESP = estimated success probability (state-blind, ALAP idling); sESP = state-aware ESP (idle gaps weighted by the idling qubit's state, <= 22 active qubits); sim = exact density-matrix state fidelity (<= 8 active qubits). Scale 0.1 = all error rates x0.1 and T1, T2 x10. mkco_noise = the MKCO candidate with the best sESP (ESP for larger circuits), the input included.

| Circuit | score | original | jk2026 | mkco | mkco_alap | mkco_full | mkco_full_alap | mkco_noise | mkco_noise picks |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| mult_8 | ESP | 0.00283 | 0.0029 | 0.0029 | **0.0029** | 0.0029 | 0.0029 | 0.00283 | original |
| mult_8 | ESP_xt | 0.00232 | 0.00234 | 0.00234 | **0.00234** | 0.00234 | 0.00234 | 0.00232 |  |
| mult_8 | ESP x0.1 | 0.526 | 0.529 | 0.529 | **0.529** | 0.529 | 0.529 | 0.526 |  |
| mult_8 | sESP | **0.00222** | 0.00141 | 0.00141 | 0.0015 | 0.00141 | 0.00141 | **0.00222** |  |
| mult_8 | sESP x0.1 | **0.543** | 0.519 | 0.519 | 0.522 | 0.519 | 0.519 | **0.543** |  |
| mult_8 | sim F | **0.0155** | 0.0126 | 0.0126 | 0.0128 | 0.0126 | 0.0126 | **0.0155** |  |
| mult_8 | sim F x0.1 | **0.567** | 0.542 | 0.542 | 0.545 | 0.542 | 0.542 | **0.567** |  |
| add_17 | ESP | 1.41e-07 | 1.37e-07 | 1.37e-07 | **1.44e-07** | 1.37e-07 | **1.44e-07** | **1.44e-07** | mkco_full_alap |
| add_17 | ESP_xt | 3.51e-08 | 3.02e-08 | 3.00e-08 | **3.58e-08** | 3.00e-08 | **3.58e-08** | **3.58e-08** |  |
| add_17 | ESP x0.1 | 0.171 | 0.171 | 0.171 | **0.172** | 0.171 | **0.172** | **0.172** |  |
| add_17 | sESP | 1.07e-08 | 1.14e-08 | 1.14e-08 | 1.27e-08 | 1.14e-08 | **1.27e-08** | **1.27e-08** |  |
| add_17 | sESP x0.1 | 0.147 | 0.148 | 0.148 | **0.149** | 0.148 | **0.149** | **0.149** |  |
| qae_17 | ESP | 3.66e-05 | 3.78e-05 | 3.78e-05 | 3.73e-05 | 3.79e-05 | **3.79e-05** | **3.79e-05** | mkco_full_alap |
| qae_17 | ESP_xt | **1.21e-05** | 1.14e-05 | 1.13e-05 | 1.13e-05 | 1.13e-05 | 1.13e-05 | 1.13e-05 |  |
| qae_17 | ESP x0.1 | 0.279 | 0.281 | 0.281 | 0.28 | 0.281 | **0.281** | **0.281** |  |
| qae_17 | sESP | 1.18e-07 | 1.30e-07 | 1.30e-07 | 1.27e-07 | 1.34e-07 | **1.34e-07** | **1.34e-07** |  |
| qae_17 | sESP x0.1 | 0.194 | 0.196 | 0.196 | 0.196 | 0.197 | **0.197** | **0.197** |  |
| qft_16 | ESP | 5.26e-05 | 5.46e-05 | 5.46e-05 | 5.45e-05 | **5.47e-05** | 5.47e-05 | 5.45e-05 | mkco_alap |
| qft_16 | ESP_xt | **9.81e-06** | 9.22e-06 | 9.07e-06 | 9.06e-06 | 9.09e-06 | 9.09e-06 | 9.06e-06 |  |
| qft_16 | ESP x0.1 | 0.316 | 0.318 | 0.318 | 0.318 | **0.318** | **0.318** | 0.318 |  |
| qft_16 | sESP | 1.10e-05 | 1.28e-05 | 1.28e-05 | **1.29e-05** | 1.29e-05 | 1.29e-05 | **1.29e-05** |  |
| qft_16 | sESP x0.1 | 0.311 | 0.316 | 0.316 | 0.316 | 0.316 | **0.316** | 0.316 |  |
| hubbard_8 | ESP | 5.09e-09 | 5.17e-09 | 5.17e-09 | 5.17e-09 | 5.22e-09 | **5.22e-09** | **5.22e-09** | mkco_full_alap |
| hubbard_8 | ESP_xt | **1.39e-09** | 1.32e-09 | 1.32e-09 | 1.34e-09 | 1.32e-09 | 1.35e-09 | 1.35e-09 |  |
| hubbard_8 | ESP x0.1 | 0.0839 | 0.0848 | 0.0848 | 0.0848 | 0.085 | **0.085** | **0.085** |  |
| hubbard_8 | sESP | 8.14e-13 | 4.30e-13 | 4.30e-13 | 1.00e-12 | 4.55e-13 | **1.06e-12** | **1.06e-12** |  |
| hubbard_8 | sESP x0.1 | 0.0618 | 0.0582 | 0.0582 | 0.0631 | 0.0586 | **0.0634** | **0.0634** |  |
| hubbard_8 | sim F | **0.00283** | 0.00252 | 0.00252 | 0.0028 | 0.00253 | 0.0028 | 0.0028 |  |
| hubbard_8 | sim F x0.1 | 0.0751 | 0.0702 | 0.0702 | 0.0764 | 0.0706 | **0.0767** | **0.0767** |  |
| hhl_8 | ESP | 8.57e-21 | 8.60e-21 | 8.60e-21 | 8.60e-21 | **8.61e-21** | 8.61e-21 | **8.61e-21** | mkco_full |
| hhl_8 | ESP_xt | **5.35e-21** | 5.29e-21 | 5.29e-21 | 5.34e-21 | 5.30e-21 | 5.30e-21 | 5.30e-21 |  |
| hhl_8 | ESP x0.1 | 0.00256 | 0.00259 | 0.00259 | **0.0026** | 0.00259 | 0.00259 | 0.00259 |  |
| hhl_8 | sESP | 4.10e-28 | 7.76e-28 | 7.77e-28 | 2.47e-28 | **7.78e-28** | **7.78e-28** | **7.78e-28** |  |
| hhl_8 | sESP x0.1 | 9.54e-04 | 0.00102 | 0.00102 | 9.23e-04 | **0.00102** | **0.00102** | **0.00102** |  |
| hhl_8 | sim F | 0.0056 | 0.00762 | 0.00762 | 0.00741 | 0.00762 | **0.00762** | 0.00762 |  |
| hhl_8 | sim F x0.1 | 0.0123 | 0.0138 | 0.0138 | 0.0126 | 0.0138 | **0.0138** | 0.0138 |  |
| heisenberg_32 | ESP | 7.47e-35 | 7.47e-35 | 7.47e-35 | 7.47e-35 | 6.84e-33 | **6.84e-33** | **6.84e-33** | mkco_full_alap |
| heisenberg_32 | ESP_xt | 7.52e-41 | 7.52e-41 | 7.52e-41 | 7.52e-41 | 3.84e-38 | **3.84e-38** | **3.84e-38** |  |
| heisenberg_32 | ESP x0.1 | 3.37e-05 | 3.37e-05 | 3.37e-05 | 3.37e-05 | 7.24e-05 | **7.24e-05** | **7.24e-05** |  |
| heisenberg_32 | sESP | – | – | – | – | – | – | – |  |
| heisenberg_32 | sESP x0.1 | – | – | – | – | – | – | – |  |
| grover_10 | ESP | 8.41e-90 | 8.42e-90 | 8.42e-90 | 8.42e-90 | 9.43e-90 | **9.43e-90** | **9.43e-90** | mkco_full_alap |
| grover_10 | ESP_xt | **1.28e-106** | 4.14e-108 | 4.14e-108 | 3.60e-108 | 4.64e-108 | 4.64e-108 | 4.64e-108 |  |
| grover_10 | ESP x0.1 | 9.12e-12 | 9.58e-12 | 9.58e-12 | 9.59e-12 | **9.68e-12** | 9.68e-12 | 9.68e-12 |  |
| grover_10 | sESP | 9.94e-151 | 8.87e-145 | 8.75e-145 | 3.69e-149 | 9.38e-145 | **9.38e-145** | **9.38e-145** |  |
| grover_10 | sESP x0.1 | 1.98e-16 | 9.31e-16 | 9.30e-16 | 2.96e-16 | 9.36e-16 | **9.36e-16** | **9.36e-16** |  |
| hubbard_18 | ESP | 1.22e-177 | 1.22e-177 | 1.22e-177 | 1.22e-177 | 1.79e-169 | 1.79e-169 | **2.70e-155** | mkco_full_dur |
| hubbard_18 | ESP_xt | 1.36e-204 | 1.33e-204 | 2.02e-204 | 8.99e-205 | 4.15e-195 | 4.15e-195 | **9.82e-182** |  |
| hubbard_18 | ESP x0.1 | 1.16e-26 | 1.16e-26 | 1.16e-26 | 1.16e-26 | 8.17e-26 | 8.17e-26 | **2.38e-24** |  |
| hubbard_18 | sESP | – | – | – | – | – | – | – |  |
| hubbard_18 | sESP x0.1 | – | – | – | – | – | – | – |  |

### Table 11 - ECRs removed by block KAK, plain vs commutation-aware block formation

| Circuit | input ECRs | removed by plain block KAK | removed by regrouped block KAK |
|---|---:|---:|---:|
| add_17 | 499 | 0 | 0 |
| grover_10 | 16397 | 0 | 0 |
| heisenberg_32 | 3942 | 60 | 60 |
| hhl_8 | 2377 | 0 | 0 |
| hubbard_18 | 33958 | 3505 | 3505 |
| hubbard_8 | 1344 | 0 | 4 |
| mult_8 | 311 | 0 | 0 |
| qae_17 | 541 | 0 | 0 |
| qft_16 | 614 | 0 | 0 |

### Table 12 - Noisy simulated backend: Aer + the circuits' device calibrations, sampled counts

Hellinger fidelity of 512 or 32768 shots against the ideal output [bootstrap 95% interval]. Noise model: Aer's NoiseModel.from_backend (independent of mkco.noise); Qiskit's ALAP scheduling; methods interleaved in one job per run. mkco_noise is the same circuit as the method it selects (a repeat measurement). Predictions at scale 0.1: mkco.noise density-matrix Hellinger fidelity (<= 8 qubits) and state-aware ESP. The 17-qubit circuits are run at scale 0.1 only (at scale 1 they are at the noise floor).

| Circuit | method | scale 1 | scale 0.1 | predicted (DM, x0.1) | sESP x0.1 |
|---|---|---:|---:|---:|---:|
| mult_8 | original | 0.0135 [0.0122, 0.0148] | 0.5461 [0.5404, 0.5512] | 0.5505 | 0.5433 |
| mult_8 | mkco | 0.0109 [0.0098, 0.0119] | 0.5128 [0.5073, 0.5179] | 0.5265 | 0.5189 |
| mult_8 | mkco_alap | 0.0110 [0.0099, 0.0121] | 0.5215 [0.5167, 0.5266] | 0.5298 | 0.5220 |
| mult_8 | mkco_full | 0.0111 [0.0100, 0.0123] | 0.5148 [0.5092, 0.5203] | 0.5266 | 0.5189 |
| mult_8 | mkco_full_alap | 0.0112 [0.0101, 0.0123] | 0.5131 [0.5076, 0.5188] | 0.5266 | 0.5189 |
| mult_8 | mkco_noise (= original) | 0.0128 [0.0116, 0.0140] | 0.5475 [0.5423, 0.5529] | 0.5505 | 0.5433 |
| add_17 | original | – | 0.1680 [0.1348, 0.2012] | – | 0.1468 |
| add_17 | mkco | – | 0.1484 [0.1191, 0.1777] | – | 0.1478 |
| add_17 | mkco_noise (= mkco_full_alap) | – | 0.1270 [0.0996, 0.1563] | – | 0.1494 |
| qae_17 | original | – | 0.2799 [0.2245, 0.3051] | – | 0.1942 |
| qae_17 | mkco | – | 0.3053 [0.2532, 0.3301] | – | 0.1963 |
| qae_17 | mkco_noise (= mkco_full_alap) | – | 0.3525 [0.2960, 0.3752] | – | 0.1969 |
| hubbard_8 | original | 0.0040 [0.0034, 0.0046] | 0.0695 [0.0667, 0.0721] | 0.0808 | 0.0618 |
| hubbard_8 | mkco | 0.0032 [0.0025, 0.0038] | 0.0647 [0.0620, 0.0673] | 0.0757 | 0.0582 |
| hubbard_8 | mkco_alap | 0.0039 [0.0032, 0.0046] | 0.0732 [0.0703, 0.0758] | 0.0820 | 0.0631 |
| hubbard_8 | mkco_full | 0.0033 [0.0027, 0.0039] | 0.0677 [0.0650, 0.0704] | 0.0760 | 0.0586 |
| hubbard_8 | mkco_full_alap | 0.0048 [0.0040, 0.0055] | 0.0740 [0.0712, 0.0770] | 0.0823 | 0.0634 |
| hubbard_8 | mkco_noise (= mkco_full_alap) | 0.0037 [0.0031, 0.0043] | 0.0732 [0.0703, 0.0761] | 0.0823 | 0.0634 |
| hhl_8 | original | 0.0630 [0.0605, 0.0654] | 0.0719 [0.0689, 0.0746] | 0.0722 | 0.0010 |
| hhl_8 | mkco | 0.0627 [0.0598, 0.0651] | 0.0717 [0.0688, 0.0743] | 0.0738 | 0.0010 |
| hhl_8 | mkco_alap | 0.0657 [0.0631, 0.0683] | 0.0731 [0.0702, 0.0760] | 0.0735 | 0.0009 |
| hhl_8 | mkco_full | 0.0661 [0.0635, 0.0687] | 0.0746 [0.0717, 0.0774] | 0.0738 | 0.0010 |
| hhl_8 | mkco_full_alap | 0.0647 [0.0619, 0.0672] | 0.0747 [0.0717, 0.0775] | 0.0738 | 0.0010 |
| hhl_8 | mkco_noise (= mkco_full) | 0.0626 [0.0597, 0.0652] | 0.0721 [0.0692, 0.0749] | 0.0738 | 0.0010 |

Scale 1: on the method pairs that sampling separates (non-overlapping intervals), the predictions order density-matrix model 4/4, state-aware ESP 4/4, ESP 2/4 correctly.

Scale 0.1: on the method pairs that sampling separates (non-overlapping intervals), the predictions order density-matrix model 7/7, state-aware ESP 7/7, ESP 3/7 correctly.

### 5.1 Second benchmark set

Four more IBM-127-transpiled circuits were run through the same pipeline
with the same settings (`experiments/run_set2.py`, results in
`results/ibm127_set2`):
- heisenberg_8, qpe_8 and tfim_8, native to ibm_brisbane;
- tfim_7_40, native to ibm_cusco: all its ECR directions match that snapshot,
  and only 80 of 714 match ibm_brisbane.

They have 7–8 active qubits and 1.5k–4.3k gates, and two of them end in
measurements. The set's grover_10 is byte-identical to the set-1 benchmark,
so its results are those of set 1.

- **Reordering.** MKCO is certified optimal on all four for total depth
  (−0.5% to −3.0%; Set 2 Table 1) and for two-qubit depth (Set 2 Table 2),
  where the inputs were already optimal. Lee et al. gains nothing; Jain &
  Kumar reaches the same depths without a certificate.
- **Gate rewriting.** MKCO-full is 0.5–3.1% shallower than the transpiled
  input and 0.1–1.1% faster in estimated time. KAK finds no cheaper two-qubit
  block in any of these circuits (Set 2 Table 8).
- **Crosstalk.** At the optimal two-qubit depth only qpe_8 has room
  (−13.6%). With a 20% two-qubit-depth budget, the weighted Max-k-Cut removes
  34–38% of the crosstalk-prone pairs on all four (Set 2 Table 9).
- **Noise (Set 2 Table 10).** All four circuits are small enough for exact
  density-matrix simulation, each with the calibration of its own device. At
  10× lower noise:
  - qpe_8: MKCO's orders are 4.3% more faithful than the input
    (0.0968 vs 0.0928);
  - heisenberg_8: +0.3% (0.3775 vs 0.3762);
  - tfim_8: all methods within 0.3% (0.469–0.470), and `mkco_noise` keeps the
    input order;
  - tfim_7_40: close to the noise floor (1/128 ≈ 0.008). MKCO-full is best
    (0.0139 vs 0.0136); the state-aware pick, plain MKCO, scores 0.0137.

  Across all method pairs, the state-aware ESP orders the pair as the
  simulation does in 90% of cases at 10× lower noise (78% at calibrated
  noise), against 80% (64%) for the state-blind ESP.
- **Noisy simulated backend (Set 2 Table 12).** Aer ran each circuit with
  its own device noise model, 32,768 shots, at both noise levels.
  - **qpe_8 is the clear case.** At 10× lower noise every MKCO order
    (0.701–0.707) beats the input (0.679), with separated intervals, as the
    density-matrix model predicted (+4%). At calibrated noise the MKCO outputs
    score 0.34, the level of pure noise for this distribution, while the input
    falls to 0.24.
  - **heisenberg_8 and tfim_8** differ by less than the sampling spread. The
    same circuit measured twice differs by up to 0.006.
  - **tfim_7_40's counts carry no information.** Its ideal output is so broad
    that uniform noise already scores 0.479, about where every method lands.
  - **Agreement.** On the pairs that sampling separates, the density-matrix
    model, the state-aware ESP and the state-blind ESP all order the pair
    correctly: 6/6 at calibrated noise, 4/4 at 10× lower noise. In this set
    the shorter MKCO orders are also the more faithful ones, so even the
    state-blind estimate ranks them correctly.
- **A bug these circuits exposed, now fixed.** With final measurements in the
  circuit, the two-qubit model counted each measurement (one qubit plus one
  classical bit) as a two-wire layer. The bound was then for depth *including*
  the measurement layer, one more than the reported two-qubit depth (131 vs
  130 on heisenberg_8), so the table showed a bound above an achieved value.
  Measurements are now zero-duration in the two-qubit model, as in Qiskit's
  two-qubit depth, unless some gate is classically conditioned. A regression
  test covers it. The set-1 circuits have no measurements and are unaffected.

#### Set 2 - Table 1 - Total depth, reorder-only methods (lower is better)

| Circuit | Gates | Original | Lee'26 (colouring) | JK'26 (MIS+beam) | **MKCO** | Certified LB | MKCO optimal? | MKCO vs original |
|---|---:|---:|---:|---:|---:|---:|:---:|---:|
| tfim_8 | 1527 | 388 | 388 | 386 | **386** | 386 | yes | -0.52% |
| heisenberg_8 | 2135 | 530 | 530 | 527 | **527** | 527 | yes | -0.57% |
| qpe_8 | 3161 | 1930 | 1930 | 1889 | **1889** | 1889 | yes | -2.12% |
| tfim_7_40 | 4288 | 1560 | 1560 | 1514 | **1514** | 1514 | yes | -2.95% |

#### Set 2 - Table 2 - Two-qubit (ECR) depth, reorder-only methods optimising 2q-depth

| Circuit | Original | Lee'26 | JK'26 | **MKCO** | Certified LB | MKCO optimal? |
|---|---:|---:|---:|---:|---:|:---:|
| tfim_8 | 90 | 90 | 90 | **90** | 90 | yes |
| heisenberg_8 | 130 | 130 | 130 | **130** | 130 | yes |
| qpe_8 | 452 | 452 | 452 | **452** | 452 | yes |
| tfim_7_40 | 368 | 368 | 368 | **368** | 368 | yes |

#### Set 2 - Table 3 - Crosstalk-prone ECR pairs (same layer, neighbouring couplers) at optimal 2q-depth

| Circuit | Original | Lee'26 | JK'26 | MKCO (2q mode) | **MKCO-XT** | Reduction vs best baseline | 2q-depth orig -> XT | Total depth orig -> XT |
|---|---:|---:|---:|---:|---:|---:|---|---|
| tfim_8 | 190 | 190 | 190 | 190 | **190** | +0.0% | 90 -> 90 | 388 -> 389 |
| heisenberg_8 | 290 | 290 | 290 | 290 | **290** | +0.0% | 130 -> 130 | 530 -> 541 |
| qpe_8 | 22 | 22 | 22 | 22 | **19** | -13.6% | 452 -> 452 | 1930 -> 1934 |
| tfim_7_40 | 156 | 156 | 156 | 156 | **156** | +0.0% | 368 -> 368 | 1560 -> 1587 |

#### Set 2 - Table 4 - Gate-rewriting modes: depth

Depth (lower is better). The inputs are already transpiled by Qiskit at optimization level 3, so the reference is the input itself; Lee'26 and JK'26 are reorder-only. MKCO-rewrite = single-qubit ZSX resynthesis + run merging + Max-k-Cut reordering; MKCO-full adds two-qubit KAK block resynthesis in the native ECR direction. Every MKCO result is certified optimal for the gate list it reorders.

| Circuit | Original | Lee'26 | JK'26 | MKCO (reorder) | MKCO-rewrite | **MKCO-full** | MKCO-full vs original |
|---|---:|---:|---:|---:|---:|---:|---:|
| tfim_8 | 388 | 388 | **386** | **386** | **386** | **386** | -0.5% |
| heisenberg_8 | 530 | 530 | **527** | **527** | **527** | **527** | -0.6% |
| qpe_8 | 1930 | 1930 | **1889** | **1889** | **1889** | **1889** | -2.1% |
| tfim_7_40 | 1560 | 1560 | 1514 | 1514 | **1512** | **1512** | -3.1% |

**Hardware-time view.** MKCO-full (duration objective) keeps, per circuit, the candidate with the lowest estimated execution time among {KAK + 1q rewrite, 1q rewrite} x {reorder for depth, for 2q-depth}.

| Circuit | est. duration original (us) | MKCO-full, depth obj. (us) | **MKCO-full, duration obj. (us)** | vs original | 2q-depth orig / MKCO-dur | ECRs orig / MKCO-dur | depth orig / MKCO-dur | reversed ECRs |
|---|---:|---:|---:|---:|---|---|---|---|
| tfim_8 | 53.05 | 52.98 | **52.98** | -0.1% | 90 / 90 | 280 / 280 | 388 / 386 | 0 |
| heisenberg_8 | 76.23 | 75.80 | **75.80** | -0.6% | 130 / 130 | 420 / 420 | 530 / 527 | 0 |
| qpe_8 | 261.83 | 260.45 | **260.45** | -0.5% | 452 / 452 | 484 / 484 | 1930 / 1889 | 0 |
| tfim_7_40 | 215.08 | 212.62 | **212.62** | -1.1% | 368 / 368 | 714 / 714 | 1560 / 1512 | 0 |

#### Set 2 - Table 5 - Estimated execution time (us; ECR 533 ns, sx/x 36 ns, rz virtual)

| Circuit | Original | Lee'26 | JK'26 | MKCO (depth) | MKCO (2q) | MKCO-XT |
|---|---:|---:|---:|---:|---:|---:|
| tfim_8 | 53.05 | 53.05 | 52.98 | 52.98 | 53.05 | 53.40 |
| heisenberg_8 | 76.23 | 76.23 | 75.80 | 75.80 | 76.23 | 76.94 |
| qpe_8 | 261.83 | 261.83 | 260.45 | 260.45 | 261.83 | 261.97 |
| tfim_7_40 | 215.08 | 215.08 | 212.87 | 212.73 | 215.08 | 216.11 |

#### Set 2 - Table 6 - Runtime (s)

| Circuit | Lee'26 | JK'26 | MKCO | MKCO-2q | MKCO-XT | MKCO-full |
|---|---:|---:|---:|---:|---:|---:|
| tfim_8 | 0.2 | 0.1 | 0.1 | 0.1 | 0.0 | 0.5 |
| heisenberg_8 | 0.3 | 0.1 | 0.1 | 0.1 | 0.0 | 0.7 |
| qpe_8 | 0.5 | 0.3 | 0.2 | 0.1 | 3.9 | 1.0 |
| tfim_7_40 | 0.8 | 0.3 | 0.4 | 0.2 | 0.1 | 9.3 |

#### Set 2 - Table 7 - Verification of every reordered output

| Circuit | Active qubits | Commutation audit (all reorderings) | Inverted pairs checked (MKCO) | State-vector check (MKCO) | State-vector (MKCO-rewrite, vs original) | State-vector (MKCO-full dur., vs original) |
|---|---:|:---:|---:|:---:|:---:|:---:|
| tfim_8 | 8 | 11/11 pass | 159 | pass (F=1.0000000000) | pass (F=1.0000000000) | pass (F=1.0000000000) |
| heisenberg_8 | 8 | 11/11 pass | 238 | pass (F=1.0000000000) | pass (F=1.0000000000) | pass (F=1.0000000000) |
| qpe_8 | 8 | 11/11 pass | 83 | pass (F=1.0000000000) | pass (F=1.0000000000) | pass (F=1.0000000000) |
| tfim_7_40 | 7 | 11/11 pass | 274 | pass (F=1.0000000000) | pass (F=1.0000000000) | pass (F=1.0000000000) |

#### Set 2 - Table 8 - Two-qubit block (KAK) resynthesis: blocks that become cheaper in native ECRs

| Circuit | two-qubit blocks | cheaper after KAK | ECRs removed |
|---|---:|---:|---:|
| tfim_8 | 140 | 0 | 0 |
| heisenberg_8 | 210 | 0 | 0 |
| qpe_8 | 256 | 0 | 0 |
| tfim_7_40 | 318 | 0 | 0 |

#### Set 2 - Table 9 - Depth budget vs crosstalk (weighted Max-k-Cut with k = k* + slack)

| Circuit | slack (% of k*) | 2q-depth | crosstalk-prone pairs | vs original | est. duration (us) |
|---|---:|---:|---:|---:|---:|
| heisenberg_8 | 0 | 130 | 290 | +0.0% | 76.94 |
| heisenberg_8 | 1 | 131 | 286 | -1.4% | 77.51 |
| heisenberg_8 | 2 | 133 | 278 | -4.1% | 78.61 |
| heisenberg_8 | 5 | 136 | 264 | -9.0% | 80.28 |
| heisenberg_8 | 10 | 143 | 238 | -17.9% | 83.88 |
| heisenberg_8 | 20 | 154 | 192 | -33.8% | 90.20 |
| qpe_8 | 0 | 452 | 19 | -13.6% | 261.97 |
| qpe_8 | 1 | 452 | 19 | -13.6% | 261.97 |
| qpe_8 | 2 | 452 | 19 | -13.6% | 261.97 |
| qpe_8 | 5 | 453 | 18 | -18.2% | 262.54 |
| qpe_8 | 10 | 455 | 16 | -27.3% | 263.75 |
| qpe_8 | 20 | 456 | 14 | -36.4% | 264.36 |
| tfim_7_40 | 0 | 368 | 156 | +0.0% | 216.11 |
| tfim_7_40 | 1 | 372 | 150 | -3.8% | 218.49 |
| tfim_7_40 | 2 | 370 | 153 | -1.9% | 217.32 |
| tfim_7_40 | 5 | 378 | 136 | -12.8% | 222.08 |
| tfim_7_40 | 10 | 386 | 126 | -19.2% | 226.70 |
| tfim_7_40 | 20 | 402 | 97 | -37.8% | 235.95 |
| tfim_8 | 0 | 90 | 190 | +0.0% | 53.40 |
| tfim_8 | 1 | 91 | 187 | -1.6% | 54.04 |
| tfim_8 | 2 | 92 | 182 | -4.2% | 54.58 |
| tfim_8 | 5 | 94 | 172 | -9.5% | 55.61 |
| tfim_8 | 10 | 99 | 150 | -21.1% | 58.52 |
| tfim_8 | 20 | 106 | 120 | -36.8% | 62.72 |

#### Set 2 - Table 10 - Noise study with device calibration snapshots (fake_brisbane, fake_cusco)

ESP = estimated success probability (state-blind, ALAP idling); sESP = state-aware ESP (idle gaps weighted by the idling qubit's state, <= 22 active qubits); sim = exact density-matrix state fidelity (<= 8 active qubits). Scale 0.1 = all error rates x0.1 and T1, T2 x10. mkco_noise = the MKCO candidate with the best sESP (ESP for larger circuits), the input included.

| Circuit | score | original | jk2026 | mkco | mkco_alap | mkco_full | mkco_full_alap | mkco_noise | mkco_noise picks |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| tfim_8 | ESP | 7.88e-04 | **7.91e-04** | **7.91e-04** | 7.79e-04 | **7.91e-04** | 7.91e-04 | 7.88e-04 | original |
| tfim_8 | ESP_xt | **1.81e-04** | 1.54e-04 | 1.56e-04 | 1.61e-04 | 1.56e-04 | 1.56e-04 | **1.81e-04** |  |
| tfim_8 | ESP x0.1 | 0.495 | 0.495 | **0.495** | 0.494 | **0.495** | **0.495** | 0.495 |  |
| tfim_8 | sESP | **7.04e-04** | 7.00e-04 | 7.00e-04 | 6.85e-04 | 7.00e-04 | 7.00e-04 | **7.04e-04** |  |
| tfim_8 | sESP x0.1 | **0.49** | 0.49 | 0.49 | 0.489 | 0.49 | 0.49 | **0.49** |  |
| tfim_8 | sim F | **0.00778** | 0.00766 | 0.00767 | 0.00761 | 0.00767 | 0.00767 | **0.00778** |  |
| tfim_8 | sim F x0.1 | **0.47** | 0.47 | 0.47 | 0.469 | 0.47 | 0.47 | **0.47** |  |
| heisenberg_8 | ESP | 2.66e-05 | **2.71e-05** | **2.71e-05** | 2.70e-05 | **2.71e-05** | 2.71e-05 | **2.71e-05** | mkco |
| heisenberg_8 | ESP_xt | **2.85e-06** | 2.30e-06 | 2.32e-06 | 2.80e-06 | 2.32e-06 | 2.32e-06 | 2.32e-06 |  |
| heisenberg_8 | ESP x0.1 | 0.355 | **0.355** | **0.355** | 0.355 | **0.355** | **0.355** | **0.355** |  |
| heisenberg_8 | sESP | 2.55e-05 | 2.59e-05 | **2.60e-05** | 2.58e-05 | **2.60e-05** | **2.60e-05** | **2.60e-05** |  |
| heisenberg_8 | sESP x0.1 | 0.354 | 0.355 | 0.355 | 0.354 | 0.355 | **0.355** | 0.355 |  |
| heisenberg_8 | sim F | 0.0108 | 0.0111 | 0.0111 | 0.011 | 0.0111 | **0.0111** | 0.0111 |  |
| heisenberg_8 | sim F x0.1 | 0.376 | 0.377 | 0.378 | 0.377 | 0.378 | **0.378** | 0.378 |  |
| qpe_8 | ESP | 4.32e-08 | 4.41e-08 | 4.41e-08 | 4.41e-08 | 4.41e-08 | **4.41e-08** | **4.41e-08** | mkco_full_alap |
| qpe_8 | ESP_xt | 3.43e-08 | 3.47e-08 | 3.47e-08 | 3.47e-08 | 3.47e-08 | **3.47e-08** | **3.47e-08** |  |
| qpe_8 | ESP x0.1 | 0.15 | 0.15 | 0.15 | 0.15 | 0.15 | **0.15** | **0.15** |  |
| qpe_8 | sESP | 6.68e-10 | **1.04e-09** | 1.04e-09 | 1.04e-09 | 1.04e-09 | 1.04e-09 | 1.04e-09 |  |
| qpe_8 | sESP x0.1 | 0.114 | **0.119** | 0.119 | 0.119 | 0.119 | 0.119 | 0.119 |  |
| qpe_8 | sim F | 0.0023 | **0.0031** | 0.0031 | 0.00303 | 0.0031 | 0.0031 | 0.0031 |  |
| qpe_8 | sim F x0.1 | 0.0928 | **0.0968** | 0.0968 | 0.0968 | 0.0968 | 0.0968 | 0.0968 |  |
| tfim_7_40 | ESP | 3.57e-28 | 4.04e-28 | 4.08e-28 | 4.02e-28 | **5.48e-28** | 5.48e-28 | 4.08e-28 | mkco |
| tfim_7_40 | ESP_xt | **8.43e-30** | 6.71e-30 | 6.63e-30 | 6.83e-30 | 5.74e-30 | 5.74e-30 | 6.63e-30 |  |
| tfim_7_40 | ESP x0.1 | 0.00163 | 0.00167 | 0.00167 | 0.00167 | **0.00171** | **0.00171** | 0.00167 |  |
| tfim_7_40 | sESP | 5.84e-30 | 9.26e-30 | **9.55e-30** | 7.25e-30 | 8.73e-30 | 8.73e-30 | **9.55e-30** |  |
| tfim_7_40 | sESP x0.1 | 0.00141 | 0.00147 | **0.00148** | 0.00144 | 0.00147 | 0.00147 | **0.00148** |  |
| tfim_7_40 | sim F | 0.0086 | 0.00826 | 0.00826 | 0.00809 | **0.00941** | 0.00941 | 0.00826 |  |
| tfim_7_40 | sim F x0.1 | 0.0136 | 0.0137 | 0.0137 | 0.0136 | **0.0139** | 0.0139 | 0.0137 |  |

#### Set 2 - Table 11 - ECRs removed by block KAK, plain vs commutation-aware block formation

| Circuit | input ECRs | removed by plain block KAK | removed by regrouped block KAK |
|---|---:|---:|---:|
| heisenberg_8 | 420 | 0 | 0 |
| qpe_8 | 484 | 0 | 0 |
| tfim_7_40 | 714 | 0 | 0 |
| tfim_8 | 280 | 0 | 0 |

#### Set 2 - Table 12 - Noisy simulated backend: Aer + the circuits' device calibrations, sampled counts

Hellinger fidelity of 32768 shots against the ideal output [bootstrap 95% interval]. Noise model: Aer's NoiseModel.from_backend (independent of mkco.noise); Qiskit's ALAP scheduling; methods interleaved in one job per run. mkco_noise is the same circuit as the method it selects (a repeat measurement). Predictions at scale 0.1: mkco.noise density-matrix Hellinger fidelity (<= 8 qubits) and state-aware ESP. The 17-qubit circuits are run at scale 0.1 only (at scale 1 they are at the noise floor).

| Circuit | method | scale 1 | scale 0.1 | predicted (DM, x0.1) | sESP x0.1 |
|---|---|---:|---:|---:|---:|
| heisenberg_8 | original | 0.0492 [0.0469, 0.0513] | 0.4846 [0.4788, 0.4897] | 0.5003 | 0.3539 |
| tfim_8 | original | 0.0455 [0.0430, 0.0477] | 0.5518 [0.5462, 0.5572] | 0.5744 | 0.4901 |
| qpe_8 | original | 0.2423 [0.2372, 0.2463] | 0.6793 [0.6735, 0.6838] | 0.6795 | 0.1136 |
| tfim_7_40 | original | 0.4782 [0.4718, 0.4830] | 0.4604 [0.4543, 0.4650] | 0.5189 | 0.0014 |
| qpe_8 | mkco | 0.3396 [0.3338, 0.3442] | 0.7012 [0.6952, 0.7053] | 0.7028 | 0.1187 |
| tfim_8 | mkco | 0.0465 [0.0441, 0.0485] | 0.5608 [0.5549, 0.5661] | 0.5738 | 0.4898 |
| tfim_7_40 | mkco | 0.4902 [0.4842, 0.4944] | 0.4688 [0.4629, 0.4738] | 0.5231 | 0.0015 |
| heisenberg_8 | mkco | 0.0508 [0.0484, 0.0532] | 0.4887 [0.4832, 0.4942] | 0.5007 | 0.3546 |
| tfim_8 | mkco_alap | 0.0442 [0.0418, 0.0464] | 0.5615 [0.5559, 0.5666] | 0.5731 | 0.4887 |
| qpe_8 | mkco_alap | 0.3314 [0.3258, 0.3358] | 0.7036 [0.6983, 0.7076] | 0.7015 | 0.1187 |
| tfim_7_40 | mkco_alap | 0.4892 [0.4831, 0.4940] | 0.4709 [0.4650, 0.4756] | 0.5223 | 0.0014 |
| heisenberg_8 | mkco_alap | 0.0503 [0.0479, 0.0527] | 0.4840 [0.4780, 0.4892] | 0.5009 | 0.3544 |
| tfim_8 | mkco_full | 0.0469 [0.0444, 0.0492] | 0.5578 [0.5521, 0.5629] | 0.5738 | 0.4898 |
| qpe_8 | mkco_full | 0.3391 [0.3339, 0.3438] | 0.7065 [0.7012, 0.7108] | 0.7028 | 0.1187 |
| tfim_7_40 | mkco_full | 0.4870 [0.4809, 0.4917] | 0.4667 [0.4612, 0.4715] | 0.5217 | 0.0015 |
| heisenberg_8 | mkco_full | 0.0521 [0.0498, 0.0545] | 0.4865 [0.4810, 0.4917] | 0.5007 | 0.3546 |
| heisenberg_8 | mkco_full_alap | 0.0524 [0.0499, 0.0546] | 0.4843 [0.4787, 0.4892] | 0.5007 | 0.3546 |
| qpe_8 | mkco_full_alap | 0.3390 [0.3337, 0.3436] | 0.7045 [0.6989, 0.7088] | 0.7028 | 0.1187 |
| tfim_8 | mkco_full_alap | 0.0457 [0.0434, 0.0481] | 0.5579 [0.5523, 0.5631] | 0.5738 | 0.4898 |
| tfim_7_40 | mkco_full_alap | 0.4851 [0.4791, 0.4898] | 0.4648 [0.4588, 0.4694] | 0.5217 | 0.0015 |
| tfim_8 | mkco_noise (= original) | 0.0429 [0.0408, 0.0450] | 0.5575 [0.5520, 0.5628] | 0.5744 | 0.4901 |
| qpe_8 | mkco_noise (= mkco_full_alap) | 0.3336 [0.3279, 0.3378] | 0.7026 [0.6969, 0.7072] | 0.7028 | 0.1187 |
| tfim_7_40 | mkco_noise (= mkco) | 0.4910 [0.4852, 0.4958] | 0.4688 [0.4630, 0.4737] | 0.5231 | 0.0015 |
| heisenberg_8 | mkco_noise (= mkco) | 0.0538 [0.0513, 0.0562] | 0.4898 [0.4843, 0.4949] | 0.5007 | 0.3546 |

Scale 1: on the method pairs that sampling separates (non-overlapping intervals), the predictions order density-matrix model 6/6, state-aware ESP 6/6, ESP 6/6 correctly.

Scale 0.1: on the method pairs that sampling separates (non-overlapping intervals), the predictions order density-matrix model 4/4, state-aware ESP 4/4, ESP 4/4 correctly.

## 6. Results in the settings of Lee et al. and on structured commuting circuits

These experiments reproduce the settings of Lee et al. They are the regime
where the *search* component of MKCO matters, because the conflict graphs are
not trivially colourable.

![E1](figures/e1_random_mcz.png)

- **E1 – the paper's random benchmark (Fig. 1 setting: m = 10/20/30 qubits,
  n = 50–200 multi-controlled-Z gates, 5 seeds each, 60 circuits).**
  - By the clique/Jackson bound, MKCO is certified optimal on **41/60** (DSatur
    36/60, JK 0/60); with the θ and θ⁺ bounds of E7, 48/60 vs 42/60. It is
    strictly better than DSatur on 14 circuits and never worse.
  - Its average excess over the certified bound is 0.57 layers, against 1.23
    for DSatur and 12.2 for JK.
  - The gains concentrate at m = 10, where the paper hypothesised ordering is
    *easier*: at n = 150–200 DSatur sits 4.6–5.2 layers above the bound and
    MKCO only 1.8–2.0.
  - For m = 20/30 the conflict graphs are near-cliques, and DSatur is already
    within 0–0.8 layers of the maximum clique on average. This answers the
    paper's open question of how far DSatur is from exact as n grows: little for
    m ≥ 20, several layers for m = 10.
  - Where the paper's backtracking finishes (n = 50, 15 circuits), MKCO equals
    the proven optimum on every one.
  - **E7 – Lovász-θ certificates.** For the instances the clique/Jackson bound
    left open, the θ number of the complement graph (an SDP, solved with
    Clarabel) raises the certified bound. The solver's matrix is repaired into
    an exactly feasible point (zeros imposed, diagonal shifted by the most
    negative eigenvalue, trace rescaled to 1), so the bound does not depend on
    solver accuracy.
    - Computed for all 15 open instances with ≤ 150 gates, it proves MKCO
      optimal on 6 more E1 circuits, raising E1's certified count from 41/60
      to **47/60**. DSatur also reaches 5 of these bounds (36/60 → 41/60); JK
      none. The one open E3 circuit stays open (θ does not reach
      MKCO's depth there).
    - At 200 gates the interior-point solver needs about an hour and 6 GB per
      instance. These 5 instances were solved for θ⁺ with the first-order SCS
      solver instead (E7b). The repair keeps the bound valid; the lower
      accuracy can only weaken it. θ⁺ proves one more circuit optimal
      (m = 20, seed 0: 95.03 → 96 = MKCO), so E1 ends at **48/60** (DSatur
      42/60).
    - θ never exceeded a proven chromatic number in the sanity tests.

![F2n multiplier](figures/gf2_multiplier.png)

- **E2 – the paper's own application (F₂ⁿ multiplication).**
  - MKCO's Toffoli-depth is optimal at all **34** field sizes, n = 2…64:
    - n ≥ 6: certified by the bound 2n−1;
    - n ≤ 5: proven by exhaustive backtracking, which gives 4, 6, 8, 10,
      confirming the paper's remark that 2n−1 is unreachable for n < 6.
  - DSatur, as used by Lee et al., is sub-optimal at 10 sizes
    (n = 5–9, 11, 13, 15–17; e.g. n = 6: 14 vs 11). This matches the paper's
    footnote 2.
  - Jain & Kumar's layering is sub-optimal at 27 sizes.
![E3](figures/e3_ccz.png)

- **E3 – Appendix C (random CCZ on 10 qubits).** MKCO is certified optimal on
  49/50 circuits (DSatur 20/50, JK 17/50), strictly better than DSatur on 30,
  and never worse. Where 10 s of backtracking could prove the optimum
  (19 circuits), MKCO equals it. At 40–50 gates MKCO also beats
  time-limited backtracking.
![E4](figures/e4_rzz.png)

- **E4 – commuting two-qubit layers (QAOA cost layers = edge colouring).**
  MKCO reaches Vizing's lower bound Δ on 14 of 18 graphs. DSatur and JK never
  do: they land 1–3.7 layers above Δ on average.
- **E5 – quantum-ready path.** Hierarchical Max-Cut with a QAOA backend (p = 3,
  state-vector) solved every Ising sub-problem to optimality (21/21) and
  produced the same layering as exact enumeration. The log encoding needs
  20–64 spins where one-hot colouring needs 40–176. HMC is optimal on all 4
  instances. On gf2_4 it gives 5 layers against a bound of 4, but exhaustive
  backtracking proves 5 is the optimum, so the bound is loose there.
![E6](figures/e6_fanout.png)

- **E6 – depth/qubit trade-offs (paper §5.2, made precise).** Fanning wires
  out into c copies turns layering into capacitated Max-k-Cut. Against a fixed
  round-robin copy split coloured by DSatur, MKCO is never worse and is up to
  24% shallower (mcz_m20_n120, c = 4: 21 → 16), fan-out CNOT layers included.
  The constructions are verified exactly by simulation (fidelity 1.0) on the
  instances small enough to simulate.

### E1 - Random commuting multi-controlled-Z circuits (Lee et al. Sec. 4.3)

Mean depth over seeds; 'opt' = instances where the method meets the certified lower bound.

| qubits m | gates n | LB | DSatur (Lee) | Backtracking (Lee, n<=50) | JK'26 | **MKCO** | DSatur opt | JK opt | MKCO opt |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 50 | 27.6 | 27.8 | 27.8 | 31.8 | **27.8** | 4/5 | 0/5 | 4/5 |
| 10 | 100 | 48.2 | 50.8 | - | 57.8 | **49.0** | 2/5 | 0/5 | 2/5 |
| 10 | 150 | 67.8 | 73.0 | - | 83.4 | **69.8** | 0/5 | 0/5 | 1/5 |
| 10 | 200 | 91.0 | 95.6 | - | 109.2 | **92.8** | 0/5 | 0/5 | 3/5 |
| 20 | 50 | 30.8 | 30.8 | 30.8 | 33.8 | **30.8** | 5/5 | 0/5 | 5/5 |
| 20 | 100 | 51.6 | 52.0 | - | 61.4 | **52.0** | 3/5 | 0/5 | 3/5 |
| 20 | 150 | 73.8 | 74.2 | - | 88.8 | **74.2** | 3/5 | 0/5 | 3/5 |
| 20 | 200 | 93.4 | 94.2 | - | 117.2 | **94.0** | 2/5 | 0/5 | 3/5 |
| 30 | 50 | 32.6 | 32.6 | 32.6 | 35.6 | **32.6** | 5/5 | 0/5 | 5/5 |
| 30 | 100 | 58.8 | 59.0 | - | 68.0 | **59.0** | 4/5 | 0/5 | 4/5 |
| 30 | 150 | 84.8 | 85.0 | - | 99.0 | **85.0** | 4/5 | 0/5 | 4/5 |
| 30 | 200 | 111.0 | 111.2 | - | 131.8 | **111.2** | 4/5 | 0/5 | 4/5 |

### E2 - F(2^n) multiplication, Toffoli-depth of phases 1+3 (Lee et al. Sec. 5.1, Fig. 2)

| n | certified LB (proven optimum for n<=7) | 2n-1 | DSatur (Lee) | JK'26 | **MKCO** |
|---:|---:|---:|---:|---:|---:|
| 2 | 4 | 3 | 4 | 4 | **4** |
| 3 | 6 | 5 | 6 | 6 | **6** |
| 4 | 8 | 7 | 8 | 8 | **8** |
| 5 | 10 | 9 | 11 | 11 | **10** |
| 6 | 11 | 11 | 14 | 12 | **11** |
| 7 | 13 | 13 | 14 | 15 | **13** |
| 8 | 15 | 15 | 16 | 17 | **15** |
| 9 | 17 | 17 | 18 | 18 | **17** |
| 10 | 19 | 19 | 19 | 20 | **19** |
| 11 | 21 | 21 | 22 | 22 | **21** |
| 12 | 23 | 23 | 23 | 24 | **23** |
| 13 | 25 | 25 | 26 | 25 | **25** |
| 14 | 27 | 27 | 27 | 27 | **27** |
| 15 | 29 | 29 | 31 | 31 | **29** |
| 16 | 31 | 31 | 32 | 32 | **31** |
| 17 | 33 | 33 | 34 | 34 | **33** |
| 18 | 35 | 35 | 35 | 37 | **35** |
| 19 | 37 | 37 | 37 | 37 | **37** |
| 20 | 39 | 39 | 39 | 41 | **39** |
| 21 | 41 | 41 | 41 | 43 | **41** |
| 22 | 43 | 43 | 43 | 45 | **43** |
| 23 | 45 | 45 | 45 | 45 | **45** |
| 24 | 47 | 47 | 47 | 48 | **47** |
| 25 | 49 | 49 | 49 | 50 | **49** |
| 26 | 51 | 51 | 51 | 53 | **51** |
| 27 | 53 | 53 | 53 | 55 | **53** |
| 28 | 55 | 55 | 55 | 56 | **55** |
| 29 | 57 | 57 | 57 | 59 | **57** |
| 30 | 59 | 59 | 59 | 61 | **59** |
| 31 | 61 | 61 | 61 | 63 | **61** |
| 32 | 63 | 63 | 63 | 65 | **63** |
| 40 | 79 | 79 | 79 | 82 | **79** |
| 48 | 95 | 95 | 95 | 97 | **95** |
| 64 | 127 | 127 | 127 | 129 | **127** |

Meets the certified bound: DSatur 24/34, JK 7/34, MKCO 34/34.

### E3 - Random CCZ circuits on 10 qubits (Lee et al. Appendix C)

| CCZ gates | LB | DSatur (Lee) | Backtracking (Lee) | JK'26 | **MKCO** | MKCO opt |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 5.6 | 5.6 | 5.6 | 5.6 | **5.6** | 5/5 |
| 20 | 9.0 | 9.2 | 9.0 | 9.8 | **9.0** | 5/5 |
| 30 | 13.2 | 14.2 | 13.2 | 13.6 | **13.2** | 5/5 |
| 40 | 16.4 | 17.4 | 16.8 | 18.0 | **16.6** | 4/5 |
| 50 | 18.6 | 20.4 | 19.6 | 20.4 | **18.6** | 5/5 |
| 60 | 23.2 | 24.2 | - | 24.6 | **23.2** | 5/5 |
| 70 | 26.8 | 28.0 | - | 27.4 | **26.8** | 5/5 |
| 80 | 30.0 | 32.6 | - | 30.8 | **30.0** | 5/5 |
| 90 | 34.0 | 35.4 | - | 34.8 | **34.0** | 5/5 |
| 100 | 37.0 | 38.8 | - | 38.4 | **37.0** | 5/5 |

### E4 - Commuting RZZ layers on random d-regular graphs (QAOA cost layer; LB = degree)

| qubits | degree d | DSatur (Lee) | JK'26 | **MKCO** | MKCO = d (optimal) |
|---:|---:|---:|---:|---:|---:|
| 30 | 5 | 6.00 | 6.00 | **5.00** | 3/3 |
| 30 | 9 | 10.00 | 10.67 | **9.00** | 3/3 |
| 50 | 15 | 17.00 | 17.00 | **15.00** | 3/3 |
| 50 | 25 | 27.33 | 27.00 | **25.33** | 2/3 |
| 100 | 15 | 17.33 | 18.00 | **15.33** | 2/3 |
| 100 | 31 | 34.67 | 34.00 | **31.67** | 1/3 |

### E5 - Hierarchical Max-Cut with exact and QAOA sub-solvers

| case | gates | LB | backend | layers | spins (log encoding) | spins (one-hot) | QAOA nodes solved optimally |
|---|---:|---:|---|---:|---:|---:|---:|
| gf2_4_phase3 | 10 | 4 | exact | 5 | 20 | 40 | - |
| gf2_4_phase3 | 10 | 4 | qaoa | 5 | 20 | 40 | 3/3 |
| gf2_5_phase3 | 15 | 5 | exact | 5 | 45 | 75 | - |
| gf2_5_phase3 | 15 | 5 | qaoa | 5 | 45 | 75 | 4/4 |
| draper_6_core | 21 | 6 | exact | 6 | 63 | 126 | - |
| draper_6_core | 21 | 6 | qaoa | 6 | 63 | 126 | 4/4 |
| ccz_m8_n16 | 16 | 11 | exact | 11 | 64 | 176 | - |
| ccz_m8_n16 | 16 | 11 | qaoa | 11 | 64 | 176 | 10/10 |

### E6 - Depth/qubit trade-off by ancilla fan-out (capacitated Max-k-Cut)

| circuit | copies per qubit | qubits | round-robin + DSatur depth | **MKCO depth** |
|---|---:|---:|---:|---:|
| draper_8_core | 1 | 16 | 8 | **8** |
| draper_8_core | 2 | 32 | 6 | **6** |
| draper_8_core | 3 | 48 | 7 | **7** |
| draper_8_core | 4 | 64 | 6 | **6** |
| draper_16_core | 1 | 32 | 16 | **16** |
| draper_16_core | 2 | 64 | 10 | **10** |
| draper_16_core | 3 | 96 | 10 | **10** |
| draper_16_core | 4 | 128 | 8 | **8** |
| ccz_m10_n80 | 1 | 10 | 35 | **31** |
| ccz_m10_n80 | 2 | 20 | 19 | **18** |
| ccz_m10_n80 | 3 | 30 | 16 | **15** |
| ccz_m10_n80 | 4 | 40 | 13 | **12** |
| ccz_m16_n150 | 1 | 16 | 38 | **38** |
| ccz_m16_n150 | 2 | 32 | 21 | **21** |
| ccz_m16_n150 | 3 | 48 | 17 | **17** |
| ccz_m16_n150 | 4 | 64 | 15 | **14** |
| mcz_m20_n120 | 1 | 20 | 57 | **57** |
| mcz_m20_n120 | 2 | 40 | 32 | **26** |
| mcz_m20_n120 | 3 | 60 | 25 | **20** |
| mcz_m20_n120 | 4 | 80 | 21 | **16** |

### E7 - Lovász-theta certificates where the clique/Jackson bound left a gap

theta(complement of the conflict graph) <= chromatic number (sandwich theorem), solved as an SDP. The 'theta' column is the objective of the solver's solution after repair into an exactly feasible point, so it is a proven lower bound on theta (and on the depth) whatever the solver's accuracy. Open instances above 150 gates were not attempted.

| exp. | m | gates | seed | clique/Jackson LB | theta (certified) | new LB | DSatur | JK'26 | MKCO | MKCO now proven optimal |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| E3 | 10 | 40 | 4 | 15 | 15.000 | 15 | 18 | 19 | 16 | no |
| E1 | 10 | 50 | 4 | 26 | 26.384 | 27 | 27 | 32 | 27 | yes |
| E1 | 10 | 100 | 0 | 47 | 47.015 | 48 | 50 | 58 | 48 | yes |
| E1 | 10 | 100 | 1 | 47 | 47.000 | 47 | 52 | 56 | 48 | no |
| E1 | 10 | 100 | 4 | 48 | 48.029 | 49 | 53 | 60 | 50 | no |
| E1 | 20 | 100 | 1 | 52 | 52.318 | 53 | 53 | 62 | 53 | yes |
| E1 | 20 | 100 | 3 | 47 | 47.000 | 47 | 48 | 58 | 48 | no |
| E1 | 30 | 100 | 2 | 49 | 49.318 | 50 | 50 | 62 | 50 | yes |
| E1 | 10 | 150 | 0 | 66 | 66.000 | 66 | 74 | 83 | 69 | no |
| E1 | 10 | 150 | 2 | 70 | 70.000 | 70 | 75 | 84 | 72 | no |
| E1 | 10 | 150 | 3 | 64 | 64.000 | 64 | 70 | 78 | 66 | no |
| E1 | 10 | 150 | 4 | 67 | 67.000 | 67 | 73 | 84 | 70 | no |
| E1 | 20 | 150 | 0 | 79 | 79.000 | 79 | 80 | 94 | 80 | no |
| E1 | 20 | 150 | 4 | 68 | 68.133 | 69 | 69 | 85 | 69 | yes |
| E1 | 30 | 150 | 0 | 89 | 89.318 | 90 | 90 | 101 | 90 | yes |

Theta closes the gap on 6 of 15 open instances.

### E7b - Szegedy theta-plus on the instances still open (incl. the 200-gate ones)

theta-plus >= theta and still <= chi (docs/THEORY.md, Proposition 9); certified by the same repair.

| exp. | m | gates | seed | clique/Jackson LB | theta | theta-plus (certified) | solver | new LB | MKCO | proven optimal |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|:---:|
| E3 | 10 | 40 | 4 | 15 | 15.000 | 15.000 | CLARABEL | 15 | 16 | no |
| E1 | 10 | 100 | 1 | 47 | 47.000 | 47.000 | CLARABEL | 47 | 48 | no |
| E1 | 10 | 100 | 4 | 48 | 48.029 | 48.077 | CLARABEL | 49 | 50 | no |
| E1 | 20 | 100 | 3 | 47 | 47.000 | 47.000 | CLARABEL | 47 | 48 | no |
| E1 | 10 | 150 | 0 | 66 | 66.000 | 66.000 | CLARABEL | 66 | 69 | no |
| E1 | 10 | 150 | 2 | 70 | 70.000 | 70.000 | CLARABEL | 70 | 72 | no |
| E1 | 10 | 150 | 3 | 64 | 64.000 | 64.000 | CLARABEL | 64 | 66 | no |
| E1 | 10 | 150 | 4 | 67 | 67.000 | 67.000 | CLARABEL | 67 | 70 | no |
| E1 | 20 | 150 | 0 | 79 | 79.000 | 79.000 | CLARABEL | 79 | 80 | no |
| E1 | 10 | 200 | 1 | 91 | – | 90.999 | SCS | 91 | 95 | no |
| E1 | 10 | 200 | 4 | 87 | – | 87.000 | SCS | 87 | 92 | no |
| E1 | 20 | 200 | 0 | 95 | – | 95.033 | SCS | 96 | 96 | yes |
| E1 | 20 | 200 | 2 | 94 | – | 94.292 | SCS | 95 | 96 | no |
| E1 | 30 | 200 | 3 | 102 | – | 101.997 | SCS | 102 | 103 | no |

Theta-plus closes 1 of 14 remaining instances.

## 7. Extensions: fault-tolerant depth, routing, block formation, noise

The same machinery (trace order, mixed graph, certified layering) carries
over to four further problems. Each one is implemented, tested and evaluated
against an established tool.

### 7.1 Non-Clifford depth with free Cliffords (E8)

In fault-tolerant execution, the expensive layers are those containing T
gates (or Toffolis); Clifford gates are cheap. `mkco.nonclifford` minimises
the *counted* depth: T-like rotations, Toffolis, or any non-Clifford rotation.
Counted gates take one step; Clifford gates take none, but still synchronise
their wires (the usual T-depth).
- **Reduction (Proposition 10).** This is a mixed-graph colouring on the
  counted gates. Its arcs come from the trace order through the free gates.
- **Solver.** A surrogate circuit with one private virtual wire per
  free-path pair lets the *unchanged* MKCO engine solve it, including the
  certified Jackson bound.
- **Merging.** Rotation merging (T·T = S) runs first.

![T-depth](figures/tdepth.png)

- **On its own**, MKCO-T lowers the T-depth of the GF(2ⁿ) multipliers by
  39–44% (e.g. gf2_mult_7: 108 → 66), and of T phase polynomials by 23–30%.
  It is certified optimal on 14 of the 17 T-depth instances; the three random
  Clifford+T circuits stay uncertified.
  - Ripple-carry (Cuccaro) adders are inherently sequential. MKCO proves that
    no reordering helps (certified = original).
  - Plain depth-minimising MKCO is worse on T-depth (e.g. cuccaro_16: 144 vs
    128), so the objective matters.
- **After PyZX** (full_reduce + extract), the strongest T-*count* tool we
  could run, MKCO-T cuts PyZX's T-depth by 10–69% (mean 41%) on all 17
  T-depth instances. Every one of these results is certified optimal.
  Examples:
  - gf2_mult_7: 74 → 23;
  - T phase polynomial n=16: 26 → 13;
  - random Clifford+T n=12: 65 → 36.
- **Toffoli-depth** of the multipliers drops by 53–64%
  (gf2_mult_12: 64 → 23).
- All 103 outputs with ≤ 20 qubits pass the state-vector check.

### 7.2 Commutation-aware routing + layering (E9)

`mkco.route` is a SABRE-style router (bidirectional layout search, lookahead,
decay) with one change: a gate enters the front layer as soon as the previous
run on each of its wires has executed.
- Mutually commuting gates (a whole QAOA cost layer) therefore all compete for
  execution.
- Two front scorings run as a small portfolio: the mean over front gates, and
  each qubit's nearest front gate (gates sharing a qubit run one after another
  anyway).
- After routing, MKCO layers the circuit, re-synthesises blocks (KAK) and
  layers it again. The trial with the smallest CNOTs + depth is kept.
- Every output passes the exact `unroute` check (Proposition 11) and the
  coupling check.
- The comparison is Qiskit's transpiler at optimization level 3 ("Qiskit
  O3": SabreLayout + SabreSwap + its optimisation loop) on IBM Eagle's
  127-qubit heavy-hex graph, at CNOT level. Unlike the IBM benchmarks, these
  are untranspiled logical circuits, so Qiskit's level-3 routing is the
  natural baseline here.

![Routing](figures/routing.png)

- **QAOA** (7 instances, 16–64 qubits, degree 3–4, p = 1–2), where whole
  cost layers commute: MKCO-route uses **3.8–21.9% fewer CNOTs** than Qiskit O3
  on all 7, and is **up to 55% shallower**. Depth is equal on one instance.
  - qaoa_n64_p1: 638 vs 726 CNOTs, depth 80 vs 177.
  - qaoa_n32_p2: 449 vs 575 CNOTs, depth 96 vs 193.
- **Trotter Ising** (CNOT–Rz–CNOT form): 2.9% fewer CNOTs and 7.9% shallower
  at n = 16; at n = 32, equal CNOTs (+0.2%) and 25% shallower.
- **QFT is Qiskit's case.** QFT-12 costs 11% more CNOTs (but is 14%
  shallower); QFT-20 costs 25% more CNOTs and is 43% deeper.
- **Phase polynomial and random Clifford+T:** within +0.6% to +5.6% CNOTs;
  the phase polynomial is 11% shallower, the random circuit 2.6% deeper.
- **Ablation.** With the plain gate-DAG front (standard SABRE) and everything
  else identical, the router needs more CNOTs on **all 13** circuits
  (e.g. qaoa_n64_p2: 1583 vs 1177). The gain therefore comes from the
  commutation-aware front.
  - The QFT gap is a weakness of our SABRE base relative to Qiskit's tuned
    implementation: the ablation is even further behind there.
- **Composition.** MKCO's post-routing passes applied to Qiskit's output
  ("Qiskit O3 + MKCO") lower Qiskit's depth on all 13 circuits (e.g. random
  Clifford+T 571 → 512, Trotter-16 164 → 140), at equal or lower CNOT count.

### 7.3 Commutation-aware block formation for KAK (E11)

Block resynthesis (here and in Qiskit's ConsolidateBlocks) only sees blocks
that are contiguous on the gate DAG. A gate that commutes past a block still
splits it. `regroup_pairs` applies a legal reordering (a linear extension of
the trace order, checked) that keeps the gates of one qubit pair together, in
a forward and a backward pass, before block KAK.
- On 19 logical (untranspiled) circuits it removes CNOTs on 17 relative to
  plain block KAK, and never adds any. Against Qiskit's level-3 optimiser on
  the same logical circuits (CX basis) it is on par in CNOTs, and its outputs
  are shallower after MKCO layering on the Trotter, QAOA and random circuits.
  Applied after Qiskit, it removes further CNOTs on 5 circuits.
- On the IBM benchmarks (Table 11) the level-3 transpiler has already merged
  every block that commutation could join. Only hubbard_8 gains (4 ECRs).
- Qiskit's KAK decomposer silently snaps near-identity blocks (e.g. a
  controlled phase of angle 5·10⁻⁵ in QFT-20) to cheaper, inexact circuits,
  even with `approximate=False`. MKCO's exact check rejects those
  replacements.

### 7.4 Noise study with device calibration data (E10)

The 9 benchmarks are native to ibm_brisbane: all 78 ECR directions match the
FakeBrisbane snapshot in qiskit-ibm-runtime. Every method's output is
therefore scored with that device's calibrated per-gate errors and durations,
T1, T2 and readout errors (`mkco.noise`, Table 10):
- an ESP with ALAP idling;
- a state-aware ESP;
- for circuits with ≤ 8 active qubits, exact density-matrix simulation at
  calibrated noise and at 10× lower noise.

![Noise validation](figures/noise_validation.png)

- **Depth is not fidelity.** All reorderings of a circuit have the same gate
  noise; switching idle noise off makes their simulated fidelities equal
  (mult_8: 0.708 for all). The differences come from idling, mainly from
  dephasing of qubits that wait in superposition. As a result, a
  depth-optimal order can be less *or* more faithful than the input:
  - mult_8: MKCO's order loses 4.4% state fidelity at 10× lower noise
    (0.542 vs 0.567), although it is 1% shorter;
  - hhl_8: it gains 12% (0.0138 vs 0.0123).
- **The state-aware ESP sees this; the usual ESP does not.** Over all pairs of
  methods on the 3 simulated circuits, the state-aware ESP orders the pair as
  the density-matrix simulation does in **95%** of cases at 10× lower noise
  (84% at calibrated noise, where fidelities approach the noise floor). The
  state-blind ESP manages 70% (57%).
- **`mkco_noise` picks the output by state-aware ESP.** Candidates are MKCO's
  orders, their ALAP variants and the input. Under the best available score
  it never falls below the input, and is above it on 8 of 9 circuits:
  - simulated fidelity: equal on mult_8 (it keeps the input order), +2%
    (hubbard_8), +12% (hhl_8);
  - state-aware ESP: +1–2% (add_17, qae_17, qft_16), ×4.7 (grover_10);
  - ESP (too large to simulate): ×2.1 (heisenberg_32); ×205 (hubbard_18,
    with 3,505 fewer ECRs than the input and an 18% shorter schedule).
  It also scores at least as well as Jain & Kumar's output on every circuit.
- **Crosstalk mode under a timing model.** Its objective counts
  neighbouring-coupler pairs *in the same layer*. With calibrated durations
  and ALAP timing, ECRs of different layers overlap in time, so the layer
  proxy does not carry over. Under ESP_xt (an extra ECR error for every
  time-overlapping neighbouring pair), mkco_xt beats plain MKCO only on
  hubbard_18 (×24). A duration-aware crosstalk objective is future work.
- **Independent check on a noisy simulated backend (Table 12).** The three
  8-qubit circuits were also run end to end as on hardware, on a simulated
  noisy backend:
  - Qiskit's ALAP scheduling, then Aer with its standard noise model built
    from the same ibm_brisbane calibration (`NoiseModel.from_backend`). This
    model shares no code with `mkco.noise`.
  - 32,768 shots per circuit, all methods interleaved in one job, at
    calibrated and at 10× lower noise.
  - On the method pairs that sampling separates, at 10× lower noise,
    `mkco.noise`'s density-matrix model and the state-aware ESP order **7/7**
    pairs correctly. The state-blind ESP gets 3/7, worse than chance, because
    it rewards the shorter orders.
  - At calibrated noise, where the circuits sit near the noise floor, the
    scores are 4/4, 4/4 and 2/4.
  - Measured at 10× lower noise, `mkco_noise` reproduces the predicted
    winners. Its circuit is measured twice, as itself and as the method it
    selects, so the pair of numbers shows the sampling spread:
    - mult_8: it keeps the input order (0.546–0.548), while plain MKCO
      drops to 0.513;
    - hubbard_8: 0.073–0.074, against 0.070 for the input and 0.065 for
      plain MKCO;
    - hhl_8 (MKCO-full): 0.072–0.075, against 0.072 for the input.
  - Larger circuits:
    - add_17 and qae_17 (17 qubits, outputs concentrated on 1 and 4
      bitstrings) were sampled at 10× lower noise: 512 shots per version,
      quantum-trajectory simulation at about 0.85 s per shot. With 512 shots the 95% intervals span about
      ±0.03, wider than the 1–2% differences the model predicts. Results
      (versions: input, plain MKCO, noise-aware MKCO):
      - qae_17: the measured order is the one the state-aware ESP predicts
        (noise-aware MKCO 0.353 > plain MKCO 0.305 > input 0.280), though the
        intervals overlap. The Hellinger values exceed the predicted state
        fidelities because phase errors do not show in counts taken in the
        computational basis.
      - add_17: the three versions overlap (0.127–0.168), and every predicted
        success probability lies inside its interval. The point estimates run
        the other way from the predicted ranking, but well within the sampling
        error.
    - qft_16 and grover_10 were not sampled. Their ideal outputs are almost
      uniform (16.0 and 9.9 bits of entropy), so measured counts cannot tell
      the methods apart; grover_10 is also at the noise floor even at 10×
      lower noise.
    - heisenberg_32 and hubbard_18 (31–32 active qubits) are beyond noisy
      simulation on this machine: one state vector would need about 70 GB.
- **On real hardware.** `run_ibm_hardware.py submit` sends the same job to an
  IBM Quantum backend. It needs the user's own account; none was available
  for this study.

### 7.5 Stronger SDP certificates (E7b)

Szegedy's θ⁺ (`X_ij ≤ 0` instead of `= 0` on non-adjacent pairs) is ≥ θ and
still ≤ χ (Proposition 9). It uses the same solver-independent repair.

- **Up to 150 gates** (9 still-open instances, Clarabel), θ⁺ equals θ to
  solver accuracy, except one instance (48.03 → 48.08). These graphs are
  near-cliques, where the non-negativity that separates θ⁺ from θ rarely
  binds.
- **At 200 gates** (5 instances, SCS, a few seconds to 30 minutes each)
  θ⁺ proves MKCO optimal on one more circuit (m = 20, seed 0: 95.03 → 96).
  It also raises the bound of another from 94 to 95, so MKCO there is within
  one layer of optimal.
- With all certificates, MKCO is certified optimal on **48/60** of the
  paper's random benchmark (DSatur 42/60, JK 0/60). Its mean excess over the
  best bound is 0.42 layers.

### E8 - Non-Clifford depth with free Cliffords (T-depth, Toffoli-depth)

Cells: count / depth of the counted gates (T-like rotations, or Toffolis). \* = certified optimal for that method's own gate set (after merging). PyZX: full_reduce + extract (full) or teleport_reduce (teleport), then basic_optimization.

| circuit | qubits | original | MKCO-depth | **MKCO-T** | PyZX full | **PyZX full + MKCO-T** | PyZX teleport | **PyZX tel. + MKCO-T** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| cuccaro_4_ct (t) | 10 | 56 / 32 | 56 / 36 | 56 / 32\* | 32 / 23 | 32 / 17\* | 32 / 32 | 32 / 29\* |
| cuccaro_8_ct (t) | 18 | 112 / 64 | 112 / 72 | 112 / 64\* | 64 / 41 | 64 / 36\* | 64 / 64 | 64 / 57\* |
| cuccaro_16_ct (t) | 34 | 224 / 128 | 224 / 144 | 224 / 128\* | 128 / 92 | 128 / 72\* | 128 / 128 | 128 / 113\* |
| mcx_vchain_5_ct (t) | 9 | 49 / 28 | 49 / 26 | 49 / 25\* | 31 / 22 | 31 / 19\* | 31 / 26 | 31 / 23\* |
| mcx_vchain_8_ct (t) | 15 | 91 / 52 | 91 / 47 | 91 / 46\* | 55 / 43 | 55 / 33\* | 55 / 45 | 55 / 41\* |
| mcx_vchain_12_ct (t) | 23 | 147 / 84 | 147 / 75 | 147 / 74\* | 87 / 58 | 87 / 52\* | 87 / 72 | 87 / 65\* |
| gf2_mult_3_ct (t) | 11 | 84 / 36 | 84 / 25 | 84 / 22\* | 50 / 18 | 50 / 8\* | 50 / 31 | 50 / 18\* |
| gf2_mult_4_ct (t) | 15 | 154 / 54 | 154 / 37 | 154 / 33\* | 86 / 31 | 86 / 11\* | 86 / 51 | 86 / 29\* |
| gf2_mult_5_ct (t) | 19 | 245 / 81 | 245 / 49 | 237 / 45\* | 133 / 41 | 133 / 14\* | 133 / 69 | 133 / 37\* |
| gf2_mult_6_ct (t) | 23 | 357 / 90 | 357 / 61 | 349 / 55\* | 189 / 55 | 189 / 20\* | 189 / 94 | 189 / 47\* |
| gf2_mult_7_ct (t) | 27 | 490 / 108 | 490 / 73 | 482 / 66\* | 256 / 74 | 256 / 23\* | 256 / 110 | 256 / 55\* |
| tpoly_n8_t40_s0 (t) | 8 | 27 / 22 | 27 / 17 | 27 / 17\* | 25 / 9 | 25 / 5\* | 25 / 20 | 25 / 15\* |
| tpoly_n12_t80_s0 (t) | 12 | 52 / 40 | 52 / 29 | 52 / 28\* | 48 / 20 | 48 / 9\* | 48 / 30 | 48 / 27\* |
| tpoly_n16_t120_s0 (t) | 16 | 79 / 47 | 79 / 37 | 79 / 33\* | 73 / 26 | 73 / 13\* | 73 / 39 | 73 / 33\* |
| rand_cliffT_n8_g400_s0 (t) | 8 | 95 / 39 | 95 / 37 | 79 / 25 | 43 / 25 | 43 / 15\* | 43 / 20 | 43 / 13\* |
| rand_cliffT_n10_g800_s0 (t) | 10 | 175 / 48 | 175 / 51 | 145 / 35 | 91 / 49 | 91 / 29\* | 91 / 36 | 91 / 24\* |
| rand_cliffT_n12_g1200_s0 (t) | 12 | 247 / 69 | 247 / 64 | 215 / 45 | 143 / 65 | 143 / 36\* | 143 / 47 | 143 / 33\* |
| cuccaro_8 (toffoli) | 18 | 16 / 16 | 16 / 16 | 16 / 16\* | – | – | – | – |
| cuccaro_16 (toffoli) | 34 | 32 / 32 | 32 / 32 | 32 / 32\* | – | – | – | – |
| cuccaro_32 (toffoli) | 66 | 64 / 64 | 64 / 64 | 64 / 64\* | – | – | – | – |
| mcx_vchain_8 (toffoli) | 15 | 13 / 13 | 13 / 13 | 13 / 13\* | – | – | – | – |
| mcx_vchain_16 (toffoli) | 31 | 29 / 29 | 29 / 29 | 29 / 29\* | – | – | – | – |
| gf2_mult_4 (toffoli) | 15 | 22 / 15 | 22 / 8 | 22 / 7\* | – | – | – | – |
| gf2_mult_5 (toffoli) | 19 | 35 / 23 | 35 / 10 | 35 / 10 | – | – | – | – |
| gf2_mult_6 (toffoli) | 23 | 51 / 25 | 51 / 12 | 51 / 11\* | – | – | – | – |
| gf2_mult_7 (toffoli) | 27 | 70 / 30 | 70 / 14 | 70 / 13\* | – | – | – | – |
| gf2_mult_9 (toffoli) | 35 | 117 / 45 | 117 / 18 | 117 / 18 | – | – | – | – |
| gf2_mult_10 (toffoli) | 39 | 145 / 52 | 145 / 20 | 145 / 19\* | – | – | – | – |
| gf2_mult_11 (toffoli) | 43 | 176 / 59 | 176 / 22 | 176 / 21\* | – | – | – | – |
| gf2_mult_12 (toffoli) | 47 | 210 / 64 | 210 / 24 | 210 / 23\* | – | – | – | – |

On the 17 T-depth instances MKCO-T lowers PyZX(full)'s T-depth by 10-69% (mean 41%); 17/17 results certified. All 103 outputs with <= 20 qubits pass the state-vector check.

### E9 - Commutation-aware routing + layering on the 127-qubit heavy-hex device (CNOT level)

Cells: CNOTs / depth after routing and optimisation of untranspiled logical circuits. Qiskit O3 = Qiskit's transpiler at level 3 (SabreLayout + SabreSwap), the routing baseline. sabre_dag is the ablation (same router, plain DAG front). Every mkco_route output passes the exact unroute check and the coupling check.

| circuit | qubits | logical CNOTs | Qiskit O3 | **MKCO-route** | SWAPs | sabre_dag (ablation) | Qiskit O3 + MKCO | CNOTs vs O3 | depth vs O3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| qaoa_n16_p1_d3 | 16 | 48 | 106 / 43 | **102 / 43** | 20 | 107 / 42 | 106 / 41 | -3.8% | +0.0% |
| qaoa_n16_p2_d3 | 16 | 96 | 204 / 100 | **190 / 96** | 32 | 222 / 94 | 204 / 96 | -6.9% | -4.0% |
| qaoa_n32_p1_d3 | 32 | 96 | 275 / 106 | **227 / 61** | 51 | 256 / 71 | 275 / 102 | -17.5% | -42.5% |
| qaoa_n32_p2_d3 | 32 | 192 | 575 / 193 | **449 / 96** | 92 | 563 / 141 | 574 / 185 | -21.9% | -50.3% |
| qaoa_n64_p1_d3 | 64 | 192 | 726 / 177 | **638 / 80** | 156 | 702 / 126 | 726 / 171 | -12.1% | -54.8% |
| qaoa_n64_p2_d3 | 64 | 384 | 1397 / 290 | **1177 / 164** | 282 | 1583 / 251 | 1395 / 275 | -15.7% | -43.4% |
| qaoa_n32_p1_d4 | 32 | 128 | 445 / 143 | **363 / 90** | 85 | 429 / 131 | 445 / 136 | -18.4% | -37.1% |
| trotter_reg3_n16_s3 | 16 | 144 | 345 / 164 | **335 / 151** | 70 | 370 / 167 | 345 / 140 | -2.9% | -7.9% |
| trotter_reg3_n32_s3 | 32 | 288 | 873 / 299 | **875 / 223** | 209 | 988 / 223 | 871 / 287 | +0.2% | -25.4% |
| qft_12 | 12 | 132 | 221 / 221 | **245 / 191** | 49 | 247 / 240 | 219 / 199 | +10.9% | -13.6% |
| qft_20 | 20 | 380 | 638 / 401 | **795 / 573** | 185 | 879 / 493 | 638 / 384 | +24.6% | +42.9% |
| phasepoly_n16_t60_s0 | 16 | 266 | 907 / 542 | **958 / 484** | 264 | 1022 / 524 | 895 / 489 | +5.6% | -10.7% |
| rand_cliffT_n16_g600_s0 | 16 | 239 | 1199 / 571 | **1206 / 586** | 350 | 1244 / 609 | 1188 / 512 | +0.6% | +2.6% |

Unroute and coupling checks: all pass.

### E11 - Commutation-aware block formation before KAK (logical circuits, CX basis)

Cells: CNOTs / depth after MKCO layering. regroup = legal reordering that keeps gates of one pair together (forward + backward pass) before block KAK.

| circuit | input CNOTs | block KAK | **regroup + KAK** | Qiskit O3 | O3 + regroup + KAK |
|---|---:|---:|---:|---:|---:|
| phasepoly_n8_t40_s0 | 178 | 178 / 124 | **174 / 128** | 170 / 127 | 170 / 127 |
| phasepoly_n8_t40_s1 | 158 | 152 / 120 | **138 / 116** | 136 / 103 | 136 / 103 |
| phasepoly_n10_t60_s0 | 266 | 266 / 157 | **262 / 162** | 262 / 157 | 262 / 157 |
| phasepoly_n10_t60_s1 | 230 | 224 / 162 | **216 / 150** | 212 / 143 | 212 / 143 |
| phasepoly_n12_t80_s0 | 336 | 336 / 176 | **332 / 174** | 332 / 174 | 332 / 174 |
| phasepoly_n12_t80_s1 | 314 | 314 / 175 | **308 / 173** | 308 / 173 | 308 / 173 |
| phasepoly_n16_t120_s0 | 500 | 496 / 217 | **480 / 208** | 480 / 208 | 480 / 208 |
| phasepoly_n16_t120_s1 | 480 | 472 / 226 | **458 / 228** | 458 / 225 | 458 / 225 |
| phasepoly_n20_t160_s0 | 650 | 648 / 214 | **634 / 212** | 632 / 213 | 632 / 213 |
| phasepoly_n20_t160_s1 | 642 | 642 / 277 | **632 / 273** | 632 / 273 | 632 / 273 |
| trotter_reg3_n10_s4 | 120 | 120 / 58 | **118 / 65** | 120 / 70 | 118 / 75 |
| qaoa_n10_p2_d3_cx | 60 | 60 / 33 | **60 / 33** | 60 / 42 | 60 / 42 |
| trotter_reg3_n12_s4 | 144 | 140 / 63 | **138 / 69** | 140 / 74 | 138 / 77 |
| qaoa_n12_p2_d3_cx | 72 | 70 / 35 | **70 / 35** | 70 / 41 | 70 / 41 |
| trotter_reg3_n16_s4 | 192 | 186 / 66 | **180 / 66** | 186 / 76 | 180 / 76 |
| qaoa_n16_p2_d3_cx | 96 | 96 / 28 | **94 / 34** | 96 / 37 | 94 / 40 |
| rand_cliffT_n10_g400_s0 | 157 | 153 / 88 | **149 / 86** | 148 / 99 | 148 / 99 |
| rand_cliffT_n10_g400_s1 | 182 | 179 / 91 | **178 / 91** | 179 / 100 | 178 / 103 |
| rand_cliffT_n10_g400_s2 | 159 | 148 / 84 | **139 / 89** | 137 / 95 | 137 / 95 |

regroup + KAK uses fewer CNOTs than plain block KAK on 17/19 circuits and never more; applied after Qiskit O3 it removes CNOTs on 5/19.

## 8. Research directions opened by the Max-Cut view

Items marked ✅ are implemented and evaluated here; 🧪 are implemented with a
small demonstration; ⭕ are open problems we identified.

1. ✅ **Exact general-circuit reduction (Thm 1) and the Max-k-Cut
   characterisation (Thm 2).** This closes the paper's main limitation (commuting
   circuits only) with a linear-memory model.
2. ✅ **Certified depth bounds (Thm 7), plus Lovász-θ SDP bounds (E7).**
   Optimality is proven on all 9 IBM benchmarks and on the F₂ⁿ multiplier. The
   θ number of the complement of the conflict graph (sandwich theorem)
   certifies 6 more random-MCZ circuits that the clique bound left open, and the
   certificate is made solver-independent by repairing the SDP solution into an
   exactly feasible point (Prop. 9). Szegedy's θ⁺ is implemented the same way
   (E7b). On these near-clique conflict graphs it equals θ up to 150 gates.
   At 200 gates it proves one more circuit optimal, giving 48/60. ⭕ Exact
   rational certificates and bounds that also use precedence (non-commuting
   circuits) remain open.
3. ✅ **Soft hardware constraints as weighted edges.** Implemented for
   crosstalk; the same mechanism extends directly to:
   - frequency collisions;
   - measurement crosstalk;
   - control-electronics limits (one global resource with capacity c);
   - leakage-prone gate pairs.
4. 🧪 **Capacities = ancilla fan-out (Lee et al. §5.2 made precise).**
   Implemented with exact verification on small instances (E6). ⭕ Constant-depth
   fan-out with mid-circuit measurement (dynamic circuits) would change the
   copy cost from 2⌈log₂c⌉ layers to O(1).
5. 🧪 **Quantum-native solving.** Each HMC node is an Ising model with
   n·⌈log₂K⌉ spins in total (Prop. 6). QAOA solves the small nodes optimally in
   E5. ⭕ Annealer or QAOA hardware runs on larger windows, and approximation
   guarantees that carry Goemans–Williamson / Frieze–Jerrum cut ratios over to
   depth, are open.
6. ✅ **Depth budgets.** Fixed-k Max-k-Cut gives the least-conflicting schedule
   under a hard latency or coherence budget. Proposition 3 bounds the repaired
   depth. Table 9 and the Pareto figure show the resulting trade-off between
   two-qubit depth and crosstalk.
7. ⭕ **Lexicographic / Pareto objectives.** Total depth vs two-qubit depth vs
   crosstalk. The data show real tensions (add_17: depth-optimal costs +2 ECR
   layers; crosstalk mode costs +0.8–7.6% total depth). A multi-objective
   Max-k-Cut (weights per objective) is the natural tool.
8. ✅ **T-depth / Toffoli-depth with free Cliffords (E8, Prop. 10).** The
   counted gates form a mixed graph whose arcs run through free gates; a
   surrogate circuit with private virtual wires lets the unchanged engine solve
   it with a certified bound. It composes with PyZX. ⭕ Coupling it with
   phase-polynomial resynthesis (T-par) is open.
9. ✅ **Joint routing + layering (E9, Prop. 11).** The router's front layer is
   the trace-order front of the layering engine. Every output is proven correct
   by `unroute`. ⭕ Placing SWAPs inside the Max-k-Cut itself (SWAPs as
   optional gates) is open.
10. ⭕ **Min-cut / Max-cut duality for distributed QC.** Partitioning qubits
    across QPUs is a min-cut; layering is a max-cut; a joint QUBO couples them.
11. ⭕ **Learned warm starts.** Jain & Kumar's learned independent-set generator
    could seed the Max-k-Cut search instead of competing with it.
12. ✅ **Single-qubit resynthesis inside the run structure** (rewrite mode).
    ZSX re-synthesis of 1q chains plus run-based merging, followed by Max-k-Cut
    reordering, lowers depth further on 5/9 benchmarks (−57.8% and −46.6% on
    heisenberg_32 and hubbard_18).
13. ✅ **Two-qubit block resynthesis (KAK) inside the run model** (MKCO-full).
    Finding: transpiled blocks are already ECR-optimal on 7 of 9 benchmarks
    (Table 8). Where KAK does find cheaper blocks (heisenberg_32, hubbard_18),
    locally cheaper blocks can *increase* global depth, because they destroy the
    cross-block rotation merging that MKCO's commutation runs enable. 🧪
    Commutation-aware block formation (E11) lets KAK see blocks that commuting
    gates had split. It removes CNOTs on 17/19 logical circuits, and 4 ECRs
    that block KAK misses on hubbard_8. ⭕ Scoring
    blocks by their effect on the global layering is still open.
14. ✅ **State-dependent idle noise (E10, Prop. 12).** A depth-optimal
    reordering can be *less* faithful on hardware, because qubits may wait in
    superposition for longer. The state-aware ESP predicts this, matching
    density-matrix simulation, and selects among MKCO candidates (`mkco_noise`).
    Confirmed on a noisy simulated backend with Aer's independent device noise
    model (Table 12). ⭕ Real-device runs: `experiments/run_ibm_hardware.py`
    is ready, but needs an IBM Quantum account.

## 9. Limitations and threats to validity

- **Benchmark difficulty.** On the 9 transpiled benchmarks, commutation-aware
  list scheduling already meets the certified bound. Every layering method that
  uses commutation (JK and MKCO) therefore reaches the same optimal depth.
  MKCO's distinctive contributions there are the *proof* of optimality, the
  crosstalk mode and the rewrite modes. Max-k-Cut search matters on
  structured commuting workloads (E1–E4).
- **JK baseline.** No public code exists, so it was re-implemented from the
  published description. A learned independent-set generator could behave
  differently, but on the IBM circuits it cannot beat the certified optimum.
- **Crosstalk proxy.** The neighbouring-coupler model and the coupling graph
  inferred from used edges are proxies. Real gains should be validated with
  device calibration data or hardware runs. Anchor barriers keep the 2q-depth
  optimal but cost 0.8–7.6% in total depth (0.0–0.9% estimated duration).
- **No Qiskit re-optimisation baseline on the IBM benchmarks.** They are
  already Qiskit's output at optimization level 3, so the rewrite modes are
  measured against the input. Qiskit appears only as the routing baseline for
  untranspiled logical circuits (E9, E11).
- **Durations** in Tables 1–9 are nominal Eagle values. The noise study (E10)
  uses the ibm_brisbane calibration snapshot from qiskit-ibm-runtime
  (ECR 660–780 ns, sx 60 ns). The ranking of methods there comes from a noise
  *model*, not from hardware.
- **Noise model.** Depolarizing gate errors, thermal relaxation while idling,
  symmetric readout errors. No crosstalk, leakage, coherent errors or
  dynamical decoupling. ESP_xt is a sensitivity analysis with an assumed extra
  ECR error per overlapping neighbouring pair.
- **Routing study.** CNOT level with symmetric couplers, as is usual in routing
  papers. One Qiskit seed, our router with 16 trials. Our SABRE base is weaker
  than Qiskit's on QFT, where it inserts more SWAPs even without commutation
  awareness (ablation column).
- **T-depth study.** PyZX is a T-*count* optimiser. The comparison shows that
  MKCO-T composes with it, not that MKCO beats phase-polynomial T-depth
  methods (T-par, TODD), which re-synthesise the circuit.
- **Runtimes** are single-process Python on a laptop, measured while other
  experiments shared the machine, so treat them as indicative. MKCO stops early
  when the bound is met.

## 10. Reproducing everything

```bash
python experiments/run_ibm127.py benchmarks/ibm127     # all methods, verification, QASM outputs
python experiments/add_merge.py && python experiments/add_rewrite.py && python experiments/add_full.py
python experiments/add_full_duration.py
python experiments/run_blocks.py && python experiments/run_pareto.py && python experiments/run_theta.py
python experiments/summarize_ibm127.py                 # tables -> results/ibm127/tables.md
python experiments/run_structured.py                   # E1-E6 -> results/structured/*.json
python experiments/summarize_structured.py
python experiments/run_set2.py                         # second benchmark set (Section 5.1)
python experiments/run_theta_plus.py                   # E7b theta-plus certificates
python experiments/run_tdepth.py                       # E8 T-depth / Toffoli-depth (needs pyzx)
python experiments/run_routing.py                      # E9 routing on heavy-hex (needs qiskit)
python experiments/run_regroup.py                      # E11 commutation-aware block formation
python experiments/run_noise.py                        # E10 noise study (needs qiskit-aer, qiskit-ibm-runtime)
python experiments/run_ibm_hardware.py submit --fake --shots 32768                    # noisy backend
python experiments/run_ibm_hardware.py submit --fake --shots 32768 --noise-scale 0.1
python experiments/plots.py                            # figures -> docs/figures
pytest -q
```

Every optimized circuit is saved as
`results/ibm127/<circuit>__<method>.qasm`.

## References

1. H. Lee, K. C. Jeong, P. Kim. Quantum circuit optimization by graph coloring. *Quantum* (2026). [arXiv:2501.14447](https://arxiv.org/abs/2501.14447)
2. P. Jain, S. Kumar. Quantum circuit depth optimization using graph coloring. NeurIPS 2026 (WiML). [neurips.cc/virtual/2026/163759](https://neurips.cc/virtual/2026/163759)
3. D. Brélaz. New methods to color the vertices of a graph. *CACM* 22 (1979).
4. A. Hertz, D. de Werra. Using tabu search techniques for graph coloring. *Computing* 39 (1987).
5. P. Galinier, J.-K. Hao. Hybrid evolutionary algorithms for graph coloring. *J. Comb. Optim.* 3 (1999).
6. M. X. Goemans, D. P. Williamson. Improved approximation algorithms for maximum cut and satisfiability problems using semidefinite programming. *JACM* 42 (1995).
7. A. Frieze, M. Jerrum. Improved approximation algorithms for MAX k-CUT and MAX BISECTION. *Algorithmica* 18 (1997).
8. D. Karger, R. Motwani, M. Sudan. Approximate graph coloring by semidefinite programming. *JACM* 45 (1998).
9. E. de Klerk, D. V. Pasechnik, J. P. Warners. On approximate graph colouring and MAX-k-CUT algorithms based on the θ-function. *J. Comb. Optim.* 8 (2004).
10. S. Burer, R. D. C. Monteiro, Y. Zhang. Rank-two relaxation heuristics for MAX-CUT and other binary quadratic programs. *SIAM J. Optim.* 12 (2002).
11. E. Farhi, J. Goldstone, S. Gutmann. A quantum approximate optimization algorithm. [arXiv:1411.4028](https://arxiv.org/abs/1411.4028)
12. F. G. Fuchs et al. Encodings of the weighted MAX k-CUT on qubit systems. [arXiv:2411.08594](https://arxiv.org/abs/2411.08594)
13. V. Diekert, G. Rozenberg (eds.). *The Book of Traces*. World Scientific (1995).
14. Y. N. Sotskov. Mixed graph colorings: a historical review. *Mathematics* 8(3):385 (2020).
15. J. R. Jackson. Scheduling a production line to minimize maximum tardiness. UCLA Research Report 43 (1955).
16. P. Murali, D. C. McKay, M. Martonosi, A. Javadi-Abhari. Software mitigation of crosstalk on noisy intermediate-scale quantum computers. ASPLOS (2020).
17. Y. Ding et al. Systematic crosstalk mitigation for superconducting qubits via frequency-aware compilation. MICRO (2020). [arXiv:2008.09503](https://arxiv.org/abs/2008.09503)
18. A synergistic compilation workflow for tackling crosstalk in quantum machines (CQC). [arXiv:2207.05751](https://arxiv.org/abs/2207.05751)
19. SurgeQ: a hybrid framework for ultra-fast quantum processor design and crosstalk-aware circuit execution. [arXiv:2601.04645](https://arxiv.org/abs/2601.04645)
20. Y. Nam, N. J. Ross, Y. Su, A. M. Childs, D. Maslov. Automated optimization of large quantum circuits with continuous parameters. *npj Quantum Inf.* 4 (2018).
21. R. Iten et al. Exact and practical pattern matching for quantum circuit optimization. *ACM Trans. Quantum Comput.* (2022).
22. A. Javadi-Abhari et al. Quantum computing with Qiskit. [arXiv:2405.08810](https://arxiv.org/abs/2405.08810)
23. D. Maslov, B. Zindorf. Depth optimization of CZ, CNOT, and Clifford circuits. *IEEE TQE* 3 (2022).
24. R. Herrman, J. Ostrowski, T. S. Humble, G. Siopsis. Lower bounds on circuit depth of the quantum approximate optimization algorithm. *Quantum Inf. Process.* 20 (2021).
25. V. Verteletskyi, T.-C. Yen, A. F. Izmaylov. Measurement optimization in the variational quantum eigensolver using a minimum clique cover. *J. Chem. Phys.* 152 (2020).
26. C. Moore, M. Nilsson. Some notes on parallel quantum computation. [quant-ph/9804034](https://arxiv.org/abs/quant-ph/9804034)
27. D. Maslov, J. Mathew, D. Cheung, D. K. Pradhan. An O(m²)-depth quantum algorithm for the elliptic curve discrete logarithm problem over GF(2^m). *QIC* 9 (2009).
28. T. G. Draper. Addition on a quantum computer. [quant-ph/0008033](https://arxiv.org/abs/quant-ph/0008033)
29. Automatic quantum function parallelization and memory management in Qrisp. [arXiv:2606.31837](https://arxiv.org/abs/2606.31837)
30. A mixed-integer program for circuit execution time minimization with precedence constraints. [arXiv:2504.09268](https://arxiv.org/abs/2504.09268)
31. ISAAQ: Ising machine assisted quantum compiler. [arXiv:2303.02830](https://arxiv.org/abs/2303.02830)

32. L. Lovász. On the Shannon capacity of a graph. *IEEE Trans. Inf. Theory* 25(1) (1979).
33. A. Schrijver. A comparison of the Delsarte and Lovász bounds. *IEEE Trans. Inf. Theory* 25(4) (1979).
34. M. Szegedy. A note on the θ number of Lovász and the generalized Delsarte bound. FOCS (1994).
35. I. Dukanovic, F. Rendl. Semidefinite programming relaxations for graph coloring and maximal clique problems. *Math. Program.* 109 (2007).
36. M. Amy, D. Maslov, M. Mosca, M. Roetteler. A meet-in-the-middle algorithm for fast synthesis of depth-optimal quantum circuits. *IEEE TCAD* 32(6) (2013).
37. M. Amy, D. Maslov, M. Mosca. Polynomial-time T-depth optimization of Clifford+T circuits via matroid partitioning. *IEEE TCAD* 33(10) (2014).
38. P. Selinger. Quantum circuits of T-depth one. *Phys. Rev. A* 87, 042302 (2013).
39. L. E. Heyfron, E. T. Campbell. An efficient quantum compiler that reduces T count. *Quantum Sci. Technol.* 4, 015004 (2018).
40. R. Duncan, A. Kissinger, S. Perdrix, J. van de Wetering. Graph-theoretic simplification of quantum circuits with the ZX-calculus. *Quantum* 4, 279 (2020).
41. A. Kissinger, J. van de Wetering. Reducing the number of non-Clifford gates in quantum circuits. *Phys. Rev. A* 102, 022406 (2020).
42. S. A. Cuccaro, T. G. Draper, S. A. Kutin, D. P. Moulton. A new quantum ripple-carry addition circuit. [quant-ph/0410184](https://arxiv.org/abs/quant-ph/0410184)
43. A. Barenco et al. Elementary gates for quantum computation. *Phys. Rev. A* 52, 3457 (1995).
44. F. Vatan, C. Williams. Optimal quantum circuits for general two-qubit gates. *Phys. Rev. A* 69, 032315 (2004).
45. G. Li, Y. Ding, Y. Xie. Tackling the qubit mapping problem for NISQ-era quantum devices. ASPLOS (2019).
46. H. Zou, M. Treinish, K. Hartman, A. Ivrii, J. Lishman. LightSABRE: a lightweight and enhanced SABRE algorithm. [arXiv:2409.08368](https://arxiv.org/abs/2409.08368)
47. A. Zulehner, A. Paler, R. Wille. An efficient methodology for mapping quantum circuits to the IBM QX architectures. *IEEE TCAD* 38(7) (2019).
48. T. Itoko, R. Raymond, T. Imamichi, A. Matsuo. Optimization of quantum circuit mapping using gate transformation and commutation. *Integration* 70 (2020).
49. M. Alam, A. Ash-Saki, S. Ghosh. Circuit compilation methodologies for quantum approximate optimization algorithm. MICRO (2020).
50. L. Lao, C. G. Almudever. 2QAN: a quantum compiler for 2-local qubit Hamiltonian simulation algorithms. ISCA (2022).
51. J. Weidenfeller et al. Scaling of the quantum approximate optimization algorithm on superconducting qubit based hardware. *Quantum* 6, 870 (2022).
52. P. Murali, J. M. Baker, A. Javadi-Abhari, F. T. Chong, M. Martonosi. Noise-adaptive compiler mappings for noisy intermediate-scale quantum computers. ASPLOS (2019).
53. S. S. Tannu, M. K. Qureshi. Not all qubits are created equal. ASPLOS (2019).
54. S. Nishio, Y. Pan, T. Satoh, H. Amano, R. Van Meter. Extracting success from IBM's 20-qubit machines using error-aware compilation. *ACM JETC* 16(3) (2020).
55. P. Das, S. Tannu, S. Dangwal, M. Qureshi. ADAPT: mitigating idling errors in qubits via adaptive dynamical decoupling. MICRO (2021).
56. A. Kissinger, J. van de Wetering. PyZX: large scale automated diagrammatic reasoning. *EPTCS* 318 (2020).

## Appendix A. Theory: statements and proofs


Notation. A circuit is a sequence of gates `g_1 … g_N`. `supp(g)` is the set of
wires (qubits and classical bits) that `g` touches. Two gates *conflict* when
their supports intersect. For a layering, *unit* gates take one layer;
*zero-duration* gates (single-wire gates when the objective is the two-qubit
depth) take none.

---

### 1. Commutation and equivalent reorderings

**Lemma 1 (axis rule).** Let `A`, `B` be unitaries with shared qubits `S`. Suppose
that for every `q ∈ S` there is one Bloch direction `n_q` such that both
`A` and `B` commute with `P_q = n_q·σ_q`, or one of them acts as the identity
on `q`. Then `AB = BA`.

*Proof.* The operators `{P_q}_{q∈S}` commute pairwise and each has a
non-degenerate spectrum `{±1}` on its qubit. Let `Π_x` (`x ∈ {±1}^S`) be the
joint eigenprojectors. Because `A` commutes with every `P_q`, it is
block-diagonal: `A = Σ_x Π_x ⊗ A_x`, where `A_x` acts on `supp(A)∖S`.
Likewise `B = Σ_x Π_x ⊗ B_x` with `B_x` on `supp(B)∖S`. These two sets are
disjoint, so `A_x ⊗ I` and `I ⊗ B_x` commute, and therefore
`AB = Σ_x Π_x ⊗ A_x B_x = BA`. ∎

For every gate and every qubit it touches, MKCO computes the *axis* `n_q` from
the gate's unitary. It solves the real null space of
`[ [U,X_q], [U,Y_q], [U,Z_q] ]`, which gives `Z`, `X`, `Y`, a general direction,
`I`, or "none". `tests/test_core.py` checks Lemma 1 exhaustively against exact
matrices for every pair of library gates.

**Runs.** On each wire, MKCO groups consecutive gates with the same axis into
maximal *runs*. Gates in consecutive runs of a wire do not commute (by the
rule), so every gate of run `r` must precede every gate of run `r+1`. Call the
resulting partial order `≺`.

**Lemma 2 (trace equivalence).** Every linear extension of `≺` implements the
same unitary as the input, up to global phase. `≺` is exactly the transitive
closure of "`g_i` before `g_j`, they share a wire, and they do not commute by
the rule". It is stored in `O(Σ_g |supp(g)|)` memory, with no quadratic edge
list.

*Proof.* Take the commutation relation of gate instances as the independence
relation of a Mazurkiewicz trace monoid. Two words over the same gate
instances are trace-equivalent iff every pair of dependent instances keeps its
relative order. Trace-equivalent words are connected by swaps of adjacent
independent letters, and each such swap preserves the unitary by Lemma 1.

Now show that the run order generates exactly the dependent pairs.
- Non-commuting gates sharing a wire `w` lie in different runs of `w`, so they
  are ordered by the chain of consecutive runs between them.
- Conversely, each arc between consecutive runs joins gates whose axes differ
  on `w`, so that pair is dependent. ∎

**Corollary (independent audit).** A reordering is correct whenever every pair
of gates whose relative order changed and which share a qubit commutes.
`mkco/verify.py` enumerates exactly those inverted pairs and checks
`[A,B]=0` numerically on their joint support. The check does not use the
run/axis machinery, so it independently verifies the optimizer.

### 2. Depth minimisation = mixed-graph colouring

A *layering* is a map `ℓ : unit gates → {0,…,k−1}` with:
- `ℓ(u) < ℓ(v)` whenever `u ≺ v` (precedence arcs);
- `ℓ(u) ≠ ℓ(v)` whenever `u, v` conflict (edges).

This is a colouring of the *mixed graph* `M = (V, A, E)`.

**Theorem 1.** The minimum depth over all reorderings permitted by Lemma 2
equals the mixed chromatic number `χ(M)`. If `≺` is empty (a commuting
circuit), this is Lee–Jeong–Kim's reduction to vertex colouring (their Claim 7
and Proposition 8).

*Proof.*
- (≤) Sort the gates by `ℓ`, breaking ties by original index. This is a linear
  extension of `≺`, and its ASAP depth is at most `k`, because gates in the same
  layer are pairwise disjoint.
- (≥) The ASAP layering of any linear extension is a valid `ℓ` with
  `k = depth`. ∎

*Zero-duration gates.* Emit with key `(slot, duration, original index)`, where
a zero-duration gate's slot is one past its preceding unit run. Then
precedence is preserved and the weighted ASAP depth is at most `k`. This is
implemented in `schedule.emit_order`, and every output is re-checked
structurally.

### 3. The Max-k-Cut formulation

Weight each conflicting pair by `w(u,v) = |supp(u) ∩ supp(v)|`, which gives the
*conflict multigraph*. For a layering into `k` slots, let `occ[t,q]` be the
number of gates in layer `t` that touch wire `q`.

**Theorem 2.**

`Φ_k(ℓ) := Σ_{t,q} C(occ[t,q], 2) = Σ_{u<v : ℓ(u)=ℓ(v)} w(u,v) = w(E) − Cut_k(ℓ)`.

So a `k`-layer circuit exists iff the precedence-constrained weighted
**Max-k-Cut** of the conflict multigraph cuts all of `w(E)` (equivalently,
`min Φ_k = 0`). Proof: count the pairs `{u,v}` per (layer, wire). ∎

What this buys:
1. **Depth budget.** For a fixed hardware or latency budget `k`, Max-k-Cut
   gives the "least conflicting" `k`-layer schedule. Plain colouring has no
   notion of a near-miss.
2. **Soft constraints.** Any extra pairwise penalty (crosstalk, frequency
   collisions, shared control lines) becomes an edge with weight `0 < w < 1`.
   MKCO adds it as a *soft resource* of capacity 1, so
   `Φ = Σ_r w_r · C(max(0, occ − c_r) + 1, 2)`.
3. **Capacities.** Wire capacity `c_q > 1` models ancilla fan-out copies of a
   diagonal (single-axis) wire. This makes the "parallelisation by extra
   qubits" of Lee et al. (§5.2) a capacitated Max-k-Cut.
4. **Scalability.** `Φ` and its move deltas cost `O(|supp(g)|)` per gate.
   The `O(n²)` conflict graph of Lee et al.'s Algorithm 1 is never built.

**Proposition 3 (repair bound).** Let `ℓ` be a `k`-layering whose
monochromatic graph `H_t` in layer `t` is non-empty. Splitting each layer into
`χ(H_t)` sub-layers gives a valid layering of depth `Σ_t χ(H_t)`, which is at
most `k + Σ_t (½ + √(2|E(H_t)|+¼) − 1)`. A near-feasible Max-k-Cut therefore
certifies a near-optimal circuit.

### 4. Max-Cut is per-wire load balancing (hierarchical Max-Cut)

Split a gate set `S` into an early and a late half with spins `z_i = ±1`. Let
`S_q = Σ_{i ∋ q} z_i` and `n_q = |{i ∈ S : q ∈ supp(i)}|`.

**Theorem 4.** `Σ_{u<v} w(u,v) z_u z_v = ½ Σ_q (S_q² − n_q)`. So maximising
the cut of the conflict multigraph is the same as minimising the per-wire
discrepancy `Σ_q S_q²`. For unequal halves (`K1 ≠ K2` layers), minimising
`Σ_q (S_q − τ_q)²` with `τ_q = n_q (K1−K2)/K` adds only local fields: it is
still an Ising/Max-Cut instance.

**Corollary 5 (when HMC is optimal).** Recursive bisection assigns every gate
a `⌈log₂ K⌉`-bit layer index. If every node of the recursion admits a split in
which each wire puts at most `K1` gates early and at most `K2` gates late,
then the leaves are proper layers. With `K = max_q n_q`, HMC then meets the
lower bound of Lee et al.'s Eq. (2) and is optimal.

*Example.* A commuting circuit of two-qubit gates whose interaction multigraph
is bipartite with maximum degree `Δ = 2^h` admits such splits (Euler
partitions). This recovers König's edge-colouring theorem. It is the case of
Draper's adder core, where HMC returns the optimum `n`.

*Precedence.* Arcs `u → v` become penalties `P·(1−z_u)(1+z_v)/4`. These are
quadratic, so a precedence-constrained bisection is still a QUBO. Local
heads and tails fix spins that cannot be on one side.

**Proposition 6 (qubit-efficient quantum encoding).** A `K`-layering of `n`
gates needs `n⌈log₂ K⌉` spins in total, over `⌈log₂ K⌉` Ising sub-problems
of at most `n` spins each. A one-hot colouring QUBO needs `nK` binary
variables plus penalty terms. Each HMC node can be solved by Goemans–Williamson
(SDP + hyperplane rounding), simulated annealing, QAOA, or a quantum annealer.
`mkco/hmc.py` implements the first three plus exact enumeration, and exports
`(h, J)`.

### 5. Certified lower bounds

Let `head(g)` be the earliest layer `g` can start in, and `tail(g)` the number
of layers that must follow it. A run's members share a wire, so they are
serialised. The earliest completion of a predecessor run is therefore the
single-machine schedule of its members with release dates equal to their
heads (Jackson's rule). Tails are the mirror image.

**Theorem 7.** `LB = max( max_g head(g)+tail(g)+1 , max_q J_q )` is a lower
bound on the depth of every equivalent reordering. Here `J_q` is the optimal
makespan of wire `q`'s gates viewed as unit jobs with release `head` and tail
`tail`, which the largest-tail-first rule solves exactly. `LB` dominates both
the critical path and Lee et al.'s Eq. (2). *Proof:* induction over `≺`
(every bound is a relaxation of the true schedule). ∎

When `depth(output) = LB`, the output is **certified optimal**: no reordering
can do better.

### 6. Window decomposition (general circuits)

**Proposition 8 (window isolation).** Take a feasible layering and a window of
layers `[a,b]`, and let `W` be the gates in it. Every chain between two gates
of `W` stays inside `[a,b]`. Moving `W` into `[a,b−1]` and shifting the later
layers down by one is therefore feasible iff `W` alone admits a
`(b−a)`-colouring of its mixed sub-graph. That is an isolated, small
precedence-constrained Max-k-Cut. MKCO solves these windows with exact
enumeration (or tabu / QAOA) inside a large-neighbourhood search, with
forward–backward justification between sweeps.

### 7. An SDP bound for commuting circuits

**Proposition 9 (θ certificate for commuting circuits).** For a commuting
circuit with conflict graph `G`, every layering is a proper colouring of `G`,
so `depth ≥ χ(G) ≥ ϑ(Ḡ) ≥ ω(G)` (Lovász sandwich theorem), where
`ϑ(Ḡ) = max ⟨J, X⟩` over `X ⪰ 0`, `tr X = 1`, `X_ij = 0` for every
non-adjacent pair `i ≠ j` of `G`. Any feasible `X` has `⟨J, X⟩ ≤ ϑ(Ḡ)`. A
numerical solution `X̃` is made exactly feasible by zeroing those entries,
adding `max(0, −λ_min)·I` (which changes only the diagonal, so the zeros stay)
and dividing by the trace. `⌈⟨J, X⟩ − ε⌉` is then a depth lower bound that does
not depend on the solver's accuracy; `ε` covers only floating-point error in
`λ_min` and the sum. It can beat the clique bound: for the 5-cycle `ω = 2`,
but `ϑ = √5` gives 3.

*Szegedy's θ⁺.* Relaxing the zero constraints to `X_ij ≤ 0` gives
`ϑ⁺(Ḡ) ≥ ϑ(Ḡ)`, and still `ϑ⁺(Ḡ) ≤ χ(G)`. *Proof:* for a proper
`k`-colouring with classes `C_1..C_k`, the matrix
`Y = k Σ_c 1_{C_c} 1_{C_c}ᵀ − J` is PSD by Cauchy–Schwarz
(`xᵀYx = k Σ_c s_c² − (Σ_c s_c)²`). It equals `kI + M − J`, where `M ≥ 0` is
supported on non-adjacent pairs of `G`. So `(λ = k, M)` is dual-feasible, and
weak duality gives `⟨J, X⟩ ≤ k` for every feasible `X`. The repair is the same,
except that positive entries on non-adjacent pairs are cut to zero and
negative ones are kept. ∎

### 8. Non-Clifford depth with free Cliffords

Fix a set `C` of *counted* gates (T-like rotations, Toffolis, or non-Clifford
rotations). Every other gate is *free*. The counted depth of a gate sequence
is its ASAP depth when counted gates take one step and free gates take none
but still synchronise their wires (the usual T-depth).

**Proposition 10.** Over all commutation-equivalent reorderings, the minimum
counted depth equals the chromatic number of the mixed graph on `C` with
- arcs `u → v` for `u ≺ v` (trace order of Lemma 2);
- edges for incomparable counted gates that share a qubit.

*Proof.* (≥) Take any reordering and give each counted gate its ASAP level.
Along a chain `u ≺ … ≺ v`, levels never decrease at free gates and increase
at counted ones, so `level(u) < level(v)`. Two counted gates on one wire get
distinct levels. So the levels form a feasible colouring.

(≤) Take a feasible colouring `L`. Give every free gate `f` the gap
`g(f) = max L(u)` over its counted ancestors (−1 if none), and sort all gates by
`(2L(c) or 2g(f)+1, original index)`. The key never decreases along `≺`:
- counted `u ≺` counted `v`: `L(u) < L(v)`;
- counted `u ≺` free `f`: `g(f) ≥ L(u)`;
- free `f ≺` counted `v`: every counted ancestor of `f` is one of `v`, so
  `L(v) > g(f)`;
- free `f ≺` free `f'`: the ancestor sets are nested.

So the sorted order is a linear extension of `≺`, hence equivalent (Lemma 2).
Its counted depth is at most the number of colours. ∎

The mixed graph is not built explicitly. A *surrogate circuit* keeps the
counted gates with their real qubits and per-qubit axes. Every pair `(u, v)`
joined by a path whose interior gates are all free gets a private virtual wire,
on which `u` and `v` have non-commuting axes. The transitive closure of these
pairs is `≺` restricted to `C`; real wires only add pairs that are already
ordered; virtual wires only add conflicts between ordered pairs. The
surrogate's feasible layerings are therefore exactly the colourings of
Proposition 10. The unchanged MKCO engine solves it, and Theorem 7 applied to
the surrogate is a certified bound on the counted depth.

### 9. Commutation-aware routing

**Proposition 11.** Let `R` be a routed circuit: gates on physical qubits, plus
SWAPs, starting from layout `π₀`. Track the layout through the SWAPs and map
every non-SWAP gate back to logical qubits. If the resulting logical sequence
is a linear extension of the input's trace order, `R` implements the input
followed by the final permutation `π_f`.

*Proof.* A SWAP only relabels which physical qubit holds which logical state.
So `R` equals the logical sequence, conjugated by the layout permutations.
Lemma 2 makes that sequence equivalent to the input. ∎

The router lets a gate enter the front layer once the previous run on each of
its wires has been executed: exactly the gates that may come next in some
linear extension. This is why every routed output passes the exact `unroute`
check of Proposition 11.

### 10. State-dependent idle noise

**Proposition 12.** Let a qubit `q` of a pure state `|ψ⟩` idle for time `t`
under amplitude damping `γ = 1 − e^{−t/T₁}` followed by dephasing
`p = (1 − e^{−t/T_φ})/2` (with `1/T_φ = 1/T₂ − 1/(2T₁)`). Then, to first order,
the fidelity with `|ψ⟩` drops by

`γ (P₁ − |⟨σ⁻⟩|²) + p (1 − ⟨Z⟩²)`,

where `P₁`, `⟨σ⁻⟩` and `⟨Z⟩` are the reduced quantities of `q` in `|ψ⟩`.

*Proof.* For the damping Kraus pair `K₀ = |0⟩⟨0| + √(1−γ)|1⟩⟨1|` and
`K₁ = √γ |0⟩⟨1|`: `|⟨ψ|K₀|ψ⟩|² = 1 − γP₁ + O(γ²)` and
`|⟨ψ|K₁|ψ⟩|² = γ|⟨σ⁻⟩|²`. For a Z error with probability `p`:
`F = 1 − p + p⟨Z⟩²`. ∎

A qubit idling in `|0⟩` loses nothing; one idling in an equal superposition
dephases fully. Two reorderings with the same depth and total idle time can
therefore differ in fidelity. A state-blind ESP cannot see this; the
state-aware ESP of mkco.noise (Proposition 12 summed over all idle gaps of the
ALAP schedule) can.

## Appendix B. Related-work study notes


### The base paper
**Lee, Jeong & Kim, "Quantum Circuit Optimization by Graph Coloring", *Quantum* (2026), arXiv:2501.14447.**

The paper shows that minimizing the depth of a circuit whose gates all
mutually commute is polynomially equivalent to vertex colouring. Gates are
vertices; an edge means "not simultaneously executable". The authors run
DSatur and backtracking as back-ends, and apply the method to:
- Maslov et al.'s F_{2^n} multiplier (Toffoli-depth 4n−4 → 2n−1);
- Draper's QFT adder (depth/qubit trade-offs using extra qubits).

Limitations the authors state, or that follow from the paper:
1. **Commuting circuits only.** The paper suggests splitting non-commuting
   circuits into commuting parts as future work.
2. **Hardware constraints are open.** Connectivity, gate sets and crosstalk are
   flagged as "highly nontrivial"; the paper hints at "colouring of a certain
   acyclic directed graph".
3. **Heuristic only.** DSatur is used for large instances. How far it is from
   optimal "for larger circuit sizes is open", and in the multiplier DSatur
   misses the 2n−1 bound for some n < 20.
4. **Extra-qubit algorithm unspecified.** The heuristic for parallelisation by
   extra qubits is not given ("not the key finding").
5. **Quadratic graph construction.** Algorithm 1 builds an explicit O(n²)
   graph.

### Direct follow-up
**Jain & Kumar, "Quantum Circuit Depth Optimization using Graph Coloring", NeurIPS 2026 (WiML affinity poster).**

This work extends Lee et al. to non-commuting circuits with a mixed graph:
directed arcs for dependencies, undirected edges for commuting gates that share
a qubit. It repeatedly extracts large independent sets from the executable
(in-degree-0) subgraph, using a learned independent-set generator (after Li et
al. 2018) and a guided beam search. The authors compare only against Qiskit's
DAG depth of the given order. No code or numbers are public, so
`mkco/jk.py` is a re-implementation from the published description.

### Colouring and partitioning in quantum compilation
- **Edge colouring for two-qubit layers:**
  - CZ/CNOT/Clifford depth (Maslov & Zindorf, IEEE TQE 2022);
  - binary-field inversion (Amento et al. 2013);
  - QAOA depth lower bounds via hypergraph chromatic index (Herrman et al., QIP 2021).
- **Pauli grouping by colouring / clique cover:**
  - Verteletskyi et al., JCP 2020;
  - Jena et al., arXiv:1907.07859;
  - Gokhale et al., IEEE TQE 2020;
  - SYK circuits (Asaduzzaman et al., PRD 2024).
- **Crosstalk-aware scheduling:**
  - Murali et al., ASPLOS 2020 (SMT scheduling with serialisation barriers);
  - Ding et al., MICRO 2020, arXiv:2008.09503 (frequency-aware);
  - CQC, arXiv:2207.05751 (colouring with crosstalk edges);
  - SurgeQ, arXiv:2601.04645 (maximum-independent-set layers).

  All of these either forbid or allow a pair. None trades depth against
  crosstalk inside one weighted cut objective.
- **Commutation-aware compilation:**
  - Qiskit commutation analysis / DAGDependency (Iten et al., ACM TQC 2022);
  - Qrisp permeability DAG (arXiv:2606.31837);
  - rotation merging (Nam et al., npj QI 2018);
  - commutation-aware routing (arXiv:2511.04608);
  - QAOA CPHASE scheduling (Alam et al. 2020).
- **QUBO/Ising formulations in compilation:**
  - ISAAQ (arXiv:2303.02830): routing as QUBO on Ising machines;
  - MIP execution-time scheduling with precedence (arXiv:2504.09268).

  We found no prior work that casts gate *layering* itself as a Max-Cut.

### Max-Cut / Max-k-Cut and colouring theory
- Goemans–Williamson SDP (JACM 1995).
- Frieze–Jerrum Max-k-Cut SDP (Algorithmica 1997).
- Karger–Motwani–Sudan vector colouring (JACM 1998).
- de Klerk, Pasechnik & Warners (J. Comb. Optim. 2004): θ-function link
  between Max-k-Cut and colouring.
- Burer–Monteiro–Zhang rank-2 heuristics (SIAM J. Optim. 2002).
- TabuCol (Hertz & de Werra 1987) and HEA (Galinier & Hao 1999). Both solve
  k-colouring by minimising monochromatic edges for fixed k, i.e. they are
  Max-k-Cut local searches. The strongest practical colouring heuristics are
  Max-k-Cut solvers.
- Mixed-graph colouring = unit-time scheduling with precedence and conflicts
  (Sotskov, Mathematics 2020).
- Jackson's rule (1955) for single-machine release/tail bounds.

### Quantum solvers for Max-k-Cut
- QAOA (Farhi et al., arXiv:1411.4028).
- Binary / log encodings of Max-k-Cut using |V|·log₂k qubits (Fuchs et al.,
  arXiv:2411.08594).
- Logarithmic HUBO encodings for colouring (2026 preprint).

### Ancilla parallelisation of diagonal gates
- Fan-out: copy, apply diagonal gates in parallel, uncopy (Moore & Nilsson,
  quant-ph/9804034).
- Recent depth-optimal diagonal synthesis on grids (arXiv:2606.17589).

### Work related to the extensions (E7–E11)
- **SDP lower bounds for colouring.**
  - Lovász θ (IEEE Trans. Inf. Theory 1979) and the sandwich theorem.
  - Schrijver's θ′ (IEEE Trans. Inf. Theory 1979) is smaller than θ.
    Szegedy's θ⁺ (FOCS 1994) is larger and still at most χ, so it is the
    stronger colouring bound.
  - Dukanovic & Rendl (Math. Program. 2007) study these relaxations for colouring.
  - None of these is used to *certify* circuit layerings in the compilation
    literature we found.
- **T-depth and non-Clifford optimisation.**
  - Exact T-depth search: meet-in-the-middle (Amy, Maslov, Mosca & Roetteler,
    IEEE TCAD 2013).
  - T-par, matroid partitioning of phase polynomials (Amy, Maslov & Mosca,
    IEEE TCAD 2014).
  - T-depth one with ancillas (Selinger, PRA 2013).
  - TODD T-count reduction (Heyfron & Campbell, QST 2018).
  - Rotation merging and phase folding (Nam et al., npj QI 2018).
  - ZX-calculus: graph-theoretic simplification (Duncan, Kissinger, Perdrix &
    van de Wetering, *Quantum* 2020) and phase teleportation (Kissinger &
    van de Wetering, PRA 2020), both in PyZX.

  These reduce the T-*count* or re-synthesise phase polynomials. MKCO's
  non-Clifford mode is complementary. It keeps the gates (after merging) and
  finds the depth-optimal commutation-equivalent layering of the counted
  gates, with a certified bound. It composes with PyZX (E8).
- **Two-qubit block resynthesis.**
  - Optimal two-qubit circuits / KAK (Vatan & Williams, PRA 2004).
  - Qiskit's Collect2qBlocks + ConsolidateBlocks collect blocks on the gate
    DAG, so a block ends at the first gate on one of its qubits, even when that
    gate commutes past.
  - Commutation-aware block formation (regroup_pairs) instead uses the trace
    order, so commuting interlopers no longer split blocks (E11).
- **Qubit routing.**
  - SABRE (Li, Ding & Xie, ASPLOS 2019) and LightSABRE (Zou et al.,
    arXiv:2409.08368) route on the gate DAG.
  - A* mapping (Zulehner, Paler & Wille, IEEE TCAD 2019).
  - Commutation-aware routing:
    - gate transformation and commutation in mapping (Itoko et al.,
      Integration 2020);
    - QAOA-specific compilation (Alam, Ash-Saki & Ghosh, MICRO 2020);
    - 2QAN for 2-local Hamiltonians (Lao & Almudever, ISCA 2022);
    - swap strategies for commuting 2q blocks (Weidenfeller et al., *Quantum* 2022).
  - These are specialised to particular circuit families. MKCO's router takes
    its front layer from the same run structure as the layering engine, for
    any circuit. An exact `unroute` check proves each routed circuit
    equivalent up to the final qubit permutation (E9).
- **Noise-aware compilation.**
  - Noise-adaptive mapping (Murali et al., ASPLOS 2019).
  - Variation-aware mapping (Tannu & Qureshi, ASPLOS 2019).
  - Estimated success probability (Nishio et al., ACM JETC 2020).
  - Adaptive dynamical decoupling against idling errors (Das et al., MICRO 2021).

  ESP-style scores ignore the state a qubit idles in. E10 shows this can rank
  reorderings wrongly. The state-aware ESP of mkco.noise weights each idle gap
  by the idling qubit's ideal state, and matches density-matrix simulation.

### Positioning of MKCO
| Capability | Lee'26 | JK'26 | MKCO |
|---|:---:|:---:|:---:|
| Commuting circuits | ✓ | ✓ | ✓ |
| Non-commuting circuits | – | ✓ | ✓ |
| Exact optimality reduction for general circuits (Thm 1) | – | – | ✓ |
| Certified lower bound / optimality proof | partial (Eq. 2) | – | ✓ (Thm 7) |
| Depth budget, soft constraints (crosstalk) | – | – | ✓ (Thm 2) |
| Capacities (ancilla fan-out) | heuristic | – | ✓ |
| Quantum-native solver path (Ising, log encoding) | – | – | ✓ (Prop 6) |
| Memory | explicit O(n²) graph | explicit mixed graph | O(Σ arity), no edge list |
| Independent equivalence audit | – | – | ✓ |
| SDP (θ, θ⁺) optimality certificates, solver-independent | – | – | ✓ (Prop 9) |
| Non-Clifford (T / Toffoli) depth with free Cliffords | partial (Toffoli, commuting) | – | ✓ (Prop 10) |
| Commutation-aware routing + layering | – | – | ✓ (Prop 11) |
| State-aware idle-noise scoring | – | – | ✓ (Prop 12) |
