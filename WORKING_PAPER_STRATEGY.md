# One maintained project version

Updated 7 September 2026 following David's request to avoid multiple maintained forks.

`working-paper` is the canonical maintained branch for the manuscript, analysis,
tools, and project documentation in this repository. This checkout should
normally stay on that branch. Earlier advice to maintain separate analysis
and prose branches is superseded.

- Integrate completed feature work into `working-paper`. Feature branches are
  temporary development aids, not separately maintained editions.
- Keep broader context, proposals, and exploratory appendices in the same
  source tree. Different audiences can have different navigation or generated
  views without independently maintained copies of the analysis.
- Treat `main`, `project`, and older feature branches as historical snapshots
  unless a specific outstanding change needs integrating. Preserve existing
  public URLs and annotations; archival availability does not require active
  maintenance of another source version.
- Keep research exclusions, prompts, and statistical fixes in this canonical
  source. Do not maintain divergent fixes across hosting branches.

See `HOSTING_PLAN.md` for the public destinations. GitHub Pages currently
deploys the prebuilt `_book/` directory from `working-paper`; source commits
must be rendered and checked before a publication update. Generated HTML and
PDF are release artifacts, not separate editable versions of the manuscript.

A local commit or merge does not publish changes. Push and deployment remain
separate actions. Branch deletion and changes to external hosting settings
are unnecessary for consolidating the source.
