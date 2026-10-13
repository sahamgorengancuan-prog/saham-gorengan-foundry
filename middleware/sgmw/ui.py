"""Gradio admin UI mounted at /ui (loopback only; reach it via SSH tunnel or VPS desktop :88)."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import gradio as gr

from . import bundle, scheduler, store, vault
from .adapters.meta import Meta, MetaError
from .adapters.web import Web, WebError
from .adapters.youtube import YouTube, YouTubeError
from .brand import brand
from .config import BRAND_DIR, INBOX, MODES, PLATFORMS, ROOT, TZ, load_settings, update_settings


def _wib(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        return datetime.fromisoformat(iso).astimezone(TZ).strftime("%m-%d %H:%M")
    except ValueError:
        return iso


def status_rows():
    return [[p["platform"], p["mode"], "yes" if p["configured"] else "no", p["detail"]]
            for p in scheduler.platform_status()]


def upcoming_rows():
    return [[_wib(p["publish_at"]), p["slug"], p["platform"], p["kind"], p["status"], (p.get("error") or "")[:90]]
            for p in store.upcoming(40)]


def job_choices():
    return [f'{j["id"]}  [{j["status"]}]' for j in store.list_jobs(60)]


def _jid(choice: str | None) -> str:
    return (choice or "").split("  [")[0].strip()


def job_detail(choice):
    jid = _jid(choice)
    j = store.get_job(jid)
    if not j:
        return {}, [], None, [], ""
    assets = store.assets_for(jid)
    imgs = [(a["path"], a["asset_id"]) for a in assets.values() if a["kind"] == "image"]
    vid = next((a["path"] for a in assets.values() if a["kind"] == "video"), None)
    posts = [[p["id"], p["platform"], p["kind"], _wib(p["publish_at"]), p["status"], p["attempts"],
              (p.get("receipt") or {}).get("url", "") if isinstance(p.get("receipt"), dict) else "",
              (p.get("error") or "")[:120]] for p in store.posts_for(jid)]
    html = next((a["path"] for a in assets.values() if a["kind"] == "html"), "")
    rep = j.get("report") or {}
    return rep, imgs, vid, posts, html


def build_ui(loop=None) -> gr.Blocks:
    s0 = load_settings()
    with gr.Blocks(title="SG Publisher Middleware") as ui:
        gr.Markdown("## Saham Gorengan · Publisher Middleware\nPipeline LLM (Claude routine / ChatGPT) → bundle → "
                    "QA & enrich → jadwal → Web · Instagram · Facebook · YouTube. Semua platform mulai **dry_run**; "
                    "ubah ke **live** setelah Verify lulus.")
        with gr.Tab("Dashboard"):
            st = gr.Dataframe(value=status_rows, headers=["Platform", "Mode", "Configured", "Detail"], interactive=False)
            with gr.Row():
                mode_in = {p: gr.Dropdown(list(MODES), value=s0["modes"][p], label=p) for p in PLATFORMS}
                auto = gr.Checkbox(value=s0["auto_approve"], label="Auto-approve (QA bersih + visual review)")
            msg = gr.Markdown()

            def save_modes(*vals):
                *modes, aa = vals
                update_settings({"modes": dict(zip(PLATFORMS, modes)), "auto_approve": bool(aa)})
                store.log(f"modes set to {dict(zip(PLATFORMS, modes))}, auto_approve={aa}", "warn")
                return "Saved.", status_rows()
            gr.Button("Save modes", variant="primary").click(save_modes, [*mode_in.values(), auto], [msg, st])
            up = gr.Dataframe(value=upcoming_rows, headers=["WIB", "Slug", "Platform", "Kind", "Status", "Error"],
                              interactive=False, label="Upcoming / waiting")
            tick_out = gr.JSON(label="Last tick")

            def do_tick():
                return scheduler.tick(), upcoming_rows(), status_rows()
            with gr.Row():
                gr.Button("Run scheduler tick now").click(do_tick, None, [tick_out, up, st])
                gr.Button("Refresh").click(lambda: (upcoming_rows(), status_rows()), None, [up, st])

        with gr.Tab("Jobs"):
            with gr.Row():
                jsel = gr.Dropdown(job_choices(), label="Job", scale=4)
                gr.Button("Reload list").click(lambda: gr.update(choices=job_choices()), None, jsel)
            report = gr.JSON(label="Ingest report (QA errors/warnings, schedule)")
            gallery = gr.Gallery(label="Images", columns=5, height=420)
            video = gr.Video(label="Short", height=480)
            posts = gr.Dataframe(headers=["Post", "Platform", "Kind", "WIB", "Status", "Tries", "URL", "Error"],
                                 interactive=False)
            html_path = gr.Textbox(label="Article HTML path (open in VPS desktop browser to review)", interactive=False)
            jsel.change(job_detail, jsel, [report, gallery, video, posts, html_path])
            jmsg = gr.Markdown()
            with gr.Row():
                for label, fn in (("Approve (schedule)", bundle.approve), ("Requeue dry-run/failed", bundle.requeue),
                                  ("Cancel job", bundle.cancel)):
                    gr.Button(label).click(lambda c, f=fn, l=label: f"{l}: {f(_jid(c), by='ui')}", jsel, jmsg)
            pid = gr.Textbox(label="Post id → publish now (respects platform mode)")

            def pub_now(p):
                try:
                    return f"Result: {scheduler.publish_now(p.strip())}"
                except Exception as e:  # noqa: BLE001
                    return f"Error: {e}"
            gr.Button("Publish now").click(pub_now, pid, jmsg)

        with gr.Tab("Ingest"):
            gr.Markdown(f"Bundle folder inside `{INBOX}` (contains bundle.json). The daily routine does this "
                        "automatically; use this for manual/ChatGPT bundles.")
            bpath = gr.Textbox(label="Bundle path")
            rep2 = gr.JSON()

            def run_ingest(p, dry):
                try:
                    return bundle.ingest(Path(p.strip()), dry=dry, source="ui")
                except Exception as e:  # noqa: BLE001
                    return {"error": str(e)}
            with gr.Row():
                gr.Button("Validate (render, no schedule)").click(lambda p: run_ingest(p, True), bpath, rep2)
                gr.Button("Ingest + schedule", variant="primary").click(lambda p: run_ingest(p, False), bpath, rep2)

        with gr.Tab("Credentials"):
            gr.Markdown("Disimpan terenkripsi (Fernet) di `state/credentials.enc`. Field kosong = tidak diubah. "
                        "Token tidak pernah ditampilkan ulang.")
            masked = gr.JSON(value=lambda: vault.masked(), label="Stored (masked)")
            with gr.Accordion("Meta: Facebook Page + Instagram (System User)", open=True):
                gr.Markdown("Business Settings → System users → (Admin) → Assign assets: Page **Komunitas Saham "
                            "Gorengan** (full control) + Instagram **@cuan_sahamgorengan** + App. Generate token for "
                            "the app with scopes: pages_show_list, pages_read_engagement, pages_manage_posts, "
                            "instagram_basic, instagram_content_publish, business_management (+ publish_video). "
                            "Expiry: Never.")
                with gr.Row():
                    m_tok = gr.Textbox(label="System User access token", type="password")
                    m_app = gr.Textbox(label="App ID")
                    m_sec = gr.Textbox(label="App Secret", type="password")
                    m_page = gr.Textbox(label="Page ID (optional; auto by name)")
                m_out = gr.JSON(label="Derived")

                def meta_save(tok, app, sec, page):
                    vault.put("meta", {"system_user_token": tok, "app_id": app, "app_secret": sec, "page_id": page})
                    try:
                        d = Meta(load_settings()).derive()
                        d = {k: v for k, v in d.items() if k != "page_token"}
                        store.log("meta derived: page=%s ig=%s" % (d.get("page_name"), d.get("ig_username")))
                        return d, vault.masked(), status_rows()
                    except MetaError as e:
                        return {"error": str(e)}, vault.masked(), status_rows()

                def meta_quota():
                    try:
                        return Meta(load_settings()).quota()
                    except MetaError as e:
                        return {"error": str(e)}
                with gr.Row():
                    gr.Button("Save & derive", variant="primary").click(meta_save, [m_tok, m_app, m_sec, m_page],
                                                                         [m_out, masked, st])
                    gr.Button("IG publishing quota").click(meta_quota, None, m_out)
            with gr.Accordion("YouTube (OAuth)", open=False):
                gr.Markdown(f"Google Cloud → APIs: enable **YouTube Data API v3** → OAuth client (Desktop app, or Web "
                            f"app with redirect `{s0['youtube']['redirect_uri']}`). Consent screen: add the channel "
                            "owner as test user or publish the app. Open the consent URL on any browser, approve with "
                            "the Saham Gorengan channel. With the SSH tunnel open the final page says **YouTube "
                            "connected** and you are done; paste the redirected URL below only if that page failed "
                            "to load. Klik *get consent URL* sekali saja dan pakai link terbaru.")

                def yt_status():
                    c = vault.get("youtube")
                    d = c.get("derived") or {}
                    if c.get("refresh_token") and d:
                        return f"**Status: ✅ terhubung** — {d.get('channel_title')} ({d.get('custom_url') or d.get('channel_id')})"
                    return "**Status: ⏳ belum terhubung**"
                y_status = gr.Markdown(yt_status)
                with gr.Row():
                    y_id = gr.Textbox(label="Client ID")
                    y_sec = gr.Textbox(label="Client Secret", type="password")
                    y_redirect = gr.Textbox(label="Redirect URI", value=s0["youtube"]["redirect_uri"])
                y_url = gr.Textbox(label="Consent URL (open it)", interactive=False)
                y_code = gr.Textbox(label="Paste redirected URL (or code)")
                y_out = gr.JSON()

                def yt_url(cid, sec, redirect):
                    vault.put("youtube", {"client_id": cid, "client_secret": sec})
                    if redirect.strip():
                        update_settings({"youtube": {"redirect_uri": redirect.strip()}})
                    try:
                        return YouTube(load_settings()).auth_url(), vault.masked()
                    except YouTubeError as e:
                        return f"Error: {e}", vault.masked()

                def yt_finish(code):
                    try:
                        d = YouTube(load_settings()).finish(code)
                        store.log(f"youtube connected: {d.get('channel_title')}")
                        return d, vault.masked(), status_rows(), yt_status()
                    except YouTubeError as e:
                        return {"error": str(e)}, vault.masked(), status_rows(), yt_status()

                def yt_check():
                    try:
                        return YouTube(load_settings()).derive(), yt_status()
                    except YouTubeError as e:
                        return {"error": str(e)}, yt_status()
                with gr.Row():
                    gr.Button("Save & get consent URL", variant="primary").click(yt_url, [y_id, y_sec, y_redirect],
                                                                                 [y_url, masked])
                    gr.Button("Finish authorisation").click(yt_finish, y_code, [y_out, masked, st, y_status])
                    gr.Button("Check connection").click(yt_check, None, [y_out, y_status])
            with gr.Accordion("Website: Jagoan Hosting via SSH", open=False):
                w = s0["web"]
                gr.Markdown("**Cukup klik _Auto-setup & verify_.** Middleware memakai key SSH Jagoan yang sudah jalan "
                            "di VPS ini (`../sg-*/host-ssh.sh`), mem-pin host key, mencari docroot sahamgorengan.id "
                            "sendiri (cocokkan hash file publik), lalu Verify — semuanya read-only di hosting. "
                            "Isi *SSH target* hanya bila VPS belum punya key Jagoan; deploy key baru akan dibuat dan "
                            "public key-nya ditampilkan untuk di-import di cPanel → SSH Access.")
                with gr.Row():
                    w_target = gr.Textbox(label="SSH target (opsional)", placeholder="user@host:port",
                                          value=f"{w['user']}@{w['host']}:{w['port']}" if w["host"] else "")
                    w_doc = gr.Textbox(label="Docroot (kosong = auto-detect)", value=w["docroot"])
                    w_mode = gr.Dropdown(["static", "wordpress"], value=w["mode"], label="Mode")
                with gr.Row():
                    b_auto = gr.Button("Auto-setup & verify", variant="primary")
                    b_verify = gr.Button("Verify connection")
                w_out = gr.Textbox(label="Result", lines=6)
                with gr.Accordion("Advanced (jarang perlu)", open=False):
                    with gr.Row():
                        w_key = gr.Textbox(label="Private key path (on VPS)", value=w["key_path"])
                        w_kh = gr.Textbox(label="known_hosts path", value=w["known_hosts"])
                        w_art = gr.Textbox(label="Article dir (relative)", value=w["article_dir"])
                        w_med = gr.Textbox(label="Media dir (relative)", value=w["media_dir"])
                    with gr.Row():
                        w_wproot = gr.Textbox(label="WP root (wordpress mode)", value=w["wp_root"])
                        w_php = gr.Textbox(label="PHP bin", value=w["php_bin"])
                        w_cli = gr.Textbox(label="wp-cli", value=w["wp_cli"])
                        w_bridge = gr.Textbox(label="Bridge php path", value=w["wp_bridge"])
                        w_inbox = gr.Textbox(label="WP private inbox dir", value=w["wp_inbox"])
                    with gr.Row():
                        b_save = gr.Button("Save manual fields")
                        b_key = gr.Button("Generate deploy key")
                        b_scan = gr.Button("Scan & pin host key")
                adv =[w_key, w_kh, w_art, w_med, w_wproot, w_php, w_cli, w_bridge, w_inbox]
                adv_names = ["key_path", "known_hosts", "article_dir", "media_dir", "wp_root", "php_bin", "wp_cli",
                             "wp_bridge", "wp_inbox"]

                def _web_fields():
                    c = load_settings()["web"]
                    return (gr.update(value=f"{c['user']}@{c['host']}:{c['port']}" if c["host"] else ""),
                            gr.update(value=c["docroot"]), gr.update(value=c["key_path"]),
                            gr.update(value=c["known_hosts"]))

                def web_auto(target, doc, mode):
                    update_settings({"web": {"mode": mode}})
                    try:
                        r = Web(load_settings()).autosetup(target=target.strip(), docroot=doc)
                        store.log(f"web auto-setup ok: docroot={r['saved'].get('docroot')}")
                        out = "OK ✓ siap dipakai (mode web masih dry_run sampai diubah ke live di Dashboard)\n" + \
                            json.dumps(r, indent=1)
                    except Exception as e:  # noqa: BLE001
                        out = f"Error: {e}"
                    return (out, status_rows(), *_web_fields())

                def web_save(target, doc, mode, *vals):
                    d = {k: (v.strip() if isinstance(v, str) else v) for k, v in zip(adv_names, vals)}
                    d.update(mode=mode, docroot=doc.strip())
                    try:
                        if target.strip():
                            d.update(Web.parse_target(target))
                    except WebError as e:
                        return f"Error: {e}", status_rows()
                    update_settings({"web": d})
                    return "Saved.", status_rows()

                def web_key():
                    path, pub = Web.generate_key()
                    update_settings({"web": {"key_path": path}})
                    return f"Key: {path}\nAdd this PUBLIC key in cPanel → SSH Access:\n{pub}", gr.update(value=path)

                def web_scan():
                    try:
                        kh, fp = Web(load_settings()).scan_host()
                        update_settings({"web": {"known_hosts": kh}})
                        return f"Pinned host keys in {kh}. Compare fingerprints with your hosting panel:\n{fp}", \
                            gr.update(value=kh)
                    except WebError as e:
                        return f"Error: {e}", gr.update()

                def web_verify():
                    try:
                        return json.dumps(Web(load_settings()).verify(), indent=1), status_rows()
                    except Exception as e:  # noqa: BLE001
                        return f"Error: {e}", status_rows()
                b_auto.click(web_auto, [w_target, w_doc, w_mode], [w_out, st, w_target, w_doc, w_key, w_kh])
                b_verify.click(web_verify, None, [w_out, st])
                b_save.click(web_save, [w_target, w_doc, w_mode, *adv], [w_out, st])
                b_key.click(web_key, None, [w_out, w_key])
                b_scan.click(web_scan, None, [w_out, w_kh])

        with gr.Tab("Brand kit"):
            b = brand()
            sw = "".join(f'<div style="display:inline-block;margin:4px;text-align:center"><div style="width:84px;height:54px;'
                         f'border-radius:10px;background:{v}"></div><small>{k}<br>{v}</small></div>'
                         for k, v in b["palette"].items() if isinstance(v, str))
            gr.HTML(f"<h3>Palette</h3>{sw}<h3>Typography</h3><p>{b['typography']['family']} — display 800 / body 500"
                    f"</p><h3>Mascot</h3><p>{b['mascot']['character_sheet']}</p>")
            mascots = sorted((BRAND_DIR / "mascot").glob("*.png"))
            gr.Gallery(value=[(str(p), p.stem) for p in mascots], columns=6, height=360, label="Bull poses (rig)")
            kit = BRAND_DIR / "BRAND_KIT.md"
            gr.Markdown(kit.read_text(encoding="utf-8") if kit.exists() else "BRAND_KIT.md missing")

        with gr.Tab("Logs"):
            ev = gr.Dataframe(value=lambda: [[e["ts"], e["level"], e["job_id"], e["message"][:200]]
                                             for e in store.events(200)],
                              headers=["UTC", "Level", "Job", "Message"], interactive=False)
            gr.Button("Refresh").click(lambda: [[e["ts"], e["level"], e["job_id"], e["message"][:200]]
                                                for e in store.events(200)], None, ev)
            gr.Markdown(f"API token file: `{ROOT / 'state' / 'api_token'}` · API docs: `/api/docs`")
    return ui
