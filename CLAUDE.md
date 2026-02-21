# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a research project that uses LLMs to evaluate academic research papers based on The Unjournal's metrics, and compares the results to human evaluations. The project is built as a Quarto book combining R (for data analysis/visualization) and Python (for LLM API calls and evaluation pipeline).

**Live site:** https://llm-uj-research-eval.netlify.app

**Current manuscript focus:** A concise working-paper structure centered on one-shot, structured LLM-vs-human evaluation comparisons.

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

- **index.qmd**: Introduction, motivation, and research question framing.
- **results.qmd**: Main findings (figures/tables used in the core working paper).
- **discussion.qmd**: Limitations, implications, governance concerns, and future work.
- **methods.qmd**: Methods chapter in prose-forward style with reproducible Python chunks.
- **references.qmd**: Bibliography.

**Appendices:**
- **results_ratings.qmd**: Extended quantitative appendix (agreement metrics, costs, additional diagnostics).
- **results_critiques.qmd**: Extended qualitative appendix (issue coverage/precision comparisons).
- **appendix_llm_traces.qmd**: Full model traces/assessment summaries for selected papers.

**UI Conventions:**
- Use `::: {.callout-note collapse="true"}` for secondary content that should be collapsed by default (e.g., detailed parameter tables, risk assessments, advisor lists)
- Use `::: {.callout-tip}` for navigation signposts and reader guidance.
- Use `::: {.callout-warning}` for work-in-progress notices

Configuration: `_quarto.yml`

### Data Flow and Directory Structure

**IMPORTANT: Data directory organization:**

- **`results/`**: Primary model outputs and tracked runs.
  - Per-model directories with raw JSON responses (for example `results/gpt5_pro_updated_jan2026/json/`).
  - `llm_runs_metadata.csv` master run registry and run-scoped CSV outputs.
  - Cross-model comparison artifacts (for example `key_issues_comparison*.json`).

- **`data/`**: Human reference data plus legacy/archival aggregate CSV snapshots.
  - Human ratings/tier exports (`rsx_evalr_rating.csv`, `research.csv`, `UJ_map.csv`, plus `.rds` snapshots).
  - Historical aggregate LLM CSVs retained for provenance and back-compat.
  - `unjournal_evaluations/` Markdown exports synced by GitHub Actions.

- **`papers/`**: Input PDFs.

**Standard data flow:**

1. **Input**: PDFs of research papers in `papers/` directory
2. **Processing**: Python code in `methods.qmd` uploads PDFs to OpenAI API and gets structured JSON evaluations
3. **Storage**: Evaluation results saved to `results/` (raw JSON plus optional run-level CSVs):
   - `combined_long.csv`: All metrics in long format
   - `metrics_long.csv`: Percentile ratings (0-100 scale)
   - `tiers_long.csv`: Journal tier predictions (0-5 scale)
   - `json/`: Individual paper response files
4. **Analysis**: `results.qmd` primarily parses model JSON files from `results/<model_run>/json/` and joins them with human-reference data from `data/`.

### Key Python Components (in methods.qmd)

The LLM evaluation pipeline includes:

- **File Upload & Caching**: Content-hashed file IDs stored in `results/.file_cache.json` to avoid re-uploading PDFs
- **Rate Limiting**: `TokenPacer` class manages TPM (tokens per minute) and RPM (requests per minute) limits with exponential backoff
- **Structured Output**: JSON Schema enforcement via OpenAI's structured outputs API
- **Retry Logic**: `call_with_retries()` handles 429 rate limits and transient errors
- **Schema**: `COMBINED_SCHEMA` defines all metrics (7 percentile ratings + 2 tier predictions), each with midpoint/bounds and rationale

**Metrics evaluated:**
- Percentile (0-100): overall, claims_evidence, methods, advancing_knowledge, logic_communication, open_science, global_relevance
- Tiers (0-5): tier_should, tier_will

### System Prompts

**Current approach:** The active system prompt is defined directly in `methods.qmd` as `SYSTEM_PROMPT_COMBINED` and is injected into the API call.

**Prompt modularization system:** The `prompts/` directory contains a modular prompt management system:

- **`prompts/components/`**: Reusable prompt components (guidelines, calibration instructions, schema definitions, metric definitions)
- **`prompts/versions/`**: Complete versioned prompts (v1_baseline_sept2024, v2_ignore_authors, v3_assessment_first, v4_assessment_expanded)
- **`prompts/builder.py`**: Utilities for composing prompts from components
- **`prompts/README.md`**: Complete documentation of the modular system

This system enables:
- Version control of prompts with clear lineage
- Reusable components across versions
- Easier A/B testing and experimentation
- Clear documentation of what changed between versions

**See `prompts/README.md` for detailed usage instructions.**

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
  --prompt-file my_prompt.txt  # Copy prompt to run directory
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

**Promoting results to analysis:**

When a tracked run is ready for the manuscript:
1. Ensure run outputs are complete in `results/{run_id}/` (especially `json/`).
2. Add/update the run in the `model_dirs` mapping in `results.qmd` (or append a new analysis chunk reading the run directory).
3. If needed for archival snapshots, export aggregate CSVs to `data/` and record provenance in metadata.

**Current tracked runs:**

Run history changes frequently; use `results/llm_runs_metadata.csv` and `python track_llm_run.py list` as the source of truth.

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

This pipeline has been moved out of this repository to `unjournal_tools_interfaces` (see `side_projects/README.md` for links). Treat references in older commits as historical context only.

### Side Projects

`side_projects/` currently serves as a pointer directory to work that has moved to `unjournal_tools_interfaces`. Do not assume side-project code in older docs still exists locally.

### Issue Annotation Tool (Manual Concordance Labeling)

**Purpose:** Browser-based UI for manually labeling the concordance between human expert critiques and LLM-identified key issues. Enables systematic assessment of coverage, precision, and alignment.

**Location:** `tools/issue_annotation_ui/`

**Key files:**
- `tools/build_issue_annotation_data.py` - Data builder that parses human critiques and LLM responses
- `tools/issue_annotation_ui/index.html` - Main annotation interface
- `tools/issue_annotation_ui/app.js` - Application logic with localStorage persistence
- `tools/issue_annotation_ui/data.json` - Generated annotation dataset
- `tools/issue_annotation_ui/README.md` - Quick reference

**Workflow:**

1. **Generate annotation data:**
   ```bash
   python3 tools/build_issue_annotation_data.py
   ```
   This parses `results/key_issues_comparison.json` and LLM response JSONs, extracts individual human issues with severity labels, and outputs `data.json` and `data.js`.

2. **Open the UI:**
   Open `tools/issue_annotation_ui/index.html` in a browser (no server required).

3. **Annotate each human issue:**
   - Select a paper from the dropdown
   - For each human-identified issue:
     - Set **match score** (0-1): How well do LLM issues capture this concern?
     - Set **confidence** (0-1): How certain are you of this assessment?
     - Check **"Context not shared with LLM"** if the human critique references information the LLM didn't have access to
     - **Link to LLM issues**: Check boxes for which LLM issues correspond to this human issue
     - Add **discussion notes** explaining your reasoning

4. **Export annotations:**
   - Download as JSON or CSV for analysis
   - Annotations are auto-saved to browser localStorage

**Data schema:**

Human issues are parsed from Coda critiques with heuristic extraction:
- Severity labels normalized to: `necessary`, `optional`, `unsure`
- Evaluator attributions (E1, E2, DR) preserved in issue text
- Enumerated lists and sentence boundaries used as delimiters

**Export fields:**
- `annotator`, `paper_id`, `paper_title`
- `human_issue_id`, `human_issue_text`, `severity`
- `match_score`, `match_confidence`, `context_not_shared`
- `linked_llm_issue_ids` (comma-separated)
- `discussion`

**Integration with analysis:**

Exported annotations can be used in `results_critiques.qmd` to compute:
- Coverage: % of human issues with match_score > threshold
- Precision: Via linked LLM issues analysis
- Inter-rater reliability: If multiple annotators label the same papers

### LLM Critique Comparison Tool

**Purpose:** Use GPT 5.2 Pro to perform detailed issue-by-issue matching between human expert critiques and LLM-identified key issues. This provides more accurate semantic matching than embedding-based cosine similarity.

**Location:** `tools/compare_issues_llm.py`

**Input/Output:**
- **Input:** `results/key_issues_comparison.json` (paper mappings with human critiques and LLM issues)
- **Output:** `results/key_issues_comparison_results.json` (detailed comparison results)

**Commands:**

```bash
# Run the full comparison (requires OpenAI API key with credits)
python tools/compare_issues_llm.py

# Process a single paper (useful for testing)
python tools/compare_issues_llm.py --paper Benabou_et_al._2023

# Dry run - parse and format without calling API
python tools/compare_issues_llm.py --dry-run

# Use a different model
python tools/compare_issues_llm.py --model gpt-4o
```

**Output format:**

The script produces detailed JSON with:
- `matched_pairs`: Each human issue with matching LLM issue(s), including:
  - `label`: Short description of the shared concern (5-10 words)
  - `match_quality`: 0-100% score
  - `match_explanation`: Brief explanation of the match
  - `detailed_discussion`: Longer analysis comparing how human and LLM framed the issue
- `unmatched_human`: Human issues not captured by LLM, with explanation
- `unmatched_llm`: LLM issues that don't match human concerns, with explanation
- `coverage_pct`: % of human issues with any LLM match (match_quality >= 30%)
- `precision_pct`: % of LLM issues that match something substantive

**Requirements:**
- OpenAI API key in `key/openai_key.txt` with sufficient credits
- Default model: `gpt-5.2-pro` (configurable via `--model` flag)

## Common Development Tasks

### To evaluate new papers

**Option A: Quick evaluation (no tracking):**
1. Add PDF files to `papers/` directory
2. Run the Python evaluation code in `methods.qmd` (for example chunks `llm-kickoff` and `llm-status-collect`)
3. Results will be saved under `results/` (raw JSON plus any run-level aggregate CSVs)
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
7. Add/update the run directory in `results.qmd` model-loading code and re-render.

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

Human reference data is loaded from `data/` (primarily `rsx_evalr_rating.csv`, `research.csv`, and `UJ_map.csv`; `.rds` snapshots are also present). These are joined with model outputs parsed from `results/*/json/`.

### To run paper response analysis

Use the migrated repository referenced in `side_projects/README.md` (`unjournal_tools_interfaces`). This pipeline is no longer maintained in this repo.

## Important Notes

- **PREFER QUARTO CHUNKS OVER STANDALONE SCRIPTS**: When adding new Python/R analysis code, put it in a Quarto chunk inside the relevant `.qmd` file (usually `methods.qmd`) rather than creating standalone scripts in `tools/` or elsewhere. This ensures:
  1. Code is visible and documented in the rendered website
  2. Results can be executed by running `quarto render`
  3. The workflow stays consistent (Valentin runs chunks, not scripts)
  Only create standalone scripts for truly reusable utilities that don't need to appear in the book.
- **Caching**: PDF rendering uses `freeze: auto` in `_quarto.yml`; appendices also set `freeze: auto`. HTML main-chapter execution is generally uncached by default. Delete `_freeze/` if you need fresh execution.
- **Code execution**: Python and R chunks have `eval: true/false` flags. Check these if code isn't running.
- **PDF handling**: The pipeline sends PDFs directly to the API (native multimodal input), preserving figures and tables. No text extraction step.
- **JSON parsing**: The code has fallback logic to extract JSON from markdown code fences if the model wraps output incorrectly.
- **Reproducibility**: File IDs are cached by content hash. Re-running on the same PDF reuses the uploaded file.
- **Python rendering environment**: The project requires jupyter/nbformat/ipykernel for Python-backed Quarto chunks. If rendering fails with missing modules, update your active environment from `environment.yml` and point `QUARTO_PYTHON` to that interpreter.

## Git Workflow

This is a collaborative research project. Active development currently happens on `working-paper`.

When committing:
- Follow the existing commit message style (see `git log`)
- LLM evaluations can be expensive to regenerate; be careful with changes to `methods.qmd` that would invalidate results
- Large PDFs are tracked in git (see `papers/` directory)

## Deployment

The site is hosted on Netlify. Deployment is triggered by pushes to the branch configured in Netlify for this repo.

**Configuration notes:**
- `embed-resources: true` in `_quarto.yml` embeds all assets (CSS, JS, images) as base64 in HTML files. This creates larger but self-contained files.
- `hypothesis: true` enables Hypothes.is annotation overlay for visitor comments. Note: Hypothesis requires external scripts from hypothes.is CDN, which may conflict with `embed-resources: true` in some browsers.
- Large HTML files (>100MB) cannot be pushed to GitHub. If full-book renders produce oversized files, commit only source `.qmd` files and let Netlify render from source.

## Automated Data Sync

**GitHub Actions workflow:** `.github/workflows/sync-unjournal-evaluations.yml`

**Purpose:** Automatically sync Unjournal evaluation markdown files from the [unjournaldata](https://github.com/unjournal/unjournaldata) repository.

**Schedule:** Weekly (Mondays at 6 AM UTC) or manual trigger

**What it does:**
1. Clones the unjournaldata repository
2. Runs the PubPub harvester to fetch latest evaluation exports
3. Syncs markdown files to `data/unjournal_evaluations/`
4. Commits and pushes changes if any new evaluations are found

This keeps the evaluation markdown corpus fresh for critique and metadata analyses.

## Visual Design and Theming

### Color Palette

The project uses a unified color scheme across all figures and themes:

- **UJ_GREEN**: `#2D9D5E` (light) / `#5AE08A` (dark) — primary Unjournal brand
- **UJ_ORANGE**: `#E8722A` (light) / `#F5A05C` (dark) — accent
- **UJ_BLUE**: `#2B7CE9` (light) / `#5DA3F5` (dark) — accent

Model-specific colors for multi-model figures:
```r
MODEL_COLORS <- c(
  "GPT-5 Pro" = "#2B7CE9", "GPT-5.2 Pro" = "#1B5EB8",
  "Claude Opus 4.6" = "#E8722A", "Claude Sonnet 4" = "#C45A1E",
  "Gemini 2.0 Flash" = "#7C3AED", "GPT-4o-mini" = "#64748B",
  "Human" = "#2D9D5E"
)
```

These are defined in `results.qmd`, `results_ratings.qmd`, and `results_critiques.qmd` (each file has its own copy). SCSS themes are in `theme-light.scss` and `theme-dark.scss`. PDF link colors are set in `preamble.tex` (all use `unjournalgreen`).

### Figure Standards

All R figures use `theme_uj()` (defined in each results file) with:
- `base_size = 12`, clean minimal theme
- Consistent axis text sizes (≥8pt), readable legends
- Descriptive captions that fully explain what the figure shows
- Green/orange color mapping: green = human higher, orange = LLM higher

### Writing Style

- **methods.qmd**: Nature/medical journal style — flowing paragraphs with bold inline headings (e.g., `**Sample and human reference data.**`), no `###` subsection headers, no bullet lists in prose. All statistical methods formally defined.
- **results.qmd**: Concise analytical prose with cross-references to appendix sections.
- **results_ratings.qmd / results_critiques.qmd**: Appendix style with brief analytical commentary per figure/table.

## Key Dependencies

**Python:** openai, anthropic, google-generativeai, pdfplumber, pandas, numpy, tiktoken, jupyter-cache
**R:** tidyverse ecosystem (ggplot2, dplyr, tidyr), ggforce, patchwork, ggrepel, irr (Krippendorff's alpha), scales, kableExtra, janitor, jsonlite, renv for package management
**Build:** Quarto (requires recent version with multi-engine support)

## Architecture Insights

- **Two-language architecture**: Python handles API calls and structured extraction; R handles statistical analysis and visualization. The bridge is primarily raw JSON responses plus derived tabular summaries.
- **Structured outputs**: The JSON Schema approach ensures every paper gets rated on identical metrics with enforced types and bounds, making comparisons clean.
- **Multi-provider evaluation**: Six models across three providers (OpenAI, Anthropic, Google) all receive identical prompts and schemas. Provider-specific API differences (file upload vs base64, sync vs background jobs) are abstracted in `methods.qmd`.
- **Rate limiting design**: The `TokenPacer` class proactively sleeps before calls based on token history, avoiding 429 errors rather than just reacting to them.
- **Credible intervals**: Both LLM and human evaluators provide 90% credible intervals (lower_bound, midpoint, upper_bound) to quantify uncertainty.
- **Ground truth**: Journal tier predictions have verifiable outcomes (where the paper actually publishes), enabling model calibration analysis.
