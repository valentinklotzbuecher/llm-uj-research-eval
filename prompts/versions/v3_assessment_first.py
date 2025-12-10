"""
Prompt Version: v3_assessment_first
Created: October 26, 2025
Based on: v2_ignore_authors + diagnostic_summary_top

Used in runs:
- assessment_first_v2 (gpt-5-pro, 2 test papers)

Characteristics:
- basic_debias (ignore authors)
- diagnostic_summary_top (≤200 words assessment before scoring)
- Changed schema to include top-level assessment_summary field

Performance notes:
- Experimental approach testing if pre-assessment improves calibration
- Commit: dba7913
"""

from prompts.builder import build_prompt, load_component

# Add diagnostic assessment after debias, before guidelines
SYSTEM_PROMPT = build_prompt(
    preamble="\n\n".join([
        load_component("base_role.txt"),
        load_component("basic_debias.txt"),
        load_component("diagnostic_summary_top.txt")
    ]),
    guidelines=load_component("base_guidelines.txt"),
    custom_components={
        "metrics": load_component("metric_definitions.txt"),
        "calibration": load_component("calibration_instructions.txt"),
        "tiers": load_component("tier_instructions.txt"),
    },
    postamble=load_component("schema_instructions.txt")
)
