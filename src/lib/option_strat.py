import pandas as pd
import awswrangler as wr
import uuid
from typing import Iterable, Optional
from constants import TMP_S3_PREFIX, DB, CONTRACT_MULTIPLIER, WEEKDAY_ALIASES
from athena_lib import athena, query_entries_range_for_leg, fetch_expiry_quotes, fetch_quotes_at_exit


# ---------------------------------------
# Strategy/Leg resolution and data fetches
# Returns data by leg
# ---------------------------------------
def query_entries_range_for_strategy(
    ts_start: str,
    ts_end: str,
    ticker: str,
    strategy: "Strategy",
    mode: str = "nearest",
    require_all_legs: bool = True,
    entry_weekdays: Optional[Iterable] = None,  # NEW: e.g., {"WED"} or {2}
) -> pd.DataFrame:
    """
    Resolve each leg to a concrete contract per day in [ts_start, ts_end).
    If require_all_legs=True, keep only entry_dates present for ALL legs.
    If entry_weekdays is provided, keep only those weekdays (0=Mon..6=Sun or {'WED'}).
    """
    per_leg = []
    for idx, leg in enumerate(strategy.legs):
        df_leg = query_entries_range_for_leg(
            ts_start=ts_start,
            ts_end=ts_end,
            ticker=ticker,
            leg=leg,
            mode=mode,
        ).copy()
        df_leg["leg_index"]     = idx
        df_leg["leg_direction"] = leg.direction.name
        df_leg["leg_type"]      = leg.opt_type.name
        df_leg["leg_quantity"]  = leg.quantity
        df_leg["target_delta"]  = float(leg.strike_delta) / 100.0
        df_leg["target_dte"]    = int(leg.dte)
        per_leg.append(df_leg)

    if not per_leg:
        return pd.DataFrame()

    tidy = pd.concat(per_leg, ignore_index=True)

    # --- NEW: filter by weekday(s) if requested ---
    wd_filter = _normalize_weekdays(entry_weekdays)
    if wd_filter:
        wd = pd.to_datetime(tidy["entry_date"]).dt.weekday
        tidy = tidy[wd.isin(wd_filter)].copy()
        if tidy.empty:
            return tidy  # nothing left after weekday filtering

    if require_all_legs:
        needed = set(range(len(strategy.legs)))
        dates_ok = tidy.groupby("entry_date")["leg_index"].apply(lambda s: set(s.unique()) == needed)
        common_dates = set(dates_ok[dates_ok].index)
        tidy = tidy[tidy["entry_date"].isin(common_dates)].copy()

    tidy.sort_values(["entry_date", "leg_index", "expiry", "strike"], inplace=True)
    tidy.reset_index(drop=True, inplace=True)
    print(f"tidy={tidy}")
    return tidy




def _normalize_weekdays(entry_weekdays: Optional[Iterable]) -> Optional[set[int]]:
    """
    Accepts integers (0=Mon..6=Sun) and/or strings like 'WED', 'Fri'.
    Returns a normalized set of ints or None.
    """
    if entry_weekdays is None:
        return None
    out = set()
    for w in entry_weekdays:
        if isinstance(w, int):
            out.add(int(w) % 7)
        elif isinstance(w, str):
            out.add(WEEKDAY_ALIASES[w.strip().upper()[:3]])
        else:
            raise ValueError(f"Unsupported weekday spec: {w!r}")
    return out



def summarize_exit_on_earliest_expiry(tidy_entries: pd.DataFrame) -> pd.DataFrame:
    """
    Generic for complex strategies: exit all legs at the earliest expiry per entry_date.
    Returns per (entry_date, exit_date) summary with PnL and ROC-like metric.
    """
    if tidy_entries.empty:
        return pd.DataFrame(columns=[
            "entry_date","exit_date","legs","total_contracts",
            "net_entry_premium","portfolio_pnl","roc_like_metric"
        ])

    work = attach_exit_date_min_expiry(tidy_entries)
    if "row_id" not in work.columns:
        work["row_id"] = range(len(work))

    # Get exit-day quotes for every leg
    exitq = fetch_quotes_at_exit(work[[
        "row_id","entry_date","exit_date","expiry","ticker","cp","strike","entry_last"
    ]])

    # Join back leg metadata (one-to-one on row_id after dedup)
    merged = exitq.merge(
        work[["row_id","entry_date","exit_date","leg_index","leg_direction","leg_type","leg_quantity","entry_last"]],
        on=["row_id","entry_date","exit_date","entry_last"],
        how="left",
        validate="one_to_one"
    )

    # Per-leg PnL at exit (signed by BUY/SELL)
    sign = merged["leg_direction"].map({"BUY": 1, "SELL": -1}).astype(int)
    merged["leg_pnl"] = (merged["quote_last"] - merged["entry_last"]) * CONTRACT_MULTIPLIER * sign * merged["leg_quantity"]

    # Signed entry premium (cash outlay at entry)
    merged["entry_premium_signed"] = (
        merged["entry_last"] * CONTRACT_MULTIPLIER * merged["leg_quantity"] * sign
    )

    # Aggregate to portfolio per entry_date + exit_date
    summary = (
        merged.groupby(["entry_date","exit_date"], as_index=False)
              .agg(
                  legs=("leg_index","nunique"),
                  total_contracts=("leg_quantity","sum"),
                  net_entry_premium=("entry_premium_signed","sum"),
                  portfolio_pnl=("leg_pnl","sum"),
              )
              .sort_values(["entry_date","exit_date"])
    )

    #outlay = summary["net_entry_premium"].replace(0, pd.NA) 
    outlay = summary["net_entry_premium"]
    summary["roc_like_metric"] = (summary["portfolio_pnl"] / (outlay)).astype(float)
    n_entries = len(summary)
    total_premium = summary["net_entry_premium"].sum()
    total_pnl = summary["portfolio_pnl"].sum()
    average_return = summary["roc_like_metric"].mean()
    count_wins = summary[summary["roc_like_metric"] > 0].shape[0]
    win_rate = count_wins / n_entries

    print("\n=== Portfolio Summary ===")
    print(f"Entries analyzed: {n_entries}")
    print(f"Total Net Entry Premium: {round(total_premium)}")
    print(f"Total Portfolio PnL: {round(total_pnl)}")
    print(f"Mean return: {round(average_return*100,1)}%")
    print(f"Win rate: {100*round(win_rate,1)}%")

    ########
    return summary






def summarize_hold_to_maturity_strategy_from_entries(tidy_entries: pd.DataFrame) -> pd.DataFrame:
    """
    Accepts the tidy DF from query_entries_range_for_strategy() (it contains leg metadata + entry_last).
    Returns portfolio-level JSON with:
      - roc: total_pnl / total_capital (condor-style capital)
      - win_rate: share of rows with positive roc_like_metric
    Also computes per (entry_date, expiry):
      - capital: max loss / BPR for a short iron condor
      - roc_like_metric: PnL / credit (legacy metric)
    """
    if tidy_entries.empty:
        return {"roc": float(0.0), "win_rate": float(0.0)}

    work = tidy_entries.copy()
    if "row_id" not in work.columns:
        work["row_id"] = range(len(work))

    # Pull expiry quotes (one row per row_id)
    expq = fetch_expiry_quotes(work[[
        "row_id","entry_date","expiry","ticker","cp","strike","entry_last"
    ]]).drop_duplicates(subset=["row_id"], keep="first")

    # Merge leg metadata (include strike/expiry to keep merge one-to-one)
    merged = expq.merge(
        work[["row_id","entry_date","expiry","strike","leg_index","leg_direction","leg_type","leg_quantity","entry_last"]],
        on=["row_id","entry_date","expiry","strike","entry_last"],
        how="left",
        validate="one_to_one"
    )

    # Per-leg PnL at expiry (NOTE: profit already includes *100*)
    sign = merged["leg_direction"].map({"BUY": 1, "SELL": -1}).astype(int)
    merged["leg_pnl"] = merged["profit"] * sign * merged["leg_quantity"]

    # Signed entry premium (already *100*)
    merged["entry_premium_signed"] = (
        merged["entry_last"] * CONTRACT_MULTIPLIER * merged["leg_quantity"] * sign
    )
    print("merged")
    print(merged)
    # ---- EARLY FILTER: drop groups with net_entry_premium ≈ 0 or NaN ----
    EPS = 1e-9
    nep_by_group = (
        merged.groupby(["entry_date","expiry"], as_index=False)["entry_premium_signed"]
              .sum()
              .rename(columns={"entry_premium_signed": "net_entry_premium"})
    )
    nep_by_group = nep_by_group[nep_by_group["net_entry_premium"].notna()]
    nep_by_group = nep_by_group[nep_by_group["net_entry_premium"].abs() > EPS]

    # Keep only allowed keys in merged
    if nep_by_group.empty:
        return {"roc": float(0.0), "win_rate": float(0.0)}

    allowed = set(map(tuple, nep_by_group[["entry_date","expiry"]].itertuples(index=False, name=None)))
    merged = merged[merged.apply(lambda r: (r["entry_date"], r["expiry"]) in allowed, axis=1)].copy()
    if merged.empty:
        return {"roc": float(0.0), "win_rate": float(0.0)}

    # Build summary core and attach filtered net_entry_premium
    summary_core = (
        merged.groupby(["entry_date","expiry"], as_index=False)
              .agg(
                  legs=("leg_index","nunique"),
                  total_contracts=("leg_quantity","sum"),
                  portfolio_pnl=("leg_pnl","sum"),
              )
              .sort_values(["entry_date","expiry"])
    )
    summary = summary_core.merge(nep_by_group, on=["entry_date","expiry"], how="left", validate="one_to_one")
    print(summary.head())

    # roc_like_metric: PnL / (-net_entry_premium) (safe)
    def _safe_roc_like(pnl, nep):
        if pd.isna(nep) or abs(nep) <= EPS:
            return pd.NA
        return float(pnl) / float(-nep)

    summary["roc_like_metric"] = [ _safe_roc_like(p, n) for p, n in zip(summary["portfolio_pnl"], summary["net_entry_premium"]) ]
    print("summary 2")
    print(summary.head())

    # ----- Capital (condor max loss) computed from group data -----
    def _compute_condor_capital_for_group(group: pd.DataFrame) -> float:
        sc = group[(group["leg_type"] == "CALL") & (group["leg_direction"] == "SELL")]
        lc = group[(group["leg_type"] == "CALL") & (group["leg_direction"] == "BUY")]
        sp = group[(group["leg_type"] == "PUT")  & (group["leg_direction"] == "SELL")]
        lp = group[(group["leg_type"] == "PUT")  & (group["leg_direction"] == "BUY")]
        if sc.empty or lc.empty or sp.empty or lp.empty:
            return float("nan")

        sc_strike = float(sc.iloc[0]["strike"]); lc_strike = float(lc.iloc[0]["strike"])
        sp_strike = float(sp.iloc[0]["strike"]); lp_strike = float(lp.iloc[0]["strike"])

        width_call = max(0.0, lc_strike - sc_strike)
        width_put  = max(0.0, sp_strike - lp_strike)
        if width_call == 0.0 and width_put == 0.0:
            return float("nan")

        sc_qty = int(sc.iloc[0]["leg_quantity"]); lc_qty = int(lc.iloc[0]["leg_quantity"])
        sp_qty = int(sp.iloc[0]["leg_quantity"]); lp_qty = int(lp.iloc[0]["leg_quantity"])
        spreads_count = min(sc_qty, lc_qty, sp_qty, lp_qty)
        if spreads_count <= 0:
            return float("nan")

        net_entry_premium_total = float(group["entry_premium_signed"].sum())  # signed, *100*
        credit_total = -net_entry_premium_total  # positive for credit

        max_wing_total = max(width_call, width_put) * CONTRACT_MULTIPLIER * spreads_count
        capital_total = max_wing_total - credit_total
        return max(capital_total, 0.0)

    cap_df = (merged.groupby(["entry_date","expiry"])
                    .apply(_compute_condor_capital_for_group)
                    .reset_index(name="capital"))

    summary = summary.merge(cap_df, on=["entry_date","expiry"], how="left", validate="one_to_one")
    print("summary 3")
    print(summary)
    output_df_csv = pd.DataFrame(summary, columns=["entry_date", "expiry", "portfolio_pnl", "net_entry_premium", "roc_like_metric", "capital" ])
    output_df_csv.to_csv("output/condor_detail.csv", index=False)
    # roc on capital (safe)
    def _safe_div(a, b):
        if pd.isna(b) or b == 0:
            return pd.NA
        return float(a) / float(b)

    summary["roc"] = [_safe_div(p, c) for p, c in zip(summary["portfolio_pnl"], summary["capital"])]

    # ---- Portfolio-level metrics ----
    n_entries = len(summary)
    total_cap = float(summary["capital"].fillna(0).sum())
    total_pnl = float(summary["portfolio_pnl"].fillna(0).sum())

    roc = (total_pnl / total_cap) if total_cap > EPS else 0.0
    count_wins = int((summary["roc_like_metric"].fillna(0) > 0).sum())
    win_rate = (count_wins / n_entries) if n_entries else 0.0

    print("\n=== Portfolio Summary ===")
    print(f"Entries analyzed: {n_entries}")
    print(f"Total capital = {round(total_cap)}")
    print(f"ROC = {round(100*roc,1)}%")
    print(f"Total Net Entry Premium: {round(float(summary['net_entry_premium'].sum()))}")
    print(f"Total Portfolio PnL: {round(total_pnl)}")
    print(f"Mean return vs credit: {round(float(pd.Series(summary['roc_like_metric']).dropna().mean()*100) if summary['roc_like_metric'].notna().any() else 0.0, 1)}%")
    print(f"Win rate: {round(win_rate*100,1)}%")

    return {
        "roc": float(round(roc, 3)),
        "win_rate": float(round(win_rate, 3)),
    }
