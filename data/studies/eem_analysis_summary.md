# EEM — Analysis Summary (Discarded)

**Date analyzed:** 2026-03-05
**Verdict: DISCARDED — viable but thin on all three approaches.**

---

## Data

- Source: options_daily_v3, 2018-01-01 → 2026-03-05
- Rows: 1,005,881 | No splits
- EEM price range: $34–53 (2015–2024), recent breakout to ~$61

## Results

### Call Spreads (best: 0.20Δ / 0.05Δ wing, All VIX)
- 274 trades, 88.7% win, **+4.33% avg ROC**
- Losing years: 2020, 2023
- Too thin vs alternatives (XLV +6.82%, GLD +7.98%)

### Put Spreads (best: 0.30Δ / 0.05Δ wing, All VIX)
- 283 trades, 85.2% win, **+6.54% avg ROC**
- Losing years: 2019, 2021, 2023 — 3 of 8
- Comparable ROC to XLV/GLD but lower win rate and more losing years
- EM macro risk (China, currency) not fully compensated by IV premium

### Condor (calls + puts combined)
- Only 1 joint-loss year (2023) — EEM whipsawed both wings sequentially
- 2020 showed ideal negative correlation (COVID crash)
- Combined ROC ~+5–6%, but 4-leg complexity for thin per-side premium
- No structural edge (no decay, no directional tailwind) — just base IV premium

## Why Discarded

EEM's range-bound character reduces IV premium — there's no structural tailwind on either
side (unlike UVXY decay, XLV upward drift, or TLT rate headwind). All three approaches
are statistically profitable but the margins are too thin to justify execution overhead
vs confirmed strategies already in the portfolio.

## Per-year (call 0.20/0.05 vs put 0.30/0.05)

| Year | Call ROC | Put ROC | Joint loss? |
|------|----------|---------|-------------|
| 2018 | +13.39% | +1.35% | No |
| 2019 | +1.69% | −2.12% | Marginal |
| 2020 | −1.31% | +13.78% | No (negatively correlated) |
| 2021 | +5.58% | −0.58% | Marginal |
| 2022 | +12.44% | +5.07% | No |
| 2023 | −0.40% | −7.42% | **Yes** |
| 2024 | +1.43% | +24.11% | No |
| 2025 | +3.39% | +15.67% | No |
