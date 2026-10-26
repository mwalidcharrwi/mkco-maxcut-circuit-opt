# Prompt for drafting the paper

Attach `mkco_paper_package.zip` (or, if the chat cannot open zip files,
`RESULTS_DIGEST.md`, `supplement/THEORY.md`, `supplement/RELATED_WORK.md` and
the PNG figures you want it to see) and paste everything below the line.

---

You are my co-author for a research paper in quantum compilation. I am
attaching a results package for a method called **MKCO (Max-k-Cut Circuit
Optimization)**. Your job is to collect the results from the package and
write a complete, submission-quality first draft that presents the strengths
of the work clearly and honestly.

## What is in the package

- `RESULTS_DIGEST.md` — the single source of truth: summary, problem and gap,
  contributions C1–C10 with their evidence, the framework, all formal
  statements, the experimental setup, results organised by research question
  (with tables), figure list with suggested captions, limitations and a
  claims-to-evidence map. **Read it completely first.**
- `tables/` — `key_*.md` (compact tables used in the digest), `ibm127_all.csv`
  (every per-circuit number), and `full_*.md` (the complete generated tables
  of each experiment, for details and the appendix).
- `figures/` — `fig1`–`fig8` made for the paper (PDF + PNG) and the report
  figures (PNG).
- `supplement/THEORY.md` — all lemmas, theorems and propositions with proofs.
- `supplement/RELATED_WORK.md` — study notes on the related work and a
  positioning table.
- `supplement/REPORT.md` — the full technical report (use for detail only).

## Paper to write

- **Format.** LaTeX, `IEEEtran` journal style (two columns), BibTeX
  references (`refs.bib`). Target length about 12 pages plus appendix. Use
  `\includegraphics{figures/<name>.pdf}` with the file names from the package.
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

1. **Use only numbers that appear in the package.** Do not invent, round
   differently or extrapolate. If a number you want is missing, write
   `\todo{...}` instead.
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

Besides the provided figures, draw these as TikZ so they are editable:
- the pipeline of the routing extension (front layer from runs → SWAP choice
  → unroute check), small;
- a hierarchical Max-Cut recursion tree (gates split into early/late halves,
  depth ⌈log₂ k⌉, each node an Ising problem solvable by QAOA);
- optionally, a 2×2 "objective" diagram: depth / two-qubit depth / crosstalk
  under budget / duration, each with what the Max-k-Cut weights are.

## How to work

1. Read the whole package. Then output a **one-page plan**: title options, the
   abstract, the section outline with the figure/table placed in each
   section, and the claims-to-evidence map (digest §10) you will follow.
2. Without waiting, write the paper section by section as LaTeX (preamble
   first, then each section). If you run out of space, stop at a section
   boundary and continue when I say "continue".
3. Finish with `refs.bib`, then a checklist: every number in the text →
   the table or file it came from, and every `\todo` you left.
