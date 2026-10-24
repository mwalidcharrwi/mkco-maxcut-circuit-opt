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
4. **Certifies its answers.** A run-serialised Jackson lower bound (Theorem 7)
   proves optimality. An independent commutation audit, plus state-vector
   simulation for ≤ 20 active qubits, verifies every output.

**Comparison against the related work.** Lee et al. 2026 and Jain & Kumar 2026
are run on identical inputs:
- rows 1–5: the 9 provided IBM-127-transpiled benchmarks (rz/sx/x/ecr,
  1.9k–358k gates);
- rows 6–10: the paper's own experimental settings and structured commuting
  circuits.

| Question | Lee et al. 2026 | Jain & Kumar 2026 | **MKCO (ours)** |
|---|---|---|---|
| Total depth, reorder-only (9 circuits) | no gain on any circuit | same depths as MKCO, uncertified | −1.9% to −5.2% on 7 circuits; **certified optimal on 9/9** |
| Two-qubit depth | already optimal or no gain | optimal on 9/9 (uncertified) | **certified optimal on 9/9** |
| Crosstalk-prone ECR pairs at optimal 2q-depth | cannot express | cannot express | **−1.8% to −25.9%** (mean −14.2%) |
| After Qiskit O3 (re-synthesis) | – | – | further 0% to −5.2%; certified optimal for Qiskit's gate list |
| Rewrite mode (1q ZSX resynthesis + reordering) vs Qiskit O3 | – | – | **shallower on 8/9** (heisenberg_32: 3,011 vs 3,538); best overall on 9/9 when composed with Qiskit |
| F₂ⁿ multiplier (paper §5.1), n = 2…64 | optimal at 24/34 sizes | 7/34 | **34/34 (proven)** |
| Random multi-controlled-Z (paper §4.3), 60 circuits | 36/60 certified optimal | 0/60 | **41/60**; never worse than DSatur |
| Random CCZ (paper App. C), 50 circuits | 20/50 certified optimal | 17/50 | **49/50** |
| RZZ/QAOA layers (edge colouring), 18 circuits | 0/18 reach Δ | 0/18 | **14/18 reach Δ (optimal)** |
| Ancilla fan-out (paper §5.2) | heuristic not specified | – | up to **−24%** vs fixed copy split |

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
Optional pre-pass (rewrite mode): single-qubit ZSX resynthesis + run-based rotation merging,
        iterated to a fixed point; every fused chain is checked numerically
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

**Methods.** Every method sees the same input file.
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
- `qiskit_o3`: Qiskit 2.6, `optimization_level=3`, basis `rz,sx,x,ecr`,
  trivial layout, coupling map = directed edges used by the circuit. This
  *re-synthesises* gates, so it belongs to a different transformation class.
- `qiskit_o3+mkco`: our reordering applied to Qiskit's output.
- `mkco_rewrite`: our rewrite mode. Each maximal chain of single-qubit gates
  is re-synthesised in the device basis (rz/sx/x) by ZSX Euler decomposition,
  same-axis rotations are merged across commuting two-qubit gates, and the
  result is reordered by MKCO. Qiskit O3 also re-synthesises two-qubit
  blocks, which MKCO does not.
- `qiskit_o3+mkco_rewrite`: our rewrite mode applied to Qiskit's output.

**Verification.** Every reordered output passes two independent checks:
1. the structural certificate (a linear extension of the dependency order);
2. the commutation audit (every pair whose order changed commutes, checked on
   exact matrices).

Outputs with at most 20 active qubits are additionally checked by state-vector
simulation on random inputs (global phase compared). A negative control — one
illegal swap — fails both the audit and the simulation.

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

**Gate rewriting vs Qiskit (Table 4).** Qiskit O3 re-synthesises gates, so
the fair comparison is MKCO's *rewrite mode*: single-qubit ZSX resynthesis
plus run-based rotation merging, then Max-k-Cut reordering.
- **Rewrite mode beats Qiskit O3 on 8 of 9 circuits.**
  - On the two Hamiltonian-simulation circuits, long rz/sx chains collapse
    under resynthesis, and rewrite mode goes further than Qiskit. heisenberg_32:
    7,143 → **3,011**, 15% shallower than Qiskit's 3,538, with a lower
    two-qubit depth as well (881 vs 936).
  - On the other circuits Qiskit O3 often makes depth *worse* (+0.2% to +5.2%
    in 6 cases), mainly from the gates it adds to re-orient re-synthesised ECRs.
- **The exception is hubbard_18.** Qiskit's two-qubit block resynthesis (KAK),
  which MKCO does not perform, gives 65,436 against rewrite mode's 72,992.
- **Composition wins there.** Qiskit O3 → MKCO rewrite gives **64,969**, the
  best result for that circuit, and also the best on hubbard_8 (4,229).
- **MKCO is part of the best pipeline on all 9 circuits.** Every MKCO result is
  certified optimal for the gate list it reorders, and rewrite-mode outputs
  match the *original* circuit under state-vector simulation (≤ 20 qubits).

**Correctness (Table 7).** All reordered outputs (99 audits) pass the independent
commutation audit (14,222 reordered gate pairs checked on grover_10 alone).
Every MKCO output with ≤ 20 active qubits also matches the input under
state-vector simulation (fidelity 1 to 10 digits, global phase consistent).

**Runtime (Table 6).** MKCO runs in 0.1–20 s, faster than block-wise colouring
on every circuit and comparable to Jain & Kumar. The crosstalk mode uses its
time budget (30–60 s).

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

### Table 4 - Gate-rewriting class: MKCO rewrite mode vs Qiskit O3, and their composition

Depth (lower is better). MKCO-rewrite = single-qubit ZSX resynthesis + run merging, then Max-k-Cut reordering; every MKCO result is certified optimal for the gate list it reorders.

| Circuit | Original | MKCO (reorder) | **MKCO-rewrite** | Qiskit O3 | O3 + MKCO | **O3 + MKCO-rewrite** | Best | Who wins |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| mult_8 | 1138 | 1102 | **1102** | 1172 | 1136 | **1136** | 1102 | MKCO-rewrite |
| add_17 | 1003 | 964 | **964** | 1026 | 988 | **988** | 964 | MKCO-rewrite |
| qae_17 | 1066 | 1035 | **1030** | 1084 | 1055 | **1051** | 1030 | MKCO-rewrite |
| qft_16 | 1009 | 980 | **980** | 1026 | 997 | **997** | 980 | MKCO-rewrite |
| hubbard_8 | 4400 | 4268 | **4251** | 4382 | 4246 | **4229** | 4229 | O3 + MKCO |
| hhl_8 | 10641 | 10434 | **10434** | 11190 | 10983 | **10983** | 10434 | MKCO-rewrite |
| heisenberg_32† | 7143 | 7143 | **3011** | 3538 | 3538 | **3534** | 3011 | MKCO-rewrite |
| grover_10 | 43923 | 41641 | **41631** | 43995 | 41713 | **41703** | 41631 | MKCO-rewrite |
| hubbard_18† | 136644 | 136637 | **72992** | 65436 | 65339 | **64969** | 64969 | O3 + MKCO |

| Circuit | 2q-depth MKCO-rewrite | 2q-depth Qiskit O3 | gates MKCO-rewrite | gates Qiskit O3 | duration MKCO-rewrite (us) | duration Qiskit O3 (us) | duration O3+MKCO-rewrite (us) |
|---|---:|---:|---:|---:|---:|---:|---:|
| mult_8 | 276 | 276 | 1897 | 1958 | 158.69 | 160.29 | 159.04 |
| add_17 | 255 | 253 | 2812 | 2918 | 145.42 | 145.78 | 145.07 |
| qae_17 | 274 | 274 | 3019 | 3090 | 156.44 | 157.55 | 156.62 |
| qft_16 | 260 | 260 | 3422 | 3518 | 148.23 | 149.26 | 148.37 |
| hubbard_8 | 1112 | 1111 | 8091 | 8059 | 634.60 | 637.83 | 633.17 |
| hhl_8 | 2319 | 2319 | 18165 | 19098 | 1359.51 | 1369.96 | 1364.06 |
| heisenberg_32 | 881 | 936 | 20324 | 23089 | 499.95 | 540.09 | 539.59 |
| grover_10 | 10895 | 10895 | 92654 | 93398 | 6220.96 | 6293.25 | 6221.60 |
| hubbard_18 | 21766 | 19938 | 170310 | 156700 | 12313.54 | 11450.49 | 11419.26 |

† Qiskit could not re-orient the ECRs it re-synthesised on the native (directed) coupling map, so it was re-run with a bidirectional map (favourable to Qiskit).


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

| Circuit | Lee'26 | JK'26 | MKCO | MKCO-2q | MKCO-XT | Qiskit O3 | MKCO after O3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| mult_8 | 0.3 | 0.2 | 0.1 | 0.1 | 4.4 | 3.8 | 0.4 |
| add_17 | 0.5 | 0.2 | 0.2 | 0.2 | 23.6 | 5.7 | 0.2 |
| qae_17 | 0.5 | 0.2 | 0.2 | 0.1 | 21.0 | 6.4 | 0.2 |
| qft_16 | 0.5 | 0.2 | 0.2 | 0.1 | 30.1 | 9.6 | 0.2 |
| hubbard_8 | 1.3 | 1.3 | 0.7 | 0.3 | 30.2 | 15.4 | 0.4 |
| hhl_8 | 2.8 | 6.2 | 1.1 | 0.7 | 30.1 | 26.5 | 1.1 |
| heisenberg_32 | 8.4 | 1.6 | 3.6 | 1.9 | 60.5 | 24.6 | 2.7 |
| grover_10 | 14.3 | 3.1 | 5.7 | 3.7 | 60.9 | 183.5 | 5.7 |
| hubbard_18 | 44.0 | 11.0 | 19.9 | 11.8 | 62.5 | 246.9 | 20.7 |

### Table 7 - Verification of every reordered output

| Circuit | Active qubits | Commutation audit (all reorderings) | Inverted pairs checked (MKCO) | State-vector check (MKCO) | State-vector check (MKCO-rewrite, vs original) |
|---|---:|:---:|---:|:---:|:---:|
| mult_8 | 8 | 11/11 pass | 75 | pass (F=1.0000000000) | pass (F=1.0000000000) |
| add_17 | 17 | 11/11 pass | 129 | pass (F=1.0000000000) | pass (F=1.0000000000) |
| qae_17 | 17 | 11/11 pass | 142 | pass (F=1.0000000000) | pass (F=1.0000000000) |
| qft_16 | 16 | 11/11 pass | 166 | pass (F=1.0000000000) | pass (F=1.0000000000) |
| hubbard_8 | 8 | 11/11 pass | 260 | pass (F=1.0000000000) | pass (F=1.0000000000) |
| hhl_8 | 8 | 11/11 pass | 333 | pass (F=1.0000000000) | pass (F=1.0000000000) |
| heisenberg_32 | 32 | 11/11 pass | 0 | n/a (>20 qubits) | n/a (>20 qubits) |
| grover_10 | 10 | 11/11 pass | 14222 | pass (F=1.0000000000) | pass (F=1.0000000000) |
| hubbard_18 | 31 | 11/11 pass | 2654 | n/a (>20 qubits) | n/a (>20 qubits) |

## 6. Results in the settings of Lee et al. and on structured commuting circuits

These experiments reproduce the settings of Lee et al. They are the regime
where the *search* component of MKCO matters, because the conflict graphs are
not trivially colourable.

- **E1 – the paper's random benchmark (Fig. 1 setting: m = 10/20/30 qubits,
  n = 50–200 multi-controlled-Z gates, 5 seeds each, 60 circuits).**
  - MKCO is certified optimal on **41/60** (DSatur 36/60, JK 0/60). It is
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
- **E3 – Appendix C (random CCZ on 10 qubits).** MKCO is certified optimal on
  49/50 circuits (DSatur 20/50, JK 17/50), strictly better than DSatur on 30,
  and never worse. Where 10 s of backtracking could prove the optimum
  (19 circuits), MKCO equals it. At 40–50 gates MKCO also beats
  time-limited backtracking.
- **E4 – commuting two-qubit layers (QAOA cost layers = edge colouring).**
  MKCO reaches Vizing's lower bound Δ on 14 of 18 graphs. DSatur and JK never
  do: they land 1–3.7 layers above Δ on average.
- **E5 – quantum-ready path.** Hierarchical Max-Cut with a QAOA backend (p = 3,
  state-vector) solved every Ising sub-problem to optimality (21/21) and
  produced the same layering as exact enumeration. The log encoding needs
  20–64 spins where one-hot colouring needs 40–176. HMC is optimal on all 4
  instances. On gf2_4 it gives 5 layers against a bound of 4, but exhaustive
  backtracking proves 5 is the optimum, so the bound is loose there.
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

## 7. Research directions opened by the Max-Cut view

Items marked ✅ are implemented and evaluated here; 🧪 are implemented with a
small demonstration; ⭕ are open problems we identified.

1. ✅ **Exact general-circuit reduction (Thm 1) and the Max-k-Cut
   characterisation (Thm 2).** This closes the paper's main limitation (commuting
   circuits only) with a linear-memory model.
2. ✅ **Certified depth bounds (Thm 7).** Optimality proven on all 9 IBM
   benchmarks and on the F₂ⁿ multiplier. Stronger certificates are open
   (⭕ Lovász-θ / vector-chromatic SDP bounds for commuting blocks, via the
   Karger–Motwani–Sudan relaxation that Max-k-Cut SDPs already compute).
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
   under a hard latency or coherence budget. Proposition 3 then bounds the
   repaired depth.
7. ⭕ **Lexicographic / Pareto objectives.** Total depth vs two-qubit depth vs
   crosstalk. The data show real tensions (add_17: depth-optimal costs +2 ECR
   layers; crosstalk mode costs +0.8–7.6% total depth). A multi-objective
   Max-k-Cut (weights per objective) is the natural tool.
8. ⭕ **T-depth / Toffoli-depth with free Cliffords.** This needs
   zero-duration multi-qubit gates, i.e. cross-wire transparent nodes in the
   run structure.
9. ⭕ **Joint routing + layering.** Treat SWAP insertion as extra gates whose
   placement is a Max-k-Cut variable on hardware with restricted connectivity.
10. ⭕ **Min-cut / Max-cut duality for distributed QC.** Partitioning qubits
    across QPUs is a min-cut; layering is a max-cut; a joint QUBO couples them.
11. ⭕ **Learned warm starts.** Jain & Kumar's learned independent-set generator
    could seed the Max-k-Cut search instead of competing with it.
12. ✅ **Single-qubit resynthesis inside the run structure** (rewrite mode).
    ZSX re-synthesis of 1q chains plus run-based merging, followed by Max-k-Cut
    reordering, is shallower than Qiskit O3 on 8/9 benchmarks.
13. ⭕ **Two-qubit block resynthesis (KAK) inside the run model.** This is the
    one transformation where Qiskit O3 still wins (hubbard_18). Adding it as a
    pre-pass, with the Max-k-Cut layering after it, is the natural next step.

## 8. Limitations and threats to validity

- **Benchmark difficulty.** On the 9 transpiled benchmarks, commutation-aware
  list scheduling already meets the certified bound. Every layering method that
  uses commutation (JK and MKCO) therefore reaches the same optimal depth.
  MKCO's distinctive contributions there are the *proof* of optimality, the
  crosstalk mode, and composability with Qiskit. Max-k-Cut search matters on
  structured commuting workloads (E1–E4).
- **JK baseline.** No public code exists, so it was re-implemented from the
  published description. A learned independent-set generator could behave
  differently, but on the IBM circuits it cannot beat the certified optimum.
- **Crosstalk proxy.** The neighbouring-coupler model and the coupling graph
  inferred from used edges are proxies. Real gains should be validated with
  device calibration data or hardware runs. Anchor barriers keep the 2q-depth
  optimal but cost 0.8–7.6% in total depth (0.0–0.9% estimated duration).
- **Qiskit settings.** Coupling map = edges used by each circuit. Two circuits
  needed a bidirectional retry (marked †), which favours Qiskit. Qiskit
  re-synthesises gates, so its depths are compared with MKCO's rewrite mode
  (same transformation class, except that MKCO does not re-synthesise
  two-qubit blocks) rather than with reorder-only methods.
- **Durations** are nominal Eagle values, not device calibrations.
- **Runtimes** are single-process Python on a laptop, measured while other
  experiments shared the machine, so treat them as indicative. MKCO stops early
  when the bound is met.

## 9. Reproducing everything

```bash
python experiments/run_ibm127.py benchmarks/ibm127     # all methods, verification, QASM outputs
python experiments/fill_qiskit.py                      # Qiskit retry where needed
python experiments/add_merge.py && python experiments/add_rewrite.py   # merge / rewrite modes
python experiments/summarize_ibm127.py                 # tables -> results/ibm127/tables.md
python experiments/run_structured.py                   # E1-E6 -> results/structured/*.json
python experiments/summarize_structured.py
python experiments/plots.py                            # figures -> docs/figures
python tests/test_core.py && python tests/test_gates_vs_qiskit.py
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

## Appendix A. Theory: statements and proofs


Notation. A circuit is a sequence of gates `g_1 … g_N`. `supp(g)` is the set of
wires (qubits and classical bits) that `g` touches. Two gates *conflict* when
their supports intersect. For a layering, *unit* gates take one layer;
*zero-duration* gates (single-wire gates when the objective is the two-qubit
depth) take none.

---

## 1. Commutation and equivalent reorderings

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

## 2. Depth minimisation = mixed-graph colouring

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

## 3. The Max-k-Cut formulation

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

## 4. Max-Cut is per-wire load balancing (hierarchical Max-Cut)

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

## 5. Certified lower bounds

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

## 6. Window decomposition (general circuits)

**Proposition 8 (window isolation).** Take a feasible layering and a window of
layers `[a,b]`, and let `W` be the gates in it. Every chain between two gates
of `W` stays inside `[a,b]`. Moving `W` into `[a,b−1]` and shifting the later
layers down by one is therefore feasible iff `W` alone admits a
`(b−a)`-colouring of its mixed sub-graph. That is an isolated, small
precedence-constrained Max-k-Cut. MKCO solves these windows with exact
enumeration (or tabu / QAOA) inside a large-neighbourhood search, with
forward–backward justification between sweeps.

## Appendix B. Related-work study notes


## The base paper
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

## Direct follow-up
**Jain & Kumar, "Quantum Circuit Depth Optimization using Graph Coloring", NeurIPS 2026 (WiML affinity poster).**

This work extends Lee et al. to non-commuting circuits with a mixed graph:
directed arcs for dependencies, undirected edges for commuting gates that share
a qubit. It repeatedly extracts large independent sets from the executable
(in-degree-0) subgraph, using a learned independent-set generator (after Li et
al. 2018) and a guided beam search. The authors compare only against Qiskit's
DAG depth of the given order. No code or numbers are public, so
`mkco/jk.py` is a re-implementation from the published description.

## Colouring and partitioning in quantum compilation
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

## Max-Cut / Max-k-Cut and colouring theory
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

## Quantum solvers for Max-k-Cut
- QAOA (Farhi et al., arXiv:1411.4028).
- Binary / log encodings of Max-k-Cut using |V|·log₂k qubits (Fuchs et al.,
  arXiv:2411.08594).
- Logarithmic HUBO encodings for colouring (2026 preprint).

## Ancilla parallelisation of diagonal gates
- Fan-out: copy, apply diagonal gates in parallel, uncopy (Moore & Nilsson,
  quant-ph/9804034).
- Recent depth-optimal diagonal synthesis on grids (arXiv:2606.17589).

## Positioning of MKCO
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
