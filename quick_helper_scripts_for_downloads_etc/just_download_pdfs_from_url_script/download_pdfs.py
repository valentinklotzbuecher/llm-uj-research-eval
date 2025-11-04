
import argparse
import csv
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse, urlunparse

import requests

# -------- Helpers --------
def normalize_url(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\s+", "", s)  # remove any stray spaces
    # If bare DOI (starts with 10.), prefix with https://doi.org/
    if s.startswith("10."):
        s = "https://doi.org/" + s
    # If missing scheme but starts with doi.org/, add https://
    if s.lower().startswith("doi.org/"):
        s = "https://" + s
    # If given without scheme but with domain
    if not re.match(r"^https?://", s):
        s = "https://" + s

    # Clean double slashes (except after scheme)
    parts = urlparse(s)
    path = re.sub(r"/{2,}", "/", parts.path)
    return urlunparse((parts.scheme, parts.netloc, path, parts.params, parts.query, parts.fragment))

def guess_filename_from_response(r: requests.Response, fallback_slug: str) -> str:
    # 1) Content-Disposition header
    cd = r.headers.get("Content-Disposition", "")
    m = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', cd, flags=re.I)
    if m:
        name = m.group(1)
        # Some servers encode spaces as %20
        name = requests.utils.unquote(name)
        if not name.lower().endswith(".pdf"):
            name += ".pdf"
        return name

    # 2) URL path
    path_name = Path(urlparse(r.url).path).name
    if path_name and path_name.lower().endswith(".pdf"):
        return path_name

    # 3) Fallback to slug + .pdf
    if not fallback_slug.lower().endswith(".pdf"):
        fallback_slug += ".pdf"
    return fallback_slug

def to_slug(u: str) -> str:
    # Use DOI or last path segment as a readable slug
    parsed = urlparse(u)
    if parsed.netloc.lower() == "doi.org":
        slug = parsed.path.strip("/").replace("/", "_")
        return f"doi_{slug}" if slug else "doi_document"
    last = Path(parsed.path).name or parsed.netloc
    last = re.sub(r"[^A-Za-z0-9._-]+", "_", last)
    return last or "document"

def is_pdf_response(r: requests.Response) -> bool:
    ctype = (r.headers.get("Content-Type") or "").lower()
    if "application/pdf" in ctype:
        return True
    # Some servers mislabel but provide .pdf path
    if urlparse(r.url).path.lower().endswith(".pdf"):
        return True
    return False

def download_one(session: requests.Session, url: str, outdir: Path, timeout: int = 45) -> dict:
    norm = normalize_url(url)
    slug = to_slug(norm)
    headers = {
        "Accept": "application/pdf, application/*;q=0.9, */*;q=0.8",
        "User-Agent": "Unjournal-PDF-Downloader/1.0 (+https://unjournal.org)",
    }
    try:
        # First try to directly negotiate PDF via Accept header
        r = session.get(norm, headers=headers, allow_redirects=True, stream=True, timeout=timeout)
        # Some DOI resolvers send HTML first; follow redirects are already handled. Check if it's a PDF.
        if not is_pdf_response(r):
            # Heuristic: sometimes landing page has a direct pdf link in the final URL with .pdf query or redirect.
            # We won't parse HTML here; we just mark as non-pdf.
            return {"input": url, "normalized_url": norm, "status": "no-pdf", "saved_path": "", "http_status": r.status_code}

        fname = guess_filename_from_response(r, slug)
        outpath = outdir / fname
        outpath.parent.mkdir(parents=True, exist_ok=True)
        with open(outpath, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 64):
                if chunk:
                    f.write(chunk)
        return {"input": url, "normalized_url": norm, "status": "ok", "saved_path": str(outpath), "http_status": r.status_code}
    except requests.exceptions.RequestException as e:
        return {"input": url, "normalized_url": norm, "status": "error", "saved_path": "", "http_status": getattr(e, 'response', None).status_code if hasattr(e, 'response') and e.response else "" , "error": str(e)}
    except Exception as e:
        return {"input": url, "normalized_url": norm, "status": "error", "saved_path": "", "http_status": "", "error": str(e)}

def main():
    ap = argparse.ArgumentParser(description="Download PDFs from a list of DOI/URL entries, skipping failures.")
    ap.add_argument("-i", "--input", type=str, default="urls.txt", help="Text file with one DOI/URL per line")
    ap.add_argument("-o", "--outdir", type=str, default="downloads", help="Directory to save PDFs")
    ap.add_argument("--timeout", type=int, default=45, help="Per-request timeout (seconds)")
    ap.add_argument("--retries", type=int, default=2, help="Number of retries on network errors")
    args = ap.parse_args()

    in_path = Path(args.input)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if not in_path.exists():
        print(f"Input file not found: {in_path}", file=sys.stderr)
        sys.exit(2)

    urls = [line.strip() for line in in_path.read_text().splitlines() if line.strip() and not line.strip().startswith("#")]
    results = []

    with requests.Session() as sess:
        adapter = requests.adapters.HTTPAdapter(max_retries=args.retries)
        sess.mount("http://", adapter)
        sess.mount("https://", adapter)

        for u in urls:
            res = download_one(sess, u, outdir, timeout=args.timeout)
            results.append(res)
            status = res.get("status")
            saved = res.get("saved_path", "")
            http_status = res.get("http_status", "")
            print(f"[{status}] {u}  -> {saved or http_status}")

    # Write a CSV report
    csv_path = outdir / "download_report.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["input", "normalized_url", "status", "saved_path", "http_status", "error"])
        w.writeheader()
        for r in results:
            if "error" not in r:
                r["error"] = ""
            w.writerow(r)

    # Summary
    ok = sum(1 for r in results if r["status"] == "ok")
    no_pdf = sum(1 for r in results if r["status"] == "no-pdf")
    errs = sum(1 for r in results if r["status"] == "error")
    print(f"\nDone. Saved {ok} PDF(s); {no_pdf} had no-direct-PDF; {errs} error(s).")
    print(f"Report: {csv_path}")

if __name__ == "__main__":
    main()
