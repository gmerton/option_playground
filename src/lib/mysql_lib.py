import math
import os
from datetime import date, datetime
import mysql.connector
import pandas as pd
from sqlalchemy import create_engine


def _safe_float(v):
    """Return float(v) or None if v is NaN or infinite."""
    try:
        f = float(v)
        return f if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def _get_conn():
    return mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password=os.environ["MYSQL_PASSWORD"],
        database="stocks",
    )


def _get_engine():
    """Return a SQLAlchemy engine — use this with pd.read_sql() to avoid warnings."""
    pw = os.environ["MYSQL_PASSWORD"]
    return create_engine(f"mysql+mysqlconnector://root:{pw}@127.0.0.1:3306/stocks")


def create_study(description: str) -> int:
    """Insert a row into studies and return the new study_id."""
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO studies (description, ran_at) VALUES (%s, NOW())",
            (description,),
        )
        conn.commit()
        study_id = cursor.lastrowid
        cursor.close()
    finally:
        conn.close()
    return study_id


def upsert_study_detail(detail_df: pd.DataFrame, study_id: int) -> int:
    """
    Insert rows from detail_df into study_detail.
    Returns the number of rows inserted.
    """
    if detail_df.empty:
        return 0

    sql = """
        INSERT INTO study_detail
            (study_id, ticker, entry_date, expiry, pricing,
             portfolio_pnl, net_entry_premium, return_on_credit, capital, roc)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            portfolio_pnl     = VALUES(portfolio_pnl),
            net_entry_premium = VALUES(net_entry_premium),
            return_on_credit  = VALUES(return_on_credit),
            capital           = VALUES(capital),
            roc               = VALUES(roc),
            updated_at        = CURRENT_TIMESTAMP
    """

    rows = [
        (
            study_id,
            str(r.ticker),
            r.entry_date,
            r.expiry,
            str(r.pricing),
            _safe_float(r.portfolio_pnl),
            _safe_float(r.net_entry_premium),
            _safe_float(r.return_on_credit),
            _safe_float(r.capital),
            _safe_float(r.roc),
        )
        for r in detail_df.itertuples(index=False)
    ]

    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.executemany(sql, rows)
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
    finally:
        conn.close()

    return affected


def upsert_strangle_study_det(detail_df: pd.DataFrame, study_id: int) -> int:
    """
    Populate strangle_study_det with call_delta and put_delta for each row
    in study_detail that was just inserted for this study_id.

    detail_df must contain columns: ticker, entry_date, expiry, pricing,
    call_delta, put_delta.

    Strategy: fetch the auto-increment IDs back from study_detail by natural
    key (study_id, ticker, entry_date, expiry, pricing), merge with detail_df,
    then bulk-insert into strangle_study_det.
    """
    if detail_df.empty:
        return 0

    needed = {"ticker", "entry_date", "expiry", "pricing", "call_delta", "put_delta"}
    missing = needed - set(detail_df.columns)
    if missing:
        raise ValueError(f"upsert_strangle_study_det: detail_df missing columns: {missing}")

    conn = _get_conn()
    try:
        cursor = conn.cursor()

        # Fetch the ids just inserted for this study
        cursor.execute(
            """
            SELECT id, ticker, entry_date, expiry, pricing
            FROM study_detail
            WHERE study_id = %s
            """,
            (study_id,),
        )
        id_rows = cursor.fetchall()
        id_df = pd.DataFrame(id_rows, columns=["id", "ticker", "entry_date", "expiry", "pricing"])
        id_df["entry_date"] = pd.to_datetime(id_df["entry_date"]).dt.date
        id_df["expiry"]     = pd.to_datetime(id_df["expiry"]).dt.date

        delta_df = detail_df[["ticker", "entry_date", "expiry", "pricing",
                               "call_delta", "put_delta"]].copy()
        delta_df["entry_date"] = pd.to_datetime(delta_df["entry_date"]).dt.date
        delta_df["expiry"]     = pd.to_datetime(delta_df["expiry"]).dt.date

        merged = id_df.merge(delta_df, on=["ticker", "entry_date", "expiry", "pricing"], how="inner")

        if merged.empty:
            return 0

        det_rows = [
            (int(r.id), _safe_float(r.call_delta), _safe_float(r.put_delta))
            for r in merged.itertuples(index=False)
        ]

        cursor.executemany(
            """INSERT INTO strangle_study_det (study_detail_id, call_delta, put_delta)
               VALUES (%s, %s, %s)
               ON DUPLICATE KEY UPDATE
                   call_delta = VALUES(call_delta),
                   put_delta  = VALUES(put_delta)""",
            det_rows,
        )
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
    finally:
        conn.close()

    return affected


def upsert_study_summary(summaries_mid: list, summaries_worst: list, study_id: int) -> int:
    """
    Upsert per-ticker summary rows into study_summary.
    Returns the number of rows affected.
    """
    rows = []
    for s in summaries_mid:
        rows.append((study_id, s["ticker"], "mid",   s["n_entries"], s["roc"], s["return_on_credit"], s["win_rate"],
                     s.get("avg_roc"), s.get("stddev_roc")))
    for s in summaries_worst:
        rows.append((study_id, s["ticker"], "worst", s["n_entries"], s["roc"], s["return_on_credit"], s["win_rate"],
                     s.get("avg_roc"), s.get("stddev_roc")))

    if not rows:
        return 0

    sql = """
        INSERT INTO study_summary
            (study_id, ticker, pricing, n_entries, roc, return_on_credit, win_rate,
             avg_roc, stddev_roc)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            n_entries        = VALUES(n_entries),
            roc              = VALUES(roc),
            return_on_credit = VALUES(return_on_credit),
            win_rate         = VALUES(win_rate),
            avg_roc          = VALUES(avg_roc),
            stddev_roc       = VALUES(stddev_roc),
            updated_at       = CURRENT_TIMESTAMP
    """

    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.executemany(sql, rows)
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
    finally:
        conn.close()

    return affected


def get_study_tickers(study_id: int = None) -> list:
    """
    Return all tickers in study_summary (distinct, sorted).
    If study_id is given, filter to that study only.
    """
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        if study_id is not None:
            cursor.execute(
                "SELECT DISTINCT ticker FROM study_summary WHERE study_id = %s ORDER BY ticker",
                (study_id,),
            )
        else:
            cursor.execute("SELECT DISTINCT ticker FROM study_summary ORDER BY ticker")
        tickers = [row[0] for row in cursor.fetchall()]
        cursor.close()
    finally:
        conn.close()
    return tickers


def recompute_summary_from_detail(study_id: int) -> int:
    """
    Recompute per-ticker summary metrics from study_detail for a given study_id
    and upsert into study_summary.  Returns rows affected.
    """
    sql_select = """
        SELECT
            study_id,
            ticker,
            pricing,
            COUNT(*)                                                 AS n_entries,
            SUM(portfolio_pnl) / NULLIF(SUM(capital), 0)            AS roc,
            SUM(portfolio_pnl) / NULLIF(-SUM(net_entry_premium), 0) AS return_on_credit,
            SUM(portfolio_pnl > 0) / COUNT(*)                       AS win_rate,
            AVG(roc)                                                 AS avg_roc,
            STDDEV(roc)                                              AS stddev_roc
        FROM study_detail
        WHERE study_id = %s
        GROUP BY study_id, ticker, pricing
    """

    sql_upsert = """
        INSERT INTO study_summary
            (study_id, ticker, pricing, n_entries, roc, return_on_credit, win_rate,
             avg_roc, stddev_roc)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            n_entries        = VALUES(n_entries),
            roc              = VALUES(roc),
            return_on_credit = VALUES(return_on_credit),
            win_rate         = VALUES(win_rate),
            avg_roc          = VALUES(avg_roc),
            stddev_roc       = VALUES(stddev_roc),
            updated_at       = CURRENT_TIMESTAMP
    """

    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(sql_select, (study_id,))
        rows = cursor.fetchall()
        cursor.executemany(sql_upsert, rows)
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
    finally:
        conn.close()
    return affected


# ── options_cache helpers ─────────────────────────────────────────────────────

def create_options_cache_table() -> None:
    """Create options_cache table if it does not already exist."""
    sql = """
        CREATE TABLE IF NOT EXISTS options_cache (
            ticker        VARCHAR(20)   NOT NULL,
            trade_date    DATE          NOT NULL,
            expiry        DATE          NOT NULL,
            cp            CHAR(1)       NOT NULL,
            strike        DECIMAL(10,3) NOT NULL,
            bid           DECIMAL(10,4),
            ask           DECIMAL(10,4),
            last          DECIMAL(10,4),
            mid           DECIMAL(10,4),
            delta         DECIMAL(8,4),
            open_interest INT,
            volume        INT,
            PRIMARY KEY (ticker, trade_date, expiry, cp, strike)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        conn.commit()
        cursor.close()
    finally:
        conn.close()


def get_options_cache_max_date(ticker: str) -> "date | None":
    """Return the latest trade_date in options_cache for *ticker*, or None."""
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT MAX(trade_date) FROM options_cache WHERE ticker = %s",
            (ticker,),
        )
        row = cursor.fetchone()
        cursor.close()
    finally:
        conn.close()
    return row[0] if row and row[0] else None


def upsert_options_cache(ticker: str, df: pd.DataFrame, chunk_size: int = 5000) -> int:
    """
    Bulk-upsert option rows into options_cache.

    df must have columns: trade_date, expiry, cp, strike, bid, ask, last,
                          mid, delta, open_interest, volume.
    Returns total rows affected.
    """
    if df.empty:
        return 0

    sql = """
        INSERT INTO options_cache
            (ticker, trade_date, expiry, cp, strike,
             bid, ask, last, mid, delta, open_interest, volume)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            bid           = VALUES(bid),
            ask           = VALUES(ask),
            last          = VALUES(last),
            mid           = VALUES(mid),
            delta         = VALUES(delta),
            open_interest = VALUES(open_interest),
            volume        = VALUES(volume)
    """

    def _to_date(v):
        if isinstance(v, date):
            return v
        return pd.Timestamp(v).date()

    def _int_or_none(v):
        try:
            f = float(v)
            return int(f) if math.isfinite(f) else None
        except (TypeError, ValueError):
            return None

    rows = [
        (
            ticker,
            _to_date(r.trade_date),
            _to_date(r.expiry),
            str(r.cp),
            _safe_float(r.strike),
            _safe_float(r.bid),
            _safe_float(r.ask),
            _safe_float(r.last),
            _safe_float(r.mid),
            _safe_float(r.delta),
            _int_or_none(r.open_interest),
            _int_or_none(r.volume),
        )
        for r in df.itertuples(index=False)
    ]

    total = 0
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        for i in range(0, len(rows), chunk_size):
            cursor.executemany(sql, rows[i : i + chunk_size])
            total += cursor.rowcount
        conn.commit()
        cursor.close()
    finally:
        conn.close()
    return total


def fetch_options_cache(ticker: str, start: "date", end: "date") -> pd.DataFrame:
    """
    Fetch all option rows for *ticker* with trade_date in [start, end].

    Returns a DataFrame with columns:
      trade_date, expiry, cp, strike, bid, ask, last, mid, delta,
      open_interest, volume, dte
    All date columns are Python date objects.
    """
    from datetime import timedelta

    cols = [
        "trade_date", "expiry", "cp", "strike",
        "bid", "ask", "last", "mid",
        "delta", "open_interest", "volume",
    ]
    # Fetch in yearly chunks to avoid dropping large connections
    rows: list = []
    chunk_start = start
    while chunk_start <= end:
        chunk_end = min(
            date(chunk_start.year, 12, 31),
            end,
        )
        conn = _get_conn()
        try:
            cursor = conn.cursor()
            cursor.execute("SET SESSION net_read_timeout=600")
            cursor.execute("SET SESSION net_write_timeout=600")
            cursor.execute(
                """
                SELECT trade_date, expiry, cp, strike, bid, ask, last, mid,
                       delta, open_interest, volume
                FROM options_cache
                WHERE ticker = %s
                  AND trade_date BETWEEN %s AND %s
                ORDER BY trade_date, expiry, cp, strike
                """,
                (ticker, chunk_start, chunk_end),
            )
            while True:
                chunk = cursor.fetchmany(50_000)
                if not chunk:
                    break
                rows.extend(chunk)
            cursor.close()
        finally:
            conn.close()
        chunk_start = date(chunk_start.year + 1, 1, 1)

    if not rows:
        return pd.DataFrame(columns=cols + ["dte"])

    df = pd.DataFrame(rows, columns=cols)
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    df["expiry"]     = pd.to_datetime(df["expiry"]).dt.date
    for c in ("strike", "bid", "ask", "last", "mid", "delta"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["open_interest"] = pd.to_numeric(df["open_interest"], errors="coerce")
    df["volume"]        = pd.to_numeric(df["volume"],        errors="coerce")
    df["dte"] = (
        pd.to_datetime(df["expiry"]) - pd.to_datetime(df["trade_date"])
    ).dt.days
    return df


def _parse_ibkr_date(v) -> date | None:
    """Convert IBKR YYYYMMDD string to a date, or None if blank/NaN."""
    try:
        s = str(int(float(v)))   # handles '20260202', 20260202.0, etc.
        return datetime.strptime(s, "%Y%m%d").date()
    except (TypeError, ValueError):
        return None


def upsert_trades(df: pd.DataFrame) -> int:
    """
    Upsert rows from a TradeConfirm DataFrame into the trades table.
    Idempotent — re-running with the same data is safe (ON DUPLICATE KEY).
    Returns number of rows affected.
    """
    if df.empty:
        return 0

    sql = """
        INSERT INTO trades
            (id, order_id, exec_id, trade_date, asset_category, symbol,
             underlying, expiry, strike, put_call, transaction_type,
             buy_sell, quantity, price, amount, proceeds, net_cash, commission)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            order_id         = VALUES(order_id),
            trade_date       = VALUES(trade_date),
            asset_category   = VALUES(asset_category),
            symbol           = VALUES(symbol),
            underlying       = VALUES(underlying),
            expiry           = VALUES(expiry),
            strike           = VALUES(strike),
            put_call         = VALUES(put_call),
            transaction_type = VALUES(transaction_type),
            buy_sell         = VALUES(buy_sell),
            quantity         = VALUES(quantity),
            price            = VALUES(price),
            amount           = VALUES(amount),
            proceeds         = VALUES(proceeds),
            net_cash         = VALUES(net_cash),
            commission       = VALUES(commission)
    """

    rows = [
        (
            int(r.tradeID),
            int(r.orderID),
            str(r.execID),
            _parse_ibkr_date(r.tradeDate),
            str(r.assetCategory),
            str(r.symbol),
            str(r.underlyingSymbol),
            _parse_ibkr_date(r.expiry),
            _safe_float(r.strike),
            str(r.putCall) if str(r.putCall) not in ("", "nan") else None,
            str(r.transactionType),
            str(r.buySell),
            int(float(r.quantity)),
            _safe_float(r.price),
            _safe_float(r.amount),
            _safe_float(r.proceeds),
            _safe_float(r.netCash),
            _safe_float(r.commission),
        )
        for r in df.itertuples(index=False)
    ]

    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.executemany(sql, rows)
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
    finally:
        conn.close()

    return affected


# ── Daily trade journal (run_daily_journal.py) ─────────────────────────────────
#
# Separate from `trades` above: that table is fed by the trade-confirms Flex
# query (id 1415008) and its upsert_trades() expects that query's schema
# (orderID, execID, amount, commission, price, ...). The NAV/Activity query
# (id 1605053) used by the journal has a different Trade section shape — no
# orderID/execID/amount/commission, tradePrice instead of price — plus an
# OpenPosition section the trade-confirms query doesn't have at all. These
# journal_* tables mirror that query's own schema rather than force-fitting it
# into `trades`. Expect to adjust these as the journaling routine matures.

def create_journal_tables() -> None:
    """Create journal_nav, journal_trades, journal_open_positions if missing."""
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS journal_nav (
                report_date  DATE PRIMARY KEY,
                nav          DECIMAL(14,2),
                day_pnl      DECIMAL(14,2),
                created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS journal_trades (
                trade_id          BIGINT UNSIGNED PRIMARY KEY,  -- IBKR tradeID
                conid             BIGINT UNSIGNED NOT NULL,
                trade_date        DATE NOT NULL,
                symbol            VARCHAR(48)  NOT NULL,
                underlying_symbol VARCHAR(32)  NOT NULL,
                asset_category    VARCHAR(10)  NOT NULL,
                put_call          CHAR(1),
                strike            DECIMAL(12,4),
                expiry            DATE,
                buy_sell          VARCHAR(4)   NOT NULL,
                open_close        VARCHAR(4),                    -- 'O' / 'C' / 'C;O' (reversal fill)
                quantity          DECIMAL(14,4) NOT NULL,
                trade_price       DECIMAL(14,4),
                trade_datetime    DATETIME,                      -- fill time, IBKR-reported (assumed ET)
                realized_pnl      DECIMAL(14,4),                 -- fifoPnlRealized
                transaction_type  VARCHAR(20),
                created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_trade_date (trade_date),
                INDEX idx_underlying (underlying_symbol)
            )
        """)
        # Migration: widen open_close for tables created before 'C;O' reversal
        # fills were discovered (a single fill that both closes and reopens).
        cur.execute("""
            ALTER TABLE journal_trades MODIFY COLUMN open_close VARCHAR(4)
        """)
        # Migration: add trade_datetime for tables created before intraday
        # chart markers needed the exact fill time (not just the date).
        # (MySQL -- unlike MariaDB -- has no ADD COLUMN IF NOT EXISTS, hence the check.)
        cur.execute("""
            SELECT COUNT(*) FROM information_schema.columns
            WHERE table_schema = DATABASE() AND table_name = 'journal_trades'
              AND column_name = 'trade_datetime'
        """)
        if cur.fetchone()[0] == 0:
            cur.execute("ALTER TABLE journal_trades ADD COLUMN trade_datetime DATETIME")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS journal_open_positions (
                report_date       DATE NOT NULL,
                conid             BIGINT UNSIGNED NOT NULL,
                symbol            VARCHAR(48)  NOT NULL,
                underlying_symbol VARCHAR(32)  NOT NULL,
                asset_category    VARCHAR(10)  NOT NULL,
                put_call          CHAR(1),
                strike            DECIMAL(12,4),
                expiry            DATE,
                side              VARCHAR(5),
                position          DECIMAL(14,4) NOT NULL,
                open_price        DECIMAL(14,4),
                mark_price        DECIMAL(14,4),
                position_value    DECIMAL(14,4),
                unrealized_pnl    DECIMAL(14,4),
                created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (report_date, conid),
                INDEX idx_underlying (underlying_symbol)
            )
        """)
        conn.commit()
        cur.close()
    finally:
        conn.close()


def upsert_journal_nav(report_date: date, nav: float | None, day_pnl: float | None) -> None:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO journal_nav (report_date, nav, day_pnl)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE nav = VALUES(nav), day_pnl = VALUES(day_pnl)
        """, (report_date, _safe_float(nav), _safe_float(day_pnl)))
        conn.commit()
        cur.close()
    finally:
        conn.close()


def _parse_ibkr_datetime(v) -> datetime | None:
    """Convert IBKR 'YYYYMMDD;HHMMSS' fill timestamp to a datetime, or None."""
    try:
        s = str(v)
        return datetime.strptime(s, "%Y%m%d;%H%M%S")
    except (TypeError, ValueError):
        return None


def upsert_journal_trades(df: pd.DataFrame) -> int:
    """Upsert rows from the NAV/Activity query's Trade section. Idempotent on tradeID."""
    if df.empty:
        return 0
    sql = """
        INSERT INTO journal_trades
            (trade_id, conid, trade_date, symbol, underlying_symbol, asset_category,
             put_call, strike, expiry, buy_sell, open_close, quantity, trade_price,
             trade_datetime, realized_pnl, transaction_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            conid             = VALUES(conid),
            trade_date        = VALUES(trade_date),
            symbol            = VALUES(symbol),
            underlying_symbol = VALUES(underlying_symbol),
            asset_category    = VALUES(asset_category),
            put_call          = VALUES(put_call),
            strike            = VALUES(strike),
            expiry            = VALUES(expiry),
            buy_sell          = VALUES(buy_sell),
            open_close        = VALUES(open_close),
            quantity          = VALUES(quantity),
            trade_price       = VALUES(trade_price),
            trade_datetime    = VALUES(trade_datetime),
            realized_pnl      = VALUES(realized_pnl),
            transaction_type  = VALUES(transaction_type)
    """
    rows = [
        (
            int(r.tradeID),
            int(r.conid),
            _parse_ibkr_date(r.tradeDate),
            str(r.symbol),
            str(r.underlyingSymbol),
            str(r.assetCategory),
            str(r.putCall) if str(getattr(r, "putCall", "")) not in ("", "nan") else None,
            _safe_float(getattr(r, "strike", None)),
            _parse_ibkr_date(getattr(r, "expiry", None)),
            str(r.buySell),
            str(r.openCloseIndicator) if str(getattr(r, "openCloseIndicator", "")) not in ("", "nan") else None,
            _safe_float(r.quantity),
            _safe_float(r.tradePrice),
            _parse_ibkr_datetime(getattr(r, "dateTime", None)),
            _safe_float(getattr(r, "fifoPnlRealized", None)),
            str(getattr(r, "transactionType", "")) or None,
        )
        for r in df.itertuples(index=False)
    ]
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.executemany(sql, rows)
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
    finally:
        conn.close()
    return affected


def upsert_journal_open_positions(df: pd.DataFrame) -> int:
    """Upsert rows from the NAV/Activity query's OpenPosition section.
    Idempotent on (report_date, conid) — re-running the same day's pull is safe."""
    if df.empty:
        return 0
    sql = """
        INSERT INTO journal_open_positions
            (report_date, conid, symbol, underlying_symbol, asset_category,
             put_call, strike, expiry, side, position, open_price, mark_price,
             position_value, unrealized_pnl)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            symbol            = VALUES(symbol),
            underlying_symbol = VALUES(underlying_symbol),
            asset_category    = VALUES(asset_category),
            put_call          = VALUES(put_call),
            strike            = VALUES(strike),
            expiry            = VALUES(expiry),
            side              = VALUES(side),
            position          = VALUES(position),
            open_price        = VALUES(open_price),
            mark_price        = VALUES(mark_price),
            position_value    = VALUES(position_value),
            unrealized_pnl    = VALUES(unrealized_pnl)
    """
    rows = [
        (
            _parse_ibkr_date(r.reportDate),
            int(r.conid),
            str(r.symbol),
            str(r.underlyingSymbol),
            str(r.assetCategory),
            str(r.putCall) if str(getattr(r, "putCall", "")) not in ("", "nan") else None,
            _safe_float(getattr(r, "strike", None)),
            _parse_ibkr_date(getattr(r, "expiry", None)),
            str(getattr(r, "side", "")) or None,
            _safe_float(r.position),
            _safe_float(getattr(r, "openPrice", None)),
            _safe_float(getattr(r, "markPrice", None)),
            _safe_float(getattr(r, "positionValue", None)),
            _safe_float(getattr(r, "fifoPnlUnrealized", None)),
        )
        for r in df.itertuples(index=False)
    ]
    conn = _get_conn()
    try:
        cursor = conn.cursor()
        cursor.executemany(sql, rows)
        conn.commit()
        affected = cursor.rowcount
        cursor.close()
    finally:
        conn.close()
    return affected


# ── Trade cycle reconstruction + qualitative review ────────────────────────────
#
# journal_trades is fill-level; a real "trade" is a flat-to-flat position cycle
# that can span several fills across several days (or several separate cycles
# for a repeatedly-traded name -- naively grouping by conid over the whole
# window conflates these, see [[project_daily_trade_journal]]). This section
# reconstructs cycles properly and stores our qualitative read on each one.

def reconstruct_trade_cycles() -> pd.DataFrame:
    """Segment journal_trades into flat-to-flat position cycles per conid.

    A cycle starts when the running signed position (BUY positive / SELL
    negative, ordered by trade_date then trade_id as a same-day sequence proxy)
    leaves zero, and ends when it returns to exactly zero. A cycle still open
    at the end of the loaded data has exit_date = None and still_open = True.

    Returns one row per cycle: conid, symbol, underlying_symbol, asset_category,
    put_call, strike, expiry, entry_date, exit_date, first_side ('LONG'/'SHORT'),
    n_fills, max_abs_qty, realized_pnl, still_open, and the quantity-weighted
    entry_price / exit_price (opening-side and closing-side fills of the cycle;
    exit_price is None while the cycle is still open).
    """
    conn = _get_conn()
    try:
        df = pd.read_sql("""
            SELECT conid, symbol, underlying_symbol, asset_category, put_call, strike, expiry,
                   trade_date, trade_id, quantity, trade_price, realized_pnl
            FROM journal_trades
            ORDER BY conid, trade_date, trade_id
        """, conn)
    finally:
        conn.close()

    df["trade_date"] = pd.to_datetime(df["trade_date"])
    # Seed each conid with the position held at the FIRST open-positions snapshot, so a position that predates
    # the trade history (the Flex window opens 2026-08-03) does not shift every later cycle off zero. Without it
    # CRWD's 9/17 75-share round trip was invisible: 30 shares sold on 8/5 had been bought before the window,
    # so the running quantity sat at -30 and never crossed zero (caught 2026-09-18).
    seed = {}
    try:
        conn = _get_conn()
        first = pd.read_sql("SELECT MIN(report_date) d FROM journal_open_positions", conn)["d"][0]
        if first is not None:
            snap = pd.read_sql("SELECT conid, position FROM journal_open_positions WHERE report_date=%s", conn, params=[first])
            seed = dict(zip(snap["conid"].astype(int), snap["position"].astype(float)))
            df = df[df["trade_date"] > pd.Timestamp(first)]          # fills on/before the snapshot are inside it
    except Exception:
        seed = {}
    finally:
        try: conn.close()
        except Exception: pass
    cycles = []
    for conid, g in df.groupby("conid"):
        g = g.reset_index(drop=True)
        running = float(seed.get(int(conid), 0.0))
        rows_in_cycle = []
        if abs(running) > 1e-6:                     # an inherited position: the open cycle it belongs to is unobservable
            open_seed = True
        else:
            open_seed = False
        for _, r in g.iterrows():
            rows_in_cycle.append(r)
            running += r["quantity"]
            if abs(running) < 1e-6:
                cyc = pd.DataFrame(rows_in_cycle)
                if open_seed:                      # fills that closed the inherited position: not a cycle we can grade
                    open_seed = False
                else:
                    cycles.append(_cycle_row(g, cyc, still_open=False))
                rows_in_cycle = []
        if rows_in_cycle and not open_seed:
            cyc = pd.DataFrame(rows_in_cycle)
            cycles.append(_cycle_row(g, cyc, still_open=True))

    return pd.DataFrame(cycles)


def _vwap(rows: pd.DataFrame) -> float | None:
    """Quantity-weighted average fill price (weights are absolute quantities)."""
    if rows.empty:
        return None
    w = rows["quantity"].abs()
    px = pd.to_numeric(rows["trade_price"], errors="coerce")
    ok = w.notna() & px.notna() & (w > 0)
    if not ok.any() or w[ok].sum() == 0:
        return None
    return float((px[ok] * w[ok]).sum() / w[ok].sum())


def _cycle_row(g: pd.DataFrame, cyc: pd.DataFrame, still_open: bool) -> dict:
    # The cycle's first fill sets the direction: same-sign fills are entries
    # (the initial open plus any adds), opposite-sign fills are exits.
    entry_sign = 1 if cyc.iloc[0]["quantity"] > 0 else -1
    entries = cyc[cyc["quantity"] * entry_sign > 0]
    exits = cyc[cyc["quantity"] * entry_sign < 0]
    return {
        "conid": g["conid"].iloc[0],
        "symbol": g["symbol"].iloc[0],
        "underlying_symbol": g["underlying_symbol"].iloc[0],
        "asset_category": g["asset_category"].iloc[0],
        "put_call": g["put_call"].iloc[0],
        "strike": g["strike"].iloc[0],
        "expiry": g["expiry"].iloc[0],
        "entry_date": (entries["trade_date"].min().date() if not entries.empty
                       else cyc["trade_date"].min().date()),
        "exit_date": None if still_open or exits.empty else exits["trade_date"].max().date(),
        "entry_price": _vwap(entries),
        "exit_price": _vwap(exits),
        "first_side": "LONG" if cyc.iloc[0]["quantity"] > 0 else "SHORT",
        "n_fills": len(cyc),
        "max_abs_qty": cyc["quantity"].cumsum().abs().max(),
        "realized_pnl": cyc["realized_pnl"].sum(),
        "still_open": still_open,
    }


# ── Reviews keyed to structures, not contracts ────────────────────────────────
#
# A review row is keyed to one contract (conid), but most trades here are
# multi-leg structures, so a review could store ONE LEG's realized P&L and
# present it as the trade's (GLD review 36: +$772.51 = the short legs only, true
# structure P&L +$250.05), and one structure could be reviewed several times.
#
# journal_campaigns already solves this for options -- it groups a spread and
# everything it was rolled into as one entity and computes structure-level P&L,
# rebuilt from fills on every journal run. So reviews get a foreign key to it
# rather than a recomputation of their own.
#
# structure_pnl is written ALONGSIDE realized_pnl, never over it: the original
# stays auditable, and readers prefer structure_pnl when it is present.
# Stock reviews have no campaign (campaigns are options-only) and need none --
# for a single instrument the contract IS the structure.

def add_review_campaign_columns() -> None:
    """Add campaign_id / structure_pnl to journal_trade_reviews if missing."""
    conn = _get_conn()
    try:
        cur = conn.cursor()
        for col, ddl in (
            ("campaign_id", "ADD COLUMN campaign_id INT NULL"),
            ("structure_pnl", "ADD COLUMN structure_pnl DECIMAL(14,4) NULL"),
            ("is_primary", "ADD COLUMN is_primary TINYINT(1) NOT NULL DEFAULT 1"),
        ):
            cur.execute("""SELECT COUNT(*) FROM information_schema.columns
                           WHERE table_schema = DATABASE() AND table_name = 'journal_trade_reviews'
                             AND column_name = %s""", (col,))
            if cur.fetchone()[0] == 0:
                cur.execute(f"ALTER TABLE journal_trade_reviews {ddl}")
        cur.execute("""SELECT COUNT(*) FROM information_schema.statistics
                       WHERE table_schema = DATABASE() AND table_name = 'journal_trade_reviews'
                         AND index_name = 'idx_campaign'""")
        if cur.fetchone()[0] == 0:
            cur.execute("ALTER TABLE journal_trade_reviews ADD INDEX idx_campaign (campaign_id)")
        conn.commit()
    finally:
        conn.close()


def sync_review_campaigns() -> dict:
    """Point every OPTION review at its journal_campaigns row and cache that
    campaign's structure-level P&L in structure_pnl.

    Matching, most specific first:
      1. the review's conid appears in the campaign's linked fills, and the
         campaign's date range covers the review's entry date
      2. no conid (a labelled structure like "NBIS (iron condor: ...)"):
         same underlying and the campaign opens on the review's entry date
      3. a review about a ROLL, whose entry date is the roll rather than the
         original open: same underlying and the campaign's span covers it
    A review that matches nothing is left untouched (campaign_id stays NULL) --
    silence beats a wrong key. Idempotent; safe to re-run.
    """
    add_review_campaign_columns()
    conn = _get_conn()
    try:
        rv = pd.read_sql("""SELECT id, underlying_symbol, asset_category, conid, entry_date, exit_date, symbol
                            FROM journal_trade_reviews""", conn)
        camps = pd.read_sql("""SELECT campaign_id, underlying, first_date, last_date, status, realized_pnl, label
                               FROM journal_campaigns""", conn)
        links = pd.read_sql("""SELECT c.campaign_id, t.conid
                               FROM journal_campaign_trades c
                               JOIN journal_trades t ON t.trade_id = c.trade_id""", conn)
        if camps.empty:
            return {"matched": 0, "unmatched": 0, "skipped_stock": 0, "corrected": 0}

        camps["first_date"] = pd.to_datetime(camps["first_date"]).dt.date
        camps["last_date"] = pd.to_datetime(camps["last_date"]).dt.date
        by_conid: dict[int, set] = {}
        for r in links.itertuples():
            by_conid.setdefault(int(r.conid), set()).add(int(r.campaign_id))
        cmap = {int(r.campaign_id): r for r in camps.itertuples()}

        updates, unmatched, skipped = [], 0, 0
        for r in rv.itertuples():
            if str(r.asset_category or "") == "STK":
                skipped += 1
                continue
            entry, exit_ = r.entry_date, r.exit_date
            cands = []
            if pd.notna(r.conid):
                for cid in by_conid.get(int(r.conid), ()):
                    c = cmap[cid]
                    if c.first_date <= entry <= c.last_date:
                        cands.append(c)
            if not cands:
                for c in camps.itertuples():
                    if c.underlying == r.underlying_symbol and c.first_date == entry:
                        cands.append(c)
            if not cands:
                # 3. a review written about a ROLL: its entry date is the roll,
                #    but the campaign's first_date is the original open, so match
                #    on the campaign's span instead of its start.
                for c in camps.itertuples():
                    if c.underlying == r.underlying_symbol and c.first_date <= entry <= c.last_date:
                        cands.append(c)
            if not cands:
                unmatched += 1
                continue
            # prefer the campaign whose label appears in the review's symbol (several structures
            # can open on one underlying the same day -- 2026-09-17 MSTR had a put spread and two
            # long calls, and all three reviews were keyed to the first campaign), then the one
            # that opens on the entry date, then the one whose close is nearest the review's exit
            sym = str(r.symbol or "")
            cands.sort(key=lambda c: (not (str(c.label or "") and str(c.label) in sym),
                                      c.first_date != entry,
                                      abs((c.last_date - (exit_ or c.last_date)).days)))
            best = cands[0]
            updates.append((int(best.campaign_id), float(best.realized_pnl), int(r.id)))

        cur = conn.cursor()
        cur.executemany(
            "UPDATE journal_trade_reviews SET campaign_id=%s, structure_pnl=%s WHERE id=%s", updates)

        # Every review of a campaign now shows that campaign's full P&L, so summing
        # them would count one structure several times. Exactly one row per campaign
        # is primary (lowest id, deterministic) -- aggregates use those, while each
        # duplicate keeps its own page and its 'duplicate_review' tag.
        cur.execute("UPDATE journal_trade_reviews SET is_primary = 1")
        cur.execute("""
            UPDATE journal_trade_reviews r
            JOIN (SELECT campaign_id, MIN(id) keep FROM journal_trade_reviews
                  WHERE campaign_id IS NOT NULL GROUP BY campaign_id) k
              ON k.campaign_id = r.campaign_id
            SET r.is_primary = 0
            WHERE r.id <> k.keep
        """)
        conn.commit()

        corrected = pd.read_sql("""SELECT COUNT(*) n FROM journal_trade_reviews
                                   WHERE structure_pnl IS NOT NULL AND realized_pnl IS NOT NULL
                                     AND ABS(structure_pnl - realized_pnl) > 1.0""", conn)["n"][0]
        dups = pd.read_sql("SELECT COUNT(*) n FROM journal_trade_reviews WHERE is_primary = 0",
                           conn)["n"][0]
        return {"matched": len(updates), "unmatched": unmatched, "skipped_stock": skipped,
                "corrected": int(corrected), "non_primary": int(dups)}
    finally:
        conn.close()


def tag_duplicate_reviews(tag: str = "duplicate_review") -> int:
    """Tag every review that shares a campaign with another (source='derived').

    Non-destructive: the rows stay, they just become queryable as duplicates.
    """
    create_review_tag_table()
    conn = _get_conn()
    try:
        df = pd.read_sql("""SELECT id, campaign_id FROM journal_trade_reviews
                            WHERE campaign_id IS NOT NULL""", conn)
        dup_campaigns = df.groupby("campaign_id").size()
        dup_campaigns = set(dup_campaigns[dup_campaigns > 1].index)
        hits = [(int(r.id), tag) for r in df.itertuples() if r.campaign_id in dup_campaigns]
        cur = conn.cursor()
        cur.execute("DELETE FROM journal_review_tags WHERE source='derived' AND tag=%s", (tag,))
        if hits:
            cur.executemany(
                "INSERT INTO journal_review_tags (review_id, tag, source) VALUES (%s, %s, 'derived') "
                "ON DUPLICATE KEY UPDATE source='derived'", hits)
        conn.commit()
        return len(hits)
    finally:
        conn.close()


# ── Review tags (queryable) ────────────────────────────────────────────────────
#
# journal_trade_reviews.tags is a comma-joined string, so the only query against
# it is LIKE '%x%' -- which matches substrings of unrelated tags and can't be
# indexed. This is the same table, normalized: one row per (review, tag), so
# "every earnings trade" is a join, not a string scan. The string column stays
# as the human-readable copy; sync_review_tags() rebuilds this from it.

def create_review_tag_table() -> None:
    """Create journal_review_tags if missing."""
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS journal_review_tags (
                review_id  INT NOT NULL,
                tag        VARCHAR(64) NOT NULL,
                source     VARCHAR(16) NOT NULL DEFAULT 'manual',  -- manual | derived
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (review_id, tag),
                INDEX idx_tag (tag),
                INDEX idx_tag_source (tag, source)
            )
        """)
        conn.commit()
    finally:
        conn.close()


def sync_review_tags() -> int:
    """Mirror every review's comma-joined tags string into journal_review_tags.

    Idempotent: manual rows are replaced wholesale, derived rows (written by
    tag_reviews_with_earnings and friends) are left alone.
    """
    create_review_tag_table()
    conn = _get_conn()
    try:
        df = pd.read_sql("SELECT id, tags FROM journal_trade_reviews WHERE tags IS NOT NULL AND tags <> ''", conn)
        pairs = [(int(r.id), t.strip()[:64])
                 for r in df.itertuples() for t in str(r.tags).split(",") if t.strip()]
        cur = conn.cursor()
        cur.execute("DELETE FROM journal_review_tags WHERE source = 'manual'")
        if pairs:
            cur.executemany(
                "INSERT INTO journal_review_tags (review_id, tag, source) VALUES (%s, %s, 'manual') "
                "ON DUPLICATE KEY UPDATE tag = VALUES(tag)", pairs)
        conn.commit()
        return len(pairs)
    finally:
        conn.close()


def tag_reviews_with_earnings(tag: str = "earnings") -> int:
    """Tag every review whose hold spans a CONFIRMED earnings date (source='derived').

    Derived rather than hand-typed so the tag means the same thing on all 644
    reviews and can be recomputed when earnings_report is refreshed. An open
    review (no exit_date) is measured to today.
    """
    create_review_tag_table()
    conn = _get_conn()
    try:
        rv = pd.read_sql(
            "SELECT id, underlying_symbol, entry_date, exit_date FROM journal_trade_reviews", conn)
        er = pd.read_sql(
            "SELECT ticker, raw_date, date_status FROM earnings_report WHERE date_status = 'Confirmed'", conn)
        er["raw_date"] = pd.to_datetime(er["raw_date"], errors="coerce").dt.date
        er = er.dropna(subset=["raw_date"])
        by_ticker: dict[str, list] = {}
        for r in er.itertuples():
            by_ticker.setdefault(r.ticker, []).append(r.raw_date)

        today = date.today()
        hits = []
        for r in rv.itertuples():
            dates = by_ticker.get(r.underlying_symbol)
            if not dates or r.entry_date is None:
                continue
            end = r.exit_date or today
            if any(r.entry_date <= d <= end for d in dates):
                hits.append((int(r.id), tag))
        cur = conn.cursor()
        cur.execute("DELETE FROM journal_review_tags WHERE source = 'derived' AND tag = %s", (tag,))
        if hits:
            cur.executemany(
                "INSERT INTO journal_review_tags (review_id, tag, source) VALUES (%s, %s, 'derived') "
                "ON DUPLICATE KEY UPDATE source = 'derived'", hits)
        conn.commit()
        return len(hits)
    finally:
        conn.close()


def reviews_by_tag(*tags: str, match_all: bool = False) -> pd.DataFrame:
    """Reviews carrying any (or all) of `tags` -- an indexed join, not a LIKE scan."""
    if not tags:
        raise ValueError("pass at least one tag")
    ph = ",".join(["%s"] * len(tags))
    having = "HAVING COUNT(DISTINCT t.tag) = %s" if match_all else ""
    sql = f"""
        SELECT r.*, GROUP_CONCAT(DISTINCT t.tag ORDER BY t.tag) AS matched_tags
        FROM journal_trade_reviews r
        JOIN journal_review_tags t ON t.review_id = r.id
        WHERE t.tag IN ({ph})
        GROUP BY r.id
        {having}
        ORDER BY r.entry_date, r.id
    """
    params = list(tags) + ([len(tags)] if match_all else [])
    conn = _get_conn()
    try:
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()


def create_trade_review_table() -> None:
    """Create journal_trade_reviews if missing."""
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS journal_trade_reviews (
                id                INT AUTO_INCREMENT PRIMARY KEY,
                underlying_symbol VARCHAR(32)  NOT NULL,
                symbol            VARCHAR(48)  NOT NULL,
                conid             BIGINT UNSIGNED,
                asset_category    VARCHAR(10),
                entry_date        DATE NOT NULL,
                exit_date         DATE,                  -- NULL if still open
                entry_verdict     VARCHAR(20),            -- free text: 'good' / 'bad' / 'gray_area' / ...
                entry_reason      TEXT,
                exit_verdict      VARCHAR(20),            -- 'good' / 'too_soon' / 'too_late' / 'held_too_long' / 'n_a' / 'gray_area'
                exit_reason       TEXT,
                market_context    TEXT,                   -- sector/market backdrop notes at the time
                tags              VARCHAR(255),            -- comma-separated short tags, e.g. 'chasing_extension,sector_rollover'
                realized_pnl      DECIMAL(14,4),           -- snapshot for convenience, not authoritative
                created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_underlying_entry (underlying_symbol, entry_date),
                INDEX idx_entry_date (entry_date)
            )
        """)
        conn.commit()
        cur.close()
    finally:
        conn.close()


def create_pending_notes_table() -> None:
    """Create journal_pending_notes if missing.

    Staging area for trader notes given BEFORE the corresponding Flex data (and therefore the
    journal_trade_reviews row) exists -- e.g. "I shorted X today because Y" given same-day, before
    tonight's IBKR pull. Applied later by matching (underlying_symbol, note_date) against a new
    review's (underlying_symbol, entry_date) and merging note_text into that review's
    market_context; `applied`/`applied_review_id` track that so a note is only merged once.
    """
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS journal_pending_notes (
                id                 INT AUTO_INCREMENT PRIMARY KEY,
                underlying_symbol  VARCHAR(32) NOT NULL,
                note_date          DATE NOT NULL,          -- the trade date the note pertains to
                note_text          TEXT NOT NULL,
                applied            TINYINT(1) NOT NULL DEFAULT 0,
                applied_review_id  INT,                     -- journal_trade_reviews.id once merged
                created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_underlying_date (underlying_symbol, note_date),
                INDEX idx_applied (applied)
            )
        """)
        conn.commit()
        cur.close()
    finally:
        conn.close()


def add_pending_note(underlying_symbol: str, note_date: date, note_text: str) -> int:
    """Stage a note for a trade not yet in journal_trade_reviews. Returns the new row's id."""
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO journal_pending_notes (underlying_symbol, note_date, note_text) VALUES (%s, %s, %s)",
            (underlying_symbol.upper(), note_date, note_text),
        )
        conn.commit()
        note_id = cur.lastrowid
        cur.close()
    finally:
        conn.close()
    return note_id


def get_pending_notes(applied: bool | None = False) -> pd.DataFrame:
    """Query staged notes, by default only the unapplied ones. Pass applied=None for all."""
    conn = _get_conn()
    try:
        sql = "SELECT * FROM journal_pending_notes"
        params: list = []
        if applied is not None:
            sql += " WHERE applied = %s"
            params.append(1 if applied else 0)
        sql += " ORDER BY note_date, underlying_symbol"
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()


def mark_pending_note_applied(note_id: int, review_id: int) -> None:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE journal_pending_notes SET applied=1, applied_review_id=%s, updated_at=NOW() WHERE id=%s",
            (review_id, note_id),
        )
        conn.commit()
        cur.close()
    finally:
        conn.close()


def apply_pending_notes() -> int:
    """Merge unapplied staged notes into any journal_trade_reviews row matching
    (underlying_symbol, entry_date == note_date) -- run this after building reviews for a new
    day's trades so same-day notes given before the Flex pull land automatically. Prepends to
    market_context (rather than overwriting) so it stacks with anything already written there.
    Returns the number of (note, review) merges applied.
    """
    notes = get_pending_notes(applied=False)
    if notes.empty:
        return 0
    conn = _get_conn()
    applied = 0
    try:
        cur = conn.cursor()
        for _, n in notes.iterrows():
            cur.execute(
                "SELECT id, market_context FROM journal_trade_reviews WHERE underlying_symbol=%s AND entry_date=%s",
                (n["underlying_symbol"], n["note_date"]),
            )
            rows = cur.fetchall()
            for review_id, existing_context in rows:
                prefix = f"TRADER NOTE (given same-day, before the Flex pull): {n['note_text']}"
                merged = prefix if not existing_context else f"{prefix}\n\n{existing_context}"
                cur.execute(
                    "UPDATE journal_trade_reviews SET market_context=%s, updated_at=NOW() WHERE id=%s",
                    (merged, review_id),
                )
                conn.commit()
                mark_pending_note_applied(int(n["id"]), review_id)
                applied += 1
    finally:
        conn.close()
    return applied


def add_trade_review(
    underlying_symbol: str,
    symbol: str,
    entry_date: date,
    exit_date: date | None,
    *,
    conid: int | None = None,
    asset_category: str | None = None,
    entry_verdict: str | None = None,
    entry_reason: str | None = None,
    exit_verdict: str | None = None,
    exit_reason: str | None = None,
    market_context: str | None = None,
    tags: str | None = None,
    realized_pnl: float | None = None,
) -> int:
    """Insert one review row. Returns the new row's id.

    No update-in-place key is enforced (a trade can reasonably get more than
    one review row over time, e.g. revisited later) -- to correct a row, query
    by (underlying_symbol, entry_date) and UPDATE/DELETE by id directly.
    """
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO journal_trade_reviews
                (underlying_symbol, symbol, conid, asset_category, entry_date, exit_date,
                 entry_verdict, entry_reason, exit_verdict, exit_reason, market_context,
                 tags, realized_pnl)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (underlying_symbol, symbol, conid, asset_category, entry_date, exit_date,
              entry_verdict, entry_reason, exit_verdict, exit_reason, market_context,
              tags, _safe_float(realized_pnl)))
        conn.commit()
        review_id = cur.lastrowid
        cur.close()
    finally:
        conn.close()
    return review_id


def get_trade_reviews(underlying_symbol: str | None = None, entry_date: date | None = None) -> pd.DataFrame:
    """Query reviews, optionally filtered by underlying symbol and/or entry date."""
    conn = _get_conn()
    try:
        sql = "SELECT * FROM journal_trade_reviews WHERE 1=1"
        params = []
        if underlying_symbol:
            sql += " AND underlying_symbol = %s"
            params.append(underlying_symbol.upper())
        if entry_date:
            sql += " AND entry_date = %s"
            params.append(entry_date)
        sql += " ORDER BY entry_date, underlying_symbol"
        return pd.read_sql(sql, conn, params=params)
    finally:
        conn.close()
