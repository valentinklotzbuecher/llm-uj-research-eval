# Handover: do current models still miss the experts' key critiques?

Claude Code, 4 Nov 2026, for a fresh session in this repo. David asked for it.

## Goal

Earlier one-shot runs sometimes missed the critique that human evaluators treated as most important. Find out which of those misses still happen with **Claude Opus 5.5 at high effort, run headless**, on a few key papers. Then sort the persistent misses by type of reasoning failure.

The result is a short ledger, not a manuscript change. It should be usable as a seed set for harder evaluation items: cases where we know what an expert caught and the model didn't.

## What's already known (verify; don't take on trust)

The source is `results/key_issues_comparison_results.json` (GPT-5.2 Pro, Jan 2026, single run, with GPT-5.2 Pro also as matching judge), plus a keyword check of `results/claude_opus_4_6/json/` and `results/claude_sonnet_4_20250514/json/`. The Claude check was not formally judged.

| Paper | Key expert critique the models missed | GPT-5.2 Pro | Claude (earlier) | Note |
|---|---|---|---|---|
| `Acemoglu_et_al._2024` | Significance in the field experiment depends on controlling for the prior election result; the SE halves with the control | missed | Opus 4.6 missed (noted only that online-experiment precision depends on balance controls) | Strongest case. Gray area: adjustment is legitimate if pre-specified, so a good answer checks the pre-registration and reports both |
| `Dullaghan_and_Zhang_2022` | (a) Forecasts conditional on >10 kt production read as unconditional evidence of consumer acceptance; (b) 1000× units error (FGF2, per kg vs per gram) in the table given to forecasters | (a) partly; (b) missed | Opus 4.6 and Sonnet 4 missed both; Opus called (a) only "complexity" | (b) needs the external Delft source, so it isn't a fair one-shot test. Record it under "needs external source" |
| `Williams_et_al._2024` | Predictors measured over the same period as the outcome (leakage); headline 215 Mha is about 7× the 31.6 Mha Fagan et al. benchmark with no hindcast; "validation" compares 2030 predictions with 2000–2016 outcomes | partly | Sonnet 4 missed all three (no Opus run) | Magnitude sanity check |
| `Frech_et_al._2023` | $40k/QALY back-of-envelope estimate stated without sensitivity analysis | missed | Opus 4.6 partly | Evaluators marked it "unsure" |
| `Clancy_2024` | Compares all the benefits of science with biotech risk only, leaving out AI risk; 2% discount rate justified inconsistently | partly | no Claude run | |
| `Green_et_al._2025` | Imputing SMD = 0.01 for unreported non-significant effects; excluding n<25 studies limits publication-bias detection | mostly caught; n<25 missed | check | n<25 point is debatable |

**Excluded:** `Benabou_et_al._2023` and `Peterman_et_al._2025`. Their critique and paper don't match; see `scripts/analysis_checks.R`. Don't reintroduce them.

## Tasks

1. **Confirm the human key critiques for each paper from the published evaluations**, not just the Coda curation. Mark which one the evaluators or evaluation manager treated as most important.
2. **Build a small headless Claude runner** modelled on `scripts/run_headless_codex_eval.py`:
   - Call `claude -p` with `--model claude-opus-5-5 --effort high` passed explicitly. Check `claude --help` for current flags and for how to attach a PDF.
   - Record per run: the model, effort, prompt version, a SHA-256 of the input PDF, the date and the CLI version.
   - Write outputs to `results/claude_opus_5_5_high_misses_<date>/`, and register the run with `track_llm_run.py`.
   - Use the same paper PDFs as the historical runs (`papers/`), not later versions.
3. **Run three prompt conditions per paper:**
   - **A, standard:** the existing combined Unjournal prompt and schema, for comparability with the earlier runs.
   - **B, prioritisation:** "What is the single most important problem with this paper's main claims? Then give your top five, ranked." This separates "can't find it" from "found something else first".
   - **C, recognition:** give the expert critique as a claim to assess: "An evaluator argues X. Is this right, and how much does it matter?" Run it only for papers missed in A and B. It separates failing to generate the critique from failing to recognise it.
4. **Score each condition against each key critique:** caught, partly caught, or missed, quoting the model's words. An LLM can do a provisional first pass, but mark it provisional; David checks the final calls.
5. **Classify each persistent miss by failure type:**
   - cross-referencing (an appendix or table against a main-text claim);
   - magnitude sanity check against a benchmark;
   - conditional-probability logic;
   - specification sensitivity or forking paths;
   - needs an external source;
   - prioritisation (found it, but didn't rank it as important).
6. **Write a 1–2 page summary** in `docs/`. Cover:
   - which misses persist;
   - the failure types;
   - for each persistent miss, one sentence on how to turn it into a test item with a known answer and a grading note.

## Constraints

- **Scale:** start with Acemoglu and Williams (the clearest cases), then the rest. That's three conditions across about six papers. Stop and report if anything looks off.
- **Contamination:** these papers and their published evaluations may be in training data. Note it in the summary. Treat a "catch" as weaker evidence than a "miss".
- **Privacy:**
  - Don't copy evaluator names, or any of the Coda curation's attribution tags that use names, into new committed files. Refer to "evaluator 1/2" or "the evaluators".
  - Use only content from published evaluations.
  - The evaluator-anonymity hook will flag names; treat a flag as a real stop.
- **Separation:** keep these outputs out of the manuscript chapters, and don't pool them with the one-shot benchmark. They are a separate diagnostic.
- **Git:** commit only your own files on `working-paper`. Leave other agents' uncommitted work alone. Pushing to `working-paper` triggers the GitHub Pages workflow, which only redeploys the prebuilt `_book`.

## Done when

- The runner and per-run outputs with provenance are committed.
- The ledger scores conditions A–C for each paper.
- The short summary doc lists the persistent misses and failure types.
- David has reviewed the provisional scores.
