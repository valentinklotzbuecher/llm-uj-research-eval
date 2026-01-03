#!/usr/bin/env python3
"""
Compare GPT-5.2 Pro Key Issues with Coda Human Expert Critiques.

This script:
1. Loads human expert critiques from Coda CSV
2. Loads GPT-5.2 Pro key_issues from JSON responses
3. Uses GPT-5.2 Pro to assess alignment between the two
4. Outputs structured comparison results
"""

import csv
import json
import pathlib
import os
from openai import OpenAI

# Paths
CODA_CSV = pathlib.Path("/Users/yosemite/githubs/coda_org_unjournal/coda_content/hub_internal/tables/research.csv")
GPT_JSON_DIR = pathlib.Path("results/gpt52_pro_focal_jan2026/json")
OUTPUT_FILE = pathlib.Path("results/key_issues_comparison.json")

# Paper name mapping: GPT filename (without .response.json) -> Coda label_paper_title (partial match)
PAPER_MAPPING = {
    "Acemoglu_et_al._2024": "Misperceptions and Demand for Democracy",
    "Adena_and_Hager_2024": "Does online fundraising increase charitable giving",
    "Benabou_et_al._2023": "Willful Ignorance and Moral Behavior",
    "Bilal_and_Kaenzig_2024": "Macroeconomic Impact of Climate Change",
    "Blimpo_and_Castaneda-Dower_2025": "Asymmetry in Civic Information",
    "Bruers_2021": "animal welfare cost of meat",
    "Clancy_2024": "Returns to Science In the Presence of Technological",
    "Dullaghan_and_Zhang_2022": "Forecasts estimate limited cultured meat",
    "Frech_et_al._2023": "wellbeing cost-effectiveness of StrongMinds",
    "Green_et_al._2025": "Meaningfully reducing consumption of meat",
    "McGuire_et_al._2024": "Ends versus Means: Kantians",
    "Peterman_et_al._2025": "Social Safety Nets, Women",
    "Weaver_et_al._2025": "Global potential for natural regeneration",
    "Williams_et_al._2024": "Cash Transfers for Child Development",
}


def load_api_key():
    """Load OpenAI API key from file."""
    key_path = pathlib.Path("key/openai_key.txt")
    if key_path.exists():
        return key_path.read_text().strip()
    raise FileNotFoundError("OpenAI API key not found at key/openai_key.txt")


def load_coda_critiques():
    """Load human expert critiques from Coda CSV."""
    critiques = {}
    with open(CODA_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            critique = row.get('Key critiques & issues with paper', '').strip()
            if critique and len(critique) > 50:
                title = row.get('label_paper_title', '')
                critiques[title] = critique
    return critiques


def load_gpt_key_issues(paper_name):
    """Load GPT-5.2 Pro key_issues from JSON response."""
    json_path = GPT_JSON_DIR / f"{paper_name}.response.json"
    if not json_path.exists():
        return None

    with open(json_path, 'r') as f:
        data = json.load(f)

    # Extract the text content which contains the JSON
    try:
        text_content = data['output'][1]['content'][0]['text']
        parsed = json.loads(text_content)
        return parsed.get('key_issues', [])
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        print(f"Error parsing {paper_name}: {e}")
        return None


def match_coda_paper(coda_critiques, search_term):
    """Find Coda paper by partial title match."""
    for title, critique in coda_critiques.items():
        if search_term.lower() in title.lower():
            return title, critique
    return None, None


def compare_issues_with_llm(client, paper_name, coda_critique, gpt_issues):
    """Use GPT-5.2 Pro to compare the critiques."""

    gpt_issues_formatted = "\n".join(gpt_issues)

    prompt = f"""You are evaluating how well an LLM's identified issues align with expert human critiques of a research paper.

## Task
Compare the GPT-5.2 Pro Key Issues against the Human Expert Critiques below. Assess:

1. **Coverage**: What proportion of the substantive issues raised by human experts are captured by the GPT key issues? (Give percentage estimate)
2. **Precision**: Are the GPT issues relevant and substantive, or does it include spurious/irrelevant issues? (Give percentage of GPT issues that are genuinely relevant)
3. **Missed Issues**: List the most important issues raised by human experts that GPT missed entirely
4. **Extra Issues**: List any important issues GPT identified that humans didn't mention (these could be valid additions or false positives)
5. **Overall Assessment**: Rate alignment as Excellent/Good/Moderate/Poor with 1-2 sentence justification

## Human Expert Critiques
{coda_critique}

## GPT-5.2 Pro Key Issues
{gpt_issues_formatted}

Respond in JSON format:
{{
  "coverage_pct": <number 0-100>,
  "precision_pct": <number 0-100>,
  "missed_issues": ["issue1", "issue2", ...],
  "extra_issues": ["issue1", "issue2", ...],
  "overall_rating": "<Excellent|Good|Moderate|Poor>",
  "overall_justification": "<1-2 sentences>",
  "detailed_notes": "<any additional observations>"
}}"""

    response = client.chat.completions.create(
        model="gpt-5.2-pro-2025-12-11",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    return json.loads(response.choices[0].message.content)


def extract_matched_data():
    """Extract and save matched data without LLM comparison (for later analysis)."""
    print("Extracting matched data...")

    # Load Coda critiques
    coda_critiques = load_coda_critiques()
    print(f"Found {len(coda_critiques)} papers with critiques in Coda")

    # Process each GPT paper
    matched_data = []
    unmatched_gpt = []
    unmatched_coda = list(coda_critiques.keys())

    for gpt_paper, search_term in PAPER_MAPPING.items():
        # Load GPT key issues
        gpt_issues = load_gpt_key_issues(gpt_paper)
        if gpt_issues is None:
            unmatched_gpt.append(gpt_paper)
            continue

        # Match to Coda paper
        coda_title, coda_critique = match_coda_paper(coda_critiques, search_term)
        if coda_critique is None:
            unmatched_gpt.append(gpt_paper)
            continue

        # Remove from unmatched list
        if coda_title in unmatched_coda:
            unmatched_coda.remove(coda_title)

        matched_data.append({
            "gpt_paper": gpt_paper,
            "coda_title": coda_title,
            "gpt_key_issues": gpt_issues,
            "coda_critique": coda_critique,
            "num_gpt_issues": len(gpt_issues),
            "coda_critique_length": len(coda_critique),
        })

    return matched_data, unmatched_gpt, unmatched_coda


def save_side_by_side(matched_data, output_path):
    """Save matched data as markdown for easy review."""
    with open(output_path, 'w') as f:
        f.write("# Key Issues Comparison: GPT-5.2 Pro vs Human Expert Critiques\n\n")
        f.write(f"**Papers matched:** {len(matched_data)}\n\n")
        f.write("---\n\n")

        for item in matched_data:
            f.write(f"## {item['gpt_paper']}\n\n")
            f.write(f"**Coda title:** {item['coda_title']}\n\n")

            f.write("### GPT-5.2 Pro Key Issues\n\n")
            for issue in item['gpt_key_issues']:
                # Clean up numbering if present
                issue_clean = issue.lstrip('0123456789) ').strip()
                f.write(f"- {issue_clean}\n")
            f.write("\n")

            f.write("### Human Expert Critiques (Coda)\n\n")
            f.write(item['coda_critique'])
            f.write("\n\n---\n\n")


def main(run_llm_comparison=False):
    print("Loading data...")

    # Extract matched data
    matched_data, unmatched_gpt, unmatched_coda = extract_matched_data()

    print(f"\n{'='*60}")
    print(f"Matched: {len(matched_data)} papers")
    print(f"Unmatched GPT papers: {unmatched_gpt}")
    print(f"Unmatched Coda papers: {[t[:50] + '...' for t in unmatched_coda]}")

    # Save raw matched data as JSON
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(matched_data, f, indent=2)
    print(f"\nRaw data saved to: {OUTPUT_FILE}")

    # Save side-by-side markdown for review
    md_output = OUTPUT_FILE.with_suffix('.md')
    save_side_by_side(matched_data, md_output)
    print(f"Side-by-side comparison saved to: {md_output}")

    if not run_llm_comparison:
        print("\n⚠ LLM comparison skipped (run with --compare flag to enable)")
        return

    # LLM comparison (optional)
    print("\nRunning LLM comparison...")
    api_key = load_api_key()
    client = OpenAI(api_key=api_key)

    results = []
    for item in matched_data:
        print(f"\nComparing: {item['gpt_paper']}")
        comparison = compare_issues_with_llm(
            client, item['gpt_paper'], item['coda_critique'], item['gpt_key_issues']
        )
        results.append({
            **item,
            "comparison": comparison
        })
        print(f"  Coverage: {comparison['coverage_pct']}%, Precision: {comparison['precision_pct']}%, Rating: {comparison['overall_rating']}")

    # Save results with comparison
    comparison_output = OUTPUT_FILE.with_name('key_issues_comparison_results.json')
    with open(comparison_output, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nComparison results saved to: {comparison_output}")

    # Summary statistics
    if results:
        avg_coverage = sum(r['comparison']['coverage_pct'] for r in results) / len(results)
        avg_precision = sum(r['comparison']['precision_pct'] for r in results) / len(results)
        ratings = [r['comparison']['overall_rating'] for r in results]

        print(f"\n{'='*60}")
        print("SUMMARY")
        print(f"Average Coverage: {avg_coverage:.1f}%")
        print(f"Average Precision: {avg_precision:.1f}%")
        print(f"Rating distribution: {dict((r, ratings.count(r)) for r in set(ratings))}")


if __name__ == "__main__":
    import sys
    run_compare = "--compare" in sys.argv
    main(run_llm_comparison=run_compare)
