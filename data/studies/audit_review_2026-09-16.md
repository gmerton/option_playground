# Audit review — 16 September 2026

*Sequel to `playbook_review_2026-09.md` (8 Sept), which asked which playbooks could carry surplus buying power. This
one asks a harder question that the calendar work forced: **which of our backtests are measuring what they claim to
measure?** Two engines were audited and passed, one study was invalidated outright, two vendor claims were tested,
and the two surviving strategies were re-scored at an honest unit of observation. The practical conclusion changed.*

---

## 1. The calendar path study was invalidated, and the mechanism matters beyond calendars

The study built over 13–15 Sept reported +12% to +41% per trade for double calendars, diagonals and same-expiry
condors, and produced a playbook plus three live screener entries. All of it was an artefact.

**The bug.** The chain pull kept only strikes within ±6% of each day's close (±12% in the long cache, plus a
0.05–0.95 delta filter on stocks). After roughly a 2% move a leg fell outside that window, the daily path stopped,
and the simulator marked the trade at the last date all four legs were quoted — **before the loss finished**. It hit
52% of diagonal paths and 87% of paths whose underlying moved more than 3%. February 2020 SPY showed +28% where the
truth was −100%.

**The fix and the re-run.** Settlement now comes from intrinsic value at the expiry close, which needs no chain row
at all, and every trade carries a `truncated` flag. A clean pull (30% strike window, no delta filter) gives:

| structure, IWM/QQQ/SPY | 12/19d | 20/27d |
|---|---|---|
| single ATM calendar | +2.1% | −8.6% |
| double calendar | +4.4% | −1.6% |
| double diagonal 2% | +3.1% | −2.3% |
| iron condor 2% wings | +0.8% | −6.6% |

Monthly t ≤ 0.7 everywhere, 2018–2020 and 2023 negative, full losses on every crash week. On 26 single names the same
structures lose 5–18% per trade with monthly t of −3.4 to −5.0. **There is no edge in the calendar family.** The
playbook is withdrawn, the three ETF entries were removed from the Friday screener, and the stock screener is retired.

**Why it matters beyond calendars.** An inflated tail is the most dangerous kind of backtest error for a defined-risk
strategy, because it produces exactly the profile that invites over-allocation: a high win rate with a thin tail. It
was Gabe's drawdown question that exposed it, not any of the twelve robustness cuts run before it.

## 2. Two engines were audited for the same flaw and passed

| engine | why it is clean | crash-week evidence |
|---|---|---|
| bull put spreads (`lib.studies.put_spread_study`) | full chain, no price window; deep-ITM legs quoted through expiry (SPY 325/315P for 2020-03-20 marked at 93/83 on the last day); expiry value = each leg's last/mid = intrinsic | Dec 2018 −39%, Feb–Mar 2020 −31%, H1 2022 −14%, Apr 2025 −21%, all with −100% trades present; 12% of trades are full losses |
| 7-DTE long straddle (`run_straddle_recenter_*`) | ±15% strike window, and settlement recovers spot from put-call parity at *any* quoted strike, so a move outside the window still settles correctly; 44 of 13,459 trades dropped (0.3%), all zero-payout, none large movers | Feb–Mar 2020 +103%, Apr 2025 +120%, Aug 2024 +17% |

Both results stand as published.

## 3. The unit of observation — a second, subtler version of the same error

Tonight's vendor test surfaced a statistic that looked decisive for the wrong reason: 6,601 option trades gave a
per-trade t of 3.4, but they cluster into 71 months and are strongly correlated inside them. Aggregated to months,
**t = 0.1**. Applied back to our own two survivors:

| | per-trade t | weekly t | monthly t | months + | median trade | concentration |
|---|---|---|---|---|---|---|
| 7-DTE long straddle (n=5,886) | 3.7 | **0.5** | 1.8 | 56% | −16.3% | top 1% of trades = **91%** of total return; mean ex-top-1% **+0.38%** |
| SPY bull put 45 DTE (n=409) | 1.9 | 1.9 | 1.2 | 74% | +14.7% | worst 1% = −29% of return |

The straddle's headline +4.14% per trade rests on 58 trades out of 5,886. That does not make it false — long vol is
supposed to be fat-tailed — but it means the expectancy estimate is far less precise than the per-trade t implies,
and that you must take essentially every signal to have a chance of catching the trades that pay for the rest.

## 4. What is actually actionable: the pair, not either leg

> **Updated later the same day — see `etf_put_spread_exit_rule_2026-09-16.md`.** The put leg below is SPY-only. Rebuilt across the 20-ETF roster with a 50% take and no stop it earns +6.92%/trade (weekly t 5.80, 19 of 20 names positive, low concentration), and the blend improves to **+6.19%/month at t 4.0** with a worst month of −32%. The table below is retained as the weaker, SPY-only version.

Monthly returns, 93 months (2018-04 → 2026-02), correlation **−0.25**:

| sleeve | mean / month | t | months + | worst | best |
|---|---|---|---|---|---|
| 7-DTE long straddle | +5.32% | 1.8 | 56% | −52% | +120% |
| SPY bull put spread | +3.15% | 1.2 | 75% | −100% | +26% |
| **50 / 50 blend** | **+4.24%** | **2.5** | **70%** | −66% | +58% |

The blend's t exceeds both components. In 14 of the 18 months where the put spread lost more than 10%, the straddle
was positive, often hugely: 2020-02 +103 vs −70, 2025-03 +120 vs −11, 2018-10 +66 vs −13. This is the only pairing
tested and the negative correlation is structural (long vol against short vol), so it is not a fitted combination.

⚠ They can still lose together — 2018-11 (−52 / −52) and 2026-02 (−33 / −100). 93 months is a short sample and t 2.5
is respectable, not conclusive. Capacity is mismatched: the straddle sleeve runs ~63 entries a month across 294
tickers, the put spread here is SPY alone at ~1/week, so **the ETF-roster version of the put spread needs rebuilding
before the blend is real rather than conceptual.** Size both per `capital_allocation_framework.md`; these are
sleeve-level per-trade averages, not account returns.

## 5. Two vendor claims tested

**oquants forward-factor calendars** (`oquants_forward_factor_replication.md`). Their FF = 1/fvr − 1, so FF ≥ 0.20
means backwardation. On clean-settlement data the correlation between FF and calendar return is ~0 at four horizons
(12/19, 20/27, 28/55, 46/71) and their gate is negative at all four. **Not a refutation** — the gate fires on only
3.5–6% of ETF days (a crash detector; zero hits in 2019 and 2023), their universe is single names, and their FF is
computed on ex-earnings IV, which we have never built. Stopped rather than finished, because completing it needs that
model plus a 95-DTE pull. It also retracts the pre-erratum term-structure finding.

**oquants momentum-skew verticals** (`momentum_skew_vertical_study.md`). 249 names, 2019 → Feb 2026, 668,834 priced
verticals. **The mechanism is real and better established than the vendor established it**: conditional on the same
underlying move the gate is worth **+15.3pp**, and it does not select bigger movers (+0.88% vs +1.03%), so the wing
really is overpriced and selling it really does raise the payoff per unit of move. **The strategy is still rejected**:
monthly t 0.1, the top 1% of trades supply 52% of total return, WDC alone averages +427% over 91 trades, only 4 of 8
years beat the control, the put wing loses (−11.0%, second half −33.0%), and the *ungated* version of the same
structure is better behaved (+6.8%, monthly t 1.9, compounds 2.36×). Their own evidence was a lognormal simulation,
which mechanically prices any volatility smile as overpriced.

## 6. Data cliffs found along the way

`options_daily_v3` degrades in three steps, verified 2026-09-16 across all tickers: **bid/ask ends March 2026**,
stored IV and greeks end **mid-May 2026**, and from **June 2026** the table is trade prints only (last/volume/OI on
~78% of rows). Consequences:

- `silver.fwd_vol_daily` stopped on 2026-02-20 because its builder prices the ATM put off bid/ask. It cannot be
  extended, and **rebuilding it would not help**: without bid/ask no backtest can be extended past March 2026 either,
  and pricing one off trade prints of unknown side is the same class of assumption that produced §1.
- The long-straddle IV-percentile gate was re-sourced live from **IBKR** (`run_straddle_screen.py --iv-source ibkr`)
  rather than backfilled. The staleness was material at the single-name level even though VIX is flat: ranking the
  same metric in the old window versus the months since moves the percentile a median 27.5pp and flips the ≤30
  verdict on 10 of 20 names. On 2026-09-15 it was wrongly blocking 4 of 7 qualifiers.
- **The straddle's validation therefore ends in February 2026.** The only way to extend it is forward capture, which
  costs nothing: date the screen's output instead of overwriting it and reconcile at expiry.

## 7. Rules adopted

1. Before reporting any path simulation, print the P&L of the known crash windows (Dec 2018, Feb–Mar 2020, Aug 2024,
   Apr 2025) and confirm full losses appear.
2. Settle expiring legs at intrinsic from the underlying close, never from a chain row.
3. Make the pull's strike window at least the largest plausible move over the holding period, and never delta-filter
   a pull that feeds a path simulation. Record a `truncated` flag per trade and report its share.
4. Report the **monthly-mean t beside the per-trade t**, and state what share of total return the top 1% of trades
   supplies. Overlapping option trades inside a month are not independent draws.
5. If a result looks too good — 99% of months positive, a monthly t of 16 — suspect the data before the strategy.

## 8. Next

- Rebuild the bull put spread across the ETF roster so the §4 blend is tradeable rather than conceptual.
- Start the forward archive for the straddle screen before Friday's entries (one line; the first live week under the
  new IBKR gate is otherwise lost).
- Do not hunt another strategy before those two are done. The binding constraint is in-sample precision on what we
  already have, not a shortage of candidates.
