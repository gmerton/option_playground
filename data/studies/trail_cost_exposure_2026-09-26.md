# Does the 20-EMA trail cost money? STOP_ONLY vs BASE, exposure held fixed (2026-09-26)

`run_trail_cost_exposure.py` (pre-registered in its docstring, committed before the run). Log
`logs/trail_cost_exposure.log`; trades `logs/trail_cost_exposure_{precision,generic}.parquet` (gitignored).

## Verdict: NULL (primary not met) · MECHANISM: ~3/4 of the lead was market exposure · keep the trail

The lead from the vol-decay run (raw STOP_ONLY − BASE +1.28pp, t 3.6 precision / +1.25pp, t 5.2 generic) reproduces
exactly. But once BASE's freed capital is parked in beta × SPY until STOP_ONLY exits, most of it goes away:

| precision pool (1,960 trades) | pp per trade | t |
|---|---|---|
| raw STOP_ONLY − BASE (the lead) | +1.28 | +3.62 |
| **STOP_ONLY − BASE+FILL(beta) — PRIMARY** | **+0.30** | **+1.16** (halves +0.49 / +0.18, 5/8 years) |
| STOP_ONLY − BASE+FILL(beta = 1) | +0.62 | +2.11 |
| both SPY-hedged on their own windows | +0.33 | +1.27 |

Generic pool (7,655 trades): primary +0.40pp, t 2.18 (halves +0.69 / +0.22); beta = 1 fill +0.66pp, t 3.15; raw +1.25pp.

## Read
- **The raw lead was mostly beta.** STOP_ONLY holds 22.8 days vs 13.8, in names with median beta 1.38, in a rising
  sample. Filling BASE's idle days with the same beta in SPY recovers ~0.98 of the 1.28pp.
- What's left (+0.3–0.4pp) leans toward holding longer and is consistent in sign across pools, but it misses the bar
  (t 1.2 precision, 2.2 generic; 5 of 8 years). Not certified; not worth changing the exit for.
- The trade-off the trail buys is visible: STOP_ONLY's top decile is fatter (+72% vs +55%) but its win rate is lower
  (24% vs 31%) and its p5 worse (−12.3% vs −10.8%), and it ties up capital ~65% longer. The trail frees capital that
  can earn the market; on this evidence that's roughly a wash.
- Consistent with the O'Neil 8-week hold NULL (2026-09-22).

## Consequences
- Keep the 20-EMA trail as the house exit.
- The queued "exit speed × gamma" test keeps BASE as its baseline, as pre-registered.
- METHOD: any exit comparison where the arms hold for different lengths needs an exposure fill; raw % return
  flatters the longer hold in a rising sample.
