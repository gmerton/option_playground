# The $MULN layup, dissected — catalyst analog, holder psychology, share turnover, and the day-2 failed drive

> **Verdict:** The clearest worked example in the KB of how he builds a long from a headline, and — unintentionally — a cross-source match for the repo's new FBO short detector.
> **Type:** setup (catalyst long → overnight momentum → day-2 failed-drive short) + review-process
> **Conviction:** 3/5 as a template, 1/5 as evidence · **Testability:** overnight-momentum piece EOD ⭐; the rest intraday · **Tested?** no
> **Source:** `-x1nbxasFcE` — How a Pro Trader Thinks: $MULN Layup Trades Dissected (2023-07-12; Mullen, a sub-20c EV name, July 5–7 2023)

---

## 1. Mechanics, in the order he thinks

1. **Timeframe weights** [02:07–02:20]: intraday ≈ 70% of the decision, 3-month chart ≈ 25%, multi-year ≈ 5%. He always looks at all three.
2. **Holder psychology = overhead supply** [03:02–04:27]: the stock had come from $300+ (split-adjusted) to 12c, so "unless you bought within the last month or two you are 99% out of the money" — those holders will never sell into a bounce, so there is no supply until recent buyers are in profit. Shorts riding it "to bankruptcy" are the trapped party.
3. **Catalyst + analog** [05:10–06:21]: a PR that management is "going after naked short selling." Pattern recognition from the Evernote database: **GNS** did the same in Jan 2023 and went 50c → $5–7. "The ticker that should be coming to your mind is GNS." Plus a speculative tape (AI, CVNA ripping) [06:33–06:55].
4. **The asymmetry math** [07:11–09:26]: risk = a penny or two + commissions; P(move ≥ 10c) "maybe above 50%"; upside 50–60c not preposterous. "I would be real interested in any reasonable assumptions where that's not super asymmetric." Entry: the headline, or **breaks to highs at 12–13c once volume confirms**, stop 10c.
5. **The overnight setup** [09:46–12:51]: closes very strong (up ~70%) on **abnormal volume (most in the market, 1.4B shares, multiples of float)** → **share turnover**: the average holder's cost basis resets to the low teens, "they're in the driver's seat." Shorts pay borrow and face unbounded loss for a 16c max gain; longs risk almost nothing. Scanners pick it up after hours → more attention. That is the whole overnight thesis: skew + turnover + attention.
6. **Day 2** [13:03–16:03]: he refuses to sell +5c at 22c ("between commissions and how beaten down the stock is... I want to have a little imagination"). An 8am buyback PR locks up more float. Pre-market builds resistance at 30c.
7. **The failed drive = the short (or the get-flat)** [17:25–20:54]: breaks 30c on great volume, **can't hold it, falls back below** — "that changes the probability spectrum." Then a **lower high** near the highs, then a break of the mini-support **below VWAP and the moving average**: "that is the moment of truth... that's where I think the short entry is, that's where I think the get-flat is," stop against the highs. He would not short just because it is day 2 ("I don't love shorting on the second day up"); the failure of the drive is the reason.
8. **Cover** [21:05]: low 20s — "if you're not covering around the low 20s that's a little crazy."
9. **Day 3+** [24:24–24:57]: "no play" — ranges too tight for the price. The plays were day 1 and day 2.

## 2. ⚠ The sizing-lever question

Stop 10c vs entry 12–13c ≈ **15–25%** — this is a sub-20c stock, so the % is meaningless for the lever question; what matters is that the stop is a **level the trapped party defends** (the pre-headline price), and he sizes to the asymmetry, not to a % rule. Overnight size is not stated here (see `risk-management-15-lessons.md`: overnights at ½–⅓ of intraday size).

## 3. Claimed edge & evidence

"One of the easiest layups of the year"; many SMB / pod traders were on it; no P&L given ("a little disappointed it didn't go further"). N = 1, in a tape he himself calls speculative. GNS as the analog is one prior instance.

## 4. ⚠ Prop-infrastructure dependency

**High.** The pod ("I texted my pod... they'd been on it all day"; the bear case arriving in real time from pod members at 30c) is explicitly part of the process. Locates/borrow on a 16c stock, sub-penny commissions, and Bloomberg/dilution-tracker float data are all prop-grade. The long side is the transferable half.

## 5. Collisions with the repo

- ⭐ **Cross-source corroboration for the FBO short detector** (`src/lib/alerts/detectors.py`, built 2026-09-09): his day-2 entry is exactly "drive above the level, fail to hold, lower high, break of support below VWAP → short, stop at the highs." The detector requires a 5-min close above the level then a 5-min close back below it and VWAP. His version adds the **lower high** between failure and break — worth testing as an extra gate once the scorecard has a sample.
- **Overnight-momentum setup is an EOD event study** the repo can run now: close in the top X% of the range, up ≥50%, volume ≥ k × ADV and ≥ float, price < $5 → next-day open and high. Same family as `ipo-strategies.md`'s overnight momentum; the small-cap universe is the constraint on data.
- **"Who's trapped"** — the counterparty field already stolen for the playbook (`no-mans-land-and-process.md`) gets its best worked example here: 99%-out-of-the-money holders (no supply) + shorts riding to zero (forced buyers).
- ⚠ **Dated:** July 2023 low-float naked-short-PR meme cycle. Flow niches decay; the mechanism (turnover resets the holder base) is the durable part.
