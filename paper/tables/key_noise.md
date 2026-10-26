| Set | Circuit | Device | Score (10× lower noise) | Input | JK'26 | MKCO (depth only) | MKCO-ALAP | MKCO-full | **Noise-aware MKCO** (picks) |
|---|---|---|---|---:|---:|---:|---:|---:|---|
| set 1 | mult_8 | fake_brisbane | density-matrix fidelity | 0.5669 | 0.5423 | 0.5422 | 0.5455 | 0.5422 | **0.5669** (original) |
| set 1 | add_17 | fake_brisbane | state-aware ESP | 0.1468 | 0.1477 | 0.1478 | 0.1494 | 0.1478 | **0.1494** (mkco_full_alap) |
| set 1 | qae_17 | fake_brisbane | state-aware ESP | 0.1942 | 0.1963 | 0.1963 | 0.1958 | 0.1969 | **0.1969** (mkco_full_alap) |
| set 1 | qft_16 | fake_brisbane | state-aware ESP | 0.3107 | 0.3158 | 0.3158 | 0.3159 | 0.3159 | **0.3159** (mkco_alap) |
| set 1 | hubbard_8 | fake_brisbane | density-matrix fidelity | 0.0751 | 0.0702 | 0.0702 | 0.0764 | 0.0706 | **0.0767** (mkco_full_alap) |
| set 1 | hhl_8 | fake_brisbane | density-matrix fidelity | 0.0123 | 0.0138 | 0.0138 | 0.0126 | 0.0138 | **0.0138** (mkco_full) |
| set 1 | heisenberg_32 | fake_brisbane | ESP | 3.37e-05 | 3.37e-05 | 3.37e-05 | 3.37e-05 | 7.24e-05 | **7.24e-05** (mkco_full_alap) |
| set 1 | grover_10 | fake_brisbane | state-aware ESP | 1.98e-16 | 9.31e-16 | 9.30e-16 | 2.96e-16 | 9.36e-16 | **9.36e-16** (mkco_full_alap) |
| set 1 | hubbard_18 | fake_brisbane | ESP | 1.16e-26 | 1.16e-26 | 1.16e-26 | 1.16e-26 | 8.17e-26 | **2.38e-24** (mkco_full_dur) |
| set 2 | tfim_8 | fake_brisbane | density-matrix fidelity | 0.4704 | 0.4703 | 0.4703 | 0.4693 | 0.4703 | **0.4704** (original) |
| set 2 | heisenberg_8 | fake_brisbane | density-matrix fidelity | 0.3762 | 0.3774 | 0.3775 | 0.3772 | 0.3775 | **0.3775** (mkco) |
| set 2 | qpe_8 | fake_brisbane | density-matrix fidelity | 0.0928 | 0.0968 | 0.0968 | 0.0968 | 0.0968 | **0.0968** (mkco_full_alap) |
| set 2 | tfim_7_40 | fake_cusco | density-matrix fidelity | 0.0136 | 0.0137 | 0.0137 | 0.0136 | 0.0139 | **0.0137** (mkco) |
