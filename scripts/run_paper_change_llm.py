#!/usr/bin/env python3
"""
LLM-based analysis: do paper updates reflect evaluator suggestions?

Run from project root:
    conda run -n qpy311_arm python scripts/run_paper_change_llm.py [--paper KEY] [--dry-run]

Inputs:
    data/paper_fetch_manifest.json
    papers/*.pdf                   (before versions)
    data/latest_papers/*.pdf       (after versions, from fetch_latest_papers.py)
    data/unjournal_evaluations/*.md

Output:
    data/paper_change_llm_results.json
"""

import argparse
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    sys.exit("pdfplumber not installed. Run: pip install pdfplumber")

try:
    import difflib
except ImportError:
    pass  # stdlib

try:
    import anthropic
except ImportError:
    sys.exit("anthropic not installed. Run: pip install anthropic")

REPO_ROOT = Path(__file__).parent.parent
MANIFEST_PATH = REPO_ROOT / "data" / "paper_fetch_manifest.json"
EVALS_DIR = REPO_ROOT / "data" / "unjournal_evaluations"
RESULTS_PATH = REPO_ROOT / "data" / "paper_change_llm_results.json"
KEY_FILE = REPO_ROOT / "key" / "anthropic_key.txt"

MODEL = "claude-opus-4-6"
TEMPERATURE = 0.2
MAX_TEXT_CHARS = 60_000   # per paper version fed to the LLM
MAX_EVAL_CHARS = 30_000   # evaluation text fed to the LLM

# Minimum change threshold — skip papers with trivial diffs
MIN_TEXT_CHANGE_PCT = 0.5
MIN_TOTAL_CHANGES = 15


# ---------------------------------------------------------------------------
# PDF text extraction
# ---------------------------------------------------------------------------

def extract_pdf_text(pdf_path: Path, max_pages: int = 60) -> str:
    try:
        pages = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:max_pages]:
                t = page.extract_text()
                if t:
                    pages.append(t)
        return "\n\n".join(pages)
    except Exception as e:
        print(f"  [warn] PDF extraction failed for {pdf_path.name}: {e}")
        return ""


# ---------------------------------------------------------------------------
# Diff
# ---------------------------------------------------------------------------

def compute_diff_stats(before: str, after: str) -> dict:
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)
    adds = dels = 0
    diff_sample_lines = []
    for line in difflib.unified_diff(before_lines, after_lines, n=3, lineterm=""):
        if line.startswith("+") and not line.startswith("+++"):
            adds += 1
        elif line.startswith("-") and not line.startswith("---"):
            dels += 1
        if len(diff_sample_lines) < 200:
            diff_sample_lines.append(line)

    len_before = len(before)
    len_after = len(after)
    change_pct = abs(len_after - len_before) / max(len_before, 1) * 100

    return {
        "additions_count": adds,
        "deletions_count": dels,
        "total_changes": adds + dels,
        "text_length_before": len_before,
        "text_length_after": len_after,
        "text_length_change": len_after - len_before,
        "text_length_change_pct": round(change_pct, 2),
        "diff_sample": "".join(diff_sample_lines[:150]),
    }


# ---------------------------------------------------------------------------
# Evaluation file matching
# ---------------------------------------------------------------------------

def _normalize(s: str) -> str:
    return re.sub(r"[^\w\s]", " ", s.lower())


def find_evaluation_file(paper_title: str, authors_str: str) -> Path | None:
    """Find the best-matching evaluation summary markdown for a paper."""
    if not EVALS_DIR.exists():
        return None

    title_words = set(_normalize(paper_title).split())
    first_author = authors_str.split(",")[0].strip().split()[-1].lower() if authors_str else ""

    best_path = None
    best_score = 0.0

    for md in EVALS_DIR.glob("*.md"):
        text = md.read_text(errors="ignore")

        # Skip author-response files
        yaml_title = ""
        m = re.search(r"^title:\s*(.+)$", text, re.MULTILINE)
        if m:
            yaml_title = m.group(1).strip().strip('"\'')
        if re.search(r"authors?\s*response", yaml_title, re.I):
            continue

        content_words = set(_normalize(text[:3000]).split())
        overlap = len(title_words & content_words) / max(len(title_words), 1)
        author_bonus = 0.2 if first_author and first_author in text.lower() else 0.0
        score = overlap + author_bonus

        if score > best_score and score > 0.25:
            best_score = score
            best_path = md

    return best_path


# ---------------------------------------------------------------------------
# Anthropic helpers
# ---------------------------------------------------------------------------

def load_api_key() -> str:
    if KEY_FILE.exists():
        return KEY_FILE.read_text().strip()
    import os
    key = os.environ.get("ANTHROPIC_API_KEY", "")
    if key:
        return key
    sys.exit(f"API key not found at {KEY_FILE} and ANTHROPIC_API_KEY env var not set")


def call_llm(client: anthropic.Anthropic, system: str, user: str) -> dict:
    for attempt in range(3):
        try:
            resp = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                temperature=TEMPERATURE,
                system=system + "\n\nReturn ONLY valid JSON. No markdown fences, no preamble, no explanation outside the JSON object.",
                messages=[
                    {"role": "user", "content": user},
                ],
            )
            raw = resp.content[0].text.strip()
            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = re.sub(r"^```(?:json)?\s*", "", raw)
                raw = re.sub(r"\s*```$", "", raw)
            return json.loads(raw)
        except Exception as e:
            print(f"  [llm error attempt {attempt+1}] {e}")
            time.sleep(4 * (attempt + 1))
    return {"error": "all attempts failed"}


# ---------------------------------------------------------------------------
# LLM prompts (adapted from unjournal_tools_interfaces)
# ---------------------------------------------------------------------------

CHANGE_DETECTION_SYSTEM = """You are an expert academic reviewer comparing two versions of a research paper.

Identify MAJOR substantive changes: new analyses, revised methods, updated conclusions, structural reorganisation, new robustness checks, changed framing.

IGNORE: typo fixes, minor rewording, citation additions that don't change substance, formatting.

Return JSON:
{
  "major_changes": [
    {
      "id": 0,
      "location": "section name or description",
      "type": "methodological|empirical|interpretational|structural|framing",
      "description": "specific description of the change",
      "importance": 1-5,
      "evidence": "brief quote or marker from the text"
    }
  ],
  "summary": "2-3 sentence overall summary of what changed"
}"""

SUGGESTION_EXTRACTION_SYSTEM = """You are reading an Unjournal peer evaluation of a research paper.

Extract the key substantive suggestions and critiques the evaluators made. Focus on:
- Specific requests for additional analysis or robustness checks
- Methodological concerns
- Framing or interpretation suggestions
- Data or measurement concerns

Return JSON:
{
  "suggestions": [
    {
      "id": 0,
      "type": "methodological|empirical|framing|data|other",
      "description": "what the evaluator suggested or criticised",
      "priority": 1-5,
      "quote": "verbatim quote from the evaluation, max 40 words"
    }
  ],
  "main_concerns": "1-2 sentence summary of the evaluators' main concerns"
}"""

ATTRIBUTION_SYSTEM = """You are assessing whether changes to a research paper were likely influenced by peer evaluator feedback.

Be CONSERVATIVE. Only mark a change as "direct" or "indirect" if there is clear conceptual alignment between the change and a specific suggestion. Many changes will be independent of the evaluation.

Return JSON:
{
  "attributions": [
    {
      "change_id": 0,
      "attribution_type": "direct|indirect|possible|unrelated",
      "confidence": 1-5,
      "matching_suggestion_ids": [0],
      "explanation": "why you think this change was or was not evaluation-driven"
    }
  ],
  "overall": {
    "pct_likely_influenced": 0,
    "confidence": 1-5,
    "narrative": "2-3 sentence summary: how much did the evaluation influence the revision?"
  }
}"""


def analyze_paper(client: anthropic.Anthropic, key: str, entry: dict, dry_run: bool) -> dict | None:
    title = entry["paper_title"]
    before_path = REPO_ROOT / entry["before_pdf"] if entry.get("before_pdf") else None
    after_path = REPO_ROOT / entry["after_pdf"] if entry.get("after_pdf") else None

    print(f"\n{'='*70}")
    print(f"Paper: {title[:65]}")

    if not before_path or not before_path.exists():
        print("  [skip] no before PDF")
        return None
    if not after_path or not after_path.exists():
        print("  [skip] no after PDF")
        return None

    print(f"  Before: {before_path.name}")
    print(f"  After:  {after_path.name}")

    # Text extraction
    before_text = extract_pdf_text(before_path)
    after_text = extract_pdf_text(after_path)
    if not before_text or not after_text:
        print("  [skip] text extraction failed")
        return None

    # Diff
    stats = compute_diff_stats(before_text, after_text)
    print(f"  Diff: {stats['additions_count']} adds, {stats['deletions_count']} dels, "
          f"{stats['text_length_change_pct']:.1f}% size change")

    # Skip trivial
    if (stats["text_length_change_pct"] < MIN_TEXT_CHANGE_PCT
            and stats["total_changes"] < MIN_TOTAL_CHANGES):
        print("  [skip] change below threshold (likely identical or trivially different)")
        return {
            "paper_key": key,
            "paper_title": title,
            "adj_status": entry.get("adj_status", ""),
            "deposit_after_uj": entry.get("deposit_after_uj", False),
            "before_pdf": str(before_path.relative_to(REPO_ROOT)),
            "after_pdf": str(after_path.relative_to(REPO_ROOT)),
            **stats,
            "eval_file": None,
            "skipped_reason": "below change threshold",
            "major_changes": [],
            "evaluator_suggestions": [],
            "attributions": [],
            "overall_assessment": None,
        }

    # Find evaluation
    eval_path = find_evaluation_file(title, entry.get("authors", ""))
    eval_text = eval_path.read_text(errors="ignore") if eval_path else ""
    if eval_path:
        print(f"  Eval: {eval_path.name}")
    else:
        print("  Eval: not found")

    result = {
        "paper_key": key,
        "paper_title": title,
        "adj_status": entry.get("adj_status", ""),
        "deposit_after_uj": entry.get("deposit_after_uj", False),
        "before_pdf": str(before_path.relative_to(REPO_ROOT)),
        "after_pdf": str(after_path.relative_to(REPO_ROOT)),
        **stats,
        "eval_file": str(eval_path.relative_to(REPO_ROOT)) if eval_path else None,
        "analysis_model": MODEL,
        "analysis_date": date.today().isoformat(),
    }

    if dry_run:
        print("  [dry-run] skipping LLM calls")
        result["major_changes"] = []
        result["evaluator_suggestions"] = []
        result["attributions"] = []
        result["overall_assessment"] = None
        return result

    # --- LLM Step 1: identify changes ---
    print("  Step 1: analyzing changes…")
    changes_result = call_llm(
        client,
        CHANGE_DETECTION_SYSTEM,
        f"BEFORE VERSION (first {MAX_TEXT_CHARS} chars):\n{before_text[:MAX_TEXT_CHARS]}\n\n"
        f"AFTER VERSION (first {MAX_TEXT_CHARS} chars):\n{after_text[:MAX_TEXT_CHARS]}",
    )
    major_changes = changes_result.get("major_changes", [])
    result["changes_summary"] = changes_result.get("summary", "")
    result["major_changes"] = major_changes
    time.sleep(2)

    # --- LLM Step 2: extract suggestions (only if we have an eval) ---
    evaluator_suggestions = []
    if eval_text:
        print("  Step 2: extracting evaluator suggestions…")
        sugg_result = call_llm(
            client,
            SUGGESTION_EXTRACTION_SYSTEM,
            f"EVALUATION TEXT:\n{eval_text[:MAX_EVAL_CHARS]}",
        )
        evaluator_suggestions = sugg_result.get("suggestions", [])
        result["eval_main_concerns"] = sugg_result.get("main_concerns", "")
        result["evaluator_suggestions"] = evaluator_suggestions
        time.sleep(2)
    else:
        result["evaluator_suggestions"] = []

    # --- LLM Step 3: attribution (only if we have both changes and suggestions) ---
    if major_changes and evaluator_suggestions:
        print("  Step 3: assessing attribution…")
        attr_result = call_llm(
            client,
            ATTRIBUTION_SYSTEM,
            f"MAJOR CHANGES:\n{json.dumps(major_changes, indent=2)}\n\n"
            f"EVALUATOR SUGGESTIONS:\n{json.dumps(evaluator_suggestions, indent=2)}",
        )
        result["attributions"] = attr_result.get("attributions", [])
        result["overall_assessment"] = attr_result.get("overall", None)
        time.sleep(2)
    else:
        result["attributions"] = []
        result["overall_assessment"] = None
        if not major_changes:
            print("  Step 3: skipped (no major changes identified)")
        else:
            print("  Step 3: skipped (no evaluation found)")

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Run LLM paper-change attribution analysis")
    parser.add_argument("--paper", help="Analyze only this paper key (from manifest)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Extract text and compute diffs but skip LLM calls")
    args = parser.parse_args()

    if not MANIFEST_PATH.exists():
        sys.exit(f"Manifest not found at {MANIFEST_PATH}. Run fetch_latest_papers.py first.")

    manifest = json.loads(MANIFEST_PATH.read_text())

    # Load existing results (allow incremental runs)
    existing_results = {}
    if RESULTS_PATH.exists():
        for r in json.loads(RESULTS_PATH.read_text()):
            existing_results[r["paper_key"]] = r

    client = None
    if not args.dry_run:
        client = anthropic.Anthropic(api_key=load_api_key())

    results = list(existing_results.values())
    processed_keys = set(existing_results.keys())

    entries = {k: v for k, v in manifest.items() if v["fetch_status"] == "success"}

    # Skip papers already manually classified (non-blank adj_status)
    # unless a specific paper was requested
    if not args.paper:
        skipped_manual = [k for k, v in entries.items() if v.get("adj_status", "").strip()]
        if skipped_manual:
            print(f"Skipping {len(skipped_manual)} already-classified papers: {', '.join(skipped_manual)}")
        entries = {k: v for k, v in entries.items() if not v.get("adj_status", "").strip()}

    if args.paper:
        entries = {k: v for k, v in manifest.items() if k == args.paper and manifest[k]["fetch_status"] == "success"}
        if not entries:
            sys.exit(f"Paper key '{args.paper}' not found or not fetched successfully.")

    print(f"Papers to analyze: {len(entries)} (skipping {len(processed_keys)} already done)\n")

    for key, entry in entries.items():
        if key in processed_keys and not args.paper:
            print(f"[skip] {key} — already in results")
            continue

        result = analyze_paper(client, key, entry, dry_run=args.dry_run)
        if result is not None:
            # Replace existing entry if re-running a specific paper
            results = [r for r in results if r["paper_key"] != key]
            results.append(result)
            # Save incrementally
            RESULTS_PATH.write_text(json.dumps(results, indent=2, ensure_ascii=False))

    print(f"\nDone. Results: {RESULTS_PATH}")
    n_with_attribution = sum(
        1 for r in results if r.get("overall_assessment") and
        r["overall_assessment"].get("pct_likely_influenced") is not None
    )
    print(f"Papers with full attribution analysis: {n_with_attribution}/{len(results)}")


if __name__ == "__main__":
    main()
