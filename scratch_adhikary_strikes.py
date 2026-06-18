"""Infer the STRIKE Tito bought from his recorded Entry_Price (option premium), using the
per-strike entry prices already in Adhikary_results.csv. Yields his moneyness/delta preference
(recipe #7 'Vehicle') and the realized option return — flagging trades he exited BEFORE expiry
(Days_In_Trade < DTE), where the at-expiration return in the results file is NOT his actual exit.
"""
import csv, datetime as dt
import pandas as pd

CSV = "data/studies/Adhikary/Adhikary_Options.csv"
RES = "data/studies/Adhikary/Adhikary_results.csv"


def parse(d): return dt.datetime.strptime(d, "%m/%d/%y").date()


def load_trades():
    rows = []
    with open(CSV, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            r = {(k or "").strip(): (v or "").strip() for k, v in r.items()}
            rows.append({
                "n": int(r["Number"]), "ticker": r["Ticker"], "cp": r["Call / Put"],
                "entry": parse(r["Entry Date"]), "exp": parse(r["Expiration"]),
                "days_in": int(r["Days_In_Trade"]), "setup": r["Setup_Type"],
                "entry_px": float(r["Entry_Price"]),
            })
    return rows


def main():
    trades = load_trades()
    res = pd.read_csv(RES)
    out = []
    for t in trades:
        dte = (t["exp"] - t["entry"]).days
        sub = res[res["number"] == t["n"]]
        if sub.empty:
            out.append({**_base(t, dte), "note": "no results row (BTC excluded)"}); continue
        # strike whose entry-day option open is closest to Tito's recorded premium
        i = (sub["open_entry"] - t["entry_px"]).abs().idxmin()
        m = sub.loc[i]
        early = t["days_in"] < dte - 1
        out.append({
            **_base(t, dte),
            "infer_strike": m["strike"], "matched_open": round(m["open_entry"], 2),
            "delta": m["delta_entry"],
            "ret_at_exp_%": round(m["return_pct"], 0),
            "exit_basis": "EARLY (needs exit-date px)" if early else "~held to expiry",
        })
    df = pd.DataFrame(out)
    cols = ["n","ticker","cp","setup","entry_px","matched_open","infer_strike","delta",
            "dte","days_in","exit_basis","ret_at_exp_%"]
    with pd.option_context("display.width", 220, "display.max_columns", None, "display.max_rows", None):
        print(df[cols].to_string(index=False))
    d = df.dropna(subset=["delta"])
    print(f"\nMoneyness / delta preference (recipe #7 'Vehicle'):")
    print(f"  delta range {d['delta'].min():.2f}–{d['delta'].max():.2f}, median {d['delta'].median():.2f}")
    print(f"  calls only: {d[d.cp=='C']['delta'].median():.2f} median delta")
    held = df[df["exit_basis"] == "~held to expiry"].dropna(subset=["ret_at_exp_%"])
    print(f"\nReturns for trades ~held to expiry ({len(held)}): "
          f"median {held['ret_at_exp_%'].median():+.0f}%, "
          f"win {int((held['ret_at_exp_%']>0).sum())}/{len(held)}")
    early = df[df["exit_basis"].astype(str).str.startswith("EARLY")]
    print(f"⚠ {len(early)} trades exited EARLY (Days_In_Trade < DTE) — at-expiry return is NOT actual exit:")
    print("   " + ", ".join(f"{r.ticker}({r.days_in}/{r.dte}d)" for r in early.itertuples()))
    df.to_csv("data/studies/Adhikary/Adhikary_inferred_strikes.csv", index=False)


def _base(t, dte):
    return {"n": t["n"], "ticker": t["ticker"], "cp": t["cp"], "setup": t["setup"],
            "entry_px": t["entry_px"], "dte": dte, "days_in": t["days_in"]}


if __name__ == "__main__":
    main()
