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
