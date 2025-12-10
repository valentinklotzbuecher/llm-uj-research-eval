# Prompt Modularization System

This directory contains a modular system for managing LLM evaluation prompts.

## Directory Structure

```
prompts/
├── README.md                    # This file
├── __init__.py                  # Package initialization
├── builder.py                   # Prompt composition utilities
├── components/                  # Reusable prompt components
│   ├── __init__.py
│   ├── base_guidelines.txt      # Core Unjournal evaluation guidelines
│   ├── calibration_instructions.txt  # Credible interval guidance
│   ├── schema_instructions.txt  # JSON output requirements
│   └── metric_definitions.txt   # Definitions of evaluation metrics
├── versions/                    # Complete prompt versions
│   ├── __init__.py
│   ├── v1_baseline_sept2024.py
│   ├── v2_ignore_authors.py
│   ├── v3_assessment_first.py
│   └── v4_assessment_expanded.py
└── experiments.py               # A/B testing configurations
```

## Quick Start

### Using a specific prompt version

```python
# In methods.qmd or anywhere
from prompts.versions.v4_assessment_expanded import SYSTEM_PROMPT

# Use in API call
response = client.responses.create(
    model="gpt-5-pro",
    input=[
        {"role": "system", "content": [{"type": "input_text", "text": SYSTEM_PROMPT}]},
        ...
    ]
)
```

### Creating a new prompt version

```python
# prompts/versions/v5_my_experiment.py
from prompts.builder import build_prompt

PREAMBLE = """
Your role -- You are an academic expert...
[Your custom preamble here]
"""

POSTAMBLE = """
Return STRICT JSON. Focus especially on [specific aspect].
"""

SYSTEM_PROMPT = build_prompt(
    guidelines="base_guidelines.txt",
    calibration="calibration_instructions.txt",
    schema="schema_instructions.txt",
    preamble=PREAMBLE,
    postamble=POSTAMBLE
)
```

### Comparing prompts

```python
from prompts.versions import v3_assessment_first, v4_assessment_expanded

# See differences
print("v3 length:", len(v3_assessment_first.SYSTEM_PROMPT))
print("v4 length:", len(v4_assessment_expanded.SYSTEM_PROMPT))

# Or use diff tool
import difflib
diff = difflib.unified_diff(
    v3_assessment_first.SYSTEM_PROMPT.splitlines(),
    v4_assessment_expanded.SYSTEM_PROMPT.splitlines(),
    lineterm=''
)
print('\n'.join(diff))
```

## Components

### base_guidelines.txt
Core Unjournal evaluation instructions that define:
- Percentile ranking system
- "Serious research" definition
- "Same area" reference group
- Metric definitions (overall, methods, claims_evidence, etc.)

### calibration_instructions.txt
Guidance on providing credible intervals:
- What 90% credible intervals mean
- How to calibrate uncertainty
- Examples of well-calibrated intervals

### schema_instructions.txt
JSON output format requirements:
- Field naming conventions
- Bounds validation (0-100 for percentiles, 0-5 for tiers)
- Required vs optional fields

### metric_definitions.txt
Detailed definitions of each evaluation metric:
- Overall assessment
- Claims and evidence
- Methods
- Advancing knowledge
- Logic and communication
- Open science
- Global relevance

## Versioning Strategy

### Version Naming Convention

`v{N}_{feature}_{date_if_applicable}.py`

Examples:
- `v1_baseline_sept2024.py` - Original baseline
- `v2_ignore_authors.py` - Added author-blind instruction
- `v3_assessment_first.py` - Diagnostic assessment approach
- `v4_assessment_expanded.py` - Longer assessment text

### Version Metadata

Each version file should include:

```python
"""
Prompt Version: v4_assessment_expanded
Created: 2024-12-10
Based on: v3_assessment_first
Changes: Expanded assessment from 200 to 1000 words

Used in runs:
- 20241210_gpt5pro_test_v4
- [Add run IDs as used]

Performance notes:
- [Add observations about calibration, correlation, etc.]
"""
```

## Builder API

### build_prompt()

```python
def build_prompt(
    guidelines: str = "base_guidelines.txt",
    calibration: str = "calibration_instructions.txt",
    schema: str = "schema_instructions.txt",
    preamble: str = "",
    postamble: str = "",
    custom_components: dict[str, str] = None
) -> str
```

Composes a complete prompt from components.

**Parameters:**
- `guidelines`: Filename in components/ or full text
- `calibration`: Filename in components/ or full text
- `schema`: Filename in components/ or full text
- `preamble`: Text to prepend
- `postamble`: Text to append
- `custom_components`: Dict of {placeholder: replacement_text}

**Returns:** Complete system prompt string

### load_component()

```python
def load_component(filename: str) -> str
```

Loads a component file from `components/` directory.

### substitute()

```python
def substitute(template: str, replacements: dict[str, str]) -> str
```

Performs placeholder substitution in templates.

## Experiments Framework

### Defining Experiments

```python
# prompts/experiments.py

EXPERIMENTS = {
    "calibration_examples_dec2024": {
        "description": "Test if calibration examples reduce interval width",
        "variants": {
            "control": "v3_assessment_first",
            "treatment": "v3_with_calibration_examples"
        },
        "test_papers": [
            "Acemoglu_2024.pdf",
            "Banerjee_2022.pdf",
            "Williams_2024.pdf"
        ],
        "metrics": ["interval_width", "calibration", "correlation"],
        "hypothesis": "Examples reduce CI width by 15% while maintaining calibration"
    }
}
```

### Running Experiments

```python
# In methods.qmd
from prompts.experiments import run_experiment

results = run_experiment(
    experiment_id="calibration_examples_dec2024",
    model="gpt-5-pro"
)

# Analyze results
results.compare_metrics()
results.plot_calibration()
```

## Best Practices

### 1. Keep Components Focused
Each component file should have a single responsibility:
- ✅ `base_guidelines.txt` - Just the guidelines
- ❌ Don't mix guidelines and schema instructions

### 2. Version Control Everything
- Commit new versions with clear messages
- Tag significant versions: `git tag prompt-v3-assessment-first`
- Link versions to runs in `llm_runs_metadata.csv`

### 3. Document Changes
- Add version metadata at top of each version file
- Update PROMPT_VERSIONS.md with characteristics and performance
- Note which components were modified

### 4. Test Before Production
- Run on 2-3 test papers first
- Check JSON schema compliance
- Verify token counts are reasonable

### 5. Track Performance
- Record correlation with human ratings
- Measure calibration (90% CI coverage)
- Monitor cost (tokens per paper)
- Note any systematic biases

## Migration from Current System

### Step 1: Extract Current Prompts

```bash
# Run extraction script
python -c "
from methods import SYSTEM_PROMPT_COMBINED
with open('prompts/versions/v4_current.txt', 'w') as f:
    f.write(SYSTEM_PROMPT_COMBINED)
"
```

### Step 2: Identify Components

Break current prompt into:
1. Preamble (role, instructions)
2. Guidelines (reusable across versions)
3. Calibration guidance (reusable)
4. Schema instructions (changes with schema)

### Step 3: Create Component Files

Extract each section into `components/*.txt`

### Step 4: Recreate as Modular Version

```python
# prompts/versions/v4_migrated.py
from prompts.builder import build_prompt

PREAMBLE = """[extracted preamble]"""
POSTAMBLE = """[extracted postamble]"""

SYSTEM_PROMPT = build_prompt(
    guidelines="base_guidelines.txt",
    calibration="calibration_instructions.txt",
    schema="schema_instructions.txt",
    preamble=PREAMBLE,
    postamble=POSTAMBLE
)
```

### Step 5: Validate Equivalence

```python
# Test that migrated version produces identical text
from methods import SYSTEM_PROMPT_COMBINED as original
from prompts.versions.v4_migrated import SYSTEM_PROMPT as migrated

assert original.strip() == migrated.strip(), "Migration changed prompt text!"
```

## Integration with methods.qmd

### Minimal Changes

```python
# At top of methods.qmd Python chunk
import sys
sys.path.insert(0, '.')  # Add project root to path

# Import specific version
from prompts.versions.v4_assessment_expanded import SYSTEM_PROMPT

# Use as before
SYSTEM_PROMPT_COMBINED = SYSTEM_PROMPT
```

### Parameterized Approach

```python
# For easy experimentation
from prompts.versions import (
    v3_assessment_first,
    v4_assessment_expanded,
    v5_experimental
)

# Set active version
ACTIVE_VERSION = "v4"  # Easy to change

VERSION_MAP = {
    "v3": v3_assessment_first.SYSTEM_PROMPT,
    "v4": v4_assessment_expanded.SYSTEM_PROMPT,
    "v5": v5_experimental.SYSTEM_PROMPT,
}

SYSTEM_PROMPT_COMBINED = VERSION_MAP[ACTIVE_VERSION]
```

## Future Enhancements

### 1. Templating Engine
Use Jinja2 or similar for more complex substitutions:
```python
from jinja2 import Template

template = Template(load_component("base_guidelines.txt"))
prompt = template.render(
    assessment_length=1000,
    metrics=["overall", "methods", "claims_evidence"]
)
```

### 2. Validation Layer
Automatically check prompts before use:
```python
from prompts.validator import validate_prompt

errors = validate_prompt(SYSTEM_PROMPT)
if errors:
    raise ValueError(f"Prompt validation failed: {errors}")
```

### 3. Performance Database
Track prompt performance systematically:
```python
from prompts.tracking import record_performance

record_performance(
    version="v4_assessment_expanded",
    run_id="20241210_test",
    metrics={
        "correlation_overall": 0.74,
        "calibration": 0.88,
        "avg_ci_width": 25.3
    }
)
```

## Related Documentation

- **[PROMPT_VERSIONS.md](../PROMPT_VERSIONS.md)** - Version tracking table
- **[results/llm_runs_metadata.csv](../results/llm_runs_metadata.csv)** - Run registry
- **[methods.qmd](../methods.qmd)** - Current active prompts
