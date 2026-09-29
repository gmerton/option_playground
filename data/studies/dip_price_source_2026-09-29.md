# Dip-in-uptrend: is the sign flip the PRICE SOURCE or the DEFINITION? (2026-09-29)

## Pre-registration (written BEFORE the run; do not edit this section after the results)

**Why.** Audit step 3 item 6 (`audit_top_down_2026-09-25.md` List A #7). The ladder's P2 dip effect (+0.7…+1.4pp / 20d
vs same-date non-dippers, t 2.5–5.5; OHLC definitions on `liquid_panel_2009`) flipped to **−0.88pp (t −3.79)** when
re-specified close-only on chain-spot parity closes for the same survivor names (`dip_survivorship_2026-09-25.md`, T1).
Two things changed at once: the price source and the definitions. This isolates them.

**The one cell.** `run_dip_survivorship.run()` UNCHANGED (close-only ADRp with the same k, P2c, 10-close peak, 1-ADRp
episode, K0/K3 rungs, ADRp-tercile same-date control from the same group, 20d close→close, 10 bp/side), fed the
**survivor panel's own split-adjusted closes** (`liquid_panel_2009.close`) instead of chain-spot closes. Same tickers
(survivor names present in chain-spot), same dates (chain-spot's index, 2010 → 2026-01), same liquidity gate
(chain-spot 50d option volume ≥ 1,000 and close ≥ $5). Only the close series differs.

**Primary.** SURV, P2, K0, month-clustered excess (as T1). Secondary: K3.

**Read (declared now).**
- Panel-close K0 **≤ 0** → the flip is the **definition**: the +1pp needs the OHLC/ADR specification → dip-in-uptrend is
  definition-fragile → PARKED becomes **NULL (fragile)**, and the survivorship question is moot.
- Panel-close K0 **≥ +0.5pp with t ≥ 2** → the flip is the **price source**: chain-spot closes misbehave for this
  purpose → dip-in-uptrend stays PARKED and survivorship stays unresolved (needs a better delisted-name series).
- Anything between → ambiguous; both explanations contribute; stays PARKED.

**Also reported:** the chain-spot run on the identical sample (should reproduce −0.88), and the median per-name
correlation of daily returns between the two close series (a data sanity check). Local; no Athena (cached).

---

## Results (run 2026-09-29, after the pre-registration above was committed in fb0e91a; `run_dip_price_source.py`, `.log`, `.csv`)

**Verdict: the DEFINITION drives the flip, not the price source → dip-in-uptrend goes PARKED → NULL (definition-
fragile). The survivorship question is moot.**

1,686 survivor names in both sources, 2010-01 → 2026-02; daily-return correlation chain vs panel median 0.95.

| close series | P2 K0 excess (20d) | t | halves | P2 K3 excess | t |
|---|---|---|---|---|---|
| chain-spot (reproduces T1) | −0.81pp | −3.47 | −0.72 / −0.89 | −0.80 | −4.32 |
| **survivor panel's own closes** | **−0.79pp** | **−4.22** | −0.45 / −1.09 | −0.74 | −4.04 |

Swapping the price series changes nothing. The close-only specification, run on the ladder's own data, gives a
**significant negative** dip effect (14/17 years), while the ladder's OHLC/ADR specification on the same names gives
+0.7…+1.4pp. The same idea is significant with opposite signs depending on how "dip" and "uptrend" are written down:
it is not an effect, it is a property of the definitions. (Level gap chain/panel median 7%: the panel is dividend-
adjusted; irrelevant to returns.)

**What it means for the book now.** Nothing to trade: "buy the dip in an uptrend" is closed as NULL (fragile). This
also covers the Quantified Strategies RSI(3) version (row 419), which leans on the same mechanism.
