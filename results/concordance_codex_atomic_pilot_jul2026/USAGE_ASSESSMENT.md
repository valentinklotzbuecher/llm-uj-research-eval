# Concordance pilot usage assessment

This was a one-paper pilot using two separately enumerated human issues and ten
LLM issues from `tools/issue_annotation_ui/data.json`.

## Recorded usage

| Stage | Model / effort | Prompt characters | Input tokens | Cached input | Output tokens | Reasoning output | Duration |
|---|---|---:|---:|---:|---:|---:|---:|
| First pass | gpt-5.6-terra / high | 6,631 | 20,058 | 0 | 1,109 | 516 | 37.7 s |
| One ambiguous pair | gpt-5.6-sol / high | 2,843 | 19,121 | 0 | 426 | 160 | 25.0 s |
| Total | | 9,474 | 39,179 | 0 | 1,535 | 676 | 62.8 s |

The dominant cost is fixed Codex agent/context overhead, not issue text. A
minimal Terra probe in the same environment used 18,314 input tokens before a
substantive prompt was supplied. The pilot therefore supports batching several
papers in one Terra call and batching several ambiguous pairs in one Sol call.

These are Codex telemetry counts, not a conversion to a percentage of the
user's subscription allowance. Subscription quota accounting and cache
weighting are not exposed by this runner, so the safe operational control is
the number of invocations plus recorded token counts.

## Pilot result

Terra placed two generic similarities near the historical 30-point coverage
threshold (28 and 32). Sol reviewed the 28-point case and assigned 24 with 91%
confidence, leaving it below the coverage threshold. This demonstrates that the
escalation step can change a threshold-sensitive decision.

The paper also appears to have a data-alignment problem: the human issues concern
belief updating and ceiling effects, while the LLM issues mostly concern
cross-task moral-choice consistency. This should be checked before interpreting
its aggregate coverage statistic.

## Suggested next increment

Run three verified, correctly aligned papers in one Terra batch. Cap Sol at
three ambiguous judgments across that batch. Review the mappings and usage
before adding another batch. Do not run all 14 papers until paper/title alignment
has been checked.
