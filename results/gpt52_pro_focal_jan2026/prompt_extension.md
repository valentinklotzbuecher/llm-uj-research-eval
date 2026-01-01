# Prompt Extension for GPT-5.2 Pro Focal Run

This run uses the same base prompt as `gpt5_pro_updated_jan2026` (modular_v2) with the following extension.

## Extended PROMPT_OUTPUT

Replace the standard `PROMPT_OUTPUT` with:

```
PROMPT_OUTPUT_EXTENDED = """
Fill all three top-level keys:
- `assessment_summary`: about 1000 words.
- `key_issues`: a numbered list (array of strings) identifying the most important methodological, interpretive, or evidential issues in the paper. Each item should be a concise statement (1-2 sentences) that a reader could use as a checklist. Aim for 5-15 issues depending on the paper. Order from most to least important.
- `metrics`: object containing all required metrics.

Field names:
- Percentile metrics → `midpoint`, `lower_bound`, `upper_bound`.
- Tier metrics → `score`, `ci_lower`, `ci_upper`.

Return STRICT JSON matching the supplied schema. No preamble. No markdown. No extra text.
"""
```

## Extended Schema

Add `key_issues` to the schema:

```python
COMBINED_SCHEMA_EXTENDED = {
    "type": "object",
    "properties": {
        "assessment_summary": {"type": "string"},
        "key_issues": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Numbered list of key issues identified in the paper"
        },
        "metrics": {
            "type": "object",
            "properties": {
                **{m: metric_schema for m in METRICS},
                "tier_should": TIER_METRIC_SCHEMA,
                "tier_will":   TIER_METRIC_SCHEMA,
            },
            "required": METRICS + ["tier_should", "tier_will"],
            "additionalProperties": False,
        },
    },
    "required": ["assessment_summary", "key_issues", "metrics"],
    "additionalProperties": False,
}
```

## Full Python Code for This Run

See `run_evaluation.py` in this directory for the complete evaluation script.
