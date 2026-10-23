"""Check every stated price/stop in the Ariel Discord ledger against that session's UNADJUSTED bar; propose fixes.

Usage: check_ariel_discord_prices.py [--channel short]   (short channel files carry a short_ prefix)
Reads  data/ariel_hernandez/discord/actions.csv (built by build_ariel_discord_ledger.py)
       data/cache/polygon_daily_raw/<SYM>.parquet (run_fetch_daily_raw_polygon.py)
Writes data/ariel_hernandez/discord/price_check.csv   one row per stated number: verdict + candidate fix
       data/ariel_hernandez/discord/price_fixes.csv   only the numbers to change (hand overrides: price_overrides.csv)

Window a number must sit in:
  regular hours (09:30-16:00 ET)  the session's [low, high], +-0.5%
  pre-market / after hours / weekend  the nearest session's [low, high] widened to +-8% around it
  stop_price                      [0.5x, 1.5x] of the session close (a stop is a level, not a fill)
A number outside its window is a typo candidate. Candidates = one keystroke away: delete, insert or replace a
digit, swap two adjacent digits, or move the decimal point. A fix is applied automatically only when exactly one
candidate lands in the window; otherwise it is listed as ambiguous for a hand decision.
"""
import csv
from datetime import datetime, time
from pathlib import Path
import pandas as pd

D = Path("data/ariel_hernandez/discord")
BARS = Path("data/cache/polygon_daily_raw")
REG_TOL, EXT_TOL, NEAR = 0.005, 0.08, 0.03


def bars(sym, _c={}):
    if sym not in _c:
        f = BARS / f"{sym}.parquet"
        _c[sym] = pd.read_parquet(f).set_index("date") if f.exists() else None
    return _c[sym]


def window(sym, ts_et, kind):
    b = bars(sym)
    if b is None:
        return None
    dt = datetime.strptime(ts_et, "%Y-%m-%d %H:%M:%S")
    d = dt.strftime("%Y-%m-%d")
    regular = d in b.index and time(9, 30) <= dt.time() < time(16, 0)
    if d in b.index:
        bar = b.loc[d]
    else:  # weekend/holiday post: the last session before it
        prior = b.index[b.index < d]
        if not len(prior):
            return None
        bar = b.loc[prior[-1]]
    if kind == "stop":
        return bar.close * 0.5, bar.close * 1.5, bar, "stop"
    if regular:
        return bar.low * (1 - REG_TOL), bar.high * (1 + REG_TOL), bar, "regular"
    lo, hi = bar.low, bar.high
    if d in b.index and dt.time() >= time(16, 0):  # after hours (earnings): the next session's gap is real
        nxt = b.index[b.index > d]
        if len(nxt):
            lo, hi = min(lo, b.loc[nxt[0]].low), max(hi, b.loc[nxt[0]].high)
    return lo * (1 - EXT_TOL), hi * (1 + EXT_TOL), bar, "extended"


def candidates(x):
    s = f"{x:.4f}".rstrip("0").rstrip(".")
    digits = "0123456789"
    out = set()
    for i in range(len(s)):
        out.add(s[:i] + s[i + 1:])                                  # delete
        for c in digits:
            out.add(s[:i] + c + s[i:])                              # insert
            out.add(s[:i] + c + s[i + 1:])                          # replace
        if i + 1 < len(s):
            out.add(s[:i] + s[i + 1] + s[i] + s[i + 2:])            # swap
    out.add(s + "0")
    plain = s.replace(".", "")
    for i in range(1, len(plain) + 1):                              # move the decimal point
        out.add(plain[:i] + "." + plain[i:])
    vals = set()
    for c in out:
        if c.count(".") <= 1 and c.strip(".") and not c.startswith("."):
            try:
                v = float(c)
            except ValueError:
                continue
            if v > 0 and v != x:
                vals.add(round(v, 4))
    return vals


def main():
    import sys
    P = "short_" if "--channel=short" in sys.argv or sys.argv[-2:] == ["--channel", "short"] else ""
    a = pd.read_csv(D / f"{P}actions.csv", dtype={"msg_ids": str})
    overrides = {}
    if (D / f"{P}price_overrides.csv").exists():
        for r in csv.DictReader(open(D / f"{P}price_overrides.csv")):
            overrides[(r["msg_id"], r["field"])] = r
    rows = []
    for _, r in a.iterrows():
        mid = r.msg_ids.split()[0]
        for field, kind in (("price", "price"), ("stop_price", "stop")):
            x = r.get(f"{field}_stated", r[field])  # always check what he wrote, not a prior fix
            if pd.isna(x):
                continue
            rec = {"msg_id": mid, "ts_et": r.ts_et, "ticker": r.ticker, "action": r.action, "field": field,
                   "stated": x, "quote": r.quote}
            w = window(r.ticker, r.ts_et, kind)
            if (mid, field) in overrides:
                o = overrides[(mid, field)]
                rec.update(verdict="override", corrected=o["corrected"] or None, note=o["reason"])
            elif w is None:
                rec.update(verdict="no_bars")
            else:
                lo, hi, bar, basis = w
                rec.update(session_low=round(bar.low, 4), session_high=round(bar.high, 4),
                           session_close=round(bar.close, 4), basis=basis)
                if lo <= x <= hi:
                    rec.update(verdict="ok")
                else:
                    fits = sorted(c for c in candidates(x) if lo <= c <= hi)
                    if len(fits) == 1:
                        rec.update(verdict="fixed", corrected=fits[0])
                    elif fits:
                        near = [c for c in fits if abs(c / bar.close - 1) <= NEAR]
                        if len(near) == 1:
                            rec.update(verdict="fixed", corrected=near[0],
                                       note=f"only candidate within {NEAR:.0%} of the close")
                        else:
                            rec.update(verdict="ambiguous", note="candidates " + " ".join(map(str, fits[:8])))
                    else:
                        rec.update(verdict="no_fix", note=f"off by {x / bar.close - 1:+.1%} vs close")
            rows.append(rec)
    out = pd.DataFrame(rows)
    for c in ("corrected", "note", "session_low", "session_high"):
        if c not in out:
            out[c] = None
    out.to_csv(D / f"{P}price_check.csv", index=False)
    fx = out[(out.verdict == "fixed") | (out.verdict == "override")]  # an override with no value blanks the number
    fx[["msg_id", "ticker", "action", "field", "stated", "corrected", "verdict"]].to_csv(D / f"{P}price_fixes.csv", index=False)
    print(out.verdict.value_counts().to_string())
    flagged = out[~out.verdict.isin(["ok"])]
    pd.set_option("display.width", 250, "display.max_colwidth", 60, "display.max_rows", 500)
    print(flagged[["ts_et", "ticker", "action", "field", "stated", "verdict", "corrected", "session_low",
                   "session_high", "note", "quote"]].to_string(index=False))


if __name__ == "__main__":
    main()
