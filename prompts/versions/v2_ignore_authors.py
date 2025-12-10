"""
Prompt Version: v2_ignore_authors
Created: October 14, 2025
Based on: v1_initial_guidelines + basic_debias

Used in runs:
- ignore_authors_v1 (gpt-4, ~10 test papers)

Characteristics:
- Added explicit "ignore author identity" instruction (basic_debias)
- Same structure as v1 otherwise

Performance notes:
- Test run to assess impact of author-blind instruction
- Commit: f97e767
"""

from prompts.builder import build_prompt, load_component

# Add basic_debias after role
SYSTEM_PROMPT = build_prompt(
    preamble="\n\n".join([
        load_component("base_role.txt"),
        load_component("basic_debias.txt")
    ]),
    guidelines=load_component("base_guidelines.txt"),
    custom_components={
        "metrics": load_component("metric_definitions.txt"),
        "calibration": load_component("calibration_instructions.txt"),
        "tiers": load_component("tier_instructions.txt"),
    },
    postamble=load_component("schema_instructions.txt")
)
