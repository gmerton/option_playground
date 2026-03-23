# Capital Allocation Framework

**Purpose:** When multiple signals fire on the same Friday, this framework determines
which strategies get priority access to capital and how much to deploy.

**Account size assumed:** $100,000

---

## The Core Idea

Not all signals are created equal. Two factors drive priority:

1. **Edge per trade** — expected ROC × win rate (how good is this trade?)
2. **Opportunity cost** — how long until the next chance at this signal?

A signal that fires only 9 times per year and misses another 43 opportunities to wait.
An always-on signal can be taken next Friday. When capital is limited, **rare, high-quality
signals should always be funded first.**

---

## Priority Score Formula

```
Priority Score = (Avg_ROC% × Win_Rate) × (52 / Weeks_Active_Per_Year)
```

This equals: expected return per trade × opportunity multiplier (how many extra Fridays
you'd have to wait for another shot at this signal).

- An always-on signal (52 weeks/year) gets multiplier = 1.0
- A signal firing 9 weeks/year gets multiplier = 52/9 = 5.8
- A signal firing 5 weeks/year gets multiplier = 52/5 = 10.4

ROC is stated on a **capital-at-risk basis** throughout (max loss = wing width − credit
for spreads; debit paid for calendars/straddles). All figures are OOS-validated or
full-backtest unless noted.

---

## Full Priority Ranking

*All confirmed strategies (8yr backtest or 5yr walk-forward). Provisional strategies listed separately.*

| Rank | Strategy / Regime | Avg ROC% | Win% | Wks/yr | Priority Score | Tier |
|------|-------------------|----------|------|--------|---------------|------|
| 1 | **XLU** — Put calendar (FVF ≤ 0.90) | 78.8% | 93.5% | 11 | **347** | A |
| 2 | **XLE** — Bull put (Bearish_HighIV only) | 35.5% | 84.6% | 9 | **174** | A |
| 3 | **SPY** — Long straddle (Bearish_LowIV) | 22.6% | 57.9% | 5 | **136** | A |
| 4 | **QQQ** — Bull put 0.35Δ/0.15Δ (Bearish_LowIV) | 8.3% | 90.5% | 5 | **78** | A |
| 5 | **QQQ** — Bull put 0.45Δ/0.35Δ (Bullish_HighIV) | 14.1% | 80.9% | 8 | **75** | A |
| 6 | **SPY** — Double cal 0.25P/0.10C (Bearish_HighIV) | 23.7% | 50.0% | 9 | **68** | A |
| 7 | **INDA** — Bull put 0.25Δ/0.20Δ ⚠️ | 12.8% | 91.7% | 10 | **61** | A |
| 8 | **SPY** — Bull put 0.25Δ/0.15Δ (Bearish_HighIV) | 7.5% | 94.7% | 9 | **41** | B |
| 9 | **SPY** — Bull put 0.45Δ/0.35Δ (Bullish_HighIV) | 8.3% | 81.9% | 9 | **39** | B |
| 10 | **XLF** — Bull put 0.40Δ/0.30Δ (Bearish_HighIV) | 11.7% | 77.5% | 13 | **36** | B |
| 11 | **QQQ** — Bull put 0.25Δ/0.15Δ (Bearish_HighIV) | 7.4% | 92.3% | 10 | **35** | B |
| 12 | **TLT** — Bull put 0.45Δ/0.35Δ (Bullish_LowIV) | 10.4% | 87.1% | 15 | **31** | B |
| 13 | **Long Straddle** — approved list, FVR ≥ 1.40 (per ticker) | 13.1% | 44.1% | 12 | **25** | B |
| 14 | **BJ** — Bull put 0.20Δ/0.10Δ (monthly) | 9.2% | 94.2% | 19 | **24** | B |
| 15 | **SOXX** — Bull put 0.35Δ/0.30Δ | 18.0% | 89.3% | 52 | **16** | C |
| 16 | **TLT** — Bear call 0.40Δ/0.30Δ (Bearish_HighIV) | 4.4% | 87.8% | 13 | **15** | C |
| 17 | **GLD** — Put calendar (iv_ratio ≥ 1.00) | 13.3% | 75.4% | 35 | **15** | C |
| 18 | **Long Straddle** — approved list, FVR 1.20–1.39 (per ticker) | 13.1% | 44.1% | 20 | **15** | C |
| 19 | **XLF** — Bear call 0.35Δ/0.25Δ (Bullish_LowIV) | 7.0% | 69.7% | 19 | **13** | C |
| 20 | **ASHR** — Iron condor (put + call spreads) | 11.2% | 90.0% | 52 | **10** | C |
| 21 | **TLT** — Bear call 0.40Δ/0.30Δ (Bullish_HighIV) | 2.6% | 86.0% | 12 | **10** | C |
| 22 | **GLD** — Bull put 0.30Δ/0.25Δ (VIX < 25) | 8.0% | 87.1% | 40 | **9** | C |
| 23 | **TLT** — Bear call 0.25Δ/0.15Δ (Bearish_LowIV) | 2.4% | 88.7% | 12 | **9** | C |
| 24 | **USO** — Bull put 0.25Δ/0.20Δ | 9.6% | 92.3% | 52 | **9** | C |
| 25 | **SPY** — Double cal 0.25P/0.25C (Bullish_LowIV) | 10.4% | 59.3% | 26 | **12** | C |
| 26 | **UVXY** — Bear call + short put (bi-weekly) | 5.6% | 74.6% | 26 | **8** | C |
| 27 | **SQQQ** — Bear call 0.50Δ/0.40Δ | 10.0% | 82.7% | 52 | **8** | C |
| 28 | **XLF** — Strangle 0.20Δ/0.25Δ (Bearish_LowIV) | 1.7% | 79.7% | 9 | **8** | C |
| 29 | **XLF** — Strangle 0.35Δ/0.40Δ (Bullish_HighIV) | 2.1% | 75.8% | 11 | **7** | C |
| 30 | **UUP** — Short ATM straddle | 2.3% | 73.1% | 13 | **7** | C |

⚠️ INDA: Score reflects historical data (2019–2022 core); recent years sparse. Verify chain liquidity before entry.

### Provisional Strategies (2 years data only — subordinate to all above)

| Strategy | Avg ROC% | Win% | Score | Notes |
|----------|----------|------|-------|-------|
| GEV — Bull put 0.25Δ/0.20Δ | 17.9% | 94.4% | 17 | Post-spinoff April 2024; no bear market test |
| CLS — Bull put 0.25Δ/0.20Δ | 17.5% | 93.4% | 16 | Viable from 2024 only; 0.05Δ wing mandatory |
| TMF — Bear call 0.35Δ/0.30Δ | 15.1% | 87.3% | 13 | Pre-2024 data unreliable (illiquid) |

Provisional strategies: take at half the recommended size until 3+ years accumulate.

---

## Tier Definitions

### Tier A — Score ≥ 50 (Rare, High-Quality)
*These signals fire infrequently. When they appear, fund them first — you may not get
another chance for weeks. Take at full recommended size regardless of other signals.*

XLU calendar, XLE BearishHI, SPY BearishLO, QQQ BearishLO,
QQQ BullishHI, SPY BearishHI double cal, INDA

### Tier B — Score 20–49 (Selective, Good Edge)
*Fires less than 20 weeks/year or offers meaningfully above-average edge.
Take at full size; reduce to 75% only if Tier A signals are crowding capital.*

SPY BearishHI put spread, SPY BullishHI put spread, XLF BearishHI,
QQQ BearishHI, TLT BullishLO, Long Straddle (FVR ≥ 1.40), BJ

### Tier C — Score < 20 (Standard / Always-On)
*Fires frequently or has lower per-trade edge. These form the base of the book.
Reduce these first when total exposure would be exceeded.*

SOXX, TLT (other regimes), GLD, Long Straddle (FVR 1.20–1.39),
ASHR, USO, SQQQ, UVXY, XLF (LowIV regimes), SPY BullishLO cal, UUP

---

## Friday Morning Decision Rules

### Step 1 — Check Tier A signals first
For each potential entry, classify its tier. If any Tier A signal is present, commit
capital to it before evaluating anything else.

### Step 2 — Fund in priority order
Work down the ranked table. Each strategy gets its recommended allocation unless
the portfolio cap would be breached.

### Step 3 — Apply the portfolio cap (25% max open risk)
Total capital at risk across all open positions ≤ 25% of account ($25,000).
When this cap would be breached, drop the lowest-ranked firing signal(s).

### Step 4 — Apply correlation adjustments (before finalizing)
See correlation rules below — some pairs require reduced sizing.

### Step 5 — Provisionals fill last
GEV, CLS, TMF enter only after confirmed strategies are funded, at half size.

---

## Recommended Allocations Per Strategy

*Standard sizing assuming no cap is breached. Reduce proportionally if cap applies.*

| Strategy | Standard Size | Notes |
|----------|--------------|-------|
| TLT | 3% ($3,000) | Defined risk only |
| XLF spreads | 3% ($3,000) | Strangles: 2% ($2,000) |
| XLF strangles | 2% ($2,000) | Undefined risk, smaller |
| SPY put spread | 1.5% ($1,500) | Paired with calendar in BearishHI |
| SPY calendar | 1.5% ($1,500) | Runs alongside put spread |
| QQQ | 2% ($2,000) | Reduce to 1.5% if SPY also fires |
| XLE (BearishHI only) | 3% ($3,000) | Rare signal; take full size |
| XLU calendar | 2% ($2,000) | Rare; take full size |
| GLD put spread | 3% ($3,000) | |
| GLD calendar | 2% ($2,000) | |
| USO | 2% ($2,000) | |
| SOXX | 2% ($2,000) | |
| SQQQ | 2% ($2,000) | |
| BJ | 3% ($3,000) | Monthly; 45 DTE |
| ASHR | 2% ($2,000) | Per side (put + call = 4% total) |
| UVXY | 2% ($2,000) | Each of call spread + short put |
| INDA | 2% ($2,000) | Verify liquidity first |
| UUP | 2% ($2,000) | Supplementary |
| Long Straddle (FVR ≥ 1.40) | 1.5% ($1,500) per trade | 3% portfolio cap total |
| Long Straddle (FVR 1.20–1.39) | 0.75% ($750) per trade | Within the 3% cap |
| GEV (provisional) | 1.5% ($1,500) | Half of normal sizing |
| CLS (provisional) | 1.5% ($1,500) | Half of normal sizing |
| TMF (provisional) | 2% ($2,000) | Half of normal sizing |

---

## Correlation Adjustments

### SPY + QQQ (both sell put spreads)
- If both fire the same week → reduce **each** to 1.5% (from 2%)
- Combined: 3% instead of 4% — maintains exposure without doubling correlated risk

### TLT + TMF (both interest rate)
- TMF is a 3× version of the same position as TLT bear call spreads
- If both fire in the same direction → reduce TMF to 1% ($1,000)
- Do not hold both at full size simultaneously

### Long Straddle + SPY BearishLO Straddle
- Both are long volatility; they tend to win and lose together
- Cap total long-vol exposure at 4.5% (SPY straddle 1.5% + long straddle 3%)

### SQQQ (inverse ETF) vs QQQ BearishHI (bull put on QQQ)
- These are structurally compatible (both profit in QQQ decline)
- But SQQQ call spread profits when SQQQ declines → QQQ rises
- **These are actually in opposite directions** — no correlation concern, can hold both

### ASHR + INDA (EM exposure)
- Both are EM ETFs and can sell off together in risk-off
- If both signal: run both but count toward a 4% EM cap total

---

## Capital Waterfall Example

*It's Friday. The following signals are active:*
- QQQ: Bullish_HighIV regime (Tier A, Score 75)
- TLT: Bullish_LowIV regime (Tier B, Score 31)
- SOXX: always-on (Tier C, Score 16)
- GLD put spread: VIX < 25 (Tier C, Score 9)
- Long straddle: OIH FVR = 1.52 (Tier B, Score 25)
- CLS: always-on (Provisional)

*Funding order:*
1. **QQQ BullishHI** → $2,000 (Tier A, full size; SPY not firing so no correlation cut)
2. **Long straddle OIH FVR 1.52** → $1,500 (Tier B, FVR ≥ 1.40 tier)
3. **TLT BullishLO** → $3,000 (Tier B)
4. **SOXX** → $2,000 (Tier C)
5. **GLD put spread** → $3,000 (Tier C)
6. **CLS** → $1,500 (Provisional, half size)

*Total deployed: $13,000 (13% of account) — well within 25% cap. All signals funded.*

*If cap were binding (say only $8,000 available):*
→ Drop CLS (Provisional), drop GLD put spread (Tier C, lowest score), drop SOXX
→ Fund QQQ + Long straddle + TLT = $6,500, then partial SOXX if room remains

---

## When to Override the Framework

The priority score is a guide, not a rule. Override in these cases:

**Promote a signal (take at full size even if cap is tight):**
- XLU FVF ≤ 0.90 fires: this is the highest-score signal in the book (347).
  Skip a Tier C or even Tier B signal to fund it.
- XLE BearishHI fires after months of absence: treat as high urgency.

**Demote a signal (take at reduced size or skip):**
- You have large open losses in correlated strategies this week
- A Tier C signal's underlying has had unusual news or gaps recently
- INDA: if chain shows <5 strikes with bid > 0, skip this week regardless of score
- Any provisional strategy if you are already at 20%+ deployment

---

## Quick Reference Card

```
TIER A (fund first, always):
  XLU cal     Score 347  → $2,000
  XLE BearHI  Score 174  → $3,000
  SPY BearLO  Score 136  → straddle at 1.5%
  QQQ BearLO  Score  78  → $2,000 (1.5% if SPY also firing)
  QQQ BullHI  Score  75  → $2,000 (1.5% if SPY also firing)
  SPY cal BHI Score  68  → $1,500 (alongside put spread)
  INDA        Score  61  → $2,000 (verify liquidity)

TIER B (full size unless cap binding):
  SPY put BHI Score  41  → $1,500
  SPY put BHI Score  39  → $1,500
  XLF put BHI Score  36  → $3,000
  QQQ put BHI Score  35  → $2,000 (1.5% if SPY also)
  TLT BullLO  Score  31  → $3,000
  Straddle 1.40+ Score 25 → $1,500/trade, 3% cap
  BJ          Score  24  → $3,000

TIER C (standard; reduce first if cap exceeded):
  SOXX        Score  16  → $2,000
  TLT other   Score ≤15  → $3,000
  GLD (both)  Score ≤15  → $3,000 + $2,000
  Straddle 1.20+ Score 15 → $750/trade, within 3% cap
  ASHR        Score  10  → $2,000/side
  USO         Score   9  → $2,000
  SQQQ        Score   8  → $2,000
  UVXY        Score   8  → $2,000
  UUP         Score   7  → $2,000

PROVISIONAL (fund last, half size):
  GEV, CLS, TMF              → 1.5–2% each
```

---

## Notes and Caveats

- Priority scores are **time-stable estimates** based on historical frequency. Actual
  regime frequencies shift with market conditions (e.g. extended bull runs mean
  BearishHI regimes are rarer in practice than historical averages suggest).
- Scores assume **independent capital** per strategy. In practice, overlapping margin
  requirements may reduce available capital — use Reg T margin calculations.
- The **25% portfolio cap** is conservative by design. With highly defined-risk
  spreads, true tail-risk exposure is lower than notional allocation suggests.
  Adjust upward (to 30%) only if all open positions are defined-risk spreads.
- **Reassess scores annually** as new backtest data accumulates, especially for
  provisional strategies (GEV, CLS, TMF) which may graduate to confirmed status.

*Framework written: 2026-03-22*
*Based on all active playbooks as of this date.*
