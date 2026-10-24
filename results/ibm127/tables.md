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

### Table 4 - Gate-rewriting class: MKCO rewrite mode vs Qiskit O3, and their composition

Depth (lower is better). MKCO-rewrite = single-qubit ZSX resynthesis + run merging, then Max-k-Cut reordering; every MKCO result is certified optimal for the gate list it reorders.

| Circuit | Original | MKCO (reorder) | **MKCO-rewrite** | Qiskit O3 | O3 + MKCO | **O3 + MKCO-rewrite** | Best | Who wins |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| mult_8 | 1138 | 1102 | **1102** | 1172 | 1136 | **1136** | 1102 | MKCO-rewrite |
| add_17 | 1003 | 964 | **964** | 1026 | 988 | **988** | 964 | MKCO-rewrite |
| qae_17 | 1066 | 1035 | **1030** | 1084 | 1055 | **1051** | 1030 | MKCO-rewrite |
| qft_16 | 1009 | 980 | **980** | 1026 | 997 | **997** | 980 | MKCO-rewrite |
| hubbard_8 | 4400 | 4268 | **4251** | 4382 | 4246 | **4229** | 4229 | O3 + MKCO |
| hhl_8 | 10641 | 10434 | **10434** | 11190 | 10983 | **10983** | 10434 | MKCO-rewrite |
| heisenberg_32† | 7143 | 7143 | **3011** | 3538 | 3538 | **3534** | 3011 | MKCO-rewrite |
| grover_10 | 43923 | 41641 | **41631** | 43995 | 41713 | **41703** | 41631 | MKCO-rewrite |
| hubbard_18† | 136644 | 136637 | **72992** | 65436 | 65339 | **64969** | 64969 | O3 + MKCO |

| Circuit | 2q-depth MKCO-rewrite | 2q-depth Qiskit O3 | gates MKCO-rewrite | gates Qiskit O3 | duration MKCO-rewrite (us) | duration Qiskit O3 (us) | duration O3+MKCO-rewrite (us) |
|---|---:|---:|---:|---:|---:|---:|---:|
| mult_8 | 276 | 276 | 1897 | 1958 | 158.69 | 160.29 | 159.04 |
| add_17 | 255 | 253 | 2812 | 2918 | 145.42 | 145.78 | 145.07 |
| qae_17 | 274 | 274 | 3019 | 3090 | 156.44 | 157.55 | 156.62 |
| qft_16 | 260 | 260 | 3422 | 3518 | 148.23 | 149.26 | 148.37 |
| hubbard_8 | 1112 | 1111 | 8091 | 8059 | 634.60 | 637.83 | 633.17 |
| hhl_8 | 2319 | 2319 | 18165 | 19098 | 1359.51 | 1369.96 | 1364.06 |
| heisenberg_32 | 881 | 936 | 20324 | 23089 | 499.95 | 540.09 | 539.59 |
| grover_10 | 10895 | 10895 | 92654 | 93398 | 6220.96 | 6293.25 | 6221.60 |
| hubbard_18 | 21766 | 19938 | 170310 | 156700 | 12313.54 | 11450.49 | 11419.26 |

† Qiskit could not re-orient the ECRs it re-synthesised on the native (directed) coupling map, so it was re-run with a bidirectional map (favourable to Qiskit).


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

| Circuit | Lee'26 | JK'26 | MKCO | MKCO-2q | MKCO-XT | Qiskit O3 | MKCO after O3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| mult_8 | 0.3 | 0.2 | 0.1 | 0.1 | 4.4 | 3.8 | 0.4 |
| add_17 | 0.5 | 0.2 | 0.2 | 0.2 | 23.6 | 5.7 | 0.2 |
| qae_17 | 0.5 | 0.2 | 0.2 | 0.1 | 21.0 | 6.4 | 0.2 |
| qft_16 | 0.5 | 0.2 | 0.2 | 0.1 | 30.1 | 9.6 | 0.2 |
| hubbard_8 | 1.3 | 1.3 | 0.7 | 0.3 | 30.2 | 15.4 | 0.4 |
| hhl_8 | 2.8 | 6.2 | 1.1 | 0.7 | 30.1 | 26.5 | 1.1 |
| heisenberg_32 | 8.4 | 1.6 | 3.6 | 1.9 | 60.5 | 24.6 | 2.7 |
| grover_10 | 14.3 | 3.1 | 5.7 | 3.7 | 60.9 | 183.5 | 5.7 |
| hubbard_18 | 44.0 | 11.0 | 19.9 | 11.8 | 62.5 | 246.9 | 20.7 |

### Table 7 - Verification of every reordered output

| Circuit | Active qubits | Commutation audit (all reorderings) | Inverted pairs checked (MKCO) | State-vector check (MKCO) | State-vector check (MKCO-rewrite, vs original) |
|---|---:|:---:|---:|:---:|:---:|
| mult_8 | 8 | 11/11 pass | 75 | pass (F=1.0000000000) | pass (F=1.0000000000) |
| add_17 | 17 | 11/11 pass | 129 | pass (F=1.0000000000) | pass (F=1.0000000000) |
| qae_17 | 17 | 11/11 pass | 142 | pass (F=1.0000000000) | pass (F=1.0000000000) |
| qft_16 | 16 | 11/11 pass | 166 | pass (F=1.0000000000) | pass (F=1.0000000000) |
| hubbard_8 | 8 | 11/11 pass | 260 | pass (F=1.0000000000) | pass (F=1.0000000000) |
| hhl_8 | 8 | 11/11 pass | 333 | pass (F=1.0000000000) | pass (F=1.0000000000) |
| heisenberg_32 | 32 | 11/11 pass | 0 | n/a (>20 qubits) | n/a (>20 qubits) |
| grover_10 | 10 | 11/11 pass | 14222 | pass (F=1.0000000000) | pass (F=1.0000000000) |
| hubbard_18 | 31 | 11/11 pass | 2654 | n/a (>20 qubits) | n/a (>20 qubits) |
