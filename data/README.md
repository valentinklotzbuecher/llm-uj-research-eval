# Data Directory

This directory now serves two purposes:

1. Human reference inputs used by the manuscript analysis.
2. Legacy/archival aggregate LLM CSV snapshots kept for provenance.

## What Is Actively Used in the Current Paper

`results.qmd` currently builds human reference data from:

- `rsx_evalr_rating.csv`
- `research.csv`
- `UJ_map.csv`

It then joins this with model outputs parsed from `results/<model_or_run_dir>/json/` (not from `data/metrics_long.csv`).

## Human Evaluation Files

- `all_ratings.csv`, `all_ratings.rds`
- `all_jtiers.csv`, `all_jtiers.rds`
- `rsx_evalr_rating.csv`
- `research.csv`
- `UJ_map.csv`, `UJ_map.xlsx`

These originate from The Unjournal evaluation exports and related mapping tables.

## Legacy and Archival LLM Files

Examples:

- `metrics_long.csv`
- `tiers_long.csv`
- `combined_long.csv`
- `metrics_long_gpt-5.csv`
- `combined_long_gpt-5.csv`
- `tiers_long_gpt-5.csv`
- `*_gpt5_pro_jan2026.csv`

These are retained for reproducibility/provenance and occasional back-compat checks.

## Related Directories

- `archive/`: older snapshots and prior versions
- `extracted/`: text-extraction artifacts from earlier experiments
- `human_issue_match_annotations/`: manual issue-matching annotation data
- `unjournal_evaluations/`: synced markdown evaluation corpus

## Provenance

For full lineage and update conventions, see:

- `DATA_PROVENANCE.md`
- `results/llm_runs_metadata.csv`

