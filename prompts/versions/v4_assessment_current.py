"""
Prompt Version: v4_assessment_current
Created: December 2025
Based on: v3_assessment_first with expanded diagnostic

Used in runs:
- assessment_first_current (gpt-5-pro, in progress)

Characteristics:
- basic_debias (ignore authors)
- diagnostic_1000words (aim for 1000-word assessment)
- High reasoning effort
- Verbosity: high, max_output_tokens: 8000

Performance notes:
- Current active prompt as of December 2025
- Located in methods.qmd:312
"""

from prompts.builder import build_prompt, load_component

# Use 1000-word diagnostic instead of 200-word
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
