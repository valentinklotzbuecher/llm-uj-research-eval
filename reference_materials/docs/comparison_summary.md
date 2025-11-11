# Comprehensive Comparison: slides_vk/index.qmd vs results.qmd

## Summary
The presentation file (slides_vk/index.qmd) contains numerous improvements, new visualizations, better data processing utilities, and more sophisticated statistical analyses compared to the main results.qmd. This document outlines all key improvements that should be incorporated back into the main book.

---

## 1. NEW VISUALIZATIONS & PLOT IMPROVEMENTS

### 1.1 Vertical Forest Plot with Annotation (forest-overall-vert-annotate)
**Location in slides:** Lines 951-1029
**Status in results.qmd:** Not present

**Improvements:**
- Cleaner vertical presentation with papers ordered by human mean rating (descending)
- Both mean reference lines (human green dotted, LLM orange dotted) for easy comparison
- Paper position on x-axis, rating on y-axis (rotated from horizontal format)
- `geom_label_repel()` for highlighting specific papers with automatic label placement
- Includes both human individual points (offset) and LLM summary with error bars
- Better visual hierarchy with larger figure (14x6) optimized for presentations

**Key Code Elements:**
```r
# Cleaner lane offset functions
lane_offsets_center <- function(m, gap = 0.18) {
  if (m <= 0) return(numeric(0))
  if (m == 1) return(0)
  k <- floor((m - 1)/2)
  offs <- sort(c(-seq_len(k), 0, seq_len(k))) * gap
  offs[seq_len(m)]
}
```

### 1.2 Human Evaluator Profile Plot (profile_humans_fixed)
**Location in slides:** Lines 549-610
**Status in results.qmd:** Not present

**Purpose:** Shows rating profiles across metrics for selected papers
**Features:**
- Displays 8 metrics: overall, adv_knowledge, logic_comms, methods, open_sci, gp_relevance, merits_journal, journal_predict
- Metrics scaled on 0-100 scale (journal tiers converted: 1-5 scale × 20 = 0-100)
- Connected path visualization showing profile shape
- Three selected papers (Banerjee et al. 2022, Bettle 2023, Williams et al. 2024)
- Clean dual y-axis (percentile rank and journal tier equivalents)

**Code Quality:** Uses metric labels for cleaner presentation and carefully calculated metric ordering

### 1.3 Scatter Plot with Statistics (scatter-overall-static-stats)
**Location in slides:** Lines 1091-1126
**Status in results.qmd:** Has basic version but lacks statistics display

**Improvements:**
- Adds visual regression line: `stat_smooth(method="lm", se=FALSE)`
- Diagonal reference line for perfect agreement
- Pearson r, Spearman rho, Krippendorff's α, and MAE statistics displayed
- Statistics calculated inline and shown in right-side column
- Proper use of `coord_equal()` for true 45-degree angle reference line

**Code:**
```r
r    <- suppressWarnings(cor(D$Human, D$LLM, method="pearson"))
rho  <- suppressWarnings(cor(D$Human, D$LLM, method="spearman"))
MAE  <- mean(abs(D$LLM - D$Human))
alpha_overall <- tryCatch({
  if (requireNamespace("irr", quietly = TRUE)) {
    M <- rbind(D$Human, D$LLM); irr::kripp.alpha(M, method = "interval")$value
  } else NA_real_
}, error = function(e) NA_real_)
```

### 1.4 Tier Correlations Dumbbell Plot (tier-correlations-comparison)
**Location in slides:** Lines 1454-1567
**Status in results.qmd:** Commented out (lines 458-571)

**Why It's Better:**
- More sophisticated correlation analysis comparing how LLM vs Human weight different metrics when predicting journal tiers
- Metric-specific correlations with "where should publish?" ratings
- Visual comparison with connecting segments between human (green) and LLM (orange) dots
- Ranked by average correlation across both evaluator types
- Reveals systematic differences in evaluation priorities

**Code Structure:**
```r
metrics_to_cor <- c("overall", "claims", "methods", "adv_knowledge",
                    "logic_comms", "open_sci", "gp_relevance")
# Separate LLM and Human correlations computed
# Then combined in dumbbell plot with segments
```

### 1.5 Human-minus-LLM Heatmap (heatmap-human-minus-llm)
**Location in slides:** Lines 1585-1632
**Status in results.qmd:** Similar basic version exists (fig-heat around line 954)

**Improvements:**
- Color scale inverted: Green = Human higher, Orange = LLM higher (more intuitive)
- Papers ordered by overall difference (descending) for better narrative flow
- Metric labels are friendlier (abbreviated) in heatmap
- Better coordinate system with proper angle for x-axis labels

---

## 2. STATISTICAL ANALYSES & AGREEMENT METRICS

### 2.1 Krippendorff's Alpha Implementation
**Location in slides:** Lines 1302-1434 (agreement-helpers chunk)
**Status in results.qmd:** Has weighted_kappa but NOT Krippendorff's alpha

**NEW in slides:**
- `irr::kripp.alpha()` function from irr package for interval-scale data
- Treats data as continuous interval measurements (appropriate for percentile ratings)
- Computes both LLM-Human agreement (α_LH) and Human-Human agreement (α_HH)
- Better interpretability: "fair agreement" vs Cohen's κ thresholds

**Implementation:**
```r
α_LH = tryCatch(irr::kripp.alpha(M, method="interval")$value, error=function(e) NA_real_)
```

**Why Better:**
- Krippendorff's alpha is preferred for:
  - Multiple raters (works with any number)
  - Continuous/interval scales
  - Handles missing data naturally
  - Suitable for research evaluation tasks

### 2.2 Comprehensive Agreement Table (combined-alpha-interval-metrics)
**Location in slides:** Lines 1388-1434
**Status in results.qmd:** Has tbl-agreement but simpler version (lines 1001-1032)

**Slides Version Shows:**
```
- n (sample size per criterion)
- Pearson r (linear correlation)
- Spearman rho (rank correlation)
- MAE (mean absolute error in points)
- α_LH (Krippendorff's alpha for LLM vs Human)
- α_HH (Krippendorff's alpha for Human vs Human comparison)
```

**Code Approach:**
```r
llm_h_stats <- metrics_use %>%
  group_by(criteria) %>%
  group_modify(function(df, key){ ... compute stats ... })

hh_alpha_metrics <- metrics_human %>%
  group_by(criteria) %>%
  group_modify(function(df, key){ ... compute human-human agreement ... })

combined_metrics <- llm_h_stats %>%
  left_join(hh_alpha_metrics, by="criteria")
```

**Benefit:** Directly compares LLM-Human agreement to Human-Human agreement, providing context for interpretation

### 2.3 Better Statistical Presentation in Tables
**Location in slides:** Lines 1201-1276 (tab-basic-metrics-matched)
**Status in results.qmd:** Not present in this form

**Features:**
- Uses `kableExtra::kbl()` and `kable_styling()` for better formatting
- Multi-line headers with HTML line breaks for readability
- Bootstrap options ("striped", "hover") for better presentation
- Larger font size (22pt) for clarity
- Proper alignment and spacing

**Code:**
```r
summ_basic_matched %>%
  kbl(escape = FALSE, align = "lcccccccc", booktabs = TRUE) %>%
  kable_styling(full_width = FALSE, position = "center",
                bootstrap_options = c("striped", "hover"),
                font_size = 22) %>%
  row_spec(0, extra_css = "line-height:0.9; font-size:24px; font-weight:bold;")
```

---

## 3. DATA PROCESSING & UTILITY FUNCTIONS

### 3.1 Metric Canonicalization Function (canon_metric)
**Location in slides:** Lines 408-416
**Status in results.qmd:** Not present as standalone function

**Purpose:** Standardizes metric names across different data sources
```r
canon_metric <- function(x) dplyr::recode(
  x,
  "advancing_knowledge" = "adv_knowledge",
  "open_science"        = "open_sci",
  "logic_communication" = "logic_comms",
  "global_relevance"    = "gp_relevance",
  "claims_evidence"     = "claims",
  .default = x
)
```

**Benefits:**
- DRY principle: Single source of truth for metric naming
- Used consistently across metrics_human and metrics_llm loading
- Makes refactoring easier if naming conventions change

### 3.2 Better Lane Offset Functions
**Location in slides:** Lines 370-383
**Status in results.qmd:** Older lane_offsets function (line 607)

**Improvements:**
- Two variants: `lane_offsets_center()` includes center lane (for LLM), `lane_offsets_skip0()` skips it
- More explicit logic for calculating symmetric offsets
- Better parameter defaults and cleaner implementation

**Slides version:**
```r
lane_offsets_center <- function(m, gap = 0.18) {
  if (m <= 0) return(numeric(0))
  if (m == 1) return(0)  # Special case: single item in center
  k <- floor((m - 1)/2)
  offs <- sort(c(-seq_len(k), 0, seq_len(k))) * gap
  offs[seq_len(m)]
}
```

**Results.qmd version (less clear):**
```r
lane_offsets <- function(m, gap = 0.18) {
  if (m <= 0) return(numeric(0))
  k <- ceiling(m/2)
  cand <- c(-seq_len(k), seq_len(k)) * gap
  sort(cand)[seq_len(m)]
}
```

### 3.3 Multi-LLM Data Loading
**Location in slides:** Lines 495-544
**Status in results.qmd:** Not present

**Purpose:** Supports comparing multiple LLM versions (GPT-5 Pro vs GPT-5)
```r
metrics_llm_pro_full <- readr::read_csv(here("data","metrics_long.csv"), ...)
metrics_llm_5_full   <- readr::read_csv(here("data","metrics_long_gpt-5.csv"), ...)

metrics_llm_both <- bind_rows(metrics_llm_pro, metrics_llm_5)
metrics_use_2llms <- bind_rows(metrics_human, metrics_llm_both)
```

**Flexibility:**
- Enables future comparisons between model versions
- Maintains separation until explicitly combined
- Each version tracked with "version" column

### 3.4 Bounds Clamping & Validation
**Location in slides:** Lines 394-397, 435-436, 473-475
**Status in results.qmd:** Basic fix_bounds exists but clamping is better in slides

**Improved bounds validation:**
```r
lo = ifelse(is.finite(lo), pmax(0, pmin(100, lo)), NA_real_),
hi = ifelse(is.finite(hi), pmax(0, pmin(100, hi)), NA_real_)
```

**Benefits:**
- Explicit clamping to valid ranges (0-100 for percentiles, 1-5 for tiers)
- Prevents invalid plotting with out-of-range values
- Applied consistently across all data loading chunks

---

## 4. BETTER NARRATIVE & PRESENTATION

### 4.1 Human-AI Preference Comparison Table (top-human-and-ai-pref)
**Location in slides:** Lines 1636-1730
**Status in results.qmd:** Not present

**Feature:** Side-by-side HTML table showing:
- Top 5 papers humans rated higher than LLM (green highlighting)
- Top 5 papers LLM rated higher than humans (orange highlighting)
- Automatically formatted with proper styling

**Code Generates:**
- Formatted list with ranking delta values
- Custom HTML table with two columns
- Color-coded differences for visual impact

### 4.2 Rationale Extraction & Display (rationales_williams)
**Location in slides:** Lines 1795-1814
**Status in results.qmd:** Mentions rationale but doesn't extract/display it

**Improvement:**
- Extracts LLM rationale text from full metrics data
- Displays as blockquotes for specific criteria
- Provides qualitative evidence alongside quantitative ratings

### 4.3 Better Exploratory Framing
**Location in slides:** "Our initial concrete questions" section (lines 805-844)
**Status in results.qmd:** Less structured presentation

**Better Organization:**
- Explicit research questions stated upfront
- Question numbering with sub-questions in notes
- Clear signposting of what's being explored

---

## 5. VISUALIZATION REFINEMENTS

### 5.1 Improved Color Handling
**Location in slides:** Line 287-289
```r
UJ_ORANGE <- "#f19e4b"   # LLM
UJ_GREEN  <- "#99bb66"   # Human
UJ_BLUE   <- "#4e79a7"   # GPT-5 (legacy)
```

**Benefit:** Added third color variable for legacy model comparisons

### 5.2 Better Theme & Plot Settings
**Slides improvements throughout:**
- Consistent `theme_uj()` application
- Better use of `theme()` for axis label angles (60 degrees vs 40 in results.qmd)
- Proper use of `clip = "off"` for label placement beyond plot area
- Better margin management with `margin()`

### 5.3 Comparative Scatter Plots
**Location in slides:** Lines 1922-1955 (scatter-overall-both-llms)
**Status in results.qmd:** Not present

**Feature:** Compares two LLM versions on same scatter plot
- Different colors and shapes for each version
- Individual regression lines for each model
- Shows one performs better than the other

---

## 6. CODE ORGANIZATION & QUALITY

### 6.1 Cleaner Data Loading Pipeline
**Slides approach (lines 305-490):**
- Separate load chunks for each data type (tiers, metrics, 2-LLM comparison)
- Clear intermediate calculations (e.g., `key_map`, `rsx_research`)
- Better use of `relationship = "many-to-one"` join specification
- More defensive coding with `filter()` for valid data

### 6.2 Helper Function Consolidation
**Slides implements:**
- `canon_metric()` - consistent metric name mapping
- `lane_offsets_center()` and `lane_offsets_skip0()` - forest plot positioning
- `bin_together()` - binning for kappa computation (also in results.qmd)
- `weighted_kappa()` - flexible kappa calculation (also in results.qmd)

### 6.3 Better Error Handling
**Examples from slides:**
```r
alpha_overall <- tryCatch({
  if (requireNamespace("irr", quietly = TRUE)) {
    M <- rbind(D$Human, D$LLM); irr::kripp.alpha(M, method = "interval")$value
  } else NA_real_
}, error = function(e) NA_real_)
```

---

## 7. MISSING DATA HANDLING

### 7.1 More Sophisticated Filtering
**Slides approach (line 471-479):**
```r
filter(!is.na(label_paper), !is.na(mid)) |>
  mutate(across(c(mid, lo, hi), ~ round(.x, 4))) |>
  distinct(label_paper, criteria, who, evaluator, mid, lo, hi, .keep_all = FALSE)
```

**Benefits:**
- Removes exact duplicates (protects against human rater duplicates)
- Rounds values to prevent float precision issues
- More explicit NA handling

### 7.2 Safe Min/Max with Fallback
**Results.qmd has this (good), slides uses it more consistently:**
```r
human_lo_union = safe_min(lower_ci, middle_rating),
human_hi_union = safe_max(upper_ci, middle_rating),
```

---

## 8. MODELING & FUTURE WORK

### 8.1 Infrastructure for Model Comparison
**Slides provides:**
- Support for loading multiple model versions
- Framework for comparing model outputs side-by-side
- Version tracking in data frames
- Ready for future LLM/hybrid comparisons

### 8.2 Documented Next Steps
**Lines 1860-1888 (notes):**
Clear roadmap for improvements:
- Statistical analyses (multi-level modeling)
- Content-swap bias tests
- Journal outcome prediction
- Hybrid human-AI trials
- Human evaluator enumerators

---

## RECOMMENDATIONS FOR INCORPORATION INTO results.qmd

### High Priority (Core Improvements)

1. **Add Krippendorff's alpha calculations** (Lines 1302-1434)
   - Import `irr` package
   - Add human-human comparison to agreement tables
   - Provides better context for LLM-Human agreement assessment

2. **Implement canon_metric() function** (Lines 408-416)
   - Use consistently across all data loading
   - Reduces naming inconsistencies

3. **Add tier-correlation visualization** (Lines 1454-1567)
   - Uncomment and adapt from slides (currently commented in results.qmd)
   - Provides insight into evaluation priorities
   - Includes both LLM and human metrics

4. **Improve scatter plot with statistics** (Lines 1091-1126)
   - Add regression line and agreement statistics
   - Display Krippendorff's alpha prominently
   - Better visual presentation

5. **Better table formatting** (Lines 1201-1276)
   - Use `kableExtra` for styled tables
   - Multi-line headers for clarity
   - Consistent formatting

### Medium Priority (Enhanced Visualizations)

6. **Add vertical forest plot variant** (Lines 951-1029)
   - Provides cleaner presentation option
   - Better for paper-by-paper comparison
   - Include annotation capability

7. **Add human evaluator profile plot** (Lines 549-610)
   - Shows rating patterns across criteria
   - Useful for understanding evaluator diversity

8. **Add heatmap color inversion** (Lines 1585-1632)
   - More intuitive color coding (green=human higher)
   - Order papers by overall difference

9. **Add human-AI preference table** (Lines 1636-1730)
   - Identifies papers with biggest disagreements
   - Useful for qualitative analysis

### Lower Priority (Future Enhancements)

10. **Multi-LLM comparison infrastructure** (Lines 495-544)
    - Set up for GPT-5 vs GPT-5 Pro comparisons
    - Version tracking in data
    - Can be implemented as data becomes available

11. **Improved lane offset functions** (Lines 370-383)
    - More explicit logic
    - Better for forest plots

12. **Better bounds clamping** (various lines)
    - Explicit clamping to valid ranges
    - More defensive programming

---

## SPECIFIC CODE SECTIONS TO REVIEW

### Key Improvements to Copy/Adapt

1. **agreement-helpers chunk** (slides lines 1302-1346)
   - Enhanced bin_together and weighted_kappa
   - Better error handling
   - Reusable for multiple analyses

2. **combined-alpha-interval-metrics chunk** (slides lines 1388-1434)
   - Combines LLM-H and H-H comparisons
   - Shows both in single table
   - Good use of group_modify()

3. **tier-correlations-comparison chunk** (slides lines 1454-1567)
   - Separate LLM vs Human correlation calculations
   - Dumbbell plot visualization
   - Interesting insights about evaluation priorities

4. **profile_humans_fixed chunk** (slides lines 549-610)
   - Multi-metric profile visualization
   - Clean metric labeling
   - Secondary axis for tier conversion

---

## SUMMARY OF VALUE-ADDS

| Category | Count | Key Items |
|----------|-------|-----------|
| New Visualizations | 5 | Forest vert, profile plot, scatter w/ stats, dumbbell, inverted heatmap |
| Statistical Analyses | 3 | Krippendorff's alpha, H-H comparison, improved agreement tables |
| Helper Functions | 4 | canon_metric, improved lane_offsets, better bounds handling |
| Data Handling | 3 | Multi-LLM loading, better filtering, value clamping |
| Code Quality | 2 | Better organization, error handling |
| Presentation | 2 | Better framing, HTML tables with kableExtra |

**Total High-Value Improvements:** 21 distinct enhancements ready to be incorporated
