"""Reconcile Tito's own Setup_Type / Days_In_Trade labels against my A/B/C/D calls.

Tito's 4 labels map to my 4 archetypes:  Breakout->A, Earnings->B, Exhaustion->C, Catalyst->D.
Print the agreement table + where they diverge, and summarize Days_In_Trade by setup (the
open 'how long does he hold / exit' question -- now answered by his own data).
"""
import csv, statistics as st

SRC = "data/studies/Adhikary/Adhikary_Options.csv"

# my archetype call per trade Number (from the mining)
MINE = {1:"A",2:"B",3:"ambig",4:"B",5:"D",6:"C",7:"A",8:"C",9:"B",10:"A",
        11:"A",12:"A",13:"A",14:"A",15:"A",16:"D",17:"B",18:"D",19:"A",20:"A(loss)"}
TITO2MINE = {"Breakout":"A","Earnings":"B","Exhaustion":"C","Catalyst":"D"}

rows = []
with open(SRC, encoding="utf-8-sig") as f:
    for r in csv.DictReader(f):
        r = { (k or "").strip(): (v or "").strip() for k,v in r.items() }
        rows.append(r)

print(f"{'#':>2} {'Ticker':6} {'Tito Setup':11} {'Days':>4}  {'Tito→':5} {'Mine':6} {'agree?'}")
agree = 0; diverge = []
for r in rows:
    n=int(r["Number"]); tito=r["Setup_Type"]; days=r["Days_In_Trade"]
    tmap=TITO2MINE.get(tito,"?"); mine=MINE[n]
    ok = (mine==tmap) or (mine in ("A(loss)",) and tmap=="A")
    if ok: agree+=1
    else: diverge.append((n,r["Ticker"],tito,tmap,mine))
    print(f"{n:>2} {r['Ticker']:6} {tito:11} {days:>4}  {tmap:5} {mine:6} {'✓' if ok else '✗'}")

print(f"\nAgreement: {agree}/{len(rows)} on the A/B/C/D mapping")
print("Divergences (Tito's label wins — it's ground truth):")
for n,tk,tito,tmap,mine in diverge:
    print(f"  #{n} {tk}: Tito={tito}({tmap})  vs  mine={mine}")

print("\nDays_In_Trade by Tito Setup_Type (the hold/exit signature):")
bys={}
for r in rows:
    bys.setdefault(r["Setup_Type"],[]).append(int(r["Days_In_Trade"]))
for s,ds in sorted(bys.items()):
    print(f"  {s:11}: n={len(ds)}  days {sorted(ds)}  median {st.median(ds):.0f}  mean {st.mean(ds):.1f}")
