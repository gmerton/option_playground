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
}
