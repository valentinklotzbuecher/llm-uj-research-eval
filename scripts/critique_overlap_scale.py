#!/usr/bin/env python3
"""
Scaled critique-overlap run: the pipeline of scripts/critique_overlap_pilot.py
applied to every paper that meets the pilot's selection rule, plus bootstrap
intervals over papers.

This wrapper imports the pilot module and changes nothing in it or in the pilot
outputs (results/critique_overlap_pilot_2026-11-10/). Differences from the pilot:

- select:    all papers that meet the pilot rule (eligible in
             data/critique_eligibility_manifest.json, >= 2 substantive individual
             evaluations, PDF dated on or before the first evaluation), in the
             pilot's order (SHA-256 of the paper label). The documented
             mispairings (Benabou, Peterman) are excluded by the manifest and
             again here. Evaluation documents are recorded by doc_ref
             (sha256 of the export file name, first 12 hex) and file SHA-256,
             not by slug or file name, because some slugs carry evaluator names.
- extract:   identical prompt, model and quote check as the pilot. For the five
             pilot papers the pilot's frozen human-issue files are copied (after
             checking the source hash) rather than re-extracted. Each new issue
             is checked for reviewer-name tokens taken from the evaluation
             documents' front matter; any hit is replaced by "[name]" and
             counted.
- generate:  model issues (Claude Opus 5.5 condition A, PDF only) are reused,
             in this order: this run, the pilot run, the 4 Nov 2026 run, the
             10 Nov 2026 expansion run. Missing papers are generated with the
             pilot's own `generate` stage.
- judge:     the pilot's judge stage, unchanged. Real and human_human judgments
             of the five pilot papers are copied from the pilot when both item
             lists are identical (same pairing id, so the same blinding).
             Placebo pairings differ because the paper order differs.
- summarize: the pilot's summary, plus percentile bootstrap intervals over
             papers for every pooled rate and for the real-minus-human_human
             difference. The pilot's side effect of rewriting the human audit
             page data is switched off for this run.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pathlib
import random
import shutil
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import critique_overlap_pilot as pilot  # noqa: E402

DEFAULT_RUN_ID = "critique_overlap_scaled_2026-11-10"
PILOT_DIR = ROOT / "results" / pilot.DEFAULT_RUN_ID
EXPANSION_A = ROOT / "results" / "claude_opus_5_5_high_keyissues_expansion_2026-11-10" / "A"
EXCLUDED = ("Benabou_et_al._2023", "Peterman_et_al._2025")
BUDGET_USD = 12.0  # this run only; the earlier human_issue_reference extraction spent ~$1.11
N_BOOT = 2000
BOOT_SEED = 20261110


def doc_ref(file_name: str) -> str:
    return hashlib.sha256(pathlib.Path(file_name).name.encode()).hexdigest()[:12]


# --------------------------------------------------------------------------
# Model issue sources (patched into the pilot module)
# --------------------------------------------------------------------------

def model_issue_file(run_dir: pathlib.Path, paper: str) -> pathlib.Path | None:
    for cand in (run_dir / "A" / f"{paper}.json", PILOT_DIR / "A" / f"{paper}.json",
                 pilot.PRIOR_A_RUN / f"{paper}.json", EXPANSION_A / f"{paper}.json"):
        if cand.exists():
            try:
                if json.loads(cand.read_text())["parsed"]["key_issues"]:
                    return cand
            except (KeyError, TypeError, json.JSONDecodeError):
                continue
    return None


pilot.model_issue_file = model_issue_file


# --------------------------------------------------------------------------
# select
# --------------------------------------------------------------------------

def stage_select(args, run_dir: pathlib.Path) -> int:
    manifest = json.loads(pilot.MANIFEST.read_text())
    min_chars = manifest["rules"]["min_eval_body_chars"]
    # Every eligible paper with >= 2 substantive evaluations. Unlike the pilot, papers whose PDF date is
    # unknown (eligible in the manifest) are kept; summarize reports a sensitivity without them.
    pool = [p for p in manifest["papers"] if p["eligible"] and p["n_substantive_individual_evaluations"] >= 2
            and p["pdf_predates_first_evaluation"] is not False and p["paper"] not in EXCLUDED]
    pool.sort(key=lambda p: pilot.sha256_text(p["paper"]))
    out = run_dir / "selection.json"
    if out.exists() and not args.force:
        print(f"exists: {out.relative_to(ROOT)}")
        return 0
    sel = {
        "created_at": pilot.utc_now(),
        "manifest_sha256": hashlib.sha256(pilot.MANIFEST.read_bytes()).hexdigest(),
        "rule": "eligible in the manifest; >=2 substantive individual evaluations; PDF creation date on or before "
                "the first evaluation date or unknown; all papers, ordered by SHA-256 of the paper label; "
                f"{', '.join(EXCLUDED)} excluded",
        "papers_with_unknown_pdf_date": sorted(p["paper"] for p in pool if p["pdf_predates_first_evaluation"] is None),
        "n": len(pool), "pool_size": len(pool),
        "doc_ref": "sha256(evaluation export file name)[:12]; slugs and file names are not recorded",
        "papers": [{
            "paper": p["paper"], "research_title": p["research_title"], "pdf_sha256": p["pdf_sha256"],
            "pdf_pages": p["pdf_pages"], "pdf_creation_date": p["pdf_creation_date"],
            "first_evaluation_date": p["first_evaluation_date"], "in_gpt52_focal_run": p["in_gpt52_focal_run"],
            "evaluations": [{"label": e["label"], "doc_ref": doc_ref(e["file"]), "date": e["date"],
                             "body_chars": e["body_chars"], "sha256": e["sha256"]}
                            for e in pilot.evaluator_files(p, min_chars)],
        } for p in pool],
    }
    out.write_text(json.dumps(sel, indent=2, ensure_ascii=False))
    print(f"selected {len(pool)} papers; {sum(len(p['evaluations']) for p in sel['papers'])} evaluations")
    return 0


def source_file(sha256: str) -> pathlib.Path:
    manifest = json.loads(pilot.MANIFEST.read_text())
    for p in manifest["papers"]:
        for e in p["evaluations"]:
            if e["sha256"] == sha256:
                return ROOT / e["file"]
    raise KeyError(sha256)


# --------------------------------------------------------------------------
# extract
# --------------------------------------------------------------------------

def name_patterns(paper: str):
    """Reviewer-name patterns from the front matter and titles of this paper's evaluation documents."""
    import build_human_issue_reference as ref

    docs = ref.load_docs()
    return ref.redaction_patterns(ref.reviewer_names(ref.paper_docs(paper, docs)))


def stage_extract(args, run_dir: pathlib.Path) -> int:
    import build_human_issue_reference as ref

    sel = pilot.load_selection(run_dir)
    out_dir = run_dir / "human_issues"
    out_dir.mkdir(parents=True, exist_ok=True)
    client, failures, redactions = None, 0, 0
    for p in sel["papers"]:
        pats = name_patterns(p["paper"])
        for ev in p["evaluations"]:
            out = out_dir / f"{p['paper']}__{ev['label']}.json"
            if out.exists() and not args.force:
                continue
            pilot_file = PILOT_DIR / "human_issues" / out.name
            if pilot_file.exists():
                d = json.loads(pilot_file.read_text())
                if d["provenance"]["source_sha256"] == ev["sha256"]:
                    d["provenance"]["copied_from"] = str(pilot_file.relative_to(ROOT))
                    d["provenance"].pop("source_slug", None)
                    d["provenance"]["source_doc_ref"] = ev["doc_ref"]
                    out.write_text(json.dumps(d, indent=2, ensure_ascii=False))
                    print(f"copied pilot issues: {out.name}")
                    continue
            if pilot.over_budget(run_dir, args.budget):
                return 99
            src = source_file(ev["sha256"])
            if hashlib.sha256(src.read_bytes()).hexdigest() != ev["sha256"]:
                raise RuntimeError(f"{ev['doc_ref']} changed since selection")
            body = pilot.strip_front_matter(src.read_text(encoding="utf-8", errors="replace"))
            client = client or pilot.make_client()
            res = pilot.call_claude(client, model=pilot.EXTRACT_MODEL, effort=pilot.EXTRACT_EFFORT,
                                    system=pilot.EXTRACT_SYSTEM, user="Evaluation text:\n\n" + body,
                                    schema=pilot.EXTRACT_SCHEMA)
            pilot.log_spend(run_dir, p["paper"], f"extract_{ev['label']}", res)
            issues = []
            for i, it in enumerate((res.get("parsed") or {}).get("issues", []), start=1):
                verified = pilot.quote_in_source(it["quote"], body)
                text, quote = ref.redact(it["text"].strip(), pats), ref.redact(it["quote"].strip(), pats)
                redactions += (text != it["text"].strip()) + (quote != it["quote"].strip())
                issues.append({"id": f"{p['paper']}::{ev['label']}::H{i:02d}", "text": text, "quote": quote,
                               "importance": it["importance"], "quote_verified": verified})
            payload = {
                "provenance": {
                    "paper": p["paper"], "evaluator_label": ev["label"], "source_doc_ref": ev["doc_ref"],
                    "source_sha256": ev["sha256"], "source_body_chars": len(body),
                    "inputs_seen_by_extractor": "this evaluation's body text only (no paper, no model output)",
                    "model_requested": pilot.EXTRACT_MODEL, "effort": pilot.EXTRACT_EFFORT,
                    "system_prompt_sha256": pilot.sha256_text(pilot.EXTRACT_SYSTEM),
                    "schema_sha256": pilot.sha256_text(json.dumps(pilot.EXTRACT_SCHEMA, sort_keys=True)),
                    "post_check": "reviewer-name tokens replaced by [name] after the quote check",
                    "completed_at": pilot.utc_now(),
                    **{k: res.get(k) for k in ("model_returned", "stop_reason", "usage", "est_cost_usd",
                                               "elapsed_seconds", "response_id", "error")},
                },
                "issues": issues,
            }
            ok = not res.get("error") and bool(issues)
            (out if ok else out.with_suffix(".failed.json")).write_text(json.dumps(payload, indent=2, ensure_ascii=False))
            print(f"{'ok' if ok else 'FAILED'}: {p['paper']} {ev['label']}: {len(issues)} issues, "
                  f"{sum(i['quote_verified'] for i in issues)} quotes verified, ~${res.get('est_cost_usd', 0):.4f}")
            failures += 0 if ok else 1
    print(f"name tokens replaced in {redactions} fields")
    if not failures:
        expected = {f"{p['paper']}__{ev['label']}.json" for p in sel["papers"] for ev in p["evaluations"]}
        have = {f.name for f in out_dir.glob("*__E*.json") if not f.name.endswith(".failed.json")}
        if expected <= have and not (run_dir / "human_issues_frozen.json").exists():
            (run_dir / "human_issues_frozen.json").write_text(json.dumps({
                "frozen_at": pilot.utc_now(),
                "files": {n: hashlib.sha256((out_dir / n).read_bytes()).hexdigest() for n in sorted(expected)},
            }, indent=2))
            print("human issues frozen")
    return 1 if failures else 0


# --------------------------------------------------------------------------
# generate / judge
# --------------------------------------------------------------------------

def stage_generate(args, run_dir: pathlib.Path) -> int:
    sel = pilot.load_selection(run_dir)
    missing = [p["paper"] for p in sel["papers"] if model_issue_file(run_dir, p["paper"]) is None]
    print(f"model issues missing for {len(missing)}: {missing}")
    if args.only_missing_focal:
        focal = {p["paper"] for p in sel["papers"] if p["in_gpt52_focal_run"]}
        keep = [m for m in missing if m in focal]
        sub = {**sel, "papers": [p for p in sel["papers"] if p["paper"] in keep]}
        orig = pilot.load_selection
        pilot.load_selection = lambda rd: sub
        try:
            return pilot.stage_generate(args, run_dir)
        finally:
            pilot.load_selection = orig
    return pilot.stage_generate(args, run_dir)


def copy_pilot_judgments(run_dir: pathlib.Path) -> int:
    """Copy real and human_human judgments of the pilot papers when both item lists are identical."""
    sel = pilot.load_selection(run_dir)
    sets = pilot.load_issue_sets(run_dir, sel)
    mine = {pr["id"]: pr for pr in pilot.build_pairings(sel, sets) if pr["kind"] in ("real", "human_human")}
    n = 0
    for jdir in sorted((PILOT_DIR / "judge").glob("*")):
        if not jdir.is_dir():
            continue
        for f in sorted(jdir.glob("*.json")):
            if f.name.endswith(".failed.json"):
                continue
            d = json.loads(f.read_text())
            pid = d.get("pairing", {}).get("id")
            if pid not in mine:
                continue
            pr = mine[pid]
            if d["side1_ids"] != [i["id"] for i in pr["side1"]] or d["side2_ids"] != [i["id"] for i in pr["side2"]]:
                print(f"not copied (item lists differ): {jdir.name}/{f.name}")
                continue
            dest = run_dir / "judge" / jdir.name / f.name
            if dest.exists():
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            d["judge"]["copied_from"] = str(f.relative_to(ROOT))
            dest.write_text(json.dumps(d, indent=2, ensure_ascii=False))
            n += 1
    print(f"copied {n} pilot judgments")
    return n


def stage_judge(args, run_dir: pathlib.Path) -> int:
    copy_pilot_judgments(run_dir)
    return pilot.stage_judge(args, run_dir)


# --------------------------------------------------------------------------
# summarize + bootstrap
# --------------------------------------------------------------------------

def judgment_rows(run_dir: pathlib.Path) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
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
            matches, _ = pilot.valid_matches(d)
            row = {"kind": d["pairing"]["kind"], "paper": d["pairing"]["paper"],
                   "n1": len(d["side1_ids"]), "n2": len(d["side2_ids"])}
            for rule in pilot.RULES:
                row[f"c1[{rule}]"] = len(pilot.covered_ids(matches, "side1", rule))
                row[f"c2[{rule}]"] = len(pilot.covered_ids(matches, "side2", rule))
            rows.append(row)
        out[jdir.name] = rows
    return out


def pooled(rows: list[dict[str, Any]], rule: str, which: str) -> float | None:
    if which == "both":
        num = sum(r[f"c1[{rule}]"] + r[f"c2[{rule}]"] for r in rows)
        den = sum(r["n1"] + r["n2"] for r in rows)
    else:
        num = sum(r[f"c{which}[{rule}]"] for r in rows)
        den = sum(r[f"n{which}"] for r in rows)
    return 100.0 * num / den if den else None


MEASURES = {  # name -> (kind, which side)
    "real_human_covered": ("real", "1"),
    "real_model_overlapping": ("real", "2"),
    "placebo_human_matched": ("placebo", "1"),
    "placebo_model_matched": ("placebo", "2"),
    "human_human_both_directions": ("human_human", "both"),
}


def bootstrap(rows: list[dict[str, Any]], n_boot: int = N_BOOT, seed: int = BOOT_SEED) -> dict[str, Any]:
    """Percentile intervals, resampling papers with replacement (each paper keeps all its pairings)."""
    by_paper: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        by_paper.setdefault(r["paper"], []).append(r)
    papers = sorted(by_paper)
    rng = random.Random(seed)
    draws = [[rng.choice(papers) for _ in papers] for _ in range(n_boot)]
    res: dict[str, Any] = {"n_papers": len(papers), "n_boot": n_boot, "seed": seed, "interval": "95% percentile"}

    def interval(vals: list[float]) -> list[float] | None:
        vals = sorted(v for v in vals if v is not None)
        if not vals:
            return None
        lo, hi = vals[int(0.025 * (len(vals) - 1))], vals[int(round(0.975 * (len(vals) - 1)))]
        return [round(lo, 1), round(hi, 1)]

    for rule in pilot.RULES:
        r_out = {}
        for name, (kind, which) in MEASURES.items():
            point = pooled([r for r in rows if r["kind"] == kind], rule, which)
            boots = []
            for d in draws:
                sub = [r for p in d for r in by_paper[p] if r["kind"] == kind]
                boots.append(pooled(sub, rule, which))
            r_out[name] = {"point": round(point, 1) if point is not None else None, "ci95": interval(boots),
                           "n_papers": len({r["paper"] for r in rows if r["kind"] == kind})}
        # Paired difference on papers that have both kinds.
        both = [p for p in papers if {"real", "human_human"} <= {r["kind"] for r in by_paper[p]}]

        def diff(ps: list[str]) -> float | None:
            a = pooled([r for p in ps for r in by_paper[p] if r["kind"] == "real"], rule, "1")
            b = pooled([r for p in ps for r in by_paper[p] if r["kind"] == "human_human"], rule, "both")
            return None if a is None or b is None else a - b

        if both:
            drng = random.Random(seed + 1)
            dboots = [diff([drng.choice(both) for _ in both]) for _ in range(n_boot)]
            pt = diff(both)
            r_out["real_minus_human_human"] = {"point": round(pt, 1) if pt is not None else None,
                                               "ci95": interval(dboots), "n_papers": len(both)}
        res[rule] = r_out
    return res


LABELS = {
    "real_human_covered": "Human issues the model also raised",
    "real_model_overlapping": "Model issues a human also raised",
    "placebo_human_matched": "Placebo: human issues matched by another paper's model issues",
    "placebo_model_matched": "Placebo: model issues matched",
    "human_human_both_directions": "One evaluator's issues the other also raised",
    "real_minus_human_human": "Difference: model coverage minus human-human (percentage points)",
}


def bootstrap_markdown(boot: dict[str, Any]) -> str:
    out = ["## Bootstrap intervals over papers", "",
           f"Pooled rates with {boot['note']}", ""]
    out += boot_tables(boot["judges"])
    sens = boot.get("sensitivity_known_pdf_date_only")
    if sens and sens["dropped"]:
        out += [f"### Sensitivity: without papers whose PDF date is unknown ({', '.join(sens['dropped'])})", ""]
        out += boot_tables(sens["judges"], level="####")
    return "\n".join(out)


def boot_tables(judges: dict[str, Any], level: str = "###") -> list[str]:
    out = []
    for name, b in judges.items():
        out += [f"{level} {pilot.JUDGE_LABEL.get(name, name)}", "",
                "| Measure | Papers | " + " | ".join(pilot.RULE_LABEL[r] for r in pilot.RULES) + " |",
                "|---|---:|" + "---|" * len(pilot.RULES)]
        for m in LABELS:
            if m not in b[pilot.RULES[0]]:
                continue
            cells = []
            for rule in pilot.RULES:
                v = b[rule][m]
                cells.append(f"{v['point']} [{v['ci95'][0]}, {v['ci95'][1]}]" if v["ci95"] else "n/a")
            out.append(f"| {LABELS[m]} | {b[pilot.RULES[0]][m]['n_papers']} | " + " | ".join(cells) + " |")
        out.append("")
    return out


def issue_table(summary: dict[str, Any]) -> list[str]:
    lines = ["| Paper | E1 issues | E2 issues | E3 issues | Model issues | Model issues from |",
             "|---|---:|---:|---:|---:|---|"]
    for paper in summary["papers"]:
        ev = {e["evaluator"]: e["n_issues"] for e in summary["extraction"]["per_evaluation"] if e["paper"] == paper}
        mi = summary["model_issues"].get(paper, {})
        src = (mi.get("source") or "none").split("/")[1] if mi.get("source") else "none"
        lines.append(f"| {paper} | {ev.get('E1', '')} | {ev.get('E2', '')} | {ev.get('E3', '')} | {mi.get('n', '')} | {src} |")
    return lines


def stage_summarize(args, run_dir: pathlib.Path) -> int:
    sys.modules["match_audit"] = None  # the pilot's audit-page export belongs to the pilot run; skip it here
    rc = pilot.stage_summarize(args, run_dir)
    summary = json.loads((run_dir / "summary.json").read_text())
    rows = judgment_rows(run_dir)
    unknown = set(pilot.load_selection(run_dir).get("papers_with_unknown_pdf_date", []))
    boot = {"judges": {name: bootstrap(r) for name, r in rows.items()},
            "sensitivity_known_pdf_date_only": {
                "dropped": sorted(unknown),
                "judges": {name: bootstrap([x for x in r if x["paper"] not in unknown]) for name, r in rows.items()}},
            "note": f"95% percentile bootstrap intervals in brackets: {N_BOOT} resamples of papers with "
                    "replacement (seed {BOOT_SEED}); each paper keeps all its pairings. The difference row "
                    "pairs papers that have both a real and a human-human pairing. Intervals reflect "
                    "variation across papers only, not judge or extraction noise.".replace("{BOOT_SEED}", str(BOOT_SEED))}
    summary["bootstrap"] = boot
    (run_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
    md = pilot.summary_markdown(summary).splitlines()
    md[0] = f"# Critique-overlap scaled run: computed summary ({summary['run_id']})"
    md[2] = ("Generated by `scripts/critique_overlap_scale.py summarize` (the pilot pipeline applied to all "
             f"papers meeting its rule). Exploratory: {len(summary['papers'])} papers, one model run per paper, "
             "AI judges, no human validation yet.")
    start = md.index("## Issue counts") + 2
    end = next(i for i in range(start, len(md)) if not md[i].startswith("|"))
    md = md[:start] + issue_table(summary) + md[end:]
    cost = md.index("## Cost (estimated from token usage)")
    md = md[:cost] + bootstrap_markdown(boot).splitlines() + [""] + md[cost:]
    text = "\n".join(md).replace(
        "Model issues reused from the 2026-11-04 run are not re-billed.",
        "Model issues reused from earlier runs (pilot, 2026-11-04, 2026-11-10 expansion) are not re-billed here.")
    (run_dir / "summary.md").write_text(text + "\n")
    print(bootstrap_markdown(boot))
    return rc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["select", "extract", "generate", "judge", "summarize"])
    ap.add_argument("--run-id", default=DEFAULT_RUN_ID)
    ap.add_argument("--budget", type=float, default=BUDGET_USD)
    ap.add_argument("--judge", choices=["sonnet", "codex"], default="sonnet")
    ap.add_argument("--codex-model", default=pilot.CODEX_JUDGE_MODEL)
    ap.add_argument("--kind", action="append", choices=["real", "placebo", "human_human"])
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--only-missing-focal", action="store_true",
                    help="generate: only focal-set papers that no earlier run covers")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    run_dir = ROOT / "results" / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    return {"select": stage_select, "extract": stage_extract, "generate": stage_generate,
            "judge": stage_judge, "summarize": stage_summarize}[args.stage](args, run_dir)


if __name__ == "__main__":
    raise SystemExit(main())
