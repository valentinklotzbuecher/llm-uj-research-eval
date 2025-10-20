#!/usr/bin/env python3
"""
Download all content from unjournal.pubpub.org in markdown format.

This script:
1. Reads URLs from the CSV file
2. For each URL, tries multiple methods to get markdown content:
   - Direct export endpoint (if available)
   - HTML scraping and conversion to markdown
   - Selenium/Playwright for download button clicking (fallback)
3. Saves each pub's content as a markdown file
4. Creates a manifest of successfully downloaded content
"""

import csv
import json
import os
import re
import time
from pathlib import Path
from typing import Optional, Dict, List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import html2text

# Configuration
BASE_URL = "https://unjournal.pubpub.org"
INPUT_CSV = "grabevalurlwork/unjournal_pubpub_urls_clean.csv"
OUTPUT_DIR = "../unjournal_evaluations"  # Save markdown files to the main evaluations folder
MANIFEST_FILE = "manifest.json"
STATE_FILE = "state.json"
DELAY_BETWEEN_REQUESTS = 1.5  # seconds

# Create output directory
OUTPUT_PATH = Path(__file__).parent / OUTPUT_DIR
OUTPUT_PATH.mkdir(exist_ok=True)

# Also create metadata directory for manifest and state files
METADATA_DIR = Path(__file__).parent / "pubpub_download_metadata"
METADATA_DIR.mkdir(exist_ok=True)


def extract_slug_from_url(url: str) -> str:
    """Extract the pub slug from a PubPub URL."""
    # Handle URLs like https://unjournal.pubpub.org/pub/e1agisafety
    match = re.search(r'/pub/([^/?#]+)', url)
    if match:
        return match.group(1)
    # Fallback: use the last part of the path
    return urlparse(url).path.split('/')[-1]


def clean_url(url: str) -> Optional[str]:
    """Clean and validate URL, removing any JSON fragments."""
    # Remove any JSON/quoted content after the URL
    url = url.split('"')[0].strip()
    url = url.split('&quot;')[0].strip()

    if url.startswith('http') and '/pub/' in url:
        return url
    return None


def load_urls_from_csv(csv_path: Path) -> List[str]:
    """Load and clean URLs from the CSV file."""
    urls = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if 'url' in row:
                url = clean_url(row['url'])
                if url:
                    urls.append(url)

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)

    return unique_urls


def try_direct_export(url: str, slug: str) -> Optional[str]:
    """Try to download content via direct export endpoint."""
    # PubPub might have export endpoints like:
    # /pub/SLUG/download/markdown
    # /pub/SLUG/export/md
    # Let's try a few possibilities
    export_urls = [
        f"{url}/download/markdown",
        f"{url}/export/markdown",
        f"{url}/download/md",
        f"{url}.md",
        f"{url}/export"
    ]

    for export_url in export_urls:
        try:
            response = requests.get(export_url, timeout=30, allow_redirects=True)
            if response.status_code == 200 and len(response.text) > 100:
                content_type = response.headers.get('content-type', '').lower()
                if 'markdown' in content_type or 'text/plain' in content_type:
                    print(f"  ✓ Downloaded via direct export: {export_url}")
                    return response.text
        except Exception as e:
            continue

    return None


def scrape_html_content(url: str, slug: str) -> Optional[str]:
    """Scrape the HTML content and convert to markdown."""
    try:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Try to find the main content area
        # PubPub typically uses specific classes or IDs for content
        content_area = None

        # Try various selectors that might contain the main content
        selectors = [
            'article',
            '.pub-body-component',
            '.pub-body',
            '[data-node-type="doc"]',
            '.editor-content',
            'main'
        ]

        for selector in selectors:
            content_area = soup.select_one(selector)
            if content_area:
                break

        if not content_area:
            # Fallback: try to find the largest text block
            content_area = soup.find('body')

        if content_area:
            # Convert HTML to markdown
            h2t = html2text.HTML2Text()
            h2t.ignore_links = False
            h2t.ignore_images = False
            h2t.body_width = 0  # Don't wrap lines

            markdown = h2t.handle(str(content_area))

            # Add metadata at the top
            title = soup.find('title')
            if title:
                markdown = f"# {title.get_text().strip()}\n\nSource: {url}\n\n---\n\n{markdown}"

            print(f"  ✓ Scraped HTML and converted to markdown ({len(markdown)} chars)")
            return markdown

    except Exception as e:
        print(f"  ✗ Error scraping HTML: {e}")
        return None


def download_pub_content(url: str, slug: str) -> Optional[str]:
    """Try multiple methods to download content from a PubPub URL."""
    print(f"\nProcessing: {slug}")
    print(f"  URL: {url}")

    # Method 1: Try direct export endpoint
    content = try_direct_export(url, slug)
    if content:
        return content

    # Method 2: Scrape HTML and convert to markdown
    content = scrape_html_content(url, slug)
    if content:
        return content

    print(f"  ✗ Failed to download content")
    return None


def load_state() -> Dict:
    """Load the state file to resume from previous runs."""
    state_path = METADATA_DIR / STATE_FILE
    if state_path.exists():
        with open(state_path, 'r') as f:
            return json.load(f)
    return {"completed": {}, "failed": {}}


def save_state(state: Dict):
    """Save the current state."""
    state_path = METADATA_DIR / STATE_FILE
    with open(state_path, 'w') as f:
        json.dump(state, f, indent=2)


def save_manifest(manifest: List[Dict]):
    """Save the manifest of downloaded files."""
    manifest_path = METADATA_DIR / MANIFEST_FILE
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)


def main():
    """Main function to download all PubPub content."""
    print("PubPub Content Downloader")
    print("=" * 50)

    # Load URLs
    csv_path = Path(__file__).parent / INPUT_CSV
    if not csv_path.exists():
        print(f"Error: CSV file not found at {csv_path}")
        return

    urls = load_urls_from_csv(csv_path)
    print(f"\nFound {len(urls)} unique URLs to process")

    # Load state
    state = load_state()
    manifest = []

    # Process each URL
    success_count = 0
    failed_count = 0
    skipped_count = 0

    for i, url in enumerate(urls, 1):
        slug = extract_slug_from_url(url)

        # Skip if already completed
        if slug in state["completed"]:
            print(f"\n[{i}/{len(urls)}] Skipping {slug} (already completed)")
            skipped_count += 1
            continue

        print(f"\n[{i}/{len(urls)}] Processing: {slug}")

        try:
            # Download content
            content = download_pub_content(url, slug)

            if content:
                # Save to file
                output_file = OUTPUT_PATH / f"{slug}.md"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(content)

                # Update state and manifest
                state["completed"][slug] = {
                    "url": url,
                    "file": str(output_file),
                    "size": len(content),
                    "timestamp": time.time()
                }
                if slug in state["failed"]:
                    del state["failed"][slug]

                manifest.append({
                    "slug": slug,
                    "url": url,
                    "file": f"{slug}.md",
                    "size": len(content),
                    "status": "success"
                })

                success_count += 1
                print(f"  ✓ Saved to {output_file}")
            else:
                # Mark as failed
                state["failed"][slug] = {
                    "url": url,
                    "error": "Failed to download content",
                    "timestamp": time.time()
                }
                manifest.append({
                    "slug": slug,
                    "url": url,
                    "status": "failed"
                })
                failed_count += 1

            # Save state after each URL
            save_state(state)
            save_manifest(manifest)

            # Rate limiting
            time.sleep(DELAY_BETWEEN_REQUESTS)

        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            state["failed"][slug] = {
                "url": url,
                "error": str(e),
                "timestamp": time.time()
            }
            failed_count += 1
            save_state(state)

    # Print summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total URLs: {len(urls)}")
    print(f"Successful: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"Skipped (already completed): {skipped_count}")
    print(f"\nMarkdown files directory: {OUTPUT_PATH}")
    print(f"Metadata directory: {METADATA_DIR}")
    print(f"Manifest: {METADATA_DIR / MANIFEST_FILE}")


if __name__ == "__main__":
    main()
