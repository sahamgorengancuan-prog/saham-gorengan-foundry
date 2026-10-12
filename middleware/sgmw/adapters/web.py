"""Website publisher over SSH (Jagoan Hosting / cPanel).

Two modes:
  static    -> upload index.html to <docroot>/<article_dir>/ + media, maintain a
               sitemap (sitemap-insight.xml) and read the page back over HTTPS.
  wordpress -> upload the HTML to a private inbox and run the existing wp-cli
               article bridge (sg-wordpress-article-bridge.php) on the host.

The same SSH channel hosts media for Meta, which only accepts public URLs.
Security: key-based auth only, StrictHostKeyChecking with a pinned known_hosts,
no passwords stored, atomic uploads (tmp + mv), remote sha256 verification.
"""
from __future__ import annotations

import hashlib
import shlex
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

import requests

from .. import store
from ..config import STATE, article_url, media_url


class WebError(RuntimeError):
    pass


class Web:
    def __init__(self, settings: dict):
        self.s = settings
        self.c = settings["web"]

    # ---------- ssh plumbing ----------
    def configured(self) -> tuple[bool, str]:
        c = self.c
        missing = [k for k in ("host", "user", "key_path", "known_hosts", "docroot") if not c.get(k)]
        if missing:
            return False, "missing: " + ", ".join(missing)
        for k in ("key_path", "known_hosts"):
            if not Path(c[k]).is_file():
                return False, f"{k} file not found"
        return True, "ok"

    def _opts(self) -> list[str]:
        c = self.c
        return ["-i", c["key_path"], "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes", "-o",
                "StrictHostKeyChecking=yes", "-o", f"UserKnownHostsFile={c['known_hosts']}", "-o", "ConnectTimeout=15"]

    def ssh(self, command: str, timeout: int = 90) -> str:
        c = self.c
        cmd = ["ssh", "-T", "-p", str(c["port"])] + self._opts() + [f"{c['user']}@{c['host']}", command]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if p.returncode:
            raise WebError(f"ssh failed ({p.returncode}): {(p.stderr or p.stdout)[-300:]}")
        return p.stdout.strip()

    def scp(self, local: Path, remote: str, timeout: int = 300) -> None:
        c = self.c
        cmd = ["scp", "-q", "-P", str(c["port"])] + self._opts() + [str(local), f"{c['user']}@{c['host']}:{remote}"]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if p.returncode:
            raise WebError(f"scp failed: {(p.stderr or p.stdout)[-300:]}")

    def put(self, local: Path, remote_path: str) -> str:
        """Atomic upload + remote sha256 check. Returns sha256."""
        local = Path(local)
        sha = hashlib.sha256(local.read_bytes()).hexdigest()
        rdir = remote_path.rsplit("/", 1)[0]
        tmp = f"{remote_path}.sgtmp{int(time.time())}"
        self.ssh(f"mkdir -p {shlex.quote(rdir)}")
        self.scp(local, tmp)
        out = self.ssh(f"sha256sum {shlex.quote(tmp)} | cut -d' ' -f1 && chmod 644 {shlex.quote(tmp)} && "
                       f"mv -f {shlex.quote(tmp)} {shlex.quote(remote_path)}")
        if out.split()[0] != sha:
            raise WebError(f"remote sha256 mismatch for {remote_path}")
        return sha

    # ---------- setup helpers (used by UI) ----------
    @staticmethod
    def generate_key() -> tuple[str, str]:
        d = STATE / "ssh"
        d.mkdir(parents=True, exist_ok=True)
        key = d / "sg_web_ed25519"
        if not key.exists():
            subprocess.run(["ssh-keygen", "-t", "ed25519", "-N", "", "-C", "sg-middleware", "-f", str(key)],
                           check=True, capture_output=True, timeout=30)
        return str(key), (d / "sg_web_ed25519.pub").read_text().strip()

    def scan_host(self) -> str:
        c = self.c
        p = subprocess.run(["ssh-keyscan", "-p", str(c["port"]), "-T", "10", c["host"]], capture_output=True,
                           text=True, timeout=30)
        lines = [l for l in p.stdout.splitlines() if l and not l.startswith("#")]
        if not lines:
            raise WebError("ssh-keyscan returned nothing: " + p.stderr[-200:])
        kh = STATE / "ssh" / "known_hosts"
        kh.write_text("\n".join(lines) + "\n")
        kh.chmod(0o600)
        fp = subprocess.run(["ssh-keygen", "-lf", str(kh)], capture_output=True, text=True, timeout=10).stdout
        return str(kh), fp.strip()

    def verify(self) -> dict:
        ok, why = self.configured()
        if not ok:
            raise WebError(why)
        dr = shlex.quote(self.c["docroot"])
        out = self.ssh(f"test -d {dr} && test -w {dr} && echo DOCROOT_OK; uname -s; "
                       f"(command -v sha256sum >/dev/null && echo SHA_OK)")
        if "DOCROOT_OK" not in out or "SHA_OK" not in out:
            raise WebError("docroot not writable or sha256sum missing: " + out[-200:])
        info = {"ssh": "ok", "docroot": self.c["docroot"], "mode": self.c["mode"]}
        if self.c["mode"] == "wordpress":
            wp = self.ssh(f"cd {shlex.quote(self.c['wp_root'])} && {self.c['php_bin']} {self.c['wp_cli']} "
                          f"core version 2>/dev/null || echo WP_MISSING")
            if "WP_MISSING" in wp:
                raise WebError("wp-cli not runnable in wp_root")
            info["wordpress"] = wp.strip()
        return info

    # ---------- media hosting (Meta needs public URLs) ----------
    def host_media(self, job_id: str, slug: str, asset: dict) -> str:
        if asset.get("public_url"):
            return asset["public_url"]
        local = Path(asset["path"])
        rel = self.c["media_dir"].format(slug=slug).strip("/")
        remote = f"{self.c['docroot'].rstrip('/')}/{rel}/{local.name}"
        sha = self.put(local, remote)
        url = media_url(self.s, slug, local.name)
        self.readback(url, sha)
        store.set_asset_url(job_id, asset["asset_id"], url)
        return url

    @staticmethod
    def readback(url: str, sha: str | None = None, must_contain: str | None = None, tries: int = 4) -> None:
        last = ""
        for i in range(tries):
            try:
                r = requests.get(url, params={"sgcheck": int(time.time())}, timeout=30,
                                 headers={"Cache-Control": "no-cache", "User-Agent": "SG-Middleware/1.0"})
                if r.status_code == 200:
                    if sha and hashlib.sha256(r.content).hexdigest() != sha:
                        last = "content hash differs (CDN cache?)"
                    elif must_contain and must_contain not in r.text:
                        last = "expected marker not found"
                    else:
                        return
                else:
                    last = f"HTTP {r.status_code}"
            except requests.RequestException as e:
                last = type(e).__name__
            time.sleep(3 * (i + 1))
        raise WebError(f"public read-back failed for {url}: {last}")

    # ---------- article ----------
    def publish_article(self, job: dict, post: dict, assets: dict, dry: bool = False) -> dict:
        slug = job["slug"]
        html_asset = assets[post["payload"]["asset"]]
        html_path = Path(html_asset["path"])
        url = article_url(self.s, slug)
        images = [a for a in assets.values() if a["kind"] == "image"]
        if dry:
            return {"dry_run": True, "would_upload": [html_path.name] + [Path(a["path"]).name for a in images],
                    "url": url, "mode": self.c["mode"]}
        for a in images:  # article references hero/og/section images by public URL
            self.host_media(job["id"], slug, a)
        if self.c["mode"] == "wordpress":
            return self._publish_wordpress(slug, html_path, url)
        rel = self.c["article_dir"].format(slug=slug).strip("/")
        remote = f"{self.c['docroot'].rstrip('/')}/{rel}/index.html"
        sha = self.put(html_path, remote)
        self.readback(url, must_contain=f'data-slug="{slug}"')
        self._update_sitemap(slug)
        return {"url": url, "sha256": sha, "remote": remote, "mode": "static",
                "published_at": datetime.now(timezone.utc).isoformat(timespec="seconds")}

    def _publish_wordpress(self, slug: str, html_path: Path, url: str) -> dict:
        c = self.c
        if not (c.get("wp_root") and c.get("wp_bridge") and c.get("wp_inbox")):
            raise WebError("wordpress mode needs wp_root, wp_bridge and wp_inbox")
        remote = f"{c['wp_inbox'].rstrip('/')}/{slug}.html"
        self.put(html_path, remote)
        env = f"SG_IMPORT_SLUG={shlex.quote(slug)} SG_IMPORT_STATUS=publish SG_ARTICLE_ALLOW_LIVE=1"
        out = self.ssh(f"cd {shlex.quote(c['wp_root'])} && {env} {c['php_bin']} {c['wp_cli']} eval-file "
                       f"{shlex.quote(c['wp_bridge'])}", timeout=120)
        if "ARTICLE_IMPORTED" not in out and "IDEMPOTENT_MATCH" not in out:
            raise WebError("WordPress bridge did not confirm import: " + out[-300:])
        self.readback(url, must_contain="<h1")
        return {"url": url, "mode": "wordpress", "bridge": out[-200:]}

    def _update_sitemap(self, current_slug: str) -> None:
        with store.db() as c:
            rows = c.execute("SELECT DISTINCT j.slug, p.updated FROM posts p JOIN jobs j ON j.id=p.job_id "
                             "WHERE p.platform='web' AND p.status='published' ORDER BY p.updated DESC").fetchall()
        urls = [(article_url(self.s, current_slug), datetime.now(timezone.utc).strftime("%Y-%m-%d"))]
        urls += [(article_url(self.s, r["slug"]), (r["updated"] or "")[:10]) for r in rows if r["slug"] != current_slug]
        xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               + "".join(f"<url><loc>{escape(u)}</loc><lastmod>{d}</lastmod></url>\n" for u, d in urls if d)
               + "</urlset>\n")
        tmp = STATE / "cache" / self.c["sitemap_name"]
        tmp.write_text(xml)
        self.put(tmp, f"{self.c['docroot'].rstrip('/')}/{self.c['sitemap_name']}")
