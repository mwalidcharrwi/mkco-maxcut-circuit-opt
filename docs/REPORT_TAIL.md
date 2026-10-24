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
