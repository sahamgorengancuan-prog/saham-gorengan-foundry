"""Paths and runtime settings. Settings live in state/settings.json (no secrets)."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(os.environ.get("SGMW_ROOT", Path(__file__).resolve().parent.parent))
STATE = ROOT / "state"
JOBS = STATE / "jobs"
INBOX = ROOT / "inbox"
LOGS = ROOT / "logs"
BRAND_DIR = ROOT / "brand"
PROMPTS = ROOT / "prompts"
SETTINGS_FILE = STATE / "settings.json"
DB_FILE = STATE / "sgmw.sqlite3"
TZ = ZoneInfo("Asia/Jakarta")

PLATFORMS = ("web", "instagram", "facebook", "youtube")
MODES = ("off", "dry_run", "live")

DEFAULT_SETTINGS = {
    "bind": "127.0.0.1",
    "port": 18790,
    # Every platform starts in dry_run. Flip to live in the UI after "Verify" passes.
    "modes": {"web": "dry_run", "instagram": "dry_run", "facebook": "dry_run", "youtube": "dry_run"},
    # QA-clean bundles with a recorded visual review are scheduled without a human click.
    "auto_approve": True,
    "slots": {"web": "10:30", "instagram": "15:00", "facebook": "15:30", "instagram_reel": "17:00",
              "facebook_reel": "17:10", "youtube": "17:00"},
    "site": {"base_url": "https://sahamgorengan.id", "article_path": "/insight/{slug}/",
             "media_path": "/media/{slug}/", "utm_campaign_prefix": "sg"},
    "web": {"mode": "static", "host": "", "port": 22, "user": "", "key_path": "", "known_hosts": "",
            "docroot": "", "article_dir": "insight/{slug}", "media_dir": "media/{slug}",
            "sitemap_name": "sitemap-insight.xml", "wp_root": "", "php_bin": "php", "wp_cli": "wp",
            "wp_bridge": "", "wp_inbox": ""},
    "meta": {"graph_version": "v24.0", "expected_page_name": "saham gorengan",
             "expected_ig_username": "cuan_sahamgorengan"},
    "youtube": {"redirect_uri": "http://127.0.0.1:18790/oauth/youtube/callback", "privacy": "public",
                "category_id": "27", "synthetic_media": False, "upload_captions": True},
    "qa": {"ig_max_hashtags": 5, "fb_max_hashtags": 3, "min_article_words": 900, "phash_min_distance": 6,
           "require_visual_review": True, "max_video_seconds": 180, "min_video_seconds": 5},
    "retry": {"max_attempts": 4, "backoff_minutes": [2, 10, 30, 90]},
}


def _merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def ensure_dirs() -> None:
    for p in (STATE, JOBS, INBOX, LOGS, STATE / "ssh", STATE / "cache"):
        p.mkdir(parents=True, exist_ok=True)
    for p in (STATE, STATE / "ssh"):
        try:
            p.chmod(0o700)
        except OSError:
            pass


def load_settings() -> dict:
    data = {}
    if SETTINGS_FILE.exists():
        data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    return _merge(DEFAULT_SETTINGS, data)


def save_settings(settings: dict) -> dict:
    ensure_dirs()
    merged = _merge(DEFAULT_SETTINGS, settings)
    tmp = SETTINGS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, SETTINGS_FILE)
    return merged


def update_settings(patch: dict) -> dict:
    return save_settings(_merge(load_settings(), patch))


def article_url(settings: dict, slug: str) -> str:
    site = settings["site"]
    return site["base_url"].rstrip("/") + site["article_path"].format(slug=slug)


def media_url(settings: dict, slug: str, filename: str) -> str:
    site = settings["site"]
    return site["base_url"].rstrip("/") + site["media_path"].format(slug=slug) + filename
