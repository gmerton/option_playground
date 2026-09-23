# HANDOFF — state of play as of 2026-09-23

For a session (or a person) picking this up cold. Everything here is the **why** and the **right now**;
the durable material lives in the files below. ⚠ Dated on purpose — the "Recently changed" and "In flight"
sections go stale fastest, so trust the files over this doc where they disagree.

## Read in this order

1. **`CLAUDE.md`** — architecture, data landmines, research conventions, working rules, hour-costing
   gotchas. Loaded automatically by every Claude Code session in this repo.
2. **`OPERATIONS.md`** — what to run and when. The repo has 230+ root scripts; only ~13 are things you run.
3. **`data/studies/TEST_INDEX.md`** — every test, its verdict, and §10 for the live queue. **Check this
   before proposing any study.** Most ideas have already been run, and several were declined for reasons
   recorded there.

## The one-paragraph version of the book

Research here is overwhelmingly **destructive** — it kills things. After a ledger-wide multiple-testing
correction (2026-09-22) exactly **one** bucket certifies: index premium selling in stress
(SPY bull put t 6.07, SPX condor t 5.21 — which are **one bet**, not two). The 10-day VRP is real
(+1.75 vol points, t 8.93, 17/17 years) but **30d and 90d clear nothing**. The equity breakout book
averages **+0.014R** and three independent angles now say it cannot be improved by mechanical selection.
The measured leak is the **entry**: the breakout buys 2.6 ADR higher than a random later entry in the same
name. Expect nulls; treat a positive as suspect until it survives real fills and a correction.

## Recently changed — live, and not obvious from the code

* **Universe switched to INT** (Trend Template ∩ Ariel's momentum scan), 98 → 50 names. TT alone does not
  select (20d excess t 1.00) and its edge over a same-name-later control is negative. ⚠ INT encodes Ariel's
  *published rule*, not his *practice* — every mega-cap he actually watches fails his own ≥70%-off-low
  criterion. The queued Ariel criterion ablation should run before anyone calls INT "Ariel's universe".
* **`prev_green` removed** from the watchlist Potent gate — untested, NULL, and it was discarding 46.5% of
  candidates. Expect a wider nightly list than the historical ones.
* **Trend Template: two criteria retracted** as *logically redundant* (close>150SMA and close>200SMA are
  entailed by the others). The rest are underpowered, not proven useful.
* **CI/CD now exists.** Four pipelines, all path-filtered so research commits don't redeploy production:
  `preferred-list-refresh`, `preferred-breakout-scan`, `journal-site`, `options_toolkit`.
* **The journal site's reviews page is split** into a 13 KB presentation shell + a data JSON. Cosmetic
  changes deploy on commit via the `journal-site` pipeline. ⚠ `summary.html` and `alerts.html` still
  inline their data and remain local-build-and-deploy.
* **A stale-list overwrite was killed twice over** — the `aws s3 cp data/preferred_tickers.txt` line is out
  of `buildspec_breakout.yml`, *and* the IAM permission that allowed it is stripped from the role. The
  preferred list is **S3-owned**; `data/preferred_tickers.txt` is a historical artefact. Never write it.

## In flight — open decisions, nobody has said no

* **Reclaim vs pullback-low entry** (TEST_INDEX §10) — the cleanest open question on the book. Three
  creators independently describe our entry finding with the *opposite sign*: they buy the reclaim of the
  pre-pullback high, our tested arm buys the lower price. Nobody has tested their version.
* **The 620 setup** — unparked; the "not enough minute data" objection was stale (the cache is 192 tickers
  × 166 sessions). Prior is low: Stage A found every intraday arm ≈ a random later minute.
* **UR/FBO stop floor** — a 0.60 ADR floor was adopted for ORB9 alerts only. UR and FBO alerts still emit
  sub-0.5-ADR stops (0.35 and 0.48 on 2026-09-22, both losses). Re-run the floor study on those types.
* **Alerts → end-of-day only** — the owner wants to de-emphasise intraday alerts. Not yet implemented.
* **`journal_campaigns` and spread rolls** — he rolled several spreads across expiries on 9/22; whether
  the campaign keying threaded them correctly is unverified.
* **Defer the heavy imports** in `run_trade_review_pages.py` so the journal-site build stops needing a
  database driver to write a static file.

## Known broken, deliberately not fixed

* **`options_toolkit` pipeline has failed every run since at least 2026-09-09** (`exit status 254`). Its
  build role has no `lambda:` permission. The target Lambda has **zero invocations in 30 days and no
  resource policy**, so nothing can even invoke it. The recommendation is to disable the trigger rather
  than fix it — a pipeline that always fails trains you to ignore pipeline failures.

## Where the live numbers are — do not trust any copy

Positions and NAV: query IBKR live (TWS on 7496). The `journal_open_positions` snapshot is a session
behind. Stops in this repo are computed at **1 ADR below the current close** — the tested "disaster stop",
the best intraday-executed variant — and are recomputed, never stored.
