#!/usr/bin/env python3
"""
Hypothes.is #implement Tag Monitor

This script monitors Hypothes.is annotations on the llm-uj-research-eval Quarto site
for annotations tagged with #implement. When found, it uses an LLM to interpret
and implement the suggested changes, then commits them to git.

Usage:
    python tools/hypothesis_implement_monitor.py           # Run once
    python tools/hypothesis_implement_monitor.py --dry-run # Preview without changes
    python tools/hypothesis_implement_monitor.py --list    # List pending annotations

Cron setup (every 24 hours at 6 AM):
    0 6 * * * cd /Users/yosemite/githubs/llm-uj-research-eval && /opt/homebrew/Caskroom/miniforge/base/envs/qpy311_arm/bin/python tools/hypothesis_implement_monitor.py >> logs/hypothesis_monitor.log 2>&1
"""

import os
import sys
import json
import re
import subprocess
import argparse
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

import requests

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
SITE_URL = "https://llm-uj-research-eval.netlify.app"
HYPOTHESIS_API = "https://api.hypothes.is/api"
PROCESSED_FILE = PROJECT_ROOT / "tools" / ".hypothesis_processed.json"
LOG_DIR = PROJECT_ROOT / "logs"

# Load API keys
def load_hypothesis_token() -> str:
    """Load Hypothes.is API token from .env file."""
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.startswith("hypothesis_PAT="):
                    return line.split("=", 1)[1].strip()
    raise ValueError("hypothesis_PAT not found in .env file")

def load_openai_key() -> str:
    """Load OpenAI API key."""
    key_file = PROJECT_ROOT / "key" / "openai_key.txt"
    if key_file.exists():
        return key_file.read_text().strip()
    raise ValueError("OpenAI API key not found in key/openai_key.txt")

def get_processed_annotations() -> dict:
    """Load the set of already-processed annotation IDs."""
    if PROCESSED_FILE.exists():
        with open(PROCESSED_FILE) as f:
            return json.load(f)
    return {"processed": [], "failed": [], "skipped": []}

def save_processed_annotations(data: dict):
    """Save processed annotation tracking data."""
    with open(PROCESSED_FILE, "w") as f:
        json.dump(data, f, indent=2)

def fetch_implement_annotations(token: str) -> list:
    """Fetch all annotations tagged with #implement from the site."""
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "wildcard_uri": f"{SITE_URL}/*",
        "tag": "implement",
        "limit": 200,
        "sort": "created",
        "order": "asc"
    }

    response = requests.get(f"{HYPOTHESIS_API}/search", headers=headers, params=params)
    response.raise_for_status()

    data = response.json()
    return data.get("rows", [])

def url_to_qmd_file(uri: str) -> Optional[Path]:
    """Convert a page URL to its source .qmd file path."""
    parsed = urlparse(uri)
    path = parsed.path.strip("/")

    # Handle root/index page
    if not path or path == "index.html":
        return PROJECT_ROOT / "index.qmd"

    # Remove .html extension and map to .qmd
    if path.endswith(".html"):
        path = path[:-5]

    qmd_file = PROJECT_ROOT / f"{path}.qmd"
    if qmd_file.exists():
        return qmd_file

    # Try in subdirectories (appendices, etc.)
    for qmd in PROJECT_ROOT.glob("**/*.qmd"):
        if qmd.stem == path.split("/")[-1]:
            return qmd

    return None

def extract_target_context(annotation: dict) -> dict:
    """Extract the text being annotated and surrounding context."""
    target = annotation.get("target", [{}])[0]
    selectors = target.get("selector", [])

    context = {
        "exact_text": None,
        "prefix": None,
        "suffix": None,
        "position": None
    }

    for selector in selectors:
        if selector.get("type") == "TextQuoteSelector":
            context["exact_text"] = selector.get("exact")
            context["prefix"] = selector.get("prefix")
            context["suffix"] = selector.get("suffix")
        elif selector.get("type") == "TextPositionSelector":
            context["position"] = (selector.get("start"), selector.get("end"))

    return context

def implement_change_with_llm(
    annotation: dict,
    qmd_file: Path,
    openai_key: str,
    dry_run: bool = False
) -> dict:
    """Use OpenAI to interpret and implement the suggested change."""
    from openai import OpenAI

    client = OpenAI(api_key=openai_key)

    # Read the source file
    source_content = qmd_file.read_text()

    # Extract annotation details
    comment_text = annotation.get("text", "")
    context = extract_target_context(annotation)
    annotator = annotation.get("user", "").split(":")[-1]  # Extract username
    annotation_id = annotation.get("id")
    uri = annotation.get("uri", "")

    system_prompt = """You are a helpful assistant that implements suggested changes to Quarto documents.
You will receive:
1. The current content of a .qmd file
2. An annotation comment describing a change to make
3. The specific text that was highlighted when the annotation was made

Your task is to:
1. Understand what change is being requested
2. Locate the relevant section in the document
3. Make the requested change
4. Return the complete modified document

Guidelines:
- Make minimal, targeted changes that address the specific request
- Preserve all existing formatting, code blocks, and structure
- If the request is unclear or cannot be safely implemented, explain why in the "notes" field
- Do not add comments like "Changed by AI" or similar - the git commit will track attribution

Return a JSON object with:
{
  "success": true/false,
  "modified_content": "full file content with changes" (or null if not successful),
  "change_description": "brief description of what was changed",
  "notes": "any additional notes or warnings"
}
"""

    user_message = f"""## Source File: {qmd_file.name}

## Annotation Details
- **Comment**: {comment_text}
- **Highlighted text**: {context.get('exact_text', 'N/A')}
- **Text before**: {context.get('prefix', 'N/A')}
- **Text after**: {context.get('suffix', 'N/A')}
- **Annotator**: {annotator}

## Current File Content
```
{source_content}
```

Please implement the requested change and return the modified content as JSON.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=16000
        )

        result = json.loads(response.choices[0].message.content)

        if result.get("success") and result.get("modified_content") and not dry_run:
            # Write the modified content
            qmd_file.write_text(result["modified_content"])
            result["file_modified"] = str(qmd_file)

        result["annotation_id"] = annotation_id
        result["annotation_uri"] = uri
        result["annotator"] = annotator
        result["comment"] = comment_text

        return result

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "annotation_id": annotation_id,
            "comment": comment_text
        }

def git_commit_change(qmd_file: Path, annotation: dict, change_description: str) -> bool:
    """Commit the change to git with proper attribution."""
    annotator = annotation.get("user", "").split(":")[-1]
    annotation_id = annotation.get("id", "unknown")
    comment_preview = annotation.get("text", "")[:100]

    try:
        # Stage the modified file
        subprocess.run(
            ["git", "add", str(qmd_file)],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True
        )

        # Create commit message
        commit_msg = f"""Implement Hypothes.is suggestion: {change_description}

Annotation ID: {annotation_id}
Suggested by: {annotator}
Comment: {comment_preview}{'...' if len(annotation.get('text', '')) > 100 else ''}

This change was automatically implemented based on a #implement tagged
annotation on the live site.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
"""

        subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True
        )

        return True

    except subprocess.CalledProcessError as e:
        print(f"Git commit failed: {e.stderr.decode()}")
        return False

def process_annotation(
    annotation: dict,
    openai_key: str,
    dry_run: bool = False
) -> dict:
    """Process a single annotation: interpret, implement, and commit."""
    annotation_id = annotation.get("id")
    uri = annotation.get("uri", "")
    comment = annotation.get("text", "")

    print(f"\n{'='*60}")
    print(f"Processing annotation: {annotation_id}")
    print(f"URI: {uri}")
    print(f"Comment: {comment[:200]}{'...' if len(comment) > 200 else ''}")

    # Map URL to source file
    qmd_file = url_to_qmd_file(uri)
    if not qmd_file:
        return {
            "success": False,
            "error": f"Could not map URI to source file: {uri}",
            "annotation_id": annotation_id
        }

    print(f"Source file: {qmd_file}")

    # Implement the change
    result = implement_change_with_llm(annotation, qmd_file, openai_key, dry_run)

    if result.get("success"):
        print(f"Change: {result.get('change_description', 'N/A')}")

        if not dry_run:
            # Commit the change
            if git_commit_change(qmd_file, annotation, result.get("change_description", "")):
                result["committed"] = True
                print("Committed to git")
            else:
                result["committed"] = False
                print("Warning: Git commit failed")
        else:
            print("[DRY RUN] Would modify file and commit")
    else:
        print(f"Failed: {result.get('error', result.get('notes', 'Unknown error'))}")

    return result

def main():
    parser = argparse.ArgumentParser(
        description="Monitor Hypothes.is for #implement tagged annotations"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview changes without modifying files or committing"
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List pending annotations without processing"
    )
    parser.add_argument(
        "--reprocess", metavar="ID",
        help="Reprocess a specific annotation ID (even if previously processed)"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Process all annotations, including previously processed ones"
    )

    args = parser.parse_args()

    # Ensure log directory exists
    LOG_DIR.mkdir(exist_ok=True)

    print(f"Hypothes.is #implement Monitor - {datetime.now().isoformat()}")
    print(f"Site: {SITE_URL}")
    print("-" * 60)

    try:
        hypothesis_token = load_hypothesis_token()
        openai_key = load_openai_key()
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Fetch annotations
    print("Fetching annotations with #implement tag...")
    annotations = fetch_implement_annotations(hypothesis_token)
    print(f"Found {len(annotations)} annotation(s)")

    if not annotations:
        print("No #implement annotations found.")
        return

    # Load processed tracking
    processed_data = get_processed_annotations()
    processed_ids = set(processed_data.get("processed", []))

    # Filter to unprocessed annotations
    if args.reprocess:
        pending = [a for a in annotations if a.get("id") == args.reprocess]
        if not pending:
            print(f"Annotation {args.reprocess} not found")
            return
    elif args.all:
        pending = annotations
    else:
        pending = [a for a in annotations if a.get("id") not in processed_ids]

    print(f"Pending: {len(pending)}, Already processed: {len(processed_ids)}")

    if args.list:
        print("\nPending annotations:")
        for ann in pending:
            created = ann.get("created", "")[:10]
            user = ann.get("user", "").split(":")[-1]
            text = ann.get("text", "")[:80]
            uri = ann.get("uri", "").replace(SITE_URL, "")
            print(f"  [{created}] {ann.get('id')}")
            print(f"    User: {user}")
            print(f"    Page: {uri}")
            print(f"    Comment: {text}...")
            print()
        return

    if not pending:
        print("No pending annotations to process.")
        return

    # Process each annotation
    results = []
    for annotation in pending:
        result = process_annotation(annotation, openai_key, args.dry_run)
        results.append(result)

        if not args.dry_run:
            # Update tracking
            ann_id = annotation.get("id")
            if result.get("success"):
                if ann_id not in processed_data["processed"]:
                    processed_data["processed"].append(ann_id)
            else:
                if ann_id not in processed_data["failed"]:
                    processed_data["failed"].append(ann_id)
            save_processed_annotations(processed_data)

    # Summary
    print("\n" + "=" * 60)
    print("Summary:")
    successful = sum(1 for r in results if r.get("success"))
    print(f"  Processed: {len(results)}")
    print(f"  Successful: {successful}")
    print(f"  Failed: {len(results) - successful}")

    if args.dry_run:
        print("\n[DRY RUN] No files were modified or commits made.")

if __name__ == "__main__":
    main()
