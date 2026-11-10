# Critique overlap on 30 papers, with a human-to-human baseline (10 Nov 2026)

Claude Code (Opus 5.5), at David's request. Exploratory; AI judges only, no
human validation yet. Not pooled with the published figures, and nothing on the
site changes. Every number below is copied from the generated
`results/critique_overlap_scaled_2026-11-10/summary.md` (from `summary.json`,
by `scripts/critique_overlap_scale.py summarize`); the per-paper counts and the
cost table are there too.

## What was done

The five-paper pilot pipeline (`scripts/critique_overlap_pilot.py`; design in
`results/critique_overlap_pilot_2026-11-10/README.md`) was run, unchanged, on
every paper in `data/critique_eligibility_manifest.json` that is eligible and
has at least two substantive published evaluations: **30 papers, 61
evaluations**. Benabou and Peterman are excluded. Two papers (Clancy,
Jaroszewicz) have no known PDF date, which the pilot rule required; they are
kept, with a sensitivity table without them.

- **Human reference.** Claude Haiku 5.5 split each published evaluation into
  separate issues, seeing only that evaluation's text: 705 issues, 690 with a
  supporting quote found verbatim in the source. One list per evaluator (E1, E2,
  E3), frozen before any model issues were generated in this run. Evaluation
  manager summaries are not used.
- **Model issues.** Claude Opus 5.5, condition A (PDF only, no tools, standard
  prompt with the key-issues list), one run per paper; reused from earlier runs
  for 26 papers and generated here for four focal-set papers.
- **Judges.** GPT (`gpt-5.6-terra` via `codex exec`) and Claude Sonnet 5.5 (same
  family as the generator, so reported separately), same prompt, unlabeled and
  shuffled lists.
- **Pairings.** *Real*: all human issues for a paper against the model's list.
  *Placebo*: human issues of one paper against another paper's model list.
  *Human-human*: E1 against E2.
- **Intervals.** 95% percentile bootstrap over papers (2,000 draws), for pooled
  rates and for the paired difference between model coverage and human-human
  coverage. They reflect variation across papers, not judge or extraction noise.

## Results (pooled over issues; score ≥ 30, the historical cut-off)

| | GPT judge | Claude judge |
|---|---|---|
| Human issues the model also raised | 61.1% [54.0, 68.5] | 34.9% [29.5, 40.7] |
| Model issues a human also raised | 67.7% [61.6, 73.5] | 47.1% [41.9, 52.6] |
| Placebo: human issues matched by another paper's model | 2.4% [0.9, 4.2] | 0.9% [0.3, 1.5] |
| One evaluator's issues the other also raised | 35.6% [28.9, 42.1] | 21.5% [16.3, 27.5] |
| Model coverage minus human-human (points) | 25.6 [17.3, 34.9] | 13.4 [7.4, 19.9] |

Stricter rules give the same ordering. At score ≥ 45, human-human is 31.6%
[24.7, 37.9] (GPT) and 15.4% [10.8, 20.7] (Claude); the model-minus-human gap is
24.3 [16.3, 33.0] and 6.1 [1.0, 11.4] points. Dropping the two papers without a
PDF date changes little (gap at score ≥ 30: 24.3 [15.4, 33.5] and 12.0 [6.0,
18.4]). Per paper, model coverage exceeds human-human coverage in 25 of 30
papers (GPT) and 23 of 30 (Claude). Human-human overlap ranges from 0% to 74%
per paper under both judges; for one paper the two evaluators share no issue
(checked by hand: the reports are about different things).

Model coverage rises with the weight the evaluator gave an issue (as read by the
extractor): under GPT, 81.0% of major, 61.8% of moderate and 36.3% of minor
issues; under Claude, 58.4%, 30.2% and 13.7%.

The judges agree on whether a human issue is covered for 71.5% of the 705 issues
(kappa 0.466). Almost all disagreements are GPT counting a match that Claude
does not (193 against 8).

## How to read this against the earlier figures

- **Evaluator-vs-evaluator is not model-vs-consensus.** The human-human figure
  asks how much of one expert's list a second expert also wrote. The 12-paper
  analysis asks how much of a short *curated consensus* list the model covers.
  Consensus items are, by construction, points evaluators agreed on or a manager
  chose, so they are easier targets than a single evaluator's full list,
  including minor points. Coverage of curated items (published judge 79.9%;
  blinded v2 judge, standard level, 44.0% with Claude Opus and 60.5% with GPT,
  `docs/issue_match_judge_v2_pilot_2026-11-10.md`) is not comparable to the
  rates here, which also use a different rubric (the pilot's 0-100 score and
  labels, not v2's locus-and-mechanism categories).
- **The comparison here is closer to like-for-like**: in both the real and the
  human-human pairings each human issue is checked against one other list of
  similar length (about 12 model items; about 12 items per evaluator). But the
  lists differ in kind. Model items are longer and often bundle several points,
  which makes them easier to match; evaluators choose a focus and divide their
  attention, so low human-human overlap partly reflects different expertise and
  emphasis, not error.
- **The judge matters as much as the comparison.** GPT is consistently more
  lenient (also on the 12-paper v2 inputs). Both judges put the model above the
  human-human baseline, but the size of the gap depends on the judge. Neither
  should be quoted alone before a human audit.
- **Contamination.** These papers and evaluations were public before the
  generator's training cutoff, so the model may have seen them. That would
  inflate model coverage, not human-human overlap.
- One model run per paper and one judge call per pairing: no run-to-run
  variation is measured.

## Checks

- Extraction spot checks by hand against the published text, five reports
  (Jaroszewicz E2, Kremer 2020 E2 from this run's Haiku extraction; Williams E1,
  Bilal and Känzig E1, Alatas E2 from an earlier Sonnet extraction that was
  retired in favour of this pipeline). Items were faithful and complete. Two
  weaknesses: the extractor sometimes calls an issue "major" when the evaluator
  gave no weight, and it splits a suggested fix off from the concern it
  addresses. Haiku splits more finely than Sonnet (Williams E1: 11 against 5).
  One report (Clancy E1) has only 4 of 7 quotes verified.
- Freeze: human issues frozen before the first model call of this run;
  unchanged since (recorded in `summary.md`).
- Version check: `data/human_issue_reference/manifest.csv` cross-checks each
  PDF against the evaluated version; Alatas (2019 PDF, 2023 version evaluated) is
  ineligible in the eligibility manifest anyway.
- Anonymity: evaluators appear only as E1/E2/E3; evaluation documents are
  recorded by hashed refs, not slugs; outputs scanned with `anon_guard.py`.

## Cost

$4.15 estimated for this run (Haiku extraction $0.07, Sonnet judge $0.89,
four Opus condition-A runs $3.18), plus $1.11 for the retired Sonnet
extraction (`data/human_issue_reference/extraction_ledger.csv`). One Opus call
dropped mid-stream and was retried; its partial cost is not in the ledger.
GPT judge calls ran on the ChatGPT subscription.

## Next steps

1. Human audit of a stratified sample of judged pairs, including human-human
   ones, to decide which judge and rule to report.
2. Repeat model runs for a subset of papers to measure run-to-run variation.
3. A model-vs-single-evaluator split (model coverage of E1's issues alone,
   compared with E2's coverage of the same issues) is computable from the
   existing judgments without new calls.
