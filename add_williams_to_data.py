#!/usr/bin/env python3
"""Add Williams et al. 2024 data to production data files."""

import json
import csv
import pathlib

# Read the Williams JSON response
json_path = pathlib.Path("results/json/Williams et al. 2024.response.json")
with open(json_path) as f:
    response_data = json.load(f)

# Extract the assessment text
output_text = response_data["output"][1]["content"][0]["text"]
assessment = json.loads(output_text)

paper_name = "Williams et al. 2024"
rationale = assessment["assessment_summary"]
metrics = assessment["metrics"]

# Prepare metrics data for metrics_long.csv
metrics_rows = []
for metric_name in ["overall", "claims_evidence", "methods", "advancing_knowledge",
                     "logic_communication", "open_science", "global_relevance"]:
    metric_data = metrics[metric_name]
    metrics_rows.append({
        "paper": paper_name,
        "metric": metric_name,
        "midpoint": metric_data["midpoint"],
        "lower_bound": metric_data["lower_bound"],
        "upper_bound": metric_data["upper_bound"],
        "rationale": rationale
    })

# Prepare tiers data for tiers_long.csv
tiers_rows = []
for tier_name in ["tier_should", "tier_will"]:
    tier_data = metrics[tier_name]
    tier_kind = "should" if tier_name == "tier_should" else "will"
    tiers_rows.append({
        "paper": paper_name,
        "tier_kind": tier_kind,
        "score": tier_data["score"],
        "lo": tier_data["ci_lower"],
        "hi": tier_data["ci_upper"],
        "rationale": rationale
    })

# Add to metrics_long.csv
metrics_csv = pathlib.Path("data/metrics_long.csv")
with open(metrics_csv, 'a', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=["paper", "metric", "midpoint", "lower_bound", "upper_bound", "rationale"])
    writer.writerows(metrics_rows)

print(f"Added {len(metrics_rows)} rows to {metrics_csv}")

# Add to tiers_long.csv
tiers_csv = pathlib.Path("data/tiers_long.csv")
with open(tiers_csv, 'a', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=["paper", "tier_kind", "score", "lo", "hi", "rationale"])
    writer.writerows(tiers_rows)

print(f"Added {len(tiers_rows)} rows to {tiers_csv}")
