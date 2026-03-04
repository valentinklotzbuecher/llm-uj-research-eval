# Working Paper Strategy: Branch and Hosting Recommendations

## Current State

- **Main branch** (`main` in `daaronr/llm-uj-research-eval`): Full project with extensive notes, funding proposals, appendices, tools, monitoring scripts
- **Working-paper branch** (`working-paper` in `valentinklotzbuecher/llm-uj-research-eval`): Condensed academic paper version with cleaner narrative
- **llm-paper-mirror** (`daaronr/llm-paper-mirror`): Static HTML hosting of the working paper with Hypothes.is annotations enabled

## Hosting Options for Hypothesis-Enabled Working Paper

### Option 1: GitHub Pages from working-paper branch (Recommended)
**Setup:**
```bash
# In Valentin's fork, enable GitHub Pages for the working-paper branch
# Settings → Pages → Source: Deploy from branch → working-paper → /_book
```

**URL:** `https://valentinklotzbuecher.github.io/llm-uj-research-eval/`

**Pros:**
- Automatic deployment on push
- Stays synced with source
- Hypothesis works automatically (already enabled in _quarto.yml)
- No separate repo to maintain

**Cons:**
- Tied to Valentin's GitHub account
- URL less memorable than custom domain

### Option 2: Netlify from working-paper branch
**Setup:**
1. Create new Netlify site linked to `valentinklotzbuecher/llm-uj-research-eval`
2. Set branch to `working-paper`
3. Build command: `quarto render --to html`
4. Publish directory: `_book`

**Pros:**
- Better URLs (can be `working-paper-llm-eval.netlify.app` or custom)
- Branch deploys for testing
- Preview deploys for PRs

**Cons:**
- Another service to manage
- Build minutes consumption

### Option 3: Keep llm-paper-mirror as manually-synced static host
**Status quo:** Copy `_book/` contents to llm-paper-mirror when ready.

**Pros:**
- Simple, works now
- Hypothesis annotations already exist there

**Cons:**
- Manual sync required
- Risk of divergence
- Harder to trace which version is annotated

### Migrating Existing Hypothes.is Annotations

The ~66 human annotations on `daaronr.github.io/llm-paper-mirror` are tied to those specific URLs. Options:

1. **Keep both sites running:** New annotations go to GitHub Pages URL, old annotations stay accessible at mirror URL
2. **Use Hypothesis groups:** Create a group for this project, manually tag important annotations for portability
3. **Accept that annotations are URL-bound:** Document the annotation sources and accept that migrating URLs breaks annotation linkage

**Recommendation:** Use Option 1 (GitHub Pages) for the canonical working paper, but keep llm-paper-mirror live as an archive of prior annotations. Document both URLs in the paper metadata.

---

## Branch Strategy Recommendation

### Should working-paper be a separate branch? **Yes, with caveats.**

**Current structure makes sense because:**

1. **Different audiences, different needs:**
   - Main branch: Funders, collaborators, full methodology, extensive appendices
   - Working paper: Academic reviewers, concise narrative, publication-ready

2. **Different update cadences:**
   - Main branch: Frequent updates, experimental features, funding proposals
   - Working paper: Deliberate updates, version-controlled releases

3. **Different content scope:**
   - Main branch has: `proposal.qmd`, `questions_answers.qmd`, `paper_response_analysis.qmd`, extensive tools/, monitoring scripts
   - Working paper has: Streamlined chapter structure, `results.qmd` (combined), cleaner discussion.qmd

### Recommended Workflow

```
main (daaronr/llm-uj-research-eval)
├── Full project, funding, tools
├── Appendix content
└── Experimental features

working-paper (valentinklotzbuecher/llm-uj-research-eval)
├── Publication-ready paper
├── _book/ committed for hosting
└── Cherry-pick key updates from main
```

**Key principles:**

1. **Analysis code lives in main:** Run analyses in main branch, export results to data/ files that working-paper reads
2. **Prose diverges intentionally:** Working paper has tighter, publication-focused prose; main has explanatory detail
3. **Sync strategically, not automatically:** Cherry-pick substantive changes; don't try to keep branches identical
4. **Version releases:** Tag working-paper releases (v0.1, v0.2) for reproducibility

### Alternative: Separate Repos

If branch management becomes unwieldy:

```
llm-uj-research-eval (main project, tools, data)
llm-uj-research-paper (publication manuscript only)
```

This makes the separation cleaner but requires explicit data sharing.

**Current branch approach is fine** as long as you establish clear conventions about what gets synced.

---

## Immediate Next Steps

1. **Push working-paper changes:**
   ```bash
   git push origin working-paper
   ```

2. **Enable GitHub Pages** on Valentin's fork for working-paper branch

3. **Re-render PDF** when TinyTeX is available:
   ```bash
   quarto install tinytex  # or use system LaTeX
   quarto render --to pdf
   ```

4. **Update main branch** with this strategy document:
   ```bash
   git checkout main
   git stash pop  # restore main branch changes
   # copy this file and commit
   ```

5. **Document the multi-site situation** in both repos' READMEs
