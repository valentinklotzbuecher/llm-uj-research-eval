#!/usr/bin/env python3
"""
Data and scoring for the human audit of AI issue matching.

`export` gathers every judged human-vs-model issue comparison in this repo into
one file that the browser audit page reads:

  results/match_audit/audit_data.json   (committed; the page loads the latest
                                          copy from GitHub, so a push is enough
                                          to update the hosted page)

and, when the sibling checkout ../unjournal_tools_interfaces exists, also writes
a bundled fallback copy there (annotation/ui/audit_data.js) so the page works
offline and from file://.

Datasets currently exported:

  gpt52_focal_jan2026        the original 12-paper comparison: GPT-5.2 Pro wrote
                             the model issues and judged the matches against
                             curated consensus critiques. The judge numbered the
                             human issues itself and kept only a short
                             description of each; those descriptions are the
                             issue text, with the full critique as context. The
                             two known mispairings (Benabou, Peterman) are left out.
  <pilot run id>             every results/critique_overlap_pilot_*/ run: issues
                             extracted from the published evaluations, two judges.

`score` reads reviewer exports from the audit page (JSON files saved under
data/human_issue_match_annotations/audit/) and reports, per dataset and judge,
how often the judge's proposed matches were confirmed (precision), how many of
the reviewer's matches the judge proposed (recall), and Cohen's kappa; plus
reviewer-to-reviewer agreement where two reviewers saw the same pair.

Evaluator names never enter the export: human issue text from the curated
critiques passes through the same anonymiser used for external Codex prompts,
and pilot issues refer to evaluators as E1, E2.

Usage:
    python scripts/match_audit.py export
    python scripts/match_audit.py score [--threshold 30]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys
from datetime import datetime, timezone
from itertools import combinations
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tools"))

OUT_DIR = ROOT / "results" / "match_audit"
OUT_JSON = OUT_DIR / "audit_data.json"
TOOLS_UI = ROOT.parent / "unjournal_tools_interfaces" / "annotation" / "ui"
REVIEWS_DIR = ROOT / "data" / "human_issue_match_annotations" / "audit"
FOCAL_RESULTS = ROOT / "results" / "key_issues_comparison_results.json"
LEGACY_EXCLUDED = {"Benabou_et_al._2023": "human critique concerns a different paper",
                   "Peterman_et_al._2025": "human critique concerns a different paper"}
PUBPUB = "https://unjournal.pubpub.org/pub/"
SCHEMA_VERSION = 1

JUDGE_INFO = {
    "gpt52pro": {"label": "GPT-5.2 Pro", "note": "Also wrote the model issues it judged."},
    "codex": {"label": "GPT judge (gpt-5.6-terra via Codex)", "note": "Different model family from the generator."},
    "sonnet": {"label": "Claude Sonnet 5.5", "note": "Same model family as the generator (Opus 5.5)."},
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_head() -> str:
    proc = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True)
    return proc.stdout.strip()


# --------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------

def focal_dataset() -> dict[str, Any] | None:
    if not FOCAL_RESULTS.exists():
        return None
    from run_concordance_codex import anonymize_human_issue

    papers = []
    for row in json.loads(FOCAL_RESULTS.read_text()):
        pid = row["gpt_paper"]
        if pid in LEGACY_EXCLUDED:
            continue
        comp = row.get("comparison") or {}
        # The judge received the whole curated critique and numbered the issues itself (methods.qmd),
        # without saving the text of each. Its own short descriptions are the only per-issue wording
        # that lines up with its indices, so they are used here; the full critique is shown alongside.
        desc: dict[int, str] = {}
        for mp in comp.get("matched_pairs", []):
            desc[int(mp["human_issue_index"])] = mp.get("label", "")
        for u in comp.get("unmatched_human", []):
            desc[int(u["index"])] = u.get("brief_description", "")
        human_issues = [{
            "id": f"{pid}::H{i:02d}",
            "text": anonymize_human_issue(desc[i]),
            "text_source": "judge's short description of the curated critique item",
        } for i in sorted(desc)]
        model_issues = [{"id": f"{pid}::L{i:02d}", "text": t.strip()}
                        for i, t in enumerate(row.get("gpt_key_issues", []), start=1)]
        matches = []
        hid = {int(h["id"].rsplit("::H", 1)[1]): h["id"] for h in human_issues}
        for mp in comp.get("matched_pairs", []):
            hi = int(mp["human_issue_index"])
            for li in mp.get("llm_issue_indices", []):
                if hi in hid and 1 <= int(li) <= len(model_issues):
                    matches.append({"human_id": hid[hi],
                                    "model_id": model_issues[int(li) - 1]["id"],
                                    "score": int(mp.get("match_quality", 0)),
                                    "label": "",
                                    "reason": mp.get("match_explanation", "")})
        papers.append({
            "paper_id": pid,
            "title": row.get("coda_title", ""),
            "links": [{"label": "Search Unjournal", "url": "https://unjournal.pubpub.org/search?q="
                       + (row.get("coda_title") or pid).replace(" ", "%20")}],
            "context": anonymize_human_issue(row.get("coda_critique", "")),
            "context_label": "Full curated critique the judge was given",
            "human_issues": human_issues,
            "model_issues": model_issues,
            "judge_matches": {"gpt52pro": matches},
        })
    return {
        "id": "gpt52_focal_jan2026",
        "title": "Original 12 papers: GPT-5.2 Pro issues vs curated consensus critiques",
        "description": "Human issues come from the evaluation managers' curated consensus critiques. GPT-5.2 Pro "
                       "numbered the items itself and saved only a short description of each, so that description "
                       "is shown; open the full critique to check it. GPT-5.2 Pro also wrote the model issues it "
                       "judged, and returned a 0-100 match quality but no match label.",
        "judges": [{"id": "gpt52pro", **JUDGE_INFO["gpt52pro"]}],
        "papers": papers,
    }


def pilot_dataset(run_dir: pathlib.Path) -> dict[str, Any] | None:
    sel_path = run_dir / "selection.json"
    if not sel_path.exists() or not (run_dir / "judge").is_dir():
        return None
    sel = json.loads(sel_path.read_text())
    judges = sorted(d.name for d in (run_dir / "judge").iterdir() if d.is_dir())
    papers = []
    for p in sel["papers"]:
        pid = p["paper"]
        human_issues = []
        for ev in p["evaluations"]:
            f = run_dir / "human_issues" / f"{pid}__{ev['label']}.json"
            if not f.exists():
                continue
            for it in json.loads(f.read_text())["issues"]:
                human_issues.append({"id": it["id"], "text": it["text"], "evaluator": ev["label"],
                                     "importance": it.get("importance", ""), "quote": it.get("quote", ""),
                                     "quote_verified": it.get("quote_verified")})
        model_file = None
        for cand in (run_dir / "A" / f"{pid}.json",
                     ROOT / "results" / "claude_opus_5_5_high_misses_2026-11-04" / "A" / f"{pid}.json"):
            if cand.exists():
                model_file = cand
                break
        if model_file is None:
            continue
        key_issues = json.loads(model_file.read_text())["parsed"]["key_issues"]
        model_issues = [{"id": f"{pid}::M{i:02d}", "text": t.strip()} for i, t in enumerate(key_issues, start=1)]
        jm: dict[str, list[dict[str, Any]]] = {}
        for j in judges:
            f = run_dir / "judge" / j / f"real__{pid}.json"
            if not f.exists():
                continue
            d = json.loads(f.read_text())
            s1, s2 = set(d["side1_ids"]), set(d["side2_ids"])
            d["matches"] = [m for m in d["matches"] if m["side1_id"] in s1 and m["side2_id"] in s2]
            jm[j] = [{"human_id": m["side1_id"], "model_id": m["side2_id"], "score": int(m["score"]),
                      "label": m.get("label", ""), "reason": m.get("reason", "")} for m in d["matches"]]
        papers.append({
            "paper_id": pid,
            "title": p.get("research_title", ""),
            "links": [{"label": f"Evaluation {ev['label'][1:]}", "url": PUBPUB + ev["slug"]} for ev in p["evaluations"]],
            "human_issues": human_issues,
            "model_issues": model_issues,
            "judge_matches": jm,
        })
    return {
        "id": run_dir.name,
        "title": f"Pilot ({run_dir.name.rsplit('_', 1)[-1]}): Opus 5.5 issues vs issues from the published evaluations",
        "description": "Human issues were extracted blind from each published evaluation (one list per evaluator). "
                       "Model issues: Claude Opus 5.5 given the PDF only. Both judges saw unlabeled, shuffled lists.",
        "judges": [{"id": j, **JUDGE_INFO.get(j, {"label": j, "note": ""})} for j in judges],
        "papers": papers,
    }


def build_export() -> dict[str, Any]:
    datasets = []
    for run_dir in sorted((ROOT / "results").glob("critique_overlap_pilot_*"), reverse=True):
        ds = pilot_dataset(run_dir)
        if ds:
            datasets.append(ds)
    focal = focal_dataset()
    if focal:
        datasets.append(focal)
    return {"schema_version": SCHEMA_VERSION, "generated_at": utc_now(), "source_commit": git_head(),
            "source_repo": "valentinklotzbuecher/llm-uj-research-eval", "datasets": datasets}


def content_hash(data: dict[str, Any]) -> str:
    body = {k: v for k, v in data.items() if k not in ("generated_at", "source_commit")}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def write_export(data: dict[str, Any], out_json: pathlib.Path = OUT_JSON, tools_ui: pathlib.Path = TOOLS_UI) -> list[str]:
    """Write only when the content changed, so re-running is a no-op in git."""
    data = {**data, "content_sha256": content_hash(data)}
    written = []
    if out_json.exists():
        old = json.loads(out_json.read_text())
        if old.get("content_sha256") == data["content_sha256"]:
            data = old
    out_json.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(data, indent=1, ensure_ascii=False)
    if not out_json.exists() or out_json.read_text() != text:
        out_json.write_text(text)
        written.append(str(out_json))
    if tools_ui.is_dir():
        js = tools_ui / "audit_data.js"
        js_text = "// Generated by llm-uj-research-eval/scripts/match_audit.py export. Do not edit.\n" \
                  "window.AUDIT_DATA = " + text + ";\n"
        if not js.exists() or js.read_text() != js_text:
            js.write_text(js_text)
            written.append(str(js))
    return written


# --------------------------------------------------------------------------
# Scoring reviewer exports
# --------------------------------------------------------------------------

ACCEPT = {"same": 1, "partial": 1, "different": 0}


def cohen_kappa(x: list[int], y: list[int]) -> float | None:
    n = len(x)
    if n == 0 or n != len(y):
        return None
    po = sum(a == b for a, b in zip(x, y)) / n
    px, py = sum(x) / n, sum(y) / n
    pe = px * py + (1 - px) * (1 - py)
    if pe == 1:
        return None
    return round((po - pe) / (1 - pe), 3)


def judge_proposes(match: dict[str, Any], threshold: int) -> bool:
    return match["score"] >= threshold


def score_reviews(data: dict[str, Any], reviews: list[dict[str, Any]], threshold: int = 30) -> dict[str, Any]:
    """reviews: audit-page exports, each {reviewer, verdicts: [{dataset, human_id, model_id, verdict}]}."""
    out: dict[str, Any] = {"threshold": threshold, "datasets": {}}
    for ds in data["datasets"]:
        judged: dict[str, dict[tuple[str, str], bool]] = {}
        for p in ds["papers"]:
            for j, ms in p["judge_matches"].items():
                for m in ms:
                    judged.setdefault(j, {})[(m["human_id"], m["model_id"])] = judge_proposes(m, threshold)
        by_reviewer: dict[str, dict[tuple[str, str], int]] = {}
        for r in reviews:
            for v in r.get("verdicts", []):
                if v.get("dataset") == ds["id"] and v.get("verdict") in ACCEPT:
                    by_reviewer.setdefault(r.get("reviewer") or "anonymous", {})[(v["human_id"], v["model_id"])] = ACCEPT[v["verdict"]]
        res: dict[str, Any] = {"reviewers": {}, "reviewer_agreement": []}
        for rv, verdicts in by_reviewer.items():
            per_judge = {}
            for j in [x["id"] for x in ds["judges"]]:
                jp = judged.get(j, {})
                pairs = list(verdicts)
                x = [int(jp.get(k, False)) for k in pairs]
                y = [verdicts[k] for k in pairs]
                proposed = [k for k in pairs if jp.get(k, False)]
                accepted = [k for k in pairs if verdicts[k] == 1]
                per_judge[j] = {
                    "pairs_reviewed": len(pairs),
                    "judge_proposals_reviewed": len(proposed),
                    "proposals_confirmed": sum(verdicts[k] for k in proposed),
                    "precision": round(sum(verdicts[k] for k in proposed) / len(proposed), 3) if proposed else None,
                    "reviewer_matches": len(accepted),
                    "reviewer_matches_judge_proposed": sum(1 for k in accepted if jp.get(k, False)),
                    "recall": round(sum(1 for k in accepted if jp.get(k, False)) / len(accepted), 3) if accepted else None,
                    "kappa": cohen_kappa(x, y),
                }
            res["reviewers"][rv] = per_judge
        for a, b in combinations(sorted(by_reviewer), 2):
            shared = sorted(set(by_reviewer[a]) & set(by_reviewer[b]))
            x = [by_reviewer[a][k] for k in shared]
            y = [by_reviewer[b][k] for k in shared]
            res["reviewer_agreement"].append({
                "reviewers": [a, b], "shared_pairs": len(shared),
                "percent_agreement": round(100 * sum(u == w for u, w in zip(x, y)) / len(shared), 1) if shared else None,
                "kappa": cohen_kappa(x, y)})
        if res["reviewers"]:
            out["datasets"][ds["id"]] = res
    return out


def load_reviews(paths: list[pathlib.Path]) -> list[dict[str, Any]]:
    reviews = []
    for p in paths:
        d = json.loads(p.read_text())
        if d.get("tool") == "issue-match-audit":
            reviews.append(d)
    return reviews


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["export", "score"])
    ap.add_argument("--threshold", type=int, default=30)
    ap.add_argument("--reviews", type=pathlib.Path, nargs="*")
    args = ap.parse_args()
    if args.command == "export":
        data = build_export()
        written = write_export(data)
        n = {d["id"]: (len(d["papers"]), sum(len(p["human_issues"]) for p in d["papers"])) for d in data["datasets"]}
        print("datasets (papers, human issues):", n)
        print("written:" if written else "unchanged", *[str(pathlib.Path(w)) for w in written], sep="\n  ")
        return 0
    data = json.loads(OUT_JSON.read_text())
    paths = args.reviews or sorted(REVIEWS_DIR.glob("*.json"))
    result = score_reviews(data, load_reviews(paths), args.threshold)
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
