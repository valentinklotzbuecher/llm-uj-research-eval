# Terra → Sol concordance: three-candidate methods note

## Scope and eligibility

This exploratory increment was run on 2026-07-18 in the dedicated branch
`codex/concordance-terra-sol-three-paper`. It did not alter confirmatory/API
results. The candidate set was fixed as the first three source-order records in
`tools/issue_annotation_ui/data.json`, before inspecting concordance. Local PDF
titles and abstracts were checked against the recorded title and both issue
sets.

- `Acemoglu_et_al._2024`: eligible; title and Türkiye democracy-information
  experiments aligned across the PDF and both issue sets.
- `Adena_and_Hager_2024`: eligible; title and Facebook postal-code fundraising
  experiment aligned across the PDF and both issue sets.
- `Benabou_et_al._2023`: excluded before judgment. Its record and human issues
  concern *Willful Ignorance and Moral Behavior*, while the local PDF and LLM
  issues concern *Ends versus Means: Kantians, Utilitarians, and Moral
  Decisions*.

The two eligible papers (10 human issues, 24 LLM issues) were sent together in
one `gpt-5.6-terra` high-effort call. Terra also marked both inputs aligned.
Only ambiguous pair judgments were sent to one `gpt-5.6-sol` high-effort call,
with a hard cap of three judgments. Stable issue IDs and the historical
30-point threshold were fixed in advance.

## Changes from escalation

| Pair | Terra | Sol | Consequence |
|---|---:|---:|---|
| Acemoglu H003 ↔ L006 | partial, 48 | related but distinct, 34 | Downgraded; remained above 30 |
| Adena–Hager H002 ↔ L006 | related but distinct, 31 | related but distinct, 27 | Crossed below 30; L006 became uncovered |
| Adena–Hager H002 ↔ L005 | partial, 56 | partial, 58 | No classification or coverage change |

Sol therefore changed one threshold-sensitive mapping out of three escalated
pairs. Human-issue coverage did not change because Adena–Hager H002 remained
covered through L005.

## Coverage calculation

A human issue is covered when at least one final, non-distinct mapping has an
overlap score of at least 30. The numerator counts unique covered human IDs,
not mappings. Human-issue coverage is that count divided by all enumerated
human issues in eligible papers. The analogous descriptive quantity for unique
LLM issue IDs is called the **LLM overlap rate**. Excluded papers enter neither
denominator.

| Paper | Human-issue coverage | LLM overlap rate |
|---|---:|---:|
| Acemoglu et al. | 2/3 = 66.7% | 3/12 = 25.0% |
| Adena–Hager | 6/7 = 85.7% | 6/12 = 50.0% |
| Pooled eligible issues | 8/10 = 80.0% | 9/24 = 37.5% |

Before Sol, the pooled LLM overlap rate was 10/24 = 41.7%; the human-issue
coverage numerator was unchanged at 8/10.

## Telemetry and artifact reuse

| Stage | Prompt characters | Input tokens | Cached input | Output tokens | Reasoning output | Duration |
|---|---:|---:|---:|---:|---:|---:|
| Terra | 14,194 | 22,077 | 0 | 3,152 | 1,034 | 60.3 s |
| Sol (three pairs) | 5,813 | 19,916 | 0 | 849 | 195 | 30.3 s |
| Recorded generation total | 20,007 | 41,993 | 0 | 4,001 | 1,229 | 90.6 s |

An identical verification rerun reused both completed call artifacts: zero new
model calls and zero new recorded token usage. The retained 41,993 input-token
total describes artifact generation; Codex reported no provider-side cached
input tokens for those original calls. Exact event streams and per-call
metadata are retained locally under
`results/concordance_codex_three_candidate_screened_batch_jul2026/calls/` but
excluded from the public package because they include machine-specific thread
and configuration metadata.

## Decision

Do not launch the full corpus yet. This increment justifies preparing a larger
preregistered-style run, but not executing it until every candidate has passed
the same title/PDF/issue alignment audit and the protocol freezes eligibility,
handling of compound human issues, pooled versus paper-weighted summaries,
ambiguity ranking under a Sol cap, and treatment of unadjudicated ambiguous
pairs. One of three candidate inputs was misaligned, and one of three escalated
pairs crossed the operational threshold; both are material at this sample
size. After those gates are met, a larger run would be justified as an
exploratory robustness study, kept separate from confirmatory API results.
