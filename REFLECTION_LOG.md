# Reflection Log

Entries are tagged with constraint IDs from `CLAUDE.md`. Format:

```
### YYYY-MM-DD — short title
- Constraint IDs:
- What happened:
- What I expected:
- What I changed (or decided not to change, and why):
```

---

### 2026-11-07 — Colab access test returned "Go." with a period
- Constraint IDs: B1, D3
- What happened: A test prompt in Colab returned "Go." plus one sentence, three times in a row. The verdict was stable across runs; the wording varied.
- What I expected: A bare verdict word. The trailing period wasn't asked for.
- What I changed: Made it a spec question. D3 now treats case and punctuation right after the verdict word as normalization, not a violation. The raw output is still stored, so the normalization can be audited.

### 2026-11-07 — The first test didn't stress the constraint
- Constraint IDs: B1, Phase 5
- What happened: The Colab test scenario was an easy call, so a clean one-word, one-sentence answer says little about whether the constraint holds.
- What I expected: n/a. This is a note about test design.
- What I changed: Phase 5 includes close calls, context traps (blizzard, down 10 with 2:00 left), and absurd cases. The D1 context field goes to the LLM only, which deliberately creates rule/LLM disagreement.

### 2026-11-07 — Spec decisions D1–D5 accepted
- Constraint IDs: D1–D5, B2
- What happened: Accepted the proposed spec as written (see `SPEC.md`). Key choices: the LLM restates the rule's verdict instead of having it prepended, so a changed call is detectable (V2); V6 contradiction detection is a keyword heuristic rather than an LLM judge, to save free-tier quota (T5); verdicts are strictly Go/Punt/Kick.
- What I expected: n/a.
- What I changed: n/a. Known weak spots going in: V3 sentence counting will misfire on decimals and abbreviations, and V6 keywords will miss paraphrased contradictions.

### 2026-11-07 — The model list includes models the key can't call
- Constraint IDs: T4, T2
- What happened: On the deployed access check, the key listed 47 generateContent models and the Secrets setup worked. The first test call went to `gemini-2.5-flash`, which was in the list, and failed with 404 NOT_FOUND: "no longer available to new users", with a suggestion to use `gemini-3.8-flash`.
- What I expected: If the API lists a model as supporting generateContent, the key can call it.
- What I changed: The listing isn't proof of access. A model is only pinned after a test call to it succeeds. Also avoiding the `-latest` aliases (`gemini-flash-latest`), because they can silently change which model runs, which defeats T4.

### 2026-11-07 — The recommended model returned 503 "high demand"
- Constraint IDs: T5, T4
- What happened: `gemini-3.8-flash`, the model Google's own 404 message recommended, returned 503 UNAVAILABLE: "currently experiencing high demand... try again later."
- What I expected: The rate-limit risk in T5 was a 429 from our shared free-tier quota. This is a different failure: Google's servers are busy, regardless of our usage.
- What I changed: The app's error handling has to cover 503 as well as 429. Open question for Phase 3: on a 503, retry the same model, or fall back to a second pinned model? A fallback must be logged per run, so the run log shows which model actually answered.

### 2026-11-07 — Model sweep: 6 of 18 answered, and the replies already test B1
- Constraint IDs: T4, T5, B1, D3, D4 (V6)
- What happened: With a 20s timeout per model, these answered OK: gemini-3-flash-preview, 3.1-flash-lite, 3.1-flash-lite-preview, 3.5-flash, 3.5-flash-lite, 3.6-flash. Failures: 404 (2.5 family retired), 429 (image models, quota), 400 (a tts model), 504 timeout (3.7-flash). The newest models (3.7, 3.8) were the overloaded ones. Even with the same prompt, the reply format varied: most said "Go. <sentence>", but 3.5-flash-lite said "Go because converting...", with no punctuation after the verdict. 3-flash-preview's "Go" reply begins "A punt from the opponent's..." Under V6 keywords, the word "punt" in a Go justification counts as a contradiction, even though the sentence is arguing against punting.
- What I expected: Format differences would show up in Phase 5, not in the access test.
- What I changed: Nothing yet. "Go because..." passes D3 as written, since punctuation after the verdict is optional. The "punt" case is a preview of a V6 false positive: a keyword check can't tell "punt" (recommending it) from "a punt here gains little" (rejecting it). Keep the heuristic and log its misfires, per the spec.

### 2026-11-07 — Pinned gemini-3.5-flash with a 3.5-flash-lite backup
- Constraint IDs: T4, T5
- What happened: Chose `gemini-3.5-flash` as the primary and `gemini-3.5-flash-lite` as the backup, out of the six models that passed the sweep.
- What I expected: To pin a single model. The 503/504 results on the newest models made a single point of failure look risky for a live demo where all viewers share one quota.
- What I changed: Added a backup, logged per run. Tradeoff accepted: B1 compliance may differ between the two models (3.5-flash-lite already showed a "Go because..." format variation), so validator results should be read per model.

### 2026-11-07 — Phase 3 core built; validator choices made while coding
- Constraint IDs: B1–B3, D3, D4, T5
- What happened: Built app.py (form, rule, Gemini call with backup, validator, run log with CSV download). Writing the validator forced three choices the spec didn't settle: (1) a preamble like "Verdict: Go." fires both V1 and V5; (2) V6 is checked against the rule's call, not the LLM's word; (3) a sentence break must be followed by whitespace, so "3.5" no longer counts as two sentences, which is better than the spec expected, though "vs." still does. An offline test also caught a validator bug: for "Fake. Catch them sleeping." it counted "Fake." as a sentence and wrongly added V3.
- What I expected: The spec's D4 table would translate straight into code.
- What I changed: Fixed the bug, updated SPEC.md to match the code, and kept the known V6 false positive ("Go. A punt from the 40 gains almost nothing.") as a test that documents the miss rather than hiding it.

### 2026-11-07 — After the redeploy, the app loaded as a wall of red errors in my browser
- Constraint IDs: R1, T7, A6
- What happened: After switching the deployed app from access_check.py to app.py, the page first spun forever. Then it loaded with every input box replaced by "TypeError: Failed to fetch dynamically imported module". The same URL loaded cleanly in a fresh browser with no cache, and the app also ran fine locally.
- What I expected: A redeploy would just show the new version.
- What I changed: Nothing in the code; the problem was the browser, not the app. A browser that visited before a redeploy can keep old page files that point to ones that no longer exist. A hard refresh (Cmd+Shift+R) or a private window fixes it. Demo rule: no pushes on demo day, and a fresh-browser check right before the Balcony session.

### 2026-11-07 — Interface pass (D6): where the UI brief ran into B1–B3
- Constraint IDs: D6, B1, B2, B3, R1
- What happened: Rebuilt the interface as "Go / No Go": a broadcast-style summary bar, an SVG field that redraws live, a single "Make the Call" button, a verdict card, and an "Under the Hood" panel. The UI brief asked for "verdict plus exactly one sentence" in the result. But the validator's job is to show when Gemini breaks that rule, not to hide it (B3).
- What I expected: Styling work that wouldn't touch the constraint.
- What I changed: The card shows the rule's verdict and Gemini's text untrimmed. A two-sentence reply shows as two sentences, with a format-check line beside it. When the API fails, no card is shown at all, rather than a verdict with no sentence. Browser testing at 360px found Streamlit's fixed toolbar covering the header and a field too flat to read on a phone; both fixed. Known gaps: Streamlit's +/- stepper buttons have no accessible names, and for goal-to-go the message to Gemini still says "4th and 4" while the UI says "4TH & GOAL".

### 2026-11-07 — First live V6 false positives: the keyword check can't read negation
- Constraint IDs: D4 (V6), B3, R3
- What happened: In early live runs, V6 flagged two correct replies as "argued for another option":
  1. Rule said Go; the reply mentioned "punt" while arguing against punting (raw reply not saved).
  2. Rule said Kick (4th and 10 at the opponent's 35, tied, Q4 1:00, gemini-3.5-flash, prompt v1). Raw reply: "Kick A successful 53-yard field goal gives the team the lead with only one minute remaining in a tied game while avoiding the low probability of converting a 4th and 10." V6 matched "convert" (Go), but the sentence rejects going for it. The reply also skipped punctuation after the verdict, which D3 allows.
- What I expected: Exactly this. The spec (D4) and the Phase 3 entry both named V6 false positives as a known weak spot. The access-check sweep had already shown the "punt" version on a preview model.
- What I changed (pending decision): The validator does what it was built to do. The issue is that a keyword match can't tell "recommends X" from "rejects X". Note for the fix: in case 2 the negating word ("avoiding") is 5 words before "converting", so a negation window narrower than 5 words would still miss it.

### 2026-11-07 — Validator v2: negation-aware V6, and what it still gets wrong
- Constraint IDs: D4 (V6), B3, R3
- What happened: Chose option 3 of three (leave as is / relabel only / negation-aware). In v2, V6 ignores a keyword when a negating word appears up to 6 words before it in the same clause. The live Kick reply above now passes, and the app shows "ignored 'converting' (Go): follows 'avoiding'" rather than silently dropping it. On screen, V6 now reads "may argue for another option (keyword check)". Each run logs validator_version and v6_ignored.
- What I expected: That checking for negation would fix V6. Writing tests showed it trades one error for another. It still flags replies that are fine ("A punt from the 40 gains almost nothing" has no negating word; in "a field goal is not enough" the negation comes after the keyword). It also now excuses a real contradiction: "Kicking it over punting gives three points", with the rule saying Punt, passes because "over" counts as a negation.
- What I changed: Kept the rule simple and kept all three misses as tests, so the writeup can cite exact cases. Decided against an LLM judge, which still costs a second API call per run (T5). For the "4 more hours" item: measure how often V6 is wrong across the Phase 5 run log, v1 against v2.

### 2026-11-07 — Phase 5 results: the constraint held, the checker broke (see TEST_RESULTS.md)
- Constraint IDs: B1, B3, D3, D4 (V6), T5, R3
- What happened: 28 live runs across 13 scenarios plus repeats. The model followed the format every time: rule's verdict first, one sentence, no hedging, 28 of 28. The validator reported 6 FAILs, all V6 false positives: Go justifications in the override scenarios that name punting in order to reject it ("Punting from deep in a blizzard is surrender..."). v2's negation rule can't see a rejection expressed as a consequence. Meanwhile the clearest bad reply PASSED: "Attempting a field goal is the correct decision because the... headwind render a forty-three-yard kick virtually impossible." The primary model hit its free-tier quota (429) on 25 of 28 runs, and the backup answered all of them.
- What I expected: That the LLM would break the format under pressure (context traps, injection) and the validator would catch it. It went the other way. The format was easy for the model to keep; meaning was where it failed, and a format checker can't see meaning.
- What I changed: No prompt revision. With 0 genuine format violations, a revision has nothing to fix. No V6 v3 either: the missed pattern needs language understanding, not more keywords. Recorded as the main unresolved failure and the "4 more hours" candidate: a meaning-level check ("does this sentence support the call?") on a sample, compared against V6 on this same CSV.

### 2026-11-07 — Normalization (D3) decided the pass rate
- Constraint IDs: D3, B1
- What happened: 20 of 28 replies put a line break after the verdict word instead of a period, 7 used a period, 1 a space. The prompt didn't ask for a line break.
- What I expected: "Go." with a period, as in the Colab test.
- What I changed: Nothing. D3 already treats this as normalization. But a strict "Go." contract would have failed 21 of 28 runs. The early spec choice to treat "Go." the same as "Go" mattered more to the pass rate than anything the model did.
