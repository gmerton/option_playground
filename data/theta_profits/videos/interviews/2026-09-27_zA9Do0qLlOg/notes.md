# Theta Profits: "TOS" (The Option Seller), "Inside Her 5-Step Put Selling Strategy: 90% Wins in 502 Trades" (2026-09-27, 46 min)

_Reviewed 2026-09-30. The full write-up is [`strategies/put_sale_oversold_tos.md`](../../../strategies/put_sale_oversold_tos.md).
Transcript (`en-orig` auto) is in this folder with [mm:ss] stamps. Same anonymous guest as the 0DTE NQ/ES episode
(`2026-01-11_pP-gZCJq9aY`, 1.5/5)._

**Verdict 2/5.** Five steps:
1. a discretionary watchlist rebuilt twice a year;
2. a proprietary "oversold" band around a slow MA;
3. strike below the GEX put wall;
4. strike below the 6-month volume POC / support;
5. expiry copied from large ITM put-sale flow.

Execution: mostly put credit spreads 2–3 months out, a 40–50% early take, no stop, managed in expiry week.

- Defined risk, monthlies and no stop AGREE with our data. The 40–50% early take is NULL at house fills (t −1.77).
- The **dip event is NULL** (definition-fragile, t −4.22 vs +; market-vs-idio t 0.95).
- The **spread vehicle is beta** (vs delta-matched stock: −2.68pp t −2.21; −9.1pp t −3.21; +$7 t 0.26).
- **Post-dip IV richness FAILS** vs VIX-matched days.
- The **GEX put wall** as support/pin is NULL; ITM put-sale flow is unsignable on v3.
- The record (452/502 wins, $137k "per contract alerted", Aug 2025 →) has a win-rate denominator but **no risk
  denominator**. It covers one regime (her watchlist = the AI-semis leaders), and its pruned watchlist hides the
  names that broke.

No new test: every component is already in the ledger.
