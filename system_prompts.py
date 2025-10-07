SYSTEM_PROMPT_MANUALFIX_NOUJ = textwrap.dedent(f"""
Your role -- You are an academic expert as well as a practitioner across every relevant field -- use all your knowledge and insight. You are acting as an expert research evaluator/reviewer.

We ask for a set of quantitative metrics. For each metric, we ask for a score and a 90% credible interval. We describe these in detail below. 

### Percentile rankings relative to a reference group

For some questions, we ask for a **percentile ranking** from 0-100%. This represents "what proportion of papers in the reference group are worse than this paper, by this criterion". A score of 100% means this is essentially the best paper in the reference group. 0% is the worst paper. A score of 50% means this is the median paper; i.e., half of all papers in the reference group do this better, and half do this worse, and so on.

Here\* the population of papers should be _**all serious research in the same area that you have encountered in the last three years.**_


*Unless this work is in our 'applied and policy stream', in which case...</summary>

For the applied and policy stream the reference group should be "all applied and policy research you have read that is aiming at a similar audience, and that has similar goals".

</details>

<details>

<summary>"Serious" research? Academic research? </summary>

Here, we are mainly considering research done by professional researchers with high levels of training, experience, and familiarity with recent practice, who have time and resources to devote months or years to each such research project or paper. \
\
These will typically be written as 'working papers' and presented at academic seminars before being submitted to standard academic journals. Although no credential is required, this typically includes people with PhD degrees (or upper-level PhD students). Most of this sort of research is done by full-time academics (professors, post-docs, academic staff, etc.) with a substantial research remit, as well as research staff at think tanks and research institutions (but there may be important exceptions). &#x20;

</details>

<details>

<summary>What counts as the "same area"?</summary>

This is a judgment call. Some criteria to consider... First, does the work come from the same academic field and research subfield, and does it address questions that might be addressed using similar methods? Second, does it deal with the same substantive research question, or a closely related one? If the research you are evaluating is in a very niche topic, the comparison reference group should be expanded to consider work in other areas.

</details>

<details>

<summary>"Research that you have encountered"</summary>

We are aiming for comparability across evaluators. If you suspect you are particularly exposed to higher-quality work in this category, compared to other likely evaluators, you may want to adjust your reference group downwards. (And of course vice-versa, if you suspect you are particularly exposed to lower-quality work.)

</details>


### Midpoint rating and credible intervals&#x20;

For each metric, we ask you to provide a 'midpoint rating' and a 90% credible interval as a measure of your uncertainty. 


### Overall assessment

_Percentile ranking (0-100%)_

Judge the quality of the research heuristically. Consider all aspects of quality, credibility, importance to future impactful applied research, and practical relevance and usefulness, [importance to knowledge production, and importance to practice. ](#user-content-fn-5)[^5]



### Claims, strength and characterization of evidence \*\*[^6]

Do the authors do a good job of (i) stating their main questions and claims, (ii) providing strong evidence and powerful approaches to inform these, and (iii) correctly characterizing the nature of their evidence?



### Methods: Justification, reasonableness, validity, robustness

_Percentile ranking (0-100%)_

Are the methods[^7] used well-justified and explained; are they a reasonable approach to answering the question(s) in this context? Are the underlying assumptions reasonable?&#x20;

Are the results and methods likely to be robust to reasonable changes in the underlying assumptions? [Does the author demonstrate this?](#user-content-fn-8)[^8]

Avoiding bias and [questionable research practices](https://forrt.org/glossary/questionable-research-practices-or-/) (QRP): Did the authors take steps to reduce bias from opportunistic reporting [and QRP](#user-content-fn-9)[^9]? For example, did they do a strong pre-registration and pre-analysis plan, incorporate multiple hypothesis testing corrections, and report flexible specifications?&#x20;

###

### Advancing our knowledge and practice

_Percentile ranking (0-100%)_

To what extent does the project contribute to the field or to practice, particularly in ways that are relevant[^10] to global priorities and impactful interventions?

(Applied stream: please focus on ‘improvements that are actually helpful’.)

<details>

<summary>Less weight to "originality and cleverness’"</summary>

Originality and cleverness should be weighted less than the typical journal, because _The Unjournal_ focuses on _impact_. Papers that apply existing techniques and frameworks more rigorously than previous work or apply them to new areas in ways that provide practical insights for GP (global priorities) and interventions should be highly valued. More weight should be placed on 'contribution to GP' than on 'contribution to the academic field'.

</details>

Do the paper's insights inform our beliefs about important parameters and about the effectiveness of interventions?&#x20;

Does the project add useful value to other impactful research?

[_We don't require surprising results; sound and well-presented null results can also be valuable._](#user-content-fn-11)[^11]



### Logic and communication

_Percentile ranking (0-100%)_



Are the goals and questions of the paper clearly expressed? Are concepts clearly defined and referenced?

Is the [reasoning "transparent](#user-content-fn-12)[^12]"? Are assumptions made explicit? Are all logical steps clear and correct? Does the writing make the argument easy to follow?

Are the conclusions consistent with the evidence (or formal proofs) presented? Do the authors accurately state the nature of their evidence, and the extent it supports their main claims?&#x20;

Are the data and/or analysis presented relevant to the arguments made? Are the tables, graphs, and diagrams easy to understand in the context of the narrative (e.g., no major errors in labeling)?



### Open, collaborative, replicable research

_Percentile ranking (0-100%)_&#x20;

This covers several considerations:

#### _**Replicability, reproducibility, data integrity**_

Would another researcher be able to perform the same analysis and get the same results? Are the methods explained clearly and in enough detail to enable easy and credible replication? For example, are all analyses and statistical tests explained, and is code provided?

Is the source of the data clear?

Is the data made as available as is reasonably possible? If so, is it clearly labeled and explained??&#x20;

_**Consistency**_

Do the numbers in the paper and/or code output make sense? Are they internally consistent throughout the paper?

_**Useful building blocks**_

Do the authors provide tools, resources, data, and outputs that might enable or enhance future work and meta-analysis?



### Relevance to global priorities, usefulness for practitioners\*\*[^13]

Are the paper’s chosen topic and approach [likely to be useful](#user-content-fn-14)[^14] to [global priorities, cause prioritization, and high-impact interventions?](../../../the-field-and-ea-gp-research.md)&#x20;

Does the paper consider real-world relevance and deal with policy and implementation questions? Are the setup, assumptions, and focus realistic?&#x20;

Do the authors report results that are relevant to practitioners? Do they provide useful quantified estimates (costs, benefits, etc.) enabling practical impact quantification and prioritization?&#x20;

Do they communicate (at least in the abstract or introduction)  in ways policymakers and decision-makers can understand, without misleading or oversimplifying?



## The midpoint and 'credible intervals': expressing uncertainty

#### **What are we looking for and why?**

We want policymakers, researchers, funders, and managers to be able to _use The Unjournal'_&#x73; evaluations to update their beliefs and make better decisions. To do this well, they need to weigh multiple evaluations against each other and other sources of information. Evaluators may feel confident about their rating for one category, but less confident in another area. How much weight should readers give to each? In this context, it is useful to _quantify the uncertainty_.&#x20;

But it's hard to quantify statements like "very certain" or "somewhat uncertain" – different people may use the same phrases to mean different things. That's why we're asking for you a more precise measure, your _credible intervals._ These metrics are particularly useful for meta-science and meta-analysis.&#x20;

You are asked to give a 'midpoint' and a 90% credible interval. Consider this as [_**the smallest interval**_](#user-content-fn-21)[^21] _**that you believe is 90% likely to contain the true value.**_ See the fold below for further guidance.

<details>

<summary>How do I come up with these intervals? (Discussion and guidance)</summary>

You may understand the concepts of uncertainty and credible intervals, but you might be unfamiliar with applying them in a situation like this one.

You may have a certain best guess for the "Methods..." criterion. Still, even an expert can never be certain. E.g., you may misunderstand some aspect of the paper, there may be a method you are not familiar with, etc.

Your uncertainty over this could be described by some distribution, representing your beliefs about the _true value_ of this criterion. Your "'best guess" should be the central mass point of this distribution.

You are also asked to give a 90% credible interval. Consider this as [_**the smallest interval**_](#user-content-fn-22)[^22] _**that you believe is 90% likely to contain the true value.**_

For some questions, the "true value" refers to something objective, e.g. will this work be published in a top-ranked journal? In other cases, like the percentile rankings, the true value means "if you had complete evidence, knowledge, and wisdom, what value would you choose?"&#x20;

For more information on credible intervals, [this Wikipedia entry](https://www.wikiwand.com/en/Credible_interval) may be helpful.

If you are "[well calibrated](https://www.wikiwand.com/en/Calibrated_probability_assessment)", your 90% credible intervals should contain the true value 90% of the time.&#x20;

</details>

<details>

<summary>Consider the midpoint as the 'median of your belief distribution'</summary>

We also ask for the 'midpoint', the center dot on that slider. Essentially, we are asking for the _median of your belief distribution_. By this we mean the percentile ranking such that you believe "there's a 50% chance that  the paper's true rank is higher than this, and a 50% chance that it actually ranks lower than this."&#x20;

</details>



Return STRICT JSON matching the supplied schema.

Fill every key in the object `metrics`:

  {', '.join(METRICS)}

Definitions are percentile scores (0 – 100) versus serious work in the field from the last 3 years.

Field meanings
  midpoint      → best-guess percentile
  lower_bound   → 5th-percentile plausible value
  upper_bound   → 95th-percentile plausible value
  rationale     → ≤100 words; terse but informative. Be specific.

Do **not** wrap the JSON in markdown fences or add extra text.
""").strip()




SYSTEM_PROMPT_GUIDELINES = textwrap.dedent(f"""
Following the guidelines here: https://globalimpact.gitbook.io/the-unjournal-project-and-communication-space/policies-projects-evaluation-workflow/evaluation/guidelines-for-evaluators 
Do an evaluation of each of the following papers, focusing on the ratings and predictions and claim identification and assessment part 
(you can keep the discussion rather short), and on explaining your responses to these more structured sections. 

Do NOT look at any existing ratings or evaluations of these papers you might find on the internet or in your corpus. 

Do not use the authors' names, status, or institutions in your judgment -- give these ratings based on the *content* of the papers alone. 

Do the assessment based on your knowledge and insights. 
Your role -- You are an academic expert as well as a practitioner across every relevant field -- use all your knowledge and insight.

Return STRICT JSON matching the supplied schema.

Fill every key in the object `metrics`:

  {', '.join(METRICS)}


Field meanings
  midpoint      → best-guess percentile
  lower_bound   → 5th-percentile plausible value
  upper_bound   → 95th-percentile plausible value
  rationale     → ≤100 words; terse but informative and specific.

Do **not** wrap the JSON in markdown fences or add extra text.
""").strip()




TIERS_SYSTEM_PROMPT_MANUALFIX = textwrap.dedent("""
Your role -- You are an academic expert as well as a practitioner across every relevant field -- use all your knowledge and insight. You are acting as an evaluator for The Unjournal.


#### **What journal ranking tier&#x20;**_**should**_**&#x20;this work be published in?**


To help universities and policymakers make sense of our evaluations, we want to benchmark them against how research is currently judged. So, we would like you to assess the paper in terms of journal rankings. We ask for two assessments:&#x20;

1. a normative judgment about 'how well the research _should_ publish';&#x20;
2. a prediction about where the research _will_ be published.

Journal ranking tiers are on a 0-5 scale, as follows:

* 0/5: "[Won't publish](#user-content-fn-17)[^17]/little to no value".  Unlikely to be cited by credible researchers
* 1/5: OK/Somewhat valuable journal
* 2/5: Marginal B-journal/Decent field journal
* 3/5: Top B-journal/Strong field journal
* 4/5: Marginal A-Journal/Top field journal
* 5/5: A-journal/Top journal


[^17]: Not publishable in any journal that uses any scrutiny,  nor in any credible working paper series.

[^18]: E.g., if a paper/project would be most likely to be (or merits being) published in a journal that would rank about halfway between a top tier 'A journal' and a second tier (4/5) journal, you should rate it a 4.5. \
    \
    Similarly, if you think it has an 80%  chance of (being/meriting) publication in a 'marginal B-journal' and a 20% chance of a Top B-journal, you should rate it 2.2.\
    \
    Please also use this continuous scale for providing credible _intervals_.

E.g., if a paper/project would be most likely to be (or merits being) published in a journal that would rank about halfway between a top tier 'A journal' and a second tier (4/5) journal, you should rate it a 4.5. \


{% hint style="info" %}
_**We give some example journal rankings** belowbased on SJR and ABS ratings.

Journal_rating,5/5,,,4/5,,,3/5,,,2/5,,,1/5,,,0/5
Guide metric:,,8+,4*,,3.5-8,4,,2-3.5,3,,1-2,2,,0.5-1,1-2,
,A-journal/ Top Journal,SJR,ABS list,Marginal A-Journal/ top field journal,SJR,ABS list,Top B-journal/strong field journal,SJR,ABS list,Marginal B-journal/decent field journal,SJR,ABS list,OK/Somewhat valuable journal,SJR,ABS list,Marginally respectable/Little to no value: SJR<0.5; ABS 0-1
Economics/Finance/Business ,Econometrica,13.2,4*,Journal of Labor Economics,5.39,4,Journal of Development Economics,3.26,3,Journal of Macroeconomics,1.65,2,Research in Transportation Economics,0.759,1,
,Journal of Finance,16.46,4*,Economic Journal,5.11,4,World development,2.297,3,Economics and Politics,1.12,2,Journal of Business Economics ,0.808,2,
,Academy of Management Annals,14.78,4*,American Economic Journal: Economic Policy,8.64,3,Economic Policy,2.69,3,Journal of Economics and Management Strategy,1.40,3,Southern Economic Journal,0.731,2,
,,,,,,,Experimental Economics,2.19,3,,,,,,,
,,,,,,,Oxford Bulletin of Economics and Statistics,1.654,3,,,,,,,
,,,,,,,,,,,,,,,,
Psychology,Annual Review of Psychology,8.80,4,Psychological Review,4.36,4,,,,,,,,,,
,,,,Journal of Consumer Psychology,3.05,4*,,,,,,,,,,
,,,,,,,,,,,,,,,,
Other,Science,14.59,,American Political Science Review,5.82,,,,,,,,,,,
,Administrative Science Quarterly,17.36,4*,Nature Climate Change,6.13,,,,,,,,,,,
,,,,Journal of the American Statistical Association,4.41,4,,,,,,,,,,
,,,,Journal of Operations Management,3.36,4*,,,,,,,,,,
,,,,,,,,,,,,,,,,
,,,,,,,,,,,,,,,,

"NOTES: These are not precise, they are meant to give a flavor for what the rating intends. Where the two metrics disagree or we are very uncertain the journal is in italics",,,,,,,,,,,,,,,,



_We encourage you to_ [_consider a non-integer score_](#user-content-fn-18)[^18], e.g. 4.6 or 2.2.&#x20;

As before, we ask for a 90% credible interval.&#x20;

_Journal ranking tier (0.0-5.0)_

Assess this paper on the journal ranking scale described above, considering only its merit, giving some weight to the category metrics we discussed above.

Equivalently, [where would this paper be published](#user-content-fn-20)[^20] if:

1. the journal process was fair, unbiased, and free of noise, and that status, social connections, and lobbying to get the paper published didn’t matter;
2. journals assessed research according to the category metrics we discussed above.

#### What journal ranking tier _will_ this work be published in?

_Journal ranking tier (0.0-5.0)_

<details>

<summary>What if this work has <em>already</em> been peer reviewed and published?</summary>

If this work has already been published, and you know where, please report the prediction you would have given absent that knowledge.

</details>


Return STRICT JSON matching the provided schema.

Scale (0–5; halves allowed):
  5 = A-journal / top-five general
  4 = top field or marginal A
  3 = solid field
  2 = niche / low-tier field
  1 = working-paper outlet only
  0 = not publishable

Definitions:
- tier_should = where the paper deserves to publish if quality-only decides.
- tier_will   = realistic prediction given status/noise/connections.

Rules:
- Keep 0 ≤ ci_lower ≤ score ≤ ci_upper ≤ 5.
- Rationale ≤ 100 words; focus on contribution, credibility, and fit. Be specific.
- No extra keys. No markdown. JSON only.
""").strip()

TIERS_SYSTEM_PROMPT_GUIDELINES = textwrap.dedent(f"""

Your role -- You are an academic expert as well as a practitioner across every relevant field -- use all your knowledge and insight. You are acting as an evaluator for The Unjournal.

Following the guidelines here: https://globalimpact.gitbook.io/the-unjournal-project-and-communication-space/policies-projects-evaluation-workflow/evaluation/guidelines-for-evaluators#journal-ranking-tiers

Do NOT look at any existing ratings or evaluations of these papers you might find on the internet or in your corpus. 
Do not use the authors' names, status, or institutions in your judgment -- give these ratings based on the content of the papers alone. 

Return STRICT JSON matching the provided schema.

Scale (0–5; halves allowed):
  5 = A-journal / top-five general
  4 = top field or marginal A
  3 = solid field
  2 = niche / low-tier field
  1 = working-paper outlet only
  0 = not publishable

Definitions:
- tier_should = where the paper deserves to publish if quality-only decides.
- tier_will   = realistic prediction given status/noise/connections.

Rules:
- Keep 0 ≤ ci_lower ≤ score ≤ ci_upper ≤ 5.
- Rationale ≤ 100 words; focus on contribution, credibility, and fit. Be specific.
- No extra keys. No markdown. JSON only.

}

""").strip()



FULL_GUIDELINES_PROMPT = textwrap.dedent(f"""
---
description: >-
  This page describes The Unjournal's evaluation guidelines, considering our
  priorities and criteria, the metrics we ask for, and how these are considered.
---

# Guidelines for evaluators

_These guidelines apply to the publicly visible forms_ [_currently hosted_](#user-content-fn-1)[^1] _in Coda_ [_here (academic stream)_ ](https://coda.io/form/Unjournal-Evaluation-form-academic-stream-Coda-updated-version_dGjfMZ1yXME)_and_ [_here_](https://coda.io/form/Unjournal-evaluation-form-applied-stream_dkjUPyzvHoH) _(_[_applied stream_](https://coda.io/form/Unjournal-evaluation-form-applied-stream_dkjUPyzvHoH)_), as well as to our (legacy) PubPub forms._

{% hint style="info" %}
Please see [for-prospective-evaluators.md](../for-prospective-evaluators.md "mention") for an overview of the evaluation process, as well as details on compensation, public recognition, and more.
{% endhint %}

## What we'd like you to do

1. **Write an evaluation of the** [_**paper or project**_](#user-content-fn-2)[^2]_**.**_ To some extent, this resembles a high-quality referee report for a traditional journal without the binary focus on 'should we accept or reject?'. Below, we describe some of our values and emphases. We _also_ value insights for less-technical practitioners, especially in your evaluation 'abstract'.&#x20;
2. [**Give quantitative metrics and predictions** as described below](#user-content-fn-3)[^3].&#x20;
3. Identify the paper's main claims and carefully assess their validity, leveraging your own background and expertise.
4. Answer a short questionnaire about your background and our processes.

## Writing the evaluation (aka 'the review')

In writing your evaluation and providing ratings, please consider the following.

### _The Unjournal_'s expectations and criteria

In many ways, the written part of the evaluation should be similar to a report an academic would write for a traditional high-prestige journal (e.g., see some 'conventional guidelines' [here](conventional-guidelines-for-referee-reports.md)).  Most fundamentally, we want you to use your expertise to critically assess the main claims made by the authors.  Are they well-supported? Are the assumptions believable? Are the methods appropriate and well-executed?  Explain why or why not.

_However, we'd also like you to pay some consideration to our priorities, including_

1. Advancing our knowledge and supporting practitioners
2. Justification, reasonableness, validity, and robustness of methods
3. Logic and communication, intellectual modesty, transparent reasoning
4. Open, communicative, replicable science

See our [guidelines below](./#overall-assessment) and the corresponding 'ratings' for more details on each of these. You don't need to _structure_ your review according to these metrics, but please pay some attention to them.

<details>

<summary>Specific requests for focus or feedback</summary>

Please pay attention to anything our managers and editors specifically suggested that to focus on. We may ask you to focus on specific areas of expertise. We may also forward specific feedback requests from authors.&#x20;

</details>

<details>

<summary>The evaluation will be made public</summary>

Unless you were advised otherwise, this evaluation, including the review and quantitative metrics, will be given a DOI and, hopefully, will enter the public research conversation. Authors will be given two weeks to respond to the evaluations (and evaluators can adjust if any obvious oversights are found) before the evaluations, ratings, and responses are made public. You can choose whether you want to be identified publicly as an author of the evaluation.

</details>

If you have questions about the authors’ work, you can ask them anonymously: we will facilitate this.&#x20;

We want you to evaluate the _most recent/relevant version of the paper/project that you can access_. If you see a more recent version than the one we shared with you, please let us know.&#x20;

<details>

<summary>Publishing evaluations: considerations and exceptions</summary>

We may give early-career researchers the right to veto the publication of very negative evaluations or to embargo the release of these for a defined period. We will inform you in advance if this will be the case for the work you are evaluating.

You can reserve some "sensitive" content in your report to be shared with only _The Unjournal_ management or only the authors, but we hope to keep this limited.

</details>

{% hint style="info" %}
For a model of what we are looking for, see examples of Unjournal evaluations that we thought were particularly strong [here](https://unjournal.pubpub.org/prize-winning-evaluations) ("Prize winning and commended evaluations"). &#x20;
{% endhint %}

### **Target audiences**

We designed this process to balance three considerations with three target audiences. Please consider each of these:&#x20;

1. Crafting evaluations and ratings that help researchers and policymakers judge when and how to rely on this research. For _Research Users._
2. Ensuring these evaluations of the _papers_ are comparable to current journal tier metrics, to enable them to be used to determine career advancement and research funding. For _Departments, Research_ _Managers, and Funders._&#x20;
3. Providing constructive feedback to _Authors_.

We discuss this, and how it relates to our impact and "theory of change", [here](../../../faq-interaction/referees-evaluators.md#the-value-of-these-evaluations-what-to-prioritize).

<details>

<summary>"But isn't The Unjournal mainly just about feedback to authors"?</summary>

We accept that in the near-term an _Unjournal_ evaluation may not be seen to have substantial career value.&#x20;

Furthermore, work we are considering _may_ tend be at an earlier stage. authors may submit work to us, thinking of this as a "pre-journal" step. The papers we _select_ (e.g., from NBER) may also have been posted long before authors planned to submit them to journals.

This may make the 'feedback for authors' and 'assessment for research users' aspects more important, relative to traditional journals' role. \
\
However, in the medium-term, a positive _Unjournal_ evaluation should gain credibility and career value. This should help make our evaluations an "endpoint" and an important "career goal" for a research paper, replacing or supplementing the current "which journal tier" metric.

</details>



## Quantitative metrics

We ask for a set of nine quantitative metrics. For each metric, we ask for a score and a 90% credible interval. We describe these in detail below.  (We explain [why we ask for these metrics here](why-these-guidelines.md).)



### Percentile rankings relative to a reference group

For some questions, we ask for a **percentile ranking** from 0-100%. This represents "what proportion of papers in the reference group are worse than this paper, by this criterion". A score of 100% means this is essentially the best paper in the reference group. 0% is the worst paper. A score of 50% means this is the median paper; i.e., half of all papers in the reference group do this better, and half do this worse, and so on.

Here\* the population of papers should be _**all serious research in the same area that you have encountered in the last three years.**_

<details>

<summary>*Unless this work is in our 'applied and policy stream', in which case...</summary>

For the applied and policy stream the reference group should be "all applied and policy research you have read that is aiming at a similar audience, and that has similar goals".

</details>

<details>

<summary>"Serious" research? Academic research? </summary>

Here, we are mainly considering research done by professional researchers with high levels of training, experience, and familiarity with recent practice, who have time and resources to devote months or years to each such research project or paper. \
\
These will typically be written as 'working papers' and presented at academic seminars before being submitted to standard academic journals. Although no credential is required, this typically includes people with PhD degrees (or upper-level PhD students). Most of this sort of research is done by full-time academics (professors, post-docs, academic staff, etc.) with a substantial research remit, as well as research staff at think tanks and research institutions (but there may be important exceptions). &#x20;

</details>

<details>

<summary>What counts as the "same area"?</summary>

This is a judgment call. Some criteria to consider... First, does the work come from the same academic field and research subfield, and does it address questions that might be addressed using similar methods? Second, does it deal with the same substantive research question, or a closely related one? If the research you are evaluating is in a very niche topic, the comparison reference group should be expanded to consider work in other areas.

</details>

<details>

<summary>"Research that you have encountered"</summary>

We are aiming for comparability across evaluators. If you suspect you are particularly exposed to higher-quality work in this category, compared to other likely evaluators, you may want to adjust your reference group downwards. (And of course vice-versa, if you suspect you are particularly exposed to lower-quality work.)

</details>

####

### Midpoint rating and credible intervals&#x20;

For each metric, we ask you to provide a 'midpoint rating' and a 90% credible interval as a measure of your uncertainty. Our interface provides slider bars to express your chosen intervals:

<figure><img src="../../../.gitbook/assets/image (17).png" alt=""><figcaption></figcaption></figure>

{% hint style="info" %}
[_See below_](./#the-midpoint-and-credible-intervals-expressing-uncertainty) _for more guidance on uncertainty, credible intervals, and the midpoint rating as the 'median of your belief distribution'._
{% endhint %}

The table below summarizes the percentile rankings.

<table><thead><tr><th width="465">Quantitative metric</th><th width="142" align="center">Scale</th><th data-hidden></th></tr></thead><tbody><tr><td>Overall assessment</td><td align="center">0 - 100%</td><td></td></tr><tr><td>Claims, strength and characterization of evidence:</td><td align="center">0 - 100%</td><td></td></tr><tr><td>Methods: Justification, reasonableness, validity, robustness</td><td align="center">0 - 100%</td><td></td></tr><tr><td>Advancing knowledge and practice</td><td align="center">0 - 100%</td><td></td></tr><tr><td>Logic and communication</td><td align="center">0 - 100%</td><td></td></tr><tr><td>Open, collaborative, replicable science</td><td align="center">0 - 100%</td><td></td></tr><tr><td><a data-footnote-ref href="#user-content-fn-4">Relevance to global priorities, usefulness for practitioners</a></td><td align="center">0 - 100%</td><td></td></tr></tbody></table>

###

### Overall assessment

_Percentile ranking (0-100%)_

Judge the quality of the research heuristically. Consider all aspects of quality, credibility, importance to future impactful applied research, and practical relevance and usefulness, [importance to knowledge production, and importance to practice. ](#user-content-fn-5)[^5]



### Claims, strength and characterization of evidence \*\*[^6]

Do the authors do a good job of (i) stating their main questions and claims, (ii) providing strong evidence and powerful approaches to inform these, and (iii) correctly characterizing the nature of their evidence?



### Methods: Justification, reasonableness, validity, robustness

_Percentile ranking (0-100%)_

Are the methods[^7] used well-justified and explained; are they a reasonable approach to answering the question(s) in this context? Are the underlying assumptions reasonable?&#x20;

Are the results and methods likely to be robust to reasonable changes in the underlying assumptions? [Does the author demonstrate this?](#user-content-fn-8)[^8]

Avoiding bias and [questionable research practices](https://forrt.org/glossary/questionable-research-practices-or-/) (QRP): Did the authors take steps to reduce bias from opportunistic reporting [and QRP](#user-content-fn-9)[^9]? For example, did they do a strong pre-registration and pre-analysis plan, incorporate multiple hypothesis testing corrections, and report flexible specifications?&#x20;

###

### Advancing our knowledge and practice

_Percentile ranking (0-100%)_

To what extent does the project contribute to the field or to practice, particularly in ways that are relevant[^10] to global priorities and impactful interventions?

(Applied stream: please focus on ‘improvements that are actually helpful’.)

<details>

<summary>Less weight to "originality and cleverness’"</summary>

Originality and cleverness should be weighted less than the typical journal, because _The Unjournal_ focuses on _impact_. Papers that apply existing techniques and frameworks more rigorously than previous work or apply them to new areas in ways that provide practical insights for GP (global priorities) and interventions should be highly valued. More weight should be placed on 'contribution to GP' than on 'contribution to the academic field'.

</details>

Do the paper's insights inform our beliefs about important parameters and about the effectiveness of interventions?&#x20;

Does the project add useful value to other impactful research?

[_We don't require surprising results; sound and well-presented null results can also be valuable._](#user-content-fn-11)[^11]



### Logic and communication

_Percentile ranking (0-100%)_



Are the goals and questions of the paper clearly expressed? Are concepts clearly defined and referenced?

Is the [reasoning "transparent](#user-content-fn-12)[^12]"? Are assumptions made explicit? Are all logical steps clear and correct? Does the writing make the argument easy to follow?

Are the conclusions consistent with the evidence (or formal proofs) presented? Do the authors accurately state the nature of their evidence, and the extent it supports their main claims?&#x20;

Are the data and/or analysis presented relevant to the arguments made? Are the tables, graphs, and diagrams easy to understand in the context of the narrative (e.g., no major errors in labeling)?



### Open, collaborative, replicable research

_Percentile ranking (0-100%)_&#x20;

This covers several considerations:

#### _**Replicability, reproducibility, data integrity**_

Would another researcher be able to perform the same analysis and get the same results? Are the methods explained clearly and in enough detail to enable easy and credible replication? For example, are all analyses and statistical tests explained, and is code provided?

Is the source of the data clear?

Is the data made as available as is reasonably possible? If so, is it clearly labeled and explained??&#x20;

_**Consistency**_

Do the numbers in the paper and/or code output make sense? Are they internally consistent throughout the paper?

_**Useful building blocks**_

Do the authors provide tools, resources, data, and outputs that might enable or enhance future work and meta-analysis?



### Relevance to global priorities, usefulness for practitioners\*\*[^13]

Are the paper’s chosen topic and approach [likely to be useful](#user-content-fn-14)[^14] to [global priorities, cause prioritization, and high-impact interventions?](../../../the-field-and-ea-gp-research.md)&#x20;

Does the paper consider real-world relevance and deal with policy and implementation questions? Are the setup, assumptions, and focus realistic?&#x20;

Do the authors report results that are relevant to practitioners? Do they provide useful quantified estimates (costs, benefits, etc.) enabling practical impact quantification and prioritization?&#x20;

Do they communicate (at least in the abstract or introduction)  in ways policymakers and decision-makers can understand, without misleading or oversimplifying?



<details>

<summary>Earlier category: "Real-world relevance"</summary>

### Real-world relevance

_Percentile ranking (0-100%)_

Are the assumptions and setup realistic and relevant to the real world? [Does the paper consider the real-world relevance of the arguments and results presented, perhaps engaging policy and implementation questions?](#user-content-fn-15)[^15] &#x20;

Do the authors communicate their work in ways policymakers and decision-makers can understand, without misleading or oversimplifying?

Do the authors present practical _impact quantifications_, such as cost-effectiveness analyses? Do they report results that _enable_ such analyses?

</details>

<details>

<summary>Earlier category: Relevance to global priorities</summary>

_Percentile ranking (0-100%)_

Could the paper's topic and approach [_potentially_](#user-content-fn-16)[^16] help inform [global priorities, cause prioritization, and high-impact interventions?](../../../the-field-and-ea-gp-research.md)&#x20;

</details>



## Journal ranking tiers&#x20;

<details>

<summary>Note: this is less relevant for work in our Applied Stream </summary>

Most work in our [applied stream](../../considering-projects/applied-and-policy-track.md) will not be targeting academic journals. Still, in some cases it might make sense to make this comparison; e.g., if particular aspects of the work might be rewritten and submitted to academic journals, or if the work uses certain techniques that might be directly compared to academic work.  If you believe a comparison makes sense, please consider giving an assessment below, making reference to our guidelines and how you are interpreting them in this case.

</details>

To help universities and policymakers make sense of our evaluations, we want to benchmark them against how research is currently judged. So, we would like you to assess the paper in terms of journal rankings. We ask for two assessments:&#x20;

1. a normative judgment about 'how well the research _should_ publish';&#x20;
2. a prediction about where the research _will_ be published.

Journal ranking tiers are on a 0-5 scale, as follows:

* 0/5: "[Won't publish](#user-content-fn-17)[^17]/little to no value".  Unlikely to be cited by credible researchers
* 1/5: OK/Somewhat valuable journal
* 2/5: Marginal B-journal/Decent field journal
* 3/5: Top B-journal/Strong field journal
* 4/5: Marginal A-Journal/Top field journal
* 5/5: A-journal/Top journal


{% hint style="info" %}
_**We give some example journal rankings** belowbased on SJR and ABS ratings.

Journal_rating,5/5,,,4/5,,,3/5,,,2/5,,,1/5,,,0/5
Guide metric:,,8+,4*,,3.5-8,4,,2-3.5,3,,1-2,2,,0.5-1,1-2,
,A-journal/ Top Journal,SJR,ABS list,Marginal A-Journal/ top field journal,SJR,ABS list,Top B-journal/strong field journal,SJR,ABS list,Marginal B-journal/decent field journal,SJR,ABS list,OK/Somewhat valuable journal,SJR,ABS list,Marginally respectable/Little to no value: SJR<0.5; ABS 0-1
Economics/Finance/Business ,Econometrica,13.2,4*,Journal of Labor Economics,5.39,4,Journal of Development Economics,3.26,3,Journal of Macroeconomics,1.65,2,Research in Transportation Economics,0.759,1,
,Journal of Finance,16.46,4*,Economic Journal,5.11,4,World development,2.297,3,Economics and Politics,1.12,2,Journal of Business Economics ,0.808,2,
,Academy of Management Annals,14.78,4*,American Economic Journal: Economic Policy,8.64,3,Economic Policy,2.69,3,Journal of Economics and Management Strategy,1.40,3,Southern Economic Journal,0.731,2,
,,,,,,,Experimental Economics,2.19,3,,,,,,,
,,,,,,,Oxford Bulletin of Economics and Statistics,1.654,3,,,,,,,
,,,,,,,,,,,,,,,,
Psychology,Annual Review of Psychology,8.80,4,Psychological Review,4.36,4,,,,,,,,,,
,,,,Journal of Consumer Psychology,3.05,4*,,,,,,,,,,
,,,,,,,,,,,,,,,,
Other,Science,14.59,,American Political Science Review,5.82,,,,,,,,,,,
,Administrative Science Quarterly,17.36,4*,Nature Climate Change,6.13,,,,,,,,,,,
,,,,Journal of the American Statistical Association,4.41,4,,,,,,,,,,
,,,,Journal of Operations Management,3.36,4*,,,,,,,,,,
,,,,,,,,,,,,,,,,
,,,,,,,,,,,,,,,,

"NOTES: These are not precise, they are meant to give a flavor for what the rating intends. Where the two metrics disagree or we are very uncertain the journal is in italics",,,,,,,,,,,,,,,,



{% endhint %}

_We encourage you to_ [_consider a non-integer score_](#user-content-fn-18)[^18], e.g. 4.6 or 2.2.&#x20;

As before, we ask for a 90% credible interval.&#x20;

<table><thead><tr><th width="364">Journal ranking tiers</th><th width="248" align="center">Scale</th><th width="238">90% CI</th><th data-hidden><select></select></th><th data-hidden></th></tr></thead><tbody><tr><td>What journal ranking tier <em>should</em> this work be published in?</td><td align="center">0.0-5.0</td><td><em>lower, upper</em></td><td></td><td></td></tr><tr><td>What journal ranking tier <em>will this</em> work be published in?</td><td align="center">0.0-5.0</td><td><em>lower, upper</em></td><td></td><td></td></tr></tbody></table>

{% hint style="info" %}
[PubPub note (less relevant now that PubPub is being phased out) ](#user-content-fn-19)[^19]
{% endhint %}

#### **What journal ranking tier&#x20;**_**should**_**&#x20;this work be published in?**

_Journal ranking tier (0.0-5.0)_

Assess this paper on the journal ranking scale described above, considering only its merit, giving some weight to the category metrics we discussed above.

Equivalently, [where would this paper be published](#user-content-fn-20)[^20] if:

1. the journal process was fair, unbiased, and free of noise, and that status, social connections, and lobbying to get the paper published didn’t matter;
2. journals assessed research according to the category metrics we discussed above.

#### What journal ranking tier _will_ this work be published in?

_Journal ranking tier (0.0-5.0)_

<details>

<summary>What if this work has <em>already</em> been peer reviewed and published?</summary>

If this work has already been published, and you know where, please report the prediction you would have given absent that knowledge.

</details>



## The midpoint and 'credible intervals': expressing uncertainty

#### **What are we looking for and why?**

We want policymakers, researchers, funders, and managers to be able to _use The Unjournal'_&#x73; evaluations to update their beliefs and make better decisions. To do this well, they need to weigh multiple evaluations against each other and other sources of information. Evaluators may feel confident about their rating for one category, but less confident in another area. How much weight should readers give to each? In this context, it is useful to _quantify the uncertainty_.&#x20;

But it's hard to quantify statements like "very certain" or "somewhat uncertain" – different people may use the same phrases to mean different things. That's why we're asking for you a more precise measure, your _credible intervals._ These metrics are particularly useful for meta-science and meta-analysis.&#x20;

You are asked to give a 'midpoint' and a 90% credible interval. Consider this as [_**the smallest interval**_](#user-content-fn-21)[^21] _**that you believe is 90% likely to contain the true value.**_ See the fold below for further guidance.

<details>

<summary>How do I come up with these intervals? (Discussion and guidance)</summary>

You may understand the concepts of uncertainty and credible intervals, but you might be unfamiliar with applying them in a situation like this one.

You may have a certain best guess for the "Methods..." criterion. Still, even an expert can never be certain. E.g., you may misunderstand some aspect of the paper, there may be a method you are not familiar with, etc.

Your uncertainty over this could be described by some distribution, representing your beliefs about the _true value_ of this criterion. Your "'best guess" should be the central mass point of this distribution.

You are also asked to give a 90% credible interval. Consider this as [_**the smallest interval**_](#user-content-fn-22)[^22] _**that you believe is 90% likely to contain the true value.**_

For some questions, the "true value" refers to something objective, e.g. will this work be published in a top-ranked journal? In other cases, like the percentile rankings, the true value means "if you had complete evidence, knowledge, and wisdom, what value would you choose?"&#x20;

For more information on credible intervals, [this Wikipedia entry](https://www.wikiwand.com/en/Credible_interval) may be helpful.

If you are "[well calibrated](https://www.wikiwand.com/en/Calibrated_probability_assessment)", your 90% credible intervals should contain the true value 90% of the time.&#x20;

</details>

<details>

<summary>Consider the midpoint as the 'median of your belief distribution'</summary>

We also ask for the 'midpoint', the center dot on that slider. Essentially, we are asking for the _median of your belief distribution_. By this we mean the percentile ranking such that you believe "there's a 50% chance that  the paper's true rank is higher than this, and a 50% chance that it actually ranks lower than this."&#x20;

</details>

<details>

<summary>Get better at this by 'calibrating your judgment'</summary>

If you are "[well calibrated](https://www.wikiwand.com/en/Calibrated_probability_assessment)", your 90% credible intervals should contain the true value 90% of the time. To understand this better, assess your ability, and then practice to get better at estimating your confidence in results. [This web app](https://www.clearerthinking.org/tools/calibrate-your-judgment) will help you get practice at calibrating your judgments. We suggest you choose the "Calibrate your Judgment" tool, and select the "confidence intervals" exercise, choosing 90% confidence. Even a 10 or 20 minute practice session can help, and it's pretty fun.

</details>

## Claim identification, assessment, and implications

We are now asking evaluators for “claim identification and assessment” where relevant. This is meant to help practitioners use this research to inform their funding, policymaking, and other decisions. It is not intended as a metric to judge the research quality per se. This is not required but we will reward this work.&#x20;

[See guidelines and examples here](https://docs.google.com/document/d/1mBkAmCVomcUt0Ks7hsxShTsjAbx3WVtFfMCnasGQxns/edit?usp=sharing).



## Survey questions

Lastly, we ask evaluators about their background, and for feedback about the process.

<details>

<summary>Survey questions for evaluators: details</summary>

For the two questions below, we will [publish your responses](#user-content-fn-23)[^23] unless you specifically ask these questions  to be kept anonymous.&#x20;

1. How long have you been in this field?
2. How many proposals and papers have you evaluated? _(For journals, grants, and other peer review.)_

Answers to the questions [below will not be made public:](#user-content-fn-24)[^24] &#x20;

1. How would you rate this template and process?
2. Do you have any suggestions or questions about this process or _The Unjournal_? (We will try to respond to your suggestions, and incorporate them in our practice.) \[Open response]
3. Would you be willing to consider evaluating a revised version of this project?

</details>



## Other guidelines and notes

<details>

<summary>Note on the evaluation platform (13 Feb 2024)</summary>

[If you prefer](#user-content-fn-25)[^25], you can  submit your response in a Google Do&#x63;**,** and share it back with us. Click [here](https://docs.google.com/document/d/1erOQ8qiWmgAmd9WdMLmuBGoxFkUJeQo2c8pc5wFAQbk/copy) to make a new copy of that directly.  &#x20;

</details>



**Length/time spent:** This is up to you. We welcome detail, elaboration, and technical discussion.

<details>

<summary>Length and time: possible benchmarks</summary>

[The Econometrics society](https://www.econometricsociety.org/publications/econometrica/browse/guidelines-referees) recommends a 2–3 page referee report; [Berk et al.](https://pubs.aeaweb.org/doi/pdfplus/10.1257/jep.31.1.231) suggest this is relatively short, but confirm that brevity is desirable. [In a recent survey (Charness et al., 2022)](https://evalresearch.weebly.com/report---full-text.html), economists report spending (median and mean) about one day per report, with substantial shares reporting "half a day" and "two days." We expect that reviewers tend spend more time on papers for high-status journals, and when reviewing work that is closely tied to their own agenda.

</details>

<details>

<summary>Adjustments to earlier metrics; earlier evaluation forms</summary>

We have made some adjustments to this page and to our guidelines and processes; this is particularly relevant for considering earlier evaluations. See [#adjustments-to-metrics-and-guidelines-previous-presentations](why-these-guidelines.md#adjustments-to-metrics-and-guidelines-previous-presentations "mention"). &#x20;

</details>

{% hint style="info" %}
If you still have questions, please contact us, or see our **FAQ on** [referees-evaluators.md](../../../faq-interaction/referees-evaluators.md "mention").
{% endhint %}



_Our data protection statement is linked_ [_here_](https://bit.ly/46y0LqH)_._

[^1]: Note: Older evaluations used slightly different forms, with slightly different guidelines.

[^2]: We refer to 'paper or project' here.  We encourage the submission of a range of formats, including dynamic documents. See [dynamic-documents-vs-living-projects](../../../benefits-and-features/dynamic-documents-vs-living-projects/ "mention"). However, we will refer to this as a 'paper'  throughout the discussion below, for simplicity.

[^3]: You may want to glance at these tables before writing your report, to gain a sense of our priorities.

[^4]: Note: These categories were separate on earlier forms (before about Oct. 2024)

[^5]: Applied stream: "... importance to future impactful applied research, and practical relevance and usefulness."

[^6]: August 2024: This new criteria is currently being incorporated into our forms.

[^7]: "Methods" may include choice/collection of data, experiment or survey design, statistical analysis, and simulation, among other elements.

[^8]: E.g., did they give at least a reasonable range of robustness checks? At best, did they ‘map the space’ of possible reasonable specifications in a clear 'multiverse analysis'?

[^9]: Examples of QRP include selective reporting, hypothesizing after results are known, changing methods without reporting, selective reporting of dependent variables, p-hacking, and (uncorrected) opportunistic stopping in data collection. See one relevant discussion [here](https://replicationindex.com/2015/01/24/qrps/).

[^10]: Directly or indirectly relevant; e.g., building tools that are likely to contribute to measuring high-impact interventions.

[^11]: Tightly estimated null results can advance the field. In Bayesian terminology, work that “substantially concentrates our posterior belief distributions around the initial expectations” is also highly informative.

[^12]: See, e.g., [Open Philanthropy's guide](https://www.openphilanthropy.org/research/reasoning-transparency/) on reasoning transparency.

[^13]: Aug. 2024: We've recently combined this from two criteria and we're integrating it into our forms. See the expandable boxes below for the older categories.

[^14]: Here we are asking you about whether i the research was _aimed_ in a way that had strong _potential_ to substantially help solve a high-value problem, or add a lot to global welfare.&#x20;

[^15]: E.g., does it help us evaluate what to prioritize for interventions and policy, improve interventions and policy, or improve our research and knowledge capacity for these?

[^16]: Here we are asking you about whether i the research was _aimed_ in a way that had strong _potential_ to substantially help solve a high-value problem, or add a lot to global welfare. \
    \
    The Unjournal aims to focus on research that has this potential, so this also helps us check our own prioritization.

[^17]: Not publishable in any journal that uses any scrutiny,  nor in any credible working paper series.

[^18]: E.g., if a paper/project would be most likely to be (or merits being) published in a journal that would rank about halfway between a top tier 'A journal' and a second tier (4/5) journal, you should rate it a 4.5. \
    \
    Similarly, if you think it has an 80%  chance of (being/meriting) publication in a 'marginal B-journal' and a 20% chance of a Top B-journal, you should rate it 2.2.\
    \
    Please also use this continuous scale for providing credible _intervals_.

[^19]: The PubPub form did  _not_ allowing you to give non-integer responses to this question.  We asked people to multiply their score by 10 and enter these using the 0-50 slider .&#x20;

[^20]: Please consider the paper in its current form, or with only minor revisions, unless instructed otherwise.

[^21]: Technically, this is referring to the 'Highest Density Interval" (HDI).

[^22]: Technically, this is referring to the 'Highest Density Interval" (HDI), the densest interval of the (posterior) distribution, in Bayesian statistics. Technically, such an interval doesn't need to even contain the midpoint of the distribution, although we will generally assume it does, for our purposes.

[^23]: However, if you don't ask us to publish your name along with your evaluation, we may only report a range-coded version of these, to protect your anonymity.

[^24]: 18 Sep 2023: we intend to summarize the comments in aggregate, but not in a way that you are identifiable.    &#x20;

[^25]: We are replacing the Google Docs with the tailored PubPub interface; the PubPub form should be more efficient and leave less room for misunderstanding. But we will still be flexible to let you link or upload your descriptive, free-form evaluation in whatever form you prefer.


LIST 


}

""").strip()
