#!/usr/bin/env python3
"""
Download papers from Coda table where deposit date > unjournal pub date.
Creates a metadata CSV and saves PDFs to latest_papers_post_UJ directory.
"""

import os
import sys
import json
import csv
import hashlib
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import time

# Configuration
CODA_API_KEY_FILE = "key/coda_key.txt"
CODA_DOC_ID = "dIEzDONWdb"  # From the URL
# Try the "research" table from "All evaluations (filterable)" page
CODA_TABLE_ID = "grid-sync-1054-Table-dynamic-ac55549d6df3bbbead8dd779fcad2c0ac3435ec9abfec7a17ef04df988e27cd4"

OUTPUT_DIR = Path("latest_papers_post_UJ")
METADATA_FILE = OUTPUT_DIR / "metadata.csv"
DOWNLOAD_LOG = Path("quick_helper_scripts_for_downloads_etc") / "download_log.txt"

# Metadata fields to capture
METADATA_FIELDS = [
    "paper_title",
    "author_date_citation",
    "doi",
    "doi_deposit_date",
    "publication_date_unjournal",
    "journal_publication_title",
    "download_date",
    "filename"
]


def log(message: str):
    """Log message to console and file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_message = f"[{timestamp}] {message}"
    print(log_message)
    with open(DOWNLOAD_LOG, "a") as f:
        f.write(log_message + "\n")


def load_coda_api_key() -> str:
    """Load Coda API key from file."""
    key_path = Path(CODA_API_KEY_FILE)
    if not key_path.exists():
        raise FileNotFoundError(
            f"Coda API key not found at {CODA_API_KEY_FILE}. "
            "Please create this file with your Coda API token."
        )
    return key_path.read_text().strip()


def get_coda_table_rows(api_key: str, doc_id: str, table_id: str) -> List[Dict]:
    """Fetch all rows from a Coda table."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    base_url = f"https://coda.io/apis/v1/docs/{doc_id}/tables/{table_id}/rows"
    all_rows = []
    page_token = None

    while True:
        params = {"useColumnNames": "true", "limit": 100}
        if page_token:
            params["pageToken"] = page_token

        log(f"Fetching rows from Coda API (page_token: {page_token})...")
        response = requests.get(base_url, headers=headers, params=params)

        if response.status_code != 200:
            log(f"Error fetching Coda data: {response.status_code}")
            log(f"Response: {response.text}")
            response.raise_for_status()

        data = response.json()
        rows = data.get("items", [])
        all_rows.extend(rows)

        log(f"Fetched {len(rows)} rows (total so far: {len(all_rows)})")

        # Check if there are more pages
        page_token = data.get("nextPageToken")
        if not page_token:
            break

        time.sleep(0.5)  # Rate limiting

    log(f"Total rows fetched: {len(all_rows)}")
    return all_rows


def extract_row_value(row: Dict, column_name: str) -> Optional[str]:
    """Extract value from a Coda row by column name."""
    values = row.get("values", {})

    # Try exact match first
    if column_name in values:
        value = values[column_name]
        if isinstance(value, dict):
            return value.get("name") or value.get("value") or str(value)
        elif isinstance(value, list):
            # Handle list values (like authors)
            return ", ".join(str(v) for v in value if v)
        return str(value) if value is not None else None

    # Try case-insensitive match
    for key, value in values.items():
        if key.lower() == column_name.lower():
            if isinstance(value, dict):
                return value.get("name") or value.get("value") or str(value)
            elif isinstance(value, list):
                return ", ".join(str(v) for v in value if v)
            return str(value) if value is not None else None

    return None


def is_checkbox_checked(row: Dict, column_name: str) -> bool:
    """Check if a checkbox column is checked."""
    value = extract_row_value(row, column_name)
    if value is None:
        return False
    # Coda checkboxes typically return "true" or True
    return value.lower() == "true" if isinstance(value, str) else bool(value)


def convert_to_direct_pdf_url(url: str) -> str:
    """
    Convert various research repository URLs to direct PDF download links.
    """
    if not url:
        return url

    url = url.strip()

    # NBER working papers
    if "nber.org/papers/" in url:
        # Extract paper number from URLs like https://www.nber.org/papers/w32093
        paper_num = url.split("/papers/")[1].strip("/")
        return f"https://www.nber.org/system/files/working_papers/{paper_num}/{paper_num}.pdf"

    # ArXiv preprints
    if "arxiv.org/abs/" in url:
        # Convert https://arxiv.org/abs/2104.09645v2 to https://arxiv.org/pdf/2104.09645v2.pdf
        arxiv_id = url.split("/abs/")[1].strip("/")
        return f"https://arxiv.org/pdf/{arxiv_id}.pdf"

    # OSF preprints
    if "osf.io/preprints/" in url:
        # Convert https://osf.io/preprints/socarxiv/s6gwu/ to download URL
        # Extract the preprint ID (last part of URL)
        parts = url.rstrip("/").split("/")
        preprint_id = parts[-1]
        return f"https://osf.io/download/{preprint_id}/"

    # Dropbox links - change dl=0 to dl=1 for direct download
    if "dropbox.com" in url:
        if "dl=0" in url:
            url = url.replace("dl=0", "dl=1")
        elif "dl=" not in url:
            url += "&dl=1" if "?" in url else "?dl=1"
        return url

    # AEA (American Economic Association)
    if "aeaweb.org/articles" in url and "id=" in url:
        # Example: https://www.aeaweb.org/articles?id=10.1257/aeri.20210612
        # becomes: https://pubs.aeaweb.org/doi/pdfplus/10.1257/aeri.20210612
        doi = url.split("id=")[1].split("&")[0]
        return f"https://pubs.aeaweb.org/doi/pdfplus/{doi}"

    # SSRN papers
    if "papers.ssrn.com/sol3/papers.cfm?" in url and "abstract_id=" in url:
        # Example: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4614212
        abstract_id = url.split("abstract_id=")[1].split("&")[0]
        return f"https://papers.ssrn.com/sol3/Delivery.cfm?abstractid={abstract_id}"

    # Dropbox folders - these won't work as-is
    if "dropbox.com" in url and "/fo/" in url:
        log("Warning: Dropbox folder link, not a direct file. Manual download needed.")
        return url

    # ResearchGate - typically blocks automated downloads
    if "researchgate.net" in url:
        log("Warning: ResearchGate links typically require manual download")
        return url

    # Nature articles - require subscription
    if "nature.com/articles/" in url:
        log("Warning: Nature articles typically require subscription access")
        return url

    return url


def resolve_doi_to_pdf_url(doi: str) -> Optional[str]:
    """
    Attempt to resolve a DOI to a PDF download URL.
    Uses content negotiation and CrossRef API.
    """
    if not doi:
        return None

    # Clean DOI
    doi = doi.strip()
    if doi.startswith("http"):
        # Extract DOI from URL
        if "doi.org/" in doi:
            doi = doi.split("doi.org/")[1]

    # Try CrossRef API to get metadata including PDF links
    try:
        crossref_url = f"https://api.crossref.org/works/{doi}"
        response = requests.get(crossref_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            message = data.get("message", {})

            # Check for PDF link in the message
            links = message.get("link", [])
            for link in links:
                if link.get("content-type") == "application/pdf":
                    return link.get("URL")

            # Try the primary URL with content negotiation
            url = message.get("URL")
            if url:
                return url
    except Exception as e:
        log(f"CrossRef API error for {doi}: {e}")

    # Fallback to doi.org
    return f"https://doi.org/{doi}"


def download_pdf(url: str, output_path: Path, doi: str) -> bool:
    """
    Download a PDF from a URL.
    Validates that the downloaded content is actually a PDF.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "application/pdf,*/*"
    }

    try:
        log(f"Attempting to download from: {url}")
        response = requests.get(url, headers=headers, timeout=30, allow_redirects=True)

        if response.status_code == 200:
            content = response.content

            # Validate that this is actually a PDF (PDFs start with %PDF)
            if content[:4] != b'%PDF':
                log(f"Downloaded content is not a PDF (first 4 bytes: {content[:4]})")
                log(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")
                return False

            # Save the PDF
            output_path.write_bytes(content)
            file_size = len(content)
            log(f"Downloaded valid PDF ({file_size} bytes) to {output_path.name}")
            return True
        else:
            log(f"Download failed with status {response.status_code}")
            return False

    except Exception as e:
        log(f"Error downloading {url}: {e}")
        return False


def sanitize_filename(text: str) -> str:
    """Create a safe filename from text."""
    if not text:
        return "unknown"

    # Remove or replace invalid characters
    safe_chars = []
    for char in text:
        if char.isalnum() or char in [" ", "-", "_"]:
            safe_chars.append(char)
        elif char in [":", "/", "\\"]:
            safe_chars.append("-")

    filename = "".join(safe_chars).strip()
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]

    return filename if filename else "unknown"


def main():
    """Main execution function."""
    log("=" * 60)
    log("Starting paper download process")
    log("=" * 60)

    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Load API key
    try:
        api_key = load_coda_api_key()
        log("Coda API key loaded successfully")
    except FileNotFoundError as e:
        log(f"ERROR: {e}")
        sys.exit(1)

    # Fetch table data
    try:
        rows = get_coda_table_rows(api_key, CODA_DOC_ID, CODA_TABLE_ID)
    except Exception as e:
        log(f"ERROR fetching Coda table: {e}")
        sys.exit(1)

    if not rows:
        log("No rows found in table")
        return

    # Debug: print first row structure
    if rows:
        log(f"First row columns: {list(rows[0].get('values', {}).keys())}")

    # NOTE: The "deposit date > unjournal pub date" column is not available via API
    # from the public synced table (it's a formula column).
    # For now, we'll download ALL papers from the research table.

    filtered_rows = rows
    log(f"Processing all {len(filtered_rows)} papers from the research table")

    # Process each paper
    metadata_records = []

    for i, row in enumerate(filtered_rows, 1):
        log(f"\n--- Processing paper {i}/{len(filtered_rows)} ---")

        # Extract metadata using exact column names from Coda table
        paper_title = (
            extract_row_value(row, "label_paper_title") or
            extract_row_value(row, "Row") or
            "Unknown"
        )

        authors = extract_row_value(row, "authors") or ""

        # Create author-date citation from authors and date if available
        pub_date_uj = extract_row_value(row, "publication_date_unjournal") or ""
        year = ""
        if pub_date_uj:
            try:
                year = pub_date_uj.split("-")[0] if "-" in pub_date_uj else pub_date_uj[:4]
            except:
                pass

        # Simple author-date format: "FirstAuthor et al. (Year)"
        first_author = authors.split(",")[0] if authors else ""
        author_date = f"{first_author} et al. ({year})" if first_author and year else authors

        journal_title = extract_row_value(row, "Journal publication title") or ""

        # Get research_url (this IS available in the API)
        research_url = extract_row_value(row, "Research url") or ""

        # Get publication status
        pub_status = extract_row_value(row, "Publication status public") or ""

        log(f"Paper: {paper_title}")
        log(f"Research URL: {research_url}")
        log(f"Publication status: {pub_status}")

        # Use research_url for download
        download_url = research_url

        if not download_url:
            log("WARNING: No research URL found, skipping")
            continue

        # Generate filename
        safe_title = sanitize_filename(paper_title)
        safe_author = sanitize_filename(author_date)
        base_filename = f"{safe_author}_{safe_title}" if safe_author else safe_title

        # Create unique filename with hash if needed
        filename = f"{base_filename}.pdf"
        output_path = OUTPUT_DIR / filename

        # Check if already downloaded and is valid PDF
        skip_download = False
        if output_path.exists():
            # Check if existing file is a valid PDF
            try:
                with open(output_path, 'rb') as f:
                    if f.read(4) == b'%PDF':
                        log(f"Valid PDF already exists: {filename}")
                        skip_download = True
                    else:
                        log(f"Existing file is not a valid PDF, will re-download")
                        output_path.unlink()  # Delete corrupted file
            except:
                pass

        if not skip_download:
            # Try to download from research_url
            if research_url:
                # Convert URL to direct PDF link
                pdf_url = convert_to_direct_pdf_url(research_url)
                log(f"Converted URL: {pdf_url}")

                success = download_pdf(pdf_url, output_path, research_url)
                if not success:
                    log(f"Could not download valid PDF from: {pdf_url}")
                    filename = f"FAILED_{filename}"
            else:
                log(f"No URL available for download")
                filename = f"NO_URL_{filename}"

        # Record metadata (with available fields only)
        metadata_records.append({
            "paper_title": paper_title,
            "author_date_citation": author_date,
            "doi": "",  # Not available via API
            "doi_deposit_date": "",  # Not available via API
            "publication_date_unjournal": pub_date_uj,
            "journal_publication_title": journal_title,
            "download_date": datetime.now().strftime("%Y-%m-%d"),
            "filename": filename
        })

    # Write metadata CSV
    if metadata_records:
        log(f"\nWriting metadata to {METADATA_FILE}")
        with open(METADATA_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=METADATA_FIELDS)
            writer.writeheader()
            writer.writerows(metadata_records)
        log(f"Metadata saved with {len(metadata_records)} records")

    log("\n" + "=" * 60)
    log(f"Download process completed. Processed {len(metadata_records)} papers.")
    log("=" * 60)


if __name__ == "__main__":
    main()
