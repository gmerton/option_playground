# tastylive KB

Skeptic-default reviews of tastylive / tastytrade research segments. The house style there is mechanical rules
(45 DTE, 50% take, 21-DTE management, high IV rank) backed by in-house studies. Those studies are usually priced at
mid and give no test statistic, so each entry here checks what the study actually compared.

## Leaderboard

| date reviewed | segment | claim | score | tested? | notes |
|---|---|---|---|---|---|
| 2026-09-15 | "Double calendar vs iron condor" (2022-10) | double calendar for earnings: short the inflated weekly, long the back cycle | 3/5 education, 1.5/5 as a trade | Earnings-placement cut **RETRACTED 2026-09-20** (path-truncation bug; TEST_INDEX §3) | [review](dcal_vs_iron_condor_2022-10_review.md) |
| 2026-09-23 | Julia Spina, "We Studied 539 Zero-DTE Iron Condors. The PDT Rule Was Costing Traders $166 a Trade." (2026-06-08, UIxluRMfh80) | managing 0DTE 20Δ condors (50% target / credit stop) saves $166 per winner, $93 per loser, halves the SD of P&L | **2.5/5** | **Not replicable on v3** (EOD only; 0DTE rows exist only at expiry). The PDT workaround (prior close → settlement) = our 1-day SPY fly: 0.0% every day, **+5.8% t 3.4 on positive-gamma days only**. The managed-vs-held result is path-conditioned, never reports either arm's own mean, and the variance cut is mechanical | [notes](videos/2026-06-08_UIxluRMfh80/notes.md) |

## Cross-references

- tastytrade's 21-DTE management rule was tested directly: ~~PASS as an exit (paired +$1.53, t 4.26) on a trade that
  loses in both arms~~ (corrected 2026-09-24, FIX-1: original run dropped worthless-expiry winners). Fixed: **NULL on return, leaning INVERTED** (21-DTE close − hold −$0.52/share,
  t −2.42; hold +$0.23, 21-DTE −$0.29), a **risk reducer only** (sd $9.33 vs $17.09, worst −$291 vs −$617)
  (TEST_INDEX §1, `exit_21dte_2026-09-23_fixed.csv`).
- Tom Sosnoff's 45-DTE / 20Δ strangle and the IV-rank vs credit/width sort: TEST_INDEX §1 and §9.
