# neurotrader KB

YouTube channel on quant and algorithmic strategy development in Python, mostly crypto (BTC/ETH hourly). Code is
public (github.com/neurotrader888). Method content leans heavily on Timothy Masters's books. Skeptic-default scoring
like every KB here. Reviewed so far for **METHOD** yield, not strategy claims.

`videos/<date>_<id>/` holds `transcript.txt` (`en-orig` auto-captions, timestamped), `meta.json`, `notes.md`.

| video | date | verdict |
|---|---|---|
| [How I Develop Trading Strategies: Permutation Tests](videos/2025-03-03_NLBXgSmRBgU/notes.md) | 2025-03-03 | **3.5/5 as METHOD · no strategy to test.** Four steps: in-sample excellence, in-sample MCPT (re-optimise on 1,000 bar permutations, p < 1%), walk-forward, walk-forward MCPT (his own Donchian example fails at p 22%). ⭐ New for us: **put the optimiser inside the null** (best-of-grid on permuted data vs best-of-grid on real data), which prices the parameter search we currently charge with a guessed Šidák k. ⚠ His bar-shuffle null destroys vol clustering and the cross-section and tests "any structure", not "beats the control", and he uses no costs. Proposal in the notes: **permute signal/control labels within our matched strata**, plus a paired edge-t fix to `pattern_test` (~2–2.5 days, serves method-queue #2) |
| [Using Trade Dependence to Improve the Donchian Breakout](videos/2023-06-26_BM3KZPg6zic/notes.md) | 2023-06-26 | **3/5 as METHOD · no new test.** Runs test on win/loss signs (z 2.7); on a stop-and-reverse Donchian, trades after a LOSER beat those after a winner at every lookback (the Turtle rule). No costs, BTC only, partly mechanical in an always-in system. → amends the queued adaptive-trader sim: runs test first, add the skip-after-a-winner arm |
| [Do Moving Averages Actually Work as Support and Resistance?](videos/2023-02-07_3zI_l_P-lF8/notes.md) | 2023-02-07 | **2.5/5 · no new test.** Band-exit bounce/penetration scorer (Osler 2000); 64% bounce vs ≤ 54% on permuted paths. ⚠ The return-shuffle null also kills trend persistence, so it can't separate MA-watching from momentum; a bounce rate isn't a return. Tradeable form = our EMA-pullback entry, already weaker than the breakout |
| [Self-Exciting Behavior and Detecting the End of Price Trends](videos/2023-04-18_wdsiZBIhAFw/notes.md) | 2023-04-18 | **3/5 · ⭐ one new test QUEUED.** Hawkes-process volatility-decay exit; 25/25 parameter cells PF > 1 but gross, BTC, beta-heavy, and the exit is never isolated. New axis for us (every exit tested so far is price-based) → vol-decay exit vs the 20-EMA trail on precision-tier breakouts, paired, % return |

## Follow-ups

- The design proposal in the notes (items A/B/D) is a candidate implementation of method-queue #2 (parameter-neighbourhood
  robustness). Not queued in TEST_INDEX by this review; the owner decides.
