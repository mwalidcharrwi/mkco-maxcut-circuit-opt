# Paper package

Everything needed to draft the MKCO paper, organised for a writing assistant.

| Path | What it is |
|---|---|
| `PAPER_PROMPT.md` | The prompt to paste into the chat, with the paper structure and the rules for numbers and comparisons. |
| `RESULTS_DIGEST.md` | All results in one document: summary, gap, contributions with evidence, framework, theory statements, setup, results by research question, figure captions, limitations, claims-to-evidence map, references. |
| `figures/fig1`–`fig8` | New paper figures (PDF vector + PNG): framework workflow, worked example, certified-optimal share, IBM overview, noise-aware selection, crosstalk under a depth budget, capability matrix, theory map. |
| `figures/*.png` (others) | Figures from the technical report. |
| `tables/key_*.md` | Compact tables used in the digest. |
| `tables/ibm127_all.csv` | Every per-circuit number for the 13 IBM-127 circuits. |
| `tables/full_*.md` | Complete generated tables of every experiment. |
| `supplement/` | Technical report, proofs (THEORY.md) and related-work notes. |
| `mkco_paper_package.zip` | All of the above in one file for upload (not committed). |

## Rebuild

From the repository root:

```bash
python paper/make_figures.py
python paper/build_package.py
```

`build_package.py` regenerates the key tables from the result JSON files,
fills `digest_template.md` into `RESULTS_DIGEST.md`, copies the report figures,
full tables and supplements, and writes the zip.
