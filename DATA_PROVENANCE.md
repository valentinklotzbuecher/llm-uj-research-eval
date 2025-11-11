# Data Provenance and Organization

This document explains the origin, structure, and metadata for all LLM evaluation data in this repository.

## Quick Reference: Active Data Files

### Production Data (Used in Book)
All files in `data/` folder are loaded by the Quarto book via `setup_params.R
`.

DR: I don't think so. This specifies the paths but it doesn't actually load anything.
Note that this 'production data' is already an output of the code and process, coming from the papers and prompts fed into an LLM.



| File | Source Run | Model | Papers | Description |
|------|-----------|-------|--------|-------------|
| `data/metrics_long.csv` | baseline_sept_2024 | gpt-4 | 50 | **PRIMARY**: Percentile ratings (0-100) with rationale |
| `data/tiers_long.csv` | baseline_sept_2024 | gpt-4 | 50 | **PRIMARY**: Journal tier predictions (0-5) |
| `data/combined_long.csv` | baseline_sept_2024 | gpt-4 | 50 | **PRIMARY**: All metrics in single long-format file |


DR: Are these really from GPT-4? I somehow doubt it

### Input papers and evaluation report content

DR: Claude code didn't document this, but I think we should do.

*Folders*

- papers: A few papers to focus on?
- `more papers`: I think these are the papers inputs into the main LLM calls for evaluation

- paper_abstracts_meta_data: Should be a CSP file of all papers, their abstracts, and some information about the authors. This is for a sort of placebo test of whether the model is mainly/solely doing statistical discrimination

- latest_papers_post_UJ: A cron job automatically downloads the latest versions of papers here based on their DOIs. This is for the "do authors adjust" side analysis.

- unjournal_evaluations: The actual content of Unjournal's evaluations full-step. Using this somewhat in the quote do authors adjust" analysis, intend to use it in the LLM comparison in future

### Human Evaluation Data
| File | Source | Description |
|------|--------|-------------|
| `data/all_ratings.rds` | Unjournal.org | Human evaluator ratings (R data format) |
| `data/all_jtiers.rds` | Unjournal.org | Human journal tier predictions |
| `data/all_jtiers.csv` | Unjournal.org | Human journal tier predictions (CSV) |
| `data/all_ratings.csv` | Unjournal.org | Human evaluator ratings (CSV) |

DR: all_ratings.csv Seems to have journal tiers as well. Note that the first column "label_paper" (Seems to be author-date) is sometimes missing but the next column "label_paper_title" Seems to be always present


## Data Structure by Schema Version

### Schema v1: Baseline (Sept 2024) - **CURRENT PRODUCTION**
- **Model**: gpt-4
- **Prompt**: `SYSTEM_PROMPT_MANUALFIX_NOUJ` in methods.qmd
- **Date**: 2024-09-15
- **Papers**: ~50
- **Location**: `data/`

**Structure**:
```csv
paper,metric,metric_type,value,lo,hi,rationale,scale_min,scale_max
```

**Metrics included**:
- Percentiles (0-100): overall, claims_evidence, methods, advancing_knowledge, logic_communication, open_science, global_relevance
- Journal tiers (0-5): tier_should, tier_will

**Key feature**: Rationale is embedded in each metric row

### Schema v2: Combined Schema (Oct 2024)
- **Model**: gpt-5
- **Prompt**: `SYSTEM_PROMPT_COMBINED` in methods.qmd
- **Date**: 2024-10-18
- **Papers**: ~40
- **Location**: `data/archive/` (prefixed with `_gpt-5.csv`)
- **Status**: Experimental test of GPT-5 model

### Schema v3: Assessment-First (Oct 28, 2024)
- **Model**: gpt-5
- **Prompt**: `SYSTEM_PROMPT_COMBINED` (modified)
- **Date**: 2024-10-28
- **Papers**: 2 (Schuett 2023, Williams 2024)
- **Location**: `results/`

**Structure Change**: Rationale separated from metrics
- `metrics_long.csv`: Only paper,metric,midpoint,lower_bound,upper_bound
- `assessment_summaries.csv`: paper,assessment_summary (1000-word diagnostic)

**Key innovation**: LLM produces upfront diagnostic assessment before numerical ratings

### Schema v4: Timestamped Runs (Nov 2024)
- **Location**: `results/YYYYMMDD_model_description_version/`
- **Metadata**: Each run has `run_config.json` with full provenance
- **Tracking**: Centralized in `results/llm_runs_metadata.csv`

**Example**: `results/20251104_gpt-5_test_tracking_v1/`

## Run Metadata Registry

All LLM evaluation runs are tracked in `results/llm_runs_metadata.csv`:

| Field | Description |
|-------|-------------|
| run_id | Unique identifier (usually timestamp-based) |
| date | ISO date of run |
| model | Model name (gpt-4, gpt-5, etc.) |
| prompt_version | Short name for prompt variant |
| prompt_description | Human-readable description |
| prompt_file | Source file and variable name |
| num_papers | Count of papers evaluated |
| papers_evaluated | List of paper names |
| output_combined_long | Path to combined CSV |
| output_metrics_long | Path to metrics CSV |
| output_tiers_long | Path to tiers CSV |
| output_json_dir | Path to raw JSON responses |
| notes | Free text notes |
| status | completed, in_progress, failed |

## Directory Structure

```
data/
├── metrics_long.csv          # PRODUCTION: LLM percentile ratings
├── tiers_long.csv            # PRODUCTION: LLM tier predictions
├── combined_long.csv         # PRODUCTION: All metrics combined
├── all_ratings.rds           # Human evaluator ratings
├── all_jtiers.rds            # Human tier predictions
├── archive/                  # Old/experimental data
│   ├── metrics_long_old.csv
│   ├── combined_long_gpt-5.csv
│   └── ...
└── [other reference data]

results/
├── llm_runs_metadata.csv     # Master registry of all runs
├── metrics_long.csv          # Latest experimental run (Oct 28)
├── tiers_long.csv
├── assessment_summaries.csv
├── json/                     # Raw API responses
│   ├── Schuett et al. 2023.response.json
│   └── Williams et al. 2024.response.json
├── per_paper/                # Per-paper CSVs
├── archive/                  # Old results
└── YYYYMMDD_model_desc_v1/   # Timestamped runs
    ├── run_config.json       # Run metadata
    ├── metrics_long.csv
    ├── tiers_long.csv
    ├── combined_long.csv
    └── json/
```

## How to Identify Data Source

### For CSV files in `data/`:
1. Check `results/llm_runs_metadata.csv` - match file path to run_id
2. Look at date modified: `ls -l data/*.csv`
3. Check first row for schema clues (rationale column = baseline run)

### For files in `results/`:
1. If in timestamped directory: read `run_config.json`
2. Otherwise: check `llm_runs_metadata.csv` by output path
3. Look at file date and schema structure

## Prompt Evolution

| Version | Date | Key Changes | Location |
|---------|------|-------------|----------|
| baseline_v1 | Sept 2024 | Initial Unjournal guidelines | methods.qmd: SYSTEM_PROMPT_MANUALFIX_NOUJ |
| combined_v1 | Oct 2024 | Single-call all metrics | methods.qmd: SYSTEM_PROMPT_COMBINED |
| improved_v2 | Oct 28, 2024 | Assessment-first approach | methods.qmd: SYSTEM_PROMPT_COMBINED (modified) |

See `system_prompts.py` for historical prompt text.

## What's Currently Used in the Book?

**File**: `setup_params.R` sets `data_path <- "data/"`

**Data loaded**:
- `data/metrics_long.csv` - 50 papers, gpt-4, baseline_sept_2024
- `data/tiers_long.csv` - 50 papers, gpt-4, baseline_sept_2024
- `data/all_ratings.rds` - Human ratings
- `data/all_jtiers.rds` - Human tiers

**Model shown**: The book uses `model_choice <- "gpt-5-pro"` in setup_params.R but this is aspirational - the actual data is from gpt-4 baseline run.

## Archived Data

`data/archive/` contains:
- **Old versions**: `metrics_long_old.csv`, `metrics_long_old (2).csv`
- **GPT-5 experiments**: `*_gpt-5.csv` files from Oct 18 test run
- **Old metadata**: `metrics_meta_old.csv`

`results/archive/` contains old result files that predate the metadata tracking system.

## Best Practices

### When creating new LLM runs:
1. Use timestamped directory: `results/YYYYMMDD_model_description_version/`
2. Create `run_config.json` with metadata
3. Add row to `results/llm_runs_metadata.csv`
4. Include all outputs: combined_long.csv, metrics_long.csv, tiers_long.csv, json/

### When updating production data:
1. Move current production files to `data/archive/` with timestamp suffix
2. Copy new files from `results/run_id/` to `data/`
3. Update `llm_runs_metadata.csv` to mark which run is "production"
4. Document in commit message which run is now active

### When comparing runs:
1. Check `llm_runs_metadata.csv` for model, prompt_version, date
2. Verify schema compatibility (rationale location, column names)
3. Note: Different schemas may require code changes in results.qmd

## Questions?

See `CLAUDE.md` for detailed architecture notes and `README.md` for setup instructions.
