#!/usr/bin/env python3
"""
Persistent-miss diagnostic: Claude Opus 5.5 (effort high) on papers where
earlier one-shot LLM evaluations missed the critique that human Unjournal
evaluators raised.

Three prompt conditions (see docs/handover_persistent_misses_opus55_2026-11-04.md):

  A  standard        the methods.qmd combined Unjournal prompt with the
                     key_issues extension (SYSTEM_PROMPT_WITH_ISSUES), JSON schema
                     COMBINED_SCHEMA_WITH_ISSUES; comparable with the GPT-5.2 Pro
                     focal run and (minus key_issues) the Opus 4.6 run.
  B  prioritisation  "What is the single most important problem with this
                     paper's main claims? Then give your top five, ranked."
  C  recognition     an expert critique stated as a claim to assess
                     ("An evaluator argues X. Is this right, and how much does
                     it matter?"). Claims live in recognition_claims.json.

Calls go to the Anthropic Messages API (streaming) with model claude-opus-5-5,
output_config.effort "high" set explicitly, adaptive thinking (summaries
kept), no tools, and the paper as a native base64 PDF document block with a
cache breakpoint after it, like the earlier one-shot API runs. The key is read
from key/anthropic_key.txt and never logged. No refusal fallbacks: a refusal
is recorded rather than answered by another model. Each output records the
usage (including cache tokens), estimated cost, stop reason, prompt and PDF
hashes, and SDK version; spend_ledger.csv accumulates cost, and a call is
skipped once the run total reaches --budget (default $25).

This is a separate diagnostic. Its outputs must not be pooled with the one-shot
benchmark or used in the manuscript chapters.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
METHODS_QMD = ROOT / "methods.qmd"
PAPERS_DIR = ROOT / "papers"
DEFAULT_RUN_ID = "claude_opus_5_5_high_misses_2026-11-04"
MODEL = "claude-opus-5-5"
EFFORT = "high"

PROMPT_VERSIONS = {
    "A": "methods_qmd_SYSTEM_PROMPT_WITH_ISSUES",
    "B": "misses_B_prioritisation_v1",
    "C": "misses_C_recognition_v1",
}

B_QUESTION = (
    "What is the single most important problem with this paper's main claims? "
    "Then give your top five, ranked."
)

B_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "main_claims": {"type": "string", "description": "One or two sentences stating the paper's main claims as you read them."},
        "single_most_important_problem": {
            "type": "object",
            "properties": {
                "problem": {"type": "string"},
                "why_it_matters": {"type": "string"},
                "where_in_paper": {"type": "string"},
            },
            "required": ["problem", "why_it_matters", "where_in_paper"],
            "additionalProperties": False,
        },
        "top_five": {
            "type": "array",
            "minItems": 5,
            "maxItems": 5,
            "items": {
                "type": "object",
                "properties": {
                    "rank": {"type": "integer", "minimum": 1, "maximum": 5},
                    "problem": {"type": "string"},
                    "why_it_matters": {"type": "string"},
                    "where_in_paper": {"type": "string"},
                },
                "required": ["rank", "problem", "why_it_matters", "where_in_paper"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["main_claims", "single_most_important_problem", "top_five"],
    "additionalProperties": False,
}

C_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "what_the_paper_shows": {
            "type": "string",
            "description": "What the paper itself reports on this point, citing tables, figures, pages or sections you checked.",
        },
        "is_the_critique_right": {
            "type": "string",
            "enum": ["right", "partly right", "wrong", "cannot assess from the paper"],
        },
        "reasoning": {"type": "string"},
        "how_much_it_matters": {
            "type": "string",
            "enum": ["central to the main claims", "important", "minor", "does not matter"],
        },
        "how_much_it_matters_explanation": {"type": "string"},
        "would_you_have_raised_it": {
            "type": "string",
            "description": "Would you have raised this point unprompted in a review, and where would it rank among your concerns?",
        },
    },
    "required": [
        "what_the_paper_shows",
        "is_the_critique_right",
        "reasoning",
        "how_much_it_matters",
        "how_much_it_matters_explanation",
        "would_you_have_raised_it",
    ],
    "additionalProperties": False,
}


# --------------------------------------------------------------------------
# Prompt extraction from methods.qmd (the canonical source of condition A)
# --------------------------------------------------------------------------

CONSTANT_CHUNKS = ["schema-definition", "prompt-role", "prompt-percentile", "prompt-metrics",
                   "prompt-uncertainty", "prompt-assembly"]
FOCAL_MARKER = "# Extended schema with key_issues array"


def _python_chunks(text: str) -> dict[str, str]:
    chunks = {}
    for body in re.findall(r"```\{python\}\n(.*?)\n```", text, flags=re.S):
        m = re.search(r"^#\| label:\s*(\S+)", body, flags=re.M)
        if m:
            chunks[m.group(1)] = "\n".join(l for l in body.splitlines() if not l.startswith("#|"))
    return chunks


def load_methods_prompts() -> dict[str, Any]:
    """Execute only the constant-defining chunks of methods.qmd.

    Uses the schema and prompt chunks by label, plus the tail of the
    focal-config chunk from the key_issues schema onwards (its head creates
    directories, so it is skipped). These snippets only define constants.
    """
    chunks = _python_chunks(METHODS_QMD.read_text())
    snippets = [chunks[label] for label in CONSTANT_CHUNKS]
    focal = chunks["focal-config"]
    snippets.append(focal[focal.index(FOCAL_MARKER):])
    ns: dict[str, Any] = {}
    for snip in snippets:
        exec(compile(snip, str(METHODS_QMD), "exec"), ns)  # noqa: S102 - trusted repo source
    needed = ["SYSTEM_PROMPT_WITH_ISSUES", "COMBINED_SCHEMA_WITH_ISSUES", "PROMPT_ROLE", "PROMPT_DEBIASING"]
    missing = [k for k in needed if k not in ns]
    if missing:
        raise RuntimeError(f"Could not extract from methods.qmd: {missing}")
    return ns


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: pathlib.Path) -> str:
    return sha256_bytes(path.read_bytes())


def git_blob(path: pathlib.Path) -> str:
    proc = subprocess.run(["git", "-C", str(ROOT), "log", "-1", "--format=%H", "--", str(path)],
                          capture_output=True, text=True)
    return proc.stdout.strip()


def pdf_pages(path: pathlib.Path) -> int | None:
    if not shutil.which("pdfinfo"):
        return None
    proc = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True)
    m = re.search(r"^Pages:\s+(\d+)", proc.stdout, flags=re.M)
    return int(m.group(1)) if m else None


# --------------------------------------------------------------------------
# Prompt construction
# --------------------------------------------------------------------------

def build_condition(cond: str, ns: dict[str, Any], claim: dict[str, Any] | None) -> tuple[str, str, dict[str, Any]]:
    """Return (system_prompt, user_text, schema)."""
    pdf_only = "Base your answer only on the attached paper. Do not browse or use other files."
    # Condition C asks the model to verify a specific claim, so it is pointed at the evidence.
    # Condition B deliberately gets no such nudge, to stay close to the unprompted setting.
    verify = " Check the paper's tables, figures and appendices where relevant, and cite them."
    if cond == "A":
        return (
            ns["SYSTEM_PROMPT_WITH_ISSUES"],
            "Return STRICT JSON per schema. No extra text.",
            ns["COMBINED_SCHEMA_WITH_ISSUES"],
        )
    role = (ns["PROMPT_ROLE"].strip() + "\n\n" + ns["PROMPT_DEBIASING"].strip())
    if cond == "B":
        return role, f"{B_QUESTION}\n\n{pdf_only}\n\nReturn JSON matching the supplied schema.", B_SCHEMA
    if cond == "C":
        if not claim:
            raise ValueError("Condition C needs a claim")
        user = (
            f"An evaluator argues: \"{claim['claim_text']}\"\n\n"
            "Is this right, and how much does it matter?\n\n"
            f"{pdf_only}{verify}\n\nReturn JSON matching the supplied schema."
        )
        return role, user, C_SCHEMA
    raise ValueError(cond)


# --------------------------------------------------------------------------
# Messages API call
# --------------------------------------------------------------------------

# USD per million tokens for claude-opus-5-5 (standard tier, first-party API).
PRICE_INPUT = 4.00
PRICE_OUTPUT = 20.00
PRICE_CACHE_WRITE_5M = 5.00   # 1.25x input
PRICE_CACHE_WRITE_1H = 8.00   # 2x input
PRICE_CACHE_READ = 0.20
BUDGET_STOP_USD = 25.0
MAX_TOKENS = 64000

UNSUPPORTED_SCHEMA_KEYS = ("minimum", "maximum", "minItems", "maxItems")


def api_schema(schema: Any) -> Any:
    """Structured outputs reject numeric and array-length bounds; strip them (validated locally)."""
    if isinstance(schema, dict):
        return {k: api_schema(v) for k, v in schema.items() if k not in UNSUPPORTED_SCHEMA_KEYS}
    if isinstance(schema, list):
        return [api_schema(x) for x in schema]
    return schema


def make_client():
    import anthropic

    key_path = ROOT / "key" / "anthropic_key.txt"
    key = key_path.read_text().strip()
    # max_retries covers 429/5xx/connection errors; the long timeout suits big PDFs at high effort.
    return anthropic.Anthropic(api_key=key, max_retries=4, timeout=3600.0)


def estimate_cost(usage: dict[str, Any]) -> float:
    cc = usage.get("cache_creation") or {}
    w5 = cc.get("ephemeral_5m_input_tokens", 0) or 0
    w1 = cc.get("ephemeral_1h_input_tokens", 0) or 0
    if not (w5 or w1):
        w5 = usage.get("cache_creation_input_tokens", 0) or 0
    return round(
        (usage.get("input_tokens", 0) or 0) * PRICE_INPUT / 1e6
        + (usage.get("output_tokens", 0) or 0) * PRICE_OUTPUT / 1e6
        + w5 * PRICE_CACHE_WRITE_5M / 1e6
        + w1 * PRICE_CACHE_WRITE_1H / 1e6
        + (usage.get("cache_read_input_tokens", 0) or 0) * PRICE_CACHE_READ / 1e6,
        4,
    )


def run_api(client, system_prompt: str, user_text: str, schema: dict[str, Any], pdf: pathlib.Path, raw_path: pathlib.Path) -> dict[str, Any]:
    import anthropic

    content = [
        {
            "type": "document",
            "source": {"type": "base64", "media_type": "application/pdf",
                       "data": base64.standard_b64encode(pdf.read_bytes()).decode()},
            # Breakpoint after the PDF: later calls with the same system prompt and paper reuse it.
            "cache_control": {"type": "ephemeral"},
        },
        {"type": "text", "text": user_text},
    ]
    t0 = time.time()
    try:
        with client.messages.stream(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            thinking={"type": "adaptive", "display": "summarized"},
            output_config={"effort": EFFORT, "format": {"type": "json_schema", "schema": api_schema(schema)}},
            messages=[{"role": "user", "content": content}],
        ) as stream:
            msg = stream.get_final_message()
            try:
                request_id = stream.response.headers.get("request-id")
            except Exception:  # noqa: BLE001 - provenance only; never lose the response over it
                request_id = None
    except anthropic.APIStatusError as e:
        return {"error": f"{type(e).__name__} {e.status_code}: {e.message}",
                "request_id": getattr(e, "request_id", None), "elapsed_seconds": round(time.time() - t0, 1)}
    except anthropic.APIConnectionError as e:
        return {"error": f"APIConnectionError: {e}", "elapsed_seconds": round(time.time() - t0, 1)}
    elapsed = time.time() - t0
    d = msg.to_dict()
    # Save the raw response first, so a later processing error cannot lose a paid call.
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps(d, ensure_ascii=False))
    text = "".join(b.get("text", "") or "" for b in d.get("content", []) if b.get("type") == "text")
    thinking = [b.get("thinking", "") or "" for b in d.get("content", []) if b.get("type") == "thinking"]
    return {
        "elapsed_seconds": round(elapsed, 1),
        "request_id": request_id,
        "response_id": d.get("id"),
        "model": d.get("model"),
        "stop_reason": d.get("stop_reason"),
        "stop_details": d.get("stop_details"),
        "usage": d.get("usage"),
        "text": text,
        "thinking_summaries": thinking,
    }


def validate(cond: str, parsed: dict[str, Any]) -> list[str]:
    errs: list[str] = []
    if cond == "A":
        for name, m in parsed.get("metrics", {}).items():
            if "midpoint" in m:
                if not (0 <= m["lower_bound"] <= m["midpoint"] <= m["upper_bound"] <= 100):
                    errs.append(f"bounds {name}")
            elif "score" in m:
                if not (0 <= m["ci_lower"] <= m["score"] <= m["ci_upper"] <= 5):
                    errs.append(f"bounds {name}")
    if cond == "B" and len(parsed.get("top_five", [])) != 5:
        errs.append(f"top_five has {len(parsed.get('top_five', []))} items")
    return errs


# --------------------------------------------------------------------------
# Spend ledger and run registry
# --------------------------------------------------------------------------

def spend_path(run_dir: pathlib.Path) -> pathlib.Path:
    return run_dir / "spend_ledger.csv"


def total_spend(run_dir: pathlib.Path) -> float:
    p = spend_path(run_dir)
    if not p.exists():
        return 0.0
    with p.open() as f:
        return sum(float(r["est_cost_usd"]) for r in csv.DictReader(f))


def record_spend(run_dir: pathlib.Path, row: dict[str, Any]) -> None:
    p = spend_path(run_dir)
    new = not p.exists()
    fields = ["timestamp", "paper", "condition", "claim_id", "replicate", "status", "stop_reason",
              "input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens",
              "est_cost_usd", "elapsed_seconds", "request_id"]
    with p.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in fields})


def register_run(run_id: str, run_dir: pathlib.Path) -> None:
    sys.path.insert(0, str(ROOT))
    import track_llm_run as t  # noqa: E402

    rows = t.read_metadata()
    if any(r["run_id"] == run_id for r in rows):
        print(f"Already registered: {run_id}")
        return
    rel = run_dir.relative_to(ROOT)
    rows.append({
        "run_id": run_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "model": f"{MODEL} (effort {EFFORT}, Messages API)",
        "prompt_version": "persistent_misses_ABC (" + "; ".join(f"{k}={v}" for k, v in PROMPT_VERSIONS.items()) + ")",
        "prompt_description": "Persistent-miss diagnostic: A standard combined prompt with key_issues, B prioritisation, C recognition of expert critique",
        "prompt_file": "methods.qmd:SYSTEM_PROMPT_WITH_ISSUES; scripts/run_headless_claude_misses.py",
        "num_papers": "0",
        "papers_evaluated": "",
        "output_combined_long": "",
        "output_metrics_long": "",
        "output_tiers_long": "",
        "output_json_dir": f"{rel}/",
        "notes": "Separate diagnostic; not pooled with the one-shot benchmark or used in manuscript chapters. Scores in ledger are provisional pending David's review.",
        "status": "in_progress",
    })
    t.write_metadata(rows)
    print(f"Registered {run_id}")


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def sdk_version() -> str:
    import anthropic

    return anthropic.__version__


def run_one(args: argparse.Namespace, client, ns: dict[str, Any], paper_stem: str, cond: str,
            claim: dict[str, Any] | None) -> int:
    pdf = PAPERS_DIR / f"{paper_stem}.pdf"
    if not pdf.exists():
        raise FileNotFoundError(pdf)
    run_dir = ROOT / "results" / args.run_id
    out_dir = run_dir / cond
    out_dir.mkdir(parents=True, exist_ok=True)
    suffix = f"__{claim['claim_id']}" if claim else ""
    rep = f"__r{args.replicate}" if args.replicate > 1 else ""
    out_file = out_dir / f"{paper_stem}{suffix}{rep}.json"
    if out_file.exists() and not args.force:
        print(f"skip (exists): {out_file.relative_to(ROOT)}")
        return 0

    spent = total_spend(run_dir)
    if spent >= args.budget:
        print(f"STOP: estimated spend ${spent:.2f} has reached the ${args.budget:.2f} limit")
        return 99

    system_prompt, user_text, schema = build_condition(cond, ns, claim)
    provenance = {
        "run_id": args.run_id,
        "paper": paper_stem,
        "condition": cond,
        "claim_id": claim["claim_id"] if claim else None,
        "replicate": args.replicate,
        "interface": "Anthropic Messages API (streaming), anthropic Python SDK",
        "sdk_version": sdk_version(),
        "model_requested": MODEL,
        "effort": EFFORT,
        "thinking": "adaptive, display summarized",
        "max_tokens": MAX_TOKENS,
        "fallbacks": "none (refusals are recorded, not rerouted)",
        "prompt_version": PROMPT_VERSIONS[cond],
        "system_prompt_sha256": sha256_bytes(system_prompt.encode()),
        "user_text_sha256": sha256_bytes(user_text.encode()),
        "schema_sha256": sha256_bytes(json.dumps(schema, sort_keys=True).encode()),
        "schema_note": "numeric and array-length bounds stripped for structured outputs; checked locally",
        "methods_qmd_sha256": sha256_file(METHODS_QMD),
        "methods_qmd_last_commit": git_blob(METHODS_QMD),
        "pdf_path": str(pdf.relative_to(ROOT)),
        "pdf_sha256": sha256_file(pdf),
        "pdf_pages": pdf_pages(pdf),
        "pdf_last_commit": git_blob(pdf),
        "input_modality": "native PDF document block (base64), cache breakpoint after the PDF",
        "tools": "none",
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    if args.dry_run:
        print(json.dumps({**provenance, "user_text": user_text, "system_prompt_chars": len(system_prompt)}, indent=1))
        return 0

    print(f"run {cond} {paper_stem}{suffix}{rep} ({provenance['pdf_pages']} pages) ...", flush=True)
    raw = run_api(client, system_prompt, user_text, schema, pdf, out_file.with_suffix(".raw_response.json"))
    usage = raw.get("usage") or {}
    cost = estimate_cost(usage) if usage else 0.0
    parsed = None
    errors: list[str] = []
    if raw.get("error"):
        errors.append(raw["error"])
    elif raw.get("stop_reason") != "end_turn":
        errors.append(f"stop_reason={raw.get('stop_reason')} stop_details={raw.get('stop_details')}")
    else:
        try:
            parsed = json.loads(raw["text"])
            errors += validate(cond, parsed)
        except json.JSONDecodeError as e:
            errors.append(f"JSON parse: {e}")
    provenance.update({
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": raw.get("elapsed_seconds"),
        "request_id": raw.get("request_id"),
        "response_id": raw.get("response_id"),
        "model_returned": raw.get("model"),
        "stop_reason": raw.get("stop_reason"),
        "stop_details": raw.get("stop_details"),
        "usage": usage,
        "est_cost_usd": cost,
        "price_basis_usd_per_mtok": {"input": PRICE_INPUT, "output": PRICE_OUTPUT,
                                     "cache_write_5m": PRICE_CACHE_WRITE_5M, "cache_read": PRICE_CACHE_READ},
        "validation_errors": errors,
    })
    payload = {
        "provenance": provenance,
        "claim": claim,
        "user_text": user_text,
        "parsed": parsed,
        "result_text": raw.get("text"),
        "thinking_summaries": raw.get("thinking_summaries"),
    }
    ok = parsed is not None and not raw.get("error") and raw.get("stop_reason") == "end_turn"
    target = out_file if ok else out_file.with_suffix(".failed.json")
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    record_spend(run_dir, {
        "timestamp": provenance["completed_at"], "paper": paper_stem, "condition": cond,
        "claim_id": provenance["claim_id"] or "", "replicate": args.replicate,
        "status": "ok" if ok else "failed", "stop_reason": raw.get("stop_reason", ""),
        "input_tokens": usage.get("input_tokens", ""),
        "cache_creation_input_tokens": usage.get("cache_creation_input_tokens", ""),
        "cache_read_input_tokens": usage.get("cache_read_input_tokens", ""),
        "output_tokens": usage.get("output_tokens", ""),
        "est_cost_usd": cost, "elapsed_seconds": raw.get("elapsed_seconds", ""),
        "request_id": raw.get("request_id", ""),
    })
    print(f"{'ok' if ok else 'FAILED'}: {target.relative_to(ROOT)} ({raw.get('elapsed_seconds')}s, "
          f"~${cost:.2f}; run total ~${total_spend(run_dir):.2f}){'' if ok else ' ' + '; '.join(errors)}",
          flush=True)
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--paper", action="append", help="Paper file stem in papers/ (repeatable)")
    ap.add_argument("--condition", choices=["A", "B", "C"], action="append")
    ap.add_argument("--claim-id", action="append", help="Condition C: only these claim ids")
    ap.add_argument("--run-id", default=DEFAULT_RUN_ID)
    ap.add_argument("--replicate", type=int, default=1)
    ap.add_argument("--budget", type=float, default=BUDGET_STOP_USD, help="Stop before a call once estimated run spend reaches this")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--register", action="store_true", help="Register the run in results/llm_runs_metadata.csv")
    args = ap.parse_args()

    run_dir = ROOT / "results" / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    if args.register:
        register_run(args.run_id, run_dir)
        if not args.paper:
            return 0
    if not args.paper or not args.condition:
        ap.error("--paper and --condition are required")

    ns = load_methods_prompts()
    client = None if args.dry_run else make_client()
    claims_path = run_dir / "recognition_claims.json"
    claims = json.loads(claims_path.read_text())["claims"] if claims_path.exists() else []

    failures = 0
    for paper in args.paper:
        for cond in args.condition:
            if cond == "C":
                todo = [c for c in claims if c["paper"] == paper and c.get("run_condition_c", True)]
                if args.claim_id:
                    todo = [c for c in todo if c["claim_id"] in args.claim_id]
                if not todo:
                    print(f"no condition-C claims for {paper}")
                items = todo
            else:
                items = [None]
            for claim in items:
                rc = run_one(args, client, ns, paper, cond, claim)
                if rc == 99:
                    return 99
                failures += rc
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
