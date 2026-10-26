### E8 - Non-Clifford depth with free Cliffords (T-depth, Toffoli-depth)

Cells: count / depth of the counted gates (T-like rotations, or Toffolis). \* = certified optimal for that method's own gate set (after merging). PyZX: full_reduce + extract (full) or teleport_reduce (teleport), then basic_optimization.

| circuit | qubits | original | MKCO-depth | **MKCO-T** | PyZX full | **PyZX full + MKCO-T** | PyZX teleport | **PyZX tel. + MKCO-T** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| cuccaro_4_ct (t) | 10 | 56 / 32 | 56 / 36 | 56 / 32\* | 32 / 23 | 32 / 17\* | 32 / 32 | 32 / 29\* |
| cuccaro_8_ct (t) | 18 | 112 / 64 | 112 / 72 | 112 / 64\* | 64 / 41 | 64 / 36\* | 64 / 64 | 64 / 57\* |
| cuccaro_16_ct (t) | 34 | 224 / 128 | 224 / 144 | 224 / 128\* | 128 / 92 | 128 / 72\* | 128 / 128 | 128 / 113\* |
| mcx_vchain_5_ct (t) | 9 | 49 / 28 | 49 / 26 | 49 / 25\* | 31 / 22 | 31 / 19\* | 31 / 26 | 31 / 23\* |
| mcx_vchain_8_ct (t) | 15 | 91 / 52 | 91 / 47 | 91 / 46\* | 55 / 43 | 55 / 33\* | 55 / 45 | 55 / 41\* |
| mcx_vchain_12_ct (t) | 23 | 147 / 84 | 147 / 75 | 147 / 74\* | 87 / 58 | 87 / 52\* | 87 / 72 | 87 / 65\* |
| gf2_mult_3_ct (t) | 11 | 84 / 36 | 84 / 25 | 84 / 22\* | 50 / 18 | 50 / 8\* | 50 / 31 | 50 / 18\* |
| gf2_mult_4_ct (t) | 15 | 154 / 54 | 154 / 37 | 154 / 33\* | 86 / 31 | 86 / 11\* | 86 / 51 | 86 / 29\* |
| gf2_mult_5_ct (t) | 19 | 245 / 81 | 245 / 49 | 237 / 45\* | 133 / 41 | 133 / 14\* | 133 / 69 | 133 / 37\* |
| gf2_mult_6_ct (t) | 23 | 357 / 90 | 357 / 61 | 349 / 55\* | 189 / 55 | 189 / 20\* | 189 / 94 | 189 / 47\* |
| gf2_mult_7_ct (t) | 27 | 490 / 108 | 490 / 73 | 482 / 66\* | 256 / 74 | 256 / 23\* | 256 / 110 | 256 / 55\* |
| tpoly_n8_t40_s0 (t) | 8 | 27 / 22 | 27 / 17 | 27 / 17\* | 25 / 9 | 25 / 5\* | 25 / 20 | 25 / 15\* |
| tpoly_n12_t80_s0 (t) | 12 | 52 / 40 | 52 / 29 | 52 / 28\* | 48 / 20 | 48 / 9\* | 48 / 30 | 48 / 27\* |
| tpoly_n16_t120_s0 (t) | 16 | 79 / 47 | 79 / 37 | 79 / 33\* | 73 / 26 | 73 / 13\* | 73 / 39 | 73 / 33\* |
| rand_cliffT_n8_g400_s0 (t) | 8 | 95 / 39 | 95 / 37 | 79 / 25 | 43 / 25 | 43 / 15\* | 43 / 20 | 43 / 13\* |
| rand_cliffT_n10_g800_s0 (t) | 10 | 175 / 48 | 175 / 51 | 145 / 35 | 91 / 49 | 91 / 29\* | 91 / 36 | 91 / 24\* |
| rand_cliffT_n12_g1200_s0 (t) | 12 | 247 / 69 | 247 / 64 | 215 / 45 | 143 / 65 | 143 / 36\* | 143 / 47 | 143 / 33\* |
| cuccaro_8 (toffoli) | 18 | 16 / 16 | 16 / 16 | 16 / 16\* | – | – | – | – |
| cuccaro_16 (toffoli) | 34 | 32 / 32 | 32 / 32 | 32 / 32\* | – | – | – | – |
| cuccaro_32 (toffoli) | 66 | 64 / 64 | 64 / 64 | 64 / 64\* | – | – | – | – |
| mcx_vchain_8 (toffoli) | 15 | 13 / 13 | 13 / 13 | 13 / 13\* | – | – | – | – |
| mcx_vchain_16 (toffoli) | 31 | 29 / 29 | 29 / 29 | 29 / 29\* | – | – | – | – |
| gf2_mult_4 (toffoli) | 15 | 22 / 15 | 22 / 8 | 22 / 7\* | – | – | – | – |
| gf2_mult_5 (toffoli) | 19 | 35 / 23 | 35 / 10 | 35 / 10 | – | – | – | – |
| gf2_mult_6 (toffoli) | 23 | 51 / 25 | 51 / 12 | 51 / 11\* | – | – | – | – |
| gf2_mult_7 (toffoli) | 27 | 70 / 30 | 70 / 14 | 70 / 13\* | – | – | – | – |
| gf2_mult_9 (toffoli) | 35 | 117 / 45 | 117 / 18 | 117 / 18 | – | – | – | – |
| gf2_mult_10 (toffoli) | 39 | 145 / 52 | 145 / 20 | 145 / 19\* | – | – | – | – |
| gf2_mult_11 (toffoli) | 43 | 176 / 59 | 176 / 22 | 176 / 21\* | – | – | – | – |
| gf2_mult_12 (toffoli) | 47 | 210 / 64 | 210 / 24 | 210 / 23\* | – | – | – | – |

On the 17 T-depth instances MKCO-T lowers PyZX(full)'s T-depth by 10-69% (mean 41%); 17/17 results certified. All 103 outputs with <= 20 qubits pass the state-vector check.

### E9 - Commutation-aware routing + layering on the 127-qubit heavy-hex device (CNOT level)

Cells: CNOTs / depth after routing and optimisation of untranspiled logical circuits. Qiskit O3 = Qiskit's transpiler at level 3 (SabreLayout + SabreSwap), the routing baseline. sabre_dag is the ablation (same router, plain DAG front). Every mkco_route output passes the exact unroute check and the coupling check.

| circuit | qubits | logical CNOTs | Qiskit O3 | **MKCO-route** | SWAPs | sabre_dag (ablation) | Qiskit O3 + MKCO | CNOTs vs O3 | depth vs O3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| qaoa_n16_p1_d3 | 16 | 48 | 106 / 43 | **102 / 43** | 20 | 107 / 42 | 106 / 41 | -3.8% | +0.0% |
| qaoa_n16_p2_d3 | 16 | 96 | 204 / 100 | **190 / 96** | 32 | 222 / 94 | 204 / 96 | -6.9% | -4.0% |
| qaoa_n32_p1_d3 | 32 | 96 | 275 / 106 | **227 / 61** | 51 | 256 / 71 | 275 / 102 | -17.5% | -42.5% |
| qaoa_n32_p2_d3 | 32 | 192 | 575 / 193 | **449 / 96** | 92 | 563 / 141 | 574 / 185 | -21.9% | -50.3% |
| qaoa_n64_p1_d3 | 64 | 192 | 726 / 177 | **638 / 80** | 156 | 702 / 126 | 726 / 171 | -12.1% | -54.8% |
| qaoa_n64_p2_d3 | 64 | 384 | 1397 / 290 | **1177 / 164** | 282 | 1583 / 251 | 1395 / 275 | -15.7% | -43.4% |
| qaoa_n32_p1_d4 | 32 | 128 | 445 / 143 | **363 / 90** | 85 | 429 / 131 | 445 / 136 | -18.4% | -37.1% |
| trotter_reg3_n16_s3 | 16 | 144 | 345 / 164 | **335 / 151** | 70 | 370 / 167 | 345 / 140 | -2.9% | -7.9% |
| trotter_reg3_n32_s3 | 32 | 288 | 873 / 299 | **875 / 223** | 209 | 988 / 223 | 871 / 287 | +0.2% | -25.4% |
| qft_12 | 12 | 132 | 221 / 221 | **245 / 191** | 49 | 247 / 240 | 219 / 199 | +10.9% | -13.6% |
| qft_20 | 20 | 380 | 638 / 401 | **795 / 573** | 185 | 879 / 493 | 638 / 384 | +24.6% | +42.9% |
| phasepoly_n16_t60_s0 | 16 | 266 | 907 / 542 | **958 / 484** | 264 | 1022 / 524 | 895 / 489 | +5.6% | -10.7% |
| rand_cliffT_n16_g600_s0 | 16 | 239 | 1199 / 571 | **1206 / 586** | 350 | 1244 / 609 | 1188 / 512 | +0.6% | +2.6% |

Unroute and coupling checks: all pass.

### E11 - Commutation-aware block formation before KAK (logical circuits, CX basis)

Cells: CNOTs / depth after MKCO layering. regroup = legal reordering that keeps gates of one pair together (forward + backward pass) before block KAK.

| circuit | input CNOTs | block KAK | **regroup + KAK** | Qiskit O3 | O3 + regroup + KAK |
|---|---:|---:|---:|---:|---:|
| phasepoly_n8_t40_s0 | 178 | 178 / 124 | **174 / 128** | 170 / 127 | 170 / 127 |
| phasepoly_n8_t40_s1 | 158 | 152 / 120 | **138 / 116** | 136 / 103 | 136 / 103 |
| phasepoly_n10_t60_s0 | 266 | 266 / 157 | **262 / 162** | 262 / 157 | 262 / 157 |
| phasepoly_n10_t60_s1 | 230 | 224 / 162 | **216 / 150** | 212 / 143 | 212 / 143 |
| phasepoly_n12_t80_s0 | 336 | 336 / 176 | **332 / 174** | 332 / 174 | 332 / 174 |
| phasepoly_n12_t80_s1 | 314 | 314 / 175 | **308 / 173** | 308 / 173 | 308 / 173 |
| phasepoly_n16_t120_s0 | 500 | 496 / 217 | **480 / 208** | 480 / 208 | 480 / 208 |
| phasepoly_n16_t120_s1 | 480 | 472 / 226 | **458 / 228** | 458 / 225 | 458 / 225 |
| phasepoly_n20_t160_s0 | 650 | 648 / 214 | **634 / 212** | 632 / 213 | 632 / 213 |
| phasepoly_n20_t160_s1 | 642 | 642 / 277 | **632 / 273** | 632 / 273 | 632 / 273 |
| trotter_reg3_n10_s4 | 120 | 120 / 58 | **118 / 65** | 120 / 70 | 118 / 75 |
| qaoa_n10_p2_d3_cx | 60 | 60 / 33 | **60 / 33** | 60 / 42 | 60 / 42 |
| trotter_reg3_n12_s4 | 144 | 140 / 63 | **138 / 69** | 140 / 74 | 138 / 77 |
| qaoa_n12_p2_d3_cx | 72 | 70 / 35 | **70 / 35** | 70 / 41 | 70 / 41 |
| trotter_reg3_n16_s4 | 192 | 186 / 66 | **180 / 66** | 186 / 76 | 180 / 76 |
| qaoa_n16_p2_d3_cx | 96 | 96 / 28 | **94 / 34** | 96 / 37 | 94 / 40 |
| rand_cliffT_n10_g400_s0 | 157 | 153 / 88 | **149 / 86** | 148 / 99 | 148 / 99 |
| rand_cliffT_n10_g400_s1 | 182 | 179 / 91 | **178 / 91** | 179 / 100 | 178 / 103 |
| rand_cliffT_n10_g400_s2 | 159 | 148 / 84 | **139 / 89** | 137 / 95 | 137 / 95 |

regroup + KAK uses fewer CNOTs than plain block KAK on 17/19 circuits and never more; applied after Qiskit O3 it removes CNOTs on 5/19.
