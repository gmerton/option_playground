# High-volume return premium (Gervais–Kaniel–Mingelgrin 2001) on our liquid panel (2026-09-29)

## Pre-registration (written BEFORE the run; do not edit this section after the results)

**Why.** Gabe's question on volume narratives ("up on high volume = smart money"). Our tests of chart-level volume
stories are NULL (volume signature at lows 0/12; RVOL gates 0/9). The academic version with evidence behind it is
cross-sectional: stocks with unusually HIGH trading volume over a week outperform over the following month (visibility
/ attention), regardless of that week's return. Untested here.

**Data.** `liquid_panel_2009` (adjusted OHLCV, survivor panel; bias shared by both arms since this is a relative test).
Eligible: 50-day ADDV ≥ $50M, price ≥ $5. Formations: the last session of each calendar week, 2010-03 → 2026-06.
**Signal.** abnormal volume AV = shares traded over the formation week's 5 sessions ÷ (5 × mean daily shares over the 49
sessions before that week). **HIGH** = top decile of AV that week; LOW = bottom decile (reported).
**Outcome.** Close-to-close return from the formation close to session +20 (PRIMARY); +5 and +60 reported.
**Control.** Same-date eligible names in the same formation-week-return quintile × ADR tercile cell, excluding HIGH and
LOW names. Excess = signal return − cell mean. (Holding the week's return fixed is the key: high volume often comes with
a big move, and short-term reversal/momentum would otherwise masquerade as a volume effect.)
**PRIMARY.** HIGH +20 excess > 0, **t ≥ 3** on formation-date means (Newey-West 4 lags for the weekly overlap), both
halves (2010–2017 / 2018–2026) > 0, positive in a majority of years. Reported: HIGH − LOW; +5/+60; HIGH split by
formation-week return sign (up-week vs down-week high volume); absolute net of 10 bp/side.
Local, background run.
