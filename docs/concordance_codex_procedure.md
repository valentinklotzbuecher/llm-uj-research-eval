# Terra → Sol concordance procedure

This procedure re-rates overlap between enumerated human issues and LLM issues
without using metered OpenAI API calls. It uses ChatGPT-authenticated
`codex exec`, so it consumes Codex subscription quota instead.

The first pass uses `gpt-5.6-terra` at high effort. Terra maps stable human
issue IDs (`paper::H001`, etc.) to stable LLM issue IDs (`paper::L001`, etc.),
assigns an overlap label and 0–100 score, and identifies ambiguous decisions.
Only those ambiguous pair-level snippets are sent to `gpt-5.6-sol` at high
effort. Sol does not receive every issue for the paper.

Terra first checks whether the paper title, human issues, and LLM issues appear
to describe the same study. Clearly misaligned inputs are marked ineligible for
aggregate metrics rather than being rescued through generic methodological
similarities.

The default human issues come from
`tools/issue_annotation_ui/data.json:human_issue_suggestions`, where compound
critique text has already been split into separately reviewable items. The
legacy `results/key_issues_matched.json` remains accepted through `--source`
for reproduction only; it should not be used for new quantitative coverage
estimates because some papers contain several concerns collapsed into one item.

The labels are:

- `exact`: essentially the same concern, mechanism, and implication;
- `partial`: a shared substantive core with material scope differences;
- `related_but_distinct`: the same topic but a different methodological claim;
- `distinct`: no substantive concordance.

The historical coverage threshold is retained: a final overlap score of 30 or
higher counts as covered. The output calls the inverse metric “LLM overlap
rate,” not precision, because a model-only concern is not necessarily wrong.

## Cost controls

- Papers are batched within a Terra invocation, avoiding repeated fixed Codex
  context overhead. The default is three papers per call and can be changed
  with `--terra-batch-size`.
- Sol sees only ambiguous candidates, capped by `--max-sol-judgments`.
- `--sol-mode none` permits a Terra-only screening run.
- `--dry-run` reports prompt size without making a model call.
- Completed call artifacts are reused unless `--force` is supplied.
- API-key environment variables are removed from child processes.
- Reviewer/evaluator attribution markers are removed from human issue text
  before it is placed in an external Codex prompt; the raw source remains local.
- Exact token counts from Codex `turn.completed` events are saved in each call's
  metadata and aggregated in `run_config.json`.

## Small pilot

Prepare a one-paper pilot without spending quota:

```bash
python3 scripts/run_concordance_codex.py \
  --paper Benabou_et_al._2023 \
  --run-id concordance_codex_terra_sol_pilot_jul2026 \
  --max-sol-judgments 1 \
  --dry-run
```

Run Terra only first:

```bash
python3 scripts/run_concordance_codex.py \
  --paper Benabou_et_al._2023 \
  --run-id concordance_codex_terra_sol_pilot_jul2026 \
  --sol-mode none
```

To allow one hard case to be escalated to Sol, rerun with a new run ID:

```bash
python3 scripts/run_concordance_codex.py \
  --paper Benabou_et_al._2023 \
  --run-id concordance_codex_terra_sol_pilot_with_sol_jul2026 \
  --max-sol-judgments 1
```

Inspect:

- `results/<run-id>/run_config.json` for models, duration, and token usage;
- `results/<run-id>/calls/` for structured outputs, JSONL events, and logs;
- `results/<run-id>/concordance_results.json` for final mappings and metrics.

The headless result is an exploratory diagnostic. It should remain distinct
from confirmatory API-based results because subscription entitlements, Codex
agent scaffolding, and model defaults can change over time.

## Screened three-candidate follow-up

The next increment fixed the candidate set as the first three source-order
records, then checked each recorded title and both issue sets against the local
PDF before model judgment. `Benabou_et_al._2023` was excluded because the human
issues described *Willful Ignorance and Moral Behavior*, while the PDF and LLM
issues described *Ends versus Means: Kantians, Utilitarians, and Moral
Decisions*. The two aligned candidates were run together:

```bash
python3 scripts/run_concordance_codex.py \
  --paper Acemoglu_et_al._2024 \
  --paper Adena_and_Hager_2024 \
  --run-id concordance_codex_three_candidate_screened_batch_jul2026 \
  --terra-batch-size 3 \
  --max-sol-judgments 3
```

The run produced 80.0% pooled human-issue coverage and a 37.5% pooled LLM
overlap rate across the eligible inputs. Sol reviewed exactly three ambiguous
pairs; one moved from 31 to 27 and therefore crossed below the operational
threshold. See `docs/concordance_three_candidate_methods_note_jul2026.md` for
the eligibility record, mappings changed by escalation, denominator rules,
token telemetry, and decision gate for a larger run.

The public repository retains structured final results and aggregate telemetry.
Raw Codex JSONL event streams and stderr logs remain local because they contain
machine-specific thread and configuration metadata and are not needed to
reproduce the consolidated judgments.
