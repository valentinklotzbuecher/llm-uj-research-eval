# Hosting and public signposting

**Last updated:** 2026-07-23

The project has separate public surfaces for the current paper, broader project context, and concordance evidence. Keep these roles explicit in navigation and prose.

---

## Current state

| Site | URL | Branch | Status |
|------|-----|--------|--------|
| Primary Netlify URL | https://llm-uj-research-eval.netlify.app | `working-paper` | Current working paper |
| GitHub Pages | https://valentinklotzbuecher.github.io/llm-uj-research-eval/ | `working-paper` | Current working paper; same role as the primary Netlify URL |
| Full project workspace | https://llm-uj-research-eval-project.netlify.app | `main` / `project` snapshot | Broader project context, grant proposal, earlier analysis, goals, and team information |
| Grant proposal | https://llm-uj-research-eval-project.netlify.app/proposal.html | `main` / `project` snapshot | Direct link for grant reviewers |
| Concordance evidence | https://llm-uj-concordance-judgments.netlify.app | separate generated site | Exploratory LLM–human critique mappings and methods notes |

**Neither site auto-renders.** Both serve pre-built `_book/` HTML committed to git. To update a site: run `quarto render`, then commit `_book/`, then push. The working-paper branch is the one to update.

---

## Signposting convention

On the working paper, label the three destinations as:

1. **Current working paper** — authoritative statistical analysis.
2. **Full project and grant proposal** — broader and partly historical project context.
3. **Concordance evidence** — exploratory issue-mapping evidence, not a confirmatory result.

Never describe `https://llm-uj-research-eval.netlify.app` as the project workspace: it now serves the working paper. Link grant reviewers directly to the separate project site or its `proposal.html` page.

---

## How to update the working-paper site

After any code/analysis change on `working-paper`:

```bash
quarto render
git add _book/ _freeze/
git commit -m "Update rendered output"
git push origin working-paper
```

GitHub Pages updates automatically via GitHub Actions (~30 seconds after push).  
Netlify also updates automatically as soon as it detects the new `_book/` (~1 minute after push).

---

## Navigation maintenance

The `paper_response_analysis.qmd` page (author engagement evidence) is currently in the book's sidebar navigation but doesn't belong in the academic working paper. To remove it from the navigation while keeping the URL alive:

In `_quarto.yml` on `working-paper`, remove `paper_response_analysis.qmd` from the `appendices:` list. The page will still render and remain accessible at its URL — it just won't appear in the sidebar. A link to it in `index.qmd` (already present in a callout) is sufficient.

---

The original Netlify URL changed roles and now mirrors the working paper. The broader, partly historical project workspace remains available at its separate `-project` Netlify URL so the grant proposal and project context are not lost.

---

## October 2026 related-work update

The AI-generated comparison with King and Worthington (2026) is maintained in
`peerless_context.qmd`, with shorter notes in `index.qmd`, `discussion.qmd`,
and `proposal.qmd`, and the citation in `references.bib`. Its public destination
is <https://llm-uj-research-eval.netlify.app/peerless_context.html>. Continue the
research assessment in that source; proposed follow-up studies are not adopted
plans or completed results.

The historical project site's homepage and proposal receive the shared notice
in `docs/peerless_project_notice.html`. On October 23, the published raw versions
of those two pages matched `67a6cea:_book/index.html` and
`67a6cea:_book/proposal.html` by SHA-1. The notice is inserted immediately after
each opening `<main>` tag. Use the live Netlify file inventory as the release
baseline and preserve every other file hash. Do not replace the historical site
with the working-paper `_book/` or create another maintained manuscript branch.

For future updates, recheck that baseline before editing, render the current
paper's HTML and PDF, and verify the new text and citation on both live sites.
The historical project's Netlify site ID is
`7c50da14-8f61-4212-8928-321519e33b0e`; its configuration was confirmed to have
no connected Git repository on October 23. A source push alone does not update
that site.

## November 2026 diagnostic notice

The provisional Claude Opus 5.5 persistent-miss diagnostic is the working-paper
appendix `persistent_misses.qmd`, live at
<https://llm-uj-research-eval.netlify.app/persistent_misses.html> and on GitHub
Pages. Both hosts serve the committed `_book/` from `working-paper`.

On November 5 the historical project site's homepage and proposal received
`docs/persistent_misses_project_notice.html`. It is inserted directly after each
opening `<main>` tag, ahead of the October notice. The baseline was deploy
`6adb662fb8afa7b82547eb83` (37 files). Its `index.html` and `proposal.html` were
reproduced byte-for-byte from `67a6cea:_book/` plus the October notice from
`54413e9`, which is inserted as `"\n" + notice.strip() + "\n"`.

The new deploy `6aec619eb66fd94e660c0586` was a file-digest deploy through the
Netlify API. It replaced only those two files; the other 35 file hashes are
unchanged. Netlify rewrites served HTML (pretty URLs and an injected comment),
so live bytes do not match deployed hashes. To check a baseline, rebuild from
source; do not download the live pages.

On November 5 (later, from David's Hypothes.is comments) both notices on the
homepage and proposal became closed `<details>` boxes, and all seven HTML pages
got a one-line Hypothes.is comment signpost after `<main>` (plus the embed
script where missing). Deploy `6aec7a6d68bd934448d479c5` replaced only those
seven pages; the other 30 file hashes are unchanged. Scripts in
`scripts/project_site/`: `proj_pull.py` saves the live hash manifest,
`proj_build.py` rebuilds the baseline from git (checking every page's hash
against the manifest before editing) and applies the edits, `proj_deploy.py`
does the file-digest deploy and refuses if the live deploy has changed. The
November notice is inserted as `"\n" + notice.strip()` (no trailing newline).
To rebuild the current pages, run `proj_build.py` against the pre-change
manifest of deploy `6aec619eb66fd94e660c0586`.

## November 9 2026: current paper copied into the project site

From David's Hypothes.is comment ("make this folded. But we should also have the
updated analysis in both"): the yellow "This is the project workspace" box on the
homepage became a closed `<details>`, and the committed working-paper `_book/`
(HEAD `2ca97cf`, 78 files, minus `robots.txt` and `sitemap.xml`) is now served at
<https://llm-uj-research-eval-project.netlify.app/working-paper/>. Its pages keep
their canonical links to the main Netlify site, so Hypothes.is groups annotations
with the canonical paper. The signpost on all seven historical pages links to the
copy; the four old analysis pages (methods, ratings, critiques, LLM traces) link
to their current versions. The historical pages are otherwise unchanged.

An interim deploy, `6af1c0296b49bd4f04dc8d99` from the hypothesis-edit-live
session, folded only that box; it was reproduced byte for byte before being
replaced. The Nov 9 deploy is `6af1c0a1c5d60571b0f35058` (115 files: the 30
untouched originals, 7 edited pages, 78 paper files).

To refresh the copy after each working-paper publish, run `proj_pull.py`,
`proj_build.py` and `proj_deploy.py "title"` from `scripts/project_site/` with one
`PROJ_SITE_DIR`. The build rebuilds every historical page from git and refuses
unless each live hash matches a known state. The deploy replaces `/working-paper/`
as a whole and keeps every other file hash.

Later on November 9 the copy was refreshed from `f690d83` (headline
critique-overlap block on `results_critiques`, computed figures on the
introduction and results pages): deploy `6af1c7b03c31dc59f70af66e`, 115 files,
6 stale `/working-paper/` files dropped. The seven historical pages were
unchanged (all matched the `nov9` state).

Then, with David's OK, the historical `results_critiques.html` got the same
headline block, copied from the rendered page at `f690d83` and placed under the
page title, with a line saying it comes from the current version and that the
historical figures below may differ. Its links point into `/working-paper/`. This
is layer 3b (`nov9b`) in `proj_build.py`; the other six historical pages are
unchanged. Deploy `6af1d30de5b7ef215f5f75e5` (115 files, one new blob).

November 10 2026: the `/working-paper/` copy was refreshed from `d578da9`
(critique overlap reported as a judge-dependent range, with the revised
blinded judge). Deploy `6af3370934c3a7ec2e479d4a`, 115 files, 6 stale
`/working-paper/` files dropped; the seven historical pages matched their
`nov9`/`nov9b` states and were unchanged. The historical `results_critiques.html`
headline block was then, with David's OK, replaced by the same block from
`d578da9` (layer `nov10` in `proj_build.py`), with a lead line saying the
figures are provisional and will be re-checked after the human audit of the
judge. Deploy `6af3387c30706133a983ab1f` (115 files, one new blob). A to-do to
re-check both sites is on David's list (due 2026-12-01).

Later on November 10 the critiques headline was rewritten to lead with the
30-paper human-to-human comparison (`c5971d2`). The `/working-paper/` copy was
refreshed from that commit and the historical page's block moved to the same
version (layer `nov10b`, same lead line). Deploy `6af36b9722ad9e83eebd4946`
(115 files).

## URLs to preserve

These have been shared externally and must remain accessible:

| URL | Content | Status |
|-----|---------|--------|
| https://llm-uj-research-eval.netlify.app | Current working paper | Must stay live |
| https://llm-uj-research-eval-project.netlify.app | Full project workspace | Must stay live |
| https://llm-uj-research-eval-project.netlify.app/proposal.html | Grant proposal | Must stay live |
| https://llm-uj-concordance-judgments.netlify.app | Concordance evidence | Must stay live |
| https://valentinklotzbuecher.github.io/llm-uj-research-eval/paper_response_analysis.html | Author engagement evidence | Must stay live — shared in grant applications |
| https://valentinklotzbuecher.github.io/llm-uj-research-eval/ | Working paper | Must stay live |
