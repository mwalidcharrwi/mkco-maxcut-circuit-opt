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
