# Code for generating side-by-side correlation plots
# LLM vs Human: journal tier correlations with other metrics
# To be integrated into results.qmd

# This creates Figure: Comparison of how LLM and Human evaluators'
# journal tier predictions correlate with their other quality metrics

library(tidyverse)
library(patchwork)

# === LLM Correlations ===
# Prepare LLM data: tier_should + all percentile metrics
llm_cors_data <- llm_raw |>
  select(label_paper, criteria, midpoint_llm) |>
  pivot_wider(names_from = criteria, values_from = midpoint_llm)

# Get LLM tier_should
tier_should_llm <- jtiers_llm |>
  filter(criteria == "merits_journal") |>
  select(label_paper, tier_should = middle_rating)

llm_cors_data <- llm_cors_data |>
  left_join(tier_should_llm, by = "label_paper") |>
  filter(!is.na(tier_should))

# Calculate LLM correlations
metrics_to_cor <- c("overall", "claims", "methods", "adv_knowledge",
                    "logic_comms", "open_sci", "gp_relevance")

cors_llm <- tibble(
  metric = metrics_to_cor,
  correlation = map_dbl(metrics_to_cor, function(m) {
    if (m %in% names(llm_cors_data)) {
      cor(llm_cors_data[[m]], llm_cors_data$tier_should,
          use = "pairwise.complete.obs")
    } else {
      NA_real_
    }
  }),
  source = "LLM"
) |>
  filter(!is.na(correlation))

# === Human Correlations ===
# Prepare Human data
human_cors_data <- human_raw |>
  select(label_paper, criteria, middle_rating) |>
  group_by(label_paper, criteria) |>
  summarise(midpoint_human = mean(middle_rating, na.rm = TRUE), .groups = "drop") |>
  pivot_wider(names_from = criteria, values_from = midpoint_human)

# Get Human tier_should (merits_journal)
tier_should_human <- jtiers_uj |>
  filter(criteria == "merits_journal") |>
  group_by(label_paper) |>
  summarise(tier_should = mean(middle_rating, na.rm = TRUE), .groups = "drop")

human_cors_data <- human_cors_data |>
  left_join(tier_should_human, by = "label_paper") |>
  filter(!is.na(tier_should))

# Calculate Human correlations
cors_human <- tibble(
  metric = metrics_to_cor,
  correlation = map_dbl(metrics_to_cor, function(m) {
    if (m %in% names(human_cors_data)) {
      cor(human_cors_data[[m]], human_cors_data$tier_should,
          use = "pairwise.complete.obs")
    } else {
      NA_real_
    }
  }),
  source = "Human"
) |>
  filter(!is.na(correlation))

# === Combine and prepare ===
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

# Order metrics by average correlation (or by LLM correlation)
metric_order <- cors_combined |>
  group_by(metric_label) |>
  summarise(avg_cor = mean(correlation)) |>
  arrange(desc(avg_cor)) |>
  pull(metric_label)

cors_combined <- cors_combined |>
  mutate(metric_label = factor(metric_label, levels = metric_order))

# === OPTION 1: Side-by-side bars (grouped) ===
plot_grouped <- ggplot(cors_combined, aes(x = metric_label, y = correlation, fill = source)) +
  geom_col(position = "dodge", alpha = 0.8) +
  geom_text(aes(label = sprintf("%.2f", correlation)),
            position = position_dodge(width = 0.9),
            vjust = ifelse(cors_combined$correlation > 0, -0.3, 1.3),
            size = 3) +
  geom_hline(yintercept = 0, linetype = "dashed", color = "gray40") +
  scale_fill_manual(values = c(LLM = UJ_ORANGE, Human = UJ_GREEN), name = NULL) +
  labs(
    x = NULL,
    y = "Correlation with 'Where should this publish?'",
    title = "Journal tier correlations with quality metrics",
    subtitle = paste0("Comparing ", currentmodel, " (orange) with Human evaluators (green)")
  ) +
  theme_uj() +
  theme(
    axis.text.x = element_text(angle = 45, hjust = 1),
    panel.grid.major.y = element_line(color = "grey90"),
    panel.grid.major.x = element_blank(),
    legend.position = "bottom"
  )

# === OPTION 2: Dumbbell plot (shows difference) ===
cors_wide <- cors_combined |>
  pivot_wider(names_from = source, values_from = correlation)

plot_dumbbell <- ggplot(cors_wide, aes(y = metric_label)) +
  geom_segment(aes(x = Human, xend = LLM, yend = metric_label),
               color = "gray60", linewidth = 1.5, alpha = 0.5) +
  geom_point(aes(x = Human), color = UJ_GREEN, size = 4) +
  geom_point(aes(x = LLM), color = UJ_ORANGE, size = 4) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "gray40") +
  geom_text(aes(x = Human, label = sprintf("%.2f", Human)),
            hjust = 1.3, size = 3, color = UJ_GREEN, fontface = "bold") +
  geom_text(aes(x = LLM, label = sprintf("%.2f", LLM)),
            hjust = -0.3, size = 3, color = UJ_ORANGE, fontface = "bold") +
  scale_x_continuous(limits = c(min(c(cors_wide$Human, cors_wide$LLM)) - 0.15,
                                 max(c(cors_wide$Human, cors_wide$LLM)) + 0.15)) +
  labs(
    x = "Correlation with 'Where should this publish?'",
    y = NULL,
    title = "Journal tier correlations with quality metrics",
    subtitle = paste0("Green = Human evaluators | Orange = ", currentmodel, " | Lines connect same metric")
  ) +
  theme_uj() +
  theme(
    panel.grid.major.x = element_line(color = "grey90"),
    panel.grid.major.y = element_blank()
  )

# === OPTION 3: Faceted horizontal bars ===
plot_faceted <- ggplot(cors_combined, aes(x = correlation, y = metric_label, fill = source)) +
  geom_col(alpha = 0.8) +
  geom_text(aes(label = sprintf("%.2f", correlation)),
            hjust = ifelse(cors_combined$correlation > 0, -0.2, 1.2),
            size = 3) +
  geom_vline(xintercept = 0, linetype = "dashed", color = "gray40") +
  facet_wrap(~ source, ncol = 2) +
  scale_fill_manual(values = c(LLM = UJ_ORANGE, Human = UJ_GREEN), guide = "none") +
  scale_x_continuous(limits = c(min(cors_combined$correlation) - 0.15,
                                 max(cors_combined$correlation) + 0.15)) +
  labs(
    x = "Correlation with 'Where should this publish?'",
    y = NULL,
    title = "Journal tier correlations with quality metrics: LLM vs Human",
    subtitle = paste0("Left: Human evaluators | Right: ", currentmodel)
  ) +
  theme_uj() +
  theme(
    panel.grid.major.x = element_line(color = "grey90"),
    panel.grid.major.y = element_blank(),
    strip.background = element_rect(fill = "grey95", color = NA),
    strip.text = element_text(face = "bold", size = 11)
  )

# Return plots (uncomment the one you want to use)
# plot_grouped
plot_dumbbell  # This is probably the most informative
# plot_faceted
