"""
GOOG option vs. underlying intraday chart.

Streamlit + Plotly app: pick an expiry/strike/right and see the option's
minute-by-minute price plotted against the underlying, on a dual-axis line
chart (underlying on the left axis, option on the right axis).

Data comes from the minute bid/ask pulls in data/cache/ (see
memory/project_intraday_option_quotes.md for how it was built) — currently
GOOG only, 4 expiries, Aug 17-21 2026 window, Monday-anchored +/-10% strike
band. Missing (contract, day) combos (e.g. fine strikes not yet listed for
far-dated expiries) simply aren't in the data; the chart just shows a gap.

Run with:
    .venv/bin/streamlit run option_chart_app.py
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from scipy.optimize import brentq
from scipy.stats import norm

DATA_DIR = Path(__file__).parent / "data" / "cache"

# expiry label -> (parquet filename, human note)
EXPIRY_FILES = {
    "2026-08-21 (weekly)": "GOOG_20260821exp_1min_bidask.parquet",
    "2026-08-28 (weekly)": "GOOG_20260828exp_1min_bidask.parquet",
    "2026-09-18 (monthly)": "GOOG_20260918exp_1min_bidask.parquet",
    "2027-02-19 (LEAP)": "GOOG_20270219exp_1min_bidask.parquet",
}
UNDERLYING_FILE = "GOOG_stock_1min_20260817_20260821.parquet"


@st.cache_data
def load_option_data(fname: str) -> pd.DataFrame:
    df = pd.read_parquet(DATA_DIR / fname)
    # IB timestamps parse as tz-aware (fixed UTC-04:00 = ET/EDT offset); the
    # underlying's timestamps parse tz-naive but are already wall-clock ET.
    # Strip the offset so both frames merge/compare cleanly on 'datetime'.
    df["datetime"] = pd.to_datetime(df["time"]).dt.tz_localize(None)
    # Bar convention: bid_open/high/low are the bid's OHL for the minute,
    # ask_close is only the ask's close. Use open-of-bid / close-of-ask as a
    # matched (bid, ask) pair for a mid estimate.
    df["bid"] = df["bid_open"]
    df["ask"] = df["ask_close"]
    df["mid"] = (df["bid"] + df["ask"]) / 2
    return df


@st.cache_data
def load_underlying() -> pd.DataFrame:
    df = pd.read_parquet(DATA_DIR / UNDERLYING_FILE)
    df["datetime"] = pd.to_datetime(df["time"])
    return df


# --- Black-Scholes: implied vol + Greeks -----------------------------------
# Standard European BS with continuous dividend yield q. Good enough for a
# quick IV/Greeks readout on equity options at these DTEs; not a production
# pricer (no American-exercise early-ex premium, no discrete dividends).


def bs_price(S, K, T, r, q, sigma, is_call):
    if T <= 0:
        return max(S - K, 0.0) if is_call else max(K - S, 0.0)
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if is_call:
        return S * np.exp(-q * T) * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    return K * np.exp(-r * T) * norm.cdf(-d2) - S * np.exp(-q * T) * norm.cdf(-d1)


def implied_vol(price, S, K, T, r, q, is_call):
    """Solve for sigma via brentq. NaN if price is at/below intrinsic (bad
    quote, crossed market, or essentially zero time value) or no root brackets."""
    intrinsic = max(S - K, 0.0) if is_call else max(K - S, 0.0)
    if T <= 0 or not np.isfinite(price) or price <= intrinsic + 1e-6:
        return np.nan
    f = lambda sigma: bs_price(S, K, T, r, q, sigma, is_call) - price
    try:
        if f(1e-4) * f(5.0) > 0:
            return np.nan
        return brentq(f, 1e-4, 5.0, xtol=1e-6)
    except Exception:
        return np.nan


def bs_greeks_vec(S, K, T, r, q, sigma, is_call):
    """Vectorized (numpy array) delta/gamma/vega/theta given sigma already known.
    vega is per 1 vol point (i.e. per 0.01 change in sigma); theta is per day."""
    d1 = (np.log(S / K) + (r - q + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    pdf_d1 = norm.pdf(d1)
    if is_call:
        delta = np.exp(-q * T) * norm.cdf(d1)
        theta = (
            -S * np.exp(-q * T) * pdf_d1 * sigma / (2 * np.sqrt(T))
            - r * K * np.exp(-r * T) * norm.cdf(d2)
            + q * S * np.exp(-q * T) * norm.cdf(d1)
        ) / 365
    else:
        delta = -np.exp(-q * T) * norm.cdf(-d1)
        theta = (
            -S * np.exp(-q * T) * pdf_d1 * sigma / (2 * np.sqrt(T))
            + r * K * np.exp(-r * T) * norm.cdf(-d2)
            - q * S * np.exp(-q * T) * norm.cdf(-d1)
        ) / 365
    gamma = np.exp(-q * T) * pdf_d1 / (S * sigma * np.sqrt(T))
    vega = S * np.exp(-q * T) * pdf_d1 * np.sqrt(T) / 100
    return delta, gamma, vega, theta


@st.cache_data
def compute_iv_greeks(
    merged: pd.DataFrame, strike: float, right_code: str, expiry_str: str, r: float, q: float
) -> pd.DataFrame:
    """merged needs columns: datetime, spot, option_price. Expiry assumed to
    close at 16:00 ET on expiry_str (YYYY-MM-DD)."""
    is_call = right_code == "C"
    expiry_ts = pd.Timestamp(f"{expiry_str} 16:00:00")
    df = merged.copy()
    df["T"] = (expiry_ts - df["datetime"]).dt.total_seconds() / (365 * 24 * 3600)
    df["T"] = df["T"].clip(lower=0)

    df["iv"] = [
        implied_vol(p, s, strike, t, r, q, is_call)
        for p, s, t in zip(df["option_price"], df["spot"], df["T"])
    ]

    valid = df["iv"].notna() & (df["T"] > 0)
    delta = np.full(len(df), np.nan)
    gamma = np.full(len(df), np.nan)
    vega = np.full(len(df), np.nan)
    theta = np.full(len(df), np.nan)
    if valid.any():
        d, g, v, th = bs_greeks_vec(
            df.loc[valid, "spot"].to_numpy(),
            strike,
            df.loc[valid, "T"].to_numpy(),
            r,
            q,
            df.loc[valid, "iv"].to_numpy(),
            is_call,
        )
        delta[valid.to_numpy()] = d
        gamma[valid.to_numpy()] = g
        vega[valid.to_numpy()] = v
        theta[valid.to_numpy()] = th
    df["delta"], df["gamma"], df["vega"], df["theta"] = delta, gamma, vega, theta
    return df


st.set_page_config(page_title="GOOG Option vs Underlying", layout="wide")
st.title("GOOG — Option vs. Underlying (intraday)")

underlying_df = load_underlying()

with st.sidebar:
    st.header("Contract")

    expiry_label = st.selectbox("Expiry", list(EXPIRY_FILES.keys()))
    opt_df = load_option_data(EXPIRY_FILES[expiry_label])

    right_label = st.radio("Type", ["Call", "Put"], horizontal=True)
    right_code = "C" if right_label == "Call" else "P"

    strikes = sorted(opt_df.loc[opt_df["right"] == right_code, "strike"].unique())
    if not strikes:
        st.error("No strikes for this expiry/type combination.")
        st.stop()
    default_idx = len(strikes) // 2
    strike = st.selectbox("Strike", strikes, index=default_idx)

    price_field = st.radio(
        "Option price line",
        ["Mid", "Bid", "Ask", "Bid + Ask band"],
        help="Mid = (bid_open + ask_close) / 2 for each minute.",
    )

    st.divider()
    st.header("Pricing model")
    r_pct = st.number_input(
        "Risk-free rate (%)", value=4.3, step=0.1, format="%.2f",
        help="Used only for the IV/Greeks readout below.",
    )
    q_pct = st.number_input(
        "Dividend yield (%)", value=0.4, step=0.1, format="%.2f",
        help="GOOG's continuous dividend yield assumption for Black-Scholes.",
    )
    st.caption("Expiry assumed to close at 16:00 ET on the expiry date.")

    st.divider()
    available_days = sorted(
        opt_df.loc[
            (opt_df["right"] == right_code) & (opt_df["strike"] == strike), "date"
        ].unique()
    )
    st.caption(f"Days with data for this contract: {len(available_days)} of 5")
    if len(available_days) < 5:
        st.caption(
            "Some sessions are missing for this strike — likely not yet "
            "listed on the chain during the pull window (see memory note "
            "on far-dated / fine-increment strikes)."
        )

contract_df = (
    opt_df[(opt_df["right"] == right_code) & (opt_df["strike"] == strike)]
    .sort_values("datetime")
    .reset_index(drop=True)
)

if contract_df.empty:
    st.warning("No data for this contract.")
    st.stop()

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=underlying_df["datetime"],
        y=underlying_df["close"],
        name="GOOG (underlying)",
        yaxis="y1",
        line=dict(color="#4C78A8", width=1.5),
    )
)

if price_field == "Bid + Ask band":
    fig.add_trace(
        go.Scatter(
            x=contract_df["datetime"],
            y=contract_df["ask"],
            name=f"{strike:g}{right_code} ask",
            yaxis="y2",
            line=dict(color="rgba(230,126,34,0.35)", width=1),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=contract_df["datetime"],
            y=contract_df["bid"],
            name=f"{strike:g}{right_code} bid",
            yaxis="y2",
            line=dict(color="rgba(230,126,34,0.35)", width=1),
            fill="tonexty",
            fillcolor="rgba(230,126,34,0.15)",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=contract_df["datetime"],
            y=contract_df["mid"],
            name=f"{strike:g}{right_code} mid",
            yaxis="y2",
            line=dict(color="#E67E22", width=1.5),
        )
    )
else:
    field_map = {"Mid": "mid", "Bid": "bid", "Ask": "ask"}
    fig.add_trace(
        go.Scatter(
            x=contract_df["datetime"],
            y=contract_df[field_map[price_field]],
            name=f"{strike:g}{right_code} {price_field.lower()}",
            yaxis="y2",
            line=dict(color="#E67E22", width=1.5),
        )
    )

day_starts = underlying_df.groupby(underlying_df["datetime"].dt.date)["datetime"].min()
for day_start in day_starts:
    fig.add_vline(
        x=day_start,
        line_width=1,
        line_dash="dot",
        line_color="gray",
        opacity=0.6,
    )
    fig.add_annotation(
        x=day_start,
        y=1.0,
        yref="paper",
        text=day_start.strftime("%a %m/%d"),
        showarrow=False,
        yanchor="bottom",
        font=dict(size=10, color="gray"),
    )

fig.update_layout(
    height=650,
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
    margin=dict(t=60, l=60, r=60, b=40),
    xaxis=dict(
        title="Time (ET)",
        rangebreaks=[
            dict(bounds=["sat", "mon"]),  # hide weekends
            dict(bounds=[16, 9.5], pattern="hour"),  # hide overnight
        ],
    ),
    yaxis=dict(title="Underlying price ($)", side="left", color="#4C78A8"),
    yaxis2=dict(
        title="Option price ($)",
        side="right",
        overlaying="y",
        color="#E67E22",
    ),
)

st.plotly_chart(fig, width="stretch")

# --- IV / Greeks readout -----------------------------------------------------
st.header("Implied vol & Greeks")

expiry_str = expiry_label.split(" ")[0]  # "2026-09-18 (monthly)" -> "2026-09-18"
merged = pd.merge(
    contract_df[["datetime", "mid"]].rename(columns={"mid": "option_price"}),
    underlying_df[["datetime", "close"]].rename(columns={"close": "spot"}),
    on="datetime",
    how="inner",
).sort_values("datetime").reset_index(drop=True)

if merged.empty:
    st.info("No overlapping (option, underlying) timestamps for this contract.")
else:
    greeks_df = compute_iv_greeks(
        merged, strike, right_code, expiry_str, r_pct / 100, q_pct / 100
    )
    n_valid = greeks_df["iv"].notna().sum()
    st.caption(
        f"IV solved for {n_valid} of {len(greeks_df)} minutes "
        f"(the rest were at/near intrinsic value or otherwise unsolvable — "
        f"likely a stale or crossed quote)."
    )

    iv_fig = go.Figure()
    iv_fig.add_trace(
        go.Scatter(
            x=greeks_df["datetime"],
            y=greeks_df["iv"] * 100,
            name="Implied vol (%)",
            line=dict(color="#59A14F", width=1.5),
        )
    )
    for day_start in day_starts:
        iv_fig.add_vline(x=day_start, line_width=1, line_dash="dot", line_color="gray", opacity=0.6)
    iv_fig.update_layout(
        height=280,
        margin=dict(t=20, l=60, r=60, b=40),
        xaxis=dict(
            title="Time (ET)",
            rangebreaks=[
                dict(bounds=["sat", "mon"]),
                dict(bounds=[16, 9.5], pattern="hour"),
            ],
        ),
        yaxis=dict(title="Implied vol (%)"),
    )
    st.plotly_chart(iv_fig, width="stretch")

    st.subheader("Point in time")
    timestamps = greeks_df["datetime"].tolist()
    pick = st.select_slider(
        "Minute",
        options=range(len(timestamps)),
        value=len(timestamps) - 1,
        format_func=lambda i: timestamps[i].strftime("%a %m/%d %H:%M"),
    )
    row = greeks_df.iloc[pick]
    top = st.columns(4)
    top[0].metric("Spot", f"${row['spot']:.2f}")
    top[1].metric("Option price", f"${row['option_price']:.3f}")
    top[2].metric("IV", f"{row['iv']*100:.2f}%" if pd.notna(row["iv"]) else "n/a")
    top[3].metric("Delta", f"{row['delta']:.3f}" if pd.notna(row["delta"]) else "n/a")
    bottom = st.columns(4)
    bottom[0].metric("Gamma", f"{row['gamma']:.4f}" if pd.notna(row["gamma"]) else "n/a")
    bottom[1].metric("Vega (per pt)", f"{row['vega']:.3f}" if pd.notna(row["vega"]) else "n/a")
    bottom[2].metric("Theta (per day)", f"{row['theta']:.3f}" if pd.notna(row["theta"]) else "n/a")

    with st.expander("Compare two points (Greeks-based price decomposition)"):
        c1, c2 = st.columns(2)
        idx_a = c1.selectbox(
            "Point A", range(len(timestamps)), index=0,
            format_func=lambda i: timestamps[i].strftime("%a %m/%d %H:%M"),
        )
        idx_b = c2.selectbox(
            "Point B", range(len(timestamps)), index=len(timestamps) - 1,
            format_func=lambda i: timestamps[i].strftime("%a %m/%d %H:%M"),
        )
        a, b = greeks_df.iloc[idx_a], greeks_df.iloc[idx_b]
        if pd.isna(a["iv"]) or pd.isna(b["iv"]):
            st.warning("IV unavailable at one or both points — can't decompose.")
        else:
            dS = b["spot"] - a["spot"]
            days_elapsed = (b["datetime"] - a["datetime"]).total_seconds() / 86400
            dIV_pts = (b["iv"] - a["iv"]) * 100
            avg_delta = (a["delta"] + b["delta"]) / 2
            avg_theta = (a["theta"] + b["theta"]) / 2
            avg_vega = (a["vega"] + b["vega"]) / 2
            delta_contrib = avg_delta * dS
            theta_contrib = avg_theta * days_elapsed
            vega_contrib = avg_vega * dIV_pts
            actual = b["option_price"] - a["option_price"]
            explained = delta_contrib + theta_contrib + vega_contrib

            decomp = pd.DataFrame(
                {
                    "Effect": ["Delta (spot move)", "Theta (time decay)", "Vega (IV change)", "Sum (explained)", "Actual price change"],
                    "Driver": [
                        f"${dS:+.3f} spot move",
                        f"{days_elapsed:+.2f} days elapsed",
                        f"{dIV_pts:+.2f} vol pts ({a['iv']*100:.2f}% -> {b['iv']*100:.2f}%)",
                        "",
                        "",
                    ],
                    "$ contribution": [
                        f"{delta_contrib:+.3f}",
                        f"{theta_contrib:+.3f}",
                        f"{vega_contrib:+.3f}",
                        f"{explained:+.3f}",
                        f"{actual:+.3f}",
                    ],
                }
            )
            st.dataframe(decomp, width="stretch", hide_index=True)
            st.caption(
                "Contribution = average Greek across the two points x the observed "
                "change in its driver. Gamma/vanna/higher-order cross-effects make "
                "up the (usually small) gap between 'Sum' and 'Actual'."
            )

with st.expander("Raw contract data"):
    st.dataframe(contract_df, width="stretch")
