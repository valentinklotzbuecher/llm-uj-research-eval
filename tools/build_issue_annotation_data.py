#!/usr/bin/env python3
"""
Build a combined JSON dataset for manual issue-matching annotation.

Inputs:
- results/key_issues_comparison.json (human critique + GPT key issues)
- results/gpt52_pro_focal_jan2026/json/*.response.json (LLM full report)

Output:
- tools/issue_annotation_ui/data.json
"""

import json
import pathlib
import re
from urllib.parse import quote
from typing import List

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMPARISON_JSON = ROOT / "results" / "key_issues_comparison.json"
LLM_JSON_DIR = ROOT / "results" / "gpt52_pro_focal_jan2026" / "json"
OUTPUT_JSON = ROOT / "tools" / "issue_annotation_ui" / "data.json"
OUTPUT_JS = ROOT / "tools" / "issue_annotation_ui" / "data.js"

LABEL_ONLY_RE = re.compile(
    r"^(necessary|optional|optional but important|unsure|less important|possibly relevant|"
    r"probably important|probably correct|probably|note|notes|optional/desirable|"
    r"probably useful|maybe|possibly)$",
    re.IGNORECASE,
)


def _parse_llm_report(gpt_paper: str) -> dict:
    json_path = LLM_JSON_DIR / f"{gpt_paper}.response.json"
    if not json_path.exists():
        return {
            "assessment_summary": "",
            "key_issues": [],
        }

    data = json.loads(json_path.read_text(encoding="utf-8"))
    try:
        text_content = data["output"][1]["content"][0]["text"]
        parsed = json.loads(text_content)
        return {
            "assessment_summary": parsed.get("assessment_summary", ""),
            "key_issues": parsed.get("key_issues", []),
            "metrics": parsed.get("metrics", {}),
        }
    except (KeyError, IndexError, json.JSONDecodeError):
        return {
            "assessment_summary": "",
            "key_issues": [],
        }


ISSUE_START_RE = re.compile(r"^(\d+[\.\)]\s+|[\-\*]\s+)")
ENUM_RE = re.compile(r"^\s*(\d+)[\.\)]\s+")
SECOND_LEVEL_RE = re.compile(r"^\s*([a-zA-Z][\.\)]\s+|\d+[A-Za-z])")
SEVERITY_TEXT_RE = re.compile(r"^(necessary|optional|optional but important|unsure)$", re.IGNORECASE)


def _is_evaluator_line(line: str) -> bool:
    return bool(re.match(r"^(E\d+|Evaluator\s*\d+|Eval\.\s*\d+)[\s:]", line))

def _is_dr_line(line: str) -> bool:
    return bool(re.match(r"^DR[\s:]", line, re.IGNORECASE))

def _is_author_response(line: str) -> bool:
    return bool(re.match(r"^Author[s’']?\s+response[\s:]", line, re.IGNORECASE))


def _clean_issue_prefix(line: str) -> str:
    return re.sub(r"^(\d+[\.\)]\s+|[\-\*]\s+)", "", line).strip()

def _normalize_severity(header: str) -> str:
    h = header.lower()
    if "necessary" in h:
        return "necessary"
    if "optional" in h:
        return "optional"
    if any(word in h for word in ["unsure", "possibly", "probably", "less important", "maybe"]):
        return "unsure"
    if "note" in h:
        return "unsure"
    return ""


def _split_human_issues(text: str) -> List[dict]:
    """Heuristic split into candidate issues with severity labels."""
    if not text:
        return []

    issues = []
    current_severity = ""
    current_issue_lines = []
    section_lines = []

    def flush_issue():
        nonlocal current_issue_lines
        if not current_issue_lines:
            return
        cleaned = "\n".join(current_issue_lines).strip()
        cleaned = re.sub(r"^[\-\*\d\.\)\s]+", "", cleaned).strip()
        if cleaned:
            stripped = cleaned.strip().strip('"').strip("'").strip()
            if SEVERITY_TEXT_RE.match(stripped):
                current_issue_lines = []
                return
            if stripped.lower() == "(empty)":
                current_issue_lines = []
                return
            issues.append(
                {
                    "text": cleaned,
                    "severity": current_severity,
                }
            )
        current_issue_lines = []

    def flush_section(lines: List[str]) -> None:
        nonlocal current_issue_lines
        if not lines:
            return

        has_enum = any(ENUM_RE.match(line.strip()) for line in lines if line.strip())
        if has_enum:
            current_issue_lines = []
            for line in lines:
                raw = line.strip()
                if not raw:
                    continue
                if ENUM_RE.match(raw):
                    flush_issue()
                    current_issue_lines = [_clean_issue_prefix(raw)]
                    continue
                if _is_evaluator_line(raw) or _is_dr_line(raw) or _is_author_response(raw):
                    if current_issue_lines:
                        current_issue_lines.append(raw)
                    continue
                if SECOND_LEVEL_RE.match(raw) or line.startswith(" ") or raw.startswith("—"):
                    if current_issue_lines:
                        current_issue_lines.append(raw)
                    continue
                if current_issue_lines:
                    current_issue_lines.append(raw)
                else:
                    current_issue_lines = [raw]
            flush_issue()
            return

        # No enumeration detected: use sentence-boundary heuristics.
        current_issue_lines = []
        prev_line = ""
        for line in lines:
            raw = line.strip()
            if not raw:
                flush_issue()
                prev_line = ""
                continue

            if _is_evaluator_line(raw) or _is_dr_line(raw) or _is_author_response(raw):
                if current_issue_lines:
                    current_issue_lines.append(raw)
                prev_line = raw
                continue

            if SECOND_LEVEL_RE.match(raw) or line.startswith(" ") or raw.startswith("—"):
                if current_issue_lines:
                    current_issue_lines.append(raw)
                else:
                    current_issue_lines = [raw]
                prev_line = raw
                continue

            starts_new = False
            if not current_issue_lines:
                starts_new = True
            else:
                prev_end = prev_line.strip()[-1:] if prev_line else ""
                if prev_end in {".", "?", "!", "]", "”", "\""}:
                    if raw[:1].isupper() or raw.startswith("\"") or raw.startswith("“"):
                        starts_new = True

            if starts_new:
                flush_issue()
                current_issue_lines = [_clean_issue_prefix(raw)]
            else:
                current_issue_lines.append(raw)
            prev_line = raw
        flush_issue()

    lines = [line.rstrip() for line in text.splitlines()]
    for line in lines:
        raw = line.strip()
        if not raw:
            section_lines.append(line)
            continue

        header = raw.strip(" :").lower()
        if LABEL_ONLY_RE.match(header):
            flush_section(section_lines)
            section_lines = []
            current_severity = _normalize_severity(header) or current_severity
            continue
        section_lines.append(line)

    flush_section(section_lines)

    return issues


def main() -> None:
    comparison = json.loads(COMPARISON_JSON.read_text(encoding="utf-8"))

    papers = []
    for item in comparison:
        gpt_paper = item.get("gpt_paper")
        coda_title = item.get("coda_title")
        coda_critique = item.get("coda_critique", "")

        llm = _parse_llm_report(gpt_paper)
        human_issue_suggestions = _split_human_issues(coda_critique)

        papers.append(
            {
                "paper_id": gpt_paper,
                "paper_title": coda_title,
                "unjournal_search_url": f"https://unjournal.pubpub.org/search?q={quote(coda_title or gpt_paper)}",
                "human_critique": coda_critique,
                "human_issue_suggestions": human_issue_suggestions,
                "llm_key_issues": llm.get("key_issues", []),
                "llm_assessment_summary": llm.get("assessment_summary", ""),
                "llm_metrics": llm.get("metrics", {}),
            }
        )

    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {"papers": papers}
    OUTPUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    OUTPUT_JS.write_text(
        "window.ANNOTATION_DATA = " + json.dumps(payload, indent=2) + ";\n",
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT_JSON}")
    print(f"Wrote {OUTPUT_JS}")


if __name__ == "__main__":
    main()
