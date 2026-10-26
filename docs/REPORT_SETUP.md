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
