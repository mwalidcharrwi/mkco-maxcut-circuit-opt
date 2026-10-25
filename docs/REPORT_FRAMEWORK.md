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
