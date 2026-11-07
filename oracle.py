"""Builds the prompt and calls Gemini, falling back to the backup model (T4, T5)."""

import httpx
from google import genai
from google.genai import errors, types

import config

# Worth trying the backup for: quota (429), server trouble (500/503), server timeout (504).
# Anything else (bad key, bad request) would fail on the backup too.
FALLBACK_CODES = {429, 500, 503, 504}


def make_client(api_key):
    return genai.Client(api_key=api_key, http_options=types.HttpOptions(timeout=config.REQUEST_TIMEOUT_MS))


def spot_label(ball_spot):
    if ball_spot == 50:
        return "midfield (50)"
    return f"opponent's {ball_spot}" if ball_spot < 50 else f"own {100 - ball_spot}"


def score_label(diff):
    if diff == 0:
        return "tied"
    return f"leading by {diff}" if diff > 0 else f"trailing by {-diff}"


def build_message(yards_to_go, ball_spot, score_diff, quarter, seconds_left, context, verdict):
    lines = [
        f"Situation: 4th and {yards_to_go} at the {spot_label(ball_spot)}.",
        f"Score: {score_label(score_diff)}.",
        f"Quarter {quarter}, {seconds_left // 60}:{seconds_left % 60:02d} left in the quarter.",
    ]
    if context.strip():
        # Context goes to the LLM only, never to the rule (D1): engineered disagreement.
        lines.append(f"Additional context: {context.strip()}")
    lines.append(f"The call: {verdict}.")
    return "\n".join(lines)


def _describe(e):
    if isinstance(e, errors.APIError):
        return f"{e.code} {e.status}"
    return type(e).__name__


def _should_fall_back(e):
    if isinstance(e, errors.APIError):
        return e.code in FALLBACK_CODES
    return isinstance(e, httpx.TimeoutException)  # our own 30s cap


def _call(client, model, message):
    resp = client.models.generate_content(
        model=model,
        contents=message,
        config=types.GenerateContentConfig(system_instruction=config.SYSTEM_PROMPT),
    )
    return resp.text or ""  # None if the model returned nothing; validator will flag it


def ask(client, message):
    """Return dict: raw, model, fallback_reason, error. Never raises."""
    try:
        return {"raw": _call(client, config.MODEL_NAME, message), "model": config.MODEL_NAME,
                "fallback_reason": "", "error": ""}
    except Exception as e:
        if not _should_fall_back(e):
            return {"raw": "", "model": config.MODEL_NAME, "fallback_reason": "", "error": _describe(e)}
        reason = f"{config.MODEL_NAME}: {_describe(e)}"

    try:
        return {"raw": _call(client, config.FALLBACK_MODEL_NAME, message), "model": config.FALLBACK_MODEL_NAME,
                "fallback_reason": reason, "error": ""}
    except Exception as e:
        return {"raw": "", "model": config.FALLBACK_MODEL_NAME, "fallback_reason": reason, "error": _describe(e)}
