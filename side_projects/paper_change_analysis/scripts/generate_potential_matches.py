#!/usr/bin/env python3
"""
Generate potential paper matches for manual confirmation.
Uses metadata.csv for better matching.
"""

import csv
import difflib
from pathlib import Path
import re

# Paths
METADATA_CSV = "latest_papers_post_UJ/metadata.csv"
BEFORE_DIRS = ["papers", "more_papers"]

def normalize_text(text):
    """Normalize text for comparison."""
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
    text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
    return text.strip()

def extract_first_author(author_citation):
    """Extract first author surname from citation."""
    if not author_citation:
        return None
    # Format: "FirstName LastName, ..." or "LastName et al."
    first = author_citation.split(',')[0].strip()
    # Get last word (likely surname)
    parts = first.split()
    if parts:
        return parts[-1]  # Last word is usually surname
    return None

def main():
    # Load metadata
    with open(METADATA_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        after_papers = [row for row in reader if not row['filename'].startswith('FAILED_')]

    # Load before papers
    before_papers = []
    for before_dir in BEFORE_DIRS:
        dir_path = Path(before_dir)
        if dir_path.exists():
            for pdf in dir_path.glob("*.pdf"):
                if pdf.is_file():
                    before_papers.append({
                        'path': str(pdf),
                        'filename': pdf.name,
                        'stem': pdf.stem
                    })

    print(f"Found {len(after_papers)} after papers (excluding failed downloads)")
    print(f"Found {len(before_papers)} before papers")
    print(f"\n{'='*100}")
    print("POTENTIAL MATCHES - Please review and confirm")
    print(f"{'='*100}\n")

    matches = []
    match_id = 1

    for after in after_papers:
        after_title = normalize_text(after['paper_title'])
        after_authors = after['author_date_citation']
        after_first_author = extract_first_author(after_authors)

        candidates = []

        for before in before_papers:
            before_filename = before['stem']
            before_norm = normalize_text(before_filename)

            # Title similarity
            title_sim = difflib.SequenceMatcher(None, after_title, before_norm).ratio()

            # Author match
            author_match = False
            if after_first_author and after_first_author.lower() in before_norm:
                author_match = True

            # Overall score
            score = 0
            if author_match:
                score += 0.5
            score += title_sim * 0.5

            if score > 0.4:  # Potential match threshold
                candidates.append({
                    'before': before,
                    'score': score,
                    'title_sim': title_sim,
                    'author_match': author_match
                })

        # Sort by score
        candidates.sort(key=lambda x: x['score'], reverse=True)

        # Show top matches
        if candidates:
            best = candidates[0]
            if best['score'] > 0.5:  # Only show good matches
                print(f"[{match_id}] MATCH (score: {best['score']:.2f})")
                print(f"  AFTER:  {after['paper_title'][:80]}")
                print(f"          Authors: {after_authors[:60]}")
                print(f"          File: {after['filename'][:80]}")
                print(f"  BEFORE: {best['before']['filename']}")
                print(f"          Path: {best['before']['path']}")
                print(f"  Similarity: title={best['title_sim']:.2f}, author={'YES' if best['author_match'] else 'NO'}")

                # Show alternatives if any
                if len(candidates) > 1 and candidates[1]['score'] > 0.4:
                    print(f"  Alternative: {candidates[1]['before']['filename']} (score: {candidates[1]['score']:.2f})")

                print()

                matches.append({
                    'match_id': match_id,
                    'confidence': 'HIGH' if best['score'] > 0.7 else 'MEDIUM',
                    'after_title': after['paper_title'],
                    'after_authors': after_authors,
                    'after_file': after['filename'],
                    'before_file': best['before']['filename'],
                    'before_path': best['before']['path'],
                    'score': best['score']
                })

                match_id += 1

    # Save to CSV for easy review
    if matches:
        output_file = Path("potential_matches.csv")
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=matches[0].keys())
            writer.writeheader()
            writer.writerows(matches)

        print(f"\n{'='*100}")
        print(f"Found {len(matches)} potential matches")
        print(f"Saved to: {output_file}")
        print(f"\nPlease review and add 'confirmed' column with YES/NO for each match")
        print(f"{'='*100}")

if __name__ == "__main__":
    main()
