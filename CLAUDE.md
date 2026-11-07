# Fourth Down Oracle — Build Handoff Brief

Handoff from a planning session to Claude Code. Read this whole file before writing any code. Save it in the repo root (or as `CLAUDE.md`) so it stays in context.

---

## 1. What this is

**The Fourth Down Oracle** is a small web app. The user enters an NFL fourth-down game situation, and the Oracle answers with **exactly one word (Go / Punt / Kick) plus one sentence of justification**. Nothing else.

It's Josh's submission for **Sandbox Sprint Beta** in BUAD 583 (AI Fluency & Strategy), part of his MBA. The course theme is **"Constraint as Craft"**: build something that lives entirely inside one hard constraint, then report honestly on where the constraint broke.

**Core architecture idea (decided):** separate the *decision* from the *narration*.
- A simple Python decision rule makes the call.
- The LLM writes only the one-sentence justification.
- A validator checks every LLM output against the constraint and logs violations.

This makes the most interesting failure mode testable: **does the LLM's justification disagree with the rule's call, or drift outside the constraint?**

---

## 2. Constraint register

Every constraint has an ID. Reference these IDs in commits, the reflection log (Section 7), and conversation with Josh. The writeup will cite them.

### A. Assignment constraints (set by the course — non-negotiable)

| ID | Constraint |
|---|---|
| A1 | Solo work. Time budget is 6–10 hours total, including demo prep and writeup. |
| A2 | Must be distinct from Josh's BUAD 583 course capstone. A football tool is distinct. |
| A3 | Theme is "Constraint as Craft": one hard constraint that the build lives inside. |
| A4 | Should stretch tooling: a tier not yet tried, or a constraint that forces creativity. Tiers are T1 prompts, T2 custom GPT, T3 no-code workflow, and T4 Python. A hosted Python app is expected to count as T4; Josh will confirm against the course's Technical Track pages. |
| A5 | Deliverables: (1) a working build link; (2) a ~150-word writeup covering what it does, which tier, and one specific thing to do differently with 4 more hours; (3) a section on Balcony Group feedback, including what was rejected and why; (4) an optional demo recording under 5 minutes. |
| A6 | Live demo at a Balcony Group session: about 5 minutes of the working build plus 3 minutes of group reaction. The build itself, not slides. |
| A7 | Optional assignment. A Beta score replaces Sprint Alpha only if it is higher, so the downside is time, not grade risk. |

### R. Rubric (100 points) — what the build is judged on

| ID | Dimension | Points | Implication for the build |
|---|---|---|---|
| R1 | Build shipped and working | 40 | Exists, accessible, does what the writeup claims, honest about its limits. **Deploy early.** |
| R2 | Ambition and fit | 20 | Appropriate tier, genuinely stretches a course skill, distinct from capstone. |
| R3 | Reflection | 20 | Specific and honest about what broke or defied expectation. Generic praise of the tool scores at the bottom. **Breakage is an asset; log it.** |
| R4 | Response to Balcony feedback | 20 | Engages with what the group actually said, including what was rejected and why. |

The course states a small, honest build that breaks interestingly scores well, and **polish is not required.**

### B. Build constraint (the "craft" constraint — decided)

| ID | Constraint |
|---|---|
| B1 | Every Oracle response is **exactly one verdict word from the allowed set** followed by **exactly one sentence** of justification. No hedging, no extra sentences, no preamble. |
| B2 | The verdict comes from the Python decision rule, not the LLM. The LLM explains a call it did not make. |
| B3 | Every LLM output is checked against B1 by a validator, and violations are logged, not silently fixed. The raw output is kept. |

### T. Technical constraints

| ID | Constraint |
|---|---|
| T1 | Stack: Python + Streamlit, hosted free on Streamlit Community Cloud, deployed from a GitHub repo. |
| T2 | LLM: Gemini via the **Google AI Studio free tier** (Josh creates the key). The `google-genai` SDK is expected. `google.colab.ai` worked in testing but **does not work outside Colab**, so it is not an option here. |
| T3 | **The API key must never be committed.** Locally it lives in `.streamlit/secrets.toml`, which must be in `.gitignore` before the first commit. In deployment it goes in Streamlit Cloud's secrets settings. Read it via `st.secrets`. Verify the gitignore before every push. |
| T4 | **Pin the model name explicitly** in config. Don't rely on defaults. List available models via the API first and let Josh pick a Flash or Flash-Lite model, since names change often. Log which model is used. |
| T5 | Free-tier rate limits are shared across all app users. Add a simple per-session request cap and a friendly message when it's hit, plus graceful handling of 429 / rate-limit errors. |
| T6 | No paid services, and nothing that requires graders to have an account or a key. Graders should only need the URL. |
| T7 | Free Streamlit apps may sleep when idle. Note in the README that the app should be opened before the demo. |

### J. How to work with Josh (interaction constraints)

| ID | Constraint |
|---|---|
| J1 | Josh is a mid-career MBA student and operator. Use a peer register; skip basic explanations of business or programming concepts unless he asks. |
| J2 | **Josh owns the design decisions in Section 4.** Do not silently decide them. Present the options and tradeoffs briefly, recommend if useful, and wait for his call. |
| J3 | Josh must be able to explain every part of the app in the demo and writeup. When you write non-obvious code, explain the *why* in a sentence or two. Keep the code small and readable over clever. |
| J4 | Treat ideas he floats as exploratory unless he says he's decided. |
| J5 | Plainspoken, dense, no emojis, no motivational filler. Lead with the useful answer. |
| J6 | If you make a mistake, name it and fix it cleanly. |

---

## 3. Status (what's already done)

- **Decided:** the Fourth Down Oracle concept, the B1–B3 architecture, and the app route (Streamlit + Gemini free tier) instead of a Colab notebook.
- **Access test passed in Colab:** Gemini models were available, and a test prompt returned a single "Go." plus one sentence, three times. The verdict was stable across runs; the wording varied.
- **First observations already logged:** (a) the output came back as "Go." with a period, so normalization of punctuation and case is an open spec question; (b) the test scenario was an easy call, so it didn't stress the constraint.
- **Prior context:** Josh's Sprint Alpha build ran into LLM API access problems. Getting access working reliably is a known risk area; verify it first.

---

## 4. Open design decisions — Josh decides these (J2)

| ID | Decision | Notes |
|---|---|---|
| D1 | **Input fields** and their allowed values | Likely: down (fixed at 4), yards to go, yard line, score differential, quarter and time remaining. Possibly a "context" field (weather, injury) as a deliberate stress test. |
| D2 | **Decision rule** | A crude lookup by field position × distance, with maybe one adjustment for score and time. **Keep it rough on purpose.** Its job is to give the LLM something to disagree with, not to be correct about football. If it takes more than a small table, simplify. |
| D3 | **Output contract details** | Exact allowed words; whether "Go." equals "Go"; capitalization; what counts as one sentence. |
| D4 | **Violation definitions** | Proposed examples: extra sentences, a verdict word outside the set, hedge words ("probably," "maybe"), a justification that contradicts the rule's verdict. Josh confirms the list. |
| D5 | **Edge-verdict policy** | Strictly Go / Punt / Kick, or also allow "Fake" and "Two-point." |
| D6 | **Interface scope** | A "cool football interface" is wanted (a field graphic showing the ball spot, a scoreboard styling). It is time-boxed to whatever budget remains after deployment (see Section 5). |

---

## 5. Build sequence (with gates)

Total target: about 8 hours of Josh's time, including the non-code phases.

| Phase | Work | Gate before moving on |
|---|---|---|
| 1. Spec | Josh settles D1–D5. Record the decisions in `SPEC.md`. | The constraint and the escape-hatch rule can each be stated in two sentences. |
| 2. Access | Repo scaffold, `.gitignore` with secrets (T3), key wired through `st.secrets`, list models, pin one (T4), one test call. | A local `streamlit run` returns an LLM response. The key is confirmed absent from git. |
| 3. Core | Input form → rule → LLM call → validator → display verdict, justification, and validator status. Session log of every run. | One clean end-to-end run, plus one run that produces a logged violation. |
| 4. Ugly deploy | Push to GitHub, deploy to Streamlit Cloud, set secrets there. | **The public URL works from a phone. This locks in R1.** Target about the halfway point of the budget. |
| 5. Test | Run about 10 scenarios: obvious, close, context traps (e.g., down 10 with 2:00 left, a blizzard), and absurd (4th-and-25 from your own 5). Repeat 3–4 of them 3 times for consistency. At most 2 prompt revisions, each one saved. | At least one failure that can be explained. If nothing broke, push harder cases. |
| 6. Interface | Football UI polish, only within the remaining budget. | The app still deploys and works after the changes. |
| 7. Package | README with what it is, how to use it, known limits, and the model used. A run log export (CSV download) for the writeup. Optional 2-minute recording. | A stranger can understand the app in 60 seconds. |

**Cut order if over budget:** interface polish → recording → repeat test runs. Never cut deployment or the reflection log.

---

## 6. Features worth building in (they serve R3 and R4)

- **Run log:** each run stores timestamp, inputs, rule verdict, raw LLM output, parsed verdict, validator result, violation types, prompt version, and model. Download as CSV.
- **Prompt versioning:** the system prompt lives in one config place with a version label, so test results can be compared across revisions.
- **Visible validator:** show pass or fail and the reason in the UI. During the demo, the group sees the constraint break in real time, which is useful for R4.
- **Optional "free text" field:** for the demo, so the group can try to break the constraint with weird situations.

---

## 7. Reflection log (maintain throughout)

Keep `REFLECTION_LOG.md` in the repo. Add an entry whenever something breaks, surprises, or forces a decision. Entry format:

```
### YYYY-MM-DD — short title
- Constraint IDs: (e.g., B1, D3)
- What happened:
- What I expected:
- What I changed (or decided not to change, and why):
```

Also log the Balcony session there: what the group tried, what they said, what was changed, what was rejected and why (R4).

---

## 8. Writeup traceability

The writeup should be able to point to evidence for each rubric dimension:

| Rubric | Evidence to cite |
|---|---|
| R1 Shipped and working | Public URL; README known-limits section; validator results showing what it does and doesn't do |
| R2 Ambition and fit | T4 Python app with hosted LLM; B2 decision/narration split; first use of an AI coding agent for the build; distinct from the capstone (A2) |
| R3 Reflection | `REFLECTION_LOG.md` entries tagged to B1–B3 and D-decisions; run-log CSV with violation rates and consistency results |
| R4 Balcony response | The Balcony entries in the reflection log: what was said, changed, and rejected, with reasons |
| A5 "4 more hours" item | Drawn from the most important unresolved failure in the log |
