"""Structured article JSON -> complete, SEO-ready branded HTML page.

The LLM writes content as data; this module owns layout, schema.org, OG tags and
brand styling, so every article looks and validates the same way.
"""
from __future__ import annotations

import html
import json
import math
import re
from datetime import datetime

from ..brand import brand

CSS = """
:root{--navy:#05183A;--deep:#09367B;--blue:#0B438E;--red:#ED2A3C;--gold:#FFCD35;--white:#FAFDFF;--soft:#D0E3FF;--ink:#0A1633;--muted:#5B6B86}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:#F4F7FD;color:var(--ink);font-family:"Plus Jakarta Sans",Inter,system-ui,sans-serif;font-size:18px;line-height:1.75;-webkit-font-smoothing:antialiased}
a{color:var(--blue)}img{max-width:100%;height:auto;display:block}
.sg-top{background:var(--navy);color:#fff;position:sticky;top:0;z-index:5}
.sg-top .in{max-width:1160px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;gap:16px;padding:12px 20px}
.sg-brand{display:flex;align-items:center;gap:10px;color:#fff;text-decoration:none;font-weight:800;letter-spacing:.12em;font-size:13px}
.sg-brand img{width:38px;height:38px;border-radius:50%;background:#fff}
.sg-top nav{display:flex;gap:18px;flex-wrap:wrap}.sg-top nav a{color:#d0e3ff;text-decoration:none;font-weight:700;font-size:14px}
.sg-top .cta{background:var(--red);color:#fff!important;padding:9px 14px;border-radius:10px}
.sg-hero{background:linear-gradient(145deg,#071d48 0%,#073c8f 65%,#0b58bc 100%);color:#fff;padding:56px 20px 40px;position:relative;overflow:hidden}
.sg-hero:before{content:"";position:absolute;inset:-160px -150px auto auto;width:480px;height:480px;border:1px solid #ffffff20;border-radius:50%;box-shadow:0 0 0 60px #ffffff08,0 0 0 140px #ffffff05}
.sg-hero .in{max-width:820px;margin:0 auto;position:relative}
.sg-eyebrow{font-size:12px;letter-spacing:.15em;font-weight:900;color:#ff7182;text-transform:uppercase;margin:0 0 12px}
.sg-art-h1{font-size:30px;line-height:1.2;color:var(--navy);margin:0 0 18px}
.sg-hero h1,.sg-hero .sg-h1{font-size:clamp(30px,5vw,48px);line-height:1.1;margin:0 0 14px;font-weight:800;letter-spacing:-.03em}
.sg-dek{color:var(--soft);font-size:19px;margin:0 0 18px}
.sg-meta{font-size:13px;color:#b8d3ff;font-weight:700}
.sg-heroimg{max-width:980px;margin:-10px auto 0;padding:0 20px;position:relative;z-index:2}
.sg-heroimg img{border-radius:22px;box-shadow:0 18px 40px #04163440}
main{padding:0 20px}article{max-width:780px;margin:0 auto;padding:34px 0 60px}
article h2{font-size:clamp(24px,3.4vw,32px);line-height:1.2;letter-spacing:-.02em;margin:46px 0 12px;color:var(--navy)}
article h3{font-size:21px;margin:28px 0 8px;color:var(--deep)}
article p{margin:0 0 16px}article li{margin:6px 0}
.sg-box{border-radius:18px;padding:20px 22px;margin:26px 0;border:1px solid #d7e2f5;background:#fff}
.sg-tldr{background:var(--navy);color:#fff;border:0}.sg-tldr h2{color:var(--gold);margin-top:0;font-size:20px}
.sg-tldr li::marker{color:var(--gold)}
.sg-toc{background:#fff}.sg-toc ol{margin:0;padding-left:22px}.sg-toc a{text-decoration:none;font-weight:700}
.sg-callout{border-left:6px solid var(--gold);background:#FFF9E5}
.sg-callout.warning{border-color:var(--red);background:#FFF0F2}.sg-callout.example{border-color:var(--blue);background:#EEF4FF}
.sg-myth{display:grid;grid-template-columns:1fr 1fr;gap:14px}
.sg-myth div{border-radius:16px;padding:18px}.sg-myth .m{background:#FFF0F2;border:2px solid #ED2A3C55}.sg-myth .f{background:#FFF9E5;border:2px solid #FFCD3599}
.sg-myth b{display:inline-block;font-size:12px;letter-spacing:.15em;padding:4px 10px;border-radius:20px;margin-bottom:8px}
.sg-myth .m b{background:var(--red);color:#fff}.sg-myth .f b{background:var(--gold);color:var(--navy)}
.sg-example{background:#0A2A63;color:#fff;border:0}.sg-example .lbl{display:inline-block;background:var(--gold);color:var(--navy);font-weight:800;font-size:12px;letter-spacing:.12em;padding:5px 12px;border-radius:20px}
.sg-example ol li::marker{color:var(--gold);font-weight:800}.sg-example .take{background:#fff;color:var(--navy);border-radius:12px;padding:14px 16px;font-weight:700}
.sg-check ul{list-style:none;padding:0}.sg-check li{padding-left:36px;position:relative}.sg-check li:before{content:"✓";position:absolute;left:0;top:2px;width:24px;height:24px;border-radius:50%;background:var(--gold);color:var(--navy);font-weight:900;text-align:center;line-height:24px;font-size:14px}
figure{margin:26px 0}figcaption{font-size:14px;color:var(--muted);margin-top:8px}
.sg-faq details{background:#fff;border:1px solid #d7e2f5;border-radius:14px;padding:14px 18px;margin:10px 0}.sg-faq summary{font-weight:800;cursor:pointer;color:var(--navy)}
.sg-sources{font-size:15px}.sg-sources li{word-break:break-word}
.sg-video{position:relative;padding-top:177%;max-width:360px;margin:20px auto;border-radius:18px;overflow:hidden}.sg-video iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.sg-cta{background:linear-gradient(145deg,#071d48,#0b58bc);color:#fff;border:0}.sg-cta a.btn{display:inline-block;background:var(--red);color:#fff;text-decoration:none;font-weight:800;padding:12px 18px;border-radius:12px;margin:6px 8px 0 0}
.sg-cta a.alt{background:#ffffff1f}
.sg-disclaimer{font-size:14px;color:var(--muted);border-top:1px solid #d7e2f5;padding-top:16px;margin-top:30px}
.sg-related a{display:block;font-weight:700;text-decoration:none;padding:8px 0;border-bottom:1px solid #e6edf8}
footer.sg-foot{background:var(--navy);color:#b8d3ff;text-align:center;padding:26px 20px;font-size:14px}
@media(max-width:640px){.sg-myth{grid-template-columns:1fr}body{font-size:17px}.sg-top nav{display:none}}
"""


def _inline(text: str) -> str:
    t = html.escape(text or "", quote=False)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
               lambda m: f'<a href="{html.escape(m.group(2))}"{_rel(m.group(2))}>{m.group(1)}</a>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", t)
    return t


def _rel(url: str) -> str:
    return "" if "sahamgorengan.id" in url else ' rel="noopener" target="_blank"'


def md(text: str) -> str:
    """Tiny markdown: paragraphs, '- ' lists, '1. ' lists, ### subheads, **bold**, *em*, [a](url)."""
    out, buf, lst = [], [], None

    def flush():
        nonlocal buf
        if buf:
            out.append("<p>" + _inline(" ".join(buf)) + "</p>")
            buf = []

    def close():
        nonlocal lst
        if lst:
            out.append(f"</{lst}>")
            lst = None

    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            flush(); close(); continue
        m_ul, m_ol = re.match(r"^[-•]\s+(.*)", line), re.match(r"^\d+[.)]\s+(.*)", line)
        if line.startswith("### "):
            flush(); close(); out.append(f"<h3>{_inline(line[4:])}</h3>")
        elif m_ul or m_ol:
            flush()
            tag = "ul" if m_ul else "ol"
            if lst != tag:
                close(); out.append(f"<{tag}>"); lst = tag
            out.append(f"<li>{_inline((m_ul or m_ol).group(1))}</li>")
        else:
            close(); buf.append(line)
    flush(); close()
    return "\n".join(out)


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")[:70]


def word_count(a: dict) -> int:
    parts = [a.get("dek", ""), " ".join(a.get("tldr", []))]
    for s in a.get("sections", []):
        parts += [s.get("heading", ""), s.get("body_md", ""), (s.get("callout") or {}).get("text", "")]
    mc = a.get("misconception") or {}
    ex = a.get("worked_example") or {}
    parts += [mc.get("myth", ""), mc.get("correction", ""), ex.get("scenario", ""), " ".join(ex.get("steps", [])),
              ex.get("takeaway", ""), " ".join(a.get("checklist", []))]
    parts += [f.get("q", "") + " " + f.get("a", "") for f in a.get("faq", [])]
    return len(re.findall(r"\b[\wÀ-ÿ]+\b", " ".join(parts)))


def render_article(a: dict, *, canonical: str, slug: str, image_urls: dict, published: str | None = None,
                   video_id: str | None = None, wp_compat: bool = False) -> str:
    """a = structured article; image_urls maps asset ids/filenames -> public URLs."""
    b = brand()
    site = b["site"].rstrip("/")
    pub = published or datetime.now().strftime("%Y-%m-%d")
    words = word_count(a)
    minutes = max(3, math.ceil(words / 200))
    hero = image_urls.get(a.get("hero", ""), "")
    og_img = image_urls.get(a.get("og_image", ""), hero)
    title = a["title"].strip()
    desc = a["meta_description"].strip()
    h1 = a.get("h1") or title
    sources = a.get("sources", [])
    src_ids = {s["id"]: i for i, s in enumerate(sources, 1)}

    def refs(ids):
        return "".join(f'<sup><a href="#src-{html.escape(x)}">[{src_ids[x]}]</a></sup>' for x in ids or [] if x in src_ids)

    toc, body = [], []
    for s in a.get("sections", []):
        sid = slugify(s["heading"])
        toc.append(f'<li><a href="#{sid}">{html.escape(s["heading"])}</a></li>')
        block = [f'<h2 id="{sid}">{html.escape(s["heading"])}</h2>', md(s.get("body_md", "")) + refs(s.get("source_refs"))]
        if s.get("image") and image_urls.get(s["image"]):
            alt = html.escape(s.get("image_alt") or s["heading"])
            block.append(f'<figure><img src="{image_urls[s["image"]]}" alt="{alt}" loading="lazy" width="1080" '
                         f'height="1350"><figcaption>{alt}</figcaption></figure>')
        if s.get("callout"):
            c = s["callout"]
            block.append(f'<div class="sg-box sg-callout {html.escape(c.get("type", "insight"))}">{md(c.get("text", ""))}</div>')
        body.append("\n".join(block))

    mc = a.get("misconception")
    if mc:
        body.append('<h2 id="mitos-vs-fakta">Mitos vs fakta</h2><div class="sg-myth">'
                    f'<div class="m"><b>MITOS</b><p>{_inline(mc["myth"])}</p></div>'
                    f'<div class="f"><b>FAKTA</b><p>{_inline(mc["correction"])}</p></div></div>')
        toc.append('<li><a href="#mitos-vs-fakta">Mitos vs fakta</a></li>')
    ex = a.get("worked_example")
    if ex:
        steps = "".join(f"<li>{_inline(x)}</li>" for x in ex.get("steps", []))
        body.append(f'<h2 id="simulasi">Simulasi hitungan</h2><div class="sg-box sg-example">'
                    f'<span class="lbl">{html.escape(ex.get("label", "SIMULASI HIPOTETIS"))}</span>'
                    f'<p>{_inline(ex.get("scenario", ""))}</p><ol>{steps}</ol>'
                    f'<div class="take">{_inline(ex.get("takeaway", ""))}</div></div>')
        toc.append('<li><a href="#simulasi">Simulasi hitungan</a></li>')
    if a.get("checklist"):
        items = "".join(f"<li>{_inline(x)}</li>" for x in a["checklist"])
        body.append(f'<h2 id="checklist">Checklist praktis</h2><div class="sg-box sg-check"><ul>{items}</ul></div>')
        toc.append('<li><a href="#checklist">Checklist praktis</a></li>')
    if video_id:
        body.append(f'<h2 id="video">Versi 60 detik bareng Bull</h2><div class="sg-video">'
                    f'<iframe src="https://www.youtube-nocookie.com/embed/{html.escape(video_id)}" title="{html.escape(h1)}" '
                    f'loading="lazy" allowfullscreen></iframe></div>')
    faq = a.get("faq", [])
    if faq:
        qa = "".join(f"<details><summary>{html.escape(f['q'])}</summary>{md(f['a'])}</details>" for f in faq)
        body.append(f'<h2 id="faq">Pertanyaan yang sering dicari</h2><div class="sg-faq">{qa}</div>')
        toc.append('<li><a href="#faq">FAQ</a></li>')
    if sources:
        li = "".join(f'<li id="src-{html.escape(s["id"])}"><a href="{html.escape(s["url"])}" rel="noopener nofollow" '
                     f'target="_blank">{html.escape(s["title"])}</a> — {html.escape(s.get("claim_supported", ""))}</li>'
                     for s in sources)
        body.append(f'<h2 id="sumber">Sumber</h2><ol class="sg-sources">{li}</ol>')
    if a.get("internal_links"):
        li = "".join(f'<a href="{html.escape(l["url"])}">{html.escape(l["title"])} →</a>' for l in a["internal_links"])
        body.append(f'<div class="sg-box sg-related"><strong>Baca juga</strong>{li}</div>')
    body.append('<div class="sg-box sg-cta"><h2 style="color:#FFCD35;margin-top:0">Belajar bareng komunitas</h2>'
                '<p>Diskusi harian gratis di Telegram, video edukasi di YouTube, dan ringkasan visual di Instagram.</p>'
                f'<a class="btn" href="{b["links"]["telegram"]}" rel="noopener" target="_blank">Gabung Telegram gratis</a>'
                f'<a class="btn alt" href="{b["links"]["youtube"]}" rel="noopener" target="_blank">YouTube Saham Gorengan</a>'
                f'<a class="btn alt" href="{b["links"]["start_here"]}">Mulai dari sini</a></div>')
    body.append(f'<p class="sg-disclaimer">{html.escape(b["compliance"]["default_disclaimer"])}</p>')

    tldr = "".join(f"<li>{_inline(x)}</li>" for x in a.get("tldr", []))
    ld = [{
        "@context": "https://schema.org", "@type": "Article", "headline": h1[:110], "description": desc,
        "image": [u for u in (og_img, hero) if u][:1], "datePublished": pub, "dateModified": pub,
        "inLanguage": "id-ID", "author": {"@type": "Organization", "name": a.get("author", "Tim Riset Saham Gorengan"),
                                           "url": site},
        "publisher": {"@type": "Organization", "name": b["legal_name"], "url": site,
                      "logo": {"@type": "ImageObject", "url": b["logo"]["url"]}},
        "mainEntityOfPage": canonical, "keywords": ", ".join([a.get("primary_keyword", "")] + a.get("keywords", [])),
        "wordCount": words}, {
        "@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Beranda", "item": site + "/"},
            {"@type": "ListItem", "position": 2, "name": "Insight", "item": site + "/insight/"},
            {"@type": "ListItem", "position": 3, "name": h1[:80], "item": canonical}]}]
    if faq:
        ld.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", md(f["a"]))}}
            for f in faq]})
    if video_id:
        ld.append({"@context": "https://schema.org", "@type": "VideoObject", "name": h1[:100], "description": desc,
                   "thumbnailUrl": [f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"], "uploadDate": pub,
                   "embedUrl": f"https://www.youtube.com/embed/{video_id}"})
    e = html.escape
    head = f"""<!doctype html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<meta name="robots" content="index,follow,max-image-preview:large">
<link rel="canonical" href="{e(canonical)}">
<meta name="theme-color" content="#074db6">
<meta property="og:type" content="article"><meta property="og:locale" content="id_ID">
<meta property="og:site_name" content="{e(b['legal_name'])}">
<meta property="og:title" content="{e(a.get('og_title') or h1)}"><meta property="og:description" content="{e(desc)}">
<meta property="og:url" content="{e(canonical)}"><meta property="og:image" content="{e(og_img)}">
<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="article:published_time" content="{pub}"><meta property="article:section" content="Edukasi Saham">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{e(h1)}">
<meta name="twitter:description" content="{e(desc)}"><meta name="twitter:image" content="{e(og_img)}">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap" rel="stylesheet">
<link rel="icon" href="{site}/assets/logo-ksg.png">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<style>{CSS}</style>
</head>"""
    hero_img = (f'<div class="sg-heroimg"><img src="{e(hero)}" alt="{e(a.get("hero_alt") or h1)}" width="1600" '
                f'height="900" fetchpriority="high"></div>' if hero else "")
    return f"""{head}
<body>
<header class="sg-top"><div class="in">
<a class="sg-brand" href="{site}/"><img src="{site}/assets/logo-ksg.png" alt="Saham Gorengan" width="38" height="38">SAHAM GORENGAN</a>
<nav aria-label="Navigasi"><a href="{site}/">Beranda</a><a href="{site}/insight/">Insight</a><a href="{b['links']['start_here']}">Mulai di Sini</a><a class="cta" href="{b['links']['premium']}">Join Premium</a></nav>
</div></header>
<section class="sg-hero"><div class="in">
<p class="sg-eyebrow">{e(a.get('eyebrow', 'Insight Saham Gorengan'))}</p>
{'<p class="sg-h1">' + e(h1) + '</p>' if wp_compat else '<h1>' + e(h1) + '</h1>'}
<p class="sg-dek">{e(a.get('dek', ''))}</p>
<p class="sg-meta">{pub} · {minutes} menit baca · {e(a.get('author', 'Tim Riset Saham Gorengan'))}</p>
</div></section>
{hero_img}
<main><article data-slug="{e(slug)}">
{'<h1 class="sg-art-h1">' + e(h1) + '</h1>' if wp_compat else ''}
<div class="sg-box sg-tldr"><h2>Ringkasan 30 detik</h2><ul>{tldr}</ul></div>
<nav class="sg-box sg-toc" aria-label="Daftar isi"><strong>Daftar isi</strong><ol>{''.join(toc)}</ol></nav>
{chr(10).join(body)}
</article></main>
<footer class="sg-foot">© {pub[:4]} {e(b['legal_name'])} · <a style="color:#FFCD35" href="{site}/">sahamgorengan.id</a></footer>
</body>
</html>
"""
