"""
Prompt Version: v1_initial_guidelines
Created: ~September 2025
Based on: Initial UJ guidelines

Used in runs:
- initial_guidelines (gpt-4, ~50 papers)

Characteristics:
- No explicit author-blind instruction
- No diagnostic assessment
- Combined percentile + tiers schema

Performance notes:
- Production baseline
- Output: data/metrics_long.csv, data/combined_long.csv
"""

from prompts.builder import build_prompt, load_component

# No debias, no diagnostic - just straight to guidelines
SYSTEM_PROMPT = build_prompt(
    preamble=load_component("base_role.txt"),
    guidelines=load_component("base_guidelines.txt"),
    custom_components={
        "metrics": load_component("metric_definitions.txt"),
        "calibration": load_component("calibration_instructions.txt"),
        "tiers": load_component("tier_instructions.txt"),
    },
    postamble=load_component("schema_instructions.txt")
)
