# LLM Prompt Version Tracking

This document tracks all system prompts used for LLM paper evaluations across different runs.

## Main Tracking Table

| prompt_label | description | link_full_prompt | models_run | papers_run | prompt_characteristics | discussion | link_to_output | other_notes | last_run |
|--------------|-------------|------------------|------------|------------|------------------------|------------|----------------|-------------|----------|
| **initial_guidelines** | Initial baseline: UJ guidelines, no mention of UJ itself, no 'average across ratings', percentile+tiers combined | [methods.qmd @ d7370df](https://github.com/valentinklotzbuecher/llm-uj-research-eval/blob/d7370df/methods.qmd#L312)<br>[prompts/versions/v1_initial_guidelines.py](prompts/versions/v1_initial_guidelines.py) | gpt-4 | ~50 | *(none)* | Baseline run. Used for all production results in book. | [data/metrics_long.csv](data/metrics_long.csv)<br>[data/combined_long.csv](data/combined_long.csv) | First systematic run. | Sep 2025 |
| **ignore_authors_v1** | Explicitly ignore author identity | [methods.qmd @ f97e767](https://github.com/valentinklotzbuecher/llm-uj-research-eval/blob/f97e767/methods.qmd#L312)<br>[prompts/versions/v2_ignore_authors.py](prompts/versions/v2_ignore_authors.py) | gpt-4 | ~10 (test) | basic_debias | Testing impact of author-blind instruction. | [results/archive/](results/archive/) | Commit f97e767: "system prompt with 'ignore authors'" | Oct 14, 2025 |
| **assessment_first_v2** | Diagnostic assessment before scoring | [methods.qmd @ dba7913](https://github.com/valentinklotzbuecher/llm-uj-research-eval/blob/dba7913/methods.qmd#L312)<br>[prompts/versions/v3_assessment_first.py](prompts/versions/v3_assessment_first.py) | gpt-5-pro | 2 (test) | basic_debias,<br>diagnostic_summary_top | Experimental - testing if pre-assessment improves calibration. | [results/](results/) | Commit dba7913. Changed schema to include top-level assessment_summary. | Oct 26, 2025 |
| **assessment_first_current** | Longer diagnostic (1000 words) | [methods.qmd:312](methods.qmd#L312)<br>[prompts/versions/v4_assessment_current.py](prompts/versions/v4_assessment_current.py) | gpt-5-pro | In progress | basic_debias,<br>diagnostic_1000words | **Current active prompt**. Verbosity="high", max_output_tokens=8000. | TBD | Currently active version. | Dec 2025 (ongoing) |
| **gpt5_comparison_misc** | GPT-5 comparison run | [methods.qmd @ 3650d51](https://github.com/valentinklotzbuecher/llm-uj-research-eval/blob/3650d51/methods.qmd) | gpt-5<br>(standard, not Pro) | ~40 | *(same as initial_guidelines)* | Comparison showed interesting model differences. Same prompt as baseline, different model. | [data/metrics_long_gpt-5.csv](data/metrics_long_gpt-5.csv) | Outputs in data/*_gpt-5.csv | Oct 2025 |

---

## Prompt Characteristics Reference

| prompt_characteristic | Description/Text |
|-----------------------|------------------|
| **basic_debias** | "Do not look at any existing ratings or evaluations of these papers you might find on the internet or in your corpus, do not use the authors' names, status, or institutions in your judgment -- give these ratings based on the *content* of the papers alone; do the assessment based on your knowledge and insights." |
| **diagnostic_summary_top** | Top of instructions (after 'role'):<br>"Diagnostic summary (≤200 words, based only on the PDF):<br>Provide a compact paragraph that identifies the most important issues you detect in the manuscript itself (e.g., identification threats, data limitations, misinterpretations, internal inconsistencies, missing robustness, replication barriers). Be specific, neutral, and concrete. This summary should precede any scoring and should guide your uncertainty. Output this text in the JSON field `assessment_summary`." |
| **diagnostic_1000words** | As in diagnostic_summary_top, but "Diagnostic summary (Aim for about 1000 words, ...):..." |

---

## Prompt Evolution Timeline

```
Sep 2025      initial_guidelines          Baseline run (~50 papers, gpt-4)
              ├─ Full Unjournal guidelines
              └─ Combined percentile + tiers

Oct 14, 2025  ignore_authors_v1          Testing author-blind instruction
              └─ Added basic_debias

Oct 26, 2025  assessment_first_v2        Diagnostic assessment approach
              ├─ Require 200-word diagnostic (diagnostic_summary_top)
              └─ Schema change: added assessment_summary field

Oct 2025      gpt5_comparison_misc       Model comparison
              ├─ Same prompt as initial_guidelines
              └─ gpt-5 (standard) instead of gpt-4

Dec 2025      assessment_first_current   Expanded assessment
              ├─ Increased to 1000-word assessment (diagnostic_1000words)
              ├─ High reasoning effort
              └─ Currently active
```

---

## Component-Based Prompt Architecture

As of December 2025, prompts are now **modularized** using a component-based system. See [prompts/README.md](prompts/README.md) for full documentation.

### Components Available

Located in `prompts/components/`:

- **base_role.txt** - Core role definition ("You are an academic expert...")
- **basic_debias.txt** - Author-blind instruction
- **diagnostic_summary_top.txt** - 200-word diagnostic assessment
- **diagnostic_1000words.txt** - 1000-word diagnostic assessment
- **base_guidelines.txt** - Percentile ranking system, reference group definitions
- **metric_definitions.txt** - The 7 evaluation metrics
- **calibration_instructions.txt** - Credible interval guidance
- **tier_instructions.txt** - Journal tier ranking system
- **schema_instructions.txt** - JSON output requirements

### Version Files

Located in `prompts/versions/`:

Each version is a Python file that composes components:

```python
# prompts/versions/v4_assessment_current.py
from prompts.builder import build_prompt, load_component

SYSTEM_PROMPT = build_prompt(
    preamble="\n\n".join([
        load_component("base_role.txt"),
        load_component("basic_debias.txt"),
        load_component("diagnostic_1000words.txt")
    ]),
    guidelines=load_component("base_guidelines.txt"),
    custom_components={
        "metrics": load_component("metric_definitions.txt"),
        "calibration": load_component("calibration_instructions.txt"),
        "tiers": load_component("tier_instructions.txt"),
    },
    postamble=load_component("schema_instructions.txt")
)
```

### Using in methods.qmd

```python
# Import modular prompt
from prompts.versions.v4_assessment_current import SYSTEM_PROMPT
SYSTEM_PROMPT_COMBINED = SYSTEM_PROMPT

# Or switch versions easily:
from prompts.versions import v3_assessment_first
SYSTEM_PROMPT_COMBINED = v3_assessment_first.SYSTEM_PROMPT
```

---

## Creating New Prompt Versions

### Step 1: Identify Changes

What do you want to change?
- Just the diagnostic length? → Swap `diagnostic_1000words.txt` for `diagnostic_summary_top.txt`
- Remove author-blind instruction? → Remove `basic_debias.txt` from preamble
- Add new calibration guidance? → Create `calibration_strict.txt` component

### Step 2: Create New Version File

```python
# prompts/versions/v5_my_experiment.py
"""
Prompt Version: v5_my_experiment
Created: [DATE]
Based on: v4_assessment_current

Changes:
- [Describe what's different]

Used in runs:
- [Add run IDs as used]
"""

from prompts.builder import build_prompt, load_component

SYSTEM_PROMPT = build_prompt(
    preamble="\n\n".join([
        load_component("base_role.txt"),
        # Add/remove/change components here
    ]),
    # ... rest of build
)
```

### Step 3: Update methods.qmd

```python
from prompts.versions.v5_my_experiment import SYSTEM_PROMPT
SYSTEM_PROMPT_COMBINED = SYSTEM_PROMPT
```

### Step 4: Track the Run

```bash
python track_llm_run.py start \
  --model gpt-5-pro \
  --prompt-version v5_my_experiment \
  --description "Testing [what you're testing]" \
  --prompt-source "prompts/versions/v5_my_experiment.py"
```

### Step 5: Document Results

Add row to this table with performance notes after run completes.

---

## Performance Tracking Template

When completing a run, document:

| Metric | Value | Notes |
|--------|-------|-------|
| **Correlation with human ratings** | | |
| - overall | TBD | |
| - methods | TBD | |
| - claims_evidence | TBD | |
| **Calibration** | TBD | % of times 90% CI contains true value |
| **Average CI width** | TBD | Measure of uncertainty |
| **Consistency** | TBD | Agreement on same paper evaluated twice |
| **Token usage** | TBD | Avg tokens per paper |
| **Cost** | TBD | $ per paper |
| **Runtime** | TBD | Seconds per paper |

---

## A/B Testing Framework

### Example Experiment

```python
# prompts/experiments/calibration_test_dec2025.py

EXPERIMENT = {
    "name": "calibration_examples_dec2025",
    "hypothesis": "Adding calibration examples reduces CI width by 15% while maintaining calibration",
    "variants": {
        "control": "v4_assessment_current",
        "treatment": "v5_with_calibration_examples"
    },
    "test_papers": [
        "Acemoglu_2024.pdf",
        "Banerjee_2022.pdf",
        "Williams_2024.pdf"
    ],
    "metrics": ["interval_width", "calibration", "correlation"]
}
```

### Running Experiments

1. Define variants in `prompts/versions/`
2. Create experiment config
3. Run both variants on same test set
4. Compare metrics in results analysis

---

## Migration Notes

**Before** (hardcoded in methods.qmd):
- 400+ line string
- Hard to compare versions
- No component reuse
- Duplicated across git history

**After** (modular system):
- ✅ Components defined once in `prompts/components/`
- ✅ Versions compose components in `prompts/versions/`
- ✅ Easy to create variants (swap one component)
- ✅ Clean diffs between versions
- ✅ Side-by-side comparison possible

**Old hardcoded prompt** is preserved in methods.qmd as a commented-out reference.

---

## Related Documentation

- **[prompts/README.md](prompts/README.md)** - Complete modularization guide
- **[prompts/builder.py](prompts/builder.py)** - Composition utilities
- **[DATA_PROVENANCE.md](DATA_PROVENANCE.md)** - Data lineage & LLM run tracking
- **[results/llm_runs_metadata.csv](results/llm_runs_metadata.csv)** - Master run registry
- **[methods.qmd:312](methods.qmd#L312)** - Current active prompt usage
