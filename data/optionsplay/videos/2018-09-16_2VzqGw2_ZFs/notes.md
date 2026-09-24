# OptionsPlay: "Credit Spread Income Strategy w/ NDX Weekly Index Options" (Tony Zhang, 2018-09-16, 73 min)

_Reviewed 2026-09-24. A Nasdaq-sponsored webinar: 25 min of slides, a 20-min OptionsPlay demo on NDX/NQX, then Q&A.
Transcript in this folder (auto `en-orig`)._

## Verdict: 2.5 / 5. The index put sale on an oversold reading points the same way as our one certified cell; the rest is sponsor copy and unpriced rules

The core trade (sell a bull put spread on the index when an oscillator reads oversold, repeatedly) is the ungated,
technical-trigger ancestor of our only certified short-premium cell (SPY bull put in the bearish-high-IV state,
t 6.07). The direction agrees. Our data says the variable doing the work is the **VIX level / selloff state, not
the oscillator**. The mirror trade he pairs with it (a bear call when overbought) fails on our data, and so do his
stop rules. The NDX-vs-SPX implied-vol gap he presents as a reason to prefer NDX is mostly higher *realised* vol,
not a larger premium. There is no credit/width ranking here: this predates the report, and strikes are chosen by
eye with a 1-SD "trading range" tool. No n, no costs, no backtest shown, beyond "based on all of our back testing"
for the 50% take.

## His selection rule

- **Underlying:** NDX, or NQX (1/5 size) for accounts under $100k. His reasons are cash settlement, European exercise,
  60/40 tax treatment and no corporate actions (08:01–11:01).
- **Tenor:** weeklies, **1–3 weeks** (24:00, 68:08).
- **Entry:** **stochastic oversold → bull put; overbought → bear call**, repeated on the same index, legging the two
  sides into a condor rather than opening one (32:02–37:00, 60:01).
- **Strike:** set the width first (the "opportunity"), then the distance: near the money with a strong view,
  far OTM with none (22:00–27:01, 47:01).
- **Exits:** take profit at 50% if more than a week is left. **Stop** at 75–100% of the credit when credit/width is
  > 20%, and at 100–200% of the credit when it is < 20% (38:00–40:01).

## Claims against our ledger

| @ | Claim | Tag | Our evidence (source) |
|---|---|---|---|
| 11:01–13:00 | NDX implied vol exceeds SPX by 1.7 (weekly) to 2.3–2.4 vol pts (2010–2017), so NDX spreads pay more premium | **PARTIAL** | Higher IV is not a higher premium. `vrp_panel_study.md` §2.10, 10d implied − realised: **QQQ +1.38vp vs SPY +1.26vp** (CIs [+0.80, +1.91] vs [+0.78, +1.71], which overlap almost entirely). The extra IV is mostly paid back in realised vol. Our certified cell also prefers SPY: SPY bearish-high-IV t 6.07 vs **QQQ bearish-high-IV t 3.53**, which fails its 54-cell sweep (TEST_INDEX §0) |
| 08:01–11:01 | Index options: cash-settled, European, 60/40 tax, no corporate actions | **AGREES (fact, not edge)** | Structural. We trade the SPX condor for the same reasons; the XSP / SPX parity pricing in the Davis study relies on European exercise |
| 24:00 | Index credit spreads: weeklies 1–3 weeks out, to maximise theta | **PARTIAL** | Short tenor is where the premium sits (10d VRP +1.75vp, t 8.93 vs 30d t 2.08, `vrp_panel_study.md` §1). The certified index cells are short (SPY bull put 20 DTE; SPY 1-day fly t 3.4), **but both are gated**. Ungated, a short-dated index put sale is not certified: QQQ bullish-low-IV −4.8% month-weighted, t −0.87 (§0) |
| 32:02–36:00 | **Enter the bull put when the stochastic is oversold**, over and over | **AGREES in direction · the oscillator is a VIX proxy** | `rsi_conditioning_study_2026-09-16.md` §A (20 ETFs, 45 DTE): RSI<40 +3.88pp pooled (t 2.21) → **+1.21pp controlling for VIX (t 0.69)**, and −0.23pp within-week. The certified version of his trade uses the selloff + VIX state directly: SPY bull put bearish-high-IV 0.25/0.15, **t 6.07** (§0 Tier A/B, doctrine A1). A stochastic is a different oscillator in the same family, so this is not a new axis |
| 35:00–36:00 | **Enter the bear call when overbought** | **CONTRADICTED** | ETF call side FAIL; the mirror-image bear call earns **−2.66%** (`etf_put_spread_exit_rule_2026-09-16.md` erratum; TEST_INDEX §1 "exit rule generalise to bear calls" row) |
| 60:01–61:01 | Iron condors make no sense (you can't be overbought and oversold at once); leg into them | **PARTIAL** | ETF condor +0.36%/trade, t 0.6: the call side adds nothing, so his instinct holds on ETFs. **But** the SPX condor in the bearish-high-IV state certifies (**t 5.21**), and it is the same bet as the SPY bull put (one set of stress episodes). It works because of the put side and the state, not because of a both-sides view |
| 19:01–22:00, 28:00–30:00 | Far-OTM 95–99% POP spreads risk 10–30× the credit; one loss wipes out 20–30 wins | **AGREES** | Doctrine rule 14 (POP is not an edge). Low-delta tail 44× vs 13× the credit (§9 tastylive row) |
| 25:01–27:01 | Near-the-money if you have a view, far OTM if you don't | **PARTIAL** | The 1-day SPY study puts the edge **at the money** (on positive-gamma days); the 16/5Δ put spread wins 94% but earns +1.9% on risk (`gex_spy_condor_putspread_2026-09-21.md`). The certified 20-DTE cell uses 0.25/0.15, neither ATM nor far OTM. A directional view is not what selects it; the state does |
| 37:00 | Puts get more volume because they carry more premium and higher IV | **AGREES** | Skew. Our put side works and the call side doesn't (above) |
| 38:00–40:01 | Take 50% early if more than a week is left | **NULL at real fills (was AGREES)** | 50% take, no stop: **+5.70%/trade, monthly t 3.13** on ETFs at 45 DTE (`etf_put_spread_exit_rule_2026-09-16.md`) ⚠ *corrected 2026-09-24: the +5.70% was GROSS and came from `options_cache`, which drops zero-bid quotes and so flatters take-profit fills. On unfiltered v3 at house fills the 50% take is **−2.78%/trade** (hold −1.37%); take − hold −1.42pp, t −1.77 → NULL (`putspread_exit_capital_time_2026-09-24.md`)*. The certified SPY bearish-high-IV cell carries the same 50% take, at 20 DTE (`run_tierab_significance.py` l.8–11) |
| 40:01 | **Stops**: 75–100% of the credit (near the money), 100–200% (far OTM) | **CONTRADICTED on bull puts · mixed in the certified cells** | ETF bull puts, 50% take + 2× stop: **−4.3%/trade, t −5.4**, negative in both halves (`etf_put_spread_study.md` §2); take alone +5.70%. The certified SPY bull put runs **no stop** (t 6.07). ⚠ But the certified **SPX condor runs a 50% take / 2× stop** (t 5.21, `run_tierab_significance.py` l.12). It was chosen from a 49-cell sweep, and no stop/no-stop comparison is on file for it, so do not read that as evidence for his stop |
| 56:01 | 10Δ/5Δ spreads are what the large NDX prints trade (e.g. $8M risk for $100k) | **UNTESTABLE / descriptive** | One print. The adjacent evidence is the tail-overlay row: 5Δ same-expiry puts were **−100% on all 75** bucket trades (§1 [WL-5f]), i.e. the 5Δ wing almost never pays |
| 64:01 | Open interest and volume are not liquidity | **AGREES** | Doctrine rule 7. We gate on the bid/ask spread |
| 57:01 | Pick strikes visually from the 1-SD trading range, not from the chain | **UNTESTED, low value** | A 1-SD strike is ≈ a 16Δ strike: a delta choice by another name. ARM B says the choice of wing within a name is flat past 0.20Δ |

## Discrepancies found in our own docs

None new in the rows cited here. The QQQ-vs-SPY VRP comparison is read from the primary table
(`vrp_panel_study.md` l.32–33), not from a summary.

## What's new / test candidates

**None.** Every testable claim is already answered:
- oscillator entry → the RSI row (§1): a VIX proxy, and the certified cell uses the state directly;
- bear call on overbought → the ETF call-side row (§1): FAIL;
- stops → `etf_put_spread_study.md` §2: INVERTED;
- 50% take → the ETF exit-rule row: AGREES;
- far-OTM POP → doctrine rule 14.

NDX itself is not in our panel. A QQQ-for-NDX substitution is reasonable, and it says the extra IV is not extra
premium, so testing NDX directly would be a new product rather than a new axis. The one variant not covered is
**weekly (1–3 week) index put spreads triggered by an oscillator, with the VIX held fixed**. The RSI regression
already answers that shape (RSI adds +1.21pp, t 0.69, once VIX is in), so do not queue it.
