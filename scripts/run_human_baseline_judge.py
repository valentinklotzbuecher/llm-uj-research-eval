#!/usr/bin/env python3
"""
Human-to-human baseline for critique overlap, with the blinded v2 judge.

For each paper with two or more usable published evaluator reports, the frozen
per-evaluator issue lists (data/human_issue_reference/items/) are compared pair
by pair (E1 vs E2, and every pair when there are three), using the v2 judge's
own rewrite, blinding, rubric and code-computed coverage, imported unchanged
from scripts/run_issue_match_judge.py.

Three kinds of case:
  hh        evaluator vs evaluator on the same paper (the baseline);
  model_ev  GPT-5.2 Pro key issues (tools/issue_annotation_ui/data.json) vs a
            single evaluator's list, for the papers that have model issues:
            the like-for-like comparator for the baseline;
  control   evaluator list of one paper vs an evaluator list of another.

Directed coverage: for a pair (A, B), the share of A's items that B raised and
the share of B's items that A raised, at the judge's strict, standard and loose
levels. For "hh" both directions are evaluator coverage; for "model_ev" the
"human" side is the evaluator.

Evaluator-vs-evaluator is not the comparison made in the model-vs-curated-human
figures (one model list vs a consensus list curated from several evaluators).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import pathlib
import sys
from datetime import datetime, timezone
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import run_issue_match_judge as v2  # noqa: E402
from run_headless_claude_misses import estimate_cost, make_client, sdk_version  # noqa: E402

REF_DIR = ROOT / "data" / "human_issue_reference"
DEFAULT_RUN_ID = "human_baseline_judge_2026-11-10"
# The 12 papers in the existing model-vs-curated-human critique comparison.
CORE = sorted({r["gpt_paper"] for r in json.loads((ROOT / "results" / "key_issues_comparison_results.json").read_text())}
              - set(v2.EXCLUDED))
N_CONTROLS = 6
CONTROL_SHIFT = 7


def item_text(it: dict[str, Any]) -> str:
    parts = [it["about"].strip().rstrip(".") + ".", it["problem"].strip()]
    if it.get("consequence", "").strip():
        parts.append(it["consequence"].strip())
    return " ".join(parts)


def load_reference() -> dict[str, dict[str, list[dict[str, Any]]]]:
    """paper -> evaluator source (E1, E2, E3) -> frozen items. Manager summaries are left out."""
    with (REF_DIR / "manifest.csv").open() as f:
        man = {r["paper"]: r for r in csv.DictReader(f)}
    ref = {}
    for f in sorted((REF_DIR / "items").glob("*.json")):
        rec = json.loads(f.read_text())
        pid = rec["paper"]
        if man.get(pid, {}).get("status") != "eligible_pair":
            continue
        evs = {s: v["items"] for s, v in rec["sources"].items()
               if s.startswith("E") and s[1:].isdigit() and v.get("status") == "ok" and v["items"]}
        if len(evs) >= 2:
            ref[pid] = evs
    return ref


def build_cases(ref: dict[str, Any], model_papers: set[str], replicates: int, model_reps: int) -> list[dict[str, Any]]:
    cases = []
    order = [p for p in CORE if p in ref] + [p for p in sorted(ref) if p not in CORE]
    for rep in range(1, replicates + 1):
        for pid in order:
            for a, b in itertools.combinations(sorted(ref[pid]), 2):
                cases.append({"case_id": f"hh__{pid}__{a}_{b}__r{rep}", "kind": "hh", "paper": pid,
                              "a": f"{pid}::{a}", "b": f"{pid}::{b}", "replicate": rep, "core": pid in CORE})
    for rep in range(1, model_reps + 1):
        for pid in order:
            if pid not in model_papers:
                continue
            for e in sorted(ref[pid]):
                cases.append({"case_id": f"model_ev__{pid}__{e}__r{rep}", "kind": "model_ev", "paper": pid,
                              "a": f"{pid}::{e}", "b": f"{pid}::MODEL", "replicate": rep, "core": pid in CORE})
    core = [p for p in CORE if p in ref]
    for k in range(min(N_CONTROLS, len(core))):
        p, q = core[k], core[(k + CONTROL_SHIFT) % len(core)]
        ea, eb = sorted(ref[p])[0], sorted(ref[q])[-1]
        cases.append({"case_id": f"control__{p}_{ea}__x__{q}_{eb}", "kind": "control", "paper": p,
                      "a": f"{p}::{ea}", "b": f"{q}::{eb}", "replicate": 1, "core": True})
    return cases


def normalized_lists(client, ref, model_issues, run_dir: pathlib.Path, needed: set[str]) -> tuple[dict[str, dict[str, str]], dict[str, Any]]:
    """Neutral statements per list (v2 rewrite step), keyed by list name; local ids map back to frozen ids."""
    lists, idmap = {}, {}
    for name in sorted(needed):
        pid, src = name.split("::")
        if src == "MODEL":
            raw = model_issues[pid]
            local = {f"M{i}": t for i, t in enumerate(raw.values(), 1)}
            idmap[name] = {f"M{i}": k for i, k in enumerate(raw, 1)}
        else:
            items = ref[pid][src]
            local = {f"M{i}": item_text(it) for i, it in enumerate(items, 1)}
            idmap[name] = {f"M{i}": it["id"] for i, it in enumerate(items, 1)}
        rec = v2.normalize_side(client, local, run_dir / "normalized" / f"{pid}__{src}.json")
        lists[name] = {k: v2.scrub(v["statement"]) for k, v in rec["items"].items()
                       if not v["no_substantive_concern"] and v["statement"]}
    return lists, idmap


def as_v2_papers(case: dict[str, Any], lists: dict[str, dict[str, str]]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Shape one case for v2.blind: side A as the 'human' list (H ids), side B as the 'model' list (L ids)."""
    a = {"H" + k[1:]: v for k, v in lists[case["a"]].items()}
    b = {"L" + k[1:]: v for k, v in lists[case["b"]].items()}
    papers = {"A": {"human": a, "model": {}}, "B": {"human": {}, "model": b}}
    return papers, {"case_id": case["case_id"], "human_paper": "A", "model_paper": "B"}


def minor_ids(ref, name: str) -> set[str]:
    pid, src = name.split("::")
    if src == "MODEL":
        return set()
    return {f"M{i}" for i, it in enumerate(ref[pid][src], 1) if it.get("minor")}


def metrics_excluding_minor(pairs, a_ids: set[str], b_ids: set[str], a_minor: set[str], b_minor: set[str]) -> dict[str, Any]:
    """Coverage restricted to non-minor items on both sides (pairs to minor items dropped)."""
    keep_a = {"H" + x[1:] for x in a_ids - a_minor}
    keep_b = {"L" + x[1:] for x in b_ids - b_minor}
    sub = [p for p in pairs if p["human"] in keep_a and p["model"] in keep_b]
    return v2.metrics(sub, len(keep_a), len(keep_b))


def spend(run_dir: pathlib.Path) -> float:
    return v2.spend(run_dir)


def extraction_spend() -> float:
    p = REF_DIR / "extraction_ledger.csv"
    if not p.exists():
        return 0.0
    with p.open() as f:
        return sum(float(r["est_cost_usd"]) for r in csv.DictReader(f))


def summarise(run_dir: pathlib.Path) -> dict[str, Any]:
    rows = [json.loads(f.read_text()) for f in sorted((run_dir / "calls").glob("*.json"))
            if not f.name.endswith(".raw_response.json")]
    rows = [r for r in rows if "metrics" in r]
    out: dict[str, Any] = {"n_calls": len(rows), "by_kind": {}}

    def pool(sub, key="metrics", both=True):
        res = {}
        for level in v2.LEVELS:
            a_cov = sum(r[key][level]["human_covered"] for r in sub)
            a_n = sum(r[key]["n_human"] for r in sub)
            b_cov = sum(r[key][level]["model_matched"] for r in sub)
            b_n = sum(r[key]["n_model"] for r in sub)
            d = {"a_covered": a_cov, "a_n": a_n, "b_covered": b_cov, "b_n": b_n,
                 "a_coverage": round(100 * a_cov / a_n, 1) if a_n else None,
                 "b_coverage": round(100 * b_cov / b_n, 1) if b_n else None}
            if both:
                d["pooled_both_directions"] = round(100 * (a_cov + b_cov) / (a_n + b_n), 1) if a_n + b_n else None
            per = [r[key][level]["coverage"] for r in sub if r[key][level]["coverage"] is not None]
            if both:
                per += [r[key][level]["overlap"] for r in sub if r[key][level]["overlap"] is not None]
            d["mean_directed_coverage"] = round(sum(per) / len(per), 1) if per else None
            res[level] = d
        return res

    for kind in ("hh", "model_ev", "control"):
        sub = [r for r in rows if r["case"]["kind"] == kind]
        if not sub:
            continue
        agg: dict[str, Any] = {"n_calls": len(sub), "n_papers": len({r["case"]["paper"] for r in sub}),
                               "same_study": {}}
        for r in sub:
            s = r["parsed"]["same_study"]
            agg["same_study"][s] = agg["same_study"].get(s, 0) + 1
        agg["all"] = pool(sub, both=(kind != "model_ev"))
        agg["excluding_minor"] = pool(sub, key="metrics_excl_minor", both=(kind != "model_ev"))
        core = [r for r in sub if r["case"]["core"]]
        if core and kind != "control":
            agg["core_papers"] = {"n_calls": len(core), "n_papers": len({r["case"]["paper"] for r in core}),
                                  "all": pool(core, both=(kind != "model_ev"))}
        out["by_kind"][kind] = agg
    (run_dir / "summary.json").write_text(json.dumps(out, indent=2))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run-id", default=DEFAULT_RUN_ID)
    ap.add_argument("--replicates", type=int, default=2)
    ap.add_argument("--model-replicates", type=int, default=1)
    ap.add_argument("--kind", action="append", choices=["hh", "model_ev", "control"])
    ap.add_argument("--core-only", action="store_true")
    ap.add_argument("--total-budget", type=float, default=15.0, help="Cap on extraction + judge spend")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--summarise-only", action="store_true")
    args = ap.parse_args()

    run_dir = ROOT / "results" / args.run_id
    calls = run_dir / "calls"
    if args.summarise_only:
        print(json.dumps(summarise(run_dir), indent=2))
        return 0
    ref = load_reference()
    v2_papers = v2.load_papers()
    model_issues = {p: v2_papers[p]["model"] for p in v2_papers if p in ref and p not in v2.EXCLUDED}
    cases = build_cases(ref, set(model_issues), args.replicates, args.model_replicates)
    if args.kind:
        cases = [c for c in cases if c["kind"] in args.kind]
    if args.core_only:
        cases = [c for c in cases if c["core"]]

    calls.mkdir(parents=True, exist_ok=True)
    ref_files = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((REF_DIR / "items").glob("*.json"))}
    (run_dir / "run_config.json").write_text(json.dumps({
        "run_id": args.run_id, "judge_model": v2.MODEL, "judge_effort": v2.EFFORT, "judge_prompt_version": v2.PROMPT_VERSION,
        "judge_system_prompt_sha256": hashlib.sha256(v2.SYSTEM_PROMPT.encode()).hexdigest(),
        "normalizer_model": v2.NORMALIZER_MODEL,
        "normalizer_prompt_sha256": hashlib.sha256(v2.NORMALIZER_PROMPT.encode()).hexdigest(),
        "levels": {k: sorted(v) for k, v in v2.LEVELS.items()},
        "reference_items_sha256": ref_files,
        "model_issue_source": str(v2.SOURCE.relative_to(ROOT)), "model_issue_source_sha256": hashlib.sha256(v2.SOURCE.read_bytes()).hexdigest(),
        "core_papers": CORE, "n_reference_papers": len(ref), "n_cases_planned": len(cases),
        "control_shift": CONTROL_SHIFT, "sdk_version": sdk_version(), "created": datetime.now(timezone.utc).isoformat(),
    }, indent=2))

    if args.dry_run:
        for c in cases:
            print(c["case_id"], c["kind"], len(ref[c["a"].split('::')[0]].get(c["a"].split('::')[1], [])))
        print(f"{len(cases)} cases")
        return 0

    client = make_client()
    needed = {c["a"] for c in cases} | {c["b"] for c in cases}
    lists, idmap = normalized_lists(client, ref, model_issues, run_dir, needed)
    leaks = v2.leak_scan({n: {"list": items} for n, items in lists.items()})
    (run_dir / "blinding_leak_scan.json").write_text(json.dumps(leaks, indent=2, ensure_ascii=False))
    print(f"normalized {len(needed)} lists; leak-scan hits: {len(leaks)}")
    for case in cases:
        out = calls / f"{case['case_id']}.json"
        if out.exists():
            continue
        total = spend(run_dir) + extraction_spend()
        if total >= args.total_budget:
            print(f"total budget ${args.total_budget} reached (${total:.2f}); stopping")
            break
        papers, v2case = as_v2_papers(case, lists)
        b = v2.blind(v2case, papers)
        print(f"judge {case['case_id']} ({b['n_human']} x {b['n_model']}) ...", flush=True)
        r = v2.call_judge(client, b["user_text"], calls / f"{case['case_id']}.raw_response.json")
        usage = r.get("usage") or {}
        cost = estimate_cost(usage) if usage else 0.0
        status = "error" if "error" in r else "ok"
        parsed = None
        if status == "ok":
            try:
                parsed = json.loads(r["text"])
            except json.JSONDecodeError:
                status = "parse_error"
        v2.record_spend(run_dir, {"timestamp": datetime.now(timezone.utc).isoformat(), "case_id": case["case_id"],
                                  "status": status, "input_tokens": usage.get("input_tokens"),
                                  "output_tokens": usage.get("output_tokens"), "est_cost_usd": cost,
                                  "elapsed_seconds": r.get("elapsed_seconds")})
        rec: dict[str, Any] = {"case": case, "blinding": {k: b[k] for k in ("seed", "human_is_a", "key")},
                               "frozen_ids": {"a": idmap[case["a"]], "b": idmap[case["b"]]},
                               "status": status, "est_cost_usd": cost, "model": r.get("model"),
                               "stop_reason": r.get("stop_reason"), "error": r.get("error")}
        if parsed is not None:
            pairs, errors = v2.unblind_pairs(parsed, b["key"])
            a_ids, b_ids = set(lists[case["a"]]), set(lists[case["b"]])
            rec.update({"parsed": parsed, "pairs": pairs, "id_errors": errors,
                        "metrics": v2.metrics(pairs, b["n_human"], b["n_model"]),
                        "metrics_excl_minor": metrics_excluding_minor(pairs, a_ids, b_ids,
                                                                      minor_ids(ref, case["a"]), minor_ids(ref, case["b"]))})
            m = rec["metrics"]["standard"]
            print(f"  same_study={parsed['same_study']} standard A->B {m['coverage']}%  B->A {m['overlap']}% (${cost:.3f})")
        out.write_text(json.dumps(rec, indent=2, ensure_ascii=False))
    print(json.dumps(summarise(run_dir), indent=2))
    print(f"judge spend ${spend(run_dir):.2f}; extraction spend ${extraction_spend():.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
