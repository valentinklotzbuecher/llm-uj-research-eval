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

sb_sensitivity_factor <- function(r_hh, k) {
  # A classical reliability approximation, not an exact adjustment for
  # Spearman correlations or unequal, non-exchangeable human panels.
  # Non-positive reliability has no interpretation under this model.
  if (length(r_hh) != 1L || length(k) != 1L ||
      !is.finite(r_hh) || !is.finite(k) ||
      r_hh <= 0 || r_hh > 1 || k < 1) return(NA_real_)
  sqrt((1 + (k - 1) * r_hh) / k)
}
