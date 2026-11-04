# Claimed "missed" critiques checked against published Unjournal evaluations

Source: Markdown exports in `data/unjournal_evaluations/` only. Evaluators are referred to by number; names are omitted.

## 1. Acemoglu et al. 2024 (demand for democracy)

Files: `e1demandfordemocracy.md`, `e2demandfordemocracy.md`, `evalsumdemandfordemocracy.md`.

| Claimed critique | Present? | Where / evidence |
|---|---|---|
| Field-experiment significance depends on controlling for the prior election; SE halves (Table 2 cols 1-2) | **Yes, but raised by the evaluation manager, not the evaluators, and explicitly downgraded** | evalsum, manager's discussion: "In Table 2 columns 1-2, the standard error declines by half when the prior election result is included... Without including it, the estimate is too noisy". It continues: "should not be considered a major limitation", because conditioning on the lagged outcome is best practice. |
| Spillovers | Yes | e2: adjacent untreated neighbourhoods in Izmir may have been exposed by word of mouth or pamphlets, so estimates "could be attenuated or biased". Suggests spatial spillover checks. (The manager's text attributes the spatial point to evaluator 1; in the exports it is evaluator 2's.) |
| "Demand for democracy" wording / construct validity | Yes | e2, "Conceptual Framing and Construct Validity": the treatments are performance-based (disasters, corruption; Sections 3.1-3.2) and the outcomes are performance beliefs, so "the conclusion that voters 'demand democracy' is not clearly supported." |
| Post-minus-pre change scores (online experiment) | Yes | e1, citing p.19 §4.6: asks why the pre-treatment-controlled specification is not the main one, and why not use "the difference between post- and pre-treatment values". |

**Flagged as most important:** nothing is flagged strongly. Evaluator 1 says "I have a few concerns and suggestions, but none of them are major." Evaluator 2's summary leads with the framing/treatment mismatch, followed by spillover and compliance. The manager's main ask is for theory on what made the intervention work (mechanism and generalizability), plus alternative estimands (CACE, persuasion rates).

**Central but missing from the claimed list:** evaluator 1's first-listed concern, the ethics of election-interference experiments ("A more robust discussion of the studies' ethics is warranted"); evaluator 1's request for persuasion rates; evaluator 2's compliance heterogeneity (35% delivery, varying by canvasser) and CACE; external validity (the manager and evaluator 2).

## 2. Williams et al. 2024 (natural regeneration)

Files: `evalsumnaturalregeneration.md` (contains the evaluators' joint synthesis report), `e1naturalregeneration.md`, `e2naturalregeneration.md`.

| Claimed critique | Present? | Where / evidence |
|---|---|---|
| (a) Predictors measured over the same period as the outcome (leakage) | Yes | Synthesis, Primary Concern 1: net primary production, burned area, road density and soils "were recorded over the same time period as the outcome", so reported accuracy "overstates true predictive performance". Details in evaluator 2's report, section "1. Data Leakage Concerns". |
| (b) 215 Mha vs the 31.6 Mha Fagan et al. benchmark, no hindcast | Yes | Synthesis, Primary Concern 3: 215 Mha is "strikingly larger" than Fagan et al. (2022), 31.6 ± 11.9 Mha for 2000-2016; no hindcast is reported, "a crucial missing validation". |
| (c) "Validation" compares 2030 predictions with 2000-2016 outcomes | Yes | Synthesis, "Other Issues" (i): the confusion matrix in Table A1.2 compares 2030 predictions with Fagan 2000-2016 regrowth, which is "not a true test" of predictive power. |

**Flagged as most important:** the synthesis lists three "Primary Concerns" (leakage; confounding by socioeconomic factors and predictor choice; magnitude and no historical validation). It says these "fundamentally challenge the validity and utility of the central 215 Mha estimate". The evalsum abstract repeats all three. Claims (a) and (b) are primary concerns. Claim (c) is a secondary "other issue".

**Central but missing:** Primary Concern 2. Dropping socioeconomic predictors "diminishes" the model's ability to isolate biophysical potential, and distance to forest and forest density are partly anthropogenic, so the outputs are not purely biophysical. Evaluator 1's summary makes the same point. Also missing: 92% user's accuracy implies at least ~197.8 Mha of ground-truth regrowth vs ~5.4 Mha in training; additionality; ephemeral regrowth; narrow CIs.

## 3. Dullaghan and Zhang 2022 (cultured meat forecasts)

Files: `e1limitedmeatprod.md`, `e2limitedmeatprod.md`, `evalsumlimitedmeadprod.md`.

| Claimed critique | Present? | Where / evidence |
|---|---|---|
| (a) Forecasts conditional on >10 kt read as unconditional evidence of consumer acceptance | Yes (evaluator 1, plus a manager's note inside evaluator 1's published report that evaluator 1 endorsed) | e1, "Consumer acceptance, misinterpretation of conditional probabilities": the conditionality "effectively screens off correlation" and "undermines the claim that 'consumer approval did not appear as a major constraint'". The manager's note quotes the question wording ("Conditional upon >10 cumulative metric kilotons..."). |
| (b) 1000x units error (FGF2 per kg vs per gram) in the table given to forecasters | Yes (evaluator 1) | e1, "Magnitude of units error in the table for Delft overstating the cost of FGF2 1000x": the table for question 24 gives Delft's FGF2 cost per kg where the source (its Table 3) is per gram. Delft then looks ~3,000x Humbird instead of ~3x. Called "a potentially critical issue". The evalsum abstract mentions "at least one ~typo... leaning towards pessimism". |

**Flagged as most important:** evaluator 1 finds "several minor issues with the first set of topics (methodology) but very major issues with the second set (framing and conclusions)". On that framing side, "Critically", the techno-economic analyses (TEAs) were not presented as "conditional estimates, not predictions", and the high-price scenarios used the costs of the time, which have since fallen. Evaluator 2's "primary concern" is that the forecasts are now out of date (2020-21 inputs, mainly the Humbird TEA). The evalsum stresses overly pessimistic choices, newer TEAs, and the luxury-product path. The two claimed critiques are real, but evaluator 1 files both under methods and results reporting, not under the "very major" framing issues.

**Central but missing:** TEAs presented as predictions; luxury-product adoption left out; aggregates hiding disagreement (9% headline vs two forecasters >40%); small sample with no discussion or updating; staleness and the cultured-meat definition (evaluator 2).

## 4. Frech et al. 2023 (pharmaceutical pricing as a global public good)

Files: `e1pharmpricing.md`, `e2pharmpricing.md`, `evalsumpharmpricing.md`.

| Claimed critique | Present? | Where / evidence |
|---|---|---|
| $40k/QALY back-of-envelope stated without sensitivity analysis | **Partly** | e2, in the section on U.S. prices being below optimal: the ~$40,000/QALY figure is taken from the authors' earlier study, and the commonly accepted value is $100,000. Evaluator 2 calls the claim "sensible" but raises "two main criticisms of these back-of-the-envelope calculations": cost-effectiveness estimates "are generally highly sensitive" to assumptions, and they vary widely by indication (e.g. oncology). Evaluator 2 never says the paper lacks a sensitivity analysis, and does not treat this as central. Evaluator 1 does not raise it. |

**Flagged as most important:** the evalsum and the manager say "Both evaluators questioned the practical credibility of the claim that ROW 'should' pay more", citing U.S. pricing systems, insurance and bargaining power. Evaluator 1's first main comment: the primary regression is "overly simplistic and may be subject to omitted variable bias", with no endogeneity or general-equilibrium treatment, so the higher-ROW-prices recommendation is "not fully supported". Evaluator 2's summary critiques: the tests are correlational, the theory assumes optimal centralized government action, and the policy prescriptions need validation.

**Central but missing:** omitted variables and reverse causality in the GDP regression; no general-equilibrium or supply side; the centralized-optimizer assumption; the risk of misuse to justify higher prices (manager).

## 5. Clancy 2024 (returns to science with technological risks)

Files: `e2technologicalrisks.md` (Evaluation 2), `e3technologicalrisks.md` (Evaluation 3), `ar_returnstoscience.md` (author response). `e1technologicalrisks.md` holds only the paper's arXiv description, so Evaluation 1's report is not in the exports. There is no `evalsum*` file for this paper.

| Claimed critique | Present? | Where / evidence |
|---|---|---|
| Compares all benefits of science with biotech risk only, leaving out AI risk | Yes (evaluator 3; briefly evaluator 2) | e3 abstract: the paper seems to make "a large mistake by comparing 'all of the benefits' of science... versus 'only the technical risks of biocatastrophe'". e3 notes that XPT AI estimates are ~38x the bio ones. e2, last row of its parameter table: the biocatastrophe parameter "might be considered a lower bound as it does not account for any contributions to other existential risks". |
| 2% discount rate justified inconsistently | Yes (evaluator 2) | e2, row for p = 0.98: the author dismisses XPT-implied rates (0.05-0.7%) because extrapolating past 2100 is inappropriate. Yet the adopted ~2% is "mainly driven by the 1.6% annual probability of transformative AI" from a contest about AGI before 2043, "Hence it is subject to the same criticism." Evaluator 2 suggests reporting thresholds for lower p. |

**Flagged as most important:** evaluator 3 found the biocatastrophe parameters "check out". It calls the AI-exclusion issue "much more important in terms of 'what to make of this paper'" and "My major worry". The author response's longest section is "Modeling AI Risk". Evaluator 2 rates the methodology as transparent and points to "minor flaws" in parameter choices; it does not single out the discount rate as central.

**Central but missing:** evaluator 2's other parameter points (g = 0 if science stops; zero mortality for pandemics killing 0-1%); evaluator 3 on weighting superforecasters over domain experts. Evaluation 1 cannot be checked from these exports; the author response says it cautions against extrapolating to large-scale changes.

## 6. Green et al. 2025 (reducing meat and animal-product consumption meta-analysis)

Files: `e1reducingconsumption.md`, `e2reducingconsumption.md`, `evalsumreducingconsumption.md`.

| Claimed critique | Present? | Where / evidence |
|---|---|---|
| Imputing SMD = 0.01 for unreported non-significant effects | Yes (evaluator 2) | e2: "A central concern... The authors imputed a fixed SMD of 0.01". This ignores imputation variance, over-weights imputed studies, tightens CIs, and puts an artificial column into the funnel plot (paper's Fig. 3). Suggests multiple imputation (metansue, or metafor plus mice). |
| Excluding n<25 studies limits publication-bias detection | Yes (evaluator 2) | e2, "Not including small studies": the exclusion of <25 per group is "unwarranted". It makes "publication bias harder to correct for and harder to detect" by restricting the SE range. At least 16 studies were excluded on size alone. |

**Flagged as most important:** evaluator 2 calls the 0.01 imputation "a central concern". Its summary lists "major methodological issues": missing-data handling, small-study exclusion, guessing in effect-size coding, no serious risk-of-bias assessment, and one outcome per study. Evaluator 1's summary centres on non-systematic methods: a Google Scholar search instead of bibliographic databases ("a strong likelihood studies have been missed"), no consistency checks on screening and extraction, and a weak risk-of-bias assessment. For the manager, the "central point" is the high degree of researcher judgment throughout. The evalsum abstract highlights search strategy, inclusion criteria, outcome selection and missing data.

**Central but missing:** all of evaluator 1's critique (search strategy, no PRISMA/ROSES, no cross-checking, risk of bias); evaluator 2's effect-size guesswork, single outcome per intervention, inconsistent prediction intervals, and selective outcome reporting.

## Cross-cutting notes

- 13 of the 14 claimed critiques appear in the published record. The exception is Frech's $40k/QALY point, which is only partly there. The Frech point and the Acemoglu prior-election point are not treated as central. The Acemoglu point comes from the evaluation manager, who explicitly calls it not a major limitation.
- In several papers the published record treats a different issue as the most important one, and the claimed list omits it: Williams (socioeconomic confounding), Dullaghan (TEAs as conditional estimates; staleness), Frech (the ROW "should pay more" credibility; omitted variables), Green (non-systematic search and risk of bias), Acemoglu (ethics; mechanism and external validity).
