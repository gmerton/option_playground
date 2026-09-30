# Value Investors Club ideas (captured 2026-09-30)

Member write-ups from valueinvestorsclub.com. They were captured from Gabe's logged-in Chrome session, which has guest
access: ideas become visible 45 days after posting.

- `raw/` - the raw idea pages (`<idea_id>_<slug>.html`), the source of truth.
- `ideas/` - one markdown file per idea (`<post_date>_<ticker>_<idea_id>.md`): the header stats, the description, and the catalyst.
- `index.csv` - one row per idea: ticker, long/short, post date, author, price/mkt cap/TEV at posting, URL.
- `pending.txt` - ideas that were listed but not captured. VIC's access limit stopped the capture after 15 pages
  ("please wait 24 hours").

Rebuild the parsed files with `PYTHONPATH=src .venv/bin/python3 run_vic_parse.py`. It is idempotent and skips any
page that is not an idea page (for example an access-limit stub).

**Capture method.** In a Claude-in-Chrome tab on the /ideas page, a small script fetches each idea URL on the same
origin (so it uses the session cookie). It then POSTs the HTML to a throwaway receiver on `127.0.0.1:8765` that
writes into `raw/`. Chrome asks once to allow valueinvestorsclub.com local-network access. Fetches are 1.5 s
apart. **Respect the access limit.** Take roughly 15 pages per day and do not work around it.

These are ideas to research, not evidence. A VIC write-up is a thesis. Any trading use still goes through the house
research rules (a control, real fills, a pre-registered bar).
