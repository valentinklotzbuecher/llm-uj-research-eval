#!/usr/bin/env python3
"""
isitcredible `review` vs one-shot critiques on Williams et al. (2024, Nature),
judged against the human Unjournal evaluations.

One paper, exploratory. Question: does the multi-stage isitcredible review find
the issues the two Unjournal evaluators raised better than a one-shot model, and
what does it find that nobody else did?

Inputs
- isitcredible: the only output shared, `results/reviewer12_joe_shared/SYNTHESIS.md`
  (Joe Francis, email of 10 Sep 2026). No stage reports, scripts or logs.
  The run had the Nature peer review file (Joe's email); access to the Unjournal
  evaluations is unconfirmed.
- Human reference: per-evaluator issues frozen by the scaled critique-overlap run
  (`results/critique_overlap_scaled_2026-11-10/human_issues/Williams_et_al._2024__E{1,2}.json`),
  and, as a sensitivity check, the curated list in `tools/issue_annotation_ui/data.json`.
- One-shot baselines: Claude Opus 5.5 condition A (4 Nov run, the file the scaled run
  used) and the GPT-5.2 Pro focal key issues.
- Leakage reference: the Nature peer review file (referee reports only; author
  rebuttals dropped), split into issues with the same extractor as the human issues.

Pipeline (imports existing code, changes none of it)
- `freeze`: Claude Haiku 5.5 splits the SYNTHESIS and each Nature referee's reports
  into issues (the scaled run's extraction prompt); quotes are checked verbatim;
  isitcredible's own severity comes from the section each quote sits in. Frozen
  before any judging.
- `normalize`: Haiku rewrites every list into neutral statements (the v2 judge's
  rewrite prompt). The curated human list and the GPT-5.2 Pro list reuse the v2
  run's rewrites, so those inputs are identical to the v2 pilot.
- `judge --judge claude|codex`: the v2 locus-and-mechanism judge (Claude Opus 5.5,
  or GPT-5.6 Terra through `codex exec`), blinded lists, two replicates for the
  main comparisons, one cross-paper placebo per tool.
- `summarize`: coverage and overlap at strict/standard/loose levels, computed here.

Privacy: the repository is public and Joe has not released his findings, so the
isitcredible item texts, normalized statements and judge reasons stay in
`<run>/private/` (ignored). Committed outputs hold ids, categories and counts.
Evaluators appear only as E1/E2.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pathlib
import re
import shutil
import sys
import urllib.request
from datetime import datetime, timezone
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import critique_overlap_pilot as pilot  # noqa: E402
import run_issue_match_judge as v2  # noqa: E402

RUN_ID = "isitcredible_vs_oneshot_williams_2026-11-10"
RUN = ROOT / "results" / RUN_ID
PRIV = RUN / "private"
PAPER = "Williams_et_al._2024"
PLACEBO_PAPER = "Chuard_et_al._2022"  # the scaled run's placebo partner for Williams
SCALED = ROOT / "results" / "critique_overlap_scaled_2026-11-10"
V2_NORM = ROOT / "results" / "issue_match_judge_v2_opus55_2026-11-10" / "normalized"
SYNTHESIS = ROOT / "results" / "reviewer12_joe_shared" / "SYNTHESIS.md"
OPUS_A = ROOT / "results" / "claude_opus_5_5_high_misses_2026-11-04" / "A" / f"{PAPER}.json"
GPT52 = ROOT / "results" / "gpt52_pro_focal_jan2026" / "json" / f"{PAPER}.response.json"
PRF_URL = ("https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-024-08106-4/"
           "MediaObjects/41586_2024_8106_MOESM7_ESM.pdf")
BUDGET_USD = 9.0
REPLICATES = 2

TOOLS = ("isit", "opus", "gpt")
TOOL_LABEL = {"isit": "isitcredible review (SYNTHESIS)", "opus": "Claude Opus 5.5, one-shot (condition A)",
              "gpt": "GPT-5.2 Pro, one-shot (focal run)"}
JUDGE_LABEL = {"claude": f"Claude judge ({v2.MODEL}, high)", "codex": f"GPT judge ({v2.CODEX_MODEL}, high, via Codex)"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: pathlib.Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False))


# --------------------------------------------------------------------------
# Spend
# --------------------------------------------------------------------------

SPEND = RUN / "spend_ledger.csv"
SPEND_FIELDS = ["timestamp", "stage", "item", "model", "status", "input_tokens", "output_tokens",
                "est_cost_usd", "elapsed_seconds"]


def record_spend(row: dict[str, Any]) -> None:
    new = not SPEND.exists()
    SPEND.parent.mkdir(parents=True, exist_ok=True)
    with SPEND.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SPEND_FIELDS)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in SPEND_FIELDS})


def spent() -> float:
    if not SPEND.exists():
        return 0.0
    with SPEND.open() as f:
        return sum(float(r["est_cost_usd"] or 0) for r in csv.DictReader(f))


# --------------------------------------------------------------------------
# Sources
# --------------------------------------------------------------------------

def synthesis_sections(text: str) -> list[tuple[int, str]]:
    """(start offset, isitcredible severity) for each part of the SYNTHESIS."""
    marks = [("## The three HIGH findings", "HIGH"), ("## Supporting findings", "MEDIUM"),
             ("## What survives", "survives"), ("## Confidence and limits", "limits"), ("### Packet", "index")]
    out = [(0, "verdict")]
    for head, sev in marks:
        i = text.find(head)
        if i >= 0:
            out.append((i, sev))
    return sorted(out)


def severity_of(quote: str, text: str) -> str:
    """Section of the first verbatim (loose) occurrence of the quote."""
    q = pilot._loose(quote).strip(" .…")
    secs = synthesis_sections(text)
    for (start, s), nxt in zip(secs, secs[1:] + [(len(text), "")]):
        if q and q in pilot._loose(text[start:nxt[0]]):
            return s
    return "unlocated"


def prf_referee_text() -> tuple[dict[str, str], dict[str, Any]]:
    """Referee reports from the Nature peer review file, author rebuttals removed."""
    src = PRIV / "sources" / "nature_peer_review_file.pdf"
    if not src.exists():
        src.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(PRF_URL, headers={"User-Agent": "Mozilla/5.0"})
        src.write_bytes(urllib.request.urlopen(req, timeout=120).read())
    txt = src.with_suffix(".txt")
    if not txt.exists():
        import subprocess

        subprocess.run(["pdftotext", "-layout", str(src), str(txt)], check=True)
    lines = txt.read_text(encoding="utf-8", errors="replace").splitlines()
    keep, cur, by_ref = False, None, {}
    for ln in lines:
        s = ln.strip()
        if s.startswith("Reviewer Reports on"):
            keep, cur = True, None
            continue
        if s.startswith("Author Rebuttals"):
            keep, cur = False, None
            continue
        m = re.match(r"Referee #(\d) \(Remarks to the Author\):", s)
        if keep and m:
            cur = f"R{m.group(1)}"
            by_ref.setdefault(cur, [])
            continue
        if keep and cur:
            by_ref[cur].append(ln)
    texts = {k: "\n".join(v).strip() for k, v in by_ref.items()}
    meta = {"url": PRF_URL, "pdf_sha256": sha(src), "referees": {k: len(v.split()) for k, v in texts.items()},
            "scope": "referee reports on the initial version and both revisions; author rebuttals dropped"}
    return texts, meta


def human_issues(paper: str) -> list[dict[str, Any]]:
    out = []
    for f in sorted((SCALED / "human_issues").glob(f"{paper}__E*.json")):
        out += json.loads(f.read_text())["issues"]
    return out


def gpt52_key_issues() -> list[str]:
    d = json.loads(GPT52.read_text())
    txt = "".join(c["text"] for o in d["output"] for c in (o.get("content") or []) if c.get("type") == "output_text")
    return [t.strip() for t in json.loads(txt)["key_issues"]]


def curated(paper: str) -> dict[str, Any]:
    data = json.loads(v2.SOURCE.read_text())
    return next(p for p in data["papers"] if p["paper_id"] == paper)


# --------------------------------------------------------------------------
# Stage: freeze
# --------------------------------------------------------------------------

def extract(client, text: str, label: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    res = pilot.call_claude(client, model=pilot.EXTRACT_MODEL, effort=pilot.EXTRACT_EFFORT,
                            system=pilot.EXTRACT_SYSTEM, user="Evaluation text:\n\n" + text,
                            schema=pilot.EXTRACT_SCHEMA)
    u = res.get("usage") or {}
    record_spend({"timestamp": utc_now(), "stage": "extract", "item": label, "model": pilot.EXTRACT_MODEL,
                  "status": "failed" if res.get("error") else "ok", "input_tokens": u.get("input_tokens"),
                  "output_tokens": u.get("output_tokens"), "est_cost_usd": res.get("est_cost_usd", 0),
                  "elapsed_seconds": res.get("elapsed_seconds")})
    if res.get("error"):
        raise RuntimeError(f"extraction failed for {label}: {res['error']}")
    meta = {k: res.get(k) for k in ("model_returned", "stop_reason", "usage", "est_cost_usd", "response_id")}
    return res["parsed"]["issues"], meta


def stage_freeze(args) -> int:
    frozen = RUN / "freeze.json"
    if frozen.exists() and not args.force:
        print("already frozen; use --force to redo (this invalidates later stages)")
        return 1
    client = pilot.make_client()
    syn = SYNTHESIS.read_text()
    items, meta = extract(client, syn, "isitcredible_synthesis")
    isit = []
    for i, it in enumerate(items, 1):
        isit.append({"id": f"ISIT{i:02d}", "text": it["text"].strip(), "quote": it["quote"].strip(),
                     "importance_extractor": it["importance"], "severity_isitcredible": severity_of(it["quote"], syn),
                     "quote_verified": pilot.quote_in_source(it["quote"], syn)})
    write_json(PRIV / "isitcredible_issues.json", {"source": str(SYNTHESIS.relative_to(ROOT)),
                                                   "source_sha256": sha(SYNTHESIS), "extractor": meta, "issues": isit})
    texts, prf_meta = prf_referee_text()
    nature = []
    nat_meta = {}
    for ref, body in sorted(texts.items()):
        its, m = extract(client, body, f"nature_{ref}")
        nat_meta[ref] = m
        for i, it in enumerate(its, 1):
            nature.append({"id": f"NATURE::{ref}::N{i:02d}", "text": it["text"].strip(), "quote": it["quote"].strip(),
                           "importance": it["importance"], "quote_verified": pilot.quote_in_source(it["quote"], body)})
    write_json(PRIV / "nature_referee_issues.json", {"source": prf_meta, "extractor": nat_meta, "issues": nature})
    rec = {
        "frozen_at": utc_now(),
        "extractor": {"model": pilot.EXTRACT_MODEL, "effort": pilot.EXTRACT_EFFORT,
                      "system_prompt_sha256": pilot.sha256_text(pilot.EXTRACT_SYSTEM),
                      "note": "same prompt and model as the scaled run's human-issue extraction"},
        "isitcredible": {"source": str(SYNTHESIS.relative_to(ROOT)), "source_sha256": sha(SYNTHESIS),
                         "n_issues": len(isit), "n_quotes_verified": sum(x["quote_verified"] for x in isit),
                         "severity": {x["id"]: x["severity_isitcredible"] for x in isit},
                         "file_sha256": sha(PRIV / "isitcredible_issues.json")},
        "nature_referees": {**prf_meta, "n_issues": len(nature),
                            "n_by_referee": {r: sum(1 for x in nature if f"::{r}::" in x["id"]) for r in texts},
                            "n_quotes_verified": sum(x["quote_verified"] for x in nature),
                            "file_sha256": sha(PRIV / "nature_referee_issues.json")},
        "human_reference": {f.name: sha(f) for f in sorted((SCALED / "human_issues").glob(f"{PAPER}__E*.json"))},
        "placebo_human_reference": {f.name: sha(f) for f in sorted((SCALED / "human_issues").glob(f"{PLACEBO_PAPER}__E*.json"))},
        "opus_a": {"file": str(OPUS_A.relative_to(ROOT)), "sha256": sha(OPUS_A)},
        "gpt52_pro": {"file": str(GPT52.relative_to(ROOT)), "sha256": sha(GPT52)},
        "curated_source": {"file": str(v2.SOURCE.relative_to(ROOT)), "sha256": sha(v2.SOURCE)},
    }
    write_json(frozen, rec)
    print(f"frozen: {len(isit)} isitcredible issues ({rec['isitcredible']['n_quotes_verified']} quotes verified), "
          f"{len(nature)} Nature referee issues; spend ${spent():.3f}")
    return 0


# --------------------------------------------------------------------------
# Stage: normalize
# --------------------------------------------------------------------------

def raw_lists() -> dict[str, dict[str, str]]:
    """Every list, keyed by stable original ids."""
    isit = json.loads((PRIV / "isitcredible_issues.json").read_text())["issues"]
    nature = json.loads((PRIV / "nature_referee_issues.json").read_text())["issues"]
    opus = json.loads(OPUS_A.read_text())["parsed"]["key_issues"]
    gpt = gpt52_key_issues()
    cur = curated(PAPER)
    if [x.strip() for x in cur["llm_key_issues"]] != gpt:
        raise RuntimeError("curated file's model list is not the GPT-5.2 Pro list")
    return {
        "per_eval": {i["id"]: i["text"] for i in human_issues(PAPER)},
        "placebo_per_eval": {i["id"]: i["text"] for i in human_issues(PLACEBO_PAPER)},
        "curated": {f"CURATED::H{k}": v for k, v in
                    enumerate([v2.anonymize_human_issue(str(h.get("text", "")).strip())
                               for h in cur["human_issue_suggestions"]], 1) if v},
        "isit": {i["id"]: i["text"] for i in isit},
        "nature": {i["id"]: i["text"] for i in nature},
        "opus": {f"OPUS_A::M{k:02d}": t.strip() for k, t in enumerate(opus, 1)},
        "gpt": {f"GPT52P::L{k:02d}": t for k, t in enumerate(gpt, 1)},
    }


REUSE = {"curated": ("human", "CURATED::H"), "gpt": ("model", "GPT52P::L")}


def stage_normalize(args) -> int:
    if not (RUN / "freeze.json").exists():
        print("run freeze first")
        return 1
    lists = raw_lists()
    client = None
    out: dict[str, dict[str, str]] = {}
    report = {}
    for name, items in lists.items():
        path = PRIV / "normalized" / f"{name}.json"
        if name in REUSE and not path.exists():
            side, prefix = REUSE[name]
            src = json.loads((V2_NORM / f"{PAPER}__{side}.json").read_text())
            mapped = {}
            for k, v in src["items"].items():
                n = int(k[1:])
                new_id = f"{prefix}{n:02d}" if name == "gpt" else f"{prefix}{n}"
                if " ".join(v["original"].split()) != " ".join(items[new_id].split()):
                    raise RuntimeError(f"v2 rewrite of {name} {k} does not match its source text")
                mapped[new_id] = v
            write_json(path, {**{k: src[k] for k in src if k != "items"}, "reused_from": str(V2_NORM.relative_to(ROOT)),
                              "items": mapped})
        if not path.exists():
            if spent() >= BUDGET_USD:
                print("budget reached")
                return 99
            client = client or pilot.make_client()
            neutral = {f"I{j}": t for j, t in enumerate(items.values(), 1)}
            back = dict(zip(neutral, items))
            rec = v2.normalize_side(client, neutral, PRIV / "normalized" / f"{name}.tmp.json")
            (PRIV / "normalized" / f"{name}.tmp.json").unlink()
            rec["items"] = {back[k]: v for k, v in rec["items"].items()}
            write_json(path, rec)
            u = rec.get("usage") or {}
            record_spend({"timestamp": utc_now(), "stage": "normalize", "item": name, "model": v2.NORMALIZER_MODEL,
                          "status": "ok", "input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens"),
                          "est_cost_usd": rec.get("est_cost_usd", 0), "elapsed_seconds": rec.get("elapsed_seconds")})
        rec = json.loads(path.read_text())
        kept = {k: v2.scrub(v["statement"]) for k, v in rec["items"].items()
                if not v["no_substantive_concern"] and v["statement"]}
        out[name] = kept
        report[name] = {"n_items": len(items), "n_kept": len(kept), "prompt_sha256": rec.get("prompt_sha256"),
                        "reused": "reused_from" in rec}
    leaks = v2.leak_scan({n: {"x": v} for n, v in out.items()})
    write_json(PRIV / "blinding_leak_scan.json", leaks)
    write_json(RUN / "normalize_report.json", {"lists": report, "leak_scan_hits": len(leaks),
                                               "leak_scan_hits_by_list": {n: sum(1 for h in leaks if h["paper"] == n) for n in out}})
    write_json(PRIV / "normalized_lists.json", out)
    print(json.dumps(report, indent=1), f"\nleak-scan hits: {len(leaks)}; spend ${spent():.3f}")
    return 0


# --------------------------------------------------------------------------
# Stage: judge
# --------------------------------------------------------------------------

def build_cases() -> list[dict[str, Any]]:
    """human side = reference list (ids relabelled H*), model side = compared list (L*)."""
    cases = []
    for rep in range(1, REPLICATES + 1):
        for tool in TOOLS:
            for ref in ("per_eval", "curated"):
                cases.append({"case_id": f"real__{tool}__{ref}__r{rep}", "kind": "real", "ref": ref, "tool": tool, "rep": rep})
        cases.append({"case_id": f"nature_vs_human__per_eval__r{rep}", "kind": "nature_vs_human",
                      "ref": "per_eval", "tool": "nature", "rep": rep})
        cases.append({"case_id": f"tool_vs_nature__isit__r{rep}", "kind": "tool_vs_nature",
                      "ref": "nature", "tool": "isit", "rep": rep})
        cases.append({"case_id": f"human_human__E1_vs_E2__r{rep}", "kind": "human_human",
                      "ref": "E1", "tool": "E2", "rep": rep})
    cases.append({"case_id": "nature_vs_human__curated__r1", "kind": "nature_vs_human", "ref": "curated", "tool": "nature", "rep": 1})
    for tool in ("opus", "gpt"):
        cases.append({"case_id": f"tool_vs_nature__{tool}__r1", "kind": "tool_vs_nature", "ref": "nature", "tool": tool, "rep": 1})
    for tool in TOOLS:
        cases.append({"case_id": f"placebo__{tool}__vs__{PLACEBO_PAPER}__r1", "kind": "placebo",
                      "ref": "placebo_per_eval", "tool": tool, "rep": 1})
    return cases


def side_items(lists: dict[str, dict[str, str]], name: str) -> dict[str, str]:
    if name in ("E1", "E2"):
        return {k: v for k, v in lists["per_eval"].items() if f"::{name}::" in k}
    return lists[name]


def stage_judge(args) -> int:
    lists = json.loads((PRIV / "normalized_lists.json").read_text())
    out_dir = RUN / "judgments" / args.judge
    priv_dir = PRIV / "calls" / args.judge
    out_dir.mkdir(parents=True, exist_ok=True)
    priv_dir.mkdir(parents=True, exist_ok=True)
    client = None
    failures = 0
    for case in build_cases():
        if args.case and case["case_id"] not in args.case:
            continue
        out = out_dir / f"{case['case_id']}.json"
        if out.exists() and not args.force:
            continue
        ref, cmp_ = side_items(lists, case["ref"]), side_items(lists, case["tool"])
        hmap = {f"H{j}": k for j, k in enumerate(ref, 1)}
        lmap = {f"L{j}": k for j, k in enumerate(cmp_, 1)}
        pseudo = {"REF": {"human": {h: ref[k] for h, k in hmap.items()}, "model": {}},
                  "CMP": {"human": {}, "model": {l: cmp_[k] for l, k in lmap.items()}}}
        b = v2.blind({"case_id": f"isitcred_williams::{case['case_id']}", "human_paper": "REF", "model_paper": "CMP"}, pseudo)
        if args.dry_run:
            print(f"{case['case_id']}: {b['n_human']} x {b['n_model']}, {len(b['user_text'])} chars")
            continue
        if args.judge == "claude":
            if spent() >= BUDGET_USD:
                print("budget reached; stopping")
                return 99
            client = client or pilot.make_client()
            r = v2.call_judge(client, b["user_text"], priv_dir / f"{case['case_id']}.raw_response.json")
            u = r.get("usage") or {}
            cost = v2.estimate_cost(u) if u else 0.0
        else:
            r = v2.call_judge_codex(b["user_text"], case["case_id"], priv_dir)
            u = r.get("usage") or {}
            cost = 0.0  # ChatGPT subscription
        status = "error" if r.get("error") else "ok"
        parsed = None
        if status == "ok":
            try:
                parsed = json.loads(r["text"])
            except json.JSONDecodeError:
                status = "parse_error"
        record_spend({"timestamp": utc_now(), "stage": f"judge_{args.judge}", "item": case["case_id"],
                      "model": r.get("model") or (v2.MODEL if args.judge == "claude" else v2.CODEX_MODEL),
                      "status": status, "input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens"),
                      "est_cost_usd": cost, "elapsed_seconds": r.get("elapsed_seconds")})
        if parsed is None:
            print(f"FAILED {case['case_id']}: {status} {r.get('error', '')}")
            failures += 1
            continue
        pairs, errors = v2.unblind_pairs(parsed, b["key"])
        m = v2.metrics(pairs, b["n_human"], b["n_model"])
        idpairs = [{"ref_id": hmap[p["human"]], "cmp_id": lmap[p["model"]], "category": p["category"],
                    "broader": p["broader"], "confidence": p["confidence"]} for p in pairs]
        write_json(priv_dir / f"{case['case_id']}.json", {"case": case, "parsed": parsed, "pairs": idpairs,
                                                         "reasons": [p["reason"] for p in pairs]})
        write_json(out, {
            "case": case,
            "judge": {"name": args.judge, "model": r.get("model"), "effort": v2.EFFORT,
                      "system_prompt_sha256": hashlib.sha256(v2.SYSTEM_PROMPT.encode()).hexdigest(),
                      "schema_sha256": hashlib.sha256(json.dumps(v2.JUDGE_SCHEMA, sort_keys=True).encode()).hexdigest(),
                      "user_text_sha256": hashlib.sha256(b["user_text"].encode()).hexdigest(),
                      "blinding": {"seed": b["seed"], "ref_is_list_a": b["human_is_a"]},
                      "completed_at": utc_now(), "est_cost_usd": cost, "usage": u},
            "same_study": parsed.get("same_study"),
            "ref_ids": list(hmap.values()), "cmp_ids": list(lmap.values()),
            "pairs": idpairs, "id_errors": errors, "metrics": m,
        })
        print(f"ok {case['case_id']}: standard coverage {m['standard']['coverage']}% overlap {m['standard']['overlap']}% "
              f"(${cost:.3f}; total ${spent():.2f})", flush=True)
    return 1 if failures else 0


# --------------------------------------------------------------------------
# Stage: summarize
# --------------------------------------------------------------------------

def load_judgments(judge: str) -> list[dict[str, Any]]:
    return [json.loads(f.read_text()) for f in sorted((RUN / "judgments" / judge).glob("*.json"))]


def covered(j: dict[str, Any], level: str, side: str = "ref") -> set[str]:
    cats = v2.LEVELS[level]
    return {p[f"{side}_id"] for p in j["pairs"] if p["category"] in cats}


def pct(n: int, d: int) -> float | None:
    return round(100 * n / d, 1) if d else None


def summarize_judge(judge: str) -> dict[str, Any]:
    js = load_judgments(judge)
    by = {j["case"]["case_id"]: j for j in js}
    res: dict[str, Any] = {"n_calls": len(js), "levels": {}}
    nature_cov = {}
    for level in v2.LEVELS:
        L: dict[str, Any] = {}
        # Real comparisons: per tool, per reference
        for ref in ("per_eval", "curated"):
            for tool in TOOLS:
                reps = [by.get(f"real__{tool}__{ref}__r{r}") for r in range(1, REPLICATES + 1)]
                reps = [x for x in reps if x]
                if not reps:
                    continue
                n_ref, n_cmp = len(reps[0]["ref_ids"]), len(reps[0]["cmp_ids"])
                cov = [len(covered(x, level)) for x in reps]
                ov = [len(covered(x, level, "cmp")) for x in reps]
                both = set.intersection(*(covered(x, level) for x in reps))
                anyr = set.union(*(covered(x, level) for x in reps))
                L[f"{tool}__{ref}"] = {
                    "n_ref": n_ref, "n_cmp": n_cmp,
                    "coverage_by_rep": [pct(c, n_ref) for c in cov],
                    "coverage_mean": pct(sum(cov), n_ref * len(reps)),
                    "overlap_by_rep": [pct(c, n_cmp) for c in ov],
                    "overlap_mean": pct(sum(ov), n_cmp * len(reps)),
                    "covered_all_reps": sorted(both), "covered_any_rep": sorted(anyr),
                }
        # Human-to-human (E1 issues covered by E2)
        hh = [by.get(f"human_human__E1_vs_E2__r{r}") for r in range(1, REPLICATES + 1)]
        hh = [x for x in hh if x]
        if hh:
            n1, n2 = len(hh[0]["ref_ids"]), len(hh[0]["cmp_ids"])
            L["human_human"] = {"n_E1": n1, "n_E2": n2,
                                "E1_covered_by_E2_mean": pct(sum(len(covered(x, level)) for x in hh), n1 * len(hh)),
                                "E2_covered_by_E1_mean": pct(sum(len(covered(x, level, "cmp")) for x in hh), n2 * len(hh))}
        # Placebo
        for tool in TOOLS:
            p = by.get(f"placebo__{tool}__vs__{PLACEBO_PAPER}__r1")
            if p:
                L[f"placebo__{tool}"] = {"n_ref": len(p["ref_ids"]), "n_cmp": len(p["cmp_ids"]),
                                         "coverage": pct(len(covered(p, level)), len(p["ref_ids"])),
                                         "overlap": pct(len(covered(p, level, "cmp")), len(p["cmp_ids"])),
                                         "same_study": p["same_study"]}
        # Nature referees: which human issues they raised; which tool items repeat them
        nv = [by.get(f"nature_vs_human__per_eval__r{r}") for r in range(1, REPLICATES + 1)]
        nv = [x for x in nv if x]
        if nv:
            raised = set.union(*(covered(x, level) for x in nv))
            nature_cov[level] = raised
            L["nature_covers_per_eval"] = {"n_ref": len(nv[0]["ref_ids"]), "covered_any_rep": sorted(raised),
                                           "coverage_mean": pct(sum(len(covered(x, level)) for x in nv),
                                                                len(nv[0]["ref_ids"]) * len(nv))}
        nc = by.get("nature_vs_human__curated__r1")
        if nc:
            L["nature_covers_curated"] = {"n_ref": len(nc["ref_ids"]), "coverage": pct(len(covered(nc, level)), len(nc["ref_ids"])),
                                          "covered": sorted(covered(nc, level))}
        for tool in TOOLS:
            tv = [by.get(f"tool_vs_nature__{tool}__r{r}") for r in range(1, REPLICATES + 1)]
            tv = [x for x in tv if x]
            if tv:
                L[f"{tool}_items_repeating_nature"] = {
                    "n_cmp": len(tv[0]["cmp_ids"]),
                    "share_mean": pct(sum(len(covered(x, level, "cmp")) for x in tv), len(tv[0]["cmp_ids"]) * len(tv)),
                    "items_any_rep": sorted(set.union(*(covered(x, level, "cmp") for x in tv)))}
        res["levels"][level] = L
    return res, nature_cov


def cross_judge(summ: dict[str, Any], nature_cov: dict[str, dict[str, set]]) -> dict[str, Any]:
    """Set comparisons that combine judges: isitcredible-only and one-shot-only human issues,
    and coverage of the human issues no Nature referee raised (by either judge)."""
    out: dict[str, Any] = {}
    per_eval_ids = [i["id"] for i in human_issues(PAPER)]
    for level in v2.LEVELS:
        lv: dict[str, Any] = {}
        not_copyable = set(per_eval_ids)
        for judge in summ:
            not_copyable -= nature_cov.get(judge, {}).get(level, set())
        lv["n_per_eval"] = len(per_eval_ids)
        lv["not_raised_by_nature_referees"] = sorted(not_copyable)
        for judge, s in summ.items():
            L = s["levels"][level]
            if "isit__per_eval" not in L:
                continue
            cov = {t: set(L[f"{t}__per_eval"]["covered_all_reps"]) for t in TOOLS if f"{t}__per_eval" in L}
            anyc = {t: set(L[f"{t}__per_eval"]["covered_any_rep"]) for t in TOOLS if f"{t}__per_eval" in L}
            oneshot = cov.get("opus", set()) | cov.get("gpt", set())
            oneshot_any = anyc.get("opus", set()) | anyc.get("gpt", set())
            lv[judge] = {
                "isit_only_vs_opus": sorted(cov["isit"] - anyc.get("opus", set())),
                "opus_only_vs_isit": sorted(cov.get("opus", set()) - anyc["isit"]),
                "isit_only_vs_either_oneshot": sorted(cov["isit"] - oneshot_any),
                "oneshot_only_vs_isit": sorted(oneshot - anyc["isit"]),
                "rule": "covered in both replicates by one list and in neither by the other",
                "not_copyable_coverage": {t: {"covered_all_reps": len(cov[t] & not_copyable),
                                              "covered_any_rep": len(anyc[t] & not_copyable),
                                              "n": len(not_copyable),
                                              "pct_all_reps": pct(len(cov[t] & not_copyable), len(not_copyable))}
                                          for t in cov},
                "by_evaluator": {t: {e: {"covered_all_reps": sum(1 for i in cov[t] if f"::{e}::" in i),
                                         "n": sum(1 for i in per_eval_ids if f"::{e}::" in i)} for e in ("E1", "E2")}
                                 for t in cov},
            }
        out[level] = lv
    return out


def md_table(summ: dict[str, Any], cross: dict[str, Any]) -> str:
    lines = ["# isitcredible vs one-shot on Williams et al. (2024): computed results", "",
             f"Generated {utc_now()} by `scripts/compare_isitcredible_williams.py summarize`. One paper; "
             "AI judges only. Coverage = share of reference (human) issues matched; overlap = share of the "
             "compared list's items that match a reference issue. Levels as in the v2 judge: strict = same concern; "
             "standard = also same concern at different scope; loose = also same target, different problem. "
             "Means over two replicates unless marked r1.", ""]
    freeze = json.loads((RUN / "freeze.json").read_text())
    lines += [f"List sizes: isitcredible {freeze['isitcredible']['n_issues']} issues "
              f"({freeze['isitcredible']['n_quotes_verified']} quotes verified); Nature referees "
              f"{freeze['nature_referees']['n_issues']} issues.", ""]
    for level in v2.LEVELS:
        lines += [f"## {level}", "", "| Comparison | " + " | ".join(JUDGE_LABEL[j] for j in summ) + " |",
                  "|---|" + "---|" * len(summ)]

        def row(label, fn):
            vals = []
            for j in summ:
                try:
                    vals.append(fn(summ[j]["levels"][level], cross[level].get(j, {})))
                except (KeyError, TypeError):
                    vals.append("–")
            lines.append(f"| {label} | " + " | ".join(str(v) for v in vals) + " |")

        for ref, rl in (("per_eval", "E1+E2 issues"), ("curated", "curated list")):
            for t in TOOLS:
                row(f"{TOOL_LABEL[t]}: coverage of {rl}",
                    lambda L, c, t=t, ref=ref: f"{L[f'{t}__{ref}']['coverage_mean']}% of {L[f'{t}__{ref}']['n_ref']} "
                                                f"(reps {L[f'{t}__{ref}']['coverage_by_rep']})")
            for t in TOOLS:
                row(f"{TOOL_LABEL[t]}: own items matching {rl}",
                    lambda L, c, t=t, ref=ref: f"{L[f'{t}__{ref}']['overlap_mean']}% of {L[f'{t}__{ref}']['n_cmp']}")
        row("Human-human: E1 issues raised by E2", lambda L, c: f"{L['human_human']['E1_covered_by_E2_mean']}% of {L['human_human']['n_E1']}")
        row("Human-human: E2 issues raised by E1", lambda L, c: f"{L['human_human']['E2_covered_by_E1_mean']}% of {L['human_human']['n_E2']}")
        for t in TOOLS:
            row(f"Placebo r1: {PLACEBO_PAPER} E1+E2 issues covered by Williams {t} list",
                lambda L, c, t=t: f"{L[f'placebo__{t}']['coverage']}% of {L[f'placebo__{t}']['n_ref']} (same_study={L[f'placebo__{t}']['same_study']})")
        row("Nature referees: E1+E2 issues they also raised", lambda L, c: f"{L['nature_covers_per_eval']['coverage_mean']}% of {L['nature_covers_per_eval']['n_ref']}")
        row("Nature referees r1: curated issues they also raised", lambda L, c: f"{L['nature_covers_curated']['coverage']}% of {L['nature_covers_curated']['n_ref']}")
        for t in TOOLS:
            row(f"{TOOL_LABEL[t]}: own items repeating a Nature referee point",
                lambda L, c, t=t: f"{L[f'{t}_items_repeating_nature']['share_mean']}% of {L[f'{t}_items_repeating_nature']['n_cmp']}")
        nc = len(cross[level]["not_raised_by_nature_referees"])
        for t in TOOLS:
            row(f"{TOOL_LABEL[t]}: coverage (both reps) of the {nc} E1+E2 issues no Nature referee raised (either judge)",
                lambda L, c, t=t: f"{c['not_copyable_coverage'][t]['covered_all_reps']} of {c['not_copyable_coverage'][t]['n']}")
        row("Human issues covered by isitcredible, not by Opus one-shot", lambda L, c: f"{len(c['isit_only_vs_opus'])}: {', '.join(i.split('::',1)[1] for i in c['isit_only_vs_opus']) or 'none'}")
        row("Human issues covered by Opus one-shot, not by isitcredible", lambda L, c: f"{len(c['opus_only_vs_isit'])}: {', '.join(i.split('::',1)[1] for i in c['opus_only_vs_isit']) or 'none'}")
        row("Covered by isitcredible, by neither one-shot", lambda L, c: f"{len(c['isit_only_vs_either_oneshot'])}: {', '.join(i.split('::',1)[1] for i in c['isit_only_vs_either_oneshot']) or 'none'}")
        row("Covered by a one-shot, not by isitcredible", lambda L, c: f"{len(c['oneshot_only_vs_isit'])}: {', '.join(i.split('::',1)[1] for i in c['oneshot_only_vs_isit']) or 'none'}")
        for t in TOOLS:
            row(f"{TOOL_LABEL[t]}: E1 / E2 issues covered (both reps)",
                lambda L, c, t=t: f"E1 {c['by_evaluator'][t]['E1']['covered_all_reps']}/{c['by_evaluator'][t]['E1']['n']}, "
                                  f"E2 {c['by_evaluator'][t]['E2']['covered_all_reps']}/{c['by_evaluator'][t]['E2']['n']}")
        lines.append("")
    with SPEND.open() as f:
        rows = list(csv.DictReader(f))
    tot = round(sum(float(r["est_cost_usd"] or 0) for r in rows), 3)
    by_stage: dict[str, float] = {}
    for r in rows:
        by_stage[r["stage"]] = by_stage.get(r["stage"], 0) + float(r["est_cost_usd"] or 0)
    lines += ["## Cost", "", f"Estimated API spend ${tot} over {len(rows)} calls: " +
              ", ".join(f"{k} ${v:.3f}" for k, v in sorted(by_stage.items())) + ". GPT judge calls ran on the ChatGPT subscription.", ""]
    return "\n".join(lines)


def stage_summarize(args) -> int:
    summ, ncov = {}, {}
    for judge in ("claude", "codex"):
        if (RUN / "judgments" / judge).exists():
            summ[judge], ncov[judge] = summarize_judge(judge)
    cross = cross_judge(summ, ncov)
    write_json(RUN / "summary.json", {"generated": utc_now(), "judges": summ, "cross": cross})
    (RUN / "summary.md").write_text(md_table(summ, cross))
    print((RUN / "summary.md").read_text())
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stage", choices=["freeze", "normalize", "judge", "summarize"])
    ap.add_argument("--judge", choices=["claude", "codex"], default="claude")
    ap.add_argument("--case", action="append")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    RUN.mkdir(parents=True, exist_ok=True)
    gi = RUN / ".gitignore"
    if not gi.exists():
        gi.write_text("# isitcredible item texts, rewrites, judge reasons and source copies stay local\nprivate/\n")
    return {"freeze": stage_freeze, "normalize": stage_normalize, "judge": stage_judge,
            "summarize": stage_summarize}[args.stage](args)


if __name__ == "__main__":
    sys.exit(main())
