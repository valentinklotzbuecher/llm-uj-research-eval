# How to Catch a GPU: A Taxonomy of Verification and Enforcement Mechanisms for International AI Agreements

**Raymond Koopmanschap and Otto Barten | [arXiv:2607.22619v1](https://arxiv.org/abs/2607.22619) | first submitted 16 June, publicly discussed July 2026 | checked 9 October 2026**

**Provisional recommendation: medium-priority verification-methods reserve, better as a focused evidence audit than as a first-wave full review.** This is a research-prioritization note, *not* an independent Unjournal referee evaluation. The screening read the complete [HTML article and appendices](https://arxiv.org/html/2607.22619v1), but did not replicate engineering estimates or access non-public intelligence.

## What is new and potentially important?

The paper usefully decomposes the enforceability of an international frontier-AI agreement into **(1) preventing uncontrolled resource acquisition; (2) detecting hidden compute outside the control regime; and (3) preventing controlled chips from escaping restrictions**. It codes **eight treaty/verification proposals** by the measures they propose and assesses where each problem becomes harder as dangerous capabilities require fewer FLOPs.

The most decision-relevant numerical claim is **conditional**: in an **absence-of-deliberate-concealment scenario**, roughly **10,000 H100-equivalents (~10 MW)** is a scale where large facilities may remain *mostly detectable* using physical infrastructure cues, while detection becomes markedly more difficult at smaller scales. The authors explicitly say hidden facilities at **10,000–100,000 H100-equivalents cannot be ruled out under active concealment**, and acknowledge that the cited satellite-detection calculation rests on **one open research analysis**. These are assumptions and uncertain engineering judgments, *not* a demonstrated lower bound, treaty enforceability theorem, or evidence an international pause will succeed. See [§5.3 and §7](https://arxiv.org/html/2607.22619v1).

This narrows the Unjournal payoff: an independent review of the detection threshold and its interaction with adversarial evasion is potentially valuable; another general introduction to compute governance would add much less.

## Current attention, carefully classified

| Evidence class | Verified through 9 Oct 2026 | How to interpret |
|---|---|---|
| **Official government/funder decision use** | No treaty-negotiation, regulator, national-security institute, major intergovernmental report or funder decision explicitly relying on this article was verified in bounded searches. | **Not established**, not a categorical absence claim. |
| **Conference/academic circulation** | arXiv [comments](https://arxiv.org/abs/2607.22619) state **accepted at the International Conference on Large-Scale AI Risks 2026, KU Leuven**. | Academic/program recognition; not official policy uptake or an independent replication. |
| **Institutional research/promotion** | The [Existential Risk Observatory](https://www.existentialriskobservatory.org/research/) lists the paper among its own outputs. | Research institution **hosting/promoting its own study**, not independent endorsement. |
| **Author promotion/community reach** | Koopmanschap and Barten published [“Is a pause enforceable? New paper out!” on LessWrong, 30 July 2026](https://www.lesswrong.com/posts/qygnNCM2FAA76Z9T4/is-a-pause-enforceable-new-paper-out), also pointing to EA Forum discussion. | Authored dissemination and specialist community attention, not adoption. |
| **Independent media/citation** | No major independent news feature or policy-agency citation specifically using the article was established. Scholarly indexing is discoverability. | **Unverified**. |
| **Paper-specific funding** | Not established in the accessible primary paper and bounded external search. | **Unknown**, not proof of no financial support. |

## Highest-value evaluation questions

1. **Audit the 10,000-H100 threshold as a conditional estimate, not a hard fact.** The paper maps facility size to power, cooling infrastructure, distinguishability and public satellite-classifier performance. Replicate the chain of assumptions and assess sensitivity to power-use effectiveness, hardware generations, siting, hybrid cooling, thermal masking, off-grid power and classification errors.
2. **Adversarial response.** Physical detection becomes a different problem when a state or clandestine actor optimizes for concealment. The article flags this. Assess the cost of realistic concealment and how an adversary's response shifts the inference about the largest undetected cluster.
3. **False negatives are not enough.** Define the base rate of covert facilities, false-positive inspection burden, acceptable detection probability and the effect of correlated signals. 'Combining independent methods' requires assessing whether satellite, power and human-intelligence detections are sufficiently independent.
4. **Governance feasibility versus technical sufficiency.** The paper assumes a concentrated fab supply chain, strong chip tracking, facilities willing or forced to accept inspectors, and enforceable shutdown. International legal jurisdiction, sovereignty, commercial incentives, enforcement response and mutual verification are acknowledged as outside scope; these may dominate technical detection.
5. **Check boundary cases of the taxonomy.** Smaller general-purpose hardware, distributed training, cross-border cloud access, algorithmic efficiency and multi-stage or decentralized training may make 'capacity to violate' hard to localize. Recode a sample of the eight proposals to test whether grouping and claimed gaps are robust.
6. **Compare marginal research payoff.** Pair this with Epoch compute measurement/smuggling estimates and relevant hardware-attestation work. A short joint report about what can actually be observed may influence decision-makers more than reviewing the taxonomy independently.

**Evaluator fit:** compute-infrastructure measurement or remote sensing specialist, paired with international verification/security specialist. **Evaluability:** high for the published coding and calculational chain; low for fully classified detection capability, real adversarial concealment and implementation costs. **Author responsiveness:** not verified; no outreach conducted.

## Reliance recommendation

**Appropriate:** a structured checklist for identifying *which compliance sub-problem* a proposed AI treaty addresses, with conditional estimates to prioritize follow-up validation. **Inappropriate:** assert that a pause is verified enforceable down to exactly 10,000 H100s, that satellite imagery can reliably find *adversarially concealed* clusters at that size, or that a proposed multilateral inspection regime is practical merely because three technical sub-problems are named.

## Sources and boundaries

- [Full paper + limitations + detection appendix](https://arxiv.org/html/2607.22619v1); [arXiv abstract and conference-acceptance metadata](https://arxiv.org/abs/2607.22619).
- [Existential Risk Observatory publication list](https://www.existentialriskobservatory.org/research/).
- [Authors' LessWrong post, 30 July 2026](https://www.lesswrong.com/posts/qygnNCM2FAA76Z9T4/is-a-pause-enforceable-new-paper-out).

**Not done:** independent satellite-classifier reproduction, technical verification experiment, field inspection, evaluator outreach or independent GPT Pro evaluation.
