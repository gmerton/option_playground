# Deploying the signal bot to AWS (single EC2 + Docker)

The whole stack runs in four containers on one EC2 instance:

```
Internet ─443─► caddy (TLS, internal CA) ─► signal-ui (login-gated) ─┐
                                                                     ├─► /data/signals.db
                       ib-gateway (paper, IBC auto-login) ◄── bot ───┘
```

Only Caddy's port 443 is public. The IB API (4002) and the UI (8000) stay on
the private Docker network.

## 1. Launch the instance

- **Type:** `t3.small` (2 GB) on-demand. Not `t3.micro` (Java gateway is tight),
  not spot (interruption forces an IB re-login).
- **OS:** Amazon Linux 2023 or Ubuntu 24.04, 20–30 GB gp3.
- **Elastic IP:** allocate and associate one — a stable outbound IP cuts down
  IBKR "login from new location" challenges.
- **Security group:**
  | Port | Source | Why |
  |------|--------|-----|
  | 22   | your IP/32 | SSH |
  | 443  | 0.0.0.0/0 | public UI (login-gated) |
  - Do **not** open 4002 or 8000.

## 2. Install Docker + compose

Amazon Linux 2023:
```bash
sudo dnf -y install docker
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user   # re-login after this
sudo dnf -y install docker-compose-plugin
```

## 3. Get the code onto the box

Copy the `ibkr_bot/` directory up (git clone of the repo, or `scp`/`rsync`).
You need at minimum: `*.py`, `watchlist_phb.txt`, `requirements.txt`,
`Dockerfile`, `docker-compose.yml`, `Caddyfile`, `.env.example`.

## 4. Configure secrets

```bash
cd ibkr_bot
cp .env.example .env
# generate the UI login hash + session secret (prints two lines):
docker run --rm -it -v "$PWD":/app -w /app python:3.13-slim python ui_auth.py
#   ...or, if you have a local venv: python ui_auth.py
```
Paste the printed `UI_PASSWORD_HASH=` and `UI_SECRET=` into `.env`, and fill in
`TWS_USERID` / `TWS_PASSWORD` for your **paper** account.

## 5. Start it

```bash
docker compose up -d --build
docker compose logs -f ib-gateway   # watch it log into paper
docker compose logs -f bot          # "OK Connected (paper [...])"
```
The bot waits (and retries) until the gateway is logged in, so ordering during
first boot is fine.

## 6. Trust Caddy's root CA (one time per device)

The UI is real HTTPS, but signed by Caddy's private CA. Trust it once to get a
clean padlock and MITM protection:
```bash
# print the root cert; copy it to the device you browse from
docker compose exec caddy cat /data/caddy/pki/authorities/local/root.crt
```
- **macOS:** save as `caddy-root.crt`, open in Keychain Access → System →
  drag it in → set "Always Trust".
- **iOS:** AirDrop/email the file → install profile → Settings → General →
  About → Certificate Trust Settings → enable it.

Then browse to **`https://<your-elastic-ip>/`** and log in. (Without trusting
the CA it still works — you just click through a browser warning.)

## 7. Operating it

- **Logs:** `docker compose logs -f bot` / `signal-ui` / `ib-gateway`.
- **Restart one service:** `docker compose restart bot`.
- **Update code:** pull/scp new files, then `docker compose up -d --build`.
- **Daily IB reset:** the gateway restarts at `AUTO_RESTART_TIME`; the bot's
  supervised mode (`IB_SUPERVISED=1`) exits on the drop and the restart policy
  reconnects it automatically. No action needed.
- **Paper accounts need no 2FA**, so this runs unattended. (A *live* account
  would require a weekly manual IBKR Mobile approval — out of scope here.)

## Managing the watchlist

The watchlist is managed **in the web UI** ("Edit watchlist"), not by editing
files on the server. `watchlist_phb.txt` is only the **first-run seed** for the
Default list — once the stack has started once, the stored lists are
authoritative and survive restarts, so editing the file later has no effect.
Changes made in the UI (editing the Default list, or applying a Custom list)
reach the running bot within a few seconds — it subscribes new tickers and
drops removed ones with no restart, keeping session state for unchanged names.
To re-seed the Default from a changed file, clear it in the `signal_data`
volume (or edit it in the UI).

## Security notes

- The UI is **read-only** — it shows signal rows, no orders/positions/keys. The
  worst case from a UI compromise is someone seeing which tickers fired.
- API is `READ_ONLY_API=yes`: even the gateway connection can't place orders.
- Login: scrypt-hashed password (plaintext never stored), HMAC-signed cookie,
  per-IP brute-force lockout (6 tries / 5 min) behind public TLS.
- Rotate `UI_SECRET` to force re-login everywhere; rotate the password by
  regenerating the hash with `ui_auth.py`.
