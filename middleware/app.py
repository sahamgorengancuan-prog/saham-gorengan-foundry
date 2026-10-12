#!/usr/bin/env python3
"""Saham Gorengan publisher middleware — entry point.

    python app.py serve                 # API + admin UI (127.0.0.1:18790) + scheduler loop
    python app.py ensure                # start the server in background if it is not running
    python app.py status [--json]       # platforms, modes, upcoming posts
    python app.py history [--days 120]  # used slugs/keywords/questions (for the LLM to avoid repeats)
    python app.py validate <bundle_dir> # render + QA, no scheduling
    python app.py ingest <bundle_dir>   # render + QA + schedule
    python app.py tick                  # run due posts once (cron alternative)
    python app.py approve|cancel|requeue <job_id>
    python app.py publish-now <post_id>
    python app.py render-card <spec.json> <out.png>
    python app.py render-video <storyboard.json> <out_dir>
    python app.py brand-export          # mascot pose + prop reference PNGs into brand/
    python app.py pool add <file.json>  # merge Ubersuggest results into the keyword pool
    python app.py pool top              # best unused opportunities (high volume, low difficulty)
    python app.py secrets --show        # print API token + UI login (local only)

No LLM API key lives here: the LLM work happens in the scheduled Claude routine or
ChatGPT, which drop bundles into inbox/ and call `ingest`.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sgmw import __version__  # noqa: E402
from sgmw.config import LOGS, ROOT, STATE, TZ, ensure_dirs, load_settings  # noqa: E402

PIDFILE = STATE / "server.pid"


def _listening(host: str, port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(1.5)
        return s.connect_ex((host, port)) == 0


def cmd_serve(a):
    import uvicorn
    from sgmw import scheduler, store
    from sgmw.api import create_app
    ensure_dirs()
    s = load_settings()
    loop = scheduler.Loop(60)
    loop.start()
    PIDFILE.write_text(str(os.getpid()))
    store.log(f"server start v{__version__} on {s['bind']}:{s['port']}")
    app = create_app(loop, with_ui=not a.no_ui)
    uvicorn.run(app, host=s["bind"], port=int(s["port"]), log_level="warning", proxy_headers=False)


def cmd_ensure(a):
    s = load_settings()
    if _listening(s["bind"], int(s["port"])):
        print(json.dumps({"server": "running", "url": f"http://{s['bind']}:{s['port']}/ui/"}))
        return
    ensure_dirs()
    LOGS.mkdir(exist_ok=True)
    log = open(LOGS / "server.log", "ab")
    subprocess.Popen([sys.executable, str(ROOT / "app.py"), "serve"], cwd=str(ROOT), stdout=log, stderr=log,
                     stdin=subprocess.DEVNULL, start_new_session=True)
    for _ in range(40):
        time.sleep(1)
        if _listening(s["bind"], int(s["port"])):
            print(json.dumps({"server": "started", "url": f"http://{s['bind']}:{s['port']}/ui/"}))
            return
    print(json.dumps({"server": "failed to start", "log": str(LOGS / "server.log")}))
    sys.exit(1)


def cmd_stop(a):
    if PIDFILE.exists():
        pid = int(PIDFILE.read_text())
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"stopped {pid}")
        except ProcessLookupError:
            print("not running")
        PIDFILE.unlink(missing_ok=True)


def cmd_status(a):
    from sgmw import scheduler, store
    from datetime import datetime
    s = load_settings()
    data = {"version": __version__, "server": _listening(s["bind"], int(s["port"])),
            "auto_approve": s["auto_approve"], "platforms": scheduler.platform_status(s),
            "upcoming": [{"wib": datetime.fromisoformat(p["publish_at"]).astimezone(TZ).strftime("%Y-%m-%d %H:%M"),
                          "slug": p["slug"], "platform": p["platform"], "kind": p["kind"], "status": p["status"],
                          "error": (p.get("error") or "")[:160]} for p in store.upcoming(30)],
            "recent_jobs": [{k: j[k] for k in ("id", "status", "title")} for j in store.list_jobs(7)]}
    if a.json:
        print(json.dumps(data, ensure_ascii=False, indent=1))
        return
    print(f"SG middleware v{__version__} · server {'UP' if data['server'] else 'DOWN'} · auto_approve={s['auto_approve']}")
    for p in data["platforms"]:
        print(f"  {p['platform']:<10} {p['mode']:<8} {'OK ' if p['configured'] else '-- '} {p['detail']}")
    print("Upcoming:")
    for u in data["upcoming"]:
        print(f"  {u['wib']}  {u['platform']:<9} {u['kind']:<8} {u['status']:<16} {u['slug']} {u['error']}")


def cmd_history(a):
    from sgmw import store
    h = store.history(a.days)
    print(json.dumps({"days": a.days, "jobs": h["jobs"]}, ensure_ascii=False, indent=1))


def cmd_ingest(a, dry=False):
    from sgmw import bundle
    try:
        rep = bundle.ingest(Path(a.dir), dry=dry, source="cli", log=lambda m: print(m, file=sys.stderr))
    except bundle.BundleError as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(2)
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    if rep["errors"]:
        sys.exit(3)


def cmd_tick(a):
    from sgmw import scheduler
    print(json.dumps(scheduler.tick(), indent=1))


def cmd_job(a):
    from sgmw import bundle
    print(getattr(bundle, a.cmd)(a.job_id, by="cli"))


def cmd_publish_now(a):
    from sgmw import scheduler
    print(scheduler.publish_now(a.post_id))


def cmd_render_card(a):
    from sgmw.render import card
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    print(card.render_card(spec, Path(a.out), seed=a.seed))


def cmd_render_video(a):
    from sgmw.render import video
    sb = json.loads(Path(a.storyboard).read_text(encoding="utf-8"))
    print(json.dumps(video.render_short(sb, Path(a.out), seed=a.seed), ensure_ascii=False, indent=1))


def cmd_brand_export(a):
    from sgmw.render import card, mascot, props
    out = ROOT / "brand" / "mascot"
    out.mkdir(parents=True, exist_ok=True)
    combos = [("explain", "smirk", "none"), ("celebrate", "happy", "none"), ("think", "think", "glasses"),
              ("warn", "serious", "tie"), ("present", "smirk", "none"), ("shrug", "worried", "none"),
              ("wave", "happy", "headset"), ("double_point", "shock", "none"), ("idle", "smirk", "none")]
    for pose, expr, acc in combos:
        svg = mascot.mascot_svg(pose, expr, acc, width=800)
        (out / f"bull-{pose}-{expr}.svg").write_text(svg)
        card.rasterize(svg, out / f"bull-{pose}-{expr}.png")
        _alpha_png(out / f"bull-{pose}-{expr}.svg", out / f"bull-{pose}-{expr}.png")
    pdir = ROOT / "brand" / "props"
    pdir.mkdir(exist_ok=True)
    for name in props.PROPS:
        svg = props.prop_svg(name, 240)
        (pdir / f"{name}.svg").write_text(svg)
    print(f"exported {len(combos)} mascot poses to {out} and {len(props.PROPS)} props to {pdir}")


def _alpha_png(svg: Path, png: Path) -> None:
    """Re-render with transparency for reference use (rasterize() flattens to navy for social)."""
    import shutil
    if shutil.which("rsvg-convert"):
        from sgmw.brand import fontconfig_file
        subprocess.run(["rsvg-convert", "-f", "png", "-o", str(png), str(svg)], check=True,
                       env=dict(os.environ, FONTCONFIG_FILE=str(fontconfig_file())))


def cmd_pool(a):
    from sgmw import pool
    if a.action == "add":
        data = json.loads(Path(a.file).read_text(encoding="utf-8"))
        rows = data.get("suggestions", []) + data.get("searched_keywords", []) if isinstance(data, dict) else data
        print(json.dumps(pool.add(rows, source=a.source, cluster=a.cluster)))
    elif a.action == "top":
        print(json.dumps(pool.top(a.n, a.max_sd, a.min_volume, a.unmeasured), ensure_ascii=False, indent=1))
    elif a.action == "use":
        pool.mark_used(a.file, a.day or __import__("datetime").date.today().isoformat())
        print("marked")


def cmd_secrets(a):
    from sgmw import vault
    if not a.show:
        print(f"API token: {STATE / 'api_token'} · UI login: {STATE / 'ui_auth.json'} (use --show to print)")
        return
    u, p = vault.ui_auth()
    print(json.dumps({"api_token": vault.api_token(), "ui_user": u, "ui_password": p}))


def main():
    ap = argparse.ArgumentParser(description="Saham Gorengan publisher middleware")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("serve"); p.add_argument("--no-ui", action="store_true"); p.set_defaults(fn=cmd_serve)
    sub.add_parser("ensure").set_defaults(fn=cmd_ensure)
    sub.add_parser("stop").set_defaults(fn=cmd_stop)
    p = sub.add_parser("status"); p.add_argument("--json", action="store_true"); p.set_defaults(fn=cmd_status)
    p = sub.add_parser("history"); p.add_argument("--days", type=int, default=120); p.set_defaults(fn=cmd_history)
    p = sub.add_parser("validate"); p.add_argument("dir"); p.set_defaults(fn=lambda a: cmd_ingest(a, True))
    p = sub.add_parser("ingest"); p.add_argument("dir"); p.set_defaults(fn=cmd_ingest)
    sub.add_parser("tick").set_defaults(fn=cmd_tick)
    for c in ("approve", "cancel", "requeue"):
        p = sub.add_parser(c); p.add_argument("job_id"); p.set_defaults(fn=cmd_job)
    p = sub.add_parser("publish-now"); p.add_argument("post_id"); p.set_defaults(fn=cmd_publish_now)
    p = sub.add_parser("render-card"); p.add_argument("spec"); p.add_argument("out"); p.add_argument("--seed", default="sg")
    p.set_defaults(fn=cmd_render_card)
    p = sub.add_parser("render-video"); p.add_argument("storyboard"); p.add_argument("out")
    p.add_argument("--seed", default="sg"); p.set_defaults(fn=cmd_render_video)
    sub.add_parser("brand-export").set_defaults(fn=cmd_brand_export)
    p = sub.add_parser("pool", help="keyword pool: add <ubersuggest.json> | top | use <keyword>")
    p.add_argument("action", choices=["add", "top", "use"]); p.add_argument("file", nargs="?")
    p.add_argument("--source", default="ubersuggest"); p.add_argument("--cluster", default="")
    p.add_argument("--n", type=int, default=40); p.add_argument("--max-sd", type=int, default=35)
    p.add_argument("--min-volume", type=int, default=500); p.add_argument("--unmeasured", action="store_true")
    p.add_argument("--day"); p.set_defaults(fn=cmd_pool)
    p = sub.add_parser("secrets"); p.add_argument("--show", action="store_true"); p.set_defaults(fn=cmd_secrets)
    a = ap.parse_args()
    if not a.cmd:
        a = ap.parse_args(["serve"])
    a.fn(a)


if __name__ == "__main__":
    main()
