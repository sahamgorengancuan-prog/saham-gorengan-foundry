"""Branded card templates (SVG -> PNG via rsvg-convert).

A card spec is plain JSON so any LLM (Claude routine, ChatGPT) can author it:

    {"template": "cover", "format": "feed_portrait", "page": "1/8",
     "data": {"eyebrow": "Edukasi Saham", "headline": "Kenapa *saham gorengan* bisa ARA?",
              "subhead": "...", "mascot": {"pose": "think", "expression": "think"}}}

Templates: cover, point, stat, myth_fact, checklist, example, quote, illustration, cta,
reel_cover, yt_thumb, og, web_hero. Frame, fonts, colours and mascot are fixed by
the brand kit; only content changes, which keeps every post on-brand.
"""
from __future__ import annotations

import base64
import hashlib
import io
import random
import shutil
import subprocess
from pathlib import Path
from xml.sax.saxutils import escape

from ..brand import brand, fontconfig_file
from ..config import BRAND_DIR
from . import mascot as M
from . import props as P
from . import text as T

NAVY, DEEP, BLUE = "#05183A", "#09367B", "#0B438E"
RED, GOLD, WHITE = "#ED2A3C", "#FFCD35", "#FAFDFF"
SOFT, MUTED, PINK, GREEN, INK = "#D0E3FF", "#B8D3FF", "#FF7182", "#48E5AD", "#0A1633"

TEMPLATES: dict = {}


def template(name):
    def deco(fn):
        TEMPLATES[name] = fn
        return fn
    return deco


def fmt_size(fmt: str) -> tuple[int, int, dict]:
    f = brand()["formats"][fmt]
    return f["w"], f["h"], f["safe"]


# ---------- shared frame pieces ----------
def _defs(w: int, h: int) -> str:
    return (
        '<defs>'
        f'<linearGradient id="bgNavy" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#071D48"/>'
        f'<stop offset=".62" stop-color="{DEEP}"/><stop offset="1" stop-color="#0B58BC"/></linearGradient>'
        f'<linearGradient id="bgDeep" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{NAVY}"/>'
        f'<stop offset="1" stop-color="#0A2A63"/></linearGradient>'
        f'<linearGradient id="bgRed" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#B3122A"/>'
        f'<stop offset="1" stop-color="{RED}"/></linearGradient>'
        f'<linearGradient id="bgLight" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{WHITE}"/>'
        f'<stop offset="1" stop-color="#E4EEFF"/></linearGradient>'
        '<radialGradient id="glow"><stop offset="0" stop-color="#3D7BFF" stop-opacity=".55"/>'
        '<stop offset=".6" stop-color="#1B5BD0" stop-opacity=".18"/><stop offset="1" stop-color="#1B5BD0" stop-opacity="0"/>'
        '</radialGradient>'
        '<radialGradient id="glowGold"><stop offset="0" stop-color="#FFCD35" stop-opacity=".45"/>'
        '<stop offset="1" stop-color="#FFCD35" stop-opacity="0"/></radialGradient>'
        f'<linearGradient id="fadeBottom" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{NAVY}" stop-opacity="0"/>'
        f'<stop offset=".45" stop-color="{NAVY}" stop-opacity=".85"/><stop offset="1" stop-color="{NAVY}"/></linearGradient>'
        '</defs>')


def background(w: int, h: int, kind: str = "navy", seed: str = "sg") -> str:
    fill = {"navy": "url(#bgNavy)", "deep": "url(#bgDeep)", "red": "url(#bgRed)", "light": "url(#bgLight)"}.get(kind, "url(#bgNavy)")
    rnd = random.Random(hashlib.sha256(seed.encode()).hexdigest())
    dark = kind != "light"
    ring = "#FFFFFF" if dark else "#0B438E"
    parts = [f'<rect width="{w}" height="{h}" fill="{fill}"/>']
    # Concentric rings (site signature, top-right)
    cx, cy, r = w * 0.92, h * 0.06, w * 0.36
    parts.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r:.0f}" fill="none" stroke="{ring}" stroke-opacity=".12" stroke-width="2"/>')
    parts.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r + 60:.0f}" fill="none" stroke="{ring}" stroke-opacity=".06" stroke-width="60"/>')
    parts.append(f'<circle cx="{cx:.0f}" cy="{cy:.0f}" r="{r + 150:.0f}" fill="none" stroke="{ring}" stroke-opacity=".035" stroke-width="80"/>')
    # Kurzgesagt-style star dust
    for _ in range(int(w * h / 26000)):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        rr = rnd.choice((1.6, 2.2, 3.0, 4.2))
        op = rnd.uniform(.12, .45) if dark else rnd.uniform(.06, .16)
        parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{rr}" fill="{ring}" fill-opacity="{op:.2f}"/>')
    return "".join(parts)


_LOGO_CACHE: dict = {}


def logo(x: float, y: float, size: float = 56) -> str:
    p = BRAND_DIR / "reference" / "logo-ksg.png"
    if p.exists():
        if "uri" not in _LOGO_CACHE:
            _LOGO_CACHE["uri"] = "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()
        return (f'<circle cx="{x + size / 2}" cy="{y + size / 2}" r="{size / 2 + 3}" fill="{WHITE}"/>'
                f'<image href="{_LOGO_CACHE["uri"]}" x="{x}" y="{y}" width="{size}" height="{size}"/>')
    return (f'<circle cx="{x + size / 2}" cy="{y + size / 2}" r="{size / 2}" fill="{RED}" stroke="{WHITE}" stroke-width="3"/>'
            f'<text x="{x + size / 2}" y="{y + size * 0.66}" text-anchor="middle" font-family="{T.FAMILY}" '
            f'font-weight="800" font-size="{size * 0.42:.0f}" fill="{WHITE}">SG</text>')


def header(w: int, safe: dict, page: str | None = None, dark: bool = True) -> str:
    fg = WHITE if dark else INK
    x, y = safe["left"], safe["top"] - 16
    out = [logo(x, y, 56),
           f'<text x="{x + 72}" y="{y + 37}" font-family="{T.FAMILY}" font-weight="800" font-size="24" '
           f'fill="{fg}" letter-spacing="0.12em">SAHAM GORENGAN</text>']
    if page:
        pw = T.width(page, 22, 800) + 36
        out.append(f'<rect x="{w - safe["right"] - pw}" y="{y + 8}" width="{pw:.0f}" height="40" rx="20" '
                   f'fill="{"#FFFFFF" if dark else INK}" fill-opacity=".14"/>'
                   f'<text x="{w - safe["right"] - pw / 2:.0f}" y="{y + 36}" text-anchor="middle" font-family="{T.FAMILY}" '
                   f'font-weight="800" font-size="22" fill="{fg}">{escape(page)}</text>')
    return "".join(out)


def footer(w: int, h: int, safe: dict, dark: bool = True, text: str | None = None) -> str:
    fg = MUTED if dark else BLUE
    t = text or f'{brand()["handles"]["instagram"]}  ·  sahamgorengan.id'
    return (f'<text x="{safe["left"]}" y="{h - safe["bottom"] + 40}" font-family="{T.FAMILY}" font-weight="700" '
            f'font-size="22" fill="{fg}">{escape(t)}</text>')


def pill(text_: str, x: float, y: float, fill: str = RED, fg: str = WHITE, size: int = 24) -> tuple[str, float]:
    tw = T.width(text_.upper(), size, 800, tracking=0.15)
    w = tw + 44
    return (f'<rect x="{x}" y="{y}" width="{w:.0f}" height="{size + 28}" rx="{(size + 28) / 2}" fill="{fill}"/>'
            + T.label(text_, x + 22, y + 13, size, fg), w)


def mascot_spot(spec: dict | None, x: float, y: float, height: float, glow: bool = True) -> str:
    if not spec:
        return ""
    g = (f'<circle cx="{x}" cy="{y - height * 0.52:.0f}" r="{height * 0.55:.0f}" fill="url(#glow)"/>' if glow else "")
    return g + M.place(spec.get("pose", "explain"), spec.get("expression", "smirk"), x, y, height,
                       accessory=spec.get("accessory", "none"), flip=bool(spec.get("flip")))


def art_box(art: dict | None, x: float, y: float, w: float, h: float) -> str:
    """Embed LLM-authored SVG art. art = {"svg": "<g>..</g>", "viewbox": "0 0 1000 600"} or {"props": [...]}"""
    if not art:
        return ""
    vb = art.get("viewbox", f"0 0 {w:.0f} {h:.0f}")
    inner = art.get("svg", "")
    for pr in art.get("props", []):
        inner += P.prop(pr["name"], pr["x"], pr["y"], pr.get("size", 180), pr.get("rotate", 0))
    if art.get("mascot"):
        m = art["mascot"]
        inner += M.place(m.get("pose", "explain"), m.get("expression", "smirk"), m["x"], m["y"], m["height"],
                         m.get("accessory", "none"), bool(m.get("flip")))
    return (f'<svg x="{x:.0f}" y="{y:.0f}" width="{w:.0f}" height="{h:.0f}" viewBox="{vb}" '
            f'preserveAspectRatio="xMidYMid meet" overflow="hidden">{inner}</svg>')


def wrap_svg(w: int, h: int, body: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{w}" height="{h}" viewBox="0 0 {w} {h}">{_defs(w, h)}{body}</svg>')


# ---------- templates ----------
@template("cover")
def t_cover(d: dict, fmt: str, page: str | None, seed: str) -> str:
    w, h, s = fmt_size(fmt)
    cw = w - s["left"] - s["right"]
    body = [background(w, h, d.get("bg", "navy"), seed), header(w, s, page)]
    y = s["top"] + 120
    if d.get("eyebrow"):
        pv, _ = pill(d["eyebrow"], s["left"], y)
        body.append(pv)
        y += 92
    svg, y = T.block(d["headline"], s["left"], y, cw, 96, 800, WHITE, max_lines=5, line_height=1.06,
                     size_min=60)
    body.append(svg)
    if d.get("subhead"):
        sub, y = T.block(d["subhead"], s["left"], y + 26, cw * 0.56, 36, 600, SOFT, max_lines=5, size_min=28)
        body.append(sub)
    body.append(mascot_spot(d.get("mascot", {"pose": "explain", "expression": "smirk"}), w - 290, h + 10, 620))
    if d.get("swipe", True):
        sy = h - s["bottom"] - 70
        tw = T.width("GESER", 22, 800, tracking=0.15)
        body.append(f'<rect x="{s["left"]}" y="{sy}" width="{tw + 92:.0f}" height="50" rx="25" fill="{WHITE}"/>'
                    + T.label("Geser", s["left"] + 22, sy + 12, 22, NAVY)
                    + P.icon("arrow_right", s["left"] + tw + 44, sy + 9, 32, NAVY))
    return wrap_svg(w, h, "".join(body))


@template("point")
def t_point(d: dict, fmt: str, page: str | None, seed: str) -> str:
    w, h, s = fmt_size(fmt)
    cw = w - s["left"] - s["right"]
    has_art = bool(d.get("art"))
    body = [background(w, h, d.get("bg", "navy"), seed), header(w, s, page)]
    y = s["top"] + 110
    if d.get("number") is not None:
        n = str(d["number"])
        body.append(f'<circle cx="{s["left"] + 46}" cy="{y + 46}" r="46" fill="{RED}" stroke="{WHITE}" stroke-width="4"/>'
                    f'<text x="{s["left"] + 46}" y="{y + 64}" text-anchor="middle" font-family="{T.FAMILY}" '
                    f'font-weight="800" font-size="50" fill="{WHITE}">{escape(n)}</text>')
        if d.get("eyebrow"):
            body.append(T.label(d["eyebrow"], s["left"] + 116, y + 32, 24, PINK))
        y += 124
    elif d.get("eyebrow"):
        body.append(T.label(d["eyebrow"], s["left"], y, 24, PINK))
        y += 52
    svg, y = T.block(d["heading"], s["left"], y, cw, 66, 800, WHITE, max_lines=3, line_height=1.08, size_min=46)
    body.append(svg)
    body_w = cw if has_art or not d.get("mascot") else cw * 0.64
    txt, y = T.block(d.get("body", ""), s["left"], y + 26, body_w, 38, 500, SOFT, max_lines=9, size_min=30)
    body.append(txt)
    if has_art:
        top = max(y + 30, h * 0.56)
        body.append(art_box(d["art"], s["left"], top, cw, h - top - s["bottom"] - 50))
    elif d.get("mascot"):
        body.append(mascot_spot(d["mascot"], w - 230, h + 10, 470))
    body.append(footer(w, h, s))
    return wrap_svg(w, h, "".join(body))


@template("stat")
def t_stat(d: dict, fmt: str, page: str | None, seed: str) -> str:
    w, h, s = fmt_size(fmt)
    cw = w - s["left"] - s["right"]
    body = [background(w, h, d.get("bg", "deep"), seed), header(w, s, page)]
    y = s["top"] + 130
    if d.get("eyebrow"):
        body.append(T.label(d["eyebrow"], s["left"], y, 24, PINK))
        y += 60
    size, lines = T.fit(d["value"], cw, 1, 250, 110, 800)
    body.append(f'<circle cx="{s["left"] + 200}" cy="{y + size * 0.5:.0f}" r="{size:.0f}" fill="url(#glowGold)"/>')
    sv, y = T.svg_lines(lines, s["left"], y, size, 800, GOLD, GOLD, 1.0)
    body.append(sv)
    lab, y = T.block(d.get("label", ""), s["left"], y + 16, cw, 54, 800, WHITE, max_lines=3, line_height=1.1, size_min=40)
    body.append(lab)
    ctx, y = T.block(d.get("context", ""), s["left"], y + 22, cw * 0.62, 36, 500, SOFT, max_lines=7, size_min=28)
    body.append(ctx)
    body.append(mascot_spot(d.get("mascot", {"pose": "present", "expression": "smirk"}), w - 290, h + 10, 470))
    if d.get("source"):
        body.append(T.block("Sumber: " + d["source"], s["left"], h - s["bottom"] - 34, cw * 0.6, 22, 600, MUTED,
                            max_lines=2)[0])
    else:
        body.append(footer(w, h, s))
    return wrap_svg(w, h, "".join(body))


@template("myth_fact")
def t_myth(d: dict, fmt: str, page: str | None, seed: str) -> str:
    w, h, s = fmt_size(fmt)
    cw = w - s["left"] - s["right"]
    body = [background(w, h, d.get("bg", "navy"), seed), header(w, s, page)]
    top = s["top"] + 100
    gap = 36
    ph = (h - top - s["bottom"] - 70 - gap) / 2
    for i, (lab, txt, col, ic) in enumerate((("Mitos", d["myth"], RED, "x"), ("Fakta", d["fact"], GOLD, "check"))):
        py = top + i * (ph + gap)
        body.append(f'<rect x="{s["left"]}" y="{py:.0f}" width="{cw}" height="{ph:.0f}" rx="28" fill="{col}" '
                    f'fill-opacity=".13" stroke="{col}" stroke-width="4"/>')
        chip, cwid = pill(lab, s["left"] + 34, py + 34, col, WHITE if col == RED else NAVY, 26)
        body.append(chip)
        body.append(f'<circle cx="{s["left"] + cw - 70}" cy="{py + 64:.0f}" r="34" fill="{col}"/>'
                    + P.icon(ic, s["left"] + cw - 92, py + 42, 44, WHITE if col == RED else NAVY))
        tx, _ = T.block(txt, s["left"] + 34, py + 120, cw - 68, 44 if i == 0 else 38, 800 if i == 0 else 600,
                        WHITE, max_lines=6, size_min=28, line_height=1.25)
        body.append(tx)
    body.append(footer(w, h, s))
    return wrap_svg(w, h, "".join(body))


@template("checklist")
def t_checklist(d: dict, fmt: str, page: str | None, seed: str) -> str:
    w, h, s = fmt_size(fmt)
    cw = w - s["left"] - s["right"]
    body = [background(w, h, d.get("bg", "navy"), seed), header(w, s, page)]
    y = s["top"] + 110
    if d.get("eyebrow"):
        body.append(T.label(d["eyebrow"], s["left"], y, 24, PINK))
        y += 54
    hv, y = T.block(d["heading"], s["left"], y, cw, 64, 800, WHITE, max_lines=3, line_height=1.08, size_min=46)
    body.append(hv)
    y += 30
    items = d.get("items", [])[:6]
    avail = h - y - s["bottom"] - 70
    per = avail / max(len(items), 1)
    size = 36 if per > 150 else 32
    for it in items:
        body.append(f'<circle cx="{s["left"] + 30}" cy="{y + 30:.0f}" r="30" fill="{GOLD}"/>'
                    + P.icon("check", s["left"] + 12, y + 12, 36, NAVY))
        tv, ny = T.block(it, s["left"] + 84, y + 4, cw - 84, size, 600, WHITE, max_lines=4, line_height=1.3)
        body.append(tv)
        y = max(ny, y + 64) + 26
    body.append(footer(w, h, s))
    return wrap_svg(w, h, "".join(body))


@template("example")
def t_example(d: dict, fmt: str, page: str | None, seed: str) -> str:
    w, h, s = fmt_size(fmt)
    cw = w - s["left"] - s["right"]
    body = [background(w, h, d.get("bg", "deep"), seed), header(w, s, page)]
    y = s["top"] + 110
    pv, _ = pill(d.get("label", "Simulasi hipotetis"), s["left"], y, GOLD, NAVY, 24)
    body.append(pv)
    y += 84
    hv, y = T.block(d["heading"], s["left"], y, cw, 58, 800, WHITE, max_lines=3, line_height=1.1, size_min=42)
    body.append(hv)
    if d.get("scenario"):
        sv, y = T.block(d["scenario"], s["left"], y + 18, cw, 32, 500, SOFT, max_lines=4, size_min=26)
        body.append(sv)
    y += 24
    for i, step in enumerate(d.get("steps", [])[:5], 1):
        body.append(f'<rect x="{s["left"]}" y="{y:.0f}" width="{cw}" height="4" fill="#FFFFFF" fill-opacity=".08"/>')
        body.append(f'<text x="{s["left"]}" y="{y + 52:.0f}" font-family="{T.FAMILY}" font-weight="800" font-size="34" '
                    f'fill="{GOLD}">{i:02d}</text>')
        tv, ny = T.block(step, s["left"] + 72, y + 20, cw - 72, 32, 600, WHITE, max_lines=3, line_height=1.3)
        body.append(tv)
        y = ny + 18
    if d.get("result"):
        rh = 150
        ry = min(y + 16, h - s["bottom"] - 70 - rh)
        body.append(f'<rect x="{s["left"]}" y="{ry:.0f}" width="{cw}" height="{rh}" rx="24" fill="{WHITE}"/>')
        body.append(T.block(d["result"], s["left"] + 30, ry + 26, cw - 60, 36, 800, NAVY, max_lines=3,
                            size_min=26, hl_fill=RED, line_height=1.2)[0])
    body.append(footer(w, h, s, text="Simulasi hipotetis, bukan ajakan beli/jual."))
    return wrap_svg(w, h, "".join(body))


@template("quote")
def t_quote(d: dict, fmt: str, page: str | None, seed: str) -> str:
    w, h, s = fmt_size(fmt)
    cw = w - s["left"] - s["right"]
    body = [background(w, h, d.get("bg", "navy"), seed), header(w, s, page)]
    y = s["top"] + 120
    body.append(f'<text x="{s["left"] - 6}" y="{y + 170}" font-family="{T.FAMILY}" font-weight="800" '
                f'font-size="260" fill="{GOLD}">“</text>')
    qv, y = T.block(d["text"], s["left"], y + 190, cw, 60, 800, WHITE, max_lines=7, line_height=1.16, size_min=40)
    body.append(qv)
    body.append(T.label(d.get("by", "Bull · Saham Gorengan"), s["left"], y + 30, 24, PINK))
    body.append(mascot_spot(d.get("mascot", {"pose": "think", "expression": "think"}), w - 230, h + 10, 440))
    body.append(footer(w, h, s))
    return wrap_svg(w, h, "".join(body))


@template("illustration")
def t_illustration(d: dict, fmt: str, page: str | None, seed: str) -> str:
    """Full-bleed topic illustration (art viewbox should match the format) + caption band."""
    w, h, s = fmt_size(fmt)
    cw = w - s["left"] - s["right"]
    art = dict(d.get("art") or {})
    art.setdefault("viewbox", f"0 0 {w} {h}")
    body = [background(w, h, d.get("bg", "deep"), seed), art_box(art, 0, 0, w, h)]
    band = h * 0.36
    body.append(f'<rect x="0" y="{h - band:.0f}" width="{w}" height="{band:.0f}" fill="url(#fadeBottom)"/>')
    body.append(header(w, s, page))
    y = h - band * 0.62
    if d.get("headline"):
        hv, y = T.block(d["headline"], s["left"], y, cw, 64, 800, WHITE, max_lines=2, line_height=1.06, size_min=44)
        body.append(hv)
    if d.get("caption"):
        body.append(T.block(d["caption"], s["left"], y + 12, cw, 32, 600, SOFT, max_lines=3, size_min=26)[0])
    return wrap_svg(w, h, "".join(body))


@template("cta")
def t_cta(d: dict, fmt: str, page: str | None, seed: str) -> str:
    w, h, s = fmt_size(fmt)
    cw = w - s["left"] - s["right"]
    b = brand()
    body = [background(w, h, d.get("bg", "navy"), seed), header(w, s, page)]
    y = s["top"] + 120
    hv, y = T.block(d.get("headline", "Simpan & *bagikan*"), s["left"], y, cw, 84, 800, WHITE, max_lines=2,
                    line_height=1.05, size_min=56)
    body.append(hv)
    rows = d.get("rows") or [("bookmark", "Simpan post ini buat dibaca ulang"),
                             ("share", "Kirim ke teman yang masih suka FOMO"),
                             ("link", "Versi lengkap + hitungan: sahamgorengan.id"),
                             ("telegram", "Diskusi gratis: t.me/sahamgorengancuan")]
    y += 30
    for ic, tx in rows:
        body.append(f'<rect x="{s["left"]}" y="{y:.0f}" width="{cw * 0.62:.0f}" height="84" rx="20" fill="#FFFFFF" fill-opacity=".09"/>'
                    f'<circle cx="{s["left"] + 42}" cy="{y + 42:.0f}" r="26" fill="{RED}"/>'
                    + P.icon(ic, s["left"] + 28, y + 28, 28, WHITE))
        body.append(T.block(tx, s["left"] + 86, y + 12, cw * 0.62 - 100, 26, 700, WHITE, max_lines=2,
                            line_height=1.25, size_min=22)[0])
        y += 100
    body.append(mascot_spot(d.get("mascot", {"pose": "wave", "expression": "happy"}), w - 250, h + 10, 600))
    disc = d.get("disclaimer", b["compliance"]["default_disclaimer"])
    body.append(T.block(disc, s["left"], h - s["bottom"] - 70, cw * 0.55, 22, 600, MUTED, max_lines=4,
                        line_height=1.3)[0])
    return wrap_svg(w, h, "".join(body))


@template("reel_cover")
def t_reel_cover(d: dict, fmt: str, page: str | None, seed: str) -> str:
    w, h, s = fmt_size("vertical")
    cw = w - s["left"] - s["right"]
    body = [background(w, h, d.get("bg", "navy"), seed)]
    body.append(logo(s["left"], s["top"] - 40, 64))
    body.append(f'<text x="{s["left"] + 82}" y="{s["top"] - 0}" font-family="{T.FAMILY}" font-weight="800" '
                f'font-size="28" fill="{WHITE}" letter-spacing="0.12em">SAHAM GORENGAN</text>')
    y = s["top"] + 120
    if d.get("eyebrow"):
        pv, _ = pill(d["eyebrow"], s["left"], y, RED, WHITE, 28)
        body.append(pv)
        y += 100
    hv, y = T.block(d["headline"], s["left"], y, cw, 108, 800, WHITE, max_lines=4, line_height=1.04, size_min=68)
    body.append(hv)
    # Bull sits below the headline, inside the 4:5 grid crop (y 285-1635) used by Instagram profiles.
    m_h = min(660, max(420, h - 250 - (y + 70)))
    body.append(mascot_spot(d.get("mascot", {"pose": "explain", "expression": "smirk"}), w / 2, h - 250, m_h))
    return wrap_svg(w, h, "".join(body))


@template("yt_thumb")
def t_thumb(d: dict, fmt: str, page: str | None, seed: str) -> str:
    w, h, s = fmt_size("yt_thumb")
    body = [background(w, h, d.get("bg", "navy"), seed)]
    body.append(mascot_spot(d.get("mascot", {"pose": "double_point", "expression": "shock"}), w - 300, h + 20, 640))
    hv, y = T.block(d["headline"], s["left"], s["top"] + 40, w * 0.56, 112, 800, WHITE, max_lines=4,
                    line_height=1.0, size_min=64)
    body.append(f'<g stroke="{NAVY}" stroke-width="10" paint-order="stroke">{hv}</g>')
    body.append(logo(s["left"], h - s["bottom"] - 10, 56))
    return wrap_svg(w, h, "".join(body))


@template("og")
def t_og(d: dict, fmt: str, page: str | None, seed: str) -> str:
    w, h, s = fmt_size("og")
    body = [background(w, h, d.get("bg", "navy"), seed), header(w, s, None)]
    hv, y = T.block(d["headline"], s["left"], s["top"] + 90, w * 0.6, 64, 800, WHITE, max_lines=4,
                    line_height=1.08, size_min=40)
    body.append(hv)
    if d.get("eyebrow"):
        body.append(T.label(d["eyebrow"], s["left"], y + 18, 22, PINK))
    body.append(mascot_spot(d.get("mascot", {"pose": "present", "expression": "smirk"}), w - 230, h + 10, 520))
    body.append(footer(w, h, s, text="sahamgorengan.id"))
    return wrap_svg(w, h, "".join(body))


@template("web_hero")
def t_web_hero(d: dict, fmt: str, page: str | None, seed: str) -> str:
    w, h, s = fmt_size("web_hero")
    body = [background(w, h, d.get("bg", "navy"), seed)]
    if d.get("art"):
        art = dict(d["art"])
        art.setdefault("viewbox", f"0 0 {w} {h}")
        body.append(art_box(art, 0, 0, w, h))
    else:
        hv, y = T.block(d.get("headline", ""), s["left"], s["top"] + 120, w * 0.55, 80, 800, WHITE, max_lines=4,
                        line_height=1.06, size_min=48)
        body.append(hv)
        body.append(mascot_spot(d.get("mascot", {"pose": "explain", "expression": "smirk"}), w - 380, h + 10, 760))
    return wrap_svg(w, h, "".join(body))


# ---------- render ----------
def card_svg(spec: dict, seed: str = "sg") -> str:
    name = spec.get("template")
    if name not in TEMPLATES:
        raise ValueError(f"unknown template {name!r}; available: {', '.join(sorted(TEMPLATES))}")
    fmt = spec.get("format") or {"reel_cover": "vertical", "yt_thumb": "yt_thumb", "og": "og",
                                 "web_hero": "web_hero"}.get(name, "feed_portrait")
    return TEMPLATES[name](spec.get("data", {}), fmt, spec.get("page"), seed + name + str(spec.get("page")))


def rasterize(svg: str, out: Path, width: int | None = None) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    src = out.with_suffix(".svg")
    src.write_text(svg, encoding="utf-8")
    if shutil.which("rsvg-convert"):
        import os
        env = dict(os.environ, FONTCONFIG_FILE=str(fontconfig_file()))
        cmd = ["rsvg-convert", "-f", "png", "-o", str(out)] + (["-w", str(width)] if width else []) + [str(src)]
        p = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=120)
        if p.returncode:
            raise RuntimeError("rsvg-convert failed: " + p.stderr[-400:])
    else:  # local dev fallback
        import cairosvg
        cairosvg.svg2png(bytestring=svg.encode(), write_to=str(out), output_width=width)
    _flatten_png(out)
    return out


def _flatten_png(path: Path) -> None:
    """Instagram rejects alpha PNG in some cases; store opaque RGB PNG."""
    from PIL import Image
    with Image.open(path) as im:
        if im.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", im.size, NAVY)
            rgba = im.convert("RGBA")
            bg.paste(rgba, mask=rgba.split()[3])
            buf = io.BytesIO()
            bg.save(buf, "PNG", optimize=True)
            path.write_bytes(buf.getvalue())


def render_card(spec: dict, out: Path, seed: str = "sg") -> Path:
    return rasterize(card_svg(spec, seed), out)


def render_carousel(slides: list[dict], out_dir: Path, seed: str = "sg", prefix: str = "slide") -> list[Path]:
    out = []
    n = len(slides)
    for i, spec in enumerate(slides, 1):
        spec = dict(spec)
        spec.setdefault("page", f"{i}/{n}")
        out.append(render_card(spec, Path(out_dir) / f"{prefix}{i:02d}.png", seed))
    return out
