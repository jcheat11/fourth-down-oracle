"""The Fourth Down Oracle. Run with:  streamlit run app.py

Flow: form -> rule makes the call -> Gemini writes one sentence -> validator checks it -> log.
"""

from datetime import datetime

import pandas as pd
import streamlit as st

import config
from oracle import ask, build_message, make_client
from rule import decide
from validator import validate

st.set_page_config(page_title="Fourth Down Oracle", page_icon="🏈")
st.title("The Fourth Down Oracle")
st.caption(
    "One word, one sentence. A fixed rule makes the call; Gemini only writes the justification; "
    "a validator checks every reply against that contract and logs what breaks."
)

# With no secrets file at all, st.secrets raises instead of returning empty, so catch that too.
try:
    has_key = "GEMINI_API_KEY" in st.secrets
except Exception:
    has_key = False
if not has_key:
    st.error("No GEMINI_API_KEY configured. Add it in the app's Settings → Secrets on Streamlit Cloud.")
    st.stop()


@st.cache_resource  # one client for the whole app, not one per click
def get_client():
    return make_client(st.secrets["GEMINI_API_KEY"])


# Per-session state: the run log and the request counter (T5).
st.session_state.setdefault("log", [])
st.session_state.setdefault("calls", 0)
st.session_state.setdefault("last", None)

# ---- Input form (D1) ----
with st.form("situation"):
    c1, c2, c3 = st.columns(3)
    yards_to_go = c1.number_input("Yards to go", min_value=1, max_value=30, value=1)
    side = c2.radio("Ball on", ["Own", "Opponent"], index=1, horizontal=True)
    yard_line = c3.number_input("Yard line", min_value=1, max_value=50, value=40)

    c4, c5, c6, c7 = st.columns(4)
    score_diff = c4.number_input("Score diff (you − them)", min_value=-28, max_value=28, value=0)
    quarter = c5.selectbox("Quarter", [1, 2, 3, 4], index=1)
    minutes = c6.number_input("Min left", min_value=0, max_value=15, value=8)
    seconds = c7.number_input("Sec left", min_value=0, max_value=59, value=0)

    context = st.text_input(
        "Context (optional, goes to the LLM only, not the rule)",
        max_chars=200,
        placeholder="e.g. blizzard, starting QB just left injured",
    )
    submitted = st.form_submit_button("Ask the Oracle", type="primary")

# Convert the football yard line to yards from the opponent's goal (what rule.py expects).
ball_spot = yard_line if side == "Opponent" else 100 - yard_line
seconds_left = minutes * 60 + seconds

if submitted:
    if seconds_left > 900:
        st.error("A quarter is 15:00 at most.")
    elif yards_to_go > ball_spot:
        st.error(f"Can't need {yards_to_go} yards with only {ball_spot} to the goal line.")
    elif st.session_state.calls >= config.SESSION_CALL_CAP:
        st.warning(
            f"This session has used its {config.SESSION_CALL_CAP} Oracle calls. The free Gemini quota is "
            "shared by everyone using the app, so the cap keeps one person from using it all. "
            "Download your run log below; a new browser session resets the cap."
        )
    else:
        st.session_state.calls += 1
        verdict, reason = decide(yards_to_go, ball_spot, score_diff, quarter, seconds_left)
        message = build_message(yards_to_go, ball_spot, score_diff, quarter, seconds_left, context, verdict)
        with st.spinner("Consulting the Oracle..."):
            result = ask(get_client(), message)
        check = validate(result["raw"], verdict) if not result["error"] else None

        # B3: every run is logged with the raw output, including failed calls.
        row = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "yards_to_go": yards_to_go,
            "ball_spot": ball_spot,
            "score_diff": score_diff,
            "quarter": quarter,
            "time_left": f"{minutes}:{seconds:02d}",
            "context": context,
            "rule_verdict": verdict,
            "rule_reason": reason,
            "raw_output": result["raw"],
            "parsed_verdict": check["parsed_verdict"] if check else "",
            "result": ("PASS" if check["passed"] else "FAIL") if check else "ERROR",
            "violations": ";".join(c for c, _ in check["violations"]) if check else "",
            "violation_details": " | ".join(f"{c}: {d}" for c, d in check["violations"]) if check else "",
            "prompt_version": config.PROMPT_VERSION,
            "model": result["model"],
            "fallback_reason": result["fallback_reason"],
            "error": result["error"],
        }
        st.session_state.log.append(row)
        st.session_state.last = {"row": row, "check": check}

# ---- Result (kept in session state so it survives reruns, e.g. the download click) ----
last = st.session_state.last
if last:
    row, check = last["row"], last["check"]
    st.divider()
    if row["error"]:
        st.error(
            f"The Oracle is unavailable right now ({row['error']}). Google's free tier is busy or out of quota; "
            "try again in a minute. This run is still in the log."
        )
    else:
        st.subheader("The Oracle says")
        st.code(row["raw_output"] or "(empty reply)", language=None, wrap_lines=True)

        c1, c2, c3 = st.columns(3)
        c1.metric("Rule's call", row["rule_verdict"], row["rule_reason"], delta_color="off")
        c2.metric("Validator", "PASS" if check["passed"] else "FAIL",
                  f"{len(check['violations'])} violation(s)", delta_color="off")
        c3.metric("Model", row["model"].replace("gemini-", ""), f"prompt {row['prompt_version']}", delta_color="off")

        for code, detail in check["violations"]:
            st.error(f"**{code}** {detail}")
        if row["fallback_reason"]:
            st.info(f"Primary model unavailable ({row['fallback_reason']}); answered by the backup model.")

# ---- Run log (Section 6) ----
if st.session_state.log:
    st.divider()
    df = pd.DataFrame(st.session_state.log)
    passed = (df["result"] == "PASS").sum()
    st.subheader(f"Run log: {len(df)} runs, {passed} passed")
    st.dataframe(df, width="stretch")
    st.download_button(
        "Download run log (CSV)",
        df.to_csv(index=False).encode("utf-8"),
        file_name=f"oracle_runs_{datetime.now():%Y%m%d_%H%M}.csv",
        mime="text/csv",
    )
    st.caption(f"Calls this session: {st.session_state.calls} of {config.SESSION_CALL_CAP}. "
               "The log lives in this browser session; download it before closing the tab.")
