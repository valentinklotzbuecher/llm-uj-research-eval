#!/usr/bin/env python3
"""
Compare human expert issues to LLM issues using LLM-based semantic matching.

This script uses the OpenAI API to perform explicit issue-to-issue matching,
providing more accurate results than embedding-based cosine similarity.

Usage:
    python tools/compare_issues_llm.py [--dry-run] [--paper PAPER_ID]

Output:
    results/key_issues_llm_matched.json

Requirements:
    - OpenAI API key in key/openai_key.txt
    - results/key_issues_comparison.json (from parse_key_issues.py)
"""

import json
import sys
import time
import argparse
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("Installing openai package...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openai"])
    from openai import OpenAI

# Configuration
MODEL = "gpt-5.2-pro"  # or "gpt-4o" for cheaper/faster option
MAX_RETRIES = 3
RETRY_DELAY = 5  # seconds

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
KEY_FILE = PROJECT_ROOT / "key" / "openai_key.txt"
COMPARISON_JSON = PROJECT_ROOT / "results" / "key_issues_comparison.json"
OUTPUT_JSON = PROJECT_ROOT / "results" / "key_issues_llm_matched.json"

# Updated prompt requesting explicit issue-to-issue matching
COMPARISON_PROMPT_TEMPLATE = """You are comparing human expert critiques with LLM-identified issues for a research paper evaluation.

## Task
For each numbered human issue below, identify which LLM issue(s) cover it (if any), and rate the match quality.

## Human Expert Issues
{human_issues}

## LLM Issues
{llm_issues}

## Instructions
1. For each human issue (H1, H2, ...), identify which LLM issue(s) address the same concern
2. Rate match quality: 0-100% where 100% = exact same concern, 0% = no overlap
3. A human issue can match multiple LLM issues (partial coverage across several)
4. An LLM issue can match multiple human issues
5. Note issues that have no matches on either side

Respond in JSON format with these exact fields:
{{
    "matched_pairs": [
        {{
            "human_issue_index": 1,
            "llm_issue_indices": [3, 5],
            "match_quality": 75,
            "match_notes": "LLM issues L3 and L5 together cover this concern, though less specifically"
        }},
        ...
    ],
    "unmatched_human": [2, 4],
    "unmatched_llm": [1, 6, 7],
    "coverage_pct": 70,
    "precision_pct": 60,
    "overall_rating": "Good",
    "overall_justification": "Most key concerns are captured but with less specificity",
    "detailed_notes": "Additional observations about the comparison"
}}

Be precise about which issues match. If a human issue discusses "sample size" and an LLM issue discusses "statistical power", those are related but distinct - rate accordingly."""


def load_api_key():
    """Load OpenAI API key from file."""
    if not KEY_FILE.exists():
        raise FileNotFoundError(
            f"API key file not found: {KEY_FILE}\n"
            "Please create the file with your OpenAI API key."
        )
    return KEY_FILE.read_text().strip()


def parse_human_issues(coda_critique):
    """
    Parse human critique text into numbered issues.
    Returns list of (index, text) tuples.
    """
    import re

    if not coda_critique:
        return []

    issues = []
    lines = coda_critique.splitlines()

    SEVERITY_PATTERNS = [
        (r'^\s*(?:necessary|critical|major)', 'necessary'),
        (r'^\s*optional', 'optional'),
        (r'^\s*unsure', 'unsure'),
    ]

    current_severity = 'optional'
    current_issue_lines = []

    def flush_issue():
        nonlocal current_issue_lines
        if not current_issue_lines:
            return
        text = "\n".join(current_issue_lines).strip()
        # Clean leading numbering
        text = re.sub(r"^[\-\*\d\.\)\s]+", "", text).strip()
        if len(text) > 15:  # Skip very short fragments
            issues.append({
                "text": text,
                "severity": current_severity
            })
        current_issue_lines = []

    for line in lines:
        stripped = line.strip()

        # Check for severity header
        for pattern, severity in SEVERITY_PATTERNS:
            if re.match(pattern, stripped, re.IGNORECASE):
                flush_issue()
                current_severity = severity
                break
        else:
            # Check for numbered item
            if re.match(r'^\s*\d+[\.\)]\s+', stripped):
                flush_issue()
                issue_text = re.sub(r'^\s*\d+[\.\)]\s+', '', stripped)
                current_issue_lines = [issue_text] if issue_text else []
            elif stripped:
                current_issue_lines.append(stripped)

    flush_issue()
    return issues


def format_issues_for_prompt(human_issues, llm_issues):
    """Format issues with numbered labels for the prompt."""
    human_text = ""
    for i, issue in enumerate(human_issues, 1):
        severity_tag = f" [{issue['severity'].upper()}]" if issue.get('severity') else ""
        human_text += f"H{i}{severity_tag}: {issue['text']}\n\n"

    llm_text = ""
    for i, issue in enumerate(llm_issues, 1):
        llm_text += f"L{i}: {issue}\n\n"

    return human_text.strip(), llm_text.strip()


def compare_with_llm(client, paper_name, human_issues, llm_issues):
    """Use LLM to compare issues and return explicit matches."""
    if not human_issues:
        return {
            "error": "No human issues",
            "matched_pairs": [],
            "unmatched_human": [],
            "unmatched_llm": list(range(1, len(llm_issues) + 1)),
            "coverage_pct": None,
            "precision_pct": None
        }

    if not llm_issues:
        return {
            "error": "No LLM issues",
            "matched_pairs": [],
            "unmatched_human": list(range(1, len(human_issues) + 1)),
            "unmatched_llm": [],
            "coverage_pct": None,
            "precision_pct": None
        }

    # Format for prompt
    human_text, llm_text = format_issues_for_prompt(human_issues, llm_issues)

    prompt = COMPARISON_PROMPT_TEMPLATE.format(
        human_issues=human_text,
        llm_issues=llm_text
    )

    # Call API with retries
    for attempt in range(MAX_RETRIES):
        try:
            response = client.responses.create(
                model=MODEL,
                text={"format": {"type": "json_object"}},
                input=[
                    {"role": "user", "content": [
                        {"type": "input_text", "text": prompt}
                    ]}
                ],
                reasoning={"effort": "medium", "summary": "auto"},
                max_output_tokens=4000,
            )

            # Extract output text
            output_text = None
            for block in response.output:
                if block.type == "message":
                    for content in block.content:
                        if content.type == "output_text":
                            output_text = content.text
                            break

            if output_text:
                result = json.loads(output_text)
                # Ensure required fields
                result.setdefault("matched_pairs", [])
                result.setdefault("unmatched_human", [])
                result.setdefault("unmatched_llm", [])
                return result
            else:
                print(f"  Warning: No output text in response")

        except Exception as e:
            print(f"  Attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)

    return {
        "error": "API call failed after retries",
        "matched_pairs": [],
        "unmatched_human": list(range(1, len(human_issues) + 1)),
        "unmatched_llm": list(range(1, len(llm_issues) + 1)),
        "coverage_pct": None,
        "precision_pct": None
    }


def main():
    parser = argparse.ArgumentParser(description="Compare issues using LLM")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse and format without calling API")
    parser.add_argument("--paper", type=str,
                        help="Only process specific paper ID")
    parser.add_argument("--model", type=str, default=MODEL,
                        help=f"Model to use (default: {MODEL})")
    args = parser.parse_args()

    global MODEL
    MODEL = args.model

    print(f"Loading data from {COMPARISON_JSON}...")
    if not COMPARISON_JSON.exists():
        print(f"Error: {COMPARISON_JSON} not found")
        print("Run the key issues matching first (see methods.qmd)")
        sys.exit(1)

    with open(COMPARISON_JSON) as f:
        data = json.load(f)

    if not args.dry_run:
        print("Loading API key...")
        api_key = load_api_key()
        client = OpenAI(api_key=api_key)
    else:
        print("DRY RUN - will not call API")
        client = None

    results = {}

    for item in data:
        paper_id = item.get("gpt_paper", "")

        if args.paper and paper_id != args.paper:
            continue

        print(f"\nProcessing: {paper_id}")

        # Parse human issues
        coda_critique = item.get("coda_critique", "")
        human_issues = parse_human_issues(coda_critique)
        llm_issues = item.get("gpt_key_issues", [])

        print(f"  Human issues: {len(human_issues)}")
        print(f"  LLM issues: {len(llm_issues)}")

        if args.dry_run:
            # Show formatted prompt
            human_text, llm_text = format_issues_for_prompt(human_issues, llm_issues)
            print("\n--- Human Issues (formatted) ---")
            print(human_text[:500] + "..." if len(human_text) > 500 else human_text)
            print("\n--- LLM Issues (formatted) ---")
            print(llm_text[:500] + "..." if len(llm_text) > 500 else llm_text)

            results[paper_id] = {
                "dry_run": True,
                "n_human": len(human_issues),
                "n_llm": len(llm_issues),
                "human_issues": human_issues,
                "llm_issues": llm_issues
            }
        else:
            # Call LLM
            comparison = compare_with_llm(client, paper_id, human_issues, llm_issues)

            # Add issue texts to result for display
            comparison["human_issues"] = human_issues
            comparison["llm_issues"] = llm_issues

            results[paper_id] = comparison

            if "error" in comparison:
                print(f"  Error: {comparison['error']}")
            else:
                n_matched = sum(1 for p in comparison.get("matched_pairs", [])
                               if p.get("llm_issue_indices"))
                print(f"  Matched: {n_matched}/{len(human_issues)} human issues")
                print(f"  Coverage: {comparison.get('coverage_pct')}%")
                print(f"  Precision: {comparison.get('precision_pct')}%")
                print(f"  Rating: {comparison.get('overall_rating')}")

    # Save results
    print(f"\nSaving results to {OUTPUT_JSON}...")
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("Done!")

    if not args.dry_run and results:
        # Summary statistics
        papers_with_results = [r for r in results.values() if "coverage_pct" in r and r.get("coverage_pct") is not None]
        if papers_with_results:
            avg_coverage = sum(r["coverage_pct"] for r in papers_with_results) / len(papers_with_results)
            avg_precision = sum(r.get("precision_pct", 0) or 0 for r in papers_with_results) / len(papers_with_results)
            print(f"\nSummary ({len(papers_with_results)} papers):")
            print(f"  Average coverage: {avg_coverage:.1f}%")
            print(f"  Average precision: {avg_precision:.1f}%")


if __name__ == "__main__":
    main()
