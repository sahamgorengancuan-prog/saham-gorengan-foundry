"""HTTP API (loopback only) + YouTube OAuth callback + Gradio admin UI mount."""
from __future__ import annotations

import io
import json
import secrets
import shutil
import tempfile
import zipfile
from pathlib import Path

from fastapi import Depends, FastAPI, File, Header, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from . import __version__, bundle, scheduler, store, vault
from .adapters.youtube import YouTube, YouTubeError
from .brand import brand
from .config import INBOX, JOBS, load_settings


def require_token(authorization: str = Header(default="")) -> None:
    tok = authorization.removeprefix("Bearer ").strip()
    if not tok or not secrets.compare_digest(tok, vault.api_token()):
        raise HTTPException(401, "invalid or missing bearer token")


def _resolve_bundle_dir(path: str) -> Path:
    p = Path(path).resolve()
    allowed = [INBOX.resolve(), JOBS.resolve()]
    if not any(p == a or a in p.parents for a in allowed):
        raise HTTPException(400, f"bundle path must be inside {INBOX}")
    if not (p / "bundle.json").is_file():
        raise HTTPException(400, "bundle.json not found in path")
    return p


def _unzip(data: bytes) -> Path:
    dst = Path(tempfile.mkdtemp(prefix="upload_", dir=str(INBOX)))
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for m in z.infolist():
            target = (dst / m.filename).resolve()
            if dst.resolve() not in target.parents and target != dst.resolve():
                raise HTTPException(400, "zip contains unsafe paths")
            if m.is_dir():
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with z.open(m) as src, open(target, "wb") as out:
                shutil.copyfileobj(src, out)
    roots = [p for p in dst.rglob("bundle.json")]
    if not roots:
        raise HTTPException(400, "zip has no bundle.json")
    return roots[0].parent


def create_app(loop: scheduler.Loop | None = None, with_ui: bool = True) -> FastAPI:
    app = FastAPI(title="SG Publisher Middleware", version=__version__, docs_url="/api/docs", redoc_url=None)
    auth = [Depends(require_token)]

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse("/ui/" if with_ui else "/api/docs")

    @app.get("/api/v1/health", dependencies=auth)
    def health():
        return {"version": __version__, "platforms": scheduler.platform_status(),
                "scheduler": loop.last if loop else None, "upcoming": store.upcoming(10)}

    @app.get("/api/v1/brand", dependencies=auth)
    def get_brand():
        return brand()

    @app.get("/api/v1/history", dependencies=auth)
    def get_history(days: int = 120):
        h = store.history(days)
        return {"jobs": h["jobs"], "phash_count": len(h["phashes"])}

    def _ingest_from(body: dict | None, upload: UploadFile | None, dry: bool):
        if upload is not None:
            src = _unzip(upload.file.read())
        elif body and body.get("path"):
            src = _resolve_bundle_dir(body["path"])
        elif body and body.get("bundle"):
            b = body["bundle"]
            src = INBOX / f'{b.get("target_day", "x")}-{b.get("slug", "inline")}'
            src.mkdir(parents=True, exist_ok=True)
            (src / "bundle.json").write_text(json.dumps(b, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            raise HTTPException(400, "send {'path': ...}, {'bundle': {...}} or a bundle.zip upload")
        try:
            return bundle.ingest(src, dry=dry, source="api")
        except bundle.BundleError as e:
            raise HTTPException(422, str(e))

    @app.post("/api/v1/bundles", dependencies=auth)
    async def post_bundle(request: Request):
        if request.headers.get("content-type", "").startswith("multipart/"):
            form = await request.form()
            return _ingest_from(None, form.get("file"), dry=False)
        return _ingest_from(await request.json(), None, dry=False)

    @app.post("/api/v1/validate", dependencies=auth)
    async def validate(request: Request):
        if request.headers.get("content-type", "").startswith("multipart/"):
            form = await request.form()
            return _ingest_from(None, form.get("file"), dry=True)
        return _ingest_from(await request.json(), None, dry=True)

    @app.get("/api/v1/jobs", dependencies=auth)
    def jobs(limit: int = 30):
        return [{k: j[k] for k in ("id", "slug", "target_day", "status", "title", "primary_keyword", "created")}
                for j in store.list_jobs(limit)]

    @app.get("/api/v1/jobs/{job_id}", dependencies=auth)
    def job(job_id: str):
        j = store.get_job(job_id)
        if not j:
            raise HTTPException(404, "job not found")
        return {"job": j, "posts": store.posts_for(job_id), "events": store.events(50, job_id)}

    @app.post("/api/v1/jobs/{job_id}/{action}", dependencies=auth)
    def job_action(job_id: str, action: str):
        if not store.get_job(job_id):
            raise HTTPException(404, "job not found")
        fn = {"approve": bundle.approve, "cancel": bundle.cancel, "requeue": bundle.requeue}.get(action)
        if not fn:
            raise HTTPException(400, "action must be approve|cancel|requeue")
        return {"result": fn(job_id, by="api")}

    @app.post("/api/v1/posts/{post_id:path}/publish-now", dependencies=auth)
    def publish_now(post_id: str):
        try:
            return {"result": scheduler.publish_now(post_id)}
        except ValueError as e:
            raise HTTPException(404, str(e))

    @app.post("/api/v1/tick", dependencies=auth)
    def tick():
        return scheduler.tick()

    @app.get("/oauth/youtube/callback", include_in_schema=False)
    def yt_callback(code: str = "", state: str = "", error: str = ""):
        if error:
            return HTMLResponse(f"<h3>Google returned: {error}</h3>", 400)
        try:
            d = YouTube(load_settings()).finish(code, state)
            return HTMLResponse(f"<h2>YouTube connected</h2><p>Channel: {d['channel_title']} ({d['channel_id']})</p>"
                                "<p>You can close this tab and return to the middleware UI.</p>")
        except YouTubeError as e:
            return HTMLResponse(f"<h3>YouTube authorisation failed</h3><p>{e}</p>", 400)

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):
        store.log(f"API error {request.url.path}: {type(exc).__name__}: {str(exc)[:300]}", "error")
        return JSONResponse({"error": type(exc).__name__, "detail": str(exc)[:300]}, 500)

    if with_ui:
        import gradio as gr
        from .ui import build_ui
        user, pw = vault.ui_auth()
        app = gr.mount_gradio_app(app, build_ui(loop), path="/ui", auth=(user, pw), ssr_mode=False,
                                  allowed_paths=[str(JOBS), str(Path(__file__).resolve().parent.parent / "brand")],
                                  footer_links=[])
    return app
