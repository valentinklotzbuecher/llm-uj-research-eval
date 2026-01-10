#!/usr/bin/env python3
"""
Match human expert issues to LLM issues using sentence embedding similarity.

This script computes cosine similarity between human issues and LLM issues
using sentence-transformers, then outputs explicit issue-to-issue mappings.

Usage:
    python tools/match_issues_embeddings.py

Output:
    results/key_issues_matched.json
"""

import json
import sys
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "sentence-transformers"])
    from sentence_transformers import SentenceTransformer
    import numpy as np

# Configuration
SIMILARITY_THRESHOLD = 0.35  # Minimum similarity to consider a match
TOP_K_MATCHES = 3  # Maximum number of LLM issues to match per human issue

# Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
COMPARISON_JSON = PROJECT_ROOT / "results" / "key_issues_comparison.json"
OUTPUT_JSON = PROJECT_ROOT / "results" / "key_issues_matched.json"


def load_comparison_data():
    """Load the comparison data with human and LLM issues."""
    with open(COMPARISON_JSON, 'r') as f:
        return json.load(f)


def parse_human_issues(coda_critique):
    """
    Parse human critique text into individual issues.
    Reuses logic from build_issue_annotation_data.py
    """
    import re

    if not coda_critique:
        return []

    issues = []
    lines = coda_critique.splitlines()

    # Severity patterns
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


def compute_similarity_matrix(human_texts, llm_texts, model):
    """Compute cosine similarity matrix between human and LLM issues."""
    if not human_texts or not llm_texts:
        return np.array([])

    human_embeddings = model.encode(human_texts, show_progress_bar=False)
    llm_embeddings = model.encode(llm_texts, show_progress_bar=False)

    # Normalize for cosine similarity
    human_norm = human_embeddings / np.linalg.norm(human_embeddings, axis=1, keepdims=True)
    llm_norm = llm_embeddings / np.linalg.norm(llm_embeddings, axis=1, keepdims=True)

    # Compute cosine similarity
    similarity = np.dot(human_norm, llm_norm.T)
    return similarity


def match_issues(similarity_matrix, threshold=SIMILARITY_THRESHOLD, top_k=TOP_K_MATCHES):
    """
    Match human issues to LLM issues based on similarity.

    Returns:
        matched_pairs: list of {human_issue_index, llm_issue_indices, match_quality}
        unmatched_human: list of human issue indices with no matches
        unmatched_llm: list of LLM issue indices not matched to any human issue
    """
    if similarity_matrix.size == 0:
        return [], list(range(1, similarity_matrix.shape[0] + 1)), []

    n_human, n_llm = similarity_matrix.shape
    matched_pairs = []
    matched_llm_indices = set()

    for i in range(n_human):
        # Get top matches above threshold
        scores = similarity_matrix[i]
        sorted_indices = np.argsort(scores)[::-1]
        matches = []

        for j in sorted_indices[:top_k]:
            if scores[j] >= threshold:
                matches.append(int(j) + 1)  # 1-indexed
                matched_llm_indices.add(int(j) + 1)

        if matches:
            match_quality = int(max(scores[matches[0] - 1] for m_idx in matches[:1]) * 100)
        else:
            match_quality = 0

        matched_pairs.append({
            "human_issue_index": i + 1,  # 1-indexed
            "llm_issue_indices": matches,
            "match_quality": match_quality
        })

    # Find unmatched issues
    unmatched_human = [p["human_issue_index"] for p in matched_pairs if not p["llm_issue_indices"]]
    unmatched_llm = [j for j in range(1, n_llm + 1) if j not in matched_llm_indices]

    return matched_pairs, unmatched_human, unmatched_llm


def main():
    print("Loading sentence transformer model...")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    print(f"Loading comparison data from {COMPARISON_JSON}...")
    data = load_comparison_data()

    results = {}

    for paper in data:
        paper_id = paper['gpt_paper']
        print(f"\nProcessing: {paper_id}")

        # Parse human issues
        human_issues = parse_human_issues(paper.get('coda_critique', ''))
        llm_issues = paper.get('gpt_key_issues', [])

        if not human_issues:
            print(f"  No human issues parsed")
            results[paper_id] = {
                "matched_pairs": [],
                "unmatched_human": [],
                "unmatched_llm": list(range(1, len(llm_issues) + 1)),
                "human_issues": [],
                "llm_issues": llm_issues
            }
            continue

        if not llm_issues:
            print(f"  No LLM issues")
            results[paper_id] = {
                "matched_pairs": [],
                "unmatched_human": list(range(1, len(human_issues) + 1)),
                "unmatched_llm": [],
                "human_issues": [{"text": h["text"], "severity": h["severity"]} for h in human_issues],
                "llm_issues": []
            }
            continue

        # Extract text for embedding
        human_texts = [h["text"] for h in human_issues]
        llm_texts = llm_issues

        # Compute similarity
        similarity = compute_similarity_matrix(human_texts, llm_texts, model)

        # Match issues
        matched_pairs, unmatched_human, unmatched_llm = match_issues(similarity)

        print(f"  Human issues: {len(human_issues)}, LLM issues: {len(llm_issues)}")
        print(f"  Matched pairs: {sum(1 for p in matched_pairs if p['llm_issue_indices'])}")
        print(f"  Unmatched human: {len(unmatched_human)}, Unmatched LLM: {len(unmatched_llm)}")

        # Store results with issue texts for display
        results[paper_id] = {
            "matched_pairs": matched_pairs,
            "unmatched_human": unmatched_human,
            "unmatched_llm": unmatched_llm,
            "human_issues": [{"text": h["text"], "severity": h["severity"]} for h in human_issues],
            "llm_issues": llm_issues
        }

    # Save results
    print(f"\nSaving results to {OUTPUT_JSON}...")
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(results, f, indent=2)

    print("Done!")


if __name__ == "__main__":
    main()
