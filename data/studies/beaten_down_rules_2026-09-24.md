# A second rule set for beaten-down names on the rise (2026-09-24)

Gabe: consider rules for badly beaten-down stocks on the rise (the Aug-2026 crypto surge; Martin/Tito long bases).
Script `run_beaten_down_rules.py` (pre-registration in the docstring); log `data/studies/logs/beaten_down_rules.log`;
crypto forensics `data/studies/logs/crypto_breakout_forensics_2026-09-24.log`; episodes `beaten_down_group_rebound_2026-09-24.csv`.

**Forensics (hypothesis only, n = 1):** the crypto surge (group +18.6% in 10 sessions, 08-13 → 08-27) came from a
median −54% drawdown, below the 200-day, with falling 50-days — NOT a base breakout (2 of 17 broke a 6-month high).
The group signal was its equal-weight index reclaiming the 50-day as in-group breadth (% > 20 EMA) went ~25% → 65%.

**Test 1 — long-base breakout** (≥ 30% below the 3-year high, no new 6-month high for 3+ months, first close above it
on RVOL ≥ 1.5, upper-half close, stack ≥ 5; pattern harness, close entry, hold 60, 2012 →): **NULL.** 120 signals /
100 names; house ema20 arm −0.10R; best-arm paired edge **t +1.02 vs `post`, +0.46 vs `xname`**, p_search 0.37 / 0.62.
Rare (~9 a year) and no edge over a random later day or a random other name.

**Test 2 — group washout rebound** (industry median member ≥ 40% down, group EW index first close above its 50-day in
40+ sessions, ≥ 60% of members above the 20 EMA after ≤ 35%): **NULL / UNDERPOWERED.** 23 episodes / 12 groups;
40d ADR-matched excess **−0.27pp, t −0.10**, 43% positive, halves −8.2 (n 4) / +1.4 (n 19); vs the same basket from a
random later session −3.65pp (t −1.00). Broken tape (breadth < 40) n 5: +1.75 (t 0.67) — the crash-leader direction,
too few to read. The two **crypto** episodes were the best of the 23 (2024-09 +26.8pp, 2025-04 +8.4pp); the Aug-2026
episode is too recent to score (needs 40 sessions).

**Reading.** Neither rule set selects. What worked in crypto looks group-specific (a BTC-driven basket), not a
general "beaten-down and rising" rule — the other 21 group rebounds averaged about zero. Consistent with the
crash-leader study (a regime bet, not selection) and industry rotation (not front-runnable).
**Possible follow-up (not queued):** crypto names as a BTC-conditioned basket — but that is BTC beta until shown otherwise.
