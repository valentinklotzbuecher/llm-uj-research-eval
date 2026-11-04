#!/usr/bin/env python3
"""
Persistent-miss diagnostic: headless Claude Code runs on papers where earlier
one-shot LLM evaluations missed the critique that human Unjournal evaluators
treated as central.

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

Each call runs `claude -p --model claude-opus-5-5 --effort high` with both flags
passed explicitly, in an empty temporary working directory, with --safe-mode
(no CLAUDE.md, hooks, skills, MCP) so the model cannot see this repository,
which contains the human critiques. The PDF is sent as a native document block
via stream-json input (input mode "document"); for PDFs over the 100-page
document limit, input mode "read" copies the PDF alone into the temp dir and
allows only the Read tool.

This is a separate diagnostic. Its outputs must not be pooled with the one-shot
benchmark or used in the manuscript chapters.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
METHODS_QMD = ROOT / "methods.qmd"
PAPERS_DIR = ROOT / "papers"
DEFAULT_RUN_ID = "claude_opus_5_5_high_misses_2026-11-04"
MODEL = "claude-opus-5-5"
EFFORT = "high"
DOCUMENT_PAGE_LIMIT = 100

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


def cli_version(binary: str) -> str:
    proc = subprocess.run([binary, "--version"], capture_output=True, text=True)
    return proc.stdout.strip()


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
# Claude CLI call
# --------------------------------------------------------------------------

def run_claude(system_prompt: str, user_text: str, schema: dict[str, Any], pdf: pathlib.Path,
               input_mode: str, timeout: int) -> dict[str, Any]:
    binary = shutil.which("claude") or "/Users/yosemite/.local/bin/claude"
    env = {k: v for k, v in os.environ.items() if k not in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")}
    with tempfile.TemporaryDirectory(prefix="uj_misses_") as td:
        tdp = pathlib.Path(td)
        cmd = [
            binary, "-p",
            "--model", MODEL,
            "--effort", EFFORT,
            "--safe-mode",
            "--system-prompt", system_prompt,
            "--permission-mode", "dontAsk",
            "--no-session-persistence",
            "--output-format", "stream-json", "--verbose",
            "--json-schema", json.dumps(schema),
        ]
        if input_mode == "document":
            cmd += ["--tools", "", "--input-format", "stream-json"]
            message = {"type": "user", "message": {"role": "user", "content": [
                {"type": "document", "source": {
                    "type": "base64", "media_type": "application/pdf",
                    "data": base64.standard_b64encode(pdf.read_bytes()).decode()}},
                {"type": "text", "text": user_text},
            ]}}
            stdin = json.dumps(message) + "\n"
        elif input_mode == "read":
            shutil.copy(pdf, tdp / "paper.pdf")
            cmd += ["--tools", "Read", "--allowedTools", "Read"]
            stdin = None
            cmd.append(
                "The paper is the file paper.pdf in the current directory. Read all of it with the Read tool "
                "(it accepts a pages range of up to 20 pages per call) before answering.\n\n" + user_text
            )
        else:
            raise ValueError(input_mode)
        t0 = time.time()
        proc = subprocess.run(cmd, input=stdin, cwd=tdp, env=env, capture_output=True, text=True, timeout=timeout)
        elapsed = time.time() - t0

    events = []
    for line in proc.stdout.splitlines():
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            events.append({"type": "unparsed", "text": line[:2000]})
    result = next((e for e in reversed(events) if e.get("type") == "result"), None)
    init = next((e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), {})
    tool_calls = []
    for e in events:
        if e.get("type") == "assistant":
            for block in e.get("message", {}).get("content", []):
                if block.get("type") == "tool_use":
                    tool_calls.append({"name": block.get("name"), "input": block.get("input")})
    return {
        "returncode": proc.returncode,
        "stderr_tail": proc.stderr[-3000:],
        "elapsed_seconds": round(elapsed, 1),
        "result_event": result,
        "init_model": init.get("model"),
        "init_tools": init.get("tools"),
        "tool_calls": tool_calls,
    }


def extract_structured(result_event: dict[str, Any] | None) -> dict[str, Any] | None:
    if not result_event:
        return None
    so = result_event.get("structured_output")
    if isinstance(so, dict):
        return so
    text = result_event.get("result")
    if isinstance(text, str):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            m = re.search(r"\{[\s\S]*\}", text)
            if m:
                try:
                    return json.loads(m.group())
                except json.JSONDecodeError:
                    return None
    return None


# --------------------------------------------------------------------------
# Run registry (results/llm_runs_metadata.csv via track_llm_run helpers)
# --------------------------------------------------------------------------

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
        "model": f"{MODEL} (effort {EFFORT}, headless claude -p)",
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

def run_one(args: argparse.Namespace, ns: dict[str, Any], paper_stem: str, cond: str,
            claim: dict[str, Any] | None, binary_version: str) -> int:
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

    pages = pdf_pages(pdf)
    input_mode = args.input_mode
    if input_mode == "auto":
        input_mode = "read" if (pages or 0) > DOCUMENT_PAGE_LIMIT else "document"

    system_prompt, user_text, schema = build_condition(cond, ns, claim)
    provenance = {
        "run_id": args.run_id,
        "paper": paper_stem,
        "condition": cond,
        "claim_id": claim["claim_id"] if claim else None,
        "replicate": args.replicate,
        "model_requested": MODEL,
        "effort_requested": EFFORT,
        "cli_flags": f"claude -p --model {MODEL} --effort {EFFORT} --safe-mode --system-prompt <...> --json-schema <...>",
        "cli_version": binary_version,
        "prompt_version": PROMPT_VERSIONS[cond],
        "system_prompt_sha256": sha256_bytes(system_prompt.encode()),
        "user_text_sha256": sha256_bytes(user_text.encode()),
        "schema_sha256": sha256_bytes(json.dumps(schema, sort_keys=True).encode()),
        "methods_qmd_sha256": sha256_file(METHODS_QMD),
        "methods_qmd_last_commit": git_blob(METHODS_QMD),
        "pdf_path": str(pdf.relative_to(ROOT)),
        "pdf_sha256": sha256_file(pdf),
        "pdf_pages": pages,
        "pdf_last_commit": git_blob(pdf),
        "input_mode": input_mode,
        "isolation": "empty temp cwd, --safe-mode, no repo access, no web tools",
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    if args.dry_run:
        print(json.dumps({**provenance, "user_text": user_text, "system_prompt_chars": len(system_prompt)}, indent=1))
        return 0

    print(f"run {cond} {paper_stem}{suffix}{rep} ({input_mode}, {pages} pages) ...", flush=True)
    raw = run_claude(system_prompt, user_text, schema, pdf, input_mode, args.timeout)
    parsed = extract_structured(raw["result_event"])
    re_ = raw["result_event"] or {}
    provenance.update({
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "elapsed_seconds": raw["elapsed_seconds"],
        "returncode": raw["returncode"],
        "init_model": raw["init_model"],
        "init_tools": raw["init_tools"],
        "model_usage": re_.get("modelUsage"),
        "usage": re_.get("usage"),
        "total_cost_usd_reported": re_.get("total_cost_usd"),
        "num_turns": re_.get("num_turns"),
        "is_error": re_.get("is_error"),
        "tool_calls": raw["tool_calls"],
    })
    payload = {
        "provenance": provenance,
        "claim": claim,
        "user_text": user_text,
        "parsed": parsed,
        "result_text": re_.get("result"),
        "stderr_tail": raw["stderr_tail"] if raw["returncode"] else "",
    }
    ok = raw["returncode"] == 0 and parsed is not None and not re_.get("is_error")
    target = out_file if ok else out_file.with_suffix(".failed.json")
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"{'ok' if ok else 'FAILED'}: {target.relative_to(ROOT)} ({raw['elapsed_seconds']}s)", flush=True)
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--paper", action="append", help="Paper file stem in papers/ (repeatable)")
    ap.add_argument("--condition", choices=["A", "B", "C"], action="append")
    ap.add_argument("--claim-id", action="append", help="Condition C: only these claim ids")
    ap.add_argument("--run-id", default=DEFAULT_RUN_ID)
    ap.add_argument("--input-mode", choices=["auto", "document", "read"], default="auto")
    ap.add_argument("--replicate", type=int, default=1)
    ap.add_argument("--timeout", type=int, default=3600)
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
    binary = shutil.which("claude") or "/Users/yosemite/.local/bin/claude"
    version = cli_version(binary)
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
                for claim in todo:
                    failures += run_one(args, ns, paper, cond, claim, version)
            else:
                failures += run_one(args, ns, paper, cond, None, version)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
