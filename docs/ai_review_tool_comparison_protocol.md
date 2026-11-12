# Comparing AI paper-review tools against human evaluations: protocol (draft)

*Drafted by Claude Code (Opus 5.5) for David Reinstein, 12 November 2026. Draft for discussion with a partner journal; nothing here has been run. It reuses the pipeline from the Williams et al. (2024) isitcredible comparison (`docs/isitcredible_vs_oneshot_williams_2026-11-10.md`) and the 30-paper critique-overlap run (`docs/critique_overlap_scaled_2026-11-10.md`).*

## Question

For papers that expert reviewers have already assessed, how well does each AI review tool find the issues the experts raised, how many of its other issues are correct and important, and what does it cost? The comparison that matters most is against a frontier model given one good prompt: a tool is worth paying for only if it beats that.

## Arms

| Arm | How it is run | Notes |
|---|---|---|
| Refine (refine.ink) | Web upload, report saved by hand | Priority arm |
| Lemma | To check: access and terms | |
| CSPaper | To check: access and terms | Used by TMLR |
| Google Deep Review | To check: access and terms | |
| CMU paper-review tool | To check: access and terms | |
| isitcredible (`review` suite) | Agent run, about a day per paper | Keep the stage reports, not only the synthesis; record the suite version and whether `audit-review` ran |
| Frontier one-shot, Claude | Opus 5.5, PDF only, no tools, the project's standard prompt (condition A) | Baseline |
| Frontier one-shot, GPT | GPT-5.2 Pro, same prompt | Baseline |
| Human-human | One expert reviewer's issues against another's | Reference level, not a tool |

Before any paper is run, record for each tool: version or date, settings, whether it searches the web or retrieves papers, what it was given (PDF only, or also code and data), price, and the terms on uploading third-party manuscripts. An arm whose terms do not allow the upload is dropped, not run quietly.

## Papers

- **Pilot:** five papers from the 30 in the scaled run, which already have frozen per-evaluator issue lists. Williams et al. (2024) is one; the other four are chosen across fields and named in the run's README before any tool is run.
- **Main run:** 10 to 15 papers, half economics or social science (Unjournal evaluations), half ML or alignment (the partner journal's reviewed papers, if they share them). Stratify so each field has at least one empirical paper with code, one formal or theory paper, and one paper whose main claims are about policy.
- **Leakage rule:** prefer papers whose expert reviews were not public when the tools were run, so no tool can find them. Where reviews are public, record whether the tool searches the web, and treat matches to issues that appear in any public review (journal referee reports included) as recall, as in the Williams note. Report coverage separately on the issues no public review raised.
- **Version rule:** every arm gets the same PDF, the version the experts reviewed, with its SHA-256 recorded.
- **Consent:** upload only public working papers, or papers whose authors have agreed.

## Human reference

- Each expert report is split into separate issues by the existing extractor (`scripts/critique_overlap_pilot.py`: Haiku 5.5, verbatim supporting quote required), one list per reviewer, labelled E1, E2 and so on. Reviewer names appear in no file, output or commit.
- Lists are frozen and hashed before any tool output is processed.
- Reviewer summaries or editor syntheses, where they exist, are a separate reference and are not pooled with the per-reviewer lists.

## Processing each tool's report

1. Save the raw report as received (private, ignored folder), with its hash.
2. Split it into issues with the same extractor and prompt as the human side; keep the tool's own severity label where it gives one. Freeze before judging.
3. Rewrite every item, human and tool, into neutral wording (the v2 judge's normalize step), so the judge cannot tell a tool by its format. Scan the rewrites for leftover tells (tool names, house phrases) and record hits.
4. Cap for length: alongside the full list, score each tool's top 10 issues by its own severity ranking (or the first 10, where it gives none). Long lists raise coverage by volume.

## Judging

- The v2 blinded judge (`scripts/run_issue_match_judge.py`): two lists labelled A and B in random order, items shuffled, four categories (same concern; same concern at different scope; same target, different problem; same topic only), reported at strict, standard and loose levels.
- Two judges from different model makers: Claude Opus 5.5 and GPT-5.6 Terra (via Codex). Where a tool is built on one maker's models, the other maker's judge is primary for that arm. Two replicates per comparison.
- Controls in every run: a cross-paper placebo (each tool's list against another paper's human issues), the human-human baseline, and the share of each tool's items that repeat an issue from any public review.

## Measures

1. **Coverage:** share of human issues the tool raised, per level, full list and top 10, with a 95% bootstrap interval over papers.
2. **Overlap:** share of the tool's items that match a human issue.
3. **Gap to baselines:** coverage minus the frontier one-shot's, and minus human-human, as paired differences over papers.
4. **Tool-only issues:** items that match no human issue. Coverage counts these as misses, though some are real (the calibration point on Williams was one). A domain expert rates a random sample of them, blind to the source and mixed with human-only issues, as correct / incorrect / can't tell and as important / minor. Ideally the original reviewers or the partner journal's reviewers do this, and are paid for it.
5. **Usefulness (optional):** an editor ranks the blinded full lists for one paper by how much they would help a decision.
6. **Cost and time:** price per paper, wall-clock time, and operator effort, recorded per arm.

## Decision rule (set before the run)

A tool counts as better than the frontier one-shot only if, under both judges, its standard-level coverage gap to the one-shot is positive with an interval excluding zero, or the expert rating shows its tool-only issues are correct and important more often than the one-shot's. A null is not equivalence: report the smallest difference the run could have detected. With 10 to 15 papers that will be large, so read the main run as a screen, not a ranking.

## Outputs and privacy

- Committed: the script, frozen hashes and counts, judgments as ids and categories, the summary with computed numbers, and the spend ledger.
- Kept private: raw tool reports, extracted tool issues, judge reasons, any unpublished manuscript text, and any tool output its maker asks to check first.
- Every reported number comes from the summary script; the write-up quotes it.
- Run the evaluator-anonymity scan on every new public file before committing.
- Not pooled with the one-shot benchmark or the scaled critique-overlap run.

## Work needed before the pilot

- Generalize `scripts/compare_isitcredible_williams.py` into a tool-agnostic harness (one folder per arm and paper, the same stages: freeze, normalize, judge, summarize), importing from `run_issue_match_judge.py` and `critique_overlap_pilot.py` rather than editing them.
- Confirm access, price and upload terms for each tool.
- Agree with the partner journal which ML or alignment papers and reviews they can share, and who runs the web-based tools.
- Estimate cost: on Williams the Claude-judge calls cost about $1.84 for 24 comparisons (`results/isitcredible_vs_oneshot_williams_2026-11-10/spend_ledger.csv`); tool fees and expert-rating time will dominate.
