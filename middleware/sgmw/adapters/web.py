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
import re
import shlex
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

import requests

from .. import store
from ..config import ROOT, STATE, article_url, media_url, update_settings


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

    # ---------- one-click setup ----------
    @staticmethod
    def parse_target(target: str) -> dict:
        """'user@host:port' (port optional) -> {user, host, port}."""
        t = target.strip().removeprefix("ssh://")
        if "@" not in t:
            raise WebError("SSH target must look like user@host or user@host:port")
        user, hp = t.split("@", 1)
        host, _, port = hp.partition(":")
        if not (user and host) or (port and not port.isdigit()):
            raise WebError("SSH target must look like user@host or user@host:port")
        return {"user": user, "host": host, "port": int(port or 22)}

    @staticmethod
    def find_identity(script: str | None = None) -> dict | None:
        """Reuse an SSH identity that already works on this VPS: a wrapper script in a sibling Saham Gorengan
        project (../sg-*/host-ssh.sh running `ssh -p PORT -i KEY -o UserKnownHostsFile=KH user@host`).
        Only sg-*/saham* folders are searched so another project's host is never picked up."""
        cands = [Path(script)] if script else sorted(
            p for pat in ("sg-*/host-ssh.sh", "sg-*/*ssh*.sh", "*saham*/*ssh*.sh")
            for p in ROOT.parent.glob(pat) if p.is_file() and p.parent != ROOT)
        for path in cands:
            try:
                text = path.read_text(errors="replace")
            except OSError:
                continue
            env = {m.group(1): m.group(2).strip("'\"") for m in re.finditer(r"^\s*(\w+)=(\S+)\s*$", text, re.M)}
            for line in text.splitlines():
                if not re.search(r"(^|\s)ssh\s", line) or line.lstrip().startswith("#"):
                    continue
                line = re.sub(r"\$\{?(\w+)\}?", lambda m: env.get(m.group(1), m.group(0)), line)
                try:
                    tok = shlex.split(line)
                except ValueError:
                    continue
                d = {"script": str(path), "port": 22}
                for i, t in enumerate(tok):
                    nxt = tok[i + 1] if i + 1 < len(tok) else ""
                    if t == "-p" and nxt.isdigit():
                        d["port"] = int(nxt)
                    elif t == "-i":
                        d["key"] = nxt
                    elif t.startswith("UserKnownHostsFile="):
                        d["known_hosts"] = t.split("=", 1)[1]
                    elif re.fullmatch(r"[\w.-]+@[\w.-]+", t):
                        d["user"], d["host"] = t.split("@")
                if d.get("host") and d.get("key") and Path(d["key"]).is_file():
                    return d
        return None

    def autosetup(self, script: str | None = None, target: str = "", docroot: str = "") -> dict:
        """Copy a working identity into state/ssh, pin host keys, detect the public docroot, save settings.
        Read-only on the host (only `test`/`sha256sum`/`echo`)."""
        found = self.find_identity(script) if not target or script else None
        d = STATE / "ssh"
        d.mkdir(parents=True, exist_ok=True)
        d.chmod(0o700)
        web: dict = {}
        if found:
            web.update(host=found["host"], user=found["user"], port=found["port"])
            for src, dst, field in ((found["key"], d / "web_ed25519", "key_path"),
                                    (found.get("known_hosts"), d / "known_hosts", "known_hosts")):
                if src and Path(src).is_file():
                    shutil.copyfile(src, dst)
                    dst.chmod(0o600)
                    web[field] = str(dst)
        if target:
            web.update(self.parse_target(target))
        self.c = {**self.c, **web}
        if not self.c.get("key_path") or not Path(self.c["key_path"]).is_file():
            path, _ = self.generate_key()
            self.c["key_path"] = web["key_path"] = path
        if not (self.c.get("host") and self.c.get("user")):
            raise WebError("no working SSH identity found on this VPS; fill 'SSH target' (user@host:port) and "
                           "authorise the deploy key shown under Advanced in cPanel → SSH Access")
        try:
            if not self.c.get("known_hosts") or not Path(self.c["known_hosts"]).is_file():
                self.c["known_hosts"], _ = self.scan_host()
                web["known_hosts"] = self.c["known_hosts"]
            web["docroot"] = docroot.strip() or self.detect_docroot()
        except WebError as e:
            update_settings({"web": web})
            pub = Path(self.c["key_path"] + ".pub")
            if "Permission denied" in str(e) and pub.is_file():
                raise WebError(f"{e}\nAuthorise this PUBLIC key in cPanel → SSH Access → Manage SSH Keys → Import, "
                               f"then run auto-setup again:\n{pub.read_text().strip()}") from e
            raise
        self.c["docroot"] = web["docroot"]
        update_settings({"web": web})
        return {"saved": web, "source": (found or {}).get("script", "manual"), "verify": self.verify()}

    def detect_docroot(self) -> str:
        """Find the folder that serves the site: same sha256 for robots.txt/favicon on disk and over HTTPS."""
        base = self.s["site"]["base_url"].rstrip("/")
        domain = base.split("//", 1)[-1].split("/")[0]
        home = self.ssh("echo $HOME").splitlines()[-1].strip()
        cands = [f"{home}/{domain}", f"{home}/public_html", f"{home}/domains/{domain}/public_html",
                 f"{home}/www", f"{home}/htdocs"]
        probes = ("robots.txt", "favicon.ico", "index.html")
        public = {}
        for f in probes:
            try:
                r = requests.get(f"{base}/{f}", timeout=20, headers={"User-Agent": "SG-Middleware/1.0"})
                if r.ok:
                    public[f] = hashlib.sha256(r.content).hexdigest()
            except requests.RequestException:
                pass
        q = " ".join(shlex.quote(f"{c}/{f}") for c in cands for f in probes)
        out = self.ssh(f"sha256sum {q} 2>/dev/null; true")
        seen = {}
        for line in out.splitlines():
            parts = line.split(None, 1)
            if len(parts) == 2:
                seen[parts[1].strip()] = parts[0]
        for c in cands:
            if any(public.get(f) and seen.get(f"{c}/{f}") == public[f] for f in probes):
                return c
        if f"{cands[0]}/index.html" in seen:  # no hash match (CDN rewrite?): accept only the folder named after the domain
            return cands[0]
        raise WebError(f"could not find the docroot of {domain} under {home}; type it in the Docroot field")

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
