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
    reordering, is shallower than Qiskit O3 on 8/9 benchmarks.
13. ✅ **Two-qubit block resynthesis (KAK) inside the run model** (MKCO-full).
    Finding: transpiled blocks are already ECR-optimal on 7 of 9 benchmarks
    (Table 8). Where KAK does find cheaper blocks (heisenberg_32, hubbard_18),
    locally cheaper blocks can *increase* global depth, because they destroy the
    cross-block rotation merging that MKCO's commutation runs enable. 🧪
    Commutation-aware block formation (E11) lets KAK see blocks that commuting
    gates had split. It removes CNOTs on 17/19 logical circuits, and ECRs that
    block KAK misses on hubbard_8 and on Qiskit's hubbard_18 output. ⭕ Scoring
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
  crosstalk mode, and composability with Qiskit. Max-k-Cut search matters on
  structured commuting workloads (E1–E4).
- **JK baseline.** No public code exists, so it was re-implemented from the
  published description. A learned independent-set generator could behave
  differently, but on the IBM circuits it cannot beat the certified optimum.
- **Crosstalk proxy.** The neighbouring-coupler model and the coupling graph
  inferred from used edges are proxies. Real gains should be validated with
  device calibration data or hardware runs. Anchor barriers keep the 2q-depth
  optimal but cost 0.8–7.6% in total depth (0.0–0.9% estimated duration).
- **Qiskit settings.** Device Target with native directed ECR edges, `ecr`
  mapped to `ECRGate`, trivial layout, `optimization_level=3`, one seed. Other
  seeds, optimization levels or Qiskit's approximation degree could change its
  numbers somewhat. Qiskit re-synthesises gates, so it is compared with MKCO's
  rewrite modes, not with reorder-only methods.
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
python experiments/run_qiskit.py                       # Qiskit O3 on a device Target (+ MKCO after it)
python experiments/add_merge.py && python experiments/add_rewrite.py && python experiments/add_full.py
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
