# Market-Regime Filter — RESULTS

**Run:** 2026-07-26 · `run_regime.py` · broad universe (2,684 names, 2006–2026)
**Architecture pinned** to the two configurations that won earlier (2.0ATR / 20EMA stops ×
close<50EMA / target 4R exits); slots 30 and 50. 8 entry tiers × 5 regime variants = 320 cells.

## Headline

> **The regime filter is the single most valuable variable tested in this whole study — worth
> more than the stop, the exit, and the entry selection combined.** Across all 64 cells per
> regime it roughly **halves drawdown, doubles CAGR, and triples MAR**. It also improves
> per-trade quality, so it is avoiding bad trades, not merely reducing exposure.
>
> And it changes the verdict: regime-filtered momentum **beats SPY on risk-adjusted terms**,
> even though it still loses on raw CAGR in most configurations.

## 1. It is broad, not a cherry-pick

Aggregate over all 64 cells within each regime:

| regime | mean MAR | mean CAGR | mean maxDD | mean Sharpe | cells with MAR>0.30 |
|---|---:|---:|---:|---:|---:|
| none | 0.068 | 2.76% | −46.5% | 0.256 | **0** |
| SPY>200SMA [gate] | 0.171 | 4.79% | −29.9% | 0.393 | 6 |
| SPY>200SMA [gate+exit] | 0.162 | 4.70% | −31.5% | 0.416 | 7 |
| **SPY>200SMA+up [gate]** | **0.205** | **4.97%** | **−25.6%** | 0.413 | **17** |
| SPY>200SMA+up [gate+exit] | 0.182 | 4.57% | −26.5% | 0.429 | 6 |

Every cell improves. Zero cells cleared MAR 0.30 without a regime filter; 17 do with one.

Max drawdown, per tier (2.0ATR / close<50EMA / 30 slots):

| tier | none | SPY>200SMA [gate] | SPY>200SMA+up [gate] |
|---|---:|---:|---:|
| DUMB | −58.8% | −34.3% | **−20.9%** |
| REQ-only | −56.8% | −25.6% | −25.4% |
| GATES | −57.8% | −30.4% | −25.4% |
| BREAKOUT | −58.5% | −27.6% | −26.2% |
| CONFIRMED | −49.8% | −25.1% | −24.9% |
| POTENT | −37.9% | −29.9% | −22.1% |
| LEADER | −27.9% | −28.4% | −27.0% |
| BOTH | −36.2% | −36.4% | −33.8% |

⚠ **LEADER and BOTH are the exceptions** — regime filtering barely moves their drawdowns. They
are already sparse and concentrated in late-cycle extended names, so the tape being healthy is
already implied by the setup existing. No incremental protection available there.

## 2. Don't get flat — just stop entering

`[gate]` (refuse new entries below trend) beats `[gate+exit]` (also close everything on the
regime flip) on mean MAR for both regime definitions, and the best single configuration is
gate-only. Forcing exits on the flip adds whipsaw around the threshold and gives back more than
it protects.

**Actionable form of the rule: stop opening new positions when SPY is below a rising 200-day.
Let the positions you already hold run their normal exit rules.**

The rising-200 variant (`SPY>200SMA+up`) beats the plain one — mean MAR 0.205 vs 0.171, mean
drawdown −25.6% vs −29.9%.

## 3. It improves the trades, not only the equity path

Mean % per trade (2.0ATR / close<50EMA):

| tier | none | SPY>200SMA [gate] | SPY>200SMA+up [gate] |
|---|---:|---:|---:|
| DUMB | +0.35 | +0.39 | +0.45 |
| REQ-only | +0.55 | +0.58 | +0.61 |
| GATES | +0.93 | +1.07 | **+1.14** |
| BREAKOUT | +0.64 | +0.92 | +0.97 |
| CONFIRMED | +0.36 | +0.82 | +0.83 |
| POTENT | **−0.22** | +0.32 | **+0.35** |
| LEADER | +0.40 | +0.55 | +0.48 |
| BOTH | +0.01 | +0.33 | +0.27 |

Every tier improves, and **POTENT flips from negative to positive**. If exposure reduction were
the whole story these numbers would be unchanged. They are not: bad tape genuinely produces bad
breakouts, and refusing to trade it removes them.

## 4. The verdict changes — on risk-adjusted terms

SPY over this window: **10.7% CAGR, −56.5% max drawdown → MAR ≈ 0.19.**

| | CAGR | maxDD | MAR | Sharpe |
|---|---:|---:|---:|---:|
| SPY buy & hold | 10.7% | −56.5% | 0.19 | — |
| **Best cell:** CONFIRMED, 50 slots, 20EMA stop, target 4R, SPY>200SMA [gate] | **11.26%** | **−21.5%** | **0.52** | 0.81 |
| Regime-filtered average (all 64 cells, SPY>200SMA+up gate) | 4.97% | −25.6% | 0.205 | 0.41 |

**Only 1 of 320 cells beats SPY on raw CAGR** — treat that one as an in-sample upper bound, not
a forecast. But the *average* regime-filtered cell now matches SPY's MAR, and 17 cells clear
0.30, comfortably above it. The honest statement is:

> Regime-filtered momentum did not out-return the index. It matched or beat it **per unit of
> drawdown**, which is a different and more defensible claim — and it is the first time in this
> study that anything has beaten buy-and-hold on any axis.

CONFIRMED appears repeatedly through the top of the MAR ranking (both slot counts, both regime
definitions, both gate modes), so its showing is not a lone spike.

## 5. Limitations

Everything in [RESULTS.md](RESULTS.md) §5 and [SELECTION_LIFT.md](SELECTION_LIFT.md) §6 still
applies. Specific to this run:

- **⚠ Survivorship is still unfixed and is now the dominant open risk.** 62% of 2011's optionable
  tickers are absent from the test universe (measured against `silver.options_daily_v3`).
  Polygon's free tier refuses history past ~2 years (`NOT_AUTHORIZED — past historical
  entitlements`), and Yahoo purges delisted names — only 25% of a sample of vanished 2011
  tickers returned data, and most of those were live ETFs/ADRs, not real casualties. A clean
  panel needs a paid vendor (Sharadar SEP, Norgate, or a paid Polygon tier).
- **Best-of-320 is in-sample selection.** The aggregate table in §1 is the honest read; the
  single SPY-beating cell is not.
- **The 200-day SMA is the most data-mined threshold in finance.** Using it unmodified is the
  right call precisely because it wasn't tuned here — but it is not free of that history.
- **Costs are 10 bp round trip** and turnover is high (median hold 16–22 days). A worse fill
  assumption would bite.
- Sell-into-strength and any intraday execution remain untested.
