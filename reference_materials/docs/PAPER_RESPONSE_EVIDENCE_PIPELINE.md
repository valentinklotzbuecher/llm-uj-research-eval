# Paper-response evidence pipeline

This is the reproducible support pipeline for `paper_response_analysis.qmd` and
the Unjournal data-blog summary. It finds and compares paper versions, but it
does not automatically claim that an evaluation caused a revision.

## Safe recurring refresh

Run from the repository root:

```bash
/opt/homebrew/Caskroom/miniforge/base/envs/qpy311_arm/bin/python \
  scripts/run_paper_response_refresh.py
```

The refresh:

1. assigns a stable paper ID from the DOI or normalized title;
2. preserves every distinct PDF as an immutable SHA-256 snapshot;
3. records retrieval URL, timestamp, ETag/Last-Modified metadata, and extraction quality;
4. verifies title/first-author evidence from the PDF text;
5. maps the exact PubPub summary and linked evaluation/author-response exports;
6. creates page-anchored deterministic change cards; and
7. writes a queue whose outputs always require a human decision.

For DOI landing pages that are not direct PDFs, `--browser-resolve auto` uses a
local headless Chrome process to inspect ordinary citation metadata and public
download links. It does not use Crossref, model, or other paid APIs. Direct NBER
and arXiv PDF links remain direct HTTP downloads because rendering them in a
browser would add fragility without adding evidence.

Use `--no-network` to ingest and validate the current local PDF cache without
contacting external sites.

Generated evidence is local and gitignored under:

- `data/paper_response_evidence/registry.json`
- `data/paper_response_evidence/snapshots/`
- `data/paper_response_evidence/extracted/`
- `data/paper_response_evidence/comparisons/`
- `data/paper_response_evidence/review_queue.json`

The comparison algorithm is intentionally conservative and deterministic. It
aligns page-local text chunks, suppresses reference/front-matter churn, flags
numeric changes, and produces before/after excerpts with page and section
anchors. It is a screening layer; tables, figures, OCR failures, ambiguous
version identities, and uncertain timelines are routed to human validation.

After the endpoint refresh, `scripts/screen_paper_response_matches.py` builds a
no-model correspondence-priority queue. It uses structured suggestion atoms
when available and otherwise extracts sentence-level request cues. A candidate
must have an exact evaluation mapping and eligible timeline; its evaluator quote
must resolve to the stored source line. The matcher discounts concepts found in
a local window anywhere in the earlier paper and compares each within-paper
score with cross-paper placebo matches. Its JSON and CSV outputs are gitignored
under `results/paper_response_evidence/`. High, medium, and low are inspection
priorities only: no candidate is an influence label or an aggregate outcome.

Exact manual checks of document mappings and chronology can be recorded in
`data/paper_response_manual_validations.json`. Each timeline decision is bound
to the SHA-256 hashes of both snapshots, so replacing either PDF automatically
invalidates the decision. A manually verified pre-evaluation “after” version is
recorded as a rejection and cannot enter agent triage.

Paper identity is anchored to the normalized DOI where available, so a later
title does not create a new paper record. PDF title checks compare against the
canonical tracked title and any explicitly reviewed `title_aliases` in the
manual validation registry. The output records which title matched, along with
canonical and best-match token coverage. The pipeline never infers an alias
merely from title similarity, and first-author evidence is still required for
automatic verification.

A byte-identical pair is not automatically a no-change finding. It can be
recorded as **verified no observed document change** only after checking that
the local input is credibly the evaluated draft, independently retrieving the
current public PDF, and binding the finding to their shared SHA-256 hash. If
the evaluated-draft provenance is unresolved, the pair remains in human review.

If a previously captured current endpoint fails transiently, the refresh keeps
the last selected snapshot and comparison in the queue with an explicit
`after_refresh_failed_using_cached_snapshot` warning. Cached reuse preserves
review work but does not count as a successful current-endpoint check.

When a DOI or arXiv endpoint is known to be stale, a reviewed public endpoint
override can be recorded in the same validation registry. The override requires
an HTTPS URL, evidence explaining why it is the correct version, and a check
date. This is intended for author-linked revisions and versions of record, not
automated URL guessing.

## Optional multi-agent review without API keys

After validating identity and timeline fields, list ready items from
`review_queue.json`, then run one paper:

```bash
/opt/homebrew/Caskroom/miniforge/base/envs/qpy311_arm/bin/python \
  scripts/run_paper_response_agents.py --paper-id PAPER_ID
```

The runner uses the locally authenticated Claude Code CLI in non-interactive
print mode, with tools disabled and no session persistence. Environment API
keys are removed so it uses subscription authentication rather than direct API
billing. `--triage-model haiku` and `--adjudicator-model sonnet` are defaults.

The roles have information barriers:

1. **Document atomizer (Haiku):** sees public evaluations/responses, not revisions.
2. **Change classifier (Haiku):** sees deterministic change cards, not evaluations.
3. **Sceptical link assessor (Haiku):** links only validated atom/card IDs and must list alternatives.
4. **Adjudicator (Sonnet):** runs only for positive candidates, disagreements, or validation failures.

Exact quotes and IDs are mechanically validated after each stage. Agent outputs
are stored under `results/paper_response_evidence/agent_runs/` and always end in
`human_review_required`. Use `--dry-run` to build and inspect the bounded packet
without any model calls.

Do not automate browser interaction with consumer model web UIs. It is brittle,
hard to audit, and can silently change behavior. The authenticated headless CLI
provides structured output and reproducible model/version records without using
an API key.

## Publication labels

Use only these evidence categories in public aggregates:

- **Explicit author acknowledgement:** a public author statement links the evaluation to a revision.
- **Documented aligned revision:** a specific evaluator suggestion aligns with a specific later change.
- **Unknown temporal association:** a later version differs, but there is no documented link.
- **No documented link:** evidence reviewed, with no matching documentation; this does not mean no influence.
- **Insufficient evidence:** identity, timeline, extraction, or document mapping is unresolved.

Reserve causal language such as “influenced” for explicit author acknowledgement.
Do not publish an uncalibrated model-generated influence percentage.

## Validation before scaling

Before using agent labels in aggregate statistics:

1. manually verify at least ten pre/post identities and dates;
2. create a written annotation guide and a gold set based on explicit public author statements;
3. double-code all proposed positive cases and a random sample of negatives;
4. run shuffled-evaluation and mismatched-paper negative controls;
5. report positive-claim precision, reviewer agreement, coverage, exclusions, and extraction failures.
