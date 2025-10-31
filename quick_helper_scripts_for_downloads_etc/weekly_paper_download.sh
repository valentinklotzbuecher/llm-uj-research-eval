#!/bin/bash

# Weekly paper download wrapper script
# This script is designed to be run by cron

set -e  # Exit on error

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR"

# Log file
LOG_DIR="$SCRIPT_DIR"
DATE_STAMP=$(date +"%Y%m%d_%H%M%S")

echo "=== Weekly Paper Download - $DATE_STAMP ===" | tee -a "$LOG_DIR/download_log.txt"

# Activate conda environment
# Initialize conda (homebrew installation)
if command -v /opt/homebrew/bin/conda &> /dev/null; then
    eval "$(/opt/homebrew/bin/conda shell.bash hook)"
    conda activate qpy311_arm 2>&1 | tee -a "$LOG_DIR/download_log.txt" || echo "Could not activate qpy311_arm, using default python" | tee -a "$LOG_DIR/download_log.txt"
elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
    conda activate qpy311 2>&1 | tee -a "$LOG_DIR/download_log.txt"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
    conda activate qpy311 2>&1 | tee -a "$LOG_DIR/download_log.txt"
else
    echo "WARNING: conda not found, trying to use system python" | tee -a "$LOG_DIR/download_log.txt"
fi

# Run the download script
echo "Running download script..." | tee -a "$LOG_DIR/download_log.txt"
python "$SCRIPT_DIR/download_post_uj_papers.py" 2>&1 | tee -a "$LOG_DIR/download_log.txt"

# Commit and push to GitHub if there are changes
if git diff --quiet && git diff --staged --quiet; then
    echo "No changes to commit" | tee -a "$LOG_DIR/download_log.txt"
else
    echo "Changes detected, committing to git..." | tee -a "$LOG_DIR/download_log.txt"

    # Add the new files and metadata
    git add latest_papers_post_UJ/ 2>&1 | tee -a "$LOG_DIR/download_log.txt"

    # Create commit message
    COMMIT_MSG="Weekly paper download: $(date +"%Y-%m-%d")

Automated download of papers from Coda table where deposit date > unjournal pub date.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

    # Commit
    git commit -m "$COMMIT_MSG" 2>&1 | tee -a "$LOG_DIR/download_log.txt"

    # Push to remote
    echo "Pushing to GitHub..." | tee -a "$LOG_DIR/download_log.txt"
    git push 2>&1 | tee -a "$LOG_DIR/download_log.txt"

    echo "Successfully committed and pushed changes" | tee -a "$LOG_DIR/download_log.txt"
fi

echo "=== Download complete - $DATE_STAMP ===" | tee -a "$LOG_DIR/download_log.txt"
