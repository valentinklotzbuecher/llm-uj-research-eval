# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a research project that uses LLMs to evaluate academic research papers based on The Unjournal's metrics, and compares the results to human evaluations. The project is built as a Quarto book combining R (for data analysis/visualization) and Python (for LLM API calls and evaluation pipeline).

**Live site:** https://llm-uj-research-eval.netlify.app

## Environment Setup

This project uses **both R and Python** in a mixed environment:

### Python Environment (via conda)

```bash
# Create/update the conda environment
conda env create -f environment.yml  # first time
conda env update -n qpy311 -f environment.yml  # update existing

# Activate
conda activate qpy311

# Tell Quarto which Python to use
export QUARTO_PYTHON="$(which python)"
```

The conda environment `qpy311` includes Python 3.11, OpenAI client, pdfplumber, pandas, numpy, and Jupyter components.

### R Environment (via renv)

```r
# In RStudio or R console
install.packages("renv")
renv::restore()
```

The R packages are managed in `renv.lock`. Key dependencies include ggplot2, dplyr, tidyr, and related tidyverse packages.

### API Keys

- OpenAI API key must be in `key/openai_key.txt` (git-ignored)
- The Python code reads this file automatically on startup

## Building and Rendering

### Render the full site

```bash
quarto render
```

Output goes to `_book/` directory.

### Render a single document

```bash
quarto render index.qmd
quarto render methods.qmd
quarto render results.qmd
```

### Check your setup

```bash
quarto check
```

### Preview during development

```bash
quarto preview
```

## Project Architecture

### Document Structure

The Quarto book is organized into chapters:

- **index.qmd**: Introduction, motivation, related work
- **methods.qmd**: Data sources, LLM evaluation pipeline, system prompts, JSON schema
- **results.qmd**: Analysis and visualizations comparing LLM vs human evaluations
- **questions_answers.qmd**: Q&A section
- **discussion.qmd**: Discussion and implications (focused on LLM evaluation project only)
- **references.qmd**: Bibliography

**Appendices:**
- **paper_response_analysis.qmd**: Separate analysis tracking whether authors updated papers in response to Unjournal evaluations (not part of main LLM evaluation discussion)

Configuration: `_quarto.yml`

### Data Flow and Directory Structure

**IMPORTANT: Data directory organization:**

- **`data/`**: Production LLM evaluation results (large runs, ~40 papers)
  - `metrics_long.csv` - Primary data file used by `results.qmd` and `slides_vk/index.qmd`
  - `combined_long.csv` - All metrics combined
  - `tiers_long.csv` - Journal tier predictions
  - `metrics_long_gpt-5.csv` - Legacy GPT-5 run for comparison
  - Pre-computed human evaluation data (`.rds` files)

- **`results/`**: New/test runs and metadata tracking
  - `llm_runs_metadata.csv` - Master tracking file for all evaluation runs
  - `jobs_index.csv` - Active job status tracking
  - `{run_id}/` - Isolated directories for tracked runs (see Tracking System below)

- **`papers/`**: Input PDF files for evaluation

**Standard data flow:**

1. **Input**: PDFs of research papers in `papers/` directory
2. **Processing**: Python code in `methods.qmd` uploads PDFs to OpenAI API and gets structured JSON evaluations
3. **Storage**: Evaluation results saved to `results/` or `results/{run_id}/` as CSV files:
   - `combined_long.csv`: All metrics in long format
   - `metrics_long.csv`: Percentile ratings (0-100 scale)
   - `tiers_long.csv`: Journal tier predictions (0-5 scale)
   - `json/`: Individual paper response files
4. **Analysis**: R code chunks in `results.qmd` read CSVs from `data/` directory (production data)

### Key Python Components (in methods.qmd)

The LLM evaluation pipeline includes:

- **File Upload & Caching**: Content-hashed file IDs stored in `cache/file_ids.json` to avoid re-uploading PDFs
- **Rate Limiting**: `TokenPacer` class manages TPM (tokens per minute) and RPM (requests per minute) limits with exponential backoff
- **Structured Output**: JSON Schema enforcement via OpenAI's structured outputs API
- **Retry Logic**: `call_with_retries()` handles 429 rate limits and transient errors
- **Schema**: `COMBINED_SCHEMA` defines all metrics (7 percentile ratings + 2 tier predictions), each with midpoint/bounds and rationale

**Metrics evaluated:**
- Percentile (0-100): overall, claims_evidence, methods, advancing_knowledge, logic_communication, open_science, global_relevance
- Tiers (0-5): tier_should, tier_will

### System Prompts

The file `system_prompts.py` contains three main prompts used historically:

- `SYSTEM_PROMPT_MANUALFIX_NOUJ`: Full text from Unjournal guidelines, used for comprehensive evaluations
- `SYSTEM_PROMPT_GUIDELINES`: Shorter version referencing the Unjournal URL
- `TIERS_SYSTEM_PROMPT_MANUALFIX`: Focused on journal tier predictions only
- `FULL_GUIDELINES_PROMPT`: Complete evaluator guidelines in markdown format

**Current system prompt** is defined directly in `methods.qmd` as `SYSTEM_PROMPT_COMBINED` and is injected into the API call.

### LLM Evaluation Run Tracking System

**Purpose:** Track all LLM evaluation runs with complete metadata including model, prompt version, papers evaluated, and output locations. Ensures reproducibility and enables systematic comparison between different prompts/models.

**Key files:**
- `track_llm_run.py` - CLI tool for managing evaluation runs
- `results/llm_runs_metadata.csv` - Master tracking file (one row per run)

**Tracked metadata fields:**
- `run_id`: Unique identifier (format: `YYYYMMDD_model_promptversion`)
- `date`, `model`, `prompt_version`, `prompt_description`
- `prompt_file`: Location of prompt text or reference to source (e.g., `methods.qmd:SYSTEM_PROMPT_COMBINED`)
- `num_papers`, `papers_evaluated`: Paper count and comma-separated list
- `output_combined_long`, `output_metrics_long`, `output_tiers_long`, `output_json_dir`: Output file paths
- `notes`: Additional context about the run
- `status`: `in_progress`, `completed`, or `failed`

**CLI commands:**

```bash
# Start a new run (creates directory structure and metadata entry)
python track_llm_run.py start \
  --model gpt-5-pro \
  --prompt-version v3_diagnostic \
  --description "Testing diagnostic assessment approach" \
  --notes "Selected 10 papers with strong methodological critiques" \
  --prompt-file example_prompt.txt  # Copy prompt to run directory
  # OR
  --prompt-source "methods.qmd:line_312"  # Reference prompt location

# Complete a run (mark as done, record papers evaluated)
python track_llm_run.py complete 20251104_gpt-5-pro_v3_diagnostic \
  --papers "Paper1,Paper2,Paper3" \
  --notes "All evaluations completed successfully"

# List all runs
python track_llm_run.py list
python track_llm_run.py list --status completed

# Show detailed run information
python track_llm_run.py show 20251104_gpt-5-pro_v3_diagnostic
```

**Directory structure for tracked runs:**

```
results/
├── llm_runs_metadata.csv                    # Master tracking file
├── {run_id}/                                # Isolated run directory
│   ├── run_config.json                      # Run configuration & timestamps
│   ├── system_prompt.txt                    # Prompt text (if --prompt-file used)
│   ├── combined_long.csv                    # All metrics
│   ├── metrics_long.csv                     # Percentile ratings
│   ├── tiers_long.csv                       # Journal tiers
│   └── json/                                # Individual paper responses
│       ├── Paper1.response.json
│       └── Paper2.response.json
```

**Integration with methods.qmd pipeline:**

The pipeline in `methods.qmd` writes outputs to `results/` by default. To use tracking:

1. **Before running evaluation**: Start a tracked run
   ```bash
   python track_llm_run.py start --model gpt-5-pro --prompt-version test_v1 \
     --description "Testing new prompt" --prompt-source "methods.qmd:SYSTEM_PROMPT_COMBINED"
   ```

2. **Modify output paths** in `methods.qmd` Python chunks to write to `results/{run_id}/` instead of `results/`
   ```python
   RUN_ID = "20251104_gpt-5-pro_test_v1"  # From track_llm_run.py start
   OUT = pathlib.Path("results") / RUN_ID
   ```

3. **After evaluation completes**: Mark run as complete
   ```bash
   python track_llm_run.py complete 20251104_gpt-5-pro_test_v1 \
     --papers "Paper1,Paper2,Paper3"
   ```

**Promoting results to production:**

When a tracked run is ready to use in `results.qmd`:
1. Copy the run's CSV files to `data/` directory
2. Update file references in `results.qmd` if needed (currently uses `data/metrics_long.csv`)
3. Document the promotion in the run's notes field

**Current tracked runs:**

See `results/llm_runs_metadata.csv` for complete history. Major runs include:
- `baseline_sept_2024`: Initial baseline (~40 papers) → `data/combined_long.csv`
- `gpt5_oct_2024`: GPT-5 comparison run (~40 papers) → `data/combined_long_gpt-5.csv`
- `improved_prompt_oct28_2024`: Diagnostic assessment approach (2 papers, test run)

### Configuration Parameters

Global parameters are set in `setup_params.R`:

```r
model_choice <- "gpt-5"
data_path <- "data/"
results_path <- "results/"
papers_path <- "papers/"
n_papers <- length(list.files(papers_path, pattern = "\\.pdf$"))
```

This file is sourced at the top of each `.qmd` document.

### Paper Response Analysis Pipeline

The `paper_change_analysis/` directory contains a separate analysis pipeline:

**Purpose:** Track whether authors updated papers in response to Unjournal evaluations

**Key scripts:**
- `scripts/analyze_paper_changes.py`: Main pipeline that:
  - Matches papers between "before" (evaluation-time) and "after" (latest) versions
  - Extracts text from PDFs using pdfplumber
  - Computes line-level diffs to identify changes
  - Matches papers to evaluations using title extraction from markdown files
- `scripts/generate_potential_matches.py`: Helper to create manual matching workflow
- `scripts/llm_change_attribution.py`: (Optional) LLM analysis to assess if changes reflect evaluator feedback

**Data inputs:**
- `papers/` and `more papers/`: Before versions (at evaluation time)
- `latest_papers_post_UJ/`: After versions (latest available)
- `latest_papers_post_UJ/metadata.csv`: Paper titles and metadata
- `unjournal_evaluations/*.md`: Evaluation files with paper titles

**Data outputs:**
- `change_analysis_results.json`: Full results with line counts, text changes, evaluation matches
- `change_analysis_summary.csv`: Summary statistics
- `extracted_texts/`: Cached PDF text extractions

**Key technique:** Evaluation matching uses regex to extract paper titles from markdown files (e.g., `Evaluation 1 of "Paper Title"`) and fuzzy matches against metadata titles.

### Helper Scripts

The `quick_helper_scripts_for_downloads_etc/` directory contains one-off utility scripts for:

- Downloading papers and metadata from various sources
- Extracting Unjournal evaluation data from PubPub
- Processing crossref API data
- Scheduled paper downloads via cron

These are not part of the main evaluation or analysis pipelines.

## Common Development Tasks

### To evaluate new papers

**Option A: Quick evaluation (no tracking):**
1. Add PDF files to `papers/` directory
2. Run the Python evaluation code in `methods.qmd` (look for chunks labeled `llm-submit` and `llm-status-collect`)
3. Results will be saved to `results/*.csv`
4. Re-render `results.qmd` to see updated comparisons

**Option B: Tracked evaluation run (recommended for production):**
1. Add PDF files to `papers/` directory
2. Start a tracked run:
   ```bash
   python track_llm_run.py start \
     --model gpt-5-pro \
     --prompt-version my_version \
     --description "Description of this run" \
     --prompt-source "methods.qmd:SYSTEM_PROMPT_COMBINED"
   ```
3. Note the generated `run_id` (e.g., `20251104_gpt-5-pro_my_version`)
4. Modify `OUT` path in `methods.qmd` Python chunks to use the run directory:
   ```python
   OUT = pathlib.Path("results") / "20251104_gpt-5-pro_my_version"
   ```
5. Run the evaluation chunks in `methods.qmd`
6. Complete the run:
   ```bash
   python track_llm_run.py complete 20251104_gpt-5-pro_my_version \
     --papers "$(ls papers/*.pdf | xargs -n1 basename | sed 's/.pdf//' | paste -sd ',' -)"
   ```
7. If results are production-ready, copy to `data/` directory and update `results.qmd` references

### To modify evaluation criteria

1. Edit `SYSTEM_PROMPT_COMBINED` in `methods.qmd` to change instructions
2. Edit `COMBINED_SCHEMA` to add/remove metrics or change bounds
3. Update `METRICS` list if adding/removing percentile metrics
4. Update the flattening logic in the batch evaluation code if schema structure changes

### To adjust rate limits

Set environment variables before running:

```bash
export UJ_TPM=30000  # tokens per minute
export UJ_RPM=50     # requests per minute
export UJ_MODEL="gpt-5"  # model name
```

Or modify the defaults in `methods.qmd` where `TokenPacer` is instantiated.

### To work with human evaluation data

Human ratings are pre-processed R data files in `data/`:
- `all_ratings.rds`: Human evaluator ratings
- `all_jtiers.rds`: Journal tier predictions from humans

These are loaded in R chunks and joined with LLM evaluation CSVs.

### To run paper response analysis

```bash
conda activate qpy311_arm  # or qpy311
python paper_change_analysis/scripts/analyze_paper_changes.py
```

This analyzes changes between paper versions and matches them to evaluations. Results are saved to `paper_change_analysis/change_analysis_results.json` and rendered in the appendix.

## Important Notes

- **Caching**: Quarto uses aggressive caching (`freeze: auto` in `_quarto.yml`). Delete `_freeze/` if you need fresh execution.
- **Code execution**: Python and R chunks have `eval: true/false` flags. Check these if code isn't running.
- **PDF handling**: The pipeline sends PDFs directly to the API (native multimodal input), preserving figures and tables. No text extraction step.
- **JSON parsing**: The code has fallback logic to extract JSON from markdown code fences if the model wraps output incorrectly.
- **Reproducibility**: File IDs are cached by content hash. Re-running on the same PDF reuses the uploaded file.
- **Python rendering environment**: The `paper_response_analysis.qmd` appendix requires jupyter/nbformat/ipykernel packages. These are in `environment.yml` but if rendering fails with "ModuleNotFoundError: No module named 'nbformat'", run `conda env update -n qpy311_arm -f environment.yml` (or your environment name). Set `QUARTO_PYTHON` to point to the correct environment's python before rendering.
- **Content separation**: Keep discussion.qmd focused on the main LLM evaluation project only. Paper response analysis content belongs exclusively in the appendix (paper_response_analysis.qmd).

## Git Workflow

This is a collaborative research project. Current branch: `main`.

When committing:
- Follow the existing commit message style (see `git log`)
- LLM evaluations can be expensive to regenerate; be careful with changes to `methods.qmd` that would invalidate results
- Large PDFs are tracked in git (see `papers/` directory)

## Deployment

The site is hosted on Netlify. The deployment process:
1. Push to main branch on GitHub
2. Netlify automatically runs `quarto render` and deploys `_book/` contents

## Key Dependencies

**Python:** openai, pdfplumber, pandas, numpy, tiktoken, jupyter-cache
**R:** tidyverse ecosystem, renv for package management
**Build:** Quarto (requires recent version with multi-engine support)

## Architecture Insights

- **Two-language architecture**: Python handles API calls and structured data extraction; R handles statistical analysis and visualization. This is bridged via CSV files.
- **Structured outputs**: The JSON Schema approach ensures every paper gets rated on identical metrics with enforced types and bounds, making comparisons clean.
- **Rate limiting design**: The `TokenPacer` class proactively sleeps before calls based on token history, avoiding 429 errors rather than just reacting to them.
- **Credible intervals**: Both LLM and human evaluators provide 90% credible intervals (lower_bound, midpoint, upper_bound) to quantify uncertainty.
- **Ground truth**: Journal tier predictions have verifiable outcomes (where the paper actually publishes), enabling model calibration analysis.
