| Question | Lee et al. 2026 | Jain & Kumar 2026 | **MKCO (ours)** |
|---|---|---|---|
| Total depth, reorder-only (9 circuits) | no gain on any circuit | same depths as MKCO, uncertified | −1.9% to −5.2% on 7 circuits; **certified optimal on 9/9** |
| Two-qubit depth | already optimal or no gain | optimal on 9/9 (uncertified) | **certified optimal on 9/9** |
| Crosstalk-prone ECR pairs at optimal 2q-depth | cannot express | cannot express | **−1.8% to −25.9%** (mean −14.2%) |
| Gate rewriting vs Qiskit O3 on a device Target (all outputs executable) | – | – | MKCO-full **shallower on 9/9** (−3.4% to −25.5%) and **faster (est. time) on 9/9**; MKCO after Qiskit removes a further 0.6–5.2% |
| Depth budget vs crosstalk (Pareto) | cannot express | cannot express | −21% to −44% pairs at +10% 2q-depth; −39% to −65% at +20% |
| F₂ⁿ multiplier (paper §5.1), n = 2…64 | optimal at 24/34 sizes | 7/34 | **34/34 (proven)** |
| Random multi-controlled-Z (paper §4.3), 60 circuits | 42/60 certified optimal (36 by clique/Jackson, 6 more by θ/θ⁺) | 0/60 | **48/60** (41 + 7 more by θ/θ⁺); never worse than DSatur |
| Random CCZ (paper App. C), 50 circuits | 20/50 certified optimal | 17/50 | **49/50** |
| RZZ/QAOA layers (edge colouring), 18 circuits | 0/18 reach Δ | 0/18 | **14/18 reach Δ (optimal)** |
| Second IBM-127 set (4 circuits with measurements, Section 5.1) | no gain | ties, uncertified | depth and 2q-depth **certified optimal 4/4**; MKCO-full −0.5% to −3.0% vs Qiskit O3; noisy simulation: qpe_8 +3–4% fidelity vs O3 |
| Ancilla fan-out (paper §5.2) | heuristic not specified | – | up to **−24%** vs fixed copy split |
| T-depth with free Cliffords, after PyZX (17 Clifford+T circuits, E8) | – | – | **−10% to −69%** (mean −41%) vs PyZX alone; 17/17 certified optimal |
| Toffoli-depth, GF(2ⁿ) multipliers n = 4–12 (E8) | commuting parts only | – | **−53% to −64%** vs input; 6/8 certified |
| Routing on the 127-qubit heavy-hex device vs Qiskit O3 (13 circuits, E9) | – | – | QAOA (7): **−3.8% to −21.9% CNOTs, up to −55% depth**; Trotter shallower; QFT worse (+11–25% CNOTs) |
| Block formation before KAK (19 logical circuits, E11) | – | – | fewer CNOTs than plain block KAK on **17/19**, never more |
| Noise with ibm_brisbane calibration (9 circuits, E10) | – | – | state-aware ESP orders method pairs like density-matrix simulation in **97%** of cases (state-blind ESP 66%); `mkco_noise` beats Qiskit O3 on **9/9** |

Every reordered output was independently verified: an exact pairwise
commutation audit, plus state-vector simulation for ≤ 20 active qubits.
