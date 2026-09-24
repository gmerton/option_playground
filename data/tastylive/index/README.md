# tastylive channel index — prioritised for the Sosnoff-doctrine review (2026-09-23)

Built for Gabe's question: *understand Tom Sosnoff's strategies* ("no charts — sell volatility"). Source:
all 75 playlists of `@tastyliveshow`, flat-listed with yt-dlp (metadata only, no transcripts).

- `playlists_raw.tsv` — the 75 playlists.
- `playlist_videos_raw.csv` — 2,914 playlist entries.
- **`video_index.csv` — 2,596 unique videos**, scored and sorted: `video_id, title, duration, views, playlists,
  reviewed, score`.

⚠ **Coverage caveat:** a dozen playlists returned exactly **100** entries (Market Measures, Options Jive, Options
Trading Backtesting & Research, Trading Trends, Guest Interviews, tasty Originals, …). That looks like yt-dlp's page
cap, not the playlists' true size. For those shows the index holds the **latest ~100 episodes only**; older
Sosnoff-era episodes aren't in it.

⚠ **Only 4 titles name Sosnoff, and review found only 3 have him on camera** (C6vrj2zu6Hc doesn't) (70 match "Tom"/"Tony", mostly Tom Lee and Tom Preston). He left for Lossdog
(see `data/more_tom/README.md`). The recent catalogue is tastylive's research desk (Julia Spina et al.) testing *his
doctrine* — 45 DTE, 16–30Δ, 50% take, 21-DTE management, IV rank, sell after spikes — which is exactly what we want
to check against our ledger.

**Scoring (heuristic, for triage only):**
- +4 for a research show (Market Measures, Options Jive, Backtesting & Research, Best of Research 2025, The Math
  Check, Life Cycle / Anatomy of a Trade, strangle / condor / rolling / 0DTE / portfolio series, Calculated Risk,
  Signal vs Noise).
- Title keywords tied to his mechanics and our open questions: strangle, 45/21 DTE, IV rank / VIX, managing /
  50%, rolling, "we studied / backtest / N years".
- −3 for crypto / macro / chart-reading / beginner series; −4 for shorts (< 2 min).
- 48 videos score ≥ 9, 150 score ≥ 7.
- Only 2 were already reviewed: UIxluRMfh80 (539 0DTE iron condors, 2.5/5) and -TsOWo9XFEo (double calendar vs iron condor, `data/tastylive/dcal_vs_iron_condor_2022-10_review.md`).

## Priority tiers

### Tier 1 — his standard trade, checkable against our real-fill results
| video | title | our nearest result |
|---|---|---|
| IyddBat9m1o | Managing at 21 Days Doubles Your Odds (Options Jive) | 21-DTE rule ~~PASS (+$1.53, t 4.26) on a losing strangle~~ → **NULL on return, leaning INVERTED** (−$0.52/share, t −2.42; hold +$0.23 / managed −$0.29), risk reducer only (corrected 2026-09-24, FIX-1) |
| 7j10VtUH2G8 | We Tested 10 Years of SPY Strangles Across Every Volatility Regime (Market Measures) | certified bucket = index put sale in bearish-high-IV; single-name 45-DTE strangle ≈ flat (+$0.23/share held; "negative" corrected 2026-09-24, FIX-1) |
| VRelP3ORlrA | Stop Selling Strangles When the Market Drops 3%? The Data Says Wrong (Market Measures) | ⭐ same claim as our one certified cell (sell after a selloff) |
| NhgIYLeCA3U | I Abandoned Neutral Strangles After This Research | tastylive's own researchers walking back the flagship trade |
| Wt90xWeRuMQ | I Stopped Trading Strangles After This Study | same (`project_tastylive_kb` has a related note) |
| saFY8btmLZ0 | Low Delta Strangles Aren't Safer — 11 Years of Data | our breach odds depend only on cushion in ADR |
| _PhzgL9OpPI | The Bullish Strangle Almost Doubles Your Return — 20 Years of SPY | directional skew of the short-premium book |
| _QYaqicT5dg | 4-Year SPY Research Reveals an IVR Sweet Spot | IV rank **NULL** head to head vs credit/width (t 3.56) |
| zSm1DLpyR7E | Probability of Touch: What 21-Day Management Changes (Options Jive) | 21-DTE test above |
| BC5KdvZ7rEY | We Tested Strangles Across Sectors | single-name vs index liquidity gate |
| W9KBp_3BpVM | We Studied 17 Years of Rolling Trades (Market Measures) | his "don't roll losers wider" (untested here) |

### Tier 2 — Sosnoff in person (the 4 titles that are his)
| video | title |
|---|---|
| 9vwnX5mTT9M | The Real Reason Why Tom Sosnoff Won't Trade Stock |
| eUTCEbx2pco | Use Tom Sosnoff's Daily Routine to Analyze Trades |
| C6vrj2zu6Hc | The Dark Side of Tom Sosnoff's Iron Condor Strategy (⚠ reviewed 2026-09-23: Sosnoff is NOT on camera — house doctrine only) |
| p_X8dyNXlUE | How Tom Sosnoff Trades 0DTE Vertical Spreads |

### Tier 3 — volatility regime and VIX (his "sell the spike" core)
| video | title | our nearest result |
|---|---|---|
| 2KosXBxkNGo | Julia Spina Breaks Down 20 Years of VIX Expansions | post-shock premium FAILS vs VIX-matched days |
| t7_7MUgXj2E | Why After This Study We Won't Ever Trade Volatility Expansion | the long 7-DTE straddle (our surviving long-vol leg) |
| I68T7ACpS-Q | Earnings Season Panic? 13 Years of VIX Data Says Don't Bother | catalysts: earnings yes, macro no |
| lxcOKPcwkhg | Each Crash, the VIX Futures Curve Warned You First (The Math Check) | untested here (term structure as a warning) |
| msuajz2Tduo | 20 Years of VIX Data Says a Spike Is Coming? | regime forecasting consistently fails here |
| GYugqsK6CV8 | SPY Put Skew Hit Extremes — When to Buy Calls Instead | skew as a signal **NULL** (2026-09-22) |

### Tier 4 — 0DTE cluster (≈ 25 research videos; review only the ones with a testable number)
h59jrIgFulM (3 yrs 0DTE: selling calls lost, ICs worked) · 9HM1unL2Z5Y (manage one side vs both, 72 scenarios) ·
eyxQQ2eydx0 / CFh_KTOuKhQ (rolling 0DTE ICs) · w7oBArafcdU (best 0DTE management) · dHM3ZTYComM (entry time doesn't
matter). Our lens: 0DTE-family selling only paid **gamma-gated** (the positive-gamma 1-day fly, t 3.4). Most of these
can't be priced on our EOD data (see UIxluRMfh80's review).

### Tier 5 — structures (after Tiers 1–3)
HMnAjgCyXp4 (SPX jade lizard, 3 yrs) · YX1ER-r3Lxg (Ultimate Guide to Strangles and Iron Condors) · d5fHYF4eZJo
(before trading iron condors) · rF0baGqUk30 (strangles vs iron condors, Jim Schultz) · kPco6uly26E / FfEyv9Dz7vY
(managing a strangle that moves against you).

## Status (2026-09-24)
Reviewed: all of Tier 1 (11) and Tier 2 (4); Tier 3 except msuajz2Tduo and GYugqsK6CV8 (both already answered by the
ledger: regime forecasting fails, skew NULL); Tier 5 HMnAjgCyXp4, kPco6uly26E, FfEyv9Dz7vY, rF0baGqUk30; plus the
untiered xccHQzd8fLk and wkYzOi4G0Vc. Remaining = the Tier 4 0DTE cluster (not priceable on EOD v3) and Tier 5
YX1ER-r3Lxg / d5fHYF4eZJo (overview episodes).

## Suggested review order
Tier 1 as one batch of 11 (one KB, one ledger cross-check), plus Tier 2 (4 Sosnoff-in-person videos) → then decide
on Tier 3. Each has a transcript on the public channel, so yt-dlp works locally (no Chrome needed).
