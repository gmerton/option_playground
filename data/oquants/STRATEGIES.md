# oquants strategies — side by side, with our cross-checks (2026-09-10)

All numbers are the vendor's own and untested by us. "Us" = the repo's studies and memory.

| # | Strategy | Signal / gate | Structure & DTE | Sizing | Exit | Vendor evidence | Relation to our work | Test priority |
|---|---|---|---|---|---|---|---|---|
| 1 | **Forward-factor calendar** | FF=(front−fwd)/fwd ex-earn IV **≥ 0.20**; liq ≥10k/day; debit ≤ calculator max | Long ATM call calendar (or ±35Δ double); 30/60, 30/90, **60/90** best | 1-4% (post) / 2-8% with 4% default (video); ¼ Kelly | Front-expiry day, as a spread; early only if FF ≤ 0 | 19y, >300k costed spreads; blind = negative, gated = +9-25% per trade; CAGR ~20-28%, Sharpe ~2 | FF(30,90)=1/fvr−1 → our backwardation gate (iron fly FVR<0.80). Our dc_time_machine calendars were NOT FF-gated | **1 — replicate first** |
| 2 | VRP on ETFs | log IV/RV↑, **IV pct low-moderate (<80)**, flat-fwd ratio, contango/flat TS | Wide IC (sell 25-30Δ, buy 1-5Δ) 30-45 DTE, or a hedged short straddle | 1-5% margin/trade; 40-60% of account | Roll ~7 DTE; exit IVP >90-95% or TS inversion | Train/test linear model; ETF short-vol mean +17%/trade (post chart) | Matches our QQQ/IWM IV-pct ≥80 veto; our SPX condors survive costs | 2 — extend our ETF studies with their gates |
| 3 | Earnings short vol | Front→45d slope very negative + 30d volume high + IV30/RV30 high | 30-day-gap ATM call calendar (his choice) or wide iron fly; enter 15 min pre-close, exit 15-20 min post-open | Calendar ~6%, straddle ~2%; 10-30% of capital | Next morning; don't hold to the close (drift loses) | 72.5k events; top ~10% → calendar +7.3% mean, sd 28% | Our straddle study: earnings straddles ≈ 0 held to expiry. Needs INTRADAY quotes (EOD v3 can't) | 3 — only with IBKR minute data |
| 4 | Momentum-skew vertical | Skew z ≤ −1.5 in the momentum direction; CS decile ≥8 / ≤3; liq ≥5-20k | Buy 45-60Δ, sell 10-25Δ; 10-20 DTE; 1-3-2 fly variant | 0.5-2%/trade | Hold to expiry; ≥90% max early; close before earnings | GBM sim +23% EV at 32% win; cherry-picked member wins | Fits Gabe's momentum names; our vehicle study: verticals trade winners for smaller losses | 4 — skew-z panel from v3 greeks |
| 5 | Pre-earnings long straddle (Play) | 4-signal regression: implied move vs last implied / last realized / avg implied / avg realized (lower = better) | Long ATM straddle, nearest monthly after earnings; enter ~14d before | 2-6% per trade (small Kelly) | Before the announcement | 21.5k trades since 2009; OOS walk-forward +3.3% mean, 42% win | Complements our long-straddle FVR book (a long-vol hedge for short-vol books) | 5 |

## Recurring principles worth adopting regardless
- **Blind short or long vol ≈ 0 after costs; the edge is always in the gate.** Same conclusion as our straddle, calendar and put-spread studies.
- **Sell vol at low-to-moderate IV percentile, not at the highs.** High IVP marks regime shifts, not rich premium (their VRP deciles; our QQQ/IWM).
- **Close a short-vol position when its thesis breaks** (IVP >90-95%, term structure inverts) regardless of P&L. The "day-zero" test.
- **Fractional Kelly (¼ or less) plus many small, diversified positions** beats concentration on Sharpe at nearly the same CAGR.
- **Execution discipline is part of the edge:** limit orders, max-debit caps, wait 15-20 minutes after an event open.

## Open items
- The three members-only videos (2 livestreams + walkthrough) are untranscribed (Mux, no captions).
- Their FF and Flat-Fwd definitions differ from ours; always map before comparing (memory: `reference_oquants_flat_fwd_ratio`).
- Replication plan for #1: options_daily_v3 ATM call IVs → ex-earnings FF (skip windows with earnings between entry and back expiry) → calendar P&L entry→front expiry with the house cost model (`lib.studies.costs`) → decile curve + FF≥0.20 subset + ¼-Kelly portfolio. v3 greeks run through ~2026-05 and bid/ask through ~2026-07.
