# LLM Evaluation Results Tracking

This directory contains LLM evaluation results and metadata for tracking different evaluation runs.

## Metadata System

All evaluation runs are tracked in `llm_runs_metadata.csv` with the following fields:

- **run_id**: Unique identifier for this run (format: `YYYYMMDD_model_prompt_version`)
- **date**: Date of the run
- **model**: LLM model used (e.g., `gpt-5`, `claude-3.5`)
- **prompt_version**: Version identifier for the prompt used
- **prompt_description**: Human-readable description of the prompt
- **num_papers**: Number of papers evaluated
- **papers_evaluated**: Comma-separated list of paper identifiers
- **output_combined_long**: Path to combined results CSV
- **output_metrics_long**: Path to metrics CSV
- **output_tiers_long**: Path to tiers CSV
- **output_json_dir**: Path to JSON outputs directory
- **notes**: Additional notes about the run
- **status**: Run status (`in_progress`, `completed`, `failed`)

## Directory Structure

Each run gets its own subdirectory:

```
results/
├── llm_runs_metadata.csv          # Master tracking file
├── YYYYMMDD_model_promptversion/  # Run-specific directory
│   ├── run_config.json            # Run configuration
│   ├── combined_long.csv          # All metrics combined
│   ├── metrics_long.csv           # Percentile ratings
│   ├── tiers_long.csv             # Journal tier predictions
│   └── json/                      # Individual paper JSONs
│       ├── paper1.response.json
│       └── paper2.response.json
└── archive/                       # Old/legacy files
```

## Using the Tracking Script

The `track_llm_run.py` script (in project root) helps manage runs:

### Start a new evaluation run

```bash
python track_llm_run.py start \
  --model gpt-5 \
  --prompt-version v3 \
  --description "Testing improved prompt with upfront diagnostic"
```

This will:
- Generate a unique run ID
- Create the directory structure
- Add entry to metadata CSV
- Create a run_config.json file

### Complete a run

After running your evaluation and saving outputs:

```bash
python track_llm_run.py complete 20251104_gpt5_v3 \
  --papers "paper1,paper2,paper3,paper4,paper5"
```

### List all runs

```bash
# All runs
python track_llm_run.py list

# Only in-progress runs
python track_llm_run.py list --status in_progress

# Only completed runs
python track_llm_run.py list --status completed
```

### Show run details

```bash
python track_llm_run.py show 20251104_gpt5_v3
```

## Workflow for 10-Paper Systematic Evaluation

For the planned systematic evaluation:

1. **Start the run:**
   ```bash
   python track_llm_run.py start \
     --model gpt-5 \
     --prompt-version systematic_v1 \
     --description "10-paper systematic evaluation with improved prompt" \
     --notes "Post-cutoff papers, known methodology issues"
   ```

2. **Run your evaluation pipeline** (in methods.qmd or separate script)
   - Save outputs to the directory shown by the script
   - Use the run_id in filenames

3. **Complete the run:**
   ```bash
   python track_llm_run.py complete 20251104_gpt5_systematic_v1 \
     --papers "paper1,paper2,paper3,paper4,paper5,paper6,paper7,paper8,paper9,paper10"
   ```

4. **Update analysis code** in `results.qmd` to read from this run's directory

## Legacy Files

Files in `data/` are from earlier runs before the metadata system:
- `data/combined_long.csv` - Baseline GPT-4 run (Sept 2024)
- `data/combined_long_gpt-5.csv` - GPT-5 testing run (Oct 2024)
- `data/metrics_long_gpt-5.csv` - Corresponding metrics

These are now tracked in `llm_runs_metadata.csv` for reference.

## Best Practices

1. **Always use the tracking script** - Don't create run directories manually
2. **Include descriptive notes** - Explain what you're testing
3. **Complete runs promptly** - Mark runs as completed when done
4. **One run per prompt/model combination** - For A/B testing, use separate runs
5. **Keep outputs in run directories** - Don't mix files from different runs
6. **Document prompt changes** - Update prompt_version and description when changing prompts

## Comparing Runs

To compare different runs in your analysis:

```r
# In results.qmd or similar
metadata <- read.csv("results/llm_runs_metadata.csv")

# Load specific run
run1 <- metadata[metadata$run_id == "20251104_gpt5_v3", ]
data1 <- read.csv(run1$output_combined_long)

run2 <- metadata[metadata$run_id == "20251105_gpt5_v4", ]
data2 <- read.csv(run2$output_combined_long)

# Compare...
```
