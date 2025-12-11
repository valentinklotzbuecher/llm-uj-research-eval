# Archive Directory

This directory contains superseded versions of LLM evaluation data that are no longer used in production analysis.

## Archived Files

### Old Versions (Superseded)
- `metrics_long_old.csv` (2024-10-08) - Previous version of metrics
- `metrics_long_old (2).csv` (2024-10-10) - Even older version
- `metrics_meta_old.csv`, `metrics_meta old.csv` - Old metadata files

**Why archived**: These were superseded by newer runs with improved prompts and schema.

## Active Production Data

All active data files are in the parent `data/` directory, including:

### Primary Results (GPT-5 Pro)
- `metrics_long.csv` - Current model ratings
- `tiers_long.csv` - Journal tier predictions
- `combined_long.csv` - All metrics combined

### Model Comparison Data (GPT-5)
- `metrics_long_gpt-5.csv` - **Actively used** in results.qmd for GPT-5 vs GPT-5 Pro comparison
- `combined_long_gpt-5.csv` - All GPT-5 metrics combined
- `tiers_long_gpt-5.csv` - GPT-5 tier predictions

**Note**: GPT-5 comparison files are NOT archived - they are actively used in the published analysis for model comparison (see results.qmd Section "Model comparison: GPT-5 vs GPT-5 Pro")

## Full Documentation

See `../../DATA_PROVENANCE.md` in the root directory for complete provenance documentation.
