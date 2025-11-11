#!/usr/bin/env python3
"""
openalex_citations_from_bib.py

Given a .bib (or a plain text file with DOIs), query OpenAlex to find:
- per-DOI citation counts
- all citing works (papers that cite each DOI)
- tally of repeat citers (authors who cite multiple of your seed DOIs)

Outputs three CSVs in the chosen output directory.
Requires: requests, pandas, bibtexparser (optional but recommended)

Usage:
    python openalex_citations_from_bib.py --input path/to/export-data.bib --out out_dir
"""
import argparse, re, os, sys, time, urllib.parse, json
from collections import defaultdict, Counter
import requests
import pandas as pd

def extract_dois_from_text(text: str):
    pat = re.compile(r'(?:(?:doi\s*=\s*[{"]\s*)|(?:https?://)?doi\.org/)?(10\.\d{4,9}/[^\s"{}]+)', re.IGNORECASE)
    dois = []
    for m in pat.finditer(text):
        doi = m.group(1).lower().strip().rstrip('.,);]')
        dois.append(doi)
    return sorted(set(dois))

def load_dois(path: str):
    txt = open(path, "r", encoding="utf-8", errors="ignore").read()
    # Try bibtexparser if available to get explicit fields first
    try:
        import bibtexparser
        db = bibtexparser.loads(txt)
        fields = []
        for e in db.entries:
            if "doi" in e:
                fields.append(e["doi"])
        explicit = [d.strip().lower() for d in fields if isinstance(d, str) and d.strip()]
    except Exception:
        explicit = []
    found = extract_dois_from_text(txt)
    # union
    all_dois = sorted(set(explicit) | set(found))
    return all_dois

def oa_get(url, params=None, sleep=0.2):
    """GET with basic retry and polite rate-limiting."""
    tries = 0
    while True:
        tries += 1
        r = requests.get(url, params=params, timeout=30)
        if r.status_code == 200:
            return r.json()
        if r.status_code in (429, 500, 502, 503, 504) and tries < 6:
            time.sleep( min(2**tries * 0.2, 5) )
            continue
        r.raise_for_status()

def fetch_work_by_doi(doi: str):
    url = "https://api.openalex.org/works"
    data = oa_get(url, params={"filter": f"doi:{doi}"})
    if data.get("results"):
        return data["results"][0]
    return None

def fetch_all_citers(cited_by_api_url: str):
    citers = []
    cursor = "*"
    per_page = 200
    while True:
        data = oa_get(cited_by_api_url, params={"per-page": per_page, "cursor": cursor})
        citers.extend(data.get("results", []))
        cursor = data.get("meta", {}).get("next_cursor")
        if not cursor:
            break
    return citers

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to .bib or text file containing DOIs")
    ap.add_argument("--out", required=True, help="Output directory")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    dois = load_dois(args.input)
    if not dois:
        print("No DOIs found in input.", file=sys.stderr)
        sys.exit(1)

    works_rows = []
    citing_rows = []
    # For repeat-citer tally
    author_to_seeddois = defaultdict(set)
    author_to_citing_works = defaultdict(set)

    for i, doi in enumerate(dois, 1):
        print(f"[{i}/{len(dois)}] Fetching OpenAlex for DOI {doi} ...")
        work = fetch_work_by_doi(doi)
        if not work:
            works_rows.append({
                "seed_doi": doi, "openalex_id": None, "title": None,
                "cited_by_count": None, "status": "not_found"
            })
            continue

        seed_id = work["id"]
        title = work.get("title")
        cited_by_count = work.get("cited_by_count", 0)
        cb_url = work.get("cited_by_api_url")
        works_rows.append({
            "seed_doi": doi, "openalex_id": seed_id, "title": title,
            "cited_by_count": cited_by_count, "status": "ok"
        })

        if cb_url and cited_by_count:
            citers = fetch_all_citers(cb_url)
            for cw in citers:
                cw_id = cw.get("id")
                cw_doi = cw.get("doi")
                cw_title = cw.get("title")
                cw_year = cw.get("publication_year")
                authors = [a.get("author", {}).get("display_name") for a in cw.get("authorships", []) if a.get("author")]
                authors = [a for a in authors if a]
                citing_rows.append({
                    "seed_doi": doi,
                    "citing_openalex_id": cw_id,
                    "citing_doi": cw_doi,
                    "citing_title": cw_title,
                    "citing_year": cw_year,
                    "citing_authors": "; ".join(authors)
                })
                for a in authors:
                    author_to_seeddois[a].add(doi)
                    if cw_id:
                        author_to_citing_works[a].add(cw_id)

        # polite rate limit
        time.sleep(0.2)

    # Save per-work summary
    df_works = pd.DataFrame(works_rows)
    df_works.to_csv(os.path.join(args.out, "works_summary.csv"), index=False)

    # Save citing works
    df_citing = pd.DataFrame(citing_rows)
    if not df_citing.empty:
        df_citing.to_csv(os.path.join(args.out, "citing_works.csv"), index=False)

    # Repeat citers
    rows = []
    for author, seeds in author_to_seeddois.items():
        rows.append({
            "author": author,
            "n_seed_dois_cited": len(seeds),
            "n_citing_works": len(author_to_citing_works.get(author, set())),
            "seed_dois": "; ".join(sorted(seeds))
        })
    df_repeat = pd.DataFrame(rows).sort_values(["n_seed_dois_cited","n_citing_works","author"], ascending=[False, False, True])
    if not df_repeat.empty:
        df_repeat.to_csv(os.path.join(args.out, "repeat_citers.csv"), index=False)

    print("Done. Wrote:", os.path.join(args.out, "works_summary.csv"))
    if not df_citing.empty:
        print("       and:", os.path.join(args.out, "citing_works.csv"))
    if not df_repeat.empty:
        print("       and:", os.path.join(args.out, "repeat_citers.csv"))

if __name__ == "__main__":
    main()
