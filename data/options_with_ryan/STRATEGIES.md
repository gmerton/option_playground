# Options With Ryan — Strategy Leaderboard

Conviction 0–5 (default LOW until tested) · Risk 1–10 · Tested: no/partial/yes.
One row per SYSTEM; per-ticker wheel plans roll up under Wheel Core unless they diverge materially.

| Strategy | Slug | Conviction | Risk | Tested | Verdict (one line) |
|---|---|---|---|---|---|
| Wheel Core (CSP→CC, mega-tech) | `wheel_core` | 2 | 6 | no | Orthodox mechanics, sane rules; 4%/mo "retirement" math needs 37Δ+ on NVDA-vol and ignores assignment MTM — real expectancy likely low-teens with equity drawdowns |
| VIX-Scaled Premium Selling ("swing trading") | `vix_scaled_premium_selling` | 2 | 7 | no | Sane spread parameters + a buy-fear ladder with no brakes: all-in (plus savings) at VIX>30 assumes every spike V-recovers; 88% win rate = unsampled left tail |
| Below-Basis CC Repair | `wheel_underwater_repair` | 2 | 7 | no | Most concrete protocol (8–12Δ/7–10DTE weekly, roll-early, real fold gates) — but built on "not a loss until you sell," and the gates were added after the one loss they'd have caught |
| LEAPS Dip-Buying | `leaps_dip_buying` | 1.5 | 7 | no | 70Δ/400DTE stock replacement with decent entry gates, ruined by inverted exits: cut winners +10–40%, hold losers through 65% drawdowns; evidence = one HOOD 12-month cherry-pick |
| Bear-Market Wheel (Fed/VIX regime) | `wheel_bear_regime` | 1.5 | 5 | no | VIX-gated response rules are coherent (and echo our regime gates); the "predict bears via the Fed" claim fails a calendar check on his own 2022 example |

## Cross-cutting findings (6 videos in)

- **"Premium collected ≠ profit" — now internally evidenced, not just suspected** (`recap_audit_2025H1.md`):
  the $218K recap pairs the premium headline with a volunteered "~22% return." Taking both at face value,
  premium was **110–140% of actual profit** — the share/assignment leg net lost money even in a half-year
  ending at all-time highs, with a −18% intra-window drawdown and a $100K bottom-tick deposit doing real work.
  Claim of "40%/yr, 5 years straight" remains unverifiable by design.
- **He doesn't follow his own rules on camera:** VIX 15–20 prescribes 25–50% cash; he holds ~15% ("a little
  more aggressive"). The 2022 origin story also changed between videos (Nov-2021 vs Dec-2022 tellings).
- **Parameter drift across videos** (pin specs before backtesting): CC = 20–30Δ/7–14DTE (Feb 2025) vs
  30Δ/20–30DTE green-day entry (Jul 2025); CSP spec stable at 25–35Δ/30–45DTE, 3–5%/mo target.
- **One quality bar recurs everywhere** (18-mo uptrend line, profitable, PE<100, double-beat earnings):
  it's really a momentum-survivorship filter — it retroactively blesses PLTR/HOOD/NVDA and excludes each
  loser after the fact (HIMS, AMD, LULU).
- **Consistent anti-Adhikary exit structure:** quick profits, patient losses, across both the long-options
  and short-premium books. Where Tito's edge is exit execution, Ryan's system is built to survive being
  wrong by never booking it.
- **Best backtest candidates for us:** (1) VIX ladder vs our 50MA×VIX regime gates (sizing vs structure-switch);
  (2) below-basis CC repair vs plain-hold vs sell-and-redeploy on 2022's fallen wheel names; (3) LEAPS
  quick-profit tiers vs holding the same entries (disposition-effect test).

## Review queue (5/56 done — see channel_videos.txt)

Suggested next: a monthly recap with real numbers (`ttN5dCDDE5c`, "$218K premiums") to audit the income
claims against the MTM critique; then one per-ticker 2026 wheel plan (`Q3IZjEFjaxc` SOFI) to see if the
per-name plans add anything beyond wheel_core.
