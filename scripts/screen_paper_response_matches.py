#!/usr/bin/env python3
"""Deterministically screen evaluator suggestions against later-paper changes.

This is a conservative prioritisation tool, not an attribution model. It consumes
version-validated comparison bundles and either previously structured suggestion
atoms or sentence-level suggestion cues. Candidate links are discounted when the
same concepts were already present before evaluation and benchmarked against
cross-paper placebo matches. Every output remains human-review-required.
"""

from __future__ import annotations

import argparse
import csv
import functools
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, NamedTuple


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "data" / "paper_response_evidence"
QUEUE_PATH = EVIDENCE_DIR / "review_queue.json"
COMPARISON_DIR = EVIDENCE_DIR / "comparisons"
RUNS_DIR = ROOT / "results" / "paper_response_evidence" / "agent_runs"
OUTPUT_PATH = ROOT / "results" / "paper_response_evidence" / "deterministic_screen.json"
CSV_PATH = ROOT / "results" / "paper_response_evidence" / "deterministic_screen.csv"

ELIGIBLE_TIMELINES = {
    "metadata_claim_post_evaluation",
    "manually_verified_post_evaluation",
}
HARD_BLOCKERS = {
    "ambiguous_before_version",
    "before_identity_not_verified",
    "before_version_missing",
    "after_identity_not_verified",
    "after_version_fetch_failed",
    "timeline_not_verified",
    "after_version_predates_evaluation",
    "known_revised_endpoint_unavailable",
    "evaluation_documents_not_exactly_mapped",
}
STOPWORDS = {
    "about", "above", "after", "again", "against", "also", "among", "because",
    "before", "being", "below", "between", "both", "could", "does", "doing",
    "during", "each", "from", "further", "have", "having", "into", "itself",
    "more", "most", "other", "over", "paper", "results", "same", "should",
    "some", "study", "such", "than", "that", "their", "them", "then", "there",
    "these", "they", "this", "those", "through", "under", "using", "very",
    "what", "when", "where", "which", "while", "with", "would", "authors",
    "author", "analysis", "comment", "comments", "evaluation", "evaluator",
    "review", "reviewer", "report", "include", "including", "provide", "suggest",
    "recommend", "important", "useful", "well", "work", "need", "needs", "given",
    "least", "main", "overall", "used", "uses", "affect", "estimated", "estimate",
}
SUGGESTION_CUE = re.compile(
    r"\b(should|could|recommend(?:ed|s|ation)?|suggest(?:ed|s|ion)?|would benefit|"
    r"needs? to|ought to|it would be useful|it would help|please|encourage)\b",
    re.I,
)
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'])")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def normalise_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


@functools.lru_cache(maxsize=1024)
def tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-z][a-z0-9-]{3,}", text.casefold())
        if token not in STOPWORDS and not token.isdigit()
    }


@functools.lru_cache(maxsize=1024)
def bigrams(text: str) -> set[str]:
    ordered = [
        token
        for token in re.findall(r"[a-z][a-z0-9-]{3,}", text.casefold())
        if token not in STOPWORDS and not token.isdigit()
    ]
    return {f"{a} {b}" for a, b in zip(ordered, ordered[1:])}


def max_before_window_coverage(cue_terms: set[str], text: str, window: int = 80) -> float:
    return _cached_before_window_coverage(frozenset(cue_terms), text, window)


@functools.lru_cache(maxsize=1024)
def _cached_before_window_coverage(
    cue_terms: frozenset[str], text: str, window: int
) -> float:
    """Maximum cue-term coverage in a local window anywhere in the earlier paper."""
    ordered = [
        token
        for token in re.findall(r"[a-z][a-z0-9-]{3,}", text.casefold())
        if token not in STOPWORDS and not token.isdigit()
    ]
    if not cue_terms or not ordered:
        return 0.0
    denominator = max(4, len(cue_terms))
    step = max(20, window // 2)
    starts = range(0, len(ordered), step)
    return max(
        len(cue_terms & set(ordered[start:start + window])) / denominator
        for start in starts
    )


def line_anchor_valid(atom: dict[str, Any], root: Path = ROOT) -> bool:
    source = root / atom.get("source_file", "")
    quote = normalise_space(atom.get("quote", "")).casefold()
    line = atom.get("line_start")
    if not source.exists() or not quote or not isinstance(line, int) or line < 1:
        return False
    lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
    start = max(0, line - 3)
    end = min(len(lines), line + 3)
    window = normalise_space(" ".join(lines[start:end])).casefold()
    return quote in window


def latest_agent_atoms(comparison_id: str, root: Path = ROOT) -> list[dict[str, Any]]:
    base = root / "results" / "paper_response_evidence" / "agent_runs" / comparison_id
    atom_files = sorted(base.glob("*/01_atoms.json"), reverse=True) if base.exists() else []
    for path in atom_files:
        payload = load_json(path, {})
        atoms = payload.get("parsed", {}).get("atoms", [])
        if atoms:
            return atoms
    return []


def heuristic_atoms(files: list[str], root: Path = ROOT, limit: int = 100) -> list[dict[str, Any]]:
    atoms: list[dict[str, Any]] = []
    for relative in files:
        path = root / relative
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        for line_number, line in enumerate(lines, 1):
            for sentence in SENTENCE_SPLIT.split(normalise_space(line)):
                if not SUGGESTION_CUE.search(sentence) or not 35 <= len(sentence) <= 600:
                    continue
                if len(tokens(sentence)) < 3:
                    continue
                atoms.append({
                    "atom_id": f"cue-{len(atoms) + 1:03d}",
                    "atom_type": "evaluator_suggestion",
                    "category": "heuristic suggestion cue",
                    "description": sentence,
                    "source_file": relative,
                    "quote": sentence,
                    "line_start": line_number,
                    "extraction_method": "deterministic_sentence_cue",
                })
                if len(atoms) >= limit:
                    return atoms
    return atoms


def suggestion_text(atom: dict[str, Any]) -> str:
    return normalise_space(" ".join([
        atom.get("category", ""), atom.get("description", ""), atom.get("quote", "")
    ]))


class MatchScore(NamedTuple):
    score: float
    coverage: float
    novelty: float
    whole_before_max_coverage: float
    new_terms: tuple[str, ...]
    preexisting_terms: tuple[str, ...]
    new_bigrams: tuple[str, ...]


def score_atom_card(
    atom: dict[str, Any], card: dict[str, Any], global_before_text: str = ""
) -> MatchScore:
    cue_text = suggestion_text(atom)
    cue_terms = tokens(cue_text)
    local_before_text = card.get("before_excerpt", "")
    before_terms = tokens(local_before_text)
    after_terms = tokens(card.get("after_excerpt", ""))
    newly_added = after_terms - before_terms
    new_matches = cue_terms & newly_added
    preexisting_matches = cue_terms & before_terms
    cue_bigrams = bigrams(cue_text)
    before_bigrams = bigrams(global_before_text or local_before_text)
    after_bigrams = bigrams(card.get("after_excerpt", ""))
    new_bigram_matches = cue_bigrams & (after_bigrams - before_bigrams)
    denominator = max(4, len(cue_terms))
    coverage = len(new_matches) / denominator
    novelty = len(new_matches) / max(1, len(new_matches) + len(preexisting_matches))
    baseline_coverage = max_before_window_coverage(cue_terms, global_before_text)
    incremental_coverage = max(0.0, coverage - baseline_coverage)
    section_bonus = min(
        0.08,
        0.02 * len(tokens(card.get("section", "")) & cue_terms),
    )
    phrase_bonus = min(0.18, 0.06 * len(new_bigram_matches))
    score = min(
        1.0,
        coverage * (0.40 + 0.40 * novelty)
        + 0.20 * incremental_coverage
        + phrase_bonus
        + section_bonus,
    )
    return MatchScore(
        score=round(score, 4), coverage=round(coverage, 4), novelty=round(novelty, 4),
        whole_before_max_coverage=round(baseline_coverage, 4),
        new_terms=tuple(sorted(new_matches)),
        preexisting_terms=tuple(sorted(preexisting_matches)),
        new_bigrams=tuple(sorted(new_bigram_matches)),
    )


def best_match(
    atom: dict[str, Any], cards: list[dict[str, Any]], global_before_text: str = ""
) -> tuple[dict[str, Any] | None, MatchScore]:
    empty = MatchScore(0.0, 0.0, 0.0, 0.0, (), (), ())
    best_card: dict[str, Any] | None = None
    best_score = empty
    for card in cards:
        if not card.get("material"):
            continue
        score = score_atom_card(atom, card, global_before_text)
        if score.score > best_score.score:
            best_card, best_score = card, score
    return best_card, best_score


def percentile_against_placebos(score: float, placebo_scores: list[float]) -> float:
    if not placebo_scores:
        return 0.5
    below = sum(value < score for value in placebo_scores)
    tied = sum(value == score for value in placebo_scores)
    return round((below + 0.5 * tied) / len(placebo_scores), 4)


def priority(score: MatchScore, placebo_percentile: float) -> str | None:
    specific = len(score.new_terms)
    phrases = len(score.new_bigrams)
    if score.whole_before_max_coverage >= score.coverage and not phrases:
        if specific >= 2 and score.coverage >= 0.15 and placebo_percentile >= 0.60:
            return "low"
        return None
    if specific >= 4 and score.coverage >= 0.30 and placebo_percentile >= 0.90 and score.novelty >= 0.50:
        return "high"
    if specific >= 3 and score.coverage >= 0.20 and placebo_percentile >= 0.75 and score.novelty >= 0.40:
        return "medium"
    if specific >= 2 and (phrases or score.coverage >= 0.15) and placebo_percentile >= 0.60:
        return "low"
    return None


def queue_eligibility(item: dict[str, Any], timeline: str | None) -> tuple[bool, list[str]]:
    reasons = sorted(set(item.get("review_reasons", [])) & HARD_BLOCKERS)
    if timeline not in ELIGIBLE_TIMELINES:
        reasons.append(f"ineligible_timeline:{timeline or 'missing'}")
    if not item.get("comparison_path"):
        reasons.append("comparison_missing")
    if not item.get("evaluation_files"):
        reasons.append("evaluation_files_missing")
    return not reasons, sorted(set(reasons))


def run(root: Path = ROOT) -> dict[str, Any]:
    queue = load_json(root / "data" / "paper_response_evidence" / "review_queue.json", {}).get("items", [])
    registry = load_json(root / "data" / "paper_response_evidence" / "registry.json", {}).get("papers", {})
    bundles: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for item in queue:
        paper = registry.get(item.get("paper_id"), {})
        eligible, reasons = queue_eligibility(item, paper.get("timeline_status"))
        if not eligible:
            if item.get("comparison_id"):
                excluded.append({
                    "paper_id": item.get("paper_id"), "paper_title": item.get("paper_title"),
                    "comparison_id": item.get("comparison_id"), "reasons": reasons,
                })
            continue
        comparison = load_json(root / item["comparison_path"], {})
        cards = [card for card in comparison.get("change_cards", []) if card.get("material")]
        atoms = latest_agent_atoms(item["comparison_id"], root)
        method = "structured_agent_atoms" if atoms else "deterministic_sentence_cues"
        if not atoms:
            atoms = heuristic_atoms(item.get("evaluation_files", []), root)
        anchored = [atom for atom in atoms if line_anchor_valid(atom, root)]
        before_version = next(
            (
                version for version in paper.get("versions", [])
                if version.get("version_id") == comparison.get("before_version_id")
            ),
            {},
        )
        before_extract = load_json(root / before_version.get("extraction", {}).get("path", ""), {})
        global_before_text = "\n".join(
            page.get("text", "") for page in before_extract.get("pages", [])
        )
        bundles.append({
            "item": item, "paper": paper, "comparison": comparison, "cards": cards,
            "atoms": anchored, "atoms_unanchored": len(atoms) - len(anchored), "method": method,
            "global_before_text": global_before_text,
        })

    cases: list[dict[str, Any]] = []
    flat_rows: list[dict[str, Any]] = []
    for bundle in bundles:
        candidates: list[dict[str, Any]] = []
        for atom in bundle["atoms"]:
            card, score = best_match(atom, bundle["cards"], bundle["global_before_text"])
            if card is None:
                continue
            placebo_scores: list[float] = []
            for other in bundles:
                if other is bundle:
                    continue
                _, placebo = best_match(atom, other["cards"], other["global_before_text"])
                placebo_scores.append(placebo.score)
            percentile = percentile_against_placebos(score.score, placebo_scores)
            label = priority(score, percentile)
            if not label:
                continue
            candidate = {
                "priority": label,
                "atom_id": atom.get("atom_id"),
                "card_id": card.get("card_id"),
                "suggestion": atom.get("description") or atom.get("quote"),
                "suggestion_quote": atom.get("quote"),
                "source_file": atom.get("source_file"),
                "line_start": atom.get("line_start"),
                "changed_section": card.get("section"),
                "score": score.score,
                "coverage": score.coverage,
                "novelty": score.novelty,
                "whole_before_max_coverage": score.whole_before_max_coverage,
                "placebo_percentile": percentile,
                "new_matched_terms": list(score.new_terms),
                "preexisting_matched_terms": list(score.preexisting_terms),
                "new_matched_bigrams": list(score.new_bigrams),
                "interpretation": "candidate_for_human_review_not_evidence_of_influence",
            }
            candidates.append(candidate)
            flat_rows.append({
                "paper_id": bundle["item"]["paper_id"],
                "paper_title": bundle["item"]["paper_title"],
                **candidate,
            })
        candidates.sort(key=lambda value: (value["priority"] != "high", -value["score"]))
        cases.append({
            "paper_id": bundle["item"]["paper_id"],
            "paper_title": bundle["item"]["paper_title"],
            "comparison_id": bundle["item"]["comparison_id"],
            "timeline_status": bundle["paper"].get("timeline_status"),
            "suggestion_extraction": bundle["method"],
            "suggestions_anchored": len(bundle["atoms"]),
            "suggestions_rejected_unanchored": bundle["atoms_unanchored"],
            "material_change_cards": len(bundle["cards"]),
            "candidate_links": candidates,
            "candidate_counts": {
                level: sum(candidate["priority"] == level for candidate in candidates)
                for level in ("high", "medium", "low")
            },
            "human_decision_required": True,
        })

    payload = {
        "schema_version": 1,
        "created_at": utc_now(),
        "purpose": "conservative suggestion-to-change candidate prioritisation",
        "non_claim": "candidate links are not evidence that an evaluation caused a paper change",
        "controls": [
            "verified before/after identity and eligible timeline",
            "exactly mapped public evaluation documents",
            "source quote and line-anchor validation",
            "new-term comparison against the pre-evaluation version",
            "cross-paper placebo-score benchmark",
            "human review required for every candidate",
        ],
        "summary": {
            "queue_items": len(queue),
            "eligible_comparison_cases": len(cases),
            "excluded_comparison_cases": len(excluded),
            "suggestions_anchored": sum(case["suggestions_anchored"] for case in cases),
            "suggestions_rejected_unanchored": sum(case["suggestions_rejected_unanchored"] for case in cases),
            "candidate_links": len(flat_rows),
            "high_priority_candidates": sum(row["priority"] == "high" for row in flat_rows),
            "medium_priority_candidates": sum(row["priority"] == "medium" for row in flat_rows),
            "low_priority_candidates": sum(row["priority"] == "low" for row in flat_rows),
        },
        "excluded_comparisons": excluded,
        "cases": cases,
    }
    output = root / "results" / "paper_response_evidence" / "deterministic_screen.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    csv_path = root / "results" / "paper_response_evidence" / "deterministic_screen.csv"
    fields = [
        "paper_id", "paper_title", "priority", "atom_id", "card_id", "suggestion",
        "suggestion_quote", "source_file", "line_start", "changed_section", "score",
        "coverage", "novelty", "whole_before_max_coverage", "placebo_percentile", "new_matched_terms",
        "preexisting_matched_terms", "new_matched_bigrams", "interpretation",
    ]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in flat_rows:
            serialised = dict(row)
            for field in ("new_matched_terms", "preexisting_matched_terms", "new_matched_bigrams"):
                serialised[field] = " | ".join(serialised[field])
            writer.writerow(serialised)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root")
    args = parser.parse_args()
    payload = run(args.root.resolve())
    print(json.dumps(payload["summary"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
