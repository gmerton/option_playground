import os
import mysql.connector
import pandas as pd


def _get_conn():
    return mysql.connector.connect(
        host="127.0.0.1",
        port=3306,
        user="root",
        password=os.environ["MYSQL_PASSWORD"],
        database="stocks",
    )


def upsert_strangle_detail(detail_df: pd.DataFrame) -> int:
    """
    Upsert rows from detail_df into strangle_study_detail.
    Primary key is (ticker, entry_date, expiry, pricing) — duplicate rows are replaced.
    Returns the number of rows affected.
    """
    if detail_df.empty:
        return 0

    sql = """
        INSERT INTO strangle_study_detail
            (ticker, entry_date, expiry, pricing,
             portfolio_pnl, net_entry_premium, return_on_credit, capital, roc)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            str(r.ticker),
            r.entry_date,
            r.expiry,
            str(r.pricing),
            float(r.portfolio_pnl)     if pd.notna(r.portfolio_pnl)     else None,
            float(r.net_entry_premium) if pd.notna(r.net_entry_premium) else None,
            float(r.return_on_credit)  if pd.notna(r.return_on_credit)  else None,
            float(r.capital)           if pd.notna(r.capital)           else None,
            float(r.roc)               if pd.notna(r.roc)               else None,
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


def upsert_strangle_summary(summaries_mid: list, summaries_worst: list) -> int:
    """
    Upsert per-ticker summary rows into strangle_study_summary.
    Primary key is (ticker, pricing) — duplicate rows are replaced.
    Returns the number of rows affected.
    """
    rows = []
    for s in summaries_mid:
        rows.append((s["ticker"], "mid",   s["n_entries"], s["roc"], s["return_on_credit"], s["win_rate"]))
    for s in summaries_worst:
        rows.append((s["ticker"], "worst", s["n_entries"], s["roc"], s["return_on_credit"], s["win_rate"]))

    if not rows:
        return 0

    sql = """
        INSERT INTO strangle_study_summary
            (ticker, pricing, n_entries, roc, return_on_credit, win_rate)
        VALUES
            (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            n_entries        = VALUES(n_entries),
            roc              = VALUES(roc),
            return_on_credit = VALUES(return_on_credit),
            win_rate         = VALUES(win_rate),
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
