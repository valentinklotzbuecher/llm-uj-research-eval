#!/usr/bin/env python3
"""
Download a batch of research links (preferring PDFs when available).


Usage:
pip install requests beautifulsoup4
  python download_research.py
  # (optional) customize the DOWNLOAD_DIR or the URLS list below

Requirements:
  pip install requests beautifulsoup4
"""

import os
import re
import sys
import time
import json
import logging
from urllib.parse import urljoin, urlparse
from typing import Optional, Tuple

import requests
from bs4 import BeautifulSoup

# ---------- Config ----------
DOWNLOAD_DIR = "downloads"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

# (name, url). You can edit names; they’ll be used for filenames.
URLS = [
    ("NBER_Working_Paper_w31728", "https://www.nber.org/papers/w31728"),
    ("A_Happy_Probability_Oxford_WRC", "https://wellbeing.hmc.ox.ac.uk/wp-content/uploads/2024/02/2401-WP-A-Happy-Probability-DOI.pdf"),
    ("Nature_HSSC_2024_article", "https://www.nature.com/articles/s41599-024-03229-5"),
    ("OUP_Book", "https://academic.oup.com/book/39348"),
    ("BostonU_OpenAccess_PDF", "https://open.bu.edu/server/api/core/bitstreams/12666acb-7311-4a94-9b1a-340b39d5705e/content"),
    ("WhiteRose_ePrints", "https://eprints.whiterose.ac.uk/id/eprint/99499/"),
    ("UK_GOV_Wellbeing_Appraisal_Background", "https://assets.publishing.service.gov.uk/media/60fa91c68fa8f50431ca80da/Wellbeing_guidance_for_appraisal_-_background_paper_reviewing_methods_and_approaches.pdf?utm_source=chatgpt.com"),
    ("Econstor_DP_13905", "https://www.econstor.eu/bitstream/10419/232657/1/dp13905.pdf"),
    ("IZA_DP_13166", "https://docs.iza.org/dp13166.pdf"),
    ("LSE_Frijters_Life_Satisfaction_Published", "https://eprints.lse.ac.uk/89398/1/Frijters_Life-satisfaction-Published.pdf"),
    ("LSE_Asaria_QALY_Health_Consumption", "https://eprints.lse.ac.uk/107065/2/Asaria_quality_adjusted_life_years_health_consumption_published.pdf"),
    ("LSE_CEP_Occasional_Paper_049", "https://cep.lse.ac.uk/pubs/download/occasional/op049.pdf"),
    ("Econstor_224090", "https://www.econstor.eu/bitstream/10419/224090/1/1727957334.pdf"),
    ("Nature_Human_Behaviour_2021", "https://www.nature.com/articles/s41562-021-01252-z"),
    # Note: “acquired by directly contacting Tessa Peasgood” has no public URL
]

# Skip list entries that aren’t public links:
SKIP_NOTES = [
    "acquired by directly contacting Tessa Peasgood"
]
# ---------- End Config ----------


def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def sanitize_filename(name: str) -> str:
    name = re.sub(r"[^\w\-.]+", "_", name.strip())
    name = re.sub(r"_+", "_", name)
    return name.strip("._")[:180] or "file"


def guess_extension_from_headers(headers) -> Optional[str]:
    ctype = headers.get("Content-Type", "").split(";")[0].strip().lower()
    if ctype == "application/pdf":
        return ".pdf"
    if ctype in {"text/html", "application/xhtml+xml"}:
        return ".html"
    return None


def is_pdf_url(url: str) -> bool:
    # Heuristic: if URL path ends with .pdf or has .pdf before query
    path = urlparse(url).path.lower()
    return path.endswith(".pdf") or ".pdf" in path


def fetch(url: str, stream: bool = True) -> requests.Response:
    # Some hosts are picky; allow redirects and set headers
    return requests.get(url, headers=HEADERS, allow_redirects=True, timeout=60, stream=stream)


def save_response_content(resp: requests.Response, out_path: str):
    chunk = 1024 * 64
    with open(out_path, "wb") as f:
        for part in resp.iter_content(chunk_size=chunk):
            if part:
                f.write(part)


def find_pdf_in_html(base_url: str, html: str) -> Optional[str]:
    soup = BeautifulSoup(html, "html.parser")

    # Look for <a href="...pdf"> and <link> tags with PDFs
    for tag in soup.find_all(["a", "link"]):
        href = tag.get("href")
        if not href:
            continue
        if ".pdf" in href.lower():
            return urljoin(base_url, href)

    # Try meta tags (og:pdf etc. — rare, but harmless)
    for meta in soup.find_all("meta"):
        for attr in ("content", "value"):
            val = meta.get(attr)
            if val and ".pdf" in val.lower():
                return urljoin(base_url, val)

    return None


def download_single(name: str, url: str) -> Tuple[str, str, str]:
    """
    Returns (status, saved_path, note)
    status: "ok", "html_saved", "skipped", or "error"
    """
    safe_name = sanitize_filename(name)

    try:
        # Quick path if url clearly looks like a PDF
        if is_pdf_url(url):
            r = fetch(url)
            r.raise_for_status()
            ext = guess_extension_from_headers(r.headers) or ".pdf"
            out = os.path.join(DOWNLOAD_DIR, f"{safe_name}{ext}")
            save_response_content(r, out)
            return ("ok", out, "downloaded direct PDF")

        # Otherwise, fetch landing page (or content)
        r = fetch(url, stream=False)
        r.raise_for_status()

        # If content-type is already PDF, save as PDF
        ext = guess_extension_from_headers(r.headers)
        if ext == ".pdf":
            out = os.path.join(DOWNLOAD_DIR, f"{safe_name}.pdf")
            # Need a fresh streamed request to write chunked
            r2 = fetch(url)
            r2.raise_for_status()
            save_response_content(r2, out)
            return ("ok", out, "downloaded as PDF (content-type)")

        # If HTML, try to find a PDF link inside
        text = r.text
        if ext == ".html" or "text/html" in r.headers.get("Content-Type", "").lower() or "<html" in text.lower():
            pdf_link = find_pdf_in_html(r.url, text)
            if pdf_link:
                rpdf = fetch(pdf_link)
                rpdf.raise_for_status()
                pdf_ext = guess_extension_from_headers(rpdf.headers) or ".pdf"
                out = os.path.join(DOWNLOAD_DIR, f"{safe_name}{pdf_ext}")
                save_response_content(rpdf, out)
                return ("ok", out, f"found PDF in page: {pdf_link}")

            # No PDF found: save HTML for reference
            out = os.path.join(DOWNLOAD_DIR, f"{safe_name}.html")
            with open(out, "w", encoding="utf-8") as f:
                f.write(text)
            return ("html_saved", out, "no PDF found; saved landing page HTML")

        # Fallback: unknown type — just save bytes with best-guess extension
        guessed = ext or ""
        if not guessed:
            # Try infer from URL path
            guessed = ".pdf" if is_pdf_url(r.url) else ".bin"
        out = os.path.join(DOWNLOAD_DIR, f"{safe_name}{guessed}")
        # Need content bytes; if stream=False, r.content is present
        with open(out, "wb") as f:
            f.write(r.content)
        note = "saved content (unknown type)"
        return ("ok", out, note)

    except requests.HTTPError as e:
        return ("error", "", f"HTTP {e.response.status_code} for {url}")
    except Exception as e:
        return ("error", "", f"{type(e).__name__}: {e}")


def main():
    ensure_dir(DOWNLOAD_DIR)

    to_download = [(n, u) for (n, u) in URLS]
    results = []

    print(f"Downloading {len(to_download)} items into ./{DOWNLOAD_DIR}\n")

    for idx, (name, url) in enumerate(to_download, 1):
        print(f"[{idx}/{len(to_download)}] {name} -> {url}")
        status, path, note = download_single(name, url)
        results.append({
            "name": name,
            "url": url,
            "status": status,
            "saved_path": path,
            "note": note
        })
        print(f"   -> {status}: {note}{' | ' + path if path else ''}\n")
        # Be polite to servers
        time.sleep(1.0)

    # Reminder for the non-public item:
    results.append({
        "name": "Peasgood_item",
        "url": None,
        "status": "skipped",
        "saved_path": "",
        "note": "No public URL. Acquire by directly contacting Tessa Peasgood."
    })

    # Write a machine-readable log
    log_path = os.path.join(DOWNLOAD_DIR, "download_log.json")
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    # Write a human-readable summary
    summary = []
    for r in results:
        summary.append(f"- {r['name']}: {r['status']} — {r['note']}" + (f" — {r['saved_path']}" if r['saved_path'] else ""))
    summary_path = os.path.join(DOWNLOAD_DIR, "download_SUMMARY.txt")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write("\n".join(summary))

    print("\nDone.")
    print(f"Summary: {summary_path}")
    print(f"Log:     {log_path}")


if __name__ == "__main__":
    # Minimal logging setup (optional)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)

