#!/usr/bin/env python3
"""
Batch evaluation script for research papers.

Evaluates all PDFs in a specified directory using the LLM evaluation pipeline,
saving results to CSV files in long format.

Usage:
    python batch_eval.py

Environment variables:
    UJ_MODEL: Model to use (default: gpt-5-pro)
    UJ_PAPERS_DIR: Directory containing PDFs (default: papers/)
    UJ_TPM: Tokens per minute limit (default: 30000)
    UJ_RPM: Requests per minute limit (default: 50)
    OPENAI_API_KEY: OpenAI API key (or put in key/openai_key.txt)
"""

import os
import pathlib
import time

import numpy as np
import pandas as pd
from openai import OpenAI

from config import API_KEY_PATH, MODEL, PAPERS_DIR, RESULTS_DIR
from evaluator import evaluate_paper

# ============================================================================
# Setup
# ============================================================================

# Initialize OpenAI client
if os.getenv("OPENAI_API_KEY") is None and API_KEY_PATH.exists():
    os.environ["OPENAI_API_KEY"] = API_KEY_PATH.read_text().strip()
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError("No API key found. Put it in key/openai_key.txt or set OPENAI_API_KEY.")

client = OpenAI()

# Ensure output directory exists
RESULTS_DIR.mkdir(exist_ok=True)

# ============================================================================
# Main
# ============================================================================

def main():
    """
    Batch evaluate all PDFs in the papers directory.

    Processes each PDF file, evaluates it using the LLM, and saves results
    to CSV files in long format.
    """
    # Find PDFs
    print("CWD:", os.getcwd())
    print("PAPERS dir:", PAPERS_DIR.resolve())

    pdfs = sorted(PAPERS_DIR.glob("*.pdf"))
    print(f"Found {len(pdfs)} PDFs:", [p.name for p in pdfs])

    if not pdfs:
        print("\n⚠️  WARNING: No PDFs found in papers/ directory")
        print(f"   Check that PDFs exist in: {PAPERS_DIR.resolve()}")
        return

    # Evaluate each paper
    records = []
    for i, pdf in enumerate(pdfs, 1):
        print(f"\n[{i}/{len(pdfs)}] Processing {pdf.name}...")
        try:
            res = evaluate_paper(
                pdf,
                client=client,
                model=MODEL,
                use_reasoning=True,
                parse_retry=1,
            )
            res["paper"] = pdf.stem
            records.append(res)
            print(f"  ✓ Done with {pdf.name}")

            # Extra sleep for RPM safety
            time.sleep(0.8)

        except Exception as e:
            print(f"  ⚠️  Error with {pdf.name}: {e}")
            continue

    if not records:
        print("\n⚠️  WARNING: No papers were successfully evaluated")
        return

    # ========================================================================
    # Convert to long format
    # ========================================================================

    rows = []
    for rec in records:
        paper_id = rec.get("paper")
        metrics = (rec.get("metrics") or {}).items()

        for metric, vals in metrics:
            if metric in ("tier_should", "tier_will"):
                # Journal tier metrics (0-5 scale)
                rows.append({
                    "paper": paper_id,
                    "metric": metric,
                    "metric_type": "tier",
                    "value": vals.get("score"),
                    "lo": vals.get("ci_lower"),
                    "hi": vals.get("ci_upper"),
                    "rationale": vals.get("rationale"),
                    "scale_min": 0,
                    "scale_max": 5,
                })
            else:
                # Percentile metrics (0-100 scale)
                rows.append({
                    "paper": paper_id,
                    "metric": metric,
                    "metric_type": "percentile",
                    "value": vals.get("midpoint"),
                    "lo": vals.get("lower_bound"),
                    "hi": vals.get("upper_bound"),
                    "rationale": vals.get("rationale"),
                    "scale_min": 0,
                    "scale_max": 100,
                })

    combined = pd.DataFrame(rows)

    if combined.empty:
        print("\n⚠️  WARNING: No rows produced from evaluations")
        return

    # ========================================================================
    # Save results
    # ========================================================================

    # Save combined (all metrics and tiers)
    combined_path = RESULTS_DIR / "combined_long.csv"
    combined.to_csv(combined_path, index=False, encoding="utf-8")
    print(f"\n✓ Saved: {combined_path}")

    # Save percentile metrics only
    metrics_path = RESULTS_DIR / "metrics_long.csv"
    (combined.query("metric_type == 'percentile'")
        .rename(columns={"value": "midpoint", "lo": "lower_bound", "hi": "upper_bound"})
        .drop(columns=["metric_type", "scale_min", "scale_max"])
        .to_csv(metrics_path, index=False, encoding="utf-8"))
    print(f"✓ Saved: {metrics_path}")

    # Save tier metrics only
    tiers_path = RESULTS_DIR / "tiers_long.csv"
    (combined.query("metric_type == 'tier'")
        .rename(columns={"metric": "tier_kind", "value": "score"})
        .drop(columns=["metric_type", "scale_min", "scale_max"])
        .to_csv(tiers_path, index=False, encoding="utf-8"))
    print(f"✓ Saved: {tiers_path}")

    # ========================================================================
    # Summary statistics
    # ========================================================================

    n_papers = combined["paper"].nunique()
    n_rows = len(combined)
    n_metrics = combined["metric"].nunique()

    overall = combined[
        (combined["metric_type"] == "percentile") & (combined["metric"] == "overall")
    ]
    mean_overall = overall["value"].mean() if not overall.empty else np.nan
    med_overall = overall["value"].median() if not overall.empty else np.nan

    print("\n" + "=" * 60)
    print("BATCH EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Papers evaluated:      {n_papers}")
    print(f"Total rows:            {n_rows:,} (across {n_metrics} metrics)")
    print(f"Overall rating (mean): {mean_overall:.1f}")
    print(f"Overall rating (med):  {med_overall:.1f}")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
