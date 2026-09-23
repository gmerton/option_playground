# neurotrader KB

YouTube channel on quant and algorithmic strategy development in Python, mostly crypto (BTC/ETH hourly). Code is
public (github.com/neurotrader888). Method content leans heavily on Timothy Masters's books. Skeptic-default scoring
like every KB here. Reviewed so far for **METHOD** yield, not strategy claims.

`videos/<date>_<id>/` holds `transcript.txt` (`en-orig` auto-captions, timestamped), `meta.json`, `notes.md`.

| video | date | verdict |
|---|---|---|
| [How I Develop Trading Strategies: Permutation Tests](videos/2025-03-03_NLBXgSmRBgU/notes.md) | 2025-03-03 | **3.5/5 as METHOD · no strategy to test.** Four steps: in-sample excellence, in-sample MCPT (re-optimise on 1,000 bar permutations, p < 1%), walk-forward, walk-forward MCPT (his own Donchian example fails at p 22%). ⭐ New for us: **put the optimiser inside the null** (best-of-grid on permuted data vs best-of-grid on real data), which prices the parameter search we currently charge with a guessed Šidák k. ⚠ His bar-shuffle null destroys vol clustering and the cross-section and tests "any structure", not "beats the control", and he uses no costs. Proposal in the notes: **permute signal/control labels within our matched strata**, plus a paired edge-t fix to `pattern_test` (~2–2.5 days, serves method-queue #2) |

## Follow-ups

- The design proposal in the notes (items A/B/D) is a candidate implementation of method-queue #2 (parameter-neighbourhood
  robustness). Not queued in TEST_INDEX by this review; the owner decides.
