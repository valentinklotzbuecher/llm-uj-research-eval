# LLM-based Research Evaluation Demo

This Quarto book studies how well frontier LLMs evaluate social-science research compared with structured expert reviews from The Unjournal.

**Live site**: <https://llm-uj-research-eval.netlify.app>  
**Repository**: <https://github.com/valentinklotzbuecher/llm-uj-research-eval>

## Quick Links

- [CLAUDE.md](CLAUDE.md): Architecture and developer notes
- [DIRECTORY_STRUCTURE.md](DIRECTORY_STRUCTURE.md): Repository layout
- [DATA_PROVENANCE.md](DATA_PROVENANCE.md): Data lineage and run provenance
- [results/README.md](results/README.md): Run tracking and output conventions
- [data/README.md](data/README.md): Human-reference and archival data notes
- [September 2026 project review](docs/project_review_2026-09-07.md): Findings, corrections, and research priorities

## What This Project Does

1. Evaluates research PDFs with structured LLM prompts/schemas.
2. Extracts standardized ratings and uncertainty intervals from model outputs.
3. Compares LLM ratings and critiques against human expert evaluations.
4. Reports quantitative and qualitative agreement patterns in a Quarto working paper.

## Repository Structure (Current)

```text
├── index.qmd, results.qmd, discussion.qmd, methods.qmd  # Main paper chapters
├── results/        Primary model outputs (per-model JSONs) + run registry
├── data/           Human reference data + legacy/archival aggregate CSVs
├── papers/         Input PDFs for evaluation runs
├── prompts/        Modular prompt components and versions
├── tools/          Issue-comparison and annotation utilities
└── key/            API key files (git-ignored)
```

## Current Analysis Inputs

- **Human reference data**: `data/rsx_evalr_rating.csv`, `data/research.csv`, `data/UJ_map.csv` (plus `.rds` snapshots).
- **Model outputs**: per-model response JSONs in `results/<run_or_model_dir>/json/`.
- **Run metadata**: `results/llm_runs_metadata.csv`.

Note: historical aggregate files in `data/` are kept for provenance and back-compat, but the main `results.qmd` workflow currently parses model JSON outputs from `results/`.

## Development Setup

This project uses both R and Python in Quarto.

### Python

`_quarto.yml` currently points to `.venv/bin/python`. You can either:

1. Create a local virtual environment (the `.venv` directory is git-ignored), or
2. Use conda and override Quarto's Python:

```bash
conda env create -f environment.yml      # first time
conda env update -n qpy311 -f environment.yml
conda activate qpy311
export QUARTO_PYTHON="$(which python)"
```

### R

```r
install.packages("renv")
renv::restore()
```

### API Key

```bash
echo "your-openai-api-key" > key/openai_key.txt
```

## Build

```bash
quarto check
quarto render
quarto render results.qmd
```

## Key Tool

Run tracking helper:

```bash
python track_llm_run.py start --model gpt-5-pro --prompt-version v1 --description "..."
python track_llm_run.py list
```

## Offline verification

Run these from the repository root with the project Python and R dependencies installed:

```bash
python -m unittest discover -s tests
Rscript tests/test_analysis_checks.R
```

These checks make no model calls. Rendering the Results chapters reads stored
responses; the model-generation chunks in `methods.qmd` have `eval: false`.
The checked-in GitHub Pages workflow deploys `_book/` without rendering it, so
source edits need an explicit render before a publication update.

## Current analysis (reviewed September 2026)

- **One maintained source:** `working-paper` holds the manuscript, analysis, tools, and documentation. Other editions and branches are historical snapshots or temporary work; see [the branch policy](WORKING_PAPER_STRATEGY.md).
- Active branch: `working-paper`
- Main manuscript: one-shot, structured LLM-vs-human evaluation working paper
- Included models in current results pipeline: GPT-5 Pro, GPT-5.2 Pro, GPT-4o-mini, Claude Sonnet 4, Claude Opus 4.6, Gemini 2.0 Flash
- Main comparison: 47 human-matched GPT-5 Pro papers, 39 with at least two evaluators. Critique analysis: 12 eligible GPT-5.2 Pro pairings after two documented identity exclusions.
- Human agreement is a noisy reference; the present analysis does not establish equivalence to another expert evaluator. Model-specific sample availability limits comparisons across models.
