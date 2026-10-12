"""Bundle ingest: validate -> render assets -> QA/enrich -> schedule posts.

A bundle is a folder with bundle.json (schema sg.bundle/1, see schemas/) plus any
media files it references. Produced daily by the LLM pipeline (Claude routine or
ChatGPT) — no LLM API key is needed here.
"""
from __future__ import annotations

import json
import re
import shutil
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from . import qa, store
from .config import JOBS, TZ, article_url, load_settings, media_url
from .render import article as A
from .render import card as C

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){1,11}$")
SLOT_KEY = {("web", "article"): "web", ("instagram", "carousel"): "instagram", ("instagram", "image"): "instagram",
            ("instagram", "reel"): "instagram_reel", ("facebook", "photos"): "facebook",
            ("facebook", "link"): "facebook", ("facebook", "reel"): "facebook_reel", ("youtube", "short"): "youtube"}
UNIQUE_TEMPLATES = {"cover", "illustration", "reel_cover", "web_hero"}


class BundleError(ValueError):
    pass


def _safe_file(base: Path, rel: str) -> Path:
    p = (base / rel).resolve()
    if base.resolve() not in p.parents or not p.is_file() or p.is_symlink():
        raise BundleError(f"file '{rel}' missing or outside bundle")
    return p


def _publish_time(spec: str | None, target_day: str, slot: str, settings: dict) -> datetime:
    if spec and spec != "auto":
        if re.fullmatch(r"\d{1,2}:\d{2}", spec):
            h, m = map(int, spec.split(":"))
            return datetime.fromisoformat(target_day).replace(hour=h, minute=m, tzinfo=TZ)
        dt = datetime.fromisoformat(spec)
        return dt if dt.tzinfo else dt.replace(tzinfo=TZ)
    h, m = map(int, settings["slots"][slot].split(":"))
    return datetime.fromisoformat(target_day).replace(hour=h, minute=m, tzinfo=TZ)


def load_bundle(src: Path) -> dict:
    f = src / "bundle.json"
    if not f.is_file():
        raise BundleError(f"{f} not found")
    b = json.loads(f.read_text(encoding="utf-8"))
    if b.get("schema") != "sg.bundle/1":
        raise BundleError("schema must be 'sg.bundle/1'")
    if not SLUG_RE.match(b.get("slug", "")):
        raise BundleError("slug must be lowercase-hyphenated, 2-12 words")
    try:
        date.fromisoformat(b.get("target_day", ""))
    except ValueError:
        raise BundleError("target_day must be YYYY-MM-DD")
    if not isinstance(b.get("assets"), dict) or not isinstance(b.get("posts"), list) or not b["posts"]:
        raise BundleError("assets{} and posts[] are required")
    return b


def build_assets(b: dict, src: Path, out: Path, settings: dict, log=print) -> dict[str, dict]:
    """Render/copy every asset into out/media. Returns asset table (id -> record)."""
    media = out / "media"
    media.mkdir(parents=True, exist_ok=True)
    slug = b["slug"]
    seed = slug
    table: dict[str, dict] = {}
    groups: dict[str, list[str]] = {}

    def add(aid, kind, path, meta=None, unique=False):
        rec = {"asset_id": aid, "kind": kind, "path": str(path), "sha256": qa.sha256(path), "meta": meta or {},
               "phash": "", "unique": unique}
        if kind == "image":
            rec["meta"] = {**qa.image_info(path), **(meta or {})}
            rec["phash"] = qa.dhash(path)
        elif kind == "video":
            rec["meta"] = {**qa.video_info(path), **(meta or {})}
        table[aid] = rec

    items = b["assets"].items()
    # images & carousels first (article needs their URLs), then videos, then article html
    order = sorted(items, key=lambda kv: {"image": 0, "carousel": 0, "video": 1, "article": 2, "html": 2}
                   .get(kv[1].get("kind"), 3))
    for aid, a in order:
        kind = a.get("kind")
        if not re.fullmatch(r"[a-z0-9_]{1,40}", aid):
            raise BundleError(f"asset id '{aid}' must be [a-z0-9_]")
        if kind == "image":
            dst = media / f"{aid}.png"
            if a.get("file"):
                srcf = _safe_file(src, a["file"])
                dst = media / f"{aid}{srcf.suffix.lower()}"
                shutil.copyfile(srcf, dst)
                add(aid, "image", dst, {"origin": a.get("origin", "provided")}, unique=True)
            elif a.get("render"):
                C.render_card(a["render"], dst, seed)
                add(aid, "image", dst, {"template": a["render"].get("template")},
                    unique=a.get("unique", a["render"].get("template") in UNIQUE_TEMPLATES))
            else:
                raise BundleError(f"image asset '{aid}' needs file or render")
        elif kind == "carousel":
            slides = (a.get("render") or {}).get("slides") or []
            if not slides:
                raise BundleError(f"carousel '{aid}' needs render.slides")
            paths = C.render_carousel(slides, media, seed, prefix=f"{aid}_")
            groups[aid] = []
            for i, (pth, spec) in enumerate(zip(paths, slides), 1):
                sid = f"{aid}_{i:02d}"
                pth2 = pth.with_name(f"{sid}.png")
                pth.rename(pth2)
                svg = pth.with_suffix(".svg")
                if svg.exists():
                    svg.unlink()
                add(sid, "image", pth2, {"template": spec.get("template"), "alt": spec.get("alt", "")},
                    unique=spec.get("template") in UNIQUE_TEMPLATES and i == 1)
                groups[aid].append(sid)
        elif kind == "video":
            if a.get("file"):
                srcf = _safe_file(src, a["file"])
                dst = media / f"{aid}.mp4"
                shutil.copyfile(srcf, dst)
                add(aid, "video", dst, {"origin": a.get("origin", "provided")})
                if a.get("cover"):
                    cv = _safe_file(src, a["cover"])
                    shutil.copyfile(cv, media / f"{aid}_cover.png")
                    add(f"{aid}_cover", "image", media / f"{aid}_cover.png")
            elif a.get("render"):
                from .render import video as V
                log(f"rendering video '{aid}' ...")
                vdir = out / "video" / aid
                meta = V.render_short(a["render"]["storyboard"], vdir, seed)
                dst = media / f"{aid}.mp4"
                shutil.copyfile(meta["mp4"], dst)
                shutil.copyfile(meta["cover"], media / f"{aid}_cover.png")
                shutil.copyfile(meta["srt"], media / f"{aid}.srt")
                add(aid, "video", dst, {"srt": str(media / f"{aid}.srt"), "transcript": meta["transcript"]})
                add(f"{aid}_cover", "image", media / f"{aid}_cover.png", {"template": "reel_cover"}, unique=True)
            else:
                raise BundleError(f"video asset '{aid}' needs file or render")
        elif kind in ("article", "html"):
            web = out / "web"
            web.mkdir(parents=True, exist_ok=True)
            dst = web / "index.html"
            canonical = article_url(settings, slug)
            if kind == "html":
                shutil.copyfile(_safe_file(src, a["file"]), dst)
                words = None
            else:
                data = a["render"]
                urls = {k: media_url(settings, slug, Path(v["path"]).name) for k, v in table.items()
                        if v["kind"] == "image"}
                dst.write_text(A.render_article(data, canonical=canonical, slug=slug, image_urls=urls,
                                                published=b["target_day"],
                                                wp_compat=settings["web"]["mode"] == "wordpress"), encoding="utf-8")
                words = A.word_count(data)
                (web / "article.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            table[aid] = {"asset_id": aid, "kind": "html", "path": str(dst), "sha256": qa.sha256(dst),
                          "meta": {"words": words, "canonical": canonical}, "phash": "", "unique": False}
        else:
            raise BundleError(f"asset '{aid}' has unknown kind '{kind}'")
    for gid, members in groups.items():
        table.setdefault("__groups__", {})[gid] = members  # type: ignore[index]
    return table


def _expand(ids, groups):
    out = []
    for i in ids or []:
        out += groups.get(i, [i])
    return out


def ingest(src: Path, dry: bool = False, source: str = "cli", log=print) -> dict:
    settings = load_settings()
    src = Path(src).resolve()
    b = load_bundle(src)
    slug = b["slug"]
    job_id = f'{b["target_day"]}-{slug}'[:90]
    existing = store.get_job(job_id)
    if existing and not dry:
        if any(p["status"] == "published" for p in store.posts_for(job_id)):
            raise BundleError(f"job {job_id} already has published posts; use a new slug")
    prior = [j for j in store.history()["jobs"] if j["slug"] == slug and not existing]
    if prior and not dry:
        raise BundleError(f"slug '{slug}' already used on {prior[0]['target_day']}")
    out = JOBS / ("_validate" if dry else "") / job_id
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    shutil.copyfile(src / "bundle.json", out / "bundle.json")
    table = build_assets(b, src, out, settings, log)
    groups = table.pop("__groups__", {})
    issues: list[dict] = []
    hist = store.history(exclude_job=job_id)["phashes"]
    for a in table.values():
        if a.get("unique"):
            issues += qa.duplicate_art(a, hist, settings["qa"]["phash_min_distance"])
    has_web = any(p.get("platform") == "web" for p in b["posts"])
    ctx = {"settings": settings, "slug": slug, "assets": table,
           "article_url": article_url(settings, slug) if has_web else (b.get("article_url") or None)}
    posts = []
    now = datetime.now(timezone.utc)
    for i, p in enumerate(b["posts"]):
        p = dict(p)
        p.setdefault("kind", {"web": "article", "youtube": "short"}.get(p.get("platform"), ""))
        if p.get("assets"):
            p["assets"] = _expand(p["assets"], groups)
        if p.get("alt_texts") is None and p.get("assets"):
            p["alt_texts"] = [table.get(a, {}).get("meta", {}).get("alt", "") for a in p["assets"]]
        payload, iss = qa.enrich(p, ctx)
        issues += iss
        slot = SLOT_KEY.get((p["platform"], p["kind"]), "web")
        when = _publish_time(p.get("publish_at"), b["target_day"], slot, settings).astimezone(timezone.utc)
        if when < now:
            when = now + timedelta(minutes=3 + 2 * i)
        pid = f"{job_id}:{p['platform']}:{p['kind']}:{i}"[:120]
        dep = p.get("depends_on", "web" if has_web and p["platform"] != "web" else None)
        posts.append({"id": pid, "platform": p["platform"], "kind": p["kind"], "publish_at": when.isoformat(),
                      "payload": payload, "depends_on": dep})
    errs = qa.errors(issues)
    vr = (b.get("qa") or {}).get("visual_review") or {}
    if errs:
        status, pstatus = "blocked", "held"
    elif settings["auto_approve"] and (vr.get("done") is True or not settings["qa"]["require_visual_review"]):
        status, pstatus = "scheduled", "scheduled"
    else:
        status, pstatus = "pending_approval", "pending_approval"
    report = {
        "job_id": job_id, "slug": slug, "status": status if not dry else f"validated ({status})",
        "errors": errs, "warnings": [i for i in issues if i["level"] == "warn"],
        "posts": [{"id": p["id"], "platform": p["platform"], "kind": p["kind"],
                   "publish_at_wib": datetime.fromisoformat(p["publish_at"]).astimezone(TZ).strftime("%Y-%m-%d %H:%M"),
                   "status": pstatus} for p in posts],
        "assets": {k: {"kind": v["kind"], "path": v["path"], **{m: v["meta"].get(m) for m in
                                                                 ("width", "height", "duration", "words")
                                                                 if v["meta"].get(m) is not None}}
                   for k, v in table.items()},
        "visual_review": vr or None,
        "dir": str(out),
    }
    if not vr.get("done") and settings["qa"]["require_visual_review"]:
        report["note"] = ("No recorded visual review: posts wait for approval in the UI "
                          "(look at the rendered PNG/MP4, then approve).")
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    if dry:
        return report
    r = b.get("research") or {}
    pk = r.get("primary_keyword") or {}
    with store.db() as c:
        c.execute("DELETE FROM posts WHERE job_id=?", (job_id,))
        c.execute("DELETE FROM assets WHERE job_id=?", (job_id,))
        c.execute("INSERT OR REPLACE INTO jobs(id,slug,target_day,created,status,source,dir,primary_keyword,question,"
                  "title,research,qa,report) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",
                  (job_id, slug, b["target_day"], store.now(), status, source, str(out),
                   pk.get("keyword", "") if isinstance(pk, dict) else str(pk),
                   (r.get("question") or {}).get("text", "") if isinstance(r.get("question"), dict) else str(r.get("question", "")),
                   b.get("title", ""), json.dumps(r, ensure_ascii=False), json.dumps(b.get("qa") or {}, ensure_ascii=False),
                   json.dumps(report, ensure_ascii=False)))
        for a in table.values():
            c.execute("INSERT INTO assets(job_id,asset_id,kind,path,sha256,phash,public_url,meta) VALUES(?,?,?,?,?,?,?,?)",
                      (job_id, a["asset_id"], a["kind"], a["path"], a["sha256"], a["phash"], "",
                       json.dumps({**a["meta"], "unique": a.get("unique", False)}, ensure_ascii=False)))
        ids = {p["platform"]: p["id"] for p in posts}
        for p in posts:
            dep = ids.get(p["depends_on"]) if p["depends_on"] else None
            c.execute("INSERT INTO posts(id,job_id,platform,kind,publish_at,status,attempts,depends_on,payload,receipt,"
                      "error,updated) VALUES(?,?,?,?,?,?,0,?,?,?,?,?)",
                      (p["id"], job_id, p["platform"], p["kind"], p["publish_at"], pstatus, dep,
                       json.dumps(p["payload"], ensure_ascii=False), "{}", "", store.now()))
    if pk and status != "blocked":
        from . import pool
        pool.mark_used(pk.get("keyword", "") if isinstance(pk, dict) else str(pk), b["target_day"])
    store.log(f"ingested {slug}: {status}, {len(posts)} posts, {len(errs)} errors", "info", job_id)
    return report


def approve(job_id: str, by: str = "ui") -> int:
    n = 0
    with store.db() as c:
        cur = c.execute("UPDATE posts SET status='scheduled', updated=? WHERE job_id=? AND status='pending_approval'",
                        (store.now(), job_id))
        n = cur.rowcount
        c.execute("UPDATE jobs SET status='scheduled' WHERE id=? AND status='pending_approval'", (job_id,))
    store.log(f"approved by {by}: {n} posts scheduled", "info", job_id)
    return n


def cancel(job_id: str, by: str = "ui") -> None:
    with store.db() as c:
        c.execute("UPDATE posts SET status='cancelled', updated=? WHERE job_id=? AND status NOT IN ('published')",
                  (store.now(), job_id))
        c.execute("UPDATE jobs SET status='cancelled' WHERE id=?", (job_id,))
    store.log(f"cancelled by {by}", "warn", job_id)


def requeue(job_id: str, by: str = "ui") -> int:
    """Re-schedule posts that only ran as dry-run or failed (e.g. after switching a platform to live)."""
    now = datetime.now(timezone.utc)
    n = 0
    with store.db() as c:
        rows = c.execute("SELECT id FROM posts WHERE job_id=? AND status IN ('dry_run_ok','failed','held')",
                         (job_id,)).fetchall()
        for i, r in enumerate(rows):
            c.execute("UPDATE posts SET status='scheduled', attempts=0, next_attempt=NULL, error='', publish_at=?, "
                      "updated=? WHERE id=?", ((now + timedelta(minutes=1 + i)).isoformat(), store.now(), r["id"]))
            n += 1
        c.execute("UPDATE jobs SET status='scheduled' WHERE id=?", (job_id,))
    store.log(f"requeued by {by}: {n} posts", "info", job_id)
    return n
