# Review: "Building a Universe List!" (Ariel Hernandez, 2026-01-11, I_VMUnJ_xJo) — 3/5

Reviewed 2026-09-21. Transcript: `videos/education/2026-01-11_I_VMUnJ_xJo/`.

## His process

1. **Groups first.** Nightly/weekly: equal-weight + sector/thematic ETFs on Finviz sorted by YTD performance ("where money
   went, where it left"); click the leading ETF (WGMI bitcoin miners, SHLD defense, oil services) and pick its most liquid,
   cleanest members. Don't take the whole group: IREN/CIFR yes, BITF/CORZ/HIVE/RIOT "not good enough".
2. **Scans.** Favourite = high momentum: ≥70% above the 52-week low, ≥2M shares/day, price > $7, above the 50 SMA,
   mcap > $300M (or > $1B). Plus a CANSLIM-style earnings + sales scan, Deepvue "emerging" scans, thinkorswim scans,
   and the day's biggest movers on big volume (AEVA) added on the spot.
3. **Discretionary admission.** "Has it shown the ability to make a big clean linear move?", dollar volume ≥ $100M/day
   (his size; smaller accounts can go lower), in a working theme. Known mega caps he already watches by eye (MSFT, AAPL,
   META) and slow trenders (RTX, LMT) are left off.
4. **Universe = 100–150 names, refined continuously**; built once over "two or three weekends", then the nightly work is
   only walking the universe.
5. **Nightly cut = a setup he trades**: flat base, high-tight flag, high-volume close, higher low, undercut-and-rally.
   ≤ 20 names on the nightly list, 8–15 with alerts. No setup → stays in the universe, not on the list (BE, CEN).
6. Avoid names under the 200-day and downtrends (NFLX, SPOT); "stocks going up tend to keep going up".

## Against our universe (preferred list) — measured on the 9/18 close

Ours = Minervini Trend Template (price > 150/200 SMA, 50 > 150 > 200, rising 200, ≥30% off the low, ≤25% off the high,
RS percentile ≥ 70) + ADDV > **$200M**. His momentum scan run on the same Polygon cache (market cap not in the cache, so
that gate is omitted):

| | names |
|---|---|
| his momentum scan (70% off low, > 50 SMA, ≥2M sh, > $7) | 153 |
| + his $100M dollar-volume floor | **99** |
| our Trend Template passers | **89** |
| in both | 46 |
| his only | 53 |
| ours only | 43 |

- **His-only (53)** are the high-momentum names our template rejects: 26 trade $100–200M/day (under our $200M floor),
  25 are more than 25% off their high after a correction (SPCX, MRVL, NBIS, COHR, AXTI, DOCN, HUT), 29 have an
  unaligned MA stack (HOOD, WDAY, TEAM). Examples: SPCX, MRVL, NBIS, MSTR, HOOD, COHR, SMCI, CRCL, AXTI, HUT, DOCN, RIOT.
- **Ours-only (43)** are slow large caps his scan can't reach: median only 58% off the low, 34 of 43 under his 70% bar —
  AAPL, KO, JNJ, XOM, CVX, COP, ABBV, GILD, MET, TD, TRV. That's exactly the "RTX: fine trend, not a name I'd buy" group
  he leaves off by hand.
- Net: his universe is **higher-momentum, higher-ADR and less liquid**; ours carries a defensive large-cap tail that
  qualifies on trend alone.

## What our evidence says about each piece

| His claim | Our evidence | Verdict |
|---|---|---|
| Groups first (leading ETF YTD) | Rotation study: leading-group filtering INVERTED (bottom-3 sectors beat top-3, t 2.6); industry RS = context only | **Contradicted** — use groups as context, not a filter |
| Momentum universe → setups | "We select well, we enter badly": the layer-2 state works; the breakout ENTRY is the leak | **Agrees** on selection |
| 70% off low beats a trend template | Untested. Our template is 30% off the low | **Testable → queued** |
| $100M floor (vs our $200M) | Untested for the equity book; for options, liquidity was the only gate that worked | **Testable → queued** (cost matters for option vehicles) |
| Add big-volume movers on the spot (AEVA) | Tito archetype B (catalyst) = no edge; FTD/post-event names better as a STATE, not a moment | Mixed |
| "Shown a clean linear move before" | Discretionary, no definition | Untestable as stated |
| ≤ 20 names nightly, 8–15 alerts | Matches our finding that coverage, not detector quality, is the constraint; alerts ≈ random entries | Agrees (process hygiene) |

## Score: 3/5

A concrete, reproducible funnel with numeric scans, and the selection half matches what our data supports. It loses points
for groups-first (our data inverts it), a discretionary admission test with no definition, and no evidence offered for any
cut. His entry styles (higher low, undercut-and-rally, flat base) are the ones our daily-bar entry studies found weakest.

## Follow-up

- Queued in TEST_INDEX §10: **universe test, 5 pre-registered arms** (spec below).

## Universe test spec (pre-registered 2026-09-21, before any result)

Each universe is a daily membership mask on the liquid panel (`data/cache/liquid_panel_2019.parquet`, ADDV ≥ $50M),
computed from data through the prior close only. Hybrids are fixed HERE, from each side's stated rationale, so
"best of each" can't be picked after seeing which cells won.

| arm | definition | why |
|---|---|---|
| **TT** | Trend Template c1–c8, RS pct ≥ 70, ADDV ≥ $200M | our current list (baseline) |
| **AH** | ≥ 70% off 52w low, > 50 SMA, ≥ 2M sh/day, > $7, ADDV ≥ $100M | his momentum scan |
| **INT** | TT ∩ AH | names both methods agree on |
| **HYB-A** | AH + price > 200 SMA + 200 SMA rising + ADR ≥ 4% | his momentum and liquidity, our Stage-2 guard; no "≤25% off high" rule, so correction-recovery leaders (MRVL, NBIS, COHR 9/18) stay; ADR ≥ 4 makes his by-hand "too slow" exclusion mechanical |
| **HYB-B** | TT at ADDV ≥ $100M + ADR ≥ 4% | our structure, his liquidity floor and speed; drops the slow large-cap tail (KO, JNJ, XOM) |

ADR ≥ 4% is the lower edge of the existing precision tier (Adhikary validation), not a new tuned number. His market-cap
gate is omitted (not in the panel); ADDV ≥ $100M does most of that work.

**Three questions per arm**, 2019-01 → 2026-09:
1. **Does the universe select?** Random-entry forward 5/20-day return inside the mask vs the whole panel, same dates
   (the `xname` idea at the universe level). This is the direct universe test; it needs no entry rule.
2. **Does the house breakout work inside it?** `run_daily` with the house breakout AND the mask, `entry_at="close"`,
   vs `control="post"`, with the `xname` control drawn from the SAME mask (else xname just re-measures question 1).
3. **Is it tradeable?** Names per day, monthly turnover, median ADR and ADDV (a 300-name universe can't be walked nightly;
   his cap is 150).

**Rules.** Pass bar = the harness bar (beats its control, both halves positive, |t| ≥ 3 on day-clustered means).
Five arms = five tries, so no arm "wins" on the best cell alone: a hybrid must beat BOTH parents on question 1 or 2 in
BOTH halves (split 2023-01-01). Effective n = episodes/dates, not trades. A universe that only wins by being bigger
doesn't count (compare per-trade and per-date, not totals). ⚠ The panel is today's liquid names (survivorship); read
the arms against each other, not as absolute returns. No hybrid gets added after the results are in; a new idea is
a new queued row.
- ⚠ Found while reviewing (not his point): the S3 preferred list was overwritten 9/20 23:28 PT by `deploy_breakout_lambda.sh`
  with the July 23 local copy (see the session recap).

**Arm sizes on the 9/18 close** (sanity check, not a result): TT 89 names (median ADR 3.3%), AH 99 (4.6%), INT 46 (4.3%),
HYB-A 55 (5.7%), HYB-B 46 (5.2%). Both hybrids sit well under his 150-name cap and roughly double our ADR. HYB-A keeps
correction-recovery names (COHR, CRCL, DOCN, HUT, AXTI); HYB-B adds $100–200M names TT drops (TXG, TGTX, VSAT, S, QRVO).

## Result (run 2026-09-21, same day) — `data/studies/universe_test_2026-09-21.md`

Selection, 20d ADR-matched excess: TT +0.56 (t 1.3, weakest) · AH +0.87 · INT +1.44 · HYB-A +1.19 · **HYB-B +1.79
(t 2.6, beats both parents in both halves) → PARKED**. HYB-A's raw lead was mostly ADR → NULL. No arm makes the breakout
entry beat a random later day. His scan does beat ours, but not significantly.
