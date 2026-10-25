### E1 - Random commuting multi-controlled-Z circuits (Lee et al. Sec. 4.3)

Mean depth over seeds; 'opt' = instances where the method meets the certified lower bound.

| qubits m | gates n | LB | DSatur (Lee) | Backtracking (Lee, n<=50) | JK'26 | **MKCO** | DSatur opt | JK opt | MKCO opt |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 | 50 | 27.6 | 27.8 | 27.8 | 31.8 | **27.8** | 4/5 | 0/5 | 4/5 |
| 10 | 100 | 48.2 | 50.8 | - | 57.8 | **49.0** | 2/5 | 0/5 | 2/5 |
| 10 | 150 | 67.8 | 73.0 | - | 83.4 | **69.8** | 0/5 | 0/5 | 1/5 |
| 10 | 200 | 91.0 | 95.6 | - | 109.2 | **92.8** | 0/5 | 0/5 | 3/5 |
| 20 | 50 | 30.8 | 30.8 | 30.8 | 33.8 | **30.8** | 5/5 | 0/5 | 5/5 |
| 20 | 100 | 51.6 | 52.0 | - | 61.4 | **52.0** | 3/5 | 0/5 | 3/5 |
| 20 | 150 | 73.8 | 74.2 | - | 88.8 | **74.2** | 3/5 | 0/5 | 3/5 |
| 20 | 200 | 93.4 | 94.2 | - | 117.2 | **94.0** | 2/5 | 0/5 | 3/5 |
| 30 | 50 | 32.6 | 32.6 | 32.6 | 35.6 | **32.6** | 5/5 | 0/5 | 5/5 |
| 30 | 100 | 58.8 | 59.0 | - | 68.0 | **59.0** | 4/5 | 0/5 | 4/5 |
| 30 | 150 | 84.8 | 85.0 | - | 99.0 | **85.0** | 4/5 | 0/5 | 4/5 |
| 30 | 200 | 111.0 | 111.2 | - | 131.8 | **111.2** | 4/5 | 0/5 | 4/5 |

### E2 - F(2^n) multiplication, Toffoli-depth of phases 1+3 (Lee et al. Sec. 5.1, Fig. 2)

| n | certified LB (proven optimum for n<=7) | 2n-1 | DSatur (Lee) | JK'26 | **MKCO** |
|---:|---:|---:|---:|---:|---:|
| 2 | 4 | 3 | 4 | 4 | **4** |
| 3 | 6 | 5 | 6 | 6 | **6** |
| 4 | 8 | 7 | 8 | 8 | **8** |
| 5 | 10 | 9 | 11 | 11 | **10** |
| 6 | 11 | 11 | 14 | 12 | **11** |
| 7 | 13 | 13 | 14 | 15 | **13** |
| 8 | 15 | 15 | 16 | 17 | **15** |
| 9 | 17 | 17 | 18 | 18 | **17** |
| 10 | 19 | 19 | 19 | 20 | **19** |
| 11 | 21 | 21 | 22 | 22 | **21** |
| 12 | 23 | 23 | 23 | 24 | **23** |
| 13 | 25 | 25 | 26 | 25 | **25** |
| 14 | 27 | 27 | 27 | 27 | **27** |
| 15 | 29 | 29 | 31 | 31 | **29** |
| 16 | 31 | 31 | 32 | 32 | **31** |
| 17 | 33 | 33 | 34 | 34 | **33** |
| 18 | 35 | 35 | 35 | 37 | **35** |
| 19 | 37 | 37 | 37 | 37 | **37** |
| 20 | 39 | 39 | 39 | 41 | **39** |
| 21 | 41 | 41 | 41 | 43 | **41** |
| 22 | 43 | 43 | 43 | 45 | **43** |
| 23 | 45 | 45 | 45 | 45 | **45** |
| 24 | 47 | 47 | 47 | 48 | **47** |
| 25 | 49 | 49 | 49 | 50 | **49** |
| 26 | 51 | 51 | 51 | 53 | **51** |
| 27 | 53 | 53 | 53 | 55 | **53** |
| 28 | 55 | 55 | 55 | 56 | **55** |
| 29 | 57 | 57 | 57 | 59 | **57** |
| 30 | 59 | 59 | 59 | 61 | **59** |
| 31 | 61 | 61 | 61 | 63 | **61** |
| 32 | 63 | 63 | 63 | 65 | **63** |
| 40 | 79 | 79 | 79 | 82 | **79** |
| 48 | 95 | 95 | 95 | 97 | **95** |
| 64 | 127 | 127 | 127 | 129 | **127** |

Meets the certified bound: DSatur 24/34, JK 7/34, MKCO 34/34.

### E3 - Random CCZ circuits on 10 qubits (Lee et al. Appendix C)

| CCZ gates | LB | DSatur (Lee) | Backtracking (Lee) | JK'26 | **MKCO** | MKCO opt |
|---:|---:|---:|---:|---:|---:|---:|
| 10 | 5.6 | 5.6 | 5.6 | 5.6 | **5.6** | 5/5 |
| 20 | 9.0 | 9.2 | 9.0 | 9.8 | **9.0** | 5/5 |
| 30 | 13.2 | 14.2 | 13.2 | 13.6 | **13.2** | 5/5 |
| 40 | 16.4 | 17.4 | 16.8 | 18.0 | **16.6** | 4/5 |
| 50 | 18.6 | 20.4 | 19.6 | 20.4 | **18.6** | 5/5 |
| 60 | 23.2 | 24.2 | - | 24.6 | **23.2** | 5/5 |
| 70 | 26.8 | 28.0 | - | 27.4 | **26.8** | 5/5 |
| 80 | 30.0 | 32.6 | - | 30.8 | **30.0** | 5/5 |
| 90 | 34.0 | 35.4 | - | 34.8 | **34.0** | 5/5 |
| 100 | 37.0 | 38.8 | - | 38.4 | **37.0** | 5/5 |

### E4 - Commuting RZZ layers on random d-regular graphs (QAOA cost layer; LB = degree)

| qubits | degree d | DSatur (Lee) | JK'26 | **MKCO** | MKCO = d (optimal) |
|---:|---:|---:|---:|---:|---:|
| 30 | 5 | 6.00 | 6.00 | **5.00** | 3/3 |
| 30 | 9 | 10.00 | 10.67 | **9.00** | 3/3 |
| 50 | 15 | 17.00 | 17.00 | **15.00** | 3/3 |
| 50 | 25 | 27.33 | 27.00 | **25.33** | 2/3 |
| 100 | 15 | 17.33 | 18.00 | **15.33** | 2/3 |
| 100 | 31 | 34.67 | 34.00 | **31.67** | 1/3 |

### E5 - Hierarchical Max-Cut with exact and QAOA sub-solvers

| case | gates | LB | backend | layers | spins (log encoding) | spins (one-hot) | QAOA nodes solved optimally |
|---|---:|---:|---|---:|---:|---:|---:|
| gf2_4_phase3 | 10 | 4 | exact | 5 | 20 | 40 | - |
| gf2_4_phase3 | 10 | 4 | qaoa | 5 | 20 | 40 | 3/3 |
| gf2_5_phase3 | 15 | 5 | exact | 5 | 45 | 75 | - |
| gf2_5_phase3 | 15 | 5 | qaoa | 5 | 45 | 75 | 4/4 |
| draper_6_core | 21 | 6 | exact | 6 | 63 | 126 | - |
| draper_6_core | 21 | 6 | qaoa | 6 | 63 | 126 | 4/4 |
| ccz_m8_n16 | 16 | 11 | exact | 11 | 64 | 176 | - |
| ccz_m8_n16 | 16 | 11 | qaoa | 11 | 64 | 176 | 10/10 |

### E6 - Depth/qubit trade-off by ancilla fan-out (capacitated Max-k-Cut)

| circuit | copies per qubit | qubits | round-robin + DSatur depth | **MKCO depth** |
|---|---:|---:|---:|---:|
| draper_8_core | 1 | 16 | 8 | **8** |
| draper_8_core | 2 | 32 | 6 | **6** |
| draper_8_core | 3 | 48 | 7 | **7** |
| draper_8_core | 4 | 64 | 6 | **6** |
| draper_16_core | 1 | 32 | 16 | **16** |
| draper_16_core | 2 | 64 | 10 | **10** |
| draper_16_core | 3 | 96 | 10 | **10** |
| draper_16_core | 4 | 128 | 8 | **8** |
| ccz_m10_n80 | 1 | 10 | 35 | **31** |
| ccz_m10_n80 | 2 | 20 | 19 | **18** |
| ccz_m10_n80 | 3 | 30 | 16 | **15** |
| ccz_m10_n80 | 4 | 40 | 13 | **12** |
| ccz_m16_n150 | 1 | 16 | 38 | **38** |
| ccz_m16_n150 | 2 | 32 | 21 | **21** |
| ccz_m16_n150 | 3 | 48 | 17 | **17** |
| ccz_m16_n150 | 4 | 64 | 15 | **14** |
| mcz_m20_n120 | 1 | 20 | 57 | **57** |
| mcz_m20_n120 | 2 | 40 | 32 | **26** |
| mcz_m20_n120 | 3 | 60 | 25 | **20** |
| mcz_m20_n120 | 4 | 80 | 21 | **16** |

### E7 - Lovász-theta certificates where the clique/Jackson bound left a gap

theta(complement of the conflict graph) <= chromatic number (sandwich theorem), solved as an SDP. The 'theta' column is the objective of the solver's solution after repair into an exactly feasible point, so it is a proven lower bound on theta (and on the depth) whatever the solver's accuracy. Open instances above 150 gates were not attempted.

| exp. | m | gates | seed | clique/Jackson LB | theta (certified) | new LB | DSatur | JK'26 | MKCO | MKCO now proven optimal |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|
| E3 | 10 | 40 | 4 | 15 | 15.000 | 15 | 18 | 19 | 16 | no |
| E1 | 10 | 50 | 4 | 26 | 26.384 | 27 | 27 | 32 | 27 | yes |
| E1 | 10 | 100 | 0 | 47 | 47.015 | 48 | 50 | 58 | 48 | yes |
| E1 | 10 | 100 | 1 | 47 | 47.000 | 47 | 52 | 56 | 48 | no |
| E1 | 10 | 100 | 4 | 48 | 48.029 | 49 | 53 | 60 | 50 | no |
| E1 | 20 | 100 | 1 | 52 | 52.318 | 53 | 53 | 62 | 53 | yes |
| E1 | 20 | 100 | 3 | 47 | 47.000 | 47 | 48 | 58 | 48 | no |
| E1 | 30 | 100 | 2 | 49 | 49.318 | 50 | 50 | 62 | 50 | yes |
| E1 | 10 | 150 | 0 | 66 | 66.000 | 66 | 74 | 83 | 69 | no |
| E1 | 10 | 150 | 2 | 70 | 70.000 | 70 | 75 | 84 | 72 | no |
| E1 | 10 | 150 | 3 | 64 | 64.000 | 64 | 70 | 78 | 66 | no |
| E1 | 10 | 150 | 4 | 67 | 67.000 | 67 | 73 | 84 | 70 | no |
| E1 | 20 | 150 | 0 | 79 | 79.000 | 79 | 80 | 94 | 80 | no |
| E1 | 20 | 150 | 4 | 68 | 68.133 | 69 | 69 | 85 | 69 | yes |
| E1 | 30 | 150 | 0 | 89 | 89.318 | 90 | 90 | 101 | 90 | yes |

Theta closes the gap on 6 of 15 open instances.

### E7b - Szegedy theta-plus on the instances still open (incl. the 200-gate ones)

theta-plus >= theta and still <= chi (docs/THEORY.md, Proposition 9); certified by the same repair.

| exp. | m | gates | seed | clique/Jackson LB | theta | theta-plus (certified) | solver | new LB | MKCO | proven optimal |
|---|---:|---:|---:|---:|---:|---:|---|---:|---:|:---:|
| E3 | 10 | 40 | 4 | 15 | 15.000 | 15.000 | CLARABEL | 15 | 16 | no |
| E1 | 10 | 100 | 1 | 47 | 47.000 | 47.000 | CLARABEL | 47 | 48 | no |
| E1 | 10 | 100 | 4 | 48 | 48.029 | 48.077 | CLARABEL | 49 | 50 | no |
| E1 | 20 | 100 | 3 | 47 | 47.000 | 47.000 | CLARABEL | 47 | 48 | no |
| E1 | 10 | 150 | 0 | 66 | 66.000 | 66.000 | CLARABEL | 66 | 69 | no |
| E1 | 10 | 150 | 2 | 70 | 70.000 | 70.000 | CLARABEL | 70 | 72 | no |
| E1 | 10 | 150 | 3 | 64 | 64.000 | 64.000 | CLARABEL | 64 | 66 | no |
| E1 | 10 | 150 | 4 | 67 | 67.000 | 67.000 | CLARABEL | 67 | 70 | no |
| E1 | 20 | 150 | 0 | 79 | 79.000 | 79.000 | CLARABEL | 79 | 80 | no |
| E1 | 10 | 200 | 1 | 91 | – | 90.999 | SCS | 91 | 95 | no |
| E1 | 10 | 200 | 4 | 87 | – | 87.000 | SCS | 87 | 92 | no |
| E1 | 20 | 200 | 0 | 95 | – | 95.033 | SCS | 96 | 96 | yes |
| E1 | 20 | 200 | 2 | 94 | – | 94.292 | SCS | 95 | 96 | no |
| E1 | 30 | 200 | 3 | 102 | – | 101.997 | SCS | 102 | 103 | no |

Theta-plus closes 1 of 14 remaining instances.

