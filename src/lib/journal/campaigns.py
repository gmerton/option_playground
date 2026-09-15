"""Option CAMPAIGNS: a spread and everything it was rolled into, tracked as one entity.

The journal keys everything by contract (conid), so a roll -- close the 9/18 200/190 put spread, open the
10/16 190/180 in the same ticket -- shows up as an unrelated loss and an unrelated new position. Gabe
(2026-09-14): "make sure the journal tracks the rolled spreads as a single entity."

Rules, deterministic from journal_trades (rebuilt from scratch every run, so it is idempotent):
  * A TICKET = all option fills of one underlying inside the same minute.
  * Fills are applied to LOTS keyed by (underlying, expiry, put/call, strike). An opening fill joins the lot's
    existing campaign if the lot is already open; otherwise it needs a campaign:
      - if the same ticket also CLOSES lots, the opening fills inherit that campaign (a roll);
      - else if it legs into an open lot (same expiry + put/call, opposite sign) it joins that lot's campaign;
      - else all opening fills in the ticket share one NEW campaign (the legs of a spread opened together).
  * A closing fill belongs to the campaign of the lot it closes. A ticket that closes lots from several
    campaigns merges them.
  * A campaign is CLOSED when every lot in it is flat; EXPIRED if its open lots are all past expiry (IBKR usually
    books an expiry as a 16:20 fill at 0.00, but not always). Realized P&L = the sum of the linked fills' realized_pnl.

Tables: journal_campaigns (one row per campaign) and journal_campaign_trades (trade_id -> campaign, role).
CLI:  PYTHONPATH=src python -m lib.journal.campaigns [UNDERLYING] [--no-db]
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict

import pandas as pd

from lib.mysql_lib import _get_conn


def load_option_trades() -> pd.DataFrame:
    conn = _get_conn()
    try:
        df = pd.read_sql("""
            SELECT trade_id, conid, trade_date, trade_datetime, symbol, underlying_symbol, put_call, strike, expiry,
                   buy_sell, open_close, quantity, trade_price, realized_pnl
            FROM journal_trades WHERE asset_category = 'OPT'
            ORDER BY underlying_symbol, trade_datetime, trade_id
        """, conn)
    finally:
        conn.close()
    df["trade_datetime"] = pd.to_datetime(df["trade_datetime"])
    df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.date
    df["expiry"] = pd.to_datetime(df["expiry"]).dt.date
    for c in ("quantity", "trade_price", "realized_pnl", "strike"):
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    return df


def _side_qty(r) -> float:
    return abs(r.quantity) if r.buy_sell == "BUY" else -abs(r.quantity)


def build_campaigns(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (campaigns, links). campaigns: campaign_id, underlying, first_date, last_date, status, n_rolls,
    legs (json list of lots with net qty), realized_pnl, net_premium (credits - debits per share, signed),
    label. links: trade_id, campaign_id, role (open / close / roll_close / roll_open)."""
    camps: dict[int, dict] = {}
    links: list[dict] = []
    next_id = 1
    for und, g in df.groupby("underlying_symbol", sort=False):
        lots: dict[tuple, dict] = {}       # (expiry, pc, strike) -> {"qty": signed, "camp": id}
        g = g.copy(); g["minute"] = g.trade_datetime.dt.floor("min")
        for _, tk in g.groupby("minute", sort=True):
            closes = tk[tk.open_close.str.contains("C", na=False)]
            opens = tk[tk.open_close.str.contains("O", na=False)]
            # campaigns touched by the closes in this ticket
            touched = set()
            for r in closes.itertuples():
                k = (r.expiry, r.put_call, float(r.strike))
                if k in lots and lots[k]["camp"] is not None:
                    touched.add(lots[k]["camp"])
            if len(touched) > 1:                        # merge into the oldest
                keep = min(touched)
                for cid in touched - {keep}:
                    for k, lot in lots.items():
                        if lot["camp"] == cid: lot["camp"] = keep
                    for l in links:
                        if l["campaign_id"] == cid: l["campaign_id"] = keep
                    camps[keep]["merged"].append(cid); camps.pop(cid, None)
                touched = {keep}
            camp_for_opens = next(iter(touched)) if touched else None
            is_roll = bool(touched) and not opens.empty
            if camp_for_opens is None and not opens.empty:
                # opening legs of a NEW spread -- unless they extend lots already open (adding to a position) or LEG INTO
                # a spread on an open lot: same expiry + put/call, opposite sign (FTNT 9/14: a 190C sold against a held 170C)
                existing = {lots[(r.expiry, r.put_call, float(r.strike))]["camp"] for r in opens.itertuples()
                            if (r.expiry, r.put_call, float(r.strike)) in lots and abs(lots[(r.expiry, r.put_call, float(r.strike))]["qty"]) > 1e-9}
                for r in opens.itertuples():
                    for k, lot in lots.items():
                        if k[0] == r.expiry and k[1] == r.put_call and abs(lot["qty"]) > 1e-9 and lot["qty"] * _side_qty(r) < 0 and lot["camp"] is not None:
                            existing.add(lot["camp"])
                existing.discard(None)
                if existing:
                    camp_for_opens = min(existing)
                else:
                    camp_for_opens = next_id; next_id += 1
                    camps[camp_for_opens] = {"underlying": und, "first_date": tk.trade_date.min(), "n_rolls": 0, "merged": []}
            if is_roll:
                camps[camp_for_opens]["n_rolls"] += 1
            for r in closes.itertuples():
                k = (r.expiry, r.put_call, float(r.strike))
                lot = lots.setdefault(k, {"qty": 0.0, "camp": camp_for_opens})
                cid = lot["camp"] if lot["camp"] is not None else camp_for_opens
                if cid is None:                          # closing a lot opened before the journal's history: its own campaign
                    cid = next_id; next_id += 1
                    camps[cid] = {"underlying": und, "first_date": tk.trade_date.min(), "n_rolls": 0, "merged": []}
                    camp_for_opens = camp_for_opens if camp_for_opens is not None else cid
                lot["qty"] += _side_qty(r); lot["camp"] = cid
                links.append({"trade_id": int(r.trade_id), "campaign_id": cid, "role": "roll_close" if is_roll else "close"})
            for r in opens.itertuples():
                k = (r.expiry, r.put_call, float(r.strike))
                lot = lots.setdefault(k, {"qty": 0.0, "camp": camp_for_opens})
                if lot["camp"] is None or abs(lot["qty"]) < 1e-9: lot["camp"] = camp_for_opens
                lot["qty"] += _side_qty(r)
                links.append({"trade_id": int(r.trade_id), "campaign_id": lot["camp"], "role": "roll_open" if is_roll else "open"})
        # finalize this underlying's campaigns
        for cid, c in list(camps.items()):
            if c["underlying"] != und: continue
            c["lots"] = [(k, lot["qty"]) for k, lot in lots.items() if lot["camp"] == cid]
    L = pd.DataFrame(links)
    rows = []
    for cid, c in camps.items():
        tids = L[L.campaign_id == cid].trade_id
        t = df[df.trade_id.isin(tids)]
        # legs from the campaign's OWN fills (the shared lot table only remembers the last campaign on a strike)
        sq = t.assign(sq=[_side_qty(r) for r in t.itertuples()]).groupby(["expiry", "put_call", "strike"], sort=True).sq.sum()
        legs = [{"expiry": str(k[0]), "pc": k[1], "strike": float(k[2]), "net_qty": float(q)} for k, q in sq.items()]
        open_lots = [l for l in legs if abs(l["net_qty"]) > 1e-9]
        prem = float(((t.buy_sell.eq("SELL") * 2 - 1) * t.trade_price * t.quantity.abs()).sum())   # + = net credit received
        kinds = [f"{str(k[0])} {k[1]}" for k in sq.index]; kinds = sorted(set(kinds), key=kinds.index)
        today = pd.Timestamp.today().date()
        status = "closed" if not open_lots else ("expired" if all(pd.Timestamp(l["expiry"]).date() < today for l in open_lots) else "open")
        rows.append(dict(campaign_id=cid, underlying=c["underlying"], first_date=t.trade_date.min(), last_date=t.trade_date.max(),
                         status=status, n_rolls=c["n_rolls"], n_fills=len(t), realized_pnl=float(t.realized_pnl.sum()),
                         net_premium=round(prem, 2), legs=json.dumps(legs), label=f"{c['underlying']} {' -> '.join(kinds)}"))
    C = pd.DataFrame(rows).sort_values(["underlying", "first_date"]).reset_index(drop=True) if rows else pd.DataFrame()
    return C, L


def persist(C: pd.DataFrame, L: pd.DataFrame) -> None:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS journal_campaigns (
            campaign_id INT PRIMARY KEY, underlying VARCHAR(32) NOT NULL, first_date DATE, last_date DATE, status VARCHAR(8),
            n_rolls INT, n_fills INT, realized_pnl DECIMAL(14,4), net_premium DECIMAL(14,4), legs JSON, label VARCHAR(255),
            rebuilt_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS journal_campaign_trades (
            trade_id BIGINT UNSIGNED PRIMARY KEY, campaign_id INT NOT NULL, role VARCHAR(12), INDEX (campaign_id))""")
        cur.execute("DELETE FROM journal_campaign_trades"); cur.execute("DELETE FROM journal_campaigns")
        if len(C):
            cur.executemany("""INSERT INTO journal_campaigns (campaign_id, underlying, first_date, last_date, status, n_rolls, n_fills,
                               realized_pnl, net_premium, legs, label) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                            [(int(r.campaign_id), r.underlying, r.first_date, r.last_date, r.status, int(r.n_rolls), int(r.n_fills),
                              float(r.realized_pnl), float(r.net_premium), r.legs, r.label[:255]) for r in C.itertuples()])
            cur.executemany("INSERT INTO journal_campaign_trades (trade_id, campaign_id, role) VALUES (%s,%s,%s)",
                            [(int(r.trade_id), int(r.campaign_id), r.role) for r in L.itertuples()])
        conn.commit()
    finally:
        conn.close()


def rebuild(persist_db: bool = True) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df = load_option_trades()
    C, L = build_campaigns(df)
    if persist_db and len(C):
        persist(C, L)
    return df, C, L


def describe(df: pd.DataFrame, C: pd.DataFrame, L: pd.DataFrame, cid: int) -> str:
    """Multi-line story of one campaign: each ticket as a line, then the running P&L."""
    c = C[C.campaign_id == cid].iloc[0]
    t = df[df.trade_id.isin(L[L.campaign_id == cid].trade_id)].copy().sort_values(["trade_datetime", "expiry", "strike"])
    t = t.merge(L[["trade_id", "role"]], on="trade_id")
    out = [f"{c.label}  [{c.status}, {c.n_rolls} roll(s), {c.n_fills} fills, {c.first_date} -> {c.last_date}]"]
    for (m, role), tk in t.groupby([t.trade_datetime.dt.floor("min"), "role"], sort=True):
        legs = ", ".join(f"{'sold' if r.buy_sell == 'SELL' else 'bought'} {abs(r.quantity):g}x {r.expiry:%m/%d} {r.strike:g}{r.put_call} @{r.trade_price:.2f}"
                         for r in tk.itertuples())
        pnl = tk.realized_pnl.sum()
        out.append(f"  {m:%Y-%m-%d %H:%M} {role:10s} {legs}" + (f"  realized {pnl:+,.0f}" if abs(pnl) > 0.005 else ""))
    open_legs = [l for l in json.loads(c.legs) if abs(l["net_qty"]) > 1e-9]
    tail = (" | CLOSED" if not open_legs else
            (" | EXPIRED (no closing fill recorded): " if c.status == "expired" else " | still open: ")
            + ", ".join(f"{l['net_qty']:+g}x {l['expiry']} {l['strike']:g}{l['pc']}" for l in open_legs))
    out.append(f"  realized to date {c.realized_pnl:+,.2f} | net premium collected {c.net_premium:+.2f}/sh" + tail)
    return "\n".join(out)


def journal_section(day) -> str:
    """Markdown block for run_daily_journal: every campaign with a fill on `day`, told as one story, so a roll's
    closing loss and its new legs are read together instead of as an unrelated exit and entry."""
    df, C, L = rebuild(persist_db=True)
    ids = touched_on(df, C, L, day) if len(C) else []
    lines = ["## Option campaigns touched today (rolled spreads tracked as ONE entity)", ""]
    if not ids:
        lines.append("_None._"); lines.append(""); return "\n".join(lines)
    for cid in ids:
        lines.append("```"); lines.append(describe(df, C, L, cid)); lines.append("```"); lines.append("")
    lines.append("_Judge a rolled spread on the campaign line (realized to date + what is still open), not on the roll's closing fill._")
    lines.append("")
    return "\n".join(lines)


def touched_on(df: pd.DataFrame, C: pd.DataFrame, L: pd.DataFrame, day) -> list[int]:
    """Campaign ids with a fill on `day` (date)."""
    tids = df[df.trade_date == day].trade_id
    return sorted(L[L.trade_id.isin(tids)].campaign_id.unique().tolist())


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    df, C, L = rebuild(persist_db="--no-db" not in sys.argv)
    sel = C[C.underlying == args[0].upper()] if args else C[(C.n_rolls > 0) | (C.status == "open")]
    print(f"{len(C)} campaigns from {len(df)} option fills; {int((C.n_rolls > 0).sum())} with rolls; {int((C.status == 'open').sum())} open")
    for cid in sel.campaign_id:
        print(); print(describe(df, C, L, int(cid)))
