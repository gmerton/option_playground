import awswrangler as wr
import pandas as pd
import uuid
from data.Leg import Leg, Strategy, Direction, OptionType
from typing import Iterable, Optional
import datetime
from condor_tools import condor_study, evaluate_condor
import numpy as np


# -----------------------------
# Athena / Catalog configuration
# -----------------------------
CATALOG   = "awsdatacatalog/s3tablescatalog/gm-equity-tbl-bucket"  # from QueryExecutionContext
WORKGROUP = "dev-v3"                                               # Athena engine v3
S3_OUTPUT = "s3://athena-919061006621/"                            # WG output location (safe to keep)
DB        = "silver"
TABLE     = "options_daily_v2"                                     # referenced as silver.options_daily_v2
TMP_S3_PREFIX = "s3://athena-919061006621/tmp_targets/" 
CONTRACT_MULTIPLIER = 100
GLUE_CATALOG = "AwsDataCatalog"  # Glue Data Catalog name
S3TABLES_CATALOG = CATALOG       # your existing "awsdatacatalog/..." string






def _compute_condor_capital_for_group(group: pd.DataFrame, net_entry_premium_total: float) -> float:
    """
    Compute total capital (max loss) for a short iron condor within a single
    (entry_date, expiry) group from `merged`.

    Returns NaN if the group is not a recognizable 4-leg condor.
    """
    # Identify legs
    sc = group[(group["leg_type"] == "CALL") & (group["leg_direction"] == "SELL")]
    lc = group[(group["leg_type"] == "CALL") & (group["leg_direction"] == "BUY")]
    sp = group[(group["leg_type"] == "PUT")  & (group["leg_direction"] == "SELL")]
    lp = group[(group["leg_type"] == "PUT")  & (group["leg_direction"] == "BUY")]

    # Must have at least one of each side to qualify as a condor
    if sc.empty or lc.empty or sp.empty or lp.empty:
        return float("nan")

    # If multiple rows per side (rare here), take the 1st by convention
    # (you can make this smarter to match by quantity if needed)
    sc_strike = float(sc.iloc[0]["strike"])
    lc_strike = float(lc.iloc[0]["strike"])
    sp_strike = float(sp.iloc[0]["strike"])
    lp_strike = float(lp.iloc[0]["strike"])

    # Wing widths (should be positive)
    width_call = max(0.0, lc_strike - sc_strike)
    width_put  = max(0.0, sp_strike - lp_strike)

    if width_call == 0.0 and width_put == 0.0:
        return float("nan")

    # Spreads count: minimum quantity across the 4 defining legs
    sc_qty = int(sc.iloc[0]["leg_quantity"])
    lc_qty = int(lc.iloc[0]["leg_quantity"])
    sp_qty = int(sp.iloc[0]["leg_quantity"])
    lp_qty = int(lp.iloc[0]["leg_quantity"])
    spreads_count = min(sc_qty, lc_qty, sp_qty, lp_qty)
    if spreads_count <= 0:
        return float("nan")

    # Total credit received is -net_entry_premium_total (your premium is signed & includes *100*qty)
    credit_total = -float(net_entry_premium_total)

    # Capital = max(wing width) * 100 * spreads_count - total credit
    max_wing_total = max(width_call, width_put) * CONTRACT_MULTIPLIER * spreads_count
    capital_total = max_wing_total - credit_total

    # Capital cannot be negative (guard for edge rounding)
    return max(capital_total, 0.0)



def athena(sql: str) -> pd.DataFrame:
    """Single path for all Athena queries against the S3 Tables catalog."""
    return wr.athena.read_sql_query(
        sql=sql,
        database=DB,
        workgroup=WORKGROUP,
        data_source=CATALOG,   # IMPORTANT: non-AwsDataCatalog
        s3_output=S3_OUTPUT,
        ctas_approach=False    # REQUIRED when data_source != AwsDataCatalog
    )

# def _normalize_weekdays(entry_weekdays: Optional[Iterable]) -> Optional[set[int]]:
#     """
#     Accepts integers (0=Mon..6=Sun) and/or strings like 'WED', 'Fri'.
#     Returns a normalized set of ints or None.
#     """
#     if entry_weekdays is None:
#         return None
#     out = set()
#     for w in entry_weekdays:
#         if isinstance(w, int):
#             out.add(int(w) % 7)
#         elif isinstance(w, str):
#             out.add(WEEKDAY_ALIASES[w.strip().upper()[:3]])
#         else:
#             raise ValueError(f"Unsupported weekday spec: {w!r}")
#     return out




def fetch_option_paths(df_entry: pd.DataFrame) -> pd.DataFrame:
    """
    Given selected entries (entry_date/expiry/ticker/cp/strike/entry_last),
    return daily price paths (quote_date) for those contracts up to expiry.
    """
    if df_entry.empty:
        return df_entry.copy()

    has_row_id = "row_id" in df_entry.columns

    base_cols = ["entry_date", "expiry", "ticker", "cp", "strike", "entry_last"]
    cols = base_cols + (["row_id"] if has_row_id else [])
    df_keys = (
        df_entry[cols]
        .dropna(subset=base_cols)
        .drop_duplicates()
        .copy()
    )

    # Normalize types
    df_keys["entry_date"] = pd.to_datetime(df_keys["entry_date"]).dt.date
    df_keys["expiry"] = pd.to_datetime(df_keys["expiry"]).dt.date
    df_keys["ticker"] = df_keys["ticker"].astype(str)
    df_keys["cp"] = df_keys["cp"].astype(str)
    df_keys["strike"] = pd.to_numeric(df_keys["strike"], errors="raise")
    df_keys["entry_last"] = pd.to_numeric(df_keys["entry_last"], errors="raise")

    def esc(s: str) -> str:
        return s.replace("'", "''")

    # Build VALUES rows
    if has_row_id:
        rows = [
            f"(DATE '{r.entry_date}', DATE '{r.expiry}', '{esc(r.ticker)}', '{esc(r.cp)}', "
            f"CAST({float(r.strike)} AS DOUBLE), CAST({float(r.entry_last)} AS DOUBLE), CAST({int(r.row_id)} AS INTEGER))"
            for _, r in df_keys.iterrows()
        ]
        targets_ddl = "(entry_date, expiry, ticker, cp, strike, entry_last, row_id)"
        select_cols = "t.entry_date, o.trade_date AS quote_date, o.expiry, o.ticker, o.cp, o.strike, t.entry_last, o.last, 100*(o.last - t.entry_last) AS profit, t.row_id"
    else:
        rows = [
            f"(DATE '{r.entry_date}', DATE '{r.expiry}', '{esc(r.ticker)}', '{esc(r.cp)}', "
            f"CAST({float(r.strike)} AS DOUBLE), CAST({float(r.entry_last)} AS DOUBLE))"
            for _, r in df_keys.iterrows()
        ]
        targets_ddl = "(entry_date, expiry, ticker, cp, strike, entry_last)"
        select_cols = "t.entry_date, o.trade_date AS quote_date, o.expiry, o.ticker, o.cp, o.strike, t.entry_last, o.last, 100*(o.last - t.entry_last) AS profit"

    values = ",\n".join(rows)

    sql = f"""
    WITH targets{targets_ddl} AS (
      VALUES
      {values}
    )
    SELECT
      {select_cols}
    FROM "{DB}"."{TABLE}" o
    JOIN targets t
      ON  o.expiry = t.expiry
      AND o.ticker = t.ticker
      AND o.cp     = t.cp
      AND o.strike = t.strike
    WHERE o.trade_date BETWEEN t.entry_date AND t.expiry
    ORDER BY o.ticker, o.cp, o.strike, o.expiry, quote_date
    """

    df = athena(sql)
    if not df.empty:
        df["entry_date"] = pd.to_datetime(df["entry_date"]).dt.date
        df["quote_date"] = pd.to_datetime(df["quote_date"]).dt.date
    return df


def fetch_option_paths_for_strategy_entries(tidy_entries: pd.DataFrame) -> pd.DataFrame:
    """
    Accepts the tidy DF from query_entries_range_for_strategy().
    Returns a long DF of daily paths with leg metadata attached.
    """
    if tidy_entries.empty:
        return tidy_entries.copy()

    tidy = tidy_entries.copy()
    tidy["row_id"] = range(len(tidy))

    paths = fetch_option_paths(tidy[[
        "row_id", "entry_date", "expiry", "ticker", "cp", "strike", "entry_last"
    ]].copy())

    out = paths.merge(
        tidy[["row_id","entry_date","leg_index","leg_direction","leg_type","leg_quantity"]],
        on=["row_id","entry_date"],
        how="left",
        validate="many_to_one"
    )
    return out


def summarize_hold_to_maturity_strategy(paths_long: pd.DataFrame) -> pd.DataFrame:
    """
    Keep expiry quotes only and compute portfolio PnL across all legs per entry_date.
    'profit' is already CONTRACT_MULTIPLIER * (opt_price - entry_price) per contract.
    """
    if paths_long.empty:
        return pd.DataFrame(columns=[
            "entry_date", "legs", "total_contracts", "net_entry_premium",
            "portfolio_pnl", "roc_like_metric"
        ])

    df_exp = paths_long[paths_long["quote_date"] == paths_long["expiry"]].copy()

    sign = df_exp["leg_direction"].map({"BUY": 1, "SELL": -1}).astype(int)
    df_exp["leg_pnl"] = df_exp["profit"] * sign * df_exp["leg_quantity"]

    df_exp["entry_premium_signed"] = (
        df_exp["entry_last"] * CONTRACT_MULTIPLIER * df_exp["leg_quantity"] * sign
    )

    summary = (
        df_exp.groupby("entry_date", as_index=False)
              .agg(
                  legs=("leg_index","nunique"),
                  total_contracts=("leg_quantity","sum"),
                  net_entry_premium=("entry_premium_signed","sum"),
                  portfolio_pnl=("leg_pnl","sum"),
              )
              .sort_values("entry_date")
    )

    outlay = summary["net_entry_premium"].replace(0, pd.NA)
    summary["roc_like_metric"] = (summary["portfolio_pnl"] / (outlay)).astype(float)

    total_pnl = summary["portfolio_pnl"].sum()
    total_investment = summary["net_entry_premium"].sum()
    roc = ((total_pnl - total_investment) / (total_investment if total_investment else 1)) + 1
    print(f"Total Investment: {total_investment}")
    print(f"Total PnL: {total_pnl}")
    print(f"ROC: {roc}")
    return summary








def summarize_hold_to_maturity(df_paths: pd.DataFrame) -> pd.DataFrame:
    """
    From fetch_option_paths output, keep only the expiry-day quote and compute total PnL.
    """
    if df_paths.empty:
        return pd.DataFrame(columns=[
            "entry_date","expiry","strike","entry_last","quote_last","profit"
        ])

    df_exp = df_paths[df_paths["quote_date"] == df_paths["expiry"]].copy()
    df_exp.rename(columns={"last": "quote_last"}, inplace=True)

    out = df_exp[[
        "entry_date", "expiry", "strike", "entry_last", "quote_last", "profit"
    ]].sort_values(["entry_date", "expiry", "strike"]).reset_index(drop=True)

    total_pnl = out["profit"].sum()
    total_investment = CONTRACT_MULTIPLIER * out["entry_last"].sum()
    roc = ((total_pnl - total_investment) / (total_investment if total_investment else 1)) + 1
    print(f"Total Investment: {total_investment}")
    print(f"Total PnL: {total_pnl}")
    print(f"ROC: {roc}")



    return out


if __name__ == "__main__":
    # example usage
    leg = Leg(direction=Direction.BUY, opt_type=OptionType.CALL, quantity=1,
              strike_delta=30.0, dte=45)

    # Butterfly
    # strat = Strategy(legs=[
    #     Leg(direction=Direction.BUY,  opt_type=OptionType.CALL,  quantity=1, strike_delta=95.0, dte=45),
    #     Leg(direction=Direction.BUY,  opt_type=OptionType.CALL,  quantity=2, strike_delta=50.0, dte=45),
    #     Leg(direction=Direction.BUY,  opt_type=OptionType.CALL,  quantity=1, strike_delta=5.0,  dte=45),
    # ])


    short_straddle = Strategy(legs=[
        Leg(direction=Direction.SELL,  opt_type=OptionType.CALL,  quantity=1, strike_delta=50, dte=30),
        Leg(direction=Direction.SELL,  opt_type=OptionType.PUT,  quantity=1, strike_delta=50, dte=30),
    ])
    
    calendar = Strategy(legs=[
        Leg(direction=Direction.SELL,  opt_type=OptionType.CALL,  quantity=1, strike_delta=50, dte=30),
        Leg(direction=Direction.BUY,  opt_type=OptionType.CALL,  quantity=1, strike_delta=50, dte=45),
    ])

    double_calendar = Strategy(legs=[
        Leg(direction=Direction.SELL,  opt_type=OptionType.CALL,  quantity=1, strike_delta=62, dte=10),
        Leg(direction=Direction.BUY,  opt_type=OptionType.CALL,  quantity=1, strike_delta=62, dte=17),
        Leg(direction=Direction.SELL,  opt_type=OptionType.PUT,  quantity=1, strike_delta=33, dte=10),
        Leg(direction=Direction.BUY,  opt_type=OptionType.PUT,  quantity=1, strike_delta=33, dte=17),
    ])


    #Evaluate different condor strike structures for a ticker.
    # condor_study("IBIT")

    #Evaluate a single condor
    evaluate_condor("IBIT", 25, 5)

    #condor = Strategy(legs=[
    #         Leg(direction=Direction.SELL,  opt_type=OptionType.CALL,  quantity=1, strike_delta=shoulder, dte=30),
    #         Leg(direction=Direction.SELL,  opt_type=OptionType.PUT,  quantity=1, strike_delta=shoulder, dte=30),
    #         Leg(direction=Direction.BUY,  opt_type=OptionType.CALL,  quantity=1, strike_delta=wing, dte=30),
    #         Leg(direction=Direction.BUY,  opt_type=OptionType.PUT,  quantity=1, strike_delta=wing, dte=30),
    #      ])

    # results = []

    # for i in range(1,2):
    #     for j in range(5, 6):
    #         wing = 5*i
    #         shoulder = 5*j
    #         condor = Strategy(legs=[
    #         Leg(direction=Direction.SELL,  opt_type=OptionType.CALL,  quantity=1, strike_delta=shoulder, dte=30),
    #         Leg(direction=Direction.SELL,  opt_type=OptionType.PUT,  quantity=1, strike_delta=shoulder, dte=30),
    #         Leg(direction=Direction.BUY,  opt_type=OptionType.CALL,  quantity=1, strike_delta=wing, dte=30),
    #         Leg(direction=Direction.BUY,  opt_type=OptionType.PUT,  quantity=1, strike_delta=wing, dte=30),
    #      ])

        
    #         entries = query_entries_range_for_strategy(
    #         ts_start="2022-12-15",
    #         ts_end="2026-03-16",
    #         ticker="IBIT",
    #         strategy=condor,
    #         mode="nearest",
    #         require_all_legs=True,
    #         entry_weekdays={"WED"}
    #         )
    #         print("")
    #         print(f"wing={wing}, shoulder={shoulder}")
    #         summary_json = summarize_hold_to_maturity_strategy_from_entries(entries) #Use this for straddles/strangles
    #         summary_json["wing"]=wing
    #         summary_json["shoulder"]=shoulder
    #         results.append(summary_json)
    # print(results)

    

    # df = pd.DataFrame(results, columns=["shoulder", "wing", "roc", "win_rate"])
    # df.to_csv("condor.csv", index=False)

    # for result in results:
    #     print(result)
    
    #cal_summary = summarize_calendar_exit_on_near_expiry(entries)
    #summarize_exit_on_earliest_expiry(entries) # use this for double calendars
    # paths = fetch_option_paths_for_strategy_entries(entries)
    # print(paths.head())

    # portfolio = summarize_hold_to_maturity_strategy(paths)
    # print(portfolio)
