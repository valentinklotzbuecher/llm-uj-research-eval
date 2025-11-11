#!/usr/bin/env python3
"""
augment_emails_from_publishers.py

Reads a citing_works.csv (from the OpenAlex script), attempts to find
lead/corresponding author email(s) by visiting the publisher landing page,
and fills missing titles from OpenAlex when possible.

Heuristics:
- Prefer mailto: links that appear near keywords like "corresponding author".
- Otherwise, collect any visible emails on the landing page.
- Avoid downloading PDFs (skip if Content-Type is application/pdf).
- Use DOI redirect (https://doi.org/DOI) first; if that fails, query OpenAlex for web_url.
- Writes a new CSV: coda_citing_table_with_emails.csv

Usage:
    python augment_emails_from_publishers.py \
        --citing /path/to/citing_works.csv \
        --out   /path/to/outdir
"""
import argparse, os, sys, re, time, json
from urllib.parse import quote
import requests
from bs4 import BeautifulSoup
import pandas as pd

USER_AGENT = "Unjournal-Email-Augment/2025 (contact: team@unjournal.org)"

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
NEARBY_KEYWORDS = re.compile(r"corresponding|correspondence|contact\s*author|author\s*for\s*correspondence", re.IGNORECASE)

def build_session():
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    sess = requests.Session()
    retries = Retry(
        total=6,
        backoff_factor=0.7,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
        raise_on_redirect=False,
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=20, pool_maxsize=40)
    sess.mount("https://", adapter)
    sess.mount("http://", adapter)
    sess.headers.update({"User-Agent": USER_AGENT})
    return sess

def get_candidate_urls(row, sess):
    urls = []
    doi = (row.get("citing_doi") or "").strip().lower()
    if doi:
        urls.append("https://doi.org/" + quote(doi, safe="/:"))
    # Fallback to OpenAlex work page to get best location url
    openalex_id = (row.get("citing_openalex_id") or "").strip()
    if openalex_id:
        try:
            r = sess.get(openalex_id, timeout=(15, 45))
            if r.status_code == 200:
                data = r.json()
                # prioritize primary location web_url
                loc = data.get("primary_location") or {}
                if loc and loc.get("source") and loc.get("source", {}).get("homepage_url"):
                    urls.append(loc["source"]["homepage_url"])
                if loc and loc.get("landing_page_url"):
                    urls.append(loc["landing_page_url"])
                # add other locations
                for l in data.get("locations", []) or []:
                    if l.get("landing_page_url"):
                        urls.append(l["landing_page_url"])
        except Exception:
            pass
    # Deduplicate, preserve order
    seen = set()
    uniq = []
    for u in urls:
        if u and u not in seen:
            seen.add(u); uniq.append(u)
    return uniq

def fetch_html(url, sess):
    try:
        r = sess.get(url, timeout=(15, 45), allow_redirects=True)
    except requests.exceptions.SSLError:
        time.sleep(1.0)
        r = sess.get(url, timeout=(15, 45), allow_redirects=True, verify=False)
    ct = r.headers.get("Content-Type", "").lower()
    if "pdf" in ct or r.url.lower().endswith(".pdf"):
        return None, r.url, ct
    if r.status_code != 200:
        return None, r.url, ct
    text = r.text
    return text, r.url, ct

def extract_emails_with_scores(html):
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    scored = []

    # 1) mailto links, scored
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.lower().startswith("mailto:"):
            email = href.split(":",1)[1].split("?")[0].strip()
            context = a.get_text(" ", strip=True) or ""
            # Look at nearby text
            block = a.parent.get_text(" ", strip=True) if a.parent else context
            score = 2
            if NEARBY_KEYWORDS.search(context) or NEARBY_KEYWORDS.search(block):
                score += 3
            scored.append((email, score, "mailto_link"))

    # 2) Any visible emails in text nodes
    text = soup.get_text(" ", strip=True)
    for m in EMAIL_RE.finditer(text):
        email = m.group(0)
        # Check small window around match for keywords
        start = max(0, m.start()-80); end = min(len(text), m.end()+80)
        window = text[start:end]
        score = 1 + (3 if NEARBY_KEYWORDS.search(window) else 0)
        scored.append((email, score, "text_scan"))

    # Deduplicate by email, keep max score & best source
    best = {}
    for email, score, src in scored:
        if email not in best or score > best[email][0]:
            best[email] = (score, src)
    out = [(email, s, src) for email, (s, src) in best.items()]
    # Sort by score desc then email
    out.sort(key=lambda t: (-t[1], t[0]))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--citing", required=True, help="Path to citing_works.csv from the OpenAlex script")
    ap.add_argument("--out", required=True, help="Output directory")
    ap.add_argument("--limit", type=int, default=None, help="Optional limit for quick tests")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    df = pd.read_csv(args.citing)

    # Normalize strings
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].fillna("").astype(str).str.strip()

    sess = build_session()

    rows_out = []
    for i, row in df.iterrows():
        if args.limit and i >= args.limit:
            break

        seed_doi = row.get("seed_doi","")
        seed_title = ""  # can be joined later if needed
        citing_id = row.get("citing_openalex_id","")
        citing_doi = row.get("citing_doi","")
        citing_title = row.get("citing_title","")
        citing_year = row.get("citing_year","")
        authors = row.get("citing_authors","")
        lead_author = authors.split(";")[0].strip() if authors else ""

        candidates = get_candidate_urls(row, sess)
        found_emails = []
        final_url = ""
        page_title = ""
        for url in candidates:
            html, final_url, ct = fetch_html(url, sess)
            if not html:
                continue
            # parse title
            try:
                soup = BeautifulSoup(html, "html.parser")
                if not citing_title:
                    t = soup.find("title")
                    if t and t.text:
                        page_title = t.text.strip()
                else:
                    page_title = ""
            except Exception:
                pass

            emails = extract_emails_with_scores(html)
            if emails:
                found_emails = emails
                break  # stop at first page with emails

        # Choose top 3 emails (most contexts have 1)
        top_emails = "; ".join([e for e,score,src in found_emails[:3]]) if found_emails else ""
        method = found_emails[0][2] if found_emails else ""
        confidence = found_emails[0][1] if found_emails else ""

        rows_out.append({
            "seed_doi": seed_doi,
            "citing_openalex_id": citing_id,
            "citing_doi": citing_doi,
            "citing_title": citing_title or page_title,
            "citing_year": citing_year,
            "lead_author": lead_author,
            "citing_authors": authors,
            "corresponding_email": top_emails,
            "email_confidence": confidence,
            "email_method": method,
            "email_source_url": final_url,
        })

        if (i+1) % 20 == 0:
            print(f"Processed {i+1} rows ...")
            pd.DataFrame(rows_out).to_csv(os.path.join(args.out, "coda_citing_table_with_emails.partial.csv"), index=False)

    out_path = os.path.join(args.out, "coda_citing_table_with_emails.csv")
    pd.DataFrame(rows_out).to_csv(out_path, index=False)
    print("Wrote:", out_path)

if __name__ == "__main__":
    main()
