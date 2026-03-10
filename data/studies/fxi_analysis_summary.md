# FXI — Analysis Summary (Discarded)

**Date analyzed:** 2026-03-05
**Verdict: DISCARDED — puts broken by downtrend; calls thin.**

---

## Data

- Source: options_daily_v3, 2018-01-01 → 2026-03-05
- Rows: 917,501

## Background

FXI (iShares China Large-Cap ETF) tracks large-cap Chinese stocks listed in Hong Kong
(H-shares, Red Chips). Over the 2018–2025 study window, FXI fell ~40% from ~$50 to
~$25–30 due to:

- 2021: Regulatory crackdowns on tech/education sector (Alibaba, Tencent, Didi, TAL)
- 2021–2022: Evergrande / property sector crisis
- 2022: US delisting threat for Chinese ADRs
- 2022–2023: COVID lockdown overhang

This sustained multi-year downtrend makes FXI fundamentally different from ASHR
(CSI 300 domestic A-shares, range-bound) and EEM (broad EM, balanced).

## Results

### Put Spreads — UNUSABLE
The downtrend ground puts into the money repeatedly. Almost no combo produces
meaningful positive ROC:

| Best combo | N | Win% | ROC% |
|---|---|---|---|
| 0.35Δ / 0.05Δ, All VIX | 255 | 76.9% | +4.17% |
| 0.35Δ / 0.05Δ, VIX<20 | 143 | 76.9% | +6.05% |

Most 0.20–0.30Δ combos: **0% to −5% ROC**. Not viable.

### Call Spreads — THIN
The downtrend helps short calls directionally but China's volatility (sharp H2 2019
rally, 2020 COVID recovery, 2023–2024 stimulus bounces) limits the edge:

| Best combo | N | Win% | ROC% |
|---|---|---|---|
| 0.35Δ / 0.05Δ, VIX<20 | 151 | 84.8% | +9.85% |
| 0.35Δ / 0.05Δ, All VIX | 251 | 80.5% | +5.54% |
| 0.20Δ / 0.05Δ, All VIX | 350 | 90.6% | +2.96% |

At All VIX, the best realistic combo is ~+5.5% — comparable to EEM call spreads
(+4.33%), which we also discarded. The VIX<20 filter improves per-trade ROC to +9.85%
but produces only ~19 trades/year, and the 76.9% win rate at 0.35Δ is low relative
to risk.

## Why Discarded

1. Puts unusable — sustained downtrend eliminates the put premium edge
2. Calls thin — no structural edge materially better than already-confirmed strategies
3. No condor viability — a condor requires both sides to be independently profitable;
   with puts broken, ASHR is the better China condor choice
4. Compared to ASHR (confirmed iron condor): ASHR puts +8.49%, calls +8.19%, zero
   joint-loss years. FXI cannot match this on either side.

## Contrast with ASHR

| | ASHR | FXI |
|---|---|---|
| Price trend 2018–2025 | Range-bound (~$20–35) | Down ~40% ($50 → $25) |
| Put ROC (best) | +8.49% | +4.17% (most combos ≤0%) |
| Call ROC (best) | +8.19% | +5.54% (VIX<20: +9.85%) |
| Condor viable? | Yes — 0 joint-loss years | No — puts broken |
| Underlying | CSI 300 A-shares (domestic) | H-shares / Hong Kong-listed |
