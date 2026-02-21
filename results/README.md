# Results Directory

This directory is the primary home for model outputs and run metadata.

## What Lives Here

- `llm_runs_metadata.csv`: run registry (status, model, prompt version, output paths)
- `<run_id>/`: run-scoped outputs created by `track_llm_run.py`
- `<model_dir>/json/*.response.json`: model response payloads used by current analysis
- `key_issues_comparison*.json`: critique-alignment artifacts
- aggregate CSVs (`combined_long.csv`, `metrics_long.csv`, `tiers_long.csv`) for compatibility and summaries

## Current Analysis Pattern

The manuscript's `results.qmd` currently reads:

1. Human reference inputs from `data/`
2. Model response JSONs from selected directories in `results/*/json/`

The model directories used are declared in a `model_dirs` mapping in `results.qmd`.

## Run Tracking Script

Use `track_llm_run.py` from repo root.

### Start run

```bash
python track_llm_run.py start \
  --model gpt-5-pro \
  --prompt-version v1 \
  --description "..."
```

### Complete run

```bash
python track_llm_run.py complete <run_id> --papers "Paper1,Paper2"
```

### Inspect runs

```bash
python track_llm_run.py list
python track_llm_run.py show <run_id>
```

## Directory Convention for Tracked Runs

```text
results/
├── llm_runs_metadata.csv
└── <run_id>/
    ├── run_config.json
    ├── combined_long.csv
    ├── metrics_long.csv
    ├── tiers_long.csv
    └── json/
        └── *.response.json
```

## Practical Guidance

1. Keep raw JSON responses for reproducibility.
2. Treat `llm_runs_metadata.csv` as the source of truth for run state.
3. When adding a new run to manuscript comparisons, update `model_dirs` in `results.qmd`.

