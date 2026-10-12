"""Due-post runner. Called every minute by the server thread (or `app.py tick` from cron)."""
from __future__ import annotations

import fcntl
import os
import threading
import time
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import store, vault
from .adapters.meta import Meta, MetaError, Pending
from .adapters.web import Web, WebError
from .adapters.youtube import YouTube, YouTubeError
from .config import STATE, TZ, load_settings

TERMINAL = {"published", "dry_run_ok", "failed", "cancelled"}


def _urls_for(post: dict, job: dict, assets: dict, settings: dict, dry: bool) -> dict:
    p = post["payload"]
    ids = list(p.get("assets") or []) + [x for x in (p.get("asset"), p.get("cover")) if x]
    if dry:
        return {i: f"(dry-run) {Path(assets[i]['path']).name}" for i in ids if i in assets}
    web = Web(settings)
    ok, why = web.configured()
    if not ok:
        raise WebError("media hosting needs the Web/SSH target configured (" + why + ")")
    return {i: web.host_media(job["id"], job["slug"], assets[i]) for i in ids}


def dispatch(post: dict, job: dict, settings: dict, dry: bool, receipt: dict) -> dict:
    assets = store.assets_for(job["id"])
    plat = post["platform"]
    if plat == "web":
        return Web(settings).publish_article(job, post, assets, dry=dry)
    if plat in ("instagram", "facebook"):
        meta = Meta(settings)
        if dry:
            d = meta.c.get("derived") or {}
            return {"dry_run": True, "kind": post["kind"], "page": d.get("page_name"), "ig": d.get("ig_username"),
                    "media": _urls_for(post, job, assets, settings, True),
                    "text": (post["payload"].get("caption") or post["payload"].get("message", ""))[:300],
                    "credentials": "derived" if d.get("page_id") else "NOT CONFIGURED"}
        urls = _urls_for(post, job, assets, settings, False)
        return (meta.publish_instagram if plat == "instagram" else meta.publish_facebook)(post, urls, receipt)
    if plat == "youtube":
        yt = YouTube(settings)
        a = assets[post["payload"]["asset"]]
        if dry:
            return {"dry_run": True, "title": post["payload"]["title"], "video": Path(a["path"]).name,
                    "channel": (yt.c.get("derived") or {}).get("channel_title") or "NOT CONFIGURED"}
        srt = (a.get("meta") or {}).get("srt")
        return yt.upload_short(post, Path(a["path"]), receipt, Path(srt) if srt else None)
    raise ValueError(f"unknown platform {plat}")


def _backoff(settings: dict, attempts: int) -> timedelta:
    steps = settings["retry"]["backoff_minutes"]
    return timedelta(minutes=steps[min(attempts - 1, len(steps) - 1)])


def run_post(post: dict, settings: dict, force: bool = False, log=print) -> str:
    job = store.get_job(post["job_id"])
    mode = settings["modes"].get(post["platform"], "dry_run")
    now = datetime.now(timezone.utc)
    if mode == "off" and not force:
        return "skipped(off)"
    if post.get("depends_on"):
        dep = store.get_post(post["depends_on"])
        if dep and dep["status"] in ("failed", "cancelled", "held"):
            store.update_post(post["id"], status="held", error=f"dependency {dep['platform']} is {dep['status']}")
            return "held"
        if dep and dep["status"] == "dry_run_ok" and mode == "live":
            store.update_post(post["id"], status="held",
                              error="article only ran as dry-run; switch web to live and requeue (links would 404)")
            return "held"
        if dep and dep["status"] not in ("published", "dry_run_ok"):
            store.update_post(post["id"], next_attempt=(now + timedelta(minutes=5)).isoformat())
            return "waiting(dependency)"
    dry = mode != "live"
    receipt = post.get("receipt") if isinstance(post.get("receipt"), dict) else {}
    store.update_post(post["id"], status="publishing")
    try:
        result = dispatch(post, job, settings, dry, receipt)
        status = "dry_run_ok" if dry else "published"
        store.update_post(post["id"], status=status, receipt=result, error="", next_attempt=None)
        store.log(f"{post['platform']}/{post['kind']} {status} {result.get('url', '')}", "info", job["id"], post["id"])
        return status
    except Pending as pe:
        store.update_post(post["id"], status="scheduled", receipt=pe.receipt or receipt,
                          next_attempt=(now + timedelta(seconds=pe.wait)).isoformat(), error=str(pe))
        return "pending"
    except Exception as e:  # noqa: BLE001 - every failure must be recorded, never crash the loop
        transient = getattr(e, "transient", isinstance(e, (WebError, OSError)))
        attempts = int(post.get("attempts") or 0) + 1
        max_a = settings["retry"]["max_attempts"]
        msg = f"{type(e).__name__}: {str(e)[:400]}"
        if attempts < max_a and (transient or attempts < 2):
            store.update_post(post["id"], status="scheduled", attempts=attempts, receipt=receipt, error=msg,
                              next_attempt=(now + _backoff(settings, attempts)).isoformat())
            store.log(f"{post['platform']} attempt {attempts} failed, retrying: {msg}", "warn", job["id"], post["id"])
            return "retry"
        store.update_post(post["id"], status="failed", attempts=attempts, receipt=receipt, error=msg)
        store.log(f"{post['platform']} FAILED: {msg}", "error", job["id"], post["id"])
        if not isinstance(e, (MetaError, WebError, YouTubeError)):
            store.log(traceback.format_exc()[-1500:], "error", job["id"], post["id"])
        return "failed"


def _refresh_job_status(job_id: str) -> None:
    posts = store.posts_for(job_id)
    st = {p["status"] for p in posts}
    if not st or not st <= TERMINAL | {"held"}:
        return
    if st <= {"published"}:
        js = "published"
    elif st <= {"dry_run_ok", "published"}:
        js = "dry_run_done" if "published" not in st else "partial"
    elif "published" in st:
        js = "partial"
    elif st <= {"cancelled"}:
        js = "cancelled"
    else:
        js = "failed"
    store.update_job(job_id, status=js)


def tick(log=print) -> dict:
    STATE.mkdir(parents=True, exist_ok=True)
    lock_path = STATE / "scheduler.lock"
    fd = os.open(lock_path, os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        return {"skipped": "another tick running"}
    try:
        settings = load_settings()
        now = datetime.now(timezone.utc).isoformat()
        results = {}
        for post in store.due_posts(now):
            results[post["id"]] = run_post(post, settings, log=log)
            _refresh_job_status(post["job_id"])
        return results
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def publish_now(post_id: str, log=print) -> str:
    post = store.get_post(post_id)
    if not post:
        raise ValueError("post not found")
    store.update_post(post_id, status="scheduled", next_attempt=None)
    r = run_post(store.get_post(post_id), load_settings(), force=True, log=log)
    _refresh_job_status(post["job_id"])
    return r


class Loop(threading.Thread):
    def __init__(self, interval: int = 60):
        super().__init__(daemon=True, name="sg-scheduler")
        self.interval = interval
        self.last = {"at": None, "result": None}

    def run(self) -> None:
        while True:
            try:
                self.last = {"at": datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S"), "result": tick()}
            except Exception as e:  # noqa: BLE001
                store.log(f"scheduler loop error: {type(e).__name__}: {e}", "error")
            time.sleep(self.interval)


def platform_status(settings: dict | None = None) -> list[dict]:
    s = settings or load_settings()
    creds = vault.load()
    out = []
    web = Web(s)
    ok, why = web.configured()
    out.append({"platform": "web", "mode": s["modes"]["web"], "configured": ok,
                "detail": f"{s['web']['mode']} -> {s['web']['host'] or '?'}:{s['web']['docroot'] or '?'}" if ok else why})
    d = (creds.get("meta") or {}).get("derived") or {}
    meta_detail = (f"Page '{d.get('page_name')}' / IG @{d.get('ig_username')}" if d.get("page_id")
                   else "not derived")
    if d.get("warnings"):
        meta_detail += " | " + "; ".join(d["warnings"])
    for plat in ("instagram", "facebook"):
        out.append({"platform": plat, "mode": s["modes"][plat], "configured": bool(d.get("page_id")) and
                    (plat == "facebook" or bool(d.get("ig_user_id"))), "detail": meta_detail})
    y = (creds.get("youtube") or {}).get("derived") or {}
    out.append({"platform": "youtube", "mode": s["modes"]["youtube"], "configured": bool(y.get("channel_id")),
                "detail": f"{y.get('channel_title')} ({y.get('channel_id')})" if y else "not authorised"})
    return out
