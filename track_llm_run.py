#!/usr/bin/env python3
"""
Helper script to track LLM evaluation runs with metadata.

Usage:
    python track_llm_run.py start --model gpt-5 --prompt-version v3 --description "Testing new prompt"
    python track_llm_run.py complete <run_id> --papers "paper1,paper2,paper3"
"""

import csv
import argparse
from datetime import datetime
from pathlib import Path
import json

METADATA_FILE = Path("results/llm_runs_metadata.csv")
RESULTS_DIR = Path("results")

def generate_run_id(model: str, prompt_version: str) -> str:
    """Generate a unique run ID based on date, model, and prompt version."""
    date_str = datetime.now().strftime("%Y%m%d")
    return f"{date_str}_{model}_{prompt_version}"

def read_metadata() -> list[dict]:
    """Read existing metadata."""
    if not METADATA_FILE.exists():
        return []

    with open(METADATA_FILE, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)

def write_metadata(rows: list[dict]):
    """Write metadata to CSV."""
    if not rows:
        return

    fieldnames = [
        'run_id', 'date', 'model', 'prompt_version', 'prompt_description',
        'num_papers', 'papers_evaluated', 'output_combined_long',
        'output_metrics_long', 'output_tiers_long', 'output_json_dir',
        'notes', 'status'
    ]

    with open(METADATA_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

def start_run(model: str, prompt_version: str, description: str, notes: str = "") -> str:
    """Start a new LLM evaluation run."""
    run_id = generate_run_id(model, prompt_version)
    date_str = datetime.now().strftime("%Y-%m-%d")

    # Create output directory structure
    run_dir = RESULTS_DIR / run_id
    run_dir.mkdir(exist_ok=True)
    (run_dir / "json").mkdir(exist_ok=True)

    # Prepare file paths
    combined_long = f"results/{run_id}/combined_long.csv"
    metrics_long = f"results/{run_id}/metrics_long.csv"
    tiers_long = f"results/{run_id}/tiers_long.csv"
    json_dir = f"results/{run_id}/json/"

    new_row = {
        'run_id': run_id,
        'date': date_str,
        'model': model,
        'prompt_version': prompt_version,
        'prompt_description': description,
        'num_papers': '0',
        'papers_evaluated': '',
        'output_combined_long': combined_long,
        'output_metrics_long': metrics_long,
        'output_tiers_long': tiers_long,
        'output_json_dir': json_dir,
        'notes': notes,
        'status': 'in_progress'
    }

    # Add to metadata
    rows = read_metadata()
    rows.append(new_row)
    write_metadata(rows)

    # Create a run config file
    config = {
        'run_id': run_id,
        'model': model,
        'prompt_version': prompt_version,
        'description': description,
        'started_at': datetime.now().isoformat(),
        'output_paths': {
            'combined_long': combined_long,
            'metrics_long': metrics_long,
            'tiers_long': tiers_long,
            'json_dir': json_dir
        }
    }

    with open(run_dir / "run_config.json", 'w') as f:
        json.dump(config, f, indent=2)

    print(f"✓ Started run: {run_id}")
    print(f"  Output directory: {run_dir}")
    print(f"  Status: in_progress")
    print(f"\nNext steps:")
    print(f"  1. Run your LLM evaluation pipeline")
    print(f"  2. Save outputs to: {run_dir}/")
    print(f"  3. Complete the run with: python track_llm_run.py complete {run_id} --papers \"paper1,paper2,...\"")

    return run_id

def complete_run(run_id: str, papers: list[str], notes: str = ""):
    """Mark a run as completed and update metadata."""
    rows = read_metadata()

    found = False
    for row in rows:
        if row['run_id'] == run_id:
            row['status'] = 'completed'
            row['num_papers'] = str(len(papers))
            row['papers_evaluated'] = ', '.join(papers)
            if notes:
                row['notes'] = f"{row['notes']}; {notes}" if row['notes'] else notes
            found = True
            break

    if not found:
        print(f"✗ Error: Run ID '{run_id}' not found in metadata")
        return

    write_metadata(rows)

    # Update run config
    run_dir = RESULTS_DIR / run_id
    config_file = run_dir / "run_config.json"
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
        config['completed_at'] = datetime.now().isoformat()
        config['papers_evaluated'] = papers
        config['num_papers'] = len(papers)
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

    print(f"✓ Completed run: {run_id}")
    print(f"  Papers evaluated: {len(papers)}")
    print(f"  Status: completed")

def list_runs(status_filter: str = None):
    """List all runs, optionally filtered by status."""
    rows = read_metadata()

    if status_filter:
        rows = [r for r in rows if r['status'] == status_filter]

    if not rows:
        print("No runs found.")
        return

    print(f"\n{'Run ID':<40} {'Date':<12} {'Model':<10} {'Papers':<8} {'Status':<12}")
    print("-" * 90)
    for row in rows:
        print(f"{row['run_id']:<40} {row['date']:<12} {row['model']:<10} {row['num_papers']:<8} {row['status']:<12}")
    print()

def show_run_details(run_id: str):
    """Show detailed information about a specific run."""
    rows = read_metadata()

    for row in rows:
        if row['run_id'] == run_id:
            print(f"\nRun Details: {run_id}")
            print("=" * 80)
            for key, value in row.items():
                print(f"  {key:25s}: {value}")

            # Show config if exists
            config_file = RESULTS_DIR / run_id / "run_config.json"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                print("\n  Config file:")
                print(f"    {json.dumps(config, indent=6)}")
            print()
            return

    print(f"✗ Error: Run ID '{run_id}' not found")

def main():
    parser = argparse.ArgumentParser(description="Track LLM evaluation runs")
    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Start command
    start_parser = subparsers.add_parser('start', help='Start a new evaluation run')
    start_parser.add_argument('--model', required=True, help='Model name (e.g., gpt-5, claude-3.5)')
    start_parser.add_argument('--prompt-version', required=True, help='Prompt version (e.g., v3, improved_v2)')
    start_parser.add_argument('--description', required=True, help='Brief description of this run')
    start_parser.add_argument('--notes', default='', help='Additional notes')

    # Complete command
    complete_parser = subparsers.add_parser('complete', help='Mark a run as completed')
    complete_parser.add_argument('run_id', help='Run ID to complete')
    complete_parser.add_argument('--papers', required=True, help='Comma-separated list of papers evaluated')
    complete_parser.add_argument('--notes', default='', help='Additional notes')

    # List command
    list_parser = subparsers.add_parser('list', help='List all runs')
    list_parser.add_argument('--status', choices=['in_progress', 'completed', 'failed'],
                           help='Filter by status')

    # Show command
    show_parser = subparsers.add_parser('show', help='Show details of a specific run')
    show_parser.add_argument('run_id', help='Run ID to show')

    args = parser.parse_args()

    if args.command == 'start':
        start_run(args.model, args.prompt_version, args.description, args.notes)
    elif args.command == 'complete':
        papers = [p.strip() for p in args.papers.split(',')]
        complete_run(args.run_id, papers, args.notes)
    elif args.command == 'list':
        list_runs(args.status)
    elif args.command == 'show':
        show_run_details(args.run_id)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
