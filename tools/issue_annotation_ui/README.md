Issue Match Annotator

Overview
- This UI supports manual matching of human critiques to LLM issues.
- Data is generated from `results/key_issues_comparison.json` and LLM response JSONs.

Generate data
- `python3 tools/build_issue_annotation_data.py`
- Outputs: `tools/issue_annotation_ui/data.json` and `tools/issue_annotation_ui/data.js`

Use
- Open `tools/issue_annotation_ui/index.html` in a browser.
- Select a paper, then select a human issue from the dropdown.
- Fill match score, confidence, context checkbox, and link to LLM issues.
- Export JSON/CSV for analysis.

Notes
- Severity labels are normalized to `necessary`, `optional`, `unsure`.
- The formatted critique panel groups issues by severity for review.
