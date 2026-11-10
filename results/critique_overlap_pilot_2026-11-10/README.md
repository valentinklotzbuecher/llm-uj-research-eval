# Critique-overlap pilot (10 November 2026)

AI-run pilot (Claude Code, at David Reinstein's request). Exploratory: five papers, one model run per paper, AI judges, no human validation yet. It is not pooled with the one-shot benchmark or the manuscript chapters.

**All results are in [`summary.md`](summary.md)**, which is generated from `summary.json` by `scripts/critique_overlap_pilot.py summarize`. This file describes the design only and states no result numbers.

## Question

The existing critique comparison covers 12 papers, uses hand-curated consensus critiques as the human reference, and has one model both write and judge. Can the comparison be extended to more papers with a reference built from the published evaluations, without the model or the extractor seeing the other side, and how much do the answers depend on the judge?

## Design

1. **Eligibility** (`scripts/build_critique_eligibility_manifest.py`, no model calls). A paper is eligible when its title is printed in the PDF, at least one substantive published evaluation quotes that title, the PDF is dated on or before the first evaluation, and the PDF does not mention The Unjournal. Title matching is normalised exact. The manifest is `data/critique_eligibility_manifest.json`; papers that fail stay in it with the reason.
2. **Selection** (`selection.json`). Eligible papers with at least two substantive individual evaluations and a known PDF date, ordered by SHA-256 of the paper label, first five. The rule looks at no outcome.
3. **Human issues** (`human_issues/`). Claude Haiku 5.5 splits each published evaluation into separate issues. It is given that evaluation's body text only: no paper, no model output, no other evaluation. Each issue carries a verbatim quote, checked against the source. The files were frozen (`human_issues_frozen.json`) before any model issues were generated in this run.
4. **Model issues** (`A/`). Claude Opus 5.5, effort high, the paper as a PDF, no tools, the standard combined prompt with the key-issues list (`scripts/run_headless_claude_misses.py`, condition A). The call never sees an evaluation. Two papers reuse the condition-A outputs of the 4 November run (`results/claude_opus_5_5_high_misses_2026-11-04/A/`), which used the same prompt, model and settings.
5. **Judging** (`judge/`). Two judges receive the same prompt: two unlabeled lists, sides assigned to "List A" and "List B" at random, items shuffled, neutral ids. One judge is from another model family (GPT, through `codex exec`); the other is Claude Sonnet 5.5, the same family as the generator.
6. **Three kinds of pairing**, all judged with the identical prompt:
   - *real*: an evaluator-level human issue list against the model's list for the same paper;
   - *placebo*: the human issues of one paper against the model issues of the next paper in the list. Any match is a false match, so this measures the judge's floor;
   - *human to human*: evaluator 1's issues against evaluator 2's for the same paper. This is the comparator for the model's coverage.
7. **Matching rules.** A judge returns a label (exact, partial, related but distinct) and a 0–100 score for each overlapping pair. Three rules are reported: score ≥ 30 (the cut-off used historically), score ≥ 45, and label exact or partial. Rates count unique issues with at least one qualifying match.

## Reading the results

- The human reference here is every issue each evaluator raised, including minor ones. The existing 12-paper analysis uses short curated consensus lists. Coverage rates from the two are not comparable.
- A model issue that matches no human issue is not thereby wrong, and a human issue the model missed is not thereby important. Neither correctness nor importance has been adjudicated; the "importance" field is the extractor's reading of the weight the evaluator gave.
- The model's issues are longer and can bundle several points, which makes them easier to match than a single evaluator's shorter items.
- These papers and their evaluations were public before the generator's training cutoff, so the model may have seen them. A match is weaker evidence than a miss.
- One run per paper and per judge call; no run-to-run variation is measured. Five papers.
- The two judges disagree on how strict to be. Until a human has checked a sample, neither judge's rates should be quoted as the result.

## Files

| Path | Contents |
|---|---|
| `selection.json` | Rule, pool size, chosen papers, evaluation files with hashes |
| `human_issues/<paper>__E<k>.json` | Extracted issues with quotes and provenance |
| `human_issues_frozen.json` | Hashes and time of the freeze |
| `A/<paper>.json` | Model output and provenance (new papers only) |
| `judge/<judge>/<pairing>.json` | Matches mapped back to original ids, with the blinding record |
| `summary.json`, `summary.md` | Computed results |
| `spend_ledger.csv` | Token usage and estimated cost per paid call |

Raw Codex event streams (`judge/codex/calls/`, `judge/codex/isolated_codex_workdir/`) stay local, as for the earlier Codex pilots, because they hold machine-specific metadata.

Evaluators are referred to as E1 and E2. Issue text and quotes come only from the published evaluations.

## Reproduce

```bash
python scripts/build_critique_eligibility_manifest.py
python scripts/critique_overlap_pilot.py select
python scripts/critique_overlap_pilot.py extract
python scripts/critique_overlap_pilot.py generate
python scripts/critique_overlap_pilot.py judge --judge sonnet
python scripts/critique_overlap_pilot.py judge --judge codex
python scripts/critique_overlap_pilot.py summarize
python -m unittest tests/test_critique_overlap_pilot.py
```

Each stage skips work that already exists. Hosted models change, so a rerun with `--force` will not reproduce the stored judgments exactly.
