# **NBA Bad Bet Scoring App**

A Python tool that scores **how close a losing NBA bet came to winning** using a 0 to 100 scale.

* **100** = heartbreak miss
* **0** = bet was never alive
* Only losing bets get scored
* Supports stat props, combo props, spreads, totals, double-doubles, and triple-doubles

---

## **How to Run**

### Requirements

* Python 3.8+

### Run the app

```bash
python3 app.py
```

Follow the menu and input the stats when asked.
The app prints a score (0–100) and a short comment.

---

## **Scoring Philosophy**

The score reflects **closeness**, not judgment.

The system calculates how far the bet was from hitting, converts that into a “closeness ratio,” and applies a curved drop-off:

* Small misses → stay near 100
* Medium misses → fall into the middle
* Large misses → collapse toward 0

This matches real betting intuition:

* Hook losses live in the 90s
* Multi-possession misses land in the middle
* Blowouts drop near zero

Double-double and triple-double bets use stat-to-goal percentages
(points, rebounds, assists compared to 10).

Injuries are **not** adjusted for.
If the bet lost, it gets scored.

---

## **Features**

* Single-stat props (PTS, REB, AST, 3PM, BLK, STL)
* PRA / PR / RA with weighting (points count more)
* Spread bets
* Game totals
* Double-double scoring
* Triple-double scoring
* Curved scoring so bad misses get punished harder

---

## **Full Code (app.py)**

```python
import math

def clamp(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, x))


# -----------------------------
# SINGLE STAT PROPS
# -----------------------------
def score_single_stat_prop(side, line, result, alpha=2.0):
    side = side.lower()
    if side not in ["over", "under"]:
        raise ValueError("side must be 'over' or 'under'")

    if side == "over" and result >= line:
        print("This bet actually won or pushed. No score needed.")
        return None
    if side == "under" and result <= line:
        print("This bet actually won or pushed. No score needed.")
        return None

    if side == "over":  
        ratio = result / line if line > 0 else 0.0
    else:               
        ratio = line / result if result > 0 else 0.0

    score = 100.0 * (ratio ** alpha)
    return clamp(score)


# -----------------------------
# COMBO PROPS (PRA, PR, RA)
# -----------------------------
def score_combo_prop(side, combo_type, line, points, rebounds, assists, alpha=2.0):
    side = side.lower()
    combo_type = combo_type.upper()

    if side not in ["over", "under"]:
        raise ValueError("side must be 'over' or 'under'")

    P, R, A = float(points), float(rebounds), float(assists)

    if combo_type == "PRA":
        actual_eff = 1.2 * P + 1.0 * R + 0.8 * A
    elif combo_type == "PR":
        actual_eff = 1.1 * P + 0.9 * R
    elif combo_type == "RA":
        actual_eff = 1.05 * R + 0.95 * A
    else:
        actual_eff = P + R + A

    line_eff = float(line)

    if side == "over" and actual_eff >= line_eff:
        print("This bet actually won or pushed. No score needed.")
        return None
    if side == "under" and actual_eff <= line_eff:
        print("This bet actually won or pushed. No score needed.")
        return None

    if side == "over":
        ratio = actual_eff / line_eff if line_eff > 0 else 0.0
    else:
        ratio = line_eff / actual_eff if actual_eff > 0 else 0.0

    score = 100.0 * (ratio ** alpha)
    return clamp(score)


# -----------------------------
# SPREAD BETS
# -----------------------------
def score_spread_bet(spread, team_score, opp_score, D=10.0, p=1.2):
    spread = float(spread)
    team_score = int(team_score)
    opp_score = int(opp_score)

    margin = team_score - opp_score          
    cover_margin = margin + spread           

    if cover_margin >= 0:
        print("This spread bet did not lose. No score needed.")
        return None

    diff = -cover_margin   

    x = min(diff / D, 1.0)
    score = 100.0 * (1.0 - (x ** p))
    return clamp(score)


# -----------------------------
# TOTALS BETS
# -----------------------------
def score_total_bet(side, total_line, team_score, opp_score, D=14.0, p=1.0):
    side = side.lower()
    if side not in ["over", "under"]:
        raise ValueError("side must be 'over' or 'under'")

    total_line = float(total_line)
    total = int(team_score) + int(opp_score)

    if side == "over":
        if total >= total_line:
            print("This total bet did not lose. No score needed.")
            return None
        diff = total_line - total
    else:
        if total <= total_line:
            print("This total bet did not lose. No score needed.")
            return None
        diff = total - total_line

    x = min(diff / D, 1.0)
    score = 100.0 * (1.0 - (x ** p))
    return clamp(score)


# -----------------------------
# DOUBLE DOUBLE
# -----------------------------
def score_double_double(points, rebounds, assists):
    P, R, A = float(points), float(rebounds), float(assists)

    cats = sum(1 for s in [P, R, A] if s >= 10.0)
    if cats >= 2:
        print("This was actually a double double. No score needed.")
        return None

    s = [min(P / 10.0, 1.0), min(R / 10.0, 1.0), min(A / 10.0, 1.0)]
    s.sort(reverse=True)
    s1, s2, s3 = s

    base = (s1 + s2) / 2.0
    bonus = 0.1 * s3

    raw = 100.0 * (base ** 2 + bonus)
    return clamp(raw)


# -----------------------------
# TRIPLE DOUBLE
# -----------------------------
def score_triple_double(points, rebounds, assists):
    P, R, A = float(points), float(rebounds), float(assists)

    if all(s >= 10.0 for s in [P, R, A]):
        print("This was actually a triple double. No score needed.")
        return None

    s = [min(P / 10.0, 1.0), min(R / 10.0, 1.0), min(A / 10.0, 1.0)]
    base = sum(s) / 3.0
    raw = 100.0 * (base ** 2)
    return clamp(raw)


# -----------------------------
# MENU + MAIN
# -----------------------------
def print_menu():
    print("\nNBA Bad Bet Scorer")
    print("Choose bet type:")
    print("1. Single stat over/under")
    print("2. Combo stat (PRA, PR, RA)")
    print("3. Spread bet")
    print("4. Game total")
    print("5. Double double")
    print("6. Triple double")
    print("0. Quit")


def comment_on_score(score):
    if score >= 95:
        return "Pure heartbreak. This was a razor thin miss."
    if score >= 80:
        return "Very close. Right side, bad variance."
    if score >= 60:
        return "Decent read, but not a sweat at the end."
    if score >= 30:
        return "Pretty bad. This one was never really alive."
    if score >= 10:
        return "Ugly. Candidate for pinhead of the night."
    return "Complete disaster. Burn this ticket."


def main():
    while True:
        print_menu()
        choice = input("Enter choice number: ").strip()

        if choice == "0":
            print("Good luck on the next card.")
            break

        elif choice == "1":
            side = input("Over or Under? ").strip().lower()
            line = float(input("Betting line: ").strip())
            result = float(input("Actual stat result: ").strip())
            score = score_single_stat_prop(side, line, result)
            if score is not None:
                print(f"\nScore: {score:.1f}")
                print("Comment:", comment_on_score(score))

        elif choice == "2":
            side = input("Over or Under? ").strip().lower()
            combo_type = input("Combo type (PRA, PR, RA): ").strip()
            line = float(input("Betting line: ").strip())
            points = float(input("Points: ").strip())
            rebounds = float(input("Rebounds: ").strip())
            assists = float(input("Assists: ").strip())
            score = score_combo_prop(side, combo_type, line, points, rebounds, assists)
            if score is not None:
                print(f"\nScore: {score:.1f}")
                print("Comment:", comment_on_score(score))

        elif choice == "3":
            spread = float(input("Spread (+/-): ").strip())
            team_score = int(input("Your team score: ").strip())
            opp_score = int(input("Opponent score: ").strip())
            score = score_spread_bet(spread, team_score, opp_score)
            if score is not None:
                print(f"\nScore: {score:.1f}")
                print("Comment:", comment_on_score(score))

        elif choice == "4":
            side = input("Over or Under? ").strip().lower()
            total_line = float(input("Total line: ").strip())
            team_score = int(input("Team score: ").strip())
            opp_score = int(input("Opponent score: ").strip())
            score = score_total_bet(side, total_line, team_score, opp_score)
            if score is not None:
                print(f"\nScore: {score:.1f}")
                print("Comment:", comment_on_score(score))

        elif choice == "5":
            points = float(input("Points: ").strip())
            rebounds = float(input("Rebounds: ").strip())
            assists = float(input("Assists: ").strip())
            score = score_double_double(points, rebounds, assists)
            if score is not None:
                print(f"\nScore: {score:.1f}")
                print("Comment:", comment_on_score(score))

        elif choice == "6":
            points = float(input("Points: ").strip())
            rebounds = float(input("Rebounds: ").strip())
            assists = float(input("Assists: ").strip())
            score = score_triple_double(points, rebounds, assists)
            if score is not None:
                print(f"\nScore: {score:.1f}")
                print("Comment:", comment_on_score(score))

        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
```

---


