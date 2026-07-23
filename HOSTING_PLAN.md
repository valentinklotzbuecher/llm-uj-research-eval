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
