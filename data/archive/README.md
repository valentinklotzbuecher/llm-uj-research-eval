# Archive Directory

This directory contains old and experimental LLM evaluation data that is no longer used in production.

## Archived Files

### Old Versions (Superseded)
- `metrics_long_old.csv` (2024-10-08) - Previous version of metrics
- `metrics_long_old (2).csv` (2024-10-10) - Even older version
- `metrics_meta_old.csv`, `metrics_meta old.csv` - Old metadata files

### GPT-5 Experimental Run (2024-10-18)
- `combined_long_gpt-5.csv` - All metrics combined
- `metrics_long_gpt-5.csv` - Percentile ratings
- `tiers_long_gpt-5.csv` - Journal tier predictions

**Run details**:
- **Run ID**: gpt5_oct_2024
- **Model**: gpt-5
- **Prompt**: combined_v1 (SYSTEM_PROMPT_COMBINED)
- **Papers**: ~40
- **Purpose**: Testing GPT-5 model performance
- **Status**: Experimental - not used in production

See `results/llm_runs_metadata.csv` for full run details.

## Why Archived?

These files were moved to archive because:
1. **Old versions**: Superseded by newer runs with improved prompts
2. **GPT-5 test**: Experimental model testing, replaced by production gpt-4 data
3. **Schema changes**: Some files use different schemas than current production

## Current Production Data

The active production data is in `../` (parent `data/` directory):
- `metrics_long.csv` - gpt-4, baseline_sept_2024, 50 papers
- `tiers_long.csv` - gpt-4, baseline_sept_2024, 50 papers
- `combined_long.csv` - gpt-4, baseline_sept_2024, 50 papers

See `../METADATA.txt` for production data details.

## Full Documentation

See `../../DATA_PROVENANCE.md` in the root directory for complete provenance documentation.
