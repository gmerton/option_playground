#!/usr/bin/env python3
"""Journal page for the certified 12-1 momentum sleeve: data/journal/momentum/index.html.

Pure renderer (no DB, no API): reads data/studies/momentum_monthly_2026-10-02.csv, the month-by-month series of the
PRIMARY cell of run_momentum_portfolio.py (top decile 12-1, survivorship-free chain_spot, 10 bp/side), regenerated
2026-10-02 from the same cached panel (excess +0.668pp/mo, matching the certified run). Safe to re-run; the site is
published by deploy_trade_journal.sh.

Usage: .venv/bin/python3 run_momentum_journal_page.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parent
SRC = REPO / "data/studies/momentum_monthly_2026-10-02.csv"
OUT = REPO / "data/journal/momentum/index.html"

HEAD = r"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>12-1 Momentum Backtest</title>
<style>
:root{
  --bg:#f7f8fa; --panel:#ffffff; --rule:#e1e4ea; --fg:#1a1d24; --muted:#6b7280; --accent:#3f6fd8;
  --pos:#157a4d; --neg:#c23b3b;
  /* series: four distinct hues, the strategy darkest and thickest */
  --dec:#0a7a4f; --qui:#7b3fc4; --ew:#e0730f; --spy:#2563eb;
  --body:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; --mono:ui-monospace,SFMono-Regular,Menlo,monospace;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 var(--body)}
a{color:var(--accent);text-decoration:none} .crumb{margin:0 0 10px;font-size:13px}
.wrap{max-width:960px;margin:0 auto;padding-inline:20px;padding-block:32px 56px;display:grid;gap:28px}
h1{font:600 clamp(24px,4vw,30px)/1.2 var(--body);margin:0;text-wrap:balance}
h2{font:600 12.5px/1 var(--body);letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0 0 12px}
.lede{color:var(--muted);max-width:68ch;margin:8px 0 0}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;background:var(--rule);border:1px solid var(--rule);border-radius:10px;overflow:hidden}
.stat{background:var(--panel);padding:14px 16px}
.stat b{display:block;font:600 22px/1.2 var(--mono);font-variant-numeric:tabular-nums}
.stat span{font-size:12.5px;color:var(--muted)}
.card{background:var(--panel);border:1px solid var(--rule);border-radius:10px;padding:18px;min-width:0}
.legend{display:flex;flex-wrap:wrap;gap:16px;font-size:13px;margin-bottom:8px}
.legend i{display:inline-block;width:16px;height:4px;border-radius:2px;vertical-align:middle;margin-right:6px}
svg{display:block;width:100%;height:auto}
svg text{fill:var(--muted);font:11px var(--mono)}
.tbl{overflow-x:auto}
table{border-collapse:collapse;width:100%;font:13px var(--mono);font-variant-numeric:tabular-nums}
th,td{padding:6px 10px;text-align:right;border-bottom:1px solid var(--rule);white-space:nowrap}
th{font:600 12px var(--body);color:var(--muted)}
th:first-child,td:first-child{text-align:left}
td.p{color:var(--pos)} td.n{color:var(--neg)}
tfoot td{font-weight:600;border-top:2px solid var(--rule)}
ul{margin:0;padding-left:20px;max-width:72ch;display:grid;gap:6px}
.foot{color:var(--muted);font-size:12.5px}
.tip{position:fixed;pointer-events:none;background:var(--panel);border:1px solid var(--rule);border-radius:6px;padding:6px 9px;font:12px var(--mono);box-shadow:0 2px 8px rgba(0,0,0,.12)}
</style>
"""

BODY = r"""<div class="wrap">
<header>
<p class="crumb"><a href="../index.html">&larr; Journal home</a></p>
<h1>12-1 Momentum, 2011–2026</h1>
<p class="lede">Each month-end, buy the top 10% of optionable stocks by their return from 12 months ago to 1 month ago, equal weight, and hold one month. The universe is survivorship-free (it includes names that later delisted), and costs are 10 bp per side on turnover. 180 months, Feb 2011 to Jan 2026, about 84 names held out of about 837. All series are price return.</p>
</header>
<section class="stats" id="stats"></section>
<section class="card">
<h2>Growth of $1 (log scale)</h2>
<div class="legend"><span><i style="background:var(--dec)"></i>Top decile (the strategy)</span><span><i style="background:var(--qui)"></i>Top quintile</span><span><i style="background:var(--ew)"></i>Equal-weight universe (benchmark)</span><span><i style="background:var(--spy)"></i>SPY</span></div>
<div id="eq"></div>
<h2 style="margin-top:18px">Drawdown, top decile vs SPY</h2>
<div id="dd"></div>
</section>
<section class="card">
<h2>Calendar-year returns</h2>
<div class="tbl"><table id="yr"></table></div>
</section>
<section>
<h2>How to read it</h2>
<ul>
<li>The certified claim is the excess over the equal-weight universe: <b>+0.67 pp a month, Newey-West t 2.93</b>, positive in both halves (+0.38 / +0.92) and in 12 of 16 years. It passed the replication bar on 2026-09-30.</li>
<li>Against SPY it earns more in total but takes more risk: about 23% volatility vs 14%, and a lower Sharpe ratio (0.87 vs 1.00). The edge is over owning the same universe, not a better risk-adjusted index.</li>
<li>Bad stretches come from momentum reversals: Sep 2019 (−12.2 pp vs the universe), Jan 2023 (−9.1), Mar 2021, Nov 2022. The losing years vs the universe were 2011, 2016, 2021 and 2023.</li>
<li>A SPY &gt; 200-day filter made it worse (excess +0.24 pp, t 0.91), so it is not used.</li>
<li>This is a backtest. The live lockbox started with the 2026-09-30 formation.</li>
</ul>
</section>
</div>
<div class="tip" id="tip" hidden></div>
"""

TAIL = r"""const S={d:{k:'d',c:'--dec',n:'Top decile'},q:{k:'q',c:'--qui',n:'Top quintile'},e:{k:'e',c:'--ew',n:'EW universe'},s:{k:'s',c:'--spy',n:'SPY'}};
const N=D.m.length, keys=['e','s','q','d'];
const cum={};keys.forEach(k=>{let v=1;cum[k]=[1].concat(D[k].map(r=>v*=1+r));});
const months=[ '2011-01' ].concat(D.m);
function stat(k){const r=D[k],n=r.length,mu=r.reduce((a,b)=>a+b)/n,sd=Math.sqrt(r.reduce((a,b)=>a+(b-mu)**2,0)/(n-1));
 let pk=1,dd=0;cum[k].forEach(v=>{pk=Math.max(pk,v);dd=Math.max(dd,1-v/pk)});
 return{cagr:Math.pow(cum[k][n],12/n)-1,vol:sd*Math.sqrt(12),sh:mu/sd*Math.sqrt(12),dd,fin:cum[k][n]};}
const st={};keys.forEach(k=>st[k]=stat(k));
const pct=(x,d=1)=>(x*100).toFixed(d)+'%';
document.getElementById('stats').innerHTML=[
 ['$'+st.d.fin.toFixed(2),'$1 became (SPY $'+st.s.fin.toFixed(2)+')'],
 [pct(st.d.cagr),'CAGR (SPY '+pct(st.s.cagr)+', universe '+pct(st.e.cagr)+')'],
 ['+0.67 pp','excess per month over the universe, t 2.93'],
 [pct(st.d.dd),'max drawdown (SPY '+pct(st.s.dd)+')'],
 [st.d.sh.toFixed(2),'Sharpe (SPY '+st.s.sh.toFixed(2)+')']
].map(([b,s])=>`<div class="stat"><b>${b}</b><span>${s}</span></div>`).join('');
const css=v=>getComputedStyle(document.documentElement).getPropertyValue(v).trim();
function draw(){
 const W=900,H=340,L=46,R=12,T=10,B=24,x=i=>L+(W-L-R)*i/N;
 const lo=Math.log(0.8),hi=Math.log(16),y=v=>T+(H-T-B)*(1-(Math.log(v)-lo)/(hi-lo));
 let g='';[1,2,4,8,16].forEach(v=>{g+=`<line x1="${L}" x2="${W-R}" y1="${y(v)}" y2="${y(v)}" stroke="${css('--rule')}"/><text x="${L-6}" y="${y(v)+4}" text-anchor="end">$${v}</text>`});
 months.forEach((m,i)=>{if(m.endsWith('-01')&&+m.slice(0,4)%2===1)g+=`<text x="${x(i)}" y="${H-6}" text-anchor="middle">${m.slice(0,4)}</text>`});
 keys.forEach(k=>{g+=`<polyline fill="none" stroke="${css(S[k].c)}" stroke-width="${k==='d'?2.6:1.7}" points="${cum[k].map((v,i)=>x(i).toFixed(1)+','+y(v).toFixed(1)).join(' ')}"/>`});
 g+=`<line id="hx" y1="${T}" y2="${H-B}" stroke="${css('--muted')}" stroke-dasharray="3 3" visibility="hidden"/>`;
 document.getElementById('eq').innerHTML=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Growth of one dollar, log scale">${g}<rect id="hit" x="${L}" y="${T}" width="${W-L-R}" height="${H-T-B}" fill="transparent"/></svg>`;
 // drawdown
 const H2=150,y2=v=>T+(H2-T-B)*(v/0.35);let h='';
 [0,.1,.2,.3].forEach(v=>{h+=`<line x1="${L}" x2="${W-R}" y1="${y2(v)}" y2="${y2(v)}" stroke="${css('--rule')}"/><text x="${L-6}" y="${y2(v)+4}" text-anchor="end">${v?'−'+v*100+'%':'0'}</text>`});
 months.forEach((m,i)=>{if(m.endsWith('-01')&&+m.slice(0,4)%2===1)h+=`<text x="${x(i)}" y="${H2-6}" text-anchor="middle">${m.slice(0,4)}</text>`});
 ['s','d'].forEach(k=>{let pk=1;const p=cum[k].map((v,i)=>{pk=Math.max(pk,v);return x(i).toFixed(1)+','+y2(1-v/pk).toFixed(1)});
  h+=k==='d'?`<polygon fill="${css('--dec')}" fill-opacity=".18" points="${x(0)},${y2(0)} ${p.join(' ')} ${x(N)},${y2(0)}"/><polyline fill="none" stroke="${css('--dec')}" stroke-width="1.6" points="${p.join(' ')}"/>`
   :`<polyline fill="none" stroke="${css('--spy')}" stroke-width="1.3" points="${p.join(' ')}"/>`});
 document.getElementById('dd').innerHTML=`<svg viewBox="0 0 ${W} ${H2}" role="img" aria-label="Drawdown">${h}</svg>`;
 const svg=document.querySelector('#eq svg'),tip=document.getElementById('tip'),hx=document.getElementById('hx');
 svg.addEventListener('mousemove',ev=>{const r=svg.getBoundingClientRect(),px=(ev.clientX-r.left)*W/r.width,i=Math.max(0,Math.min(N,Math.round((px-L)/(W-L-R)*N)));
  hx.setAttribute('x1',x(i));hx.setAttribute('x2',x(i));hx.setAttribute('visibility','visible');
  tip.innerHTML=`<b>${months[i]}</b><br>`+['d','q','e','s'].map(k=>`${S[k].n}: $${cum[k][i].toFixed(2)}`).join('<br>');
  tip.hidden=false;tip.style.left=Math.min(ev.clientX+14,innerWidth-170)+'px';tip.style.top=(ev.clientY+14)+'px';});
 svg.addEventListener('mouseleave',()=>{tip.hidden=true;hx.setAttribute('visibility','hidden')});
}
draw();
// yearly table
const yrs={};D.m.forEach((m,i)=>{const y=m.slice(0,4);yrs[y]=yrs[y]||{d:1,q:1,e:1,s:1};keys.forEach(k=>yrs[y][k]*=1+D[k][i])});
const c=v=>`<td class="${v>=0?'p':'n'}">${v>=0?'+':''}${(v*100).toFixed(1)}%</td>`;
let t='<thead><tr><th>Year</th><th>Top decile</th><th>Top quintile</th><th>EW universe</th><th>SPY</th><th>Decile − universe</th></tr></thead><tbody>';
Object.entries(yrs).forEach(([y,o])=>{const a={d:o.d-1,q:o.q-1,e:o.e-1,s:o.s-1};t+=`<tr><td>${y}${y==='2011'?' (Feb–Dec)':y==='2026'?' (Jan)':''}</td>${c(a.d)}${c(a.q)}${c(a.e)}${c(a.s)}${c(a.d-a.e)}</tr>`});
t+=`</tbody><tfoot><tr><td>CAGR</td>${c(st.d.cagr)}${c(st.q.cagr)}${c(st.e.cagr)}${c(st.s.cagr)}${c(st.d.cagr-st.e.cagr)}</tr></tfoot>`;
document.getElementById('yr').innerHTML=t;
</script>
"""


def main() -> int:
    d = pd.read_csv(SRC)
    data = dict(m=d.month.tolist(), d=d.top_decile.round(5).tolist(), q=d.top_quintile.round(5).tolist(),
                e=d.ew_universe.round(5).tolist(), s=d.spy.round(5).tolist())
    foot = (f'<p class="foot">Source: <code>{SRC.relative_to(REPO)}</code> (study: '
            '<code>data/studies/momentum_portfolio_2026-09-25.md</code>). Rendered by <code>run_momentum_journal_page.py</code>.</p>')
    page = HEAD + BODY.replace("</section>\n</div>", "</section>\n" + foot + "\n</div>") \
        + "<script>\nconst D=" + json.dumps(data, separators=(",", ":")) + ";\n" + TAIL
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page)
    print(f"wrote {OUT.relative_to(REPO)} ({len(d)} months, {len(page):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
