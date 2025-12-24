# Improving LLM Output Formatting for Appendix Display

## Current Problem

The `assessment_summary` field in the JSON output is currently a large, unformatted text block that appears as a "huge clump" in the appendix callout blocks. The output lacks:

1. **Visual structure** - No clear sections or hierarchy
2. **Digestible bullet points** - No quick-scan summary of strengths/critiques
3. **Formatting** - No markdown formatting for readability

## Recommended Solutions

### 1. Enhanced JSON Schema

Modify the `COMBINED_SCHEMA` in `methods.qmd` to request structured assessment components:

```python
COMBINED_SCHEMA = {
    "type": "object",
    "properties": {
        "key_strengths": {
            "type": "array",
            "items": {"type": "string"},
            "description": "3-5 bullet points highlighting main strengths"
        },
        "key_critiques": {
            "type": "array",
            "items": {"type": "string"},
            "description": "3-5 bullet points highlighting main concerns or limitations"
        },
        "assessment_summary": {
            "type": "string",
            "description": "Formatted markdown with clear sections (see prompt for structure)"
        },
        "metrics": {
            # ... existing metrics structure ...
        }
    },
    "required": ["key_strengths", "key_critiques", "assessment_summary", "metrics"],
    "additionalProperties": False
}
```

### 2. Improved System Prompt

Replace the current diagnostic summary instruction in `SYSTEM_PROMPT_COMBINED` (lines 315-316) with:

```python
SYSTEM_PROMPT_COMBINED = f"""
Your role -- You are an academic expert as well as a practitioner across every relevant field -- use all your knowledge and insight. You are acting as an expert research evaluator/reviewer.
Do not look at any existing ratings or evaluations of these papers you might find on the internet or in your corpus, do not use the authors' names, status, or institutions in your judgment; ignore where (or whether) the work is published, the prestige of any venue, and how much attention it has received. Do not use this as evidence about quality. You must base all judgments entirely on the content of the PDF.

## Output Structure Requirements

You must provide THREE components in your JSON output:

### 1. Key Strengths (JSON field: `key_strengths`)
Provide an array of 3-5 concise bullet points (each 1-2 sentences) identifying the paper's most important **strengths**. Focus on:
- Novel methodology or approach
- Strong empirical evidence or data quality
- Clear contribution to the field
- Robust experimental design or identification strategy
- Excellent clarity of presentation
- Strong policy relevance or practical insights

### 2. Key Critiques (JSON field: `key_critiques`)
Provide an array of 3-5 concise bullet points (each 1-2 sentences) identifying the paper's most important **limitations, concerns, or areas for improvement**. Focus on:
- Identification threats or confounds
- Data limitations or measurement issues
- Missing robustness checks or sensitivity analyses
- Unclear exposition or logical gaps
- Limited external validity or generalizability
- Replication barriers or transparency issues
- Overstated claims relative to evidence

### 3. Detailed Assessment Summary (JSON field: `assessment_summary`)
Provide a structured markdown document (800-1200 words) with the following sections:

**Use this exact markdown structure:**

```markdown
## Overview
[1-2 paragraphs: Research question, approach, and headline findings]

## Methodological Strengths
[2-3 paragraphs: What the paper does well methodologically]

## Key Limitations and Concerns
[2-3 paragraphs: Main identification threats, data issues, or analytical concerns]

## Contribution and Relevance
[1-2 paragraphs: How this advances knowledge and its policy/practice relevance]

## Presentation and Transparency
[1 paragraph: Clarity of writing, replicability, open science practices]

## Overall Assessment
[1 paragraph: Synthesis of strengths and weaknesses, positioning relative to field]
```

**Formatting guidelines for assessment_summary:**
- Use markdown headers (##, ###) for sections
- Use **bold** for emphasis on key terms
- Use bullet lists (- ) when enumerating multiple points within a paragraph
- Keep paragraphs focused (3-6 sentences each)
- Be specific and concrete - cite page numbers, table numbers, or specific results when possible
- Maintain a professional, balanced tone

---

## Percentile Rankings and Credible Intervals

[... rest of existing prompt continues as before ...]
"""
```

### 3. Modified Response Parsing

Update the R code in `appendix_llm_traces.qmd` to display the structured output:

```r
read_llm_from_json <- function(paper, json_dir = here::here("data", "llm_evals")) {
  path <- file.path(json_dir, paste0(paper, ".response.json"))
  if (!file.exists(path)) {
    warning("JSON not found for paper: ", paper)
    return(list(
      assessment = NA_character_,
      reasoning = NA_character_,
      strengths = NA_character_,
      critiques = NA_character_
    ))
  }

  j <- jsonlite::fromJSON(path, simplifyVector = FALSE)
  out <- j$output %||% list()

  # Extract reasoning block
  reasoning_block <- NULL
  message_block   <- NULL
  for (blk in out) {
    if (is.list(blk) && identical(blk$type, "reasoning")) {
      reasoning_block <- blk
    }
    if (is.list(blk) && identical(blk$type, "message")) {
      message_block <- blk
    }
  }

  # Full reasoning trace
  reasoning_full <- NA_character_
  if (!is.null(reasoning_block)) {
    summaries <- reasoning_block$summary %||% list()
    if (length(summaries)) {
      texts <- purrr::map_chr(summaries, ~ .x$text %||% "")
      reasoning_full <- paste(texts, collapse = "\n\n")
    }
  }

  # Parse message content
  assessment_summary <- NA_character_
  key_strengths <- NA_character_
  key_critiques <- NA_character_

  if (!is.null(message_block) && length(message_block$content) > 0) {
    txt <- message_block$content[[1]]$text %||% ""
    if (nzchar(txt)) {
      parsed <- tryCatch(
        jsonlite::fromJSON(txt, simplifyVector = TRUE),
        error = function(e) NULL
      )
      if (!is.null(parsed)) {
        if (!is.null(parsed$assessment_summary)) {
          assessment_summary <- parsed$assessment_summary
        }
        if (!is.null(parsed$key_strengths)) {
          # Format as markdown bullets
          key_strengths <- paste0("- ", parsed$key_strengths, collapse = "\n")
        }
        if (!is.null(parsed$key_critiques)) {
          # Format as markdown bullets
          key_critiques <- paste0("- ", parsed$key_critiques, collapse = "\n")
        }
      }
    }
  }

  list(
    assessment = assessment_summary,
    reasoning = reasoning_full,
    strengths = key_strengths,
    critiques = key_critiques
  )
}
```

### 4. Enhanced Appendix Display

Update the rendering loop in `appendix_llm_traces.qmd` (lines 112-145):

```r
for (p in papers_all) {
  dat <- read_llm_from_json(p, json_dir = json_dir)
  if (is.na(dat$assessment) && is.na(dat$reasoning)) next

  cat("## ", p, "\n\n", sep = "")

  # Key Strengths callout
  if (!is.na(dat$strengths) && nzchar(dat$strengths)) {
    cat("::: {.callout-tip}\n")
    cat("#### Key Strengths\n\n")
    cat(dat$strengths, "\n")
    cat(":::\n\n")
  }

  # Key Critiques callout
  if (!is.na(dat$critiques) && nzchar(dat$critiques)) {
    cat("::: {.callout-warning}\n")
    cat("#### Key Critiques & Limitations\n\n")
    cat(dat$critiques, "\n")
    cat(":::\n\n")
  }

  # Detailed Assessment (collapsible)
  cat("::: {.callout-note collapse=\"true\"}\n")
  cat("#### Detailed Assessment Summary\n\n")
  if (!is.na(dat$assessment) && nzchar(dat$assessment)) {
    cat(dat$assessment, "\n")
  } else {
    cat("No assessment summary found.\n")
  }
  cat(":::\n\n")

  # Reasoning trace (collapsible)
  cat("::: {.callout-tip collapse=\"true\"}\n")
  cat("#### Model Reasoning Trace\n\n")
  cat("::: {.small}\n")
  if (!is.na(dat$reasoning) && nzchar(dat$reasoning)) {
    cat(dat$reasoning, "\n")
  } else {
    cat("No reasoning trace found.\n")
  }
  cat(":::\n")
  cat(":::\n\n")

  if (knitr::is_latex_output()) {
    cat("\\newpage\n\n")
  } else {
    cat("---\n\n")
  }
}
```

### 5. Alternative: Post-Processing with LLM

If you don't want to re-run evaluations, you could post-process existing `assessment_summary` text with a lightweight LLM call:

```python
# Add to methods.qmd after collecting results
def format_assessment(raw_assessment: str) -> dict:
    """Use GPT-4o-mini to reformat existing assessment into structured output"""

    formatting_prompt = """
    You will receive an unformatted research paper assessment.

    Extract and output:
    1. key_strengths: Array of 3-5 bullet points (1-2 sentences each) of main strengths
    2. key_critiques: Array of 3-5 bullet points (1-2 sentences each) of main limitations
    3. formatted_summary: The full assessment reorganized with markdown headers:
       - ## Overview
       - ## Methodological Strengths
       - ## Key Limitations and Concerns
       - ## Contribution and Relevance
       - ## Presentation and Transparency
       - ## Overall Assessment

    Preserve all substantive content. Just reorganize and add structure.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": formatting_prompt},
            {"role": "user", "content": raw_assessment}
        ],
        response_format={"type": "json_object"}
    )

    return json.loads(response.choices[0].message.content)
```

### 6. API Parameter Adjustments

Consider these parameter tweaks in `evaluate_paper()` (lines 419-454):

```python
p = dict(
    model=model,
    text={"format": TEXT_FORMAT_COMBINED, "verbosity": "high"},  # Request more structured output
    input=[
        {"role": "system", "content": [
            {"type": "input_text", "text": SYSTEM_PROMPT_COMBINED}
        ]},
        {"role": "user", "content": [
            {"type": "input_file", "file_id": fid},
            {"type": "input_text", "text": """
Return STRICT JSON per schema with:
1. key_strengths: array of 3-5 concise bullets
2. key_critiques: array of 3-5 concise bullets
3. assessment_summary: markdown formatted with ## headers for sections

No preamble. No extra text outside JSON.
"""}
        ]},
    ],
    max_output_tokens=16000,  # Increased for structured output
    temperature=0.3,  # Lower temperature for more consistent formatting
    background=True,
    store=True,
)
```

## Implementation Priority

**Quick wins (no re-evaluation needed):**
1. Update `appendix_llm_traces.qmd` display code to add section breaks to existing text
2. Add simple regex-based extraction of bullet points from existing assessments

**Medium effort (requires re-evaluation):**
1. Update schema to include `key_strengths` and `key_critiques` arrays
2. Modify system prompt with clear structure instructions
3. Re-run evaluations on subset to test

**Best long-term solution:**
1. Full schema + prompt update with markdown structure requirements
2. Update all parsing and display code
3. Re-run full evaluation suite

## Example Expected Output

With these changes, the appendix would display:

---

### Paper Name

::: {.callout-tip}
#### Key Strengths
- Large-scale geo-randomized field experiment with national scope provides strong causal identification
- Comprehensive outcome measurement across all donation channels eliminates attribution bias
- Pre-registered design with extensive robustness checks including randomization inference
- Valuable analysis of competitor spillovers rarely examined in digital advertising studies
:::

::: {.callout-warning}
#### Key Critiques & Limitations
- Individual-level ad exposure unmeasured; estimates are ITT not TOT, likely understating true effects
- Spatial spillovers incompletely addressed; neighbor-share analysis is observational not experimental
- ROI calculation relies on untested lifetime value assumptions and excludes overhead costs
- Code and data not shared due to confidentiality; full replication impossible
:::

::: {.callout-note collapse="true"}
#### Detailed Assessment Summary

## Overview
This paper presents a geo-randomized field experiment evaluating...

[... formatted markdown sections ...]
:::

---

This structure provides:
- **Scannable summary** at top (strengths/critiques)
- **Detailed analysis** available on click
- **Clear visual hierarchy** instead of wall of text
- **Better user experience** for readers skimming the appendix
