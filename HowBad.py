import math

def clamp(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, x))

# 1. Single stat props: points, rebounds, assists, 3PM, blocks, steals
def score_single_stat_prop(side, line, result, alpha=2.0):
    """
    side: 'over' or 'under'
    line: float, betting line (e.g. 20.5)
    result: float, actual stat
    returns: score 0 to 100 for a LOSING bet
    """
    side = side.lower()
    if side not in ["over", "under"]:
        raise ValueError("side must be 'over' or 'under'")

    # Check if it even lost
    if side == "over" and result >= line:
        print("This bet actually won or pushed. No score needed.")
        return None
    if side == "under" and result <= line:
        print("This bet actually won or pushed. No score needed.")
        return None

    if side == "over":  # lost because result < line
        ratio = result / line if line > 0 else 0.0
    else:               # under lost because result > line
        ratio = line / result if result > 0 else 0.0

    score = 100.0 * (ratio ** alpha)
    return clamp(score)


# 2. Combo stats props: PRA, PR, RA
def score_combo_prop(side, combo_type, line, points, rebounds, assists, alpha=2.0):
    """
    combo_type: 'PRA', 'PR', 'RA'
    We weight points slightly more than other stats.
    """
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
        # Fallback. Treat as simple PRA
        actual_eff = P + R + A

    line_eff = float(line)

    # Determine win or loss using the effective total
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


# 3. Spread bets
def score_spread_bet(spread, team_score, opp_score, D=10.0, p=1.2):
    """
    spread: what you bet, positive for +points, negative for -points
    team_score: your team's final points
    opp_score: opponent's final points

    Uses how many points you were off the spread.
    """
    spread = float(spread)
    team_score = int(team_score)
    opp_score = int(opp_score)

    margin = team_score - opp_score          # positive if your team won
    cover_margin = margin + spread          # how many points above spread

    if cover_margin >= 0:
        print("This spread bet did not lose. No score needed.")
        return None

    diff = -cover_margin   # how many points you fell short by

    x = min(diff / D, 1.0)
    score = 100.0 * (1.0 - (x ** p))
    return clamp(score)


# 4. Game total bets
def score_total_bet(side, total_line, team_score, opp_score, D=14.0, p=1.0):
    """
    side: 'over' or 'under'
    total_line: line like 220.5
    team_score, opp_score: final points
    """
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
    else:  # under
        if total <= total_line:
            print("This total bet did not lose. No score needed.")
            return None
        diff = total - total_line

    x = min(diff / D, 1.0)
    score = 100.0 * (1.0 - (x ** p))
    return clamp(score)


# 5. Double double
def score_double_double(points, rebounds, assists):
    """
    Assume bet was 'Yes double double' and it lost.
    """
    P, R, A = float(points), float(rebounds), float(assists)

    # Check if it actually hit
    cats = sum(1 for s in [P, R, A] if s >= 10.0)
    if cats >= 2:
        print("This was actually a double double. No score needed.")
        return None

    # Fractions of goal in each category
    s = [min(P / 10.0, 1.0), min(R / 10.0, 1.0), min(A / 10.0, 1.0)]
    s.sort(reverse=True)
    s1, s2, s3 = s

    base = (s1 + s2) / 2.0
    bonus = 0.1 * s3  # reward having the third category somewhat live

    raw = 100.0 * (base ** 2 + bonus)
    return clamp(raw)


# 6. Triple double
def score_triple_double(points, rebounds, assists):
    """
    Assume bet was 'Yes triple double' and it lost.
    """
    P, R, A = float(points), float(rebounds), float(assists)

    if all(s >= 10.0 for s in [P, R, A]):
        print("This was actually a triple double. No score needed.")
        return None

    s = [min(P / 10.0, 1.0), min(R / 10.0, 1.0), min(A / 10.0, 1.0)]
    base = sum(s) / 3.0
    raw = 100.0 * (base ** 2)
    return clamp(raw)


def print_menu():
    print("\nNBA Bad Bet Scorer")
    print("Choose bet type:")
    print("1. Single stat over or under (points, rebounds, assists, 3PM, blocks, steals)")
    print("2. Combo stat over or under (PRA, PR, RA)")
    print("3. Spread bet")
    print("4. Game total over or under")
    print("5. Double double (Yes) that lost")
    print("6. Triple double (Yes) that lost")
    print("0. Quit")


def main():
    while True:
        print_menu()
        choice = input("Enter choice number: ").strip()

        if choice == "0":
            print("Good luck on the next card.")
            break

        elif choice == "1":
            side = input("Over or Under? ").strip().lower()
            line = float(input("Betting line (e.g. 20.5): ").strip())
            result = float(input("Actual stat result: ").strip())
            score = score_single_stat_prop(side, line, result)
            if score is not None:
                print(f"\nScore: {score:.1f} out of 100.")
                print("Comment:", comment_on_score(score))

        elif choice == "2":
            side = input("Over or Under? ").strip().lower()
            combo_type = input("Combo type (PRA, PR, RA): ").strip()
            line = float(input("Betting line (e.g. 31.5): ").strip())
            points = float(input("Points: ").strip())
            rebounds = float(input("Rebounds: ").strip())
            assists = float(input("Assists: ").strip())
            score = score_combo_prop(side, combo_type, line, points, rebounds, assists)
            if score is not None:
                print(f"\nScore: {score:.1f} out of 100.")
                print("Comment:", comment_on_score(score))

        elif choice == "3":
            spread = float(input("Spread you bet (use sign, e.g. +4.5 or -3.5): ").strip())
            team_score = int(input("Your team final score: ").strip())
            opp_score = int(input("Opponent final score: ").strip())
            score = score_spread_bet(spread, team_score, opp_score)
            if score is not None:
                print(f"\nScore: {score:.1f} out of 100.")
                print("Comment:", comment_on_score(score))

        elif choice == "4":
            side = input("Over or Under? ").strip().lower()
            total_line = float(input("Total line (e.g. 220.5): ").strip())
            team_score = int(input("Home or chosen team score: ").strip())
            opp_score = int(input("Opponent score: ").strip())
            score = score_total_bet(side, total_line, team_score, opp_score)
            if score is not None:
                print(f"\nScore: {score:.1f} out of 100.")
                print("Comment:", comment_on_score(score))

        elif choice == "5":
            points = float(input("Points: ").strip())
            rebounds = float(input("Rebounds: ").strip())
            assists = float(input("Assists: ").strip())
            score = score_double_double(points, rebounds, assists)
            if score is not None:
                print(f"\nScore: {score:.1f} out of 100.")
                print("Comment:", comment_on_score(score))

        elif choice == "6":
            points = float(input("Points: ").strip())
            rebounds = float(input("Rebounds: ").strip())
            assists = float(input("Assists: ").strip())
            score = score_triple_double(points, rebounds, assists)
            if score is not None:
                print(f"\nScore: {score:.1f} out of 100.")
                print("Comment:", comment_on_score(score))

        else:
            print("Invalid choice. Try again.")


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

if __name__ == "__main__":
    main()
