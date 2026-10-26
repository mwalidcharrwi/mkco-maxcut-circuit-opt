| Logical circuit | Qubits | Qiskit L3 (SABRE) CNOTs / depth | **MKCO-route** CNOTs / depth | CNOTs vs Qiskit | Depth vs Qiskit | Ablation (DAG front) CNOTs / depth |
|---|---:|---|---|---:|---:|---|
| qaoa_n16_p1_d3 | 16 | 106 / 43 | **102 / 43** | -3.8% | +0.0% | 107 / 42 |
| qaoa_n16_p2_d3 | 16 | 204 / 100 | **190 / 96** | -6.9% | -4.0% | 222 / 94 |
| qaoa_n32_p1_d3 | 32 | 275 / 106 | **227 / 61** | -17.5% | -42.5% | 256 / 71 |
| qaoa_n32_p2_d3 | 32 | 575 / 193 | **449 / 96** | -21.9% | -50.3% | 563 / 141 |
| qaoa_n64_p1_d3 | 64 | 726 / 177 | **638 / 80** | -12.1% | -54.8% | 702 / 126 |
| qaoa_n64_p2_d3 | 64 | 1397 / 290 | **1177 / 164** | -15.7% | -43.4% | 1583 / 251 |
| qaoa_n32_p1_d4 | 32 | 445 / 143 | **363 / 90** | -18.4% | -37.1% | 429 / 131 |
| trotter_reg3_n16_s3 | 16 | 345 / 164 | **335 / 151** | -2.9% | -7.9% | 370 / 167 |
| trotter_reg3_n32_s3 | 32 | 873 / 299 | **875 / 223** | +0.2% | -25.4% | 988 / 223 |
| qft_12 | 12 | 221 / 221 | **245 / 191** | +10.9% | -13.6% | 247 / 240 |
| qft_20 | 20 | 638 / 401 | **795 / 573** | +24.6% | +42.9% | 879 / 493 |
| phasepoly_n16_t60_s0 | 16 | 907 / 542 | **958 / 484** | +5.6% | -10.7% | 1022 / 524 |
| rand_cliffT_n16_g600_s0 | 16 | 1199 / 571 | **1206 / 586** | +0.6% | +2.6% | 1244 / 609 |

Untranspiled logical circuits routed onto IBM Eagle's 127-qubit heavy-hex graph (CNOT level). Every MKCO-route output passes the exact unroute and coupling checks.
