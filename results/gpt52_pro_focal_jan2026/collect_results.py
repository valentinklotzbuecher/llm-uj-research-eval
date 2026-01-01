#!/usr/bin/env python3
"""
Poll status and collect completed results for GPT-5.2 Pro focal run.

Usage:
    conda activate qpy311
    python results/gpt52_pro_focal_jan2026/collect_results.py
"""

import os
import json
import pathlib
from typing import Dict, Any

import pandas as pd
from openai import OpenAI

RUN_DIR = pathlib.Path(__file__).parent
IDX_FILE = RUN_DIR / "jobs_index_focal.csv"
JSON_DIR = RUN_DIR / "json"
JSON_DIR.mkdir(exist_ok=True)

def get_api_key():
    key_path = pathlib.Path("key/openai_key.txt")
    if key_path.exists():
        return key_path.read_text().strip()
    return os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=get_api_key())

def _resp_as_dict(r):
    if hasattr(r, "model_dump"):
        return r.model_dump()
    if hasattr(r, "to_dict"):
        return r.to_dict()
    if isinstance(r, dict):
        return r
    return dict(r)

def main():
    if not IDX_FILE.exists():
        print(f"No jobs index found at {IDX_FILE}")
        return

    idx = pd.read_csv(IDX_FILE, dtype={'error': 'object'})
    print(f"Found {len(idx)} jobs in index")

    updated = 0
    collected = 0

    for i, row in idx.iterrows():
        paper = row["paper"]
        resp_id = row["response_id"]

        if pd.isna(resp_id):
            continue

        # Check if already collected
        json_path = JSON_DIR / f"{paper}.response.json"
        if json_path.exists() and row.get("collected") == True:
            continue

        # Poll status
        try:
            resp = client.responses.retrieve(resp_id)
            rd = _resp_as_dict(resp)
            status = rd.get("status", "unknown")
            idx.at[i, "status"] = status
            idx.at[i, "last_update"] = pd.Timestamp.utcnow().isoformat()
            updated += 1

            if status == "completed":
                # Save full response
                json_path.write_text(json.dumps(rd, indent=2, default=str))
                idx.at[i, "collected"] = True
                collected += 1
                print(f"✓ Collected: {paper}")

                # Extract token usage
                usage = rd.get("usage", {})
                idx.at[i, "input_tokens"] = usage.get("input_tokens")
                idx.at[i, "output_tokens"] = usage.get("output_tokens")
                odet = usage.get("output_tokens_details", {})
                idx.at[i, "reasoning_tokens"] = odet.get("reasoning_tokens")

            elif status == "failed":
                idx.at[i, "error"] = rd.get("error", "Unknown error")
                print(f"✗ Failed: {paper} - {rd.get('error')}")

            elif status in ("queued", "in_progress", "incomplete"):
                print(f"⏳ {status}: {paper}")

        except Exception as e:
            print(f"⚠️ Error polling {paper}: {e}")

    idx.to_csv(IDX_FILE, index=False)
    print(f"\nUpdated {updated} jobs, collected {collected} responses")

    # Summary
    status_counts = idx["status"].value_counts()
    print("\nStatus summary:")
    for status, count in status_counts.items():
        print(f"  {status}: {count}")

if __name__ == "__main__":
    main()
