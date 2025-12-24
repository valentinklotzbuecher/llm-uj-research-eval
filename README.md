# LLM-based Research Evaluation Demo 📑🤖

This Quarto book uses LLMs to evaluate research papers based on The Unjournal metrics, and compares the results to human evaluations.

**Live site**: <https://llm-uj-research-eval.netlify.app>

**Repository**: [github.com/valentinklotzbuecher/llm-uj-research-eval](https://github.com/valentinklotzbuecher/llm-uj-research-eval)

## 📋 Quick Links

- **[DIRECTORY_STRUCTURE.md](DIRECTORY_STRUCTURE.md)** - Complete guide to repository organization
- **[DATA_PROVENANCE.md](DATA_PROVENANCE.md)** - Data lineage & LLM run tracking
- **[CLAUDE.md](CLAUDE.md)** - Development guide (detailed architecture notes)

## 🎯 What This Project Does

1. **Uploads research papers** (PDFs) to LLM APIs
2. **Generates structured evaluations** using The Unjournal's rating schema
3. **Compares LLM ratings** with human expert evaluations
4. **Analyzes patterns** to understand AI's research assessment capabilities

## 📂 Repository Structure

```
├── index.qmd, methods.qmd, results.qmd, etc.  # Main Quarto book chapters
├── data/           Production LLM evaluation results (gpt-4/gpt-5, 50 papers)
├── papers/         Research papers (PDFs) to evaluate
├── results/        Experimental runs & tracking metadata
├── prompts/        Modular prompt management system (components & versions)
├── side_projects/  Separate analysis pipelines (paper changes, citations)
└── key/            openai_key.txt (git-ignored, required for API calls)
```

**See [DIRECTORY_STRUCTURE.md](DIRECTORY_STRUCTURE.md) for complete directory guide.**

### Key Data Files

- **Production data** (used in book): `data/metrics_long.csv`, `data/tiers_long.csv`, `data/combined_long.csv`
  - Model: gpt-4 (baseline_sept_2024 run)
  - Papers: ~50 evaluated research papers
- **Comparison data**: `data/metrics_long_gpt-5.csv`, `data/combined_long_gpt-5.csv`, `data/tiers_long_gpt-5.csv`
  - Model: gpt-5 (gpt5_oct_2024 run)
  - Papers: ~50 evaluated research papers
- **Human evaluations**: `data/all_ratings.rds`, `data/all_jtiers.rds` (from Unjournal.org)
- **Run tracking**: `results/llm_runs_metadata.csv` (master registry of all LLM runs)
- **Unjournal evaluations**: `data/unjournal_evaluations/` (markdown files, synced weekly via GitHub Actions)

**See [DATA_PROVENANCE.md](DATA_PROVENANCE.md) for detailed data lineage.**

## 🚀 Development Setup

This project uses **both R and Python** in Quarto. Follow these steps:

### 1. Python Setup (via conda)

```bash
# Install Miniforge or Miniconda
# https://github.com/conda-forge/miniforge

# Create environment (first time)
conda env create -f environment.yml

# Or update existing environment
conda env update -n qpy311 -f environment.yml

# Activate environment
conda activate qpy311

# Tell Quarto which Python to use
export QUARTO_PYTHON="$(which python)"
```

### 2. R Setup (via renv)

```r
# In RStudio or R console
install.packages("renv")
renv::restore()  # Installs packages from renv.lock
```

### 3. API Keys

```bash
# Create key file (git-ignored)
echo "your-openai-api-key" > key/openai_key.txt
```

### 4. Build & Render

```bash
# Check setup
quarto check

# Render full site
quarto render

# Render single document
quarto render methods.qmd
```

### Optional: Persistent Python Path

Add to `~/.bashrc` or `~/.zshrc`:

```bash
export QUARTO_PYTHON="$(conda run -n qpy311 which python)"
```

---

## 📚 Documentation

- **[DIRECTORY_STRUCTURE.md](DIRECTORY_STRUCTURE.md)** - Repository organization guide
- **[DATA_PROVENANCE.md](DATA_PROVENANCE.md)** - Data lineage & tracking
- **[CLAUDE.md](CLAUDE.md)** - Architecture & development notes
- **[data/README.md](data/README.md)** - Production data documentation
- **[results/README.md](results/README.md)** - Experimental runs guide
- **[prompts/README.md](prompts/README.md)** - Prompt modularization system

---

## 🛠️ Key Tools

- **`track_llm_run.py`** - CLI for tracking evaluation runs
  ```bash
  python track_llm_run.py start --model gpt-5 --prompt-version v2
  python track_llm_run.py list
  ```

---

## 📊 Current Status

- **Model**: gpt-4 (baseline_sept_2024)
- **Papers evaluated**: ~50
- **Deployment**: Auto-deploy to Netlify on push to main

---

## 🤝 Contributing

This is collaborative research. See [CLAUDE.md](CLAUDE.md) for detailed architecture and development guidance.
