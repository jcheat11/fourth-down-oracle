# Go / No Go — the Fourth Down Oracle

**Live app:** https://fourth-down-oracle.streamlit.app
(No account or key needed. If it's been idle, give it up to a minute to wake up.)

Enter an NFL fourth-down situation and the Oracle answers with **one word, Go, Punt, or Kick, and one sentence of why.** Nothing else.

Built for Sandbox Sprint Beta, BUAD 583 (AI Fluency & Strategy). The theme is "Constraint as Craft": the whole build lives inside that one-word, one-sentence rule, and the interesting part is seeing where the rule breaks.

## How it works

The decision and the explanation are deliberately split:

1. **A fixed Python rule makes the call** (`rule.py`). It's a rough table of field position × yards to go, plus one late-game override. It's crude on purpose: its job is to give the AI a call it might disagree with, not to be right about football.
2. **Gemini only writes the sentence** (`oracle.py`). It's told the call and asked to justify it. It never makes the decision.
3. **A validator checks every reply** (`validator.py`) against the one-word, one-sentence contract and logs what breaks. It reports problems and never edits the reply.

So the question the app can answer is: **does the AI's explanation stay inside the constraint, and does it actually support a call it didn't make?**

## Using it

1. Set field position (own/opponent territory plus yard line), yards to gain, score margin, quarter, and time left. The field and situation bar update as you type, and nothing is sent to Gemini yet.
2. Optionally add **context** ("blizzard, kicker injured"). Context goes to Gemini only; the rule ignores it. That's a deliberate way to make the explanation fight the call.
3. Click **Make the Call**.
4. Read the result:
   - **The call:** the verdict and Gemini's sentence, exactly as returned.
   - **Format check:** PASS or BROKEN, with each problem in plain words.
   - **Under the Hood:** the rule's reasoning, the exact message sent to Gemini, the raw reply, and the model used.
5. **Download session results (CSV)** saves every run in your session.

### The rule

| Ball spot | 1–2 yards to go | 3+ yards to go |
|---|---|---|
| Own territory | Punt | Punt |
| Opponent 50 to 36 | Go | Punt |
| Opponent 35 and in (FG range) | Go | Kick |

**Override (checked first):** in Q4 with 5:00 or less left, trailing by 4 or more → **Go**, from anywhere.

### What the format check looks for

| Code | Problem |
|---|---|
| V1 | Doesn't open with Go, Punt, or Kick |
| V2 | Names a different call than the rule |
| V3 | Not exactly one sentence |
| V4 | Hedge words (probably, maybe, might, perhaps, likely, arguably, depends) |
| V5 | Text before the verdict |
| V6 | May argue for another option (keyword check; v2 skips mentions right after negating words like "avoid", "than", "not") |

Case and punctuation after the verdict are treated as normal, so "Go.", "go", and "Go" on its own line all pass.

## Model

- **Primary:** `gemini-3.5-flash`
- **Backup:** `gemini-3.5-flash-lite`, used only when the primary is overloaded or erroring (500, 503), out of quota (429), or times out (504, or no answer within 30 seconds)
- Both run on the Google AI Studio free tier. Each run logs which model answered.
- Prompt version **v1**, validator version **v2**. Both are recorded on every run.

## Known limits

- **The format check can't judge meaning.** In testing, a reply calling a field goal "the correct decision because the headwind render a forty-three-yard kick virtually impossible" scored PASS. See [TEST_RESULTS.md](TEST_RESULTS.md).
- **V6 has false alarms.** It flags replies that mention another option in order to reject it ("Punting into a blizzard is surrender"). In Phase 5 testing, all 6 V6 flags were false positives.
- **The rule isn't football analytics.** It ignores leads (it says Go when up 14 with 1:00 left), weather, and anything else in the context field.
- **Shared free-tier quota.** Everyone using the app draws on one Gemini quota. Each browser session is capped at 25 calls, and when the primary model's quota runs out the backup answers. If both are exhausted, the app shows a plain "try again" message and no verdict.
- **Results live in your browser tab.** Download the CSV before closing it; nothing is stored on a server.
- **Old copies of the page after an update.** A browser that visited before a redeploy can show red "Failed to fetch dynamically imported module" boxes. Press **Cmd/Ctrl+Shift+R**, or open the app in a private window.
- **The app sleeps when idle.** Free Streamlit apps go to sleep after inactivity and take up to a minute to wake.
- **Small accessibility gap.** Streamlit's +/− stepper buttons have no screen-reader labels.

## Demo-day checklist

1. **No pushes on demo day.** Every push redeploys the app and can break pages that are already open.
2. **10–15 minutes before:** open the app in a **private window** to wake it and avoid old cached copies.
3. **Make one call** to confirm Gemini is answering.
4. **Demo from that window.** If something breaks live, press Cmd+Shift+R; if Gemini is down, show a downloaded CSV and [TEST_RESULTS.md](TEST_RESULTS.md).

## Project files

| File | What it is |
|---|---|
| `app.py` | The page and the flow: inputs → rule → Gemini → validator → log |
| `rule.py` | The decision rule |
| `oracle.py` | Builds the message for Gemini and calls it, with the backup model |
| `validator.py` | The format check (V1–V6) |
| `ui.py` | Look and layout: field drawing, situation bar, verdict card |
| `config.py` | Pinned model names, prompt text and version, request limits |
| `test_core.py` | Offline checks for the rule and validator (`python test_core.py`) |
| `access_check.py` | Setup tool: lists models and tests which ones answer |
| `SPEC.md` | Design decisions D1–D6 |
| `REFLECTION_LOG.md` | What broke, what surprised me, what I changed, tagged by constraint |
| `TEST_RESULTS.md` | Phase 5 results from 28 live runs |
| `TEST_PLAN.md` | The scenarios used for testing |

## Running it locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml   # then paste your Google AI Studio key
.venv/bin/streamlit run app.py
```

`.streamlit/secrets.toml` is gitignored; the key never goes into the repo. On Streamlit Cloud, the key lives in the app's **Settings → Secrets**.
