from constants import DB, WORKGROUP, CATALOG, S3_OUTPUT
import pandas as pd
import awswrangler as wr
from constants import GLUE_CATALOG, S3TABLES_CATALOG, TABLE, TMP_S3_PREFIX
import uuid
from data import Leg

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

def fetch_quotes_at_exit(df_entry: pd.DataFrame, debug_keep_tmp: bool = False) -> pd.DataFrame:
    """
    Expect columns: row_id, entry_date, exit_date, expiry, ticker, cp, strike, entry_last
    Returns one row per row_id with quote_last on exit_date (even if exit_date < leg expiry).
    """
    if df_entry.empty:
        return df_entry.copy()

    needed = ["row_id","entry_date","exit_date","expiry","ticker","cp","strike","entry_last"]
    miss = [c for c in needed if c not in df_entry.columns]
    if miss:
        raise ValueError(f"fetch_quotes_at_exit: missing columns: {miss}")

    tgt = (df_entry[needed]
           .dropna(subset=["entry_date","exit_date","expiry","ticker","cp","strike","entry_last"])
           .drop_duplicates()
           .copy())

    # normalize types
    for c in ("entry_date","exit_date","expiry"):
        tgt[c] = pd.to_datetime(tgt[c]).dt.date
    tgt["ticker"] = tgt["ticker"].astype(str)
    tgt["cp"] = tgt["cp"].astype(str)
    tgt["strike"] = pd.to_numeric(tgt["strike"], errors="raise")
    tgt["entry_last"] = pd.to_numeric(tgt["entry_last"], errors="raise")

    _ensure_glue_db(DB)
    tmp_table, tmp_path = _create_temp_targets_table(tgt, DB)

    try:
        # Get the price on the exit_date. If your table can have >1 row that day, collapse to a single row per row_id.
        sql = f"""
        WITH matched AS (
          SELECT
            t.row_id,
            t.entry_date,
            t.exit_date,
            o.expiry,
            o.ticker,
            o.cp,
            o.strike,
            t.entry_last,
            o.last
          FROM "{S3TABLES_CATALOG}"."{DB}"."{TABLE}" o
          JOIN "{GLUE_CATALOG}"."{DB}"."{tmp_table}" t
            ON  o.expiry = t.expiry
            AND o.ticker = t.ticker
            AND o.cp     = t.cp
            AND o.strike = t.strike
          WHERE o.trade_date = t.exit_date
        )
        SELECT
          row_id,
          entry_date,
          exit_date,
          expiry,
          ticker,
          cp,
          strike,
          entry_last,
          MAX(last) AS quote_last     -- use MAX/AVG or a ROW_NUMBER tie-breaker if you have a timestamp
        FROM matched
        GROUP BY row_id, entry_date, exit_date, expiry, ticker, cp, strike, entry_last
        ORDER BY row_id
        """
        df = athena(sql)
    finally:
        if not debug_keep_tmp:
            _drop_temp_targets_table(DB, tmp_table, tmp_path)
        else:
            print(f"[DEBUG] kept temp table: {GLUE_CATALOG}.{DB}.{tmp_table}")

    if df.empty:
        return df

    # Safety: dedup by row_id if backend still returned dups
    before = len(df)
    df = df.drop_duplicates(subset=["row_id"], keep="first").copy()
    if len(df) != before:
        print(f"⚠️ Deduplicated exit quotes: removed {before - len(df)} duplicate rows by row_id.")

    # normalize
    df["entry_date"] = pd.to_datetime(df["entry_date"]).dt.date
    df["exit_date"]  = pd.to_datetime(df["exit_date"]).dt.date
    df["expiry"]     = pd.to_datetime(df["expiry"]).dt.date
    return df

def _drop_temp_targets_table(database: str, table: str, s3_path: str) -> None:
    try:
        wr.catalog.delete_table_if_exists(database=database, table=table)
    except Exception:
        pass
    try:
        wr.s3.delete_objects(s3_path)
    except Exception:
        pass

def _ensure_glue_db(database: str):
    """
    Ensure a Glue database exists. Uses does_database_exist when available,
    otherwise falls back to scanning get_databases().
    """
    try:
        # Newer awswrangler versions
        if hasattr(wr.catalog, "does_database_exist"):
            if not wr.catalog.does_database_exist(name=database):
                wr.catalog.create_database(name=database)
            return

        # Fallback for older versions
        dbs = wr.catalog.get_databases()
        names = {d.get("Name") or d.get("name") for d in dbs if isinstance(d, dict)}
        if database not in names:
            wr.catalog.create_database(name=database)

    except Exception as e:
        # Surface a clearer error with context
        raise RuntimeError(f"Unable to verify or create Glue database '{database}': {e}") from e
    
def _create_temp_targets_table(df: pd.DataFrame, database: str) -> tuple[str, str]:
    """Write df to S3 as parquet and register a temporary Glue table."""
    table_name = f"tmp_targets_{uuid.uuid4().hex}"
    s3_path = TMP_S3_PREFIX.rstrip("/") + f"/{table_name}/"

    dfw = df.copy()
    # Normalize types for Glue/Athena
    for c in ("entry_date", "expiry"):
        dfw[c] = pd.to_datetime(dfw[c]).dt.date

    dtype = {
        "entry_date": "date",
        "expiry": "date",
        "ticker": "string",
        "cp": "string",
        "strike": "double",
        "entry_last": "double",
    }
    if "row_id" in dfw.columns:
        dtype["row_id"] = "bigint"

    wr.s3.to_parquet(
        df=dfw,
        path=s3_path,
        dataset=True,
        database=DB,
        table=table_name,
        compression="snappy",
        mode="overwrite",
        dtype=dtype,
    )
    return table_name, s3_path

def step2Sql(ticker:str, ts_start:str, ts_end:str):
    return f"""SELECT X.ticker, X.entry_date, X.expiry, X.cp, X.strike, X.delta, entry_price_mid, exit_price_mid 
        FROM temp2 X inner join
    (SELECT ticker, expiry,cp, strike, trade_date, round((bid + ask)/2,3) as exit_price_mid FROM options_daily_v2 
        WHERE ticker = '{ticker}' AND trade_date >= TIMESTAMP '{ts_start} 00:00:00'
    AND  trade_date <= TIMESTAMP '{ts_end} 00:00:00' and trade_date = expiry) as Y
    ON X.ticker = Y.ticker and X.expiry = Y.expiry and X.cp = Y.cp and X.strike = Y.strike
    """
    

def step1Sql(ticker:str, ts_start:str, ts_end: str, dte:int):
    return f"""CREATE TABLE silver.temp2 as
    WITH cand AS (
        SELECT
            o.trade_date AS entry_date,
            o.expiry,
            o.ticker,
            o.cp,
            o.strike,
            o.delta,
            ROUND((o.bid + o.ask) / 2, 3) AS entry_price_mid,
            ABS(date_diff('day', o.expiry, date_add('day', {dte}, o.trade_date))) AS expiry_diff
    FROM "silver"."options_daily_v2" o
    WHERE o.ticker = '{ticker}'
        AND o.trade_date >= TIMESTAMP '{ts_start} 00:00:00'
        AND o.trade_date <= TIMESTAMP '{ts_end} 00:00:00'
        ),
    ranked AS (
    SELECT
      *,
      ROW_NUMBER() OVER (
        PARTITION BY entry_date, cp, strike
        ORDER BY expiry_diff, expiry  -- tie-breaker on earlier expiry if equally close
      ) AS rn
    FROM cand
        )
    SELECT entry_date, expiry, ticker, cp, strike, delta, entry_price_mid
    FROM ranked
    WHERE rn = 1
    ORDER BY entry_date, cp, strike;
        """


def query_ticker(
    ts_start: str,
    ts_end: str,
    ticker: str, 
    dte:int
    ):
    athena("DROP TABLE IF EXISTS temp2")
    sql1 = step1Sql(ticker, ts_start, ts_end, dte)
    print(sql1)
    athena(step1Sql(ticker, ts_start, ts_end, dte))
    df = athena(step2Sql(ticker, ts_start, ts_end))
    athena("DROP TABLE IF EXISTS temp2")
    return df
    


def query_entries_range_for_leg(
    ts_start: str,
    ts_end: str,
    ticker: str,
    leg: Leg,
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
    print(sql)

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
    print(df)
    return df

def fetch_expiry_quotes(df_entry: pd.DataFrame) -> pd.DataFrame:
    if df_entry.empty:
        return df_entry.copy()

    base_cols = ["entry_date", "expiry", "ticker", "cp", "strike", "entry_last"]
    keep_cols = base_cols + (["row_id"] if "row_id" in df_entry.columns else [])

    tgt = (
        df_entry[keep_cols]
        .dropna(subset=base_cols)
        .drop_duplicates()
        .copy()
    )
    # normalize
    tgt["entry_date"] = pd.to_datetime(tgt["entry_date"]).dt.date
    tgt["expiry"]     = pd.to_datetime(tgt["expiry"]).dt.date
    tgt["ticker"]     = tgt["ticker"].astype(str)
    tgt["cp"]         = tgt["cp"].astype(str)
    tgt["strike"]     = pd.to_numeric(tgt["strike"], errors="raise")
    tgt["entry_last"] = pd.to_numeric(tgt["entry_last"], errors="raise")

    # make sure Glue DB exists (the temp table is registered there)
    _ensure_glue_db(DB)

    tmp_table, tmp_path = _create_temp_targets_table(tgt, DB)
    try:
        select_rowid = ", t.row_id" if "row_id" in tgt.columns else ""

        # IMPORTANT: fully-qualify with catalog.database.table on BOTH sides:
        # - Main options table lives in your S3 Tables catalog (S3TABLES_CATALOG)
        # - Temp targets table lives in Glue Data Catalog (GLUE_CATALOG)
        sql = f"""
        SELECT
          t.entry_date,
          o.expiry,
          o.ticker,
          o.cp,
          o.strike,
          t.entry_last,
          o.last AS quote_last,
          100.0 * (o.last - t.entry_last) AS profit
          {select_rowid}
        FROM "{S3TABLES_CATALOG}"."{DB}"."{TABLE}" o
        JOIN "{GLUE_CATALOG}"."{DB}"."{tmp_table}" t
          ON  o.expiry = t.expiry
          AND o.ticker = t.ticker
          AND o.cp     = t.cp
          AND o.strike = t.strike
        WHERE o.trade_date = t.expiry
        ORDER BY o.ticker, o.cp, o.strike, o.expiry
        """
        df = athena(sql)  # keep data_source=S3TABLES_CATALOG in athena()
    finally:
        _drop_temp_targets_table(DB, tmp_table, tmp_path)

    if df.empty:
        return df

    df["entry_date"] = pd.to_datetime(df["entry_date"]).dt.date
    df["expiry"]     = pd.to_datetime(df["expiry"]).dt.date
    return df

