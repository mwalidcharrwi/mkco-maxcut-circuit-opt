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
