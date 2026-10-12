"""Platform QA + deterministic enrichment.

The LLM decides *what* to say; this module guarantees *how* it lands on each
platform: lengths, hashtag limits, UTM links, disclaimers, media specs, SEO
invariants and duplicate-art detection. Errors block publishing (fail closed);
warnings are reported but do not block.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, urlparse, urlsplit, urlunsplit, parse_qsl

from PIL import Image

from .brand import brand, compliance_issues, ensure_disclaimer


def issue(level: str, msg: str, where: str = "") -> dict:
    return {"level": level, "msg": msg, "where": where}


def errors(issues: list[dict]) -> list[dict]:
    return [i for i in issues if i["level"] == "error"]


# ---------- media ----------
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dhash(path: Path, size: int = 8) -> str:
    with Image.open(path) as im:
        g = im.convert("L").resize((size + 1, size), Image.LANCZOS)
        px = list(g.getdata())
    bits = 0
    for y in range(size):
        for x in range(size):
            bits = (bits << 1) | (px[y * (size + 1) + x] > px[y * (size + 1) + x + 1])
    return f"{bits:0{size * size // 4}x}"


def hamming(a: str, b: str) -> int:
    try:
        return bin(int(a, 16) ^ int(b, 16)).count("1")
    except ValueError:
        return 64


def image_info(path: Path) -> dict:
    with Image.open(path) as im:
        im.verify()
    with Image.open(path) as im:
        return {"format": im.format, "width": im.width, "height": im.height, "mode": im.mode,
                "bytes": path.stat().st_size}


def video_info(path: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", str(path)],
                       capture_output=True, text=True, timeout=60)
    if r.returncode:
        raise ValueError("ffprobe failed: " + r.stderr[-200:])
    d = json.loads(r.stdout)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), None)
    a = next((s for s in d["streams"] if s["codec_type"] == "audio"), None)
    if not v:
        raise ValueError("no video stream")
    num, den = (v.get("r_frame_rate") or "30/1").split("/")
    return {"codec": v["codec_name"], "width": int(v["width"]), "height": int(v["height"]),
            "fps": round(float(num) / float(den or 1), 2), "duration": float(d["format"].get("duration", 0)),
            "audio": a["codec_name"] if a else None, "bytes": int(d["format"].get("size", path.stat().st_size)),
            "pix_fmt": v.get("pix_fmt")}


def check_image(asset: dict, purpose: str) -> list[dict]:
    out = []
    info = asset.get("meta") or {}
    w, h = info.get("width", 0), info.get("height", 0)
    where = asset["asset_id"]
    if info.get("format") not in ("PNG", "JPEG"):
        out.append(issue("error", f"image must be PNG/JPEG (got {info.get('format')})", where))
    if info.get("bytes", 0) > 8 * 1024 * 1024:
        out.append(issue("error", "image larger than 8 MB", where))
    if purpose in ("instagram", "facebook"):
        ratio = w / h if h else 0
        if not 0.79 <= ratio <= 1.91:
            out.append(issue("error", f"feed aspect ratio {w}x{h} outside 4:5..1.91:1", where))
        if w < 1080:
            out.append(issue("warn", f"image width {w}px < 1080px (soft on retina)", where))
    return out


def check_video(asset: dict, settings: dict) -> list[dict]:
    out = []
    v = asset.get("meta") or {}
    where = asset["asset_id"]
    q = settings["qa"]
    if v.get("codec") != "h264":
        out.append(issue("error", f"video codec must be H.264 (got {v.get('codec')})", where))
    if v.get("pix_fmt") not in (None, "yuv420p"):
        out.append(issue("warn", f"pix_fmt {v.get('pix_fmt')} (yuv420p is safest)", where))
    if v.get("height", 0) * 9 != v.get("width", 0) * 16:
        out.append(issue("error", f"vertical 9:16 required (got {v.get('width')}x{v.get('height')})", where))
    if not q["min_video_seconds"] <= v.get("duration", 0) <= q["max_video_seconds"]:
        out.append(issue("error", f"duration {v.get('duration')}s outside {q['min_video_seconds']}-"
                                  f"{q['max_video_seconds']}s", where))
    if v.get("duration", 0) > 90:
        out.append(issue("warn", "over 90 s: Reels reach and Shorts retention usually drop", where))
    if not v.get("audio"):
        out.append(issue("warn", "no audio track (Reels/Shorts perform worse silent)", where))
    if v.get("fps", 30) > 60:
        out.append(issue("error", "fps above 60", where))
    if v.get("bytes", 0) > 300 * 1024 * 1024:
        out.append(issue("error", "video larger than 300 MB", where))
    return out


def duplicate_art(asset: dict, history_hashes: list[str], min_distance: int) -> list[dict]:
    ph = asset.get("phash")
    if not ph:
        return []
    best = min((hamming(ph, h) for h in history_hashes), default=64)
    if best <= 2:
        return [issue("error", f"artwork is a near-identical reuse of a previous post (dHash distance {best})",
                      asset["asset_id"])]
    if best < min_distance:
        return [issue("warn", f"artwork very similar to a previous post (dHash distance {best})", asset["asset_id"])]
    return []


# ---------- copy helpers ----------
def norm_tags(tags, limit: int) -> list[str]:
    out = []
    for t in tags or []:
        t = re.sub(r"[^0-9a-zA-Z_]", "", str(t).lstrip("#")).lower()
        if t and t not in out:
            out.append(t)
    return out[:limit]


def with_utm(url: str, source: str, medium: str, campaign: str) -> str:
    parts = urlsplit(url)
    q = dict(parse_qsl(parts.query))
    q.setdefault("utm_source", source)
    q.setdefault("utm_medium", medium)
    q.setdefault("utm_campaign", campaign)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(q), parts.fragment))


def _append_tags(text: str, tags: list[str]) -> str:
    missing = [t for t in tags if f"#{t}" not in text.lower()]
    return text.rstrip() + ("\n\n" + " ".join(f"#{t}" for t in missing) if missing else "")


# ---------- article SEO ----------
class _SEO(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self._in_title = False
        self.desc = None
        self.canonical = []
        self.h1 = 0
        self.robots = ""
        self.ld = 0
        self.imgs_no_alt = 0
        self.og_image = None
        self.links_internal = 0
        self._in_ld = False

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "meta" and (d.get("name") or "").lower() == "description":
            self.desc = d.get("content") or ""
        elif tag == "meta" and (d.get("name") or "").lower() == "robots":
            self.robots = d.get("content") or ""
        elif tag == "meta" and d.get("property") == "og:image":
            self.og_image = d.get("content")
        elif tag == "link" and "canonical" in (d.get("rel") or "").split():
            self.canonical.append(d.get("href"))
        elif tag == "h1":
            self.h1 += 1
        elif tag == "img" and not (d.get("alt") or "").strip() and "sg-brand" not in (d.get("class") or ""):
            self.imgs_no_alt += 1
        elif tag == "script" and d.get("type") == "application/ld+json":
            self.ld += 1
        elif tag == "a" and "sahamgorengan.id" in (d.get("href") or ""):
            self.links_internal += 1

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def check_article_html(html_text: str, canonical: str, min_words: int, words: int | None = None) -> list[dict]:
    p = _SEO()
    p.feed(html_text)
    out = []
    t = p.title.strip()
    if not 25 <= len(t) <= 65:
        out.append(issue("warn" if 15 <= len(t) <= 75 else "error", f"title length {len(t)} (ideal 30-60)", "web"))
    if not p.desc:
        out.append(issue("error", "missing meta description", "web"))
    elif not 110 <= len(p.desc) <= 160:
        out.append(issue("warn" if 70 <= len(p.desc) <= 200 else "error",
                         f"meta description length {len(p.desc)} (ideal 120-155)", "web"))
    if p.canonical != [canonical]:
        out.append(issue("error", f"canonical must be exactly {canonical} (got {p.canonical})", "web"))
    if p.h1 != 1:
        out.append(issue("error", f"exactly one <h1> required (got {p.h1})", "web"))
    if "noindex" in p.robots.lower():
        out.append(issue("error", "page is noindex", "web"))
    if p.ld < 1:
        out.append(issue("warn", "no JSON-LD structured data", "web"))
    if p.imgs_no_alt:
        out.append(issue("warn", f"{p.imgs_no_alt} images without alt text", "web"))
    if not p.og_image:
        out.append(issue("warn", "no og:image (link previews will be blank)", "web"))
    if words is not None and words < min_words:
        out.append(issue("error", f"article has {words} words; minimum {min_words}", "web"))
    return out


def check_article_data(a: dict) -> list[dict]:
    out = []
    srcs = a.get("sources", [])
    hosts = set()
    for s in srcs:
        u = urlparse(s.get("url", ""))
        if u.scheme != "https" or len(u.path.strip("/")) < 6:
            out.append(issue("error", f"source {s.get('id')} must be a specific https page, not a homepage", "web"))
        hosts.add((u.hostname or "").removeprefix("www."))
    if len(srcs) < 2 or len(hosts) < 2:
        out.append(issue("error", "need >= 2 sources from >= 2 independent hosts", "web"))
    ids = {s.get("id") for s in srcs}
    for s in a.get("sections", []):
        if not set(s.get("source_refs") or []) & ids:
            out.append(issue("warn", f"section '{s.get('heading', '')[:40]}' cites no source", "web"))
    if len(a.get("sections", [])) < 5:
        out.append(issue("warn", "fewer than 5 sections", "web"))
    if len(a.get("faq", [])) < 2:
        out.append(issue("warn", "add >= 2 FAQ entries (People Also Ask coverage)", "web"))
    ex = a.get("worked_example")
    if ex and "hipotetis" not in (ex.get("label", "") + ex.get("scenario", "")).lower():
        out.append(issue("error", "worked example must be labelled HIPOTETIS", "web"))
    if not a.get("internal_links"):
        out.append(issue("warn", "no internal links to other sahamgorengan.id pages", "web"))
    return out


# ---------- per-platform enrichment ----------
def enrich(post: dict, ctx: dict) -> tuple[dict, list[dict]]:
    """Return (normalised payload, issues). ctx: settings, slug, article_url, assets, history_hashes."""
    s = ctx["settings"]
    b = brand()
    p = dict(post)
    plat, kind = p["platform"], p["kind"]
    where = f"{plat}/{kind}"
    out: list[dict] = []
    campaign = f'{s["site"]["utm_campaign_prefix"]}-{ctx["slug"]}'
    assets = ctx["assets"]

    def need_assets(ids, kind_req):
        for a in ids:
            if a not in assets:
                out.append(issue("error", f"unknown asset '{a}'", where))
            elif assets[a]["kind"] != kind_req:
                out.append(issue("error", f"asset '{a}' must be {kind_req}", where))

    if plat == "instagram":
        limit = s["qa"]["ig_max_hashtags"]
        tags = norm_tags(p.get("hashtags") or b["hashtags"]["core"], limit)
        if len(p.get("hashtags") or []) > limit:
            out.append(issue("warn", f"hashtags trimmed to {limit} (Instagram limit)", where))
        cap = ensure_disclaimer(p.get("caption", ""), short=True)
        if ctx.get("article_url") and "sahamgorengan.id" not in cap:
            cap = cap.rstrip() + "\n\nVersi lengkap + hitungan: link di bio (sahamgorengan.id)"
        cap = _append_tags(cap, tags)
        first = cap.strip().split("\n", 1)[0]
        if len(first) > 125:
            out.append(issue("warn", "first line > 125 chars; hook is cut before 'more'", where))
        if len(cap) > 2200:
            out.append(issue("error", f"caption {len(cap)} chars > 2200", where))
        p.update(caption=cap, hashtags=tags)
        if kind == "carousel":
            ids = p.get("assets", [])
            if not 2 <= len(ids) <= 10:
                out.append(issue("error", "carousel needs 2-10 images", where))
            need_assets(ids, "image")
            alts = p.get("alt_texts") or []
            if len(alts) < len(ids):
                out.append(issue("warn", "missing alt_texts for some slides (accessibility + IG SEO)", where))
            p["alt_texts"] = [a[:1000] for a in alts]
            for a in ids:
                if a in assets:
                    out += check_image(assets[a], "instagram")
        elif kind == "image":
            need_assets([p.get("asset")], "image")
            if p.get("asset") in assets:
                out += check_image(assets[p["asset"]], "instagram")
        elif kind == "reel":
            need_assets([p.get("asset")], "video")
            if p.get("asset") in assets:
                out += check_video(assets[p["asset"]], s)
            if p.get("cover"):
                need_assets([p["cover"]], "image")
            p.setdefault("share_to_feed", True)
        else:
            out.append(issue("error", f"unsupported instagram kind '{kind}'", where))
        text_all = cap + " " + p.get("first_comment", "")

    elif plat == "facebook":
        limit = s["qa"]["fb_max_hashtags"]
        tags = norm_tags(p.get("hashtags") or b["hashtags"]["core"], limit)
        msg = ensure_disclaimer(p.get("message", ""), short=True)
        link = p.get("link") or ctx.get("article_url")
        if link:
            link = with_utm(link, "facebook", "social", campaign)
            p["link"] = link
            if kind != "link" and link.split("?")[0] not in msg:
                msg = msg.rstrip() + f"\n\nBaca lengkap: {link}"
        msg = _append_tags(msg, tags)
        p.update(message=msg, hashtags=tags)
        if kind == "photos":
            ids = p.get("assets", [])
            if not 1 <= len(ids) <= 10:
                out.append(issue("error", "photos post needs 1-10 images", where))
            need_assets(ids, "image")
            for a in ids:
                if a in assets:
                    out += check_image(assets[a], "facebook")
        elif kind == "reel":
            need_assets([p.get("asset")], "video")
            if p.get("asset") in assets:
                out += check_video(assets[p["asset"]], s)
        elif kind == "link":
            if not link:
                out.append(issue("error", "link post without link", where))
        else:
            out.append(issue("error", f"unsupported facebook kind '{kind}'", where))
        text_all = msg

    elif plat == "youtube":
        if kind != "short":
            out.append(issue("error", "only YouTube 'short' is supported", where))
        need_assets([p.get("asset")], "video")
        if p.get("asset") in assets:
            out += check_video(assets[p["asset"]], s)
        title = re.sub(r"\s+", " ", p.get("title", "")).strip()
        if "#shorts" not in title.lower() and len(title) + 8 <= 100:
            title += " #Shorts"
        if len(title) > 100:
            out.append(issue("error", f"title {len(title)} chars > 100", where))
        elif len(title) > 70:
            out.append(issue("warn", "title > 70 chars gets truncated in the Shorts feed", where))
        desc = ensure_disclaimer(p.get("description", ""))
        if ctx.get("article_url") and "sahamgorengan.id" not in desc:
            desc = desc.rstrip() + "\n\nBaca versi lengkap: " + with_utm(ctx["article_url"], "youtube", "social", campaign)
        if b["links"]["telegram"] not in desc:
            desc += f"\nDiskusi gratis: {b['links']['telegram']}"
        tags = []
        total = 0
        for t in p.get("tags", []):
            t = str(t).strip().lstrip("#")
            cost = len(t) + (2 if " " in t else 0) + 1
            if t and t.lower() not in (x.lower() for x in tags) and total + cost <= 480:
                tags.append(t)
                total += cost
        hashtags = norm_tags(p.get("hashtags") or ["shorts"] + b["hashtags"]["core"], 3)
        desc = _append_tags(desc, hashtags)
        if len(desc) > 5000:
            out.append(issue("error", "description > 5000 chars", where))
        if re.search(r"[<>]", title + desc):
            out.append(issue("error", "YouTube rejects '<' or '>' in title/description", where))
        p.update(title=title, description=desc, tags=tags,
                 privacy=p.get("privacy") or s["youtube"]["privacy"],
                 category_id=str(p.get("category_id") or s["youtube"]["category_id"]),
                 made_for_kids=bool(p.get("made_for_kids", False)),
                 synthetic_media=bool(p.get("synthetic_media", s["youtube"]["synthetic_media"])))
        text_all = title + " " + desc

    elif plat == "web":
        if kind != "article":
            out.append(issue("error", "web supports kind 'article' only", where))
        a = assets.get(p.get("asset"))
        if not a or a["kind"] != "html":
            out.append(issue("error", "web post needs an html/article asset", where))
            text_all = ""
        else:
            html_text = Path(a["path"]).read_text(encoding="utf-8")
            meta = a.get("meta") or {}
            out += check_article_html(html_text, ctx["article_url"], s["qa"]["min_article_words"], meta.get("words"))
            text_all = re.sub(r"<[^>]+>", " ", html_text)
            p["url"] = ctx["article_url"]
    else:
        out.append(issue("error", f"unknown platform '{plat}'", where))
        text_all = ""

    for i in compliance_issues(text_all, require_disclaimer=plat != "web"):
        out.append(issue(i["level"], i["msg"], where))
    return p, out
