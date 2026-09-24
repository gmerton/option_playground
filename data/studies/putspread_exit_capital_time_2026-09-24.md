# ETF bull put spreads: profit-take vs hold, Friday vs any-day entry, on return per capital-day (2026-09-24)

**Question (Gabe):** hold-to-expiry leaves capital tied up; if a spread earns 50% of its premium in a day, closing
it has a huge annualised ROC. Should we optimise for return on capital-time rather than dollars per trade? And why
only enter on Thursday/Friday?

**Scripts:** `run_putspread_exit_capital_time.py` (pre-registration in the docstring; v3 pull, trade build, per-entry
arms, primary, weekday) and `run_putspread_exit_phase_slots.py` (the capital-time slot simulation, phase-averaged —
supersedes the single-phase "SECONDARY" table in the main log, see §3). Logs:
`data/studies/logs/putspread_exit_capital_time.log`, `..._phase.log`; trades `..._trades.parquet`.

**Setup.** 20-ETF in-book roster, puts from `silver.options_daily_v3` **unfiltered** (zero bids kept — the
`options_cache` source used by every earlier roster study drops them, which suppresses take-profit fills).
Every trading day 2018-01 → 2026-01 (expiry ≤ 2026-03-20): expiry nearest 45 DTE (40–50), short ≈ −0.35Δ, long
≈ −0.25Δ. House fills on every traded leg using **that day's** bid-ask (25% of the spread + $0.65/contract);
held spreads settle at intrinsic vs the raw spot recovered from the chain (median error vs raw close 0.03%).
Split guard drops trades spanning a split (SOXX 2024-03, USO 2020-04, XLE/XLK/XLU 2025-12-05; 63 entries).
29,000+ entries; every entry run through six exit arms (paired). ROC on capital = width − credit.

## 1. Per trade, Friday entries (n 7,494)

| arm | gross % | **net %** | t | win % | taken % | days |
|---|---|---|---|---|---|---|
| HOLD to expiry | +3.99 | **−1.37** | −0.55 | 73 | 0 | 42 |
| T25 (close at 25% captured) | +4.69 | −4.15 | −2.86 | 84 | 82 | 21 |
| **T50 (the live roster rule)** | +6.28 | **−2.78** | −1.44 | 80 | 75 | 27 |
| T75 | +7.86 | −1.54 | −0.66 | 76 | 66 | 33 |
| FAST50 (50% within 5 sessions, else hold) | +4.36 | −1.49 | −0.63 | 74 | 8 | 39 |
| ANN100 (close at ≥100% annualised ROC) | +4.69 | −4.33 | −3.75 | 87 | 84 | 17 |

**PRIMARY (pre-registered): T50 − HOLD = −1.42pp, t −1.77, halves −2.96 (t −2.5) / 0.00 → FAIL** (no significant
difference; the sign favours holding in 8 of 9 years).

**Mechanism — it is the cost of the second round trip.** At mid every take beats holding (T50 +2.3pp gross, T75
+3.9pp) — Gabe's intuition is right *before costs*. But entry friction alone is ~5.1pp of capital per trade and an
early close adds ~3.7pp more (gross−net: HOLD 5.1pp, T50 8.8pp). A held OTM spread expires for free.

## 2. The annualised-ROC idea, directly

ANN100 has the highest win rate (87%) and the shortest hold (17 days) and is the **worst** arm per trade (−2.96pp vs
HOLD, t −2.0) and per capital-year (§3, t −4.6 vs HOLD). High annualised ROC on a single trade is produced by
closing early, and every close pays the friction again; recycling the capital faster multiplies the friction
faster than it multiplies the premium. **INVERTED.**

## 3. Capital-time: one slot per ticker, re-deployed the next eligible session

⚠ The single-phase version in the main log is start-date dependent (one fixed chain of entry dates per ticker; its
Fri-HOLD +17%/yr came from a slot subset averaging +2.4%/trade vs −1.4% for all Friday holds). Averaged over 30
staggered start offsets:

| entry | exit | trades/yr | **net / yr** | gross / yr | worst month | t vs Fri-HOLD |
|---|---|---|---|---|---|---|
| Fri | HOLD | 7.1 | **−2.3%** (phase sd 12.8) | +36.7% | −56% | — |
| Fri | T50 (live) | 11.0 | −34.1% | +56.9% | −83% | −2.13 |
| Fri | T75 | 9.2 | −10.0% | +73.8% | −53% | −0.55 |
| Fri | FAST50 | 7.6 | −11.0% | +30.8% | −65% | −0.91 |
| Fri | T25 | 14.0 | −50.7% | +64.5% | −68% | −3.33 |
| Fri | ANN100 | 17.3 | −75.2% | +61.9% | −79% | **−4.60** |
| any | HOLD | 7.2 | −16.8% | +25.9% | −51% | −1.42 |
| any | T50 | 11.7 | −35.3% | +73.2% | −84% | −2.10 |
| any | ANN100 | 20.0 | −75.0% | +87.3% | −79% | **−4.42** |

Šidák bar for the 11 comparisons |t| ≥ 3.6: **ANN100 is significantly worse than holding (both entry rules)**;
nothing is significantly better than holding. Gross, the fast exits look like the best capital use in the book;
net, turnover is the loss. (Paired monthly t on phase-averaged series is somewhat optimistic; the ANN100 margin
is wide enough that it does not matter.)

## 4. Entry weekday — NULL

Mon–Thu vs the Friday of the same ticker-week, per trade: HOLD −0.29 / +0.28 / −0.29 / −0.05pp, T50 −0.15 / +0.48 /
−0.42 / −0.45pp; every |t| ≤ 1.14. At 45 DTE the entry weekday carries no information, so Friday is harmless — and
any-day entry does not raise return per capital-year either (§3: any-HOLD −16.8% vs Fri-HOLD −2.3%, t −1.4, within
the phase noise). The only thing daily entry changes is idle share (≈10% vs ≈16%), and idle capital is not the
binding constraint when the trade is net-negative.

## 5. ⚠ The bigger finding: the in-book put leg has no edge after costs

Roster-wide, every exit rule is net-negative or flat: HOLD −1.37%/trade (t −0.55), the live T50 −2.78% (t −1.44).
By year (HOLD net): 2018 −13.0, 2019 +9.3, 2020 +4.7, 2021 −0.3, 2022 −12.2, 2023 −6.5, 2024 +3.8, 2025 +8.4.
Only **GLD (+9.4), QQQ (+6.7), SPY (+5.2), XLU (+3.6), XLK (+3.2)** are positive held (ASHR −11, FXI −9, INDA −7,
EEM −6, XBI −6, TLT −6, XOP −5). This agrees in sign with the 2026-09-22 committed rebuild on `options_cache`
(T50 −6.78% net), whose log was never written up. The earlier "+5.70%/trade" roster headline was gross of costs.
The GLD/QQQ/SPY/XLK/XLU subset is selected **in-sample from this run** and is not evidence by itself.

**Caveats.** (1) The house cost model (25% of the quoted spread per leg) is the dominant term; on SPY/QQQ the real
fill may be better — the journal is admissible for *cost realism* and can check that. (2) EOD marks: a resting GTC
limit fills some takes intraday, so take arms are slightly understated — not enough to cover ~3.7pp. (3) The pull
drops rows with Δ < −0.85, so "path coverage" < 100% marks deep-ITM losers (corr with HOLD ROC +0.69), not data
gaps; no take could trigger on those days anyway.

## Verdicts

- **Take-profit vs hold (T50 − HOLD, primary): NULL** (−1.42pp, t −1.77; leans hold). YIELD MECHANISM: takes win
  at mid and lose at real fills — the second round trip.
- **Annualised-ROC exit (ANN100): INVERTED** (−4.60 t vs hold per capital-year).
- **Any-day vs Friday entry: NULL.**
- **The ETF roster put leg after costs: FAILS** (HOLD −1.37%, T50 −2.78% net) — the in-book status of the pair's
  put half needs a decision; this study does not make it.
