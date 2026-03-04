# UVXY Combined Strategy — Bear Call Spread + Short Put

**Run date:** 2026-03-02

**Related studies:**
- `data/studies/uvxy_bear_call_spread.md` — call spread standalone
- `data/studies/uvxy_short_put_sweep_20dte.md` — put standalone
- `data/studies/uvxy_short_call_sweep.md` — naked call baseline

---

## Strategy Definition

Every Friday, 20 DTE, spread ≤ 25% on short legs, 50% profit take:

| Condition | Action |
|---|---|
| **Always** | Sell 0.50Δ call / Buy 0.40Δ call (bear call spread) |
| **VIX < 20** | Also sell 0.40Δ put |
| **VIX ≥ 20** | Call spread only (puts too risky in elevated vol) |

**Capital model (equal allocation):**
Combined ROC = 0.5 × spread_roc + 0.5 × put_roc (when both active)
Combined ROC = spread_roc (call-only weeks)

This answers: "if I split my options budget 50/50 between the two strategies, what blended ROC do I earn per week?"

---

## Results

```
  Year   Spr  Put   SprROC%   PutROC%   CombROC%   CombAnn%   Win%
  --------------------------------------------------------------------------
  2018    45   37     -7.08%    +10.82%      +0.31%    +499%   71.1%
  2019    51   50    +17.23%     -5.68%      +6.19%    +587%   52.9%
  2020    48    8     +5.74%    +16.77%      +9.22%    +579%   91.7%
  2021    46   29     +6.46%    +12.61%      +8.22%    +401%   82.6%
  2022    50    4     +4.22%    +18.60%      +7.74%    +566%   88.0%
  2023    41   30     +4.30%     +0.49%      +3.48%    +530%   65.9%
  2024    46   40     +1.16%     +5.85%      +3.17%    +598%   69.6%
  2025    42   27    +11.54%     +7.35%     +10.08%    +770%   76.2%
  --------------------------------------------------------------------------
   ALL   374  228     +5.06%     +5.22%      +5.60%    +557%   74.6%
```

*2026 excluded (5 weeks, incomplete).*

`Spr/Put` = entries per year | `CombROC%` = equal-capital blended per-trade ROC | `Win%` = fraction of weeks with positive combined P&L

---

## The Dominant Finding: Both Sides Never Lose Together

```
  Joint outcomes (weeks with both sides active, N=228):
    Both win         : 133  (58.3%)
    Spread win only  :  59  (25.9%)
    Put win only     :  36  (15.8%)
    Both lose        :   0   (0.0%)   ← zero in 8 years
```

**In 8 years and 228 weeks where both sides were active, there was not a single week where both the call spread and the put lost simultaneously.** The two strategies fail in structurally opposite scenarios — when one bleeds, the other earns.

Spread/put ROC correlation during VIX<20 weeks: **-0.22** (modest negative, not perfectly hedged, but meaningfully diversifying).

---

## Every Year Is Profitable

The combined strategy is positive in all 8 full years — including the two years that nearly bankrupted each standalone strategy:

| Year | What happened | Standalone result | Combined result |
|---|---|---|---|
| **2018** | Volmageddon (Feb 5 VIX spike) | Spread: **-7.08%** | **+0.31%** — puts saved it |
| **2019** | Slow UVXY decay, calm VIX | Put: **-5.68%** | **+6.19%** — spreads dominated |
| **2020** | COVID March spike | Spread (naked): -22.75% | **+9.22%** — wing+puts both helped |
| **2023** | Weakest combined year | Both sides modest | **+3.48%** — still positive |

No single year produced a combined loss on a per-trade basis.

---

## VIX Regime Breakdown

```
  Call spread only (VIX ≥ 20): 146 weeks  avg spread ROC =  +7.59%
  Both sides       (VIX < 20): 228 weeks  avg combined ROC = +4.33%
                                            (spread +3.45%  put +5.22%)
```

Two notable observations:

1. **Call spreads earn more in high-VIX weeks (+7.59%)** than in low-VIX weeks (+3.45%). High VIX = elevated UVXY premium = richer credit collected. This is consistent with the naked call finding that "All VIX" outperforms VIX<20 for the call side.

2. **The combined strategy earns more in low-VIX weeks (+4.33%)** when both sides are active vs the call spread alone (+3.45%), because put premium in calm markets is reliable. The put adds +1.78% per week (on equal capital) in VIX<20 environments.

---

## Comparison: Standalone vs Combined

| Metric | Call Spread only | Put only (VIX<20) | Combined |
|---|---|---|---|
| Per-trade ROC | +5.06% | +5.22% | **+5.60%** |
| AnnROC | +593% | +433% | **+557%** |
| Worst year ROC | -7.08% (2018) | -5.68% (2019) | **+0.31% (2018)** |
| "Both lose" rate | — | — | **0.0%** |
| Win% | 86.6% | 73.2% | 74.6% |

Combined per-trade ROC (+5.60%) exceeds both standalone strategies. The combined AnnROC (+557%) sits between the two standalones, as expected. The win rate drops vs naked call because adding the put introduces more individual losing weeks — but the *losing weeks are smaller* because the other side partially offsets.

---

## Practical Implementation

### Entry frequency
**Bi-weekly** (every other Friday) is preferred over weekly:
- Max 2 concurrent positions in a spike vs 4 weekly
- Size ~2× larger per trade for the same catastrophic-loss budget
- ~26 spread trades + ~13 put trades per year (at current VIX<20 frequency of ~60%)

### Position sizing ($100k portfolio)
With bi-weekly entry and a 10% max-loss budget ($10k):
```
Per-trade max-loss budget  = $10,000 ÷ 2 concurrent = $5,000
  Call spread (~$38–76 max_loss/contract): ~65–130 contracts
  Put (Reg T ~$200–300/contract):          ~16–25 contracts
```

The call spread requires far less capital per contract — use the equal-capital rule to
decide absolute contract counts: allocate $2,500 to each side per trade.

### Capital usage at any given time
- VIX ≥ 20 (38% of weeks): only call spread margin tied up (~$2,500)
- VIX < 20 (62% of weeks): both sides tied up (~$5,000 per concurrent position)
- Total deployed at peak: 2 positions × $5,000 = **$10,000** (10% of portfolio)

---

## Code

```bash
# Run combined analysis (loads from existing CSVs — instant):
PYTHONPATH=src python run_uvxy_combined.py

# Try different put delta:
PYTHONPATH=src python run_uvxy_combined.py --put-delta 0.35

# Try different wing width:
PYTHONPATH=src python run_uvxy_combined.py --wing 0.15
```

**Key files:**
- `run_uvxy_combined.py` — CLI runner (CSV-based, fast)
- `src/lib/studies/combined_study.py` — merge + analysis engine
- `uvxy_puts_20dte_spread25_2026-03-02.csv` — put trades (input)
- `uvxy_call_spreads_20dte_spread25_2026-03-02.csv` — spread trades (input)
