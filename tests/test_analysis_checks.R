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
cat("Analysis checks passed.\n")
