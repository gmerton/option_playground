# Does every Minervini Trend Template criterion earn its place? (2026-09-22)

**Verdict: 2 criteria RETRACTED as logically redundant (proven, not estimated) · the other 8 UNDERPOWERED —
none individually certifies, and the whole template buys ~0.58pp of 20d excess.**
Script: `run_trend_template_ablation.py` (pre-registered in its docstring) · log + `…_2026-09-22.csv`.

Gabe, 2026-09-22: *"I'm skeptical that every criterion of the Minervini adds value."* The template had only
ever been tested **whole** — `universe_test_2026-09-21.md` found it the weakest of five universes ADR-matched,
and HYB-B (TT core at a $100M floor + ADR ≥ 4) beat it. The nine conjuncts had never been scored individually.

## Method

Leave-one-out ablation on the liquid panel, 2020-01 → 2026-09. Rebuild the universe ten times, each dropping
one criterion. **Primary statistic is paired and holds the date fixed**: per non-overlapping 20-session date,
`delta(k) = mean forward return of members WITHOUT k − mean forward return of full-TT members`. A criterion
cannot look good merely by being in the universe on good days.

Every cell is **ADR-matched** — the benchmark is reweighted to the members' own ADR-decile mix — so an arm
cannot win by admitting more volatile names. Bar: Šidák over 20 cells, **|t| ≥ 3.02**, plus halves agreeing.

`delta < 0` = dropping it hurts = the criterion **adds**. `delta > 0` = it **subtracts**.

## Result 1 — c1 and c2 are mathematically redundant, and this is provable

Dropping *close > 150 SMA* or *close > 200 SMA* changes **nothing**: the mask is bit-identical to the full
template (114,829 member-days either way), delta exactly 0.000 at both horizons. They are not "statistically
inert" — they are **logically entailed** by the criteria that follow them:

```
c6 (close > 50 SMA)  ∧  c5 (50 SMA > 150 SMA)                    ⟹  c1 (close > 150 SMA)
c6 ∧ c5 ∧ c3 (150 SMA > 200 SMA)                                 ⟹  c2 (close > 200 SMA)
```

Verified directly on every eligible cell: no counterexample exists. **Two of the nine criteria carry zero
information.** They cost nothing in returns, but they are two of the nine things being checked, maintained
and explained — and their presence makes the template look more selective than it is.

## Result 2 — no remaining criterion clears the bar

20d horizon, ADR-matched, ordered by contribution (full TT: 66 names/day, median ADR 2.83%, **+0.575pp**
20d excess over the ADR-matched panel):

| dropped | names/day | Δ adj (pp) | t | halves | reading |
|---|---|---|---|---|---|
| c10 ADDV ≥ $200M | 66 → **166** | **−0.259** | −1.46 | −0.11 / −0.38 | adds most, costs most |
| c9 RS ≥ 70 | 66 → 98 | −0.090 | −0.95 | −0.03 / −0.14 | directionally adds |
| c8 within 25% of high | 66 → 67 | −0.082 | −1.39 | −0.03 / −0.12 | directionally adds |
| c7 ≥ 30% off the low | 66 → 67 | −0.067 | −1.79 | −0.12 / −0.03 | highest \|t\|, still short |
| c3 150 > 200 | 66 → 70 | −0.053 | −1.03 | −0.06 / −0.05 | directionally adds |
| c4 200 SMA rising | 66 → 66 | −0.028 | −1.14 | −0.05 / −0.01 | ~nothing |
| c5 50 > 150 | 66 → 69 | −0.006 | −0.13 | −0.01 / −0.00 | **nothing** |
| c6 close > 50 SMA | 66 → 77 | **+0.038** | +0.29 | +0.09 / −0.00 | only one that *subtracts*, halves disagree |
| c1, c2 | 66 → 66 | 0.000 | — | — | **redundant (above)** |

**Nothing reaches |t| ≥ 3.02.** Every non-redundant criterion is UNDERPOWERED, not disproven — with ~85
non-overlapping 20d dates, a 0.1pp effect is not resolvable. That is itself the finding: *the template's
criteria are individually too small to measure*, and the template as a whole buys just **+0.575pp per 20
sessions** over an ADR-matched liquid panel.

At 5d the picture is the same and smaller (full TT +0.115pp); c5 and c6 flip positive (+0.020, +0.026),
reinforcing that the 50-SMA-relationship criteria are the weakest of the set.

## What is actually actionable

1. **Drop c1 and c2.** Proven redundant. Free simplification, nine criteria become seven.
2. **c10 (ADDV ≥ $200M) is the criterion to re-tune, not keep as-is.** It is the largest single contributor
   (−0.259pp) but it is also *by far* the most expensive: it discards **60% of the universe** (166 → 66
   names) to buy that. The parent universe test already found HYB-B — the same core at a $100M floor plus
   ADR ≥ 4 — beats full TT. This ablation says why: the floor is doing real work, but $200M is a blunt
   setting of it, and ADR is a better second axis than raw dollar volume.
3. **c5 and c6 are candidates for removal on cost grounds.** c5 contributes −0.006pp (indistinguishable from
   zero) and c6 is the only criterion that is directionally *negative* while also costing 11 names/day.
   ⚠ Neither is certified — removing them is a bet on "small and unmeasurable" being "zero."
4. **Note the ADR mix.** Full TT sits at median ADR **2.83%**, below the 3–4% the breakout book wants. The
   template selects large, liquid, low-volatility names — consistent with the same day's finding that
   dollar-volume ranking is the one thing that sorts breakouts (and is era-bound).

## Caveats

* **Survivorship**: the panel is today's liquid names, so arms are comparable with each other but the
  absolute excess is optimistic.
* RS percentile is ranked inside the 1,742-name liquid panel, not the ~5k Polygon universe production ranks
  against, so c9 is *weaker here* than in production. Its real contribution may be larger.
* This measures **universe selection only** (Q1). It does not re-ask whether the house breakout works inside
  each variant (Q2) — and the parent test already found no universe fixes the entry.
