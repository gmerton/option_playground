# More Tom: "How Far Out of the Money You Should REALLY Sell" (u-86ZHe-d5s) -- review 2026-09-25

**Score 2/5.** A 670-word Q&A clip with a product plug at the end. One concrete, testable rule; the rest is feel.

| # | claim | verdict |
|---|---|---|
| 1 | **Low vol -> sell further OTM (~16 delta) and further out in time; high vol -> move in (20-25 delta)** | **Untested as a delta x vol interaction.** Related evidence: vol level predicts put-spread ROC (vix_pct t +6.54), and the certified SPY cell is 0.25/0.15 with VIX >= 20, which matches his high-vol half. Nobody has shown that going to 16 delta in LOW vol beats 25 delta. **Testable on the cached data** (see below). |
| 2 | "Winners are way more important than collecting premium" (favour win rate over credit) | **CONTRADICTED.** Across our spreads the win rate FALLS (79.6 -> 75.7%) as net ROC RISES (-2.96 -> +4.07%, t 3.74). Today's call-side delta sweep: the 91%-win cell still lost money. Win rate is not the objective. |
| 3 | "Too many stocks moving outside the expected move, almost daily" | **Against the average evidence.** Implied > realized in 17 of 17 years (10d VRP +1.75 vol pts, t 8.93); single names realise above implied only 25-29% of the time. True in the fat tails, false as a base rate. |
| 4 | Small account, meaningless profits -> a strangle instead of a condor to raise profit potential | This is **more risk**, not more edge (the unhedged wing). It contradicts his own "size is how everyone blows up". |
| 5 | Premium relative to buying power decides whether a trade is worth it | Reasonable, but credit/width turned out to be beta when compared with delta-matched stock (OptionsPlay spec -2.68pp, t -2.21). |

**Test for #1, if wanted (not run):** bull put spreads at short delta {0.16, 0.20, 0.25, 0.30} x the VIX tercile at entry,
13 underlyings 2012-2026 from the leg_in cache (puts down to -0.60 delta are already pulled), real fills. The claim is the
INTERACTION: the 16-delta minus 25-delta difference must be positive in low VIX and negative in high VIX.
