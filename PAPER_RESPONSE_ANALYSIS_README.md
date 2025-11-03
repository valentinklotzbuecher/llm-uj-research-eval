# Paper Response Analysis Pipeline

This directory contains tools to analyze whether research papers were revised in response to Unjournal evaluations.

## Overview

The pipeline uses LLMs to:
1. **Identify changes** between paper versions (before/after Unjournal evaluation)
2. **Extract suggestions** from Unjournal evaluations
3. **Assess attribution** - determine if changes likely reflect evaluator feedback
4. **Generate evidence** - provide specific quotes and explanations

## Files

### Analysis Scripts

- **`analyze_paper_changes.py`** - Phase 1: Paper matching and text extraction
  - Finds paper pairs across `papers/`, `more papers/`, and `latest_papers_post_UJ/` folders
  - Extracts PDF text using pdfplumber
  - Computes text diffs between versions
  - Matches papers to evaluation files
  - Outputs: `paper_change_analysis/change_analysis_results.json`

- **`llm_change_attribution.py`** - Phase 2: LLM-based analysis
  - Uses GPT-4 to analyze changes and suggestions
  - Three-step analysis:
    1. Change detection (identify major changes)
    2. Suggestion extraction (parse evaluation files)
    3. Attribution assessment (match changes to suggestions)
  - Outputs: `paper_change_analysis/llm_analysis/*.json`

- **`paper_response_analysis.qmd`** - Phase 3: Quarto chapter
  - Presents results in the published book
  - Shows case studies with evidence
  - Configured as an appendix in `_quarto.yml`

## Usage

### Step 1: Identify Paper Pairs

```bash
conda activate qpy311_arm
python analyze_paper_changes.py
```

This will:
- Search for matching papers by author name and year
- Extract text from PDFs (first 50 pages)
- Compute diffs and statistics
- Save results to `paper_change_analysis/`

**Output:**
- `paper_change_analysis/change_analysis_results.json` - Full results
- `paper_change_analysis/change_analysis_summary.csv` - Summary table
- `paper_change_analysis/extracted_texts/` - Extracted PDF texts

### Step 2: Run LLM Analysis

```bash
conda activate qpy311_arm
python llm_change_attribution.py
```

This will:
- Load paper pairs from Step 1
- Call GPT-4 API to analyze each pair
- Generate detailed attribution analysis
- Cost: ~$0.50-2.00 per paper pair (depending on length)

**Output:**
- `paper_change_analysis/llm_analysis/PAPER_ID_analysis.json` - Individual results
- `paper_change_analysis/llm_analysis/combined_attribution_results.json` - All results

### Step 3: Render Results

```bash
quarto render paper_response_analysis.qmd
```

Or render the full book:

```bash
quarto render
```

## Current Limitations

### 1. DOI Deposit Dates Not Available

The Coda public API doesn't expose:
- `doi_deposit_date` (DOI deposit timestamp)
- `deposit date > unjournal pub date` (calculated formula column)

**Workaround:**
- Manual matching based on filenames
- Export CSV from Coda and import

### 2. Filename Matching Challenges

Papers have different naming conventions:
- **latest_papers_post_UJ**: `"FirstName LastNameFirstName LastName_Title.pdf"`
- **more papers**: `"LastName et al. YEAR.pdf"`

**Solution:**
- Fuzzy matching on author surnames
- Manual verification for important pairs
- See `paper_response_analysis.qmd` for curated matches

### 3. PDF Text Extraction

Some PDFs may have:
- Poor OCR quality
- Complex layouts (tables, figures)
- Non-standard formatting

**Mitigation:**
- Only analyze first 50 pages (abstract, intro, methods, results)
- Skip failed extractions
- Manual review of important cases

## Configuration

### API Keys

OpenAI API key must be in `key/openai_key.txt`

### Model Settings

Edit `llm_change_attribution.py`:
```python
MODEL = "gpt-4-turbo-preview"  # or "gpt-4o"
MAX_TOKENS = 4096
TEMPERATURE = 0.3  # Lower = more focused
```

### Rate Limits

Default settings:
- TPM: 90,000 (tokens per minute)
- RPM: 3,500 (requests per minute)
- 2-second sleep between papers

## Output Structure

### change_analysis_results.json

```json
{
  "paper_id": "Paper title",
  "before_path": "path/to/before.pdf",
  "after_path": "path/to/after.pdf",
  "match_method": "author_year_match",
  "match_score": 0.9,
  "before_text_length": 50000,
  "after_text_length": 52000,
  "text_length_change_pct": 4.0,
  "additions_count": 150,
  "deletions_count": 100,
  "has_evaluation": true,
  "evaluation_files": ["unjournal_evaluations/eval1.md"]
}
```

### LLM Analysis Output

```json
{
  "changes_analysis": {
    "major_changes": [
      {
        "location": "Methods section",
        "type": "methodological",
        "description": "Added robustness checks with alternative specifications",
        "importance": 4,
        "evidence": "Quote from paper..."
      }
    ]
  },
  "suggestions_analysis": [
    {
      "type": "analytical",
      "description": "Test sensitivity to alternative model specifications",
      "priority": 4,
      "quote": "Quote from evaluation..."
    }
  ],
  "attribution_analysis": {
    "attributions": [
      {
        "likely_influenced": true,
        "confidence": 4,
        "attribution_type": "direct",
        "explanation": "The added robustness checks directly address..."
      }
    ],
    "overall_assessment": {
      "percent_likely_influenced": "60-70%",
      "confidence_in_assessment": 4
    }
  }
}
```

## Future Improvements

1. **Better Paper Matching**
   - Use DOI metadata from Crossref
   - Parse author lists from PDF metadata
   - Use embedding similarity on abstracts

2. **Enhanced Change Detection**
   - Semantic diff (not just text diff)
   - Track specific sections (abstract, methods, results)
   - Identify figure/table changes

3. **Evaluation Parsing**
   - Extract structured suggestions from evaluations
   - Categorize by type (major/minor, method/interpretation)
   - Track which suggestions were addressed

4. **Automated Reporting**
   - Generate case study templates
   - Create visualizations of changes
   - Produce summary statistics

## Troubleshooting

### "No paper pairs found"

**Cause:** Filename matching failed

**Solution:**
1. Check filenames manually
2. Add manual matches to `paper_response_analysis.qmd`
3. Improve regex patterns in `extract_author_year()`

### "Could not extract text from PDF"

**Cause:** PDF is scanned image or corrupted

**Solution:**
1. Check PDF opens correctly
2. Try OCR if needed
3. Skip and note in appendix

### "API rate limit exceeded"

**Cause:** Too many requests to OpenAI

**Solution:**
1. Increase sleep time between calls
2. Reduce batch size
3. Check rate limits for your API tier

## Contact

For questions about this pipeline, see the main project README or open an issue on GitHub.
