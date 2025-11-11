# Archive Metadata: Unused and Obsolete Files

**Archive Date**: November 11, 2025
**Purpose**: This directory contains files that are not actively used in the main LLM evaluation pipeline, but may be useful for reference or future work.

## Quick Summary

**Why archived**: These files were moved because they:
1. Are compiled outputs that can be regenerated
2. Are one-off scripts that have already been executed
3. Are side projects not integrated into main pipeline
4. Are superseded by newer versions or workflows
5. Are useful reference materials but not code dependencies

**Safety**: All files were verified to have NO active dependencies in:
- Quarto documents (*.qmd)
- R code (setup_params.R, *.R)
- Python pipeline (methods.qmd, config.py, evaluator.py, llm_utils.py)
- Documentation (CLAUDE.md, DATA_PROVENANCE.md, README.md)

## Inventory by Category

### Compiled Outputs (Regenerable)

#### `Comparing-LLM-and-human-reviews-of-social-science-research-using-data-from-Unjournal.org.tex`
- **Type**: LaTeX compiled output
- **Date**: November 4, 2025
- **Source**: Generated from Quarto render process
- **Why archived**: Compiled artifact, can be regenerated with `quarto render`
- **Dependencies**: None
- **Restore if**: Never - regenerate from source instead

#### `slidesvk.html`
- **Type**: Compiled presentation slides (HTML)
- **Date**: October 18, 2024
- **Source**: Generated from `slides_vk/index.qmd`
- **Size**: 4.5 MB
- **Why archived**: Large compiled artifact, regenerate with `quarto render slides_vk/index.qmd`
- **Dependencies**: None
- **Restore if**: Never - regenerate from source

#### `slidesvkgpt5.html`
- **Type**: Compiled presentation slides (HTML) - GPT-5 version
- **Date**: October 18, 2024
- **Source**: Variant of slides_vk/index.qmd
- **Size**: 8.1 MB
- **Why archived**: Large compiled artifact from experimental run
- **Dependencies**: None
- **Restore if**: Never - regenerate if needed

### Log Files and Test Results

#### `render_log.txt`
- **Type**: Quarto render log
- **Date**: November 4, 2025 08:35
- **Content**: Output from `quarto render 2>&1 | tee render_log.txt`
- **Why archived**: Temporary log file, gitignored anyway (*.log in .gitignore)
- **Dependencies**: None
- **Restore if**: Never - generates fresh on each render

#### `TRACKING_SYSTEM_TEST_RESULTS.md`
- **Type**: Test results document
- **Date**: November 4, 2025
- **Content**: Results from testing the run tracking system (track_llm_run.py)
- **Why archived**: Test results for a specific run, not documentation
- **Dependencies**: None
- **Future value**: Reference for understanding tracking system development
- **Restore if**: Documenting tracking system history

### One-Off Scripts (Already Executed)

#### `add_williams_to_data.py`
- **Type**: Python script
- **Date**: November 5, 2024
- **Purpose**: One-time script to add Williams et al. 2024 paper to production data
- **Status**: Already executed - Williams data now in data/metrics_long.csv
- **Why archived**: Task completed, no longer needed
- **Dependencies**: None (referenced nowhere in active code)
- **Code**:
  ```python
  # Added Williams 2024 data to:
  # - data/metrics_long.csv
  # - data/tiers_long.csv
  # - data/combined_long.csv
  ```
- **Restore if**: Need to understand how data was manually added
- **Future alternative**: Use proper pipeline (methods.qmd) instead

#### `batch_eval.py`
- **Type**: Python script (legacy)
- **Date**: October 18, 2024
- **Purpose**: Old batch evaluation script
- **Status**: Superseded by methods.qmd pipeline
- **Why archived**: Replaced by integrated Quarto + Python pipeline
- **Dependencies**: None (only self-reference in docstring)
- **Restore if**: Need to understand old evaluation workflow
- **Modern equivalent**: Use methods.qmd with track_llm_run.py

### Example/Test Files

#### `example_prompt.txt`
- **Type**: Text file
- **Purpose**: Example or test prompt (content not verified)
- **Why archived**: Not referenced anywhere, appears to be development artifact
- **Dependencies**: None
- **Restore if**: Contains useful prompt templates

### Standalone Scripts (Not Integrated)

#### `tier_correlations_plot.R`
- **Type**: R script
- **Purpose**: Standalone script for plotting tier correlations
- **Status**: Functionality integrated into results.qmd
- **Why archived**: Not sourced by any Quarto document
- **Dependencies**: None
- **Restore if**: Need standalone plotting script (but results.qmd is better)

## Archived Directories

### `openalex_work_finding_citers/`
- **Type**: Side project directory
- **Purpose**: Scripts for finding paper citations using OpenAlex API
- **Status**: Not integrated into main pipeline
- **Why archived**: Separate analysis not part of LLM evaluation or paper response tracking
- **Contents**:
  - `oa_env/` - Separate conda environment
  - `open_alex_scripts_seeds/` - Scripts (7 files)
  - `openalex_results/` - Results (11 files)
- **Dependencies**: None in main project
- **Future value**: If doing citation network analysis
- **Restore if**: Building citation analysis feature

### `UJ_ratings/`
- **Type**: Old data directory
- **Purpose**: Earlier versions of Unjournal ratings data
- **Status**: Superseded by data/ directory
- **Why archived**: data/ contains more complete and up-to-date ratings
- **Contents**:
  - `rsx_evalr_rating (6).csv`
  - `rsx_evalr_rating (7).csv`
  - `UJ_map.csv` (also in data/)
  - `UJ_map.xlsx` (also in data/)
- **Dependencies**: None (not referenced in any code)
- **Data comparison**: data/ has all_ratings.csv, all_jtiers.csv which are newer
- **Restore if**: Need historical versions for comparison

### `docs/`
- **Type**: Documentation directory
- **Purpose**: Analysis documentation comparing slides vs results improvements
- **Status**: Useful reference but not part of active code
- **Why archived**: Documentation artifacts, not code dependencies
- **Contents**:
  - `ANALYSIS_README.md` - Guide to the analysis
  - `FINAL_SUMMARY.txt` - Executive summary of improvements
  - `comparison_summary.md` - Detailed comparison
  - `PAPER_RESPONSE_ANALYSIS_README.md` - Paper response analysis notes
  - `PYTHON_MODULES_README.md` - Python modules documentation
  - `code_snippets_ready_to_use.md` - Code snippets
  - `collaboration_tips_readme.md` - Collaboration tips
- **Dependencies**: None (pure documentation)
- **Future value**: Understanding how slides_vk/index.qmd improvements evolved
- **Restore if**: Documenting project history or replicating analysis improvements
- **Note**: The improvements described here are already implemented in slides_vk/

### `Literature_review/`
- **Type**: Reference materials directory
- **Purpose**: Academic papers about LLM evaluation and peer review
- **Status**: Useful references but not code dependencies
- **Why archived**: External research papers, not part of pipeline
- **Contents**: 10 PDF files:
  - Dycke et al 2023 - NLP for peer review
  - Eger et al. 2025 - LLMs for science
  - Guo et al 2023 - Substantiation analysis
  - Kuznetsov et al 2024 - NLP for peer review
  - Liu and Sha 2023 - ReviewerGPT
  - Luo et al. 2025 - LLMs for scientific research
  - Okasa et al 2024 - ML for grant peer review
  - Son et al 2025 - Automated verification
  - Zhang and Abernethy 2025 - Reasoning LLMs
  - Zhang et al - Pairwise comparison
  - econ_prad_thing_recent_2502.00070v2.pdf
- **Dependencies**: None (cited in writing but not in code)
- **Future value**: Background reading, related work section
- **Restore if**: Writing literature review or comparing approaches
- **Alternative**: These PDFs could be stored externally (Zotero, Mendeley, etc.)

## Files Already in Archive (Pre-existing)

These files were already in `archive_to_revisit/` before this cleanup:

- `compare_ratings.qmd` - Old rating comparison document
- `discussion-CONFLICT-1.qmd` - Merge conflict version
- `methods-CONFLICT-1.qmd` - Merge conflict version
- `numerical_ratings.ipynb` - Jupyter notebook version
- `numerical_ratings.qmd` - Old numerical ratings analysis
- `numerical_ratings_files/` - Supporting files
- `system_prompts.py` - Old system prompts (historical reference)
- `README.md` - Archive documentation (pre-existing)

## Narrative: Why These Files Were Archived

### The Evolution of the Project

This LLM evaluation project has gone through several phases:

1. **Early development (Sept-Oct 2024)**: Standalone Python scripts (batch_eval.py), separate data folders (UJ_ratings/), experimental prompts
2. **Integration phase (Oct 2024)**: Moving to Quarto-integrated pipeline, consolidating data into data/ directory
3. **Maturation (Nov 2024)**: Metadata tracking system (track_llm_run.py), standardized output structure, documentation cleanup

### What This Archive Represents

**One-off scripts**: Scripts like `add_williams_to_data.py` and `batch_eval.py` represent the transitional period before the current pipeline was established. They were necessary at the time but are now superseded by more systematic approaches.

**Side projects**: `openalex_work_finding_citers/` represents exploratory work that didn't integrate into the main pipeline. It may be valuable future work but isn't currently used.

**Documentation artifacts**: The `docs/` folder contains excellent analysis of how the presentation evolved to be better than the main results document. This analysis informed improvements but is now historical - the improvements are already implemented.

**Reference materials**: `Literature_review/` PDFs are valuable background reading but aren't code dependencies. They're better managed in a reference manager than in the git repository.

**Data transitions**: `UJ_ratings/` represents an earlier data organization that was superseded by the current `data/` structure.

### What Remains Active

The core pipeline now consists of:
- **Main analysis**: index.qmd, methods.qmd, results.qmd, questions_answers.qmd, discussion.qmd, references.qmd
- **Appendix**: paper_response_analysis.qmd (separate "do authors adjust" analysis)
- **Python modules**: config.py, evaluator.py, llm_utils.py, track_llm_run.py, check_job_status.py
- **Data sources**:
  - `data/` - Production LLM evaluation data
  - `results/` - Experimental runs and timestamped evaluations
  - `papers/`, `more papers/` - Input research papers
  - `latest_papers_post_UJ/` - Updated paper versions for response analysis
  - `unjournal_evaluations/` - Evaluation markdown files for response analysis
  - `paper_abstracts_meta_data/` - For future placebo test
- **Analysis code**: paper_change_analysis/ - Active analysis for appendix
- **Utilities**: quick_helper_scripts_for_downloads_etc/ - Download automation

## Cross-Reference with Planned Work

Checked against:
- **CLAUDE.md**: Documents active directories and workflow - none of the archived items are mentioned as active
- **DATA_PROVENANCE.md**: User DR added notes about input folders (papers/, more papers/, latest_papers_post_UJ/, unjournal_evaluations/, paper_abstracts_meta_data/) - all confirmed NOT archived
- **paper_response_analysis.qmd**: Uses latest_papers_post_UJ/ and unjournal_evaluations/ - both NOT archived
- **README.md**: Points to DATA_PROVENANCE.md for data understanding - no references to archived items

## Restoration Guide

### If you need to restore files:

```bash
# Restore specific file
cp archive_to_revisit/filename ./

# Restore directory
cp -r archive_to_revisit/dirname ./

# View archive contents
ls -la archive_to_revisit/
```

### When NOT to restore:

- **Compiled outputs** (.tex, .html): Just regenerate with `quarto render`
- **Logs** (render_log.txt): Will be regenerated on next render
- **One-off scripts**: Better to use current pipeline

### When TO restore:

- **Historical context**: Understanding how workflow evolved
- **Data archaeology**: Comparing old vs new data structures
- **Side project revival**: If building citation analysis feature (openalex_work_finding_citers/)
- **Reference materials**: If writing literature review (Literature_review/)

## Maintenance

This archive should be:
- **Kept in git**: These files have historical value
- **Not actively maintained**: Files here are frozen in time
- **Documented**: This metadata file explains everything
- **Rarely restored**: Most needs should use current pipeline instead

## Verification

Files were verified safe to archive by:
1. ✅ Checking ALL .qmd files for references (grep -r)
2. ✅ Checking ALL .py files for imports/usage
3. ✅ Checking ALL .R files for source() calls
4. ✅ Reviewing CLAUDE.md for planned work mentions
5. ✅ Reviewing DATA_PROVENANCE.md for data provenance
6. ✅ Confirming data/ folder has newer versions of UJ_ratings/ content
7. ✅ Verifying docs/ analysis is already implemented in slides_vk/

**Result**: NO active dependencies found for any archived item.
