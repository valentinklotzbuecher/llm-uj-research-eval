"""
Utility functions and classes for LLM-based research evaluation.

This module provides:
- File caching with content-based hashing
- Rate limiting and pacing
- API retry logic with exponential backoff
- Response parsing and JSON extraction
- Background task polling
"""

import hashlib
import json
import pathlib
import random
import re
import time
from collections import deque
from typing import Any, Callable, Dict, Optional, Union

from openai import OpenAI

from config import (
    FILES_CACHE_PATH,
    INITIAL_POLLING_DELAY,
    INITIAL_RETRY_DELAY,
    MAX_POLLING_DELAY,
    MAX_RETRIES,
    MAX_RETRY_DELAY,
    POLLING_BACKOFF,
    RATE_LIMIT_SAFETY,
    RETRY_DELAY_MULTIPLIER,
    RPM_LIMIT,
    TPM_LIMIT,
    WARMUP_TOKEN_ESTIMATE,
)

# ============================================================================
# File ID Caching
# ============================================================================

# Global cache of file IDs (maps content hash -> OpenAI file ID)
FILES_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
_file_ids: Dict[str, str] = {}

# Load existing cache
if FILES_CACHE_PATH.exists():
    try:
        _file_ids.update(json.loads(FILES_CACHE_PATH.read_text()))
    except Exception:
        _file_ids = {}


def _sha256_of_file(p: pathlib.Path) -> str:
    """
    Compute SHA-256 hash of file contents.

    Args:
        p: Path to file

    Returns:
        Hex digest of SHA-256 hash
    """
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def get_file_id(pdf_path: Union[str, pathlib.Path], client: OpenAI) -> str:
    """
    Get or create OpenAI file ID for a PDF, with content-based caching.

    If the file's content hash is already in the cache and the file ID is still
    valid on OpenAI's servers, returns the cached ID. Otherwise, uploads the
    file and caches the new ID.

    Args:
        pdf_path: Path to PDF file
        client: OpenAI client instance

    Returns:
        OpenAI file ID

    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    p = pathlib.Path(pdf_path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")

    # Check cache
    key = _sha256_of_file(p)
    if key in _file_ids:
        fid = _file_ids[key]
        try:
            # Verify file still exists on OpenAI
            client.files.retrieve(fid)
            return fid
        except Exception:
            pass  # Stale ID, will re-upload

    # Upload file
    with open(p, "rb") as fh:
        up = client.files.create(file=fh, purpose="assistants")

    # Update cache
    _file_ids[key] = up.id
    FILES_CACHE_PATH.write_text(json.dumps(_file_ids, ensure_ascii=False, indent=2))

    return up.id


# ============================================================================
# Rate Limiting
# ============================================================================

class TokenPacer:
    """
    Rate limiter for API calls with both token-per-minute (TPM) and
    requests-per-minute (RPM) tracking.

    Maintains a sliding window of recent API calls and their token usage.
    Before each call, checks if the limits would be exceeded and sleeps if
    necessary. After each call, records the actual token usage.

    Attributes:
        tpm: Effective tokens-per-minute limit (after safety factor)
        rpm: Effective requests-per-minute limit (after safety factor)
        token_events: Deque of (timestamp, tokens) tuples
        call_events: Deque of (timestamp,) tuples
        est: Running estimate of tokens per call
    """

    def __init__(
        self,
        tpm_limit: int = TPM_LIMIT,
        rpm_limit: int = RPM_LIMIT,
        safety: float = RATE_LIMIT_SAFETY,
        warmup_est: int = WARMUP_TOKEN_ESTIMATE,
    ):
        """
        Initialize rate limiter.

        Args:
            tpm_limit: Tokens per minute limit
            rpm_limit: Requests per minute limit
            safety: Safety factor (0-1) to apply to limits
            warmup_est: Initial token estimate before observing actual usage
        """
        self.tpm = int(tpm_limit * safety)
        self.rpm = int(rpm_limit * safety)
        self.token_events = deque()
        self.call_events = deque()
        self.est = warmup_est

    def _purge(self):
        """Remove events older than 60 seconds from the sliding window."""
        now = time.time()
        while self.token_events and now - self.token_events[0][0] > 60:
            self.token_events.popleft()
        while self.call_events and now - self.call_events[0][0] > 60:
            self.call_events.popleft()

    def before(self, est_tokens: Optional[int] = None):
        """
        Check rate limits before making an API call. Sleeps if necessary.

        Args:
            est_tokens: Estimated tokens for this call (uses running average if None)
        """
        est = self.est if est_tokens is None else est_tokens
        self._purge()
        now = time.time()

        # Check token limit
        used_tokens = sum(t for _, t in self.token_events)
        need_sleep = 0.0
        if used_tokens + est > self.tpm and self.token_events:
            need_sleep = max(need_sleep, 60 - (now - self.token_events[0][0]))

        # Check request limit
        if len(self.call_events) + 1 > self.rpm and self.call_events:
            need_sleep = max(need_sleep, 60 - (now - self.call_events[0][0]))

        # Sleep if needed
        if need_sleep > 0:
            time.sleep(need_sleep + random.random() * 0.3)

    def after(self, resp) -> int:
        """
        Record token usage after an API call.

        Args:
            resp: API response object

        Returns:
            Total tokens used in this call
        """
        self._purge()
        self.call_events.append((time.time(),))

        # Extract token usage from response
        d = _resp_as_dict(resp)
        u = d.get("usage") or {}
        tok = (u.get("input_tokens") or 0) + (u.get("output_tokens") or 0)
        od = u.get("output_tokens_details") or {}
        tok += od.get("reasoning_tokens") or 0

        # Record usage and update estimate
        self.token_events.append((time.time(), tok))
        self.est = max(1000, 0.5 * self.est + 0.5 * tok)

        return tok


# Global pacer instance
PACER = TokenPacer(
    tpm_limit=TPM_LIMIT,
    rpm_limit=RPM_LIMIT,
    safety=RATE_LIMIT_SAFETY,
    warmup_est=WARMUP_TOKEN_ESTIMATE,
)


# ============================================================================
# Retry Logic
# ============================================================================

def _sleep_from_429_text(msg: str, base: float = 3.0) -> float:
    """
    Extract retry delay from 429 error message.

    Args:
        msg: Error message text
        base: Base delay if no specific delay found in message

    Returns:
        Delay in seconds (with small random jitter)
    """
    m = re.search(r"try again in ([0-9.]+)s", msg, flags=re.I)
    return (float(m.group(1)) if m else base) + random.random() * 0.5


def call_with_retries(
    make_call: Callable,
    max_tries: int = MAX_RETRIES,
) -> Any:
    """
    Execute an API call with automatic retries and rate limiting.

    Handles:
    - Rate limiting (via PACER)
    - Automatic retries for rate limit errors (429)
    - Automatic retries for transient errors (timeouts, gateway errors, etc.)
    - Exponential backoff

    Args:
        make_call: Callable that makes the API call (no arguments)
        max_tries: Maximum number of attempts

    Returns:
        API response object

    Raises:
        RuntimeError: If all retries are exhausted
        Exception: Re-raises non-retryable exceptions
    """
    delay = INITIAL_RETRY_DELAY

    for _ in range(max_tries):
        PACER.before()
        try:
            resp = make_call()
            PACER.after(resp)
            return resp
        except Exception as e:
            s = str(e).lower()

            # Rate limit errors
            if "rate limit" in s or "429" in s or "tpm" in s:
                time.sleep(_sleep_from_429_text(str(e), base=delay))
                delay = min(delay * RETRY_DELAY_MULTIPLIER, MAX_RETRY_DELAY)
                continue

            # Transient errors
            if any(t in s for t in ("timeout", "service unavailable", "gateway", "overloaded")):
                time.sleep(delay + random.random() * 0.5)
                delay = min(delay * RETRY_DELAY_MULTIPLIER, MAX_RETRY_DELAY)
                continue

            # Non-retryable error
            raise

    raise RuntimeError("Too many retries.")


# ============================================================================
# Response Parsing
# ============================================================================

def _resp_as_dict(resp) -> Dict[str, Any]:
    """
    Convert API response to dictionary.

    Tries multiple methods to convert the response object to a dict,
    as different SDK versions may use different structures.

    Args:
        resp: API response object

    Returns:
        Dictionary representation of response
    """
    # Try model_dump (Pydantic v2)
    try:
        return resp.model_dump()
    except Exception:
        pass

    # Try to_dict method
    try:
        return resp.to_dict()
    except Exception:
        pass

    # Already a dict
    if isinstance(resp, dict):
        return resp

    return {}


def _get_output_text(resp) -> str:
    """
    Extract output text from API response.

    Handles various response formats and structures.

    Args:
        resp: API response object

    Returns:
        Extracted text output
    """
    # Try direct attribute
    try:
        t = getattr(resp, "output_text", None)
        if t:
            return t
    except Exception:
        pass

    # Parse from dict
    d = _resp_as_dict(resp)
    if not d:
        return ""

    if d.get("output_text"):
        return d["output_text"]

    # Extract from output array
    parts = []
    for item in d.get("output", []) or []:
        if item.get("type") == "message":
            for c in item.get("content") or []:
                txt = c.get("text")
                if txt:
                    parts.append(txt)

    return "".join(parts).strip()


def _strip_code_fences(s: str) -> str:
    """
    Remove markdown code fences from string.

    Args:
        s: String potentially containing ```json ... ``` fences

    Returns:
        String with fences removed
    """
    if "```" not in s:
        return s

    first = s.find("```")
    if first == -1:
        return s

    second = s.find("```", first + 3)
    if second == -1:
        return s

    inner = s[first + 3:second]
    return re.sub(r"^\s*json\r?\n", "", inner, flags=re.I)


def extract_json(s: str) -> Dict[str, Any]:
    """
    Extract JSON object from string, handling various formats.

    Tries to parse the string directly as JSON. If that fails, attempts to:
    1. Strip markdown code fences
    2. Find and extract the first complete JSON object

    Args:
        s: String containing JSON (possibly with surrounding text)

    Returns:
        Parsed JSON object

    Raises:
        ValueError: If no valid JSON object found
    """
    # Try direct parse
    try:
        return json.loads(s)
    except Exception:
        pass

    # Strip code fences and find JSON object
    s2 = _strip_code_fences(s).strip()
    start = s2.find("{")
    if start == -1:
        raise ValueError("No JSON object start found.")

    # Track braces to find complete object
    depth = 0
    in_str = False
    esc = False

    for i in range(start, len(s2)):
        ch = s2[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = s2[start:i+1]
                    return json.loads(candidate)

    raise ValueError("Unterminated JSON object in model output.")


# ============================================================================
# Reasoning Metadata
# ============================================================================

def extract_reasoning_meta(resp) -> Dict[str, Any]:
    """
    Extract reasoning metadata from API response.

    For models that support extended thinking/reasoning, extracts:
    - Response ID
    - Reasoning ID
    - Reasoning summary
    - Token usage (input, output, reasoning)

    Args:
        resp: API response object

    Returns:
        Dictionary with metadata fields
    """
    d = _resp_as_dict(resp)
    rid, summary_text = None, None

    # Extract reasoning info
    out = d.get("output") or []
    if out and isinstance(out, list) and out[0].get("type") == "reasoning":
        rid = out[0].get("id")
        summ = out[0].get("summary") or []
        if summ and isinstance(summ, list):
            summary_text = summ[0].get("text")

    # Extract usage info
    usage = d.get("usage") or {}
    odet = usage.get("output_tokens_details") or {}

    return {
        "response_id": d.get("id"),
        "reasoning_id": rid,
        "reasoning_summary": summary_text,
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "reasoning_tokens": odet.get("reasoning_tokens"),
    }


# ============================================================================
# Background Task Polling
# ============================================================================

def wait_for_background(
    client: OpenAI,
    response_id: str,
    timeout_s: int = 7200,
    initial_delay: float = INITIAL_POLLING_DELAY,
    max_delay: float = MAX_POLLING_DELAY,
    backoff: float = POLLING_BACKOFF,
):
    """
    Poll for completion of a background API task.

    Args:
        client: OpenAI client instance
        response_id: ID of background response to poll
        timeout_s: Maximum time to wait (seconds)
        initial_delay: Initial polling interval (seconds)
        max_delay: Maximum polling interval (seconds)
        backoff: Multiplier for exponential backoff

    Returns:
        Completed response object

    Raises:
        RuntimeError: If task fails, is cancelled, or expires
        TimeoutError: If timeout is reached
    """
    start = time.time()
    delay = initial_delay

    while True:
        r = client.responses.retrieve(response_id)
        d = _resp_as_dict(r)
        s = d.get("status")

        if s == "completed":
            return r

        if s in ("failed", "cancelled", "expired"):
            raise RuntimeError(f"status={s}, details={d.get('incomplete_details')}")

        if time.time() - start > timeout_s:
            raise TimeoutError(f"timeout waiting for {response_id}, last status={s}")

        time.sleep(delay)
        delay = min(max_delay, delay * backoff)
