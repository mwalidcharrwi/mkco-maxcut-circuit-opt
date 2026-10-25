| Question | Lee et al. 2026 | Jain & Kumar 2026 | **MKCO (ours)** |
|---|---|---|---|
| Total depth, reorder-only (9 circuits) | no gain on any circuit | same depths as MKCO, uncertified | −1.9% to −5.2% on 7 circuits; **certified optimal on 9/9** |
| Two-qubit depth | already optimal or no gain | optimal on 9/9 (uncertified) | **certified optimal on 9/9** |
| Crosstalk-prone ECR pairs at optimal 2q-depth | cannot express | cannot express | **−1.8% to −25.9%** (mean −14.2%) |
| Gate rewriting vs Qiskit O3 on a device Target (all outputs executable) | – | – | MKCO-full **shallower on 9/9** (−3.4% to −25.5%) and **faster (est. time) on 9/9**; MKCO after Qiskit removes a further 0.6–5.2% |
| Depth budget vs crosstalk (Pareto) | cannot express | cannot express | −21% to −44% pairs at +10% 2q-depth; −39% to −65% at +20% |
| F₂ⁿ multiplier (paper §5.1), n = 2…64 | optimal at 24/34 sizes | 7/34 | **34/34 (proven)** |
| Random multi-controlled-Z (paper §4.3), 60 circuits | 36/60 certified optimal | 0/60 | **41/60**; never worse than DSatur |
| Random CCZ (paper App. C), 50 circuits | 20/50 certified optimal | 17/50 | **49/50** |
| RZZ/QAOA layers (edge colouring), 18 circuits | 0/18 reach Δ | 0/18 | **14/18 reach Δ (optimal)** |
| Ancilla fan-out (paper §5.2) | heuristic not specified | – | up to **−24%** vs fixed copy split |

Every reordered output was independently verified: an exact pairwise
commutation audit, plus state-vector simulation for ≤ 20 active qubits.
