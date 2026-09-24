# tastylive / Market Measures: "Everyone Panics During Earnings Season. 13 Years of VIX Data Says Don't Bother." (2026-05-17, 10:21)

_Reviewed 2026-09-23 for the Sosnoff "sell vol when it's high" wave. Tony Battista and Ryan read a research-desk
deck (00:00-07:17); the rest is opening-bell market chatter. Transcript (`en-orig` auto-captions) in this folder._

## Verdict: 2 / 5

A true, modest and nearly self-evident result: **the VIX isn't systematically higher during earnings seasons**,
because single-name event vol diversifies away in an index. Ryan predicts it before the slide (01:18-01:45), and
Tony calls it "CliffNotes" (06:40). The method is crude but fit for this purpose:
- "number of times VIX made a new high" (undefined);
- the wider-range counts;
- mean and median VIX by season.

It loses points because it answers a question no trade depends on. There is no strategy, no P&L and no
significance test, and the transcript and the video description disagree on the headline average.

## Data audit

| item | what the video gives |
|---|---|
| sample | VIX daily, "since 2013" through April 2026 (02:00-02:22) |
| n | **50 earnings seasons** (4 per year + 2 in 2026), each "about 6 weeks" |
| rules | earnings season vs non-earnings season windows; metrics = VIX new highs, VIX high-low range, mean/median VIX |
| definitions | "new high" is **undefined** (all-time? within-season? vs the prior window?); season boundaries unstated |
| fills / costs | n/a, no trade |
| control | the non-earnings windows are the control. Fair, but consecutive windows aren't independent (VIX regimes last longer than 6 weeks) |
| tail shown? | n/a |
| significance | none; "I don't even think it's statistically important… basically 50/50" (03:18-03:24) |
| selection | none apparent |

## Their numbers (transcribed)

| @ | number |
|---|---|
| 00:55 | single stocks stay inside the expected move "about **68%** of the time" |
| 02:00-02:05 | earnings season ≈ **6 weeks**; **50** seasons since 2013 |
| 03:10-03:15 | VIX new highs: **26** during earnings season vs **24** outside |
| 03:55 | wider VIX range: **25 vs 25** |
| 04:57-05:02 | earnings season VIX **mean ~19, median ~16**; non-earnings **19 and 17** (⚠ the video description instead says "average during earnings **19**, outside **17**". Transcript and description disagree; the transcript reading is the one on camera) |
| 05:52 | single names show vol expansion into earnings "usually more than **70%** of the time" |

## Claim-by-claim

| @ | claim | our evidence |
|---|---|---|
| 03:03 | the VIX isn't sensitive to earnings season (26 vs 24 new highs) | ✅ **Agrees in kind, not tested directly.** Closest row: scheduled macro events carry no index information. FOMC = noise (SPY T−5→T0 +0.47%, t 1.5; archetype D flips sign across k), `fomc_event_study_2026-09-18.md`, §7 catalysts row. Nothing here would change a trade |
| 06:28 | "almost no correlation between index IV and single-stock IV during earnings season" | Plausible (index = diversified basket; single-name event vol is idiosyncratic), but they show no correlation number. The implied trade is dispersion (sell single-name event vol, buy index), and its short leg already fails here: **earnings vol premium +0.601% at mid, −0.428% at the bid, crossing costs 171% of gross** (§9 "Earnings vol premium" row). The dispersion trade dies on the single-name spread before the index leg matters |
| 00:55 / 05:52 | stocks stay inside the expected move ~68%; single-name IV expands into earnings >70% of the time | The ramp is real but not capturable: pre-earnings vol RAMP, buy ATM straddle −3/−5/−10 bd, lost −3 to −14% at mid (§9 ramp row; 30-45 DTE version queued-declined, §10). "Inside the expected move 68%" is the 1-SD definition, not an edge; the premium question is answered by the vol-premium row above |
| 05:28 | "I like post-earnings trades" (Tony) | Post-catalyst entry NULL (DR-EP arm B −0.067R, t 0.21); PEAD NULL (memory: earnings ledger closed 2026-09-20) |
| 04:36 | don't buy S&P puts / VIX calls because of single-stock earnings | ✅ Consistent with FOMC-noise and with the event-convexity result being about **calls on high-ADR names** before macro events, not index puts |

## "Sell high vol": index-after-stress, per-name, or neither?

**Neither.** The study conditions on the calendar, not on the vol level, and has no P&L. One indirect implication
supports our reading: **a single-name IV that is "high" because an event is pending isn't a premium to sell at real
fills.** The earnings premium is real at mid and negative at the bid, and its selectivity lever inverts (the q5
implied move is the *worst* at the bid). That's another per-name "sell high IV" failure, and it's already in the
ledger.

## What I would take

- **Nothing new to act on.** "Earnings season" isn't a regime variable for index premium. Keep conditioning the
  index cell on the VIX level / stress state, not the calendar.

## Not tested, could be

- **Nothing genuinely new.** "Sell index premium during vs outside earnings seasons" would be a new *axis*, but
  their own data says the VIX (the thing our certified cell conditions on) is the same in both. There's no
  mechanism for a difference beyond the VIX level, and it would cost a multiple-testing charge on our one certified
  bucket. Not proposed.
- Dispersion (short single-name event straddles / long index) is new as a *structure*, but its short leg fails
  on the spread already (−0.428% at the bid, 171% cost). Not proposed.
