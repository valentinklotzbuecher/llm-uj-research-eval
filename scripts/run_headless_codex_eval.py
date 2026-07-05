#!/usr/bin/env python3
"""
Run a small OpenAI Codex headless evaluation pilot using ChatGPT/Codex auth.

This intentionally does not use the OpenAI API. It calls `codex exec` with a
JSON Schema and stores output in the same broad shape as the existing result
folders, while marking the input modality as extracted PDF text.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"

PERCENTILE_METRICS = [
    "overall",
    "claims_evidence",
    "methods",
    "advancing_knowledge",
    "logic_communication",
    "open_science",
    "global_relevance",
]
TIER_METRICS = ["tier_should", "tier_will"]

METRIC_SCHEMA = {
    "type": "object",
    "properties": {
        "midpoint": {"type": "number", "minimum": 0, "maximum": 100},
        "lower_bound": {"type": "number", "minimum": 0, "maximum": 100},
        "upper_bound": {"type": "number", "minimum": 0, "maximum": 100},
    },
    "required": ["midpoint", "lower_bound", "upper_bound"],
    "additionalProperties": False,
}

TIER_SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "number", "minimum": 0, "maximum": 5},
        "ci_lower": {"type": "number", "minimum": 0, "maximum": 5},
        "ci_upper": {"type": "number", "minimum": 0, "maximum": 5},
    },
    "required": ["score", "ci_lower", "ci_upper"],
    "additionalProperties": False,
}

OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "assessment_summary": {"type": "string"},
        "metrics": {
            "type": "object",
            "properties": {
                **{name: METRIC_SCHEMA for name in PERCENTILE_METRICS},
                **{name: TIER_SCHEMA for name in TIER_METRICS},
            },
            "required": PERCENTILE_METRICS + TIER_METRICS,
            "additionalProperties": False,
        },
    },
    "required": ["assessment_summary", "metrics"],
    "additionalProperties": False,
}


def load_system_prompt() -> str:
    sys.path.insert(0, str(ROOT))
    from prompts.versions.v4_assessment_current import SYSTEM_PROMPT

    return SYSTEM_PROMPT


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def extract_pdf_text(pdf_path: pathlib.Path) -> str:
    if not shutil.which("pdftotext"):
        raise RuntimeError("pdftotext is required for this headless pilot")

    with tempfile.NamedTemporaryFile(suffix=".txt") as tmp:
        subprocess.run(
            ["pdftotext", "-layout", str(pdf_path), tmp.name],
            check=True,
            capture_output=True,
            text=True,
        )
        return pathlib.Path(tmp.name).read_text(errors="replace")


def normalize_text(text: str, max_chars: int) -> tuple[str, bool]:
    text = re.sub(r"\n{4,}", "\n\n\n", text).strip()
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars].rstrip(), True


def build_prompt(system_prompt: str, paper_name: str, extracted_text: str, truncated: bool) -> str:
    truncation_note = (
        "The supplied text was truncated for this pilot. State this limitation in "
        "assessment_summary and widen uncertainty where appropriate."
        if truncated
        else "The supplied text is the extracted PDF text from the paper."
    )
    return f"""{system_prompt}

---

Evaluate the following paper using ONLY the supplied extracted PDF text.

Important constraints:
- Do not browse the web.
- Do not read repository files or use shell commands.
- Do not use author identity, institution, venue prestige, citations, or external memory as evidence.
- Treat layout, tables, equations, and figures as potentially degraded because this is extracted text.
- {truncation_note}

Paper file stem: {paper_name}

Extracted PDF text:
<<<BEGIN_PAPER_TEXT
{extracted_text}
END_PAPER_TEXT>>>

Return only JSON matching the supplied schema."""


def parse_final_json(path: pathlib.Path) -> dict[str, Any]:
    text = path.read_text()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]*\}", text)
        if not match:
            raise
        return json.loads(match.group())


def validate_result(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    metrics = result.get("metrics")
    if not isinstance(metrics, dict):
        return ["missing metrics object"]

    for name in PERCENTILE_METRICS:
        m = metrics.get(name)
        if not isinstance(m, dict):
            errors.append(f"missing metric: {name}")
            continue
        lb, mid, ub = m.get("lower_bound"), m.get("midpoint"), m.get("upper_bound")
        if not all(isinstance(x, (int, float)) for x in (lb, mid, ub)):
            errors.append(f"non-numeric metric bounds: {name}")
        elif not (0 <= lb <= mid <= ub <= 100):
            errors.append(f"invalid metric bounds: {name}")

    for name in TIER_METRICS:
        m = metrics.get(name)
        if not isinstance(m, dict):
            errors.append(f"missing tier: {name}")
            continue
        lb, score, ub = m.get("ci_lower"), m.get("score"), m.get("ci_upper")
        if not all(isinstance(x, (int, float)) for x in (lb, score, ub)):
            errors.append(f"non-numeric tier bounds: {name}")
        elif not (0 <= lb <= score <= ub <= 5):
            errors.append(f"invalid tier bounds: {name}")

    if not isinstance(result.get("assessment_summary"), str) or not result["assessment_summary"].strip():
        errors.append("missing assessment_summary")
    return errors


def run_codex(prompt: str, schema_path: pathlib.Path, output_path: pathlib.Path, model: str, timeout: int) -> dict[str, Any]:
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in ("OPENAI_API_KEY", "CODEX_API_KEY", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN")
    }
    cmd = [
        "codex",
        "exec",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "--model",
        model,
        "--output-schema",
        str(schema_path),
        "-o",
        str(output_path),
        prompt,
    ]
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def write_compatible_response(
    out_file: pathlib.Path,
    result: dict[str, Any],
    paper: pathlib.Path,
    model: str,
    run_id: str,
    prompt_version: str,
    max_chars: int,
    truncated: bool,
    raw: dict[str, Any],
) -> None:
    payload = {
        "object": "headless_codex_response",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model": f"{model} (codex exec, ChatGPT auth)",
        "run_id": run_id,
        "prompt_version": prompt_version,
        "input_modality": "pdftotext_extracted_text",
        "input_limit_chars": max_chars,
        "input_truncated": truncated,
        "source_pdf": str(paper),
        "source_pdf_sha256": sha256_file(paper),
        "parsed": result,
        "output_text": json.dumps(result, ensure_ascii=False),
        "codex_exec": {
            "returncode": raw["returncode"],
            "stderr_tail": raw["stderr"][-4000:],
        },
    }
    out_file.write_text(json.dumps(payload, indent=2, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper", required=True, help="PDF to evaluate")
    parser.add_argument("--run-id", default="codex_gpt55_headless_pilot_jul2026")
    parser.add_argument("--model", default="gpt-5.5")
    parser.add_argument("--max-chars", type=int, default=80000)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--prompt-version", default="v4_assessment_current_text_extraction")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    paper = pathlib.Path(args.paper)
    if not paper.is_absolute():
        paper = ROOT / paper
    paper = paper.resolve()
    if not paper.exists():
        raise FileNotFoundError(paper)

    run_dir = RESULTS_DIR / args.run_id
    json_dir = run_dir / "json"
    json_dir.mkdir(parents=True, exist_ok=True)
    out_file = json_dir / f"{paper.stem}.response.json"

    text, truncated = normalize_text(extract_pdf_text(paper), args.max_chars)
    prompt = build_prompt(load_system_prompt(), paper.stem, text, truncated)

    run_config = {
        "run_id": args.run_id,
        "model": f"{args.model} via codex exec",
        "prompt_version": args.prompt_version,
        "input_modality": "pdftotext_extracted_text",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "notes": "Pilot of ChatGPT-authenticated Codex non-interactive evaluation. Not comparable to native-PDF API runs without modality caveat.",
    }
    (run_dir / "run_config.json").write_text(json.dumps(run_config, indent=2))

    if args.dry_run:
        print(f"Prepared prompt for {paper.name}: {len(prompt)} chars")
        print(f"Output would be written to {out_file}")
        return 0

    with tempfile.TemporaryDirectory() as td:
        tempdir = pathlib.Path(td)
        schema_path = tempdir / "schema.json"
        final_path = tempdir / "final.json"
        schema_path.write_text(json.dumps(OUTPUT_SCHEMA, indent=2))
        raw = run_codex(prompt, schema_path, final_path, args.model, args.timeout)
        if raw["returncode"] != 0:
            print(raw["stderr"][-4000:], file=sys.stderr)
            return raw["returncode"] or 1
        result = parse_final_json(final_path)

    errors = validate_result(result)
    write_compatible_response(
        out_file,
        result,
        paper,
        args.model,
        args.run_id,
        args.prompt_version,
        args.max_chars,
        truncated,
        raw,
    )

    run_config["completed_at"] = datetime.now(timezone.utc).isoformat()
    run_config["status"] = "completed" if not errors else "completed_with_warnings"
    run_config["papers_evaluated"] = [paper.stem]
    run_config["outputs"] = {
        "combined_long": str(run_dir / "combined_long.csv"),
        "metrics_long": str(run_dir / "metrics_long.csv"),
        "tiers_long": str(run_dir / "tiers_long.csv"),
        "assessment_summaries": str(run_dir / "assessment_summaries.csv"),
        "json_dir": str(json_dir),
    }
    (run_dir / "run_config.json").write_text(json.dumps(run_config, indent=2))

    if errors:
        print("Wrote response with validation warnings:")
        for error in errors:
            print(f"- {error}")
        return 2

    print(f"Wrote valid response: {out_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
