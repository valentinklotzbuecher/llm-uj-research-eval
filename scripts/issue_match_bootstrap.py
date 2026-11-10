#!/usr/bin/env python3
"""Bootstrap intervals over papers and between-judge agreement for v2 judge runs.

For each run (results/<run-id>/calls/*.json from run_issue_match_judge.py) and
each strictness level, a paper's coverage is the share of its human issues
covered, averaged over replicates. Papers are resampled with replacement
(cluster bootstrap); the statistic is the mean per-paper rate, as in the
published headline. With two runs on identical inputs, it also reports the
paired difference (same resampled papers), and item-level agreement and
Cohen's kappa on which human issues are covered (replicate 1).

Counts only; no issue text. Writes results/<first-run-id>/bootstrap.json.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import random
import statistics as st

ROOT = pathlib.Path(__file__).resolve().parents[1]
LEVELS = ("strict", "standard", "loose")


def load(run_id: str) -> list[dict]:
    d = ROOT / "results" / run_id / "calls"
    recs = [json.loads(f.read_text()) for f in sorted(d.glob("*.json")) if not f.name.endswith(".raw_response.json")]
    return [r for r in recs if "metrics" in r]


def per_paper(recs: list[dict], level: str, what: str = "coverage") -> dict[str, float]:
    out: dict[str, list[float]] = {}
    for r in recs:
        if r["case"]["kind"] != "real":
            continue
        out.setdefault(r["case"]["human_paper"], []).append(r["metrics"][level][what])
    return {k: st.mean(v) for k, v in out.items()}


def covered_items(rec: dict, level_cats: set[str]) -> set[str]:
    return {p["human"] for p in rec["pairs"] if p["category"] in level_cats}


def kappa(a: list[bool], b: list[bool]) -> float | None:
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    return None if pe == 1 else round((po - pe) / (1 - pe), 3)


def ci(vals: list[float]) -> list[float]:
    v = sorted(vals)
    return [round(v[int(0.025 * len(v))], 1), round(v[int(0.975 * len(v)) - 1], 1)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_ids", nargs="+")
    ap.add_argument("--draws", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=20261110)
    args = ap.parse_args()

    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from run_issue_match_judge import LEVELS as CATS  # noqa: E402

    runs = {rid: load(rid) for rid in args.run_ids}
    pub = {r["gpt_paper"]: r["comparison"]["coverage_pct"]
           for r in json.loads((ROOT / "results/key_issues_comparison_results.json").read_text())}
    papers = sorted(set.intersection(*(set(per_paper(v, "standard")) for v in runs.values())))
    rng = random.Random(args.seed)
    draws = [[rng.choice(papers) for _ in papers] for _ in range(args.draws)]
    out: dict = {"papers": papers, "n_papers": len(papers), "draws": args.draws, "seed": args.seed, "runs": {}}

    pub_pp = {p: float(pub[p]) for p in papers}
    out["published"] = {"mean": round(st.mean(pub_pp.values()), 1),
                        "ci95": ci([st.mean(pub_pp[p] for p in d) for d in draws])}
    for rid, recs in runs.items():
        res = {}
        for lv in LEVELS:
            cov = per_paper(recs, lv)
            ovl = per_paper(recs, lv, "overlap")
            res[lv] = {"coverage_mean": round(st.mean(cov[p] for p in papers), 1),
                       "coverage_ci95": ci([st.mean(cov[p] for p in d) for d in draws]),
                       "overlap_mean": round(st.mean(ovl[p] for p in papers), 1),
                       "overlap_ci95": ci([st.mean(ovl[p] for p in d) for d in draws]),
                       "diff_vs_published": round(st.mean(cov[p] - pub_pp[p] for p in papers), 1),
                       "diff_vs_published_ci95": ci([st.mean(cov[p] - pub_pp[p] for p in d) for d in draws])}
        ctl = [r for r in recs if r["case"]["kind"] != "real"]
        res["controls"] = {"n": len(ctl), "max_loose_coverage": max((r["metrics"]["loose"]["coverage"] for r in ctl), default=None)}
        out["runs"][rid] = res

    if len(args.run_ids) == 2:
        a_id, b_id = args.run_ids
        pair = {}
        for lv in LEVELS:
            ca, cb = per_paper(runs[a_id], lv), per_paper(runs[b_id], lv)
            # item-level agreement on replicate 1
            ia = {r["case"]["human_paper"]: r for r in runs[a_id] if r["case"]["kind"] == "real" and r["case"]["replicate"] == 1}
            ib = {r["case"]["human_paper"]: r for r in runs[b_id] if r["case"]["kind"] == "real" and r["case"]["replicate"] == 1}
            xa, xb = [], []
            for p in papers:
                items = sorted(k for k in ia[p]["blinding"]["key"].values() if k.startswith("H"))
                sa, sb = covered_items(ia[p], CATS[lv]), covered_items(ib[p], CATS[lv])
                xa += [k in sa for k in items]
                xb += [k in sb for k in items]
            pair[lv] = {"mean_diff_coverage": round(st.mean(ca[p] - cb[p] for p in papers), 1),
                        "diff_ci95": ci([st.mean(ca[p] - cb[p] for p in d) for d in draws]),
                        "human_items": len(xa), "agree": sum(x == y for x, y in zip(xa, xb)),
                        "only_first": sum(x and not y for x, y in zip(xa, xb)),
                        "only_second": sum(y and not x for x, y in zip(xa, xb)),
                        "kappa": kappa(xa, xb)}
        out["paired"] = {"first": a_id, "second": b_id, "levels": pair}

    (ROOT / "results" / args.run_ids[0] / "bootstrap.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
