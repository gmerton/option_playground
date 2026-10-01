# HANDOFF — state of play as of 2026-09-30

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

Research here is overwhelmingly **destructive** — it kills things. Since the 2026-09-25 top-down audit (TEST_INDEX §0)
**nothing was certified as a strategy** until 2026-09-30, when Gabe added a REPLICATION track for published premia
(CLAUDE.md) and 12-1 momentum certified under it. The index stress put sale, the old "one certified bucket", was PARKED on
2026-09-28 because 60–80% of its P&L is beta (the post-selloff rebound) and the rebound is absent 1990–2009. What is
live is small and forward-tested:
* **Calm-regime SPY weekly put** (Fridays, CALM & GEX > 0, 7-DTE 5Δ, hold to expiry; t 7.14 excess over beta,
  replicates on QQQ) — LIVE at 5Δ × 1 contract, desk step 0b prints `LIVE ACTION`.
* ⭐ **12-1 momentum sleeve — CERTIFIED (replication track, 2026-09-30), the first certified strategy** (survivorship-free,
  t_NW 2.93, 12/16 yrs) — `run_momentum_screener.py`, first formation 2026-09-30.
* **GEX regime** is a certified *mechanism* (not a trade); the 1-day 2× fly and the long straddle are paper/token only.

The house breakout is **uncertified selection, trade small**. The measured leak is the **entry**: the breakout buys
2.6 ADR higher than a random later entry in the same name. Expect nulls; treat a positive as suspect until it
survives real fills, a control that holds the confound fixed, and a correction.

## Recently changed — live, and not obvious from the code

**2026-09-30 (8 tests, all NULL / UNDERPOWERED; rows in TEST_INDEX, docs in `data/studies/*_2026-09-30.md`):**
* **Exits — keep the 20-EMA trail.** RS-loss exit NULL (differs on 1.1% of trades); swing-low trail NULL
  (exposure-matched +0.44pp t 1.71, width-fragile). ⚠ Pattern now seen four times (STOP_ONLY, RS-only, swing-low,
  vol-decay): any LOOSER exit wins ~+0.8pp raw, ~half of it beta, residual t < 2. Always run the beta × SPY
  exposure-matched control on an exit test (`run_trail_cost_exposure.py` / `run_swing_low_trail.py`).
* **Selection/universe:** CAN SLIM "C" EPS growth on INT NULL (wrong sign, thin); laggard-breakdown contagion NULL
  (the "contagion" is a shared day-0 industry shock, no follow-through).
* **Intraday:** right side of the V on the SPY/QQQ gap fade 2007–26 NULL, lean INVERTED (the turn is paid for in
  price); FBO lower-high gate NULL, his literal sequence INVERTED → FBO stays retired.
* **Calendar:** quarter-end turn and the quarter-end VIX "V" (JHEQX roll) both UNDERPOWERED; his up-quarter
  mechanism runs the wrong way.
* **Journal (conformance only):** loss-limit arm 0 NULL — no tilt after losses (k≥2 +$12, t 0.60); Cameron's
  "80% double the loss" = 25% here; **size creeps with the loss streak (0.93× → 1.19× median, t 1.66) — lean only**.
  Same-day round trips 336 of 585 episodes since 8/03, −$11.6k at 21% win (Gabe declined a desk tally 9/30; keep
  flagging it in replies).
* **KB:** Karsan quarter-end 2/5, Theta Profits "TOS" put seller 2/5 (no new test), Ariel on TraderLion 2.5/5 (his
  ADR ≥ 3% floor is the one AH-encoding gap that could matter). 1-min SPY/QQQ RTH history 2007→ lives in
  `data/cache/intraday_hist/` — use it for any index intraday test.

**2026-09-25 → 09-29 (see TEST_INDEX §0 and the dated rows):** top-down audit (supersedes the 9/20 book table);
audit step 3 list A complete (QQQ 2× fly re-cut SUPPORTED t 3.64; activity gate + HYB-A REVERSED in the 2010–19
holdout; paid-to-wait IV gate NULL → `run_putspread_scan.py` has no tested edge; Sleeping Giants retired; event
convexity NULL); stress put sale PARKED (beta); calm weekly put CERTIFIED-CANDIDATE → live 5Δ × 1; momentum
sleeve built; Ariel-criterion ablation on INT ran 9/28 (a3 ≥ 2M sh/day ADDS, t −4.24 when dropped); vanna/charm
flows NULL; earnings ramp at 30–45 DTE FAIL as a trade; IPO lockup NULL.


**2026-09-24 (one long session; details in TEST_INDEX / OPERATIONS):**
* **Ops:** 74 dead scripts → `scripts/archive/`; `options_toolkit` (Lambda + CodeBuild + pipeline) deleted; **CI owns
  Lambda code, `deploy_*_lambda.sh` own infra** (`deploy/code_guard.sh`, one module list per Lambda); the
  undocumented **`options-daily-updater`** ECS task (v3's nightly feed) is now in OPERATIONS/CLAUDE; the desk reads
  the Lambda's EOD scan after 19:15 ET, sources `~/.trading_env`, defaults `AWS_PROFILE`; the liquid-panel builder
  fills yfinance-dropped sessions from Polygon (9/22 had 181/1726 names); journal cache backup now automated;
  **`universe_focus.txt` retired** — the alert universe is always the auto union (incl. open holdings).
* **Research verdicts:** FDX-template breakdown short NULL; long-INT/short-DIST spread UNDERPOWERED and not a hedge;
  **sector-momentum 12-1 spread = the first genuine book hedge** (NULL return, cuts maxDD 4–5 pts, costs ~0.12
  Sharpe — adoption is Gabe's preference call); ADR floor and in-play gate NULL; distribution-day count NULL on
  SPY/QQQ/IWM (a lagging vol gauge; `market_conditions.py` now shows it as a percentile).
* **Corrections:** the ETF-roster put leg is net-negative at real fills (+5.70% was gross); SPY/IWM calendar
  "Tier B" superseded; "69.8% better held" is the long straddle's stop, not a short-premium roll (7 citations fixed).
* **GEX paper trade logged its first signal + fly on 2026-09-24** (positive gamma at 15:37 ET).
* KB: tastylive list done except the 0DTE cluster; OptionsPlay Tiers 4–5 done; new `data/al_brooks/`;
  `data/studies/dealer_gamma_primer.html` (GEX / vanna / charm primer).

* **Universe switched to INT** (Trend Template ∩ Ariel's momentum scan), 98 → 50 names. TT alone does not
  select (20d excess t 1.00) and its edge over a same-name-later control is negative. ⚠ INT encodes Ariel's
  *published rule*, not his *practice* — every mega-cap he actually watches fails his own ≥70%-off-low
  criterion. (The Ariel criterion ablation ran 2026-09-28: a3 ≥ 2M sh/day ADDS, a1 leans ADDS — TEST_INDEX §4.)
* **`prev_green` removed** from the watchlist Potent gate — untested, NULL, and it was discarding 46.5% of
  candidates. Expect a wider nightly list than the historical ones.
* **Trend Template: two criteria retracted** as *logically redundant* (close>150SMA and close>200SMA are
  entailed by the others). The rest are underpowered, not proven useful.
* **CI/CD now exists.** Three pipelines, all path-filtered so research commits don't redeploy production:
  `preferred-list-refresh`, `preferred-breakout-scan`, `journal-site`. (A fourth, `options_toolkit`, was deleted 2026-09-24.)
* **The journal site's reviews page is split** into a 13 KB presentation shell + a data JSON. Cosmetic
  changes deploy on commit via the `journal-site` pipeline. ⚠ `summary.html` and `alerts.html` still
  inline their data and remain local-build-and-deploy.
* **A stale-list overwrite was killed twice over** — the `aws s3 cp data/preferred_tickers.txt` line is out
  of `buildspec_breakout.yml`, *and* the IAM permission that allowed it is stripped from the role. The
  preferred list is **S3-owned**; `data/preferred_tickers.txt` is a historical artefact. Never write it.

## In flight — open decisions, nobody has said no

* **(2026-09-24) Waiting on Gabe:** ETF-roster / Friday-screener book status; whether to forward-track a 25%
  sector-spread hedge sleeve; forward lockbox for the RV spread; `run_putspread_scan.py` fixes (mid pricing,
  hard-coded 10/16 expiry, up/B+ veto not enforced, no earnings check) + its universe (SETUP vs leaders).

* **Tomorrow (2026-10-01) AM:** first momentum-sleeve formation — run `run_momentum_screener.py` (OPERATIONS 7b).
* **Fridays from 2026-10-02:** calm weekly put LIVE (5Δ × 1) + paper log; run the desk at/after 15:30 ET.
* **The 620 setup** — the last untested intraday entry with a spec (192 tickers × 166 sessions of 1-min cache).
  Prior is low: Stage A found every intraday arm ≈ a random later minute, and FBO / the V test (9/30) agree.
* **Strongest bounce since the correction low** (§10) — specced, ~60 episodes, UNDERPOWERED at best.
* ~~Reclaim vs pullback-low~~ (NULL 9/23), ~~UR/FBO stop floor~~ (closed 9/23, floor stays ORB9-only),
  ~~Ariel criterion ablation~~ (ran 9/28) — done; listed here earlier as open.
* **Alerts → end-of-day only** — the owner wants to de-emphasise intraday alerts. Not yet implemented.
* **`journal_campaigns` and spread rolls** — he rolled several spreads across expiries on 9/22; whether
  the campaign keying threaded them correctly is unverified.
* ✅ **RESOLVED 2026-09-24:** `universe_focus.txt` was retired (git history keeps it); `lib.alerts.universe` now
  always unions preferred list + open holdings (Flex snapshot, one session late) + the evening scans + the EOD
  monitor roster + plan/creator lists no older than 7 days + `universe_extra.txt`, minus `universe_exclude.txt`.
  Original note: **The live-alert universe is fed by stale hand-kept inputs** (found 2026-09-23, parked by the owner to
  revisit). `start_alerts.sh` streams `universe_focus.txt` (last edited 9/14) + the newest `trade_plan_*.md`
  (9/09) — `lib.alerts.universe` only unions them, it never refreshes them. So the evening desk's new names
  (9/23: OKTA, CRWD, TEAM, FSLY, CNH…) are not watched unless added by hand. Decide: auto-feed the focus file
  from the Adhikary scan / breakout scan / clusters, or keep it curated and add a staleness warning.
* **8 stock reviews still show "open" for names no longer held** (parked by the owner 2026-09-23 to clean
  up later). The new `close_out_stock_reviews()` in `run_build_reviews.py` closed 21 stuck rows but
  deliberately skips what it can't match unambiguously: **HALO 9/18 and FTNT 8/12** (several cycles fit the
  review) and **CRWD, NTAP, ZM, RY, RVMD, WDCX** (early-Aug `(open)` rows with no `@price` in the label and
  no matching flat-to-flat cycle in `journal_trades`). Fix by hand: find the sell in `journal_trades` or the
  owner's recollection, then `UPDATE journal_trade_reviews` by id (exit_date, realized_pnl, drop the
  `open_position` tag), re-render with `run_trade_review_pages.py`, deploy. Do **not** re-run the review
  builder over past dates.
* **Defer the heavy imports** in `run_trade_review_pages.py` so the journal-site build stops needing a
  database driver to write a static file.

## Known broken, deliberately not fixed

* ✅ **RETIRED 2026-09-24 (Gabe's OK):** the `options_toolkit` pipeline, the `options_toolkit_prod` CodeBuild project and
  Lambda, and `buildspec.yml` were deleted; definitions saved locally in `data/backups/aws_retired_2026-09-24/` (not committed).
  History: the `options_toolkit` pipeline had failed every run since at least 2026-09-09 (`exit status 254`). Its
  build role has no `lambda:` permission. The target Lambda has **zero invocations in 30 days and no
  resource policy**, so nothing can even invoke it. The recommendation is to disable the trigger rather
  than fix it — a pipeline that always fails trains you to ignore pipeline failures.

## Where the live numbers are — do not trust any copy

Positions and NAV: query IBKR live (TWS on 7496). The `journal_open_positions` snapshot is a session
behind.

**Stops — two of them, and they execute differently.** Full definitions in
**`data/studies/stop_definitions.md`** (canonical; fix any doc that disagrees with it).
* **Disaster stop — 1 ADR below the current close.** The best *intraday-executed* variant: **rest it with
  the broker.** Its job is the crash, not the noise; it fires 4–6% of days. Recomputed daily, never stored.
* **Tight stop — the session low (0.4–0.8 ADR). Judged on the CLOSE.** Resting this one intraday is the
  thing the entry study rejects.

⚠ Quoting the close-judged rule against the 1-ADR level is a mistake that was actually made on 2026-09-23.
"Hard stop" is the trade reviewer's retrospective grading criterion, not a live level, and **"emergency
stop" is not a term in this repo**.
