"""
Per-ticker configuration for the generic study runners (run_puts, run_call_spreads,
run_combined, run_optimizer).

Add a new ticker by adding a dict entry here — no runner files need to change.

Each entry is a dict with the following keys:

  start          : date — first entry date for the study. Should correspond to a
                   meaningful regime change (e.g. leverage change, index rebalance)
                   or simply the start of reliable options data for the ticker.

  split_dates    : list[date] — reverse-split dates within the study window.
                   Any position whose holding period spans one of these dates is
                   flagged and excluded from summary stats, because the option
                   strikes are rescaled by the split ratio and P&L comparisons
                   become meaningless across the split boundary.

  put_deltas     : list[float] — unsigned put delta targets swept by run_puts.
                   Higher IV underlyings support higher delta entries (more premium
                   per dollar of risk), so UVXY spans 0.10–0.40 while TLT stops at 0.30.

  short_deltas   : list[float] — unsigned short call delta targets swept by
                   run_call_spreads. Same logic as put_deltas.

  wing_widths    : list[float] — call spread wing widths in delta units. The long
                   call is bought at (short_delta - wing_width)Δ — i.e. further OTM.
                   Wider wings cap more loss but reduce the credit collected.

  vix_thresholds : list[float | None] — VIX filter levels swept by both runners.
                   None means no filter (enter regardless of VIX). Numeric values
                   skip entry when VIX >= threshold (puts) or < threshold (calls).

  Optimizer search bounds — all tuples of (low, high); step=0.05 for deltas/
  fractions, step=5.0 for VIX values. These define the Optuna TPE search space.

  opt_short_delta  : bounds for the call spread short leg delta.
  opt_put_delta    : bounds for the short put delta.
  opt_wing_width   : bounds for the call spread wing width.
  opt_profit_take  : bounds for the profit-take fraction (exit at this % of credit).
  opt_max_spread   : bounds for the max bid-ask spread filter on the short leg
                     (expressed as a fraction of mid; e.g. 0.25 = 25%).
  opt_put_vix_max  : bounds for the max VIX allowed to enter a short put.
  opt_call_vix_min : bounds for the min VIX required to enter a call spread
                     (0 = always enter; higher values restrict to elevated-vol days).
"""

from datetime import date

from lib.studies.straddle_study import (
    UVXY_SPLIT_DATES, TLT_SPLIT_DATES, GLD_SPLIT_DATES,
    XLE_SPLIT_DATES, XLV_SPLIT_DATES, XOP_SPLIT_DATES, USO_SPLIT_DATES,
    XLU_SPLIT_DATES, XLP_SPLIT_DATES, IWM_SPLIT_DATES, GDX_SPLIT_DATES,
    QQQ_SPLIT_DATES, INDA_SPLIT_DATES, UVIX_SPLIT_DATES, TMF_SPLIT_DATES,
    EEM_SPLIT_DATES, XLF_SPLIT_DATES, ASHR_SPLIT_DATES, FXI_SPLIT_DATES,
    SOXX_SPLIT_DATES, SQQQ_SPLIT_DATES, BJ_SPLIT_DATES, YINN_SPLIT_DATES,
    GEV_SPLIT_DATES, CLS_SPLIT_DATES, FN_SPLIT_DATES, CASY_SPLIT_DATES,
)


TICKER_CONFIG: dict[str, dict] = {

    "UVXY": {
        # UVXY changed from 2× to 1.5× leverage on 2018-01-12; data before this
        # date is not comparable to the current product structure.
        "start": date(2018, 1, 12),

        # Five reverse splits occurred post-leverage-change (1:5, 1:10, 1:10, 1:5, 1:5).
        "split_dates": UVXY_SPLIT_DATES,

        # UVXY's high IV (60–100%) supports higher-delta short puts — more premium,
        # more directional risk, but structurally UVXY decays toward zero over time.
        "put_deltas": [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40],

        # Short call deltas for bear call spreads; higher end viable due to high IV.
        "short_deltas": [0.30, 0.35, 0.40, 0.50],

        # Wider wings capture more protection; UVXY's wide markets make 0.20Δ feasible.
        "wing_widths": [0.10, 0.15, 0.20],

        # VIX filter sweep; for UVXY puts, entering when VIX is already elevated
        # is dangerous (UVXY spikes further). High VIX = skip puts.
        "vix_thresholds": [None, 30, 25, 20],

        # ── Optimizer search bounds ────────────────────────────────────────────
        # Higher short_delta ceiling — UVXY 0.50Δ calls have historically been
        # the most productive short strike given the structural decay.
        "opt_short_delta":  (0.30, 0.55),
        # Puts work well up to 0.45Δ in low-volatility regimes for UVXY.
        "opt_put_delta":    (0.10, 0.45),
        # Wings up to 0.25Δ are viable given UVXY's wide bid-ask markets.
        "opt_wing_width":   (0.05, 0.25),
        # Profit-take fraction: same range for all tickers.
        "opt_profit_take":  (0.30, 0.70),
        # Spread filter: slightly looser floor for UVXY's wider markets.
        "opt_max_spread":   (0.15, 0.40),
        # Max VIX to enter puts — UVXY spikes coincide with high VIX, so
        # 35 is the ceiling; going higher would let in the worst put trades.
        "opt_put_vix_max":  (15.0, 35.0),
        # Min VIX to enter call spreads — UVXY calls are most productive when
        # VIX is elevated (fear already in market, premium is higher).
        "opt_call_vix_min": (0.0,  25.0),
    },

    "TLT": {
        # 2018 covers: low-rate regime (2018–2019), COVID flight-to-safety (2020),
        # aggressive Fed hikes / TLT −31% (2022), and the subsequent recovery + cuts.
        "start": date(2018, 1, 1),

        # TLT has no reverse splits.
        "split_dates": TLT_SPLIT_DATES,

        # Lower delta targets than UVXY — TLT's IV (~15–20%) means OTM options
        # carry less premium per unit of delta, so we step lower to find the
        # credit/risk tradeoff sweet spot.
        "put_deltas": [0.10, 0.15, 0.20, 0.25, 0.30],

        # Short call deltas shifted lower for the same IV reason.
        "short_deltas": [0.15, 0.20, 0.25, 0.30, 0.35],

        # Narrower wings — TLT's tighter bid-ask supports smaller widths, and
        # the lower IV means a 0.05Δ wing still captures meaningful protection.
        "wing_widths": [0.05, 0.10, 0.15],

        # VIX thresholds — same initial levels as UVXY. Note that TLT often
        # rallies when VIX spikes (flight to safety = bond buying), which is the
        # opposite of UVXY's behavior. The optimizer will find the best regime filter.
        "vix_thresholds": [None, 30, 25, 20],

        # ── Optimizer search bounds ────────────────────────────────────────────
        # Narrower delta ranges calibrated to TLT's lower IV environment.
        "opt_short_delta":  (0.15, 0.40),
        "opt_put_delta":    (0.10, 0.35),
        "opt_wing_width":   (0.05, 0.20),
        # Profit-take fraction: same range for all tickers.
        "opt_profit_take":  (0.30, 0.70),
        # Slightly stricter floor — TLT's tighter markets mean a 10% spread
        # filter is realistic, whereas UVXY needs 15% as a minimum.
        "opt_max_spread":   (0.10, 0.40),
        # Wider VIX ceiling: TLT put behavior at VIX=45 is very different from
        # UVXY (TLT may actually rally in a fear spike = good for short puts).
        "opt_put_vix_max":  (15.0, 45.0),
        # Higher call_vix_min ceiling: TLT short calls may be more attractive in
        # high-vol regimes when TLT is selling off (rates rising = TLT falling).
        "opt_call_vix_min": (0.0,  30.0),
    },

    "GLD": {
        # 2018 covers: rate hike cycle (2018–2019), COVID flight-to-safety (2020),
        # inflation spike / Fed hikes (2022), and the subsequent gold rally into 2024.
        "start": date(2018, 1, 1),

        # GLD has no reverse splits.
        "split_dates": GLD_SPLIT_DATES,

        # Low IV (~10–15%) means OTM options carry limited premium; keep delta ≤ 0.35
        # to balance credit with probability of profit.
        "put_deltas": [0.10, 0.15, 0.20, 0.25, 0.30, 0.35],

        # Short put leg targets for bull put spreads; same range as put_deltas.
        "short_deltas": [0.15, 0.20, 0.25, 0.30, 0.35],

        # Narrow wings — tight GLD bid-ask supports 0.05Δ widths; 0.15Δ is the max
        # worth buying given the low premium environment.
        "wing_widths": [0.05, 0.10, 0.15],

        # VIX thresholds — GLD often rallies when VIX spikes (flight-to-safety),
        # so high-VIX entries may actually be beneficial for short puts.
        "vix_thresholds": [None, 30, 25, 20],

        # ── Optimizer search bounds ────────────────────────────────────────────
        "opt_short_delta":  (0.15, 0.40),
        "opt_put_delta":    (0.10, 0.35),
        "opt_wing_width":   (0.05, 0.20),
        "opt_profit_take":  (0.30, 0.70),
        "opt_max_spread":   (0.10, 0.40),
        # GLD may be safe to enter puts at higher VIX (flight-to-safety = GLD rallies).
        "opt_put_vix_max":  (15.0, 45.0),
        "opt_call_vix_min": (0.0,  30.0),
    },

    "XLE": {
        # Energy Select Sector SPDR. 2018 captures rate hike cycle, COVID crash/
        # recovery, and the 2022 energy supercycle (+65% that year alone).
        "start": date(2018, 1, 1),
        "split_dates": XLE_SPLIT_DATES,

        # IV ~20–30%; similar range to GLD/TLT.
        "put_deltas":   [0.15, 0.20, 0.25, 0.30, 0.35],
        "short_deltas": [0.15, 0.20, 0.25, 0.30, 0.35],
        "wing_widths":  [0.05, 0.10, 0.15],
        "vix_thresholds": [None, 30, 25, 20],

        "opt_short_delta":  (0.15, 0.40),
        "opt_put_delta":    (0.10, 0.35),
        "opt_wing_width":   (0.05, 0.20),
        "opt_profit_take":  (0.30, 0.70),
        "opt_max_spread":   (0.10, 0.40),
        "opt_put_vix_max":  (15.0, 45.0),
        "opt_call_vix_min": (0.0,  30.0),
    },

    "XLV": {
        # Health Care Select Sector SPDR. Defensive sector, low macro sensitivity,
        # steady earnings regardless of rate cycle or VIX regime.
        "start": date(2018, 1, 1),
        "split_dates": XLV_SPLIT_DATES,

        # Low IV (~15–20%); keep delta range conservative to ensure adequate premium.
        "put_deltas":   [0.10, 0.15, 0.20, 0.25, 0.30],
        "short_deltas": [0.10, 0.15, 0.20, 0.25, 0.30],
        "wing_widths":  [0.05, 0.10, 0.15],
        "vix_thresholds": [None, 30, 25, 20],

        "opt_short_delta":  (0.10, 0.35),
        "opt_put_delta":    (0.10, 0.30),
        "opt_wing_width":   (0.05, 0.20),
        "opt_profit_take":  (0.30, 0.70),
        "opt_max_spread":   (0.10, 0.40),
        "opt_put_vix_max":  (15.0, 45.0),
        "opt_call_vix_min": (0.0,  30.0),
    },

    "XOP": {
        # SPDR S&P Oil & Gas Exploration & Production ETF. Higher beta to oil
        # than XLE (no refining/pipeline diversification). Had a 1:4 reverse
        # split on 2020-06-09 during the COVID oil crash.
        "start": date(2018, 1, 1),
        "split_dates": XOP_SPLIT_DATES,

        # Higher IV (~30–45%) supports wider delta sweeps.
        "put_deltas":   [0.15, 0.20, 0.25, 0.30, 0.35, 0.40],
        "short_deltas": [0.15, 0.20, 0.25, 0.30, 0.35, 0.40],
        "wing_widths":  [0.05, 0.10, 0.15],
        "vix_thresholds": [None, 30, 25, 20],

        "opt_short_delta":  (0.15, 0.45),
        "opt_put_delta":    (0.10, 0.40),
        "opt_wing_width":   (0.05, 0.20),
        "opt_profit_take":  (0.30, 0.70),
        "opt_max_spread":   (0.10, 0.40),
        "opt_put_vix_max":  (15.0, 40.0),
        "opt_call_vix_min": (0.0,  30.0),
    },

    "XLP": {
        # Consumer Staples Select Sector SPDR. Non-cyclical, pricing-power driven,
        # structural upward bias. No sector-specific legislative risk (unlike XLV).
        # XLP had a 2:1 forward split in Oct 2019; delta-based selection handles this
        # naturally as strikes rescale with spot. No reverse splits.
        "start": date(2018, 1, 1),
        "split_dates": XLP_SPLIT_DATES,

        # Low IV (~12–18%); conservative delta range similar to XLV.
        "put_deltas":   [0.10, 0.15, 0.20, 0.25, 0.30],
        "short_deltas": [0.10, 0.15, 0.20, 0.25, 0.30],
        "wing_widths":  [0.05, 0.10, 0.15],
        "vix_thresholds": [None, 30, 25, 20],

        "opt_short_delta":  (0.10, 0.35),
        "opt_put_delta":    (0.10, 0.30),
        "opt_wing_width":   (0.05, 0.20),
        "opt_profit_take":  (0.30, 0.70),
        "opt_max_spread":   (0.10, 0.40),
        "opt_put_vix_max":  (15.0, 45.0),
        "opt_call_vix_min": (0.0,  30.0),
    },

    "XLU": {
        # Utilities Select Sector SPDR. Highly rate-sensitive; mean-reverts around
        # Fed expectations. Periodic IV spikes on rate surprises followed by calm —
        # ideal calendar spread candidate. No reverse splits.
        "start": date(2018, 1, 1),
        "split_dates": XLU_SPLIT_DATES,

        # Low IV (~15–20%); conservative delta range.
        "put_deltas":   [0.10, 0.15, 0.20, 0.25, 0.30],
        "short_deltas": [0.10, 0.15, 0.20, 0.25, 0.30],
        "wing_widths":  [0.05, 0.10, 0.15],
        "vix_thresholds": [None, 30, 25, 20],

        "opt_short_delta":  (0.10, 0.35),
        "opt_put_delta":    (0.10, 0.30),
        "opt_wing_width":   (0.05, 0.20),
        "opt_profit_take":  (0.30, 0.70),
        "opt_max_spread":   (0.10, 0.40),
        "opt_put_vix_max":  (15.0, 45.0),
        "opt_call_vix_min": (0.0,  30.0),
    },

    "QQQ": {
        # Invesco Nasdaq 100 ETF. Tech-heavy (Apple, Microsoft, Nvidia, etc.).
        # IV ~20–30% in normal regimes, spikes to 40%+ in risk-off. No reverse splits.
        # 2018 covers: rate hike cycle, COVID crash/recovery, 2022 bear market (−33%),
        # and the 2023–2024 AI-driven rally (+55%, +25%).
        "start": date(2018, 1, 1),
        "split_dates": QQQ_SPLIT_DATES,

        # Moderate IV — similar range to IWM but slightly lower beta moves.
        "put_deltas":   [0.10, 0.15, 0.20, 0.25, 0.30, 0.35],
        "short_deltas": [0.15, 0.20, 0.25, 0.30, 0.35, 0.40],
        "wing_widths":  [0.05, 0.10, 0.15],
        "vix_thresholds": [None, 30, 25, 20],

        "opt_short_delta":  (0.15, 0.45),
        "opt_put_delta":    (0.10, 0.40),
        "opt_wing_width":   (0.05, 0.20),
        "opt_profit_take":  (0.30, 0.70),
        "opt_max_spread":   (0.10, 0.40),
        "opt_put_vix_max":  (15.0, 45.0),
        "opt_call_vix_min": (0.0,  30.0),
    },

    "GDX": {
        # VanEck Gold Miners ETF. Tracks large gold/silver mining companies.
        # Higher beta to gold price (~1.5–2×), higher IV (~25–40%) than GLD.
        # Structural upward drift mirrors gold's inflation-hedge tailwind.
        # No reverse splits.
        "start": date(2018, 1, 1),
        "split_dates": GDX_SPLIT_DATES,

        # Higher IV than GLD allows wider delta sweep while staying OTM.
        "put_deltas":   [0.15, 0.20, 0.25, 0.30, 0.35, 0.40],
        "short_deltas": [0.15, 0.20, 0.25, 0.30, 0.35, 0.40],
        "wing_widths":  [0.05, 0.10, 0.15],
        "vix_thresholds": [None, 30, 25, 20],

        "opt_short_delta":  (0.15, 0.45),
        "opt_put_delta":    (0.10, 0.40),
        "opt_wing_width":   (0.05, 0.20),
        "opt_profit_take":  (0.30, 0.70),
        "opt_max_spread":   (0.10, 0.40),
        "opt_put_vix_max":  (15.0, 45.0),
        "opt_call_vix_min": (0.0,  30.0),
    },

    "IWM": {
        # iShares Russell 2000 ETF. Small-cap index, highest equity beta, most
        # sensitive to credit conditions and rate expectations. No reverse splits.
        # 2018 covers: rate hike cycle, COVID crash/recovery, and the 2022 bear market.
        "start": date(2018, 1, 1),
        "split_dates": IWM_SPLIT_DATES,

        # IV ~20–30% in normal regimes, spikes to 40%+ in selloffs. Wider delta
        # range than TLT/GLD to capture higher premiums when vol is elevated.
        "put_deltas":   [0.10, 0.15, 0.20, 0.25, 0.30, 0.35],
        "short_deltas": [0.15, 0.20, 0.25, 0.30, 0.35, 0.40],
        "wing_widths":  [0.05, 0.10, 0.15],
        "vix_thresholds": [None, 30, 25, 20],

        "opt_short_delta":  (0.15, 0.45),
        "opt_put_delta":    (0.10, 0.40),
        "opt_wing_width":   (0.05, 0.20),
        "opt_profit_take":  (0.30, 0.70),
        "opt_max_spread":   (0.10, 0.40),
        "opt_put_vix_max":  (15.0, 40.0),
        "opt_call_vix_min": (0.0,  30.0),
    },

    "EEM": {
        # iShares MSCI Emerging Markets ETF. Broad EM basket — China, Taiwan,
        # India, Brazil, Korea, etc. More range-bound than single-country ETFs
        # (~$34–53 for most of 2015–2024). IV ~25–30%. No splits.
        "start": date(2018, 1, 1),
        "split_dates": EEM_SPLIT_DATES,

        "put_deltas":   [0.10, 0.15, 0.20, 0.25, 0.30, 0.35],
        "short_deltas": [0.15, 0.20, 0.25, 0.30, 0.35],
        "wing_widths":  [0.05, 0.10, 0.15],
        "vix_thresholds": [None, 30, 25, 20],

        "opt_short_delta":  (0.15, 0.40),
        "opt_put_delta":    (0.10, 0.35),
        "opt_wing_width":   (0.05, 0.20),
        "opt_profit_take":  (0.30, 0.70),
        "opt_max_spread":   (0.10, 0.40),
        "opt_put_vix_max":  (15.0, 45.0),
        "opt_call_vix_min": (0.0,  30.0),
    },

    "XLF": {
        # Financial Select Sector SPDR. Banks, insurance, asset managers.
        # Rate-sensitive but oscillates with the cycle rather than trending
        # structurally. Upward drift 2018–2026 ($28→$55). IV ~20–25%. No splits.
        "start": date(2018, 1, 1),
        "split_dates": XLF_SPLIT_DATES,

        "put_deltas":   [0.10, 0.15, 0.20, 0.25, 0.30, 0.35],
        "short_deltas": [0.10, 0.15, 0.20, 0.25, 0.30, 0.35],
        "wing_widths":  [0.05, 0.10, 0.15],
        "vix_thresholds": [None, 30, 25, 20],

        "opt_short_delta":  (0.10, 0.35),
        "opt_put_delta":    (0.10, 0.35),
        "opt_wing_width":   (0.05, 0.20),
        "opt_profit_take":  (0.30, 0.70),
        "opt_max_spread":   (0.10, 0.40),
        "opt_put_vix_max":  (15.0, 45.0),
        "opt_call_vix_min": (0.0,  30.0),
    },

    "TMF": {
        # Direxion Daily 20+ Year Treasury Bull 3X Shares. 3x leveraged TLT.
        # Two splits in history: 1:4 forward split 2016-08-25 (pre-study window),
        # 1:10 reverse split 2023-12-05 (within study window).
        # Higher IV than TLT (~40-60%) from 3x leverage. Same directional thesis:
        # short calls when rates are rising / TLT falling (VIX≥20 regime).
        "start": date(2018, 1, 1),
        "split_dates": TMF_SPLIT_DATES,

        # Higher IV than TLT supports wider delta sweep.
        "put_deltas":   [0.10, 0.15, 0.20, 0.25, 0.30, 0.35],
        "short_deltas": [0.20, 0.25, 0.30, 0.35, 0.40],
        "wing_widths":  [0.05, 0.10, 0.15],
        "vix_thresholds": [None, 30, 25, 20],

        "opt_short_delta":  (0.15, 0.45),
        "opt_put_delta":    (0.10, 0.35),
        "opt_wing_width":   (0.05, 0.20),
        "opt_profit_take":  (0.30, 0.70),
        "opt_max_spread":   (0.10, 0.40),
        "opt_put_vix_max":  (15.0, 45.0),
        "opt_call_vix_min": (0.0,  30.0),
    },

    "UVIX": {
        # ProShares Ultra VIX Short-Term Futures ETF. 2x leveraged VIX futures.
        # Launched 2022-04-14. Two reverse splits within the study window:
        #   2023-10-11 (~1:4) and 2025-01-15 (~1:4).
        # Structurally similar to UVXY (1.5x) but higher leverage = higher IV,
        # faster decay, and lower price. Low price = liquidity risk on premiums.
        "start": date(2022, 4, 14),
        "split_dates": UVIX_SPLIT_DATES,

        # High IV (80–150%) from 2x leverage. Wider delta sweep than UVXY viable.
        "put_deltas":   [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40],
        "short_deltas": [0.30, 0.35, 0.40, 0.50],
        "wing_widths":  [0.10, 0.15, 0.20],
        "vix_thresholds": [None, 30, 25, 20],

        "opt_short_delta":  (0.30, 0.55),
        "opt_put_delta":    (0.10, 0.45),
        "opt_wing_width":   (0.05, 0.25),
        "opt_profit_take":  (0.30, 0.70),
        "opt_max_spread":   (0.15, 0.50),
        "opt_put_vix_max":  (15.0, 35.0),
        "opt_call_vix_min": (0.0,  25.0),
    },

    "INDA": {
        # iShares MSCI India ETF. Tracks large/mid-cap Indian equities.
        # EM risk premium pushes IV higher (~20–30%) than US large-cap ETFs.
        # No reverse splits. 2018 captures rate hike cycle, COVID crash/recovery,
        # and the post-2020 India growth rally.
        "start": date(2018, 1, 1),
        "split_dates": INDA_SPLIT_DATES,

        # Moderate-to-high IV; similar sweep to IWM/QQQ.
        "put_deltas":   [0.10, 0.15, 0.20, 0.25, 0.30, 0.35],
        "short_deltas": [0.15, 0.20, 0.25, 0.30, 0.35],
        "wing_widths":  [0.05, 0.10, 0.15],
        "vix_thresholds": [None, 30, 25, 20],

        "opt_short_delta":  (0.15, 0.40),
        "opt_put_delta":    (0.10, 0.35),
        "opt_wing_width":   (0.05, 0.20),
        "opt_profit_take":  (0.30, 0.70),
        "opt_max_spread":   (0.10, 0.40),
        "opt_put_vix_max":  (15.0, 45.0),
        "opt_call_vix_min": (0.0,  30.0),
    },

    "ASHR": {
        # Xtrackers Harvest CSI 300 China A-Shares ETF. Tracks mainland China
        # A-shares via the CSI 300 index. Higher China-specific risk than EEM or FXI
        # (domestic policy, capital controls, PBOC intervention). IV ~25–35%.
        # No known splits. Price range ~$20–35 in study window.
        "start": date(2018, 1, 1),
        "split_dates": ASHR_SPLIT_DATES,

        "put_deltas":   [0.10, 0.15, 0.20, 0.25, 0.30, 0.35],
        "short_deltas": [0.15, 0.20, 0.25, 0.30, 0.35],
        "wing_widths":  [0.05, 0.10, 0.15],
        "vix_thresholds": [None, 30, 25, 20],

        "opt_short_delta":  (0.15, 0.40),
        "opt_put_delta":    (0.10, 0.35),
        "opt_wing_width":   (0.05, 0.20),
        "opt_profit_take":  (0.30, 0.70),
        "opt_max_spread":   (0.10, 0.40),
        "opt_put_vix_max":  (15.0, 45.0),
        "opt_call_vix_min": (0.0,  30.0),
    },

    "FXI": {
        # iShares China Large-Cap ETF. Tracks large-cap Chinese stocks listed in
        # Hong Kong (H-shares, Red Chips). Highly liquid, one of the oldest China
        # ETFs. More policy/geopolitical sensitive than EEM. IV ~30–40%.
        # No known splits. Price range ~$25–50 in study window.
        "start": date(2018, 1, 1),
        "split_dates": FXI_SPLIT_DATES,

        "put_deltas":   [0.10, 0.15, 0.20, 0.25, 0.30, 0.35],
        "short_deltas": [0.15, 0.20, 0.25, 0.30, 0.35],
        "wing_widths":  [0.05, 0.10, 0.15],
        "vix_thresholds": [None, 30, 25, 20],

        "opt_short_delta":  (0.15, 0.40),
        "opt_put_delta":    (0.10, 0.35),
        "opt_wing_width":   (0.05, 0.20),
        "opt_profit_take":  (0.30, 0.70),
        "opt_max_spread":   (0.10, 0.40),
        "opt_put_vix_max":  (15.0, 45.0),
        "opt_call_vix_min": (0.0,  30.0),
    },

    "SOXX": {
        # iShares Semiconductor ETF. Tracks the PHLX Semiconductor Sector Index
        # (SOX). High-beta tech subsector — AI/data-center tailwind since 2023 but
        # severe selloffs in 2022 (−43%) and cyclical downturns. IV ~30–45% normal,
        # spikes to 60%+ in risk-off. Structurally upward-trending 2018–2025.
        # 2:1 forward split 2021-10-13 (~$500 → ~$250); delta selection handles it
        # naturally (no strike rescaling issue for P&L in % terms). No reverse splits.
        "start": date(2018, 1, 1),
        "split_dates": SOXX_SPLIT_DATES,

        # Higher IV than broad ETFs (IWM/QQQ) — extend delta range upward.
        "put_deltas":   [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40],
        "short_deltas": [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40],
        "wing_widths":  [0.05, 0.10, 0.15],
        "vix_thresholds": [None, 30, 25, 20],

        # ── Optimizer search bounds ────────────────────────────────────────────
        "opt_short_delta":  (0.15, 0.45),
        "opt_put_delta":    (0.10, 0.40),
        "opt_wing_width":   (0.05, 0.20),
        "opt_profit_take":  (0.30, 0.70),
        "opt_max_spread":   (0.10, 0.40),
        # Semiconductors sell off hard WITH VIX spikes — restrict puts in fear regimes.
        "opt_put_vix_max":  (15.0, 40.0),
        "opt_call_vix_min": (0.0,  30.0),
    },

    "SQQQ": {
        # ProShares UltraPro Short QQQ. 3x inverse of the Nasdaq 100.
        # Structurally decays toward zero over time as QQQ trends upward — this is
        # a headwind for short puts (SQQQ falling = short put losses) but the very
        # high IV (60–100%+) compensates with large credits. VIX filter matters:
        # when VIX spikes, SQQQ surges (market crashes) → short puts expire worthless;
        # when VIX is low, QQQ drifts up → SQQQ drifts down → short puts hurt.
        # So the VIX dynamic is OPPOSITE to UVXY: high VIX = SQQQ rally = good for puts.
        # Reverse split 2022-05-24 (1:10); additional splits possible — verify from data.
        "start": date(2018, 1, 1),
        "split_dates": SQQQ_SPLIT_DATES,

        # Very high IV — same broad sweep as UVXY.
        "put_deltas":   [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40],
        "short_deltas": [0.30, 0.35, 0.40, 0.50],
        "wing_widths":  [0.10, 0.15, 0.20],
        "vix_thresholds": [None, 30, 25, 20],

        # ── Optimizer search bounds ────────────────────────────────────────────
        "opt_short_delta":  (0.30, 0.55),
        "opt_put_delta":    (0.10, 0.45),
        "opt_wing_width":   (0.05, 0.25),
        "opt_profit_take":  (0.30, 0.70),
        "opt_max_spread":   (0.15, 0.50),
        # High VIX = SQQQ rally = puts expire worthless → no max VIX cap needed.
        # Low VIX environments are the dangerous ones for SQQQ short puts.
        "opt_put_vix_max":  (15.0, 45.0),
        "opt_call_vix_min": (0.0,  25.0),
    },

    "BJ": {
        # BJ's Wholesale Club Holdings. NYSE-listed US membership warehouse retailer.
        # IPO: June 28, 2018. Defensive consumer spending with membership fee moat.
        # IV ~25–35% (moderate retail sector volatility). No splits.
        # Skip early post-IPO period — allow ~6 months for options liquidity to develop.
        # IMPORTANT: BJ has MONTHLY OPTIONS ONLY (~14 expirations/year, no weeklies).
        # Use --dte 45 --dte-tol 10 for reliable monthly entries (~19/year).
        # At 20 DTE (default), only ~4 entries/year are found — use 45 DTE.
        "start": date(2019, 1, 1),
        "split_dates": BJ_SPLIT_DATES,

        "put_deltas":   [0.10, 0.15, 0.20, 0.25, 0.30, 0.35],
        "short_deltas": [0.10, 0.15, 0.20, 0.25, 0.30, 0.35],
        "wing_widths":  [0.05, 0.10, 0.15],
        "vix_thresholds": [None, 30, 25, 20],

        "opt_short_delta":  (0.10, 0.40),
        "opt_put_delta":    (0.10, 0.35),
        "opt_wing_width":   (0.05, 0.20),
        "opt_profit_take":  (0.30, 0.70),
        "opt_max_spread":   (0.10, 0.40),
        "opt_put_vix_max":  (15.0, 45.0),
        "opt_call_vix_min": (0.0,  30.0),
    },

    "YINN": {
        # Direxion Daily FTSE China Bull 3X Shares. 3x leveraged China large-cap ETF.
        # Tracks the FTSE China 50 Index (H-shares listed in Hong Kong). Very high IV
        # (60–120%+) from 3x leverage + China policy risk. Structural decay from daily
        # rebalancing. Multiple reverse splits.
        "start": date(2018, 1, 1),
        "split_dates": YINN_SPLIT_DATES,

        # High IV similar to UVIX; use wide delta sweep.
        "put_deltas":   [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40],
        "short_deltas": [0.20, 0.25, 0.30, 0.35, 0.40, 0.50],
        "wing_widths":  [0.05, 0.10, 0.15, 0.20],
        "vix_thresholds": [None, 30, 25, 20],

        "opt_short_delta":  (0.20, 0.55),
        "opt_put_delta":    (0.10, 0.45),
        "opt_wing_width":   (0.05, 0.25),
        "opt_profit_take":  (0.30, 0.70),
        "opt_max_spread":   (0.15, 0.50),
        "opt_put_vix_max":  (15.0, 40.0),
        "opt_call_vix_min": (0.0,  30.0),
    },

    "USO": {
        # United States Oil Fund. Holds WTI crude futures; structurally different
        # post-2020 restructuring (June 2020: changed from 100% front-month to
        # a spread of contract months after WTI went negative). Study window
        # starts after the restructuring stabilized.
        "start": date(2020, 7, 1),
        "split_dates": USO_SPLIT_DATES,

        # High IV (~35–50%) from oil price volatility.
        "put_deltas":   [0.15, 0.20, 0.25, 0.30, 0.35, 0.40],
        "short_deltas": [0.15, 0.20, 0.25, 0.30, 0.35, 0.40],
        "wing_widths":  [0.05, 0.10, 0.15],
        "vix_thresholds": [None, 30, 25, 20],

        "opt_short_delta":  (0.15, 0.45),
        "opt_put_delta":    (0.10, 0.40),
        "opt_wing_width":   (0.05, 0.20),
        "opt_profit_take":  (0.30, 0.70),
        "opt_max_spread":   (0.10, 0.40),
        "opt_put_vix_max":  (15.0, 40.0),
        "opt_call_vix_min": (0.0,  30.0),
    },

    "GEV": {
        # GE Vernova — spun off from GE on 2024-04-02. Power generation equipment
        # (gas turbines, wind, grid). Direct beneficiary of data center power demand
        # and grid electrification buildout. Limited history (~2 years).
        "start": date(2024, 4, 7),   # First full week of trading after spinoff
        "split_dates": GEV_SPLIT_DATES,

        # Moderate-to-high IV (~30–50%) for an industrial capital goods name.
        "put_deltas":   [0.15, 0.20, 0.25, 0.30, 0.35],
        "short_deltas": [0.15, 0.20, 0.25, 0.30, 0.35],
        "wing_widths":  [0.05, 0.10, 0.15],
        "vix_thresholds": [None, 30, 25, 20],

        "opt_short_delta":  (0.15, 0.40),
        "opt_put_delta":    (0.10, 0.35),
        "opt_wing_width":   (0.05, 0.20),
        "opt_profit_take":  (0.30, 0.70),
        "opt_max_spread":   (0.10, 0.40),
        "opt_put_vix_max":  (15.0, 40.0),
        "opt_call_vix_min": (0.0,  30.0),
    },

    "CLS": {
        # Celestica — electronics manufacturing services (EMS). Major hyperscaler
        # customer exposure (AI compute hardware, networking gear). Strong upward
        # trend driven by AI capex. Listed NYSE; no known splits.
        "start": date(2018, 1, 1),
        "split_dates": CLS_SPLIT_DATES,

        # Moderate IV (~30–45%) for an EMS/tech manufacturing name.
        "put_deltas":   [0.15, 0.20, 0.25, 0.30, 0.35],
        "short_deltas": [0.15, 0.20, 0.25, 0.30, 0.35],
        "wing_widths":  [0.05, 0.10, 0.15],
        "vix_thresholds": [None, 30, 25, 20],

        "opt_short_delta":  (0.15, 0.40),
        "opt_put_delta":    (0.10, 0.35),
        "opt_wing_width":   (0.05, 0.20),
        "opt_profit_take":  (0.30, 0.70),
        "opt_max_spread":   (0.10, 0.40),
        "opt_put_vix_max":  (15.0, 40.0),
        "opt_call_vix_min": (0.0,  30.0),
    },

    "FN": {
        # Fabrinet — contract manufacturer specializing in optical/photonic products,
        # laser components, and precision assemblies. Key customers include NVIDIA,
        # Coherent, II-VI. Benefits from AI networking (optical interconnects).
        "start": date(2018, 1, 1),
        "split_dates": FN_SPLIT_DATES,

        # Moderate IV (~25–40%) for a precision manufacturing name.
        "put_deltas":   [0.15, 0.20, 0.25, 0.30, 0.35],
        "short_deltas": [0.15, 0.20, 0.25, 0.30, 0.35],
        "wing_widths":  [0.05, 0.10, 0.15],
        "vix_thresholds": [None, 30, 25, 20],

        "opt_short_delta":  (0.15, 0.40),
        "opt_put_delta":    (0.10, 0.35),
        "opt_wing_width":   (0.05, 0.20),
        "opt_profit_take":  (0.30, 0.70),
        "opt_max_spread":   (0.10, 0.40),
        "opt_put_vix_max":  (15.0, 40.0),
        "opt_call_vix_min": (0.0,  30.0),
    },

    "CASY": {
        # Casey's General Stores — convenience store chain, Midwest/rural US.
        # Sells fuel, prepared food, beverages. Defensive consumer staples-like
        # business model; loyal regional customer base; consistent earnings.
        "start": date(2018, 1, 1),
        "split_dates": CASY_SPLIT_DATES,

        # Low-to-moderate IV (~20–30%) for a defensive consumer staples name.
        "put_deltas":   [0.15, 0.20, 0.25, 0.30, 0.35],
        "short_deltas": [0.15, 0.20, 0.25, 0.30, 0.35],
        "wing_widths":  [0.05, 0.10, 0.15],
        "vix_thresholds": [None, 30, 25, 20],

        "opt_short_delta":  (0.15, 0.40),
        "opt_put_delta":    (0.10, 0.35),
        "opt_wing_width":   (0.05, 0.20),
        "opt_profit_take":  (0.30, 0.70),
        "opt_max_spread":   (0.10, 0.40),
        "opt_put_vix_max":  (15.0, 40.0),
        "opt_call_vix_min": (0.0,  30.0),
    },

}
