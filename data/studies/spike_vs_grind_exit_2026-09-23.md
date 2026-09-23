# Tito's spike branch vs the 20-EMA trail, on real call prints (2026-09-23)

**Verdict: NULL on the pre-registered primary. PARKED for the cumulative variant. YIELD: REFRAME.**
Pre-registered in `run_spike_vs_grind_exit.py` before Stage 1 (the chain pull) landed.
Trades: `spike_vs_grind_exit_2026-09-23.csv`.

## The claim

`tito_selection_playbook.md` L231: his exit is **conditional**, not one rule — *grind up → trail the 20 EMA
on a daily close; spike → sell into strength* — and the trail **fails** on spike trades. His own numbers:
on ARM he took **+1966%** selling the spike where the 20-EMA trail returned **+578%**, "held to expiry,
gave back the 2/12 spike." Stated mechanism: a short-dated option that spikes gives back the spike **plus
theta** long before a daily close confirms a trend break.

**Why this and not another selection test.** Four independent angles now say mechanical selection cannot
improve the breakout book (within-date ranking t −0.11, the universe test, the Trend-Template ablation,
the precision-tier freeze-forward). The pool's own shape says the money is in the TAIL: 30% win, median
−1.05R, top 1% carrying 26% of gross. For that distribution tail management is first-order. **Every prior
exit test here used the trail unconditionally; the branch had never been tested**, and it is the one part
of his system the four selection nulls never touched.

⚠ It is also **not a loser-cutting rule**. Our exit ledger is 0-for-many, but every rule killed there
conditions on P&L. The 21-DTE rule certified the same day (t +4.26) precisely because it removes exposure
at a fixed, P&L-independent event. A spike rule conditions on a **move**.

## Method

| | |
|---|---|
| Pool | archetype-A breakouts, **generic pool not the precision tier** (the tier does not select, and the pool supplies the n Tito's rarity never will), top-200 names |
| Sample | **3,428 call trades · 197 names · 2019-06-25 → 2026-02-20** |
| Vehicle | his documented one: on the signal **close**, buy the call nearest **0.275Δ** within [0.20, 0.35], DTE nearest 35 within [15, 75]. Realised: median delta 0.275, median DTE 36 |
| Fills | **REAL — buy the ASK, sell the BID**, plus commission. Never mid |
| ARM A | 20-EMA trail: exit on the first daily close of the underlying below its 20 EMA |
| ARM B | conditional: exit on the first spike ≥ K × ADR, else the ARM A trail — whichever comes first |
| ARM C | spike only; if no spike ever comes, hold to option expiry |
| Backstop | option expiry or 60 sessions. **Paired** — all arms are the same trades |

Data: Athena `options_daily_v3` (44.2M call-days pulled; `options_cache` was unusable — 49 tickers, almost
all ETFs). Test window ends ~2026-03 at the v3 bid/ask coverage cliff.

## Primary — FAILS

**Spike = single-day move ≥ 2.0 ADR.** ARM B minus ARM A, paired, month-clustered:

**+1.2pp, t +0.18, halves +2.9 / −1.8 → PRE-REGISTERED PASS: NO.**

## But look at the distribution — it is a RISK rule, not a return rule

| | A (trail) | B (spike override) | C (spike only) |
|---|---:|---:|---:|
| mean | −23.4% | −22.3% | **−19.8%** |
| win % | 14.6 | **19.3** | **22.8** |
| median | −85.4% | −84.0% | −95.2% |
| sd | 201pp | **158pp** | 166pp |
| **p99** | **+834%** | +671% | +675% |

The spike rule raises the win rate, cuts variance by a quarter — **and caps the right tail from +834% to
+671%.** That is the whole story: it trades tail for consistency. ⭐ This was the **pre-registered prior**
(~35% that B beats A on the mean, "the mechanically likely outcome is that B raises win rate and median
while LOWERING the mean, a risk claim rather than a return claim") and it is what happened.

## ⭐ The sweep — the operative variable is CUMULATIVE extension, not a single-day spike

8 cells, Šidák |t| ≥ 2.73; the house bar 3.0 governs.

| spike definition | B − A | t | halves |
|---|---:|---:|---|
| single-day ≥ 1.5 ADR | +5.4pp | +1.46 | +11.0 / +2.3 |
| **single-day ≥ 2.0 (primary)** | **+1.2pp** | **+0.18** | +2.9 / **−1.8** |
| single-day ≥ 2.5 ADR | +0.6pp | +0.07 | +0.7 / −0.3 |
| single-day ≥ 3.0 ADR | +0.5pp | −0.22 | +0.6 / −2.0 |
| cumulative ≥ 1.5 ADR | +10.5pp | +2.38 | +24.5 / +2.2 |
| cumulative ≥ 2.0 ADR | +10.9pp | +2.40 | +21.6 / +4.1 |
| cumulative ≥ 2.5 ADR | +11.0pp | +2.12 | +16.4 / +5.8 |
| **cumulative ≥ 3.0 ADR** | **+12.5pp** | **+2.51** | +16.7 / +6.9 |

**Cumulative dominates single-day at every threshold**, and all four cumulative cells are positive with
**both halves the same sign**. Best t is +2.51 — short of both Šidák and the house bar. **PARKED.**

⚠ **This is a REFRAME of his own rule.** Tito describes a *single-day* spike — "sell into strength" on a
big move. What actually sorts is **how far the trade has run from entry**, irrespective of how fast. The
single-day version is the weaker reading of his idea and it is the one that fails.

In the strongest cell (cumulative ≥ 3.0 ADR) the pure spike-exit arm C returns **−6.5%** against the
trail's −23.4% — a 17pp gap.

## ⚠ The finding that governs everything above: ALL ARMS ARE NEGATIVE

The 0.275Δ / ~36 DTE call on a generic archetype-A breakout **loses money at real fills**: 14.6% win rate,
median −85%, mean −23.4% under the trail. The best cell in the entire sweep still loses 6.5%. **The spike
rule makes a losing structure lose less; it does not make it work.** Identical in shape to the 21-DTE
result the same day — a real management rule applied to a trade that does not pay.

## What this does and does not establish

* **Settled:** the single-day spike override does not beat the 20-EMA trail on this pool, and the
  conditional branch is a variance lever rather than a return lever. Do not adopt it expecting more money.
* **PARKED, worth revisiting:** cumulative extension from entry as the exit trigger. Consistent sign,
  both halves, four thresholds, but t ≤ 2.51 against a bar of 3.0.
* ⚠ **Not established: that Tito's exit is wrong in his hands.** This tests his *mechanism at high
  frequency* (3,428 trades) precisely because his own practice is rare and discretionary. A rule applied
  to ~330 signals/year is not the rule applied to a handful of hand-picked trades.
* ⚠ **Not a refutation of his ARM example.** One trade at +1966% vs +578% is consistent with a rule that
  has a large effect on the tail — which is exactly what the p99 column shows — and says nothing about
  the mean.
* ⚠ **Universe:** top-200 breakout names by event count, which over-weights names that break out
  repeatedly. Since the comparison is *paired*, this affects generalisation, not internal validity.

## Data-integrity blocks (both clean)

**Path coverage:** median 83.3%, mean 77.2%, p10 45.8%. At a 60% floor, 2,756 resolved / 672 unresolved
(19.6%). The headline does **not** decay as coverage rises — the guard passed.

**Dark-path convention:** the Stage 1 pull filtered `delta BETWEEN 0.02 AND 0.98`, so a dying call drops
out of the data — missing marks concentrate in **losers**. Those contracts are therefore **settled at
ZERO, not dropped** (the conservative direction; 2.7% of trades). Both conventions reported: settle-at-zero
**+1.2pp** vs drop-dark **+0.7pp**. The answer does not depend on the choice.

⚠ v3 is the RAW table — 0.47% of contract-days appear twice with identical bid/ask and greeks differing at
the 4th decimal. Deduped on load; P&L-neutral. (The table was subsequently made unique table-wide; see
CLAUDE.md.)
