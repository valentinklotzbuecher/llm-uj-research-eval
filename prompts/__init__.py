"""
Modular prompt management system for LLM paper evaluations.

This package provides:
- Reusable prompt components
- Versioned complete prompts
- Builder utilities for composing prompts
- Experiment management for A/B testing

Usage:
    from prompts.versions.v4_assessment_expanded import SYSTEM_PROMPT

    # Or
    from prompts.builder import build_prompt
    prompt = build_prompt(guidelines="base_guidelines.txt", preamble="...")
"""

__version__ = "0.1.0"
