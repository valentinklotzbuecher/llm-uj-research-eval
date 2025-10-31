# Weekly Paper Download Setup Instructions

This directory contains scripts to automatically download papers from the Unjournal Coda table where the deposit date is after the Unjournal publication date.

## Prerequisites

1. **Coda API Key**: You need a Coda API token to access the table data.

### Getting a Coda API Key

1. Go to https://coda.io/account
2. Navigate to "API Settings" or "Account Settings"
3. Generate a new API token
4. Copy the token

### Setting up the API Key

Create the key file:

```bash
mkdir -p key
echo "YOUR_CODA_API_TOKEN_HERE" > key/coda_key.txt
```

Make sure this file is git-ignored (already configured in `.gitignore`).

## Testing the Download Script

First, test the download script manually:

```bash
# Activate the conda environment
conda activate qpy311

# Run the download script
python quick_helper_scripts_for_downloads_etc/download_post_uj_papers.py
```

This will:
- Fetch all rows from the Coda table
- Filter for papers where "deposit date > unjournal pub date" is checked
- Download PDFs using DOI resolution
- Create a `latest_papers_post_UJ/` directory with:
  - Downloaded PDF files
  - `metadata.csv` with paper information

## Setting up the Weekly Cron Job

### Step 1: Make the wrapper script executable

```bash
chmod +x quick_helper_scripts_for_downloads_etc/weekly_paper_download.sh
```

### Step 2: Test the wrapper script

```bash
./quick_helper_scripts_for_downloads_etc/weekly_paper_download.sh
```

### Step 3: Add to crontab

Open your crontab:

```bash
crontab -e
```

Add this line to run every Monday at 9 AM:

```cron
0 9 * * 1 /Users/yosemite/githubs/llm-uj-research-eval/quick_helper_scripts_for_downloads_etc/weekly_paper_download.sh
```

Or for a different schedule:

```cron
# Every Sunday at midnight
0 0 * * 0 /Users/yosemite/githubs/llm-uj-research-eval/quick_helper_scripts_for_downloads_etc/weekly_paper_download.sh

# Every Friday at 5 PM
0 17 * * 5 /Users/yosemite/githubs/llm-uj-research-eval/quick_helper_scripts_for_downloads_etc/weekly_paper_download.sh

# First day of every month at 8 AM
0 8 1 * * /Users/yosemite/githubs/llm-uj-research-eval/quick_helper_scripts_for_downloads_etc/weekly_paper_download.sh
```

### Step 4: Verify cron job

List your cron jobs:

```bash
crontab -l
```

## What the Cron Job Does

1. **Downloads papers**: Fetches papers from Coda where deposit date > unjournal pub date
2. **Creates metadata**: Saves a CSV with:
   - Paper title
   - Author-date citation
   - DOI
   - DOI deposit date
   - Publication date (Unjournal)
   - Journal publication title
   - Download date
   - Filename
3. **Commits to git**: Automatically adds and commits new papers
4. **Pushes to GitHub**: Pushes changes to the remote repository

## Monitoring

Check the log file to see what happened:

```bash
tail -f quick_helper_scripts_for_downloads_etc/download_log.txt
```

## Troubleshooting

### "Coda API key not found"

Make sure you created `key/coda_key.txt` with your API token.

### "No rows found in table"

The table ID or doc ID might be wrong. Check the Coda URL:
- Doc ID: `dIEzDONWdb` (from `_ddIEzDONWdb`)
- Table ID: `grid-sufmGZoM` (from `_sufmGZoM` with `grid-` prefix)

### "Could not download PDF"

Some publishers don't allow automated downloads. The script will:
- Try CrossRef API to find PDF links
- Use content negotiation
- Fall back to the DOI URL
- Mark failed downloads with `FAILED_` prefix in metadata

### Cron not running

On macOS, you may need to give Terminal or cron Full Disk Access:
1. System Preferences → Security & Privacy → Privacy → Full Disk Access
2. Add Terminal or `/usr/sbin/cron`

## Column Name Mapping

The script tries multiple column name variations:

| Metadata Field | Possible Coda Column Names |
|----------------|---------------------------|
| paper_title | "paper_title", "Paper title", "title" |
| author_date_citation | "author_date_citation", "Author-date citation", "citation" |
| doi | "doi", "DOI" |
| doi_deposit_date | "doi_deposit_date", "DOI deposit date" |
| publication_date_unjournal | "publication_date_unjournal", "Publication date (Unjournal)" |
| journal_publication_title | "journal_publication_title", "Journal publication title" |
| deposit_date_check | "deposit date > unjournal pub date", "Deposit date > Unjournal pub date" |

If your Coda table uses different column names, update the script accordingly.

## Files Created

- `latest_papers_post_UJ/` - Directory with downloaded PDFs
- `latest_papers_post_UJ/metadata.csv` - Metadata for all downloads
- `quick_helper_scripts_for_downloads_etc/download_log.txt` - Log of all download attempts
