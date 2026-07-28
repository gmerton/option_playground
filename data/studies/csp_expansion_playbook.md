# CSP Expansion Playbook — adding cash-secured puts deliberately

> Created 2026-07-14 from the top-down triage + live screen of 26 low-ADR quality names.
> Premise: the breakout screen's **rejects are the CSP universe** — strong uptrend, at/near highs, low
> realized vol, names you'd own. Same top-down signal, opposite vehicle.

## The gate stack (all must pass — order matters)

1. **Trend/RS gate:** stock is in the market's leading rotation (uptrend, rising 50d, RS ≥ SPY) — from the
   daily triage, not a static list. Selling puts on laggards is catching knives for pennies.
2. **Own-it gate:** would genuinely hold 100 shares through a drawdown (quality/fundamentals). Assignment is
   an intended outcome, not a failure.
3. **VRP gate:** target-delta IV > RV20. No structural reason to sell premium that's cheaper than realized.
4. **Liquidity gate:** OI ≥ ~150 at the target strike, BA ≤ ~25% of mid (prefer ≤15%). The HWM/MATX lesson:
   option liquidity is an independent universe filter.
5. **Earnings gate:** expiry window contains NO print — sell *after* earnings into the clean window. If IV
   crush makes the yield unattractive post-print, the premium was event premium, not VRP — pass.
6. **Correlation gate:** sleeves, not tickers. Max 2 names per sleeve (banks / insurers / rails / payments /
   healthcare); NO new AI-infra while MRVL+NBIS are open. All financials are one Fed trade at the margin.
7. **Sizing:** prefer small-ticket underliers ($5–12K collateral) for granularity and laddering; per-name
   collateral cap; ladder entries over weeks, don't deploy in one shot.

Standard spec: **25–30Δ, 30–45 DTE**, yield target ≥ ~1.3%/mo (≥ ~15% annualized) at 25–30Δ.
Management (from the 2026-07-14 MRVL/NBIS review): act at delta ~0.70 or extrinsic <25%; roll only for
credit; never roll into an earnings print by accident; assignment → CC above basis (wheel).

**Scoreboard rule (the Ryan-KB lesson):** track *net P&L including assignment MTM*, never premium collected.
The recap audit showed premium can exceed 100% of true profit even in a V-recovery half-year.

## Screen results 2026-07-14 (Aug 21 expiry ≈ 38 DTE, ~0.27Δ put, live quotes)

| Rank | Name | Strike/yield | Ann. | VRP | OI/BA | Earnings | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | **AXP** | 340P, 2.19% | 21% | +6.4 | 471/7% | **Jul 24 — wait** | Best quality-yield combo; sell after print |
| 2 | **USB** | 60P, 1.88% | 18% | +3.9 | 1010/21% | Jul 16 | Post-print candidate; $6K ticket |
| 3 | **FITB** | 55P, 2.14% | 20% | +3.2 | 550/21% | Jul 17 | Post-print; same sleeve as USB — pick one or half-size both |
| 4 | **UNP** | 275P, 1.73% | 17% | +5.8 | 181/11% | **Jul 23 — wait** | Rails sleeve; at 52wk high |
| 5 | **TRV** | 320P, 1.19% | 11% | +5.5 | 195/16% | Jul 17 | Insurance sleeve; 19% RV grinder; modest yield is the honest price of safety |
| 6 | **UNH** | 400P, 2.29% | 22% | +11.8 | 1036/5% | Jul 16 | Rich because of the print — re-price after; $40K ticket |
| 7 | **V** | 340P, 1.62% | 16% | +4.0 | 434/18% | **Jul 28 — wait** | Payments sleeve, post-print |
| — | JPM/BAC | 1.1–1.5% | 11–14% | −1.3/+3.6 | huge/8% | Jul 14 | Most liquid, thinnest edge; anchor only |

**Rejected & why:** HWM (it's the breakout LONG candidate — a 260P doubles the same bet; + Aug 6 print in
window), WST/GWW/MTB/ZION/CFG/RF/MET (OI < 50: fail liquidity), PNC/NSC/GD/KEY (BA 39–55%), CB/ABBV/JNJ
(negative VRP at screen time — recheck post-print), CNI (marginal BA 35%, UNP is the better rail).
⚠ Some off-hours spot quotes were stale (NSC/MTB) — always re-price at entry; trust chain deltas over quote mids.

## This week's execution plan

- **Jul 17–18:** re-run the screen on USB, FITB, TRV, UNH, JNJ post-print. If VRP survives the IV crush and
  the name didn't gap into a downtrend, sell Aug 21 25–30Δ. Start with ONE bank (USB or FITB) + TRV.
- **Jul 24+:** AXP and UNP post-print — the two best names on the board. Aug 21 (4 wks) or Sep 18.
- **Budget:** ~$15–30K new collateral total across 2–3 names/sleeves (MRVL+NBIS already hold $42.5K of
  correlated AI-infra risk — that sleeve is FULL). Half-size everything while SPY distribution days ≥ 5.
- Re-screen cadence: after each earnings wave; the gate stack is the checklist, `run_csp_screen.py`
  (repo root, `PYTHONPATH=src .venv/bin/python3 run_csp_screen.py`) is the tool — edit TICKERS to re-target.
