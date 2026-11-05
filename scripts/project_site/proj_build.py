"""Rebuild the project site's HTML pages from source, check against the live deploy
manifest, then apply this session's edits (folding notices + Hypothes.is signpost).

Usage: python3 proj_build.py [--check-only]
"""
import hashlib, json, pathlib, re, subprocess, sys

REPO = "/Users/yosemite/githubs/llm-uj-research-eval"
SCR = pathlib.Path(__import__("os").environ.get("PROJ_SITE_DIR", "/tmp/uj_project_site_build"))
manifest = json.loads((SCR / "manifest.json").read_text())["files"]
PAGES = ["index.html", "proposal.html", "methods.html", "references.html",
         "results_ratings.html", "results_critiques.html", "appendix_llm_traces.html"]


def show(rev, path):
    return subprocess.run(["git", "-C", REPO, "show", f"{rev}:{path}"],
                          capture_output=True, check=True).stdout.decode("utf-8")


def sha1(s):
    return hashlib.sha1(s.encode("utf-8")).hexdigest()


oct_notice = show("54413e9", "docs/peerless_project_notice.html")
nov_notice = show("43d6037", "docs/persistent_misses_project_notice.html")
MAIN_RE = re.compile(r"<main[^>]*>")

base = {}
ok = True
for p in PAGES:
    html = show("67a6cea", f"_book/{p}")
    if p in ("index.html", "proposal.html"):
        m = MAIN_RE.search(html)
        html = html[:m.end()] + "\n" + oct_notice.strip() + "\n" + html[m.end():]
        m = MAIN_RE.search(html)
        html = html[:m.end()] + "\n" + nov_notice.strip() + html[m.end():]
    match = sha1(html) == manifest["/" + p]
    ok &= match
    print(f"{p}: rebuilt matches live = {match}")
    base[p] = html

if not ok or "--check-only" in sys.argv:
    sys.exit(0 if ok else 1)

# ---- edits ----
SIGNPOST = """<p class="uj-hypothesis-signpost" style="font-size:0.9em;color:#555;border-left:3px solid #2D9D5E;padding:0.3em 0.7em;margin:0.5em 0 1em;">Comments welcome: select any text and annotate it with <a href="https://web.hypothes.is/start/" target="_blank" rel="noopener">Hypothes.is</a> (the sidebar at the top right). Annotations are public. This is a historical project page; the <a href="https://llm-uj-research-eval.netlify.app/">current working paper</a> has the latest results.</p>"""

HYP_EMBED = '<script async src="https://hypothes.is/embed.js"></script>'

DETAILS_CSS = """<style>
details.uj-notice{border:1px solid #cfe3d8;border-left:4px solid #2D9D5E;border-radius:4px;padding:0.4em 0.9em;margin:0.6em 0;background:rgba(45,157,94,0.04);}
details.uj-notice > summary{cursor:pointer;}
details.uj-notice[open] > summary{margin-bottom:0.4em;}
</style>"""


def fold_notice(html, aside_id, summary_hint):
    """Turn an <aside id=...> callout whose first <p><strong>..</strong></p> is the title
    into a closed <details> box whose summary is that title plus a short hint."""
    pat = re.compile(r'<aside id="' + aside_id + r'"[^>]*>(.*?)</aside>', re.S)
    m = pat.search(html)
    if not m:
        raise SystemExit(f"notice {aside_id} not found")
    inner = m.group(1)
    t = re.search(r"<p><strong>(.*?)</strong></p>", inner, re.S)
    title = t.group(1)
    body = inner.replace(t.group(0), "", 1)
    body = re.sub(r'^\s*<div class="callout-body-container callout-body">', "", body)
    body = re.sub(r"</div>\s*$", "", body)
    new = (f'<details id="{aside_id}" class="uj-notice">\n<summary><strong>{title}</strong>'
           f' <span style="font-size:0.9em;">{summary_hint}</span></summary>\n{body.strip()}\n</details>')
    return html[:m.start()] + new + html[m.end():]


out = {}
for p, html in base.items():
    if p in ("index.html", "proposal.html"):
        html = fold_notice(html, "persistent-misses-update", "(click to expand)")
        oct_id = re.search(r'<aside id="([^"]+)"', oct_notice).group(1)
        html = fold_notice(html, oct_id, "(click to expand)")
        html = html.replace("</head>", DETAILS_CSS + "\n</head>", 1)
    m = MAIN_RE.search(html)
    html = html[:m.end()] + "\n" + SIGNPOST + "\n" + html[m.end():]
    if "hypothes.is/embed.js" not in html:
        html = html.replace("</head>", HYP_EMBED + "\n</head>", 1)
    out[p] = html
    dest = SCR / "new" / p
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(html, encoding="utf-8")
    print(f"{p}: new sha {sha1(html)}")
