# Archive Directory

**Last updated**: December 10, 2024

This directory contains files that are no longer actively used in the main project but are preserved for reference, historical context, or potential future use.

---

## 📂 Contents

### `archive_to_revisit/`
**Comprehensive archive** of unused code and obsolete files with full documentation.

Contains:
- **unused_python_modules/** - Python modules never integrated into the pipeline (config.py, evaluator.py, llm_utils.py, check_job_status.py)
- **One-off scripts** - Scripts that have already been executed (add_williams_to_data.py, batch_eval.py)
- **Old .qmd files** - Superseded versions (numerical_ratings.qmd, compare_ratings.qmd)
- **Documentation** - Detailed explanations of what's archived and why:
  - `ARCHIVE_METADATA.md` - Complete inventory with reasoning
  - `PYTHON_SCRIPTS_AUDIT.md` - Analysis of unused Python scripts
  - `REPO_CLEANUP_SUMMARY.md` - Overview of cleanup work
  - `INVENTORY.txt` - File-level listing

**See [archive_to_revisit/ARCHIVE_METADATA.md](archive_to_revisit/ARCHIVE_METADATA.md) for detailed information.**

### Compiled Outputs
- `Comparing-LLM-and-human-reviews...tex` - LaTeX output (regenerable from Quarto)

### Test/Example Files
- `example_prompt.txt` - Example or test prompt text
- `render_log.txt` - Build log from a previous render

### Standalone Scripts
- `tier_correlations_plot.R` - Standalone R plotting script (functionality integrated into results.qmd)

---

## 🎯 Purpose

Files are archived rather than deleted to:
1. **Preserve history** - Understand past approaches and decisions
2. **Enable recovery** - Retrieve if needed for reference or restoration
3. **Document evolution** - Show how the project structure improved over time
4. **Maintain auditability** - Track what was removed and why

---

## 🔍 How to Use

### Finding Archived Items
See the detailed documentation in `archive_to_revisit/`:
- `ARCHIVE_METADATA.md` - Categorized inventory with explanations
- `INVENTORY.txt` - Simple file listing

### Restoring Archived Files
If you need to restore something:
1. Check `ARCHIVE_METADATA.md` to understand why it was archived
2. Copy the file back to its original location (documented in metadata)
3. Verify dependencies and update any references

### Adding New Archives
When archiving new files:
1. Move them to this directory or `archive_to_revisit/`
2. Update `archive_to_revisit/ARCHIVE_METADATA.md` with:
   - What was archived
   - Why it was archived
   - Original location
   - Dependencies (if any)

---

## 📊 Archive Statistics

**Items in this directory**: ~20 files and subdirectories
**archive_to_revisit/ items**: ~15 files and scripts
**Total archived code**: ~40,000 lines (unused Python modules, old .qmd files)

---

## ⚠️ Important Notes

- **Do not modify archived files** - They're preserved as-is for historical reference
- **Check documentation first** - Before restoring, understand why something was archived
- **Archive is gitignored** - These files may not be in version control (check .gitignore)

---

## 🔗 Related Documentation

- [DIRECTORY_STRUCTURE.md](../DIRECTORY_STRUCTURE.md) - Overall repository structure
- [archive_to_revisit/ARCHIVE_METADATA.md](archive_to_revisit/ARCHIVE_METADATA.md) - Detailed archive inventory
- [archive_to_revisit/PYTHON_SCRIPTS_AUDIT.md](archive_to_revisit/PYTHON_SCRIPTS_AUDIT.md) - Python modules analysis
