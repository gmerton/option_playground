import awswrangler as wr
import pandas as pd
from data.Leg import Leg, Strategy, Direction, OptionType

# -----------------------------
# Athena / Catalog configuration
# -----------------------------
CATALOG   = "awsdatacatalog/s3tablescatalog/gm-equity-tbl-bucket"  # from QueryExecutionContext
WORKGROUP = "dev-v3"                                               # Athena engine v3
S3_OUTPUT = "s3://athena-919061006621/"                            # WG output location (safe to keep)
DB        = "silver"
TABLE     = "options_daily_v2"                                     # referenced as silver.options_daily_v2

CONTRACT_MULTIPLIER = 100

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

# ---------------------------------------
# Strategy/Leg resolution and data fetches
# ---------------------------------------
def query_entries_range_for_strategy(
    ts_start: str,
    ts_end: str,
    ticker: str,
    strategy: "Strategy",
    mode: str = "nearest",
    require_all_legs: bool = True,
) -> pd.DataFrame:
    """
    Resolve each leg to a concrete contract per day in [ts_start, ts_end).
    If require_all_legs=True, keep only entry_dates present for ALL legs.
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

    if require_all_legs:
        needed = set(range(len(strategy.legs)))
        dates_ok = tidy.groupby("entry_date")["leg_index"].apply(lambda s: set(s.unique()) == needed)
        common_dates = set(dates_ok[dates_ok].index)
        tidy = tidy[tidy["entry_date"].isin(common_dates)].copy()

    tidy.sort_values(["entry_date", "leg_index", "expiry", "strike"], inplace=True)
    tidy.reset_index(drop=True, inplace=True)
    return tidy


def query_entries_range_for_leg(
    ts_start: str,
    ts_end: str,
    ticker: str,
    leg: "Leg",
    mode: str = "nearest",
) -> pd.DataFrame:
    """
    Resolve one Leg (delta + DTE) into concrete contracts across [ts_start, ts_end).
    """
    cp = "C" if leg.opt_type.name == "CALL" else "P"
    delta_mag = float(leg.strike_delta) / 100.0
    delta_target = delta_mag if cp == "C" else -delta_mag
    horizon_days = int(leg.dte)

    base_where = f"""
      o.ticker = '{ticker}'
      AND o.cp = '{cp}'
      AND o.trade_date >= TIMESTAMP '{ts_start} 00:00:00'
      AND o.trade_Date <=  TIMESTAMP '{ts_end} 00:00:00'
    """

    if mode == "exact":
        expiry_clause = f"o.expiry = date_add('day', {horizon_days}, o.trade_date)"
        order = "ORDER BY ABS(delta - {delta_target}), strike"
        select_extra = ""
    elif mode == "next_on_or_after":
        expiry_clause = f"o.expiry >= date_add('day', {horizon_days}, o.trade_date)"
        order = "ORDER BY o.expiry, ABS(delta - {delta_target}), strike"
        select_extra = ""
    else:  # nearest
        expiry_clause = None
        order = "ORDER BY expiry_diff, ABS(delta - {delta_target}), strike"
        select_extra = (
            f", ABS(date_diff('day', o.expiry, date_add('day', {horizon_days}, o.trade_date))) AS expiry_diff"
        )

    sql = f"""
    WITH cand AS (
      SELECT
          o.trade_date AS entry_date,
          o.expiry,
          o.ticker,
          o.cp,
          o.strike,
          o.delta,
          (o.bid + o.ask) / 2 AS entry_last
          {select_extra}
      FROM "{DB}"."{TABLE}" o
      WHERE {base_where}
      {" AND " + expiry_clause if expiry_clause else ""}
    ),
    ranked AS (
      SELECT
          *,
          ROW_NUMBER() OVER (
            PARTITION BY entry_date
            {order.format(delta_target=delta_target)}
          ) AS rn
      FROM cand
    )
    SELECT entry_date, expiry, ticker, cp, strike, delta, entry_last
    FROM ranked
    WHERE rn = 1
    ORDER BY entry_date;
    """

    df = athena(sql)

    # Normalize dates
    for col in ("entry_date", "expiry"):
        if col in df:
            df[col] = pd.to_datetime(df[col]).dt.date

    # traceability
    df["leg_direction"] = leg.direction.name
    df["leg_type"] = leg.opt_type.name
    df["leg_quantity"] = leg.quantity
    df["target_delta"] = delta_target
    df["target_dte"] = horizon_days

    return df


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
    summary["roc_like_metric"] = (summary["portfolio_pnl"] / outlay).astype(float)

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

    strat = Strategy(legs=[
        Leg(direction=Direction.SELL,  opt_type=OptionType.CALL,  quantity=1, strike_delta=25.0, dte=30),
        Leg(direction=Direction.SELL,  opt_type=OptionType.PUT,  quantity=1, strike_delta=25.0, dte=30),
    ])

    entries = query_entries_range_for_strategy(
        ts_start="2014-01-01",
        ts_end="2026-01-31",
        ticker="UVXY",
        strategy=strat,
        mode="nearest",
        require_all_legs=True,
    )
    print(entries.head())

    paths = fetch_option_paths_for_strategy_entries(entries)
    print(paths.head())

    portfolio = summarize_hold_to_maturity_strategy(paths)
    print(portfolio)
