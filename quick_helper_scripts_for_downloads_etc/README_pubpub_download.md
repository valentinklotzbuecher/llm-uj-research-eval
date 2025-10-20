# PubPub Content Downloader for The Unjournal

This directory contains scripts for automatically downloading and organizing content from The Unjournal's PubPub site (https://unjournal.pubpub.org).

## Overview

The download system consists of:
- **`download_pubpub_content.py`**: Main script that downloads all evaluation content from PubPub
- **`organize_pubpub_files.py`**: Script to rename and organize downloaded files
- **`grabevalurlwork/unjournal_pubpub_urls_clean.csv`**: CSV file containing all PubPub URLs to download

## How It Works

### Download Script (`download_pubpub_content.py`)

The script downloads markdown content from PubPub using two methods:

1. **Direct Export Endpoint**: Attempts to download via `/download/markdown` endpoint (fastest and most reliable)
2. **HTML Scraping**: If direct download fails, scrapes HTML and converts to markdown using `html2text`

#### Features:
- **Resumable**: Uses state tracking to resume interrupted downloads
- **Rate Limited**: 1.5 second delay between requests to avoid overloading the server
- **Progress Tracking**: Detailed logging and manifest generation
- **Error Handling**: Gracefully handles failures and records them for review

#### Output:
- **Markdown files**: Saved to `../unjournal_evaluations/`
- **Metadata**: Saved to `pubpub_download_metadata/`
  - `manifest.json`: Complete record of all downloads with status
  - `state.json`: Resumable state for interrupted downloads

### File Organization Script (`organize_pubpub_files.py`)

This script:
- Renames files with non-meaningful slugs (e.g., `jq95bapl.md` → `evalsumdoesthesqueaky.md`)
- Moves template files to `../unjournal_evaluations/templates/`
- Moves blank/test files to `../unjournal_evaluations/templates/`
- Creates a mapping file documenting all renames

## Installation

### Prerequisites

1. Python 3.7 or higher
2. Virtual environment (recommended)

### Setup

```bash
# Navigate to the scripts directory
cd quick_helper_scripts_for_downloads_etc

# Activate the existing virtual environment
source ../.venv/bin/activate

# Install required packages (if not already installed)
pip install requests beautifulsoup4 html2text
```

## Usage

### Manual Download

```bash
# Activate virtual environment
source ../.venv/bin/activate

# Run the download script
python download_pubpub_content.py
```

### Automated Download (Cron)

The script is configured to run automatically every 2 months via cron:

```bash
# View the cron job
crontab -l

# Edit cron jobs
crontab -e
```

**Cron Schedule**: `0 0 1 */2 * cd /Users/yosemite/githubs/llm-uj-research-eval/quick_helper_scripts_for_downloads_etc && ../.venv/bin/python download_pubpub_content.py >> pubpub_download_metadata/cron.log 2>&1`

This runs on the 1st day of every 2nd month at midnight.

### File Organization

```bash
# Organize and rename downloaded files
python organize_pubpub_files.py
```

## File Naming Conventions

Downloaded files follow these patterns:

- `e1*.md`, `e2*.md`, `e3*.md` - Individual evaluations (Evaluation 1, 2, 3, etc.)
- `evalsum*.md` - Evaluation summaries
- `eval1*.md`, `eval2*.md`, `eval3*.md` - Older evaluation format
- `response*.md`, `author*.md` - Author responses to evaluations
- Other descriptive names based on paper titles or content

Template and blank files are moved to the `templates/` subdirectory.

## Configuration

Edit `download_pubpub_content.py` to modify:

```python
BASE_URL = "https://unjournal.pubpub.org"
INPUT_CSV = "grabevalurlwork/unjournal_pubpub_urls_clean.csv"
OUTPUT_DIR = "../unjournal_evaluations"
DELAY_BETWEEN_REQUESTS = 1.5  # seconds
```

## Troubleshooting

### Download Failures

Check `pubpub_download_metadata/manifest.json` for failed URLs. Common reasons:
- Login/authentication required
- Content not publicly accessible
- Missing export functionality
- Rate limiting

### Resume Interrupted Download

The script automatically resumes from where it left off. To force a re-download of a specific file, edit `pubpub_download_metadata/state.json` and remove the slug from the "completed" section.

### Logs

- **Console output**: Real-time progress during execution
- **Cron log**: `pubpub_download_metadata/cron.log` (for automated runs)

## Dependencies

- **requests**: HTTP library for downloading content
- **beautifulsoup4**: HTML parsing for scraping fallback
- **html2text**: Converts HTML to markdown

## License

This script is part of The Unjournal project evaluation data tools.

## Contributing

To add new URLs to download:
1. Update `grabevalurlwork/unjournal_pubpub_urls_clean.csv`
2. Run the download script - it will automatically detect and download new URLs

## Maintenance

### Monthly Tasks
- Review `manifest.json` for new failures
- Check cron logs for any issues
- Verify new content is properly categorized

### When PubPub Structure Changes
- Update selectors in `scrape_html_content()` function
- Test download with a sample URL
- Update this README if configuration changes
