### Table 1 - Total depth, reorder-only methods (lower is better)

| Circuit | Gates | Original | Lee'26 (colouring) | JK'26 (MIS+beam) | **MKCO** | Certified LB | MKCO optimal? | MKCO vs original |
|---|---:|---:|---:|---:|---:|---:|:---:|---:|
| tfim_8 | 1527 | 388 | 388 | 386 | **386** | 386 | yes | -0.52% |
| heisenberg_8 | 2135 | 530 | 530 | 527 | **527** | 527 | yes | -0.57% |
| qpe_8 | 3161 | 1930 | 1930 | 1889 | **1889** | 1889 | yes | -2.12% |
| tfim_7_40 | 4288 | 1560 | 1560 | 1514 | **1514** | 1514 | yes | -2.95% |

### Table 2 - Two-qubit (ECR) depth, reorder-only methods optimising 2q-depth

| Circuit | Original | Lee'26 | JK'26 | **MKCO** | Certified LB | MKCO optimal? |
|---|---:|---:|---:|---:|---:|:---:|
| tfim_8 | 90 | 90 | 90 | **90** | 90 | yes |
| heisenberg_8 | 130 | 130 | 130 | **130** | 130 | yes |
| qpe_8 | 452 | 452 | 452 | **452** | 452 | yes |
| tfim_7_40 | 368 | 368 | 368 | **368** | 368 | yes |

### Table 3 - Crosstalk-prone ECR pairs (same layer, neighbouring couplers) at optimal 2q-depth

| Circuit | Original | Lee'26 | JK'26 | MKCO (2q mode) | **MKCO-XT** | Reduction vs best baseline | 2q-depth orig -> XT | Total depth orig -> XT |
|---|---:|---:|---:|---:|---:|---:|---|---|
| tfim_8 | 190 | 190 | 190 | 190 | **190** | +0.0% | 90 -> 90 | 388 -> 389 |
| heisenberg_8 | 290 | 290 | 290 | 290 | **290** | +0.0% | 130 -> 130 | 530 -> 541 |
| qpe_8 | 22 | 22 | 22 | 22 | **19** | -13.6% | 452 -> 452 | 1930 -> 1934 |
| tfim_7_40 | 156 | 156 | 156 | 156 | **156** | +0.0% | 368 -> 368 | 1560 -> 1587 |

### Table 4 - Gate-rewriting modes: depth

Depth (lower is better). The inputs are already transpiled by Qiskit at optimization level 3, so the reference is the input itself; Lee'26 and JK'26 are reorder-only. MKCO-rewrite = single-qubit ZSX resynthesis + run merging + Max-k-Cut reordering; MKCO-full adds two-qubit KAK block resynthesis in the native ECR direction. Every MKCO result is certified optimal for the gate list it reorders.

| Circuit | Original | Lee'26 | JK'26 | MKCO (reorder) | MKCO-rewrite | **MKCO-full** | MKCO-full vs original |
|---|---:|---:|---:|---:|---:|---:|---:|
| tfim_8 | 388 | 388 | **386** | **386** | **386** | **386** | -0.5% |
| heisenberg_8 | 530 | 530 | **527** | **527** | **527** | **527** | -0.6% |
| qpe_8 | 1930 | 1930 | **1889** | **1889** | **1889** | **1889** | -2.1% |
| tfim_7_40 | 1560 | 1560 | 1514 | 1514 | **1512** | **1512** | -3.1% |

**Hardware-time view.** MKCO-full (duration objective) keeps, per circuit, the candidate with the lowest estimated execution time among {KAK + 1q rewrite, 1q rewrite} x {reorder for depth, for 2q-depth}.

| Circuit | est. duration original (us) | MKCO-full, depth obj. (us) | **MKCO-full, duration obj. (us)** | vs original | 2q-depth orig / MKCO-dur | ECRs orig / MKCO-dur | depth orig / MKCO-dur | reversed ECRs |
|---|---:|---:|---:|---:|---|---|---|---|
| tfim_8 | 53.05 | 52.98 | **52.98** | -0.1% | 90 / 90 | 280 / 280 | 388 / 386 | 0 |
| heisenberg_8 | 76.23 | 75.80 | **75.80** | -0.6% | 130 / 130 | 420 / 420 | 530 / 527 | 0 |
| qpe_8 | 261.83 | 260.45 | **260.45** | -0.5% | 452 / 452 | 484 / 484 | 1930 / 1889 | 0 |
| tfim_7_40 | 215.08 | 212.62 | **212.62** | -1.1% | 368 / 368 | 714 / 714 | 1560 / 1512 | 0 |

### Table 5 - Estimated execution time (us; ECR 533 ns, sx/x 36 ns, rz virtual)

| Circuit | Original | Lee'26 | JK'26 | MKCO (depth) | MKCO (2q) | MKCO-XT |
|---|---:|---:|---:|---:|---:|---:|
| tfim_8 | 53.05 | 53.05 | 52.98 | 52.98 | 53.05 | 53.40 |
| heisenberg_8 | 76.23 | 76.23 | 75.80 | 75.80 | 76.23 | 76.94 |
| qpe_8 | 261.83 | 261.83 | 260.45 | 260.45 | 261.83 | 261.97 |
| tfim_7_40 | 215.08 | 215.08 | 212.87 | 212.73 | 215.08 | 216.11 |

### Table 6 - Runtime (s)

| Circuit | Lee'26 | JK'26 | MKCO | MKCO-2q | MKCO-XT | MKCO-full |
|---|---:|---:|---:|---:|---:|---:|
| tfim_8 | 0.2 | 0.1 | 0.1 | 0.1 | 0.0 | 0.5 |
| heisenberg_8 | 0.3 | 0.1 | 0.1 | 0.1 | 0.0 | 0.7 |
| qpe_8 | 0.5 | 0.3 | 0.2 | 0.1 | 3.9 | 1.0 |
| tfim_7_40 | 0.8 | 0.3 | 0.4 | 0.2 | 0.1 | 9.3 |

### Table 7 - Verification of every reordered output

| Circuit | Active qubits | Commutation audit (all reorderings) | Inverted pairs checked (MKCO) | State-vector check (MKCO) | State-vector (MKCO-rewrite, vs original) | State-vector (MKCO-full dur., vs original) |
|---|---:|:---:|---:|:---:|:---:|:---:|
| tfim_8 | 8 | 11/11 pass | 159 | pass (F=1.0000000000) | pass (F=1.0000000000) | pass (F=1.0000000000) |
| heisenberg_8 | 8 | 11/11 pass | 238 | pass (F=1.0000000000) | pass (F=1.0000000000) | pass (F=1.0000000000) |
| qpe_8 | 8 | 11/11 pass | 83 | pass (F=1.0000000000) | pass (F=1.0000000000) | pass (F=1.0000000000) |
| tfim_7_40 | 7 | 11/11 pass | 274 | pass (F=1.0000000000) | pass (F=1.0000000000) | pass (F=1.0000000000) |

### Table 8 - Two-qubit block (KAK) resynthesis: blocks that become cheaper in native ECRs

| Circuit | two-qubit blocks | cheaper after KAK | ECRs removed |
|---|---:|---:|---:|
| tfim_8 | 140 | 0 | 0 |
| heisenberg_8 | 210 | 0 | 0 |
| qpe_8 | 256 | 0 | 0 |
| tfim_7_40 | 318 | 0 | 0 |

### Table 9 - Depth budget vs crosstalk (weighted Max-k-Cut with k = k* + slack)

| Circuit | slack (% of k*) | 2q-depth | crosstalk-prone pairs | vs original | est. duration (us) |
|---|---:|---:|---:|---:|---:|
| heisenberg_8 | 0 | 130 | 290 | +0.0% | 76.94 |
| heisenberg_8 | 1 | 131 | 286 | -1.4% | 77.51 |
| heisenberg_8 | 2 | 133 | 278 | -4.1% | 78.61 |
| heisenberg_8 | 5 | 136 | 264 | -9.0% | 80.28 |
| heisenberg_8 | 10 | 143 | 238 | -17.9% | 83.88 |
| heisenberg_8 | 20 | 154 | 192 | -33.8% | 90.20 |
| qpe_8 | 0 | 452 | 19 | -13.6% | 261.97 |
| qpe_8 | 1 | 452 | 19 | -13.6% | 261.97 |
| qpe_8 | 2 | 452 | 19 | -13.6% | 261.97 |
| qpe_8 | 5 | 453 | 18 | -18.2% | 262.54 |
| qpe_8 | 10 | 455 | 16 | -27.3% | 263.75 |
| qpe_8 | 20 | 456 | 14 | -36.4% | 264.36 |
| tfim_7_40 | 0 | 368 | 156 | +0.0% | 216.11 |
| tfim_7_40 | 1 | 372 | 150 | -3.8% | 218.49 |
| tfim_7_40 | 2 | 370 | 153 | -1.9% | 217.32 |
| tfim_7_40 | 5 | 378 | 136 | -12.8% | 222.08 |
| tfim_7_40 | 10 | 386 | 126 | -19.2% | 226.70 |
| tfim_7_40 | 20 | 402 | 97 | -37.8% | 235.95 |
| tfim_8 | 0 | 90 | 190 | +0.0% | 53.40 |
| tfim_8 | 1 | 91 | 187 | -1.6% | 54.04 |
| tfim_8 | 2 | 92 | 182 | -4.2% | 54.58 |
| tfim_8 | 5 | 94 | 172 | -9.5% | 55.61 |
| tfim_8 | 10 | 99 | 150 | -21.1% | 58.52 |
| tfim_8 | 20 | 106 | 120 | -36.8% | 62.72 |

### Table 10 - Noise study with device calibration snapshots (fake_brisbane, fake_cusco)

ESP = estimated success probability (state-blind, ALAP idling); sESP = state-aware ESP (idle gaps weighted by the idling qubit's state, <= 22 active qubits); sim = exact density-matrix state fidelity (<= 8 active qubits). Scale 0.1 = all error rates x0.1 and T1, T2 x10. mkco_noise = the MKCO candidate with the best sESP (ESP for larger circuits), the input included.

| Circuit | score | original | jk2026 | mkco | mkco_alap | mkco_full | mkco_full_alap | mkco_noise | mkco_noise picks |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| tfim_8 | ESP | 7.88e-04 | **7.91e-04** | **7.91e-04** | 7.79e-04 | **7.91e-04** | 7.91e-04 | 7.88e-04 | original |
| tfim_8 | ESP_xt | **1.81e-04** | 1.54e-04 | 1.56e-04 | 1.61e-04 | 1.56e-04 | 1.56e-04 | **1.81e-04** |  |
| tfim_8 | ESP x0.1 | 0.495 | 0.495 | **0.495** | 0.494 | **0.495** | **0.495** | 0.495 |  |
| tfim_8 | sESP | **7.04e-04** | 7.00e-04 | 7.00e-04 | 6.85e-04 | 7.00e-04 | 7.00e-04 | **7.04e-04** |  |
| tfim_8 | sESP x0.1 | **0.49** | 0.49 | 0.49 | 0.489 | 0.49 | 0.49 | **0.49** |  |
| tfim_8 | sim F | **0.00778** | 0.00766 | 0.00767 | 0.00761 | 0.00767 | 0.00767 | **0.00778** |  |
| tfim_8 | sim F x0.1 | **0.47** | 0.47 | 0.47 | 0.469 | 0.47 | 0.47 | **0.47** |  |
| heisenberg_8 | ESP | 2.66e-05 | **2.71e-05** | **2.71e-05** | 2.70e-05 | **2.71e-05** | 2.71e-05 | **2.71e-05** | mkco |
| heisenberg_8 | ESP_xt | **2.85e-06** | 2.30e-06 | 2.32e-06 | 2.80e-06 | 2.32e-06 | 2.32e-06 | 2.32e-06 |  |
| heisenberg_8 | ESP x0.1 | 0.355 | **0.355** | **0.355** | 0.355 | **0.355** | **0.355** | **0.355** |  |
| heisenberg_8 | sESP | 2.55e-05 | 2.59e-05 | **2.60e-05** | 2.58e-05 | **2.60e-05** | **2.60e-05** | **2.60e-05** |  |
| heisenberg_8 | sESP x0.1 | 0.354 | 0.355 | 0.355 | 0.354 | 0.355 | **0.355** | 0.355 |  |
| heisenberg_8 | sim F | 0.0108 | 0.0111 | 0.0111 | 0.011 | 0.0111 | **0.0111** | 0.0111 |  |
| heisenberg_8 | sim F x0.1 | 0.376 | 0.377 | 0.378 | 0.377 | 0.378 | **0.378** | 0.378 |  |
| qpe_8 | ESP | 4.32e-08 | 4.41e-08 | 4.41e-08 | 4.41e-08 | 4.41e-08 | **4.41e-08** | **4.41e-08** | mkco_full_alap |
| qpe_8 | ESP_xt | 3.43e-08 | 3.47e-08 | 3.47e-08 | 3.47e-08 | 3.47e-08 | **3.47e-08** | **3.47e-08** |  |
| qpe_8 | ESP x0.1 | 0.15 | 0.15 | 0.15 | 0.15 | 0.15 | **0.15** | **0.15** |  |
| qpe_8 | sESP | 6.68e-10 | **1.04e-09** | 1.04e-09 | 1.04e-09 | 1.04e-09 | 1.04e-09 | 1.04e-09 |  |
| qpe_8 | sESP x0.1 | 0.114 | **0.119** | 0.119 | 0.119 | 0.119 | 0.119 | 0.119 |  |
| qpe_8 | sim F | 0.0023 | **0.0031** | 0.0031 | 0.00303 | 0.0031 | 0.0031 | 0.0031 |  |
| qpe_8 | sim F x0.1 | 0.0928 | **0.0968** | 0.0968 | 0.0968 | 0.0968 | 0.0968 | 0.0968 |  |
| tfim_7_40 | ESP | 3.57e-28 | 4.04e-28 | 4.08e-28 | 4.02e-28 | **5.48e-28** | 5.48e-28 | 4.08e-28 | mkco |
| tfim_7_40 | ESP_xt | **8.43e-30** | 6.71e-30 | 6.63e-30 | 6.83e-30 | 5.74e-30 | 5.74e-30 | 6.63e-30 |  |
| tfim_7_40 | ESP x0.1 | 0.00163 | 0.00167 | 0.00167 | 0.00167 | **0.00171** | **0.00171** | 0.00167 |  |
| tfim_7_40 | sESP | 5.84e-30 | 9.26e-30 | **9.55e-30** | 7.25e-30 | 8.73e-30 | 8.73e-30 | **9.55e-30** |  |
| tfim_7_40 | sESP x0.1 | 0.00141 | 0.00147 | **0.00148** | 0.00144 | 0.00147 | 0.00147 | **0.00148** |  |
| tfim_7_40 | sim F | 0.0086 | 0.00826 | 0.00826 | 0.00809 | **0.00941** | 0.00941 | 0.00826 |  |
| tfim_7_40 | sim F x0.1 | 0.0136 | 0.0137 | 0.0137 | 0.0136 | **0.0139** | 0.0139 | 0.0137 |  |

### Table 11 - ECRs removed by block KAK, plain vs commutation-aware block formation

| Circuit | input ECRs | removed by plain block KAK | removed by regrouped block KAK |
|---|---:|---:|---:|
| heisenberg_8 | 420 | 0 | 0 |
| qpe_8 | 484 | 0 | 0 |
| tfim_7_40 | 714 | 0 | 0 |
| tfim_8 | 280 | 0 | 0 |

### Table 12 - Noisy simulated backend: Aer + the circuits' device calibrations, sampled counts

Hellinger fidelity of 32768 shots against the ideal output [bootstrap 95% interval]. Noise model: Aer's NoiseModel.from_backend (independent of mkco.noise); Qiskit's ALAP scheduling; methods interleaved in one job per run. mkco_noise is the same circuit as the method it selects (a repeat measurement). Predictions at scale 0.1: mkco.noise density-matrix Hellinger fidelity (<= 8 qubits) and state-aware ESP. The 17-qubit circuits are run at scale 0.1 only (at scale 1 they are at the noise floor).

| Circuit | method | scale 1 | scale 0.1 | predicted (DM, x0.1) | sESP x0.1 |
|---|---|---:|---:|---:|---:|
| heisenberg_8 | original | 0.0492 [0.0469, 0.0513] | 0.4846 [0.4788, 0.4897] | 0.5003 | 0.3539 |
| tfim_8 | original | 0.0455 [0.0430, 0.0477] | 0.5518 [0.5462, 0.5572] | 0.5744 | 0.4901 |
| qpe_8 | original | 0.2423 [0.2372, 0.2463] | 0.6793 [0.6735, 0.6838] | 0.6795 | 0.1136 |
| tfim_7_40 | original | 0.4782 [0.4718, 0.4830] | 0.4604 [0.4543, 0.4650] | 0.5189 | 0.0014 |
| qpe_8 | mkco | 0.3396 [0.3338, 0.3442] | 0.7012 [0.6952, 0.7053] | 0.7028 | 0.1187 |
| tfim_8 | mkco | 0.0465 [0.0441, 0.0485] | 0.5608 [0.5549, 0.5661] | 0.5738 | 0.4898 |
| tfim_7_40 | mkco | 0.4902 [0.4842, 0.4944] | 0.4688 [0.4629, 0.4738] | 0.5231 | 0.0015 |
| heisenberg_8 | mkco | 0.0508 [0.0484, 0.0532] | 0.4887 [0.4832, 0.4942] | 0.5007 | 0.3546 |
| tfim_8 | mkco_alap | 0.0442 [0.0418, 0.0464] | 0.5615 [0.5559, 0.5666] | 0.5731 | 0.4887 |
| qpe_8 | mkco_alap | 0.3314 [0.3258, 0.3358] | 0.7036 [0.6983, 0.7076] | 0.7015 | 0.1187 |
| tfim_7_40 | mkco_alap | 0.4892 [0.4831, 0.4940] | 0.4709 [0.4650, 0.4756] | 0.5223 | 0.0014 |
| heisenberg_8 | mkco_alap | 0.0503 [0.0479, 0.0527] | 0.4840 [0.4780, 0.4892] | 0.5009 | 0.3544 |
| tfim_8 | mkco_full | 0.0469 [0.0444, 0.0492] | 0.5578 [0.5521, 0.5629] | 0.5738 | 0.4898 |
| qpe_8 | mkco_full | 0.3391 [0.3339, 0.3438] | 0.7065 [0.7012, 0.7108] | 0.7028 | 0.1187 |
| tfim_7_40 | mkco_full | 0.4870 [0.4809, 0.4917] | 0.4667 [0.4612, 0.4715] | 0.5217 | 0.0015 |
| heisenberg_8 | mkco_full | 0.0521 [0.0498, 0.0545] | 0.4865 [0.4810, 0.4917] | 0.5007 | 0.3546 |
| heisenberg_8 | mkco_full_alap | 0.0524 [0.0499, 0.0546] | 0.4843 [0.4787, 0.4892] | 0.5007 | 0.3546 |
| qpe_8 | mkco_full_alap | 0.3390 [0.3337, 0.3436] | 0.7045 [0.6989, 0.7088] | 0.7028 | 0.1187 |
| tfim_8 | mkco_full_alap | 0.0457 [0.0434, 0.0481] | 0.5579 [0.5523, 0.5631] | 0.5738 | 0.4898 |
| tfim_7_40 | mkco_full_alap | 0.4851 [0.4791, 0.4898] | 0.4648 [0.4588, 0.4694] | 0.5217 | 0.0015 |
| tfim_8 | mkco_noise (= original) | 0.0429 [0.0408, 0.0450] | 0.5575 [0.5520, 0.5628] | 0.5744 | 0.4901 |
| qpe_8 | mkco_noise (= mkco_full_alap) | 0.3336 [0.3279, 0.3378] | 0.7026 [0.6969, 0.7072] | 0.7028 | 0.1187 |
| tfim_7_40 | mkco_noise (= mkco) | 0.4910 [0.4852, 0.4958] | 0.4688 [0.4630, 0.4737] | 0.5231 | 0.0015 |
| heisenberg_8 | mkco_noise (= mkco) | 0.0538 [0.0513, 0.0562] | 0.4898 [0.4843, 0.4949] | 0.5007 | 0.3546 |

Scale 1: on the method pairs that sampling separates (non-overlapping intervals), the predictions order density-matrix model 6/6, state-aware ESP 6/6, ESP 6/6 correctly.

Scale 0.1: on the method pairs that sampling separates (non-overlapping intervals), the predictions order density-matrix model 4/4, state-aware ESP 4/4, ESP 4/4 correctly.
