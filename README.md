````markdown
# NBA Bad Bet Scoring App

A Streamlit app that scores **how close a losing NBA bet came to winning** on a scale from **0 to 100**.

- **100** = about as close as a loss can get  
- **0** = never really had a chance  
- Only **losing bets** are scored (wins and pushes return a message instead of a number)

The goal is not to judge if the bet was “smart,” but to measure how tightly it lined up with the final result.

---

## Supported Bet Types

### Single stat overs/unders
- Points  
- Rebounds  
- Assists  
- Threes made  
- Blocks  
- Steals  

### Combo props
With extra weight on points (where relevant):

- **PRA** (Points + Rebounds + Assists)  
- **PR**  (Points + Rebounds)  
- **RA**  (Rebounds + Assists)  

For RA, points are **not** used at all.

### Team spreads
Standard spreads such as `+4.5` or `-3.5`, scored based on how many points away the final margin was from covering.

### Game totals
Full game over/under totals such as `O/U 220.5`, scored by how far the combined score was from the line.

### Multi-path stat milestones
- **Double-double (Yes)**  
- **Triple-double (Yes)**  

These look at how close each relevant stat category was to the target of 10.

---

## How It Feels In Practice

- A loss that misses the line by **a very small amount** will usually score in the **90s**.  
- A loss that was **somewhat close** but not down to the final possession or basket will land in the **middle range**.  
- A loss where the result was **nowhere near** the target will drop toward **zero**.  
- Double-double / triple-double bets get higher scores when **multiple categories** were close to 10, not just one.

If the bet actually **won or pushed**, the app does not assign a score and instead shows:

> This bet did not lose. Tool only scores losing bets.

---

## Running The App

### 1. Install requirements

```bash
pip install streamlit
````

(or add `streamlit` to your existing environment)

### 2. Save the app

Save your Streamlit code as `streamlit_app.py` in your project.

### 3. Run locally

```bash
streamlit run streamlit_app.py
```

This will open a browser window (or give you a local URL) where you can:

1. Choose the bet type from a dropdown
2. Enter the bet line and actual stats
3. Click **“Score bet”** to get:

   * A score from **0 to 100**, and
   * A short comment describing how close it was

---

## Example Flow

1. Select **“Single stat over/under”**
2. Side: `under`
3. Line: `20.5`
4. Actual stat: `27`
5. Click **Score bet**

You might see something like:

> Score: 42.7 / 100
>
> Comment: Pretty bad. This one was never really alive.

---

## Comments On Scores

The app maps scores to simple text labels:

* **95–100** → “Pure heartbreak. Razor thin miss.”
* **80–94**  → “Very close. Right side, bad variance.”
* **60–79**  → “Decent read, but not a sweat at the end.”
* **30–59**  → “Pretty bad. This one was never really alive.”
* **10–29**  → “Ugly. Candidate for pinhead of the night.”
* **0–9**    → “Complete disaster. Burn this ticket.”

You can tweak these ranges or phrases in `comment_on_score()` if you want a different tone.

---

## Advanced: How The Scoring Works

This section explains the logic behind the 0–100 scores.
You do not need this to use the app, but it helps if you want to tune it.

### 1. Core Idea

Every bet is converted into a **closeness value** between **0 and 1**, and then transformed into a score:

[
\text{score} = 100 \times f(\text{closeness})
]

* Closeness near **1** → score near **100**
* Closeness near **0** → score near **0**

The functions are curved so that:

* Tiny misses keep you very close to 100
* Medium misses drop more noticeably
* Big misses fall off hard toward 0

---

### 2. Single Stat Props

For single stats (points, rebounds, assists, etc.), we compare the **line** ( L ) and the **result** ( R ).

* For an **over** bet that lost, we know ( R < L ).
  We define:
  [
  \text{ratio} = \frac{R}{L}
  ]

* For an **under** bet that lost, we know ( R > L ).
  We define:
  [
  \text{ratio} = \frac{L}{R}
  ]

In both cases, `ratio` is between 0 and 1 for a losing bet.

The score uses a curved relationship:

[
\text{score} = 100 \times (\text{ratio})^{\alpha}
]

In the code, (\alpha = 2), which means:

* Small misses (ratio close to 1) keep the score high
* Larger misses (ratio small) get punished more than linearly

You can make the curve harsher or softer by adjusting `alpha`.

---

### 3. Combo Props (PRA, PR, RA)

Combo props build a **weighted effective total** before applying the same ratio logic:

* **PRA**:
  [
  \text{effective} = 1.2P + 1.0R + 0.8A
  ]
* **PR**:
  [
  \text{effective} = 1.1P + 0.9R
  ]
* **RA**:
  [
  \text{effective} = 1.05R + 0.95A
  ]

P, R, A are the player’s points, rebounds, and assists.

Then:

* For losing **overs**:
  [
  \text{ratio} = \frac{\text{effective}}{\text{line}}
  ]
* For losing **unders**:
  [
  \text{ratio} = \frac{\text{line}}{\text{effective}}
  ]

and again:

[
\text{score} = 100 \times (\text{ratio})^2
]

This keeps the behavior consistent with single-stat props, but lets you favor points slightly more where it makes sense.

---

### 4. Spreads

For spreads, the app focuses on how many points away you were from covering.

* Let ( S ) be the spread you bet (positive for +, negative for -).
* Let ( T ) be your team’s score and ( O ) be the opponent’s score.

Margin of the game:

[
\text{margin} = T - O
]

Adjusted margin against the spread:

[
\text{cover_margin} = \text{margin} + S
]

If `cover_margin >= 0`, the bet did not lose, so the tool returns no score.

If it **did** lose, then:

[
\text{diff} = -\text{cover_margin}
]

represents how many points short of covering you were.

That diff is normalized with a scale ( D ) (in the code, ( D = 10 )):

[
x = \min\left( \frac{\text{diff}}{D}, 1 \right)
]

Then the score is:

[
\text{score} = 100 \times \bigl(1 - x^p\bigr)
]

with ( p = 1.2 ) in the code.
This means:

* Very small `diff` (close loss) → `x` small → score near 100
* Moderate `diff` → score in the middle
* Large `diff` → `x` pushed toward 1 → score near 0

You can tune `D` and `p` to change how harshly spread misses are treated.

---

### 5. Game Totals

Game totals use similar logic but with a simpler power:

* Total score:
  [
  \text{total} = T + O
  ]
* For losing overs:
  [
  \text{diff} = \text{line} - \text{total}
  ]
* For losing unders:
  [
  \text{diff} = \text{total} - \text{line}
  ]

Normalize with a scale ( D = 14 ):

[
x = \min\left( \frac{\text{diff}}{14}, 1 \right)
]

Score:

[
\text{score} = 100 \times (1 - x^p)
]

with ( p = 1.0 ), making totals a bit more linear and less aggressive than spreads.

---

### 6. Double-Double

For double-double bets, the app looks at how close each stat was to 10.

Let:

[
s_P = \min(P / 10, 1),\quad
s_R = \min(R / 10, 1),\quad
s_A = \min(A / 10, 1)
]

Sort these three values in descending order and call them ( s_1, s_2, s_3 ).

The app builds:

[
\text{base} = (s_1 + s_2)/2
]
[
\text{score} = 100 \times \bigl( \text{base}^2 + 0.1 \times s_3 \bigr)
]

So:

* If two categories are very close to 10, `base` is high and squaring it pushes the score into the high range.
* If only one category is close and the others are far, `base` is much smaller and the score falls into the middle or low range.
* The third stat contributes a small bonus via `0.1 * s3`.

If at least two stats are already ≥ 10, it is a true double-double and the tool returns no score.

---

### 7. Triple-Double

Triple-double bets work similarly but with all three stats contributing equally.

Using the same scaled values ( s_P, s_R, s_A ):

[
\text{base} = (s_P + s_R + s_A) / 3
]
[
\text{score} = 100 \times \text{base}^2
]

If points, rebounds, and assists are all near 10, `base` is high and the score climbs into the very high range. If only one category is near 10 and the others are far away, `base` is low and the score stays low.

Again, if all three stats are already ≥ 10, the tool returns no score because the bet actually hit.

---

```
```
