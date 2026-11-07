"""Go / No Go: the Fourth Down Oracle. Run with:  streamlit run app.py

Flow: inputs -> rule makes the call -> Gemini writes one sentence -> validator checks it -> log.
Inputs redraw the field live; Gemini is only called when "Make the Call" is clicked.
Presentation lives in ui.py; this file is the flow.
"""

from datetime import datetime

import pandas as pd
import streamlit as st

import config
import ui
from oracle import ask, build_message, make_client
from rule import decide
from validator import validate

st.set_page_config(page_title="Go / No Go · Fourth Down Oracle", page_icon="🏈", layout="wide")
st.markdown(ui.CSS, unsafe_allow_html=True)
st.markdown(ui.HEADER, unsafe_allow_html=True)

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


# Per-session state: run log, request counter (T5), last result, and the in-flight flag.
for k, v in {"log": [], "calls": 0, "last": None, "busy": False}.items():
    st.session_state.setdefault(k, v)


def request_call():
    # Runs before the next script pass, so that pass renders everything disabled
    # while Gemini works. This is what blocks double-clicks and mid-call edits.
    st.session_state.busy = True


busy = st.session_state.busy
left, right = st.columns([1, 1.15], gap="large")  # stacks to one column on phones

# ---------------- Controls (D1) ----------------
with left, st.container(key="controls"):
    st.markdown(ui.section("Field position"), unsafe_allow_html=True)
    side = st.radio("Ball is in", ["Own", "Opp"], index=1, horizontal=True, key="side", disabled=busy,
                    format_func=lambda s: "Own territory" if s == "Own" else "Opponent territory")
    c1, c2 = st.columns(2)
    yard_line = c1.number_input("Yard line (1–50)", min_value=1, max_value=50, value=40, key="yard_line", disabled=busy)
    # rule.py measures from the opponent's goal line: opp 40 -> 40, own 20 -> 80, 50 -> 50.
    ball_spot = yard_line if side == "Opp" else 100 - yard_line
    if yard_line == 50:
        c1.markdown('<p class="gng-hint">50 is midfield; territory doesn\'t matter.</p>', unsafe_allow_html=True)

    yards_to_go = c2.number_input("Yards to gain", min_value=1, max_value=30, value=1, key="ytg", disabled=busy)
    ytg_error = yards_to_go > ball_spot
    if ytg_error:
        c2.markdown(f'<p class="gng-fielderr">Only {ball_spot} yards to the goal line from here. '
                    f'Use {ball_spot} for 4th &amp; Goal.</p>', unsafe_allow_html=True)

    st.markdown(ui.section("Game state (used by the late-game rule)"), unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    score_diff = c3.number_input("Score margin (you − them)", min_value=-28, max_value=28, value=0, key="score",
                                 disabled=busy, help="Positive if you lead, negative if you trail.")
    quarter = c4.selectbox("Quarter", [1, 2, 3, 4], index=1, key="quarter", disabled=busy)
    c5, c6 = st.columns(2)
    minutes = c5.number_input("Minutes left in quarter", min_value=0, max_value=15, value=8, key="minutes", disabled=busy)
    seconds = c6.number_input("Seconds", min_value=0, max_value=59, value=0, key="seconds", disabled=busy)
    time_error = minutes * 60 + seconds > 900
    if time_error:
        st.markdown('<p class="gng-fielderr">A quarter is 15:00 at most. Set seconds to 0.</p>', unsafe_allow_html=True)

    st.markdown(ui.section("Optional context"), unsafe_allow_html=True)
    context = st.text_input("Context for Gemini only (the rule ignores it)", max_chars=200, key="context",
                            disabled=busy, placeholder="e.g. blizzard, starting QB just left injured")

situation = {"yards_to_go": yards_to_go, "ball_spot": ball_spot, "score_diff": score_diff, "quarter": quarter,
             "minutes": minutes, "seconds": seconds, "context": context}
invalid = ytg_error or time_error
capped = st.session_state.calls >= config.SESSION_CALL_CAP


def run_call(s):
    """One Oracle request: rule -> prompt -> Gemini (with backup) -> validator -> log (B2, B3)."""
    st.session_state.calls += 1
    secs = s["minutes"] * 60 + s["seconds"]
    verdict, reason = decide(s["yards_to_go"], s["ball_spot"], s["score_diff"], s["quarter"], secs)
    message = build_message(s["yards_to_go"], s["ball_spot"], s["score_diff"], s["quarter"], secs, s["context"], verdict)
    result = ask(get_client(), message)
    check = validate(result["raw"], verdict) if not result["error"] else None

    # B3: every run is logged with the raw output, including failed calls.
    row = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "yards_to_go": s["yards_to_go"], "ball_spot": s["ball_spot"], "score_diff": s["score_diff"],
        "quarter": s["quarter"], "time_left": f"{s['minutes']}:{s['seconds']:02d}", "context": s["context"],
        "rule_verdict": verdict, "rule_reason": reason, "raw_output": result["raw"],
        "parsed_verdict": check["parsed_verdict"] if check else "",
        "result": ("PASS" if check["passed"] else "FAIL") if check else "ERROR",
        "violations": ";".join(c for c, _ in check["violations"]) if check else "",
        "violation_details": " | ".join(f"{c}: {d}" for c, d in check["violations"]) if check else "",
        "prompt_version": config.PROMPT_VERSION, "model": result["model"],
        "fallback_reason": result["fallback_reason"], "error": result["error"],
    }
    st.session_state.log.append(row)
    st.session_state.last = {"row": row, "check": check, "situation": dict(s), "message": message}


PLAIN = {"V1": "didn't open with Go, Punt, or Kick", "V2": "named a different call than the rule",
         "V3": "wasn't exactly one sentence", "V4": "hedged", "V5": "added text before the verdict",
         "V6": "argued for another option"}


def render_result(current):
    last = st.session_state.last
    if not last:
        if not invalid:  # the fix-the-input message already covers the invalid case
            st.markdown(ui.status_line("Set the situation, then make the call."), unsafe_allow_html=True)
        return
    row, check = last["row"], last["check"]
    stale = last["situation"] != current

    if row["error"]:
        # No card on failure: a verdict without its sentence would break the one-word-one-sentence contract.
        msg = ("Gemini couldn't be reached just now (Google's free tier is busy or out of quota), "
               "so there's no call to show. Try again in a minute.")
        if stale:
            msg = "The last attempt, for the previous situation, couldn't reach Gemini."
        st.warning(msg)
        return

    st.markdown(ui.result_card(row["rule_verdict"], check["justification"],
                               ui.summary_text(last["situation"]) if stale else None), unsafe_allow_html=True)
    if stale:
        st.markdown(ui.status_line("<b>Inputs changed.</b> This call was for the previous situation. "
                                   "Make the Call again for the new one."), unsafe_allow_html=True)
        return
    if row["fallback_reason"]:
        st.markdown(ui.status_line("<b>Backup model:</b> the main model was busy, so the backup answered."),
                    unsafe_allow_html=True)


# ---------------- Situation, field, action, result ----------------
with right:
    st.markdown(ui.section("Situation"), unsafe_allow_html=True)
    st.markdown(ui.summary_bar(situation), unsafe_allow_html=True)
    st.markdown(ui.field_svg(ball_spot, min(yards_to_go, ball_spot)), unsafe_allow_html=True)

    st.button("Make the Call", key="make_call", type="primary", width="stretch",
              on_click=request_call, disabled=busy or invalid or capped)
    if invalid:
        st.markdown(ui.status_line("Fix the input marked in red to make the call."), unsafe_allow_html=True)
    if capped:
        st.markdown(ui.status_line(
            f"This session has used its {config.SESSION_CALL_CAP} calls. The free Gemini quota is shared by "
            "everyone using the app. Download your results below; a new browser session resets the cap."),
            unsafe_allow_html=True)

    if busy:
        # Clear the flag before calling, so an interrupted run can't fire a second request.
        st.session_state.busy = False
        if not invalid and not capped:
            with st.spinner("Making the call…"):
                run_call(situation)
        st.rerun()

    render_result(situation)

# ---------------- Secondary information ----------------
st.divider()
last = st.session_state.last

# Format check: its own visible section, so the validator result (B3) is on screen
# during the demo without crowding the answer itself.
st.markdown(ui.section("Format check"), unsafe_allow_html=True)
if not last:
    st.caption("After each call, the reply is checked for one verdict word, one sentence, and no hedging.")
elif last["row"]["error"]:
    st.caption("Nothing to check: the last request didn't get a reply.")
else:
    stale_label = ui.summary_text(last["situation"]) if last["situation"] != situation else None
    st.markdown(ui.format_check(last["check"]["violations"], PLAIN, stale_label), unsafe_allow_html=True)

with st.expander("Under the Hood"):
    if not last:
        st.caption("Make a call to see the rule's reasoning and the raw Gemini reply.")
    else:
        row, check = last["row"], last["check"]
        st.markdown(f"**Rule's call:** {row['rule_verdict']} ({row['rule_reason']}). "
                    "The rule makes the call; Gemini only explains it.")
        st.markdown("**Situation sent to Gemini**")
        st.code(last["message"], language=None, wrap_lines=True)
        if row["error"]:
            st.markdown(f"**Request failed:** {row['error']}"
                        + (f" (after main model: {row['fallback_reason']})" if row["fallback_reason"] else ""))
        else:
            st.markdown("**Raw reply** (exactly as returned, never edited)")
            st.code(row["raw_output"] or "(empty)", language=None, wrap_lines=True)
        st.markdown(f"**Model:** `{row['model']}` · **Prompt:** {row['prompt_version']}"
                    + (f" · **Backup used:** {row['fallback_reason']}" if row["fallback_reason"] else ""))

if st.session_state.log:
    df = pd.DataFrame(st.session_state.log)
    st.download_button("Download session results (CSV)", df.to_csv(index=False).encode("utf-8"), key="download",
                       file_name=f"oracle_runs_{datetime.now():%Y%m%d_%H%M}.csv", mime="text/csv")
    with st.expander(f"Session log: {len(df)} run{'s' if len(df) != 1 else ''}, {(df['result'] == 'PASS').sum()} passed"):
        st.dataframe(df, width="stretch")
    st.caption(f"Calls this session: {st.session_state.calls} of {config.SESSION_CALL_CAP}. "
               "Results live in this browser tab only; download them before closing it.")
