import math
import os
from datetime import date, datetime
import mysql.connector
import pandas as pd


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
