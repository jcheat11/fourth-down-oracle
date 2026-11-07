# Fourth Down Oracle — Spec

Decisions D1–D5 accepted by Josh on 2026-11-07. D6 deferred until after the Phase 4 deploy.

## Phase 1 gate statements

**The constraint (B1–B3), in two sentences.** Every Oracle response is the rule's verdict word (Go, Punt, or Kick) followed by exactly one sentence of justification, with nothing before, after, or hedged. The LLM writes that response but never makes the call, and every raw output is checked and logged against this contract rather than repaired.

**The escape-hatch rule (D2 override), in two sentences.** In the 4th quarter with 5:00 or less left, a team trailing by 4 or more always goes for it, whatever the field position or distance. It exists because a punt or field goal can't win that game, and it will sometimes produce an obviously bad call, which is the point.

---

## D1 — Inputs

| Field | Type | Allowed values | Used by |
|---|---|---|---|
| Down | fixed | 4 | — |
| Yards to go | int | 1–30 | rule + LLM |
| Ball spot | int | 1–99, yards from the **opponent's** goal line (99 = own 1, 50 = midfield, 1 = opp 1) | rule + LLM |
| Score differential | int | −28 to +28, from the offense's view (negative = trailing) | rule + LLM |
| Quarter | int | 1–4 | rule + LLM |
| Time left in quarter | mm:ss | 0:00–15:00 | rule + LLM |
| Context | free text | optional, short | **LLM only** |

The context field reaches the LLM but not the rule. That deliberately creates disagreement: a blizzard changes what the LLM is told but not the call it has to justify.

The UI shows ball spot as a normal football yard line ("own 25", "opp 30"); internally it is stored as yards from the opponent's goal.

## D2 — Decision rule

Base table, by ball spot (yards from the opponent's goal) × yards to go:

| Ball spot | 1–2 to go | 3+ to go |
|---|---|---|
| Own territory (51–99) | Punt | Punt |
| Opp 50 to opp 36 (36–50) | Go | Punt |
| Opp 35 and in (1–35, FG range) | Go | Kick |

Override (checked first): quarter 4, time left ≤ 5:00, score differential ≤ −4 → **Go**.

It's crude on purpose. The rule's job is to give the LLM a call it might disagree with, not to be right about football.

## D3 — Output contract

- **Allowed verdict words:** Go, Punt, Kick.
- **Shape:** `<Verdict> <one sentence>`. The LLM is told the rule's verdict and must restate it as the first word, so the validator can detect the LLM changing the call.
- **Normalization (not a violation):** case, and punctuation right after the verdict word (`Go.`, `go`, `GO:`, `Go —` all parse as `Go`). Leading/trailing whitespace is stripped.
- **One sentence:** after the verdict word, the justification contains exactly one sentence-ending `.`, `!`, or `?`. The terminator may be missing at the very end, which counts as one sentence. Decimals and abbreviations ("3.5", "vs.") may trip this; those are logged as validator false positives, not tuned away.
- **The raw output is always stored**, alongside the parsed verdict and justification (B3).

## D4 — Violations

| Code | Violation | Detection |
|---|---|---|
| V1 | First word is not an allowed verdict | First token after normalization is not in {Go, Punt, Kick} |
| V2 | Verdict word differs from the rule's call | Parsed verdict ≠ rule verdict |
| V3 | Not exactly one sentence | Sentence-terminator count in justification ≠ 1 (see D3) |
| V4 | Hedge words | Case-insensitive word match: probably, maybe, might, perhaps, likely, arguably, depends |
| V5 | Preamble | Any text before the verdict word (e.g., "Verdict:", "The Oracle says") |
| V6 | Justification argues for another option | Keyword heuristic: verdict Punt/Kick but text says "go for it" / "convert" / "keep the offense on the field"; verdict Go/Punt but text says "field goal" / "kick it" / "three points"; verdict Go/Kick but text says "punt" / "pin them" / "flip the field" |

A run passes only with zero violations. Several violations can fire on one run; all are logged.

V6 is a keyword heuristic, not an LLM judge. A second judge call would double free-tier usage (T5). Its false positives and misses are expected and are material for the reflection log.

## D5 — Edge verdicts

Strictly Go / Punt / Kick. "Fake" or "Two-point" in the verdict position is a V1 violation and gets logged.

## D6 — Interface

Deferred. Time-boxed to whatever budget remains after Phase 4 (ugly deploy).

---

## Model (T4, T5)

Decided by Josh on 2026-11-07, after the access-check sweep.

- **Primary:** `gemini-3.5-flash`. A stable release, clean format in the sweep, one step behind the newest (overloaded) models.
- **Backup:** `gemini-3.5-flash-lite`. Used only when the primary returns 503, 429, or times out. It runs on separate capacity, and quotas are per model.
- Each run logs which model actually answered. A run answered by the backup counts as a normal run, not a violation, but it's visible in the run log.
- No `-latest` aliases and no preview models.
