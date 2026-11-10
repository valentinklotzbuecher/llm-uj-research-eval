#!/usr/bin/env python3
"""
Critique-overlap pilot: a leak-controlled way to compare the issues a model
raises about a paper with the issues human evaluators raised, on papers beyond
the original 12.

Stages (each is resumable and writes under results/<run-id>/):

  select    Pick pilot papers from data/critique_eligibility_manifest.json by a
            fixed rule that looks at no outcome: eligible, at least two
            substantive individual evaluations, PDF dated before the first
            evaluation; ordered by SHA-256 of the paper label; first N.
  extract   A cheap model (Claude Haiku 5.5) splits each published evaluation
            into separate issues. It receives only that evaluation's text
            (front matter removed): never the paper, never model output. Each
            issue carries a verbatim quote, which is checked against the source.
  generate  Model key issues come from scripts/run_headless_claude_misses.py
            condition A (Claude Opus 5.5, effort high, PDF only, no tools). That
            call never sees an evaluation. Existing condition-A outputs from the
            2026-11-04 run are reused when the paper is the same.
  judge     Two judges match issues between two unlabeled, shuffled lists:
            GPT (via `codex exec`, subscription) and Claude Sonnet 5.5 (API,
            same family as the generator; reported separately for that reason).
            Three kinds of pairing use the identical prompt:
              real         human issues vs model issues, same paper
              placebo      human issues of one paper vs model issues of another
              human_human  evaluator 1 issues vs evaluator 2 issues, same paper
  summarize Coverage and overlap rates with explicit denominators, the placebo
            floor, the human-to-human baseline, judge agreement, and cost.

This is an exploratory diagnostic. Its outputs are not pooled with the
one-shot benchmark or the manuscript chapters. No refusal fallbacks are used:
a refusal is recorded, not answered by another model.

Usage:
    python scripts/critique_overlap_pilot.py select
    python scripts/critique_overlap_pilot.py extract
    python scripts/critique_overlap_pilot.py generate
    python scripts/critique_overlap_pilot.py judge --judge sonnet
    python scripts/critique_overlap_pilot.py judge --judge codex
    python scripts/critique_overlap_pilot.py summarize
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import random
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

MANIFEST = ROOT / "data" / "critique_eligibility_manifest.json"
DEFAULT_RUN_ID = "critique_overlap_pilot_2026-11-10"
PRIOR_A_RUN = ROOT / "results" / "claude_opus_5_5_high_misses_2026-11-04" / "A"
N_PILOT = 5
BUDGET_STOP_USD = 6.0

EXTRACT_MODEL = "claude-haiku-5-5"
EXTRACT_EFFORT = "medium"
SONNET_JUDGE_MODEL = "claude-sonnet-5-5"
SONNET_JUDGE_EFFORT = "high"
CODEX_JUDGE_MODEL = "gpt-5.6-terra"
CODEX_JUDGE_EFFORT = "high"

# USD per million tokens, first-party API (claude-api skill table cached 2026-11-03).
PRICES = {
    "claude-haiku-5-5": {"input": 0.10, "output": 0.50},
    "claude-sonnet-5-5": {"input": 2.00, "output": 10.00},
}

THRESHOLDS = (30, 45)  # 30 is the historical cut-off; 45 is a sensitivity check


# --------------------------------------------------------------------------
# Prompts and schemas
# --------------------------------------------------------------------------

EXTRACT_SYSTEM = """You are helping build a reference set for a study of peer review. You will be given the full text of one published evaluation (referee report) of a research paper. List every distinct substantive concern, criticism, or request for further analysis that the evaluator raises about the paper.

Rules:
- One issue per item. Split a paragraph into separate issues when it raises different problems; merge repeated statements of the same problem into one.
- Each `text` must stand alone: a reader who has not seen the report should understand what the problem is and why the evaluator thinks it matters, in one to three sentences. Report the evaluator's concern faithfully. Do not add your own judgement or anything that is not in the report.
- Include only concerns about the paper: identification, data, measurement, analysis, interpretation, robustness, missing evidence, generalisability, transparency, or presentation that affects understanding. Leave out praise, summaries of the paper, numeric ratings, journal-tier predictions, and remarks about the evaluation process.
- `quote`: a short excerpt (about 10 to 40 words) copied exactly, character for character, from the report, that supports the issue.
- `importance`: the weight the evaluator gives it. "major" if they call it central, serious, or a main concern; "minor" if they call it minor, optional, or a small suggestion; "moderate" if in between; "unstated" if the report gives no signal.
- Never include the evaluator's name or personal details. Refer to "the evaluator" if needed."""

EXTRACT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "quote": {"type": "string"},
                    "importance": {"type": "string", "enum": ["major", "moderate", "minor", "unstated"]},
                },
                "required": ["text", "quote", "importance"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["issues"],
    "additionalProperties": False,
}

JUDGE_SYSTEM = """You compare two lists of concerns about a research paper. The lists were written independently. Identify which items raise the same underlying concern.

For every pair (one item from List A, one from List B) that overlaps substantively, return a match with:
- label: "exact" if they are essentially the same concern (same problem, same mechanism, same implication); "partial" if they share a substantive core but differ materially in scope or specifics; "related_but_distinct" if they concern the same topic or part of the paper but make different claims.
- score: 0 to 100 for how fully the two items express the same concern (exact about 80 to 100, partial about 40 to 79, related_but_distinct about 10 to 39).
- reason: one sentence.

Do not return pairs with no substantive overlap. An item may match several items or none; it is fine to return no matches at all. Judge only the content. Shared general vocabulary (both mention robustness, external validity, sample size, and so on) is not a match unless the specific problem is the same. Use only the item ids given."""

JUDGE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "matches": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "a_id": {"type": "string"},
                    "b_id": {"type": "string"},
                    "label": {"type": "string", "enum": ["exact", "partial", "related_but_distinct"]},
                    "score": {"type": "integer"},
                    "reason": {"type": "string"},
                },
                "required": ["a_id", "b_id", "label", "score", "reason"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["matches"],
    "additionalProperties": False,
}


# --------------------------------------------------------------------------
# Small helpers (pure; covered by tests/test_critique_overlap_pilot.py)
# --------------------------------------------------------------------------

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def select_papers(manifest: dict[str, Any], n: int = N_PILOT) -> list[dict[str, Any]]:
    """Fixed, outcome-blind selection rule."""
    pool = [
        p for p in manifest["papers"]
        if p["eligible"]
        and p["n_substantive_individual_evaluations"] >= 2
        and p["pdf_predates_first_evaluation"] is True
    ]
    pool.sort(key=lambda p: sha256_text(p["paper"]))
    return pool[:n]


def evaluator_files(paper: dict[str, Any], min_chars: int) -> list[dict[str, Any]]:
    """Substantive individual evaluations, labelled E1, E2, ... in a stable order."""
    evs = [e for e in paper["evaluations"] if e["kind"] == "evaluation" and e["body_chars"] >= min_chars]
    evs.sort(key=lambda e: (e["evaluator_index"] if e["evaluator_index"] is not None else 99, e["slug"]))
    return [{**e, "label": f"E{i}"} for i, e in enumerate(evs, start=1)]


def strip_front_matter(md: str) -> str:
    if md.startswith("---"):
        end = md.find("\n---", 3)
        if end != -1:
            return md[end + 4:].strip()
    return md.strip()


def _loose(text: str) -> str:
    """Normalise for quote checking: markdown escapes, quote styles, whitespace, case."""
    text = text.replace("\\", "")
    text = re.sub(r"[“”„‟\"]", '"', text)
    text = re.sub(r"[‘’‚‛']", "'", text)
    text = re.sub(r"[*_`>#\[\]]", "", text)
    text = re.sub(r"[‐‑‒–—]", "-", text)
    return re.sub(r"\s+", " ", text).strip().lower()


def quote_in_source(quote: str, source: str) -> bool:
    q = _loose(quote).strip(" .…")
    return len(q) >= 20 and q in _loose(source)


def blind_lists(pairing_id: str, side1: list[dict[str, str]], side2: list[dict[str, str]]) -> dict[str, Any]:
    """Assign the two sides to List A / List B at random and shuffle each list.

    Deterministic in pairing_id. Returns the prompt lists and the map back to
    original ids, so a judge sees neither source labels nor original order.
    """
    rng = random.Random(sha256_text(pairing_id))
    swap = rng.random() < 0.5
    first, second = (side2, side1) if swap else (side1, side2)
    a = first[:]
    b = second[:]
    rng.shuffle(a)
    rng.shuffle(b)
    id_map: dict[str, str] = {}
    list_a, list_b = [], []
    for i, item in enumerate(a, start=1):
        id_map[f"A{i}"] = item["id"]
        list_a.append({"id": f"A{i}", "text": item["text"]})
    for i, item in enumerate(b, start=1):
        id_map[f"B{i}"] = item["id"]
        list_b.append({"id": f"B{i}", "text": item["text"]})
    return {"swapped": swap, "list_a": list_a, "list_b": list_b, "id_map": id_map}


def judge_user_prompt(blinded: dict[str, Any]) -> str:
    def block(name: str, items: list[dict[str, str]]) -> str:
        return f"{name}\n" + "\n".join(f"[{it['id']}] {it['text']}" for it in items)
    return (
        block("List A", blinded["list_a"]) + "\n\n" + block("List B", blinded["list_b"])
        + "\n\nReturn JSON matching the supplied schema."
    )


def unblind_matches(raw: dict[str, Any], blinded: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    """Map judge output back to original ids as (side1_id, side2_id). Returns (matches, n_invalid)."""
    id_map = blinded["id_map"]
    out, invalid = [], 0
    for m in raw.get("matches", []):
        a, b = id_map.get(m.get("a_id", "")), id_map.get(m.get("b_id", ""))
        if a is None or b is None:
            invalid += 1
            continue
        s1, s2 = (b, a) if blinded["swapped"] else (a, b)
        out.append({"side1_id": s1, "side2_id": s2, "label": m["label"],
                    "score": int(m["score"]), "reason": m.get("reason", "")})
    return out, invalid


def covered_ids(matches: list[dict[str, Any]], side: str, rule: str) -> set[str]:
    """Ids on `side` ('side1' or 'side2') with at least one qualifying match.

    rule: 'score>=30', 'score>=45', or 'label' (exact or partial).
    """
    key = f"{side}_id"
    out = set()
    for m in matches:
        if rule == "label":
            ok = m["label"] in ("exact", "partial")
        else:
            ok = m["score"] >= int(rule.split(">=")[1])
        if ok:
            out.add(m[key])
    return out


RULES = tuple(f"score>={t}" for t in THRESHOLDS) + ("label",)


def rate(num: int, den: int) -> float | None:
    return round(100.0 * num / den, 1) if den else None


def cohen_kappa(x: list[int], y: list[int]) -> float | None:
    n = len(x)
    if n == 0 or n != len(y):
        return None
    po = sum(a == b for a, b in zip(x, y)) / n
    p1x, p1y = sum(x) / n, sum(y) / n
    pe = p1x * p1y + (1 - p1x) * (1 - p1y)
    if pe == 1:
        return None
    return round((po - pe) / (1 - pe), 3)


# --------------------------------------------------------------------------
# Claude API calls
# --------------------------------------------------------------------------

def make_client():
    import anthropic

    key = (ROOT / "key" / "anthropic_key.txt").read_text().strip()
    return anthropic.Anthropic(api_key=key, max_retries=4, timeout=1800.0)


def claude_cost(model: str, usage: dict[str, Any]) -> float:
    p = PRICES[model]
    return round(
        ((usage.get("input_tokens", 0) or 0) + (usage.get("cache_creation_input_tokens", 0) or 0)) * p["input"] / 1e6
        + (usage.get("output_tokens", 0) or 0) * p["output"] / 1e6,
        5,
    )


def call_claude(client, *, model: str, effort: str, system: str, user: str, schema: dict[str, Any],
                max_tokens: int = 32000) -> dict[str, Any]:
    """One structured-output call. Thinking is left at the model default (adaptive)."""
    import anthropic

    t0 = time.time()
    try:
        with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            system=system,
            output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
            messages=[{"role": "user", "content": user}],
        ) as stream:
            msg = stream.get_final_message()
    except anthropic.APIStatusError as e:
        return {"error": f"{type(e).__name__} {e.status_code}: {e.message}", "elapsed_seconds": round(time.time() - t0, 1)}
    except anthropic.APIConnectionError as e:
        return {"error": f"APIConnectionError: {e}", "elapsed_seconds": round(time.time() - t0, 1)}
    d = msg.to_dict()
    text = "".join(b.get("text", "") or "" for b in d.get("content", []) if b.get("type") == "text")
    usage = d.get("usage") or {}
    out: dict[str, Any] = {
        "elapsed_seconds": round(time.time() - t0, 1),
        "response_id": d.get("id"),
        "model_returned": d.get("model"),
        "stop_reason": d.get("stop_reason"),
        "usage": {k: usage.get(k) for k in ("input_tokens", "output_tokens",
                                            "cache_creation_input_tokens", "cache_read_input_tokens")},
        "est_cost_usd": claude_cost(model, usage),
    }
    if d.get("stop_reason") != "end_turn":
        out["error"] = f"stop_reason={d.get('stop_reason')}"
        return out
    try:
        out["parsed"] = json.loads(text)
    except json.JSONDecodeError as e:
        out["error"] = f"JSON parse: {e}"
    return out


def spend_tools():
    import run_headless_claude_misses as runner

    return runner.record_spend, runner.total_spend


def log_spend(run_dir: pathlib.Path, paper: str, stage: str, res: dict[str, Any]) -> None:
    record_spend, _ = spend_tools()
    usage = res.get("usage") or {}
    record_spend(run_dir, {
        "timestamp": utc_now(), "paper": paper, "condition": stage, "claim_id": "", "replicate": 1,
        "status": "failed" if res.get("error") else "ok", "stop_reason": res.get("stop_reason", ""),
        "input_tokens": usage.get("input_tokens", ""),
        "cache_creation_input_tokens": usage.get("cache_creation_input_tokens", ""),
        "cache_read_input_tokens": usage.get("cache_read_input_tokens", ""),
        "output_tokens": usage.get("output_tokens", ""),
        "est_cost_usd": res.get("est_cost_usd", 0.0), "elapsed_seconds": res.get("elapsed_seconds", ""),
        "request_id": res.get("response_id", ""),
    })


def over_budget(run_dir: pathlib.Path, budget: float) -> bool:
    _, total_spend = spend_tools()
    spent = total_spend(run_dir)
    if spent >= budget:
        print(f"STOP: estimated spend ${spent:.2f} has reached the ${budget:.2f} limit")
        return True
    return False


# --------------------------------------------------------------------------
# Stages
# --------------------------------------------------------------------------

def stage_select(args: argparse.Namespace, run_dir: pathlib.Path) -> int:
    manifest = json.loads(MANIFEST.read_text())
    min_chars = manifest["rules"]["min_eval_body_chars"]
    chosen = select_papers(manifest, args.n)
    sel = {
        "created_at": utc_now(),
        "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        "rule": "eligible; >=2 substantive individual evaluations; PDF creation date on or before the first "
                "evaluation date; ordered by SHA-256 of the paper label; first N",
        "n": args.n,
        "pool_size": len(select_papers(manifest, 10**6)),
        "papers": [
            {
                "paper": p["paper"],
                "research_title": p["research_title"],
                "pdf_sha256": p["pdf_sha256"],
                "pdf_pages": p["pdf_pages"],
                "pdf_creation_date": p["pdf_creation_date"],
                "first_evaluation_date": p["first_evaluation_date"],
                "in_gpt52_focal_run": p["in_gpt52_focal_run"],
                "evaluations": [
                    {k: e[k] for k in ("label", "slug", "file", "date", "body_chars", "sha256")}
                    for e in evaluator_files(p, min_chars)
                ],
            }
            for p in chosen
        ],
    }
    out = run_dir / "selection.json"
    if out.exists() and not args.force:
        print(f"exists: {out.relative_to(ROOT)} (use --force to redo)")
        return 0
    out.write_text(json.dumps(sel, indent=2, ensure_ascii=False))
    for p in sel["papers"]:
        print(f"  {p['paper']}: {p['pdf_pages']} pages, {len(p['evaluations'])} evaluations"
              f"{' (already in GPT-5.2 focal run)' if p['in_gpt52_focal_run'] else ''}")
    print(f"selected {len(sel['papers'])} of {sel['pool_size']} in the pool")
    return 0


def load_selection(run_dir: pathlib.Path) -> dict[str, Any]:
    return json.loads((run_dir / "selection.json").read_text())


def stage_extract(args: argparse.Namespace, run_dir: pathlib.Path) -> int:
    sel = load_selection(run_dir)
    out_dir = run_dir / "human_issues"
    out_dir.mkdir(parents=True, exist_ok=True)
    client = None
    failures = 0
    for p in sel["papers"]:
        for ev in p["evaluations"]:
            out = out_dir / f"{p['paper']}__{ev['label']}.json"
            if out.exists() and not args.force:
                print(f"skip (exists): {out.relative_to(ROOT)}")
                continue
            if over_budget(run_dir, args.budget):
                return 99
            src_path = ROOT / ev["file"]
            if hashlib.sha256(src_path.read_bytes()).hexdigest() != ev["sha256"]:
                raise RuntimeError(f"{ev['file']} changed since selection")
            body = strip_front_matter(src_path.read_text(encoding="utf-8", errors="replace"))
            user = "Evaluation text:\n\n" + body
            if args.dry_run:
                print(f"dry run: {p['paper']} {ev['label']} ({len(body)} chars)")
                continue
            client = client or make_client()
            res = call_claude(client, model=EXTRACT_MODEL, effort=EXTRACT_EFFORT, system=EXTRACT_SYSTEM,
                              user=user, schema=EXTRACT_SCHEMA)
            log_spend(run_dir, p["paper"], f"extract_{ev['label']}", res)
            issues = []
            for i, it in enumerate((res.get("parsed") or {}).get("issues", []), start=1):
                issues.append({
                    "id": f"{p['paper']}::{ev['label']}::H{i:02d}",
                    "text": it["text"].strip(),
                    "quote": it["quote"].strip(),
                    "importance": it["importance"],
                    "quote_verified": quote_in_source(it["quote"], body),
                })
            payload = {
                "provenance": {
                    "paper": p["paper"], "evaluator_label": ev["label"], "source_slug": ev["slug"],
                    "source_sha256": ev["sha256"], "source_body_chars": len(body),
                    "inputs_seen_by_extractor": "this evaluation's body text only (no paper, no model output)",
                    "model_requested": EXTRACT_MODEL, "effort": EXTRACT_EFFORT,
                    "system_prompt_sha256": sha256_text(EXTRACT_SYSTEM),
                    "schema_sha256": sha256_text(json.dumps(EXTRACT_SCHEMA, sort_keys=True)),
                    "completed_at": utc_now(),
                    **{k: res.get(k) for k in ("model_returned", "stop_reason", "usage", "est_cost_usd",
                                               "elapsed_seconds", "response_id", "error")},
                },
                "issues": issues,
            }
            ok = not res.get("error") and bool(issues)
            (out if ok else out.with_suffix(".failed.json")).write_text(json.dumps(payload, indent=2, ensure_ascii=False))
            nver = sum(i["quote_verified"] for i in issues)
            print(f"{'ok' if ok else 'FAILED'}: {p['paper']} {ev['label']}: {len(issues)} issues, "
                  f"{nver} quotes verified, ~${res.get('est_cost_usd', 0):.4f} {res.get('error', '')}")
            failures += 0 if ok else 1
    if not args.dry_run and not failures:
        freeze = {
            "frozen_at": utc_now(),
            "files": {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(out_dir.glob("*__E*.json"))},
        }
        (run_dir / "human_issues_frozen.json").write_text(json.dumps(freeze, indent=2))
    return 1 if failures else 0


def model_issue_file(run_dir: pathlib.Path, paper: str) -> pathlib.Path | None:
    for cand in (run_dir / "A" / f"{paper}.json", PRIOR_A_RUN / f"{paper}.json"):
        if cand.exists():
            return cand
    return None


def stage_generate(args: argparse.Namespace, run_dir: pathlib.Path) -> int:
    sel = load_selection(run_dir)
    if not (run_dir / "human_issues_frozen.json").exists() and not args.dry_run:
        print("Run `extract` first: human issues are frozen before model issues are generated.")
        return 2
    rc = 0
    for p in sel["papers"]:
        existing = model_issue_file(run_dir, p["paper"])
        if existing and not args.force:
            print(f"reuse: {existing.relative_to(ROOT)}")
            continue
        cmd = [sys.executable, str(ROOT / "scripts" / "run_headless_claude_misses.py"),
               "--run-id", args.run_id, "--condition", "A", "--paper", p["paper"], "--budget", str(args.budget)]
        if args.dry_run:
            cmd.append("--dry-run")
        proc = subprocess.run(cmd, text=True)
        if proc.returncode == 99:
            return 99
        rc = rc or proc.returncode
    return rc


def load_issue_sets(run_dir: pathlib.Path, sel: dict[str, Any]) -> dict[str, Any]:
    sets: dict[str, Any] = {}
    for p in sel["papers"]:
        human: dict[str, list[dict[str, str]]] = {}
        for ev in p["evaluations"]:
            f = run_dir / "human_issues" / f"{p['paper']}__{ev['label']}.json"
            human[ev["label"]] = [{"id": i["id"], "text": i["text"]} for i in json.loads(f.read_text())["issues"]]
        mf = model_issue_file(run_dir, p["paper"])
        model = None
        if mf is not None:
            key_issues = json.loads(mf.read_text())["parsed"]["key_issues"]
            model = [{"id": f"{p['paper']}::M{i:02d}", "text": t.strip()} for i, t in enumerate(key_issues, start=1)]
        sets[p["paper"]] = {"human": human, "model": model,
                            "model_source": str(mf.relative_to(ROOT)) if mf else None}
    return sets


def build_pairings(sel: dict[str, Any], sets: dict[str, Any]) -> list[dict[str, Any]]:
    """Real, placebo and human-to-human pairings. Pairings that need model issues
    are left out (and reported) until `generate` has produced them."""
    papers = [p["paper"] for p in sel["papers"]]
    pairings = []
    for i, paper in enumerate(papers):
        human_all = [it for label in sorted(sets[paper]["human"]) for it in sets[paper]["human"][label]]
        other = papers[(i + 1) % len(papers)]
        if sets[paper]["model"] is None:
            print(f"note: no model issues yet for {paper}; its real pairing is skipped")
        else:
            pairings.append({"id": f"real::{paper}", "kind": "real", "paper": paper,
                             "side1": human_all, "side2": sets[paper]["model"],
                             "side1_desc": "human issues (all evaluators)", "side2_desc": "model issues"})
        if sets[other]["model"] is None:
            print(f"note: no model issues yet for {other}; the placebo pairing with {paper} is skipped")
        else:
            pairings.append({"id": f"placebo::{paper}::{other}", "kind": "placebo", "paper": paper,
                             "other_paper": other, "side1": human_all, "side2": sets[other]["model"],
                             "side1_desc": "human issues (all evaluators)",
                             "side2_desc": f"model issues for {other}"})
        labels = sorted(sets[paper]["human"])
        if len(labels) >= 2:
            pairings.append({"id": f"human_human::{paper}", "kind": "human_human", "paper": paper,
                             "side1": sets[paper]["human"][labels[0]], "side2": sets[paper]["human"][labels[1]],
                             "side1_desc": f"{labels[0]} issues", "side2_desc": f"{labels[1]} issues"})
    return pairings


def stage_judge(args: argparse.Namespace, run_dir: pathlib.Path) -> int:
    sel = load_selection(run_dir)
    sets = load_issue_sets(run_dir, sel)
    pairings = build_pairings(sel, sets)
    if args.kind:
        pairings = [p for p in pairings if p["kind"] in args.kind]
    if args.limit:
        pairings = pairings[: args.limit]

    if args.judge == "sonnet":
        judge_name, model, effort = "sonnet", SONNET_JUDGE_MODEL, SONNET_JUDGE_EFFORT
    else:
        judge_name, model, effort = "codex", args.codex_model, CODEX_JUDGE_EFFORT
    out_dir = run_dir / "judge" / judge_name
    out_dir.mkdir(parents=True, exist_ok=True)

    client = None
    codex = None
    binary = None
    if args.judge == "codex" and not args.dry_run:
        import run_concordance_codex as codex  # noqa: PLC0415

        binary = codex.APP_CODEX if codex.APP_CODEX.exists() else pathlib.Path(shutil.which("codex") or "")
        if not binary or not binary.exists():
            print("codex binary not found")
            return 2

    failures = 0
    for pr in pairings:
        safe = pr["id"].replace("::", "__")
        out = out_dir / f"{safe}.json"
        if out.exists() and not args.force:
            print(f"skip (exists): {out.relative_to(ROOT)}")
            continue
        blinded = blind_lists(pr["id"], pr["side1"], pr["side2"])
        user = judge_user_prompt(blinded)
        if args.dry_run:
            print(f"dry run: {pr['id']} ({len(pr['side1'])} x {len(pr['side2'])} items, {len(user)} chars)")
            continue
        meta: dict[str, Any] = {}
        raw: dict[str, Any] | None = None
        error = None
        if args.judge == "sonnet":
            if over_budget(run_dir, args.budget):
                return 99
            client = client or make_client()
            res = call_claude(client, model=model, effort=effort, system=JUDGE_SYSTEM, user=user, schema=JUDGE_SCHEMA)
            log_spend(run_dir, pr["paper"], f"judge_sonnet_{pr['kind']}", res)
            raw, error = res.get("parsed"), res.get("error")
            meta = {k: res.get(k) for k in ("model_returned", "stop_reason", "usage", "est_cost_usd",
                                            "elapsed_seconds", "response_id")}
        else:
            try:
                raw, cmeta = codex.run_codex_call(
                    call_name=safe, prompt=JUDGE_SYSTEM + "\n\n" + user, schema=JUDGE_SCHEMA, model=model,
                    effort=effort, run_dir=out_dir, binary=binary, timeout=args.timeout, force=args.force)
                meta = {k: cmeta.get(k) for k in ("model", "reasoning_effort", "usage", "duration_seconds",
                                                  "auth_surface", "request_sha256")}
            except Exception as e:  # noqa: BLE001 - record and continue with the next pairing
                error = f"{type(e).__name__}: {e}"
        matches, invalid = unblind_matches(raw or {}, blinded)
        payload = {
            "pairing": {k: pr[k] for k in ("id", "kind", "paper", "side1_desc", "side2_desc")}
                       | ({"other_paper": pr["other_paper"]} if "other_paper" in pr else {}),
            "judge": {"name": judge_name, "model_requested": model, "effort": effort,
                      "prompt_sha256": sha256_text(JUDGE_SYSTEM), "schema_sha256": sha256_text(json.dumps(JUDGE_SCHEMA, sort_keys=True)),
                      "blinding": "sides assigned to List A/B at random; items shuffled; neutral ids; no source labels",
                      "completed_at": utc_now(), **meta},
            "list_a_was_side2": blinded["swapped"],
            "side1_ids": [it["id"] for it in pr["side1"]],
            "side2_ids": [it["id"] for it in pr["side2"]],
            "matches": matches,
            "invalid_id_matches_dropped": invalid,
            "error": error,
        }
        ok = error is None and raw is not None
        (out if ok else out.with_suffix(".failed.json")).write_text(json.dumps(payload, indent=2, ensure_ascii=False))
        print(f"{'ok' if ok else 'FAILED'}: {judge_name} {pr['id']}: {len(matches)} matches {error or ''}", flush=True)
        failures += 0 if ok else 1
    return 1 if failures else 0


RULE_LABEL = {"score>=30": "score ≥ 30 (historical)", "score>=45": "score ≥ 45", "label": "exact or partial label"}
JUDGE_LABEL = {"codex": f"GPT judge ({CODEX_JUDGE_MODEL}, via Codex)",
               "sonnet": f"Claude judge ({SONNET_JUDGE_MODEL}; same family as the generator)"}


def summary_markdown(s: dict[str, Any]) -> str:
    """Every number in the write-up comes from summary.json; nothing is typed by hand."""
    def frac(c: int, n: int, pct: Any) -> str:
        return f"{c}/{n} ({pct}%)" if n else "0/0"

    out = [f"# Critique-overlap pilot: computed summary ({s['run_id']})", "",
           "Generated by `scripts/critique_overlap_pilot.py summarize`. Exploratory: "
           f"{len(s['papers'])} papers, one model run per paper, AI judges, no human validation yet.", ""]

    out += ["## Issue counts", "", "| Paper | E1 issues | E2 issues | Model issues | Model issues from |", "|---|---:|---:|---:|---|"]
    for paper in s["papers"]:
        ev = {e["evaluator"]: e["n_issues"] for e in s["extraction"]["per_evaluation"] if e["paper"] == paper}
        mi = s["model_issues"].get(paper, {})
        src = "this run" if (mi.get("source") or "").startswith(f"results/{s['run_id']}/") else "2026-11-04 run (reused)"
        out.append(f"| {paper} | {ev.get('E1', '')} | {ev.get('E2', '')} | {mi.get('n', '')} | {src} |")
    ex = s["extraction"]
    out += ["", f"Human issues: {ex['n_issues']} in total; {ex['n_quotes_verified']} have a supporting quote "
                "found verbatim in the published evaluation. "
                f"The human issue files were frozen at {ex['frozen_at'][:19]}Z, before the first model call of this "
                f"run ({(ex['first_model_call_in_this_run_started_at'] or 'none')[:19]}Z); "
                f"unchanged since: {'yes' if ex['unchanged_since_freeze'] else 'NO'}.", ""]

    for name, j in s["judges"].items():
        out += [f"## {JUDGE_LABEL.get(name, name)}", "",
                "| Matching rule | Human issues the model also raised | Model issues a human also raised | "
                "Placebo: human issues \"matched\" by another paper's model issues | "
                "Placebo: model issues \"matched\" | One evaluator's issues the other also raised |",
                "|---|---|---|---|---|---|"]
        agg = j["aggregate"]
        for rule in RULES:
            cells = [RULE_LABEL[rule]]
            for kind, sides in (("real", ("side1", "side2")), ("placebo", ("side1", "side2"))):
                a = agg.get(kind)
                for side in sides:
                    cells.append(frac(a[rule][f"{side}_covered"], a[f"n_{side}"], a[rule][f"{side}_pooled_pct"]) if a else "not run")
            hh = agg.get("human_human")
            cells.append(frac(hh[rule]["both_directions_covered"], hh[rule]["both_directions_n"],
                              hh[rule]["both_directions_pooled_pct"]) if hh else "not run")
            out.append("| " + " | ".join(cells) + " |")
        out += ["", "Counts are pooled over papers (unique issues with at least one qualifying match, over all issues).", ""]
        if "real" in agg:
            out += ["Per-paper rates, real pairings, score ≥ 30:", "",
                    "| Paper | Human issues covered | Model issues overlapping |", "|---|---|---|"]
            for r in j["pairings"]:
                if r["kind"] == "real":
                    out.append(f"| {r['paper']} | {r['side1_covered[score>=30]']}/{r['n_side1']} | "
                               f"{r['side2_covered[score>=30]']}/{r['n_side2']} |")
            out.append("")
        bi = j.get("real_human_coverage_by_importance", {}).get("score>=30")
        if bi and any(v["n"] for v in bi.values()):
            out += ["Human issues the model also raised, by the weight the evaluator gave them (score ≥ 30): "
                    + "; ".join(f"{lvl} {frac(v['covered'], v['n'], v['pct'])}" for lvl, v in bi.items() if v["n"]) + ".", ""]

    ag = s.get("judge_agreement_real_pairings")
    if ag:
        j1, j2 = ag["judges"]
        out += ["## Do the two judges agree on which issues are covered? (real pairings)", "",
                f"| Rule | Issues | n | Both say covered | Neither | Only {j1} | Only {j2} | Agreement | Cohen's kappa |",
                "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
        for rule in RULES:
            for group in ("human_issues", "model_issues"):
                g = ag[rule][group]
                out.append(f"| {RULE_LABEL[rule]} | {group.replace('_', ' ')} | {g['n_items']} | {g['both_covered']} | "
                           f"{g['neither_covered']} | {g['only_' + j1]} | {g['only_' + j2]} | "
                           f"{g['percent_agreement']}% | {g['cohen_kappa']} |")
        out.append("")

    c = s["cost"]
    out += ["## Cost (estimated from token usage)", "", "| Stage | Calls | USD |", "|---|---:|---:|"]
    for stage, v in c["by_stage"].items():
        out.append(f"| {stage} | {int(v['calls'])} | {v['usd']:.2f} |")
    out += [f"| Total | | {c['total_usd_this_run']:.2f} |", "", c["note"], ""]
    return "\n".join(out)


def stage_summarize(args: argparse.Namespace, run_dir: pathlib.Path) -> int:
    sel = load_selection(run_dir)
    _, total_spend = spend_tools()
    summary: dict[str, Any] = {"run_id": args.run_id, "generated_at": utc_now(),
                               "papers": [p["paper"] for p in sel["papers"]], "judges": {}}

    # Extraction facts
    ext = []
    importance: dict[str, str] = {}
    for p in sel["papers"]:
        for ev in p["evaluations"]:
            d = json.loads((run_dir / "human_issues" / f"{p['paper']}__{ev['label']}.json").read_text())
            importance.update({i["id"]: i["importance"] for i in d["issues"]})
            ext.append({"paper": p["paper"], "evaluator": ev["label"], "n_issues": len(d["issues"]),
                        "n_quotes_verified": sum(i["quote_verified"] for i in d["issues"]),
                        "cost_usd": d["provenance"].get("est_cost_usd")})
    frozen = json.loads((run_dir / "human_issues_frozen.json").read_text())
    unchanged = all(
        hashlib.sha256((run_dir / "human_issues" / name).read_bytes()).hexdigest() == digest
        for name, digest in frozen["files"].items()
    )
    a_dir = run_dir / "A"
    first_model_output = min(
        (json.loads(f.read_text())["provenance"]["started_at"] for f in a_dir.glob("*.json")
         if not f.name.endswith(".raw_response.json")), default=None) if a_dir.exists() else None
    summary["extraction"] = {
        "per_evaluation": ext,
        "n_issues": sum(e["n_issues"] for e in ext),
        "n_quotes_verified": sum(e["n_quotes_verified"] for e in ext),
        "frozen_at": frozen["frozen_at"],
        "unchanged_since_freeze": unchanged,
        "first_model_call_in_this_run_started_at": first_model_output,
    }

    per_item: dict[str, dict[str, dict[str, int]]] = {}
    for jdir in sorted((run_dir / "judge").glob("*")):
        if not jdir.is_dir():
            continue
        rows = []
        for f in sorted(jdir.glob("*.json")):
            if f.name.endswith(".failed.json"):
                continue
            d = json.loads(f.read_text())
            if "pairing" not in d:
                continue
            row = {"id": d["pairing"]["id"], "kind": d["pairing"]["kind"], "paper": d["pairing"]["paper"],
                   "n_side1": len(d["side1_ids"]), "n_side2": len(d["side2_ids"]), "n_matches": len(d["matches"])}
            for rule in RULES:
                c1 = covered_ids(d["matches"], "side1", rule)
                c2 = covered_ids(d["matches"], "side2", rule)
                row[f"side1_covered[{rule}]"] = len(c1)
                row[f"side2_covered[{rule}]"] = len(c2)
                if d["pairing"]["kind"] == "real":
                    store = per_item.setdefault(jdir.name, {}).setdefault(rule, {})
                    for i in d["side1_ids"]:
                        store[i] = int(i in c1)
                    for i in d["side2_ids"]:
                        store[i] = int(i in c2)
            rows.append(row)
        agg: dict[str, Any] = {}
        for kind in ("real", "placebo", "human_human"):
            ks = [r for r in rows if r["kind"] == kind]
            if not ks:
                continue
            a: dict[str, Any] = {"n_pairings": len(ks), "n_side1": sum(r["n_side1"] for r in ks),
                                 "n_side2": sum(r["n_side2"] for r in ks)}
            for rule in RULES:
                s1 = sum(r[f"side1_covered[{rule}]"] for r in ks)
                s2 = sum(r[f"side2_covered[{rule}]"] for r in ks)
                per1 = [100.0 * r[f"side1_covered[{rule}]"] / r["n_side1"] for r in ks if r["n_side1"]]
                per2 = [100.0 * r[f"side2_covered[{rule}]"] / r["n_side2"] for r in ks if r["n_side2"]]
                a[rule] = {
                    "side1_covered": s1, "side1_pooled_pct": rate(s1, a["n_side1"]),
                    "side1_mean_of_pairing_pct": round(sum(per1) / len(per1), 1) if per1 else None,
                    "side2_covered": s2, "side2_pooled_pct": rate(s2, a["n_side2"]),
                    "side2_mean_of_pairing_pct": round(sum(per2) / len(per2), 1) if per2 else None,
                }
            if kind == "human_human":
                # Share of one evaluator's issues that the other evaluator also raised, both directions pooled.
                for rule in RULES:
                    both = a[rule]["side1_covered"] + a[rule]["side2_covered"]
                    a[rule]["both_directions_covered"] = both
                    a[rule]["both_directions_n"] = a["n_side1"] + a["n_side2"]
                    a[rule]["both_directions_pooled_pct"] = rate(both, a["n_side1"] + a["n_side2"])
            agg[kind] = a
        # Human-issue coverage in real pairings, split by the weight the evaluator gave the issue.
        by_imp: dict[str, Any] = {}
        for rule in RULES:
            items = {i: c for i, c in per_item.get(jdir.name, {}).get(rule, {}).items() if "::H" in i}
            for level in ("major", "moderate", "minor", "unstated"):
                ids = [i for i in items if importance.get(i) == level]
                cov = sum(items[i] for i in ids)
                by_imp.setdefault(rule, {})[level] = {"n": len(ids), "covered": cov, "pct": rate(cov, len(ids))}
        summary["judges"][jdir.name] = {"pairings": rows, "aggregate": agg,
                                        "real_human_coverage_by_importance": by_imp}

    # Judge agreement on real pairings: is each issue counted as covered?
    names = sorted(per_item)
    if len(names) >= 2:
        j1, j2 = names[0], names[1]
        agree: dict[str, Any] = {"judges": [j1, j2]}
        for rule in RULES:
            a, b = per_item[j1].get(rule, {}), per_item[j2].get(rule, {})
            for group, test in (("human_issues", lambda i: "::H" in i), ("model_issues", lambda i: "::M" in i)):
                ids = sorted(i for i in set(a) & set(b) if test(i))
                x, y = [a[i] for i in ids], [b[i] for i in ids]
                agree.setdefault(rule, {})[group] = {
                    "n_items": len(ids),
                    "both_covered": sum(1 for u, v in zip(x, y) if u and v),
                    "neither_covered": sum(1 for u, v in zip(x, y) if not u and not v),
                    "only_" + j1: sum(1 for u, v in zip(x, y) if u and not v),
                    "only_" + j2: sum(1 for u, v in zip(x, y) if v and not u),
                    "percent_agreement": rate(sum(u == v for u, v in zip(x, y)), len(ids)),
                    "cohen_kappa": cohen_kappa(x, y),
                }
        summary["judge_agreement_real_pairings"] = agree

    # Cost
    import csv as _csv

    ledger = run_dir / "spend_ledger.csv"
    by_stage: dict[str, dict[str, float]] = {}
    if ledger.exists():
        with ledger.open() as fh:
            for r in _csv.DictReader(fh):
                stage = re.sub(r"_(E\d+|real|placebo|human_human)$", "", r["condition"])
                s = by_stage.setdefault(stage, {"calls": 0, "usd": 0.0})
                s["calls"] += 1
                s["usd"] = round(s["usd"] + float(r["est_cost_usd"] or 0), 4)
    summary["cost"] = {"by_stage": by_stage, "total_usd_this_run": round(total_spend(run_dir), 2),
                       "note": "Codex judge calls use a ChatGPT subscription and have no metered cost here. "
                               "Model issues reused from the 2026-11-04 run are not re-billed."}
    summary["model_issues"] = {}
    sets = load_issue_sets(run_dir, sel)
    for paper, s in sets.items():
        summary["model_issues"][paper] = {"n": len(s["model"] or []), "source": s["model_source"]}
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    (run_dir / "summary.md").write_text(summary_markdown(summary))
    print(json.dumps({k: summary[k] for k in ("extraction", "cost") if k in summary}, indent=1)[:1500])
    for name, j in summary["judges"].items():
        print(f"\n== judge: {name} ==")
        for kind, a in j["aggregate"].items():
            for rule in RULES:
                r = a[rule]
                print(f"  {kind:12s} {rule:10s} side1 {r['side1_covered']}/{a['n_side1']} ({r['side1_pooled_pct']}%)"
                      f"  side2 {r['side2_covered']}/{a['n_side2']} ({r['side2_pooled_pct']}%)")
    return 0


def stage_register(args: argparse.Namespace, run_dir: pathlib.Path) -> int:
    """Add this run to results/llm_runs_metadata.csv (same columns as the other tracked runs)."""
    sys.path.insert(0, str(ROOT))
    import track_llm_run as t  # noqa: PLC0415

    rows = t.read_metadata()
    if any(r["run_id"] == args.run_id for r in rows):
        print(f"Already registered: {args.run_id}")
        return 0
    sel = load_selection(run_dir)
    papers = [p["paper"] for p in sel["papers"]]
    rel = run_dir.relative_to(ROOT)
    rows.append({
        "run_id": args.run_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "model": f"claude-opus-5-5 (effort high, PDF only) for model issues; {EXTRACT_MODEL} (effort {EXTRACT_EFFORT}) "
                 f"for blind human-issue extraction; judges {CODEX_JUDGE_MODEL} (Codex, effort {CODEX_JUDGE_EFFORT}) "
                 f"and {SONNET_JUDGE_MODEL} (effort {SONNET_JUDGE_EFFORT})",
        "prompt_version": "critique_overlap_pilot_v1 (model issues: methods_qmd_SYSTEM_PROMPT_WITH_ISSUES)",
        "prompt_description": "Leak-controlled critique-overlap pilot: published evaluations split into issues blind, "
                              "PDF-only model issues, two judges on unlabeled lists, placebo and human-to-human pairings",
        "prompt_file": "scripts/critique_overlap_pilot.py; methods.qmd:SYSTEM_PROMPT_WITH_ISSUES",
        "num_papers": str(len(papers)),
        "papers_evaluated": ",".join(papers),
        "output_combined_long": "",
        "output_metrics_long": "",
        "output_tiers_long": "",
        "output_json_dir": f"{rel}/",
        "notes": "Exploratory pilot; not pooled with the one-shot benchmark or used in manuscript chapters. "
                 "AI-judged; no human validation yet. Two papers reuse condition-A outputs from "
                 "claude_opus_5_5_high_misses_2026-11-04.",
        "status": "completed",
    })
    t.write_metadata(rows)
    print(f"Registered {args.run_id}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["select", "extract", "generate", "judge", "summarize", "register"])
    ap.add_argument("--run-id", default=DEFAULT_RUN_ID)
    ap.add_argument("--n", type=int, default=N_PILOT)
    ap.add_argument("--budget", type=float, default=BUDGET_STOP_USD,
                    help="Stop before a paid call once estimated run spend reaches this")
    ap.add_argument("--judge", choices=["sonnet", "codex"], default="sonnet")
    ap.add_argument("--codex-model", default=CODEX_JUDGE_MODEL)
    ap.add_argument("--kind", action="append", choices=["real", "placebo", "human_human"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    run_dir = ROOT / "results" / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return {"select": stage_select, "extract": stage_extract, "generate": stage_generate,
            "judge": stage_judge, "summarize": stage_summarize, "register": stage_register}[args.stage](args, run_dir)


if __name__ == "__main__":
    raise SystemExit(main())
