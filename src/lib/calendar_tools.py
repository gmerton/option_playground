import pandas as pd
from constants import CONTRACT_MULTIPLIER

def attach_exit_date_min_expiry(tidy_entries: pd.DataFrame) -> pd.DataFrame:
    """For each entry_date, set exit_date = min(expiry) among all legs that day."""
    if tidy_entries.empty:
        return tidy_entries.copy()
    out = tidy_entries.copy()
    min_exp = (
        out.groupby("entry_date", as_index=False)["expiry"]
           .min()
           .rename(columns={"expiry": "exit_date"})
    )
    out = out.merge(min_exp, on="entry_date", how="left", validate="many_to_one")
    out["exit_date"] = pd.to_datetime(out["exit_date"]).dt.date
    return out

def summarize_calendar_exit_on_near_expiry(tidy_entries: pd.DataFrame) -> pd.DataFrame:
    """
    For calendar spreads: exit at the earlier leg's expiry (min expiry per entry_date).
    Returns a per (entry_date, exit_date, expiry_far?) summary.
    """
    if tidy_entries.empty:
        return pd.DataFrame(columns=[
            "entry_date","exit_date","legs","total_contracts",
            "net_entry_premium","portfolio_pnl","roc_like_metric"
        ])

    work = attach_exit_date_min_expiry(tidy_entries)
    if "row_id" not in work.columns:
        work["row_id"] = range(len(work))

    # Fetch quotes at exit_date for both legs
    exitq = fetch_quotes_at_exit(work[[
        "row_id","entry_date","exit_date","expiry","ticker","cp","strike","entry_last"
    ]])

    # Attach leg metadata back
    merged = exitq.merge(
        work[["row_id","entry_date","exit_date","leg_index","leg_direction","leg_type","leg_quantity","entry_last"]],
        on=["row_id","entry_date","exit_date","entry_last"],
        how="left",
        validate="one_to_one"
    )

    # Leg PnL at exit
    sign = merged["leg_direction"].map({"BUY": 1, "SELL": -1}).astype(int)
    # merged["leg_pnl_cd"] = "Debit" if merged["leg_direction"] == "BUY" else "Credit"

    merged["leg_pnl"] = (merged["quote_last"] - merged["entry_last"]) * CONTRACT_MULTIPLIER * sign * merged["leg_quantity"]

    # Cash outlay (signed premium at entry)
    merged["entry_premium_signed"] = (
        merged["entry_last"] * CONTRACT_MULTIPLIER * merged["leg_quantity"] * sign
    )

    print(merged.head().T)
    # Aggregate per entry_date + exit_date
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

    outlay = summary["net_entry_premium"].replace(0, pd.NA)
    summary["roc_like_metric"] = (summary["portfolio_pnl"] / (outlay)).astype(float)

    n_entries = len(summary)
    total_premium = summary["net_entry_premium"].sum()
    total_pnl = summary["portfolio_pnl"].sum()
    average_return = summary["roc_like_metric"].mean()
    count_wins = summary[summary["roc_like_metric"] > 0].shape[0]
    win_rate = count_wins / n_entries
    print(summary)

    print("\n=== Portfolio Summary ===")
    print(f"Entries analyzed: {n_entries}")
    print(f"Total Net Entry Premium: {round(total_premium)}")
    print(f"Total Portfolio PnL: {round(total_pnl)}")
    print(f"Mean return: {round(average_return*100,1)}%")
    print(f"Win rate: {100*round(win_rate,1)}%")

    return summary


