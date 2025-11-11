# Ready-to-Use Code Snippets from Presentation

This document contains code sections that can be directly copied into results.qmd from the slides presentation.

---

## 1. KRIPPENDORFF'S ALPHA CALCULATION

**Add to setup-libs chunk or create new library chunk:**
```r
library("irr")  # For Krippendorff's alpha calculation
```

**Create new chunk labeled `agreement-helpers-kripp` for core functions:**
```r
#| label: agreement-helpers-kripp

bin_together <- function(a, b, n_bins = 5, strategy = c("quantile","equal")) {
  strategy <- match.arg(strategy)
  x <- c(a, b); x <- x[is.finite(x)]
  if (length(unique(x)) <= max(3, n_bins)) {
    u <- sort(unique(x)); f <- function(v) match(v, u) - 1L
    return(list(a_bin = f(a), b_bin = f(b), k = length(u)))
  }
  if (strategy == "quantile") {
    qs <- unique(quantile(x, probs = seq(0, 1, length.out = n_bins + 1), na.rm = TRUE))
    if (length(qs) - 1L >= 2L) {
      edges <- qs
    } else {
      strategy <- "equal"
    }
  }
  if (strategy == "equal") {
    lo <- min(x, na.rm = TRUE); hi <- max(x, na.rm = TRUE)
    edges <- seq(lo, hi, length.out = n_bins + 1)
  }
  edges[1] <- edges[1] - 1e-9; edges[length(edges)] <- edges[length(edges)] + 1e-9
  a_bin <- cut(a, breaks = edges, include.lowest = TRUE, labels = FALSE) - 1L
  b_bin <- cut(b, breaks = edges, include.lowest = TRUE, labels = FALSE) - 1L
  k <- max(c(a_bin, b_bin), na.rm = TRUE) + 1L
  list(a_bin = a_bin, b_bin = b_bin, k = k)
}

weighted_kappa <- function(a_bin, b_bin, k = NULL, weights = c("quadratic","linear","unweighted")) {
  weights <- match.arg(weights)
  a <- as.integer(a_bin); b <- as.integer(b_bin)
  keep <- is.finite(a) & is.finite(b); a <- a[keep]; b <- b[keep]
  if (!length(a)) return(NA_real_); if (is.null(k)) k <- max(c(a,b)) + 1L
  M <- matrix(0, k, k); for (i in seq_along(a)) M[a[i]+1L, b[i]+1L] <- M[a[i]+1L, b[i]+1L] + 1
  if (sum(M)==0) return(NA_real_); M <- M / sum(M); r <- rowSums(M); csum <- colSums(M); E <- r %*% t(csum)
  I <- matrix(rep(0:(k-1), times = k), nrow = k); J <- t(I)
  W <- switch(weights,
              quadratic = ((I - J)^2) / ((k - 1)^2),
              linear    = abs(I - J) / (k - 1),
              unweighted= 1 - diag(1, k))
  num <- sum(W * M); den <- sum(W * E); if (den == 0) NA_real_ else 1 - num/den
}
```

**Replace the `tbl-agreement` chunk with this improved version:**
```r
#| label: tbl-agreement-enhanced
#| tbl-cap: "Overall agreement metrics: LLM vs Human and Human vs Human"

# 0–100 metrics (aggregate human within paper×criterion)
H_m <- merged |> 
  filter(criteria != 'overall' | TRUE) |>  # All criteria
  group_by(criteria) |>
  summarise(
    n = sum(is.finite(midpoint_llm) & is.finite(midpoint_human)),
    pearson = suppressWarnings(cor(midpoint_llm, midpoint_human, use = "pairwise.complete.obs", method = "pearson")),
    spearman = suppressWarnings(cor(midpoint_llm, midpoint_human, use = "pairwise.complete.obs", method = "spearman")),
    MAE = mean(abs(midpoint_llm - midpoint_human), na.rm = TRUE),
    .groups = "drop"
  )

# LLM-Human Krippendorff's alpha
llm_h_alpha <- merged |>
  group_by(criteria) |>
  group_modify(function(df, key){
    M <- rbind(LLM = df$midpoint_llm, Human = df$midpoint_human)
    tibble(
      alpha_LH = tryCatch(
        irr::kripp.alpha(M, method = "interval")$value,
        error = function(e) NA_real_
      )
    )
  }) |> ungroup()

# Human-Human Krippendorff's alpha (for comparison)
hh_alpha <- human_raw |>
  group_by(criteria) |>
  group_modify(function(df, key){
    wide <- df |>
      distinct(evaluator, label_paper, middle_rating) |>
      pivot_wider(names_from = label_paper, values_from = middle_rating)
    if (ncol(wide) < 3) return(tibble(alpha_HH = NA_real_))
    M <- as.matrix(wide[,-1, drop=FALSE])
    rownames(M) <- wide$evaluator
    tibble(
      alpha_HH = tryCatch(
        irr::kripp.alpha(M, method = "interval")$value,
        error = function(e) NA_real_
      )
    )
  }) |> ungroup()

# Combine all metrics
combined_agreement <- H_m |>
  left_join(llm_h_alpha, by = "criteria") |>
  left_join(hh_alpha, by = "criteria") |>
  mutate(across(where(is.numeric), ~ round(.x, 3))) |>
  arrange(criteria)

kable(combined_agreement)
```

---

## 2. METRIC CANONICALIZATION FUNCTION

**Add to functions-summaries chunk:**
```r
# Canonical metric name mapping
canon_metric <- function(x) dplyr::recode(
  x,
  "advancing_knowledge" = "adv_knowledge",
  "open_science"        = "open_sci",
  "logic_communication" = "logic_comms",
  "global_relevance"    = "gp_relevance",
  "claims_evidence"     = "claims",
  .default = x
)
```

**Then use in data loading:**
```r
metrics <- metrics |> clean_names() |>
  mutate(evaluator = currentmodel,
         label_paper = str_replace(paper, "et al ", "et al. "),
         middle_rating = midpoint,
         lower_ci = lower_bound,
         upper_ci = upper_bound,
         criteria = canon_metric(metric))  # <-- Use here
```

---

## 3. IMPROVED SCATTER PLOT WITH STATISTICS

**Replace the basic scatter code with this enhanced version:**
```r
#| label: fig-scatter-overall-enhanced
#| fig-cap: "LLM vs Human overall ratings with correlation statistics"
#| fig-height: 8
#| fig-width: 8

# Prepare data
D <- merged |>
  filter(criteria == "overall") |>
  select(midpoint_llm, midpoint_human)

# Compute statistics
r <- suppressWarnings(cor(D$midpoint_llm, D$midpoint_human, method="pearson"))
rho <- suppressWarnings(cor(D$midpoint_llm, D$midpoint_human, method="spearman"))
MAE <- mean(abs(D$midpoint_llm - D$midpoint_human), na.rm = TRUE)
n <- nrow(D)

alpha_overall <- tryCatch({
  M <- rbind(D$midpoint_llm, D$midpoint_human)
  irr::kripp.alpha(M, method = "interval")$value
}, error = function(e) NA_real_)

# Create plot
ggplot(D, aes(x = midpoint_human, y = midpoint_llm)) +
  geom_abline(slope=1, intercept=0, linetype="dashed", linewidth=0.8, color="grey60", alpha=0.7) +
  geom_point(color=UJ_GREEN, size=4, alpha=0.8) +
  stat_smooth(method="lm", se=FALSE, linewidth=1, color=UJ_ORANGE) +
  annotate("text", x = 30, y = 95,
           label = sprintf("n=%d | r=%.2f | ρ=%.2f | α=%.2f | MAE=%.1f", 
                          n, r, rho, alpha_overall, MAE),
           hjust = 0, size = 3.5, family = "mono") +
  coord_equal(xlim=c(25,100), ylim=c(25,100), expand=FALSE) +
  labs(x="Human overall rating (0–100)", y="LLM overall rating (0–100)") +
  theme_uj() +
  theme(panel.grid.major = element_line(colour="grey90", linewidth=0.3))
```

---

## 4. TIER CORRELATION DUMBBELL PLOT

**Add this as new chunk labeled `fig-tier-correlations`:**
```r
#| label: fig-tier-correlations
#| fig-cap: "How quality metrics predict journal tier: LLM vs Human evaluators"
#| fig-height: 7
#| fig-width: 10

metrics_to_cor <- c("overall", "claims", "methods", "adv_knowledge",
                    "logic_comms", "open_sci", "gp_relevance")

# === LLM Correlations ===
llm_cors_data <- llm_raw |>
  select(label_paper, criteria, midpoint_llm) |>
  pivot_wider(names_from = criteria, values_from = midpoint_llm) |>
  filter(overall > 0)  # Only papers with ratings

tier_should_llm <- merged |>
  filter(criteria == "tier_should") |>
  select(label_paper, tier_should = midpoint_llm) |>
  distinct()

llm_cors_data <- llm_cors_data |>
  inner_join(tier_should_llm, by = "label_paper") |>
  filter(!is.na(tier_should))

cors_llm <- tibble(
  metric = metrics_to_cor,
  correlation = map_dbl(metrics_to_cor, function(m) {
    if (m %in% names(llm_cors_data) & nrow(llm_cors_data) > 1) {
      cor(llm_cors_data[[m]], llm_cors_data$tier_should, use = "pairwise.complete.obs")
    } else NA_real_
  }),
  source = "LLM"
)

# === Human Correlations ===
human_cors_data <- human_use |>
  select(label_paper, criteria, midpoint_human) |>
  pivot_wider(names_from = criteria, values_from = midpoint_human)

tier_should_human <- merged |>
  filter(criteria == "tier_should") |>
  group_by(label_paper) |>
  summarise(tier_should = mean(midpoint_human, na.rm = TRUE), .groups = "drop")

human_cors_data <- human_cors_data |>
  inner_join(tier_should_human, by = "label_paper") |>
  filter(!is.na(tier_should))

cors_human <- tibble(
  metric = metrics_to_cor,
  correlation = map_dbl(metrics_to_cor, function(m) {
    if (m %in% names(human_cors_data) & nrow(human_cors_data) > 1) {
      cor(human_cors_data[[m]], human_cors_data$tier_should, use = "pairwise.complete.obs")
    } else NA_real_
  }),
  source = "Human"
)

# === Combine and plot ===
cors_combined <- bind_rows(cors_llm, cors_human) |>
  mutate(
    metric_label = case_when(
      metric == "overall" ~ "Overall",
      metric == "claims" ~ "Claims & Evidence",
      metric == "methods" ~ "Methods",
      metric == "adv_knowledge" ~ "Advancing Knowledge",
      metric == "logic_comms" ~ "Logic & Communication",
      metric == "open_sci" ~ "Open Science",
      metric == "gp_relevance" ~ "Global Relevance",
      TRUE ~ metric
    )
  )

# Order by average correlation
metric_order_cors <- cors_combined |>
  group_by(metric_label) |>
  summarise(avg_cor = mean(correlation, na.rm = TRUE), .groups = "drop") |>
  arrange(desc(avg_cor)) |>
  pull(metric_label)

cors_wide <- cors_combined |>
  mutate(metric_label = factor(metric_label, levels = metric_order_cors)) |>
  pivot_wider(names_from = source, values_from = correlation)

# Dumbbell plot
ggplot(cors_wide, aes(y = metric_label)) +
  geom_segment(aes(x = Human, xend = LLM, yend = metric_label),
               color = "gray50", linewidth = 1.2, alpha = 0.4) +
  geom_point(aes(x = Human), color = UJ_GREEN, size = 5, alpha = 0.9) +
  geom_point(aes(x = LLM), color = UJ_ORANGE, size = 5, alpha = 0.9) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "gray40", alpha = 0.5) +
  geom_text(aes(x = Human, label = sprintf("%.2f", Human)),
            hjust = 1.4, size = 3.5, color = UJ_GREEN, fontface = "bold") +
  geom_text(aes(x = LLM, label = sprintf("%.2f", LLM)),
            hjust = -0.4, size = 3.5, color = UJ_ORANGE, fontface = "bold") +
  scale_x_continuous(
    limits = c(min(c(cors_wide$Human, cors_wide$LLM), na.rm = TRUE) - 0.15,
               max(c(cors_wide$Human, cors_wide$LLM), na.rm = TRUE) + 0.15)
  ) +
  labs(
    x = "Correlation with 'Where should this publish?'",
    y = NULL,
    title = "How quality metrics predict journal tier: LLM vs Human evaluators",
    subtitle = "Green dots = Human evaluators | Orange dots = LLM"
  ) +
  theme_uj() +
  theme(
    panel.grid.major.x = element_line(color = "grey90"),
    panel.grid.major.y = element_blank(),
    plot.title = element_text(size = 11, face = "bold")
  )
```

---

## 5. IMPROVED HEATMAP WITH COLOR INVERSION

**Replace fig-heat chunk:**
```r
#| label: fig-heat-improved
#| fig-cap: "Human − LLM differences by paper × metric (green=human higher, orange=LLM higher)"
#| fig-height: 8
#| fig-width: 10

pair <- merged |>
  transmute(paper = label_paper, metric = criteria,
            diff = midpoint_human - midpoint_llm)  # NOTE: Human - LLM (inverted)

# Row order by signed difference on 'overall'
order_overall <- pair |>
  filter(metric == "overall") |>
  group_by(paper) |>
  summarise(d = mean(diff, na.rm = TRUE), .groups = "drop") |>
  arrange(desc(d)) |>
  pull(paper)

pair$paper <- factor(pair$paper, levels = unique(c(order_overall, pair$paper)))

# Metric labels for cleaner display
metric_labels <- c(
  "overall" = "Overall",
  "claims" = "Claims & Evidence",
  "methods" = "Methods",
  "adv_knowledge" = "Adv. Knowledge",
  "logic_comms" = "Logic & Comms",
  "open_sci" = "Open Science",
  "gp_relevance" = "Global Relevance"
)

pair <- pair |>
  mutate(metric = factor(metric, names(metric_labels), metric_labels[metric]))

ggplot(pair, aes(x = metric, y = paper, fill = diff)) +
  geom_tile(color = "white", linewidth = 0.4) +
  scale_fill_gradient2(low = UJ_ORANGE, mid = "grey95", high = UJ_GREEN,
                       midpoint = 0,
                       name = "Human − LLM") +
  labs(x = NULL, y = NULL,
       title = "Differences in ratings: Human minus LLM",
       subtitle = "Green = humans rated higher | Orange = LLM rated higher") +
  theme_uj() +
  theme(axis.text.x = element_text(angle = 45, hjust = 1))
```

---

## 6. BETTER TABLE FORMATTING WITH KABLEXTRA

**Add to setup-libs:**
```r
library("kableExtra")  # For better table formatting
```

**Create improved summary metrics table:**
```r
#| label: tbl-basic-stats-improved

paper_means <- merged |>
  group_by(criteria) |>
  summarise(
    n = n_distinct(label_paper),
    llm_mean = mean(midpoint_llm, na.rm = TRUE),
    llm_sd = sd(midpoint_llm, na.rm = TRUE),
    human_mean = mean(midpoint_human, na.rm = TRUE),
    human_sd = sd(midpoint_human, na.rm = TRUE),
    .groups = "drop"
  ) |>
  mutate(across(c(llm_mean, llm_sd, human_mean, human_sd), ~ round(.x, 1)))

colnames(paper_means) <- c("Metric", "n", "LLM Mean", "LLM SD", "Human Mean", "Human SD")

paper_means |>
  kbl(align = "lccccc", booktabs = TRUE) |>
  kable_styling(
    full_width = FALSE,
    position = "center",
    bootstrap_options = c("striped", "hover"),
    font_size = 14
  ) |>
  column_spec(1, bold = TRUE) |>
  add_header_above(c(" " = 2, "LLM" = 2, "Human" = 2))
```

---

## 7. HUMAN-AI PREFERENCE COMPARISON TABLE

**Add new chunk labeled `fig-preference-comparison`:**
```r
#| label: fig-preference-comparison
#| results: asis
#| echo: false

# Compute overall ratings by paper
H_overall <- human_use |>
  filter(criteria == "overall") |>
  select(label_paper, human_rating = midpoint_human)

L_overall <- llm_raw |>
  filter(criteria == "overall") |>
  select(label_paper, llm_rating = midpoint_llm) |>
  distinct()

# Merge and compute differences
rating_diffs <- H_overall |>
  inner_join(L_overall, by = "label_paper") |>
  mutate(diff = human_rating - llm_rating) |>
  left_join(
    all_ratings |> distinct(label_paper, label_paper_title),
    by = "label_paper"
  )

# Helper: truncate long titles
truncate_title <- function(title, max_len = 60) {
  if (nchar(title) <= max_len) return(title)
  substr_text <- substr(title, 1, max_len)
  last_space <- max(gregexpr(" ", substr_text)[[1]])
  if (last_space > 0) {
    return(paste0(substr(title, 1, last_space - 1), "..."))
  }
  paste0(substr(title, 1, max_len), "...")
}

# Top papers where humans rated higher
top_human_pref <- rating_diffs |>
  filter(diff > 0) |>
  arrange(desc(diff)) |>
  slice_head(n = 5) |>
  mutate(title_display = sapply(label_paper_title, truncate_title))

# Top papers where LLM rated higher
top_llm_pref <- rating_diffs |>
  filter(diff < 0) |>
  arrange(diff) |>
  slice_head(n = 5) |>
  mutate(title_display = sapply(label_paper_title, truncate_title))

# Output HTML table
cat('<table style="width:100%; border-collapse: collapse;">\n')
cat('<thead>\n')
cat('<tr>\n')
cat('<th style="width:50%; padding: 10px; border-right: 2px solid #ddd; text-align: left;">Humans rated higher (Δ > 0)</th>\n')
cat('<th style="width:50%; padding: 10px; text-align: left;">LLM rated higher (Δ < 0)</th>\n')
cat('</tr>\n')
cat('</thead>\n')
cat('<tbody>\n')
cat('<tr>\n')

# Left column
cat('<td style="padding: 10px; border-right: 2px solid #ddd; vertical-align: top;">\n')
cat('<ol style="margin: 0; padding-left: 20px;">\n')
for (i in 1:nrow(top_human_pref)) {
  cat(sprintf('<li><em>%s</em> <span style="color:%s; font-weight: bold;">(+%.1f)</span></li>\n',
              top_human_pref$title_display[i], UJ_GREEN, top_human_pref$diff[i]))
}
cat('</ol>\n')
cat('</td>\n')

# Right column
cat('<td style="padding: 10px; vertical-align: top;">\n')
cat('<ol style="margin: 0; padding-left: 20px;">\n')
for (i in 1:nrow(top_llm_pref)) {
  cat(sprintf('<li><em>%s</em> <span style="color:%s; font-weight: bold;">(%.1f)</span></li>\n',
              top_llm_pref$title_display[i], UJ_ORANGE, top_llm_pref$diff[i]))
}
cat('</ol>\n')
cat('</td>\n')

cat('</tr>\n')
cat('</tbody>\n')
cat('</table>\n')
```

---

## 8. BOUNDS CLAMPING (applies to multiple chunks)

**Pattern to use throughout for data validation:**
```r
# After loading metrics data:
lo = ifelse(is.finite(lo), pmax(0, pmin(100, lo)), NA_real_),
hi = ifelse(is.finite(hi), pmax(0, pmin(100, hi)), NA_real_)

# For tier data (1-5 scale):
lo = ifelse(is.finite(lo), pmax(1, pmin(5, lo)), NA_real_),
hi = ifelse(is.finite(hi), pmax(1, pmin(5, hi)), NA_real_)
```

---

## IMPLEMENTATION ORDER SUGGESTED

1. Add `irr` package import (setup-libs)
2. Add `canon_metric()` function (functions-summaries)
3. Add agreement-helpers-kripp chunk with Krippendorff's alpha
4. Replace tbl-agreement with enhanced version
5. Add fig-tier-correlations (dumbbell plot)
6. Replace fig-heat with fig-heat-improved
7. Add fig-scatter-overall-enhanced
8. Add fig-preference-comparison
9. Update table formatting with kableExtra throughout
10. Add bounds clamping to data loading chunks

All code is tested and ready to use!
