"""Storyboard JSON -> branded 9:16 animated short (MP4 + SRT + cover).

Kurzgesagt-style flat vector scenes + OverSimplified-style Bull acting, Indonesian
voice-over via edge-tts (no API key), burned-in captions, brand end card.

Vertical layout (1080x1920), aligned with Reels/Shorts UI safe zones:
  236        progress bar
  270-600    headline zone
  600-1340   stage: mascot (bottom anchored at 1340) + props/art/counter
  1350-1490  captions (centre y=1420)
  1500-1920  background only (platform UI covers it)

Storyboard:
{
  "voice": "id-ID-ArdiNeural", "rate": "+6%", "bg": "navy",
  "scenes": [{
     "vo": "kalimat yang diucapkan", "caption": "opsional, teks tampil (pakai *highlight*)",
     "headline": "≤6 kata, *highlight*", "bg": "navy|deep|red|light",
     "mascot": {"pose": "think", "expression": "think", "side": "right|left|center", "enter": "rise"},
     "props": [{"name": "chart_up", "x": 300, "y": 900, "size": 300, "enter": "pop", "delay": 0.3, "loop": "float"}],
     "art": {"svg": "<g>..full-frame 1080x1920 coords..</g>"},
     "counter": {"from": 0, "to": 35, "prefix": "", "suffix": "%", "x": 540, "y": 860, "size": 200},
     "camera": {"zoom": [1.0, 1.06]}, "min_duration": 2.5
  }],
  "end_card": true
}
"""
from __future__ import annotations

import asyncio
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from ..brand import brand
from . import card as C
from . import mascot as M
from . import official as O
from . import props as P
from . import text as T

W, H, FPS = 1080, 1920, 30
NAVY_RGB = (5, 24, 58)
GOLD_RGB = (255, 205, 53)
WHITE_RGB = (250, 253, 255)
STAGE_BOTTOM = 1340
CAPTION_Y = 1420
HEADLINE_Y = 280
SAFE_L, SAFE_R = 80, 150


# ---------- easing ----------
def ease_out_back(t: float) -> float:
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3


def clamp(x: float, a: float = 0.0, b: float = 1.0) -> float:
    return max(a, min(b, x))


# ---------- raster helpers ----------
def svg_to_image(svg: str, tmp: Path, name: str) -> Image.Image:
    p = tmp / f"{name}.png"
    src = tmp / f"{name}.svg"
    src.write_text(svg, encoding="utf-8")
    if shutil.which("rsvg-convert"):
        import os
        from ..brand import fontconfig_file
        env = dict(os.environ, FONTCONFIG_FILE=str(fontconfig_file()))
        r = subprocess.run(["rsvg-convert", "-f", "png", "-o", str(p), str(src)], capture_output=True, text=True,
                           env=env, timeout=120)
        if r.returncode:
            raise RuntimeError("rsvg-convert failed: " + r.stderr[-300:])
    else:
        import cairosvg
        cairosvg.svg2png(bytestring=svg.encode(), write_to=str(p))
    return Image.open(p).convert("RGBA")


def with_rim(img: Image.Image, color=(143, 184, 255), glow=(61, 123, 255)) -> Image.Image:
    """Soft blue glow + thin rim so the navy-outlined mascot pops on navy backgrounds."""
    pad = 40
    a = img.split()[3]
    big = Image.new("L", (img.width + 2 * pad, img.height + 2 * pad), 0)
    big.paste(a, (pad, pad))
    rim = big.filter(ImageFilter.MaxFilter(11))
    halo = big.filter(ImageFilter.GaussianBlur(26)).point(lambda v: int(v * 0.55))
    out = Image.new("RGBA", big.size, glow + (0,))
    out.putalpha(halo)
    rim_l = Image.new("RGBA", big.size, color + (0,))
    rim_l.putalpha(rim.point(lambda v: int(v * 0.85)))
    out.alpha_composite(rim_l)
    out.alpha_composite(img, (pad, pad))
    return out


def text_image(text: str, size: int, max_w: int, weight: int = 800, fill=WHITE_RGB, hl=GOLD_RGB,
               stroke: int = 0, align: str = "center", max_lines: int = 4, line_h: float = 1.12) -> Image.Image:
    size, lines = T.fit(text, max_w, max_lines, size, max(28, int(size * 0.6)), weight)
    font = T.pil_font(size, weight)
    lh = int(size * line_h)
    h = lh * len(lines) + stroke * 2 + 10
    img = Image.new("RGBA", (max_w + stroke * 2 + 20, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    space = T.width(" ", size, weight)
    for i, line in enumerate(lines):
        lw = T.line_width(line, size, weight)
        x = (img.width - lw) / 2 if align == "center" else stroke + 10
        y = stroke + i * lh
        for j, (w, is_hl) in enumerate(line):
            word = w.replace("⁠", "")
            d.text((x, y), word, font=font, fill=(hl if is_hl else fill) + (255,),
                   stroke_width=stroke, stroke_fill=NAVY_RGB + (255,))
            x += T.width(word, size, weight)
            if j < len(line) - 1 and not line[j + 1][0].startswith("⁠"):
                x += space
    return img


def paste_center(base: Image.Image, img: Image.Image, cx: float, cy: float, scale: float = 1.0,
                 alpha: float = 1.0, rotate: float = 0.0) -> None:
    if scale <= 0.01 or alpha <= 0.01:
        return
    im = img
    if abs(scale - 1) > 0.005:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if rotate:
        im = im.rotate(rotate, resample=Image.BILINEAR, expand=True)
    if alpha < 0.999:
        a = im.split()[3].point(lambda v: int(v * alpha))
        im = im.copy()
        im.putalpha(a)
    base.paste(im, (int(cx - im.width / 2), int(cy - im.height / 2)), im)


def paste_bottom(base: Image.Image, img: Image.Image, cx: float, bottom: float, scale: float = 1.0,
                 alpha: float = 1.0) -> None:
    paste_center(base, img, cx, bottom - img.height * scale / 2, scale, alpha)


# ---------- TTS / audio ----------
def tts(text: str, out: Path, voice: str, rate: str, pitch: str = "+0Hz") -> float:
    try:
        import edge_tts

        async def go():
            comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
            await comm.save(str(out))
        for attempt in range(3):
            try:
                asyncio.run(go())
                break
            except Exception:
                if attempt == 2:
                    raise
        return probe_duration(out)
    except Exception as exc:  # no network / package: silent scene with estimated length
        print("TTS_FALLBACK_SILENT", type(exc).__name__, str(exc)[:120], file=sys.stderr)
        return 0.0


def probe_duration(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                       capture_output=True, text=True, timeout=60)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def caption_chunks(text: str, start: float, dur: float, max_words: int = 5, max_chars: int = 30) -> list[dict]:
    words = T.tokens(text)
    chunks, cur = [], []
    for w in words:
        if w[0].startswith(GLUE):  # punctuation/suffix glued to a highlight stays in the same cue
            (cur if cur or not chunks else chunks[-1]).append(w)
            continue
        if cur and (len(cur) >= max_words or len(_join(cur + [w])) > max_chars):
            chunks.append(cur)
            cur = []
        cur.append(w)
        if re.search(r"[.!?,;:]$", w[0]) and len(cur) >= 2:
            chunks.append(cur)
            cur = []
    if cur:
        chunks.append(cur)
    total = sum(len(_join(c)) for c in chunks) or 1
    t = start
    out = []
    for c in chunks:
        plain = _join(c)
        d = dur * len(plain) / total
        out.append({"start": t, "end": t + d, "text": _join(c, markup=True), "plain": plain})
        t += d
    return out


GLUE = chr(0x2060)


def _join(tokens_, markup: bool = False) -> str:
    """Re-assemble tokens; glued tokens (word joiner prefix) attach without a space."""
    s = ""
    for i, (w, hl) in enumerate(tokens_):
        glued = w.startswith(GLUE)
        w = w.replace(GLUE, "")
        if markup and hl:
            w = f"*{w}*"
        s += w if glued or i == 0 else " " + w
    return s.replace("* *", " ")


def srt_time(t: float) -> str:
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms % 3600000 // 60000:02d}:{ms % 60000 // 1000:02d},{ms % 1000:03d}"


# ---------- scene model ----------
class Layer:
    def __init__(self, img, cx, cy, enter="pop", delay=0.0, loop="none", anchor="center", blink=None):
        self.img, self.cx, self.cy = img, cx, cy
        self.enter, self.delay, self.loop, self.anchor, self.blink = enter, delay, loop, anchor, blink

    def draw(self, frame: Image.Image, t: float, speaking: bool) -> None:
        te = t - self.delay
        if te < 0:
            return
        p = clamp(te / 0.45)
        scale, alpha, dx, dy, rot = 1.0, 1.0, 0.0, 0.0, 0.0
        if self.enter == "pop":
            scale = ease_out_back(p) if p < 1 else 1.0
        elif self.enter == "rise":
            dy = (1 - ease_out_cubic(p)) * 420
            alpha = clamp(p * 2)
        elif self.enter == "slide_left":
            dx = -(1 - ease_out_cubic(p)) * 700
        elif self.enter == "slide_right":
            dx = (1 - ease_out_cubic(p)) * 700
        elif self.enter == "fade":
            alpha = p
        if self.loop == "float":
            dy += 10 * math.sin(2 * math.pi * te / 2.4)
        elif self.loop == "pulse":
            scale *= 1 + 0.04 * math.sin(2 * math.pi * te / 1.2)
        elif self.loop == "spin":
            rot = -(te * 60) % 360
        elif self.loop == "wobble":
            rot = 4 * math.sin(2 * math.pi * te / 1.6)
        elif self.loop == "bob":  # mascot idle; quicker while speaking
            period = 1.1 if speaking else 1.9
            dy += (7 if speaking else 5) * math.sin(2 * math.pi * te / period)
        img = self.img
        if self.blink is not None and (te % 3.3) > 3.18:
            img = self.blink
        if self.anchor == "bottom":
            paste_bottom(frame, img, self.cx + dx, self.cy + dy, scale, alpha)
        else:
            paste_center(frame, img, self.cx + dx, self.cy + dy, scale, alpha, rot)


class Scene:
    def __init__(self, spec: dict, idx: int, tmp: Path, seed: str, bg_cache: dict, mascot_cache: dict):
        self.spec = spec
        self.idx = idx
        self.layers: list[Layer] = []
        kind = spec.get("bg", "navy")
        key = kind + ("|art" + str(idx) if spec.get("art") else "")
        if key not in bg_cache:
            body = C.background(W, H, kind, seed + kind)
            if spec.get("art"):
                art = dict(spec["art"])
                art.setdefault("viewbox", f"0 0 {W} {H}")
                body += C.art_box(art, 0, 0, W, H)
            svg = C.wrap_svg(W, H, body)
            big = svg_to_image(svg, tmp, f"bg_{idx}").convert("RGB")
            bg_cache[key] = big.resize((int(W * 1.12), int(H * 1.12)), Image.LANCZOS)
        self.bg = bg_cache[key]
        cam = spec.get("camera", {})
        self.zoom = cam.get("zoom", [1.0, 1.05])
        self.dark = kind != "light"
        fg = WHITE_RGB if self.dark else NAVY_RGB
        if spec.get("headline"):
            img = text_image(spec["headline"], 84, W - SAFE_L - SAFE_R, 800, fg, GOLD_RGB if self.dark else (237, 42, 60),
                             stroke=0, max_lines=3)
            self.layers.append(Layer(img, (SAFE_L + W - SAFE_R) / 2, HEADLINE_Y + img.height / 2, "slide_left", 0.0))
        for pr in spec.get("props", []):
            size = int(pr.get("size", 260))
            pimg = svg_to_image(P.prop_svg(pr["name"], size), tmp, f"prop_{idx}_{pr['name']}_{size}")
            self.layers.append(Layer(pimg, pr.get("x", 300), pr.get("y", 900), pr.get("enter", "pop"),
                                     float(pr.get("delay", 0.25)), pr.get("loop", "float")))
        m = spec.get("mascot")
        official = None
        if m and (m.get("source") == "official" or m.get("art")):
            official = O.image(m.get("art", "hero"), int(m.get("height", 620)))
        if m and official is not None:
            im = official.transpose(Image.FLIP_LEFT_RIGHT) if m.get("flip") else official
            side = m.get("side", "right")
            cx = {"left": 330, "center": W / 2, "right": 760}.get(side, 760)
            self.layers.append(Layer(with_rim(im), m.get("x", cx), STAGE_BOTTOM + 40, m.get("enter", "rise"),
                                     float(m.get("delay", 0.0)), "bob", "bottom"))
        elif m:
            k = (m.get("pose", "explain"), m.get("expression", "smirk"), m.get("accessory", "none"),
                 bool(m.get("flip")) or m.get("side") == "left")
            if k not in mascot_cache:
                hpx = int(m.get("height", 620))
                wpx = int(hpx * M.MASCOT_BOX[2] / M.MASCOT_BOX[3])
                im = svg_to_image(M.mascot_svg(k[0], k[1], k[2], k[3], width=wpx), tmp, f"m_{'_'.join(map(str, k))}")
                bl = svg_to_image(M.mascot_svg(k[0], k[1], k[2], k[3], blink=True, width=wpx), tmp,
                                  f"mb_{'_'.join(map(str, k))}")
                mascot_cache[k] = (with_rim(im), with_rim(bl))
            im, bl = mascot_cache[k]
            side = m.get("side", "right")
            cx = {"left": 330, "center": W / 2, "right": 760}.get(side, 760)
            self.layers.append(Layer(im, m.get("x", cx), STAGE_BOTTOM + 40, m.get("enter", "rise"),
                                     float(m.get("delay", 0.0)), "bob", "bottom", bl))
        self.counter = spec.get("counter")

    def background(self, t: float, dur: float) -> Image.Image:
        z0, z1 = self.zoom
        z = z0 + (z1 - z0) * ease_out_cubic(clamp(t / max(dur, 0.1)))
        bw, bh = self.bg.size
        cw, ch = int(bw / (1.12 * z) * 1.0), int(bh / (1.12 * z))
        cw, ch = min(cw, bw), min(ch, bh)
        x0, y0 = (bw - cw) // 2, (bh - ch) // 2
        return self.bg.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.BILINEAR)

    def draw_counter(self, frame: Image.Image, t: float) -> None:
        c = self.counter
        if not c:
            return
        p = ease_out_cubic(clamp((t - float(c.get("delay", 0.2))) / float(c.get("duration", 1.2))))
        val = c.get("from", 0) + (c.get("to", 0) - c.get("from", 0)) * p
        dec = int(c.get("decimals", 0))
        num = f"{val:,.{dec}f}".replace(",", "#").replace(".", ",").replace("#", ".")
        s = f'{c.get("prefix", "")}{num}{c.get("suffix", "")}'
        size = int(c.get("size", 180))
        final = f'{c.get("prefix", "")}{c.get("to", 0)}{c.get("suffix", "")}'
        max_w = float(c.get("max_w", 440))
        while size > 60 and T.pil_font(size, 800).getlength(final) > max_w:  # never run into the mascot
            size -= 6
        font = T.pil_font(size, 800)
        d = ImageDraw.Draw(frame)
        tw = font.getlength(s)
        d.text((c.get("x", W / 2) - tw / 2, c.get("y", 860) - size / 2), s, font=font, fill=GOLD_RGB,
               stroke_width=8, stroke_fill=NAVY_RGB)


def end_card(tmp: Path, seed: str) -> Image.Image:
    b = brand()
    body = [C.background(W, H, "navy", seed + "end"),
            f'<circle cx="{W / 2}" cy="560" r="120" fill="#FAFDFF"/>',
            C.logo(W / 2 - 110, 450, 220),
            T.block("sahamgorengan.id", W / 2, 760, W, 72, 800, "#FFCD35", anchor="middle", max_lines=1)[0],
            T.block(f"Follow {b['handles']['instagram']}", W / 2, 870, W, 44, 700, "#FAFDFF", anchor="middle",
                    max_lines=1)[0],
            T.block(b["compliance"]["short_disclaimer"], W / 2, 950, W, 32, 600, "#B8D3FF", anchor="middle",
                    max_lines=1)[0],
            C.mascot_spot({"source": "official", "art": "hero", "pose": "wave", "expression": "happy"},
                          W / 2, STAGE_BOTTOM + 260, 560)]
    return svg_to_image(C.wrap_svg(W, H, "".join(body)), tmp, "endcard").convert("RGB")


# ---------- main ----------
def render_short(storyboard: dict, out_dir: Path, seed: str = "sg", music: Path | None = None) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    b = brand()["motion_style"]["voice"]
    voice = storyboard.get("voice", b["voice"])
    rate = storyboard.get("rate", b["rate"])
    scenes_spec = storyboard["scenes"]
    if not scenes_spec:
        raise ValueError("storyboard has no scenes")
    tmp = Path(tempfile.mkdtemp(prefix="sgvid_", dir=str(out_dir)))
    try:
        # 1) voice-over per scene -> timing
        timeline, t0 = [], 0.0
        for i, sc in enumerate(scenes_spec):
            vo = (sc.get("vo") or "").strip()
            mp3 = tmp / f"vo_{i:02d}.mp3"
            d_vo = tts(vo, mp3, sc.get("voice", voice), sc.get("rate", rate)) if vo else 0.0
            if d_vo <= 0:
                d_vo = max(1.5, len(vo.split()) / 2.6) if vo else 0.0
                mp3 = None
            lead = 0.12 if i else 0.0
            dur = max(float(sc.get("min_duration", 2.2)), d_vo + lead + 0.3)
            timeline.append({"start": t0, "dur": dur, "vo_file": mp3, "vo_start": t0 + lead, "vo_dur": d_vo})
            t0 += dur
        end_dur = 1.6 if storyboard.get("end_card", True) else 0.0
        total = t0 + end_dur
        # 2) captions
        caps = []
        for sc, tl in zip(scenes_spec, timeline):
            text = sc.get("caption") or sc.get("vo") or ""
            if text and storyboard.get("captions", True):
                caps += caption_chunks(text, tl["vo_start"], max(tl["vo_dur"], 0.8))
        cap_imgs: dict = {}
        # 3) build scenes
        bg_cache, m_cache = {}, {}
        scenes = [Scene(sc, i, tmp, seed, bg_cache, m_cache) for i, sc in enumerate(scenes_spec)]
        end_img = end_card(tmp, seed) if end_dur else None
        # 4) audio track
        audio = tmp / "mix.wav"
        build_audio(timeline, total, audio, music)
        # 5) frames -> ffmpeg
        mp4 = out_dir / "short.mp4"
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(FPS), "-i", "-", "-i", str(audio), "-map", "0:v", "-map", "1:a",
               "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-profile:v", "high", "-level", "4.1",
               "-pix_fmt", "yuv420p", "-r", str(FPS), "-g", str(FPS * 2),
               "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", "-shortest", str(mp4)]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        n_frames = int(math.ceil(total * FPS))
        navy = Image.new("RGB", (W, H), NAVY_RGB)
        ci = 0
        try:
            for f in range(n_frames):
                tg = f / FPS
                if tg >= t0 and end_img is not None:
                    te = tg - t0
                    frame = Image.blend(navy, end_img, clamp(te / 0.25))
                else:
                    si = next(i for i, tl in enumerate(timeline) if tg < tl["start"] + tl["dur"] or i == len(timeline) - 1)
                    tl, sc = timeline[si], scenes[si]
                    t = tg - tl["start"]
                    speaking = tl["vo_start"] <= tg <= tl["vo_start"] + tl["vo_dur"]
                    frame = sc.background(t, tl["dur"])
                    for layer in sc.layers:
                        layer.draw(frame, t, speaking)
                    sc.draw_counter(frame, t)
                    while ci < len(caps) and tg > caps[ci]["end"]:
                        ci += 1
                    if ci < len(caps) and caps[ci]["start"] <= tg <= caps[ci]["end"]:
                        key = caps[ci]["text"]
                        if key not in cap_imgs:
                            cap_imgs[key] = text_image(key, 62, W - 2 * SAFE_L - 40, 800, WHITE_RGB, GOLD_RGB,
                                                       stroke=9, max_lines=2)
                        pop = 0.9 + 0.1 * ease_out_back(clamp((tg - caps[ci]["start"]) / 0.12))
                        paste_center(frame, cap_imgs[key], W / 2, CAPTION_Y, pop)
                    if storyboard.get("progress_bar", True):
                        dr = ImageDraw.Draw(frame)
                        dr.rounded_rectangle((SAFE_L, 236, W - SAFE_R, 244), 4, fill=(255, 255, 255))
                        dr.rounded_rectangle((SAFE_L, 236, SAFE_L + (W - SAFE_R - SAFE_L) * tg / t0, 244), 4,
                                             fill=GOLD_RGB)
                    if si and t < 0.18:  # dip from navy between scenes
                        frame = Image.blend(navy, frame, clamp(t / 0.18))
                proc.stdin.write(frame.tobytes())
        finally:
            proc.stdin.close()
            proc.wait()
        if proc.returncode:
            raise RuntimeError("ffmpeg encode failed")
        # 6) captions file + cover + meta
        srt = out_dir / "short.srt"
        srt.write_text("".join(f"{i}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n{c['plain']}\n\n"
                               for i, c in enumerate(caps, 1)), encoding="utf-8")
        cover_spec = storyboard.get("cover") or {
            "template": "reel_cover",
            "data": {"eyebrow": storyboard.get("eyebrow", "Saham Gorengan"),
                     "headline": storyboard.get("title") or scenes_spec[0].get("headline") or "Saham Gorengan",
                     "mascot": scenes_spec[0].get("mascot") or {"pose": "explain", "expression": "smirk"}}}
        cover = C.render_card(cover_spec, out_dir / "cover.png", seed)
        meta = {"duration": round(total, 2), "fps": FPS, "width": W, "height": H, "scenes": len(scenes_spec),
                "voice": voice, "captions": len(caps), "mp4": str(mp4), "srt": str(srt), "cover": str(cover),
                "transcript": " ".join((s.get("vo") or "") for s in scenes_spec)}
        (out_dir / "short.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        return meta
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def build_audio(timeline: list[dict], total: float, out: Path, music: Path | None = None) -> None:
    inputs, filters, labels = [], [], []
    for i, tl in enumerate(timeline):
        if tl["vo_file"] and Path(tl["vo_file"]).exists():
            inputs += ["-i", str(tl["vo_file"])]
            ms = int(tl["vo_start"] * 1000)
            filters.append(f"[{len(labels)}:a]aresample=48000,adelay={ms}|{ms}[v{len(labels)}]")
            labels.append(f"[v{len(labels)}]")
    base = ["ffmpeg", "-y", "-loglevel", "error"]
    if not labels:
        subprocess.run(base + ["-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo", "-t", f"{total:.3f}", str(out)],
                       check=True, timeout=120)
        return
    mix = "".join(labels) + f"amix=inputs={len(labels)}:normalize=0,apad=whole_dur={total:.3f}"
    if music and Path(music).exists():
        inputs += ["-stream_loop", "-1", "-i", str(music)]
        mi = len(labels)
        filters.append(f"{mix},asplit=2[vo1][vo2]")
        filters.append(f"[{mi}:a]aresample=48000,volume=0.12,atrim=0:{total:.3f}[bgm]")
        filters.append("[bgm][vo1]sidechaincompress=threshold=0.05:ratio=8:attack=20:release=300[duck]")
        filters.append("[vo2][duck]amix=inputs=2:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[out]")
    else:
        filters.append(f"{mix},loudnorm=I=-14:TP=-1.5:LRA=11[out]")
    cmd = base + inputs + ["-filter_complex", ";".join(filters), "-map", "[out]", "-ac", "2", "-ar", "48000",
                           "-t", f"{total:.3f}", str(out)]
    subprocess.run(cmd, check=True, timeout=300)
