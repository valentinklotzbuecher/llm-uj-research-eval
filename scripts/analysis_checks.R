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

sb_sensitivity_factor <- function(r_hh, k) {
  # A classical reliability approximation, not an exact adjustment for
  # Spearman correlations or unequal, non-exchangeable human panels.
  # Non-positive reliability has no interpretation under this model.
  if (length(r_hh) != 1L || length(k) != 1L ||
      !is.finite(r_hh) || !is.finite(k) ||
      r_hh <= 0 || r_hh > 1 || k < 1) return(NA_real_)
  sqrt((1 + (k - 1) * r_hh) / k)
}
