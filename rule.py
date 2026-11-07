"""The decision rule (D2, B2). It makes the call; the LLM only explains it.

Crude on purpose: its job is to give the LLM a call it might disagree with,
not to be right about football.

ball_spot is yards from the OPPONENT's goal line: 99 = own 1, 50 = midfield, 1 = opp 1.
"""


def decide(yards_to_go, ball_spot, score_diff, quarter, seconds_left):
    """Return (verdict, reason). reason is shown in the UI and the run log."""
    # The escape hatch is checked first: late and down by 4+, a kick can't win it.
    if quarter == 4 and seconds_left <= 300 and score_diff <= -4:
        return "Go", "Override: Q4, 5:00 or less left, trailing by 4+"

    short = yards_to_go <= 2

    if ball_spot >= 51:
        return "Punt", "Own territory"
    if ball_spot >= 36:
        return ("Go", "Opp 36-50, 1-2 to go") if short else ("Punt", "Opp 36-50, 3+ to go")
    return ("Go", "FG range, 1-2 to go") if short else ("Kick", "FG range, 3+ to go")
