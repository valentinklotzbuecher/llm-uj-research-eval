# Issue Match Annotator

Browser-based UI for manually labeling concordance between human expert critiques and LLM-identified key issues.

## Overview

This tool supports systematic comparison of human critiques (from Coda/Unjournal evaluation managers) with LLM key issues (from GPT-5.2 Pro evaluations). Annotators score how well LLM issues capture human concerns, link corresponding issues, and export structured labels for analysis.

**Note:** Human issues shown here are an ad-hoc distillation of key critiques, not the full evaluation text. The goal is to assess whether the LLM captures the most important concerns flagged by human experts.

## Quick Start

### 1. Generate data

```bash
python3 tools/build_issue_annotation_data.py
```

**Inputs:**
- `results/key_issues_comparison.json` (human critique + GPT key issues)
- `results/gpt52_pro_focal_jan2026/json/*.response.json` (LLM full reports)

**Outputs:**
- `tools/issue_annotation_ui/data.json`
- `tools/issue_annotation_ui/data.js`

### 2. Open the UI

```bash
open tools/issue_annotation_ui/index.html
# Or just open the file in any modern browser
```

No server required - runs entirely client-side.

### 3. Annotate

1. Enter your name in the "Annotator" field
2. Select a paper from the dropdown
3. For each human issue:
   - **Match score (0-1)**: How well LLM issues capture this concern
   - **Confidence (0-1)**: Your certainty in this assessment
   - **Context not shared**: Check if human critique references info LLM didn't have
   - **Link to LLM issues**: Check boxes for corresponding LLM issues
   - **Discussion**: Notes explaining your reasoning
4. Export when done

### 4. Export

**Export buttons download annotations for ALL papers** (not just the currently selected paper).

- **Download JSON**: Structured format with metadata
- **Download CSV**: Flat format for spreadsheet analysis

Annotations are also auto-saved to browser localStorage.

## Data Schema

### Input: Human Issue Suggestions

Human critiques are parsed with heuristics:
- **Severity labels** normalized to: `necessary`, `optional`, `unsure`
- Issue boundaries detected via enumeration, sentence breaks, section headers
- Evaluator attributions (E1, E2, DR) preserved in text

### Output: Annotation Fields

| Field | Type | Description |
|-------|------|-------------|
| `annotator` | string | Annotator name |
| `paper_id` | string | Paper identifier (e.g., "Acemoglu_et_al._2024") |
| `paper_title` | string | Full paper title |
| `human_issue_id` | string | Issue ID (H1, H2, ...) |
| `human_issue_text` | string | Full issue text |
| `human_issue_severity` | string | `necessary`, `optional`, `unsure`, or empty |
| `match_score` | float | 0-1 scale |
| `match_confidence` | float | 0-1 scale |
| `context_not_shared` | boolean | True if human had info LLM didn't |
| `llm_issue_ids` | string | Semicolon-separated (e.g., "L1;L3;L7") |
| `llm_issue_texts` | string | Full text of linked LLM issues |
| `discussion` | string | Free-text notes |

## Storage

Annotations are auto-saved to browser `localStorage` with key `issue-annotation-v2`. This persists across browser sessions but is local to your browser/machine.

**To share annotations** with collaborators, use the export buttons and share the JSON/CSV file.

## Suggested Improvements

### High Priority: Deployment & Sharing

**1. Hosted version with database backend**

For sharing with external annotators or collaborators, a hosted deployment would be valuable:
- Host on a simple server (GitHub Pages, Netlify, or custom backend)
- Replace localStorage with a database (e.g., Supabase, Firebase, or simple JSON API)
- Enable multiple annotators to work simultaneously
- Centralized data collection for analysis

*This would enable hiring external enumerators and showing the tool to others without requiring them to set up locally.*

### Medium Priority: Workflow Improvements

**2. Progress tracking**
- Visual indicator of completion status per paper (e.g., "8/12 issues annotated")
- Dashboard showing overall progress across all papers
- Flag papers that are fully complete vs. partially done

**3. Annotation guidelines panel**
- Embed calibration examples directly in the UI
- Show examples of 0, 0.5, 1 match scores
- Quick reference for edge cases

**4. Keyboard shortcuts**
- Arrow keys to navigate between issues
- Number keys for quick match score (1-9 → 0.1-0.9)
- Tab to move between fields

**5. Search and filter**
- Filter issues by severity level
- Filter by match status (unscored, low match, high match)
- Text search across issues

### Lower Priority

**6. Validation warnings**
- Flag issues with match_score > 0 but no linked LLM issues
- Flag issues with linked LLM issues but match_score = 0
- Warn before exporting if any issues are incomplete

**7. Undo/redo**
- Track annotation history
- Allow reverting recent changes

**8. Real-time summary statistics**
- Show mean match score, coverage rate, confidence distribution
- Update dynamically as annotations are made

**9. Inter-rater reliability tools** *(nice-to-have; analysis often done externally)*
- Import annotations from other annotators
- Compute agreement metrics (Cohen's kappa)
- Highlight disagreements

**10. Bidirectional coverage view** *(less priority given ad-hoc distillation)*
- Show which LLM issues are NOT linked to any human issue
- Could alternatively be assessed via LLM analysis

## Integration with Analysis

Exported annotations can be loaded in `results_critiques.qmd` to compute:

```r
# Example R code for loading annotations
annotations <- jsonlite::fromJSON("issue_annotations.json")$rows

# Coverage: % of human issues with match_score > threshold
coverage <- mean(annotations$match_score > 0.5, na.rm = TRUE)

# Average match by severity
annotations |>
  group_by(human_issue_severity) |>
  summarise(mean_match = mean(match_score))
```

## Technical Notes

- Pure client-side JavaScript (no backend required for local use)
- Uses browser localStorage for persistence
- Data files are static JSON loaded via `<script>` tag
- Responsive design works on desktop and tablet
- Export includes ALL papers, not just currently selected
