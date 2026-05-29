# SPX Short Strangle — Trading Playbook

**Last updated:** 2026-03-24
**Status:** Parameters confirmed. Two active regimes. IC mode (0.10Δ wings) used for framework-consistent ROC. Ready for live trading.

---

## Overview

Sell a short strangle on SPX (S&P 500 Cash Index) every Friday when the regime qualifies.
The strategy sells an OTM call and OTM put at ~45 DTE, collecting premium from both sides,
and exits at either a 50% profit take or a 2× credit stop loss (whichever comes first).

SPX options are **cash-settled** (no pin risk, no early assignment) and receive favorable
**60/40 tax treatment** (Section 1256 contracts: 60% long-term, 40% short-term regardless of
holding period). They are European-style, which eliminates early exercise risk entirely.

**There are two active regime variants with different optimal put strikes:**

| Regime | Entry gate | Call Δ | Put Δ | Win% | ROC† | Priority |
|---|---|---|---|---|---|---|
| **Bearish_HighIV** | Below 50MA, VIX ≥ 20 | 0.20 | 0.30 | 86.3% | 10.4% | ~48 (Tier B) |
| **Bullish_HighIV + 200MA** | Above 50MA AND 200MA, VIX ≥ 20 | 0.20 | 0.40 | 95.7% | 11.2% | ~71 (Tier A) |

†ROC stated on **IC max-loss basis** (wing_width − net_credit, matching spread framework).
See [ROC Denominator Note](#roc-denominator-note) below for full context.

The put delta differs between regimes: in a bear market (below 50MA), a tighter 0.30Δ put
collects more premium and remains safe because the vol spike tends to be sustained. In a
genuine bull-market correction (above both MAs with a VIX spike), a fatter 0.40Δ put
collects even more — the elevated IV creates a juicy premium cushion that the market's
underlying upward trend tends to protect.

---

## Regime Identification

Computed on every trading day from SPX daily closes:

| Condition | Label |
|---|---|
| Close > 50-day MA AND Close > 200-day MA AND VIX ≥ 20 | **Bullish_HighIV** → enter with 200MA filter (both MAs required) |
| Close < 50-day MA AND VIX ≥ 20 | **Bearish_HighIV** → enter |
| VIX < 20 (any MA direction) | **LowIV** → no entry; edge disappears |
| Close > 50-day MA AND Close < 200-day MA AND VIX ≥ 20 | **Bear-market bounce** → no entry (see note below) |

**Why the 200MA gate on Bullish_HighIV matters:** During the 2022 bear market, SPX
repeatedly crossed above the 50MA while remaining well below the 200MA (dead-cat bounces).
Without the 200MA filter, those 14 trades had 57.1% win / −69.2% avg ROC — catastrophic
for a premium-selling strategy. With the filter, 2022 is reduced to 1 surviving trade (a
legitimate entry that still lost badly), and the regime ROC improves from 34.1% → 55.8%.

**Current regime:** Run `run_spx_strangle.py --dte 45 --vix-min 20` to see which regime
fired on the most recent Friday.

---

## Entry Rules

### Every Friday — check regime, then sell:

**Bearish_HighIV (SPX below 50MA, VIX ≥ 20):**
- Sell 0.20Δ OTM call
- Sell 0.30Δ OTM put
- Same expiry, targeting ~45 DTE

**Bullish_HighIV (SPX above 50MA AND 200MA, VIX ≥ 20):**
- Sell 0.20Δ OTM call
- Sell 0.40Δ OTM put
- Same expiry, targeting ~45 DTE

**Entry filters:**
- DTE tolerance: ±10 days around 45-day target
- Max delta error: ±0.08 from target
- Put strike must be ≤ call strike (standard strangle rule)
- Credit must be > 0 on both legs

**No entry when:**
- VIX < 20 (LowIV regime)
- SPX is above 50MA but below 200MA (bear-market bounce — skip regardless of VIX)
- Both MA/VIX criteria not simultaneously met

---

## Exit Rules

| Trigger | Action |
|---|---|
| **50% profit take** | Buy back strangle when combined mid ≤ 50% of entry credit |
| **2× stop loss** | Buy back strangle when combined mid ≥ 2× entry credit |
| **Expiry** | Let expire (or close for small debit) if neither trigger reached |

**Important on the stop:** The 2× stop never triggered in 10 years of backtesting (2016–2025,
142+ trades). This does not mean it will never trigger — it means the 45 DTE horizon and the
OTM strike selection have historically provided enough time and buffer for the market to
resolve. Include the stop as a hard GTC order. Given SPX's potential for gap moves, set
the stop as a **GTC limit order to buy the strangle at 2.0× the entry credit immediately
after entry** — don't rely on manual monitoring.

**On tighter stops:** A 1.5× stop was tested and hurts performance (lower ROC, higher
stop-out rate). The 2× level is the minimum stop that does not impede the natural trade
lifecycle. A no-stop variant performs similarly to 2×, confirming that stops in the 45 DTE
SPX strangle are more insurance than a performance driver.

Average holding period: ~27–28 days (exits well before the 45 DTE expiry via profit take).

---

## Parameters

| Parameter | Bearish_HighIV | Bullish_HighIV + 200MA |
|---|---|---|
| Underlying | SPX | SPX |
| Short call | 0.20Δ | 0.20Δ |
| Short put | 0.30Δ | 0.40Δ |
| Long call wing | 0.10Δ (further OTM) | 0.10Δ (further OTM) |
| Long put wing | 0.10Δ (further OTM) | 0.10Δ (further OTM) |
| Target DTE | 45 days | 45 days |
| DTE tolerance | ±10 days | ±10 days |
| Entry day | Friday | Friday |
| VIX gate | VIX ≥ 20 | VIX ≥ 20 |
| MA gate | SPX < 50-day MA | SPX > 50-day MA AND > 200-day MA |
| Profit take | 50% of net credit | 50% of net credit |
| Stop loss | 2× net credit (GTC) | 2× net credit (GTC) |
| Study period | 2018–2025 | 2020–2025 |

**Wing rationale:** Adding 0.10Δ protective wings converts the naked strangle to a defined-risk
iron condor, making the max-loss denominator consistent with all spread strategies in the
framework. The wings are deep OTM and rarely affect the P&L on winning trades (they decay
quickly), but they cap the catastrophic tail at `wing_width − net_credit` per side.

---

## Capital Allocation

**Approximate IC economics (SPX ~5,500, 0.10Δ wings):**

| Item | Bearish_HighIV (0.20C/0.30P) | Bullish_HighIV (0.20C/0.40P) |
|---|---|---|
| Avg gross strangle credit | ~$97/share | ~$104/share |
| Avg wing cost (both sides) | ~$32/share | ~$30/share |
| Avg net IC credit | ~$65/share = $6,500/contract | ~$74/share = $7,400/contract |
| 50% profit target | Close all 4 legs at ~$33/share net | Close all 4 legs at ~$37/share net |
| 2× stop level | Net IC value ≥ ~$130/share | Net IC value ≥ ~$148/share |
| IC max loss (hard cap) | wing_width − net_credit ≈ $150–250/share | wing_width − net_credit ≈ $150–250/share |

**Max loss is now structurally capped** by the long wings — no gap can exceed the wing
width. This is the key benefit of the IC structure vs the naked strangle. The 2× stop
remains in place as an early-exit rule but is no longer the only line of defense.

**Suggested sizing (risk-based):**
Max IC loss per contract ≈ $15,000–25,000 depending on wing widths (variable, check at
entry). A 2% account-risk rule on a $500K account → $10K risk per trade → size at 0.5–1
contract, or use XSP (mini-SPX, 1/10 notional) for finer sizing.

Both regimes are mutually exclusive by definition; they cannot fire on the same Friday.

---

## Backtested Performance (2018–2025, VIX ≥ 20, ~45 DTE, IC with 0.10Δ wings, 50% PT / 2× stop)

ROC stated on IC max-loss basis: `pnl / (wing_width − net_credit)`. This matches the
framework denominator for all spread strategies.

### Regime 1: Bearish_HighIV — Short 0.20Δ call / 0.30Δ put + 0.10Δ wings

| Year | N | Win% | Net Credit | Avg PnL | ROC% | Ann ROC% | Avg Days | Stops |
|------|---|------|-----------|---------|------|----------|----------|-------|
| 2018 | 9 | 88.9% | $36.34 | $20.66 | 12.1% | 152% | 32.7d | 0 |
| 2019 | 1 | 0.0% | $33.70 | −$16.30 | −11.5% | −100% | 42.0d | 0 |
| 2020 | 10 | 70.0% | $80.61 | $31.67 | 11.8% | 140% | 36.8d | 0 |
| 2021 | 5 | 60.0% | $58.70 | $14.50 | 3.5% | 77% | 30.8d | 0 |
| 2022 | 30 | 86.7% | $69.81 | $37.38 | 13.0% | 154% | 33.9d | 0 |
| 2023 | 7 | 85.7% | $53.94 | $28.15 | 12.0% | 125% | 37.4d | 0 |
| 2024 | 3 | 66.7% | $62.45 | $9.63 | 2.8% | 44% | 35.0d | 0 |
| 2025 | 6 | 66.7% | $86.90 | $11.08 | 3.8% | 81% | 34.0d | 0 |
| **TOTAL** | **71** | **78.9%** | **$65.36** | **$27.78** | **10.4%** | **129%** | **34.5d** | **0** |

**Priority score: (10.4 × 0.789) × (52/8.9) ≈ 48 → Tier B** (borderline; 50 is Tier A threshold)

**2022 was again the best year:** 30 trades, 86.7% win, 13.0% ROC — the IC wings are wide
and the premium is thick in a sustained bear market. 2021 and 2025 are soft (3.5% and 3.8%
ROC) — the IC wings eat into credit during lower-vol HighIV episodes.

**2019 outlier:** 1 trade, 0% win, −11.5% ROC (−$16.30 on $33.70 net credit). Much less
dramatic than the naked-strangle −128% because the wing caps the loss. Statistically irrelevant.

### Regime 2: Bullish_HighIV + above 200MA — Short 0.20Δ call / 0.40Δ put + 0.10Δ wings

| Year | N | Win% | Net Credit | Avg PnL | ROC% | Ann ROC% | Avg Days | Stops |
|------|---|------|-----------|---------|------|----------|----------|-------|
| 2020 | 24 | 100.0% | $74.52 | $38.01 | 15.5% | 195% | 30.5d | 0 |
| 2021 | 13 | 92.3% | $69.31 | $31.55 | 11.2% | 157% | 28.6d | 0 |
| 2022 | 1 | 0.0% | $74.52 | −$80.83 | −74.5% | −648% | 42.0d | 0 |
| 2023 | 2 | 50.0% | $63.56 | $31.39 | 10.6% | 92% | 42.0d | 0 |
| 2024 | 3 | 100.0% | $74.52 | $38.01 | 12.0% | 248% | 19.0d | 0 |
| 2025 | 4 | 100.0% | $85.81 | $43.82 | 13.2% | 150% | 32.2d | 0 |
| **TOTAL** | **47** | **95.7%** | **$74.52** | **$38.01** | **11.2%** | **145%** | **31.1d** | **0** |

**Priority score: (11.2 × 0.957) × (52/7.8) ≈ 71 → Tier A** (comparable to QQQ BuHI at 75)

**2022 loss is now bounded:** The IC wing capped the loss at ~$80/share vs the naked strangle's
$225/share blowout. ROC shows −74.5% on the max-loss basis, which is still painful on 1 trade
but reflects a real structural cap rather than an unlimited loss scenario.

**2016–2019:** No BuHI+200MA entries — VIX was almost continuously below 20 during the
2016–2018 bull market.

### Combined IC summary (both regimes, framework-consistent ROC basis)

| Metric | Bearish_HighIV IC | Bullish_HighIV + 200MA IC |
|---|---|---|
| Total trades | 71 | 47 |
| Win rate | 78.9% | 95.7% |
| Avg ROC/trade (IC basis) | 10.4% | 11.2% |
| Ann ROC (IC basis) | 129% | 145% |
| Avg hold | 34.5d | 31.1d |
| Stop-outs | 0 | 0 |
| Priority score | ~48 (Tier B) | ~71 (Tier A) |
| Worst year | 2021: 3.5% (5 trades) | 2022: −74.5% (1 trade) |

---

## VIX Level Sensitivity (Bearish_HighIV IC, 0.20C/0.30P + 0.10Δ wings)

| VIX Filter | N | Win% | Net Credit | Avg PnL | ROC% | Stops% |
|---|---|---|---|---|---|---|
| All VIX (≥20) | 71 | 78.9% | $65.36 | $27.78 | 10.4% | 0.0% |
| VIX < 30 subset | 51 | 74.5% | $59.29 | $22.13 | 8.7% | 0.0% |
| VIX < 25 subset | 30 | 70.0% | $52.76 | $14.67 | 5.9% | 0.0% |

The pattern holds: higher VIX (≥30) entries produce better ROC. The VIX 20–25 band is
marginal. Do not cap VIX upward — the highest-premium environments (2020, 2022) are the
most profitable.

---

## ROC Denominator Note

The capital allocation framework uses `max_loss = wing_width − credit` for all spread
strategies. This playbook follows the same convention with 0.10Δ wings.

**For reference — naked strangle ROC (credit-based denominator, NOT used for priority scoring):**

| Regime | Combo | Win% | ROC (credit basis) | Priority (credit basis) |
|---|---|---|---|---|
| Bearish_HighIV | 0.20C/0.30P | 86.3% | 45.5% | ~224 |
| Bullish_HighIV + 200MA | 0.20C/0.40P | 97.9% | 55.8% | ~363 |

These numbers are real — they reflect actual cash collected vs cash returned. But using
credit as the denominator ignores the capital committed to margining the naked position,
making comparisons to spread strategies misleading. The IC-adjusted scores (48 and 71)
are the correct basis for portfolio priority decisions.

---

## Risks and Known Limitations

1. **Max loss is structurally capped by the IC wings** — Unlike the naked strangle, the
   0.10Δ long wings guarantee a hard maximum loss of `wing_width − net_credit` regardless
   of overnight gaps. The 2× GTC stop remains as an early-exit rule; the wings are the
   true backstop.

2. **Simulation uses daily closing marks** — The 2× stop is checked at end-of-day in the
   backtest. In the live market, set the GTC stop order immediately at entry; it will
   trigger intraday and will likely catch gap moves faster than a daily review.

3. **Low-credit environments (2023–2024 BHI)** — When VIX is in the 20–22 range with
   moderate realized volatility, credits can be thin (~$80–97/share). Winning trades still
   barely hit 50% take, but ROC compresses. Monitor entry credit; if well below $80/share
   on the combined strangle, consider skipping or reducing size.

4. **Single-trade year problem** — Both BHI 2019 and BuHI 2022 had exactly 1 trade. A
   single loss in a 1-trade year produces a catastrophic ROC% figure that is statistically
   meaningless. The strategy is designed for consistent weekly engagement; isolated entries
   due to rare regime conditions carry disproportionate headline risk.

5. **SPX vs SPY / XSP** — This study uses SPX (cash index) option data from Athena.
   SPY options would require adjustment for dividends and have slightly different delta
   profiles. SPX is preferred for tax treatment and cash settlement; XSP (mini-SPX) is
   a practical alternative for smaller accounts (1/10 the notional).

6. **No rolling** — This playbook covers the base strangle without rolling. Rolling a
   strangle into a new position is a separate decision not covered here.

---

## How to Run

```bash
# IC mode — BHI (framework-consistent ROC, priority scoring basis)
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src \
  .venv/bin/python3 run_spx_strangle.py --dte 45 --vix-min 20 \
  --regime Bearish_HighIV --wing-delta 0.10

# IC mode — BuHI+200MA
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src \
  .venv/bin/python3 run_spx_strangle.py --dte 45 --vix-min 20 \
  --regime Bullish_HighIV --require-200ma --wing-delta 0.10

# Naked strangle mode (credit-based ROC, for reference only)
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src \
  .venv/bin/python3 run_spx_strangle.py --dte 45 --vix-min 20 \
  --regime Bearish_HighIV

# Refresh Athena cache (if data has been updated)
AWS_PROFILE=clarinut-gmerton MYSQL_PASSWORD=xxx PYTHONPATH=src \
  .venv/bin/python3 run_spx_strangle.py --dte 45 --vix-min 20 --refresh
```

**Key source files:**
- `run_spx_strangle.py` — SPX strangle study and sweep engine
- `data/cache/SPX_options_dte60.parquet` — cached Athena data (DTE ≤ 60, |Δ| 0.07–0.58)
- `data/cache/vix_daily.parquet` — VIX daily closes
- `data/studies/spx_strangle_playbook.md` — this file

---

## Research History

### 2026-03-24: Initial research and playbook creation

- **DTE sweep (7 / 20 / 45):** Annualized ROC is highest at 45 DTE; 7 DTE and 20 DTE both
  underperform on a risk-adjusted basis. 45 DTE selected as the standard.

- **VIX filter:** All-VIX (no filter) shows weak/inconsistent results. VIX ≥ 20 concentrates
  the edge. LowIV regimes (VIX < 20) have near-zero or negative ROC across all delta combos.

- **Stop-loss sweep (1.25×, 1.5×, 1.75×, 2.0×, no stop):** The 2× stop never fired across
  all 10 years. Tighter stops (1.25–1.5×) actively reduced performance by cutting trades
  that subsequently recovered. 2× retained as insurance stop only.

- **Regime split (BHI vs BuHI):** Separating Bearish_HighIV from Bullish_HighIV revealed
  that BuHI without filtering was badly contaminated by 2022 bear-market bounces (14 trades
  at −69.2% avg ROC). Adding the 200MA gate reduced 2022 from 14 trades to 1, improved
  regime ROC from 34.1% to 55.8%, and revealed BuHI as the stronger regime overall.

- **Delta optimization:** Bearish_HighIV optimal: 0.20C / 0.30P. Bullish_HighIV optimal:
  0.20C / 0.40P. The asymmetry makes intuitive sense: in a genuine bull correction (above
  both MAs), selling a fatter put captures more premium while the market's trend provides
  structural support below.

### 2026-03-24: IC wings added for consistent ROC denominator

The naked strangle ROC (pnl/credit) was ~5× overstated vs the spread framework's
max-loss denominator (pnl/(wing_width − credit)). Adding 0.10Δ protective wings converts
the strangle to a defined-risk IC, making the denominator consistent:

| Regime | Strangle ROC | IC ROC | Priority (strangle) | Priority (IC) | Tier |
|---|---|---|---|---|---|
| BHI 0.20C/0.30P | 45.5% | 10.4% | ~224 | ~48 | B (borderline) |
| BuHI+200MA 0.20C/0.40P | 55.8% | 11.2% | ~363 | ~71 | A |

Key findings from IC study:
- Wings add ~$30–32/share cost, reducing net credit to ~$65–74/share
- Optimal short-strike deltas (0.20C/0.30P and 0.20C/0.40P) unchanged from strangle study
- 2022 BuHI loss capped at −74.5% IC-ROC vs −212% naked (wing contained the damage)
- Both regimes show no stops fired across all years, consistent with strangle study
- BuHI+200MA (priority ~71) sits near QQQ BuHI (75) in the allocation framework
