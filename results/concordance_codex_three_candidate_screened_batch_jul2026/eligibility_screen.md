# Candidate eligibility screen

Screened on 2026-07-18 before any Terra or Sol judgment. The candidate set was
the first three records in source order in
`tools/issue_annotation_ui/data.json`; it was not selected using observed
concordance. Titles were checked against the first pages of the corresponding
local PDFs, and the study described by both issue sets was checked against the
PDF title and abstract. This screen assesses input alignment, not whether any
critique is correct.

| Candidate | Input title | PDF title | Issue-to-paper check | Decision |
|---|---|---|---|---|
| `Acemoglu_et_al._2024` | *Misperceptions and Demand for Democracy under Authoritarianism* | Same | Both issue sets concern the Türkiye online/field information experiments, voting outcomes, spillovers, and interpretation. | Eligible |
| `Adena_and_Hager_2024` | *Does online fundraising increase charitable giving? A nationwide field experiment on Facebook* | Same | Both issue sets concern the Facebook postal-code experiment, winsorization, spillovers, heterogeneity, and profitability. | Eligible |
| `Benabou_et_al._2023` | *Willful Ignorance and Moral Behavior* | *Ends versus Means: Kantians, Utilitarians, and Moral Decisions* | Human issues concern belief updating, information avoidance, and Likert ceiling effects. The PDF and LLM issues concern cross-task moral choices. | Excluded: title/manuscript mismatch |

PDF SHA-256 values at screening were:

- Acemoglu: `3d923e247e6c3f069fcf5908388e2bbc286222638f8408dce399c9b2ab982bb1`
- Adena–Hager: `bc3997f97b9ffd96299e60882d35c0707d29dec3887d1c099f26bc7f7b2dc8ae`
- Bénabou et al.: `67b3ea68bc7c53a7767150f119bf0cb04133bdcfd6dbd32e052b88b69a7f3841`

The eligible batch therefore contains two papers, 10 separately enumerated
human issues, and 24 LLM issues. The excluded case is retained in the screen
but is not passed to Terra and cannot enter aggregate coverage.
