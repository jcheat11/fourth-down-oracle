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
