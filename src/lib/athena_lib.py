from lib.constants import DB, WORKGROUP, CATALOG, S3_OUTPUT
import pandas as pd
import awswrangler as wr
from lib.constants import GLUE_CATALOG, S3TABLES_CATALOG, TABLE, TMP_S3_PREFIX
import uuid
from lib.data import Leg
from typing import Optional

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


def fetch_strangle_trades(
    tickers: list,
    ts_start: str,
    ts_end: str,
    call_delta: float,
    put_delta: float,
    dte: int,
    entry_weekdays: Optional[set] = None,
) -> pd.DataFrame:
    """
    Single Athena query for one or more tickers, returning both mid and worst-case entry prices.

    Both pricings are computed in one round-trip so callers don't need a second query.
    entry_weekdays: optional set of Python weekday ints (Mon=0, Fri=4, Sun=6).
    Returns one row per (ticker, entry_date, expiry) with columns:
      call_entry_last_mid, call_entry_last_worst, put_entry_last_mid, put_entry_last_worst.
    """
    if isinstance(tickers, str):
        tickers = [tickers]
    tickers_sql = ", ".join(f"'{t}'" for t in tickers)

    if entry_weekdays:
        # Presto day_of_week: Mon=1 .. Fri=5 .. Sun=7  (Python is Mon=0..Sun=6)
        presto_days = ", ".join(str(w + 1) for w in sorted(entry_weekdays))
        weekday_clause = f"AND day_of_week(o.trade_date) IN ({presto_days})"
    else:
        weekday_clause = ""

    sql = f"""
    WITH
    call_cand AS (
      SELECT
        o.trade_date AS entry_date,
        o.expiry,
        o.ticker,
        o.strike,
        o.delta,
        (o.bid + o.ask) / 2 AS entry_last_mid,
        o.bid               AS entry_last_worst,
        ABS(date_diff('day', o.expiry, date_add('day', {dte}, o.trade_date))) AS expiry_diff
      FROM "{DB}"."{TABLE}" o
      WHERE o.ticker IN ({tickers_sql})
        AND o.cp = 'C'
        AND o.trade_date >= TIMESTAMP '{ts_start} 00:00:00'
        AND o.trade_date <= TIMESTAMP '{ts_end} 00:00:00'
        AND o.bid > 0
        AND o.ask > 0
        AND o.open_interest > 0
        AND (o.ask - o.bid) / ((o.ask + o.bid) / 2) <= 0.35
        {weekday_clause}
    ),
    call_ranked AS (
      SELECT *,
        ROW_NUMBER() OVER (
          PARTITION BY ticker, entry_date
          ORDER BY expiry_diff, ABS(delta - {call_delta}), strike
        ) AS rn
      FROM call_cand
    ),
    call_leg AS (
      SELECT entry_date, expiry, ticker,
             strike AS call_strike, delta AS call_delta,
             entry_last_mid   AS call_entry_last_mid,
             entry_last_worst AS call_entry_last_worst
      FROM call_ranked WHERE rn = 1
    ),
    put_cand AS (
      SELECT
        o.trade_date AS entry_date,
        o.expiry,
        o.ticker,
        o.strike,
        o.delta,
        (o.bid + o.ask) / 2 AS entry_last_mid,
        o.bid               AS entry_last_worst,
        ABS(date_diff('day', o.expiry, date_add('day', {dte}, o.trade_date))) AS expiry_diff
      FROM "{DB}"."{TABLE}" o
      WHERE o.ticker IN ({tickers_sql})
        AND o.cp = 'P'
        AND o.trade_date >= TIMESTAMP '{ts_start} 00:00:00'
        AND o.trade_date <= TIMESTAMP '{ts_end} 00:00:00'
        AND o.bid > 0
        AND o.ask > 0
        AND o.open_interest > 0
        AND (o.ask - o.bid) / ((o.ask + o.bid) / 2) <= 0.35
        {weekday_clause}
    ),
    put_ranked AS (
      SELECT *,
        ROW_NUMBER() OVER (
          PARTITION BY ticker, entry_date
          ORDER BY expiry_diff, ABS(delta - {-put_delta}), strike DESC
        ) AS rn
      FROM put_cand
    ),
    put_leg AS (
      SELECT entry_date, expiry, ticker,
             strike AS put_strike, delta AS put_delta,
             entry_last_mid   AS put_entry_last_mid,
             entry_last_worst AS put_entry_last_worst
      FROM put_ranked WHERE rn = 1
    ),
    matched AS (
      SELECT
        c.entry_date,
        c.expiry,
        c.ticker,
        c.call_strike,
        c.call_delta,
        c.call_entry_last_mid,
        c.call_entry_last_worst,
        p.put_strike,
        p.put_delta,
        p.put_entry_last_mid,
        p.put_entry_last_worst
      FROM call_leg c
      JOIN put_leg p ON c.entry_date = p.entry_date AND c.expiry = p.expiry AND c.ticker = p.ticker
    ),
    call_expiry AS (
      SELECT o.expiry, o.ticker, o.strike, MAX(o.last) AS call_exit_last
      FROM "{DB}"."{TABLE}" o
      JOIN matched m
        ON o.expiry = m.expiry
        AND o.ticker = m.ticker
        AND o.strike = m.call_strike
        AND o.trade_date = m.expiry
      WHERE o.cp = 'C'
      GROUP BY o.expiry, o.ticker, o.strike
    ),
    put_expiry AS (
      SELECT o.expiry, o.ticker, o.strike, MAX(o.last) AS put_exit_last
      FROM "{DB}"."{TABLE}" o
      JOIN matched m
        ON o.expiry = m.expiry
        AND o.ticker = m.ticker
        AND o.strike = m.put_strike
        AND o.trade_date = m.expiry
      WHERE o.cp = 'P'
      GROUP BY o.expiry, o.ticker, o.strike
    )
    SELECT
      m.entry_date,
      m.expiry,
      m.ticker,
      m.call_strike,
      m.call_delta,
      m.call_entry_last_mid,
      m.call_entry_last_worst,
      ce.call_exit_last,
      m.put_strike,
      m.put_delta,
      m.put_entry_last_mid,
      m.put_entry_last_worst,
      pe.put_exit_last
    FROM matched m
    JOIN call_expiry ce ON m.expiry = ce.expiry AND m.ticker = ce.ticker AND m.call_strike = ce.strike
    JOIN put_expiry pe  ON m.expiry = pe.expiry AND m.ticker = pe.ticker AND m.put_strike  = pe.strike
    ORDER BY m.ticker, m.entry_date
    """

    df = athena(sql)
    for col in ("entry_date", "expiry"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col]).dt.date
    return df

