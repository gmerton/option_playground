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


def create_position_tables() -> None:
    """Create strategy_positions and position_trades tables if they don't exist."""
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS strategy_positions (
                id               INT AUTO_INCREMENT PRIMARY KEY,
                strategy_name    VARCHAR(64)  NOT NULL,
                ticker           VARCHAR(16)  NOT NULL,
                position_type    VARCHAR(20)  NOT NULL,  -- 'bull_put_spread', 'bear_call_spread', 'put_calendar', 'short_put'
                status           VARCHAR(10)  NOT NULL DEFAULT 'open',  -- 'open', 'closed'
                contracts        INT          NOT NULL DEFAULT 1,
                entry_date       DATE         NOT NULL,
                expiry           DATE,
                short_strike     DECIMAL(10,4),
                long_strike      DECIMAL(10,4),
                entry_value      DECIMAL(10,4),  -- credit received (>0) or debit paid (<0) per share
                profit_target_pct DECIMAL(5,4) NOT NULL,
                ann_target        DECIMAL(8,4) NULL,  -- annualized ROC target (e.g. 1.0 = 100%); NULL = use profit_target_pct
                close_date       DATE,
                notes            TEXT,
                created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_status (status),
                INDEX idx_ticker (ticker)
            )
        """)
        # Migration: add ann_target if the table existed before this column was added
        cur.execute("""
            ALTER TABLE strategy_positions
            ADD COLUMN IF NOT EXISTS ann_target DECIMAL(8,4) NULL
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS position_trades (
                id           INT AUTO_INCREMENT PRIMARY KEY,
                position_id  INT             NOT NULL,
                trade_id     BIGINT UNSIGNED NOT NULL,
                leg_role     VARCHAR(20)     NOT NULL,  -- 'open_short', 'open_long', 'close_short', 'close_long'
                UNIQUE KEY uq_pos_trade (position_id, trade_id),
                FOREIGN KEY (position_id) REFERENCES strategy_positions(id),
                FOREIGN KEY (trade_id)   REFERENCES trades(id)
            )
        """)
        conn.commit()
        cur.close()
    finally:
        conn.close()


def create_position(
    strategy_name: str,
    ticker: str,
    position_type: str,
    contracts: int,
    entry_date: date,
    expiry: date,
    short_strike: float,
    long_strike: float | None,
    entry_value: float,
    profit_target_pct: float,
    notes: str = "",
    ann_target: float | None = None,
) -> int:
    """Insert a new strategy_positions row and return its id."""
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO strategy_positions
                (strategy_name, ticker, position_type, status, contracts,
                 entry_date, expiry, short_strike, long_strike,
                 entry_value, profit_target_pct, ann_target, notes)
            VALUES (%s, %s, %s, 'open', %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (strategy_name, ticker, position_type, contracts,
              entry_date, expiry, short_strike, long_strike,
              entry_value, profit_target_pct, ann_target, notes))
        conn.commit()
        position_id = cur.lastrowid
        cur.close()
    finally:
        conn.close()
    return position_id


def link_trades_to_position(position_id: int, trade_legs: list[tuple[int, str]]) -> None:
    """
    Link trade IDs to a position.
    trade_legs: list of (trade_id, leg_role) where leg_role is one of:
        'open_short', 'open_long', 'close_short', 'close_long'
    """
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.executemany("""
            INSERT IGNORE INTO position_trades (position_id, trade_id, leg_role)
            VALUES (%s, %s, %s)
        """, [(position_id, tid, role) for tid, role in trade_legs])
        conn.commit()
        cur.close()
    finally:
        conn.close()


def close_position(position_id: int, close_date: date) -> None:
    """Mark a position as closed."""
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            UPDATE strategy_positions SET status='closed', close_date=%s WHERE id=%s
        """, (close_date, position_id))
        conn.commit()
        cur.close()
    finally:
        conn.close()


def get_open_positions() -> list[dict]:
    """Return all open positions with their open legs joined from trades."""
    conn = _get_conn()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT
                sp.id, sp.strategy_name, sp.ticker, sp.position_type,
                sp.contracts, sp.entry_date, sp.expiry,
                sp.short_strike, sp.long_strike,
                sp.entry_value, sp.profit_target_pct, sp.notes,
                pt.trade_id, pt.leg_role,
                t.buy_sell, t.quantity, t.price, t.strike AS trade_strike,
                t.expiry AS trade_expiry, t.put_call
            FROM strategy_positions sp
            JOIN position_trades pt ON pt.position_id = sp.id
            JOIN trades t           ON t.id = pt.trade_id
            WHERE sp.status = 'open'
              AND pt.leg_role IN ('open_short', 'open_long')
            ORDER BY sp.id, pt.leg_role
        """)
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()

    # Group by position
    positions: dict[int, dict] = {}
    for row in rows:
        pid = row["id"]
        if pid not in positions:
            positions[pid] = {
                "id":                pid,
                "strategy_name":     row["strategy_name"],
                "ticker":            row["ticker"],
                "position_type":     row["position_type"],
                "contracts":         row["contracts"],
                "entry_date":        row["entry_date"],
                "expiry":            row["expiry"],
                "short_strike":      float(row["short_strike"] or 0),
                "long_strike":       float(row["long_strike"]) if row["long_strike"] else None,
                "entry_value":       float(row["entry_value"]),
                "profit_target_pct": float(row["profit_target_pct"]),
                "ann_target":        None,   # column removed; kept for monitor compatibility
                "notes":             row["notes"] or "",
                "legs":              [],
            }
        positions[pid]["legs"].append({
            "leg_role":    row["leg_role"],
            "trade_strike": float(row["trade_strike"]),
            "trade_expiry": row["trade_expiry"],
            "put_call":     row["put_call"],
            "price":        float(row["price"]),
        })
    return list(positions.values())


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
    n_fills, max_abs_qty, realized_pnl, still_open.
    """
    conn = _get_conn()
    try:
        df = pd.read_sql("""
            SELECT conid, symbol, underlying_symbol, asset_category, put_call, strike, expiry,
                   trade_date, trade_id, quantity, realized_pnl
            FROM journal_trades
            ORDER BY conid, trade_date, trade_id
        """, conn)
    finally:
        conn.close()

    df["trade_date"] = pd.to_datetime(df["trade_date"])
    cycles = []
    for conid, g in df.groupby("conid"):
        g = g.reset_index(drop=True)
        running = 0.0
        rows_in_cycle = []
        for _, r in g.iterrows():
            rows_in_cycle.append(r)
            running += r["quantity"]
            if abs(running) < 1e-6:
                cyc = pd.DataFrame(rows_in_cycle)
                cycles.append(_cycle_row(g, cyc, still_open=False))
                rows_in_cycle = []
        if rows_in_cycle:
            cyc = pd.DataFrame(rows_in_cycle)
            cycles.append(_cycle_row(g, cyc, still_open=True))

    return pd.DataFrame(cycles)


def _cycle_row(g: pd.DataFrame, cyc: pd.DataFrame, still_open: bool) -> dict:
    return {
        "conid": g["conid"].iloc[0],
        "symbol": g["symbol"].iloc[0],
        "underlying_symbol": g["underlying_symbol"].iloc[0],
        "asset_category": g["asset_category"].iloc[0],
        "put_call": g["put_call"].iloc[0],
        "strike": g["strike"].iloc[0],
        "expiry": g["expiry"].iloc[0],
        "entry_date": cyc["trade_date"].min().date(),
        "exit_date": None if still_open else cyc["trade_date"].max().date(),
        "first_side": "LONG" if cyc.iloc[0]["quantity"] > 0 else "SHORT",
        "n_fills": len(cyc),
        "max_abs_qty": cyc["quantity"].cumsum().abs().max(),
        "realized_pnl": cyc["realized_pnl"].sum(),
        "still_open": still_open,
    }


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
