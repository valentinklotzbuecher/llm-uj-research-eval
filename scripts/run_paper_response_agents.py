#!/usr/bin/env python3
"""Run bounded, evidence-only paper-response review agents without API keys.

The default runner is the locally authenticated Claude Code CLI in print mode.
It uses subscription authentication, disables tools, applies JSON Schemas, and
gives each agent only the evidence packet needed for its role. No agent result
is a publication decision; every output is routed to human review.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "data" / "paper_response_evidence"
QUEUE_PATH = EVIDENCE_DIR / "review_queue.json"
RUNS_DIR = ROOT / "results" / "paper_response_evidence" / "agent_runs"


ATOM_SCHEMA = {
    "type": "object",
    "properties": {
        "atoms": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "atom_id": {"type": "string", "pattern": "^atom-[0-9]{3}$"},
                    "atom_type": {"type": "string", "enum": ["evaluator_suggestion", "author_acknowledgement"]},
                    "category": {"type": "string"},
                    "description": {"type": "string"},
                    "source_file": {"type": "string"},
                    "quote": {"type": "string"},
                    "line_start": {"type": "integer", "minimum": 1},
                },
                "required": ["atom_id", "atom_type", "category", "description", "source_file", "quote", "line_start"],
                "additionalProperties": False,
            },
        },
        "limitations": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["atoms", "limitations"],
    "additionalProperties": False,
}

CHANGE_SCHEMA = {
    "type": "object",
    "properties": {
        "classifications": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "card_id": {"type": "string", "pattern": "^chg-[0-9]{4}$"},
                    "substantive": {"type": "boolean"},
                    "category": {
                        "type": "string",
                        "enum": ["method_or_data", "estimate_or_result", "interpretation_or_conclusion", "framing", "correction", "formatting_or_unclear"],
                    },
                    "reason": {"type": "string"},
                    "evidence_pages": {"type": "array", "items": {"type": "integer"}},
                },
                "required": ["card_id", "substantive", "category", "reason", "evidence_pages"],
                "additionalProperties": False,
            },
        },
        "limitations": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["classifications", "limitations"],
    "additionalProperties": False,
}

LINK_SCHEMA = {
    "type": "object",
    "properties": {
        "candidate_links": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "atom_id": {"type": "string", "pattern": "^atom-[0-9]{3}$"},
                    "card_id": {"type": "string", "pattern": "^chg-[0-9]{4}$"},
                    "link_label": {
                        "type": "string",
                        "enum": ["explicit_acknowledgement", "documented_alignment", "temporal_only", "no_documented_link"],
                    },
                    "specificity": {"type": "string", "enum": ["high", "medium", "low"]},
                    "reason": {"type": "string"},
                    "alternative_explanations": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["atom_id", "card_id", "link_label", "specificity", "reason", "alternative_explanations"],
                "additionalProperties": False,
            },
        },
        "unresolved": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["candidate_links", "unresolved"],
    "additionalProperties": False,
}

ADJUDICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "paper_label": {
            "type": "string",
            "enum": ["explicit_author_acknowledgement", "documented_aligned_revision", "unknown_temporal_association", "no_documented_link", "insufficient_evidence"],
        },
        "accepted_links": {"type": "array", "items": {"type": "object"}},
        "rejected_links": {"type": "array", "items": {"type": "object"}},
        "missing_evidence": {"type": "array", "items": {"type": "string"}},
        "human_checks_required": {"type": "array", "items": {"type": "string"}},
        "summary": {"type": "string"},
    },
    "required": ["paper_label", "accepted_links", "rejected_links", "missing_evidence", "human_checks_required", "summary"],
    "additionalProperties": False,
}


def now_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def numbered_document(path: Path, max_chars: int = 70000) -> str:
    lines = path.read_text(errors="replace").splitlines()
    rendered = "\n".join(f"L{index}: {line}" for index, line in enumerate(lines, start=1))
    return rendered[:max_chars]


def parse_cli_result(stdout: str) -> dict[str, Any]:
    payload = json.loads(stdout)
    for key in ("structured_output", "result"):
        value = payload.get(key) if isinstance(payload, dict) else None
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError:
                pass
    if isinstance(payload, dict) and set(payload) & {"atoms", "classifications", "candidate_links", "paper_label"}:
        return payload
    raise ValueError("Claude CLI output did not contain structured JSON")


def run_claude(prompt: str, schema: dict[str, Any], model: str, timeout: int) -> dict[str, Any]:
    binary = shutil.which("claude") or "/Users/yosemite/.local/bin/claude"
    env = dict(os.environ)
    for key in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
        env.pop(key, None)
    cmd = [
        binary, "-p", "--model", model, "--safe-mode", "--tools", "",
        "--permission-mode", "dontAsk", "--no-session-persistence",
        "--output-format", "json", "--json-schema", json.dumps(schema), prompt,
    ]
    proc = subprocess.run(
        cmd, cwd=ROOT, env=env, capture_output=True, text=True, timeout=timeout,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Claude CLI failed ({proc.returncode}): {proc.stderr[-3000:]}")
    return {"parsed": parse_cli_result(proc.stdout), "stderr_tail": proc.stderr[-2000:]}


def queue_item(paper_id: str) -> dict[str, Any]:
    queue = load_json(QUEUE_PATH).get("items", [])
    matches = [item for item in queue if item["paper_id"] == paper_id]
    if not matches:
        raise SystemExit(f"Paper ID not found in review queue: {paper_id}")
    return matches[0]


def validate_atoms(result: dict[str, Any], source_paths: list[Path]) -> list[str]:
    errors: list[str] = []
    by_name = {str(path.relative_to(ROOT)): path.read_text(errors="replace") for path in source_paths}
    seen_ids: set[str] = set()
    for atom in result.get("atoms", []):
        atom_id = atom.get("atom_id")
        if not atom_id or atom_id in seen_ids:
            errors.append(f"duplicate or missing atom_id: {atom_id}")
        seen_ids.add(atom_id)
        source = atom.get("source_file")
        quote = atom.get("quote", "")
        if source not in by_name:
            errors.append(f"unknown atom source: {source}")
            continue
        source_lines = by_name[source].splitlines()
        line_start = atom.get("line_start", 0)
        window = " ".join(source_lines[max(0, line_start - 3):line_start + 2])
        quote_tokens = re.findall(r"[a-z0-9]+", quote.casefold())
        window_tokens = re.findall(r"[a-z0-9]+", window.casefold())
        source_tokens = re.findall(r"[a-z0-9]+", by_name[source].casefold())
        quote_key = " ".join(quote_tokens)
        if len(quote_tokens) < 5:
            errors.append(f"quote too short for {atom_id}")
        elif quote_key not in " ".join(source_tokens):
            errors.append(f"quote not found for {atom_id}")
        elif quote_key not in " ".join(window_tokens):
            errors.append(f"line anchor mismatch for {atom_id}")
    return errors


def validate_change_classifications(result: dict[str, Any], valid_cards: set[str]) -> list[str]:
    returned = [item.get("card_id") for item in result.get("classifications", [])]
    errors = [f"unknown change card: {card}" for card in returned if card not in valid_cards]
    errors.extend(f"duplicate change card: {card}" for card in set(returned) if returned.count(card) > 1)
    return errors


def validate_links(result: dict[str, Any], atom_ids: set[str], card_ids: set[str]) -> list[str]:
    errors: list[str] = []
    for link in result.get("candidate_links", []):
        if link.get("atom_id") not in atom_ids:
            errors.append(f"unknown atom in link: {link.get('atom_id')}")
        if link.get("card_id") not in card_ids:
            errors.append(f"unknown card in link: {link.get('card_id')}")
    return errors


def run_agents(args: argparse.Namespace) -> dict[str, Any]:
    item = queue_item(args.paper_id)
    if item["status"] != "ready_for_agent_triage" and not args.allow_unvalidated:
        raise SystemExit(
            "This paper still needs human identity/timeline validation. "
            "Use --allow-unvalidated only for a clearly marked exploratory run."
        )
    comparison = load_json(ROOT / item["comparison_path"])
    material_cards = [card for card in comparison["change_cards"] if card["material"]]
    evaluation_paths = [ROOT / path for path in item["evaluation_files"]]
    # Exact summaries often repeat linked evaluations. When individual reports
    # exist, omit the summary to avoid duplicate atoms and reduce usage.
    if len(evaluation_paths) > 1:
        evaluation_paths = evaluation_paths[1:]
    source_paths = evaluation_paths + [ROOT / path for path in item["public_response_files"]]
    documents = "\n\n".join(
        f"===== {path.relative_to(ROOT)} =====\n{numbered_document(path)}" for path in source_paths
    )
    cards_payload = json.dumps(material_cards[:80], indent=2, ensure_ascii=False)

    run_dir = RUNS_DIR / comparison["comparison_id"] / now_slug()
    run_dir.mkdir(parents=True, exist_ok=True)
    packet = {
        "paper_id": item["paper_id"], "paper_title": item["paper_title"],
        "comparison_id": comparison["comparison_id"],
        "comparison_path": item["comparison_path"],
        "evaluation_files": item["evaluation_files"],
        "public_response_files": item["public_response_files"],
        "material_change_cards": len(material_cards),
        "exploratory_unvalidated": item["status"] != "ready_for_agent_triage",
    }
    write_json(run_dir / "packet.json", packet)
    if args.dry_run:
        return {"status": "packet_created", "run_dir": str(run_dir), **packet}

    atom_prompt = f"""You are the evaluation-document atomizer in an evidence audit.
You see ONLY public evaluation and public author-response documents, not paper revisions.
Extract atomic, specific evaluator suggestions and explicit author acknowledgements.
Assign atom IDs exactly as atom-001, atom-002, and so on. Every atom must include
an exact contiguous 6-25 word quote copied from the source, without ellipses or
paraphrase, plus the exact source filename and the first source line containing it.
Do not infer whether a paper changed. Do not infer causality. Return only schema-valid JSON.

PAPER: {item['paper_title']}

DOCUMENTS:\n{documents}"""
    atom_run = run_claude(atom_prompt, ATOM_SCHEMA, args.triage_model, args.timeout)
    atom_errors = validate_atoms(atom_run["parsed"], source_paths)
    write_json(run_dir / "01_atoms.json", {**atom_run, "validation_errors": atom_errors})

    change_prompt = f"""You are the blinded paper-change classifier in an evidence audit.
You see ONLY deterministic before/after change cards, not evaluator documents.
Classify whether each card is substantive and its type. Cite only card IDs and supplied pages.
Do not infer why the change happened. Treat extraction artifacts conservatively.
Return only schema-valid JSON.

PAPER: {item['paper_title']}

CHANGE CARDS:\n{cards_payload}"""
    change_run = run_claude(change_prompt, CHANGE_SCHEMA, args.triage_model, args.timeout)
    card_ids = {card["card_id"] for card in material_cards}
    change_errors = validate_change_classifications(change_run["parsed"], card_ids)
    write_json(run_dir / "02_change_classifications.json", {**change_run, "validation_errors": change_errors})

    link_prompt = f"""You are the skeptical link assessor in an evidence audit.
Use ONLY the supplied validated atom and change-card IDs. Try to disprove evaluator influence.
Timing alone is temporal_only. documented_alignment requires a specific recommendation and a
specific matching change. explicit_acknowledgement requires a public author statement.
List plausible alternatives such as journal review, coauthor decisions, new data, or routine revision.
Emit candidate_links ONLY when both a real atom-NNN and chg-NNNN are linked. Put atoms with no
matching change in unresolved; never emit blank IDs. No evidence means unresolved, never proof of no influence.
Return only schema-valid JSON.

ATOMS:\n{json.dumps(atom_run['parsed'], indent=2, ensure_ascii=False)}

CHANGE CLASSIFICATIONS:\n{json.dumps(change_run['parsed'], indent=2, ensure_ascii=False)}"""
    link_run = run_claude(link_prompt, LINK_SCHEMA, args.triage_model, args.timeout)
    atom_ids = {atom["atom_id"] for atom in atom_run["parsed"].get("atoms", [])}
    link_errors = validate_links(link_run["parsed"], atom_ids, card_ids)
    write_json(run_dir / "03_skeptical_links.json", {**link_run, "validation_errors": link_errors})

    candidate_links = link_run["parsed"].get("candidate_links", [])
    needs_adjudication = bool(
        atom_errors or change_errors or link_errors or
        any(link["link_label"] in {"explicit_acknowledgement", "documented_alignment"} for link in candidate_links)
    )
    adjudication = None
    if needs_adjudication:
        adjudication_prompt = f"""You are the senior adjudicator for a paper-response evidence audit.
Review the bounded evidence outputs and their mechanical validation errors. Be conservative.
Reject any link whose IDs or quotes failed validation. Timing is not attribution. A publication-facing
positive label still requires human review. Return a proposed evidence label, missing evidence, and
specific human checks. Do not report a probability or causal percentage.

PAPER: {item['paper_title']}
ATOM OUTPUT:\n{json.dumps(atom_run['parsed'], indent=2, ensure_ascii=False)}
CHANGE OUTPUT:\n{json.dumps(change_run['parsed'], indent=2, ensure_ascii=False)}
SKEPTICAL LINK OUTPUT:\n{json.dumps(link_run['parsed'], indent=2, ensure_ascii=False)}
VALIDATION ERRORS:\n{json.dumps(atom_errors + change_errors + link_errors, indent=2)}"""
        adjudication = run_claude(adjudication_prompt, ADJUDICATION_SCHEMA, args.adjudicator_model, args.timeout)
        write_json(run_dir / "04_adjudication.json", adjudication)

    summary = {
        "status": "human_review_required", "created_at": datetime.now(timezone.utc).isoformat(),
        "run_dir": str(run_dir.relative_to(ROOT)), "paper_id": item["paper_id"],
        "comparison_id": comparison["comparison_id"],
        "triage_model": args.triage_model, "adjudicator_model": args.adjudicator_model,
        "validation_errors": atom_errors + change_errors + link_errors,
        "adjudication_run": bool(adjudication),
        "proposed_label": adjudication["parsed"].get("paper_label") if adjudication else "no_positive_link_to_adjudicate",
        "human_decision_required": True,
    }
    write_json(run_dir / "summary.json", summary)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper-id", required=True)
    parser.add_argument("--triage-model", default="haiku")
    parser.add_argument("--adjudicator-model", default="sonnet")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--dry-run", action="store_true", help="create a bounded packet without model calls")
    parser.add_argument("--allow-unvalidated", action="store_true")
    args = parser.parse_args()
    if not QUEUE_PATH.exists():
        raise SystemExit("Review queue not found. Run paper_response_evidence.py refresh first.")
    result = run_agents(args)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
