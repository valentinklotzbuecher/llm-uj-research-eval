#!/usr/bin/env python3
"""
GPT-5.2 Pro Focal Papers Evaluation Run

This script evaluates 14 focal papers using GPT-5.2-pro with an extended prompt
that includes a numbered list of key issues.

Usage:
    conda activate qpy311
    python results/gpt52_pro_focal_jan2026/run_evaluation.py

The script will:
1. Submit background jobs for each focal paper
2. Wait 90s between submissions to avoid rate limits
3. Save job status to jobs_index_focal.csv
"""

import os
import json
import time
import hashlib
import pathlib
from typing import Dict, Any, Optional, Union

import pandas as pd
from openai import OpenAI

# Configuration
MODEL = "gpt-5.2-pro"
RUN_DIR = pathlib.Path(__file__).parent
PAPERS_DIR = pathlib.Path("papers")
CACHE_FILE = pathlib.Path("cache/file_ids.json")

# 14 Focal papers
FOCAL_PAPERS = [
    "Acemoglu_et_al._2024",
    "Adena_and_Hager_2024",
    "Benabou_et_al._2023",
    "Bilal_and_Kaenzig_2024",
    "Blimpo_and_Castaneda-Dower_2025",
    "Bruers_2021",
    "Clancy_2024",
    "Dullaghan_and_Zhang_2022",
    "Frech_et_al._2023",
    "Green_et_al._2025",
    "McGuire_et_al._2024",
    "Peterman_et_al._2025",
    "Weaver_et_al._2025",
    "Williams_et_al._2024",
]

# Initialize OpenAI client
def get_api_key():
    key_path = pathlib.Path("key/openai_key.txt")
    if key_path.exists():
        return key_path.read_text().strip()
    return os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=get_api_key())

# ============================================================================
# EXTENDED SCHEMA WITH KEY_ISSUES
# ============================================================================

METRICS = [
    "overall",
    "claims_evidence",
    "methods",
    "advancing_knowledge",
    "logic_communication",
    "open_science",
    "global_relevance",
]

metric_schema = {
    "type": "object",
    "properties": {
        "midpoint":    {"type": "number", "minimum": 0, "maximum": 100},
        "lower_bound": {"type": "number", "minimum": 0, "maximum": 100},
        "upper_bound": {"type": "number", "minimum": 0, "maximum": 100},
    },
    "required": ["midpoint", "lower_bound", "upper_bound"],
    "additionalProperties": False,
}

TIER_METRIC_SCHEMA = {
    "type": "object",
    "properties": {
        "score":   {"type": "number", "minimum": 0, "maximum": 5},
        "ci_lower":{"type": "number", "minimum": 0, "maximum": 5},
        "ci_upper":{"type": "number", "minimum": 0, "maximum": 5},
    },
    "required": ["score", "ci_lower", "ci_upper"],
    "additionalProperties": False,
}

# Extended schema with key_issues array
COMBINED_SCHEMA_EXTENDED = {
    "type": "object",
    "properties": {
        "assessment_summary": {"type": "string"},
        "key_issues": {
            "type": "array",
            "items": {"type": "string"},
        },
        "metrics": {
            "type": "object",
            "properties": {
                **{m: metric_schema for m in METRICS},
                "tier_should": TIER_METRIC_SCHEMA,
                "tier_will":   TIER_METRIC_SCHEMA,
            },
            "required": METRICS + ["tier_should", "tier_will"],
            "additionalProperties": False,
        },
    },
    "required": ["assessment_summary", "key_issues", "metrics"],
    "additionalProperties": False,
}

TEXT_FORMAT_EXTENDED = {
    "type": "json_schema",
    "name": "paper_assessment_with_key_issues_v1",
    "strict": True,
    "schema": COMBINED_SCHEMA_EXTENDED,
}

# ============================================================================
# EXTENDED PROMPT (same base as modular_v2, with key_issues extension)
# ============================================================================

PROMPT_ROLE = """
Your role -- You are an academic expert as well as a practitioner across every relevant field -- use all your knowledge and insight. You are acting as an expert research evaluator/reviewer.
"""

PROMPT_DEBIASING = """
Do not look at any existing ratings or evaluations of these papers you might find on the internet or in your corpus, do not use the authors' names, status, or institutions in your judgment; ignore where (or whether) the work is published, the prestige of any venue, and how much attention it has received. Do not use this as evidence about quality. You must base all judgments entirely on the content of the PDF.
"""

PROMPT_DIAGNOSTIC = """
Diagnostic summary (Aim for about 1000 words, based only on the PDF):
Provide a compact paragraph that identifies the most important issues you detect in the manuscript itself (e.g., identification threats, data limitations, misinterpretations, internal inconsistencies, missing robustness, replication barriers). Be specific, neutral, and concrete. This summary should precede any scoring and should guide your uncertainty. Output this text in the JSON field `assessment_summary`.
"""

PROMPT_PERCENTILE_INTRO = """
Percentile rankings: You will be rating the paper on a scale from 0-100, where 50 represents the median. These are percentile ratings, meaning 0 is the lowest quality and 100 is the highest. **You should expect to rarely give any rating above 95.**
"""

PROMPT_REFERENCE_GROUP = """
Reference group: You must compare this paper to **all serious research in the same area encountered in the last three years**, meaning both published and unpublished (e.g., NBER, IZA working paper series) work of comparable scope. Do not restrict the reference group to top journal publications. A rating of 50 means the paper is better than about half of this broad set.
"""

PROMPT_METRICS = """
Metrics (each 0-100 except where noted):

- overall: Your overall assessment of the paper's merit, weighting all considerations.
- claims_evidence: How well do the main claims follow from the evidence and analysis?
- methods: Quality of methodology, including design, data handling, and statistical approach.
- advancing_knowledge: Contribution to the field and novelty of insights.
- logic_communication: Clarity, structure, and quality of exposition.
- open_science: Transparency, data/code availability, preregistration if applicable.
- global_relevance: Relevance to global priorities, policy, or welfare (use 50 if not clearly applicable).
"""

PROMPT_UNCERTAINTY = """
Credible intervals: For each percentile metric, provide a 90% credible interval (lower_bound, midpoint, upper_bound) reflecting your uncertainty. The lower and upper bounds should differ from the midpoint. Use wide intervals when genuinely uncertain.
"""

PROMPT_TIERS = """
Journal tier predictions (0-5 scale):

- tier_should: What journal tier *should* this paper be published in based on content quality alone?
- tier_will: What journal tier do you predict it *will* actually be published in?

Tier scale:
0 = Not publishable
1 = Low-ranked field journal
2 = Respectable field journal
3 = Top field journal (e.g., JDE, JEEM)
4 = Top-5 general interest (e.g., AER, QJE, Econometrica, JPE, ReStud)
5 = Top-3 or exceptional (Nature, Science, QJE, Econometrica at their best)

Provide score, ci_lower, ci_upper for each.
"""

PROMPT_VALIDATION = """
Before finalising your JSON:
- Check that your numeric scores are consistent with your own assessment_summary. If your summary describes serious or fundamental problems with methods, evidence, or interpretation, your scores for those metrics (and for "overall") should clearly reflect that.
- Conversely, if you assign very high scores in any metric, your summary should explicitly justify why that aspect of the paper is unusually strong relative to other serious work in the field.
- If you find yourself about to make the lower and upper bounds equal to the midpoint, adjust them so they form a non-degenerate interval that honestly reflects your uncertainty. Do not be afraid to use wide credible intervals when you are genuinely uncertain.
"""

# EXTENDED OUTPUT PROMPT with key_issues
PROMPT_OUTPUT_EXTENDED = """
Fill all three top-level keys:
- `assessment_summary`: about 1000 words.
- `key_issues`: a numbered list (array of strings) identifying the most important methodological, interpretive, or evidential issues in the paper. Each item should be a concise statement (1-2 sentences) that a reader could use as a checklist. Aim for 5-15 issues depending on the paper. Order from most to least important.
- `metrics`: object containing all required metrics.

Field names:
- Percentile metrics → `midpoint`, `lower_bound`, `upper_bound`.
- Tier metrics → `score`, `ci_lower`, `ci_upper`.

Return STRICT JSON matching the supplied schema. No preamble. No markdown. No extra text.
"""

SYSTEM_PROMPT_EXTENDED = "\n".join([
    PROMPT_ROLE,
    PROMPT_DEBIASING,
    PROMPT_DIAGNOSTIC,
    PROMPT_PERCENTILE_INTRO,
    PROMPT_REFERENCE_GROUP,
    PROMPT_METRICS,
    PROMPT_UNCERTAINTY,
    PROMPT_TIERS,
    PROMPT_VALIDATION,
    PROMPT_OUTPUT_EXTENDED,
]).strip()

# ============================================================================
# FILE HANDLING AND API CALLS
# ============================================================================

def _resp_as_dict(r):
    if hasattr(r, "model_dump"):
        return r.model_dump()
    if hasattr(r, "to_dict"):
        return r.to_dict()
    if isinstance(r, dict):
        return r
    return dict(r)

def _file_signature(path):
    p = pathlib.Path(path)
    return {"size": p.stat().st_size, "mtime": p.stat().st_mtime}

def _load_cache():
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text())
    return {}

def _save_cache(cache):
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, indent=2))

def get_file_id(pdf_path, client):
    """Upload file if not cached, return file_id."""
    path = pathlib.Path(pdf_path)
    key = str(path.resolve())
    sig = _file_signature(path)
    cache = _load_cache()

    if key in cache and cache[key].get("size") == sig["size"]:
        return cache[key]["file_id"]

    print(f"  Uploading {path.name}...")
    with open(path, "rb") as fh:
        f = client.files.create(file=fh, purpose="assistants")
    fd = _resp_as_dict(f)
    fid = fd.get("id")
    if not fid:
        raise RuntimeError(f"Upload did not return file id: {fd}")
    cache[key] = {"file_id": fid, **sig}
    _save_cache(cache)
    return fid

def evaluate_paper(pdf_path: Union[str, pathlib.Path]) -> Dict[str, Any]:
    """Submit a paper for evaluation, return job info."""
    fid = get_file_id(pdf_path, client)

    payload = dict(
        model=MODEL,
        text={"format": TEXT_FORMAT_EXTENDED},
        input=[
            {"role": "system", "content": [
                {"type": "input_text", "text": SYSTEM_PROMPT_EXTENDED}
            ]},
            {"role": "user", "content": [
                {"type": "input_file", "file_id": fid},
                {"type": "input_text", "text": "Return STRICT JSON per schema. No extra text."}
            ]},
        ],
        max_output_tokens=15000,  # Increased for key_issues
        background=True,
        store=True,
        reasoning={"effort": "high", "summary": "detailed"},
    )

    kickoff = client.responses.create(**payload)
    kd = _resp_as_dict(kickoff)
    return {
        "response_id": kd.get("id"),
        "file_id": fid,
        "status": kd.get("status") or "queued",
        "model": MODEL,
        "created_at": kd.get("created_at"),
    }

def read_csv_or_empty(path, columns=None):
    p = pathlib.Path(path)
    if not p.exists():
        return pd.DataFrame(columns=columns or [])
    try:
        return pd.read_csv(p, dtype={'error': 'object'})
    except Exception:
        return pd.DataFrame(columns=columns or [])

# ============================================================================
# MAIN
# ============================================================================

def main():
    print(f"GPT-5.2 Pro Focal Papers Run")
    print(f"Model: {MODEL}")
    print(f"Focal papers: {len(FOCAL_PAPERS)}")
    print("=" * 60)

    IDX = RUN_DIR / "jobs_index_focal.csv"
    cols = ["paper", "pdf", "response_id", "file_id", "model", "status",
            "created_at", "last_update", "collected", "error"]
    idx = read_csv_or_empty(IDX, columns=cols)

    existing = dict(zip(idx["paper"], idx["status"])) if not idx.empty else {}
    started = []

    for paper_name in FOCAL_PAPERS:
        pdf_path = PAPERS_DIR / f"{paper_name}.pdf"

        if not pdf_path.exists():
            print(f"⚠️ PDF not found: {pdf_path}")
            continue

        if existing.get(paper_name) in ("queued", "in_progress", "incomplete"):
            print(f"⏭️ Skip {paper_name}: job already running")
            continue

        if existing.get(paper_name) == "completed":
            print(f"✅ Skip {paper_name}: already completed")
            continue

        try:
            print(f"📄 Submitting {paper_name}...")
            job = evaluate_paper(pdf_path)
            started.append({
                "paper": paper_name,
                "pdf": str(pdf_path),
                "response_id": job.get("response_id"),
                "file_id": job.get("file_id"),
                "model": job.get("model"),
                "status": job.get("status"),
                "created_at": job.get("created_at") or pd.Timestamp.utcnow().isoformat(),
                "last_update": pd.Timestamp.utcnow().isoformat(),
                "collected": False,
                "error": pd.NA,
            })
            print(f"  ✓ Job submitted: {job.get('response_id')}")

            # Wait between submissions to avoid rate limits
            if paper_name != FOCAL_PAPERS[-1]:
                print(f"  ⏳ Waiting 90s before next submission...")
                time.sleep(90)

        except Exception as e:
            print(f"  ❌ Failed: {e}")

    if started:
        idx = pd.concat([idx, pd.DataFrame(started)], ignore_index=True)
        idx.drop_duplicates(subset=["paper"], keep="last", inplace=True)
        idx.to_csv(IDX, index=False)
        print(f"\n✓ Started {len(started)} jobs → {IDX}")
    else:
        print("\nNo new jobs started.")

    print("\nNext steps:")
    print("1. Run poll_status.py to check job completion")
    print("2. Run collect_results.py to download completed responses")

if __name__ == "__main__":
    main()
