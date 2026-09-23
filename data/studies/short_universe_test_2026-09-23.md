# Is there a SHORT-selectable universe? (2026-09-23) — **NO, not on survivors**

**Verdict: NULL for outright shorts. 0 of 10 cells pass.** Pre-registered in `run_short_universe_test.py`
before the first run. Cells: `short_universe_test_2026-09-23.csv`.

The gating question for the whole short effort, asked before any setup work: *is there a population whose
forward returns are bad enough to be worth being short?* If not, the rest is not worth funding.

## Method

Q1 of the universe test, inverted. Five short-candidate universes on the liquid panel 2020-01 → 2026-09,
all with a $100M ADDV floor (a short needs borrow and an exit). Per non-overlapping date, members' mean
forward return vs an **ADR-matched** benchmark — the panel reweighted to the members' own ADR-decile mix,
so an arm cannot win by holding wilder names. Month-clustered t; halves split 2023-01-01.

⚠ **A short is not a long with the sign flipped.** Beating the panel is enough for a long; a short must
also overcome the market's drift, borrow and financing. So the pass bar required **both** a negative
ADR-matched excess **and** a negative *absolute* return.

## Result — 20-day horizon

| arm | names/day | ADR | **absolute** | ADR-matched excess | t | halves |
|---|---|---|---|---|---|---|
| **CRASH-H** (crash-leader veto inverted) | 30 | 4.9% | **+1.12%** | **−0.96pp** | −1.28 | −2.47 / −0.08 |
| LAGGARD (≥30% off the high) | 65 | 4.3% | +0.77% | −0.57pp | −1.30 | −1.05 / −0.23 |
| INV-TT (Trend Template inverted) | 48 | 3.3% | +0.69% | −0.48pp | −1.49 | −0.58 / −0.42 |
| DIST (below 200 SMA, RS ≤ 20) | 105 | 3.3% | +1.21% | −0.40pp | −1.26 | −0.61 / −0.24 |
| DOWN (EMA stack inverted) | 150 | 3.0% | +1.06% | −0.14pp | −0.64 | −0.06 / −0.22 |

5-day horizon: same ordering, same signs, everything smaller (excess −0.14pp to −0.04pp).

**10 of 10 cells have negative ADR-matched excess. 0 of 10 have a negative absolute return.**

⟹ **Weak names do underperform — and they still drift up.** The best arm gives up about a point of
relative performance per 20 sessions while gaining a point outright. You cannot short that.

## What this does and does not establish

* **Settled:** there is no short-selectable universe among surviving liquid names. Do not fund outright
  single-name directional shorts on the strength of a universe screen. This is consistent with every
  short setup already tested — bouncy ball, counter-trend, pullback-short and the capitulation scorecard
  all failed, and this says the *population* they were drawing from was never shortable to begin with.
* ⚠ **Not established: that no short edge exists.** Survivorship cuts the wrong way here and harder than
  it does for longs — the panel is today's liquid names, so anything delisted, acquired or taken to zero
  is absent, and that is precisely a short's best outcome. Read this as *not proven on survivors*.
* ⚠ **The 10-of-10 consistency is weaker than it looks.** The arms overlap heavily (DOWN 150 names, DIST
  105, INV-TT 48 — largely nested), so this is closer to one observation than ten. No binomial argument.

## ⭐ The one thing worth carrying forward

A consistently **negative excess** paired with a **positive absolute** return is the signature of a
**relative-value** trade, not an outright short: short-weak against long-strong (or against the index)
would harvest the spread without fighting the drift. ⚠ But the excess itself does not certify — the best
t is −1.49 against a bar of 3.0 — so this is a direction to look, not a result.

Note that **CRASH-H is the strongest arm**, and it conditions on a *healthy* tape. That is the
crash-leader veto seen from the other side: deep drawdowns in a healthy tape are the worst relative
performers, which is exactly why the long-side veto was confirmed. The inversion is directionally right
and still not tradeable outright.

## Where the short effort should go instead

The book's only confirmed positives are **index options × dealer gamma**, and the strongest single cell in
the entire ledger is already a short: **SPY 1-day short straddle on positive-gamma days, t 5.6** (with the
2× fly at 3.4 and the put spread at 3.5). Shorts work here when they are **short volatility conditioned on
dealer gamma**, not short direction. That is where to spend the time.
