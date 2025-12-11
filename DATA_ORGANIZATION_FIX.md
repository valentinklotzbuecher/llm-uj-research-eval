# Data Organization Fix

**Date**: December 10, 2025

## Issue Identified

The GPT-5 comparison data files were incorrectly placed in `data/archive/` when they are **actively used** in the main analysis for model comparison (results.qmd Section "Model comparison: GPT-5 vs GPT-5 Pro").

## Root Cause

During the repository cleanup, GPT-5 data files were moved to `data/archive/` along with truly archived files (old superseded versions). However, the GPT-5 data is not archived - it's comparison data that's part of the published analysis.

## Solution

### Files Moved Back to `data/`
Moved the following files from `data/archive/` to `data/`:
- `metrics_long_gpt-5.csv` (128K) - **Actively used** for model comparison
- `combined_long_gpt-5.csv` (167K) - All GPT-5 metrics combined
- `tiers_long_gpt-5.csv` (31K) - GPT-5 tier predictions

### Files Remaining in `data/archive/`
Only truly archived/superseded files remain:
- `metrics_long_old.csv` (78K)
- `metrics_long_old (2).csv` (94K)
- `metrics_meta_old.csv` (22K)
- `metrics_meta old.csv` (27K)

## Code Updates

### results.qmd (line 1609)
- **Before**: `read_csv(here("data", "archive", "metrics_long_gpt-5.csv"), ...)`
- **After**: `read_csv(here("data", "metrics_long_gpt-5.csv"), ...)`
- Comment updated: "Load GPT-5 metrics (comparison model)"

### slides_vk/index.qmd (line 520)
- **Before**: `readr::read_csv(here("data","archive","metrics_long_gpt-5.csv"), ...)`
- **After**: `readr::read_csv(here("data","metrics_long_gpt-5.csv"), ...)`
- Comment updated: "LLM (GPT‑5 comparison)"

### slides_vk/index.qmd (line 1743)
- **Before**: `readr::read_csv(here("data","archive","metrics_long_gpt-5.csv"), ...)`
- **After**: `readr::read_csv(here("data","metrics_long_gpt-5.csv"), ...)`

### PROMPT_VERSIONS.md (line 13)
- **Before**: `[data/archive/metrics_long_gpt-5.csv](data/archive/metrics_long_gpt-5.csv)`
- **After**: `[data/metrics_long_gpt-5.csv](data/metrics_long_gpt-5.csv)`
- Notes updated: "Outputs in data/*_gpt-5.csv"

## Documentation Updates

### data/archive/README.md
Completely rewritten to clarify:
- Archive contains only superseded old versions
- GPT-5 comparison files are **NOT** archived - they're in parent `data/` directory
- Added note explaining GPT-5 files are actively used in results.qmd

## Correct Data Organization

```
data/
├── # Primary production data (GPT-5 Pro)
├── metrics_long.csv           # Current model (50 papers)
├── combined_long.csv           # All metrics
├── tiers_long.csv              # Tier predictions
│
├── # Model comparison data (GPT-5)
├── metrics_long_gpt-5.csv      # GPT-5 ratings (40 papers) - ACTIVE
├── combined_long_gpt-5.csv     # All GPT-5 metrics - ACTIVE
├── tiers_long_gpt-5.csv        # GPT-5 tiers - ACTIVE
│
├── # Other production data
├── rsx_evalr_rating.csv        # Human evaluator ratings
├── research.csv                # Research metadata
├── metrics_meta.csv            # Metric definitions
├── jql-enriched.csv            # Journal quality data
├── ...
│
└── archive/
    ├── metrics_long_old.csv        # Superseded (Oct 8)
    ├── metrics_long_old (2).csv    # Superseded (Oct 10)
    ├── metrics_meta_old.csv        # Superseded
    └── metrics_meta old.csv        # Superseded
```

## Rationale: Why GPT-5 Files Are NOT Archived

1. **Actively Used**: Referenced in results.qmd for model comparison analysis
2. **Published Analysis**: Part of the main research findings comparing model performance
3. **Key Results**: Section "Model comparison: GPT-5 vs GPT-5 Pro" depends on this data
4. **Presentation**: Used in slides (slides_vk/index.qmd) for communicating findings
5. **Documentation**: Tracked in PROMPT_VERSIONS.md as active comparison run

## Verification

### All Files in Correct Locations
```bash
✓ data/metrics_long_gpt-5.csv exists (128K)
✓ data/combined_long_gpt-5.csv exists (167K)
✓ data/tiers_long_gpt-5.csv exists (31K)
✓ data/archive/ contains only truly archived files
```

### Code References Work
```bash
✓ results.qmd renders successfully
✓ No broken file references
✓ Full book render works
```

### Documentation Updated
```bash
✓ PROMPT_VERSIONS.md corrected
✓ data/archive/README.md clarified
✓ DATA_ORGANIZATION_FIX.md created
```

## Key Principle

**Archive Criteria**: Files should only be in `archive/` if they are:
1. Superseded by newer versions, AND
2. Not referenced in any active analysis code

**Comparison/Secondary Data**: Files that are used for comparison or supplementary analysis (even if from an earlier run) should remain in the main data directory.

## Testing

```bash
# Verify rendering works
quarto render results.qmd
# Output: Success - _book/results.html created

# Check file locations
ls data/*gpt-5.csv
# Output: All three GPT-5 files in data/

ls data/archive/
# Output: Only old/superseded files

# Test imports
grep -n "metrics_long_gpt-5" results.qmd slides_vk/index.qmd
# Output: All point to data/metrics_long_gpt-5.csv (not archive)
```

## Summary

**Before (Incorrect)**:
- GPT-5 comparison files in `data/archive/`
- Implied they were experimental/unused
- Confusing organization

**After (Correct)**:
- GPT-5 comparison files in `data/`
- Clear they're active comparison data
- Logical organization: active vs superseded

This fix ensures the data organization reflects actual usage in the analysis.
