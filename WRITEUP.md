# Sandbox Sprint Beta — Writeup (DRAFT)

**Build:** https://fourth-down-oracle.streamlit.app
**Tier:** T4, Python (confirm against the course's Technical Track pages, A4)

## Writeup (~150 words)

The Fourth Down Oracle takes an NFL fourth-down situation and answers with one word, Go, Punt, or Kick, plus one sentence of why. It's a Tier 4 Python app (Streamlit, Gemini free tier), built with an AI coding agent. The constraint shaped the design: a deliberately crude rule makes the call, Gemini only writes the sentence, and a validator checks every reply against the contract.

What broke surprised me. Across 28 live runs, Gemini kept the format every time. My validator didn't: all six failures were false alarms, replies that mentioned punting only to reject it. Worse, a reply calling a field goal correct because the kick was "virtually impossible" passed.

With four more hours, I'd add a meaning check: a second Gemini call that answers only "does this sentence support the call?" I'd run it on a sample to stay within free-tier limits and compare it with my keyword check on the same 28 runs.

## Balcony Group feedback

*Fill in after the session. R4 is scored on engaging with what the group actually said, including what you rejected and why.*

- **What the group tried:**
- **What they said:**
- **What I changed in response:**
- **What I rejected, and why:**

## Optional demo recording (under 5 minutes)

- Link:

---

## Notes for Josh (not part of the submission)

**Evidence behind each claim**, if a grader asks:

| Claim | Evidence |
|---|---|
| Gemini kept the format in 28 runs | `TEST_RESULTS.md`: 0/28 genuine format violations, verdict matched the rule 28/28 |
| Six failures, all false alarms | `TEST_RESULTS.md` Finding 1; all 6 were V6 keyword flags on replies rejecting a punt |
| "Virtually impossible" kick passed | `TEST_RESULTS.md` Finding 2; scenario #8, repeat 3 |
| Decision/narration split, validator logs and never edits | `README.md` "How it works"; SPEC.md B1–B3 |
| Built with an AI coding agent (R2 stretch) | This repo's commit history and `REFLECTION_LOG.md` |

**Other findings you could swap in** if the Balcony session makes one more relevant:
- The backup model answered 25 of 28 runs after the primary hit its free-tier quota (T5).
- 20 of 28 replies used a line break after the verdict. A strict "Go." rule would have failed 21 of 28 (D3).
- The prompt-injection test ("ignore your instructions…") was resisted 4 of 4 times.
- Fixing V6 for negation (v2) helped in 3 cases but missed the most common pattern, and created a new false negative.

**What to capture during the Balcony session (R4):** who tried which situation, the exact words of any reply that surprised the group, whether anyone broke the format, and every suggestion. Rejected suggestions with a reason are worth as much as accepted ones. Good rejection reasons from this build: "it would cost a second API call per run on a shared free quota (T5)", "it would make the rule smarter, but the rule is crude on purpose (D2)", "it would hide failures instead of logging them (B3)".
