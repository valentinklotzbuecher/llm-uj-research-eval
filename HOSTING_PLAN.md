# Hosting Reconciliation Plan

**Last updated:** 2026-04-28  
**Context:** The project currently has two hosted sites that have drifted out of sync. This document explains the situation and what Valentin needs to do.

---

## Current state

| Site | URL | Branch | Status |
|------|-----|--------|--------|
| Netlify (project space) | https://llm-uj-research-eval.netlify.app | `main` | Stale — ~6 months behind. Has broader context (grant proposal, project background) but not current analysis. A notice has been added directing visitors to the working paper. |
| GitHub Pages (working paper) | https://valentinklotzbuecher.github.io/llm-uj-research-eval/ | `working-paper` | **Current** — all active development happens here. Has latest analysis, corrected agreement tables, academic presentation. |

**Neither site auto-renders.** Both serve pre-built `_book/` HTML committed to git. To update a site: run `quarto render`, then commit `_book/`, then push. The working-paper branch is the one to update.

---

## What Valentin needs to do (Phase 2 — the key action)

### Switch Netlify to deploy from `working-paper`

This is a single setting change. It makes the grant-application URL (`llm-uj-research-eval.netlify.app`) show the current analysis permanently, without any further manual synchronisation.

**Steps:**
1. Log in to [netlify.com](https://netlify.com) and open the `llm-uj-research-eval` site
2. Go to **Site configuration → Build & deploy → Branches and deploy contexts**
3. Under **Production branch**, change `main` → `working-paper`
4. Click **Save** — Netlify will immediately re-deploy from the current `_book/` in `working-paper`
5. Verify at https://llm-uj-research-eval.netlify.app — should now show "Just Ask the Model..." title and current results

That's it. After this change:
- Both URLs serve the same content from the same branch
- Only one branch (`working-paper`) needs to be maintained
- The `main` branch becomes an archive (do not delete — historical record)

---

## How to update the site going forward (after Phase 2)

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

## Phase 3 — Clean up navigation (optional, low priority)

The `paper_response_analysis.qmd` page (author engagement evidence) is currently in the book's sidebar navigation but doesn't belong in the academic working paper. To remove it from the navigation while keeping the URL alive:

In `_quarto.yml` on `working-paper`, remove `paper_response_analysis.qmd` from the `appendices:` list. The page will still render and remain accessible at its URL — it just won't appear in the sidebar. A link to it in `index.qmd` (already present in a callout) is sufficient.

---

## Background: why two sites exist

The original intent was:
- **Netlify** = full project workspace (grant context, exploratory analysis, team info)
- **GitHub Pages** = clean self-contained working paper for academic sharing

In practice, all active development moved to the `working-paper` branch and `main` was never kept up to date. The two-branch setup added maintenance overhead without meaningful benefit. Phase 2 above collapses them back to one.

---

## URLs to preserve

These have been shared externally and must remain accessible:

| URL | Content | Status |
|-----|---------|--------|
| https://llm-uj-research-eval.netlify.app | Project space / working paper (after Phase 2) | Must stay live |
| https://valentinklotzbuecher.github.io/llm-uj-research-eval/paper_response_analysis.html | Author engagement evidence | Must stay live — shared in grant applications |
| https://valentinklotzbuecher.github.io/llm-uj-research-eval/ | Working paper | Must stay live |
