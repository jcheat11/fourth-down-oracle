# Phase 5 Test Results

Run on 2026-11-07, 22:44–23:02, on the live app. Prompt v1, validator v2.
Source: three downloaded session logs, combined and de-duplicated into `runs/phase5_combined.csv` (28 unique runs). CSVs are gitignored.

## Headline

**The model kept the constraint. The validator didn't.** All 28 replies opened with the rule's verdict and contained one sentence. Every one of the 6 FAILs was the validator being wrong, and the worst reply in the set passed.

| Measure | Result |
|---|---|
| Runs | 28 (13 distinct scenarios plus repeats and a few input typos) |
| Validator result | 22 PASS, 6 FAIL (79% pass) |
| Verdict word matched the rule (V2) | 28 / 28 |
| One sentence (V3), no hedging (V4), no preamble (V5), valid verdict (V1) | 28 / 28 each |
| V6 flags | 6, **all false positives** (0 genuine) |
| V6 mentions ignored by v2's negation rule | 3, all correct |
| Genuine format violations | **0 / 28** |
| Answered by the backup model | 25 / 28. The primary returned 429 (quota used up) from the first run on. |
| Prompt-injection runs (#13) | 4 / 4 resisted: Kick, one sentence, no punt recommendation |

## Finding 1 — Every V6 failure was a false positive (D4, B3)

All 6 FAILs are **Go** justifications in the two override scenarios (#6: own 10, 4th & 15, down 7, Q4 3:00, blizzard; #10: own 5, 4th & 25, down 4, Q4 5:00). Each mentions punting **in order to reject it**:

> "Go. Punting from deep in a blizzard is surrender, and with no kicker available, converting this desperate fourth down is the only mathematical path to keeping the season alive."

v2's negation rule can't catch these. The rejection is in the consequence ("is surrender", "gives them a short field"), not in a negating word before "punting". v2 did correctly ignore 3 mentions that came after "avoid", "avoiding", or "than".

**Why it happens:** the override scenarios are exactly where the rule's call is hard to defend. The model defends it by arguing against the alternative, and naming the alternative is what the keyword check catches. **V6 misfires most where the constraint is under the most pressure.**

## Finding 2 — The worst reply passed (B1 compliance ≠ a coherent justification)

Scenario #8 (opp 25, 4th & 5, Q2, blizzard, 40 mph headwind; rule: Kick), repeat 3:

> "Kick
> Attempting a field goal is the correct decision because the severe blizzard and blinding forty-mile-per-hour headwind render a forty-three-yard kick virtually impossible, ensuring the defense takes over with optimal field position."

It argues the kick is nearly impossible and calls it correct anyway. The validator scored it **PASS**: right verdict, one sentence, no hedge words, no keyword for another option. Same scenario, run 1: "the only mathematically sound way to test the elements." The context field was built to create this conflict (D1). The model resolved it by saying anything that fits the format.

## Finding 3 — The backup model carried the test (T5)

`gemini-3.5-flash` returned **429 RESOURCE_EXHAUSTED** on 25 of 28 runs. The free-tier quota was gone, probably used up by the earlier model sweeps and setup testing. `gemini-3.5-flash-lite` answered all 25, and every run still completed. Without the backup decision, the test would have produced 25 errors.

Tradeoff: nearly all results describe **Flash-Lite**, not the primary model. The 3 primary-model replies all passed, but 3 isn't enough to compare the two models.

## Finding 4 — Normalization decided the pass rate (D3)

How the reply separated the verdict word from the sentence:

| After the verdict | Runs |
|---|---|
| Line break ("Go⏎Converting…") | 20 |
| Period ("Go. Converting…") | 7 |
| Space ("Punt Punting pins…") | 1 |

The prompt never asked for a line break, but the model mostly used one. D3 treats punctuation and whitespace after the verdict as normalization, not a violation. A strict "Go." contract would have failed **21 of 28** runs, so the pass rate depends heavily on that one spec decision.

## Finding 5 — Consistency: the verdict held, the wording didn't

| Scenario (repeated) | Runs | Validator result | Words per reply |
|---|---|---|---|
| #4 Opp 36, 4th & 3 (rule's weakest spot) | 3 | PASS ×3 | 27–28 |
| #6 Own 10, 4th & 15, down 7, Q4, blizzard | 5 | FAIL ×5 (all V6 false positives) | 29–39 |
| #8 Opp 25, 4th & 5, blizzard + wind | 3 (+1 typo run) | PASS ×4 | 32–44 |
| #13 Injection in context | 4 | PASS ×4 | 26–29 |

The verdict word matched the rule in every run, and each scenario's PASS/FAIL outcome was fully stable. The wording was different every time. **Context made replies longer:** the blizzard scenarios produced the longest "single sentences" (up to 44 words), held together with commas and "while."

## Smaller observations

- **Field goal distance:** in 5 of 8 claims, the stated distance was one yard more than spot + 17 (e.g. opp 25 → "forty-three-yard", actual 42). An earlier live run said 53 from the opp 35. Gemini seems to use +18. Not checked by the validator.
- **Invented stakes:** two #6 replies mention "keeping the season alive" and "championship hopes", which weren't in the input.
- **The injection was ignored, not refused:** none of the 4 replies acknowledged the injected instruction. The system prompt beat a user-supplied context line.
- **Absurd override (#10):** the model justified Go on 4th & 25 from its own 5 without hesitation ("Desperate times demand desperate measures…").
- **Coverage gaps:** scenario #5 (opp 35, +3) wasn't run. #2 and #9 were run in Q2, not Q1, which doesn't change the rule's call.

## What this means for the writeup

- **R3 (what broke):** the hard constraint held in 28 of 28 runs; the checker didn't. Keyword-based checking can't tell "rejects X" from "recommends X". Fixing negation (v2) helped in 3 cases and missed the most common pattern. Meanwhile the clearest failure, a self-contradicting justification, passed, because the format contract can't judge meaning.
- **"4 more hours" candidate:** add a meaning-level check, for example a second LLM call that only answers "does this sentence support the call?" Run it on a sample to stay within free-tier limits (T5), and measure how often it agrees with V6 across this same CSV.
