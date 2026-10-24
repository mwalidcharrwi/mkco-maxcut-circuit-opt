# Related work (study notes)

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
