#!/usr/bin/env python3
"""
Frozen, per-evaluator human issue reference built from the *published*
Unjournal evaluations in data/unjournal_evaluations/.

Two steps:

  manifest  For every PDF in papers/, find its published evaluation documents,
            classify each (evaluator report E1/E2/E3, evaluation-manager
            summary EM, authors' response, compiled duplicate), and write
            data/human_issue_reference/manifest.csv. No API calls.
  extract   For each usable evaluator report (and, separately, each manager
            summary), ask Claude Sonnet 5.5 for one item per distinct
            substantive critique, with a short verbatim anchor quote, and
            freeze the items with stable IDs (<paper>::E1::001).

Anonymity: evaluators are referred to only as E1/E2/E3. Document titles and
slugs are not written out, because some contain evaluator names; documents are
identified by doc_ref = sha256(file name)[:12] plus the file's SHA-256, which
can be recomputed from the committed exports. Before any text is sent to the
API, the YAML front matter is removed and every name listed as an author of
any evaluation document for the same paper is replaced by "[name]". Sections
holding ratings tables, evaluator details, references and process notes are
dropped.

Outputs: data/human_issue_reference/ (manifest.csv, items/<paper>.json,
items_long.csv, extraction ledger and raw responses).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pathlib
import re
import sys
import time
from datetime import datetime, timezone
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

EVAL_DIR = ROOT / "data" / "unjournal_evaluations"
PAPERS_DIR = ROOT / "papers"
OUT_DIR = ROOT / "data" / "human_issue_reference"
EXCLUDED = {  # documented human-critique pairing mismatches (scripts/analysis_checks.R)
    "Benabou_et_al._2023": "documented pairing mismatch (scripts/analysis_checks.R); excluded",
    "Peterman_et_al._2025": "documented pairing mismatch (scripts/analysis_checks.R); excluded",
}
MIN_REPORT_CHARS = 1500  # cleaned text below this is treated as a failed/stub export

# Distinctive title phrase (alphanumerics only, lower case) per paper PDF.
# None: no Unjournal evaluation of this paper in the exports.
TITLE_KEYS: dict[str, str | None] = {
    "Abbink_et_al._2025": None,
    "Acemoglu_et_al._2024": "misperceptionsanddemandfordemocracy",
    "Adena_and_Hager_2024": "doesonlinefundraisingincrease",
    "Aghion_et_al._2017": "artificialintelligenceandeconomicgrowth",
    "Akram_et_al._2017": "effectsofemigrationonrurallabor",
    "Alatas_et_al._2019": "twitterexperimentpromotingvaccination",
    "Alcott_et_al._2024": "nudgesincreasewelfare",
    "Angrist_et_al._2023": "buildingresilienteducationsystems",
    "Arora_et_al._2023": "effectofpublicscienceoncorporate",
    "Bahar_et_al._2022": "legalizingentrepreneurship",
    "Banerjee_et_al._2022": "selectingthemosteffectivenudge",
    "Banerjee_et_al._2023": "universalbasicincome",
    "Barberio_et_al._2022": "acceleratingvaccineinnovation",
    "Barker_et_al._2021": "mentalhealththerapyasacorestrategy",
    "BenYishay_et_al._2024": "irrigationstrengthensclimateresilience",
    "Benabou_et_al._2023": "endsversusmeans",
    "Benjamin_et_al._2023": None,
    "Bergeron_et_al._2024": "evolutionofeffortsuppressingbeliefs",
    "Bettle_2023": "guidetoceadiscounts",
    "Bhat_et_al._2022": "longruneffectsofpsychotherapy",
    "Bhattacharya_and_Packalen_2020": "stagnationandscientificincentives",
    "Bilal_and_Kaenzig_2024": "macroeconomicimpactofclimatechange",
    "Blimpo_and_Castaneda-Dower_2025": "asymmetryincivicinformation",
    "Bruelhart et al. 2021": None,
    "Bruers_2021": "animalwelfarecostofmeat",
    "Buntaine_et_al._2023": "squeakywheel",
    "Carson_et_al._2023": "chooseyourmoments",
    "Caviola_et_al._2022": "populationethicalintuitions",
    "Chuard_et_al._2022": "epidemiologicalapproachestomeasuring",
    "Clancy_2024": "returnstoscienceinthepresence",
    "Crawfurd_et_al._2023": "reducingleadexposure",
    "Denkenberger_et_al._2022": "resilientfoodsforglobalcatastrophes",
    "Dullaghan_and_Zhang_2022": "limitedculturedmeatproduction",
    "Epperson_and_Gerster_2024": "willfulignoranceandmoralbehavior",
    "Fangwa_et_al._2023": "governanceofnonprofits",
    "Frech_et_al._2023": "pharmaceuticalpricingandrd",
    "Green_et_al._2025": "meaningfullyreducingconsumptionofmeat",
    "Hahn_et_al._2025": "welfareanalysisofpoliciesimpactingclimate",
    "Haushofer_et_al._2020": "comparativeimpactofcashtransfers",
    "Hill_et_al._2024": "pivotpenalty",
    "Jack_et_al._2022": "moneynottoburn",
    "Jaroszewicz_et_al._2024": "randomizingunconditionalcashtransfer",
    "Kirkland_et_al._2023": None,
    "Kremer_et_al._2020": "advancemarketcommitments",
    "Kremer_et_al._2022": "watertreatmentandchildmortality",
    "Kubo_et_al._2023": "banningwildlifetrade",
    "Kudymowa_et_al._2023": None,
    "Liang_et_al._2025": None,
    "Liang_et_al_2023": "environmentaleffectsofeconomicproduction",
    "McGuire_et_al._2024": "strongmindsandfriendshipbench",
    "Naidu_et_al._2023": "guestworkerprograms",
    "Peterman_et_al._2025": "socialsafetynetswomen",
    "Salazar_and_Restrepo_2024": "conservationworkingeneralequilibrium",
    "Schoenegger_et_al._2025": None,
    "Schuett_et_al._2023": "bestpracticesinagisafety",
    "Trammel_and_Aschenbrenner_2024": "existentialriskandgrowth",
    "Walker_et_al._2023": "intergenerationalchildmortality",
    "Weaver_et_al._2025": "maternalcashtransfersforgenderequity",
    "Williams_et_al._2024": "naturalregenerationindeforested",
    "Xing_et_al._2023": "urbanforests",
}

# Reviewed by hand (first page of the PDF against the evaluation titles):
# title differences that suggest the PDF may not be the version evaluated.
VERSION_NOTES = {
    "Alatas_et_al._2019": "VERSION MISMATCH: PDF is the 2019 NBER version ('When Celebrities Speak'); the evaluation summary says the May 2023 version ('Do Celebrity Endorsements Matter?') was evaluated, and E2 contrasts the two",
    "Bergeron_et_al._2024": "PDF title says 'Zero-Sum Environments', evaluations say 'Zero-Sum Thinking'; possibly a different version",
    "Barker_et_al._2021": "UJ_map.csv lists a different title ('Cognitive Behavioral Therapy among Ghana's Rural Poor...'); the PDF matches the evaluated title",
    "Haushofer_et_al._2020": "titles match; check the PDF date against the 2023 evaluations",
    "Kremer_et_al._2020": "PDF is the 5-page AEA P&P article; evaluated title matches",
}

DROP_SECTIONS = re.compile(
    r"(?i)^(summary measures|metrics|ratings|overall ratings|journal ranking tiers|evaluator details|"
    r"references|unjournal process notes|unjournal process|predictions|data presentation of metrics|"
    r"quality scale rating|evaluation process|how we chose the evaluators|coi issues|"
    r"metrics all evaluators|r unnumbered|r|note applied and policy stream|contents)\b")
GENERIC_AUTHOR = re.compile(r"(?i)evaluator|anonymous|reviewer|unjournal|manager|^anon")


def norm_key(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def sha256_file(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def doc_ref(name: str) -> str:
    return hashlib.sha256(name.encode()).hexdigest()[:12]


def split_front_matter(text: str) -> tuple[str, str]:
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    return (m.group(1), text[m.end():]) if m else ("", text)


def is_full_export(text: str) -> bool:
    return bool(re.match(r"---\n.*?\n---\n", text, re.S))


def doc_title(text: str) -> str:
    fm, body = split_front_matter(text)
    m = re.search(r"^title:\s*(.*?)(?=^\S|\Z)", fm, re.S | re.M)
    if m:
        return " ".join(m.group(1).split()).strip("'\"")
    h = re.search(r"^# (.+)$", body, re.M)
    return h.group(1).strip() if h else ""


def doc_authors(text: str) -> list[str]:
    fm, _ = split_front_matter(text)
    m = re.search(r"^author:\s*\n((?:- .*\n?)+)", fm, re.M)
    if not m:
        return []
    names = [ln[2:].strip().strip("'\"") for ln in m.group(1).splitlines() if ln.startswith("- ")]
    return [n for n in names if n and not GENERIC_AUTHOR.search(n)]


def classify(title: str) -> str:
    t = title.lower().replace('"', "").replace("\\", "").strip()
    if t.startswith(("authors' response", "author's response", "authors response")):
        return "AR"
    if t.startswith("compiled evaluations"):
        return "compiled"
    if t.startswith("evaluation summary") or t.startswith("evaluation summaries"):
        return "EM"
    m = re.match(r"evaluation\s*:?\s*(\d)", t)
    if m:
        return f"E{m.group(1)}"
    if t.startswith("evaluation of"):
        return "E1"
    return "other"


def redaction_patterns(names: list[str]) -> list[re.Pattern]:
    pats = set()
    for n in names:
        n = re.sub(r"\s*\(.*?\)", "", n).strip()
        if not n:
            continue
        pats.add(re.escape(n))
        for part in re.split(r"[\s,]+", n):
            part = part.strip(".")
            if len(part) >= 3:
                pats.add(re.escape(part))
    return [re.compile(rf"\b{p}\b", re.I) for p in sorted(pats, key=len, reverse=True)]


def reviewer_names(mine: list[dict[str, Any]]) -> list[str]:
    """Names listed as authors of evaluator reports and manager summaries (not authors' responses)."""
    out = []
    for d in mine:
        if not re.fullmatch(r"E\d|EM", d["role"]):
            continue
        out += d["authors"]
        # Names given in the title after the paper title: '... (by A B)', '..." by A B', '...": A B'.
        tail = re.split(r'["”]', d["title"].replace('\\"', '"'))[-1]
        m = re.search(r"\(by ([^)]+)\)|\bby ([A-Z][^,()]+)$|^\s*:\s*([A-Z][^,()]+)$", tail.strip())
        if m:
            name = next(g for g in m.groups() if g)
            if not GENERIC_AUTHOR.search(name):
                out.append(name.strip())
    return out


def redact(s: str, patterns: list[re.Pattern]) -> str:
    for p in patterns:
        s = p.sub("[name]", s)
    return s


def clean_text(text: str, patterns: list[re.Pattern]) -> str:
    """Report text as sent to the extractor: no front matter, tables, images or admin sections; names redacted."""
    _, body = split_front_matter(text)
    body = re.sub(r"!\[[^\]]*\]\([^)]*\)(\{[^}]*\})?", "", body)
    body = re.sub(r"data:[a-z]+/[a-z0-9.+-]+;base64,[A-Za-z0-9+/=]+", "", body)
    out, skip1, skip2 = [], False, False
    for line in body.splitlines():
        h = re.match(r"^(#{1,2}) +(.*)$", line)
        if h:
            label = re.sub(r"[^a-z ]", "", h.group(2).lower()).strip()
            drop = bool(DROP_SECTIONS.match(label))
            if len(h.group(1)) == 1:
                skip1, skip2 = drop, False
            else:
                skip2 = drop
        if skip1 or skip2:
            continue
        if re.match(r"^\s*[+|]", line):  # grid/pipe tables (ratings)
            continue
        out.append(line)
    cleaned = "\n".join(out)
    cleaned = re.sub(r"\[\^\d+\]", "", cleaned)
    cleaned = re.sub(r"\\\n", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return redact(cleaned, patterns).strip()


def pdf_first_page(path: pathlib.Path) -> str:
    try:
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            return " ".join((pdf.pages[0].extract_text() or "").split())[:400]
    except Exception:  # noqa: BLE001
        return ""


def load_docs() -> list[dict[str, Any]]:
    docs = []
    for f in sorted(EVAL_DIR.glob("*.md")):
        text = f.read_text()
        title = doc_title(text)
        docs.append({"file": f, "text": text, "title": title, "key": norm_key(title),
                     "role": classify(title), "authors": doc_authors(text)})
    return docs


def paper_docs(stem: str, docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    key = TITLE_KEYS.get(stem)
    if not key:
        return []
    return [d for d in docs if key in d["key"]]


def version_statements(stem: str) -> str:
    """Statements in the extracted reports about which paper version was evaluated (after extraction)."""
    f = OUT_DIR / "items" / f"{stem}.json"
    if not f.exists():
        return ""
    rec = json.loads(f.read_text())
    return " | ".join(f"{s}: {' '.join(v['version_statement'].split())[:200]}" for s, v in sorted(rec["sources"].items())
                      if v.get("version_statement", "").strip())


def build_manifest() -> list[dict[str, Any]]:
    docs = load_docs()
    pdfs = sorted(PAPERS_DIR.glob("*.pdf"))
    unknown = [p.stem for p in pdfs if p.stem not in TITLE_KEYS]
    if unknown:
        raise SystemExit(f"papers without a TITLE_KEYS entry: {unknown}")
    rows, used = [], set()
    for pdf in pdfs:
        stem = pdf.stem
        mine = paper_docs(stem, docs)
        used.update(d["file"].name for d in mine)
        pats = redaction_patterns(reviewer_names(mine))
        reports, em, other = {}, [], []
        notes = []
        for d in mine:
            cleaned = clean_text(d["text"], pats)
            # Exports without YAML front matter are scrape fallbacks holding only the paper's description.
            d["clean_chars"] = len(cleaned) if is_full_export(d["text"]) else 0
            if re.fullmatch(r"E\d", d["role"]):
                if d["role"] in reports:
                    notes.append(f"duplicate {d['role']} document")
                reports.setdefault(d["role"], []).append(d)
            elif d["role"] == "EM":
                em.append(d)
            else:
                other.append(d)
        usable = {r: ds[0] for r, ds in reports.items() if ds[0]["clean_chars"] >= MIN_REPORT_CHARS}
        stubs = sorted(r for r, ds in reports.items() if ds[0]["clean_chars"] < MIN_REPORT_CHARS)
        if stubs:
            notes.append(f"export incomplete (title stub only) for {', '.join(stubs)}")
        key = TITLE_KEYS.get(stem)
        first = pdf_first_page(pdf) if key else ""
        title_match = None
        if key:
            title_match = key in norm_key(first) or key[:20] in norm_key(first)
        if key and not mine:
            notes.append("no matching evaluation documents found")
        if stem in VERSION_NOTES:
            notes.append(VERSION_NOTES[stem])
        if key and title_match is False and stem not in VERSION_NOTES:
            notes.append("PDF first page has no text layer; title not checked automatically" if not first
                         else "evaluation title phrase not found on PDF first page; check version")
        status = "no_evaluation" if not key else ("excluded" if stem in EXCLUDED else
                  ("eligible_pair" if len(usable) >= 2 else ("single_report" if usable else "no_usable_report")))
        if stem in EXCLUDED:
            notes.append(EXCLUDED[stem])
        rows.append({
            "paper": stem, "pdf_sha256": sha256_file(pdf), "status": status,
            "n_evaluator_reports_published": len(reports), "n_evaluator_reports_usable": len(usable),
            "evaluators_usable": ";".join(sorted(usable)),
            "evaluator_doc_refs": ";".join(f"{r}={doc_ref(ds[0]['file'].name)}" for r, ds in sorted(reports.items())),
            "evaluator_doc_sha256": ";".join(f"{r}={sha256_file(ds[0]['file'])[:16]}" for r, ds in sorted(reports.items())),
            "evaluator_clean_chars": ";".join(f"{r}={ds[0]['clean_chars']}" for r, ds in sorted(reports.items())),
            "manager_summary_doc_ref": ";".join(doc_ref(d["file"].name) for d in em),
            "manager_summary_clean_chars": ";".join(str(d["clean_chars"]) for d in em),
            "n_other_docs": len(other),
            "pdf_title_matches_evaluated_title": "" if title_match is None else ("yes" if title_match else "no"),
            "version_statements": version_statements(stem),
            "notes": " | ".join(notes),
        })
    orphan = [d for d in docs if d["file"].name not in used and d["role"] in ("E1", "E2", "E3", "EM")]
    return rows, orphan


def write_manifest(rows: list[dict[str, Any]], orphan: list[dict[str, Any]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUT_DIR / "manifest.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    counts: dict[str, int] = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    meta = {"created": datetime.now(timezone.utc).isoformat(), "n_pdfs": len(rows), "status_counts": counts,
            "n_evaluation_exports": len(list(EVAL_DIR.glob("*.md"))),
            "evaluation_docs_without_a_pdf": len(orphan),
            "min_report_chars": MIN_REPORT_CHARS,
            "doc_ref": "sha256(export file name)[:12]; *_sha256 columns give the first 16 hex of the export file's SHA-256",
            "excluded": EXCLUDED}
    (OUT_DIR / "manifest_meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))


# --------------------------------------------------------------------------
# Extraction
# --------------------------------------------------------------------------

EXTRACT_MODEL = "claude-sonnet-5-5"
EXTRACT_EFFORT = "medium"
PRICE_IN, PRICE_OUT = 2.00, 10.00  # $/MTok, Sonnet 5.5
PROMPT_VERSION = "human_issue_extract_v1"

EXTRACT_PROMPT = """You extract the critiques from one published evaluation of a research paper, so that they can later be compared with critiques written by other reviewers. You do not judge the critiques.

Return one item per distinct substantive critique of the paper: a concern about its data, methods, identification, assumptions, calculations, results, interpretation, claims, scope, framing or reporting that the reviewer says is a problem or asks the authors to address.

For each item give:
- about: what the critique concerns (the specific result, table, estimate, variable, assumption, data source, model or claim), with any section, table, figure or page references the reviewer gives;
- problem: why the reviewer thinks it is a problem;
- consequence: what follows for the paper's claims, or what the reviewer asks for, if stated (empty string if not);
- anchor_quote: a short verbatim quote (5 to 30 words) copied exactly from the evaluation text, where the reviewer makes this point, for checking;
- reviewer_severity: the reviewer's own label for how serious it is, if they give one ("major", "minor", "most important", "necessary", "optional", a rank), copied briefly; empty string if none;
- minor: true if the reviewer presents it as minor or it is a small presentational point (wording, labelling, a missing citation); false otherwise.

Rules:
- Merge repeated mentions of the same point (for example a bullet in the abstract and its fuller discussion in the report) into one item, using the fuller version.
- Split points that concern different results or give different reasons, even if they appear in one paragraph.
- Exclude: praise and strengths; summaries of what the paper does; the reviewer's ratings and their justifications unless they state a specific critique; comments on The Unjournal, its process or the evaluation form; replies to or discussion of author responses; pure typos and copy-editing.
- Keep the reviewer's specific details: numbers, variable names, methods, data sources, section references.
- Write in plain third person ("The analysis...", "The paper..."). Do not name or describe the reviewer.
- Text shown as [name] was redacted; leave it as is.

Also give version_statement: any sentence in the evaluation saying which version or date of the paper was evaluated, copied verbatim (empty string if none)."""

EXTRACT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "version_statement": {"type": "string"},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "about": {"type": "string"},
                    "problem": {"type": "string"},
                    "consequence": {"type": "string"},
                    "anchor_quote": {"type": "string"},
                    "reviewer_severity": {"type": "string"},
                    "minor": {"type": "boolean"},
                },
                "required": ["about", "problem", "consequence", "anchor_quote", "reviewer_severity", "minor"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["version_statement", "items"],
    "additionalProperties": False,
}

EM_NOTE = ("\n\nThis document is the evaluation manager's summary of several evaluations. Extract only critiques "
           "of the paper that this document states, including the manager's own; do not attribute them to anyone.")


def squash(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def anchor_found(quote: str, text: str) -> bool:
    q = squash(quote)
    return bool(q) and q in squash(text)


def call_extractor(client, system: str, user: str, raw_path: pathlib.Path) -> dict[str, Any]:
    from run_headless_claude_misses import api_schema

    t0 = time.time()
    with client.messages.stream(
        model=EXTRACT_MODEL, max_tokens=32000, system=system,
        output_config={"effort": EXTRACT_EFFORT, "format": {"type": "json_schema", "schema": api_schema(EXTRACT_SCHEMA)}},
        messages=[{"role": "user", "content": user}],
    ) as stream:
        msg = stream.get_final_message()
    d = msg.to_dict()
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(json.dumps(d, ensure_ascii=False))
    if d.get("stop_reason") != "end_turn":
        raise RuntimeError(f"extractor stop_reason {d.get('stop_reason')} ({raw_path.name})")
    text = "".join(b.get("text", "") or "" for b in d.get("content", []) if b.get("type") == "text")
    u = d.get("usage") or {}
    cost = round((u.get("input_tokens", 0) or 0) * PRICE_IN / 1e6 + (u.get("output_tokens", 0) or 0) * PRICE_OUT / 1e6, 5)
    return {"parsed": json.loads(text), "usage": u, "cost": cost, "model": d.get("model"),
            "elapsed": round(time.time() - t0, 1)}


def ledger_total() -> float:
    p = OUT_DIR / "extraction_ledger.csv"
    if not p.exists():
        return 0.0
    with p.open() as f:
        return sum(float(r["est_cost_usd"]) for r in csv.DictReader(f))


def record(row: dict[str, Any]) -> None:
    p = OUT_DIR / "extraction_ledger.csv"
    fields = ["timestamp", "paper", "source", "doc_ref", "model", "input_tokens", "output_tokens", "est_cost_usd", "elapsed_seconds", "n_items"]
    new = not p.exists()
    with p.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in fields})


def sources_for(stem: str, docs: list[dict[str, Any]]) -> tuple[list[tuple[str, dict[str, Any]]], list[re.Pattern]]:
    mine = paper_docs(stem, docs)
    pats = redaction_patterns(reviewer_names(mine))
    out, seen, n_em = [], set(), 0
    for d in sorted(mine, key=lambda x: x["file"].name):
        role = d["role"]
        if role == "EM":
            n_em += 1
            src = "EM" if n_em == 1 else f"EM{n_em}"
        elif re.fullmatch(r"E\d", role):
            src = role
        else:
            continue
        if src in seen:  # duplicate evaluator number: keep the first (noted in the manifest)
            continue
        seen.add(src)
        out.append((src, d))
    return sorted(out, key=lambda x: x[0]), pats


def extract(papers: list[str], budget: float, include_em: bool, force: bool) -> None:
    from run_headless_claude_misses import make_client

    docs = load_docs()
    client = make_client()
    prompt_sha = hashlib.sha256(EXTRACT_PROMPT.encode()).hexdigest()
    (OUT_DIR / "extract_prompt.txt").write_text(EXTRACT_PROMPT + "\n\n[manager-summary addendum]" + EM_NOTE)
    for stem in papers:
        out = OUT_DIR / "items" / f"{stem}.json"
        if out.exists() and not force:
            continue
        srcs, pats = sources_for(stem, docs)
        rec: dict[str, Any] = {"paper": stem, "prompt_version": PROMPT_VERSION, "prompt_sha256": prompt_sha,
                               "model": EXTRACT_MODEL, "effort": EXTRACT_EFFORT, "frozen": datetime.now(timezone.utc).isoformat(),
                               "sources": {}}
        for src, d in srcs:
            if src.startswith("EM") and not include_em:
                continue
            cleaned = clean_text(d["text"], pats)
            if len(cleaned) < MIN_REPORT_CHARS or not is_full_export(d["text"]):
                rec["sources"][src] = {"doc_ref": doc_ref(d["file"].name), "status": "stub_export", "items": []}
                continue
            if ledger_total() >= budget:
                print(f"budget ${budget} reached; stopping")
                return
            system = EXTRACT_PROMPT + (EM_NOTE if src.startswith("EM") else "")
            user = "Evaluation text:\n\n" + cleaned + "\n\nReturn JSON matching the supplied schema."
            print(f"extract {stem} {src} ({len(cleaned)} chars) ...", flush=True)
            r = call_extractor(client, system, user, OUT_DIR / "raw" / f"{stem}__{src}.raw_response.json")
            items = []
            for i, it in enumerate(r["parsed"]["items"], 1):
                for k in ("about", "problem", "consequence", "anchor_quote"):  # never let a name through
                    it[k] = redact(it[k], pats)
                items.append({"id": f"{stem}::{src}::{i:03d}", **it,
                              "anchor_verified": anchor_found(it["anchor_quote"], cleaned)})
            rec["sources"][src] = {
                "doc_ref": doc_ref(d["file"].name), "doc_sha256": sha256_file(d["file"]),
                "cleaned_text_sha256": hashlib.sha256(cleaned.encode()).hexdigest(), "cleaned_chars": len(cleaned),
                "role": "evaluation_manager_summary" if src.startswith("EM") else "evaluator_report",
                "status": "ok", "model": r["model"], "usage": r["usage"], "est_cost_usd": r["cost"],
                "version_statement": redact(r["parsed"]["version_statement"], pats),
                "items": items}
            record({"timestamp": datetime.now(timezone.utc).isoformat(), "paper": stem, "source": src,
                    "doc_ref": doc_ref(d["file"].name), "model": r["model"],
                    "input_tokens": r["usage"].get("input_tokens"), "output_tokens": r["usage"].get("output_tokens"),
                    "est_cost_usd": r["cost"], "elapsed_seconds": r["elapsed"], "n_items": len(items)})
            print(f"  {len(items)} items, {sum(x['anchor_verified'] for x in items)} anchors verified (${r['cost']:.3f})")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(rec, indent=2, ensure_ascii=False))
    write_long()


def write_long() -> None:
    rows = []
    for f in sorted((OUT_DIR / "items").glob("*.json")):
        rec = json.loads(f.read_text())
        for src, s in rec["sources"].items():
            for it in s.get("items", []):
                rows.append({"paper": rec["paper"], "source": src, "role": s.get("role", ""), **{k: it[k] for k in
                             ("id", "about", "problem", "consequence", "anchor_quote", "reviewer_severity", "minor", "anchor_verified")}})
    if rows:
        with (OUT_DIR / "items_long.csv").open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
    print(f"items_long.csv: {len(rows)} items")


def dump_clean(stem: str, src: str, dest: pathlib.Path) -> None:
    """Write the cleaned text for one source (for hand spot checks; not committed)."""
    docs = load_docs()
    srcs, pats = sources_for(stem, docs)
    d = dict(srcs)[src]
    dest.write_text(clean_text(d["text"], pats))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("manifest")
    e = sub.add_parser("extract")
    e.add_argument("--paper", action="append")
    e.add_argument("--status", default="eligible_pair,single_report", help="Manifest statuses to extract")
    e.add_argument("--no-em", action="store_true", help="Skip evaluation-manager summaries")
    e.add_argument("--budget", type=float, default=8.0)
    e.add_argument("--force", action="store_true")
    dc = sub.add_parser("dump-clean")
    dc.add_argument("paper")
    dc.add_argument("source")
    dc.add_argument("dest")
    sub.add_parser("long")
    args = ap.parse_args()
    if args.cmd == "manifest":
        rows, orphan = build_manifest()
        write_manifest(rows, orphan)
    elif args.cmd == "extract":
        with (OUT_DIR / "manifest.csv").open() as f:
            man = list(csv.DictReader(f))
        wanted = set(args.status.split(","))
        papers = args.paper or [r["paper"] for r in man if r["status"] in wanted]
        extract(papers, args.budget, not args.no_em, args.force)
    elif args.cmd == "dump-clean":
        dump_clean(args.paper, args.source, pathlib.Path(args.dest))
    elif args.cmd == "long":
        write_long()
    return 0


if __name__ == "__main__":
    sys.exit(main())
