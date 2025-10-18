# Python Modules for LLM Research Evaluation

This document describes the modular Python code organization for the LLM-based research evaluation pipeline.

## Overview

The Python code has been extracted from `methods.qmd` into separate modules for better organization, maintainability, and reusability.

## Module Structure

### `config.py`
**Purpose**: Centralized configuration settings

**Contents**:
- Model configuration (MODEL, API keys)
- Cache paths (FILES_CACHE_PATH)
- Rate limiting parameters (TPM_LIMIT, RPM_LIMIT)
- Evaluation metrics list (METRICS)
- JSON schemas (METRIC_SCHEMA, TIER_METRIC_SCHEMA, COMBINED_SCHEMA)
- Directory paths (PAPERS_DIR, RESULTS_DIR)
- Timeout and retry configurations

**Usage**:
```python
from config import MODEL, METRICS, TEXT_FORMAT_COMBINED
```

### `llm_utils.py`
**Purpose**: Utility functions and classes for API interaction

**Contents**:
- `TokenPacer`: Rate limiting class for API calls
- `get_file_id()`: File caching with content-based hashing
- `call_with_retries()`: Automatic retry logic with exponential backoff
- `extract_json()`: Parse JSON from various response formats
- `wait_for_background()`: Poll for completion of async API tasks
- `extract_reasoning_meta()`: Extract metadata from reasoning responses

**Usage**:
```python
from llm_utils import call_with_retries, get_file_id, extract_json
```

### `evaluator.py`
**Purpose**: Main evaluation logic

**Contents**:
- `SYSTEM_PROMPT_COMBINED`: Full evaluation prompt
- `evaluate_paper()`: Main function to evaluate a research paper PDF

**Usage**:
```python
from evaluator import evaluate_paper
from openai import OpenAI

client = OpenAI()
results = evaluate_paper("paper.pdf", client=client)
```

### `batch_eval.py`
**Purpose**: Standalone script for batch processing

**Contents**:
- Main function to process multiple PDFs
- CSV export functionality
- Progress reporting and error handling

**Usage**:
```bash
# Process all PDFs in papers/ directory
python batch_eval.py

# Configure via environment variables
export UJ_MODEL="gpt-5-pro"
export UJ_PAPERS_DIR="/path/to/papers"
python batch_eval.py
```

## Environment Variables

The following environment variables can be used to configure the system:

- `OPENAI_API_KEY`: OpenAI API key (or place in `key/openai_key.txt`)
- `UJ_MODEL`: Model to use (default: `gpt-5-pro`)
- `UJ_TPM`: Tokens per minute limit (default: 30000)
- `UJ_RPM`: Requests per minute limit (default: 50)
- `UJ_PAPERS_DIR`: Directory containing PDFs to evaluate (default: `papers/`)

## File Structure

```
llm-uj-research-eval/
├── config.py                 # Configuration settings
├── llm_utils.py              # Utility functions
├── evaluator.py              # Evaluation logic
├── batch_eval.py             # Batch processing script
├── methods.qmd               # Quarto document (now imports from modules)
├── papers/                   # Input PDFs
├── results/                  # Output CSVs
└── cache/                    # File ID cache
    └── file_ids.json
```

## Output Files

The batch evaluation script produces three CSV files in `results/`:

1. **combined_long.csv**: All metrics and tiers in long format
2. **metrics_long.csv**: Only percentile metrics (0-100 scale)
3. **tiers_long.csv**: Only journal tier ratings (0-5 scale)

## Integration with Quarto

The `methods.qmd` file has been updated to import from these modules. The original inline code is preserved for reference but can be replaced with imports:

```python
# In methods.qmd
from config import API_KEY_PATH, MODEL, METRICS, TEXT_FORMAT_COMBINED
from evaluator import SYSTEM_PROMPT_COMBINED, evaluate_paper
```

## Migration Notes

- The modular code is functionally equivalent to the original inline code
- `get_file_id()` replaces `_get_file_id()` and takes a `client` parameter
- `extract_json()` replaces `_extract_json()`
- `extract_reasoning_meta()` replaces `_reasoning_meta()`
- All other functions maintain the same signatures

## Benefits of Modular Structure

1. **Reusability**: Functions can be imported into other scripts
2. **Maintainability**: Easier to update configuration and logic
3. **Testing**: Modules can be unit tested independently
4. **Documentation**: Clearer separation of concerns
5. **Version Control**: Smaller, focused diffs
