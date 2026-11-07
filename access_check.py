"""Phase 2 access check. Run with:  streamlit run access_check.py

1. Lists the Gemini models this key can call (T4: pick one, don't trust defaults).
2. Sends one test prompt to the model you select and shows the raw reply.

Throwaway: once config.MODEL_NAME is set and a call works, app.py takes over.
"""

import streamlit as st
from google import genai

import config

st.title("Gemini access check")

# st.secrets reads .streamlit/secrets.toml locally and the Secrets panel on
# Streamlit Cloud, so the same code works in both places without the key in git (T3).
if "GEMINI_API_KEY" not in st.secrets:
    st.error("No GEMINI_API_KEY in .streamlit/secrets.toml. Copy secrets.toml.example and paste your key.")
    st.stop()

client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

# Only models that support generateContent are usable for text replies.
try:
    models = [
        m.name.removeprefix("models/")
        for m in client.models.list()
        if "generateContent" in (m.supported_actions or [])
    ]
except Exception as e:  # surface the real error; access problems are the known risk here
    st.error(f"Listing models failed: {type(e).__name__}: {e}")
    st.stop()

flash = sorted(m for m in models if "flash" in m)
st.subheader(f"{len(flash)} Flash / Flash-Lite models available")
st.code("\n".join(flash) or "(none)")

with st.expander(f"All {len(models)} generateContent models"):
    st.code("\n".join(sorted(models)))

default_idx = flash.index(config.MODEL_NAME) if config.MODEL_NAME in flash else 0
choice = st.selectbox("Model to test", flash, index=default_idx) if flash else None

prompt = (
    "It is 4th and 1 at the opponent's 40, tied, 2nd quarter. "
    "The call is Go. Reply with the word Go followed by exactly one sentence explaining why."
)

if choice and st.button("Send test call"):
    try:
        resp = client.models.generate_content(model=choice, contents=prompt)
        st.success(f"Model: {choice}")
        st.code(resp.text)
    except Exception as e:
        st.error(f"Call failed: {type(e).__name__}: {e}")

# Sweep: one call per text Flash model, so we can see which ones actually answer
# right now. The listing alone isn't proof (404 retired models, 503 overloaded ones).
# -tts models produce audio, so they're skipped.
st.divider()
text_flash = [m for m in flash if not m.endswith("-tts")]
if text_flash and st.button(f"Test all {len(text_flash)} text Flash models"):
    rows = []
    progress = st.progress(0.0)
    for i, m in enumerate(text_flash):
        try:
            resp = client.models.generate_content(model=m, contents=prompt)
            rows.append({"model": m, "result": "OK", "reply": (resp.text or "").strip()})
        except Exception as e:
            code = getattr(e, "code", "")  # 404 / 429 / 503 from the SDK's error object
            rows.append({"model": m, "result": f"FAIL {code}", "reply": str(e)[:120]})
        progress.progress((i + 1) / len(text_flash))
    st.dataframe(rows, use_container_width=True)
