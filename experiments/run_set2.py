"""Run the full IBM-127 pipeline on the second benchmark set.

benchmarks/ibm127_set2 holds heisenberg_8, qpe_8, tfim_8 (native to
ibm_brisbane) and tfim_7_40 (native to ibm_cusco); all four end in
measurements.  (The set also included grover_10, byte-identical to the
set-1 benchmark, so its results are those of set 1.)

Steps, all writing to results/ibm127_set2: reorder-only methods and
verification, the rewrite modes, the KAK block
and regrouping studies, the crosstalk Pareto fronts, the tables, and the
noise study on each circuit's own calibration snapshot.  The noisy-simulator
runs are separate commands (see the report).
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

import add_full            # noqa: E402
import add_full_duration   # noqa: E402
import add_merge           # noqa: E402
import add_rewrite         # noqa: E402
import run_blocks          # noqa: E402
import run_ibm127          # noqa: E402
import run_noise           # noqa: E402
import run_pareto          # noqa: E402
import run_regroup         # noqa: E402
import summarize_ibm127    # noqa: E402

B, R = "benchmarks/ibm127_set2", "results/ibm127_set2"


def main():
    run_ibm127.run(B, R)
    add_merge.main(B, R)
    add_rewrite.main(B, R)
    add_full.main(B, R)
    add_full_duration.main(B, R)
    run_blocks.main(B, os.path.join(R, "blocks.json"))
    run_pareto.main(B, os.path.join(R, "pareto.json"))
    json.dump({"ibm127": list(run_regroup.ibm_rows(B, R))}, open(os.path.join(R, "regroup.json"), "w"),
              indent=1)
    run_noise.main(R)
    summarize_ibm127.main(R)


if __name__ == "__main__":
    main()
