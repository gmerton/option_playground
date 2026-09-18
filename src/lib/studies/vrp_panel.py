"""
Variance-risk-premium panel — the stage-one estimator.

Why this exists
---------------
Every study in this repo so far has measured edge the expensive way: simulate a
structure along a daily path and look at the mean P&L.  That estimator compresses
a whole holding period into one scalar that is dominated by *where the underlying
happened to close*, so a small volatility signal is read through a large direction
error term.  Typical power on ~190 monthly observations is t ~ 1, which is why so
many studies come back "no edge" without distinguishing "the premium is absent"
from "the premium is there but my estimator cannot see it".

This module measures the premium directly instead:

    vrp = iv(t, tenor)  -  rv_fwd(t, tenor)

`iv` is the ATM implied vol quoted at t for `tenor` calendar days.  `rv_fwd` is the
close-to-close realized vol that actually shows up over the next `tenor` calendar
days.  The difference is the thing a vol seller is paid (positive) or a vol buyer
is paid (negative).  It uses every daily return in the window rather than one
terminal price, so it resolves the same economic question with far more power.

It is a SCREEN, not a strategy.  A positive premium does not mean the trade is
capturable: an unhedged structure is gamma-weighted, carries direction risk, and
pays spreads and commissions, all of which live in the stage-two path backtest.
The reliable direction is the converse — if the premium is not here, no structure
manufactures it.

Panel schema (long format, one row per ticker x date x tenor)
------------------------------------------------------------
    ticker, trade_date, tenor
    iv            annualized ATM implied vol at `tenor` (from options_daily_v3)
    n_contracts   contracts averaged into `iv` (drop < MIN_CONTRACTS)
    rv_fwd        annualized realized vol over (t, t+tenor]   <- forward, the target half
    rv_trail      annualized realized vol over [t-tenor, t)   <- observable at t
    vrp           iv - rv_fwd                                  <- THE TARGET
    vrp_trail     iv - rv_trail                                <- observable at t, a predictor
    iv_pctile     iv rank within own trailing 252 observations (observable at t)
    ret_trail_21  trailing 21-trading-day return               (observable at t)
    vix           ^VIX close at t                              (observable at t)
    vix_pctile    ^VIX rank within trailing 252 sessions        (observable at t)

Everything except `rv_fwd` and `vrp` is known at entry, so the observable columns
are legal conditioning variables and the two forward columns are targets only.

Data sources
------------
IV      : silver.options_daily_v3, stored bid_iv/ask_iv averaged across near-ATM
          contracts.  Coverage caveats live in the reference notes: stored IV runs
          out around mid-May 2026, and 2010-2013 is thin.  Neither matters for a
          historical premium estimate; both matter for live scoring.
Closes  : yfinance auto-adjusted closes.  Adjusted prices are the correct input for
          RETURNS (splits and dividends handled).  They are NOT strike-comparable,
          but nothing here touches strikes, so the usual split-adjustment caveat
          does not apply.

Inference lives in lib.studies.vrp_stats — do not use a plain t-test on this panel,
the rows overlap and are cross-sectionally correlated.
"""

from __future__ import annotations

import pathlib
import warnings
from datetime import date
from typing import Iterable, Optional

import numpy as np
import pandas as pd

from lib.athena_lib import athena
from lib.constants import DB, TABLE

# ── Tenor definitions: label -> (dte_lo, dte_hi) accepted from the chain ──────
# Labels are the nominal calendar-day horizon; the window is what the chain must
# supply.  10 covers the 7-DTE long straddle, 30 the put-spread / condor book,
# 90 the far leg of the 30->90 forward-vol trades.
TENORS: dict[int, tuple[int, int]] = {
    10: (7, 14),
    30: (25, 35),
    90: (76, 104),
}

ATM_DELTA_LO = 0.45
ATM_DELTA_HI = 0.55
MIN_CONTRACTS = 2          # 1-contract days are a noisy ATM proxy
TRADING_DAYS = 252.0
CACHE_DIR = pathlib.Path("data/cache/vrp_panel")


# ══════════════════════════════════════════════════════════════════════════════
# Implied vol side (Athena)
# ══════════════════════════════════════════════════════════════════════════════

def fetch_atm_iv(
    tickers: list[str],
    start: date,
    end: date,
    tenor: int,
    cp: Optional[str] = None,
) -> pd.DataFrame:
    """
    Per (ticker, trade_date) ATM implied vol at `tenor`, averaged over near-ATM
    contracts.

    cp=None (default) averages calls and puts together.  Averaging the two cancels
    most of the borrow/dividend wedge between same-strike call and put IV and is
    closer to what a straddle actually pays than either side alone.  Pass 'C' to
    reproduce the older call-only recipe used by the Squeeze VRP test.

    Chunked one query per calendar year — v3 is partitioned by year(trade_date)
    and bucketed on ticker, so year-at-a-time with an IN list is the fast shape.
    """
    if not tickers:
        return pd.DataFrame()
    if tenor not in TENORS:
        raise ValueError(f"unknown tenor {tenor}; known: {sorted(TENORS)}")

    dte_lo, dte_hi = TENORS[tenor]
    tickers_sql = ", ".join(f"'{t}'" for t in tickers)
    cp_clause = f"AND cp = '{cp}'" if cp else ""

    frames: list[pd.DataFrame] = []
    for yr in range(start.year, end.year + 1):
        y_lo = max(start, date(yr, 1, 1))
        y_hi = min(end, date(yr, 12, 31))
        if y_lo > y_hi:
            continue

        sql = f"""
        SELECT
            ticker,
            trade_date,
            avg((bid_iv + ask_iv) / 2.0) AS iv,
            count(*)                     AS n_contracts
        FROM "{DB}"."{TABLE}"
        WHERE ticker IN ({tickers_sql})
          AND trade_date >= TIMESTAMP '{y_lo.isoformat()} 00:00:00'
          AND trade_date <= TIMESTAMP '{y_hi.isoformat()} 00:00:00'
          {cp_clause}
          AND bid_iv IS NOT NULL AND ask_iv IS NOT NULL
          AND bid_iv > 0 AND ask_iv > 0
          AND delta IS NOT NULL
          AND ABS(delta) BETWEEN {ATM_DELTA_LO} AND {ATM_DELTA_HI}
          AND date_diff('day', trade_date, expiry) BETWEEN {dte_lo} AND {dte_hi}
        GROUP BY ticker, trade_date
        """
        df = athena(sql)
        if not df.empty:
            frames.append(df)
        print(f"    [iv {tenor}d] {yr}: {len(df):,} ticker-days")

    if not frames:
        return pd.DataFrame(columns=["ticker", "trade_date", "iv", "n_contracts", "tenor"])

    out = pd.concat(frames, ignore_index=True)
    out["trade_date"] = pd.to_datetime(out["trade_date"]).dt.normalize()
    out["iv"] = pd.to_numeric(out["iv"], errors="coerce")
    out["n_contracts"] = pd.to_numeric(out["n_contracts"], errors="coerce")
    out = out[out["n_contracts"] >= MIN_CONTRACTS]
    out = out[out["iv"] > 0]
    out["tenor"] = tenor
    return out.sort_values(["ticker", "trade_date"]).reset_index(drop=True)


# ══════════════════════════════════════════════════════════════════════════════
# Realized vol side (yfinance closes)
# ══════════════════════════════════════════════════════════════════════════════

def fetch_closes(
    tickers: Iterable[str],
    start: date,
    end: date,
    batch_size: int = 40,
) -> pd.DataFrame:
    """
    Daily auto-adjusted closes, long format: ticker, trade_date, close.

    Adjusted closes are correct for returns and therefore for realized vol.  They
    are not comparable to historical strikes, but this panel never touches strikes.
    """
    import yfinance as yf

    tickers = list(dict.fromkeys(tickers))
    frames: list[pd.DataFrame] = []

    for i in range(0, len(tickers), batch_size):
        batch = tickers[i : i + batch_size]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            raw = yf.download(
                batch,
                start=start.isoformat(),
                end=(pd.Timestamp(end) + pd.Timedelta(days=1)).date().isoformat(),
                auto_adjust=True,
                progress=False,
                group_by="column",
                threads=True,
            )
        if raw is None or raw.empty:
            print(f"    [closes] batch {i // batch_size + 1}: no data")
            continue

        if isinstance(raw.columns, pd.MultiIndex):
            close = raw["Close"]
        else:  # single ticker -> flat columns
            close = raw[["Close"]].rename(columns={"Close": batch[0]})

        tidy = (
            close.stack(future_stack=True)
            .rename("close")
            .reset_index()
            .rename(columns={"Date": "trade_date", "level_1": "ticker", "Ticker": "ticker"})
        )
        frames.append(tidy)
        print(f"    [closes] batch {i // batch_size + 1}: {len(tidy):,} rows, {close.shape[1]} tickers")

    if not frames:
        return pd.DataFrame(columns=["ticker", "trade_date", "close"])

    out = pd.concat(frames, ignore_index=True)
    out["trade_date"] = pd.to_datetime(out["trade_date"]).dt.tz_localize(None).dt.normalize()
    out["close"] = pd.to_numeric(out["close"], errors="coerce")
    out = out.dropna(subset=["close"])
    out = out[out["close"] > 0]
    return out.sort_values(["ticker", "trade_date"]).reset_index(drop=True)


def _annualized_rv(sq_returns: np.ndarray) -> float:
    """Zero-mean annualized realized vol from squared log returns."""
    if sq_returns.size == 0:
        return np.nan
    return float(np.sqrt(TRADING_DAYS * np.nanmean(sq_returns)))


def realized_vol_windows(
    closes: pd.DataFrame,
    tenor: int,
    min_coverage: float = 0.6,
) -> pd.DataFrame:
    """
    For each (ticker, trade_date) compute forward and trailing annualized realized
    vol over a `tenor`-CALENDAR-day window.

    Forward window is (t, t+tenor] — strictly future, no leakage from day t itself.
    Trailing window is [t-tenor, t) — strictly past, so it is observable at entry.

    Calendar days are used (not trading days) because the implied vol being compared
    is quoted for a calendar-day horizon.  Annualization is by 252 x mean(r^2), the
    standard zero-mean estimator; zero-mean is the right choice here because an
    option's gamma P&L tracks the sum of squared returns, not variance about a mean.

    Rows whose forward window is cut short by the end of the price history are
    dropped rather than computed on partial data — a truncated window is exactly the
    failure mode that invalidated the calendar path study.
    """
    out: list[pd.DataFrame] = []
    span = pd.Timedelta(days=tenor)
    # Expected trading days in the window, used for the coverage floor.
    expected = max(1, int(round(tenor * TRADING_DAYS / 365.0)))
    floor = max(2, int(np.floor(min_coverage * expected)))

    for ticker, grp in closes.groupby("ticker", sort=False):
        g = grp.sort_values("trade_date").reset_index(drop=True)
        dates = g["trade_date"].to_numpy()
        px = g["close"].to_numpy(dtype=float)
        if px.size < floor + 2:
            continue

        logret = np.full(px.size, np.nan)
        logret[1:] = np.log(px[1:] / px[:-1])
        sq = logret ** 2

        # Cumulative sums of squared returns / counts for O(1) window queries.
        valid = ~np.isnan(sq)
        sq0 = np.where(valid, sq, 0.0)
        csum = np.concatenate([[0.0], np.cumsum(sq0)])
        ccnt = np.concatenate([[0], np.cumsum(valid.astype(int))])

        last_date = dates[-1]
        # Index of the first bar strictly after t, and the last bar <= t + span.
        fwd_lo = np.searchsorted(dates, dates, side="right")
        fwd_hi = np.searchsorted(dates, dates + span, side="right")
        # Trailing: bars in [t - span, t) -> first bar >= t-span, up to but not t.
        trl_lo = np.searchsorted(dates, dates - span, side="left")
        trl_hi = np.searchsorted(dates, dates, side="left")

        n_fwd = ccnt[fwd_hi] - ccnt[fwd_lo]
        s_fwd = csum[fwd_hi] - csum[fwd_lo]
        n_trl = ccnt[trl_hi] - ccnt[trl_lo]
        s_trl = csum[trl_hi] - csum[trl_lo]

        with np.errstate(invalid="ignore", divide="ignore"):
            rv_fwd = np.sqrt(TRADING_DAYS * s_fwd / np.where(n_fwd > 0, n_fwd, np.nan))
            rv_trail = np.sqrt(TRADING_DAYS * s_trl / np.where(n_trl > 0, n_trl, np.nan))

        # Drop truncated forward windows: too few bars, or the window runs past the
        # end of the price history (we cannot know it was complete).
        complete = (n_fwd >= floor) & ((dates + span) <= last_date)
        rv_fwd = np.where(complete, rv_fwd, np.nan)
        rv_trail = np.where(n_trl >= floor, rv_trail, np.nan)

        # Trailing 21-trading-day return, observable at t.
        ret21 = np.full(px.size, np.nan)
        ret21[21:] = px[21:] / px[:-21] - 1.0

        out.append(
            pd.DataFrame({
                "ticker": ticker,
                "trade_date": dates,
                "rv_fwd": rv_fwd,
                "rv_trail": rv_trail,
                "n_fwd_bars": n_fwd,
                "ret_trail_21": ret21,
            })
        )

    if not out:
        return pd.DataFrame(
            columns=["ticker", "trade_date", "rv_fwd", "rv_trail", "n_fwd_bars", "ret_trail_21"]
        )
    res = pd.concat(out, ignore_index=True)
    res["tenor"] = tenor
    return res


def realized_vol_between(
    closes: pd.DataFrame,
    lo_days: int,
    hi_days: int,
    min_coverage: float = 0.6,
) -> pd.DataFrame:
    """
    Annualized realized vol over the FORWARD window (t+lo_days, t+hi_days].

    This is the realized counterpart to a forward implied vol.  A 30->90 calendar
    is a bet on the vol that shows up between day 30 and day 90, not on the vol
    between now and day 90, so this is the window its premium must be measured over.

    Same truncation discipline as `realized_vol_windows`: a window that runs past
    the end of the price history is dropped, never computed on partial data.
    """
    if hi_days <= lo_days:
        raise ValueError("hi_days must exceed lo_days")

    out: list[pd.DataFrame] = []
    lo_span = pd.Timedelta(days=lo_days)
    hi_span = pd.Timedelta(days=hi_days)
    expected = max(1, int(round((hi_days - lo_days) * TRADING_DAYS / 365.0)))
    floor = max(2, int(np.floor(min_coverage * expected)))

    for ticker, grp in closes.groupby("ticker", sort=False):
        g = grp.sort_values("trade_date").reset_index(drop=True)
        dates = g["trade_date"].to_numpy()
        px = g["close"].to_numpy(dtype=float)
        if px.size < floor + 2:
            continue

        logret = np.full(px.size, np.nan)
        logret[1:] = np.log(px[1:] / px[:-1])
        sq = logret ** 2
        valid = ~np.isnan(sq)
        csum = np.concatenate([[0.0], np.cumsum(np.where(valid, sq, 0.0))])
        ccnt = np.concatenate([[0], np.cumsum(valid.astype(int))])

        i_lo = np.searchsorted(dates, dates + lo_span, side="right")
        i_hi = np.searchsorted(dates, dates + hi_span, side="right")
        n = ccnt[i_hi] - ccnt[i_lo]
        s = csum[i_hi] - csum[i_lo]

        with np.errstate(invalid="ignore", divide="ignore"):
            rv = np.sqrt(TRADING_DAYS * s / np.where(n > 0, n, np.nan))

        complete = (n >= floor) & ((dates + hi_span) <= dates[-1])
        rv = np.where(complete, rv, np.nan)

        out.append(pd.DataFrame({
            "ticker": ticker,
            "trade_date": dates,
            "rv_fwd_between": rv,
            "n_between_bars": n,
        }))

    if not out:
        return pd.DataFrame(columns=["ticker", "trade_date", "rv_fwd_between", "n_between_bars"])
    return pd.concat(out, ignore_index=True)


def forward_iv(iv_near: pd.Series, t_near: float, iv_far: pd.Series, t_far: float) -> pd.Series:
    """
    Forward implied vol between t_near and t_far years, from the two spot IVs.

        sigma_fwd = sqrt( (iv_far^2 * t_far - iv_near^2 * t_near) / (t_far - t_near) )

    Same identity as lib.studies.fwd_vol_study._fvr uses, but vectorized and
    returning the vol itself rather than its ratio to the near leg.  NaN (not zero)
    on an inverted term structure, so those days drop out of the mean instead of
    being recorded as a forward vol of nothing.
    """
    var_fwd = iv_far.astype(float) ** 2 * t_far - iv_near.astype(float) ** 2 * t_near
    var_fwd = var_fwd.where(var_fwd > 0)
    return np.sqrt(var_fwd / (t_far - t_near))


def build_forward_premium(
    panel: pd.DataFrame,
    closes: pd.DataFrame,
    near: int = 30,
    far: int = 90,
) -> pd.DataFrame:
    """
    The term-structure premium: forward implied vol between `near` and `far` days,
    minus the realized vol that then shows up in exactly that window.

    This is the stage-one screen for every calendar / diagonal / forward-factor idea.
    If `fwd_vrp` has no mean and no conditioner, a calendar structure has nothing to
    harvest and the expensive path simulation will only tell you so more slowly.
    """
    wide = (
        panel[panel["tenor"].isin([near, far])]
        .pivot_table(index=["ticker", "trade_date"], columns="tenor", values="iv", aggfunc="first")
        .rename(columns={near: "iv_near", far: "iv_far"})
        .dropna()
        .reset_index()
    )
    if wide.empty:
        return pd.DataFrame()

    t_near, t_far = near / 365.0, far / 365.0
    wide["iv_fwd"] = forward_iv(wide["iv_near"], t_near, wide["iv_far"], t_far)
    wide["fvr"] = wide["iv_fwd"] / wide["iv_near"]

    rv = realized_vol_between(closes, near, far)
    wide = wide.merge(rv, on=["ticker", "trade_date"], how="inner")
    wide["fwd_vrp"] = wide["iv_fwd"] - wide["rv_fwd_between"]

    # Carry the observable state columns across from the near-tenor rows.
    state = panel[panel["tenor"] == near][
        [c for c in ("ticker", "trade_date", "iv_pctile", "ret_trail_21", "vix", "vix_pctile")
         if c in panel.columns]
    ]
    wide = wide.merge(state, on=["ticker", "trade_date"], how="left")
    return wide.sort_values(["ticker", "trade_date"]).reset_index(drop=True)


def fetch_vix(start: date, end: date) -> pd.DataFrame:
    """^VIX close plus its trailing-252 percentile, both observable at t."""
    vix = fetch_closes(["^VIX"], start, end)
    if vix.empty:
        return pd.DataFrame(columns=["trade_date", "vix", "vix_pctile"])
    vix = vix.rename(columns={"close": "vix"})[["trade_date", "vix"]]
    vix = vix.sort_values("trade_date").reset_index(drop=True)
    vix["vix_pctile"] = vix["vix"].rolling(252, min_periods=60).rank(pct=True)
    return vix


# ══════════════════════════════════════════════════════════════════════════════
# Panel assembly
# ══════════════════════════════════════════════════════════════════════════════

def build_panel(
    tickers: list[str],
    start: date,
    end: date,
    tenors: Iterable[int] = (10, 30, 90),
    cp: Optional[str] = None,
    closes: Optional[pd.DataFrame] = None,
    vix: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Assemble the long-format VRP panel.  One row per ticker x date x tenor.

    Price history is pulled with a pad on both ends so that trailing windows at the
    start and forward windows at the end are complete rather than truncated.
    """
    tenors = sorted(set(int(t) for t in tenors))
    pad = max(tenors) + 40

    if closes is None:
        print("  fetching closes...")
        closes = fetch_closes(
            tickers,
            (pd.Timestamp(start) - pd.Timedelta(days=pad + 400)).date(),  # +400 for iv_pctile warmup
            (pd.Timestamp(end) + pd.Timedelta(days=pad)).date(),
        )
    if closes.empty:
        raise RuntimeError("no price history returned; cannot compute realized vol")

    if vix is None:
        print("  fetching ^VIX...")
        vix = fetch_vix(
            (pd.Timestamp(start) - pd.Timedelta(days=400)).date(),
            (pd.Timestamp(end) + pd.Timedelta(days=pad)).date(),
        )

    frames: list[pd.DataFrame] = []
    for tenor in tenors:
        print(f"  tenor {tenor}d:")
        iv = fetch_atm_iv(tickers, start, end, tenor, cp=cp)
        if iv.empty:
            print(f"    -> no IV rows at {tenor}d, skipping")
            continue
        rv = realized_vol_windows(closes, tenor)

        df = iv.merge(rv.drop(columns=["tenor"]), on=["ticker", "trade_date"], how="inner")
        if df.empty:
            print(f"    -> IV and price history do not overlap at {tenor}d, skipping")
            continue

        df["vrp"] = df["iv"] - df["rv_fwd"]
        df["vrp_trail"] = df["iv"] - df["rv_trail"]
        df["tenor"] = tenor

        # Own-IV percentile vs trailing 252 observations (observable at t).
        df = df.sort_values(["ticker", "trade_date"])
        df["iv_pctile"] = (
            df.groupby("ticker", sort=False)["iv"]
            .transform(lambda s: s.rolling(252, min_periods=60).rank(pct=True))
        )

        if not vix.empty:
            df = df.merge(vix, on="trade_date", how="left")

        n_drop = df["vrp"].isna().sum()
        print(f"    -> {len(df):,} rows ({n_drop:,} without a complete forward window)")
        frames.append(df)

    if not frames:
        raise RuntimeError("no tenor produced any rows")

    panel = pd.concat(frames, ignore_index=True)
    cols = [
        "ticker", "trade_date", "tenor", "iv", "n_contracts",
        "rv_fwd", "rv_trail", "vrp", "vrp_trail",
        "iv_pctile", "ret_trail_21", "vix", "vix_pctile", "n_fwd_bars",
    ]
    cols = [c for c in cols if c in panel.columns]
    return panel[cols].sort_values(["tenor", "ticker", "trade_date"]).reset_index(drop=True)


# ══════════════════════════════════════════════════════════════════════════════
# Cache
# ══════════════════════════════════════════════════════════════════════════════

def cache_path(name: str) -> pathlib.Path:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / f"{name}.parquet"


def save_panel(panel: pd.DataFrame, name: str) -> pathlib.Path:
    p = cache_path(name)
    panel.to_parquet(p, index=False)
    print(f"  wrote {len(panel):,} rows -> {p}")
    return p


def load_panel(name: str) -> pd.DataFrame:
    p = cache_path(name)
    if not p.exists():
        raise FileNotFoundError(f"no cached panel at {p} — run run_vrp_panel.py first")
    return pd.read_parquet(p)
