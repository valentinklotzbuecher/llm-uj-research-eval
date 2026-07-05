#!/usr/bin/env python3
"""
Aggregate JSON response files from an LLM evaluation run into long-format CSVs.
"""

import json
import csv
import sys
from pathlib import Path

def extract_metrics_from_response(response_data: dict) -> dict | None:
    """Extract metrics from OpenAI, provider, or headless compatibility JSON."""
    try:
        # Headless/provider compatibility shape used by newer runs.
        parsed = response_data.get("parsed")
        if isinstance(parsed, dict) and "metrics" in parsed:
            return parsed

        output_text = response_data.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return json.loads(output_text)

        # Find the message output containing the metrics
        for output_item in response_data.get("output", []):
            if output_item.get("type") == "message" and output_item.get("role") == "assistant":
                for content_item in output_item.get("content", []):
                    if content_item.get("type") == "output_text":
                        text = content_item.get("text", "")
                        # Parse the JSON text
                        return json.loads(text)
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        print(f"  Warning: Could not parse metrics: {e}")
    return None


def aggregate_run(run_dir: Path):
    """Aggregate all JSON files in a run directory into CSVs."""
    json_dir = run_dir / "json"
    if not json_dir.exists():
        print(f"Error: {json_dir} does not exist")
        return

    json_files = list(json_dir.glob("*.response.json"))
    print(f"Found {len(json_files)} JSON response files")

    # Collect all data
    metrics_rows = []
    tiers_rows = []
    combined_rows = []
    summaries = []

    PERCENTILE_METRICS = [
        "overall", "claims_evidence", "methods", "advancing_knowledge",
        "logic_communication", "open_science", "global_relevance"
    ]
    TIER_METRICS = ["tier_should", "tier_will"]

    for json_file in sorted(json_files):
        paper_name = json_file.stem.replace(".response", "")
        print(f"  Processing: {paper_name}")

        try:
            with open(json_file) as f:
                response = json.load(f)
        except json.JSONDecodeError as e:
            print(f"    Error reading JSON: {e}")
            continue

        data = extract_metrics_from_response(response)
        if not data:
            print(f"    Warning: No metrics found")
            continue

        metrics = data.get("metrics", {})
        assessment_summary = data.get("assessment_summary", "")
        model = response.get("model", "unknown")

        # Percentile metrics (0-100 scale)
        for metric_name in PERCENTILE_METRICS:
            metric_data = metrics.get(metric_name, {})
            row = {
                "paper": paper_name,
                "metric": metric_name,
                "midpoint": metric_data.get("midpoint"),
                "lower_bound": metric_data.get("lower_bound"),
                "upper_bound": metric_data.get("upper_bound"),
                "model": model
            }
            metrics_rows.append(row)
            combined_rows.append({**row, "scale": "percentile"})

        # Tier metrics (0-5 scale)
        for metric_name in TIER_METRICS:
            metric_data = metrics.get(metric_name, {})
            row = {
                "paper": paper_name,
                "metric": metric_name,
                "score": metric_data.get("score"),
                "ci_lower": metric_data.get("ci_lower"),
                "ci_upper": metric_data.get("ci_upper"),
                "model": model
            }
            tiers_rows.append(row)
            combined_rows.append({
                "paper": paper_name,
                "metric": metric_name,
                "midpoint": metric_data.get("score"),
                "lower_bound": metric_data.get("ci_lower"),
                "upper_bound": metric_data.get("ci_upper"),
                "model": model,
                "scale": "tier"
            })

        # Assessment summary
        if assessment_summary:
            summaries.append({
                "paper": paper_name,
                "assessment_summary": assessment_summary,
                "model": model
            })

    # Write CSVs
    if metrics_rows:
        metrics_file = run_dir / "metrics_long.csv"
        with open(metrics_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["paper", "metric", "midpoint", "lower_bound", "upper_bound", "model"])
            writer.writeheader()
            writer.writerows(metrics_rows)
        print(f"Wrote {len(metrics_rows)} rows to {metrics_file}")

    if tiers_rows:
        tiers_file = run_dir / "tiers_long.csv"
        with open(tiers_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["paper", "metric", "score", "ci_lower", "ci_upper", "model"])
            writer.writeheader()
            writer.writerows(tiers_rows)
        print(f"Wrote {len(tiers_rows)} rows to {tiers_file}")

    if combined_rows:
        combined_file = run_dir / "combined_long.csv"
        with open(combined_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["paper", "metric", "midpoint", "lower_bound", "upper_bound", "model", "scale"])
            writer.writeheader()
            writer.writerows(combined_rows)
        print(f"Wrote {len(combined_rows)} rows to {combined_file}")

    if summaries:
        summaries_file = run_dir / "assessment_summaries.csv"
        with open(summaries_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["paper", "assessment_summary", "model"])
            writer.writeheader()
            writer.writerows(summaries)
        print(f"Wrote {len(summaries)} summaries to {summaries_file}")

    print(f"\nDone! Processed {len(json_files)} papers.")
    return len(json_files)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python aggregate_json_to_csv.py <run_directory>")
        print("Example: python aggregate_json_to_csv.py results/gpt5_pro_updated_jan2026")
        sys.exit(1)

    run_dir = Path(sys.argv[1])
    if not run_dir.exists():
        print(f"Error: {run_dir} does not exist")
        sys.exit(1)

    aggregate_run(run_dir)
