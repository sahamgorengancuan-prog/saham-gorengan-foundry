"""SQLite job/post/asset store with an append-only event log."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from .config import DB_FILE, ensure_dirs

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs(
  id TEXT PRIMARY KEY, slug TEXT, target_day TEXT, created TEXT, status TEXT, source TEXT,
  dir TEXT, primary_keyword TEXT, question TEXT, title TEXT, research TEXT, qa TEXT, report TEXT);
CREATE TABLE IF NOT EXISTS posts(
  id TEXT PRIMARY KEY, job_id TEXT, platform TEXT, kind TEXT, publish_at TEXT, status TEXT,
  attempts INTEGER DEFAULT 0, next_attempt TEXT, depends_on TEXT, payload TEXT, receipt TEXT,
  error TEXT, updated TEXT);
CREATE TABLE IF NOT EXISTS assets(
  job_id TEXT, asset_id TEXT, kind TEXT, path TEXT, sha256 TEXT, phash TEXT, public_url TEXT, meta TEXT,
  PRIMARY KEY(job_id, asset_id));
CREATE TABLE IF NOT EXISTS events(
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, level TEXT, job_id TEXT, post_id TEXT, message TEXT);
CREATE INDEX IF NOT EXISTS posts_due ON posts(status, publish_at);
CREATE INDEX IF NOT EXISTS jobs_slug ON jobs(slug);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@contextmanager
def db():
    ensure_dirs()
    c = sqlite3.connect(DB_FILE, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript(SCHEMA)
    try:
        yield c
        c.commit()
    finally:
        c.close()


def row(r) -> dict | None:
    if r is None:
        return None
    d = dict(r)
    for k in ("research", "qa", "report", "payload", "receipt", "meta"):
        if k in d and isinstance(d[k], str) and d[k][:1] in "{[":
            try:
                d[k] = json.loads(d[k])
            except ValueError:
                pass
    return d


def log(message: str, level: str = "info", job_id: str = "", post_id: str = "") -> None:
    with db() as c:
        c.execute("INSERT INTO events(ts,level,job_id,post_id,message) VALUES(?,?,?,?,?)",
                  (now(), level, job_id, post_id, message[:2000]))


def events(limit: int = 200, job_id: str | None = None) -> list[dict]:
    with db() as c:
        q = "SELECT * FROM events" + (" WHERE job_id=?" if job_id else "") + " ORDER BY id DESC LIMIT ?"
        return [dict(r) for r in c.execute(q, ((job_id, limit) if job_id else (limit,)))]


def get_job(job_id: str) -> dict | None:
    with db() as c:
        return row(c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone())


def list_jobs(limit: int = 50) -> list[dict]:
    with db() as c:
        return [row(r) for r in c.execute("SELECT * FROM jobs ORDER BY created DESC LIMIT ?", (limit,))]


def posts_for(job_id: str) -> list[dict]:
    with db() as c:
        return [row(r) for r in c.execute("SELECT * FROM posts WHERE job_id=? ORDER BY publish_at", (job_id,))]


def get_post(post_id: str) -> dict | None:
    with db() as c:
        return row(c.execute("SELECT * FROM posts WHERE id=?", (post_id,)).fetchone())


def update_post(post_id: str, **fields) -> None:
    fields["updated"] = now()
    for k in ("payload", "receipt"):
        if k in fields and not isinstance(fields[k], str):
            fields[k] = json.dumps(fields[k], ensure_ascii=False)
    cols = ", ".join(f"{k}=?" for k in fields)
    with db() as c:
        c.execute(f"UPDATE posts SET {cols} WHERE id=?", (*fields.values(), post_id))


def update_job(job_id: str, **fields) -> None:
    for k in ("research", "qa", "report"):
        if k in fields and not isinstance(fields[k], str):
            fields[k] = json.dumps(fields[k], ensure_ascii=False)
    cols = ", ".join(f"{k}=?" for k in fields)
    with db() as c:
        c.execute(f"UPDATE jobs SET {cols} WHERE id=?", (*fields.values(), job_id))


def assets_for(job_id: str) -> dict[str, dict]:
    with db() as c:
        return {r["asset_id"]: row(r) for r in c.execute("SELECT * FROM assets WHERE job_id=?", (job_id,))}


def set_asset_url(job_id: str, asset_id: str, url: str) -> None:
    with db() as c:
        c.execute("UPDATE assets SET public_url=? WHERE job_id=? AND asset_id=?", (url, job_id, asset_id))


def due_posts(now_iso: str) -> list[dict]:
    with db() as c:
        return [row(r) for r in c.execute(
            "SELECT * FROM posts WHERE status='scheduled' AND publish_at<=? AND (next_attempt IS NULL OR next_attempt<=?)"
            " ORDER BY publish_at", (now_iso, now_iso))]


def upcoming(limit: int = 30) -> list[dict]:
    with db() as c:
        return [row(r) for r in c.execute(
            "SELECT p.*, j.slug FROM posts p JOIN jobs j ON j.id=p.job_id "
            "WHERE p.status IN ('scheduled','pending_approval','publishing','held') ORDER BY p.publish_at LIMIT ?",
            (limit,))]


def history(days: int = 120, exclude_job: str = "") -> dict:
    """What the LLM must not repeat: slugs, keywords, questions, titles, and recent perceptual hashes."""
    with db() as c:
        jobs = [dict(r) for r in c.execute(
            "SELECT slug, target_day, primary_keyword, question, title, status FROM jobs "
            "WHERE status NOT IN ('rejected','cancelled') AND created >= datetime('now', ?) ORDER BY created DESC",
            (f"-{days} days",))]
        phashes = [r["phash"] for r in c.execute(
            "SELECT a.phash FROM assets a JOIN jobs j ON j.id=a.job_id WHERE a.phash IS NOT NULL AND a.phash!='' "
            "AND j.status NOT IN ('rejected','cancelled') AND j.created >= datetime('now', ?) AND j.id != ?",
            (f"-{days} days", exclude_job))]
    return {"jobs": jobs, "phashes": phashes}
