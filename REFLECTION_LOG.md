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
