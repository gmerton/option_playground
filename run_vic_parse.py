"""Parse saved Value Investors Club idea pages into markdown + an index.

Input:  data/vic/raw/<idea_id>_<slug>.html  (raw pages captured from a logged-in browser session;
        see data/vic/README.md for how they are collected)
Output: data/vic/ideas/<post_date>_<ticker>_<idea_id>.md  and  data/vic/index.csv

Idempotent: re-running rewrites every output from the raw pages.
"""
import csv
import re
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent / "data" / "vic"
RAW, OUT = ROOT / "raw", ROOT / "ideas"

STAT_LABELS = {
    "Price:": "price", "Shares Out. (in M):": "shares_out_m", "Market Cap (in $M):": "mkt_cap_m",
    "Net Debt (in $M):": "net_debt_m", "TEV (in $M):": "tev_m",
}


def text_block(el):
    """Readable text: one line per block element, blank line between paragraphs."""
    if el is None:
        return ""
    for br in el.find_all("br"):
        br.replace_with("\n")
    for h in el.find_all(["h1", "h2", "h3", "h4"]):
        h.insert_before("\n\n### ")
    for li in el.find_all("li"):
        li.insert_before("\n- ")
    for tr in el.find_all("tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
        tr.replace_with("\n| " + " | ".join(cells) + " |")
    for p in el.find_all(["p", "div"]):
        p.insert_after("\n\n")
    txt = el.get_text()
    txt = re.sub(r"[ \t\xa0]+", " ", txt)
    txt = re.sub(r" *\n *", "\n", txt)
    return re.sub(r"\n{3,}", "\n\n", txt).strip()


def parse(path):
    soup = BeautifulSoup(path.read_text(errors="replace"), "html.parser")
    idea_id = path.stem.split("_", 1)[0]
    name_el = soup.select_one(".idea_name .vich1")
    ticker_el = name_el.find("span") if name_el else None
    ticker = ticker_el.get_text(strip=True) if ticker_el else ""
    if ticker_el:
        ticker_el.extract()
    company = name_el.get_text(" ", strip=True) if name_el else path.stem
    by = soup.select_one(".idea_by")
    date_txt = by.find("div").get_text(" ", strip=True) if by else ""
    m = re.match(r"(\w+ \d{1,2}, \d{4})", date_txt)
    post_date = datetime.strptime(m.group(1), "%B %d, %Y").date().isoformat() if m else ""
    author_el = by.select_one("a.display_name") if by else None
    header = soup.select_one(".idea_name").find_parent("div", class_="row") if name_el else soup
    side = "short" if header.select_one(".label-short") else "long"

    stats = {}
    for tr in header.find_all("tr"):
        tds = [td.get_text(strip=True) for td in tr.find_all("td")]
        if tds and tds[0] in STAT_LABELS and len(tds) > 2:
            stats[STAT_LABELS[tds[0]]] = tds[2]

    desc = soup.select_one("#description")
    catalyst = ""
    if desc:
        cat_h = desc.find("h4", string=re.compile("Catalyst"))
        if cat_h:
            parts = []
            for sib in list(cat_h.find_next_siblings()):
                parts.append(text_block(sib))
                sib.extract()
            cat_h.extract()
            catalyst = "\n\n".join(p for p in parts if p)
    body = re.sub(r"^(### )?Description\s*", "", text_block(desc))
    return {
        "idea_id": idea_id, "ticker": ticker, "company": company, "side": side,
        "post_date": post_date, "author": author_el.get_text(strip=True) if author_el else "",
        **{k: stats.get(k, "") for k in STAT_LABELS.values()},
        "url": f"https://valueinvestorsclub.com/idea/{path.stem.split('_', 1)[1]}/{idea_id}",
        "chars": len(body), "_body": body, "_catalyst": catalyst,
    }


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(RAW.glob("*.html")):
        if 'class="idea_name"' not in path.read_text(errors="replace"):
            print(f"skip (not an idea page - access-limit stub?): {path.name}")
            continue
        r = parse(path)
        safe_tkr = re.sub(r"[^A-Za-z0-9.]", "", r["ticker"]) or "NA"
        md = OUT / f"{r['post_date']}_{safe_tkr}_{r['idea_id']}.md"
        md.write_text(
            f"# {r['company']} ({r['ticker']}) - {r['side'].upper()}\n\n"
            f"- Posted: {r['post_date']} by {r['author']}\n"
            f"- Price at post: {r['price']} | Mkt cap $M: {r['mkt_cap_m']} | TEV $M: {r['tev_m']}\n"
            f"- Source: {r['url']}\n\n## Description\n\n{r['_body']}\n\n## Catalyst\n\n{r['_catalyst']}\n"
        )
        r["file"] = md.name
        rows.append(r)
    rows.sort(key=lambda r: r["post_date"], reverse=True)
    cols = [k for k in rows[0] if not k.startswith("_")]
    with open(ROOT / "index.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} ideas -> {OUT}  (index: {ROOT / 'index.csv'})")


if __name__ == "__main__":
    main()
