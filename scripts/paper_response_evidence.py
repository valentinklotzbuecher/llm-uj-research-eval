#!/usr/bin/env python3
"""Build an auditable evidence queue for paper-response analysis.

This pipeline deliberately stops before causal attribution. It:

1. registers stable paper IDs and known evaluation documents;
2. preserves immutable before/after PDF snapshots by SHA-256;
3. validates paper identity from extracted title/author text;
4. emits page-anchored deterministic change cards; and
5. creates a review queue for optional bounded agent review and humans.

Public source retrieval uses direct PDF URLs where available. For other DOI
landing pages, a local headless Chrome resolver can inspect citation metadata;
this avoids metadata/model API calls and works with ordinary public webpages.
"""

from __future__ import annotations

import argparse
import csv
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin, urlparse

import pdfplumber
import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
CSV_PATH = DATA_DIR / "author_adjustment_manual.csv"
PAPERS_DIR = ROOT / "papers"
LEGACY_LATEST_DIR = DATA_DIR / "latest_papers"
EVALS_DIR = DATA_DIR / "unjournal_evaluations"
EVIDENCE_DIR = DATA_DIR / "paper_response_evidence"
SNAPSHOT_DIR = EVIDENCE_DIR / "snapshots"
EXTRACTED_DIR = EVIDENCE_DIR / "extracted"
COMPARISON_DIR = EVIDENCE_DIR / "comparisons"
REGISTRY_PATH = EVIDENCE_DIR / "registry.json"
QUEUE_PATH = EVIDENCE_DIR / "review_queue.json"
REPORT_PATH = EVIDENCE_DIR / "last_run_report.json"

DEFAULT_CHROME_PATHS = [
    Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
    Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
]

USER_AGENT = "Unjournal paper-response evidence monitor/2.0 (public research sources)"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": USER_AGENT})
_FIRST_PAGES_CACHE: dict[Path, str] = {}

SECTION_WORDS = {
    "abstract", "introduction", "background", "data", "methods", "method",
    "results", "discussion", "conclusion", "conclusions", "limitations",
    "appendix", "references", "bibliography", "robustness", "analysis",
}
HIGH_VALUE_SECTIONS = {
    "abstract", "methods", "method", "results", "discussion", "conclusion",
    "conclusions", "robustness", "analysis",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text())


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize_doi(raw: str) -> str:
    if not raw:
        return ""
    value = raw.strip().replace(" ", "")
    value = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", value, flags=re.I)
    value = re.sub(r"^doi:\s*", "", value, flags=re.I)
    return value.rstrip("/.,")


def slugify(value: str, limit: int = 48) -> str:
    value = value.casefold().encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value[:limit].rstrip("-") or "paper"


def stable_paper_id(title: str, doi: str = "") -> str:
    canonical = normalize_doi(doi).casefold() or re.sub(r"\s+", " ", title.casefold()).strip()
    digest = hashlib.sha256(canonical.encode()).hexdigest()[:10]
    return f"{slugify(title, 38)}-{digest}"


def first_author_last(authors: str) -> str:
    first = (authors or "").split(",")[0].strip()
    return first.split()[-1].casefold() if first else ""


def title_tokens(title: str) -> set[str]:
    stop = {"a", "an", "and", "of", "on", "in", "the", "to", "for", "from", "with", "vs"}
    return {
        token for token in re.findall(r"[a-z0-9]+", title.casefold())
        if len(token) > 2 and token not in stop
    }


def identity_score(title: str, authors: str, extracted_text: str) -> dict[str, Any]:
    expected = title_tokens(title)
    observed = set(re.findall(r"[a-z0-9]+", extracted_text[:15000].casefold()))
    title_coverage = len(expected & observed) / max(len(expected), 1)
    surname = first_author_last(authors)
    author_found = bool(surname and surname in observed)
    score = round(0.82 * title_coverage + 0.18 * float(author_found), 3)
    if score >= 0.72:
        status = "verified"
    elif score >= 0.48:
        status = "needs_review"
    else:
        status = "mismatch"
    return {
        "score": score,
        "status": status,
        "title_token_coverage": round(title_coverage, 3),
        "first_author_found": author_found,
    }


def nber_url(doi: str) -> str | None:
    match = re.match(r"^10\.3386/w(\d+)$", normalize_doi(doi), re.I)
    if not match:
        return None
    number = match.group(1)
    return f"https://www.nber.org/system/files/working_papers/w{number}/w{number}.pdf"


def arxiv_url(doi: str) -> str | None:
    match = re.search(r"arxiv\.(\d{4}\.\d+)", normalize_doi(doi), re.I)
    return f"https://arxiv.org/pdf/{match.group(1)}" if match else None


def source_url_for_doi(doi: str) -> str:
    return nber_url(doi) or arxiv_url(doi) or (f"https://doi.org/{normalize_doi(doi)}" if doi else "")


def find_chrome() -> Path | None:
    for binary in ("google-chrome", "chromium", "chromium-browser"):
        found = shutil.which(binary)
        if found:
            return Path(found)
    return next((path for path in DEFAULT_CHROME_PATHS if path.exists()), None)


def pdf_link_from_html(html: str, base_url: str) -> str | None:
    soup = BeautifulSoup(html, "html.parser")
    for key in ("citation_pdf_url", "eprints.document_url", "dc.identifier"):
        tag = soup.find("meta", attrs={"name": re.compile(f"^{re.escape(key)}$", re.I)})
        if tag and tag.get("content"):
            candidate = urljoin(base_url, tag["content"])
            if candidate.casefold().endswith(".pdf") or "pdf" in candidate.casefold():
                return candidate
    for tag in soup.find_all("a", href=True):
        href = urljoin(base_url, tag["href"])
        label = tag.get_text(" ", strip=True).casefold()
        if href.casefold().endswith(".pdf") or label in {"pdf", "download pdf", "full text pdf"}:
            return href
    return None


def resolve_with_headless_chrome(url: str, timeout: int = 15) -> dict[str, Any]:
    chrome = find_chrome()
    if not chrome:
        return {"status": "unavailable", "reason": "Chrome/Chromium not found"}
    with tempfile.TemporaryDirectory(prefix="uj-paper-browser-") as profile_dir:
        cmd = [
            str(chrome), "--headless=new", "--disable-gpu", "--disable-extensions",
            "--disable-background-networking", "--no-first-run", "--no-default-browser-check",
            "--virtual-time-budget=5000",
            f"--user-data-dir={profile_dir}",
            "--dump-dom", url,
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        timed_out = False
        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            # Current macOS Chrome can emit a complete DOM and then keep its
            # headless parent alive. Preserve the DOM, terminate the isolated
            # temporary-profile process, and validate the result below.
            timed_out = True
            proc.terminate()
            try:
                stdout, stderr = proc.communicate(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                stdout, stderr = proc.communicate()
    if proc.returncode not in (0, -15) and not stdout.strip():
        return {"status": "failed", "reason": stderr[-500:]}
    pdf_url = pdf_link_from_html(stdout, url)
    return {
        "status": "success" if pdf_url else "not_found",
        "pdf_url": pdf_url,
        "browser": str(chrome),
        "terminated_after_dom": timed_out,
        "stderr_tail": stderr[-500:],
    }


def fetch_public_pdf(source_url: str, browser_mode: str = "auto", timeout: int = 60) -> dict[str, Any]:
    """Fetch a public PDF, using a browser to resolve non-direct landing pages."""
    if not source_url:
        return {"status": "skipped", "reason": "no source URL"}
    candidate_url = source_url
    resolver: dict[str, Any] | None = None
    direct_hint = source_url.casefold().endswith(".pdf") or "arxiv.org/pdf/" in source_url.casefold()
    if not direct_hint and browser_mode in {"auto", "always"}:
        resolver = resolve_with_headless_chrome(source_url)
        if resolver.get("pdf_url"):
            candidate_url = resolver["pdf_url"]
    try:
        response = SESSION.get(candidate_url, timeout=timeout, allow_redirects=True)
        response.raise_for_status()
    except requests.RequestException as exc:
        return {
            "status": "failed", "source_url": source_url, "resolved_url": candidate_url,
            "resolver": resolver, "reason": str(exc),
        }
    content = response.content
    content_type = response.headers.get("Content-Type", "")
    if not content.startswith(b"%PDF"):
        pdf_url = pdf_link_from_html(response.text, response.url)
        if pdf_url and pdf_url != candidate_url:
            try:
                pdf_response = SESSION.get(pdf_url, timeout=timeout, allow_redirects=True)
                pdf_response.raise_for_status()
                content = pdf_response.content
                response = pdf_response
                candidate_url = pdf_url
                content_type = response.headers.get("Content-Type", "")
            except requests.RequestException as exc:
                return {
                    "status": "failed", "source_url": source_url, "resolved_url": pdf_url,
                    "resolver": resolver, "reason": str(exc),
                }
    if not content.startswith(b"%PDF"):
        return {
            "status": "failed", "source_url": source_url, "resolved_url": candidate_url,
            "resolver": resolver, "content_type": content_type,
            "reason": "resolved content is not a PDF",
        }
    return {
        "status": "success", "content": content, "source_url": source_url,
        "resolved_url": response.url, "content_type": content_type,
        "etag": response.headers.get("ETag"),
        "last_modified": response.headers.get("Last-Modified"),
        "resolver": resolver,
    }


def extract_pages(pdf_path: Path) -> list[dict[str, Any]]:
    pdftotext = shutil.which("pdftotext")
    if pdftotext:
        with tempfile.NamedTemporaryFile(suffix=".txt") as output:
            proc = subprocess.run(
                [pdftotext, "-layout", "-enc", "UTF-8", str(pdf_path), output.name],
                capture_output=True, text=True, check=False, timeout=180,
            )
            if proc.returncode == 0:
                text = Path(output.name).read_text(errors="replace")
                raw_pages = text.split("\f")
                if raw_pages and not raw_pages[-1].strip():
                    raw_pages.pop()
                return [{"page": index, "text": page} for index, page in enumerate(raw_pages, start=1)]
    pages: list[dict[str, Any]] = []
    with pdfplumber.open(pdf_path) as pdf:
        for number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text(x_tolerance=2, y_tolerance=3) or ""
            pages.append({"page": number, "text": text})
    return pages


def first_pages_text(pdf_path: Path, max_pages: int = 2) -> str:
    """Extract and memoize only the opening pages used for identity matching."""
    if pdf_path in _FIRST_PAGES_CACHE:
        return _FIRST_PAGES_CACHE[pdf_path]
    pdftotext = shutil.which("pdftotext")
    text = ""
    if pdftotext:
        with tempfile.NamedTemporaryFile(suffix=".txt") as output:
            proc = subprocess.run(
                [pdftotext, "-layout", "-enc", "UTF-8", "-f", "1", "-l", str(max_pages), str(pdf_path), output.name],
                capture_output=True, text=True, check=False, timeout=60,
            )
            if proc.returncode == 0:
                text = Path(output.name).read_text(errors="replace")
    if not text:
        pages: list[str] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages[:max_pages]:
                pages.append(page.extract_text(x_tolerance=2, y_tolerance=3) or "")
        text = "\n".join(pages)
    _FIRST_PAGES_CACHE[pdf_path] = text
    return text


def extraction_for_snapshot(snapshot_path: Path, sha256: str) -> dict[str, Any]:
    cache_path = EXTRACTED_DIR / f"{sha256}.json"
    if cache_path.exists():
        return load_json(cache_path, {})
    try:
        pages = extract_pages(snapshot_path)
        payload = {
            "sha256": sha256, "extractor": "pdftotext-layout-or-pdfplumber-fallback",
            "extractor_version": getattr(pdfplumber, "__version__", "unknown"),
            "created_at": utc_now(), "page_count": len(pages), "pages": pages,
            "quality": "ok" if sum(len(p["text"]) for p in pages) >= 1000 else "low_text",
        }
    except Exception as exc:
        payload = {
            "sha256": sha256, "extractor": "pdfplumber", "created_at": utc_now(),
            "page_count": 0, "pages": [], "quality": "failed", "error": str(exc),
        }
    write_json(cache_path, payload)
    return payload


def store_snapshot(
    paper_id: str,
    content: bytes,
    role: str,
    source: dict[str, Any],
    registry_entry: dict[str, Any],
) -> dict[str, Any]:
    if not content.startswith(b"%PDF"):
        raise ValueError("snapshot content is not a PDF")
    sha = sha256_bytes(content)
    paper_dir = SNAPSHOT_DIR / paper_id
    paper_dir.mkdir(parents=True, exist_ok=True)
    path = paper_dir / f"{sha}.pdf"
    if not path.exists():
        path.write_bytes(content)
    now = utc_now()
    versions = registry_entry.setdefault("versions", [])
    existing = next((version for version in versions if version["sha256"] == sha), None)
    event = {
        "retrieved_at": now,
        "role": role,
        "source_url": source.get("source_url"),
        "resolved_url": source.get("resolved_url"),
        "etag": source.get("etag"),
        "last_modified": source.get("last_modified"),
        "retrieval_method": source.get("retrieval_method", "local"),
    }
    if existing:
        existing["last_seen_at"] = now
        existing.setdefault("roles", [])
        if role not in existing["roles"]:
            existing["roles"].append(role)
        existing.setdefault("retrieval_events", []).append(event)
        version = existing
    else:
        version = {
            "version_id": sha[:16], "sha256": sha,
            "snapshot_path": str(path.relative_to(ROOT)), "size_bytes": len(content),
            "first_seen_at": now, "last_seen_at": now, "roles": [role],
            "retrieval_events": [event],
        }
        versions.append(version)
    extraction = extraction_for_snapshot(path, sha)
    version["extraction"] = {
        "path": str((EXTRACTED_DIR / f"{sha}.json").relative_to(ROOT)),
        "quality": extraction.get("quality"), "page_count": extraction.get("page_count"),
    }
    return version


def candidate_before_pdfs(authors: str, title: str) -> list[Path]:
    surname = slugify(first_author_last(authors), 60)
    title_words = title_tokens(title)
    candidates: list[tuple[float, Path]] = []
    for path in PAPERS_DIR.glob("*.pdf"):
        normalized_stem = slugify(path.stem, 200)
        surname_hit = surname and surname in normalized_stem.split("-")
        stem_words = set(normalized_stem.split("-"))
        overlap = len(title_words & stem_words) / max(len(title_words), 1)
        score = 0.7 * float(surname_hit) + 0.3 * overlap
        if surname_hit or overlap >= 0.25:
            candidates.append((score, path))
    return [path for _, path in sorted(candidates, key=lambda pair: (-pair[0], pair[1].name))]


def choose_before_pdf(row: dict[str, str]) -> dict[str, Any]:
    candidates = candidate_before_pdfs(row.get("authors", ""), row.get("label_paper_title", ""))
    scored: list[dict[str, Any]] = []
    for path in candidates[:8]:
        try:
            text = first_pages_text(path)
            identity = identity_score(row.get("label_paper_title", ""), row.get("authors", ""), text)
        except Exception as exc:
            identity = {"score": 0.0, "status": "mismatch", "error": str(exc)}
        scored.append({"path": str(path.relative_to(ROOT)), "identity": identity})
    scored.sort(key=lambda item: item["identity"]["score"], reverse=True)
    selected = scored[0] if scored else None
    ambiguous = bool(len(scored) > 1 and selected and scored[1]["identity"]["score"] >= selected["identity"]["score"] - 0.05)
    return {"selected": selected, "candidates": scored, "ambiguous": ambiguous}


def looks_like_heading(line: str) -> bool:
    stripped = re.sub(r"^\d+(?:\.\d+)*\s*", "", line.strip())
    words = re.findall(r"[A-Za-z]+", stripped)
    if not words or len(words) > 14 or len(stripped) > 110:
        return False
    lower = " ".join(word.casefold() for word in words)
    return lower in SECTION_WORDS or stripped.isupper() or bool(re.match(r"^(abstract|introduction|methods?|results?|discussion|conclusions?|references|appendix)\b", lower))


def page_chunks(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chunks: list[dict[str, Any]] = []
    current_section = "unknown"
    for page in pages:
        buffer: list[str] = []
        for raw_line in page.get("text", "").splitlines() + [""]:
            line = raw_line.strip()
            if looks_like_heading(line):
                if buffer:
                    chunks.append(_make_chunk(page["page"], current_section, buffer))
                    buffer = []
                current_section = re.sub(r"^\d+(?:\.\d+)*\s*", "", line).strip().casefold()
                continue
            if not line:
                if sum(len(item) for item in buffer) >= 180:
                    chunks.append(_make_chunk(page["page"], current_section, buffer))
                    buffer = []
                continue
            if re.fullmatch(r"\d+", line):
                continue
            buffer.append(line)
            if sum(len(item) for item in buffer) >= 900:
                chunks.append(_make_chunk(page["page"], current_section, buffer))
                buffer = []
        if buffer:
            chunks.append(_make_chunk(page["page"], current_section, buffer))
    return [chunk for chunk in chunks if len(chunk["normalized"]) >= 80]


def _make_chunk(page: int, section: str, lines: list[str]) -> dict[str, Any]:
    text = " ".join(lines)
    normalized = re.sub(r"\s+", " ", re.sub(r"[^\w.%+-]", " ", text.casefold())).strip()
    return {"page": page, "section": section, "text": text, "normalized": normalized}


def numbers(text: str) -> list[str]:
    return re.findall(r"(?<!\w)[+-]?(?:\d+\.\d+|\d+)(?:%|\b)", text)


def change_cards(before_pages: list[dict[str, Any]], after_pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    before = page_chunks(before_pages)
    after = page_chunks(after_pages)
    matcher = difflib.SequenceMatcher(
        None, [chunk["normalized"] for chunk in before],
        [chunk["normalized"] for chunk in after], autojunk=False,
    )
    cards: list[dict[str, Any]] = []
    for opcode_index, (tag, i1, i2, j1, j2) in enumerate(matcher.get_opcodes(), start=1):
        if tag == "equal":
            continue
        old_chunks = before[i1:i2]
        new_chunks = after[j1:j2]
        old_text = "\n".join(chunk["text"] for chunk in old_chunks)
        new_text = "\n".join(chunk["text"] for chunk in new_chunks)
        section = (new_chunks or old_chunks or [{"section": "unknown"}])[0]["section"]
        old_words = re.findall(r"\w+", old_text)
        new_words = re.findall(r"\w+", new_text)
        # Word-level matching is substantially faster and less sensitive to PDF
        # line wrapping than character-level matching. Cap unusually large
        # replacement blocks; page/section excerpts remain available for review.
        ratio = difflib.SequenceMatcher(
            None,
            [word.casefold() for word in old_words[:2500]],
            [word.casefold() for word in new_words[:2500]],
            autojunk=True,
        ).ratio()
        old_numbers = numbers(old_text)
        new_numbers = numbers(new_text)
        number_changed = old_numbers != new_numbers
        word_scale = min(max(len(old_words), len(new_words)) / 120, 1.0)
        score = (1 - ratio) * word_scale
        if number_changed:
            score += 0.25
        if any(word in section for word in HIGH_VALUE_SECTIONS):
            score += 0.15
        if "reference" in section or "bibliograph" in section:
            score -= 0.55
        pages = [chunk["page"] for chunk in old_chunks + new_chunks]
        if pages and min(pages) <= 1 and section == "unknown":
            score -= 0.2
        score = round(max(0.0, min(score, 1.0)), 3)
        material = score >= 0.25 and max(len(old_words), len(new_words)) >= 20
        card_id = f"chg-{opcode_index:04d}"
        cards.append({
            "card_id": card_id, "operation": tag, "section": section,
            "before_pages": sorted({chunk["page"] for chunk in old_chunks}),
            "after_pages": sorted({chunk["page"] for chunk in new_chunks}),
            "before_excerpt": old_text[:1400], "after_excerpt": new_text[:1400],
            "before_word_count": len(old_words), "after_word_count": len(new_words),
            "before_numbers": old_numbers[:40], "after_numbers": new_numbers[:40],
            "numeric_change": number_changed, "text_similarity": round(ratio, 3),
            "materiality_score": score, "material": material,
        })
    return cards


def public_document_mapping(pubpub_url: str) -> dict[str, Any]:
    slug_match = re.search(r"unjournal\.pubpub\.org/pub/([^/?#]+)", pubpub_url or "", re.I)
    if not slug_match:
        return {"status": "unmapped", "evaluation_files": [], "public_response_files": []}
    summary_slug = slug_match.group(1)
    summary_path = EVALS_DIR / f"{summary_slug}.md"
    if not summary_path.exists():
        return {
            "status": "needs_review", "summary_slug": summary_slug,
            "evaluation_files": [], "public_response_files": [],
            "reason": "exact PubPub summary export not found",
        }
    text = summary_path.read_text(errors="replace")
    linked_slugs = sorted(set(re.findall(r"unjournal\.pubpub\.org/pub/([^/?#\"')]+)", text, re.I)))
    evaluation_files = [summary_path]
    response_files: list[Path] = []
    for slug in linked_slugs:
        path = EVALS_DIR / f"{slug}.md"
        if not path.exists() or path == summary_path:
            continue
        head = path.read_text(errors="replace")[:2500]
        if re.search(r"author.?s?\s+response|response\s+to", head, re.I):
            response_files.append(path)
        else:
            evaluation_files.append(path)
    return {
        "status": "exact_pubpub_mapping",
        "summary_slug": summary_slug,
        "evaluation_files": [str(path.relative_to(ROOT)) for path in evaluation_files],
        "public_response_files": [str(path.relative_to(ROOT)) for path in response_files],
    }


def compare_versions(paper: dict[str, Any], before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    before_extract = load_json(ROOT / before["extraction"]["path"], {})
    after_extract = load_json(ROOT / after["extraction"]["path"], {})
    comparison_id = hashlib.sha256(
        f"{paper['paper_id']}:{before['sha256']}:{after['sha256']}:change-card-v1".encode()
    ).hexdigest()[:20]
    cards = change_cards(before_extract.get("pages", []), after_extract.get("pages", []))
    material_cards = [card for card in cards if card["material"]]
    payload = {
        "comparison_id": comparison_id, "paper_id": paper["paper_id"],
        "paper_title": paper["title"], "created_at": utc_now(),
        "algorithm": "page-chunk-sequence-diff-v1",
        "before_version_id": before["version_id"], "before_sha256": before["sha256"],
        "after_version_id": after["version_id"], "after_sha256": after["sha256"],
        "before_extraction_quality": before["extraction"]["quality"],
        "after_extraction_quality": after["extraction"]["quality"],
        "summary": {
            "all_change_cards": len(cards), "material_change_cards": len(material_cards),
            "numeric_change_cards": sum(card["numeric_change"] for card in material_cards),
            "sections_changed": sorted({card["section"] for card in material_cards}),
        },
        "change_cards": cards,
    }
    path = COMPARISON_DIR / f"{comparison_id}.json"
    write_json(path, payload)
    payload["comparison_path"] = str(path.relative_to(ROOT))
    return payload


def legacy_latest_for_entry(entry: dict[str, Any]) -> Path | None:
    for version in reversed(entry.get("versions", [])):
        for event in reversed(version.get("retrieval_events", [])):
            legacy = event.get("legacy_path")
            if legacy and (ROOT / legacy).exists():
                return ROOT / legacy
    return None


def run_pipeline(args: argparse.Namespace) -> dict[str, Any]:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    registry = load_json(REGISTRY_PATH, {"schema_version": 1, "papers": {}, "runs": []})
    queue: list[dict[str, Any]] = []
    report = {
        "started_at": utc_now(), "network_enabled": not args.no_network,
        "browser_resolve": args.browser_resolve, "papers_total": 0,
        "after_snapshots_available": 0, "comparisons_created": 0,
        "ready_for_agent_triage": 0, "needs_human_validation": 0,
        "errors": [],
    }
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if getattr(args, "paper_id", None):
        rows = [
            row for row in rows
            if stable_paper_id(row.get("label_paper_title", ""), row.get("doi", "")) == args.paper_id
        ]
        if not rows:
            raise SystemExit(f"Paper ID not found: {args.paper_id}")
    report["papers_total"] = len(rows)
    legacy_manifest = load_json(DATA_DIR / "paper_fetch_manifest.json", {})

    for row in rows:
        title = (row.get("label_paper_title") or "").strip()
        if not title:
            continue
        doi = normalize_doi(row.get("doi", ""))
        paper_id = stable_paper_id(title, doi)
        entry = registry["papers"].setdefault(paper_id, {"paper_id": paper_id, "versions": []})
        entry.update({
            "title": title, "authors": row.get("authors", ""), "doi": doi,
            "pubpub_url": row.get("dup_pubpub_final_links", ""),
            "unjournal_publication_date": row.get("publication_date_unjournal", ""),
            "manual_adjustment_status": row.get("Adjusted_paper?", ""),
        })
        entry["public_documents"] = public_document_mapping(entry["pubpub_url"])
        review_reasons: list[str] = []

        before_choice = choose_before_pdf(row)
        entry["before_selection"] = before_choice
        before_version = None
        if before_choice.get("selected"):
            before_path = ROOT / before_choice["selected"]["path"]
            before_version = store_snapshot(
                paper_id, before_path.read_bytes(), "before_evaluation",
                {"retrieval_method": "local_input", "source_url": None}, entry,
            )
            before_version["identity"] = before_choice["selected"]["identity"]
            entry["selected_before_version_id"] = before_version["version_id"]
            if before_choice["ambiguous"]:
                review_reasons.append("ambiguous_before_version")
            if before_version["identity"]["status"] != "verified":
                review_reasons.append("before_identity_not_verified")
        else:
            review_reasons.append("before_version_missing")

        source_url = source_url_for_doi(doi)
        fetch_result: dict[str, Any] = {"status": "skipped", "reason": "network disabled"}
        content: bytes | None = None
        if source_url and not args.no_network:
            fetch_result = fetch_public_pdf(source_url, args.browser_resolve)
            if fetch_result["status"] == "success":
                content = fetch_result.pop("content")
                fetch_result["retrieval_method"] = (
                    "headless_browser_resolved_http" if fetch_result.get("resolver") else "direct_http"
                )

        legacy_entry = next(
            (item for item in legacy_manifest.values() if item.get("paper_title", "").strip() == title),
            None,
        )
        legacy_path = ROOT / legacy_entry["after_pdf"] if legacy_entry and legacy_entry.get("after_pdf") else None
        if content is None and legacy_path and legacy_path.exists():
            content = legacy_path.read_bytes()
            fetch_result = {
                "status": "success", "retrieval_method": "legacy_local_cache",
                "source_url": source_url, "resolved_url": None,
                "legacy_path": str(legacy_path.relative_to(ROOT)),
                "network_failure": fetch_result if fetch_result.get("status") == "failed" else None,
            }
        after_version = None
        if content is not None and content.startswith(b"%PDF"):
            after_version = store_snapshot(paper_id, content, "candidate_post_evaluation", fetch_result, entry)
            after_extract = load_json(ROOT / after_version["extraction"]["path"], {})
            first_text = "\n".join(page.get("text", "") for page in after_extract.get("pages", [])[:2])
            after_version["identity"] = identity_score(title, entry["authors"], first_text)
            entry["selected_after_version_id"] = after_version["version_id"]
            entry["source_url"] = source_url
            report["after_snapshots_available"] += 1
            if after_version["identity"]["status"] != "verified":
                review_reasons.append("after_identity_not_verified")
        elif source_url:
            review_reasons.append("after_version_fetch_failed")
            if fetch_result.get("status") == "failed":
                report["errors"].append({"paper_id": paper_id, "error": fetch_result.get("reason")})
        else:
            review_reasons.append("no_supported_public_source")

        timeline_status = "metadata_claim_post_evaluation" if str(row.get("deposit date > unjournal pub date", "")).casefold() == "true" else "needs_review"
        entry["timeline_status"] = timeline_status
        if timeline_status != "metadata_claim_post_evaluation":
            review_reasons.append("timeline_not_verified")

        comparison = None
        if before_version and after_version and before_version["sha256"] != after_version["sha256"]:
            comparison = compare_versions(entry, before_version, after_version)
            entry["latest_comparison_id"] = comparison["comparison_id"]
            report["comparisons_created"] += 1
        elif before_version and after_version:
            review_reasons.append("before_after_hashes_identical")

        material_count = comparison["summary"]["material_change_cards"] if comparison else 0
        if not material_count:
            review_reasons.append("no_material_change_cards")
        docs = entry["public_documents"]
        if docs["status"] != "exact_pubpub_mapping":
            review_reasons.append("evaluation_documents_not_exactly_mapped")

        hard_blockers = {
            "ambiguous_before_version", "before_identity_not_verified", "before_version_missing",
            "after_identity_not_verified", "after_version_fetch_failed", "timeline_not_verified",
            "evaluation_documents_not_exactly_mapped",
        }
        ready = bool(comparison and material_count and not (set(review_reasons) & hard_blockers))
        queue_status = "ready_for_agent_triage" if ready else "needs_human_validation"
        report[queue_status] += 1
        queue.append({
            "paper_id": paper_id, "paper_title": title, "status": queue_status,
            "review_reasons": sorted(set(review_reasons)),
            "comparison_id": comparison["comparison_id"] if comparison else None,
            "comparison_path": comparison.get("comparison_path") if comparison else None,
            "material_change_cards": material_count,
            "evaluation_files": docs.get("evaluation_files", []),
            "public_response_files": docs.get("public_response_files", []),
            "human_decision_required": True,
        })

    registry["updated_at"] = utc_now()
    registry["runs"].append({
        "completed_at": registry["updated_at"], "report_path": str(REPORT_PATH.relative_to(ROOT)),
        "network_enabled": not args.no_network, "browser_resolve": args.browser_resolve,
    })
    registry["runs"] = registry["runs"][-50:]
    report["completed_at"] = utc_now()
    write_json(REGISTRY_PATH, registry)
    if getattr(args, "paper_id", None) and QUEUE_PATH.exists():
        existing_items = load_json(QUEUE_PATH, {}).get("items", [])
        queue_by_id = {item["paper_id"]: item for item in existing_items}
        queue_by_id.update({item["paper_id"]: item for item in queue})
        queue = list(queue_by_id.values())
    write_json(QUEUE_PATH, {"created_at": utc_now(), "items": queue})
    write_json(REPORT_PATH, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    refresh = subparsers.add_parser("refresh", help="refresh snapshots and deterministic review queue")
    refresh.add_argument("--no-network", action="store_true", help="use existing local PDF cache only")
    refresh.add_argument("--paper-id", help="refresh one stable paper ID for testing or review")
    refresh.add_argument(
        "--browser-resolve", choices=("never", "auto", "always"), default="auto",
        help="use local headless Chrome for non-direct DOI landing pages",
    )
    browser_check = subparsers.add_parser("browser-check", help="verify local headless Chrome metadata resolution")
    browser_check.add_argument(
        "--url",
        default="data:text/html,<meta%20name='citation_pdf_url'%20content='https://example.org/paper.pdf'>",
    )
    args = parser.parse_args()
    if args.command == "refresh":
        report = run_pipeline(args)
        print(json.dumps(report, indent=2))
        return 0 if not report["errors"] else 2
    if args.command == "browser-check":
        result = resolve_with_headless_chrome(args.url)
        print(json.dumps(result, indent=2))
        return 0 if result.get("status") == "success" else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
