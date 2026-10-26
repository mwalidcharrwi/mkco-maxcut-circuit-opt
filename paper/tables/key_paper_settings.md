| Setting (Lee et al.) | Instances | Lee et al. (DSatur) | Jain & Kumar | **MKCO** | Note |
|---|---:|---:|---:|---:|---|
| E1 random multi-controlled-Z (§4.3), m=10/20/30, n=50–200 | 60 | 42/60 | 0/60 | **48/60** | mean layers above best proven bound: DSatur 1.08, JK 12.1, MKCO 0.42 |
| E2 F₂ⁿ multiplier Toffoli-depth (§5.1), n = 2…64 | 34 sizes | 24/34 | 7/34 | **34/34** | optimum = 2n−1 for n ≥ 6; n ≤ 5 proven by exhaustive search |
| E3 random CCZ on 10 qubits (App. C) | 50 | 20/50 | 17/50 | **49/50** | MKCO strictly better than DSatur on 30 |
| E4 commuting RZZ / QAOA layers (edge colouring) | 18 | 0/18 | 0/18 | **14/18** | reaching Vizing's bound Δ; mean excess DSatur 2.1, JK 2.1, MKCO 0.22 |
| E6 ancilla fan-out (§5.2, capacitated Max-k-Cut) | 20 | – | – | up to **24%** shallower | vs round-robin copies + DSatur (mcz_m20_n120, c=4: 21 → 16) |

Counts are instances where the method meets the best proven lower bound (clique / Jackson, Lovász θ, Szegedy θ⁺, or exhaustive search).
