"""
IBKR data source for the long-straddle screen: FVR and ~7-DTE straddle quotes without Tradier.

Returns the same shapes as run_straddle_fvr_scan.scan_one / quote_straddle so
run_straddle_screen.py can switch sources with `--data-source ibkr`:

  scan result  {tkr, spot, iv30, iv90, t30, t90, fvr}  or  {tkr, err}
  quote        {dte, cost, ba, oi, strikes}  or  {dte, bad: True}  or  None

Same selection rules as the Tradier path:
  near expiry  20-45 DTE, nearest 30     far expiry  50-160 DTE, > near + 15, nearest 90
  ATM IV       put nearest 0.50 delta among the 3 strikes closest to spot
  straddle     6-17 DTE, nearest 10; call and put each nearest 0.50 delta; cost at mid,
               BA% = worst leg's (ask - bid) / mid, OI = the smaller leg's

Market data:
  - Quotes and model greeks use market data type 2 (FROZEN): live during the session, the
    closing values after it. Verified 2026-09-16 evening on PLTR.
  - Open interest (generic tick 101) only populates under type 1, so the chosen straddle
    legs get a second, type-1 request just for OI.
  - Requests go out in batches under the default 100-line market-data limit.

⚠ Vendor difference: Tradier's IV is ORATS mid_iv; IBKR's is its own model IV. FVR is a ratio
of two IVs from the same vendor, so the level should agree closely but not exactly. The
screen prints both sources' FVR when a Tradier archive exists for the day.

Read-only: reqSecDefOptParams / reqMktData / cancelMktData. No orders.
"""
from __future__ import annotations

import math
from datetime import date, datetime

from ib_async import Option, Stock

BATCH = 90            # market-data lines per batch (default account limit is 100)
WAIT_S = 4.0          # time for frozen quotes + model greeks to arrive
GAP_S = 5.0           # after cancelling a batch, lines take seconds to free: with a 0.2s gap the
                      # 2nd+ batches of a 326-name run came back 36/90, 35/90, 6/56 (2026-09-16);
                      # with 5s every batch is full
OI_WAIT_S = 3.0
N_STRIKES = 3


def _num(x) -> float | None:
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else float(x)


def _dte(exp: str) -> int:
    return (datetime.strptime(exp, "%Y%m%d").date() - date.today()).days


class _Snap:
    """Values copied out of an ib_async Ticker at read time.

    ib_async keeps ONE Ticker per contract, so a later request on the same contract (the type-1
    OI pass) overwrites the frozen bid/ask captured earlier. Copying the numbers out is what
    keeps the two passes independent. Built empty for contracts IBKR could not qualify.
    """
    def __init__(self, t=None):
        nan = float("nan")
        g = t.modelGreeks if t is not None else None
        self.last = t.last if t is not None else nan
        self.close = t.close if t is not None else nan
        self.mkt = t.marketPrice() if t is not None else nan
        self.bid = t.bid if t is not None else nan
        self.ask = t.ask if t is not None else nan
        self.delta = g.delta if g else None
        self.iv = g.impliedVol if g else None
        self.call_oi = t.callOpenInterest if t is not None else nan
        self.put_oi = t.putOpenInterest if t is not None else nan


def _qualify(ib, contracts) -> None:
    """Populate conId in place, in chunks; strikes that don't exist at an expiry stay at conId 0."""
    todo = [c for c in contracts if not c.conId]
    for i in range(0, len(todo), 200):
        try:
            ib.qualifyContracts(*todo[i:i + 200])
        except Exception:                                           # noqa: BLE001
            pass


def _empty(q: "_Snap") -> bool:
    vals = (q.last, q.close, q.mkt, q.bid, q.ask, q.call_oi, q.put_oi, q.iv)
    return not any(v is not None and v == v and v > 0 for v in vals)


def _pass(ib, contracts, mdt, generic, wait, out):
    ib.reqMarketDataType(mdt)
    for i in range(0, len(contracts), BATCH):
        batch = contracts[i:i + BATCH]
        tks = [(c, ib.reqMktData(c, generic, False, False)) for c in batch]
        ib.sleep(wait)
        for c, t in tks:
            out[id(c)] = _Snap(t)
            ib.cancelMktData(c)
        ib.sleep(GAP_S)


def _snapshot(ib, contracts, mdt: int, generic: str = "", wait: float = WAIT_S) -> dict:
    """{id(contract): _Snap} after streaming each batch for `wait` seconds then cancelling.

    One retry pass, at double the wait, for qualified contracts that came back empty.
    """
    _qualify(ib, contracts)
    out = {id(c): _Snap() for c in contracts if not c.conId}
    contracts = [c for c in contracts if c.conId]
    _pass(ib, contracts, mdt, generic, wait, out)
    retry = [c for c in contracts if _empty(out[id(c)])]
    if retry:
        _pass(ib, retry, mdt, generic, 2 * wait, out)
    return out


def _chain(ib, stk):
    chains = ib.reqSecDefOptParams(stk.symbol, "", stk.secType, stk.conId)
    smart = [c for c in chains if c.exchange == "SMART"] or chains
    if not smart:
        return None
    same = [c for c in smart if c.tradingClass == stk.symbol]      # skip adjusted/mini classes
    return max(same or smart, key=lambda c: len(c.expirations))


def scan_and_quote(ib, tickers: list[str], quote_min_fvr: float = 1.0, log=print):
    """(results, quotes) for `tickers`, mirroring run_straddle_screen.gather()."""
    stocks = {t: Stock(t, "SMART", "USD") for t in tickers}
    ib.qualifyContracts(*stocks.values())
    res = {t: {"tkr": t, "err": "not qualified"} for t, s in stocks.items() if not s.conId}
    live = {t: s for t, s in stocks.items() if s.conId}

    log(f"  IBKR: spot for {len(live)} names")
    snap = _snapshot(ib, list(live.values()), mdt=2)
    spot = {}
    for t, s in live.items():
        tk = snap[id(s)]
        px = next((v for v in (_num(tk.last), _num(tk.mkt), _num(tk.close)) if v and v > 0), None)
        if px:
            spot[t] = px
        else:
            res[t] = {"tkr": t, "err": "no spot"}

    log(f"  IBKR: option chains for {len(spot)} names")
    plan, legs = {}, []
    for t in spot:
        try:
            ch = _chain(ib, live[t])
        except Exception as e:                                      # noqa: BLE001
            res[t] = {"tkr": t, "err": f"chain {type(e).__name__}"[:30]}; continue
        if not ch:
            res[t] = {"tkr": t, "err": "no chain"}; continue
        dted = [(e, _dte(e)) for e in ch.expirations]
        near = [x for x in dted if 20 <= x[1] <= 45]
        if not near:
            res[t] = {"tkr": t, "err": "no near expiry"}; continue
        e30, t30 = min(near, key=lambda x: abs(x[1] - 30))
        far = [x for x in dted if 50 <= x[1] <= 160 and x[1] > t30 + 15]
        if not far:
            res[t] = {"tkr": t, "err": "no far expiry"}; continue
        e90, t90 = min(far, key=lambda x: abs(x[1] - 90))
        ks = sorted(ch.strikes, key=lambda k: abs(k - spot[t]))[:N_STRIKES]
        mk = lambda e, k, r: Option(t, e, k, r, "SMART", tradingClass=ch.tradingClass, multiplier=ch.multiplier)
        p30 = [mk(e30, k, "P") for k in ks]
        p90 = [mk(e90, k, "P") for k in ks]
        wk = [x for x in dted if 6 <= x[1] <= 17]
        # Friday expiries only when listed (Mon/Wed weeklies are untested tenors); target 7 DTE
        wk = [x for x in wk if datetime.strptime(x[0], "%Y%m%d").weekday() == 4] or wk
        plan[t] = dict(e30=e30, t30=t30, e90=e90, t90=t90, p30=p30, p90=p90, ch=ch, ks=ks,
                       wk=min(wk, key=lambda x: abs(x[1] - 7)) if wk else None)
        legs += p30 + p90

    log(f"  IBKR: ATM put IVs, {len(legs)} contracts")
    snap = _snapshot(ib, legs, mdt=2)

    def atm_iv(opts):
        best = None
        for o in opts:
            q = snap[id(o)]
            d, iv = _num(q.delta), _num(q.iv)
            if d is None or not iv or iv <= 0:
                continue
            score = abs(abs(d) - 0.50)
            if best is None or score < best[0]:
                best = (score, iv)
        return best[1] if best else None

    for t, p in plan.items():
        iv30, iv90 = atm_iv(p["p30"]), atm_iv(p["p90"])
        if not iv30 or not iv90:
            res[t] = {"tkr": t, "err": "no ATM IV"}; continue
        var_fwd = (iv90 ** 2 * p["t90"] - iv30 ** 2 * p["t30"]) / (p["t90"] - p["t30"])
        if var_fwd <= 0:
            res[t] = {"tkr": t, "err": "negative fwd var"}; continue
        res[t] = {"tkr": t, "spot": spot[t], "iv30": iv30, "iv90": iv90,
                  "t30": p["t30"], "t90": p["t90"], "fvr": math.sqrt(var_fwd) / iv30}

    # ---- ~7 DTE straddle quotes for the plausible names
    want = [t for t, r in res.items() if not r.get("err") and r["fvr"] >= quote_min_fvr]
    quotes, sq = {}, {}
    for t in want:
        p = plan[t]
        if not p["wk"]:
            quotes[t] = None; continue
        e, _ = p["wk"]
        ch = p["ch"]
        sq[t] = [Option(t, e, k, r, "SMART", tradingClass=ch.tradingClass, multiplier=ch.multiplier)
                 for k in p["ks"] for r in "CP"]
    log(f"  IBKR: straddle quotes for {len(sq)} names (FVR >= {quote_min_fvr})")
    snap_q = _snapshot(ib, [o for v in sq.values() for o in v], mdt=2)

    chosen = {}
    for t, opts in sq.items():
        pick = {}
        for right in "CP":
            best = None
            for o in (o for o in opts if o.right == right):
                d = _num(snap_q[id(o)].delta)
                if d is None:
                    continue
                score = abs(abs(d) - 0.50)
                if best is None or score < best[0]:
                    best = (score, o)
            if best:
                pick[right] = best[1]
        if len(pick) == 2:
            chosen[t] = pick
        else:
            quotes[t] = None

    snap_oi = _snapshot(ib, [o for pk in chosen.values() for o in pk.values()], mdt=1,
                        generic="101", wait=OI_WAIT_S)
    for t, pk in chosen.items():
        dte = plan[t]["wk"][1]
        cost, vals, bad = 0.0, [], False
        for right, o in pk.items():
            q = snap_q[id(o)]
            bid, ask = _num(q.bid) or 0, _num(q.ask) or 0
            if bid <= 0 or ask <= 0:
                bad = True; break
            mid = (bid + ask) / 2
            cost += mid
            oq = snap_oi[id(o)]
            oi = _num(oq.call_oi if right == "C" else oq.put_oi)
            vals.append(((ask - bid) / mid * 100, oi))
        if bad:
            quotes[t] = {"dte": dte, "bad": True}; continue
        ois = [v[1] for v in vals]
        quotes[t] = {"dte": dte, "cost": cost, "ba": max(v[0] for v in vals),
                     "oi": min(ois) if all(x is not None for x in ois) else None,
                     "strikes": f"{pk['C'].strike:g}C/{pk['P'].strike:g}P"}
    return [res[t] for t in tickers if t in res], quotes
