# Repository Directory Structure

**Live site**: https://llm-uj-research-eval.netlify.app

This repository uses LLMs to evaluate research papers and compares results with human evaluations from The Unjournal. See [README.md](README.md) for setup instructions.

---

## 📂 Core Structure (What You Need to Know)

### Main Content (Quarto Book)
```
├── index.qmd                    # Introduction & motivation
├── methods.qmd                  # LLM evaluation pipeline (Python)
├── results.qmd                  # Analysis & visualizations (R)
├── questions_answers.qmd        # Q&A section
├── discussion.qmd               # Discussion & implications
├── references.qmd               # Bibliography
├── paper_response_analysis.qmd  # Appendix: Author response tracking
└── _quarto.yml                  # Book configuration
```

### Data & Papers

DR: `data` folder is output that was manually copied into the data folder; both moved from `results` -- LLM runs, as well as the human evaluations -- also pasted in and manually coded

`paper` is also manually added -- note we have interim systems for automation that we can bring in

`results` is the output of the LLM calls

```
├── data/                        # Production data used in book
│   ├── metrics_long.csv         # LLM ratings (baseline_sept_2024, gpt-4, 50 papers)
│   ├── combined_long.csv        # All metrics combined (gpt-4)
│   ├── tiers_long.csv           # Journal tier predictions (gpt-4)
│   ├── metrics_long_gpt-5.csv   # GPT-5 comparison run
│   ├── combined_long_gpt-5.csv  # GPT-5 all metrics
│   ├── tiers_long_gpt-5.csv     # GPT-5 tier predictions
│   ├── all_ratings.rds          # Human evaluations from Unjournal
│   ├── all_jtiers.rds           # Human journal tier predictions
│   ├── unjournal_evaluations/   # Markdown exports (synced weekly via GitHub Actions)
│   └── README.md                # Full data documentation
│
├── papers/                      # Research papers to evaluate (PDFs)
│   └── [3 PDF files currently]
│
└── results/                     # Experimental LLM runs
    ├── llm_runs_metadata.csv    # Master tracking file
    ├── jobs_index.csv           # Active job tracking
    ├── [timestamped runs]/      # Individual evaluation runs
    └── README.md                # Run tracking documentation
```

### Prompt Management
```
└── prompts/                     # Modular prompt system (NEW)
    ├── components/              # Reusable prompt components
    │   ├── base_guidelines.txt
    │   ├── calibration_instructions.txt
    │   ├── schema_instructions.txt
    │   └── metric_definitions.txt
    ├── versions/                # Versioned complete prompts
    │   ├── v1_baseline_sept2024.py
    │   ├── v2_ignore_authors.py
    │   ├── v3_assessment_first.py
    │   └── v4_assessment_expanded.py
    ├── builder.py               # Prompt composition utilities
    └── README.md                # Full documentation
```

### Side Projects & Analysis Pipelines
```
└── side_projects/
    ├── paper_change_analysis/   # Tracks if authors updated papers post-evaluation
    │   ├── scripts/
    │   │   ├── analyze_paper_changes.py
    │   │   └── llm_change_attribution.py
    │   └── README.md
    └── openalex_work_finding_citers/  # Citation network analysis
        └── open_alex_scripts_seeds/
```

### Organization & Reference
```
├── archive/                     # Archived files and old code
│   ├── archive_to_revisit/      # Unused code preserved for reference
│   │   ├── unused_python_modules/
│   │   ├── ARCHIVE_METADATA.md
│   │   └── PYTHON_SCRIPTS_AUDIT.md
│   ├── *.tex                    # Compiled LaTeX outputs
│   ├── example_prompt.txt       # Test/example prompts
│   └── render_log.txt           # Old build logs
│
└── reference_materials/         # Background reading
    ├── Literature_review/       # Academic papers on LLM peer review
    └── docs/                    # Historical documentation
```

### Automation
```
└── .github/
    └── workflows/
        └── sync-unjournal-evaluations.yml  # Weekly sync of Unjournal evaluations
```

---

## 🗂️ Supporting Files & Directories

### Configuration
- `environment.yml` - Python dependencies (conda)
- `renv.lock` - R dependencies
- `netlify.toml` - Deployment settings
- `references.bib`, `grateful-refs.bib` - Citations

### Build Outputs & Caches (gitignored)
```
├── _book/                       # Rendered HTML output
├── _freeze/                     # Quarto execution cache
└── __pycache__/                 # Python bytecode (auto-generated)
```

**Note**: Per-document cache directories (`*_cache/`) have been removed. Quarto will regenerate them as needed during builds.

### Tools & Utilities
- `track_llm_run.py` - CLI for tracking evaluation runs
- `TRACKING_SYSTEM_TEST_RESULTS.md` - Test results for tracking system

### Documentation
- `README.md` - Quick start & setup
- `CLAUDE.md` - Instructions for Claude Code (development assistant)
- `DIRECTORY_STRUCTURE.md` - This file (repository organization)
- `DATA_PROVENANCE.md` - Data lineage & versions
- `PROMPT_VERSIONS.md` - Prompt version tracking & characteristics
- `CACHE_README.md` - Explanation of cache directories
- `TRACKING_SYSTEM_TEST_RESULTS.md` - Test results for LLM run tracking

---

## ✅ Recent Cleanup (Completed)

The following items have been addressed:

1. **✅ Cache directories removed** - All `*_cache/` directories deleted (Quarto regenerates as needed)
2. **✅ Archives consolidated** - `archive_to_revisit/` moved into `archive/`
3. **✅ Loose files archived** - `example_prompt.txt`, `render_log.txt`, `.tex` files moved to `archive/`
4. **✅ Root directory cleaned** - Reduced from 56 to 40 items

---

## 🤷 Remaining Items to Clarify

### Multiple Paper Directories
- **papers/** (50+ PDFs) - Main papers being evaluated ✅
- **more_papers/** (50+ PDFs) - Additional papers, unclear if actively used
- **latest_papers_post_UJ/** - Papers after Unjournal evaluation (for paper_change_analysis)

*Suggestion: Document purpose of more_papers/ or consolidate with papers/*

### Data Directories
- **data/** - ✅ Active production data
- **UJ_ratings/** - Old ratings data (may be superseded by data/)
- **paper_abstracts_meta_data/** - Paper metadata (purpose unclear)

*Suggestion: Clarify if UJ_ratings/ and paper_abstracts_meta_data/ are still needed*

### Presentation Files
- **slides_vk/** - Separate Quarto presentation directory
- **slidesvk.html**, **slidesvkgpt5.html** - Compiled presentation outputs (4-8 MB each)

*Purpose: Conference/talk slides. Consider: document purpose or move compiled outputs to archive*

---

## 📊 Quick Stats

- **40 items** in root directory (down from 56)
- **~50 research papers** in papers/
- **7 Quarto documents** (.qmd files)
- **3 main data locations** (data/, results/, papers/)
- **Cleaned up**: Cache directories removed, archives consolidated

---

## 🎯 Next Cleanup Opportunities

If further cleanup is desired:

1. **Clarify paper directories**
   - Document purpose of `more_papers/` (is it actively used?)
   - Consider consolidating with `papers/` if redundant

2. **Review old data directories**
   - Check if `UJ_ratings/` is still needed (may be superseded by `data/`)
   - Clarify purpose of `paper_abstracts_meta_data/`

3. **Presentation files**
   - Add `slides_vk/README.md` explaining its purpose
   - Consider moving large compiled HTML files (`slidesvk*.html`) to archive or .gitignore

4. **Update .gitignore**
   - Add `*.tex` (LaTeX outputs, regenerable)
   - Add `*_cache/` (already removed, but prevent re-addition)

---

## 📖 For More Details

- **Data documentation**: [data/README.md](data/README.md)
- **Results tracking**: [results/README.md](results/README.md)
- **Prompt system**: [prompts/README.md](prompts/README.md)
- **Archive inventory**: [archive/archive_to_revisit/ARCHIVE_METADATA.md](archive/archive_to_revisit/ARCHIVE_METADATA.md)
- **Paper response analysis**: [side_projects/paper_change_analysis/README.md](side_projects/paper_change_analysis/README.md)
- **Data provenance**: [DATA_PROVENANCE.md](DATA_PROVENANCE.md)
- **Prompt versions**: [PROMPT_VERSIONS.md](PROMPT_VERSIONS.md)
- **Setup & development**: [README.md](README.md) and [CLAUDE.md](CLAUDE.md)
