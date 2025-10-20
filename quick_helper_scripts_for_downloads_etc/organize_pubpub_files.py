#!/usr/bin/env python3
"""
Organize and rename PubPub markdown files.

This script:
1. Examines files with non-meaningful names (8-character slugs)
2. Extracts titles and determines appropriate filenames
3. Identifies and moves template/blank files
4. Renames files to descriptive names
5. Creates a mapping file documenting all changes
"""

import json
import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Configuration
EVALUATIONS_DIR = Path("/Users/yosemite/githubs/llm-uj-research-eval/unjournal_evaluations")
TEMPLATES_DIR = EVALUATIONS_DIR / "templates"
MAPPING_FILE = EVALUATIONS_DIR / "file_renames_mapping.json"

# Patterns to identify templates and blank files
TEMPLATE_INDICATORS = [
    "REPLACE WITH ACTUAL",
    "[Template]",
    "\\[#\\]",
    "Evaluator name",
    "Paper Title",
    "Import' this using PubPub tools"
]

BLANK_INDICATORS = [
    "...",  # Placeholder content
]


def extract_title_from_markdown(file_path: Path) -> Optional[str]:
    """Extract the title from a markdown file's YAML frontmatter or first heading."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract YAML frontmatter
        yaml_match = re.search(r'^---\n(.*?)\n---', content, re.DOTALL | re.MULTILINE)
        if yaml_match:
            yaml_content = yaml_match.group(1)

            # Extract title field from YAML (handle multi-line, multi-quoted titles)
            # Looking for: title: "some text ... more text"
            # Handle multi-line by finding from 'title:' to next line that doesn't start with whitespace + more content
            title_match = re.search(r'title:\s*"([^"]*(?:\\"[^"]*)*)"', yaml_content, re.DOTALL)
            if not title_match:
                title_match = re.search(r"title:\s*'([^']*(?:\\'[^']*)*)'", yaml_content, re.DOTALL)

            if title_match:
                title = title_match.group(1).strip()
                # Clean up multi-line titles (replace newlines and extra spaces)
                title = re.sub(r'\s+', ' ', title)
                # Unescape quotes
                title = title.replace('\\"', '"').replace("\\'", "'")
                # Remove backslashes before quotes
                title = title.replace('\\', '')
                return title

        # Fallback to first H1 heading
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if h1_match:
            return h1_match.group(1).strip()

        return None
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None


def is_template_or_blank(file_path: Path) -> Tuple[bool, str]:
    """
    Check if a file is a template or blank file.
    Returns (is_template, reason)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for template indicators
        for indicator in TEMPLATE_INDICATORS:
            if indicator in content:
                return (True, f"Contains template indicator: '{indicator}'")

        # Check if file is very small (likely blank)
        if len(content) < 1000:
            return (True, "File too small (< 1000 chars)")

        # Check for blank indicators
        for indicator in BLANK_INDICATORS:
            # Count occurrences - if too many, likely a template
            count = content.count(indicator)
            if count > 5:
                return (True, f"Too many placeholder instances of '{indicator}'")

        return (False, "")
    except Exception as e:
        return (False, f"Error: {e}")


def create_filename_from_title(title: str, prefix: str = "") -> str:
    """
    Create a valid filename from a title.

    Args:
        title: The full title
        prefix: Optional prefix (e.g., 'evalsum', 'e1', etc.)

    Returns:
        A filesystem-safe filename (without .md extension)
    """
    # Extract key terms from evaluation titles
    paper_title = title

    # For "Evaluation X of "Paper Title""
    if re.match(r'Evaluation\s+\d+\s+of\s+"', title, re.IGNORECASE):
        match = re.search(r'of\s+"([^"]+)"', title, re.IGNORECASE)
        if match:
            paper_title = match.group(1).strip()

    # For "Evaluation Summary and Metrics: "Paper Title""
    elif "Evaluation Summary" in title or "Metrics:" in title:
        match = re.search(r':\s+"([^"]+)"', title)
        if match:
            paper_title = match.group(1).strip()

    # For "Compiled evaluations: "Paper Title""
    elif "Compiled evaluations:" in title:
        match = re.search(r':\s+"([^"]+)"', title)
        if match:
            paper_title = match.group(1).strip()

    # For "Author's response to Unjournal evaluations of "Paper Title""
    elif "response to Unjournal evaluations" in title:
        match = re.search(r'of\s+"([^"]+)"', title, re.IGNORECASE)
        if match:
            paper_title = match.group(1).strip()

    # Take first few meaningful words
    words = []
    for word in paper_title.split():
        # Skip common words
        if word.lower() in ['the', 'a', 'an', 'of', 'for', 'and', 'in', 'on', 'at', 'to', 'by', 'with', 'from']:
            continue
        # Clean word
        clean_word = re.sub(r'[^a-zA-Z0-9]', '', word).lower()
        if clean_word and len(clean_word) > 1:  # Skip single letters
            words.append(clean_word)
        if len(words) >= 5:  # Take first 5 meaningful words
            break

    # Create filename
    if prefix:
        filename = prefix + ''.join(words)
    else:
        filename = ''.join(words)

    # Limit length
    if len(filename) > 50:
        filename = filename[:50]

    return filename if filename else "untitled"


def scan_files_for_renaming() -> Dict[str, Dict]:
    """
    Scan all files in the evaluations directory and identify which need renaming.

    Returns a dict mapping: old_filename -> {
        'title': str,
        'suggested_name': str,
        'is_template': bool,
        'reason': str
    }
    """
    files_to_process = {}

    # Find files with 8-character slugs or other non-meaningful names
    for file_path in EVALUATIONS_DIR.glob("*.md"):
        filename = file_path.stem

        # Skip files that already have meaningful names
        if filename.startswith(('e1', 'e2', 'e3', 'eval', 'response', 'author')):
            # These patterns are already meaningful
            if len(filename) > 12 or any(c.isupper() for c in filename[4:]):
                # Likely already descriptive
                continue

        # Check if it looks like a random slug (8 alphanumeric characters)
        if re.match(r'^[0-9a-z]{8}$', filename):
            title = extract_title_from_markdown(file_path)
            is_template, reason = is_template_or_blank(file_path)

            if is_template:
                files_to_process[filename] = {
                    'title': title,
                    'suggested_name': None,
                    'is_template': True,
                    'reason': reason,
                    'path': str(file_path)
                }
            elif title:
                # Determine prefix based on title
                prefix = ""
                if "Evaluation Summary" in title or "Metrics" in title:
                    prefix = "evalsum"
                elif re.match(r'Evaluation\s+\d+', title):
                    eval_num = re.search(r'Evaluation\s+(\d+)', title).group(1)
                    prefix = f"e{eval_num}"
                elif "Evaluation" in title and " of " in title:
                    prefix = "eval1"  # Default to eval1 if evaluation number not specified

                suggested_name = create_filename_from_title(title, prefix)

                files_to_process[filename] = {
                    'title': title,
                    'suggested_name': suggested_name,
                    'is_template': False,
                    'reason': 'Random slug',
                    'path': str(file_path)
                }

    return files_to_process


def move_templates(files_to_process: Dict[str, Dict]) -> List[str]:
    """Move template files to templates directory."""
    TEMPLATES_DIR.mkdir(exist_ok=True)
    moved_files = []

    for old_name, info in files_to_process.items():
        if info['is_template']:
            src = Path(info['path'])
            dst = TEMPLATES_DIR / f"{old_name}.md"

            if src.exists():
                shutil.move(str(src), str(dst))
                moved_files.append(old_name)
                print(f"Moved template: {old_name}.md -> templates/{old_name}.md")
                print(f"  Reason: {info['reason']}")

    return moved_files


def rename_files(files_to_process: Dict[str, Dict], dry_run: bool = True) -> Dict[str, str]:
    """
    Rename files to descriptive names.

    Args:
        files_to_process: Dict of files to rename
        dry_run: If True, only print what would be done

    Returns:
        Dict mapping old_name -> new_name
    """
    renames = {}

    for old_name, info in files_to_process.items():
        if info['is_template'] or not info['suggested_name']:
            continue

        new_name = info['suggested_name']
        src = Path(info['path'])

        # Avoid naming conflicts
        dst = EVALUATIONS_DIR / f"{new_name}.md"
        counter = 1
        while dst.exists() and dst.stem != old_name:
            dst = EVALUATIONS_DIR / f"{new_name}{counter}.md"
            counter += 1
            new_name = f"{info['suggested_name']}{counter}"

        if dry_run:
            print(f"\nWould rename: {old_name}.md -> {new_name}.md")
            print(f"  Title: {info['title']}")
        else:
            if src.exists():
                shutil.move(str(src), str(dst))
                renames[old_name] = new_name
                print(f"\nRenamed: {old_name}.md -> {new_name}.md")
                print(f"  Title: {info['title']}")

    return renames


def save_mapping(files_to_process: Dict[str, Dict], renames: Dict[str, str], moved: List[str]):
    """Save the mapping of renamed and moved files."""
    mapping = {
        'renames': renames,
        'moved_to_templates': moved,
        'details': files_to_process
    }

    with open(MAPPING_FILE, 'w') as f:
        json.dump(mapping, f, indent=2)

    print(f"\nMapping saved to: {MAPPING_FILE}")


def main():
    """Main function."""
    print("PubPub File Organizer")
    print("=" * 50)
    print(f"Scanning directory: {EVALUATIONS_DIR}")
    print()

    # Scan files
    files_to_process = scan_files_for_renaming()

    if not files_to_process:
        print("No files need renaming or organizing.")
        return

    print(f"\nFound {len(files_to_process)} files to process:")
    templates = sum(1 for f in files_to_process.values() if f['is_template'])
    to_rename = sum(1 for f in files_to_process.values() if not f['is_template'])
    print(f"  - Templates/blanks to move: {templates}")
    print(f"  - Files to rename: {to_rename}")

    # Show what will be done
    print("\n" + "=" * 50)
    print("DRY RUN - Showing proposed changes")
    print("=" * 50)

    # Move templates
    print("\n### Templates to move ###")
    for old_name, info in files_to_process.items():
        if info['is_template']:
            print(f"  {old_name}.md -> templates/ ({info['reason']})")

    # Rename files
    print("\n### Files to rename ###")
    rename_files(files_to_process, dry_run=True)

    # Ask for confirmation
    print("\n" + "=" * 50)
    response = input("\nProceed with these changes? (yes/no): ").strip().lower()

    if response == 'yes':
        # Actually perform the operations
        moved = move_templates(files_to_process)
        renames = rename_files(files_to_process, dry_run=False)

        # Save mapping
        save_mapping(files_to_process, renames, moved)

        print("\n" + "=" * 50)
        print("COMPLETE")
        print("=" * 50)
        print(f"Moved {len(moved)} files to templates/")
        print(f"Renamed {len(renames)} files")
    else:
        print("\nCancelled - no changes made.")


if __name__ == "__main__":
    main()
