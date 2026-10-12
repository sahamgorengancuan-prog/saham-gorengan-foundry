"""Encrypted credential vault (Fernet). Secrets never leave this file in clear text."""
from __future__ import annotations

import json
import os
import secrets
from pathlib import Path

from cryptography.fernet import Fernet

from .config import STATE, ensure_dirs

KEY = STATE / "vault.key"
VAULT = STATE / "credentials.enc"
API_TOKEN = STATE / "api_token"
UI_AUTH = STATE / "ui_auth.json"

SECRET_FIELDS = {"system_user_token", "app_secret", "page_token", "client_secret", "refresh_token",
                 "access_token", "token"}


def _write_private(path: Path, data: bytes) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


def _fernet() -> Fernet:
    ensure_dirs()
    if not KEY.exists():
        _write_private(KEY, Fernet.generate_key())
    return Fernet(KEY.read_bytes())


def load() -> dict:
    if not VAULT.exists():
        return {}
    return json.loads(_fernet().decrypt(VAULT.read_bytes()))


def get(platform: str) -> dict:
    return load().get(platform, {})


def put(platform: str, values: dict, replace: bool = False) -> dict:
    data = load()
    cur = {} if replace else dict(data.get(platform, {}))
    for k, v in values.items():
        if v is None:
            cur.pop(k, None)
        elif isinstance(v, (dict, list, bool, int, float)) or str(v).strip():
            cur[k] = v.strip() if isinstance(v, str) else v
    data[platform] = cur
    _write_private(VAULT, _fernet().encrypt(json.dumps(data).encode()))
    return cur


def masked(platform: str | None = None) -> dict:
    """Field names + masked values, safe to show in UI/logs."""
    def mask(k, v):
        if isinstance(v, dict):
            return {kk: mask(kk, vv) for kk, vv in v.items()}
        if k in SECRET_FIELDS and v:
            s = str(v)
            return f"•••{s[-4:]}" if len(s) > 12 else "•••"
        return v
    data = load()
    if platform:
        data = {platform: data.get(platform, {})}
    return {p: {k: mask(k, v) for k, v in d.items()} for p, d in data.items()}


def api_token() -> str:
    ensure_dirs()
    if not API_TOKEN.exists():
        _write_private(API_TOKEN, secrets.token_urlsafe(32).encode())
    return API_TOKEN.read_text().strip()


def ui_auth() -> tuple[str, str]:
    ensure_dirs()
    if not UI_AUTH.exists():
        _write_private(UI_AUTH, json.dumps({"user": "sgadmin", "password": secrets.token_urlsafe(14)}).encode())
    d = json.loads(UI_AUTH.read_text())
    return d["user"], d["password"]
