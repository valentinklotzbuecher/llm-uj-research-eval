# exporter

**User:** Anonymous (contact@unjournal.org)  
**Created:**   
**Updated:**   
**Exported:** 3/4/2026 12:24:32  
**Link:** [https://chatgpt.com/share/e/69a86a8d-cb8c-8002-b672-70a8593b9d51](https://chatgpt.com/share/e/69a86a8d-cb8c-8002-b672-70a8593b9d51)  

## Prompt:
Uploaded a file

Write a detailed referee report on this paper. Provide ratings and detailed suggestions. Particularly focus on methodology -- both in our data generation (human and LLM and the comparison) and in our statistical analysis/information theory. Provide detailed mythological discussions explaining things that we might not understand, and providing clear references to other texts and resources explaining these.

I had a set of next steps that we should implement. Perhaps even a set of marching orders we could ask an LLM to implement minor fixes and improvements. 

https://daaronr.github.io/llm-paper-mirror/ -- updated version of the paper

## Response:
Pro thinking • Thinking

Answer now

## Response:
According to a document from **2026-02-21**, I reviewed _“Just Ask the Model: One-Shot LLM Research Evaluation and Structured Expert Review”_ (uploaded PDF:

Just-Ask-the-Model--One-Shot-LL…

).

Just-Ask-the-Model--One-Shot-LL…

Below is a referee-style report with ratings, major and minor revision requests, and a “methodology mythology” section (myths → realities) focused on **(i) data generation & comparability** and **(ii) statistical / information-theoretic analysis**.

* * *

1) Summary of the paper
-----------------------

**Goal.** The paper asks how reliably frontier LLMs can evaluate research relative to expert peer review, under realistic inter-rater disagreement.

Just-Ask-the-Model--One-Shot-LL…

**Design.**

*   Human “reference signal” comes from **The Unjournal**: typically 2 expert evaluators per paper (sometimes 1 or 3), each providing (a) narrative critique and (b) **seven 0–100 percentile criteria** with **90% uncertainty intervals**, plus two journal-tier predictions (“should” and “will”) on a 0–5 scale.
    Just-Ask-the-Model--One-Shot-LL…
    Just-Ask-the-Model--One-Shot-LL…
*   You aggregate human scores via **arithmetic mean per paper per criterion**, and treat humans as “high-quality but noisy reference,” not ground truth.
    Just-Ask-the-Model--One-Shot-LL…
    Just-Ask-the-Model--One-Shot-LL…
*   You prompt **six frontier LLMs** with the same rubric and ask for JSON output containing a ~1,000-word assessment summary plus midpoint and 90% interval for each metric.
    Just-Ask-the-Model--One-Shot-LL…
    Just-Ask-the-Model--One-Shot-LL…
*   Importantly: you pass **the PDF directly** to each model’s multimodal input “rather than extracting text.”
    Just-Ask-the-Model--One-Shot-LL…

**Data volume.**

*   Across all models, you have **45** papers with both human and LLM evaluations; **33** papers are in a “matched sample” that also has Claude Opus 4.6 evaluations, used for rank comparisons / agreement tables.
    Just-Ask-the-Model--One-Shot-LL…

**Headline claims.**

*   Best model (GPT‑5 Pro) matches/exceeds pairwise human inter-rater rank agreement on overall quality (Spearman).
    Just-Ask-the-Model--One-Shot-LL…
*   Failure modes include **central compression**, **uneven criterion coverage**, and inconsistent identification of expert-flagged concerns.
    Just-Ask-the-Model--One-Shot-LL…

* * *

2) Ratings (with brief justification)
-------------------------------------

I’m using a 1–10 scale (10 = excellent).

**Significance / timeliness:** **9/10**  
Peer review stress + fast adoption of AI reviewer tools makes this very high-impact; your use of a structured, open human-evaluation dataset is unusually valuable.

Just-Ask-the-Model--One-Shot-LL…

Just-Ask-the-Model--One-Shot-LL…

**Novelty:** **7/10**  
The core “LLM vs expert review” question is active, but your pairing with _Unjournal_’s multidimensional rubric + uncertainty intervals is a distinctive contribution.

Just-Ask-the-Model--One-Shot-LL…

**Methodological soundness:** **6/10 (major revision needed)**  
The one-shot multimodal design is clean and conservative, but several statistical framing choices (especially “ceiling” interpretation and the way reliability is used) are currently misleading or under-specified.

Just-Ask-the-Model--One-Shot-LL…

Just-Ask-the-Model--One-Shot-LL…

**Statistical analysis / validity of inferences:** **5/10 (major revision needed)**  
You report the right families of metrics (rank agreement, bias, MAE/RMSE, reliability), but the _interpretation_ and some computations (e.g., “human ceiling”) need re-derivation, and uncertainty quantification should be promoted from appendix to main claims.

Just-Ask-the-Model--One-Shot-LL…

Just-Ask-the-Model--One-Shot-LL…

**Clarity / writing:** **7/10**  
Overall readable, but there are internal inconsistencies (e.g., N in “matched” tables, placeholder cross-references) that must be fixed before publication.

Just-Ask-the-Model--One-Shot-LL…

**Reproducibility / openness:** **8/10**  
You state code and appendices are available online; the pipeline description is detailed (PDF-in, schema, job logging).

Just-Ask-the-Model--One-Shot-LL…

Just-Ask-the-Model--One-Shot-LL…

**Ethics / governance awareness:** **8/10**  
You directly discuss prompt injection, confidentiality, Goodharting, and need for red-teaming and recalibration.

Just-Ask-the-Model--One-Shot-LL…

**Overall recommendation:** **Major revision**  
The dataset + question are strong. The main blocking issue is methodological/statistical framing: if fixed, the paper becomes substantially more credible and reusable.

* * *

3) Strengths
------------

1.  **Strong evaluation substrate.** Unjournal gives structured multi-criterion human evaluations with uncertainty intervals and public posting—rare in peer-review studies.
    Just-Ask-the-Model--One-Shot-LL…
2.  **Conservative experimental design.** One-shot, no retrieval, no agent loop: good as a baseline and defensible “lower bound” framing.
    Just-Ask-the-Model--One-Shot-LL…
3.  **Multimodal PDF ingestion.** Passing the PDF directly reduces avoidable extraction artifacts and better matches how humans see the paper.
    Just-Ask-the-Model--One-Shot-LL…
4.  **You explicitly acknowledge major threats.** Contamination, single-run instability, LLM-as-judge dependence, and prompt injection are surfaced (not buried).
    Just-Ask-the-Model--One-Shot-LL…

* * *

4) Major issues and detailed methodological suggestions
-------------------------------------------------------

### A. Data generation & comparability

#### A1) Human “reference signal”: define what it is (and what it isn’t)

You correctly say you do **not** treat human ratings as ground truth.

Just-Ask-the-Model--One-Shot-LL…

But several downstream choices still implicitly treat the **human mean** as a proxy for “truth” without a measurement model.

Concrete concerns:

*   **Percentile rubric is inherently “contextual.”** Humans are told to anchor to “all serious research … encountered in the last 3 years.”
    Just-Ask-the-Model--One-Shot-LL…
    Two different evaluators likely have _different_ mental reference distributions; that alone induces disagreement not attributable to “paper quality.”  
    Recommendation: explicitly model this as _rater calibration differences_ (severity/leniency + scale use), not just “noise.”
*   **Averaging percentiles may be defensible, but only with caveats.** You average the two evaluator midpoints per paper/criterion.
    Just-Ask-the-Model--One-Shot-LL…
    That’s fine pragmatically, but you should (i) justify mean vs median, and (ii) describe how you handle papers with 1 or 3 evaluators. You mention “occasionally one or three,” but the downstream “human mean” definition under that imbalance matters a lot for reliability comparisons.
    Just-Ask-the-Model--One-Shot-LL…
*   **Human uncertainty intervals are treated descriptively, not analytically.** Humans provide 90% credible intervals per metric.
    Just-Ask-the-Model--One-Shot-LL…
    Right now, these CIs mostly show “spread is big.” But there’s more you can do:
    *   quantify whether some evaluators are systematically over/under-confident (CI widths vs absolute disagreement)
    *   use CI widths as weights or as an estimated observation variance in a hierarchical model (see “measurement model” below).

**High-value addition:** include a short “Data generating process” section describing human scoring as:

*   latent paper quality  $q_i$  (per criterion)
*   rater-specific severity  $b_r$ 
*   rater-specific scale-use / compression  $s_r$ 
*   idiosyncratic error  $\epsilon_{ir}$ 

Even if you don’t fully estimate it, naming it clarifies what you mean by “noisy reference.”

#### A2) LLM generation: you need to standardize and document inference settings more aggressively

You do a good job describing the pipeline (one PDF, one call, strict schema, long assessment summary).

Just-Ask-the-Model--One-Shot-LL…

But, for a paper about _measurement_, inference conditions are part of the measurement instrument.

Key fixes:

*   **State temperature / stochasticity explicitly for each provider.** You mention “single-run” and that multiple runs or temperature settings could change the picture.
    Just-Ask-the-Model--One-Shot-LL…
    But the paper should say: what temperature/top\_p/seed (if any) did you use, and are they comparable across providers? If you used default values, that is important too.
*   **Fairness across “reasoning effort.”** You explicitly note Claude Opus 4.6 was run without extended thinking and may understate capability.
    Just-Ask-the-Model--One-Shot-LL…
    If Table 1 is used to compare models, this is a confound that should be resolved (re-run) or clearly separated (label as “no extended thinking”).
*   **Matched-sample consistency is currently broken.** The text says the 33-paper matched sample is used so every model is evaluated on identical papers,
    Just-Ask-the-Model--One-Shot-LL…
    but Table 1 includes models with N far smaller (e.g., GPT‑5.2 Pro N=5, Claude Sonnet 4 N=8).
    Just-Ask-the-Model--One-Shot-LL…
    This needs a redesign:
    *   either run all models on the same N=33
    *   or present a “full matched” comparison table excluding partial-run models
    *   and a separate “exploratory / partial-run” table for the others.

#### A3) Human vs LLM comparison: don’t conflate _ability_ with _calibration_

A major theme is **central compression** (LLMs pulling extreme scores toward the middle).

Just-Ask-the-Model--One-Shot-LL…

Just-Ask-the-Model--One-Shot-LL…

Right now you treat this as a “failure mode,” which is plausible. But methodologically you must separate two cases:

1.  **True informational deficit:** LLM misses real quality differences → should reduce rank agreement and increase error.
2.  **Scale-use mismatch:** LLM sees differences but reports them in a compressed mapping → rank agreement may be fine, error (RMSE/MAE) may look worse, and correlation interpretation becomes tricky.

**Recommendation:** add a “calibration layer” analysis:

*   Fit  $\hat{y}^{LLM}_i = a + b \cdot \bar{y}^{human}_i$  per criterion.
*   Interpret  $b<1$  as compression;  $a\neq 0$  as bias.
*   Then evaluate:
    *   rank agreement before/after monotone calibration (isotonic regression)
    *   MAE/RMSE before/after affine calibration  
        If post-calibration error drops a lot while rank stays similar, your conclusion should shift from “LLMs fail” to “LLMs use different scale.”

This is a standard move in psychometrics and method-comparison work; it will make your paper much more precise.

#### A4) Qualitative critique comparison: “LLM-judged coverage/precision” is useful—but currently too endogenous

You evaluate key-issue overlap using GPT‑5.2 Pro as both generator (key\_issues) and judge (alignment scores), with human critiques as reference.

Just-Ask-the-Model--One-Shot-LL…

This is a reasonable first prototype, but for a scientific claim you need to tighten:

*   **Independence:** A judge model from the same family (or even the same model) can inflate apparent alignment because it shares paraphrase preferences.  
    At minimum: use a _different_ judge model than the generator; ideally: two judges + human adjudication on a subsample.
*   **Extraction protocol for “human issues” must be explicit.** You mention a “manually curated markdown document” pairing machine and expert assessments.
    Just-Ask-the-Model--One-Shot-LL…
    But: how were “issues” extracted from human narratives? How many per paper? Was it the union of evaluator issues? A manager synthesis? These choices massively affect “coverage.”
*   **Thresholding at 30% match score is arbitrary.** You define coverage as fraction of human issues with judge match ≥30%.
    Just-Ask-the-Model--One-Shot-LL…
    You should report sensitivity to threshold (10/30/50/70), and ideally use a continuous metric (e.g., average best-match score per human issue) alongside the binary.
*   **Sample size is small (subset of 14 papers).**
    Just-Ask-the-Model--One-Shot-LL…
    Treat qualitative results as exploratory unless expanded.

* * *

### B. Statistical analysis: what to fix (and why)

#### B1) The “human ceiling” framing is currently incorrect / misleading

You repeatedly frame pairwise human–human Spearman (or αHH) as “the ceiling available to any model.”

Just-Ask-the-Model--One-Shot-LL…

This is the single biggest methodological problem because it makes some results logically inconsistent:

*   In Table 2, for example, you call H–H Spearman the ceiling, but then report average LLM Spearman larger than that ceiling for multiple criteria (e.g., Claims & Evidence H–H 0.087 vs LLM 0.279).
    Just-Ask-the-Model--One-Shot-LL…

**Why this happens (intuition):**  
A model is compared to the **human mean**, not to a single human. Averaging two noisy raters increases reliability, so correlation with the mean can exceed correlation with a single rater. That’s not “superhuman”; it’s a statistical artifact of using an averaged reference.

**What to do instead (two viable options):**

**Option 1: “Ceiling for correlation-with-mean” via classical test theory (attenuation correction).**  
Let each individual human rating be  $Y = T + \epsilon$  (true + noise). If the reliability of the human mean  $\bar{Y}$  is  $Rel(\bar{Y})$ , then the maximum achievable correlation between any noisy proxy and  $\bar{Y}$  depends on these reliabilities—not on pairwise rho.

You can estimate  $Rel(\bar{Y})$  from ICC or from within-paper human variance (with assumptions). Then:

*   Report observed  $corr(LLM, \bar{Y})$ 
*   Report the implied  $corr(LLM, T)$  via attenuation correction:
    $$
    corr(LLM, T) \approx \frac{corr(LLM,\bar{Y})}{\sqrt{Rel(\bar{Y})}}
    $$

(And bound it to \[−1,1\].)

**Option 2: Treat LLM as an additional rater and compute ICC / α on the full rater set.**  
Instead of αHL between “human mean” and LLM, compute reliability on the matrix of raters:

*   human rater A, human rater B, … (as available)
*   plus the LLM as one additional rater  
    Then ask: does adding the LLM increase reliability of the aggregate rating? (This is _exactly_ the question you want operationally.)

Either approach makes the “ceiling” language rigorous.

#### B2) Correlation ≠ agreement (especially under compression)

You list Pearson r, Spearman ρ, bias, RMSE, MAE.

Just-Ask-the-Model--One-Shot-LL…

That’s good. But the narrative still leans too heavily on “Spearman ≈ human.”

Two key additions will prevent common misinterpretations:

*   **Concordance correlation coefficient (CCC)** (Lin): measures agreement around the 45° line (penalizes both bias and scale differences).
*   **Bland–Altman analysis**: plot difference vs mean to show systematic compression / heteroskedasticity.

These are standard in method comparison (e.g., new medical device vs old device). Peer review scoring is analogous: you are validating a “measurement device.”

#### B3) Krippendorff’s α: good choice, but current use-case is off

You describe α as chance-corrected reliability, general across measurement levels and missingness, and compute αHH as ceiling and αHL between human mean and each LLM.

Just-Ask-the-Model--One-Shot-LL…

Concerns:

*   **α is defined over a set of raters’ raw judgments.** A “human mean” is not a rater; it’s an aggregate statistic. Computing α between the human mean and LLM mixes levels of analysis.
*   **If you want α-style comparability**, include the LLM as another rater and compute α on the rater matrix (with missingness handled naturally). Then compare:
    *   α among humans only
    *   α among humans + LLM  
        This directly tests whether LLM behaves “like a rater.”

#### B4) Uncertainty quantification should be in the main text, not just appendices

You mention bootstrapped confidence intervals are in Appendix A,

Just-Ask-the-Model--One-Shot-LL…

but the main paper makes big comparative statements while showing only point estimates (and, in Table 1, mixing models with tiny N).

Recommended:

*   For each key metric (Spearman/MAE/CCC), report **95% bootstrap CI**.
*   For differences between models, report **paired bootstrap** (since evaluated on the same papers) and show probability that Model A > Model B.

This is especially critical for small-N models (e.g., N=5, N=8).

Just-Ask-the-Model--One-Shot-LL…

#### B5) The paper elicits 90% uncertainty intervals from LLMs; you should evaluate them as _forecasts_

You require LLMs to output 90% “credible intervals” paralleling humans, to avoid false precision.

Just-Ask-the-Model--One-Shot-LL…

But then you largely ignore whether those intervals are meaningful. Two high-value analyses:

1.  **Empirical coverage**: how often does the human mean fall inside the LLM interval? (Not perfect because human mean is noisy, but still informative.)
2.  **Interval scoring rules**: e.g., _Winkler score_ / _interval score_ (penalize width + misses). This lets you compare models’ uncertainty quality, not just point predictions.

I’d strongly suggest replacing “credible interval” language for LLMs with “elicited uncertainty interval,” unless you provide a calibration evaluation.

* * *

### C. Information-theoretic analysis: likely high value, but easy to do wrong

You say Appendix A includes “mutual information.”

Just-Ask-the-Model--One-Shot-LL…

Mutual information can be a powerful complement to correlation, because it captures _any_ dependence (not just linear/monotone). But there are serious pitfalls:

1.  **Small sample bias.** With N≈33–45, MI estimators (especially binned “plug-in” estimators) are biased upward, and kNN estimators have high variance.
2.  **Continuous vs discrete MI.** For continuous variables, MI is well-defined but estimation is delicate; for discretized bins, MI depends on binning choice (deciles vs quintiles changes the reported “bits”).
3.  **Interpretation risk.** “More MI” does not necessarily mean “better reviewer” unless you define what information should be preserved (rank? absolute quality? criterion-specific patterns?).

**Suggested best-practice package (simple and defendable):**

*   Predefine discretization (e.g., deciles of human mean) and compute discrete MI with a bias correction (Miller–Madow) + bootstrap CI.
*   Also report **Kendall τ** or **Spearman ρ** side-by-side; treat MI as exploratory unless N is large.
*   If you keep continuous MI (kNN / Kraskov): report sensitivity to k, and bootstrap uncertainty.

**Even better (but more work): “information about latent quality.”**  
If you adopt a measurement model with latent  $q_i$ , you can quantify how much the LLM reduces uncertainty about  $q_i$  relative to humans alone—i.e., reduction in posterior entropy. That turns MI into something operational: “How many bits does an LLM add as an extra rater?”

* * *

5) Methodology mythology: common myths + what’s actually true
-------------------------------------------------------------

I’m interpreting your request for “mythological discussions” literally as **myths that papers like this often accidentally propagate**—and what to replace them with.

### Myth 1: “Human–human correlation is the ceiling for human–LLM correlation”

**Reality:** Not when the LLM is compared to the **human mean**. Averaging reduces noise, so correlation with the mean can exceed pairwise correlation.  
**Fix:** Use ICC/reliability of the mean, or compare LLM to individual raters (pairwise), or treat LLM as an additional rater and recompute reliability.

**Where your paper currently leans into the myth:** calling H–H Spearman “the ceiling available to any model.”

Just-Ask-the-Model--One-Shot-LL…

**Suggested resources:**

*   Classical Test Theory and attenuation correction: _Lord & Novick (1968)_; _Spearman (1904)_; _Hunter & Schmidt (2004)_.
*   ICC and reliability of averages: _Shrout & Fleiss (1979)_; _McGraw & Wong (1996)_.

* * *

### Myth 2: “High correlation means the model agrees with humans”

**Reality:** Correlation is insensitive to systematic bias and scale differences. Under central compression, you can have decent rank correlation with poor agreement.  
**Fix:** report concordance (CCC), Bland–Altman, and calibrated vs uncalibrated error.

**Suggested resources:**

*   Agreement vs correlation: _Bland & Altman (1986)_.
*   Concordance correlation: _Lin (1989)_.

* * *

### Myth 3: “Krippendorff’s α between a human mean and an LLM is a clean reliability statistic”

**Reality:** The mean is not a rater; α is designed for raw coder assignments.  
**Fix:** compute α on all raters (humans + LLM as another coder), or switch to ICC framework.

**Suggested resources:**

*   _Krippendorff, Content Analysis_ (latest edition): the definitive α reference and design guidance.

* * *

### Myth 4: “LLM ‘credible intervals’ are probabilistic”

**Reality:** Unless you validate calibration, they’re better treated as _elicited uncertainty intervals_—a behavioral output of the model/prompt.  
**Fix:** evaluate coverage and use proper scoring rules for intervals.

**Suggested resources:**

*   Proper scoring rules / probabilistic forecasts: _Gneiting & Raftery (2007)_.
*   Interval scoring / calibration: _Winkler (1996)_; _Dawid (1984)_.

* * *

### Myth 5: “Mutual information is an objective, estimator-free measure of dependence”

**Reality:** MI is objective in theory, but estimation is fragile at small N and choices matter (binning, k in kNN).  
**Fix:** pre-register estimator choices, show sensitivity, bootstrap CI, keep interpretation modest.

**Suggested resources:**

*   _Cover & Thomas, Elements of Information Theory_.
*   MI estimation survey: _Paninski (2003)_.
*   kNN MI estimator: _Kraskov et al. (2004)_.

* * *

6) Concrete “next steps” and marching orders (LLM-executable)
-------------------------------------------------------------

Below are tasks ordered by impact (P0 highest). I’m writing them so you can paste them into an LLM and get useful diffs / code.

### P0 — Must-fix before making strong claims

**P0.1 Fix “ceiling” framing and rebuild baseline properly**

*   Replace: “H–H Spearman is the ceiling.”
    Just-Ask-the-Model--One-Shot-LL…
*   Add: either (a) ICC-based reliability ceiling, or (b) attenuation-corrected interpretation, or (c) α/ICC with LLM as additional rater.

**LLM marching order prompt**

> You are a psychometrics/statistics editor. Rewrite the sections that describe “human ceiling” and interpret Table 1/Table 2.
> 
> *   Remove any incorrect statement that pairwise human-human Spearman is a hard ceiling for LLM-vs-human-mean correlation.
> *   Propose replacement text using ICC/reliability-of-mean or attenuation correction.
> *   Provide LaTeX-ready equations and a short explanatory paragraph suitable for a broad audience.
> *   Identify any tables/figures that must be updated to match the corrected framing.
>     

* * *

**P0.2 Make “matched sample” consistent**

*   Table 1 currently mixes N=33 models with N=5 and N=8 while claiming identical-paper comparison.
    Just-Ask-the-Model--One-Shot-LL…
    Just-Ask-the-Model--One-Shot-LL…
*   Decide and enforce one of:
    1.  evaluate all models on N=33, or
    2.  restrict the comparison table to models with full coverage and move partials to appendix, or
    3.  create two tables: “full matched” and “partial exploratory.”

**LLM marching order prompt**

> You are a technical editor. Audit every place the paper claims “matched sample” or “identical papers.”
> 
> *   Locate inconsistencies between text and Table 1/2 Ns.
> *   Propose a revised table structure and exact revised captions that are logically correct.
> *   List the minimal code/data steps needed to regenerate the corrected tables.
>     

* * *

**P0.3 Promote uncertainty to the main paper**

*   Add bootstrap CIs for headline metrics, at least for GPT‑5 Pro vs Claude Opus vs Human–Human.
*   Especially important where N is small.
    Just-Ask-the-Model--One-Shot-LL…

**LLM marching order prompt**

> You are a data analyst. Implement paired bootstrap confidence intervals for Spearman, MAE, RMSE, and CCC (if added) comparing each model to the human mean on the matched sample.
> 
> *   Output: a table with point estimates and 95% CIs, plus a figure (forest plot) for Spearman and MAE.
> *   Ensure the bootstrap respects the paired nature (resample papers with replacement).
> *   Provide code + a short “Methods: Uncertainty estimation” paragraph.
>     

* * *

### P1 — High-value methodological upgrades

**P1.1 Add calibration analysis for central compression**

*   Fit slope/intercept, show compression  $b<1$ .
*   Show “after linear calibration” MAE/RMSE and whether ranks change.

**LLM marching order prompt**

> You are a statistician. Add a calibration section that models LLM scores as an affine function of human mean scores per criterion.
> 
> *   Report fitted slope/intercept with CIs.
> *   Interpret slope<1 as central compression.
> *   Compute MAE/RMSE before and after calibration.
> *   Draft 1–2 paragraphs explaining why correlation alone can be misleading under compression.
>     

* * *

**P1.2 Replace / supplement Krippendorff αHL with rater-matrix reliability**  
You already motivate α because it handles varying raters/missingness.

Just-Ask-the-Model--One-Shot-LL…

But compute it on raw raters.

**LLM marching order prompt**

> You are a psychometrician. Recompute Krippendorff’s alpha (or ICC) using the full rater matrix for each criterion: include all human raters and (as applicable) the LLM as an additional rater.
> 
> *   Report alpha\_humans and alpha\_humans+LLM.
> *   Interpret whether the LLM improves reliability of the aggregate.
> *   Provide a clear explanation of why alpha between “human mean” and LLM is conceptually different.
>     

* * *

**P1.3 Validate LLM uncertainty intervals**  
You require intervals for both humans and LLMs.

Just-Ask-the-Model--One-Shot-LL…

Now evaluate them.

**LLM marching order prompt**

> You are a forecasting evaluation expert. Evaluate the calibration and sharpness of LLM-provided 90% intervals for each criterion.
> 
> *   Compute empirical coverage of the human mean falling inside each model’s interval.
> *   Compute an interval score (penalize width + misses).
> *   Provide plots comparing interval widths across humans vs models.
> *   Draft a short section explaining limitations (human mean is noisy).
>     

* * *

**P1.4 Make critique coverage/precision less endogenous**  
You acknowledge LLM-as-judge dependence.

Just-Ask-the-Model--One-Shot-LL…

Do at least one of:

*   human validation on a stratified subsample
*   multi-judge ensemble with agreement
*   switch judge to a different vendor/model than the generator.

**LLM marching order prompt**

> You are a methods auditor. Propose a validation protocol for the key-issue coverage/precision analysis that does NOT rely solely on an LLM judge.
> 
> *   Include: human annotation instructions, sampling scheme, and inter-annotator reliability plan.
> *   Provide a minimal-cost design (e.g., 50–100 issue pairs).
> *   Recommend how to report agreement between humans and the LLM judge.
>     

* * *

### P2 — Longer-horizon, high scientific payoff (you already gesture at many)

You already list strong future-work items: content-swap bias tests, journal-outcome prediction, prompt/model comparisons, human enumerator validation, out-of-time validation, hybrid trials.

Just-Ask-the-Model--One-Shot-LL…

I would add two more that fit your framing:

**P2.1 Test–retest reliability (“jaggedness”) within your pipeline**  
Run each model multiple times per paper (even 3×) and quantify:

*   within-model variance vs between-paper variance
*   stability of rank ordering  
    This directly addresses the “single-run” limitation you note.
    Just-Ask-the-Model--One-Shot-LL…

**P2.2 Many-facet rater modeling (severity + halo)**  
Given your own concern about halo effects and range restriction (citing prior work), a many-facet model can quantify:

*   rater severity (humans and LLM as “raters”)
*   criterion difficulty
*   halo/criterion coupling

* * *

7) Minor / editorial issues (quick wins)
----------------------------------------

1.  **Broken cross-reference:** “Krippendorff’s αHH in ?@tbl-human-baseline …” appears as a placeholder.
    Just-Ask-the-Model--One-Shot-LL…
    Fix before circulation.
2.  **Notation glitches:** “Spearman ff” appears where ρ should appear; looks like encoding/rendering artifacts. This is distracting in a methods-heavy paper.
    Just-Ask-the-Model--One-Shot-LL…
3.  **Clarify what “N” means in Table 1 Human–Human row.** Human–Human N=27 but “matched sample” is 33; you need an explicit definition (e.g., number of papers with ≥2 human raters within the matched set).
    Just-Ask-the-Model--One-Shot-LL…
4.  **Claude Opus extended thinking footnote should be elevated.** It’s a fairness-critical confound, not a minor footnote.
    Just-Ask-the-Model--One-Shot-LL…

* * *

Closing assessment
------------------

This paper is very close to being a “reference” study that others will cite and build on, because the structured Unjournal rubric + multimodal one-shot evaluation setup is unusually clean and practically relevant.

Just-Ask-the-Model--One-Shot-LL…

But to get there, I would treat the **measurement/reliability framing** as the core scientific contribution—and that means you need to:

*   repair the “ceiling” logic,
*   standardize the matched-sample comparisons,
*   and make uncertainty (bootstrap + interval calibration) a first-class citizen in the main text.

If you want, I can also provide a _drop-in replacement_ for the “ceiling” paragraphs + an example “Methods: reliability framing” subsection (written in your style), but the roadmap above should already translate directly into an LLM-assisted revision workflow.



---
Powered by [ChatGPT Exporter](https://www.chatgptexporter.com)