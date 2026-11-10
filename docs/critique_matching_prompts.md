# Critique-matching judge prompts: recovered text and assessment

Claude Code (Opus 5.5), 10 Nov 2026, at David's request. This note collects the
prompts used to judge whether the model's key issues match the human critiques,
and assesses them. It changes no results.

## Which prompt produced the published numbers

The published coverage and overlap figures (12 papers, `results/key_issues_comparison_results.json`,
GPT-5.2 Pro, reasoning effort medium, restored 6 Jul 2026) were produced by
**`tools/compare_issues_llm.py`**. The evidence: its matched pairs have no
`human_issue_text` field, which the `methods.qmd` variant's schema requires.

| Prompt | Where | Used for | Judge |
|---|---|---|---|
| 1. Published judge | `tools/compare_issues_llm.py:112` | The 12-paper headline numbers | GPT-5.2 Pro, medium effort |
| 2. Book-chunk variant | `methods.qmd:1328` | Shown in Methods; not the source of the stored results | GPT-5.2 Pro, medium effort |
| 3. Terra first pass | `scripts/run_concordance_codex.py:298` | July pilot, 2 papers | `gpt-5.6-terra`, high effort |
| 4. Sol adjudicator | `scripts/run_concordance_codex.py:398` | Up to 3 ambiguous pairs | `gpt-5.6-sol`, high effort |

## How the inputs were prepared (prompt 1)

- **Human issues:** the Coda consensus critique for each paper, split by a regex
  (`parse_human_issues`): severity headers ("Necessary", "Optional", "Unsure")
  set the severity, numbered lines start a new issue, and fragments of 15
  characters or fewer are dropped. Each issue is passed as `H{i} [SEVERITY]: text`.
  Attribution tags such as "[Eval. manager, also relates to E1 critique]" stay in the text.
- **Model issues:** the `key_issues` list from the GPT-5.2 Pro focal run, as `L{i}: text`.
- **Not given:** the paper, its title, or either side's wider report.
- **Settings:** one call per paper, strict JSON schema, `max_output_tokens` 6000,
  no repeat runs.

## Prompt 1 (published), verbatim

```text
You are comparing human expert critiques with LLM-identified issues for a research paper evaluation.

## Task
Create a detailed issue-by-issue comparison between human expert critiques and LLM-identified issues.

## Human Expert Issues
{human_issues}

## LLM Issues
{llm_issues}

## Instructions
1. For each human issue (H1, H2, ...), identify which LLM issue(s) address the same or related concern
2. Create a DETAILED matched_pairs entry for each human issue that has any LLM coverage
3. For each match, provide:
   - A short descriptive LABEL for the shared concern (5-10 words)
   - match_quality: 0-100% where 100% = exact same concern, 0% = no overlap
   - match_explanation: Brief 1-2 sentence explanation of WHY this is a match
   - detailed_discussion: Longer analysis (3-5 sentences) comparing HOW the human and LLM framed the issue, noting differences in emphasis, specificity, or scope
4. Note issues that have no matches on either side
5. Provide overall coverage_pct (% of human issues with match_quality >= 30) and precision_pct (% of LLM issues that match something)

Respond in JSON format with this structure (values shown are examples - generate actual content based on your analysis):
{
    "matched_pairs": [
        {
            "human_issue_index": 1,
            "llm_issue_indices": [3, 5],
            "match_quality": 75,
            "label": "Sample size limitations",
            "match_explanation": "Both human H1 and LLM L3/L5 identify concerns about the small sample affecting statistical power.",
            "detailed_discussion": "The human expert critique focuses on how the small sample (n=6) 'severely limits conclusions' and notes overstated claims. LLM issues L3 and L5 cover similar ground but frame it more technically in terms of aggregation sensitivity and multiple comparisons. The human provides more concrete examples of problematic claims, while the LLM offers broader methodological critique. Overall, the core concern is well-matched though framed differently."
        },
        ...
    ],
    "unmatched_human": [
        {
            "index": 2,
            "brief_description": "Units error in FGF2 cost table",
            "why_missed": "LLM did not identify this specific data error, possibly because it requires domain knowledge about biochemistry costs"
        },
        ...
    ],
    "unmatched_llm": [
        {
            "index": 6,
            "brief_description": "Resolution protocol concerns",
            "why_extra": "LLM raised this valid methodological point that human evaluators did not emphasize"
        },
        ...
    ],
    "coverage_pct": 70,
    "precision_pct": 80,
    "overall_rating": "Good",
    "overall_justification": "Most key concerns are captured. The LLM identifies X of Y human issues with reasonable fidelity, though it misses [specific gaps].",
    "detailed_notes": "Additional observations about patterns in what the LLM captures well vs misses."
}

Be precise about which issues match. Related but distinct concerns (e.g., "sample size" vs "statistical power") should have lower match_quality scores (40-60%) with explanation of the distinction.
```

(The source doubles the braces for Python `.format`; they are shown single here.)

## Prompt 2 (`methods.qmd` variant): differences only

This version passes the raw Coda critique text with no splitting, although its
header says "numbered H1, H2, ...", so the judge decides where one human issue
ends and the next begins. It drops the worked JSON example and relies on the
schema, which adds a `human_issue_text` field. Its closing line has no example
pair. Otherwise the instructions are the same.

## Prompt 3 (Terra first pass), verbatim

```text
You are judging semantic concordance between independently prepared human research critiques and LLM-generated research critiques.

Use issue substance only. Ignore evaluator identity, author identity, prestige, and writing style. Do not browse, use tools, or read files.

Before matching, check whether the paper title, human concerns, and LLM concerns appear to describe the same study. Mark input_alignment=misaligned when they clearly concern different designs, outcomes, or manuscripts; use uncertain when the evidence is insufficient. Explain the check. Do not rescue a misaligned case by matching generic methodological vocabulary.

Rubric:
- exact: essentially the same concern, mechanism, and implication (normally 80-100).
- partial: a meaningful shared core, but one side is broader, narrower, or materially different (normally 45-79).
- related_but_distinct: same topic but different methodological claim or implication (normally 20-44).
- distinct: no substantive concordance (normally 0-19).

Map each human issue to zero, one, or several LLM issues. Do not force a match. A single LLM issue may be relevant to more than one human issue. Put only exact, partial, or genuinely borderline related pairs in judgments; list issues with no counterpart as unmatched. Explain the shared core and the most important difference. Confidence is confidence in the overlap classification, not confidence that either critique is correct.

Mark needs_sol_review=true when reasonable judges could cross either the 30-point coverage threshold or the 45-point partial-match boundary. Also list possible missed matches or grouping ambiguities in review_candidates. Use only the supplied stable IDs.

INPUT CASES:
{payload}

Return only JSON matching the supplied schema.
```

`{payload}` is JSON with stable IDs (`paper::H001`, `paper::L001`), the paper
title, human issues pre-split in `tools/issue_annotation_ui/data.json`, and
attribution markers removed. Three papers go in each call.

## Prompt 4 (Sol adjudicator), verbatim

```text
Act as a high-effort second adjudicator for difficult human–LLM critique concordance judgments.

Use issue substance only. Ignore names, prestige, and prose quality. Do not browse, use tools, or read files. Reconsider each candidate independently; Terra's judgment is context, not authority.

Labels and typical scores:
- exact: same concern, mechanism, and implication (80-100)
- partial: meaningful shared core with material scope or implication differences (45-79)
- related_but_distinct: same topic but a different methodological claim (20-44)
- distinct: no substantive concordance (0-19)

The key operational threshold is 30: a score at or above 30 counts as covered in the historical metric. Explain why the final judgment lies above or below that threshold. Confidence concerns the classification, not whether the critique itself is true.

AMBIGUOUS CANDIDATES:
{payload}

Return exactly one adjudication for each candidate, using only the supplied IDs and JSON schema.
```

Sol sees the candidate pair, Terra's judgment, and the issue texts. It does not
see the other issues for the paper.

## Assessment of prompt 1 (the one behind the headline)

**What works.** It asks for explicit H-to-L links with a short reason for each,
so every match can be checked. It allows one-to-many matches. It records
unmatched issues on both sides and asks why each was missed.

**Problems, roughly in order of how much they could move the numbers.**

1. **The worked example contains the answer for one study paper.** The sample
   "unmatched human" item is "Units error in FGF2 cost table", which is the real
   Dullaghan and Zhang miss, and the sample discussion quotes "n=6", their panel
   size. On that paper the judge was handed a template for one verdict. Elsewhere
   it may lean towards that pattern. Any rerun should use invented examples.
2. **"Same or related concern" sets a low bar, and the scale has no anchors below
   40.** Coverage counts anything scored 30 or more, but the prompt defines only
   100 ("exact same concern") and 40–60 ("related but distinct"). A score of 30–39
   is undefined, so "covered" in effect includes some related-but-distinct pairs.
   The worked example (75 for a "sample size" vs "aggregation sensitivity and
   multiple comparisons" match) also models generous scoring.
3. **The judge does its own arithmetic and summary.** `coverage_pct` and
   `precision_pct` come from the model, not from the pair list. The stored values
   look consistent with the pair counts, but this should be computed in code.
   `overall_rating` has no definition.
4. **`precision_pct` is undefined.** "Match something" has no threshold, unlike
   coverage, so the overlap rate can be on a different scale.
5. **No paper context or identity check.** Without the title or abstract, the
   judge cannot tell a match on generic vocabulary from a real one. This is how
   the two mismatched pairings still scored 40–50% coverage.
6. **The judge is not blind to which side is which.** It knows one list is "human
   expert" and the other "LLM", and the example's "why_extra: valid
   methodological point" invites crediting the model.
7. **Same model as the generator.** GPT-5.2 Pro wrote the issues and judged them.
8. **Severity and attribution tags left in.** "[NECESSARY]" and "[Eval. manager ...]"
   carry no matching information but may sway the judge; the second also sends
   attribution into an external call.
9. **One run, medium effort, no confidence field.** There is no measure of
   run-to-run variation and no flag for uncertain calls.

Prompts 3 and 4 fix several of these (identity check, named labels with score
bands, "do not force a match", attribution removed, confidence, escalation).
They keep problems 3, 6 and 9 in part: Terra still knows which side is which,
and the 30-point line still falls inside the "related but distinct" band, whose
definition is "different methodological claim".

## Building a rubric: key choices and their difficulties

**What counts as "the same issue".** A critique has at least three parts: the
*locus* (which result, table or assumption), the *mechanism* (why it is a
problem, e.g. selection, leakage, a units error) and the *implication* (what
follows for the claim, and the fix). A useful rubric scores these separately, or
at least defines matches in their terms:

| Level | Locus | Mechanism | Implication |
|---|---|---|---|
| Same | same | same | same or compatible |
| Same, narrower or broader | same or overlapping | same core, one side less specific | may differ |
| Same target, different problem | same | different | different |
| Same topic only | general area only | different or absent | different |
| None | — | — | — |

"Covered" should then mean the first two rows only, decided in advance, and the
third row should be reported separately. Today's 30-point line counts some
third-row pairs as covered.

**Main difficulties.**

- **Granularity.** One human item often bundles several concerns, and model items
  are often broad lists of minor points ("robustness checks, clustering, power").
  A broad model item can then "cover" many specific human points. The rubric needs
  a rule: a match requires the model item to name the specific mechanism, not just
  the topic. Freeze issue splitting before judging, since it sets both denominators.
- **Specificity versus vocabulary.** "Concerns about identification" overlaps in
  wording with nearly any identification critique. The test is whether a reader of
  the model item alone would be led to the same fix.
- **Direction.** "Does the model cover the human issue?" and "does the human cover
  the model issue?" are different questions when one side is broader. The rubric
  should be applied in both directions, not inferred from one mapping.
- **Partial credit and the threshold.** Coverage results moved when one Sol score
  went from 31 to 27. Report results at more than one cut-off and with
  categories, not just one number.
- **Severity and validity are separate questions.** A match says nothing about
  whether either critique is right or important. Keep "is it the same concern?"
  apart from "is it valid?" and "how important?", and rate them in different passes.
- **Information access.** Some human critiques rely on supplements, data or outside
  sources that the model never saw (the FGF2 units error, the Williams validation
  table). Tag these before judging and report coverage with and without them.
- **Judge independence and blinding.** Use a different model family from the
  generator, hide which list is human, shuffle order, and keep paper context to
  the title and abstract so that the judge cannot re-critique the paper itself.
- **Validation.** The rubric is only as good as human agreement on it. Before
  scaling, have two people apply it to the same 30–50 pairs, report their
  agreement, and then compare the LLM judge with them. Include cross-paper pairs
  as controls to measure the chance-match rate.

**Done 10 Nov 2026:** a first version of this judge is in
`scripts/run_issue_match_judge.py`; results in
`docs/issue_match_judge_v2_pilot_2026-11-10.md`.

**Original suggestion.** Rewrite the judge prompt around the table above, with
invented examples, a paper title and abstract, blinded and shuffled lists, a
confidence field and an explicit "different problem, same target" category. Have
code compute coverage and overlap from the pairs. Then run it alongside the
existing prompt on the 12 papers and on a few cross-paper controls, and check both
against a human-labelled sample.
