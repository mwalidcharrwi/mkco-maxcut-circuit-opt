"""Two-qubit block (KAK) resynthesis study: how many blocks of each benchmark
can be re-synthesised more cheaply in native ECRs?  Writes results/ibm127/blocks.json."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mkco.blocks import collect_blocks, resynthesize_blocks   # noqa: E402
from mkco.qasm import load_qasm                               # noqa: E402


def main(bdir="benchmarks/ibm127", out="results/ibm127/blocks.json"):
    rows = []
    for f in sorted(os.listdir(bdir), key=lambda x: os.path.getsize(os.path.join(bdir, x))):
        c = load_qasm(os.path.join(bdir, f))
        t = time.time()
        blocks = collect_blocks(c)
        _, st = resynthesize_blocks(c)
        row = {"circuit": c.name, "blocks_with_2q": len(blocks),
               "multi_gate_blocks": st["blocks"], "cheaper_after_kak": st["replaced"],
               "ecr_removed": st["ecr_removed"], "time_s": round(time.time() - t, 1)}
        rows.append(row)
        print(row, flush=True)
        json.dump(rows, open(out, "w"), indent=1)


if __name__ == "__main__":
    main()
