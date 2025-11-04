#!/usr/bin/env python3
"""
Analyze whether papers were updated in response to Unjournal evaluations.

This script:
1. Identifies papers that exist in both "before" (papers/) and "after" (latest_papers_post_UJ/) versions
2. Extracts text from both versions
3. Identifies major changes between versions
4. Matches papers to their Unjournal evaluations
5. Uses LLMs to assess whether changes reflect evaluator suggestions
"""

import os
import sys
import json
import csv
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import difflib
import hashlib

# PDF text extraction
try:
    import pdfplumber
except ImportError:
    print("Installing pdfplumber...")
    os.system("pip install pdfplumber")
    import pdfplumber

# Configuration
PAPERS_BEFORE_DIRS = ["papers", "more papers"]
PAPERS_AFTER_DIR = "latest_papers_post_UJ"
EVALUATIONS_DIR = "unjournal_evaluations"
OUTPUT_DIR = Path("paper_change_analysis")
RESULTS_FILE = OUTPUT_DIR / "change_analysis_results.json"
CONFIRMED_MATCHES_CSV = OUTPUT_DIR / "potential_matches.csv"

# Create output directory
OUTPUT_DIR.mkdir(exist_ok=True)


def normalize_title(title: str) -> str:
    """Normalize paper title for matching."""
    # Remove common variations
    title = title.lower()
    title = re.sub(r'[^\w\s]', '', title)  # Remove punctuation
    title = re.sub(r'\s+', ' ', title)  # Normalize whitespace
    title = title.strip()
    return title


def extract_pdf_text(pdf_path: Path, max_pages: int = None) -> str:
    """Extract text from PDF file."""
    try:
        text = []
        with pdfplumber.open(pdf_path) as pdf:
            pages_to_read = pdf.pages[:max_pages] if max_pages else pdf.pages
            for page in pages_to_read:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
        return "\n\n".join(text)
    except Exception as e:
        print(f"Error extracting text from {pdf_path}: {e}")
        return ""


def extract_title_from_pdf(pdf_path: Path) -> Optional[str]:
    """Extract likely title from first page of PDF."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            first_page = pdf.pages[0].extract_text()
            if first_page:
                # Get first few non-empty lines
                lines = [line.strip() for line in first_page.split('\n') if line.strip()]
                # Title is usually in first 1-3 lines
                likely_title = ' '.join(lines[:3])
                return likely_title[:200]  # Limit length
    except:
        pass
    return None


def extract_author_year(filename: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract author(s) and year from filename.
    Examples:
      - "Schuett et al. 2023.pdf" -> ("Schuett", "2023")
      - "Abhijit BanerjeeMichael Faye..." -> ("Banerjee", None)
      - "Anicet FangwaCaroline Flammer..." -> ("Fangwa", None)
    """
    stem = Path(filename).stem

    # Pattern 1: "Author et al. YYYY" (standard format)
    match = re.search(r'^([A-Z][a-z]+)(?:\s+et\s+al\.?)?\s+(\d{4})', stem)
    if match:
        return match.group(1), match.group(2)

    # Pattern 2: "FirstName LastNameFirstName..." (latest_papers_post_UJ format)
    # Look for pattern of CapitalLetter followed by lowercase, then CapitalLetter (likely last name start)
    # Example: "Abhijit BanerjeeMichael" -> "Banerjee" is the likely last name
    match = re.search(r'^[A-Z][a-z]+\s+([A-Z][a-z]+)[A-Z]', stem)
    if match:
        # Found: FirstName SPACE LastName[NextFirstName]
        last_name = match.group(1)

        # Try to find year anywhere in filename
        year_match = re.search(r'\b(19|20)\d{2}\b', stem)
        year = year_match.group(0) if year_match else None

        return last_name, year

    # Pattern 3: Generic first author extraction
    match = re.search(r'^([A-Z][a-z]+)', stem)
    if match:
        first_word = match.group(1)

        # Try to find year anywhere
        year_match = re.search(r'\b(19|20)\d{2}\b', stem)
        year = year_match.group(0) if year_match else None

        return first_word, year

    return None, None


def find_paper_pairs() -> List[Dict]:
    """
    Find papers that exist in both before and after directories.
    Reads from confirmed matches CSV if it exists, otherwise does matching.
    Returns list of dicts with before_path, after_path, and metadata.
    """
    # Check if we have confirmed matches
    if CONFIRMED_MATCHES_CSV.exists():
        print(f"\nReading confirmed matches from {CONFIRMED_MATCHES_CSV}...")

        # Load metadata to get paper titles
        metadata_file = Path(PAPERS_AFTER_DIR) / "metadata.csv"
        title_lookup = {}
        if metadata_file.exists():
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata_reader = csv.DictReader(f)
                for row in metadata_reader:
                    title_lookup[row['filename']] = row['paper_title']
            print(f"  Loaded {len(title_lookup)} paper titles from metadata")

        pairs = []
        with open(CONFIRMED_MATCHES_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('confirmed', '').upper() == 'YES':
                    # Build full paths
                    after_path = Path(PAPERS_AFTER_DIR) / row['after_file']
                    before_path = Path(row['before_path'])

                    if after_path.exists() and before_path.exists():
                        # Get paper title from metadata
                        paper_title = title_lookup.get(row['after_file'], row.get('after_title', ''))

                        pairs.append({
                            "before_path": str(before_path),
                            "after_path": str(after_path),
                            "match_method": "confirmed_manual",
                            "match_score": float(row['score']),
                            "paper_id": after_path.stem,
                            "paper_title": paper_title,
                            "before_name": before_path.name,
                            "after_name": after_path.name
                        })
                        print(f"  ✓ Confirmed match: {after_path.name[:60]}... <-> {before_path.name}")
                    else:
                        print(f"  ✗ Skipping (files not found): {row['after_file']} <-> {row['before_file']}")

        print(f"\nLoaded {len(pairs)} confirmed paper pairs")
        return pairs

    # Original matching logic (fallback)
    pairs = []

    # Get all "after" papers
    after_dir = Path(PAPERS_AFTER_DIR)
    after_papers = [p for p in after_dir.glob("*.pdf") if not p.name.startswith("FAILED_")]

    print(f"\nSearching for paper pairs...")
    print(f"Found {len(after_papers)} papers in {PAPERS_AFTER_DIR}")

    # Collect all before papers from all directories
    all_before_papers = []
    for before_dir_name in PAPERS_BEFORE_DIRS:
        before_dir = Path(before_dir_name)
        if not before_dir.exists():
            continue
        before_papers = list(before_dir.glob("*.pdf"))
        # Skip subdirectories
        before_papers = [p for p in before_papers if p.is_file()]
        all_before_papers.extend(before_papers)

    print(f"Found {len(all_before_papers)} papers in before directories")

    # For each after paper, try to find corresponding before version
    for after_pdf in after_papers:
        after_author, after_year = extract_author_year(after_pdf.name)
        after_title_norm = normalize_title(after_pdf.stem)

        best_match = None
        best_score = 0
        best_method = None

        for before_pdf in all_before_papers:
            before_author, before_year = extract_author_year(before_pdf.name)
            before_title_norm = normalize_title(before_pdf.stem)

            # Exact filename match (highest priority)
            if after_pdf.name == before_pdf.name:
                best_match = before_pdf
                best_score = 1.0
                best_method = "exact_filename"
                break

            # Author + year match
            if after_author and before_author and after_author == before_author:
                if after_year and before_year and after_year == before_year:
                    score = 0.9
                    if score > best_score:
                        best_match = before_pdf
                        best_score = score
                        best_method = f"author_year_match"
                elif after_year and before_year:
                    # Same author, different year - might be updated version
                    score = 0.7
                    if score > best_score:
                        best_match = before_pdf
                        best_score = score
                        best_method = f"author_match_different_year"
                else:
                    # Same author, but one or both missing year - still match
                    score = 0.8
                    if score > best_score:
                        best_match = before_pdf
                        best_score = score
                        best_method = f"author_match_no_year"

            # Fuzzy title matching
            similarity = difflib.SequenceMatcher(None, after_title_norm, before_title_norm).ratio()
            if similarity > 0.5 and similarity > best_score:  # At least 50% similar
                best_match = before_pdf
                best_score = similarity
                best_method = "fuzzy_title"

        if best_match and best_score >= 0.5:  # Minimum threshold
            pairs.append({
                "before_path": str(best_match),
                "after_path": str(after_pdf),
                "match_method": best_method,
                "match_score": best_score,
                "paper_id": after_pdf.stem,
                "before_name": best_match.name,
                "after_name": after_pdf.name
            })
            print(f"  ✓ Matched ({best_method}, {best_score:.0%}): {after_pdf.name[:50]}... <-> {best_match.name[:50]}...")

    print(f"\nFound {len(pairs)} paper pairs")
    return pairs


def extract_title_from_eval(eval_path: Path) -> Optional[str]:
    """Extract paper title from evaluation markdown file."""
    try:
        with open(eval_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Look for patterns like 'Evaluation X of "Title Here"'
        patterns = [
            r'Evaluation\s+\d+\s+of\s+"([^"]+)"',  # Evaluation 1 of "Title"
            r'Evaluation\s+\d+\s+of\s+â([^â]+)â',  # Smart quotes
            r'title:\s*["\']?Evaluation.*of\s+"([^"]+)"',  # In YAML frontmatter
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None
    except Exception as e:
        print(f"Error reading {eval_path}: {e}")
        return None


def find_evaluation_for_paper(paper_id: str, paper_title: str) -> Optional[List[Path]]:
    """Find evaluation file(s) for a given paper using title matching."""
    eval_dir = Path(EVALUATIONS_DIR)
    if not eval_dir.exists():
        return None

    eval_files = list(eval_dir.glob("*.md"))
    matches = []

    # Normalize paper title for matching
    title_norm = normalize_title(paper_title)

    print(f"    Looking for evaluations of: '{paper_title[:60]}...'")

    for eval_file in eval_files:
        # Extract title from evaluation content
        eval_title = extract_title_from_eval(eval_file)

        if eval_title:
            eval_title_norm = normalize_title(eval_title)

            # Check similarity
            similarity = difflib.SequenceMatcher(None, title_norm, eval_title_norm).ratio()

            if similarity > 0.6:  # Higher threshold for better matches
                matches.append(eval_file)
                print(f"      ✓ Match (sim={similarity:.2f}): {eval_file.name} - '{eval_title[:60]}...'")

    if not matches:
        print(f"      ✗ No evaluations found")

    return matches if matches else None


def compute_text_diff(text1: str, text2: str, context_lines: int = 3) -> Dict:
    """
    Compute differences between two texts.
    Returns dict with statistics and sample changes.
    """
    lines1 = text1.split('\n')
    lines2 = text2.split('\n')

    differ = difflib.Differ()
    diff = list(differ.compare(lines1, lines2))

    # Count changes
    additions = [line for line in diff if line.startswith('+ ')]
    deletions = [line for line in diff if line.startswith('- ')]

    # Get unified diff for better readability
    unified_diff = difflib.unified_diff(
        lines1, lines2,
        lineterm='',
        n=context_lines
    )

    return {
        "additions_count": len(additions),
        "deletions_count": len(deletions),
        "total_changes": len(additions) + len(deletions),
        "unified_diff_sample": '\n'.join(list(unified_diff)[:100])  # First 100 lines
    }


def analyze_paper_pair(pair: Dict) -> Dict:
    """Analyze a single paper pair (before/after)."""
    print(f"\n{'='*80}")
    print(f"Analyzing: {pair['paper_id']}")
    print(f"{'='*80}")

    before_path = Path(pair['before_path'])
    after_path = Path(pair['after_path'])

    # Extract text from both versions
    print("Extracting text from before version...")
    before_text = extract_pdf_text(before_path, max_pages=50)  # Limit for speed

    print("Extracting text from after version...")
    after_text = extract_pdf_text(after_path, max_pages=50)

    if not before_text or not after_text:
        return {
            **pair,
            "status": "error",
            "error": "Could not extract text from one or both PDFs"
        }

    # Compute differences
    print("Computing differences...")
    diff_stats = compute_text_diff(before_text, after_text)

    # Find evaluations
    print("Finding evaluations...")
    paper_title = pair.get('paper_title', pair['paper_id'])
    eval_files = find_evaluation_for_paper(pair['paper_id'], paper_title)

    result = {
        **pair,
        "status": "success",
        "before_text_length": len(before_text),
        "after_text_length": len(after_text),
        "text_length_change": len(after_text) - len(before_text),
        "text_length_change_pct": ((len(after_text) - len(before_text)) / len(before_text) * 100) if before_text else 0,
        **diff_stats,
        "evaluation_files": [str(f) for f in eval_files] if eval_files else [],
        "has_evaluation": bool(eval_files),
        "timestamp": datetime.now().isoformat()
    }

    # Save extracted texts for LLM analysis
    text_dir = OUTPUT_DIR / "extracted_texts" / pair['paper_id']
    text_dir.mkdir(parents=True, exist_ok=True)

    (text_dir / "before.txt").write_text(before_text)
    (text_dir / "after.txt").write_text(after_text)
    if diff_stats['unified_diff_sample']:
        (text_dir / "diff.txt").write_text(diff_stats['unified_diff_sample'])

    print(f"\nResults:")
    print(f"  Text length change: {result['text_length_change']:+,} chars ({result['text_length_change_pct']:+.1f}%)")
    print(f"  Total changes: {result['total_changes']:,} (additions: {result['additions_count']:,}, deletions: {result['deletions_count']:,})")
    print(f"  Has evaluation: {'Yes' if result['has_evaluation'] else 'No'}")
    if result['has_evaluation']:
        print(f"  Evaluation files: {len(result['evaluation_files'])}")

    return result


def main():
    """Main execution function."""
    print("="*80)
    print("PAPER CHANGE ANALYSIS - Phase 1: Identification and Text Extraction")
    print("="*80)

    # Step 1: Find paper pairs
    pairs = find_paper_pairs()

    if not pairs:
        print("\nNo paper pairs found. Nothing to analyze.")
        return

    # Step 2: Analyze each pair
    results = []
    for i, pair in enumerate(pairs, 1):
        print(f"\n\n[{i}/{len(pairs)}]")
        result = analyze_paper_pair(pair)
        results.append(result)

    # Step 3: Save results
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")

    with_evals = [r for r in results if r.get('has_evaluation')]
    print(f"\nTotal pairs analyzed: {len(results)}")
    print(f"Pairs with evaluations: {len(with_evals)}")
    print(f"Pairs without evaluations: {len(results) - len(with_evals)}")

    # Save JSON results
    RESULTS_FILE.write_text(json.dumps(results, indent=2))
    print(f"\nResults saved to: {RESULTS_FILE}")

    # Create summary CSV
    csv_file = OUTPUT_DIR / "change_analysis_summary.csv"
    with open(csv_file, 'w', newline='') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    print(f"Summary CSV saved to: {csv_file}")

    print(f"\nExtracted texts saved to: {OUTPUT_DIR / 'extracted_texts'}/")
    print("\nNext step: Run LLM analysis on these pairs to assess whether changes reflect evaluator suggestions.")


if __name__ == "__main__":
    main()
