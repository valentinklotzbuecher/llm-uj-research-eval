#!/usr/bin/env python3
"""
Revised critique-matching judge (v2): does a model's key-issue list contain the
concerns in the curated human critique, and vice versa?

Changes from the judge behind the published coverage numbers
(tools/compare_issues_llm.py; see docs/critique_matching_prompts.md):

- Blinded: both lists are first rewritten by a cheap model (Claude Haiku 5.5)
  into neutral statements with the same prompt, removing attribution, quotes,
  severity labels and author-response text; items with no substantive concern
  are dropped and counted. The judge then sees "List A" and "List B"; which is
  human is randomised per case and items are shuffled. The paper title is
  withheld. A leak scan of the rewritten text is saved for review.
- Rubric by parts: each pair is classified by whether it shares the locus,
  mechanism and implication, into named categories. Worked examples are
  invented, not taken from study papers.
- Code, not the judge, computes coverage and overlap, at three strictness
  levels.
- A different model family from the issue generator (GPT-5.2 Pro): Claude
  Opus 5.5 at high effort.
- Controls: human issues from one paper paired with model issues from
  another, to measure how often unrelated lists "match". The two documented
  mismatched pairings (Benabou, Peterman) are natural controls.
- Replicates with different shuffles measure run-to-run variation.

Inputs: tools/issue_annotation_ui/data.json (pre-split human issues and the
GPT-5.2 Pro focal key issues). Outputs: results/<run-id>/. This is an
exploratory judge comparison and is not pooled with the published figures.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pathlib
import random
import re
import sys
from datetime import datetime, timezone
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from run_concordance_codex import anonymize_human_issue  # noqa: E402
from run_headless_claude_misses import api_schema, estimate_cost, make_client, sdk_version  # noqa: E402

SOURCE = ROOT / "tools" / "issue_annotation_ui" / "data.json"
DEFAULT_RUN_ID = "issue_match_judge_v2_opus55_2026-11-10"
MODEL = "claude-opus-5-5"
EFFORT = "high"
MAX_TOKENS = 32000
PROMPT_VERSION = "issue_match_judge_v2"
EXCLUDED = ("Benabou_et_al._2023", "Peterman_et_al._2025")  # documented paper mismatches
CONTROL_SHIFT = 6  # control k pairs eligible paper k's human issues with paper k+6's model issues
N_CONTROLS = 6

CATEGORIES = [
    "same_concern",
    "same_concern_different_scope",
    "same_target_different_problem",
    "same_topic_only",
]
LEVELS = {
    "strict": {"same_concern"},
    "standard": {"same_concern", "same_concern_different_scope"},
    "loose": {"same_concern", "same_concern_different_scope", "same_target_different_problem"},
}

NORMALIZER_MODEL = "claude-haiku-5-5"
NORMALIZER_PRICE_IN, NORMALIZER_PRICE_OUT = 0.10, 0.50  # $/MTok, prompts under 100K tokens

NORMALIZER_PROMPT = """You rewrite a list of critiques of a research paper into a uniform, neutral style, so that a later reader cannot tell who wrote them or how. You do not judge the critiques.

For each item, write one to three plain sentences, third person, present tense, stating:
- what the critique is about (the result, table, estimate, variable, assumption, data or claim);
- why that is a problem;
- what follows for the paper's claims, or what is asked for, if the item says so.

Keep every substantive point and every specific detail: numbers, table and figure references, variable names, methods, data sources, page or section references.

Remove: who raised the point (evaluators, reviewers, managers, tools, names, labels such as "E1" or "[...]"), quotation marks and first-person phrasing ("I think", "I agree"), references to author responses, revisions or later versions, agreement between reviewers, severity or priority labels ("necessary", "optional", "unsure", "major"), list numbering, and meta-commentary.

Do not add points, explanations or opinions. Do not merge items or split them: return exactly one rewritten item per input item, with the same id. If an item contains no substantive critique (only a heading, a label or an attribution), set no_substantive_concern to true and leave statement empty."""

NORMALIZER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "statement": {"type": "string"},
                    "no_substantive_concern": {"type": "boolean"},
                },
                "required": ["id", "statement", "no_substantive_concern"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["items"],
    "additionalProperties": False,
}

SYSTEM_PROMPT = """You compare two lists of critiques of a research paper. Each list was written independently by a different reviewer. A reviewer may be a person or an AI system; you are not told which, and you should not try to guess.

Your only task is to decide which items in the two lists raise the same concern. Do not judge whether a critique is correct or important, and do not add critiques of your own.

A critique has three parts:
- LOCUS: what it is about (a specific result, table, estimate, assumption, data source, or claim).
- MECHANISM: why that is a problem (for example selection on the outcome, a units error, leakage between predictors and outcome, an untested assumption, low power, an inconsistency).
- IMPLICATION: what follows for the paper's claims, or what the reviewer asks for.

Classify each pair of items that has anything in common into exactly one category:

- same_concern: same locus and same mechanism. The implications agree or are compatible. Different wording or emphasis does not matter.
- same_concern_different_scope: same mechanism, but one item is clearly broader or narrower (it covers several loci, or states the mechanism only in general terms while the other is specific). Say which list's item is broader.
- same_target_different_problem: same locus, but a different mechanism. Both criticise the same result or assumption for different reasons.
- same_topic_only: the items share only a general area or vocabulary (both mention "identification", "robustness", or "external validity") without a shared locus and mechanism.

Leave out pairs with nothing in common. Do not force a match: many items have no counterpart. One item may pair with several items in the other list.

Tests to apply:
- Would a reader of either item alone be led to the same concern and broadly the same fix? If not, it is not same_concern.
- A list of generic topics ("robustness checks, clustering, power") does not share a mechanism with a specific critique unless it states that mechanism.
- Matching words are not enough. A shared mechanism must be stated in both items.

Invented examples (not from any paper you will see):
- A: "The wage effect relies on firms that survived to 2015, so exits induced by the policy bias the estimate upward." B: "Survivorship: the panel keeps only surviving firms, so the positive effect may reflect selective exit." -> same_concern.
- A: "Several robustness concerns: selection, clustering of standard errors, and the choice of control group." B: "The panel keeps only surviving firms, biasing the wage effect." -> same_concern_different_scope, A broader (A names selection but not where or how).
- A: "The wage effect is not robust to clustering at the state level." B: "The wage effect is biased by survivorship." -> same_target_different_problem.
- A: "External validity to other countries is unclear." B: "Results may not generalise beyond manufacturing." -> same_topic_only, unless both name the same population and reason.

Also say whether the two lists appear to describe the same study, from their content alone (yes, no, unclear), and why. Classify the pairs either way: do not drop pairs because you think the lists concern different studies.

For each pair give your confidence (0-100) that the category is right, and one or two sentences naming the shared locus and mechanism and the main difference. Consider every item in both lists. Use only the item IDs given."""

JUDGE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "same_study": {"type": "string", "enum": ["yes", "no", "unclear"]},
        "same_study_reason": {"type": "string"},
        "pairs": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "a_id": {"type": "string"},
                    "b_id": {"type": "string"},
                    "category": {"type": "string", "enum": CATEGORIES},
                    "broader_side": {"type": "string", "enum": ["A", "B", "neither"]},
                    "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
                    "reason": {"type": "string"},
                },
                "required": ["a_id", "b_id", "category", "broader_side", "confidence", "reason"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["same_study", "same_study_reason", "pairs"],
    "additionalProperties": False,
}


# --------------------------------------------------------------------------
# Cases
# --------------------------------------------------------------------------

def load_papers() -> dict[str, dict[str, Any]]:
    """Original items, keyed by stable source IDs (H1.., L1..) in source order."""
    data = json.loads(SOURCE.read_text())
    papers = {}
    for p in data["papers"]:
        humans = [anonymize_human_issue(str(h.get("text", "")).strip()) for h in p.get("human_issue_suggestions", [])]
        models = [str(x).strip() for x in p.get("llm_key_issues", [])]
        papers[p["paper_id"]] = {"human": {f"H{i}": t for i, t in enumerate(humans, 1) if t},
                                 "model": {f"L{i}": t for i, t in enumerate(models, 1) if t}}
    return papers


def normalize_side(client, items: dict[str, str], out: pathlib.Path) -> dict[str, Any]:
    """Rewrite one list into neutral statements with the cheap model; cached on disk."""
    if out.exists():
        return json.loads(out.read_text())
    import time

    user = "Items:\n" + "\n\n".join(f"{k}: {' '.join(v.split())}" for k, v in items.items()) + "\n\nReturn JSON matching the supplied schema."
    t0 = time.time()
    with client.messages.stream(
        model=NORMALIZER_MODEL,
        max_tokens=16000,
        system=NORMALIZER_PROMPT,
        output_config={"effort": "medium", "format": {"type": "json_schema", "schema": api_schema(NORMALIZER_SCHEMA)}},
        messages=[{"role": "user", "content": user}],
    ) as stream:
        msg = stream.get_final_message()
    d = msg.to_dict()
    if d.get("stop_reason") != "end_turn":
        raise RuntimeError(f"normalizer stop_reason {d.get('stop_reason')} for {out.name}")
    text = "".join(b.get("text", "") or "" for b in d.get("content", []) if b.get("type") == "text")
    parsed = json.loads(text)
    got = {x["id"]: x for x in parsed["items"]}
    if set(got) != set(items):
        raise RuntimeError(f"normalizer returned ids {sorted(got)} for {sorted(items)} ({out.name})")
    u = d.get("usage") or {}
    cost = round((u.get("input_tokens", 0) or 0) * NORMALIZER_PRICE_IN / 1e6 + (u.get("output_tokens", 0) or 0) * NORMALIZER_PRICE_OUT / 1e6, 5)
    rec = {"model": d.get("model"), "prompt_sha256": hashlib.sha256(NORMALIZER_PROMPT.encode()).hexdigest(),
           "usage": u, "est_cost_usd": cost, "elapsed_seconds": round(time.time() - t0, 1),
           "items": {k: {"original": items[k], "statement": got[k]["statement"].strip(),
                         "no_substantive_concern": bool(got[k]["no_substantive_concern"])} for k in items}}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(rec, indent=2, ensure_ascii=False))
    return rec


RESIDUAL_ATTRIBUTION = re.compile(r"(?i)\b(?:the |a )?(?:human )?(?:evaluators?|reviewers?|referees?)\b")


def scrub(text: str) -> str:
    """Deterministic fallback for attribution words the rewrite left in."""
    return RESIDUAL_ATTRIBUTION.sub(lambda m: "the critique" if m.group(0)[:1].islower() else "The critique", text)


def normalized_papers(client, papers: dict[str, dict[str, Any]], run_dir: pathlib.Path, needed: set[str]) -> dict[str, dict[str, Any]]:
    """Neutral statements for each needed paper; items with no substantive concern are dropped."""
    out, scrubbed = {}, []
    for pid in sorted(needed):
        side = {}
        for s in ("human", "model"):
            rec = normalize_side(client, papers[pid][s], run_dir / "normalized" / f"{pid}__{s}.json")
            items = {}
            for k, v in rec["items"].items():
                if v["no_substantive_concern"] or not v["statement"]:
                    continue
                t = scrub(v["statement"])
                if t != v["statement"]:
                    scrubbed.append({"paper": pid, "side": s, "id": k, "before": v["statement"], "after": t})
                items[k] = t
            side[s] = items
        out[pid] = side
    (run_dir / "scrubbed_statements.json").write_text(json.dumps(scrubbed, indent=2, ensure_ascii=False))
    return out


def build_cases(papers: dict[str, dict[str, Any]], replicates: int) -> list[dict[str, Any]]:
    eligible = sorted(k for k in papers if k not in EXCLUDED)
    cases = []
    for rep in range(1, replicates + 1):
        for pid in eligible:
            cases.append({"case_id": f"{pid}__r{rep}", "kind": "real", "human_paper": pid,
                          "model_paper": pid, "replicate": rep})
    for pid in EXCLUDED:
        if pid in papers:
            cases.append({"case_id": f"{pid}__mismatch", "kind": "documented_mismatch",
                          "human_paper": pid, "model_paper": pid, "replicate": 1})
    for k in range(min(N_CONTROLS, len(eligible))):
        h, m = eligible[k], eligible[(k + CONTROL_SHIFT) % len(eligible)]
        cases.append({"case_id": f"control__{h}__x__{m}", "kind": "cross_paper_control",
                      "human_paper": h, "model_paper": m, "replicate": 1})
    return cases


def blind(case: dict[str, Any], papers: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Randomise which list is A, shuffle items, and assign neutral IDs."""
    seed = int(hashlib.sha256(case["case_id"].encode()).hexdigest()[:8], 16)
    rng = random.Random(seed)
    human = list(papers[case["human_paper"]]["human"].items())
    model = list(papers[case["model_paper"]]["model"].items())
    human_is_a = rng.random() < 0.5
    a_items, b_items = (human, model) if human_is_a else (model, human)
    a_items, b_items = a_items[:], b_items[:]
    rng.shuffle(a_items)
    rng.shuffle(b_items)
    key = {}
    lines = ["List A:"]
    for j, (src_id, text) in enumerate(a_items, 1):
        key[f"A{j}"] = src_id
        lines.append(f"A{j}: {' '.join(text.split())}")
    lines += ["", "List B:"]
    for j, (src_id, text) in enumerate(b_items, 1):
        key[f"B{j}"] = src_id
        lines.append(f"B{j}: {' '.join(text.split())}")
    lines += ["", "Return JSON matching the supplied schema."]
    return {"seed": seed, "human_is_a": human_is_a, "key": key, "user_text": "\n".join(lines),
            "n_human": len(human), "n_model": len(model)}


LEAK_PATTERN = re.compile(
    r"(?i)\b(human|evaluators?|reviewers?|referees?|manager|notebooklm|llm|gpt|claude|e\d|"
    r"necessary|optional|unsure|i think|i agree|author'?s response|revised version)\b|[\[\]\"“”]")


def leak_scan(papers: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    """Words left after normalisation that could reveal a list's source (for review, not auto-fixed)."""
    hits = []
    for pid, sides in papers.items():
        for side, items in sides.items():
            for k, text in items.items():
                for m in LEAK_PATTERN.finditer(text):
                    hits.append({"paper": pid, "side": side, "id": k, "match": m.group(0),
                                 "context": text[max(0, m.start() - 50): m.end() + 50]})
    return hits


# --------------------------------------------------------------------------
# Metrics (computed here, never by the judge)
# --------------------------------------------------------------------------

def unblind_pairs(parsed: dict[str, Any], key: dict[str, str]) -> tuple[list[dict[str, Any]], list[str]]:
    out, errors = [], []
    for p in parsed.get("pairs", []):
        a, b = key.get(p["a_id"]), key.get(p["b_id"])
        if not a or not b or a[0] == b[0]:
            errors.append(f"bad ids {p['a_id']}/{p['b_id']}")
            continue
        human, model = (a, b) if a[0] == "H" else (b, a)
        side_of = {"A": a, "B": b}
        broader = side_of.get(p["broader_side"])
        out.append({"human": human, "model": model, "category": p["category"],
                    "broader": ("human" if broader and broader[0] == "H" else "model") if broader else "neither",
                    "confidence": p["confidence"], "reason": p["reason"]})
    return out, errors


def metrics(pairs: list[dict[str, Any]], n_human: int, n_model: int) -> dict[str, Any]:
    res: dict[str, Any] = {"n_human": n_human, "n_model": n_model, "n_pairs": len(pairs)}
    for level, cats in LEVELS.items():
        hit_h = {p["human"] for p in pairs if p["category"] in cats}
        hit_m = {p["model"] for p in pairs if p["category"] in cats}
        res[level] = {"human_covered": len(hit_h), "model_matched": len(hit_m),
                      "coverage": round(100 * len(hit_h) / n_human, 1) if n_human else None,
                      "overlap": round(100 * len(hit_m) / n_model, 1) if n_model else None}
    res["category_counts"] = {c: sum(1 for p in pairs if p["category"] == c) for c in CATEGORIES}
    # Standard-level matches that rest only on a broader model item.
    std = [p for p in pairs if p["category"] in LEVELS["standard"]]
    only_broad = {p["human"] for p in std} - {p["human"] for p in std if not (p["category"] == "same_concern_different_scope" and p["broader"] == "model")}
    res["human_covered_only_by_broader_model_item"] = len(only_broad)
    return res


# --------------------------------------------------------------------------
# Running
# --------------------------------------------------------------------------

def call_judge(client, user_text: str, raw_path: pathlib.Path) -> dict[str, Any]:
    import anthropic
    import time

    t0 = time.time()
    try:
        with client.messages.stream(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            thinking={"type": "adaptive", "display": "summarized"},
            output_config={"effort": EFFORT, "format": {"type": "json_schema", "schema": api_schema(JUDGE_SCHEMA)}},
            messages=[{"role": "user", "content": user_text}],
        ) as stream:
            msg = stream.get_final_message()
    except (anthropic.APIStatusError, anthropic.APIConnectionError) as e:
        return {"error": f"{type(e).__name__}: {e}", "elapsed_seconds": round(time.time() - t0, 1)}
    d = msg.to_dict()
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps(d, ensure_ascii=False))
    text = "".join(b.get("text", "") or "" for b in d.get("content", []) if b.get("type") == "text")
    return {"elapsed_seconds": round(time.time() - t0, 1), "model": d.get("model"), "response_id": d.get("id"),
            "stop_reason": d.get("stop_reason"), "usage": d.get("usage"), "text": text}


def spend(run_dir: pathlib.Path) -> float:
    p = run_dir / "spend_ledger.csv"
    if not p.exists():
        return 0.0
    with p.open() as f:
        return sum(float(r["est_cost_usd"]) for r in csv.DictReader(f))


def record_spend(run_dir: pathlib.Path, row: dict[str, Any]) -> None:
    p = run_dir / "spend_ledger.csv"
    fields = ["timestamp", "case_id", "status", "input_tokens", "output_tokens", "est_cost_usd", "elapsed_seconds"]
    new = not p.exists()
    with p.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in fields})


def summarise(run_dir: pathlib.Path) -> dict[str, Any]:
    rows = []
    for f in sorted((run_dir / "calls").glob("*.json")):
        if f.name.endswith(".raw_response.json"):
            continue
        c = json.loads(f.read_text())
        if "metrics" in c:
            rows.append(c)
    summary: dict[str, Any] = {"n_calls": len(rows), "by_kind": {}}
    for kind in ("real", "documented_mismatch", "cross_paper_control"):
        sub = [r for r in rows if r["case"]["kind"] == kind]
        if not sub:
            continue
        agg: dict[str, Any] = {"n": len(sub), "same_study": {}}
        for r in sub:
            agg["same_study"][r["parsed"]["same_study"]] = agg["same_study"].get(r["parsed"]["same_study"], 0) + 1
        for level in LEVELS:
            hc = sum(r["metrics"][level]["human_covered"] for r in sub)
            nh = sum(r["metrics"]["n_human"] for r in sub)
            mm = sum(r["metrics"][level]["model_matched"] for r in sub)
            nm = sum(r["metrics"]["n_model"] for r in sub)
            agg[level] = {"pooled_coverage": round(100 * hc / nh, 1), "pooled_overlap": round(100 * mm / nm, 1),
                          "mean_paper_coverage": round(sum(r["metrics"][level]["coverage"] for r in sub) / len(sub), 1),
                          "mean_paper_overlap": round(sum(r["metrics"][level]["overlap"] for r in sub) / len(sub), 1),
                          "human_covered": hc, "n_human": nh, "model_matched": mm, "n_model": nm}
        summary["by_kind"][kind] = agg
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2))
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-id", default=DEFAULT_RUN_ID)
    ap.add_argument("--replicates", type=int, default=2)
    ap.add_argument("--case", action="append", help="Only these case ids")
    ap.add_argument("--budget", type=float, default=15.0)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--summarise-only", action="store_true")
    ap.add_argument("--normalize-only", action="store_true", help="Run only the Haiku rewrite step and leak scan")
    args = ap.parse_args()

    run_dir = ROOT / "results" / args.run_id
    calls = run_dir / "calls"
    papers = load_papers()
    cases = build_cases(papers, args.replicates)
    if args.case:
        cases = [c for c in cases if c["case_id"] in set(args.case)]
    if args.summarise_only:
        print(json.dumps(summarise(run_dir), indent=2))
        return 0

    calls.mkdir(parents=True, exist_ok=True)
    (run_dir / "run_config.json").write_text(json.dumps({
        "run_id": args.run_id, "model": MODEL, "effort": EFFORT, "prompt_version": PROMPT_VERSION,
        "system_prompt_sha256": hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest(),
        "source": str(SOURCE.relative_to(ROOT)), "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "excluded_from_real": list(EXCLUDED), "control_shift": CONTROL_SHIFT, "n_cases": len(cases),
        "sdk_version": sdk_version(), "created": datetime.now(timezone.utc).isoformat(),
    }, indent=2))
    (run_dir / "system_prompt.txt").write_text(SYSTEM_PROMPT)

    client = None if args.dry_run else make_client()
    if not args.dry_run:
        needed = {c["human_paper"] for c in cases} | {c["model_paper"] for c in cases}
        papers = normalized_papers(client, papers, run_dir, needed)
        leaks = leak_scan(papers)
        (run_dir / "blinding_leak_scan.json").write_text(json.dumps(leaks, indent=2, ensure_ascii=False))
        print(f"normalized {len(needed)} papers; leak-scan hits: {len(leaks)}")
        if args.normalize_only:
            return 0
    for case in cases:
        out = calls / f"{case['case_id']}.json"
        if out.exists() and not args.force:
            continue
        b = blind(case, papers)
        if args.dry_run:
            print(f"{case['case_id']}: {b['n_human']} human, {b['n_model']} model, human_is_a={b['human_is_a']}, {len(b['user_text'])} chars")
            continue
        if spend(run_dir) >= args.budget:
            print(f"budget ${args.budget} reached; stopping")
            break
        print(f"judge {case['case_id']} ...", flush=True)
        r = call_judge(client, b["user_text"], calls / f"{case['case_id']}.raw_response.json")
        usage = r.get("usage") or {}
        cost = estimate_cost(usage) if usage else 0.0
        status = "error" if "error" in r else "ok"
        parsed = None
        if status == "ok":
            try:
                parsed = json.loads(r["text"])
            except json.JSONDecodeError:
                status = "parse_error"
        record_spend(run_dir, {"timestamp": datetime.now(timezone.utc).isoformat(), "case_id": case["case_id"],
                               "status": status, "input_tokens": usage.get("input_tokens"),
                               "output_tokens": usage.get("output_tokens"), "est_cost_usd": cost,
                               "elapsed_seconds": r.get("elapsed_seconds")})
        rec: dict[str, Any] = {"case": case, "blinding": {k: b[k] for k in ("seed", "human_is_a", "key")},
                               "status": status, "est_cost_usd": cost, "model": r.get("model"),
                               "stop_reason": r.get("stop_reason"), "error": r.get("error")}
        if parsed is not None:
            pairs, errors = unblind_pairs(parsed, b["key"])
            rec.update({"parsed": parsed, "pairs": pairs, "id_errors": errors,
                        "metrics": metrics(pairs, b["n_human"], b["n_model"])})
            m = rec["metrics"]["standard"]
            print(f"  same_study={parsed['same_study']} standard coverage {m['coverage']}% overlap {m['overlap']}% (${cost:.2f})")
        out.write_text(json.dumps(rec, indent=2, ensure_ascii=False))
    if not args.dry_run:
        print(json.dumps(summarise(run_dir), indent=2))
        print(f"estimated spend ${spend(run_dir):.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
