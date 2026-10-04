# Current-debate candidates

[Back to overview](README.md)

**Evidence refreshed October 4, 2026. AI-assisted prioritization notes, not official Unjournal evaluations.** These six papers were not among the seven reports already handled in the initial shortlist pass. For each paper, "attention" is split into distinct signals: documented policy use, funding/support, policy-institution circulation, independent media, and author/institution promotion. A citation or press mention is not treated as adoption.

## Snapshot

| Paper | Recommendation | Documented policy use | Funding/support signal | Independent media | Evaluation fit |
|---|---|---|---|---|---|
| Delays to Frontier AI in the EU and UK | **High; first commissioning discussion** | Not verified | GovAI technical report; funding not separately verified | Euronews/EU Tech Loop | **Strong empirical audit** |
| Why Is AI So Contentious? | **Medium-high** | Not verified | BPEA/Brookings venue; no paper-specific funder use verified | Limited independent pickup found | **Moderate-to-strong, depends on empirical content** |
| Economics of Recursive Self-Improvement | **Very high; first commissioning discussion** | No direct government use verified | METR-linked research; no paper-specific funder adoption verified | Limited direct media | **Excellent theory/measurement audit** |
| Buying Time Against AI Proliferation | **Medium-high reserve** | No direct use verified; indexed in Korean National Assembly strategy portal | RAND says internally initiated using operating income and gifts from supporters | Specialist defense/policy circulation | **Very good formal-model audit** |
| Intelligence Explosion | **High, paired with upstream evidence audits** | No formal government citation verified yet | Multi-institution working paper; no paper-specific funder reliance verified | **Very high**: Guardian and other major outlets | **Moderate as a synthesis; high for selected inputs** |
| Economic Scenarios for Transformative AI | **High reserve / comparative economics review** | Not verified | Produced by Anthropic Institute; CEPR distribution | Economics and technology coverage | **Strong model audit, overlaps FRI** |

"Not verified" means a bounded search did not find clear evidence, not that no use exists.

<a name="govai-delays"></a>
## Delays to Frontier AI in the EU and UK

**John Lidiard, Oleksandra Vereschak, Tom Gibbs, and Markus Anderljung. Proposed queue: 5. Keep in the first commissioning discussion.**

### Why this could matter

The report assembles 375 LLM releases by Meta, Google, OpenAI, and Anthropic from June 2018 through May 2026 and asks how often Europe and the UK received models later than the United States, and why. The authors report that 11% of releases were delayed or withheld in the EU and 7% in the UK; among 68 delayed/non-released cases, they tentatively assign regulatory factors as the primary cause in 56. They identify data protection as the main regulatory barrier and say they do not find strong evidence that the AI Act caused delays during the observed period. [Primary report](https://www.governance.ai/research-paper/delays-to-frontier-ai-in-the-eu-and-uk).

This is unusually close to a live policy tradeoff: how much access cost should policymakers attribute to privacy and AI regulation, and which rule is responsible? An evaluation could improve claims already entering public debate by distinguishing descriptive release gaps from causal attribution.

### Attention, separated by type

**Independent media:** Euronews/EU Tech Loop covered the study on July 3 and repeated its headline findings in the context of the EU Digital Omnibus. [Euronews](https://www.euronews.com/next/2026/07/03/data-protection-rules-slow-llm-rollout-in-europe-study-says).

**Policy-institution circulation:** The topic is directly framed for regulators by GovAI, but I did not verify a European Commission, UK government, parliamentary, or regulator document citing the report. Therefore I would describe current attention as policy-media exposure, not demonstrated official reliance.

**Funding/support:** The report page says GovAI technical reports receive extensive feedback but do not undergo formal peer review. I did not verify paper-specific funder sponsorship from the sources checked.

### What an Unjournal evaluation could add

The most important question is attribution. The authors use public statements to classify the likely primary cause of delays. A referee should inspect the coding rules, ambiguous cases, inter-coder process, and sensitivity to alternative classifications. Other useful checks are: what counts as a release; whether app, API, modality, and trusted-access releases are comparable; company-level clustering; changing compliance capacity over time; and whether "no strong evidence" on the AI Act is mainly a consequence of limited post-enforcement exposure.

A strong team would combine an empirical regulation economist or political economist with an EU data-protection lawyer. The paper is unusually evaluable because it has a finite dataset and explicit classification exercise. Request the row-level data, coding protocol, source archive, and revision history before commissioning.

**Bottom line:** prioritize. The report is more decision-proximate and more empirically auditable than many AI-governance white papers, but the key causal language should receive a serious independent coding audit.

---

<a name="beraja"></a>
## Why Is AI So Contentious?

**Martin Beraja and Noam Yuchtman. Proposed queue: roughly 12–15 pending full-paper inspection.**

### Why this could matter

The paper argues that opposition to AI is not fully explained by displacement or existential-risk concerns. It proposes an additional "moral grievance": systems are built from people's words, creations, and expertise without consent, so policies focused only on redistribution, retraining, or slowing AI may leave a central political grievance unaddressed. [Brookings summary](https://www.brookings.edu/articles/why-is-ai-so-contentious/).

If supported, this matters for the political economy of copyright, compensation, attribution, and the durability of AI regulation. The evaluation target should be the evidence for the explanatory claim, not the rhetorical force of the "original sin" framing.

### Attention, separated by type

**Policy-institution circulation:** The paper was presented September 25 at the fall 2026 Brookings Papers on Economic Activity conference. Brookings describes BPEA as a policy-facing economics conference and journal designed to maximize impact on economic understanding and policymaking. That is prestigious institutional exposure, but it is not evidence that a government or funder acted on the paper.

**Independent media:** In the refreshed search I did not find strong independent coverage comparable to the intelligence-explosion paper. A previously listed Inside AI Policy URL is not reliable evidence for this paper: the page resolves to an older, unrelated 2025 Brookings/AI-backlash story. It should be removed from the dashboard's attention evidence rather than counted.

**Funding/support:** No paper-specific funding or grantmaker reliance was verified from the sources checked.

### What an Unjournal evaluation could add

The value depends heavily on the full empirical design. A referee should separate three claims: many people dislike AI; moral/ownership concerns exist; and those concerns materially *cause* opposition or regulatory demand above and beyond job and safety concerns. Survey correlations, descriptive polling, and historical analogy would support these claims to different degrees.

A political economist plus a public-opinion/survey specialist would be a good match. Check question wording, treatment or vignette structure if used, representativeness, alternative mechanisms, and whether policy prescriptions follow from measured preferences. If the conference draft is mainly conceptual synthesis, lower the priority because Unjournal can add less through empirical review.

**Bottom line:** keep, but below the first-wave empirical and formal-model candidates unless the full draft contains stronger identification than the public summary reveals.

---

<a name="rsi-econ"></a>
## The Economics of Recursive Self-Improvement

**Tom Cunningham, Lukas Althoff, Basil Halperin, Brian Jabarian, Andrew Koh, Arjun Ramani, Phil Trammell, Parker Whitfill, and Cheryl Wu. Proposed queue: 4. High priority.**

### Why this could matter

The paper formalizes the feedback loops through which AI-assisted AI R&D could accelerate capability growth. It represents those loops as directed graphs, shows that acceleration depends on products of elasticities, distinguishes narrow R&D skill from broader economically useful capability, surveys existing parameter estimates, and offers a preliminary calibration. The authors' own abstract says current feedback appears insufficient for self-sustaining acceleration but may be strengthening. [arXiv](https://arxiv.org/abs/2609.15802).

This is exactly the kind of work where a public evaluation can add value: the policy debate increasingly turns on a small number of parameters that are hard to estimate and easy to smuggle into qualitative claims.

### Attention, separated by type

**Research-to-policy-synthesis uptake:** This signal strengthened materially since the original dashboard brief. The September 28 multi-author intelligence-explosion paper cites Cunningham et al. for the claim that current productivity gains have not yet crossed the self-sustaining threshold and for the need to measure R&D inputs and returns. [Intelligence-explosion paper](https://arxiv.org/abs/2609.36054). This is genuine downstream use in a high-profile policy synthesis, though it is still research-community uptake rather than government adoption.

**Institutional promotion:** METR published an earlier note explaining the framework and explicitly characterized the calibration as loose/first-draft work. [METR note](https://metr.org/notes/2026-07-22-economics-of-recursive-self-improvement/). That candor increases the expected value of independent checking; it does not count as external validation.

**Government/funder use:** Not verified in the bounded search. **Direct media:** much lower than the intelligence-explosion report itself.

### What an Unjournal evaluation could add

This is an excellent fit for a growth economist plus an AI-R&D measurement specialist. Audit the derivation of feedback conditions, the elasticity products, the narrow/broad capability decomposition, empirical parameter mapping, and sensitivity of the calibration. Ask which missing lab-level measurements most reduce decision uncertainty and whether public proxies can identify them. Distinguish "approaching the threshold" from a calibrated probability of crossing it.

A particularly useful deliverable would reproduce the back-of-the-envelope calibration under alternative parameter distributions and show which inputs dominate the conclusion. If data are sparse, that is a result to make explicit rather than a reason to skip the evaluation.

**Bottom line:** retain at #4. Its direct media attention is modest, but it is already an upstream quantitative input to one of the most visible AI-governance reports of the moment, and its assumptions are unusually checkable.

---

<a name="rand-governed"></a>
## Buying Time Against AI Proliferation: The Economics of Governed Access

**Tobias Sytsma, RAND. Proposed queue: about 12. Strong reserve, especially for an export-control/proliferation round.**

### Why this could matter

The 74-page RAND report models adoption through governed and ungoverned channels and asks when policy-induced cost changes steer users toward monitored access, do little, or backfire. RAND reports that raising compliance costs on governed channels without pressure on ungoverned alternatives can push users toward the latter. [RAND report](https://www.rand.org/pubs/research_reports/RRA4996-1.html).

This matters for export controls, licensing, controlled cloud access, and open-model policy. It is also a useful counterweight to supply-side discussions that treat access as a binary technical constraint rather than an economic choice.

### Attention, separated by type

**Funding/support:** RAND states that the work was independently initiated by its Center for the Geopolitics of Artificial General Intelligence and used income from operations and gifts from RAND supporters. This is organizational/philanthropic support, not evidence that a specific funder commissioned the conclusion.

**Policy-institution circulation:** The report appears in the Republic of Korea National Assembly Library's national-strategy portal. [National Assembly Library entry](https://nsp.nanet.go.kr/plan/subject/detail.do?nationalPlanControlNo=PLAN0000067057). That is meaningful discoverability inside a legislative research institution, but cataloging is not evidence that legislators read or used it.

**Specialist media/circulation:** It has been summarized by defense/policy blogs and newsletters, including Indian Strategic Studies. [Example](https://www.strategicstudyindia.com/2026/09/buying-time-against-ai-proliferation.html). I did not verify major-media or direct government uptake.

### What an Unjournal evaluation could add

The central review question is how much of the result is structural rather than empirically calibrated. RAND's simulations explore many parameter combinations; frequencies across those scenarios should not be read as real-world probabilities unless the scenario distribution justifies that interpretation. Referees should examine channel substitutability, demand elasticity, switching costs, enforcement-cost assumptions, capability value, and the Robust Decision Making setup.

A trade/industrial-organization economist or decision analyst with export-control expertise would be ideal. Evaluation can also clarify which observable quantities policymakers would need to decide whether governed-access policies are working.

**Bottom line:** good paper, good fit, lower observed external attention than the current top tier. Move it up if an export-control policymaker or funder identifies a live design choice for which these parameters are central.

---

<a name="intel-explosion"></a>
## What If Automating AI R&D Triggers an Intelligence Explosion?

**Alan Chan, Christoph Winter, Andrew Barto, Jakub Pachocki, Geoffrey Hinton, Eric Horvitz, Yoshua Bengio, Dawn Song, Jack Clark, Hilary Greaves, Anton Korinek, Samuel Hammond, Thore Graepel, Ben Bariach, Philip H. S. Torr, Sheila A. McIlraith, Jeff Clune, Sam Manning, Girish Sastry, Tom Davidson, Daniel Eth, and Sören Mindermann. Proposed queue: 7, paired with upstream evidence audits.**

### Why this could matter

Released September 28, the paper argues that increasing automation of AI R&D could create a positive feedback loop in which years of progress arrive in months. It explicitly says current evidence is preliminary and calls for visibility into R&D automation, mechanisms to steer or constrain acceleration, and preparation for its consequences. [arXiv](https://arxiv.org/abs/2609.36054).

The paper matters because it translates technical and economic evidence into near-term governance proposals and carries unusually prominent authors. But as an Unjournal target it is a synthesis: the largest marginal value may come from independently auditing the empirical and economic inputs rather than writing a second broad synthesis.

### Attention, separated by type

**Independent media:** very high and immediate. The Guardian covered the report on September 28, emphasizing the participation of Hinton, Bengio, and senior lab researchers. [Guardian](https://www.theguardian.com/technology/2026/sep/28/ai-godfathers-warn-of-runaway-intelligence-explosion). Other major business/technology outlets also covered it. This is the strongest current media-attention signal in the set.

**Institutional/author prominence:** the paper is distributed through the Cambridge Programme on AI Science & Policy, GovAI, and the Foundation for American Innovation. The authors include people affiliated with major labs and universities, but they write in personal capacities; affiliation must not be reported as organizational endorsement.

**Government use/funder reliance:** no formal government citation or paper-specific grantmaker decision was verified in the refreshed search. Media attention should not be converted into a claim of policy uptake.

### What an Unjournal evaluation could add

Treat the report as a bundle of high-impact claims. Audit: the evidence on the share of AI R&D completed by AI systems; extrapolations from software-task time horizons to months-long research projects; the returns-to-research/recursive-improvement parameters; bottlenecks outside coding; and the interpretation of "approaching" a self-sustaining threshold. Then evaluate each policy proposal against the uncertainty it is supposed to manage.

The strongest design is a paired evaluation with the RSI economics paper and relevant METR measurement work. A broad "is intelligence explosion plausible?" essay risks duplicating existing debate. A source-by-source audit can instead tell decision-makers which quantitative inputs deserve reliance.

**Bottom line:** high priority because of current attention and stakes, but not #1. Evaluate the upstream evidence first or in parallel, so the public report adds information rather than echoing an already highly visible synthesis.

---

<a name="anthropic-scenarios"></a>
## Economic Scenarios for Transformative AI

**Anton Korinek, Charles I. Jones, Szymon Sacher, Tess Cotter, and Peter McCrory. Proposed queue: 8. Strong reserve; compare with FRI only after independent first readings.**

### Why this could matter

The Anthropic Institute model maps AI capability and adoption assumptions into US GDP, labor share, wages, reallocation, and unemployment through 2030. The authors present modest, substantial, and extreme scenarios and explicitly do not assign them probabilities. In the extreme scenario the model implies very rapid growth alongside a fall in labor's share and high unemployment among cognitive workers. [Anthropic scenario explorer](https://www.anthropic.com/institute/econ-scenarios); [CEPR discussion paper](https://cepr.org/publications/dp21939).

The policy value is not in treating these paths as forecasts. It is in making assumptions explicit enough to discuss taxation, redistribution, labor-market adjustment, and preparedness under very different capability/adoption paths.

### Attention, separated by type

**Institutional/academic distribution:** the work is produced by the Anthropic Institute and also circulated as CEPR Discussion Paper 21939, published September 15. CEPR distribution is academic exposure, not policy adoption.

**Independent commentary/media:** Tyler Cowen discussed the paper on Marginal Revolution on September 10. [Marginal Revolution](https://marginalrevolution.com/marginalrevolution/2026/09/economic-scenarios-for-transformative-ai.html). Technology/economics coverage has also discussed the interactive model. This is meaningful attention, but I did not verify a government fiscal forecast, central-bank analysis, or grantmaker decision actually using the scenarios.

**Funding/support:** because this is an Anthropic Institute product, institutional production is clear. That should be recorded separately from independent funding or external endorsement, neither of which was verified here.

### What an Unjournal evaluation could add

A macro/growth economist and labor economist should audit the task-production structure, capability-to-adoption mapping, automation versus augmentation, capital supply, new-task creation, reallocation frictions, wage dynamics, and sensitivity. The public survey and the economic model should be evaluated separately: respondents' beliefs do not validate the model, and the named scenarios are not probabilities.

This overlaps materially with FRI, but the objects differ. FRI elicits beliefs from experts and others; Anthropic maps specified capability/adoption paths through a structural scenario model. A later comparative synthesis could be valuable, but initial evaluations should be independent to avoid anchoring.

**Bottom line:** keep high, especially if the Unjournal wants to cover economic-distribution policy. Under the requested emphasis on demonstrated downstream use, it remains below FRI until a concrete policy user is verified.

---

## Cross-paper synthesis for this group

Three different types of "attention" matter here and should not be collapsed. The intelligence-explosion report has exceptional current media and elite-author attention. RSI has less press but stronger **research-to-policy-synthesis uptake**, because its calibration and measurement agenda are being used inside that report. The EU/UK delays paper has relevant policy-media exposure and a directly auditable dataset. Anthropic's scenarios have substantial economics-community circulation but, in the search so far, no demonstrated policy-model use comparable to FRI.

That distinction changes the commissioning logic. **RSI and EU/UK delays deserve to stay above papers that merely have more headlines.** The intelligence-explosion report should still be evaluated, but as a targeted audit of consequential inputs. RAND is a strong methods fit whose priority rises sharply if a real export-control decision-maker identifies an immediate application. Beraja-Yuchtman is intellectually important but should wait until the full empirical basis for its causal political-economy claim is clear.

## Corrections to carry back to the dashboard

1. Remove the previously listed Inside AI Policy link as evidence for Beraja-Yuchtman; the URL resolves to an older, unrelated 2025 story.
2. Strengthen the attention note for recursive self-improvement: it is directly cited as an input to the September 28 intelligence-explosion policy report.
3. Label Korean National Assembly Library indexing of the RAND report as **institutional discoverability**, not policymaker use.
4. For the intelligence-explosion paper, label lab affiliations and host institutions separately from organizational endorsement; the authors write in personal capacities.
5. For Anthropic scenarios, describe CEPR as academic dissemination and Anthropic as the producing institution, not as independent validation.

## GPT Pro evaluation status

No GPT Pro evaluation was executed in this run. I found no callable GPT Pro/session runner among the available tools, and the repository exposes no evaluation GitHub Action that can be safely invoked instead. The stored [evaluation handoff](EVALUATION_HANDOFF.md) remains ready for an actual runner. Preparation, source gathering, and queueing are not counted as completed evaluations.
