# Legacy-source usage probe

This one-paper Terra run is retained only as an execution and usage probe. It
used the legacy `results/key_issues_matched.json` input, where seven distinct
human concerns for this paper had been collapsed into one large issue. Its
100% human-issue coverage figure is therefore not a meaningful concordance
estimate and must not enter aggregate results.

The probe used 20,720 input tokens (19,712 reported as cached), 1,190 output
tokens, and 76 reasoning-output tokens. No Sol call was made.

New runs default to the separately enumerated
`tools/issue_annotation_ui/data.json:human_issue_suggestions` source.
