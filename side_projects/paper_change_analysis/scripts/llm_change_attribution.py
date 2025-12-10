#!/usr/bin/env python3
"""
LLM-based analysis to assess whether paper changes reflect evaluator suggestions.

This script uses the OpenAI API to:
1. Identify major/important changes between paper versions
2. Extract key suggestions from Unjournal evaluations
3. Assess whether changes align with evaluator suggestions
4. Generate detailed explanations and evidence
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# OpenAI imports
try:
    from openai import AsyncOpenAI
except ImportError:
    print("Installing openai...")
    os.system("pip install openai")
    from openai import AsyncOpenAI

# Configuration
API_KEY_FILE = "key/openai_key.txt"
INPUT_DIR = Path("paper_change_analysis")
OUTPUT_DIR = Path("paper_change_analysis/llm_analysis")
MODEL = "gpt-4-turbo-preview"  # or "gpt-4o" for latest
MAX_TOKENS = 4096
TEMPERATURE = 0.3  # Lower for more focused analysis

# Rate limiting
TPM_LIMIT = 90000  # Tokens per minute
RPM_LIMIT = 3500   # Requests per minute

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_api_key() -> str:
    """Load OpenAI API key."""
    key_path = Path(API_KEY_FILE)
    if not key_path.exists():
        raise FileNotFoundError(f"API key not found at {API_KEY_FILE}")
    return key_path.read_text().strip()


# System prompts for different analysis tasks

CHANGE_DETECTION_PROMPT = """You are an expert academic reviewer analyzing changes between two versions of a research paper.

Your task is to identify MAJOR and IMPORTANT changes between the "before" and "after" versions. Focus on:

1. **Substantive changes**: New analyses, different methods, revised conclusions
2. **Structural changes**: Reorganization, new sections, removed content
3. **Methodological changes**: Different data, updated models, revised approaches
4. **Interpretational changes**: Different framing, updated conclusions, new implications

IGNORE minor changes like:
- Typo fixes
- Minor wording changes
- Formatting updates
- Reference additions that don't change substance

For each major change, provide:
1. **Location**: Which section/part of the paper
2. **Type**: What kind of change (method, analysis, interpretation, etc.)
3. **Description**: What specifically changed
4. **Importance**: Why this change matters (1-5 scale, 5 = most important)

Return your analysis as a structured JSON object."""

SUGGESTION_EXTRACTION_PROMPT = """You are analyzing an Unjournal evaluation to extract key suggestions and critiques.

Your task is to identify:

1. **Major critiques**: Significant concerns about methods, data, interpretation
2. **Specific suggestions**: Concrete recommendations for improvement
3. **Requests for additional analysis**: Suggestions to add robustness checks, explore mechanisms, etc.
4. **Framing/interpretation suggestions**: Different ways to present or interpret results

For each suggestion/critique, provide:
1. **Type**: Methodological, interpretational, presentational, or analytical
2. **Description**: What the evaluator suggested
3. **Priority**: How strongly emphasized (1-5 scale, 5 = most emphasized)
4. **Quote**: Relevant quote from the evaluation (if available)

Return your analysis as a structured JSON object."""

ATTRIBUTION_PROMPT = """You are assessing whether changes to a research paper were likely influenced by evaluator suggestions.

You will be given:
1. A list of major changes made to the paper
2. A list of suggestions from Unjournal evaluations
3. Context about the timeline

Your task is to assess, for each major change:
1. **Likely attribution**: Does this change appear to address an evaluator suggestion?
2. **Strength of evidence**: How confident are you in the attribution? (1-5 scale)
3. **Matching suggestion(s)**: Which evaluator suggestion(s) does this address?
4. **Explanation**: WHY you think this change was/wasn't influenced by the evaluation

Consider:
- **Direct matches**: Change directly addresses a specific suggestion
- **Indirect matches**: Change is in the spirit of a suggestion but not exactly as stated
- **Coincidental**: Change might have happened anyway
- **Independent**: Change clearly unrelated to any evaluator feedback

Be balanced and evidence-based. Not all changes will be evaluation-driven.

Return your analysis as a structured JSON object."""


async def call_llm(
    client: AsyncOpenAI,
    system_prompt: str,
    user_message: str,
    json_mode: bool = True
) -> Dict:
    """Call OpenAI API with retry logic."""
    try:
        response = await client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            response_format={"type": "json_object"} if json_mode else {"type": "text"}
        )

        content = response.choices[0].message.content

        if json_mode:
            return json.loads(content)
        else:
            return {"text": content}

    except Exception as e:
        print(f"Error calling LLM: {e}")
        return {"error": str(e)}


async def analyze_changes(client: AsyncOpenAI, before_text: str, after_text: str, paper_id: str) -> Dict:
    """Identify major changes between paper versions."""
    print(f"  Analyzing changes for {paper_id}...")

    # Truncate texts if too long (GPT-4 context limit)
    max_chars = 50000  # Rough estimate for context window
    before_truncated = before_text[:max_chars]
    after_truncated = after_text[:max_chars]

    user_message = f"""Compare these two versions of a research paper and identify MAJOR changes.

BEFORE VERSION (first {len(before_truncated)} characters):
{before_truncated}

AFTER VERSION (first {len(after_truncated)} characters):
{after_truncated}

Provide your analysis as JSON with this structure:
{{
    "major_changes": [
        {{
            "location": "section name or description",
            "type": "methodological|analytical|interpretational|structural",
            "description": "detailed description of the change",
            "importance": 1-5,
            "evidence": "specific quote or reference from the text"
        }}
    ],
    "summary": "overall summary of changes"
}}"""

    result = await call_llm(client, CHANGE_DETECTION_PROMPT, user_message)
    return result


async def extract_suggestions(client: AsyncOpenAI, evaluation_text: str, paper_id: str) -> Dict:
    """Extract key suggestions from an evaluation."""
    print(f"  Extracting suggestions from evaluation for {paper_id}...")

    user_message = f"""Extract key suggestions and critiques from this Unjournal evaluation:

EVALUATION TEXT:
{evaluation_text[:30000]}

Provide your analysis as JSON with this structure:
{{
    "suggestions": [
        {{
            "type": "methodological|interpretational|presentational|analytical",
            "description": "what the evaluator suggested",
            "priority": 1-5,
            "quote": "relevant quote from evaluation"
        }}
    ],
    "overall_tone": "description of the overall evaluation tone",
    "main_concerns": "summary of the main concerns raised"
}}"""

    result = await call_llm(client, SUGGESTION_EXTRACTION_PROMPT, user_message)
    return result


async def assess_attribution(
    client: AsyncOpenAI,
    changes: Dict,
    suggestions: Dict,
    paper_id: str
) -> Dict:
    """Assess whether changes reflect evaluator suggestions."""
    print(f"  Assessing attribution for {paper_id}...")

    user_message = f"""Assess whether the changes to this paper were likely influenced by the evaluator suggestions.

CHANGES MADE TO THE PAPER:
{json.dumps(changes, indent=2)}

EVALUATOR SUGGESTIONS:
{json.dumps(suggestions, indent=2)}

Provide your analysis as JSON with this structure:
{{
    "attributions": [
        {{
            "change_id": "reference to the change from the changes list",
            "likely_influenced": true|false,
            "confidence": 1-5,
            "matching_suggestions": ["list of matching suggestion IDs"],
            "explanation": "detailed explanation of why you think this change was/wasn't influenced",
            "attribution_type": "direct|indirect|possible|unlikely|unrelated"
        }}
    ],
    "overall_assessment": {{
        "percent_likely_influenced": "estimated percentage",
        "confidence_in_assessment": 1-5,
        "summary": "overall summary of the attribution analysis"
    }}
}}"""

    result = await call_llm(client, ATTRIBUTION_PROMPT, user_message)
    return result


async def analyze_paper_pair(client: AsyncOpenAI, pair_data: Dict) -> Dict:
    """Complete analysis pipeline for a single paper pair."""
    paper_id = pair_data['paper_id']
    print(f"\n{'='*80}")
    print(f"Analyzing: {paper_id}")
    print(f"{'='*80}")

    text_dir = INPUT_DIR / "extracted_texts" / paper_id

    # Load extracted texts
    before_text = (text_dir / "before.txt").read_text()
    after_text = (text_dir / "after.txt").read_text()

    # Step 1: Analyze changes
    changes = await analyze_changes(client, before_text, after_text, paper_id)

    # Step 2: Extract suggestions from evaluations
    all_suggestions = []
    if pair_data.get('evaluation_files'):
        for eval_file in pair_data['evaluation_files']:
            eval_text = Path(eval_file).read_text()
            suggestions = await extract_suggestions(client, eval_text, paper_id)
            all_suggestions.append({
                "file": eval_file,
                "suggestions": suggestions
            })

    # Step 3: Assess attribution
    attribution = None
    if all_suggestions and changes.get('major_changes'):
        # Combine all suggestions for attribution analysis
        combined_suggestions = {
            "all_suggestions": all_suggestions,
            "summary": f"Found {len(all_suggestions)} evaluation(s) with suggestions"
        }
        attribution = await assess_attribution(client, changes, combined_suggestions, paper_id)

    result = {
        "paper_id": paper_id,
        "before_path": pair_data['before_path'],
        "after_path": pair_data['after_path'],
        "changes_analysis": changes,
        "suggestions_analysis": all_suggestions,
        "attribution_analysis": attribution,
        "timestamp": datetime.now().isoformat()
    }

    # Save individual result
    result_file = OUTPUT_DIR / f"{paper_id}_analysis.json"
    result_file.write_text(json.dumps(result, indent=2))
    print(f"  Saved results to {result_file}")

    return result


async def main():
    """Main execution function."""
    print("="*80)
    print("LLM-BASED CHANGE ATTRIBUTION ANALYSIS")
    print("="*80)

    # Load API key
    api_key = load_api_key()
    client = AsyncOpenAI(api_key=api_key)

    # Load results from phase 1
    results_file = INPUT_DIR / "change_analysis_results.json"
    if not results_file.exists():
        print(f"\nError: {results_file} not found. Run analyze_paper_changes.py first.")
        return

    with open(results_file) as f:
        pairs_data = json.load(f)

    # Filter to pairs with evaluations
    pairs_with_evals = [p for p in pairs_data if p.get('has_evaluation')]

    print(f"\nFound {len(pairs_with_evals)} paper pairs with evaluations")

    if not pairs_with_evals:
        print("No pairs with evaluations to analyze.")
        return

    # Analyze each pair
    all_results = []
    for i, pair in enumerate(pairs_with_evals, 1):
        print(f"\n[{i}/{len(pairs_with_evals)}]")
        result = await analyze_paper_pair(client, pair)
        all_results.append(result)

        # Rate limiting: sleep between calls
        if i < len(pairs_with_evals):
            await asyncio.sleep(2)  # 2 seconds between papers

    # Save combined results
    combined_file = OUTPUT_DIR / "combined_attribution_results.json"
    combined_file.write_text(json.dumps(all_results, indent=2))
    print(f"\n\nCombined results saved to: {combined_file}")

    # Generate summary statistics
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"Papers analyzed: {len(all_results)}")

    # Count papers with likely influenced changes
    influenced_count = sum(
        1 for r in all_results
        if r.get('attribution_analysis', {}).get('overall_assessment', {}).get('percent_likely_influenced')
    )
    print(f"Papers with attribution analysis: {influenced_count}")


if __name__ == "__main__":
    asyncio.run(main())
