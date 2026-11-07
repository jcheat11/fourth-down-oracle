"""Single place for settings that results depend on (T4, prompt versioning).

Anything that changes Oracle output lives here, so each run-log row can record
exactly which model and prompt produced it.
"""

# T4: pinned explicitly, never a "-latest" alias. Both passed the access-check
# sweep on 2026-11-07 (see REFLECTION_LOG.md).
MODEL_NAME = "gemini-3.5-flash"

# T5: tried only when the primary returns 503 (overloaded), 429 (its quota is
# used up; quotas are per model), or times out.
# Separate capacity pool and usually a larger free-tier allowance.
# Every run logs which model actually answered.
FALLBACK_MODEL_NAME = "gemini-3.5-flash-lite"

# Request limits (T5). The cap is per browser session; the timeout is per call.
SESSION_CALL_CAP = 25
REQUEST_TIMEOUT_MS = 30_000

# Prompt versioning: bump PROMPT_VERSION on every edit to SYSTEM_PROMPT so the
# run log can compare results across revisions (Phase 5 allows at most 2 revisions).
PROMPT_VERSION = "v1"
SYSTEM_PROMPT = """You are the Fourth Down Oracle. You are given an NFL fourth-down situation and the call that has already been made for it. You did not make the call and you do not change it. Your only job is to justify it.

The possible calls are: Go (go for it), Punt, Kick (attempt a field goal).

Reply in exactly this form: the call word, then exactly one sentence explaining why the call is right for this situation. No preamble, no hedging, no extra sentences, no formatting."""
