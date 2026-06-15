#!/usr/bin/env python3
"""Web UI for the signal monitor: a live opportunities table.

A standalone aiohttp app (no new dependency -- aiohttp already ships with the
toolkit) that reads the shared SQLite signal store and renders a table. New
signals appear as new rows in real time via Server-Sent Events: the bot writes
to SQLite, this process polls for rows past the last id it streamed and pushes
them to every connected browser.

Decoupled from the monitor on purpose -- either side can restart without taking
the other down, which matters once the daily Gateway reset is in the mix.

  UI_HOST   bind address (default 127.0.0.1; set 0.0.0.0 in the container)
  UI_PORT   bind port    (default 8000)
  SIGNAL_DB shared store path (see signal_store)

Run:
  PYTHONPATH=src .venv/bin/python3 ibkr_bot/signal_ui.py
"""

from __future__ import annotations

import asyncio
import json
import os
import time

from aiohttp import web

import signal_store
import ui_auth

POLL_SECONDS = 1.5

# --- auth config (auth is OFF unless a password hash is provided) -----------
PASSWORD_HASH = os.environ.get("UI_PASSWORD_HASH", "")
SECRET = os.environ.get("UI_SECRET", "")
SESSION_TTL = int(os.environ.get("UI_SESSION_TTL", str(7 * 24 * 3600)))  # 7 days
COOKIE_NAME = "sigui_session"
# Behind Caddy the browser-facing hop is HTTPS; trust X-Forwarded-Proto, and
# allow an explicit override for local plain-http testing.
COOKIE_SECURE_DEFAULT = os.environ.get("UI_COOKIE_SECURE", "1") == "1"

# Brute-force throttle: lock an IP out after too many failures in a window.
_MAX_FAILS, _LOCKOUT_SECONDS = 6, 300
_fails: dict[str, list[float]] = {}


def auth_enabled() -> bool:
    return bool(PASSWORD_HASH and SECRET)

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Signal Monitor</title>
<style>
  :root { color-scheme: dark; }
  body { font: 14px/1.4 -apple-system, system-ui, sans-serif; margin: 0;
         background: #0f1115; color: #e6e6e6; }
  header { padding: 12px 18px; border-bottom: 1px solid #222;
           display: flex; align-items: center; gap: 12px; }
  h1 { font-size: 15px; margin: 0; font-weight: 600; }
  #status { font-size: 12px; padding: 2px 8px; border-radius: 10px;
            background: #333; color: #aaa; }
  #status.live { background: #14361f; color: #4ade80; }
  #status.down { background: #3a1414; color: #f87171; }
  #count { font-size: 12px; color: #888; margin-left: auto; }
  table { border-collapse: collapse; width: 100%; }
  th, td { text-align: left; padding: 8px 14px; border-bottom: 1px solid #1c1f26; }
  th { font-size: 11px; text-transform: uppercase; letter-spacing: .05em;
       color: #8a8f98; position: sticky; top: 0; background: #0f1115; }
  td.sym { font-weight: 600; }
  td.detail { color: #c2c7d0; font-variant-numeric: tabular-nums; }
  .tag { font-size: 11px; font-weight: 700; padding: 2px 7px; border-radius: 4px; }
  .tag.PHB { background: #14361f; color: #4ade80; }
  .tag.MFR { background: #3a2e10; color: #fbbf24; }
  .tag.EMA { background: #1e2530; color: #93c5fd; }
  tr.new td { animation: flash 1.6s ease-out; }
  @keyframes flash { from { background: #1d2b3a; } to { background: transparent; } }
  .empty { padding: 28px 18px; color: #666; }
  /* watchlist panel */
  #wl { border-bottom: 1px solid #222; background: #11141b; }
  .wl-bar { display: flex; align-items: center; gap: 10px; padding: 9px 18px; }
  .wl-bar .src { font-size: 12px; color: #8a8f98; }
  .wl-bar .src b { color: #e6e6e6; }
  .wl-bar button { margin-left: auto; background: #1e2530; color: #cbd5e1;
    border: 1px solid #2a3340; border-radius: 6px; padding: 4px 10px; cursor: pointer; font-size: 12px; }
  #wl-edit { padding: 4px 18px 16px; display: grid; gap: 6px; max-width: 760px; }
  #wl-edit[hidden] { display: none; }
  #wl-edit label { font-size: 11px; text-transform: uppercase; letter-spacing: .05em; color: #8a8f98; margin-top: 8px; }
  #wl-edit textarea { width: 100%; box-sizing: border-box; background: #0f1115;
    color: #e6e6e6; border: 1px solid #2a2f3a; border-radius: 6px; padding: 8px 10px;
    font: 13px ui-monospace, SFMono-Regular, Menlo, monospace; resize: vertical; }
  .wl-btns { display: flex; gap: 8px; }
  .wl-btns button { background: #2563eb; color: #fff; border: 0; border-radius: 6px;
    padding: 6px 12px; font-weight: 600; cursor: pointer; font-size: 13px; }
  .wl-btns button.alt { background: #1e2530; color: #cbd5e1; border: 1px solid #2a3340; }
  #wl-msg { font-size: 12px; color: #4ade80; min-height: 15px; }
  #wl-msg.err { color: #f87171; }
</style>
</head>
<body>
<header>
  <h1>Signal Monitor</h1>
  <span id="status">connecting…</span>
  <span id="count"></span>
</header>
<section id="wl">
  <div class="wl-bar">
    <span class="src">Watching <b id="wl-count">…</b> · source: <b id="wl-source">…</b></span>
    <button id="wl-toggle" type="button">Edit watchlist ▾</button>
  </div>
  <div id="wl-edit" hidden>
    <label for="wl-default">Default list (whitespace-separated)</label>
    <textarea id="wl-default" rows="3"></textarea>
    <div class="wl-btns">
      <button id="wl-save-default" type="button">Save default</button>
      <button id="wl-use-default" type="button" class="alt">Use default list</button>
    </div>
    <label for="wl-custom">Custom list (whitespace-separated)</label>
    <textarea id="wl-custom" rows="2" placeholder="e.g. TSLA NVDA AMD"></textarea>
    <div class="wl-btns">
      <button id="wl-apply-custom" type="button">Apply custom list</button>
    </div>
    <div id="wl-msg"></div>
  </div>
</section>
<table>
  <thead><tr><th>Time</th><th>Symbol</th><th>Pattern</th><th>Detail</th></tr></thead>
  <tbody id="rows"></tbody>
</table>
<div class="empty" id="empty">No signals yet — waiting for the next opportunity.</div>
<script>
  const tbody = document.getElementById('rows');
  const statusEl = document.getElementById('status');
  const countEl = document.getElementById('count');
  const emptyEl = document.getElementById('empty');
  let count = 0, maxId = MAXID_PLACEHOLDER;

  function esc(s){ const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }
  function addRow(r, isNew){
    emptyEl.style.display = 'none';
    const tr = document.createElement('tr');
    if (isNew) tr.className = 'new';
    tr.innerHTML =
      '<td>' + esc(r.ts) + '</td>' +
      '<td class="sym">' + esc(r.symbol) + '</td>' +
      '<td><span class="tag ' + esc(r.pattern) + '">' + esc(r.pattern) + '</span></td>' +
      '<td class="detail">' + esc(r.message) + '</td>';
    tbody.insertBefore(tr, tbody.firstChild);  // newest on top
    count++; countEl.textContent = count + ' signal' + (count === 1 ? '' : 's');
  }

  INITIAL_PLACEHOLDER.forEach(r => addRow(r, false));  // server sends newest-first

  function connect(){
    const es = new EventSource('/events?after=' + maxId);
    es.onopen = () => { statusEl.textContent = 'live'; statusEl.className = 'live'; };
    es.onmessage = e => { const r = JSON.parse(e.data); addRow(r, true); maxId = r.id; };
    es.onerror = () => { statusEl.textContent = 'reconnecting…'; statusEl.className = 'down';
                         es.close(); setTimeout(connect, 2000); };
  }
  connect();

  // --- watchlist panel ---
  const wlMsg = document.getElementById('wl-msg');
  function renderWL(w){
    document.getElementById('wl-count').textContent = w.active.length + ' ticker' + (w.active.length===1?'':'s');
    document.getElementById('wl-source').textContent = w.source;
    document.getElementById('wl-default').value = w.default.join(' ');
    if (w.source === 'custom') document.getElementById('wl-custom').value = w.active.join(' ');
  }
  function wlSay(text, isErr){ wlMsg.textContent = text; wlMsg.className = isErr ? 'err' : ''; }
  async function wlPost(url, tickers){
    const opts = { method: 'POST' };
    if (tickers != null) opts.body = new URLSearchParams({ tickers });
    const r = await fetch(url, opts);
    if (!r.ok){ const e = await r.json().catch(()=>({})); wlSay(e.error || ('error ' + r.status), true); return; }
    const w = await r.json(); renderWL(w);
    wlSay('Now watching ' + w.active.length + ' tickers (' + w.source + '). The bot picks this up within a few seconds.');
  }
  document.getElementById('wl-toggle').onclick = () => {
    const e = document.getElementById('wl-edit'); e.hidden = !e.hidden;
  };
  document.getElementById('wl-save-default').onclick = () =>
    wlPost('/watchlist/default', document.getElementById('wl-default').value);
  document.getElementById('wl-use-default').onclick = () => wlPost('/watchlist/use-default', null);
  document.getElementById('wl-apply-custom').onclick = () =>
    wlPost('/watchlist/custom', document.getElementById('wl-custom').value);
  fetch('/watchlist').then(r => r.json()).then(renderWL);
</script>
</body>
</html>"""


LOGIN_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Sign in</title>
<style>
  :root { color-scheme: dark; }
  body { font: 14px -apple-system, system-ui, sans-serif; background: #0f1115;
         color: #e6e6e6; display: grid; place-items: center; height: 100vh; margin: 0; }
  form { background: #161922; padding: 28px; border-radius: 10px; width: 280px;
         border: 1px solid #232732; }
  h1 { font-size: 15px; margin: 0 0 16px; }
  input { width: 100%; box-sizing: border-box; padding: 9px 11px; margin-bottom: 12px;
          background: #0f1115; border: 1px solid #2a2f3a; border-radius: 6px; color: #e6e6e6; }
  button { width: 100%; padding: 9px; background: #2563eb; color: #fff; border: 0;
           border-radius: 6px; font-weight: 600; cursor: pointer; }
  .err { color: #f87171; font-size: 13px; margin-bottom: 12px; min-height: 16px; }
</style></head>
<body><form method="post" action="/login">
  <h1>Signal Monitor</h1>
  <div class="err">ERR</div>
  <input type="password" name="password" placeholder="Password" autofocus required>
  <button type="submit">Sign in</button>
</form></body></html>"""


def _client_ip(request: web.Request) -> str:
    fwd = request.headers.get("X-Forwarded-For", "")
    return fwd.split(",")[0].strip() if fwd else (request.remote or "?")


def _locked_out(ip: str) -> bool:
    now = time.time()
    recent = [t for t in _fails.get(ip, []) if now - t < _LOCKOUT_SECONDS]
    _fails[ip] = recent
    return len(recent) >= _MAX_FAILS


def _cookie_secure(request: web.Request) -> bool:
    return COOKIE_SECURE_DEFAULT or request.headers.get("X-Forwarded-Proto") == "https"


@web.middleware
async def auth_middleware(request: web.Request, handler):
    open_paths = {"/login", "/health"}
    if not auth_enabled() or request.path in open_paths:
        return await handler(request)
    if ui_auth.verify_session(SECRET, request.cookies.get(COOKIE_NAME)):
        return await handler(request)
    # Unauthenticated: API/SSE callers get 401 (so fetch/EventSource can react);
    # page navigations get redirected to the login form.
    if request.path == "/events" or request.path.startswith("/watchlist"):
        return web.Response(status=401, text="unauthorized")
    raise web.HTTPFound("/login")


async def login(request: web.Request) -> web.Response:
    if request.method == "GET":
        return web.Response(text=LOGIN_PAGE.replace("ERR", ""), content_type="text/html")
    ip = _client_ip(request)
    if _locked_out(ip):
        return web.Response(status=429,
            text=LOGIN_PAGE.replace("ERR", "Too many attempts -- wait a few minutes."),
            content_type="text/html")
    data = await request.post()
    if ui_auth.verify_password(str(data.get("password", "")), PASSWORD_HASH):
        _fails.pop(ip, None)
        resp = web.HTTPFound("/")
        resp.set_cookie(COOKIE_NAME, ui_auth.sign_session(SECRET, SESSION_TTL),
                        max_age=SESSION_TTL, httponly=True,
                        secure=_cookie_secure(request), samesite="Lax")
        return resp
    _fails.setdefault(ip, []).append(time.time())
    return web.Response(status=401,
        text=LOGIN_PAGE.replace("ERR", "Incorrect password."),
        content_type="text/html")


async def logout(request: web.Request) -> web.Response:
    resp = web.HTTPFound("/login")
    resp.del_cookie(COOKIE_NAME)
    return resp


async def index(request: web.Request) -> web.Response:
    rows = signal_store.recent_signals(limit=500)   # newest-first
    html = (PAGE
            .replace("INITIAL_PLACEHOLDER", json.dumps(rows))
            .replace("MAXID_PLACEHOLDER", str(signal_store.max_id())))
    return web.Response(text=html, content_type="text/html")


async def events(request: web.Request) -> web.StreamResponse:
    resp = web.StreamResponse(headers={
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",   # disable proxy buffering if fronted by nginx
    })
    await resp.prepare(request)
    last_id = int(request.query.get("after", 0))
    try:
        while True:
            for row in signal_store.signals_after(last_id):
                last_id = row["id"]
                await resp.write(f"data: {json.dumps(row)}\n\n".encode())
            await resp.write(b": ping\n\n")        # keep-alive / detect drop
            await asyncio.sleep(POLL_SECONDS)
    except (ConnectionResetError, asyncio.CancelledError):
        pass                                        # browser navigated away
    return resp


async def watchlist_get(request: web.Request) -> web.Response:
    return web.json_response(signal_store.get_watchlist())


async def watchlist_default(request: web.Request) -> web.Response:
    data = await request.post()
    signal_store.set_default_tickers(str(data.get("tickers", "")))
    return web.json_response(signal_store.get_watchlist())


async def watchlist_use_default(request: web.Request) -> web.Response:
    signal_store.use_default()
    return web.json_response(signal_store.get_watchlist())


async def watchlist_custom(request: web.Request) -> web.Response:
    data = await request.post()
    tickers = signal_store.set_active_custom(str(data.get("tickers", "")))
    if not tickers:
        return web.json_response({"error": "no valid tickers"}, status=400)
    return web.json_response(signal_store.get_watchlist())


async def health(request: web.Request) -> web.Response:
    return web.json_response({"ok": True, "signals": signal_store.max_id()})


def main() -> None:
    signal_store.init_db()
    app = web.Application(middlewares=[auth_middleware])
    app.add_routes([
        web.get("/", index),
        web.get("/events", events),
        web.get("/health", health),
        web.get("/login", login),
        web.post("/login", login),
        web.get("/logout", logout),
        web.get("/watchlist", watchlist_get),
        web.post("/watchlist/default", watchlist_default),
        web.post("/watchlist/use-default", watchlist_use_default),
        web.post("/watchlist/custom", watchlist_custom),
    ])
    host = os.environ.get("UI_HOST", "127.0.0.1")
    port = int(os.environ.get("UI_PORT", "8000"))
    if auth_enabled():
        print("Auth: ENABLED (single password)")
    else:
        print("Auth: DISABLED -- set UI_PASSWORD_HASH + UI_SECRET to require login")
    print(f"Signal UI on http://{host}:{port}  (db: {signal_store.db_path()})")
    web.run_app(app, host=host, port=port, print=None)


if __name__ == "__main__":
    main()
