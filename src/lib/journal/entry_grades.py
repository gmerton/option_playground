"""Grade every STOCK entry with the shared setup rubric (lib/alerts/grading.py) -- the same function
that decides what the alert monitor shows -- plus an execution score for entries that followed an
alert (fill vs the alert price in ADR, and minutes of delay). Writes journal_entry_grades and stamps
the rubric verdict onto journal_trade_reviews, so the journal and the alerts cannot disagree.

Matching: an entry = opening stock fills of one symbol/side within 5 min. It follows an alert when the
same symbol fired a same-side alert 0-30 min before the first fill (latest such alert wins). Alerts come
from the live monitor logs when a session has them, else from the replay logs. Unmatched entries are
graded as 'entry without an alert' at the fill time.
"""
from __future__ import annotations

import asyncio
import re
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from lib.alerts import study
from lib.alerts.grading import RUBRIC_VERSION, SHORT_KINDS, VERDICT, setup_grade
from lib.mysql_lib import _get_conn

EXEC_ERR = Path(__file__).resolve().parents[3] / "data" / "journal" / "execution_errors.csv"
ALERT_LOGS_START = "2026-08-13"      # first session with alert logs (replays)
MATCH_WINDOW_MIN = 30
CLUSTER_SEC = 300
SLIP_OK_ADR = 0.25                   # filled more than 1/4 ADR worse than the alert = chased
DELAY_OK_MIN = 10
SYSTEMATIC = "straddle_screener|systematic_spread_likely|playbook_verified|playbook_deviation|^systematic$|,systematic,|,systematic$"


def drop_execution_errors(t: pd.DataFrame) -> pd.DataFrame:
    """Remove fat-finger fills (data/journal/execution_errors.csv) so they don't count as entries,
    round trips, fills or cycles. Partial rows shrink by exclude_qty; emptied rows drop."""
    if not EXEC_ERR.exists():
        return t
    e = pd.read_csv(EXEC_ERR, comment="#")
    t = t.copy()
    for r in e.itertuples():
        m = (t.underlying_symbol == r.underlying_symbol) & (pd.to_datetime(t.trade_datetime) == pd.Timestamp(r.trade_datetime)) & (t.buy_sell == r.buy_sell)
        for i in t.index[m]:
            q = abs(float(t.at[i, "quantity"])) - float(r.exclude_qty)
            t.at[i, "quantity"] = q if float(t.at[i, "quantity"]) > 0 else -q
    return t[t.quantity.abs() > 1e-9]


def create_table() -> None:
    c = _get_conn()
    try:
        c.cursor().execute("""
            CREATE TABLE IF NOT EXISTS journal_entry_grades (
                trade_date        DATE NOT NULL,
                underlying_symbol VARCHAR(32) NOT NULL,
                t_fill            DATETIME NOT NULL,
                side              VARCHAR(5),
                qty               DECIMAL(14,4),
                fill_px           DECIMAL(14,4),
                alert_kind        VARCHAR(8),
                alert_t           VARCHAR(5),
                alert_px          DECIMAL(14,4),
                alert_src         VARCHAR(8),
                day_state         VARCHAR(8),
                setup_grade       CHAR(1),
                grade_why         VARCHAR(160),
                slip_adr          DECIMAL(8,3),
                delay_min         DECIMAL(8,2),
                exec_ok           TINYINT,
                rubric            VARCHAR(20),
                updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                PRIMARY KEY (trade_date, underlying_symbol, t_fill)
            )""")
        c.commit()
    finally:
        c.close()


def alerts_for(d: date) -> pd.DataFrame:
    ds = d.isoformat()
    live = [p for p in (study.LOGS / f"universe_alerts_{ds}.log", study.LOGS / f"universe_alerts_{ds}_oop.log") if p.exists()]
    use_live = sum(len(p.read_text().splitlines()) for p in live) >= 5
    paths = live if use_live else [p for p in (study.LOGS / f"universe_alerts_{ds}_replay.log",
                                               study.LOGS / f"universe_alerts_{ds}_replay_oop.log") if p.exists()]
    a = study.parse_logs(paths) if paths else pd.DataFrame(columns=study.KEY)
    if len(a):
        a["mins"] = a.t.str[:2].astype(int) * 60 + a.t.str[3:].astype(int)
        a["side"] = np.where(a.kind.isin(SHORT_KINDS), "short", "long")
    a["src"] = "live" if use_live else "replay"
    return a


def entries_for(t_day: pd.DataFrame) -> list[dict]:
    o = t_day[(t_day.asset_category == "STK") & t_day.open_close.isin(["O", "C;O"])].copy()
    o["dt"] = pd.to_datetime(o.trade_datetime)
    out: list[dict] = []
    for (sym, bs), g in o.sort_values("dt").groupby(["underlying_symbol", "buy_sell"]):
        cur = None
        for r in g.itertuples():
            q = abs(float(r.quantity))
            if cur and (r.dt - cur["dt"]).total_seconds() <= CLUSTER_SEC:
                cur["cost"] += q * float(r.trade_price); cur["qty"] += q
                continue
            cur = dict(sym=sym, side="long" if bs == "BUY" else "short", dt=r.dt, qty=q, cost=q * float(r.trade_price))
            out.append(cur)
    for e in out:
        e["px"] = e["cost"] / e["qty"]
    return out


def grade_day(d: date, t_day: pd.DataFrame) -> pd.DataFrame:
    from lib.alerts.context import load_context
    ents = entries_for(t_day)
    if not ents:
        return pd.DataFrame()
    ctx = asyncio.run(load_context(sorted({e["sym"] for e in ents}), d))
    al = alerts_for(d)
    rows = []
    for e in ents:
        c = ctx.get(e["sym"]); ds = getattr(c, "day_state", None); adr = getattr(c, "adr_pct", None) or 3.0
        fm = e["dt"].hour * 60 + e["dt"].minute
        m = al[(al.sym == e["sym"]) & (al.side == e["side"]) & (al.mins <= fm) & (fm - al.mins <= MATCH_WINDOW_MIN)] if len(al) else al
        if len(m):
            a = m.sort_values("mins").iloc[-1]
            g = setup_grade(e["side"], a.kind, int(a.mins), ds)
            sign = 1 if e["side"] == "long" else -1
            slip = sign * (e["px"] - a.px) / a.px * 100 / adr
            delay = (e["dt"] - pd.Timestamp(f"{d} {a.t}")).total_seconds() / 60
            rows.append(dict(trade_date=d, underlying_symbol=e["sym"], t_fill=e["dt"], side=e["side"], qty=e["qty"], fill_px=round(e["px"], 4),
                             alert_kind=a.kind, alert_t=a.t, alert_px=a.px, alert_src=al.src.iloc[0], day_state=ds, setup_grade=g.grade,
                             grade_why=g.why, slip_adr=round(slip, 3), delay_min=round(delay, 2),
                             exec_ok=int(slip <= SLIP_OK_ADR and delay <= DELAY_OK_MIN), rubric=RUBRIC_VERSION))
        else:
            g = setup_grade(e["side"], None, fm, ds)
            rows.append(dict(trade_date=d, underlying_symbol=e["sym"], t_fill=e["dt"], side=e["side"], qty=e["qty"], fill_px=round(e["px"], 4),
                             alert_kind=None, alert_t=None, alert_px=None, alert_src=al.src.iloc[0] if len(al) else None, day_state=ds,
                             setup_grade=g.grade, grade_why=g.why, slip_adr=None, delay_min=None, exec_ok=None, rubric=RUBRIC_VERSION))
    return pd.DataFrame(rows)


def _save(d: date, df: pd.DataFrame) -> None:
    c = _get_conn()
    try:
        cur = c.cursor()
        cur.execute("DELETE FROM journal_entry_grades WHERE trade_date=%s", (d,))
        cols = list(df.columns)
        for r in df.itertuples(index=False):
            vals = [None if (isinstance(v, float) and np.isnan(v)) else (v.to_pydatetime() if isinstance(v, pd.Timestamp) else v) for v in r]
            cur.execute(f"INSERT INTO journal_entry_grades ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))})", vals)
        c.commit()
    finally:
        c.close()


_TIME = re.compile(r"\b(\d{1,2}):(\d{2})\b")
_RUBRIC_PARA = re.compile(r"^RUBRIC [^\n]*\n\n", re.S)
_PROSE = re.compile(r"\(Prose verdict before the rubric: ([a-z_]+)\.\)")


def stamp_reviews(d: date, g: pd.DataFrame) -> int:
    """Set entry_verdict on the day's discretionary stock reviews from the rubric (idempotent)."""
    if g.empty:
        return 0
    c = _get_conn(); n = 0
    try:
        cur = c.cursor()
        cur.execute("SELECT id, underlying_symbol, symbol, entry_verdict, entry_reason, tags, asset_category FROM journal_trade_reviews WHERE entry_date=%s", (d,))
        for rid, u, sym, ev, er, tags, ac in cur.fetchall():
            if ac != "STK" or re.search(SYSTEMATIC, tags or "") or re.search("multi-leg|straddle|condor|spread", sym or "", re.I):
                continue
            cand = g[g.underlying_symbol == u]
            low = (sym or "").lower()
            if "short" in low:
                cand = cand[cand.side == "short"]
            elif "(long" in low:
                cand = cand[cand.side == "long"]
            if cand.empty:
                continue
            er = er or ""
            prior = _RUBRIC_PARA.match(er)
            prose = (_PROSE.search(prior.group(0)).group(1) if prior and _PROSE.search(prior.group(0)) else ev) or "none"
            body = er[prior.end():] if prior else er
            hint = _TIME.search(sym or "") or _TIME.search(body)
            if hint and len(cand) > 1:
                hm = int(hint.group(1)) * 60 + int(hint.group(2))
                cand = cand.assign(_d=(cand.t_fill.dt.hour * 60 + cand.t_fill.dt.minute - hm).abs()).sort_values("_d")
            r = cand.iloc[0]
            line = f"RUBRIC {r.rubric}: setup grade {r.setup_grade} -- {r.grade_why}."
            if r.alert_kind:
                line += (f" Execution vs the {r.alert_kind} alert {r.alert_t} @{float(r.alert_px):.2f}: filled {float(r.slip_adr):+.2f} ADR "
                         f"{'worse' if float(r.slip_adr) > 0 else 'better'}, {float(r.delay_min):.0f} min after it "
                         f"({'ok' if r.exec_ok else 'LATE / CHASED'}).")
            else:
                line += " No same-side alert in the 30 min before the fill."
            line += f" (Prose verdict before the rubric: {prose}.)"
            tg = [x for x in (tags or "").split(",") if x and not x.startswith(("setup_", "rubric_graded", "exec_late"))]
            tg += ["rubric_graded", f"setup_{r.setup_grade}"] + (["exec_late"] if r.alert_kind and not r.exec_ok else [])
            cur.execute("UPDATE journal_trade_reviews SET entry_verdict=%s, entry_reason=%s, tags=%s WHERE id=%s",
                        (VERDICT[r.setup_grade], line + "\n\n" + body, ",".join(tg)[:255], rid))
            n += 1
        c.commit()
    finally:
        c.close()
    return n


def rebuild(since: str | None = None, stamp: bool = True) -> pd.DataFrame:
    create_table()
    c = _get_conn()
    t = pd.read_sql("SELECT trade_date, underlying_symbol, asset_category, open_close, trade_datetime, buy_sell, quantity, trade_price FROM journal_trades", c)
    c.close()
    t["trade_date"] = pd.to_datetime(t.trade_date).dt.date
    t = drop_execution_errors(t)
    start = max(since or ALERT_LOGS_START, ALERT_LOGS_START)
    out = []
    for d in sorted(x for x in t.trade_date.unique() if str(x) >= start):
        g = grade_day(d, t[t.trade_date == d])
        if g.empty:
            continue
        _save(d, g)
        n = stamp_reviews(d, g) if stamp else 0
        print(f"  {d}: {len(g)} entries  grades {g.setup_grade.value_counts().reindex(list('ABCF')).fillna(0).astype(int).to_dict()}  "
              f"alert-matched {g.alert_kind.notna().sum()}  exec ok {int(g.exec_ok.fillna(0).sum())}  reviews stamped {n}", flush=True)
        out.append(g)
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()
