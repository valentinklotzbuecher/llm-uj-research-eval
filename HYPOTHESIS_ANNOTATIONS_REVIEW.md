# Hypothes.is Annotations Review

Generated: 2026-03-04

Two sites have annotations:

1. **llm-uj-research-eval.netlify.app** - 77 annotations (many on archived pages)
2. **daaronr.github.io/llm-paper-mirror** - 66 human annotations (separate draft version)

---

## Implemented

### In llm-uj-research-eval (this repo)
- **index.qmd**: "Research Goals and Questions" → Converted to callout box

### In llm-paper-mirror repo (commit caf5176, 2026-03-04)
Applied the following annotation-driven fixes to the rendered HTML:

**index.html:**
- Rewrote "milquetoast" abstract text to be more precise about limitations
- Changed "60 papers" → "57 papers" (accurate count)
- Changed "six frontier LLMs" → "six LLMs spanning different capability and cost tiers"
- Softened "strong case" → "suggesting that top reasoning models can serve"
- Removed redundant "deliberately" before "minimal"
- Added "currently" to "can achieve" for temporal accuracy
- Fixed "external reference point" → "external validation opportunity"

**discussion.html:**
- Replaced "ceiling set by inter-rater variability" → "agreement levels observed among human evaluators" (ceiling was a misnomer)
- Quantified "perform respectably" → "achieve moderate correlations (r ≈ 0.5–0.6)"
- Clarified "block extrinsic priors" → explained what we're blocking (author/institution/history knowledge)

---

## llm-paper-mirror Annotations (Priority - Recent Feedback)

These are on a newer draft version at `~/githubs/llm-paper-mirror/`. Most from Feb 26-Mar 4, 2026.

### Writing/Tone Issues


| Location   | Issue                                     | Annotation                                                                 |
| ---------- | ----------------------------------------- | -------------------------------------------------------------------------- |
| index      | "milquetoast generic caveat"              | "Our results support AI as structured screening..." - seems pandering      |
| index      | "strong case" too strong                  | Re: "strong case that frontier LLMs can serve as additional expert raters" |
| index      | Remove "deliberately"                     | Repeats what was just said                                                 |
| index      | Rephrase iteration statement              | "We do not do any iteration..." as separate sentence                       |
| index      | "can achieve" → "can currently achieve"   | Add "currently"                                                            |
| index      | "high-quality but noisy reference signal" | Check if "reference signal" is technically correct                         |
| discussion | "respectably" undefined                   | Avoid vague terms, quantify                                                |
| discussion | "ceiling" misnomer                        | Inter-rater agreement isn't mathematically a ceiling                       |


### Factual/Accuracy Issues


| Location | Issue                                  | Annotation                      |
| -------- | -------------------------------------- | ------------------------------- |
| index    | "60 papers" wrong                      | Should be ~57 publicly released |
| index    | "six frontier LLMs"                    | Are they all really "frontier"? |
| index    | "reducing gatekeeping motives" unclear | Not fully justified             |
| index    | Citation needed for "strain"           | Add reference                   |
| results  | "matched sample" needs explanation     | Clarify what matching means     |
| results  | Diagrams too small                     | Need to be larger for print     |


### Substantive Concerns


| Location   | Issue                                             | Annotation                                                                      |
| ---------- | ------------------------------------------------- | ------------------------------------------------------------------------------- |
| index      | Adversarial manipulation discussed but not tested | "I don't think we discussed adversarial manipulation or have any results on it" |
| index      | "headline finding" comparison                     | Is comparing to human average fair? Check vs individual raters                  |
| index      | Multi-dimensional advantage unclear               | What's the actual advantage?                                                    |
| discussion | Training data contamination                       | Need empirical checks, robustness with pre-cutoff models                        |
| discussion | "while we block extrinsic priors"                 | What exactly are we blocking?                                                   |
| results    | "performing within human interrater range"        | Unclear what this means                                                         |
| results    | CIs statement confusing                           | "CIs often span 20-40 points" - which CIs?                                      |
| results    | LLMs outside human range                          | "I seem to see a lot of cases where LLM ratings fall outside"                   |


### Technical/Display Issues


| Location        | Issue                               | Annotation                                   |
| --------------- | ----------------------------------- | -------------------------------------------- |
| results         | Computation not rendering           | `r n_papers_slope-` shows raw code           |
| results         | "Hide all code" button broken       | Doesn't work                                 |
| results         | Paper labels missing                | In human-human comparison panel              |
| results         | Add hover labels to rank comparison | Would be much better                         |
| results         | Put correlation metric in each plot | Hard to eyeball scatter                      |
| results_ratings | K's alpha interval method           | Is penalizing squared distances appropriate? |
| results_ratings | GPT-5.2 Pro column position         | Should be second from left (best performer)  |
| results_ratings | Include journal tier agreement      | Should be comparable                         |


### Claims to Verify


| Claim                                      | Issue                                      |
| ------------------------------------------ | ------------------------------------------ |
| "compressed rating scales" as failure mode | May be premature generalization            |
| "approaching ceiling"                      | Strong claim, need careful framing         |
| References hallucinated?                   | User checking - Elsevier policy checks out |


---

## llm-uj-research-eval.netlify.app Annotations

Many on archived pages (`/compare_ratings`, `/results`, `/numerical_ratings`). Key items from current pages:

### Layout Issues

- Paper-by-Paper margins too narrow (results_critiques)
- Forest plots too dense (results_ratings)

### Methodological

- Which GPT Pro version exactly?
- "Taste" terminology vs noise/bias
- Why round to 0.5?
- "Calibration" terminology misleading
- Overall score calculation (arithmetic mean vs weighted)

---

## Action Items

**High priority (llm-paper-mirror feedback):**

1. ~~Review/edit text flagged as "milquetoast" or "pandering"~~ ✅ Done (commit caf5176)
2. ~~Fix factual claims (paper count, model descriptions)~~ ✅ Done (commit caf5176)
3. Add citations where noted (strain reference still needed)
4. Fix rendering issues (code display, hover labels)

**Medium priority:**

1. Clarify statistical interpretations (CIs, "within range" language)
2. Add robustness checks for training data contamination
3. ~~Review "ceiling" terminology throughout~~ ✅ Done (commit caf5176)

**Needs discussion:**

1. Is the llm-paper-mirror version the target for edits, or should changes go back to this repo?
2. How to sync annotations between the two sites?

---

## Repo Reconciliation Needs

**Critical finding:** The two repos have significantly diverged. Content in `llm-paper-mirror` does not exist in `llm-uj-research-eval` source files:

### Content discrepancies:

| llm-paper-mirror HTML | llm-uj-research-eval source | Status |
|----------------------|----------------------------|--------|
| `index.html` (with abstract, "60 papers" text, etc.) | `index.qmd` | **Different content** - mirror has newer text not in source |
| `discussion.html` | `archive/discussion.qmd` only | **No active source** - discussion was archived |
| `results.html`, `results_critiques.html`, `results_ratings.html` | `results_ratings.qmd`, `results_critiques.qmd` | Likely diverged |

### Key questions to resolve:

1. **Where is the canonical source for llm-paper-mirror content?**
   - The mirror appears to be generated from a different branch/repo
   - Annotations were made on content that doesn't exist in this repo's main branch

2. **Should discussion.qmd be unarchived?**
   - Active annotations exist on discussion content
   - Currently only exists in `archive/discussion.qmd`

3. **What is the working-paper branch?**
   - The PDF link points to `valentinklotzbuecher/llm-uj-research-eval/raw/working-paper/`
   - This may be where the divergent content lives

### Recommended next steps:

1. Check if `working-paper` branch in Valentin's fork has the source for llm-paper-mirror
2. Decide which repo/branch should be the canonical source
3. Either:
   - a) Port the fixes back to the source .qmd files (if found), OR
   - b) Accept llm-paper-mirror as the editing target for now and reconcile later

