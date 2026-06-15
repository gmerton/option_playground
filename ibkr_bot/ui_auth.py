#!/usr/bin/env python3
"""Single-password auth for the signal UI -- stdlib only.

Two primitives:
  * password hashing (scrypt) so the plaintext never lives in env/files, and
  * signed session tokens (HMAC) so a login survives as a tamper-proof cookie.

Generate a hash to drop into UI_PASSWORD_HASH:

    .venv/bin/python3 ibkr_bot/ui_auth.py

It prompts (no echo), prints the hash line, and never writes the plaintext.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time

# scrypt cost params (n must be a power of two). 16384/8/1 is the interactive
# default -- ample for a single-user gate, fast enough to verify per login.
_N, _R, _P, _DKLEN = 16384, 8, 1, 32


def _b64e(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def _b64d(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


# --- password hashing -------------------------------------------------------

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.scrypt(password.encode(), salt=salt, n=_N, r=_R, p=_P, dklen=_DKLEN)
    return f"scrypt${_N}${_R}${_P}${_b64e(salt)}${_b64e(dk)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, n, r, p, salt_b64, hash_b64 = stored.split("$")
        if algo != "scrypt":
            return False
        dk = hashlib.scrypt(password.encode(), salt=_b64d(salt_b64),
                            n=int(n), r=int(r), p=int(p), dklen=len(_b64d(hash_b64)))
        return hmac.compare_digest(dk, _b64d(hash_b64))
    except Exception:
        return False


# --- signed session tokens --------------------------------------------------

def sign_session(secret: str, ttl_seconds: int) -> str:
    payload = _b64e(json.dumps({"exp": int(time.time()) + ttl_seconds}).encode())
    sig = _b64e(hmac.new(secret.encode(), payload.encode(), hashlib.sha256).digest())
    return f"{payload}.{sig}"


def verify_session(secret: str, token: str | None) -> bool:
    if not token or "." not in token:
        return False
    payload, sig = token.rsplit(".", 1)
    expected = _b64e(hmac.new(secret.encode(), payload.encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(sig, expected):
        return False
    try:
        return int(json.loads(_b64d(payload))["exp"]) > int(time.time())
    except Exception:
        return False


if __name__ == "__main__":
    import getpass
    pw = getpass.getpass("New UI password: ")
    if pw != getpass.getpass("Confirm: "):
        raise SystemExit("passwords did not match")
    if len(pw) < 10:
        raise SystemExit("use at least 10 characters for a public login")
    print("\nAdd this to your .env (the plaintext is not stored anywhere):\n")
    print(f"UI_PASSWORD_HASH={hash_password(pw)}")
    print(f"UI_SECRET={_b64e(os.urandom(32))}   # also rotate this to log everyone out\n")
