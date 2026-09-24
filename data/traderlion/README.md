# TraderLion — Setup Knowledge Base

Archive of the **TraderLion** YouTube channel: interviews and case-study sessions with
momentum/growth traders, mostly in the O'Neil → Minervini lineage (VCP, Stage 2, leadership RS).

Same skeptic-default convention as `data/theta_profits/` and `data/options_with_ryan/`: the unit
of value is the **setup**, and the deliverable is an **objective** write-up of its risk/reward.

## Prime directive: skepticism — with a channel-specific twist

TraderLion guests are usually **educators selling a service** (private-access platforms, workshops,
alert products) rather than anonymous retail traders. That changes the failure mode:

> **The methodology is often genuinely sound — it's the EVIDENCE and the DIFFERENTIATION that are
> the problem.** These are real practitioners teaching a real, century-old momentum framework. But
> the case studies are winners-only, the returns are unaudited, and the parts presented as the edge
> are frequently **proprietary indicators you can only get by subscribing**. Separate the public,
> testable mechanics from the black box and the marketing.

Red flags to call out when present:
- **Winners-only case studies.** Near-universal on this channel. Note when losers are discussed
  only in the abstract ("all our losers look the same").
- **Headline dollar/return figures with no denominator** — no starting capital, no CAGR, no
  drawdown, no time-weighted return, no audit.
- **US Investing Championship citations.** Small self-selected accounts, marketing collateral;
  a real result but not evidence a method generalizes to a normal book.
- **Proprietary indicators as the mechanism** (RS ratings, custom "behavior analytics", extension
  alerts). If the rule can't be reconstructed from public data, it can't be tested — say so.
- **Mid-roll sponsor reads** for the platform being demonstrated. Note the commercial relationship.
- **Unfalsifiable joints:** "violations of the rules" where the rules aren't enumerated; "the
  market tells us what to trade."

**But don't over-correct.** The core O'Neil/Minervini framework is the same one this repo already
implements (`run_minervini_scan.py`, the breakout monitor, the scorecard). Where a guest states a
mechanical rule the repo can test, that is a genuine research lead — score it on the merits.

## Layout

```
README.md                  This file — convention + skeptic mandate.
SETUPS.md                  Index / leaderboard: setup · trader · conviction · risk · tested? · verdict.
setups/<slug>.md           One objective write-up per setup (the deliverable).
videos/interviews/<date>_<id>/   transcript.txt · meta.json · notes.md
backtests/<slug>/          (created on demand) test scripts + results.
```

## Videos

| Date | Video | Guest | Notes | Verdict |
|---|---|---|---|---|
| 2023-10-04 | [The Perfect VCP Trading Setup](https://www.youtube.com/watch?v=M_tD6X0CSOI) (38 min) | Mark Minervini | [notes](videos/interviews/2023-10-04_M_tD6X0CSOI/notes.md) | **2/5.** "VCP" is said once and never defined. FTD + first-to-new-highs is already NULL/UNDERPOWERED here. Useful for: [30:41] "fastest are extended -> wait for a subsequent entry" (= our entry-extension finding). Codable VCP spec + pre-registered test design in the notes (NOT RUN) |
| 2024-10-09 | [THIS is How Leif Soreide Finds 90%+ Winners (High Tight Flags)](https://www.youtube.com/watch?v=mpe2_FCfpRg) (12 min) | Leif Soreide | [notes](videos/interviews/2024-10-09_mpe2_FCfpRg/notes.md) | **2/5.** "90%+ winners" is never said: the 90% is the *pole's* rise. The most complete HTF definition in these KBs; zero evidence. Codable spec in [setups/soreide_high_tight_flag.md](setups/soreide_high_tight_flag.md) (NOT RUN) |
| 2024-10-27 | [+222% Return in 27 Days - The High Tight Flag Setup](https://www.youtube.com/watch?v=rdmjsbDVuoU) (50 min) | Leif Soreide | [notes](videos/interviews/2024-10-27_rdmjsbDVuoU/notes.md) | **2/5.** "+222% in 27 days" is not in the video. HTF Masterclass funnel; shows some losers. Management (scale at 1-3R, sell 100%, pyramid) contradicted/NULL here. ⭐ Early low-volume inside-day entry *inside* the flag = the right side of the entry-extension finding |
| 2025-12-21 | [The Wedge Pop Swing Trading Setup](https://www.youtube.com/watch?v=fYxSQvuwOQc) (66 min) | Oliver Kell | [notes](videos/interviews/2025-12-21_fYxSQvuwOQc/notes.md) | **2.5/5.** Most objective setup in the KB: "the buy is the swing-high break of a tight mini-base, not the MA cross" = a claim with a built-in same-date control. "60-70% losers" matches our book. EMA crossback = pullback FAIL; RS-in-correction INVERTED. Spec in [setups/kell_wedge_pop.md](setups/kell_wedge_pop.md) (NOT RUN) |
| 2026-02-07 | [+1300% Return in 2 Years (Chris Flanders)](https://www.youtube.com/watch?v=6aOnCK1gv2w) (1h53) | Christian Flanders | [notes](videos/interviews/2026-02-07_6aOnCK1gv2w/notes.md) | **3/5.** Best disclosure in the KB (489 trades, 30.5% win, top 5 trades = the year, losers in depth). Setups rejected here (EP-day ORB = catalyst-day -0.173R + ORB -1.22pp). ⭐ Pony: ~6 round trips in a day, -5% of the account = Gabe's same-day leak; ⭐ 5% monthly drawdown cap. ⚠ USIC 2025 MM +166% conflicts with the MPA write-up's Weissman "winner at +115%" |
| 2026-09-23 | [How to Find A+ Trades Like a Market Wizard (CAN SLIM screens)](https://www.youtube.com/watch?v=afkUTFNVpso) (2 h 02) | Ross Haber (ex-O'Neil) with Richard (Deepvue) | [notes](videos/interviews/2026-09-23_afkUTFNVpso/notes.md) | **2/5.** No Market Wizard; the description's timestamps are wrong. RS12-sorted Up-on-Volume / DV Leaders (proprietary) / "62.5%" screens, then CAN SLIM C/A fundamentals. Technical half already answered: RS12 = TT c9 UNDERPOWERED, low ADR vs HYB-B (ADR>=4) contradicted, group confirmation NULL, 62.5% ~ down-day RS INVERTED. ⭐ EPS growth (C) is the one never-tested axis, codable on `earnings_yf.parquet`: spec in [setups/haber_canslim_screen.md](setups/haber_canslim_screen.md) (NOT RUN) |
| 2026-07-22 | kCLiSsIZ7L4 | Pradeep Bonde | [review](2026-07-22_bonde_episodic_pivot_review.md) | Episodic pivot; DR-EP tested 2026-09-22 -> NULL |
| 2026-07-29 | [Trading $100K Into $20M, VCP](https://www.youtube.com/watch?v=uMJXA_I9HDw) | Ritchie II / Hedgepath / Weissman (MPA) | [setup](setups/minervini_vcp_low_risk_entry.md) | 2.5/5 |
| 2026-09-06 | J-I6iLGjp1Q | Alan Ellman (BCI) | [setup](setups/bci_covered_calls_cash_secured_puts.md) | 1/5 after test |

## Adding a video

```bash
.venv/bin/python3 add_luk_video.py <url> --kb data/traderlion --type interviews
```
(the Luk script is generic — `--kb` retargets it; requires `yt-dlp` in the venv)

⚠ Auto-captions **mis-transcribe tickers and numbers constantly** — verify every ticker and every
dollar figure against the chart discussion before quoting it. Observed in this KB: "DCP" for VCP,
"three-quarters of a billion" for three-quarters of a *million*, "Mark Mervini/Menervini/Manini"
for Minervini, "DFW" for the Deepvue platform, "MoniLert" and "Iron/IREN" uncertain. Added 2026-09-23: "ests" = ASTS, "Kors"/"coz" = CORZ, "Iron" = IREN (confirmed in the Flanders video), "Abivac" = ABVX, "Cororeweave" = CRWV, "Wolf" = WULF; Flanders' "risked 75% of my account" = 0.75% (a lost decimal).

## Per-setup write-up structure

1. **Verdict box** — one line, conviction (0–5), risk (1–10), tested? (no/partial/yes).
2. **Who / what's being sold** — the commercial context, stated up front.
3. **Mechanics** — precise enough to backtest.
4. **Claimed edge & returns** — their numbers, quoted, with timestamps.
5. **Objective assessment** — red flags, real risks, what's unverifiable.
6. **What's genuinely sound** — the legitimate core.
7. **Testability** — EOD-testable now / needs intraday / proprietary-untestable.
8. **Overlap with the existing book** — what the repo already does, and what's actually new.
