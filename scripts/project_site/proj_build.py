"""Rebuild the historical project site's edited HTML pages from git, check them against
the live deploy manifest, apply the current edits, and stage a copy of the current
working paper under /working-paper/.

Layers, in order (each reproducible from git):
  1. 67a6cea:_book pages, plus the October and November notices on index/proposal.
  2. Nov 5 2026: those notices folded into <details>, Hypothes.is signpost on every page.
     -> this is what deploy 6aec7a6d68bd934448d479c5 serves; checked by hash.
  3. Nov 9 2026: the yellow "project workspace" box folded; signposts point to the
     in-site copy of the current working paper (and, on the four old analysis pages,
     to the current version of that page).
  4. /working-paper/: the committed working-paper _book/ at HEAD (canonical links
     still point to llm-uj-research-eval.netlify.app).

Usage: python3 proj_pull.py; python3 proj_build.py [--check-only]; python3 proj_deploy.py "title"
  The build refuses unless every live page matches a known rebuilt state. Once the Nov 9
  pages are live, rerunning it stages only the refreshed /working-paper/ copy.
"""
import hashlib, json, os, pathlib, re, shutil, subprocess, sys

REPO = "/Users/yosemite/githubs/llm-uj-research-eval"
SCR = pathlib.Path(os.environ.get("PROJ_SITE_DIR", "/tmp/uj_project_site_build"))
manifest = json.loads((SCR / "manifest.json").read_text())["files"]
PAGES = ["index.html", "proposal.html", "methods.html", "references.html",
         "results_ratings.html", "results_critiques.html", "appendix_llm_traces.html"]
OLD_ANALYSIS = {"methods.html", "results_ratings.html", "results_critiques.html",
                "appendix_llm_traces.html"}
WP_DIR = "working-paper"
WP_SKIP = {"robots.txt", "sitemap.xml"}


def show(rev, path):
    return subprocess.run(["git", "-C", REPO, "show", f"{rev}:{path}"],
                          capture_output=True, check=True).stdout


def sha1(s):
    return hashlib.sha1(s.encode("utf-8") if isinstance(s, str) else s).hexdigest()


oct_notice = show("54413e9", "docs/peerless_project_notice.html").decode()
nov_notice = show("43d6037", "docs/persistent_misses_project_notice.html").decode()
MAIN_RE = re.compile(r"<main[^>]*>")

# ---- layer 1 ----
base = {}
for p in PAGES:
    html = show("67a6cea", f"_book/{p}").decode()
    if p in ("index.html", "proposal.html"):
        m = MAIN_RE.search(html)
        html = html[:m.end()] + "\n" + oct_notice.strip() + "\n" + html[m.end():]
        m = MAIN_RE.search(html)
        html = html[:m.end()] + "\n" + nov_notice.strip() + html[m.end():]
    base[p] = html

# ---- layer 2 (Nov 5) ----
SIGNPOST_NOV5 = """<p class="uj-hypothesis-signpost" style="font-size:0.9em;color:#555;border-left:3px solid #2D9D5E;padding:0.3em 0.7em;margin:0.5em 0 1em;">Comments welcome: select any text and annotate it with <a href="https://web.hypothes.is/start/" target="_blank" rel="noopener">Hypothes.is</a> (the sidebar at the top right). Annotations are public. This is a historical project page; the <a href="https://llm-uj-research-eval.netlify.app/">current working paper</a> has the latest results.</p>"""

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


nov5 = {}
for p, html in base.items():
    if p in ("index.html", "proposal.html"):
        html = fold_notice(html, "persistent-misses-update", "(click to expand)")
        oct_id = re.search(r'<aside id="([^"]+)"', oct_notice).group(1)
        html = fold_notice(html, oct_id, "(click to expand)")
        html = html.replace("</head>", DETAILS_CSS + "\n</head>", 1)
    m = MAIN_RE.search(html)
    html = html[:m.end()] + "\n" + SIGNPOST_NOV5 + "\n" + html[m.end():]
    if "hypothes.is/embed.js" not in html:
        html = html.replace("</head>", HYP_EMBED + "\n</head>", 1)
    nov5[p] = html

# ---- layer 3 (Nov 9) ----
YELLOW_RE = re.compile(r'<div style="background:#fff3cd;[^"]*">.*?</div>', re.S)
WORKSPACE_DETAILS = """<details id="project-workspace-notice" class="uj-notice">
<summary><strong>This is the project workspace. The current analysis is in the working paper, also mirrored here.</strong> <span style="font-size:0.9em;">(click to expand)</span></summary>
<p>This site keeps the grant proposal, earlier analysis iterations and broader project background as they were; those pages are not updated. The current working paper, with the latest statistical analysis (corrected agreement metrics, Spearman-Brown adjustment, like-for-like comparisons, panel Krippendorff's alpha), is copied into this site at <a href="working-paper/index.html" style="font-weight:600;">working-paper/</a> and refreshed each time the paper is published. Its main home is <a href="https://llm-uj-research-eval.netlify.app/">llm-uj-research-eval.netlify.app</a>. Please cite results from the working paper.</p>
</details>"""


def signpost(p):
    if p in OLD_ANALYSIS:
        cur = (f'Historical version of this page; the <a href="{WP_DIR}/{p}">current version</a> '
               f'is in the <a href="{WP_DIR}/index.html">working paper</a> (copy on this site).')
    else:
        cur = (f'Historical project page; the <a href="{WP_DIR}/index.html">current working paper</a> '
               f'(copy on this site) has the latest results.')
    return ('<p class="uj-hypothesis-signpost" style="font-size:0.9em;color:#555;border-left:3px solid #2D9D5E;'
            'padding:0.3em 0.7em;margin:0.5em 0 1em;">Comments welcome: select any text and annotate it with '
            '<a href="https://web.hypothes.is/start/" target="_blank" rel="noopener">Hypothes.is</a> '
            f'(sidebar at the top right; annotations are public). {cur}</p>')


nov9 = {}
for p, html in nov5.items():
    html, n = YELLOW_RE.subn(WORKSPACE_DETAILS, html, count=1)
    if n and "details.uj-notice{" not in html:
        html = html.replace("</head>", DETAILS_CSS + "\n</head>", 1)
    assert html.count(SIGNPOST_NOV5) == 1, p
    html = html.replace(SIGNPOST_NOV5, signpost(p), 1)
    if p in OLD_ANALYSIS:
        assert os.path.exists(f"{REPO}/_book/{p}"), f"working paper has no {p}"
    nov9[p] = html
    print(f"{p}: workspace box folded = {bool(n)}")

# Interim state, deploy 6af1c0296b49bd4f04dc8d99 (Nov 9, from the hypothesis-edit-live
# session): Nov 5 pages with only index.html's yellow box turned into this <details>.
INTERIM_BANNER = """<details class="uj-workspace-banner" style="background:#fff3cd;border-left:5px solid #e6a817;padding:1em 1.4em;margin:0 0 1.5em 0;border-radius:3px;font-size:0.97em;">
<summary style="cursor:pointer;"><strong>This is the project workspace — for the current analysis, see the working paper.</strong></summary>
<p style="margin:0.5em 0 0;">This site contains grant proposal context, earlier analysis iterations, and broader project background,
  but is <em>not actively updated</em>. The <a href="https://llm-uj-research-eval.netlify.app/" style="font-weight:600;">current working paper</a>
  has the latest statistical analysis, corrected agreement metrics (Spearman-Brown, like-for-like comparisons,
  panel Krippendorff's alpha), and the academic presentation. Please use that version for citing results.</p>
</details>"""
interim = dict(nov5)
interim["index.html"] = YELLOW_RE.sub(lambda _: INTERIM_BANNER, nov5["index.html"], count=1)

# ---- check against live ----
# Every page must match a known state (nov5, the interim deploy, or nov9 after it ships).
ok = True
for p in PAGES:
    live = manifest["/" + p]
    state = next((n for n, d in (("nov5", nov5), ("interim", interim), ("nov9", nov9))
                  if sha1(d[p]) == live), None)
    ok &= state is not None
    print(f"{p}: live matches rebuilt state = {state}")
if not ok or "--check-only" in sys.argv:
    sys.exit(0 if ok else 1)

# ---- stage ----
out = SCR / "new"
if out.exists():
    shutil.rmtree(out)
for p, html in nov9.items():
    if sha1(html) != manifest["/" + p]:
        (out / p).parent.mkdir(parents=True, exist_ok=True)
        (out / p).write_text(html, encoding="utf-8")
        print(f"stage {p}")

# ---- layer 4: working-paper copy from committed HEAD ----
dirty = subprocess.run(["git", "-C", REPO, "status", "--porcelain", "_book"],
                       capture_output=True, text=True, check=True).stdout.strip()
if dirty:
    print("WARNING: _book/ has uncommitted changes; copying the committed HEAD version")
head = subprocess.run(["git", "-C", REPO, "rev-parse", "--short", "HEAD"],
                      capture_output=True, text=True, check=True).stdout.strip()
files = subprocess.run(["git", "-C", REPO, "ls-tree", "-r", "--name-only", "HEAD", "_book"],
                       capture_output=True, text=True, check=True).stdout.split("\n")
n = 0
for f in filter(None, files):
    rel = f[len("_book/"):]
    if rel in WP_SKIP:
        continue
    dest = out / WP_DIR / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(show("HEAD", f))
    n += 1
(SCR / "staged_from.txt").write_text(head)
print(f"staged {n} working-paper files from {head}")
