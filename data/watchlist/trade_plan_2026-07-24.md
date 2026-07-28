# Trade Plan — Friday 2026-07-24

> Built 2026-07-23 evening from the Thursday EOD scan (42 candidates / 109-name generated list)
> + earnings-gate pass. Grammar unchanged: buy the power bar through the pivot; no anticipation,
> no chasing light-volume drifts (this week's exhibits: CVS, USB, AAPL — all rolled back).

---

## Market context (as of 7/23 close)

- **SPY 8 / QQQ 8 distribution days (SERIOUS); QQQ below its falling 9 EMA (~705), SPY below
  ~745.** Luk flipped fully bearish 7/22; breadth damage concentrated in tech/speculative.
  Financials/insurance/energy/transports lead — which is exactly where this plan's names live.
- **Consequences: max 1–2 new positions, HALF normal size.** No entries while SPY is down >0.2%
  on rising volume at decision time (forming distribution day).
- TSLA/GOOGL calls already on = existing growth-tech risk. New entries here are the OTHER side
  of the rotation (rails, insurance, energy) — deliberate.

## Global gates (before ANY entry)

1. **Market gate** — SPY flat-to-green at trigger time (rule above).
2. **Trigger = power bar** — wide range, close top ~25%, RVOL ≥ ~1.2× and rising ("closes
   above," NOT "ticks above").
3. **Earnings gate** — Tier 2 all report Aug 4–5: any entry carries a **pre-committed de-risk
   date of Mon Aug 3 close** (flatten or cushioned-core only into the prints).
4. **Stop at entry** — trigger-bar low (or pivot, whichever tighter), daily-close basis.

---

## TIER 1 — armed triggers

### WAB — day-2 of a CONFIRMED breakout (priority claim on the risk budget)
- **Status:** closed $297.99, +0.9% over pivot **295.41** on **1.9× RVOL** Thursday — the only
  confirmed breakout on the board. Earnings **Oct 21** (max runway). Transports (IYT) top-6
  lower-risk industry.
- **Tomorrow:** gap-and-hold rules. Open holding ≥295.41 → enter (day-2 continuation); dip to
  the pivot that holds on the cash session = the entry. **Open back below 295.41 = failed
  trigger — do NOT buy the "discount"; wait for a re-close above.** Opens >~304 (3% ext) →
  stand down, wait for first pullback to the 9-EMA.
- **Stop:** Thursday's low (trigger bar), daily-close basis.
- **Vehicle:** stock, modest size (ADR 2.8% `!adr`); optional call check — only if ≤25% BA.

### TRV — confirmation watch (do NOT front-run the volume)
- **Status:** third act of the 7/17 EP: re-broke the post-EP flag, closed $376.37, +0.6% over
  pivot **374.00** on 1.3× — shy of the 1.5× gate. Earnings passed (next Oct 15). Insurance #2
  industry.
- **Trigger: close (or last-hour hold) above 374 on RVOL ≥1.5×** ≈ ≥4.1M shares (50d avg
  ~2.7M). Pace checkpoints: ~1.6M by 11:30 · ~2.6M by 1:30 · ~3.5M by 3pm ET.
- Another light-volume drift above the pivot = the CVS pattern → no entry, keep watching.
- **Stop:** trigger-bar low. **Vehicle:** ADR 2.5% `!adr` → small stock position or ATM/1-strike
  ITM Aug/Sep call (short-dated chain quoted ~18% BA at 0.24Δ on 7/23 — re-verify ≤25%).

### TRGP — at the line
- **Status:** closed $285.58, **−0.2%** from pivot **286.25**. Energy (XOP #1 industry). 1M +6%.
  Earnings **Aug 6** → entry tomorrow has 9 sessions; **de-risk by Aug 4 close**.
- **Trigger:** power bar closing above 286.25 on RVOL ≥1.2× (≈ ≥1.25M shares) and rising.
- **Stop:** trigger-bar low. **Vehicle:** ADR 2.4% `!adr` → modest stock / call check.
- Cross-ref: TRGP is also on the post-earnings bull-put queue — if no breakout fires and the
  print goes fine, the income entry re-checks Aug 7+.

### Priority if multiple fire under the 2-position cap: **WAB** (confirmed + runway), then
**TRV** (confirmation + earnings-clear) over TRGP (deadline-carrying).

---

## TIER 2 — coils with an Aug 4–5 print: triggers armed, deadline attached

Shared rules: power-bar-through-pivot only (RVOL ≥1.2× rising), half-of-half size given the
deadline, **hard de-risk Mon Aug 3 close**, stop = trigger-bar low.

| Name | Pivot | Dist | Earnings | Notes |
|---|---|---|---|---|
| ALL  | 257.67 | −1.2% | Aug 5 | Insurance leader, 1M +10% |
| MRK  | 131.74 | −1.0% | Aug 4 | Healthcare, 1M +9% |
| RPRX | 59.44  | −0.7% | Aug 5 | Royalty pharma, 1M +7% |
| ADM  | 87.67  | −1.5% | Aug 4 | Ag, 1M +14% |
| CF   | 130.43 | −2.9% | Aug 5 | Ag/fertilizer, **1M +24%** |
| CRNX | ~84.00 | −0.4% | Aug 4 | ⚠ hottest name on the list (1M +133%) but ADR 1.9% + biotech print: **half-size cap, no chase, nothing on a drift** |

---

## Bench (armed in the intraday monitor, not in this plan)

- **WST** — post-earnings (reported 7/23, RVOL 2.4×), −3.3% under 367.66: Archetype-B if it
  drives through on continued volume.
- **HWM** — back at the 7/15 plan's exact 290.63 pivot, earnings Aug 6.

## No-touch today (earnings-gated Jul 27–31)

ILMN (+0.1% light — the 7/30 EP plan owns it), CTVA, VLO, FTI, LYV, STX, FTNT, WELL, CRS, AAPL.
These are next week's EP procession — see `trade_plan_2026-07-30.md` / `trade_plan_2026-08-05.md`.

## Exits (all positions)

- GRIND: trail the 20-EMA on daily closes. SPIKE: sell into strength, don't trail.
- Failed breakout: exit on daily close below trigger-bar low. Fast, small, no averaging.

## Friday routine reminders

- Morning: check `refresh_latest.txt` (first scheduled cloud refresh ran overnight — AMAT may
  re-qualify) and run the weekly income screener + FVR scan (playbook Friday cadence).
- Intraday monitor: `monitor_latest.json` on S3 already carries the near-pivot names.
