# Tools

> **MOVED:** These tools have been moved to the `unjournal_tools_interfaces` repository:
> - `build_issue_annotation_data.py` → https://github.com/daaronr/unjournal_tools_interfaces/tree/main/annotation
> - `match_issues_embeddings.py` → https://github.com/daaronr/unjournal_tools_interfaces/tree/main/annotation
> - `compare_issues_llm.py` → https://github.com/daaronr/unjournal_tools_interfaces/tree/main/annotation
> - `issue_annotation_ui/` → https://github.com/daaronr/unjournal_tools_interfaces/tree/main/annotation/ui
>
> The files here are kept for reference but the canonical location is now in the new repository.

## Original Contents

This directory contained issue annotation and matching tools for comparing human expert critiques with LLM-generated research issue assessments.

See the new repository for documentation and updates:
https://github.com/daaronr/unjournal_tools_interfaces

---

## Active Tools (in this repository)

### hypothesis_implement_monitor.py

Monitors Hypothes.is annotations on the live site for annotations tagged with `#implement`. When found, uses GPT-4o to interpret and implement the suggested changes, then commits them to git.

**Usage:**
```bash
# Run once (check for new annotations and implement them)
python tools/hypothesis_implement_monitor.py

# Preview without making changes
python tools/hypothesis_implement_monitor.py --dry-run

# List pending annotations
python tools/hypothesis_implement_monitor.py --list

# Reprocess a specific annotation
python tools/hypothesis_implement_monitor.py --reprocess ANNOTATION_ID
```

**Cron job:** Runs daily at 6 AM. See `crontab -l` for the entry.

**How to use:**
1. Add a Hypothes.is annotation on any page at https://llm-uj-research-eval.netlify.app
2. Include the tag `#implement` in your annotation
3. Describe the change you want in the annotation text
4. The script will automatically implement and commit the change within 24 hours
