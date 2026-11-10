#!/usr/bin/env python3
"""
Eligibility manifest for expanding the critique-overlap comparison.

For every PDF in papers/ this records, deterministically and without any model
call:

  - the PDF's SHA-256, page count and creation date;
  - the research title we believe it is (from three local label tables), and
    whether that title is actually printed in the first pages of the PDF;
  - the published Unjournal evaluation files (data/unjournal_evaluations/*.md)
    whose own front-matter title quotes that research title, with their kind
    (evaluation, summary, author response), publication date and body length;
  - whether the PDF plausibly predates the evaluations (creation date, and no
    mention of The Unjournal in its text), since a later version may already
    answer the evaluators.

A paper is `eligible` only when every check passes. Papers that fail are kept
in the manifest with the reason, so the denominator is visible. Matching is by
normalised exact title, never fuzzy: the earlier Benabou and Peterman
mispairings came from attractive but wrong matches.

Evaluator names are never written. Evaluations are identified by file slug.

Usage:
    python scripts/build_critique_eligibility_manifest.py
    python scripts/build_critique_eligibility_manifest.py --out-dir /tmp/x
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import unicodedata
from datetime import date, datetime, timezone
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
PAPERS_DIR = ROOT / "papers"
EVAL_DIR = ROOT / "data" / "unjournal_evaluations"
UJ_MAP = ROOT / "data" / "UJ_map.csv"
META_CSV = ROOT / "data" / "paper_abstracts_meta_data" / "paper_abstracts_and_metadata.csv"
FETCH_MANIFEST = ROOT / "data" / "paper_fetch_manifest.json"
DEFAULT_OUT = ROOT / "data"

# Pairings excluded from the existing critique analysis (scripts/analysis_checks.R).
# They are flagged, not silently dropped; David decides whether the published-evaluation
# reference changes their status.
LEGACY_EXCLUDED = {"Benabou_et_al._2023", "Peterman_et_al._2025"}
FOCAL_RUN_DIR = ROOT / "results" / "gpt52_pro_focal_jan2026" / "json"

MIN_EVAL_BODY_CHARS = 3000   # shorter files are stubs that point elsewhere
TITLE_PAGES = 3              # pages of the PDF searched for the title


# --------------------------------------------------------------------------
# Text helpers
# --------------------------------------------------------------------------

def norm(text: str) -> str:
    """Lower-case, strip accents and every non-alphanumeric character."""
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def norm_label(text: str) -> str:
    """Normalise an author-year label ("Kudymowa et al., 2023", "Kudymowa_et_al._2023")."""
    return norm(text)


def split_front_matter(md: str) -> tuple[str, str]:
    """Return (front_matter, body) for a pandoc-style markdown export."""
    if not md.startswith("---"):
        return "", md
    end = md.find("\n---", 3)
    if end == -1:
        return "", md
    return md[3:end], md[end + 4:]


def front_matter_title(fm: str) -> str:
    """The `title:` scalar, joining indented continuation lines."""
    m = re.search(r"^title:[ \t]*(.*(?:\n[ \t]+.*)*)", fm, flags=re.M)
    if not m:
        return ""
    title = re.sub(r"\s*\n\s*", " ", m.group(1)).strip()
    if len(title) >= 2 and title[0] == title[-1] and title[0] in "\"'":
        title = title[1:-1]
    return title.replace('\\"', '"').strip()


def front_matter_date(fm: str) -> str:
    """ISO date from the `date:` block (day/month/year), or ''."""
    m = re.search(r"^date:\s*\n((?:[ \t]+.*\n?)+)", fm, flags=re.M)
    if not m:
        return ""
    parts = dict(re.findall(r"(day|month|year):\s*\"?(\d+)\"?", m.group(1)))
    try:
        return date(int(parts["year"]), int(parts["month"]), int(parts["day"])).isoformat()
    except (KeyError, ValueError):
        return ""


def quoted_titles(title: str) -> list[str]:
    """Paper titles quoted inside an evaluation's own title."""
    out = re.findall(r"[\"“]([^\"”]{8,})[\"”]", title)
    return [t.strip() for t in out]


def classify_kind(title: str, slug: str) -> str:
    t = title.lower()
    s = slug.lower()
    if "author" in t and "response" in t or s.startswith(("authorresponse", "authorsresponse", "ar_")) or "authorresponse" in s:
        return "author_response"
    if "summary" in t or "evalsum" in s or s.endswith(("evalsum", "summary")):
        return "summary"
    if re.match(r"\s*evaluation\s*\d*\s*(of|:)", t) or re.search(r"(^e\d|eval\d|e\d$)", s):
        return "evaluation"
    return "other"


def evaluator_index(title: str, slug: str) -> int | None:
    m = re.match(r"\s*evaluation\s*(\d+)\s*(of|:)", title.lower())
    if m:
        return int(m.group(1))
    m = re.search(r"(?:^e|eval|e)(\d)(?=[a-z_]|$)", slug.lower())
    return int(m.group(1)) if m else None


# --------------------------------------------------------------------------
# Local label tables
# --------------------------------------------------------------------------

def load_label_titles() -> dict[str, dict[str, str]]:
    """Map normalised author-year label -> {source: research title}."""
    out: dict[str, dict[str, str]] = {}

    def add(label: str, title: str, source: str) -> None:
        if label and title:
            out.setdefault(norm_label(label), {})[source] = " ".join(title.split())

    if UJ_MAP.exists():
        for line in UJ_MAP.read_text(encoding="utf-8", errors="replace").splitlines()[1:]:
            if ";" in line:
                label, title = line.split(";", 1)
                add(label, title, "UJ_map")
    if META_CSV.exists():
        with META_CSV.open(newline="", encoding="utf-8", errors="replace") as fh:
            for row in csv.DictReader(fh):
                add(row.get("author_date", ""), row.get("label_paper_title", ""), "paper_metadata")
    if FETCH_MANIFEST.exists():
        for item in json.loads(FETCH_MANIFEST.read_text()).values():
            pdf = item.get("before_pdf") or ""
            if pdf:
                add(pathlib.Path(pdf).stem, item.get("paper_title", ""), "fetch_manifest")
    return out


def load_evaluations() -> list[dict[str, Any]]:
    evals = []
    for path in sorted(EVAL_DIR.glob("*.md")):
        md = path.read_text(encoding="utf-8", errors="replace")
        fm, body = split_front_matter(md)
        title = front_matter_title(fm)
        evals.append({
            "slug": path.stem,
            "file": str(path.relative_to(ROOT)),
            "title": title,
            "quoted_titles_norm": [norm(t) for t in quoted_titles(title)],
            "title_norm": norm(title),
            "kind": classify_kind(title, path.stem),
            "evaluator_index": evaluator_index(title, path.stem),
            "date": front_matter_date(fm),
            "body_chars": len(body.strip()),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    return evals


# --------------------------------------------------------------------------
# PDF facts
# --------------------------------------------------------------------------

def pdf_info(path: pathlib.Path) -> dict[str, Any]:
    info: dict[str, Any] = {"pages": None, "creation_date": ""}
    if not shutil.which("pdfinfo"):
        return info
    proc = subprocess.run(["pdfinfo", "-isodates", str(path)], capture_output=True, text=True, errors="replace")
    m = re.search(r"^Pages:\s+(\d+)", proc.stdout, flags=re.M)
    if m:
        info["pages"] = int(m.group(1))
    m = re.search(r"^CreationDate:\s+(\d{4}-\d{2}-\d{2})", proc.stdout, flags=re.M)
    if m:
        info["creation_date"] = m.group(1)
    return info


def pdf_text(path: pathlib.Path, first_pages: int | None = None) -> str:
    if not shutil.which("pdftotext"):
        return ""
    cmd = ["pdftotext", "-q"]
    if first_pages:
        cmd += ["-l", str(first_pages)]
    cmd += [str(path), "-"]
    proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace")
    return proc.stdout


# --------------------------------------------------------------------------
# Manifest
# --------------------------------------------------------------------------

def build() -> dict[str, Any]:
    labels = load_label_titles()
    evals = load_evaluations()
    focal = {p.name.replace(".response.json", "").replace(".json", "") for p in FOCAL_RUN_DIR.glob("*.json")}
    papers = []

    for pdf in sorted(PAPERS_DIR.glob("*.pdf")):
        stem = pdf.stem
        info = pdf_info(pdf)
        head_norm = norm(pdf_text(pdf, TITLE_PAGES))
        full_text = pdf_text(pdf)
        titles = labels.get(norm_label(stem), {})
        distinct = sorted({norm(t) for t in titles.values()})

        # A candidate title counts only if the PDF itself prints it.
        verified = [t for t in dict.fromkeys(titles.values()) if norm(t) and norm(t) in head_norm]
        research_title = verified[0] if verified else ""
        tnorm = norm(research_title)

        matched = []
        if tnorm:
            for ev in evals:
                if tnorm in ev["quoted_titles_norm"] or (len(tnorm) >= 25 and tnorm in ev["title_norm"]):
                    matched.append(ev)

        indiv = [e for e in matched if e["kind"] == "evaluation"]
        substantive = [e for e in indiv if e["body_chars"] >= MIN_EVAL_BODY_CHARS]
        eval_dates = sorted(e["date"] for e in matched if e["date"])
        first_eval = eval_dates[0] if eval_dates else ""
        mentions_uj = bool(re.search(r"unjournal", full_text, flags=re.I))
        predates = None
        if info["creation_date"] and first_eval:
            predates = info["creation_date"] <= first_eval

        reasons = []
        if not titles:
            reasons.append("no research title in local label tables")
        elif not research_title:
            reasons.append("no candidate title is printed in the first pages of the PDF")
        if len(distinct) > 1:
            reasons.append("label tables disagree on the title")
        if research_title and not matched:
            reasons.append("no published evaluation file quotes this title")
        if matched and not substantive:
            reasons.append("no individual evaluation with a substantive body")
        if mentions_uj:
            reasons.append("PDF text mentions The Unjournal (possibly a post-evaluation version)")
        if predates is False:
            reasons.append("PDF creation date is after the first evaluation date")
        if stem in LEGACY_EXCLUDED:
            reasons.append("excluded from the existing critique analysis (legacy mispairing)")

        papers.append({
            "paper": stem,
            "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
            "pdf_pages": info["pages"],
            "pdf_creation_date": info["creation_date"],
            "candidate_titles": titles,
            "research_title": research_title,
            "title_printed_in_pdf": bool(research_title),
            "pdf_mentions_unjournal": mentions_uj,
            "first_evaluation_date": first_eval,
            "pdf_predates_first_evaluation": predates,
            "n_evaluation_files": len(matched),
            "n_individual_evaluations": len(indiv),
            "n_substantive_individual_evaluations": len(substantive),
            "has_summary": any(e["kind"] == "summary" for e in matched),
            "has_author_response": any(e["kind"] == "author_response" for e in matched),
            "in_gpt52_focal_run": stem in focal,
            "eligible": not reasons,
            "ineligible_reasons": reasons,
            "evaluations": [
                {k: e[k] for k in ("slug", "file", "kind", "evaluator_index", "date", "body_chars", "sha256")}
                for e in matched
            ],
        })

    used = {e["slug"] for p in papers for e in p["evaluations"]}
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rules": {
            "title_match": "normalised exact; the title must be printed in the first "
                           f"{TITLE_PAGES} PDF pages and quoted in the evaluation's own title",
            "min_eval_body_chars": MIN_EVAL_BODY_CHARS,
            "eligible": "title verified, >=1 substantive individual evaluation, PDF does not mention "
                        "The Unjournal, PDF creation date not after the first evaluation, not a legacy exclusion",
        },
        "counts": {
            "pdfs": len(papers),
            "eligible": sum(p["eligible"] for p in papers),
            "eligible_with_2plus_evaluations": sum(
                p["eligible"] and p["n_substantive_individual_evaluations"] >= 2 for p in papers),
            "evaluation_files": len(evals),
            "evaluation_files_matched_to_a_pdf": len(used),
        },
        "papers": papers,
    }


def write(manifest: dict[str, Any], out_dir: pathlib.Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "critique_eligibility_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    cols = ["paper", "eligible", "ineligible_reasons", "research_title", "pdf_pages", "pdf_creation_date",
            "first_evaluation_date", "pdf_predates_first_evaluation", "pdf_mentions_unjournal",
            "n_individual_evaluations", "n_substantive_individual_evaluations", "has_summary",
            "has_author_response", "in_gpt52_focal_run", "pdf_sha256"]
    with (out_dir / "critique_eligibility_manifest.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for p in manifest["papers"]:
            row = {k: p[k] for k in cols}
            row["ineligible_reasons"] = "; ".join(p["ineligible_reasons"])
            w.writerow(row)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", type=pathlib.Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    manifest = build()
    write(manifest, args.out_dir)
    c = manifest["counts"]
    print(json.dumps(c, indent=1))
    tally: dict[str, int] = {}
    for p in manifest["papers"]:
        for r in p["ineligible_reasons"]:
            tally[r] = tally.get(r, 0) + 1
    for r, n in sorted(tally.items(), key=lambda kv: -kv[1]):
        print(f"  {n:3d}  {r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
