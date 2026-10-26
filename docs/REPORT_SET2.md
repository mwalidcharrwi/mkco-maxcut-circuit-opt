Four more IBM-127-transpiled circuits were run through the same pipeline
with the same settings (`experiments/run_set2.py`, results in
`results/ibm127_set2`):
- heisenberg_8, qpe_8 and tfim_8, native to ibm_brisbane;
- tfim_7_40, native to ibm_cusco: all its ECR directions match that snapshot,
  and only 80 of 714 match ibm_brisbane.

They have 7–8 active qubits and 1.5k–4.3k gates, and two of them end in
measurements. The set's grover_10 is byte-identical to the set-1 benchmark,
so its results are those of set 1.

- **Reordering.** MKCO is certified optimal on all four for total depth
  (−0.5% to −3.0%; Set 2 Table 1) and for two-qubit depth (Set 2 Table 2),
  where the inputs were already optimal. Lee et al. gains nothing; Jain &
  Kumar reaches the same depths without a certificate.
- **Gate rewriting.** MKCO-full is 0.5–3.1% shallower than the transpiled
  input and 0.1–1.1% faster in estimated time. KAK finds no cheaper two-qubit
  block in any of these circuits (Set 2 Table 8).
- **Crosstalk.** At the optimal two-qubit depth only qpe_8 has room
  (−13.6%). With a 20% two-qubit-depth budget, the weighted Max-k-Cut removes
  34–38% of the crosstalk-prone pairs on all four (Set 2 Table 9).
- **Noise (Set 2 Table 10).** All four circuits are small enough for exact
  density-matrix simulation, each with the calibration of its own device. At
  10× lower noise:
  - qpe_8: MKCO's orders are 4.3% more faithful than the input
    (0.0968 vs 0.0928);
  - heisenberg_8: +0.3% (0.3775 vs 0.3762);
  - tfim_8: all methods within 0.3% (0.469–0.470), and `mkco_noise` keeps the
    input order;
  - tfim_7_40: close to the noise floor (1/128 ≈ 0.008). MKCO-full is best
    (0.0139 vs 0.0136); the state-aware pick, plain MKCO, scores 0.0137.

  Across all method pairs, the state-aware ESP orders the pair as the
  simulation does in 90% of cases at 10× lower noise (78% at calibrated
  noise), against 80% (64%) for the state-blind ESP.
- **Noisy simulated backend (Set 2 Table 12).** Aer ran each circuit with
  its own device noise model, 32,768 shots, at both noise levels.
  - **qpe_8 is the clear case.** At 10× lower noise every MKCO order
    (0.701–0.707) beats the input (0.679), with separated intervals, as the
    density-matrix model predicted (+4%). At calibrated noise the MKCO outputs
    score 0.34, the level of pure noise for this distribution, while the input
    falls to 0.24.
  - **heisenberg_8 and tfim_8** differ by less than the sampling spread. The
    same circuit measured twice differs by up to 0.006.
  - **tfim_7_40's counts carry no information.** Its ideal output is so broad
    that uniform noise already scores 0.479, about where every method lands.
  - **Agreement.** On the pairs that sampling separates, the density-matrix
    model, the state-aware ESP and the state-blind ESP all order the pair
    correctly: 6/6 at calibrated noise, 4/4 at 10× lower noise. In this set
    the shorter MKCO orders are also the more faithful ones, so even the
    state-blind estimate ranks them correctly.
- **A bug these circuits exposed, now fixed.** With final measurements in the
  circuit, the two-qubit model counted each measurement (one qubit plus one
  classical bit) as a two-wire layer. The bound was then for depth *including*
  the measurement layer, one more than the reported two-qubit depth (131 vs
  130 on heisenberg_8), so the table showed a bound above an achieved value.
  Measurements are now zero-duration in the two-qubit model, as in Qiskit's
  two-qubit depth, unless some gate is classically conditioned. A regression
  test covers it. The set-1 circuits have no measurements and are unaffected.
