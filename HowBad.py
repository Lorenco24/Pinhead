import math
import streamlit as st

def clamp(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, x))

# ---------- SCORING FUNCTIONS ----------

def score_single_stat_prop(side, line, result, alpha=2.0):
    side = side.lower()
    if side not in ["over", "under"]:
        raise ValueError("side must be 'over' or 'under'")

    # Only score if it actually lost
    if side == "over" and result >= line:
        return None
    if side == "under" and result <= line:
        return None

    if side == "over":
        ratio = result / line if line > 0 else 0.0
    else:  # under
        ratio = line / result if result > 0 else 0.0

    score = 100.0 * (ratio ** alpha)
    return clamp(score)

def score_combo_prop(side, combo_type, line, points, rebounds, assists, alpha=2.0):
    side = side.lower()
    combo_type = combo_type.upper()

    if side not in ["over", "under"]:
        raise ValueError("side must be 'over' or 'under'")

    P, R, A = float(points), float(rebounds), float(assists)

    # Weighted effective totals
    if combo_type == "PRA":
        actual_eff = 1.2 * P + 1.0 * R + 0.8 * A
    elif combo_type == "PR":
        actual_eff = 1.1 * P + 0.9 * R
    elif combo_type == "RA":
        actual_eff = 1.05 * R + 0.95 * A
    else:
        # Fallback: straight sum
        actual_eff = P + R + A

    line_eff = float(line)

    # Check win/loss on effective total
    if side == "over" and actual_eff >= line_eff:
        return None
    if side == "under" and actual_eff <= line_eff:
        return None

    if side == "over":
        ratio = actual_eff / line_eff if line_eff > 0 else 0.0
    else:
        ratio = line_eff / actual_eff if actual_eff > 0 else 0.0

    score = 100.0 * (ratio ** alpha)
    return clamp(score)

def score_spread_bet(spread, team_score, opp_score, D=10.0, p=1.2):
    spread = float(spread)
    team_score = int(team_score)
    opp_score = int(opp_score)

    margin = team_score - opp_score
    cover_margin = margin + spread

    # If it covered or pushed, do not score
    if cover_margin >= 0:
        return None

    diff = -cover_margin  # how many points short of covering

    x = min(diff / D, 1.0)
    score = 100.0 * (1.0 - (x ** p))
    return clamp(score)

def score_total_bet(side, total_line, team_score, opp_score, D=14.0, p=1.0):
    side = side.lower()
    if side not in ["over", "under"]:
        raise ValueError("side must be 'over' or 'under'")

    total_line = float(total_line)
    total = int(team_score) + int(opp_score)

    if side == "over":
        if total >= total_line:
            return None
        diff = total_line - total
    else:  # under
        if total <= total_line:
            return None
        diff = total - total_line

    x = min(diff / D, 1.0)
    score = 100.0 * (1.0 - (x ** p))
    return clamp(score)

def score_double_double(points, rebounds, assists):
    P, R, A = float(points), float(rebounds), float(assists)

    # If it actually was a double double, do not score
    cats = sum(1 for s in [P, R, A] if s >= 10.0)
    if cats >= 2:
        return None

    # Scale stats relative to 10 and sort
    s = [min(P / 10.0, 1.0), min(R / 10.0, 1.0), min(A / 10.0, 1.0)]
    s.sort(reverse=True)
    s1, s2, s3 = s

    base = (s1 + s2) / 2.0
    base_score = (base ** 2) * 100.0

    # Hybrid logic:
    # - s2 >= 0.9 : two stats basically at 9+ → very high scores, boosted by the 3rd stat
    # - 0.8 <= s2 < 0.9 : one full, one around 8–9 → mid-range scores
    # - s2 < 0.8 : only one or zero truly live stats → heavy penalty
    if s2 >= 0.9:
        score = base_score + 4.46 * s3 + 3.662
    elif s2 >= 0.8:
        score = 0.65 * base_score + 10.0 * s3
    else:
        score = 0.4 * base_score + 5.0 * s3

    return clamp(score)


def score_triple_double(points, rebounds, assists):
    P, R, A = float(points), float(rebounds), float(assists)

    # If it actually was a triple double, do not score
    if all(s >= 10.0 for s in [P, R, A]):
        return None

    s = [min(P / 10.0, 1.0), min(R / 10.0, 1.0), min(A / 10.0, 1.0)]
    hits = sum(1 for v in s if v >= 1.0)      # stats that actually hit 10+
    nears = sum(1 for v in s if v >= 0.9)     # stats at 9+
    s_sorted = sorted(s, reverse=True)
    s1, s2, s3 = s_sorted

    base = sum(s) / 3.0
    base_score = (base ** 2) * 100.0

    # Hybrid logic for triple doubles:
    # - 2 hits + 3rd >= 0.9 : insane near-miss (e.g. 40-15-9) → ~98+
    # - 0 hits, all ~9      : 9-9-9 type → mid 50s
    # - 1 hit, all ~9       : 12-9-9 type → mid 60s
    # - 2 hits, 3rd middling: I/J/L type → 20s–30s
    # - everything else     : mostly dead → low scores
    if hits >= 2 and s3 >= 0.9:
        # Brutal, near-perfect miss
        score = 0.9 * base_score + 14.0
    elif hits == 0 and nears == 3:
        # 9-9-9 style
        score = 0.68 * base_score
    elif hits == 1 and nears == 3:
        # 12-9-9 style
        score = 0.75 * base_score
    elif hits >= 2:
        # Two stats at 10+, third somewhere between ~0.3–0.6
        score = 1.223137585 * base_score - 51.038
    else:
        # Mostly dead: one or zero stats really alive
        mid = sum(1 for v in s if v >= 0.6)
        if mid >= 2:
            score = 0.5 * base_score - 10.0
        else:
            score = 0.25 * base_score

    return clamp(score)


def comment_on_score(score):
    if score is None:
        return "This bet did not lose. Tool only scores losing bets."
    if score >= 95:
        return "Pure heartbreak. Razor thin miss."
    if score >= 80:
        return "Very close. Right side, bad variance."
    if score >= 60:
        return "Decent read, but not a sweat at the end."
    if score >= 30:
        return "Pretty bad. This one was never really alive."
    if score >= 10:
        return "Ugly. Candidate for pinhead of the night."
    return "Complete disaster. Burn this ticket."

# ---------- STREAMLIT UI ----------

st.title("NBA Bad Bet Scoring App")
st.write("Score how close a **losing** NBA bet came to hitting (0–100).")

bet_type = st.selectbox(
    "Bet type",
    [
        "Single stat over/under",
        "Combo stat (PRA, PR, RA)",
        "Spread bet",
        "Game total",
        "Double double (Yes)",
        "Triple double (Yes)",
    ],
)

score = None

if bet_type == "Single stat over/under":
    side = st.selectbox("Side", ["over", "under"])
    line = st.number_input("Betting line", value=20.5, step=0.5)
    result = st.number_input("Actual stat result", value=15.0, step=0.5)

    if st.button("Score bet"):
        score = score_single_stat_prop(side, line, result)
        if score is None:
            st.info("This bet did not lose. Tool only scores losing bets.")
        else:
            st.markdown(f"## Score: **{score:.1f} / 100**")
            st.write(comment_on_score(score))

elif bet_type == "Combo stat (PRA, PR, RA)":
    side = st.selectbox("Side", ["over", "under"])
    combo_type = st.selectbox("Combo type", ["PRA", "PR", "RA"])
    line = st.number_input("Betting line", value=30.5, step=0.5)

    # Ask only for the stats that actually matter
    if combo_type == "PRA":
        P = st.number_input("Points", value=20.0, step=0.5)
        R = st.number_input("Rebounds", value=5.0, step=0.5)
        A = st.number_input("Assists", value=5.0, step=0.5)
    elif combo_type == "PR":
        P = st.number_input("Points", value=20.0, step=0.5)
        R = st.number_input("Rebounds", value=8.0, step=0.5)
        A = 0.0
    else:  # RA
        P = 0.0
        R = st.number_input("Rebounds", value=8.0, step=0.5)
        A = st.number_input("Assists", value=6.0, step=0.5)

    if st.button("Score bet"):
        score = score_combo_prop(side, combo_type, line, P, R, A)
        if score is None:
            st.info("This bet did not lose. Tool only scores losing bets.")
        else:
            st.markdown(f"## Score: **{score:.1f} / 100**")
            st.write(comment_on_score(score))

elif bet_type == "Spread bet":
    spread = st.number_input("Spread you bet (use sign, e.g. +4.5 or -3.5)", value=4.5, step=0.5)
    team_score = st.number_input("Your team final score", value=100, step=1)
    opp_score = st.number_input("Opponent final score", value=105, step=1)

    if st.button("Score bet"):
        score = score_spread_bet(spread, team_score, opp_score)
        if score is None:
            st.info("This bet did not lose. Tool only scores losing bets.")
        else:
            st.markdown(f"## Score: **{score:.1f} / 100**")
            st.write(comment_on_score(score))

elif bet_type == "Game total":
    side = st.selectbox("Side", ["over", "under"])
    total_line = st.number_input("Total line", value=220.5, step=0.5)
    team_score = st.number_input("Team 1 score", value=110, step=1)
    opp_score = st.number_input("Team 2 score", value=108, step=1)

    if st.button("Score bet"):
        score = score_total_bet(side, total_line, team_score, opp_score)
        if score is None:
            st.info("This bet did not lose. Tool only scores losing bets.")
        else:
            st.markdown(f"## Score: **{score:.1f} / 100**")
            st.write(comment_on_score(score))

elif bet_type == "Double double (Yes)":
    P = st.number_input("Points", value=18.0, step=0.5)
    R = st.number_input("Rebounds", value=9.0, step=0.5)
    A = st.number_input("Assists", value=2.0, step=0.5)

    if st.button("Score bet"):
        score = score_double_double(P, R, A)
        if score is None:
            st.info("This was actually a double double. Tool only scores losing bets.")
        else:
            st.markdown(f"## Score: **{score:.1f} / 100**")
            st.write(comment_on_score(score))

elif bet_type == "Triple double (Yes)":
    P = st.number_input("Points", value=20.0, step=0.5)
    R = st.number_input("Rebounds", value=9.0, step=0.5)
    A = st.number_input("Assists", value=9.0, step=0.5)

    if st.button("Score bet"):
        score = score_triple_double(P, R, A)
        if score is None:
            st.info("This was actually a triple double. Tool only scores losing bets.")
            st.write(comment_on_score(score))
        else:
            st.markdown(f"## Score: **{score:.1f} / 100**")
            st.write(comment_on_score(score))
