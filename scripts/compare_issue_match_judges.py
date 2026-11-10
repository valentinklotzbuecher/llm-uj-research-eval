#!/usr/bin/env python3
"""Compare the v2 critique-matching judge with the published GPT-5.2 Pro judge.

Reads results/<run-id>/calls/*.json (from run_issue_match_judge.py) and
results/key_issues_comparison_results.json. Writes results/<run-id>/comparison.json
and prints a Markdown summary. Counts only; no issue text.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import statistics as st

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEVELS = ("strict", "standard", "loose")


def covered(rec: dict, level: str, cats: dict[str, set[str]]) -> tuple[set[str], set[str]]:
    h = {p["human"] for p in rec["pairs"] if p["category"] in cats[level]}
    m = {p["model"] for p in rec["pairs"] if p["category"] in cats[level]}
    return h, m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", default="issue_match_judge_v2_opus55_2026-11-10")
    args = ap.parse_args()
    run_dir = ROOT / "results" / args.run_id

    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from run_issue_match_judge import LEVELS as CATS  # noqa: E402

    recs = [json.loads(f.read_text()) for f in sorted((run_dir / "calls").glob("*.json"))
            if not f.name.endswith(".raw_response.json")]
    recs = [r for r in recs if "metrics" in r]
    pub = {r["gpt_paper"]: r["comparison"] for r in json.loads((ROOT / "results/key_issues_comparison_results.json").read_text())}

    real = [r for r in recs if r["case"]["kind"] == "real"]
    by_paper: dict[str, dict[int, dict]] = {}
    for r in real:
        by_paper.setdefault(r["case"]["human_paper"], {})[r["case"]["replicate"]] = r

    rows = []
    for pid, reps in sorted(by_paper.items()):
        row = {"paper": pid, "n_human": reps[min(reps)]["metrics"]["n_human"], "n_model": reps[min(reps)]["metrics"]["n_model"],
               "published_coverage": pub[pid]["coverage_pct"], "published_overlap": pub[pid]["precision_pct"],
               "published_n_human": len(pub[pid]["matched_pairs"]) + len(pub[pid]["unmatched_human"])}
        for lv in LEVELS:
            row[f"{lv}_coverage"] = round(st.mean(x["metrics"][lv]["coverage"] for x in reps.values()), 1)
            row[f"{lv}_overlap"] = round(st.mean(x["metrics"][lv]["overlap"] for x in reps.values()), 1)
        if len(reps) >= 2:
            a, b = reps[1], reps[2]
            ha, ma = covered(a, "standard", CATS)
            hb, mb = covered(b, "standard", CATS)
            hall = set(a["blinding"]["key"].values())
            hum = {k for k in hall if k.startswith("H")}
            mod = {k for k in hall if k.startswith("L")}
            row["rep_agree_human_items"] = sum((k in ha) == (k in hb) for k in hum)
            row["rep_n_human_items"] = len(hum)
            row["rep_agree_model_items"] = sum((k in ma) == (k in mb) for k in mod)
            row["rep_n_model_items"] = len(mod)
            pa = {(p["human"], p["model"]): p["category"] for p in a["pairs"]}
            pb = {(p["human"], p["model"]): p["category"] for p in b["pairs"]}
            both = set(pa) & set(pb)
            row["rep_pairs_union"] = len(set(pa) | set(pb))
            row["rep_pairs_both"] = len(both)
            row["rep_pairs_same_category"] = sum(pa[k] == pb[k] for k in both)
        rows.append(row)

    def pooled(sub, lv):
        hc = sum(r["metrics"][lv]["human_covered"] for r in sub)
        nh = sum(r["metrics"]["n_human"] for r in sub)
        mm = sum(r["metrics"][lv]["model_matched"] for r in sub)
        nm = sum(r["metrics"]["n_model"] for r in sub)
        return {"human_covered": hc, "n_human": nh, "model_matched": mm, "n_model": nm,
                "pooled_coverage": round(100 * hc / nh, 1), "pooled_overlap": round(100 * mm / nm, 1),
                "mean_paper_coverage": round(st.mean(r["metrics"][lv]["coverage"] for r in sub), 1),
                "mean_paper_overlap": round(st.mean(r["metrics"][lv]["overlap"] for r in sub), 1)}

    controls = [r for r in recs if r["case"]["kind"] != "real"]
    out = {
        "papers": rows,
        "real": {lv: pooled(real, lv) for lv in LEVELS},
        "published_12": {"mean_paper_coverage": round(st.mean(r["published_coverage"] for r in rows), 1),
                         "mean_paper_overlap": round(st.mean(r["published_overlap"] for r in rows), 1)},
        "controls": [{"case": r["case"]["case_id"], "kind": r["case"]["kind"], "same_study": r["parsed"]["same_study"],
                      **{f"{lv}_coverage": r["metrics"][lv]["coverage"] for lv in LEVELS},
                      **{f"{lv}_overlap": r["metrics"][lv]["overlap"] for lv in LEVELS},
                      "category_counts": r["metrics"]["category_counts"]} for r in controls],
        "real_same_study": {k: sum(1 for r in real if r["parsed"]["same_study"] == k) for k in ("yes", "no", "unclear")},
        "real_category_counts": {c: sum(r["metrics"]["category_counts"][c] for r in real) for c in real[0]["metrics"]["category_counts"]} if real else {},
        "real_human_covered_only_by_broader_model_item": sum(r["metrics"]["human_covered_only_by_broader_model_item"] for r in real),
        "controls_pooled": {lv: pooled([r for r in controls if r["case"]["kind"] == "cross_paper_control"], lv) for lv in LEVELS}
        if any(r["case"]["kind"] == "cross_paper_control" for r in controls) else {},
    }
    if rows and "rep_agree_human_items" in rows[0]:
        out["replicate_agreement"] = {
            "human_items": f"{sum(r['rep_agree_human_items'] for r in rows)}/{sum(r['rep_n_human_items'] for r in rows)}",
            "model_items": f"{sum(r['rep_agree_model_items'] for r in rows)}/{sum(r['rep_n_model_items'] for r in rows)}",
            "pairs_found_in_both": f"{sum(r['rep_pairs_both'] for r in rows)}/{sum(r['rep_pairs_union'] for r in rows)}",
            "same_category_given_both": f"{sum(r['rep_pairs_same_category'] for r in rows)}/{sum(r['rep_pairs_both'] for r in rows)}",
        }
    (run_dir / "comparison.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({k: v for k, v in out.items() if k != "papers"}, indent=2))
    print("\n| Paper | n H (pub) | Published cov / ovl | v2 strict | v2 standard | v2 loose |")
    print("|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['paper']} | {r['n_human']} ({r['published_n_human']}) | {r['published_coverage']} / {r['published_overlap']} | "
              f"{r['strict_coverage']:.0f} / {r['strict_overlap']:.0f} | {r['standard_coverage']:.0f} / {r['standard_overlap']:.0f} | "
              f"{r['loose_coverage']:.0f} / {r['loose_overlap']:.0f} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
