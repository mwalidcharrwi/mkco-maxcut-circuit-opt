### Table 1 - Total depth, reorder-only methods (lower is better)

| Circuit | Gates | Original | Lee'26 (colouring) | JK'26 (MIS+beam) | **MKCO** | Certified LB | MKCO optimal? | MKCO vs original |
|---|---:|---:|---:|---:|---:|---:|:---:|---:|
| mult_8 | 1898 | 1138 | 1138 | 1102 | **1102** | 1102 | yes | -3.16% |
| add_17 | 2812 | 1003 | 1003 | 964 | **964** | 964 | yes | -3.89% |
| qae_17 | 3033 | 1066 | 1066 | 1035 | **1035** | 1035 | yes | -2.91% |
| qft_16 | 3444 | 1009 | 1009 | 980 | **980** | 980 | yes | -2.87% |
| hubbard_8 | 8125 | 4400 | 4400 | 4268 | **4268** | 4268 | yes | -3.00% |
| hhl_8 | 18165 | 10641 | 10641 | 10434 | **10434** | 10434 | yes | -1.95% |
| heisenberg_32 | 58848 | 7143 | 7143 | 7143 | **7143** | 7143 | yes | +0.00% |
| grover_10 | 93235 | 43923 | 43923 | 41641 | **41641** | 41641 | yes | -5.20% |
| hubbard_18 | 357535 | 136644 | 136644 | 136637 | **136637** | 136637 | yes | -0.01% |

### Table 2 - Two-qubit (ECR) depth, reorder-only methods optimising 2q-depth

| Circuit | Original | Lee'26 | JK'26 | **MKCO** | Certified LB | MKCO optimal? |
|---|---:|---:|---:|---:|---:|:---:|
| mult_8 | 276 | 276 | 276 | **276** | 276 | yes |
| add_17 | 253 | 253 | 253 | **253** | 253 | yes |
| qae_17 | 274 | 274 | 274 | **274** | 274 | yes |
| qft_16 | 260 | 260 | 260 | **260** | 260 | yes |
| hubbard_8 | 1111 | 1111 | 1110 | **1110** | 1110 | yes |
| hhl_8 | 2319 | 2319 | 2319 | **2319** | 2319 | yes |
| heisenberg_32 | 881 | 881 | 881 | **881** | 881 | yes |
| grover_10 | 10895 | 10895 | 10895 | **10895** | 10895 | yes |
| hubbard_18 | 21769 | 21769 | 21766 | **21766** | 21766 | yes |

### Table 3 - Crosstalk-prone ECR pairs (same layer, neighbouring couplers) at optimal 2q-depth

| Circuit | Original | Lee'26 | JK'26 | MKCO (2q mode) | **MKCO-XT** | Reduction vs best baseline | 2q-depth orig -> XT | Total depth orig -> XT |
|---|---:|---:|---:|---:|---:|---:|---|---|
| mult_8 | 31 | 31 | 31 | 31 | **23** | -25.8% | 276 -> 276 | 1138 -> 1154 |
| add_17 | 151 | 151 | 151 | 151 | **144** | -4.6% | 253 -> 253 | 1003 -> 1019 |
| qae_17 | 165 | 165 | 165 | 165 | **138** | -16.4% | 274 -> 274 | 1066 -> 1075 |
| qft_16 | 210 | 210 | 210 | 210 | **195** | -7.1% | 260 -> 260 | 1009 -> 1027 |
| hubbard_8 | 166 | 166 | 167 | 167 | **130** | -21.7% | 1111 -> 1110 | 4400 -> 4415 |
| hhl_8 | 56 | 56 | 56 | 56 | **55** | -1.8% | 2319 -> 2319 | 10641 -> 10658 |
| heisenberg_32 | 1234 | 1234 | 1234 | 1234 | **1087** | -11.9% | 881 -> 881 | 7143 -> 7687 |
| grover_10 | 4431 | 4431 | 4431 | 4431 | **3870** | -12.7% | 10895 -> 10895 | 43923 -> 45858 |
| hubbard_18 | 7332 | 7332 | 7336 | 7334 | **5435** | -25.9% | 21769 -> 21766 | 136644 -> 137968 |

### Table 4 - Gate-rewriting class: MKCO rewrite modes vs Qiskit O3 (device target), and composition

Depth (lower is better). Qiskit O3 runs on a Target with ECRs only on the native directed edges, so every output below is executable on the device (0 reversed ECRs). MKCO-rewrite = single-qubit ZSX resynthesis + run merging + Max-k-Cut reordering; MKCO-full adds two-qubit KAK block resynthesis. Every MKCO result is certified optimal for the gate list it reorders.

| Circuit | Original | MKCO (reorder) | MKCO-rewrite | **MKCO-full** | Qiskit O3 | O3 + MKCO | O3 + MKCO-rewrite | Best | MKCO-full vs Qiskit O3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| mult_8 | 1138 | **1102** | **1102** | **1102** | 1173 | 1137 | 1137 | 1102 | -6.1% |
| add_17 | 1003 | **964** | **964** | **964** | 1026 | 988 | 988 | 964 | -6.0% |
| qae_17 | 1066 | 1035 | **1030** | **1030** | 1084 | 1055 | 1051 | 1030 | -5.0% |
| qft_16 | 1009 | **980** | **980** | **980** | 1026 | 997 | 997 | 980 | -4.5% |
| hubbard_8 | 4400 | 4268 | 4251 | 4241 | 4390 | 4256 | **4239** | 4239 | -3.4% |
| hhl_8 | 10641 | **10434** | **10434** | **10434** | 11212 | 11005 | 11005 | 10434 | -6.9% |
| heisenberg_32 | 7143 | 7143 | **3011** | **3011** | 4039 | 4039 | 4013 | 3011 | -25.5% |
| grover_10 | 43923 | 41641 | **41631** | **41631** | 43995 | 41713 | 41703 | 41631 | -5.4% |
| hubbard_18 | 136644 | 136637 | **72992** | **72992** | 84761 | 84698 | 84134 | 72992 | -13.9% |

**Hardware-time view.** MKCO-full (duration objective) keeps, per circuit, the candidate with the lowest estimated execution time among {KAK + 1q rewrite, 1q rewrite} x {reorder for depth, for 2q-depth}.

| Circuit | est. duration original (us) | Qiskit O3 (us) | MKCO-full, depth obj. (us) | **MKCO-full, duration obj. (us)** | vs Qiskit | 2q-depth Qiskit / MKCO-dur | ECRs Qiskit / MKCO-dur | depth Qiskit / MKCO-dur | reversed ECRs |
|---|---:|---:|---:|---:|---:|---|---|---|---|
| mult_8 | 159.89 | 160.29 | 158.69 | **158.69** | -1.0% | 276 / 276 | 311 / 311 | 1173 / 1102 | 0 / 0 |
| add_17 | 145.60 | 145.78 | 145.42 | **145.42** | -0.2% | 253 / 255 | 499 / 499 | 1026 / 964 | 0 / 0 |
| qae_17 | 157.37 | 157.55 | 156.44 | **156.44** | -0.7% | 274 / 274 | 541 / 541 | 1084 / 1030 | 0 / 0 |
| qft_16 | 149.12 | 149.26 | 148.23 | **148.23** | -0.7% | 260 / 260 | 614 / 614 | 1026 / 980 | 0 / 0 |
| hubbard_8 | 638.05 | 637.94 | 633.96 | **633.96** | -0.6% | 1111 / 1111 | 1344 / 1344 | 4390 / 4241 | 0 / 0 |
| hhl_8 | 1365.41 | 1369.96 | 1359.51 | **1359.51** | -0.8% | 2319 / 2319 | 2377 / 2377 | 11212 / 10434 | 0 / 0 |
| heisenberg_32 | 549.16 | 542.37 | 499.95 | **499.95** | -7.8% | 936 / 881 | 4071 / 3942 | 4039 / 3011 | 0 / 0 |
| grover_10 | 6292.61 | 6293.25 | 6220.96 | **6220.96** | -1.1% | 10895 / 10895 | 16397 / 16397 | 43995 / 41631 | 0 / 0 |
| hubbard_18 | 13230.21 | 11565.99 | 12313.54 | **10891.42** | -5.8% | 19938 / 18795 | 33586 / 30453 | 84761 / 80677 | 0 / 0 |

### Table 5 - Estimated execution time (us; ECR 533 ns, sx/x 36 ns, rz virtual)

| Circuit | Original | Lee'26 | JK'26 | MKCO (depth) | MKCO (2q) | MKCO-XT |
|---|---:|---:|---:|---:|---:|---:|
| mult_8 | 159.89 | 159.89 | 158.69 | 158.69 | 159.89 | 160.39 |
| add_17 | 145.60 | 145.60 | 145.42 | 145.42 | 145.56 | 145.74 |
| qae_17 | 157.37 | 157.37 | 156.52 | 156.52 | 157.37 | 157.51 |
| qft_16 | 149.12 | 149.12 | 148.23 | 148.23 | 149.08 | 149.37 |
| hubbard_8 | 638.05 | 638.05 | 634.95 | 634.95 | 637.12 | 637.55 |
| hhl_8 | 1365.41 | 1365.41 | 1359.51 | 1359.51 | 1365.41 | 1365.77 |
| heisenberg_32 | 549.16 | 549.16 | 549.16 | 549.16 | 549.16 | 552.58 |
| grover_10 | 6292.61 | 6292.61 | 6221.17 | 6221.17 | 6292.61 | 6347.09 |
| hubbard_18 | 13230.21 | 13230.21 | 13228.79 | 13187.43 | 13228.57 | 13256.92 |

### Table 6 - Runtime (s)

| Circuit | Lee'26 | JK'26 | MKCO | MKCO-2q | MKCO-XT | MKCO-full | Qiskit O3 (target) | MKCO after O3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| mult_8 | 0.3 | 0.2 | 0.1 | 0.1 | 4.4 | 3.7 | 0.1 | 0.2 |
| add_17 | 0.5 | 0.2 | 0.2 | 0.2 | 23.6 | 1.3 | 0.0 | 0.3 |
| qae_17 | 0.5 | 0.2 | 0.2 | 0.1 | 21.0 | 3.6 | 0.1 | 0.4 |
| qft_16 | 0.5 | 0.2 | 0.2 | 0.1 | 30.1 | 7.5 | 0.1 | 0.3 |
| hubbard_8 | 1.3 | 1.3 | 0.7 | 0.3 | 30.2 | 17.1 | 0.1 | 0.8 |
| hhl_8 | 2.8 | 6.2 | 1.1 | 0.7 | 30.1 | 14.5 | 0.1 | 1.8 |
| heisenberg_32 | 8.4 | 1.6 | 3.6 | 1.9 | 60.5 | 49.5 | 0.4 | 2.5 |
| grover_10 | 14.3 | 3.1 | 5.7 | 3.7 | 60.9 | 90.5 | 0.6 | 9.4 |
| hubbard_18 | 44.0 | 11.0 | 19.9 | 11.8 | 62.5 | 378.1 | 4.6 | 25.4 |

### Table 7 - Verification of every reordered output

| Circuit | Active qubits | Commutation audit (all reorderings) | Inverted pairs checked (MKCO) | State-vector check (MKCO) | State-vector (MKCO-rewrite, vs original) | State-vector (MKCO-full dur., vs original) |
|---|---:|:---:|---:|:---:|:---:|:---:|
| mult_8 | 8 | 13/13 pass | 75 | pass (F=1.0000000000) | pass (F=1.0000000000) | pass (F=1.0000000000) |
| add_17 | 17 | 13/13 pass | 129 | pass (F=1.0000000000) | pass (F=1.0000000000) | pass (F=1.0000000000) |
| qae_17 | 17 | 13/13 pass | 142 | pass (F=1.0000000000) | pass (F=1.0000000000) | pass (F=1.0000000000) |
| qft_16 | 16 | 13/13 pass | 166 | pass (F=1.0000000000) | pass (F=1.0000000000) | pass (F=1.0000000000) |
| hubbard_8 | 8 | 13/13 pass | 260 | pass (F=1.0000000000) | pass (F=1.0000000000) | pass (F=1.0000000000) |
| hhl_8 | 8 | 13/13 pass | 333 | pass (F=1.0000000000) | pass (F=1.0000000000) | pass (F=1.0000000000) |
| heisenberg_32 | 32 | 13/13 pass | 0 | n/a (>20 qubits) | n/a (>20 qubits) | n/a (>20 qubits) |
| grover_10 | 10 | 13/13 pass | 14222 | pass (F=1.0000000000) | pass (F=1.0000000000) | pass (F=1.0000000000) |
| hubbard_18 | 31 | 13/13 pass | 2654 | n/a (>20 qubits) | n/a (>20 qubits) | n/a (>20 qubits) |

### Table 8 - Two-qubit block (KAK) resynthesis: blocks that become cheaper in native ECRs

| Circuit | two-qubit blocks | cheaper after KAK | ECRs removed |
|---|---:|---:|---:|
| mult_8 | 151 | 0 | 0 |
| add_17 | 198 | 0 | 0 |
| qae_17 | 213 | 0 | 0 |
| qft_16 | 237 | 0 | 0 |
| hubbard_8 | 695 | 1 | 0 |
| hhl_8 | 1433 | 1 | 0 |
| heisenberg_32 | 1594 | 1073 | 60 |
| grover_10 | 8387 | 58 | 0 |
| hubbard_18 | 12823 | 4856 | 3505 |

### Table 9 - Depth budget vs crosstalk (weighted Max-k-Cut with k = k* + slack)

| Circuit | slack (% of k*) | 2q-depth | crosstalk-prone pairs | vs original | est. duration (us) |
|---|---:|---:|---:|---:|---:|
| mult_8 | 0 | 276 | 23 | -25.8% | 160.39 |
| mult_8 | 1 | 278 | 21 | -32.3% | 161.67 |
| mult_8 | 2 | 278 | 22 | -29.0% | 161.57 |
| mult_8 | 5 | 277 | 24 | -22.6% | 161.00 |
| mult_8 | 10 | 283 | 19 | -38.7% | 164.37 |
| mult_8 | 20 | 291 | 11 | -64.5% | 168.96 |
| add_17 | 0 | 253 | 144 | -4.6% | 145.74 |
| add_17 | 1 | 256 | 141 | -6.6% | 147.41 |
| add_17 | 2 | 257 | 140 | -7.3% | 147.95 |
| add_17 | 5 | 261 | 128 | -15.2% | 150.51 |
| add_17 | 10 | 270 | 117 | -22.5% | 155.66 |
| add_17 | 20 | 288 | 87 | -42.4% | 165.65 |
| qae_17 | 0 | 274 | 138 | -16.4% | 157.51 |
| qae_17 | 1 | 276 | 133 | -19.4% | 158.76 |
| qae_17 | 2 | 277 | 131 | -20.6% | 159.29 |
| qae_17 | 5 | 282 | 124 | -24.8% | 162.10 |
| qae_17 | 10 | 289 | 113 | -31.5% | 166.04 |
| qae_17 | 20 | 307 | 85 | -48.5% | 176.46 |
| qft_16 | 0 | 260 | 195 | -7.1% | 149.37 |
| qft_16 | 1 | 262 | 193 | -8.1% | 150.36 |
| qft_16 | 2 | 264 | 185 | -11.9% | 151.50 |
| qft_16 | 5 | 269 | 173 | -17.6% | 154.74 |
| qft_16 | 10 | 281 | 162 | -22.9% | 161.53 |
| qft_16 | 20 | 309 | 102 | -51.4% | 177.53 |
| hubbard_8 | 0 | 1110 | 130 | -21.7% | 637.55 |
| hubbard_8 | 1 | 1113 | 127 | -23.5% | 639.47 |
| hubbard_8 | 2 | 1121 | 120 | -27.7% | 643.77 |
| hubbard_8 | 5 | 1123 | 119 | -28.3% | 645.12 |
| hubbard_8 | 10 | 1153 | 93 | -44.0% | 662.22 |
| hubbard_8 | 20 | 1189 | 58 | -65.1% | 683.27 |
| hhl_8 | 0 | 2319 | 55 | -1.8% | 1365.77 |
| hhl_8 | 1 | 2320 | 54 | -3.6% | 1366.30 |
| hhl_8 | 2 | 2323 | 51 | -8.9% | 1368.01 |
| hhl_8 | 5 | 2323 | 51 | -8.9% | 1367.97 |
| hhl_8 | 10 | 2330 | 44 | -21.4% | 1372.24 |
| hhl_8 | 20 | 2339 | 34 | -39.3% | 1377.32 |

### Table 10 - Noise study with the ibm_brisbane calibration snapshot (fake_brisbane)

ESP = estimated success probability (state-blind, ALAP idling); sESP = state-aware ESP (idle gaps weighted by the idling qubit's state, <= 22 active qubits); sim = exact density-matrix state fidelity (<= 8 active qubits). Scale 0.1 = all error rates x0.1 and T1, T2 x10. mkco_noise = the MKCO candidate with the best sESP (ESP for larger circuits), the input included.

| Circuit | score | original | qiskit_o3 | mkco | mkco_alap | mkco_full | mkco_full_alap | mkco_noise | mkco_noise picks |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| mult_8 | ESP | 0.00283 | 0.00279 | 0.0029 | **0.0029** | 0.0029 | 0.0029 | 0.00283 | original |
| mult_8 | ESP_xt | 0.00232 | 0.00228 | 0.00234 | **0.00234** | 0.00234 | 0.00234 | 0.00232 |  |
| mult_8 | ESP x0.1 | 0.526 | 0.525 | 0.529 | **0.529** | 0.529 | 0.529 | 0.526 |  |
| mult_8 | sESP | **0.00222** | 0.00218 | 0.00141 | 0.0015 | 0.00141 | 0.00141 | **0.00222** |  |
| mult_8 | sESP x0.1 | **0.543** | 0.542 | 0.519 | 0.522 | 0.519 | 0.519 | **0.543** |  |
| mult_8 | sim F | **0.0155** | 0.0154 | 0.0126 | 0.0128 | 0.0126 | 0.0126 | **0.0155** |  |
| mult_8 | sim F x0.1 | **0.567** | 0.566 | 0.542 | 0.545 | 0.542 | 0.542 | **0.567** |  |
| add_17 | ESP | 1.41e-07 | 1.39e-07 | 1.37e-07 | **1.44e-07** | 1.37e-07 | **1.44e-07** | **1.44e-07** | mkco_full_alap |
| add_17 | ESP_xt | 3.51e-08 | 3.36e-08 | 3.00e-08 | **3.58e-08** | 3.00e-08 | **3.58e-08** | **3.58e-08** |  |
| add_17 | ESP x0.1 | 0.171 | 0.171 | 0.171 | **0.172** | 0.171 | **0.172** | **0.172** |  |
| add_17 | sESP | 1.07e-08 | 1.09e-08 | 1.14e-08 | 1.27e-08 | 1.14e-08 | **1.27e-08** | **1.27e-08** |  |
| add_17 | sESP x0.1 | 0.147 | 0.147 | 0.148 | **0.149** | 0.148 | **0.149** | **0.149** |  |
| qae_17 | ESP | 3.66e-05 | 3.62e-05 | 3.78e-05 | 3.73e-05 | 3.79e-05 | **3.79e-05** | **3.79e-05** | mkco_full_alap |
| qae_17 | ESP_xt | **1.21e-05** | 1.20e-05 | 1.13e-05 | 1.13e-05 | 1.13e-05 | 1.13e-05 | 1.13e-05 |  |
| qae_17 | ESP x0.1 | 0.279 | 0.278 | 0.281 | 0.28 | 0.281 | **0.281** | **0.281** |  |
| qae_17 | sESP | 1.18e-07 | 1.16e-07 | 1.30e-07 | 1.27e-07 | 1.34e-07 | **1.34e-07** | **1.34e-07** |  |
| qae_17 | sESP x0.1 | 0.194 | 0.194 | 0.196 | 0.196 | 0.197 | **0.197** | **0.197** |  |
| qft_16 | ESP | 5.26e-05 | 5.21e-05 | 5.46e-05 | 5.45e-05 | **5.47e-05** | 5.47e-05 | 5.45e-05 | mkco_alap |
| qft_16 | ESP_xt | **9.81e-06** | 9.72e-06 | 9.07e-06 | 9.06e-06 | 9.09e-06 | 9.09e-06 | 9.06e-06 |  |
| qft_16 | ESP x0.1 | 0.316 | 0.315 | 0.318 | 0.318 | **0.318** | **0.318** | 0.318 |  |
| qft_16 | sESP | 1.10e-05 | 1.06e-05 | 1.28e-05 | **1.29e-05** | 1.29e-05 | 1.29e-05 | **1.29e-05** |  |
| qft_16 | sESP x0.1 | 0.311 | 0.299 | 0.316 | 0.316 | 0.316 | **0.316** | 0.316 |  |
| hubbard_8 | ESP | 5.09e-09 | 5.13e-09 | 5.17e-09 | 5.17e-09 | 5.22e-09 | **5.22e-09** | **5.22e-09** | mkco_full_alap |
| hubbard_8 | ESP_xt | 1.39e-09 | **1.40e-09** | 1.32e-09 | 1.34e-09 | 1.32e-09 | 1.35e-09 | 1.35e-09 |  |
| hubbard_8 | ESP x0.1 | 0.0839 | 0.084 | 0.0848 | 0.0848 | 0.085 | **0.085** | **0.085** |  |
| hubbard_8 | sESP | 8.14e-13 | 8.40e-13 | 4.30e-13 | 1.00e-12 | 4.55e-13 | **1.06e-12** | **1.06e-12** |  |
| hubbard_8 | sESP x0.1 | 0.0618 | 0.062 | 0.0582 | 0.0631 | 0.0586 | **0.0634** | **0.0634** |  |
| hubbard_8 | sim F | 0.00283 | **0.00285** | 0.00252 | 0.0028 | 0.00253 | 0.0028 | 0.0028 |  |
| hubbard_8 | sim F x0.1 | 0.0751 | 0.0753 | 0.0702 | 0.0764 | 0.0706 | **0.0767** | **0.0767** |  |
| hhl_8 | ESP | 8.57e-21 | 6.29e-21 | 8.60e-21 | 8.60e-21 | **8.61e-21** | 8.61e-21 | **8.61e-21** | mkco_full |
| hhl_8 | ESP_xt | **5.35e-21** | 3.93e-21 | 5.29e-21 | 5.34e-21 | 5.30e-21 | 5.30e-21 | 5.30e-21 |  |
| hhl_8 | ESP x0.1 | 0.00256 | 0.00247 | 0.00259 | **0.0026** | 0.00259 | 0.00259 | 0.00259 |  |
| hhl_8 | sESP | 4.10e-28 | 2.77e-28 | 7.77e-28 | 2.47e-28 | **7.78e-28** | **7.78e-28** | **7.78e-28** |  |
| hhl_8 | sESP x0.1 | 9.54e-04 | 9.12e-04 | 0.00102 | 9.23e-04 | **0.00102** | **0.00102** | **0.00102** |  |
| hhl_8 | sim F | 0.0056 | 0.0056 | 0.00762 | 0.00741 | 0.00762 | **0.00762** | 0.00762 |  |
| hhl_8 | sim F x0.1 | 0.0123 | 0.0122 | 0.0138 | 0.0126 | 0.0138 | **0.0138** | 0.0138 |  |
| heisenberg_32 | ESP | 7.47e-35 | 1.18e-34 | 7.47e-35 | 7.47e-35 | 6.84e-33 | **6.84e-33** | **6.84e-33** | mkco_full_alap |
| heisenberg_32 | ESP_xt | 7.52e-41 | 2.72e-40 | 7.52e-41 | 7.52e-41 | 3.84e-38 | **3.84e-38** | **3.84e-38** |  |
| heisenberg_32 | ESP x0.1 | 3.37e-05 | 3.83e-05 | 3.37e-05 | 3.37e-05 | 7.24e-05 | **7.24e-05** | **7.24e-05** |  |
| heisenberg_32 | sESP | – | – | – | – | – | – | – |  |
| heisenberg_32 | sESP x0.1 | – | – | – | – | – | – | – |  |
| grover_10 | ESP | 8.41e-90 | 8.26e-90 | 8.42e-90 | 8.42e-90 | 9.43e-90 | **9.43e-90** | **9.43e-90** | mkco_full_alap |
| grover_10 | ESP_xt | **1.28e-106** | 1.25e-106 | 4.14e-108 | 3.60e-108 | 4.64e-108 | 4.64e-108 | 4.64e-108 |  |
| grover_10 | ESP x0.1 | 9.12e-12 | 9.10e-12 | 9.58e-12 | 9.59e-12 | **9.68e-12** | 9.68e-12 | 9.68e-12 |  |
| grover_10 | sESP | 9.94e-151 | 9.68e-151 | 8.75e-145 | 3.69e-149 | 9.38e-145 | **9.38e-145** | **9.38e-145** |  |
| grover_10 | sESP x0.1 | 1.98e-16 | 1.97e-16 | 9.30e-16 | 2.96e-16 | 9.36e-16 | **9.36e-16** | **9.36e-16** |  |
| hubbard_18 | ESP | 1.22e-177 | 2.79e-180 | 1.22e-177 | 1.22e-177 | 1.79e-169 | 1.79e-169 | **2.70e-155** | mkco_full_dur |
| hubbard_18 | ESP_xt | 1.36e-204 | 1.56e-209 | 2.02e-204 | 8.99e-205 | 4.15e-195 | 4.15e-195 | **9.82e-182** |  |
| hubbard_18 | ESP x0.1 | 1.16e-26 | 7.36e-27 | 1.16e-26 | 1.16e-26 | 8.17e-26 | 8.17e-26 | **2.38e-24** |  |
| hubbard_18 | sESP | – | – | – | – | – | – | – |  |
| hubbard_18 | sESP x0.1 | – | – | – | – | – | – | – |  |

### Table 11 - ECRs removed by block KAK, plain vs commutation-aware block formation

| Circuit | input ECRs | plain KAK | regrouped KAK | Qiskit O3 ECRs | plain KAK on O3 | regrouped KAK on O3 |
|---|---:|---:|---:|---:|---:|---:|
| add_17 | 499 | 0 | 0 | 499 | 0 | 0 |
| grover_10 | 16397 | 0 | 0 | 16397 | 0 | 0 |
| heisenberg_32 | 3942 | 60 | 60 | 4071 | 0 | 0 |
| hhl_8 | 2377 | 0 | 0 | 2377 | 0 | 0 |
| hubbard_18 | 33958 | 3505 | 3505 | 33586 | 0 | 14 |
| hubbard_8 | 1344 | 0 | 4 | 1344 | 0 | 4 |
| mult_8 | 311 | 0 | 0 | 311 | 0 | 0 |
| qae_17 | 541 | 0 | 0 | 541 | 0 | 0 |
| qft_16 | 614 | 0 | 0 | 614 | 0 | 0 |

### Table 12 - Noisy simulated backend: Aer + ibm_brisbane calibration, sampled counts

Hellinger fidelity of 512 or 32768 shots against the ideal output [bootstrap 95% interval]. Noise model: Aer's NoiseModel.from_backend (independent of mkco.noise); Qiskit's ALAP scheduling; methods interleaved in one job per run. mkco_noise is the same circuit as the method it selects (a repeat measurement). Predictions at scale 0.1: mkco.noise density-matrix Hellinger fidelity (<= 8 qubits) and state-aware ESP. The 17-qubit circuits are run at scale 0.1 only (at scale 1 they are at the noise floor).

| Circuit | method | scale 1 | scale 0.1 | predicted (DM, x0.1) | sESP x0.1 |
|---|---|---:|---:|---:|---:|
| mult_8 | original | 0.0135 [0.0122, 0.0148] | 0.5461 [0.5404, 0.5512] | 0.5505 | 0.5433 |
| mult_8 | mkco | 0.0109 [0.0098, 0.0119] | 0.5128 [0.5073, 0.5179] | 0.5265 | 0.5189 |
| mult_8 | mkco_alap | 0.0110 [0.0099, 0.0121] | 0.5215 [0.5167, 0.5266] | 0.5298 | 0.5220 |
| mult_8 | mkco_full | 0.0111 [0.0100, 0.0123] | 0.5148 [0.5092, 0.5203] | 0.5266 | 0.5189 |
| mult_8 | mkco_full_alap | 0.0112 [0.0101, 0.0123] | 0.5131 [0.5076, 0.5188] | 0.5266 | 0.5189 |
| mult_8 | mkco_noise (= original) | 0.0128 [0.0116, 0.0140] | 0.5475 [0.5423, 0.5529] | 0.5505 | 0.5433 |
| mult_8 | qiskit_o3 | 0.0127 [0.0116, 0.0139] | 0.5417 [0.5359, 0.5469] | 0.5494 | 0.5423 |
| add_17 | original | – | 0.1680 [0.1348, 0.2012] | – | 0.1468 |
| add_17 | mkco | – | 0.1484 [0.1191, 0.1777] | – | 0.1478 |
| add_17 | mkco_noise (= mkco_full_alap) | – | 0.1270 [0.0996, 0.1563] | – | 0.1494 |
| add_17 | qiskit_o3 | – | 0.1621 [0.1309, 0.1953] | – | 0.1470 |
| qae_17 | original | – | 0.2799 [0.2245, 0.3051] | – | 0.1942 |
| qae_17 | mkco | – | 0.3053 [0.2532, 0.3301] | – | 0.1963 |
| qae_17 | mkco_noise (= mkco_full_alap) | – | 0.3525 [0.2960, 0.3752] | – | 0.1969 |
| qae_17 | qiskit_o3 | – | 0.2544 [0.2013, 0.2751] | – | 0.1938 |
| hubbard_8 | original | 0.0040 [0.0034, 0.0046] | 0.0695 [0.0667, 0.0721] | 0.0808 | 0.0618 |
| hubbard_8 | mkco | 0.0032 [0.0025, 0.0038] | 0.0647 [0.0620, 0.0673] | 0.0757 | 0.0582 |
| hubbard_8 | mkco_alap | 0.0039 [0.0032, 0.0046] | 0.0732 [0.0703, 0.0758] | 0.0820 | 0.0631 |
| hubbard_8 | mkco_full | 0.0033 [0.0027, 0.0039] | 0.0677 [0.0650, 0.0704] | 0.0760 | 0.0586 |
| hubbard_8 | mkco_full_alap | 0.0048 [0.0040, 0.0055] | 0.0740 [0.0712, 0.0770] | 0.0823 | 0.0634 |
| hubbard_8 | mkco_noise (= mkco_full_alap) | 0.0037 [0.0031, 0.0043] | 0.0732 [0.0703, 0.0761] | 0.0823 | 0.0634 |
| hubbard_8 | qiskit_o3 | 0.0040 [0.0033, 0.0047] | 0.0716 [0.0688, 0.0742] | 0.0810 | 0.0620 |
| hhl_8 | original | 0.0630 [0.0605, 0.0654] | 0.0719 [0.0689, 0.0746] | 0.0722 | 0.0010 |
| hhl_8 | mkco | 0.0627 [0.0598, 0.0651] | 0.0717 [0.0688, 0.0743] | 0.0738 | 0.0010 |
| hhl_8 | mkco_alap | 0.0657 [0.0631, 0.0683] | 0.0731 [0.0702, 0.0760] | 0.0735 | 0.0009 |
| hhl_8 | mkco_full | 0.0661 [0.0635, 0.0687] | 0.0746 [0.0717, 0.0774] | 0.0738 | 0.0010 |
| hhl_8 | mkco_full_alap | 0.0647 [0.0619, 0.0672] | 0.0747 [0.0717, 0.0775] | 0.0738 | 0.0010 |
| hhl_8 | mkco_noise (= mkco_full) | 0.0626 [0.0597, 0.0652] | 0.0721 [0.0692, 0.0749] | 0.0738 | 0.0010 |
| hhl_8 | qiskit_o3 | 0.0601 [0.0574, 0.0626] | 0.0694 [0.0665, 0.0719] | 0.0720 | 0.0009 |

Scale 1: on the method pairs that sampling separates (non-overlapping intervals), the predictions order density-matrix model 6/6, state-aware ESP 5/6, ESP 4/6 correctly.

Scale 0.1: on the method pairs that sampling separates (non-overlapping intervals), the predictions order density-matrix model 12/12, state-aware ESP 13/13, ESP 4/13 correctly.
