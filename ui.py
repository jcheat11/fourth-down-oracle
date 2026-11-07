"""Presentation only: page CSS, the field drawing, the summary bar, the verdict card (D6).

No decisions or API calls happen here. Everything returns an HTML string that app.py
renders with st.markdown(..., unsafe_allow_html=True). Any text that came from the LLM
is passed through html.escape first, so a reply can never inject markup into the page.

Field geometry: the SVG is 1200 units wide. Each end zone is 100 units (10 yards), and
each yard of the playing field is 10 units. The offense always drives left to right,
so its own goal line is at x=100 and the opponent's is at x=1100.
"""

import html

# ---------- labels ----------

def spot_short(ball_spot):
    """ball_spot = yards from the opponent's goal (rule.py convention) -> 'OPP 42' / 'OWN 20' / 'MIDFIELD'."""
    if ball_spot == 50:
        return "MIDFIELD"
    return f"OPP {ball_spot}" if ball_spot < 50 else f"OWN {100 - ball_spot}"


def down_distance(yards_to_go, ball_spot):
    return "4TH & GOAL" if yards_to_go >= ball_spot else f"4TH & {yards_to_go}"


def score_short(diff):
    if diff == 0:
        return "TIED"
    return f"UP {diff}" if diff > 0 else f"DOWN {-diff}"


def summary_text(s):
    """One-line situation, also used to label a stale result. s = situation dict from app.py."""
    return (f"{down_distance(s['yards_to_go'], s['ball_spot'])} | {spot_short(s['ball_spot'])} | "
            f"Q{s['quarter']} {s['minutes']}:{s['seconds']:02d} | {score_short(s['score_diff'])}")


# ---------- page CSS ----------
# Hooks used: the st-key-<key> classes Streamlit puts on keyed elements, ARIA roles,
# and our own gng-* classes. Streamlit's generated class names are avoided because
# they change between releases.

CSS = """
<style>
:root { --gng-amber:#F2B233; --gng-turf:#1E7444; --gng-ink:#14171B; --gng-panel:#1F242B; --gng-line:#3A414B; }

/* Keep the page centered and readable on big screens; 16px side gutter on phones. */
/* Top padding clears Streamlit's fixed 60px toolbar so it never covers the header. */
.block-container { max-width: 1120px; padding-top: 4.25rem; padding-bottom: 3rem; }
@media (max-width: 640px) { .block-container { padding-left: 16px; padding-right: 16px; padding-top: 4rem; } }

/* Header */
.gng-header { margin: 0 0 0.75rem; }
.gng-kicker { font-size: 0.78rem; font-weight: 700; letter-spacing: 0.14em; color: var(--gng-amber); text-transform: uppercase; }
.gng-header h1 { font-size: clamp(2rem, 6vw, 2.9rem); font-weight: 900; line-height: 1.05; margin: 0.15rem 0 0.35rem; padding: 0; letter-spacing: -0.01em; }
.gng-header p { margin: 0; font-size: 1rem; color: #C9CDD2; max-width: 46rem; }
.gng-header .gng-note { margin-top: 0.35rem; font-size: 0.85rem; color: #9AA1AA; }

/* Section labels */
.gng-section { font-size: 0.78rem; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase; color: #9AA1AA; margin: 0.25rem 0 0.25rem; }

/* Touch targets: >= 44px for inputs, steppers, radio options, the main button. */
.st-key-controls input, .st-key-controls [data-baseweb="select"] > div { min-height: 44px; font-size: 1rem; }
.st-key-controls button { min-width: 44px; min-height: 44px; }
.st-key-controls [role="radiogroup"] label { min-height: 44px; padding-right: 1rem; display: flex; align-items: center; }
.gng-fielderr { color: #FF8A80; font-size: 0.9rem; margin: -0.4rem 0 0.6rem; }
.gng-hint { color: #9AA1AA; font-size: 0.85rem; margin: -0.4rem 0 0.6rem; }

/* Visible keyboard focus everywhere. */
button:focus-visible, input:focus-visible, [role="radio"]:focus-visible, summary:focus-visible, a:focus-visible {
  outline: 3px solid var(--gng-amber) !important; outline-offset: 2px;
}

/* Make the Call */
.st-key-make_call button { min-height: 54px; font-size: 1.1rem; font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase; color: var(--gng-ink); }
.st-key-make_call button:disabled { color: #5B626B; }
.st-key-download button, details > summary { min-height: 44px !important; }
details > summary { display: flex; align-items: center; }

/* Broadcast situation bar */
.gng-bar { display: flex; flex-wrap: wrap; align-items: stretch; border-radius: 6px; overflow: hidden; background: #0E1013; border: 1px solid var(--gng-line); font-weight: 800; letter-spacing: 0.05em; text-transform: uppercase; margin-bottom: 0.6rem; }
.gng-bar span { padding: 0.5rem 0.8rem; font-size: 0.95rem; border-right: 1px solid var(--gng-line); white-space: nowrap; }
.gng-bar span:last-child { border-right: 0; }
.gng-bar .gng-dd { background: var(--gng-amber); color: var(--gng-ink); }
.gng-bar .gng-spot { background: #2A3038; }

/* Field */
.gng-field svg { width: 100%; height: auto; display: block; border-radius: 6px; }
.gng-field .lbl-short { display: none; }
@media (max-width: 520px) {
  .gng-field .num-minor { display: none; }
  .gng-field .lbl-long { display: none; }
  .gng-field .lbl-short { display: inline; }
}
.gng-legend { display: flex; flex-wrap: wrap; gap: 0.25rem 1rem; font-size: 0.85rem; color: #C9CDD2; margin: 0.35rem 0 0.9rem; }
.gng-legend b { color: var(--gng-amber); }

/* Verdict card. Meaning is carried by the word and its label, not by color alone. */
.gng-result { border: 1px solid var(--gng-line); border-left: 8px solid var(--gng-accent, #fff); background: var(--gng-panel); border-radius: 6px; padding: 1rem 1.1rem 1.1rem; margin-top: 0.9rem; }
.gng-result.v-go   { --gng-accent: #3DDC84; }
.gng-result.v-punt { --gng-accent: #8FB8FF; }
.gng-result.v-kick { --gng-accent: var(--gng-amber); }
.gng-result .gng-eyebrow { font-size: 0.78rem; font-weight: 800; letter-spacing: 0.14em; text-transform: uppercase; color: #9AA1AA; }
.gng-result .gng-verdict { display: flex; align-items: baseline; flex-wrap: wrap; gap: 0.25rem 0.75rem; margin: 0.1rem 0 0.4rem; }
.gng-result .gng-word { font-size: clamp(2.6rem, 11vw, 3.6rem); font-weight: 900; line-height: 1; color: var(--gng-accent); letter-spacing: 0.02em; }
.gng-result .gng-tag { font-size: 0.95rem; font-weight: 700; color: #C9CDD2; text-transform: uppercase; letter-spacing: 0.08em; }
.gng-result .gng-why { font-size: 1.1rem; line-height: 1.5; margin: 0; overflow-wrap: anywhere; }
.gng-result.stale { opacity: 0.55; border-style: dashed; border-left-style: solid; }
/* Format check panel (validator result, B3). PASS/BROKEN is spelled out, not color-only. */
.gng-check { border: 1px solid var(--gng-line); background: var(--gng-panel); border-radius: 6px; padding: 0.8rem 1rem; margin: 0.2rem 0 1rem; }
.gng-check .gng-badge { display: inline-block; font-weight: 900; letter-spacing: 0.08em; padding: 0.15rem 0.55rem; border-radius: 4px; margin-right: 0.5rem; }
.gng-check.ok .gng-badge { background: #1E5E3A; color: #CFF5DD; }
.gng-check.bad .gng-badge { background: #6B2A24; color: #FFD9D4; }
.gng-check ul { margin: 0.5rem 0 0; padding-left: 1.2rem; }
.gng-check li { margin: 0.2rem 0; overflow-wrap: anywhere; }
.gng-check .gng-code { font-weight: 800; color: var(--gng-amber); }
.gng-check .gng-sub { color: #9AA1AA; font-size: 0.85rem; margin-top: 0.4rem; }
.gng-status { font-size: 0.9rem; color: #C9CDD2; margin: 0.5rem 0 0; }
.gng-status b { color: #F3F4F1; }
</style>
"""

# ---------- header ----------

HEADER = """
<div class="gng-header">
  <div class="gng-kicker">Fourth Down Oracle</div>
  <h1>Go / No Go</h1>
  <p>Set the fourth-down situation and make the call: Go, Punt, or Kick, with one sentence of why.</p>
  <p class="gng-note">A simplified rule makes the call and Gemini explains it. Not real NFL analytics.</p>
</div>
"""


def section(label):
    return f'<div class="gng-section">{html.escape(label)}</div>'


def summary_bar(s):
    return (
        '<div class="gng-bar" role="group" aria-label="Situation">'
        f'<span class="gng-dd">{down_distance(s["yards_to_go"], s["ball_spot"])}</span>'
        f'<span class="gng-spot">{spot_short(s["ball_spot"])}</span>'
        f'<span>Q{s["quarter"]} {s["minutes"]}:{s["seconds"]:02d}</span>'
        f'<span>{score_short(s["score_diff"])}</span>'
        "</div>"
    )


# ---------- field ----------

def _x(spot):
    """Yards-from-opponent-goal -> SVG x. Own goal line is x=100, opponent's is x=1100."""
    return 100 + (100 - spot) * 10


def _label(x, y, long_text, short_text, fill, size=40):
    # Clamp so labels near the end zones stay inside the drawing.
    x = max(170, min(1030, x))
    common = f'x="{x}" y="{y}" text-anchor="middle" font-size="{size}" font-weight="800" fill="{fill}"'
    return (f'<text class="lbl-long" {common}>{html.escape(long_text)}</text>'
            f'<text class="lbl-short" {common} font-size="{size + 8}">{html.escape(short_text)}</text>')


def field_svg(ball_spot, yards_to_go):
    """Horizontal field: end zones, yard lines, ball (football shape + arrow), first-down line (amber bar + flag)."""
    goal_to_go = yards_to_go >= ball_spot
    target = 0 if goal_to_go else ball_spot - yards_to_go  # never past the goal line
    xb, xt = _x(ball_spot), _x(target)
    top, bottom = 64, 404  # playing surface y-range (tall enough to read on a phone)

    p = []
    # Turf with 10-yard stripes, then end zones.
    for i in range(10):
        shade = "#1E7444" if i % 2 == 0 else "#22804B"
        p.append(f'<rect x="{100 + i * 100}" y="{top}" width="100" height="{bottom - top}" fill="{shade}"/>')
    p.append(f'<rect x="0" y="{top}" width="100" height="{bottom - top}" fill="#15532F"/>')
    p.append(f'<rect x="1100" y="{top}" width="100" height="{bottom - top}" fill="#15532F"/>')
    mid = (top + bottom) // 2
    p.append(f'<text x="50" y="{mid}" transform="rotate(-90 50 {mid})" text-anchor="middle" dominant-baseline="middle" '
             f'font-size="40" font-weight="900" letter-spacing="8" fill="#FFFFFF" opacity="0.8">OWN</text>')
    p.append(f'<text x="1150" y="{mid}" transform="rotate(90 1150 {mid})" text-anchor="middle" dominant-baseline="middle" '
             f'font-size="40" font-weight="900" letter-spacing="8" fill="#FFFFFF" opacity="0.8">OPP</text>')

    # Yard lines every 5, goal lines heavier, numbers every 10.
    for yd in range(5, 100, 5):
        x = 100 + yd * 10
        w = 3 if yd % 10 == 0 else 1.5
        p.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{bottom}" stroke="#FFFFFF" stroke-opacity="0.55" stroke-width="{w}"/>')
    for x in (100, 1100):
        p.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{bottom}" stroke="#FFFFFF" stroke-width="6"/>')
    for yd in range(10, 100, 10):
        n = yd if yd <= 50 else 100 - yd
        cls = "num-minor" if n in (10, 30) else "num"
        p.append(f'<text class="{cls}" x="{100 + yd * 10}" y="{bottom - 22}" text-anchor="middle" font-size="56" '
                 f'font-weight="800" fill="#FFFFFF" opacity="0.8">{n}</text>')

    # First-down / goal line: amber bar plus a downward flag at the top (shape, not just color).
    p.append(f'<line x1="{xt}" y1="{top}" x2="{xt}" y2="{bottom}" stroke="#F2B233" stroke-width="9"/>')
    p.append(f'<polygon points="{xt - 16},{top - 4} {xt + 16},{top - 4} {xt},{top + 18}" fill="#F2B233"/>')
    t_long = "GOAL LINE" if goal_to_go else f"1ST DOWN · {spot_short(target)}"
    p.append(_label(xt, 44, t_long, "GOAL" if goal_to_go else "1ST", "#F2B233"))

    # Line of scrimmage (dashed white), the ball, and an arrow showing the offense's direction.
    p.append(f'<line x1="{xb}" y1="{top}" x2="{xb}" y2="{bottom}" stroke="#FFFFFF" stroke-width="4" stroke-dasharray="14 10"/>')
    p.append(f'<ellipse cx="{xb}" cy="{mid}" rx="40" ry="24" fill="#7A3E1D" stroke="#FFFFFF" stroke-width="3"/>')
    p.append(f'<line x1="{xb - 16}" y1="{mid}" x2="{xb + 16}" y2="{mid}" stroke="#FFFFFF" stroke-width="3"/>')
    p.append(f'<polygon points="{xb + 50},{mid - 18} {xb + 80},{mid} {xb + 50},{mid + 18}" fill="#FFFFFF"/>')
    p.append(_label(xb, bottom + 40, f"BALL · {spot_short(ball_spot)}", "BALL", "#FFFFFF"))

    desc = (f"Field: ball at {spot_short(ball_spot).lower()}, "
            f"{'goal line is the target' if goal_to_go else 'first-down line at ' + spot_short(target).lower()}, "
            "offense moving left to right toward the opponent's end zone.")
    return (f'<div class="gng-field"><svg viewBox="0 0 1200 460" role="img" aria-label="{html.escape(desc)}" '
            f'xmlns="http://www.w3.org/2000/svg" font-family="inherit">{"".join(p)}</svg></div>'
            '<div class="gng-legend"><span>Dashed line + football: <b>ball</b></span>'
            f'<span>Amber bar + flag: <b>{"goal line" if goal_to_go else "line to gain"}</b></span>'
            "<span>Offense drives left → right</span></div>")


# ---------- result ----------

TAGS = {"Go": "Go for it", "Punt": "Punt it away", "Kick": "Field goal try"}


def result_card(verdict, justification, stale_summary=None):
    """The constrained answer: verdict word + the LLM's sentence. Status and diagnostics live outside it."""
    eyebrow = (f"Previous situation · {html.escape(stale_summary)}" if stale_summary else "The call")
    why = html.escape(justification) if justification else "<em>(no justification returned)</em>"
    return (
        f'<div class="gng-result v-{verdict.lower()}{" stale" if stale_summary else ""}" role="region" aria-label="Recommendation">'
        f'<div class="gng-eyebrow">{eyebrow}</div>'
        f'<div class="gng-verdict"><span class="gng-word">{verdict.upper()}</span>'
        f'<span class="gng-tag">{TAGS[verdict]}</span></div>'
        f'<p class="gng-why">{why}</p>'
        "</div>"
    )


def status_line(text):
    return f'<p class="gng-status">{text}</p>'


def format_check(violations, plain, stale_summary=None):
    """Validator panel: PASS or BROKEN, then each violation in plain words with its code and detail."""
    ok = not violations
    head = ("One verdict word, one sentence, no hedging." if ok
            else f"{len(violations)} problem{'s' if len(violations) != 1 else ''} with the reply.")
    items = "".join(
        f'<li><span class="gng-code">{c}</span> {html.escape(plain[c])} <span class="gng-sub">({html.escape(d)})</span></li>'
        for c, d in violations)
    stale = (f'<div class="gng-sub">For the previous situation: {html.escape(stale_summary)}</div>'
             if stale_summary else "")
    return (f'<div class="gng-check {"ok" if ok else "bad"}" role="status">'
            f'<span class="gng-badge">{"PASS" if ok else "BROKEN"}</span>{head}'
            f'{"<ul>" + items + "</ul>" if items else ""}'
            '<div class="gng-sub">The raw reply is under the hood.</div>'
            f"{stale}</div>")
