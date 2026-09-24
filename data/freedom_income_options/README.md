# Freedom Income Options KB

YouTube channel "Freedom Income Options" (`UC0hD4cIZ_RnvuVjBXWYMOiQ`, site freedomincomeoptions.com). Income-framed
premium selling: weekly 45-DTE short puts on ES / MES futures, plus cash-secured puts for small accounts. The
channel popularises tastytrade / Tom Sosnoff mechanics as a "weekly paycheck". Every video funnels to a paid members
community and a "case study" page. Skeptic-default scoring like every KB here.

Captions come down with yt-dlp (`en-orig` auto track). `videos/<date>_<id>/` holds `transcript.txt`, `meta.json`,
`notes.md`.
⚠ **Read the transcript, not the description.** On the first video they disagree on whether the account is real
money or simulated, and on which delta is "Tom's".

| video | date | verdict |
|---|---|---|
| [I Tested Tom Sosnoff's Strategy for 3 Months](videos/2026-05-28_JMso3dDSg5A/notes.md) | 2026-05-28 | **2/5.** A complete tastytrade rule set (ES 10Δ put, 45 DTE, 50% take, 21-DTE management, 1 lot/week) on a **$75k simulated** account. $11,357.50 from ≈ 13 entries, all winners, **effective n ≈ 1**. The window (2026-02 → 05) was close to ideal: a −8.8% selloff to VIX 31, then a +20% V-rally to new highs. His best month (March) is exactly our certified bearish-high-IV index put cell. Pre-spike entries (VIX ~20) model as losers at 21 DTE. Contradicted: "you make more money in a crash" (conflates new-entry premium with open-position P&L), "4 bear markets in 20 years" (2008 and 2009 are one), "~90% probability = safety" (POP ≠ edge). ~$1–1.4M of short-put notional on $75k is never stated |

## Cross-references

- Sosnoff's own rule set (45-DTE ~20Δ strangle, 21-DTE management, IV rank): [OptionsPlay interview
  notes](../optionsplay/videos/2024-10-14_pQlGgcyrUoQ/notes.md) and the [More Tom KB](../more_tom/README.md).
- The 21-DTE exit was tested directly: ~~PASS as an exit (paired +$1.53, t 4.26), both arms negative~~ (corrected 2026-09-24, FIX-1: original run dropped worthless-expiry winners).
  Fixed: 21-DTE close − hold **−$0.52/share, month-clustered t −2.42** (hold +$0.23, 74% win; 21-DTE −$0.29, 64% win; n 14,367) → **NULL on return, leaning INVERTED; a risk reducer only** (sd $9.33 vs $17.09, worst −$291 vs −$617) (TEST_INDEX §1,
  `data/studies/exit_21dte_2026-09-23_fixed.csv`; the old SPY rows −$1.77 held / −$0.46 managed came from the buggy
  run and are not re-derived).
- The certified index put sale: `data/studies/tierab_significance_2026-09-22.csv` (SPY bull put Bearish_HighIV
  t 6.07, SPX condor t 5.21, one bet).
- **Gap:** a naked 10Δ index put at 45/50%/21 DTE, always-on, at real fills, has never been run. Neither has
  anything on futures options. The spec is in the video notes; it is not queued.

## Not downloaded

- "45-Day Put Selling Strategy | Tom Sosnoff's Proven Trade" (`0f2kr2iOXzg`). It's in the owner's Watch Later.
  This is the strategy explainer the 3-month test is based on.
- The challenge launch video (`Q3Rmbs5_nEM`). It should give the **start date of the test**, which decides whether
  his "no losses" survives his own 21-DTE rule (see the audit in the notes).
