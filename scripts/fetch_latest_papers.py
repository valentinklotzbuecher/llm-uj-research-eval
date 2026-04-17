#!/usr/bin/env python3
"""
Fetch latest versions of Unjournal-evaluated papers from NBER and arxiv.

Run from project root:
    conda run -n qpy311_arm python scripts/fetch_latest_papers.py

Outputs:
    data/latest_papers/*.pdf       (downloaded PDFs, git-ignored)
    data/paper_fetch_manifest.json (provenance manifest, committed)
"""

import csv
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).parent.parent
CSV_PATH = REPO_ROOT / "data" / "author_adjustment_manual.csv"
PAPERS_DIR = REPO_ROOT / "papers"
LATEST_DIR = REPO_ROOT / "data" / "latest_papers"
MANIFEST_PATH = REPO_ROOT / "data" / "paper_fetch_manifest.json"

LATEST_DIR.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "unjournal-research/1.0 (academic research; contact: unjournal.org)"
})


# ---------------------------------------------------------------------------
# DOI normalisation helpers
# ---------------------------------------------------------------------------

def normalize_doi(raw: str) -> str:
    """Strip URL prefix and whitespace from a DOI string."""
    if not raw:
        return ""
    d = raw.strip().replace(" ", "")
    d = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", d, flags=re.I)
    d = re.sub(r"^doig?\.org/", "", d, flags=re.I)
    return d


def nber_id(doi: str) -> str | None:
    """Return NBER working-paper number if DOI is an NBER WP, else None."""
    m = re.match(r"^10\.3386/w(\d+)$", normalize_doi(doi), re.I)
    return m.group(1) if m else None


def arxiv_id(doi: str) -> str | None:
    """Return arxiv ID if DOI is an arxiv DOI, else None."""
    m = re.search(r"arXiv\.(\d{4}\.\d+)", normalize_doi(doi), re.I)
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# Filename matching: CSV row → papers/ file
# ---------------------------------------------------------------------------

def first_author_last(authors_str: str) -> str:
    """Extract first author's last name from a comma-separated authors string."""
    if not authors_str:
        return ""
    first = authors_str.split(",")[0].strip()
    # Last name is last word
    return first.split()[-1].lower() if first else ""


def year_from_dates(*date_strs) -> str:
    """Extract a 4-digit year from the first non-empty date string."""
    for d in date_strs:
        if d:
            m = re.search(r"\b(20\d{2})\b", d)
            if m:
                return m.group(1)
    return ""


def find_before_pdf(last_name: str, year: str) -> Path | None:
    """Match first-author last name + year to a file in papers/.

    Uses word-boundary matching so 'bhat' does not match 'bhattacharya'.
    """
    candidates = list(PAPERS_DIR.glob("*.pdf"))
    # Normalize: remove accents, lowercase
    last_name_lc = last_name.lower()
    last_name_ascii = (last_name_lc
                       .replace("é", "e").replace("è", "e").replace("ê", "e")
                       .replace("ü", "u").replace("ö", "o").replace("ä", "a")
                       .replace("ñ", "n").replace("ç", "c"))

    def stem_matches(stem: str, lname: str) -> bool:
        """True if lname appears as a full token in stem (split on _ and -)."""
        tokens = re.split(r"[_\-\s]", stem.lower())
        return lname in tokens

    for name in [last_name_ascii, last_name_lc]:
        for p in candidates:
            stem = p.stem
            if stem_matches(stem, name) and (not year or year in stem):
                return p
    # Relax: ignore year
    for name in [last_name_ascii, last_name_lc]:
        for p in candidates:
            if stem_matches(p.stem, name):
                return p
    return None


# ---------------------------------------------------------------------------
# Downloading
# ---------------------------------------------------------------------------

def download_pdf(url: str, dest: Path) -> bool:
    """Download a PDF to dest; return True on success."""
    if dest.exists() and dest.stat().st_size > 10_000:
        print(f"  [cached] {dest.name}")
        return True
    try:
        r = SESSION.get(url, timeout=45, allow_redirects=True)
        r.raise_for_status()
        if "pdf" not in r.headers.get("Content-Type", "").lower() and len(r.content) < 5000:
            print(f"  [skip] unexpected content-type: {r.headers.get('Content-Type')}")
            return False
        dest.write_bytes(r.content)
        print(f"  [ok] {dest.name}  ({len(r.content)//1024} KB)")
        return True
    except Exception as e:
        print(f"  [error] {url}: {e}")
        return False


def nber_url(wp_id: str) -> str:
    return f"https://www.nber.org/system/files/working_papers/w{wp_id}/w{wp_id}.pdf"


def arxiv_url(ax_id: str) -> str:
    return f"https://arxiv.org/pdf/{ax_id}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    rows = []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Processing {len(rows)} papers from CSV…\n")

    manifest = {}
    today = date.today().isoformat()

    for row in rows:
        title = row.get("label_paper_title", "").strip()
        authors = row.get("authors", "").strip()
        doi_raw = row.get("doi", "").strip()
        adj_status = row.get("Adjusted_paper?", "").strip()
        deposit_after = row.get("deposit date > unjournal pub date", "").strip().lower()
        wp_date = row.get("working_paper_release_date", "").strip()
        uj_date = row.get("publication_date_unjournal", "").strip()

        if not title:
            continue

        last = first_author_last(authors)
        yr = year_from_dates(wp_date, uj_date)
        before_pdf = find_before_pdf(last, yr)

        # Build a stable key from first-author + abbreviated title
        title_slug = re.sub(r"[^\w]", "_", title[:40]).strip("_").lower()
        key = f"{last}_{title_slug}"[:60]

        entry = {
            "paper_title": title,
            "authors": authors,
            "doi": doi_raw,
            "adj_status": adj_status,
            "deposit_after_uj": deposit_after == "true",
            "before_pdf": str(before_pdf.relative_to(REPO_ROOT)) if before_pdf else None,
            "after_pdf": None,
            "fetch_status": "skipped",
            "fetch_reason": "",
            "fetch_date": today,
        }

        # Determine fetch strategy
        nid = nber_id(doi_raw)
        aid = arxiv_id(doi_raw)

        if nid:
            url = nber_url(nid)
            dest = LATEST_DIR / f"{key}.pdf"
            print(f"{title[:60]}")
            print(f"  NBER w{nid} → {dest.name}")
            ok = download_pdf(url, dest)
            entry["after_pdf"] = str(dest.relative_to(REPO_ROOT)) if ok else None
            entry["fetch_status"] = "success" if ok else "failed"
            entry["fetch_reason"] = f"NBER w{nid}"
            time.sleep(1.2)

        elif aid:
            url = arxiv_url(aid)
            dest = LATEST_DIR / f"{key}.pdf"
            print(f"{title[:60]}")
            print(f"  arxiv {aid} → {dest.name}")
            ok = download_pdf(url, dest)
            entry["after_pdf"] = str(dest.relative_to(REPO_ROOT)) if ok else None
            entry["fetch_status"] = "success" if ok else "failed"
            entry["fetch_reason"] = f"arxiv {aid}"
            time.sleep(1.0)

        else:
            entry["fetch_reason"] = "no NBER/arxiv DOI"

        manifest[key] = entry

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"\nManifest written to {MANIFEST_PATH}")

    n_ok = sum(1 for e in manifest.values() if e["fetch_status"] == "success")
    n_skip = sum(1 for e in manifest.values() if e["fetch_status"] == "skipped")
    n_fail = sum(1 for e in manifest.values() if e["fetch_status"] == "failed")
    print(f"Results: {n_ok} downloaded, {n_skip} skipped (no DOI), {n_fail} failed")


if __name__ == "__main__":
    main()
