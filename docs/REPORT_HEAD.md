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

<!-- HEADLINE -->

## 2. What the base paper leaves open (and what MKCO does about it)

| Open point in Lee et al. | MKCO |
|---|---|
| Only commuting circuits (§6) | Exact reduction for arbitrary circuits via a mixed graph (Thm 1); O(Σ arity) memory |
| Hardware restrictions "highly nontrivial" (§6) | Hardware penalties become weighted soft edges of the Max-k-Cut (Thm 2); crosstalk mode on IBM heavy-hex |
| DSatur vs exact gap "open for further experiment" (§4.3) | Answered: on the paper's random circuits DSatur is within 0–0.8 layers of the maximum clique for m ≥ 20 qubits but 4.6–5.2 layers above the bound at m = 10, n ≥ 150, where MKCO cuts the gap by more than half; on structured circuits (F₂ⁿ multiplier, CCZ, RZZ layers) MKCO closes DSatur's gap to the certified bound |
| DSatur misses 2n−1 for some n < 20 (fn. 2) | MKCO is optimal for every n = 2…64 (bound 2n−1 for n ≥ 6, exhaustive proof for n ≤ 5); DSatur is sub-optimal at 10 sizes |
| Extra-qubit parallelisation algorithm not given (§5.2) | Capacitated Max-k-Cut (wire capacity = number of fan-out copies), implemented and verified (E6): up to 24% shallower than a fixed copy split |
| No optimality certificate beyond Eq. (2) | Stronger certified bound (Thm 7); optimality proven on every IBM benchmark |
