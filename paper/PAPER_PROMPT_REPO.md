# Prompt for drafting the paper from the GitHub repository

Use this version when the chat reads the results straight from the repository
instead of an uploaded zip. The repository is public, so any chat that can
browse the web can read the raw links below (a GitHub connector works too).

Paste everything below the line.

---

You are my co-author for a research paper in quantum compilation. All results
of my method **MKCO (Max-k-Cut Circuit Optimization)** are in the GitHub
repository **mwalidcharrwi/mkco-maxcut-circuit-opt** (branch `main`). Fetch the
results from the repository, then write a complete, submission-quality first
draft that presents the strengths of the work clearly and honestly.

## Step 0 — fetch the results (before writing anything)

Read the files through your GitHub connector if you have one; otherwise use
the raw URLs, which all start with
`https://raw.githubusercontent.com/mwalidcharrwi/mkco-maxcut-circuit-opt/main/`
followed by the path. Read them in this order:

**Required (everything needed to draft is in these):**
1. `paper/RESULTS_DIGEST.md` — the single source of truth: summary, problem
   and gap, contributions C1–C10 with evidence, framework, all formal
   statements, experimental setup, results by research question RQ1–RQ7 with
   their tables, figure list with suggested captions, limitations,
   claims-to-evidence map, references. Read it completely.
2. `paper/supplement/THEORY.md` — all lemmas, theorems and propositions with
   proofs.
3. `paper/supplement/RELATED_WORK.md` — related-work notes and the
   positioning table.

**Tables (the digest already contains the key ones; use these to check and
for the appendix):**
- `paper/tables/key_ibm.md`, `key_paper_settings.md`, `key_tdepth.md`,
  `key_routing.md`, `key_regroup.md`, `key_noise.md`, `key_noisy_backend.md`,
  `key_runtime.md` (all in `paper/tables/`)
- `paper/tables/ibm127_all.csv` — every per-circuit number for the 13 IBM-127
  circuits
- `paper/tables/full_ibm127_set1.md`, `full_ibm127_set2.md`,
  `full_paper_settings_E1-E7.md`, `full_extensions_E8-E11.md` — the complete
  generated tables of every experiment

**Figures** (`paper/figures/`; each new figure as `.pdf` for LaTeX and `.png`
to look at):
- `fig1_framework` — framework workflow
- `fig2_example` — worked example (depth 6 → certified 3)
- `fig3_certified` — share of instances proven optimal per method
- `fig4_ibm_overview` — depth reduction on the 13 IBM-127 circuits
- `fig5_noise_selection` — fidelity of MKCO orders relative to the input
- `fig6_crosstalk_budget` — crosstalk pairs removed under a depth budget
- `fig7_capabilities` — capability matrix vs prior work
- `fig8_theory_map` — dependency map of the formal results
- report figures (`.png` only): `e1_random_mcz`, `gf2_multiplier`, `e3_ccz`,
  `e4_rzz`, `e6_fanout`, `ibm127_depth`, `ibm127_crosstalk`, `ibm127_rewrite`,
  `ibm127_duration`, `pareto_crosstalk`, `runtime_scaling`, `tdepth`,
  `routing`, `noise_validation`

If you cannot display images, use the captions and the data in the digest;
you do not need to see a figure to place and caption it.

**Optional, for detail only:**
- `paper/supplement/REPORT.md` (≈130 kB, the full technical report);
- the implementation, if you want to describe an algorithm precisely:
  `mkco/optimize.py` (top-level pipeline), `mkco/depmodel.py` (mixed graph),
  `mkco/maxkcut.py` (Max-k-Cut engine), `mkco/lns.py` (window LNS),
  `mkco/hmc.py` (hierarchical Max-Cut / Ising), `mkco/bounds.py` and
  `mkco/sdp_bounds.py` (certificates), `mkco/crosstalk.py`,
  `mkco/nonclifford.py`, `mkco/route.py`, `mkco/noise.py`, `mkco/verify.py`.

**When you have fetched them, reply first with a short fetch report:** which
files you read, and which (if any) you could not open. If you could not open
`paper/RESULTS_DIGEST.md`, stop there and tell me. Do not write the paper from
memory or guesses.

## Paper to write

- **Format.** LaTeX, `IEEEtran` journal style (two columns), BibTeX
  references (`refs.bib`). Target length about 12 pages plus appendix.
  Reference figures as `\includegraphics{figures/<name>.pdf}` (or `.png` for
  the report figures); I will copy `paper/figures/` next to the `.tex` file.
- **Author.** Mohammad Walid Charrwi (leave the affiliation as a placeholder).
- **Sections.**
  1. Title (propose 3 options; the digest has candidates) and Abstract
     (≤ 200 words, with the 3–4 strongest quantitative results).
  2. Introduction: motivation (depth and idling dominate errors on NISQ
     devices; T-depth on fault-tolerant ones), the colouring line of work and
     its gap, our approach in one paragraph, a bulleted contribution list
     (C1–C10 condensed to 5–6 bullets), and the headline results. Put Fig. 7
     (capability matrix) here or in Related Work.
  3. Background and Related Work: graph colouring for circuit depth (Lee et
     al.; Jain & Kumar), commutation-aware compilation, colouring/partitioning
     in compilation (Pauli grouping, edge colouring), Max-k-Cut and SDP bounds,
     Ising/QAOA formulations, crosstalk- and noise-aware scheduling, T-depth
     optimisation, routing, two-qubit resynthesis. End with how MKCO differs.
  4. Problem Formulation and Theory: notation; Lemma 1, Lemma 2 and the audit
     corollary; Theorem 1 (exact reduction); Theorem 2 (Max-k-Cut);
     Proposition 3; Theorem 4 / Corollary 5 / Proposition 6 (Ising
     structure); Theorem 7 (certified bound); Proposition 9 (θ, θ⁺). Give
     short proofs in the text for Thm 1 and Thm 2 and move the others to the
     appendix. Use Fig. 8 (theory map) to orient the reader.
  5. The MKCO Framework: Fig. 1 (workflow) walked through stage by stage;
     Fig. 2 (worked example); the solver engine (tabu Max-k-Cut with
     k-descent, window LNS with Proposition 8, hierarchical Max-Cut with
     SA/GW/QAOA); objectives (depth, two-qubit depth, crosstalk with budget,
     capacities, duration, ALAP); gate-rewriting composition; verification.
     Include algorithm pseudocode (`algorithm2e` or `algorithmic`) for the
     main loop and for the window LNS.
  6. Extensions: non-Clifford depth (Prop 10), commutation-aware routing
     (Prop 11), state-aware idle noise and noise-aware selection (Prop 12).
  7. Experimental Setup: benchmarks, baselines, metrics, noise settings,
     verification, environment — exactly as in digest §6.
  8. Results, one subsection per research question RQ1–RQ7 of the digest,
     each opening with the question, then a table or figure, then 1–2
     paragraphs of interpretation. Recommended placement: Fig. 3 in RQ1,
     Fig. 4 + the IBM table in RQ2, Fig. 6 in RQ3, the T-depth table in RQ4,
     the routing table in RQ5, Fig. 5 + noise tables in RQ6, the runtime table
     in RQ7.
  9. Discussion and Limitations: everything in digest §9, framed
     constructively (what each limitation means and what would address it).
  10. Conclusion and future work (duration-aware crosstalk objective, real
      hardware runs, QAOA/annealer solvers at scale, re-synthesis T-depth
      comparisons).
  11. Appendix: remaining proofs, full per-circuit tables, the base-paper
      settings in detail, the SDP tables (E7/E7b).

## Rules (important)

1. **Use only numbers that appear in the repository files above.** Do not
   invent, round differently or extrapolate. If a number you want is missing,
   write `\todo{...}` instead. Cite the file each table comes from in a LaTeX
   comment (`% source: paper/tables/key_ibm.md`).
2. **Comparisons must be fair and stated precisely.**
   - The IBM-127 benchmarks are *already* Qiskit level-3 output. On them the
     reference is the input circuit; Qiskit is not a baseline there.
   - Qiskit level-3 SABRE is the baseline only for routing and block
     formation on untranspiled logical circuits (RQ5).
   - Jain & Kumar is our re-implementation (no public code); say so.
   - On the IBM circuits JK reaches the same depths as MKCO; MKCO's advantage
     there is the optimality certificate, the hardware objectives and the
     rewrite modes. Say this plainly — it strengthens credibility.
3. **Report the negative results** listed in digest §9 (QFT routing, the
   crosstalk proxy under a timing model, depth-only orders losing fidelity on
   mult_8, simulation-only noise results). Present them as scope and future
   work, not as hidden caveats.
4. **Precise language.** "Certified optimal" means depth = proven lower bound
   over all commutation-equivalent reorderings (not over all circuits). Noise
   results come from calibration snapshots and simulation, never "hardware".
5. **Citations.** Build `refs.bib` from digest §11 and RELATED_WORK.md. Mark
   any entry whose venue, year or page numbers you are not sure of with
   `% VERIFY` and do not fabricate DOIs.
6. **Style.** Academic, concise, active voice; define every symbol before
   use; consistent notation with THEORY.md (≺, M, Φ_k, LB, ϑ, ϑ⁺).

## Extra figures to add (TikZ, in the LaTeX)

Besides the repository figures, draw these as TikZ so they are editable:
- the pipeline of the routing extension (front layer from runs → SWAP choice
  → unroute check), small;
- a hierarchical Max-Cut recursion tree (gates split into early/late halves,
  depth ⌈log₂ k⌉, each node an Ising problem solvable by QAOA);
- optionally, a 2×2 "objective" diagram: depth / two-qubit depth / crosstalk
  under budget / duration, each with what the Max-k-Cut weights are.

## How to work

1. Fetch the files (Step 0) and give the fetch report.
2. Output a **one-page plan**: title options, the abstract, the section
   outline with the figure/table placed in each section, and the
   claims-to-evidence map (digest §10) you will follow.
3. Without waiting, write the paper section by section as LaTeX (preamble
   first, then each section). If you run out of space, stop at a section
   boundary and continue when I say "continue".
4. Finish with `refs.bib`, then a checklist: every number in the text → the
   repository file it came from, and every `\todo` you left.
