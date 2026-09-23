# Qullamaggie — "My setups, methodology, and how to build trading mastery" (2020-05-27, 37 min)

_Reviewed 2026-09-23. Solo, unprepared screen-share: parabolic short, parabolic long (the "bounce"), earnings-gap
breakout (his later "EP"), plain breakout, a walk through his live portfolio, and his nightly scans. Transcript
(auto-captions, timestamped) in this folder. Timestamps below are from `transcript.txt`._

## Verdict: 2.5 / 5

The best short statement of his three setups on video, and more candid than most in the genre. He says outright
that 60–70% of his trades are losses or breakevens, he names a $125k loss, and he admits the portfolio he
shows is all green only because the losers were sold.

As evidence it's worth nothing, and in two places it's structurally biased:
- **Every chart is a winner picked in hindsight.** He says so himself: "I'm just showing perfect examples"
  (00:17:14).
- **The portfolio screenshot is survivorship on camera.** "Obviously all of these trades are profitable because
  I sell my losers" (00:23:46). The open book of a trader who cuts losers is always green, so it says nothing
  about expectancy.
- **His "edge-building" method is an outcome-selected database**: an Evernote file of breakouts that worked,
  "from 1980" (00:35:10–00:35:56). A library of successes can't show a base rate. It's the same defect as the
  retracted Tito 17/17 fade, done by hand.

Where our ledger has an answer, it runs against the mechanical versions of these setups. The discretionary
residue (which catalyst, which base, "linearity") is untested and probably can't be tested.

## Claim-by-claim against our ledger

| @ | Claim | Our evidence |
|---|---|---|
| 00:00:52–00:02:24 | **Parabolic short**: up 200–300%+ (even 1000%) in ~3 days–2 weeks, ideally "on nothing" (hype, pump). Don't short day 1–2; the best ones have run 3–5+ straight up days | **Nearest proxies all FAIL, but none is at his threshold.** Tito exhaustion fade, honest intraday version (`run_exhaustion_fade_honest.py`, 2026-09-22): setup = prior close ≥10% above the 10-SMA, armed above the 10-day high on ≥2× volume pace, short the first 1-min close below VWAP. **−0.26%/day, t −0.59, edge vs a random minute −0.02 (t −0.15)**. Also: Breitstein capitulation scorecard short (every bucket −0.12…−0.22R), bouncy-ball short (−0.41…−0.67R). ⚠ **His trigger is far more extreme** (+100–300% in days vs 10% over the 10-SMA), and his names (INO, GNUS, NKLA, WKHS) are small-cap pumps mostly outside our liquid panel. Short-universe test caveat: delisted/zeroed names are absent, and those are a short's best outcome. **Untested at his spec, not refuted** |
| 00:03:10–00:04:41 | Short trigger = break of the **opening-range low** (first 1-min, 5-min, or first 60-min candle) | Intraday triggers in our data don't beat a random minute. Stage A (11,227 long alerts): every arm ≈ a random later minute; ORB9 (long) **−0.425pp vs a random minute in its own window, t −8.50** (`alert_triggers_2026-09-23.md`). ⚠ All long-side. A short ORL on a +200% name is untested |
| 00:08:34–00:09:20 | Short only after weakness shows: VWAP test fails, multi-hour range, then a mid/late-day break. "You don't randomly short them, you wait for weakness" | VWAP double-rejection short **FAIL, worse than random**: 2nd touch −0.26R, t −6.2 vs a same-day random minute −0.17R (`vwap_rejection_short_2026-09-21.md`). Liquid names, not parabolics. ⛔ Note the cached `vwap` column is per-bar; any retest must rebuild session VWAP |
| 00:10:50–00:14:39 | **Parabolic long / bounce**: down 50–70% in 3–4 sessions, washout gap-down, then reclaim VWAP. Buy the **first green 5-min candle** with its low as the stop, add at the ORH | **Every liquid-panel analogue FAILs.** Breitstein counter-trend long (≥3 ADR below the 20 EMA + prior-bar-high break = "wait for it to go green") **−0.15 to −0.33R**, bare trigger ≈ control. Capitulation long ex-panic-months +0.055R = flat. Boring/violent **INVERTED**. Mari Trades' "first green day" is the same idea, **PARKED** until a small-cap universe exists. ⚠ His universe is outside ours; the 5-min version is untested |
| 00:15:25–00:17:02 | **Earnings-gap breakout (his "EP")**: beat on EPS and revenue, guides higher, gaps up on big volume, and **breaks a multi-month or multi-year range**; growth names (TDOC, DXCM, EPS +261% y/y) | **The mechanical catalyst-day buy is NEGATIVE:** DR-EP arm A (gap ≥3%, RVOL ≥1.8, ADR ≥3), **−0.173R, t −4.70, both halves negative**, loses to both controls. PEAD on the actual EPS surprise is **NULL** (0/50 cells). ⭐ **His two extra conditions are untested here:** (a) the gap breaks a ≥6–12-month range high, and (b) growth fundamentals. Our catalyst gate has no prior-base condition. That's the testable residue (see README, test 2) |
| 00:17:14–00:17:43 | "I'm just showing perfect examples… about 60%, maybe 70% of my trades are losses or breakevens, and yet I'm wildly profitable: small losers, big winners" | **Shape AGREES with our book, which is the point.** The house breakout is bimodal: **23.6% never return = +1.273R, 76.4% return = −0.374R** (`retrace_entry_2026-09-20.md`). The 20-EMA trail's median trade is −1.08R and the mean is all right tail (exit-timing study). ⚠ The split **cannot be called at entry** (9 features, best +0.057R, t ~2). A low win rate with fat winners is what a trend book looks like whether or not it has edge |
| 00:23:46, 00:30:35–00:31:20 | Portfolio screenshot, everything green: "because I sell my losers; you keep your winners" | **Survivorship by construction**, and he says so. Not evidence of anything. Cutting losers is consistent with house practice (the day-low stop), but it's no edge on its own: the stop doesn't discriminate. Stop-out rates are identical for breakouts and random later entries, **48.4% vs 48.0%** (`entry_vs_stop_2026-09-20.md`) |
| 00:25:17–00:26:02 | Short example: "one leg up, second, third, fourth, fifth leg; on the third day, opening-range lows" | Same as the parabolic-short row. One chart |
| 00:26:47 | VTIQ: "I took a $125,000 loss on it… too aggressive too early" | One disclosed loss. Credit for candour; not a sample |
| 00:27:32–00:28:17 | BLDP / FAS: buy **opening-range highs** on a gap-up out of a tight flag. FAS stopped first, re-bought on a later ORH | **Contradicted as an entry.** Entry study (layer-2 name-days, 1-min bars): **ORB+re-entry −1.22pp vs buying the CLOSE, t −3.4**; control set −0.9 (t −1.8) (`entry_study_2026-09-17.md`). Intraday stop execution makes tight stops worse, and re-entry repairs only part of it |
| 00:29:02 | "Trade stocks that have volume and range; that's where the money is" | **AGREES directionally.** Universe test: HYB-B = TT at $100M ADDV + **ADR ≥4**, +1.79 (t 2.6, PARKED); the TT's own ADDV ≥$200M criterion discards 60% of the universe. Range (ADR) is where the book's return lives, though no arm passes on breakouts |
| 00:31:27–00:33:39 | **Scans**: $60M average dollar volume, 20-day ADR ≥ "2.4%" (as captioned; possibly mis-heard), top ~7% by performance over 1, 3, 6, 12 and 18 months; plus 5-day gainers ≥25% | **Partly tested.** Universe test Q1 (20d, ADR-matched): TT +0.56 (weakest), Ariel momentum scan +0.87, INT +1.44. **Momentum-rank universes beat the Trend Template**, which supports his "scan for the strongest" framing. ⚠ His exact top-7%-by-return × multi-horizon scan has never been run. In 2021 he quotes top 2% and $150M (see the interview notes). ⚠ 2.4% ADR is below the house 3.5–4% gate. Treat that number as unverified |
| 00:35:10–00:36:42 | Build mastery with an Evernote database of tens of thousands of historical breakouts back to 1980; "no one can help you" | ⚠ **Outcome-selected by construction.** It's a catalogue of moves that happened. Useful for learning what winners look like, useless for learning how often the setup wins. Our retracted Tito fade (17/17 → −0.26%/day) is what this method produces when it's run mechanically |

## What I would take

1. **The setup taxonomy, as a spec.** Breakout, earnings gap ("EP") and parabolic short/long are cleanly separated,
   with timeframe-agnostic triggers (ORH/ORL on 1-, 5- and 60-min). README §Setups consolidates them.
2. **The one untested residue with a real prior:** an earnings gap that *also* breaks a multi-month base. Our DR-EP
   catalyst gate ignored the base entirely.
3. **Nothing to adopt.** ORH entry is contradicted by the entry study. Mechanical parabolic long/short proxies fail
   on our universe. The win-rate profile is descriptive, not evidential.

## Not tested, could be

- **EP with a base-break condition** (earnings gap ≥ X% + RVOL ≥ 3 + close above the prior 126/252-session high),
  close entry, LOD stop on the close, 20-EMA trail; `post` + `xname` controls vs DR-EP arm A. ~½ day on
  `pattern_test` + the earnings dates already cached for PEAD.
- **Parabolic short at his threshold** (+100% in ≤10 sessions, ≥3 consecutive up closes), short the first
  close below the prior day's low. Needs a universe that includes small-cap pumps *and delisted names*. Blocked on
  data, the same blocker as Mari's first green day. **Not queued.**
