# Breitstein test 2: "boring stock, violent move"

_2026-09-19 · `run_boring_violent.py` · log `logs/boring_violent_2026-09-19.log` · summary
`boring_violent_summary_2026-09-19.csv` · source `ubofAZwgd4w` [06:15] · refines
`data/studies/crash_leader_reversion_study.md`_

## Verdict

**Fails, and in the direction opposite to the claim.** Normalising a one-day selloff by the name's
own ADR and requiring the name to be "boring" (bottom-tercile ADR) makes the reversion *smaller*,
not larger. The un-normalised raw ≥15% drop reverts far more, and that reversion is driven by the
high-ADR names he says to avoid and by the weak-tape regime the crash-leader study already found.
In a healthy tape (SPY above its 21 EMA) every cell underperforms SPY at 5, 20 and 60 sessions.
Both ledger rows `passed = False`.

## What was run

Liquid panel, 1,743 names, signals 2019-10 → 2026-09, long at next open, 10 bps each side.

| cell | definition | n |
|---|---|---|
| A (his claim) | 1-day drop ≥ 4× own trailing-20 ADR AND prior ADR in the universe's bottom tercile (cut ≈ 2.2%) | 896 |
| A sweeps | same at 3× / 5× | 2,208 / 440 |
| B (A/B leg) | drop ≥ 4× own ADR, any ADR | 2,168 |
| C (un-normalised) | raw 1-day drop ≥ 15% | 2,273 |
| CB | raw ≥ 15% AND boring | 148 |

Harness arms (hold 5, stop = signal-bar low, same-name random control same month) for the ledger;
5/20/60-session forward return in % vs the same control and vs SPY for the claim itself; splits by
SPY > 21 EMA and by breadth (% of eligible names above their 200sma); earnings ±1 session for the
126 covered names.

## Results

**Harness (hold 5, R units).** Every arm of every cell is negative: A(4×) best arm `ema20` −0.16,
`t1R` −0.60, t −3.5 to −6.8; halves −0.01 / −0.24. The stop at the signal-bar low is tagged 57–69%
of the time (median 1-day drop −9.7%, low sits next to the close; 30% of signals were dropped by the
harness's 0.5% minimum-risk filter). The "edge vs control" of +0.2 to +0.5R only says the control
is worse still (−0.6 to −0.9R): a random session in the same name and month is inside the same
downtrend. Not tradeable on any arm.

**Forward returns (%), signal mean / vs same-name control / vs SPY:**

| cell | 5d | 20d | 60d | 60d win |
|---|---|---|---|---|
| A boring+violent 4× | −1.55 / +0.3 / −1.2 | +0.44 / +4.2 / −1.6 | +3.2 / +4.4 / −3.7 | 59% |
| A 3× | −1.29 / +0.2 / – | +0.72 / +3.7 / – | +4.4 / +4.4 / – | – |
| A 5× | −1.40 / +0.5 / – | +0.09 / +5.2 / – | +2.2 / +5.2 / – | – |
| B violent, any ADR 4× | −1.56 / +0.9 / – | +0.65 / +6.0 / – | +5.1 / +6.6 / – | – |
| C raw ≥15% | +0.35 / +4.1 / +1.6 | **+7.1** / +11.1 / +2.7 | **+23.3** / +14.5 / +12.6 | 66% |
| CB raw ≥15% + boring | −3.14 / −0.6 / – | +9.4 / +10.2 / – | +18.9 / +10.9 / – | – |

(t on the daily-clustered signal mean: A 60d 0.9; C 20d 2.6, 60d 5.1.)

- **The boring leg subtracts.** B > A at 20d and 60d at the same k; CB < C.
- **Normalising subtracts.** C (raw 15%) reverts 5–7× more than A; the median 1-day drop in A is
  −9.7%, in C ≥ −15% by construction — the reversion scales with the *absolute* shock, and the
  absolute shock is largest in the high-ADR names his rule excludes.
- A is **below SPY at every horizon**, in every k.

**Tape split (the crash-leader veto):**

| cell | tape | n | 20d | 60d | 60d win | 60d vs SPY |
|---|---|---|---|---|---|---|
| A 4× | SPY < 21 EMA | 416 | +1.6 | +7.4 | 70% | −4.5 |
| A 4× | SPY > 21 EMA | 480 | −0.5 | **−0.4** | 50% | −2.9 |
| C raw 15% | SPY < 21 EMA | 1,308 | +12.4 | **+38.1** | 79% | +22.0 |
| C raw 15% | SPY > 21 EMA | 965 | −0.05 | +2.0 | 48% | −1.1 |

Breadth split gives the same picture. The entire reversion in C is the weak-tape regime; in a
healthy tape the raw-drop cell has a −2.8% median at 60d. The crash-leader conclusion replicates
in one-day form: **buying a violent selloff is a regime bet, not selection**, and the veto (never
in a healthy tape) stands. A bounces with the index in a weak tape but by less than the index.

**Earnings (126 covered names, 462 signals, k=3):** near-earnings signals were *less* bad at 5d
(−0.4 vs −3.6) and 20d, and worse at 60d (+1.7 vs +7.0). No clean support for the no-news
preference; coverage too thin to say more.

## Reading

His mechanism ("a sleepy name that drops 15% is way more likely to be an overreaction") does not
survive on daily bars 2019–2026. Two reasons visible in the data: the boring names' shocks are
smaller in absolute terms and revert less, and the outsized reversion that does exist belongs to
the weak-tape regime, where everything reverts. What he may be seeing intraday (a −12%-in-two-hours
utility into support with climactic tape) is not identifiable from the daily bar, and the
timeframe-agnostic rule applies: a daily-bar null is not a refutation of the intraday claim. But
the daily-bar version, which is the one we could trade, is dead.

Nothing changes in the repo. The crash-leader veto stands; `project_crash_leader_study` gains the
note that normalising the shock by own ADR inverts rather than sharpens the result.
