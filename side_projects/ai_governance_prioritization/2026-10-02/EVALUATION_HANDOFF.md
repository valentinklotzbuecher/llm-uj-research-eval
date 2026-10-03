# Independent evaluation handoff: AI-governance priority papers

**Status:** prepared, not executed. This file is an execution specification, not evidence that a GPT Pro evaluation has run.

## First wave

Run independent Unjournal-style evaluations of:

1. Forecasting the Economic Effects of AI — NBER w35046.
2. Diversion and resale: estimating compute smuggling to China — Epoch AI.
3. The AGI Race and Existential Risk — NBER w35276.

Second wave, after the first three are saved: The Economics of Recursive Self-Improvement; Delays to Frontier AI in the EU and UK; METR's Measuring AI Ability to Complete Long Software Tasks.

## Independence protocol

For each paper, start a fresh model context. Give the evaluator the paper, appendices/supplement, replication materials when available, and current Unjournal evaluator guidelines. Do **not** initially give it the prioritization report, queue position, proposed criticisms, other model evaluations, or human evaluations.

Require it to identify the paper's highest-impact claims; distinguish descriptive, causal, forecasting, construct-validity and operational claims; assess evidence against those claims; check arithmetic/internal consistency; inspect appendices and replication materials; state what it could not inspect; assess decision relevance; and provide the current Unjournal metrics with uncertainty.

For forecasting work, explicitly assess scenario conditioning, elicitation, aggregation, coherence, calibration where observable, benchmark comparability, and downstream interpretation. For theoretical work, audit assumptions, equilibrium selection, comparative statics and welfare interpretation. For difficult-to-observe quantities, audit evidence overlap, measurement model, priors/uncertainty, sensitivity and the distinction between an estimated quantity and the policy counterfactual.

## Verification pass

After the independent first pass is frozen, provide the evaluator with the corresponding prioritization report and any existing human/model reviews. Ask it to:
- verify or reject each proposed concern;
- identify important concerns missed by both;
- distinguish confirmed errors from sensitivities and interpretive cautions;
- cite the paper and external evidence precisely;
- revise scores only where the new evidence warrants it.

Do not present a speculative counterexample as a paper error without independently checking it.

## Output

Store one folder per paper containing:
- paper/version metadata and retrieval date;
- first-pass evaluation;
- verification/addendum;
- structured metric JSON/CSV compatible with the existing LLM-evaluation project where practical;
- provenance: model identifier, prompt version, date, materials supplied, unavailable materials, and whether external research was used;
- a short public-facing summary that states appropriate and inappropriate reliance on the work.

Add a visible AI-assistance disclosure. A human evaluator should verify and adopt final judgments before any output is presented as an official Unjournal evaluation.

## Pipeline note

The repository's documented pipeline uploads paper PDFs, obtains structured evaluations, and tracks runs under results/. It has previously used GPT-5.2 Pro. Before launching a new run, inspect the current OpenAI model availability and update the runner rather than assuming an old model identifier is still current. Never label a run "GPT Pro" unless its recorded model actually is the requested Pro model.

## Completion criterion

A run is complete only when the model response has been collected, parsed, saved with provenance, and checked for missing sections. A queued job or prepared prompt is not a completed evaluation.
