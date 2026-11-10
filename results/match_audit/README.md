# Match audit data

`audit_data.json` feeds the browser page where people check the AI judges' issue matches:
<https://daaronr.github.io/unjournal_tools_interfaces/annotation/ui/audit.html>.
The page loads this file from GitHub (`working-paper` branch), so regenerating and pushing it updates the hosted page; a bundled copy in `unjournal_tools_interfaces/annotation/ui/audit_data.js` is the offline fallback.

- **Regenerate:** `python scripts/match_audit.py export`. The critique-overlap pilot's `summarize` stage runs it automatically. The file is rewritten only when its content changes.
- **What it holds:** for each dataset (the 12-paper GPT-5.2 Pro comparison and each `critique_overlap_pilot_*` run), the human issues, the model issues and every match each judge returned, with scores, labels and reasons. Pairs a judge returned that put two items from the same list together are left out.
- **Privacy:** human issues come from published evaluations or evaluation managers' curated summaries; evaluators appear as E1, E2, and curated text passes through the same name-removing filter used for external Codex prompts. Run `anon_guard.py scan` on the file before pushing a new dataset.
- **Reviewer verdicts:** save the page's JSON exports to `data/human_issue_match_annotations/audit/` and run `python scripts/match_audit.py score` (add `--threshold 45` for the stricter rule) for judge precision, recall and Cohen's kappa against reviewers, and reviewer-to-reviewer agreement.
