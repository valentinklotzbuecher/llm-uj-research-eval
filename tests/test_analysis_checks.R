source("scripts/analysis_checks.R")

# A known mispair must stay excluded even if a future data refresh restores it.
inputs <- data.frame(
  gpt_paper = c("Aligned", "Benabou_et_al._2023", "Peterman_et_al._2025"),
  coverage_pct = c(50, 100, 0)
)
eligible <- exclude_misaligned_critiques(inputs)
stopifnot(nrow(eligible) == 1L, eligible$gpt_paper == "Aligned",
          nrow(inputs) == 3L,
          nrow(exclude_misaligned_critiques(inputs[FALSE, ])) == 0L,
          identical(exclude_misaligned_critiques(eligible), eligible))
duplicate <- inputs[c(1, 1), ]
stopifnot(inherits(try(exclude_misaligned_critiques(duplicate), silent = TRUE), "try-error"))
missing <- inputs
missing$gpt_paper[1] <- NA_character_
stopifnot(inherits(try(exclude_misaligned_critiques(missing), silent = TRUE), "try-error"))

# Known classical reliability case: r=.5, two-rater reliability=2/3.
stopifnot(isTRUE(all.equal(sb_sensitivity_factor(.5, 2), sqrt(.75))),
          sb_sensitivity_factor(.5, 1) == 1,
          sb_sensitivity_factor(1, 3) == 1,
          sb_sensitivity_factor(.5, 3) < sb_sensitivity_factor(.5, 2))
for (r in c(-.5, 0, NA_real_, Inf, 1.1)) {
  stopifnot(is.na(sb_sensitivity_factor(r, 2)))
}
for (k in c(0, NA_real_, Inf)) {
  stopifnot(is.na(sb_sensitivity_factor(.5, k)))
}
# Headline critique figures: excluded pairings drop out, counts add up.
pair <- function(h, l) list(human_issue_index = h, llm_issue_indices = list(l))
judge <- list(
  list(gpt_paper = "A", num_gpt_issues = 4, comparison = list(
    coverage_pct = 50, precision_pct = 50,
    matched_pairs = list(pair(1, 1), pair(1, 2)),
    unmatched_human = list(list(index = 2)),
    unmatched_llm = list(list(index = 3), list(index = 4)))),
  list(gpt_paper = "B", num_gpt_issues = 2, comparison = list(
    coverage_pct = 100, precision_pct = 100,
    matched_pairs = list(pair(1, 1), pair(2, 2)),
    unmatched_human = list(), unmatched_llm = list())),
  list(gpt_paper = "Benabou_et_al._2023", num_gpt_issues = 9, comparison = list(
    coverage_pct = 0, precision_pct = 0, matched_pairs = list(),
    unmatched_human = list(list(index = 1)), unmatched_llm = list(list(index = 1))))
)
judge_file <- tempfile(fileext = ".json")
jsonlite::write_json(judge, judge_file, auto_unbox = TRUE)
h <- critique_headline(judge_file)
stopifnot(h$n_papers == 2, h$coverage_mean == 75, h$overlap_mean == 75,
          h$coverage_min == 50, h$coverage_max == 100,
          h$human_matched == 3, h$human_unmatched == 1, h$human_total == 4,
          h$llm_total == 6, h$llm_unmatched == 2, h$llm_matched == 4,
          grepl("In 2 eligible papers", critique_headline_text(h)))
cat("Analysis checks passed.\n")
