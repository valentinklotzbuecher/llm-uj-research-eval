#!/usr/bin/env python3
"""Judge human–LLM issue concordance through ChatGPT-authenticated Codex.

This is an exploratory, subscription-backed alternative to the OpenAI API
runner in ``tools/compare_issues_llm.py``.  It uses Terra for the first pass,
then sends only ambiguous judgments to Sol.  Every issue receives a stable ID,
and every Codex JSONL usage event is retained and summarized.

The script deliberately runs Codex in an isolated, read-only directory and
removes API-key environment variables.  It is resumable: completed Terra and
Sol call artifacts are reused unless ``--force`` is supplied.
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
import time
from datetime import datetime, timezone
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "tools" / "issue_annotation_ui" / "data.json"
DEFAULT_RUN_ID = "concordance_codex_terra_sol_pilot_jul2026"
APP_CODEX = pathlib.Path("/Applications/ChatGPT.app/Contents/Resources/codex")
API_ENV_KEYS = {
    "OPENAI_API_KEY",
    "CODEX_API_KEY",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
}

LABELS = ["exact", "partial", "related_but_distinct", "distinct"]

JUDGMENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "human_issue_id": {"type": "string"},
        "llm_issue_ids": {"type": "array", "items": {"type": "string"}},
        "label": {"type": "string", "enum": LABELS},
        "overlap_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
        "shared_core": {"type": "string"},
        "important_difference": {"type": "string"},
        "needs_sol_review": {"type": "boolean"},
    },
    "required": [
        "human_issue_id",
        "llm_issue_ids",
        "label",
        "overlap_score",
        "confidence",
        "shared_core",
        "important_difference",
        "needs_sol_review",
    ],
    "additionalProperties": False,
}

REVIEW_CANDIDATE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "human_issue_id": {"type": "string"},
        "llm_issue_ids": {"type": "array", "items": {"type": "string"}},
        "reason": {"type": "string"},
    },
    "required": ["human_issue_id", "llm_issue_ids", "reason"],
    "additionalProperties": False,
}

TERRA_PAPER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "paper_id": {"type": "string"},
        "judgments": {"type": "array", "items": JUDGMENT_SCHEMA},
        "unmatched_human_ids": {"type": "array", "items": {"type": "string"}},
        "unmatched_llm_ids": {"type": "array", "items": {"type": "string"}},
        "review_candidates": {
            "type": "array",
            "items": REVIEW_CANDIDATE_SCHEMA,
        },
        "input_alignment": {
            "type": "string",
            "enum": ["aligned", "uncertain", "misaligned"],
        },
        "alignment_explanation": {"type": "string"},
        "paper_difficulty": {"type": "integer", "minimum": 0, "maximum": 100},
        "overall_assessment": {"type": "string"},
    },
    "required": [
        "paper_id",
        "judgments",
        "unmatched_human_ids",
        "unmatched_llm_ids",
        "review_candidates",
        "input_alignment",
        "alignment_explanation",
        "paper_difficulty",
        "overall_assessment",
    ],
    "additionalProperties": False,
}

TERRA_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "papers": {"type": "array", "items": TERRA_PAPER_SCHEMA},
    },
    "required": ["papers"],
    "additionalProperties": False,
}

SOL_JUDGMENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "paper_id": {"type": "string"},
        "human_issue_id": {"type": "string"},
        "llm_issue_ids": {"type": "array", "items": {"type": "string"}},
        "label": {"type": "string", "enum": LABELS},
        "overlap_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
        "shared_core": {"type": "string"},
        "important_difference": {"type": "string"},
        "decision_rationale": {"type": "string"},
    },
    "required": [
        "paper_id",
        "human_issue_id",
        "llm_issue_ids",
        "label",
        "overlap_score",
        "confidence",
        "shared_core",
        "important_difference",
        "decision_rationale",
    ],
    "additionalProperties": False,
}

SOL_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "adjudications": {"type": "array", "items": SOL_JUDGMENT_SCHEMA},
    },
    "required": ["adjudications"],
    "additionalProperties": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_path(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slug_issue_id(paper_id: str, prefix: str, index: int) -> str:
    return f"{paper_id}::{prefix}{index:03d}"


def anonymize_human_issue(text: str) -> str:
    """Remove reviewer/evaluator attribution markers before external calls."""
    text = re.sub(
        r"(?i)\b(?:evaluator|reviewer)\s*\d+\b|\bE\d+\b|\bDR\b",
        "human evaluator",
        text,
    )
    text = re.sub(
        r"\[(?:[^\]\n]*(?:eval|review|manager|notebooklm)[^\]\n]*|[A-Z][A-Za-z'’.-]{2,30})\]",
        "[human evaluator]",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"(?m)^\s*[A-Z][A-Za-z'’.-]{2,30}:\s*(?=[\"“])",
        "Human evaluator: ",
        text,
    )
    text = re.sub(
        r"(?m)^\s*[A-Z][A-Za-z'’.-]{2,30}\s*$",
        "human evaluator",
        text,
    )
    text = re.sub(
        r"\b[A-Z][A-Za-z'’.-]{2,30}\s+(?=(?:notes?|argues?|observes?|requests?|requested|recommended|suggests?|emphasizes?|critiqued|wrote|writes?|said|says?)\b)",
        "human evaluator ",
        text,
    )
    text = re.sub(
        r"\b[A-Z][A-Za-z'’.-]{2,30}\s+[A-Z][A-Za-z'’.-]{2,30}\s+(?=is not an expert\b)",
        "a human evaluator ",
        text,
    )
    return text


def load_cases(source_path: pathlib.Path) -> list[dict[str, Any]]:
    raw = json.loads(source_path.read_text())
    cases: list[dict[str, Any]] = []

    # Preferred source: the human annotation UI's separately enumerated issue
    # suggestions.  Keep legacy support for key_issues_matched.json so archived
    # runs remain reproducible, but do not use it by default because some of its
    # human items combine several substantively distinct concerns.
    if isinstance(raw, dict) and isinstance(raw.get("papers"), list):
        records = [
            (
                record["paper_id"],
                {
                    "human_issues": record.get("human_issue_suggestions", []),
                    "llm_issues": record.get("llm_key_issues", []),
                    "paper_title": record.get("paper_title", ""),
                },
            )
            for record in raw["papers"]
        ]
        source_format = "issue_annotation_ui"
    elif isinstance(raw, dict):
        records = list(raw.items())
        source_format = "legacy_key_issues_matched"
    else:
        raise ValueError("Unsupported concordance input format")

    for paper_id, record in records:
        humans = []
        for index, issue in enumerate(record.get("human_issues", []), 1):
            humans.append(
                {
                    "id": slug_issue_id(paper_id, "H", index),
                    "severity": issue.get("severity", "unspecified"),
                    "text": issue.get("text", "").strip(),
                }
            )
        llms = []
        for index, issue in enumerate(record.get("llm_issues", []), 1):
            llms.append(
                {
                    "id": slug_issue_id(paper_id, "L", index),
                    "text": str(issue).strip(),
                }
            )
        if humans and llms:
            cases.append(
                {
                    "paper_id": paper_id,
                    "paper_title": record.get("paper_title", ""),
                    "source_format": source_format,
                    "human_issues": humans,
                    "llm_issues": llms,
                }
            )
    return cases


def select_cases(
    cases: list[dict[str, Any]], requested: list[str] | None, limit: int | None
) -> list[dict[str, Any]]:
    if requested:
        index = {case["paper_id"]: case for case in cases}
        missing = [paper for paper in requested if paper not in index]
        if missing:
            raise ValueError(f"Unknown paper IDs: {', '.join(missing)}")
        selected = [index[paper] for paper in requested]
    else:
        selected = cases
    return selected[:limit] if limit else selected


def chunk_cases(cases: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    if size < 1:
        raise ValueError("--terra-batch-size must be at least 1")
    return [cases[index : index + size] for index in range(0, len(cases), size)]


def prompt_case(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "paper_id": case["paper_id"],
        "paper_title": case.get("paper_title", ""),
        "human_issues": [
            {**issue, "text": anonymize_human_issue(issue["text"])}
            for issue in case["human_issues"]
        ],
        "llm_issues": case["llm_issues"],
    }


def build_terra_prompt(cases: list[dict[str, Any]]) -> str:
    payload = json.dumps([prompt_case(case) for case in cases], ensure_ascii=False)
    return f"""You are judging semantic concordance between independently prepared human research critiques and LLM-generated research critiques.

Use issue substance only. Ignore evaluator identity, author identity, prestige, and writing style. Do not browse, use tools, or read files.

Before matching, check whether the paper title, human concerns, and LLM concerns appear to describe the same study. Mark input_alignment=misaligned when they clearly concern different designs, outcomes, or manuscripts; use uncertain when the evidence is insufficient. Explain the check. Do not rescue a misaligned case by matching generic methodological vocabulary.

Rubric:
- exact: essentially the same concern, mechanism, and implication (normally 80-100).
- partial: a meaningful shared core, but one side is broader, narrower, or materially different (normally 45-79).
- related_but_distinct: same topic but different methodological claim or implication (normally 20-44).
- distinct: no substantive concordance (normally 0-19).

Map each human issue to zero, one, or several LLM issues. Do not force a match. A single LLM issue may be relevant to more than one human issue. Put only exact, partial, or genuinely borderline related pairs in judgments; list issues with no counterpart as unmatched. Explain the shared core and the most important difference. Confidence is confidence in the overlap classification, not confidence that either critique is correct.

Mark needs_sol_review=true when reasonable judges could cross either the 30-point coverage threshold or the 45-point partial-match boundary. Also list possible missed matches or grouping ambiguities in review_candidates. Use only the supplied stable IDs.

INPUT CASES:
{payload}

Return only JSON matching the supplied schema."""


def issue_lookup(cases: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for case in cases:
        for issue in case["human_issues"] + case["llm_issues"]:
            lookup[issue["id"]] = issue
    return lookup


def collect_sol_candidates(
    terra: dict[str, Any], max_candidates: int
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[tuple[str, tuple[str, ...]]] = set()
    for paper in terra.get("papers", []):
        # Do not spend Sol quota adjudicating pairs whose underlying paper/issue
        # alignment has not passed the first-stage check.
        if paper.get("input_alignment") != "aligned":
            continue
        paper_id = paper["paper_id"]
        for judgment in paper.get("judgments", []):
            score = judgment["overlap_score"]
            confidence = judgment["confidence"]
            ambiguous = (
                judgment["needs_sol_review"]
                or confidence < 70
                or 25 <= score <= 55
            )
            if ambiguous:
                key = (judgment["human_issue_id"], tuple(judgment["llm_issue_ids"]))
                if key not in seen:
                    seen.add(key)
                    candidates.append(
                        {
                            "paper_id": paper_id,
                            "human_issue_id": judgment["human_issue_id"],
                            "llm_issue_ids": judgment["llm_issue_ids"],
                            "terra_judgment": judgment,
                            "reason": "Terra marked or scored this judgment as ambiguous",
                        }
                    )
        for candidate in paper.get("review_candidates", []):
            key = (candidate["human_issue_id"], tuple(candidate["llm_issue_ids"]))
            if key not in seen:
                seen.add(key)
                candidates.append(
                    {
                        "paper_id": paper_id,
                        **candidate,
                        "terra_judgment": None,
                    }
                )
    candidates.sort(
        key=lambda x: (
            0 if (x.get("terra_judgment") or {}).get("needs_sol_review") else 1,
            (x.get("terra_judgment") or {}).get("confidence", 100),
        )
    )
    return candidates[:max_candidates]


def build_sol_prompt(
    candidates: list[dict[str, Any]], cases: list[dict[str, Any]]
) -> str:
    lookup = issue_lookup(cases)
    compact = []
    for candidate in candidates:
        human_issue = lookup[candidate["human_issue_id"]]
        compact.append(
            {
                **candidate,
                "human_issue": {
                    **human_issue,
                    "text": anonymize_human_issue(human_issue["text"]),
                },
                "llm_issues": [lookup[issue_id] for issue_id in candidate["llm_issue_ids"]],
            }
        )
    payload = json.dumps(compact, ensure_ascii=False)
    return f"""Act as a high-effort second adjudicator for difficult human–LLM critique concordance judgments.

Use issue substance only. Ignore names, prestige, and prose quality. Do not browse, use tools, or read files. Reconsider each candidate independently; Terra's judgment is context, not authority.

Labels and typical scores:
- exact: same concern, mechanism, and implication (80-100)
- partial: meaningful shared core with material scope or implication differences (45-79)
- related_but_distinct: same topic but a different methodological claim (20-44)
- distinct: no substantive concordance (0-19)

The key operational threshold is 30: a score at or above 30 counts as covered in the historical metric. Explain why the final judgment lies above or below that threshold. Confidence concerns the classification, not whether the critique itself is true.

AMBIGUOUS CANDIDATES:
{payload}

Return exactly one adjudication for each candidate, using only the supplied IDs and JSON schema."""


def clean_env() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if key not in API_ENV_KEYS}


def read_jsonl_usage(path: pathlib.Path) -> dict[str, int]:
    usage = {
        "input_tokens": 0,
        "cached_input_tokens": 0,
        "output_tokens": 0,
        "reasoning_output_tokens": 0,
    }
    for line in path.read_text(errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") != "turn.completed":
            continue
        for key in usage:
            usage[key] += int(event.get("usage", {}).get(key, 0) or 0)
    return usage


def codex_version(binary: pathlib.Path) -> str:
    proc = subprocess.run(
        [str(binary), "--version"], capture_output=True, text=True, env=clean_env()
    )
    return (proc.stdout or proc.stderr).strip()


def run_codex_call(
    *,
    call_name: str,
    prompt: str,
    schema: dict[str, Any],
    model: str,
    effort: str,
    run_dir: pathlib.Path,
    binary: pathlib.Path,
    timeout: int,
    force: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    calls_dir = run_dir / "calls"
    calls_dir.mkdir(parents=True, exist_ok=True)
    schema_path = calls_dir / f"{call_name}.schema.json"
    final_path = calls_dir / f"{call_name}.final.json"
    jsonl_path = calls_dir / f"{call_name}.events.jsonl"
    stderr_path = calls_dir / f"{call_name}.stderr.log"
    meta_path = calls_dir / f"{call_name}.meta.json"
    schema_path.write_text(json.dumps(schema, indent=2))

    if final_path.exists() and meta_path.exists() and not force:
        cached_meta = json.loads(meta_path.read_text())
        return (
            json.loads(final_path.read_text()),
            {**cached_meta, "artifact_reused_this_execution": True},
        )

    isolated_dir = run_dir / "isolated_codex_workdir"
    isolated_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        str(binary),
        "exec",
        "--ignore-user-config",
        "--ephemeral",
        "--sandbox",
        "read-only",
        "--skip-git-repo-check",
        "--cd",
        str(isolated_dir),
        "--model",
        model,
        "-c",
        f"model_reasoning_effort={effort}",
        "--output-schema",
        str(schema_path),
        "--output-last-message",
        str(final_path),
        "--json",
        "-",
    ]
    started = time.monotonic()
    proc = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        env=clean_env(),
        timeout=timeout,
    )
    duration = round(time.monotonic() - started, 3)
    jsonl_path.write_text(proc.stdout)
    stderr_path.write_text(proc.stderr)
    if proc.returncode != 0:
        raise RuntimeError(
            f"{call_name} failed with exit code {proc.returncode}; see {stderr_path}"
        )
    result = json.loads(final_path.read_text())
    meta = {
        "call_name": call_name,
        "model": model,
        "reasoning_effort": effort,
        "prompt_chars": len(prompt),
        "duration_seconds": duration,
        "usage": read_jsonl_usage(jsonl_path),
        "completed_at": utc_now(),
        "auth_surface": "ChatGPT/Codex subscription",
        "api_key_environment_removed": True,
        "artifact_reused_this_execution": False,
    }
    meta_path.write_text(json.dumps(meta, indent=2))
    return result, meta


def validate_ids(result: dict[str, Any], cases: list[dict[str, Any]]) -> None:
    allowed = set(issue_lookup(cases))
    allowed_papers = {case["paper_id"] for case in cases}
    for paper in result.get("papers", []):
        if paper["paper_id"] not in allowed_papers:
            raise ValueError(f"Unexpected paper ID: {paper['paper_id']}")
        for judgment in paper.get("judgments", []):
            ids = [judgment["human_issue_id"], *judgment["llm_issue_ids"]]
            unknown = [issue_id for issue_id in ids if issue_id not in allowed]
            if unknown:
                raise ValueError(f"Unknown issue IDs in Terra output: {unknown}")


def synthesize_results(
    cases: list[dict[str, Any]],
    terra: dict[str, Any],
    sol: dict[str, Any] | None,
) -> dict[str, Any]:
    sol_index: dict[tuple[str, tuple[str, ...]], dict[str, Any]] = {}
    if sol:
        for item in sol.get("adjudications", []):
            key = (item["human_issue_id"], tuple(item["llm_issue_ids"]))
            sol_index[key] = item

    case_index = {case["paper_id"]: case for case in cases}
    papers = []
    for terra_paper in terra["papers"]:
        final_judgments = []
        for item in terra_paper["judgments"]:
            key = (item["human_issue_id"], tuple(item["llm_issue_ids"]))
            if key in sol_index:
                final_judgments.append({**sol_index[key], "adjudicator": "Sol"})
            else:
                final_judgments.append({**item, "adjudicator": "Terra"})

        case = case_index[terra_paper["paper_id"]]
        covered_h = {
            item["human_issue_id"]
            for item in final_judgments
            if item["overlap_score"] >= 30 and item["label"] != "distinct"
        }
        covered_l = {
            issue_id
            for item in final_judgments
            if item["overlap_score"] >= 30 and item["label"] != "distinct"
            for issue_id in item["llm_issue_ids"]
        }
        h_total = len(case["human_issues"])
        l_total = len(case["llm_issues"])
        papers.append(
            {
                "paper_id": terra_paper["paper_id"],
                "final_judgments": final_judgments,
                "unmatched_human_ids": [
                    x["id"] for x in case["human_issues"] if x["id"] not in covered_h
                ],
                "unmatched_llm_ids": [
                    x["id"] for x in case["llm_issues"] if x["id"] not in covered_l
                ],
                "metrics": {
                    "threshold": 30,
                    "human_issue_count": h_total,
                    "llm_issue_count": l_total,
                    "covered_human_issue_count": len(covered_h),
                    "covered_llm_issue_count": len(covered_l),
                    "coverage_pct": round(100 * len(covered_h) / h_total, 1),
                    "llm_overlap_rate_pct": round(100 * len(covered_l) / l_total, 1),
                    "aggregate_eligible": terra_paper.get("input_alignment")
                    == "aligned",
                },
                "input_alignment": terra_paper.get(
                    "input_alignment", "not_assessed_legacy_output"
                ),
                "alignment_explanation": terra_paper.get(
                    "alignment_explanation",
                    "This pilot output predates the integrated alignment check.",
                ),
                "terra_overall_assessment": terra_paper["overall_assessment"],
            }
        )
    return {"generated_at": utc_now(), "papers": papers}


def sum_usage(call_meta: list[dict[str, Any]]) -> dict[str, int]:
    keys = [
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
    ]
    return {
        key: sum(meta.get("usage", {}).get(key, 0) for meta in call_meta)
        for key in keys
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run resumable Terra→Sol concordance judgments via codex exec"
    )
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--paper", action="append", help="Exact paper ID; repeatable")
    parser.add_argument("--limit", type=int, help="Use only the first N selected papers")
    parser.add_argument("--terra-model", default="gpt-5.6-terra")
    parser.add_argument("--terra-effort", default="high")
    parser.add_argument(
        "--terra-batch-size",
        type=int,
        default=3,
        help="Papers per Terra invocation; batching amortizes fixed Codex context",
    )
    parser.add_argument("--sol-model", default="gpt-5.6-sol")
    parser.add_argument("--sol-effort", default="high")
    parser.add_argument(
        "--sol-mode", choices=["none", "ambiguous"], default="ambiguous"
    )
    parser.add_argument("--max-sol-judgments", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--codex-binary")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    source_path = pathlib.Path(args.source).resolve()
    cases = select_cases(load_cases(source_path), args.paper, args.limit)
    if not cases:
        raise ValueError("No eligible cases selected")

    binary = pathlib.Path(args.codex_binary) if args.codex_binary else APP_CODEX
    if not binary.exists():
        resolved = shutil.which("codex")
        if not resolved:
            raise FileNotFoundError("Could not find a Codex CLI binary")
        binary = pathlib.Path(resolved)

    run_dir = ROOT / "results" / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    input_manifest = {
        "source": str(source_path.relative_to(ROOT)),
        "source_sha256": sha256_path(source_path),
        "source_format": cases[0]["source_format"],
        "selected_papers": [case["paper_id"] for case in cases],
        "stable_issue_ids": True,
        "external_prompt_anonymized": True,
        "human_issue_count": sum(len(case["human_issues"]) for case in cases),
        "llm_issue_count": sum(len(case["llm_issues"]) for case in cases),
    }
    (run_dir / "input_manifest.json").write_text(json.dumps(input_manifest, indent=2))

    batches = chunk_cases(cases, args.terra_batch_size)
    terra_prompts = [build_terra_prompt(batch) for batch in batches]
    preview = {
        "paper_count": len(cases),
        "paper_ids": [case["paper_id"] for case in cases],
        "terra_batch_size": args.terra_batch_size,
        "terra_batch_count": len(batches),
        "terra_prompt_chars_by_batch": [len(prompt) for prompt in terra_prompts],
        "terra_prompt_chars_total": sum(len(prompt) for prompt in terra_prompts),
        "terra_model": args.terra_model,
        "terra_effort": args.terra_effort,
        "sol_mode": args.sol_mode,
        "max_sol_judgments": args.max_sol_judgments,
    }
    if args.dry_run:
        print(json.dumps(preview, indent=2))
        return 0

    run_config: dict[str, Any] = {
        "run_id": args.run_id,
        "started_at": utc_now(),
        "status": "in_progress",
        "procedure": "Terra first pass; ambiguous pair-level cases only to Sol",
        "codex_binary": str(binary),
        "codex_version": codex_version(binary),
        "auth_surface": "ChatGPT/Codex subscription; API keys removed from child environment",
        "inputs": input_manifest,
        "configuration": preview,
    }
    (run_dir / "run_config.json").write_text(json.dumps(run_config, indent=2))

    terra_papers: list[dict[str, Any]] = []
    call_meta: list[dict[str, Any]] = []
    for index, (batch, prompt) in enumerate(zip(batches, terra_prompts), 1):
        terra_batch, terra_meta = run_codex_call(
            call_name=f"terra_batch_{index:03d}",
            prompt=prompt,
            schema=TERRA_SCHEMA,
            model=args.terra_model,
            effort=args.terra_effort,
            run_dir=run_dir,
            binary=binary,
            timeout=args.timeout,
            force=args.force,
        )
        validate_ids(terra_batch, batch)
        terra_papers.extend(terra_batch["papers"])
        call_meta.append(terra_meta)
    terra = {"papers": terra_papers}

    sol = None
    candidates = collect_sol_candidates(terra, args.max_sol_judgments)
    if args.sol_mode == "ambiguous" and candidates:
        sol_prompt = build_sol_prompt(candidates, cases)
        sol, sol_meta = run_codex_call(
            call_name="sol_ambiguous_001",
            prompt=sol_prompt,
            schema=SOL_SCHEMA,
            model=args.sol_model,
            effort=args.sol_effort,
            run_dir=run_dir,
            binary=binary,
            timeout=args.timeout,
            force=args.force,
        )
        call_meta.append(sol_meta)

    final = synthesize_results(cases, terra, sol)
    (run_dir / "concordance_results.json").write_text(
        json.dumps(final, indent=2, ensure_ascii=False)
    )
    run_config.update(
        {
            "completed_at": utc_now(),
            "status": "completed",
            "calls": call_meta,
            "total_usage": sum_usage(call_meta),
            "new_usage_this_execution": sum_usage(
                [
                    meta
                    for meta in call_meta
                    if not meta.get("artifact_reused_this_execution", False)
                ]
            ),
            "new_model_call_count": sum(
                not meta.get("artifact_reused_this_execution", False)
                for meta in call_meta
            ),
            "artifact_reused_call_count": sum(
                meta.get("artifact_reused_this_execution", False)
                for meta in call_meta
            ),
            "sol_candidate_count": len(candidates),
            "sol_call_made": sol is not None,
            "output": str((run_dir / "concordance_results.json").relative_to(ROOT)),
        }
    )
    (run_dir / "run_config.json").write_text(json.dumps(run_config, indent=2))
    print(json.dumps({"run_dir": str(run_dir), **run_config["total_usage"]}, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, FileNotFoundError, RuntimeError, subprocess.TimeoutExpired) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
