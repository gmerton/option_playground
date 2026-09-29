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
