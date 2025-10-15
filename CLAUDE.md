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
- **discussion.qmd**: Discussion and implications
- **references.qmd**: Bibliography

Configuration: `_quarto.yml`

### Data Flow

1. **Input**: PDFs of research papers in `papers/` directory
2. **Processing**: Python code in `methods.qmd` uploads PDFs to OpenAI API and gets structured JSON evaluations
3. **Storage**: Evaluation results saved to `results/` directory as CSV files:
   - `combined_long.csv`: All metrics in long format
   - `metrics_long.csv`: Percentile ratings (0-100 scale)
   - `tiers_long.csv`: Journal tier predictions (0-5 scale)
   - Pre-computed human evaluation data in `data/` as `.rds` files
4. **Analysis**: R code chunks in `results.qmd` read CSVs and generate comparisons

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

### Helper Scripts

The `quick_helper_scripts_for_downloads_etc/` directory contains scripts for:

- Downloading papers and metadata from various sources
- Extracting Unjournal evaluation data from PubPub
- Processing crossref API data

These are one-off utility scripts, not part of the main pipeline.

## Common Development Tasks

### To evaluate new papers

1. Add PDF files to `papers/` directory
2. Run the Python evaluation code in `methods.qmd` (look for chunk labeled `eval-many-metrics`)
3. Results will be saved to `results/*.csv`
4. Re-render `results.qmd` to see updated comparisons

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

## Important Notes

- **Caching**: Quarto uses aggressive caching (`freeze: auto` in `_quarto.yml`). Delete `_freeze/` if you need fresh execution.
- **Code execution**: Python and R chunks have `eval: true/false` flags. Check these if code isn't running.
- **PDF handling**: The pipeline sends PDFs directly to the API (native multimodal input), preserving figures and tables. No text extraction step.
- **JSON parsing**: The code has fallback logic to extract JSON from markdown code fences if the model wraps output incorrectly.
- **Reproducibility**: File IDs are cached by content hash. Re-running on the same PDF reuses the uploaded file.

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
