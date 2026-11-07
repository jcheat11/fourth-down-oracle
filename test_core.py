"""Offline checks for the rule and validator (no API calls). Run with:  python test_core.py"""

from oracle import build_message
from rule import decide
from validator import validate


def codes(raw, rule_verdict):
    return [c for c, _ in validate(raw, rule_verdict)["violations"]]


# ---- rule.py (D2) ----  args: yards_to_go, ball_spot, score_diff, quarter, seconds_left
assert decide(1, 80, 0, 2, 480)[0] == "Punt"      # own 20, short: still punt
assert decide(2, 40, 0, 2, 480)[0] == "Go"        # opp 40, 2 to go
assert decide(5, 40, 0, 2, 480)[0] == "Punt"      # opp 40, 5 to go
assert decide(1, 20, 0, 2, 480)[0] == "Go"        # FG range, 1 to go
assert decide(7, 20, 0, 2, 480)[0] == "Kick"      # FG range, 7 to go
assert decide(15, 90, -4, 4, 300)[0] == "Go"      # override: own 10, 4th-and-15, down 4, 5:00
assert decide(15, 90, -3, 4, 300)[0] == "Punt"    # down 3: override doesn't fire
assert decide(7, 20, -10, 4, 120)[0] == "Go"      # override beats the FG

# ---- validator.py (D3, D4) ----
assert codes("Go. Short yardage near midfield is worth the risk.", "Go") == []
assert codes("go: Short yardage is worth the risk.", "Go") == []            # case + colon normalized
assert codes("Go because converting this short yardage keeps the drive alive.", "Go") == []  # real 3.5-flash-lite reply shape
assert codes("Go. A 3.5-yard average makes this easy.", "Go") == []          # decimal isn't a sentence break
assert codes("Punt. Pin them deep. Play defense.", "Punt") == ["V3"]
assert codes("Kick. You should go for it here.", "Kick") == ["V6"]
assert codes("Go. This is probably the right call.", "Go") == ["V4"]
assert codes("Verdict: Go. It is the right call.", "Go") == ["V1", "V5"]
assert codes("Fake. Catch them sleeping.", "Punt") == ["V1"]
assert codes("Punt. Field position matters most here.", "Go") == ["V2"]
assert codes("", "Go") == ["V1", "V3"]
# ---- V6 v2: negation-aware keyword check ----
# Real reply (live run, gemini-3.5-flash, prompt v1): flagged by v1, correctly passes in v2.
KICK_REAL = ("Kick A successful 53-yard field goal gives the team the lead with only one minute remaining "
             "in a tied game while avoiding the low probability of converting a 4th and 10.")
assert codes(KICK_REAL, "Kick") == []
assert validate(KICK_REAL, "Kick")["notes"] == ["ignored 'converting' (Go): follows 'avoiding'"]
assert codes("Go. Rather than punt, keep the offense on the field.", "Go") == []      # cue before the comma
assert codes("Punt. Don't go for it from your own 30.", "Punt") == []                  # n't counts
assert codes("Kick. You should go for it here.", "Kick") == ["V6"]                     # real contradiction still caught
assert codes("Kick. Not now, go for it.", "Kick") == ["V6"]                            # comma ends the clause
# Known v2 misses, kept as tests so the writeup can cite them:
# false positive: rejects a punt without a negating word (seen in the access-check sweep)
assert codes("Go. A punt from the opponent's 40 gains almost nothing.", "Go") == ["V6"]
# false positive: the negation comes AFTER the keyword, and v2 only looks back
assert codes("Go. Settling for a field goal is not enough here.", "Go") == ["V6"]
# false negative: "over" excuses a sentence that really argues for the kick
assert codes("Punt. Kicking it over punting gives three points.", "Punt") == []

# ---- oracle.build_message ----
msg = build_message(4, 90, -7, 4, 95, "  blizzard ", "Go")
assert "4th and 4 at the own 10" in msg and "trailing by 7" in msg and "1:35 left" in msg
assert "Additional context: blizzard" in msg and msg.endswith("The call: Go.")
assert "Additional context" not in build_message(1, 50, 0, 1, 900, "", "Go")

print("all checks passed")
