"""Checks every LLM reply against the output contract (B1, B3, D3, D4).

It reports violations and never rewrites the reply. Codes match SPEC.md:
  V1 first word isn't Go/Punt/Kick     V4 hedge words
  V2 verdict differs from the rule      V5 text before the verdict
  V3 not exactly one sentence           V6 justification argues for another option

Version history (logged on every run so results can be compared):
  v1  V6 flags any mention of another option's keywords.
  v2  V6 ignores a mention when a negating word ("avoid", "than", "not", ...) comes
      shortly before it in the same clause. Added after two live false positives.
"""

import re

VALIDATOR_VERSION = "v2"

VERDICTS = {"go": "Go", "punt": "Punt", "kick": "Kick"}
HEDGE_RE = re.compile(r"\b(probably|maybe|might|perhaps|likely|arguably|depends)\b", re.IGNORECASE)

# V6 keyword heuristic. Phrases that argue FOR each option; a justification that
# uses another option's phrases counts as contradicting the rule's call.
# Patterns match word starts, so "punt" also catches "punting" and "convert" catches "converting".
ARGUES_FOR = {
    "Go": ["go for it", "convert", "keep the offense on the field"],
    "Kick": ["field goal", "kick it", "three points"],
    "Punt": ["punt", "pin them", "flip the field"],
}

# v2: a keyword mention doesn't count when one of these words appears in the
# NEGATION_WINDOW words before it, within the same clause (commas etc. end a clause).
# Window is 6 because a real reply had "avoiding the low probability of converting":
# the cue sits 5 words back. Wider would start excusing genuine contradictions.
NEGATION_CUES = {"not", "no", "never", "instead", "than", "rather", "over", "without", "against",
                 "avoid", "avoids", "avoiding", "skip", "skipping", "forgo", "forgoing"}
NEGATION_WINDOW = 6
CLAUSE_BREAK_RE = re.compile(r"[,;:\u2014\u2013()]")
TOKEN_RE = re.compile(r"[a-z]+(?:['\u2019]t)?")  # keeps "don't" / "can't" as one token

WORD_RE = re.compile(r"[A-Za-z]+")
# A sentence ends at . ! or ? followed by whitespace or end of text,
# so decimals like "3.5" don't count as sentence breaks.
SENTENCE_END_RE = re.compile(r"[.!?]+(?=\s|$)")


def negation_before(lower, start):
    """Return the negating word shortly before position `start` in its clause, or None."""
    clause = CLAUSE_BREAK_RE.split(lower[:start])[-1]
    for tok in reversed(TOKEN_RE.findall(clause)[-NEGATION_WINDOW:]):
        if tok in NEGATION_CUES or tok.endswith(("n't", "n\u2019t")):
            return tok
    return None


def count_sentences(text):
    parts = SENTENCE_END_RE.split(text.strip())
    return sum(1 for p in parts if p.strip())


def validate(raw, rule_verdict):
    """Return dict: parsed_verdict, justification, violations [(code, detail)], notes, passed.

    notes lists V6 mentions that were ignored because they were negated, so the
    decision is visible instead of silent (B3)."""
    text = (raw or "").strip()
    words = list(WORD_RE.finditer(text))
    violations, notes = [], []
    verdict, rest = None, text

    first = words[0] if words else None
    starts_at_zero = first is not None and text[: first.start()].strip() == ""

    if first and starts_at_zero and first.group().lower() in VERDICTS:
        verdict = VERDICTS[first.group().lower()]
        rest = text[first.end():]
    else:
        violations.append(("V1", f"first word was '{first.group() if first else '(empty)'}'"))
        # Treat the bad first word as the would-be verdict, so it isn't counted as a sentence.
        rest = text[first.end():] if first else ""
        # Look a few words in for a verdict, to tell a preamble ("Verdict: Go.")
        # apart from a missing or invented verdict ("Fake.").
        for w in words[1:6]:
            if w.group().lower() in VERDICTS:
                verdict = VERDICTS[w.group().lower()]
                violations.append(("V5", f"preamble before verdict: '{text[: w.start()].strip()}'"))
                rest = text[w.end():]
                break

    # Punctuation right after the verdict word is normalization, not a violation (D3).
    justification = rest.lstrip(" \t\n.,:;!-—–")

    if verdict and verdict != rule_verdict:
        violations.append(("V2", f"said {verdict}, rule said {rule_verdict}"))

    n = count_sentences(justification)
    if n != 1:
        violations.append(("V3", f"{n} sentences"))

    hedges = sorted({h.lower() for h in HEDGE_RE.findall(text)})
    if hedges:
        violations.append(("V4", "hedge words: " + ", ".join(hedges)))

    # V6 is judged against the rule's call, since that's what the LLM was told to justify (B2).
    lower = justification.lower()
    for option, phrases in ARGUES_FOR.items():
        if option == rule_verdict:
            continue
        for p in phrases:
            for m in re.finditer(r"\b" + re.escape(p) + r"\w*", lower):
                cue = negation_before(lower, m.start())
                if cue:
                    notes.append(f"ignored '{m.group()}' ({option}): follows '{cue}'")
                else:
                    violations.append(("V6", f"rule said {rule_verdict}, text says '{m.group()}' ({option})"))
                    break  # one flag per phrase is enough

    return {
        "parsed_verdict": verdict or "",
        "justification": justification,
        "violations": violations,
        "notes": notes,
        "passed": not violations,
    }
