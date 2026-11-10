# Shared, offline checks for the manuscript and its appendices.

exclude_misaligned_critiques <- function(data) {
  stopifnot(is.data.frame(data), "gpt_paper" %in% names(data))
  if (anyNA(data$gpt_paper) || anyDuplicated(data$gpt_paper)) {
    stop("Critique inputs need a non-missing, unique gpt_paper key.")
  }
  # Keep raw judgments unchanged. These exclusions apply only to the
  # human-critique / LLM-critique pairing, not to quantitative ratings.
  # Evidence: results/key_issues_comparison.md (Peterman) and
  # docs/concordance_three_candidate_methods_note_jul2026.md (Benabou).
  excluded <- c("Peterman_et_al._2025", "Benabou_et_al._2023")
  data[!data$gpt_paper %in% excluded, , drop = FALSE]
}

critique_headline <- function(
    results_file = "results/key_issues_comparison_results.json") {
  # Headline critique-overlap figures, computed from the judge output after
  # the shared pairing exclusions. Per-paper means are the headline; pooled
  # counts are reported alongside so readers can see the raw totals.
  raw <- jsonlite::fromJSON(results_file, simplifyVector = FALSE)
  keys <- vapply(raw, function(r) r$gpt_paper, character(1))
  keep <- exclude_misaligned_critiques(
    data.frame(gpt_paper = keys, row = seq_along(keys))
  )$row
  rows <- raw[keep]
  cmp <- lapply(rows, function(r) r$comparison)
  num <- function(f) vapply(cmp, function(x) as.numeric(f(x)), numeric(1))
  coverage <- num(function(x) x$coverage_pct)
  overlap <- num(function(x) x$precision_pct)
  matched_human <- num(function(x) length(unique(vapply(
    x$matched_pairs, function(p) as.numeric(p$human_issue_index), numeric(1)))))
  unmatched_human <- num(function(x) length(x$unmatched_human))
  unmatched_llm <- num(function(x) length(x$unmatched_llm))
  n_llm <- vapply(rows, function(r) as.numeric(r$num_gpt_issues), numeric(1))
  stopifnot(length(rows) > 0, !anyNA(coverage), !anyNA(overlap),
            all(unmatched_llm <= n_llm))
  list(
    n_papers = length(rows),
    coverage_mean = mean(coverage),
    coverage_min = min(coverage),
    coverage_max = max(coverage),
    overlap_mean = mean(overlap),
    overlap_min = min(overlap),
    overlap_max = max(overlap),
    human_matched = sum(matched_human),
    human_unmatched = sum(unmatched_human),
    human_total = sum(matched_human + unmatched_human),
    llm_total = sum(n_llm),
    llm_matched = sum(n_llm - unmatched_llm),
    llm_unmatched = sum(unmatched_llm)
  )
}

critique_headline_text <- function(h) {
  # One quotable sentence, shared by every page that states the headline.
  sprintf(paste0(
    "In %d eligible papers, the one-shot GPT-5.2 Pro reports raised on ",
    "average %.0f%% of the curated human consensus issues (range %.0f to %.0f%%), ",
    "and on average %.0f%% of the issues the model raised matched one of ",
    "those human concerns."),
    h$n_papers, h$coverage_mean, h$coverage_min, h$coverage_max,
    h$overlap_mean)
}

critique_v2_headline <- function(
    comparison_file = "results/issue_match_judge_v2_opus55_2026-11-10/comparison.json") {
  # Exploratory blinded re-judging (scripts/run_issue_match_judge.py;
  # docs/issue_match_judge_v2_pilot_2026-11-10.md). Means of per-paper rates,
  # averaged over two replicates, at three strictness levels.
  x <- jsonlite::fromJSON(comparison_file, simplifyVector = FALSE)
  lv <- function(l, f) as.numeric(x$real[[l]][[f]])
  ctl <- Filter(function(r) r$kind %in% c("cross_paper_control", "documented_mismatch"), x$controls)
  ctl_cov <- vapply(ctl, function(r) as.numeric(r$loose_coverage), numeric(1))
  rep_h <- as.numeric(strsplit(x$replicate_agreement$human_items, "/")[[1]])
  stopifnot(length(x$papers) > 0, length(ctl) > 0)
  list(
    n_papers = length(x$papers),
    n_human_items = sum(vapply(x$papers, function(p) as.numeric(p$n_human), numeric(1))),
    strict_cov = lv("strict", "mean_paper_coverage"),
    standard_cov = lv("standard", "mean_paper_coverage"),
    loose_cov = lv("loose", "mean_paper_coverage"),
    strict_ovl = lv("strict", "mean_paper_overlap"),
    standard_ovl = lv("standard", "mean_paper_overlap"),
    loose_ovl = lv("loose", "mean_paper_overlap"),
    n_controls = length(ctl),
    controls_max_loose_cov = max(ctl_cov),
    rep_agree = rep_h[1], rep_n = rep_h[2]
  )
}

critique_v2_text <- function(v) {
  sprintf(paste0(
    "A stricter, blinded re-judging of the same %d papers gives lower overlap: ",
    "%.0f%% coverage when only the same concern counts, %.0f%% at a loose level ",
    "that also counts criticism of the same result for a different reason."),
    v$n_papers, v$standard_cov, v$loose_cov)
}

critique_v2_boot <- function(
    boot_file = "results/issue_match_judge_v2_gpt56terra_2026-11-10/bootstrap.json",
    claude_run = "issue_match_judge_v2_opus55_2026-11-10",
    gpt_run = "issue_match_judge_v2_gpt56terra_2026-11-10") {
  # Cluster-bootstrap intervals over papers for the two v2 judges on identical
  # blinded inputs (scripts/issue_match_bootstrap.py, run with the GPT run
  # first, so the paired difference is GPT minus Claude).
  x <- jsonlite::fromJSON(boot_file, simplifyVector = FALSE)
  stopifnot(x$paired$first == gpt_run, x$paired$second == claude_run)
  num <- function(v) as.numeric(unlist(v))
  run <- function(id) lapply(x$runs[[id]][c("strict", "standard", "loose")], function(l)
    list(cov = num(l$coverage_mean), cov_ci = num(l$coverage_ci95),
         ovl = num(l$overlap_mean), ovl_ci = num(l$overlap_ci95),
         vs_pub = num(l$diff_vs_published), vs_pub_ci = num(l$diff_vs_published_ci95)))
  pr <- x$paired$levels
  list(
    n_papers = as.numeric(x$n_papers), draws = as.numeric(x$draws),
    published = list(cov = num(x$published$mean), cov_ci = num(x$published$ci95)),
    claude = run(claude_run), gpt = run(gpt_run),
    gpt_controls_max = num(x$runs[[gpt_run]]$controls$max_loose_coverage),
    gpt_controls_n = num(x$runs[[gpt_run]]$controls$n),
    diff = lapply(pr, function(l) list(d = num(l$mean_diff_coverage), ci = num(l$diff_ci95),
                                       only_gpt = num(l$only_first), only_claude = num(l$only_second),
                                       n = num(l$human_items), kappa = num(l$kappa)))
  )
}

critique_scaled_overlap <- function(
    summary_file = "results/critique_overlap_scaled_2026-11-10/summary.json",
    rule = "score>=30") {
  # 30-paper per-evaluator comparison with a human-to-human baseline
  # (scripts/critique_overlap_scale.py; docs/critique_overlap_scaled_2026-11-10.md).
  # Rates pooled over issues; intervals bootstrap papers.
  x <- jsonlite::fromJSON(summary_file, simplifyVector = FALSE)
  num <- function(v) as.numeric(unlist(v))
  j <- function(id) {
    b <- x$bootstrap$judges[[id]]
    r <- b[[rule]]
    get <- function(k) list(p = num(r[[k]]$point), ci = num(r[[k]]$ci95))
    list(n_papers = num(b$n_papers), n_boot = num(b$n_boot),
         cov = get("real_human_covered"), ovl = get("real_model_overlapping"),
         placebo = get("placebo_human_matched"), hh = get("human_human_both_directions"),
         gap = get("real_minus_human_human"))
  }
  ag <- x$judge_agreement_real_pairings[[rule]]$human_issues
  out <- list(gpt = j("codex"), claude = j("sonnet"),
              n_issues = num(x$extraction$n_issues),
              n_evaluations = length(x$extraction$per_evaluation),
              agree_pct = num(ag$percent_agreement), kappa = num(ag$cohen_kappa),
              only_gpt = num(ag$only_codex), only_claude = num(ag$only_sonnet))
  stopifnot(out$gpt$n_papers == out$claude$n_papers, out$n_issues > 0)
  out
}

critique_scaled_text <- function(s) {
  # One quotable sentence for the 30-paper result; s from critique_scaled_overlap().
  sprintf(paste0(
    "On %d papers, a one-shot Claude Opus 5.5 report raised %.0f%% of an individual evaluator's ",
    "issues by a GPT judge and %.0f%% by a stricter Claude judge; a second evaluator raised %.0f%% ",
    "and %.0f%% of the same issues."),
    s$gpt$n_papers, s$gpt$cov$p, s$claude$cov$p, s$gpt$hh$p, s$claude$hh$p)
}

pct_ci <- function(p, ci, digits = 0) {
  f <- paste0("%.", digits, "f")
  sprintf(paste0(f, "%% [", f, ", ", f, "]"), p, ci[1], ci[2])
}

sb_sensitivity_factor <- function(r_hh, k) {
  # A classical reliability approximation, not an exact adjustment for
  # Spearman correlations or unequal, non-exchangeable human panels.
  # Non-positive reliability has no interpretation under this model.
  if (length(r_hh) != 1L || length(k) != 1L ||
      !is.finite(r_hh) || !is.finite(k) ||
      r_hh <= 0 || r_hh > 1 || k < 1) return(NA_real_)
  sqrt((1 + (k - 1) * r_hh) / k)
}
