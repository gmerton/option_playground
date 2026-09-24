# tastylive KB

Skeptic-default reviews of tastylive / tastytrade research segments. The house style there is mechanical rules
(45 DTE, 50% take, 21-DTE management, high IV rank) backed by in-house studies. Those studies are usually priced at
mid and give no test statistic, so each entry here checks what the study actually compared.

## Leaderboard

| date reviewed | segment | claim | score | tested? | notes |
|---|---|---|---|---|---|
| 2026-09-15 | "Double calendar vs iron condor" (2022-10) | double calendar for earnings: short the inflated weekly, long the back cycle | 3/5 education, 1.5/5 as a trade | Earnings-placement cut **RETRACTED 2026-09-20** (path-truncation bug; TEST_INDEX §3) | [review](dcal_vs_iron_condor_2022-10_review.md) |
| 2026-09-23 | Julia Spina, "We Studied 539 Zero-DTE Iron Condors. The PDT Rule Was Costing Traders $166 a Trade." (2026-06-08, UIxluRMfh80) | managing 0DTE 20Δ condors (50% target / credit stop) saves $166 per winner, $93 per loser, halves the SD of P&L | **2.5/5** | **Not replicable on v3** (EOD only; 0DTE rows exist only at expiry). The PDT workaround (prior close → settlement) = our 1-day SPY fly: 0.0% every day, **+5.8% t 3.4 on positive-gamma days only**. The managed-vs-held result is path-conditioned, never reports either arm's own mean, and the variance cut is mechanical | [notes](videos/2026-06-08_UIxluRMfh80/notes.md) |
| 2026-09-24 | "Why 21 DTE May Change How You Manage Options" (2026-02-18, xccHQzd8fLk) | 20Δ/45-DTE SPY puts: closing at 21 DTE gives the lowest P&L volatility at "similar return"; 50% take best in a bull tape | **1.5/5** | Volatility half AGREES (sd $9.33 vs $17.09); **"similar return" CONTRADICTED** (21-DTE − hold −$0.52/share, t −2.42; worse per day held, SPY subset same sign). No n, no period, mid | [notes](videos/research/2026-02-18_xccHQzd8fLk/notes.md) |
| 2026-09-24 | "Why Volatility Gets 42% Worse the Longer You Hold Your Strangle" (2026-03-10, wkYzOi4G0Vc) | strangle P&L volatility grows with time held, faster near the money → manage at 21 DTE | **2/5** | True but mechanical; exploratory check on the FIX-1 CSV: 21-DTE close cuts per-share sd 45% (IQR/MAD and both halves agree; 2024 ratio 1.36 is the exception); **lower variance is not higher expectancy** (mean/sd +0.014 held vs −0.032 managed) | [notes](videos/research/2026-03-10_wkYzOi4G0Vc/notes.md) |
| 2026-09-24 | "How to Manage Strangles", Anatomy of a Trade (2023-07-01, kPco6uly26E) | rebalance at 50–70 net delta, roll untested side, go inverted → a 33% move scratches | **1.5/5** | One hindsight-picked ROKU trade, no costs, dollar figures don't reconcile to one lot. Delta-band rebalancing UNTESTED; "stay small" AGREES (size is the only non-inverted tail lever) | [notes](videos/research/2023-07-01_kPco6uly26E/notes.md) |
| 2026-09-24 | "How I Would Manage a Short Strangle Moving Against Me" (2023-05-09, FfEyv9Dz7vY) | untested → do nothing; tested → roll out in time; ITM → partial inversion | **1.5/5** | Hypothetical framework, no study ("no clear-cut winner"). Do-nothing AGREES with hold > 21-DTE close; rolling / inverting UNTESTED with a negative prior; entry is an earnings strangle (closed cell, −0.428% at the bid) | [notes](videos/research/2023-05-09_FfEyv9Dz7vY/notes.md) |
| 2026-09-24 | Jim Schultz, "Short Strangles vs Iron Condors, and When to Use Each" (2026-07-28, rF0baGqUk30) | strangles for full theta and room to adjust; condors = defined risk for ≤$25k accounts | **2/5** | Margin/tail trade-off and account-size rule sound as risk advice; no expectancy claim and neither earns off-index here; **wing friction never mentioned** (spot check: ~10% of credit strangle vs ~40% condor = the Davis mechanism); "less credit" is per contract, not per $ of buying power | [notes](videos/research/2026-07-28_rF0baGqUk30/notes.md) |

## Cross-references

- tastytrade's 21-DTE management rule was tested directly: ~~PASS as an exit (paired +$1.53, t 4.26) on a trade that
  loses in both arms~~ (corrected 2026-09-24, FIX-1: original run dropped worthless-expiry winners). Fixed: **NULL on return, leaning INVERTED** (21-DTE close − hold −$0.52/share,
  t −2.42; hold +$0.23, 21-DTE −$0.29), a **risk reducer only** (sd $9.33 vs $17.09, worst −$291 vs −$617)
  (TEST_INDEX §1, `exit_21dte_2026-09-23_fixed.csv`).
- Tom Sosnoff's 45-DTE / 20Δ strangle and the IV-rank vs credit/width sort: TEST_INDEX §1 and §9.
