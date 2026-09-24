# OptionsPlay — "I Built the ULTIMATE Algorithm to Trade Earnings!" (Tony Zhang, 2025-07-20, 31 min)

_Reviewed 2026-09-24. It has the same title as the 2025-05-02 launch webinar
[3VVjDDJvu2s](../2025-05-02_3VVjDDJvu2s/notes.md), but it is **not** a re-edit or duplicate. It is a
**separate session**: the Q2-2025 season kickoff, with different names and a different delivery channel (a Monday
research report instead of the Friday email). The same three-step framework is re-presented, and an IV-rank vehicle choice is
added. This note covers only what differs. For the framework, the exploratory check and the codable spec, see 3VVjDDJvu2s.
Transcript in this folder._

**How "not a duplicate" was established:** a word-level sequence match of the two transcripts with timestamps
stripped. 3VVjDDJvu2s has 8,302 words and this one 5,373. Only **647 words** align in sequence, and the
**longest shared run is 32 words** (the legal disclaimer). Compare wG0yvxmDuXI vs lV8Jkl37h4M, where all
but 198 of 6,875 words matched. The examples here are completely different (MRNA? captioned "Madna",
TMUS, GOOGL, TSLA; list: GOOGL/UNP/NEM bullish, TSLA/PM/TMUS/T/DOW bearish), and so are the dates (Q2-2025 season).

## Verdict: 1.5 / 5 (same framework as 3VVjDDJvu2s, same problems)

It is the same three legs (trend, RS, valuation vs peers), again called a "proven earning strategy" (05:13,
08:05) with no numbers. It adds nothing that rescues it. The direction claim is sharper here: they're "likely
going to surprise to the upside" (08:48). On our events, trend + RS alignment calls the reaction's direction
**50.0% / 49.6%** of the time (exploratory check in 3VVjDDJvu2s). The one new mechanical element, **IV rank
picks debit vs credit**, is a tested NULL. He promises a paper-trading review "in a couple of weeks" (20:27,
27:06, 30:09), but no such review is in our transcripts.

## Data audit

| item | what he shows |
|---|---|
| Backtest / sample | None. "proven earning strategy" (05:13, 08:05) |
| Track record | None shown. Three paper trades entered live (GOOGL call spread, TSLA put spread, TMUS call credit spread) for a promised later review |
| Pricing | Platform mid. Returns come from the platform P&L simulator at his own price target |
| Filter rate | Liquidity removes "97–98%" of reporters (02:56). The three steps remove "eight or nine out of 10" liquid names (08:11). Unverified |

## What is new relative to 3VVjDDJvu2s

| @ | Claim | Our evidence |
|---|---|---|
| 08:25–08:48 | Names passing all three "have the highest probability of making that big move … likely going to surprise to the upside" | ❌ Exploratory (3VVjDDJvu2s): direction hit 50.0% bull / 49.6% bear. Aligned names realise **less** of their implied move (0.91 vs 0.965). The surprise itself doesn't drive drift either: surprise-based PEAD is NULL, `corr(surprise, reaction)` = 0.20 (`pead_2026-09-20.md`) |
| 17:50–18:36, 27:40 | **IV rank picks the vehicle:** GOOGL IVR 22 → buy (a call or debit spread); TMUS IVR 42 → sell a call credit spread | ❌ **NULL.** IV rank as a vehicle chooser: DiD +15.4pp bullish, **t 0.68** (`run_ivrank_vehicle.py`, `ivrank_vehicle_2026-09-22.csv`). ⚠ Just before a print, a name's IV rank largely measures the **event ramp** (front-expiry ATM IV +40 to +57 vol points into the print), not whether the name's options are cheap |
| 19:30–20:09, 25:38 | **Vertical beats the outright.** GOOGL 185/200 call spread "208%" vs the 185 call "142%" at his $202 target; TSLA put vs put spread about equal, "always take the lower-risk one" | ❌ **Reverses his own May advice** (3VVjDDJvu2s 32:46: outright "for unlimited upside"). Both return figures are **conditional on hitting his target**, so neither is an expectation. On real fills, the second leg's friction cost −27.1pp (t −5.51) and the cap mattered on 1.7% of trades (`event_spread_2026-09-20.md`; FOMC/election events, not earnings) |
| 23:11–24:47 | TSLA: a 320/370 call credit spread is rejected for a poor risk/reward (risk $3,500 to make $1,500); a 315/280 put debit spread at $11.63 is taken instead | Risk/reward framing is fine as arithmetic. The bear-aligned put in our exploratory check was the **worst** cell: −26.9% of premium at the ask (front-expiry ATM, not his 5-week spread) |
| 27:40–28:21 | TMUS: expected move only 4.37%, so selling premium fits better (risk $548 to make $452, ~45% credit/width) | Closest to anything that survives: credit/width ranks single-name bull puts (`run_premium_to_width.py`, borderline PASS), but that was tested **not** through earnings and on bull puts. A call credit spread through the print is untested. Selling through the print on naked puts: through-earnings +0.19pp within-week, t +3.6, not beyond direction (`bci_csp_study_2026-09-17.md`) |
| 16:59–17:04, 22:26–23:11 | Valuation: GOOGL 19× forward with 30% margins vs a 7% industry average; TSLA 166× vs an 11× median | Untested, since we have no point-in-time fundamentals (see the spec in 3VVjDDJvu2s) |

## Not tested, could be

Nothing beyond 3VVjDDJvu2s. The IV-rank vehicle switch is answered (`run_ivrank_vehicle.py`). The navigator rule and the
"alignment as a seller's selector" axis are specified in that note.
