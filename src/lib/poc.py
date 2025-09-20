import awswrangler as wr
import pandas as pd

WORKGROUP="primary"
S3_OUTPUT = "s3://athena-919061006621/"
DB="gm_equity"
TABLE = "gm_equity.options_daily_parquet"
tables = wr.catalog.get_tables(database=DB)
print([t["Name"] for t in tables])

# ------------------------------
# 1) ENTRIES: pick ~30Δ call with expiry ≈ entry_date + horizon_days
#    mode: "nearest" (closest to +45), "exact" (only exact +45), "next_on_or_after" (first expiry >= +45)
# ------------------------------
def query_entries_range(
    ts_start: str, ts_end: str,
    ticker: str = "XSP", cp: str = "C",
    delta_target: float = 0.30, horizon_days: int = 45,
    mode: str = "nearest"
) -> pd.DataFrame:
    base_where = f"""
      o.ticker = '{ticker}'
      AND o.cp = '{cp}'
      AND o.ts >= TIMESTAMP '{ts_start} 00:00:00'
      AND o.ts <  TIMESTAMP '{ts_end} 00:00:00'
    """

    if mode == "exact":
        expiry_clause = f"o.expiry = date_add('day', {horizon_days}, DATE(o.ts))"
        order = "ORDER BY ABS(delta - {delta_target}), strike"
        select_extra = ""
    elif mode == "next_on_or_after":
        expiry_clause = f"o.expiry >= date_add('day', {horizon_days}, DATE(o.ts))"
        order = "ORDER BY o.expiry, ABS(delta - {delta_target}), strike"
        select_extra = ""
    else:  # nearest
        expiry_clause = None
        order = "ORDER BY expiry_diff, ABS(delta - {delta_target}), strike"
        select_extra = f", ABS(date_diff('day', o.expiry, date_add('day', {horizon_days}, DATE(o.ts)))) AS expiry_diff"

    sql = f"""
    WITH cand AS (
      SELECT
          DATE(o.ts) AS entry_date,
          o.ts,
          o.expiry,
          o.ticker,
          o.cp,
          o.strike,
          o.delta,
          o.last AS entry_last
          {select_extra}
      FROM {TABLE} o
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

    df = wr.athena.read_sql_query(
        sql=sql,
        database=DB,
        workgroup=WORKGROUP,
        s3_output=S3_OUTPUT,
        ctas_approach=True  # efficient for bigger ranges
    )
    # Ensure dtypes
    for col in ["entry_date", "expiry"]:
        if col in df:
            df[col] = pd.to_datetime(df[col]).dt.date
    return df




def fetch_option_paths(df_entry: pd.DataFrame) -> pd.DataFrame:
    """
    For each (entry_date, expiry, ticker, cp, strike, entry_last) in df_entry,
    return the daily path from entry_date through expiry, with a SQL-computed
    profit column: profit = last - entry_last.
    """
    if df_entry.empty:
        return df_entry.copy()

    # Use only required columns and dedupe
    cols = ["entry_date", "expiry", "ticker", "cp", "strike", "entry_last"]
    df_keys = (
        df_entry[cols]
        .dropna(subset=cols)
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

    # Safe string escape for SQL
    def esc(s: str) -> str:
        return s.replace("'", "''")

    # Build VALUES rows (all rows must have identical types/order)
    rows = [
        f"(DATE '{r.entry_date}', DATE '{r.expiry}', '{esc(r.ticker)}', '{esc(r.cp)}', "
        f"CAST({float(r.strike)} AS DOUBLE), CAST({float(r.entry_last)} AS DOUBLE))"
        for _, r in df_keys.iterrows()
    ]
    values = ",\n".join(rows)

    sql = f"""
    WITH targets(entry_date, expiry, ticker, cp, strike, entry_last) AS (
      VALUES
      {values}
    )
    SELECT
      t.entry_date,
      DATE(o.ts) AS quote_date,
      o.expiry,
      o.ticker,
      o.cp,
      o.strike,
      t.entry_last,
      o.last,
      100*(o.last - t.entry_last) AS profit
    FROM {TABLE} o
    JOIN targets t
      ON  o.expiry = t.expiry
      AND o.ticker = t.ticker
      AND o.cp     = t.cp
      AND o.strike = t.strike
    WHERE DATE(o.ts) BETWEEN t.entry_date AND t.expiry
    ORDER BY o.ticker, o.cp, o.strike, o.expiry, quote_date
    """

    df = wr.athena.read_sql_query(
        sql=sql,
        database=DB,
        workgroup=WORKGROUP,
        s3_output=S3_OUTPUT,
        ctas_approach=True
    )
    if not df.empty:
        df["entry_date"] = pd.to_datetime(df["entry_date"]).dt.date
        df["quote_date"] = pd.to_datetime(df["quote_date"]).dt.date
    return df


def summarize_hold_to_maturity(df_paths: pd.DataFrame) -> pd.DataFrame:
    """
    From fetch_option_paths output, keep only the expiry-day quote and compute PnL.

    Returns columns:
      entry_date, expiry, strike, entry_last, quote_last, pnl
    """
    if df_paths.empty:
        return pd.DataFrame(columns=[
            "entry_date","expiry","strike","entry_last","quote_last","pnl"
        ])

    # keep only rows where the quote is on expiry
    df_exp = df_paths[df_paths["quote_date"] == df_paths["expiry"]].copy()

    # rename and compute pnl
    df_exp.rename(columns={"last": "quote_last"}, inplace=True)
    #df_exp["pnl"] = df_exp["quote_last"] - df_exp["entry_last"]

    # select/order columns
    out = df_exp[[
        "entry_date", "expiry", "strike", "entry_last", "quote_last", "profit"
    ]].sort_values(["entry_date", "expiry", "strike"]).reset_index(drop=True)

    return out



if __name__ == "__main__":
   
    # 1) Entries across a date range
    df_entry = query_entries_range (
        ts_start="2022-06-10",
        ts_end="2022-06-17",
        ticker="XSP",
        cp="C",
        delta_target=0.30,
        horizon_days=45,
        mode="nearest"  # or "exact" / "next_on_or_after"
    )
    print(df_entry.head())
    df2 = fetch_option_paths(df_entry)
    print(df2.head())
    df_final = summarize_hold_to_maturity(df2)
    print(df_final.head())