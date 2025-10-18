"""
Configuration settings for LLM-based research evaluation.

This module centralizes all configuration constants for the evaluation pipeline,
including model settings, API configuration, rate limits, and evaluation schemas.
"""

import os
import pathlib
from typing import Dict, List

# ============================================================================
# Model Configuration
# ============================================================================

# Default LLM model to use for evaluations
MODEL = os.getenv("UJ_MODEL", "gpt-5-pro")  # Can also use: o3, etc.

# ============================================================================
# API Configuration
# ============================================================================

# Path to OpenAI API key file (fallback if env var not set)
API_KEY_PATH = pathlib.Path("key/openai_key.txt")

# ============================================================================
# Cache Configuration
# ============================================================================

# Path to file ID cache (maps content hashes to OpenAI file IDs)
FILES_CACHE_PATH = pathlib.Path("cache/file_ids.json")

# ============================================================================
# Rate Limiting Configuration
# ============================================================================

# Tokens per minute limit (can be overridden with UJ_TPM env var)
TPM_LIMIT = int(os.getenv("UJ_TPM", "30000"))

# Requests per minute limit (can be overridden with UJ_RPM env var)
RPM_LIMIT = int(os.getenv("UJ_RPM", "50"))

# Safety factor for rate limiting (0.9 = use 90% of limits)
RATE_LIMIT_SAFETY = 0.9

# Initial token estimate for warmup
WARMUP_TOKEN_ESTIMATE = 8000

# ============================================================================
# Directory Configuration
# ============================================================================

# Directory containing PDFs to evaluate
PAPERS_DIR = pathlib.Path(os.getenv("UJ_PAPERS_DIR", "papers")).expanduser()

# Output directory for results
RESULTS_DIR = pathlib.Path("results")

# ============================================================================
# Evaluation Metrics
# ============================================================================

# List of percentile-based evaluation metrics (0-100 scale)
METRICS: List[str] = [
    "overall",
    "claims_evidence",
    "methods",
    "advancing_knowledge",
    "logic_communication",
    "open_science",
    "global_relevance",
]

# ============================================================================
# JSON Schemas
# ============================================================================

# Schema for individual percentile metrics (0-100 scale)
METRIC_SCHEMA: Dict = {
    "type": "object",
    "properties": {
        "midpoint": {"type": "number", "minimum": 0, "maximum": 100},
        "lower_bound": {"type": "number", "minimum": 0, "maximum": 100},
        "upper_bound": {"type": "number", "minimum": 0, "maximum": 100},
        "rationale": {"type": "string", "maxLength": 400},
    },
    "required": ["midpoint", "lower_bound", "upper_bound", "rationale"],
    "additionalProperties": False,
}

# Schema for journal tier metrics (0-5 scale)
TIER_METRIC_SCHEMA: Dict = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "score": {"type": "number", "minimum": 0, "maximum": 5},
        "ci_lower": {"type": "number", "minimum": 0, "maximum": 5},
        "ci_upper": {"type": "number", "minimum": 0, "maximum": 5},
        "rationale": {"type": "string", "maxLength": 400},
    },
    "required": ["score", "ci_lower", "ci_upper", "rationale"],
}

# Combined schema for all metrics
COMBINED_SCHEMA: Dict = {
    "type": "object",
    "properties": {
        "metrics": {
            "type": "object",
            "properties": {
                **{m: METRIC_SCHEMA for m in METRICS},
                "tier_should": TIER_METRIC_SCHEMA,
                "tier_will": TIER_METRIC_SCHEMA,
            },
            "required": METRICS + ["tier_should", "tier_will"],
            "additionalProperties": False,
        }
    },
    "required": ["metrics"],
    "additionalProperties": False,
}

# Text format specification for OpenAI API
TEXT_FORMAT_COMBINED: Dict = {
    "type": "json_schema",
    "name": "paper_assessment_with_tiers_v1",
    "strict": True,
    "schema": COMBINED_SCHEMA,
}

# ============================================================================
# Evaluation Configuration
# ============================================================================

# Maximum output tokens for LLM responses
MAX_OUTPUT_TOKENS = 3000

# Maximum retries for failed API calls
MAX_RETRIES = 6

# Initial retry delay (seconds)
INITIAL_RETRY_DELAY = 2.0

# Maximum retry delay (seconds)
MAX_RETRY_DELAY = 20.0

# Retry delay multiplier
RETRY_DELAY_MULTIPLIER = 1.7

# ============================================================================
# Background Polling Configuration
# ============================================================================

# Timeout for waiting for background responses (seconds)
BACKGROUND_TIMEOUT = 7200  # 2 hours

# Initial polling delay (seconds)
INITIAL_POLLING_DELAY = 1.0

# Maximum polling delay (seconds)
MAX_POLLING_DELAY = 8.0

# Polling delay backoff factor
POLLING_BACKOFF = 1.5
