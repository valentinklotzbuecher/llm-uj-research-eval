# Project review: 7 September 2026

AI-authored review and implementation note (Astra), based on the local working tree.

## Assessment

The project has a useful contribution: structured, multidimensional expert
evaluations provide a richer comparison than accept/reject decisions, and the
stored model outputs make failures inspectable. The strongest paper is an
auditable study of agreement, systematic differences, and critique overlap in
a selected research corpus. The current evidence does not establish that an
LLM is interchangeable with another expert or that adding it improves decisions.

I would prioritize measurement validity and a genuinely prospective test over
adding more models. The project already has enough model variety to expose
the central problem: we need to know what the comparisons measure, which
papers enter each estimate, and whether apparently useful feedback survives
independent validation.

This review covered the main manuscript and active appendix analysis, stored
ratings and critique joins, the recent concordance protocol and runner,
paper-response pipeline structure, existing tests, and local build/deployment
configuration. It did not individually authenticate every PDF or evaluation,
audit every historical script, re-run paid evaluations, refresh public endpoints,
or verify production hosting settings. Existing cost-recovery work and local
configuration edits were left untouched.

## Corrections implemented

### 1. Narrow the human-equivalence claim

The introduction, abstract, discussion, methods, and results previously went
from an interval containing zero to language implying performance comparable
to another expert. That inference is not justified without a meaningful
equivalence or non-inferiority margin and sufficient precision. See
[Lakens (2017), Equivalence Tests](https://pmc.ncbi.nlm.nih.gov/articles/PMC5502906/)
for the distinction between failing to reject a difference and establishing
equivalence.

The main bootstrap also used an average panel size from all focal papers,
including single-evaluator papers outside the human-human comparison, and held
it fixed during resampling. It now uses the matched panels, recalculates the
mean panel size in each draw, and uses each table row's panel size for its
adjustment. The human correlation is no longer rounded before calculation.
The displayed interval explicitly reports invalid draws and its conditional
interpretation.

Recomputed from stored inputs:

| Quantity | Result |
|---|---:|
| GPT-5 Pro papers with human ratings | 47 |
| Matched papers with at least two human evaluators | 39 |
| Human-human overall Spearman correlation | 0.331 |
| GPT-5 Pro versus human mean, 39-paper sample | 0.627 |
| Approximately adjusted model correlation | 0.508 |
| Paired bootstrap interval for adjusted difference | −0.12 to +0.43 |
| Valid bootstrap draws | 1,965 / 2,000 |

These are descriptive estimates under the retained analysis, not a validated
individual-rater equivalence test. The interval allows a meaningful deficit
as well as a sizeable advantage. The Spearman-Brown calculation assumes a
classical reliability model; applying it to ranks and unequal panels is an
approximation. The main human baseline uses the first two evaluator rows,
whereas its human mean can include a third evaluator. Paper resampling also
conditions on the observed evaluator panel.

### 2. Exclude a documented critique mispair consistently

The July concordance note already identified that `Benabou_et_al._2023` paired
human critiques of *Willful Ignorance and Moral Behavior* with model critiques
of *Ends versus Means: Kantians, Utilitarians, and Moral Decisions*. The main
critique chapters still included this pairing.

Both chapters now use `scripts/analysis_checks.R` to exclude this key and the
previously documented Peterman mismatch, validate unique source keys, and
require a one-to-one judgment join. Raw responses remain unchanged. These
exclusions are specific to critique matching; the separate quantitative joins
need their own identity audit.

The resulting 12 eligible pairings average **79.9% human-issue coverage** and
**51.5% LLM overlap**. These are equal-paper averages of historical judge scores,
not pooled atomic-issue rates or validated factual precision. Remaining pairs
are not certified aligned merely because they are absent from the exclusion list.
The judging call uses the same GPT-5.2 Pro model as the focal critique generator;
the text now makes that dependence explicit.

### 3. Correct appendix and methods descriptions

The appendix's Opus-defined set was described as an identical sample for every
model. In the restricted agreement table, actual model Ns are 29 for four
models, 6 for Claude Sonnet 4, and 4 for GPT-5.2 Pro; the human baseline uses 29.
The revised labels disclose that these are available subsets, not matched
cross-model comparisons. The appendix's shared reliability factor remains an
explicitly approximate sensitivity calculation.

Methods now correctly state that Pearson correlation is invariant to positive
linear rescaling and offsets. They also describe the appendix's actual alpha
calculation: the human panel with the model added, rather than a model-human
mean coefficient. Panel alpha stability is not an equivalence test. Human
agreement is a reference, not a universal performance ceiling.

Unsupported guarantees were removed: one-shot performance is a baseline rather
than a guaranteed lower bound; score compression does not identify alignment
training as its cause; future publication outcomes are not automatically
contamination-free; interval widths alone do not demonstrate calibration.

### 4. Prevent silent reuse of changed concordance requests

`run_concordance_codex.py` previously reused a completed call solely because
its named output and metadata files existed. A changed prompt, schema, model,
or reasoning effort could silently receive the earlier judgment.

New calls store a SHA-256 request fingerprint covering those four inputs.
Changed requests and legacy artifacts without fingerprints now stop before
that call is made. A new run ID preserves the original artifacts; explicit
`--force` permits regeneration. Rejected reuse leaves the cached schema and
judgment intact. Existing run-level provenance is retained until a resumed
run succeeds. Old pilot artifacts were not retroactively fingerprinted because
the exact historical request must not be inferred from current code.

This protects request identity, not reproducibility of a changing hosted model
or Codex runtime. The protocol still needs recorded runtime and snapshot
information. The examples now use an aligned candidate rather than the known
mismatched Bénabou record.

## Research priorities

1. **Audit identity and information access before expanding the corpus.** Build
   a versioned manifest linking stable paper IDs to titles, DOIs, PDF hashes,
   human evaluation versions, model response files, and exclusion reasons.
   Validate both ratings and critique joins. Filenames and author-year labels
   are insufficient: the known mismatch demonstrates that attractive semantic
   matches can be produced for different papers. Record when humans had access
   to supplementary materials, correspondence, or later versions unavailable
   to the model.

2. **Use the same reference target for an additional-rater comparison.** For each
   eligible paper, hold out a human evaluator, form the reference from the
   remaining evaluators, and compare both the model and held-out human against
   that same reference. Rotate held-out evaluators, weight papers explicitly,
   and resample papers as clusters. Report rank association alongside paired
   absolute errors. Predefine the practical deficit that would matter before
   collecting a confirmatory sample. For the present data, report this as an
   exploratory sensitivity analysis, including dependence on rater ordering
   and treatment of three-evaluator papers.

3. **Validate useful critiques, including model-only concerns.** Freeze the
   issue-splitting protocol, candidate eligibility, severity definitions,
   threshold sensitivity (for example 30 versus 45), weighting, and escalation
   cap before a larger concordance run. Human adjudicators should independently
   assess a stratified sample of matches, nonmatches, and model-only concerns,
   blinded to model identity where possible. Overlap alone rewards imitation
   and cannot establish that novel critiques are wrong. Track correctness,
   importance, actionability, and redundancy separately. Keep unadjudicated
   ambiguity visible rather than treating budget-capped escalation as certainty.

4. **Test incremental value, not just correlation.** The decision-relevant
   question is whether a human using an LLM finds more valid consequential
   problems, makes better judgments, or saves time. A prospective randomized
   assisted-versus-unassisted evaluation would address this. A cheap preliminary
   analysis can compare held-out predictive performance of human-only and
   human-plus-model combinations, but fit weights and calibrations only within
   training folds. Do not treat in-sample ensemble improvements as validation.

5. **Register publication predictions prospectively.** Preserve timestamped
   predictions and PDFs before public outcomes, including acceptance or venue
   cues in manuscripts. Fix the outcome definition and follow-up horizon;
   report unresolved papers and selective early resolution. Publication venue
   is an observable institutional outcome, not a measure of intrinsic quality.
   Three elicited quantiles do not identify a full predictive distribution:
   avoid scoring rules that silently invent one.

6. **Consolidate reproducibility before release.** The main and appendix loaders
   duplicate parsing, alias reconciliation, and statistical logic. Both can
   silently drop malformed responses through `tryCatch(..., error = NULL)`.
   A shared validated loader should emit included/missing/failed counts and
   enforce one response per paper/model/criterion. Archive exact prompts,
   schemas, provider settings, PDF hashes, and model IDs per run. The current
   source's prompt does not prove historical runs used identical prompts or
   schemas. Historical cost recovery should distinguish observed usage,
   imputations, retries, cached input, and missing telemetry before claiming
   total project costs.

7. **Keep the author-response study separate from the main validity claim.**
   Its immutable snapshots, timeline checks, and placebo screening are useful
   safeguards. Textual change after an evaluation does not identify influence
   from that evaluation, and author self-reports measure another outcome again.
   Continue the human release gate and publish denominator-aware aggregates.
   Avoid allowing this additional project to postpone a defensible main paper.

## Build and verification

The actual `.github/workflows/publish-gh-pages.yml` deploys prebuilt `_book/`
without rendering. `netlify.toml` also specifies `_book/` without a build command.
Some developer notes claimed automatic rendering and named a nonexistent
workflow; those notes are corrected. Source-only changes do not update the
public paper. The historical provenance document now prominently identifies
its outdated production labels while preserving author comments.

Validation performed:

- 27 Python unit tests pass in the existing `qpy311_arm` environment, including
  cache hits, changed request components, missing legacy fingerprints, and
  preservation of rejected artifacts.
- `Rscript tests/test_analysis_checks.R` passes exclusion and reliability
  boundary tests without external calls.
- R chunks in the five analysis/introduction/methods sources parse; the main
  data loaders, bootstrap, agreement table, appendix agreement tables, and
  alpha table execute on stored inputs.
- Main Results, Ratings, and Critiques HTML pages render with fresh execution
  into a temporary local preview. Some figures emit ggrepel warnings about
  omitted overlapping labels; no numeric execution failed.

No new model evaluations were launched, and nothing was committed, pushed,
or deployed. Preview-generated changes to tracked freeze artifacts are removed
from this source review. A publication update should render the complete HTML
and PDF package from the reviewed source and check both before deploying.
