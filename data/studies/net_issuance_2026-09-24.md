# Net share issuance as a veto on the breakout book (2026-09-24)

New free data: `run_sec_companyfacts_pull.py` → `data/cache/sec_companyfacts.parquet` (SEC XBRL company facts,
1,770,085 facts, 1,692 of 1,720 panel companies, filed 2009-04 → 2026-09, point-in-time on the filed date; share
counts, net income, revenue, assets, liabilities, equity, operating cash flow, long-term debt).
Test: `run_net_issuance.py` (pre-registration in the docstring); log `data/studies/logs/net_issuance.log`.
Issuance = 1-year change in the cover-page share count, split-adjusted (Polygon splits), known at the date; 2013 →.

**A — the anomaly in our liquid universe (monthly deciles, 60d ADR-matched excess, 161 months):** heavy issuers
(median +11.8%/yr) **−0.08pp (t −0.27)** — no issuer penalty; net buybacks (median −7.6%) **+0.71pp (t +2.94)**;
buybacks − issuers +0.79 (t 1.80). The buyback side shows; the issuer side does not.

**PRIMARY — veto issuers (≥ +5%) from the precision tier: FAIL.** 1,556 of 2,016 trades scored: issuers −0.08%/trade
vs the rest +0.69%, **−1.16pp, t −1.40**, halves **+0.74 / −2.27** (disagree). Not monotone: +5–15% issuers −1.03%
but ≥ +15% +1.43%; buybacks +1.72%, flat +0.10%. The veto would have lifted the book +0.48 → +0.69%/trade by removing
27% of trades, but the split is not stable enough to certify.
**Lead (not pre-registered as primary):** the buyback tilt — +0.71pp at t 2.94 across the liquid universe, and buyback
names were the best tier bucket (+1.72%, n 241). A pre-registered buyback-preference test would be new.
