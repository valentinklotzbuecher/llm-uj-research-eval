# Revised critique-matching judge: first run (10 Nov 2026)

Claude Code (Opus 5.5), at David's request. Exploratory; not pooled with the
published figures, and nothing on the site changes. Prompts and the critique of
the old judge are in `docs/critique_matching_prompts.md`.

## What changed

| | Published judge | v2 judge |
|---|---|---|
| Judge model | GPT-5.2 Pro (also wrote the issues), medium effort | Claude Opus 5.5, high effort |
| Blinding | Lists labelled "Human Expert" and "LLM" | Both lists rewritten into neutral statements by Claude Haiku 5.5 with the same prompt; shown as List A/B, side randomised, items shuffled; no title |
| Scale | 0–100 "match quality", covered at 30+; anchors only at 40–60 and 100 | Four named categories built on locus, mechanism and implication; coverage computed in code at three levels |
| Worked examples | Contained a real study paper's miss | Invented |
| Controls | None | 6 cross-paper pairs + the 2 documented mismatches |
| Repeats | 1 | 2 per paper, different shuffles |

Levels: **strict** = same concern; **standard** = same concern, or same
mechanism with different scope; **loose** = also counts "same target, different
problem" (same result or assumption criticised for a different reason).

Human issues are the pre-split items in `tools/issue_annotation_ui/data.json`
(56 for the 12 papers). The rewrite flagged 2 as containing no critique
(attribution-only lines), leaving 54. The published judge split the same
critiques into 63 items itself. Denominators therefore differ.

## Results

**Controls behave.** All 8 control cases (unrelated lists) scored 0% coverage at
every level, and the judge said "not the same study" in all 8 and "same study"
in all 24 real cases. The chance-match floor under this rubric is about zero.

**Coverage is much lower than published.**

| | Mean per-paper coverage | Mean per-paper model-side overlap |
|---|---:|---:|
| Published judge (12 papers) | 79.9% | 51.5% |
| v2 strict | 27.5% | 10.2% |
| v2 standard | 44.0% | 17.2% |
| v2 loose | 64.0% | 33.5% |

Pooled over items and both replicates, standard-level coverage is 43/108 = 39.8%.
Of the 179 pairs the judge recorded, 30 were "same concern", 26 "same concern,
different scope", 59 "same target, different problem" and 64 "same topic only".
Seven human issues were covered only by a broader model item.

| Paper | Human items v2 (published) | Published cov / ovl | v2 strict | v2 standard | v2 loose |
|---|---|---|---|---|---|
| Acemoglu et al. 2024 | 3 (4) | 50 / 33 | 33 / 8 | 33 / 8 | 50 / 12 |
| Adena and Hager 2024 | 7 (12) | 92 / 67 | 22 / 21 | 43 / 38 | 79 / 62 |
| Bilal and Känzig 2024 | 6 (5) | 100 / 55 | 0 / 0 | 17 / 14 | 67 / 41 |
| Blimpo and Castaneda-Dower 2025 | 3 (3) | 100 / 58 | 83 / 21 | 100 / 38 | 100 / 50 |
| Bruers 2021 | 3 (2) | 50 / 17 | 0 / 0 | 33 / 4 | 33 / 4 |
| Clancy 2024 | 2 (3) | 100 / 42 | 25 / 4 | 50 / 8 | 50 / 17 |
| Dullaghan and Zhang 2022 | 6 (8) | 88 / 55 | 33 / 18 | 33 / 18 | 50 / 27 |
| Frech et al. 2023 | 2 (2) | 50 / 33 | 50 / 8 | 50 / 8 | 50 / 17 |
| Green et al. 2025 | 5 (7) | 86 / 58 | 40 / 21 | 60 / 21 | 70 / 33 |
| McGuire et al. 2024 | 4 (4) | 75 / 83 | 25 / 8 | 50 / 29 | 50 / 29 |
| Weaver et al. 2025 | 5 (5) | 80 / 50 | 0 / 0 | 40 / 8 | 70 / 46 |
| Williams et al. 2024 | 8 (8) | 88 / 67 | 19 / 12 | 19 / 12 | 100 / 62 |

v2 columns average the two replicates (coverage / overlap, %).

**Replicates agree well on items, less on pairs.** Whether a human issue counts
as covered (standard) agreed across replicates for 51 of 54 items, and for 135 of
142 model items. But only 79 of 100 pairs were found in both runs, and 59 of
those 79 got the same category. Item-level coverage is stable; category labels
near the boundaries are not.

## Spot checks (two papers, by me, not by a human expert)

- **Williams: v2 looks right.** The published judge matched the leakage critique
  (predictors measured over the outcome period inflate performance) to model
  items about mixed raster resolutions and forest covariates updated to 2018, at
  75%. Neither model item mentions outcome leakage or inflated performance. v2
  called it "same target, different problem". This fits the persistent-misses
  finding that GPT-5.2 Pro only partly caught the leakage point.
- **Bilal and Känzig: v2 may be too strict.** Both sides question whether the
  confidence intervals are valid, with different reasons (asymptotics failing
  with about 50 observations; overlapping long-horizon outcomes and persistent
  regressors). v2 called this "same target, different problem". A reasonable
  reader could call it the same concern with different scope.

So the published 80% looks generous, and v2's standard level (about 44%) may be
somewhat strict. The answer turns on the "same target, different problem"
category, which holds 59 of 179 pairs. That category is where human judgement is
needed.

## Caveats

- The rewrite step could drop detail or blur differences. Originals and rewrites
  are stored side by side in `normalized/` for checking; my reading of about 15
  found them faithful. Five residual attribution words were replaced by a logged
  substitution (`scrubbed_statements.json`). Quotation marks remain on both sides.
- Different human item splits from the published run, so per-paper numbers are
  not like-for-like.
- One judge model and two replicates. No human labels yet.
- No paper context: the judge cannot check whether a model item's claim is
  about the paper's actual content.

## Cost

$1.32 for 32 judge calls (Opus 5.5, high effort) plus $0.02 for the Haiku
rewrite of 28 lists.

## Next steps

1. **Human labels on a stratified sample**, using the existing annotation UI or
   an audit mode for it: about 40 pairs, weighted towards "same target, different
   problem" and pairs where the two judges disagree. Two annotators if possible.
   This decides which v2 level, if any, to report.
2. If v2 holds up, rerun the published figures with it and replace the headline
   with the standard and loose levels, with the published judge kept as a
   sensitivity check.
3. Then the expansion beyond 12 papers can use this judge.

## Files

- `scripts/run_issue_match_judge.py`: runner (rewrite, blinding, judge, metrics).
- `scripts/compare_issue_match_judges.py`: comparison with the published judge.
- `results/issue_match_judge_v2_opus55_2026-11-10/`: system prompt, rewrites,
  per-call judgments with unblinding keys, raw responses, spend ledger,
  `comparison.json`.
- `tests/test_run_issue_match_judge.py`.
