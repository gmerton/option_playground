"""Tito's actual Return column is now ground truth. Compare to my two estimators:
  - at-expiry intrinsic (matched strike in Adhikary_results.csv)
  - exit-date close (for the 6 early-exit trades)
to (a) validate strike inference where he held to expiry, (b) quantify how much his
intraday exit execution adds where he didn't. Then aggregate stats + the survivorship caveat.
"""
import csv, datetime as dt
import pandas as pd

CSV = "data/studies/Adhikary/Adhikary_Options.csv"
RES = "data/studies/Adhikary/Adhikary_results.csv"

# my exit-date-close estimates for the 6 early exits (from scratch_adhikary_exits.py)
MY_EXIT = {"ARM":368,"BRKB":298,"GEV":672,"BABA":1343,"DJT":18,"COST":117}


def parse(d): return dt.datetime.strptime(d, "%m/%d/%y").date()


def main():
    res = pd.read_csv(RES)
    rows = []
    with open(CSV, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            r = {(k or "").strip(): (v or "").strip() for k, v in r.items()}
            n = int(r["Number"]); tkr = r["Ticker"]; ep = float(r["Entry_Price"])
            dte = (parse(r["Expiration"]) - parse(r["Entry Date"])).days
            days_in = int(r["Days_In_Trade"]); tito = float(r["Return"])
            sub = res[res["number"] == n]
            at_exp = None
            if not sub.empty:
                i = (sub["open_entry"] - ep).abs().idxmin()
                at_exp = round(sub.loc[i, "return_pct"], 0)
            early = days_in < dte - 1
            rows.append({"n": n, "ticker": tkr, "setup": r["Setup_Type"],
                         "tito_ret": tito, "my_at_exp": at_exp,
                         "my_exit": MY_EXIT.get(tkr) if early else None,
                         "exit_type": "early" if early else "held"})
    df = pd.DataFrame(rows)
    print(f"{'#':>2} {'ticker':6} {'setup':10} {'exit':6} {'TITO':>7} {'my_at_exp':>10} {'my_exit':>8}  delta")
    for r in df.itertuples():
        best = r.my_exit if r.my_exit is not None else r.my_at_exp
        d = f"{r.tito_ret-best:+.0f}" if best is not None else "--"
        print(f"{r.n:>2} {r.ticker:6} {r.setup:10} {r.exit_type:6} {r.tito_ret:7.0f} "
              f"{('' if r.my_at_exp is None else f'{r.my_at_exp:.0f}'):>10} "
              f"{('' if r.my_exit is None else f'{r.my_exit:.0f}'):>8}  {d}")

    held = df[df.exit_type == "held"].dropna(subset=["my_at_exp"])
    print(f"\nHELD-to-expiry trades — validate strike inference (Tito vs my at-expiry intrinsic):")
    err = (held.tito_ret - held.my_at_exp).abs() / held.tito_ret * 100
    print(f"  n={len(held)}, median |error| = {err.median():.0f}% of Tito's return  (low = inference good)")

    early = df[df.exit_type == "early"]
    print(f"\nEARLY-exit trades — how much his INTRADAY exit beat my exit-close estimate:")
    for r in early.itertuples():
        print(f"  {r.ticker:5}: Tito {r.tito_ret:.0f}%  vs my exit-close {r.my_exit:.0f}%  "
              f"(at-expiry {r.my_at_exp:.0f}%)")

    print(f"\n⚠ AGGREGATE (this is a CURATED 'best trades' list — survivorship-biased, NOT expectancy):")
    print(f"  n={len(df)}  wins={int((df.tito_ret>0).sum())}/{len(df)}  "
          f"median {df.tito_ret.median():.0f}%  mean {df.tito_ret.mean():.0f}%  "
          f"range {df.tito_ret.min():.0f}–{df.tito_ret.max():.0f}%")
    print("  By setup (median return):")
    for s, g in df.groupby("setup"):
        print(f"    {s:11} n={len(g)}  median {g.tito_ret.median():.0f}%")
    df.to_csv("data/studies/Adhikary/Adhikary_returns_compare.csv", index=False)


if __name__ == "__main__":
    main()
