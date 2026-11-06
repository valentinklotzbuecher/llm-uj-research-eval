# Persistent misses with Claude Opus 5.5: provisional results

4 November 2026. Every score here is a **provisional first pass by Claude Opus 5.5**. David has not yet reviewed it. This is a separate diagnostic, kept out of the manuscript chapters and out of the one-shot benchmark.

## What was run

The question: earlier one-shot runs (GPT-5.2 Pro, Claude Opus 4.6, Claude Sonnet 4) missed some critiques the human evaluators raised. Do current models still miss them?

**Setup**
- Six papers, using the same `papers/` PDFs as the historical runs. Bénabou and Peterman stay excluded.
- Model `claude-opus-5-5`, called through the Messages API with `output_config.effort` set to `high`, adaptive thinking, and the PDF sent natively. There were no tools and no refusal fallbacks.
- One sample per condition. No call was refused.
- Estimated spend: about $13.7 of Unjournal API credit. That includes about $1.35 for two calls whose responses were lost to a runner bug, since fixed, and a $0.35 condition-C rerun on 6 Nov (Williams leakage; see the correction below).

**Conditions**
- A: the `methods.qmd` combined prompt with key issues.
- B: "single most important problem, then top five".
- C: recognition. The model is told an evaluator's critique and asked whether it is right and how much it matters. C ran for each critique that was missed or only partly caught in both A and B.

**Scoring reference:** the critiques were re-checked against the *published* evaluations (`results/claude_opus_5_5_high_misses_2026-11-04/human_reference_from_published_evaluations.md`), not just the Coda curation. Two corrections came out of that:
- The Acemoglu prior-election point came from the evaluation manager, who called it "not a major limitation".
- The Frech $40k/QALY point is only partly supported by the published record.

The full ledger, with verbatim quotes, is `results/claude_opus_5_5_high_misses_2026-11-04/ledger_provisional.csv`.

## Headline

The two clearest earlier misses **no longer persist**:
- **Acemoglu:** both A and B say that field-experiment significance depends on the 2018-vote control. A adds that the control is "pre-specified and sensible", which is the answer we were looking for.
- **Williams:** both conditions catch the gap between 215 Mha and the 31.6 Mha of observed regrowth. B ranks it first. A calls it a "~7-fold multiple ... not reconciled".

Also caught now:
- Acemoglu spillovers and framing;
- Williams socioeconomic confounding;
- Frech's mechanical GDP regression;
- Clancy's omission of AI risk (rank 4 in B);
- Green's 0.01 imputation and non-systematic search.

What still fails falls into three groups:
- one clean generation failure that the model recognises when told (Clancy);
- one logic failure (Dullaghan conditional forecasts);
- cases where the PDF does not contain the evidence the evaluators used.

In two further cases (Acemoglu change scores, Green n<25), C says the critique itself is wrong or weak. David needs to adjudicate those before they can count as misses. A third dispute (Williams leakage) turned out to be an artefact of our shortened prompt; see the correction below.

## Persistent or disputed misses (provisional)

| Paper | Critique | A / B | C verdict | Failure type | Status |
|---|---|---|---|---|---|
| Clancy 2024 | 2% discount rate open to the same criticism used to reject XPT rates | partly / partly | right, important | cross-referencing / internal consistency | persists |
| Dullaghan & Zhang 2022 | Consumer-acceptance answers conditional on >10 kt read as unconditional | missed / missed | partly right, minor | conditional-probability logic; then prioritisation | persists |
| Dullaghan & Zhang 2022 | FGF2 1000x units error in forecaster table | missed / missed | cannot assess | needs external source | persists (not a fair one-shot test) |
| Dullaghan & Zhang 2022 | TEAs presented as predictions, not conditional estimates | partly / partly | partly right, important | needs external source (reference material); prioritisation | partly persists |
| Williams 2024 | "Validation" compares 2030 predictions with 2000–2016 outcomes | missed / missed | partly right, important | needs external source (Table A1.2 is in the Supplementary Information, which our PDF lacks) | persists |
| Williams 2024 | Predictors measured over the outcome period (leakage), including SoilGrids soil data | partly / missed; soil leg not raised in either | first run (shortened wording): **wrong**; rerun with full published wording (6 Nov): **partly right, minor** | generation (soil leg); prioritisation | persists |

**Correction, 6 Nov: Williams leakage.**
- **The original prompt was shortened.** The first condition-C prompt took its wording from the Coda curation and named only NPP, burned area and road density. None of the three is in the final ten-variable model (Extended Data Fig. 2), so the model called the critique wrong.
- **The published critique is broader.** It also names soil characteristics: the joint synthesis lists them under Primary Concern 1, and evaluator 2's leakage section leads with SoilGrids. Soil organic carbon is in the final model, ranking third by Gini importance, and the paper explains its effect as carbon being "higher within and near forests".
- **The rerun.** With the full wording (claim `WIL1b_leakage_full`), the model:
  - accepts "a legitimate, partial leakage risk via SOC that the paper does not test";
  - rejects the other legs as far as the final model goes;
  - asks for a refit without the soil variables;
  - rates the point minor, because forest density and distance to forest dominate. That last step is its own untested claim.
- **The original output is kept** (`C/Williams_et_al._2024__WIL1_leakage.json`), and the ledger marks it superseded.
| Acemoglu 2024 | Use post-minus-pre change scores (online experiment) | missed / missed | **wrong**: says the headline spec already controls for baseline outcome (Table 1 col 5) | none established; disputed | David to check |
| Green 2025 | n<25 exclusion limits publication-bias detection | missed / missed | partly right, minor: the paper's selection-model methods don't rely on SE asymmetry | specification sensitivity; debatable | David to judge |
| Frech 2023 | $40k/QALY claim with no sensitivity analysis | partly / partly | partly right, minor; says the paper's benchmark is $200k, not $100k | prioritisation | weak item |

## Failure types

- **Cross-referencing and internal consistency (Clancy).** The model listed p = 0.98 as "judgmental" but never noticed that the paper's own argument against the XPT rates undercuts its 2% rate. When told, it agrees and would rank the point "mid-to-high". This is the cleanest case of failing to generate a point the model can recognise.
- **Conditional-probability logic (Dullaghan).** Neither A nor B mentions the >10 kt conditioning. When told, the model accepts the narrower version: the null correlation is "non-diagnostic", and the low bar selects worlds where demand already existed. It then rates the point minor, below panel size.
- **Needs an external source (Dullaghan FGF2; Williams Table A1.2; partly Dullaghan TEAs).** The evidence sits in reference material or a supplement that the one-shot input does not include. Earlier models got the same PDFs, so these were never fair one-shot misses.
- **Prioritisation.** For Dullaghan's conditional forecasts and TEAs, for Frech's QALY figure and for the Williams soil-data leakage, the model engages once prompted but ranks the point below other concerns. For Frech, that ranking matches the published record. For Williams it does not: the evaluators list leakage as a primary concern.
- **Wording of the critique (design lesson).** Recognition verdicts depend on how the critique is phrased. A paraphrase that dropped the strongest leg of the Williams leakage critique drew a confident "wrong"; the full published wording drew "partly right". Condition-C prompts should quote the published critique, not a summary of it.
- **Magnitude sanity check (Williams).** This was a miss in the earlier runs and is now caught, with a mechanism: uncalibrated, class-balanced random-forest scores are summed into an "expected area". No benchmark-check failure remains.
- **Specification sensitivity (Acemoglu, Green).** The Acemoglu forking-paths point is now caught. The Green point is disputed, not missed.

## Turning these into test items (one line each)

- **Clancy:** Ask whether the paper's reason for rejecting XPT-implied discount rates also applies to its own 2% rate. Known answer: yes, about 1.6 points of it comes from an AGI-by-2043 credence turned into a perpetual hazard. Grade on naming that source and asking for sensitivity over p.
- **Dullaghan, conditional:** Ask what the >10 kt-conditional acceptance questions can and cannot show. Grade on spotting the selection by the conditioning event and the non-diagnostic null correlation.
- **Dullaghan, FGF2:** Use only as a multi-document item that supplies the forecaster table and the CE Delft source. Known answer: the 1000x per-kg vs per-gram error.
- **Dullaghan, TEAs:** Ask whether TEA costs are forecasts or conditional scenarios, and how presenting them to forecasters biases the results. Grade on conditional-on-scale and on dated input costs.
- **Williams, validation:** Attach the supplement and ask what period Table A1.2 validates against. Known answer: 2030 predictions against 2000–2016 regrowth, so it is not a test of forward skill.
- **Williams, leakage:** Ask whether any predictor in the final model could encode the outcome, and how to test it. Grade on naming soil organic carbon (in the final model; the paper links it to forest proximity), noting that NPP, burned area and road density are not in the final model, and proposing an ablation without the soil variables. Whether SoilGrids was built with post-2000 land cover needs an external source.
- **Acemoglu, change scores:** If the model is right, this is a "reject a mistaken critique" item, graded on citing Table 1 col 5 and ANCOVA versus change scores.
- **Green, n<25:** A judgement item with two defensible answers. Credit either answer if it engages with the bias methods the paper actually uses and with the range of standard errors in Fig. 3.
- **Frech:** Low value. Drop it unless David confirms the benchmark.

## Caveats

- **Contamination.** These papers and their published evaluations may be in training data, so a catch is weaker evidence than a miss. The two big "now caught" results (Acemoglu, Williams) could partly reflect exposure to the evaluations.
  - **Exposure was plausible.** Most of the papers and their Unjournal evaluations were public, with DOIs and indexed on PubPub, before Opus 5.5's training cutoff (about mid-2026).
  - **The pattern argues against simple recall:**
    1. The model missed points that appear in the published evaluations (Clancy's discount rate, the Dullaghan conditional forecasts). This is the strongest evidence: recall should have produced them.
    2. What it caught can be found from the paper alone: the roughly 7× gap uses the paper's own figures, and the prior-election control appears in the main table.
    3. (Weak, corrected 6 Nov.) In condition C the model was *shown* published critiques, so it obviously saw them, and it disputed some rather than deferring. That only weakly suggests it was not recalling the evaluations, since a model can disagree after re-reading the paper either way.
  - **Partial influence on the catches can't be ruled out.**
  - **Cleaner tests:**
    - papers evaluated after the cutoff;
    - disguised variants with names, setting and numbers changed, where the flaw is kept and checked for whether catches hold.

    Disguised variants are also how these cases would become test items the model can't have memorised.
- **One sample per condition.** Catches and misses at rank 4–8 could flip on a rerun.
- **Same model family.** The provisional scorer (Opus 5.5 in Claude Code) is the same model family as the model being tested.
- **Not comparable with earlier runs.** Condition A uses the `SYSTEM_PROMPT_WITH_ISSUES` prompt, like the GPT-5.2 Pro focal run. Opus 4.6 used the combined prompt without `key_issues`. The model and interface also differ, so A/B results are not a clean like-for-like comparison with the earlier runs.
- **Clancy coverage.** Evaluation 1's report for Clancy is not in the Markdown exports, so the critique set for that paper is incomplete.

## Files

- Runner: `scripts/run_headless_claude_misses.py`.
- Outputs, raw API responses, `spend_ledger.csv` and `recognition_claims.json`: `results/claude_opus_5_5_high_misses_2026-11-04/`.
- The run is registered in `results/llm_runs_metadata.csv`.
