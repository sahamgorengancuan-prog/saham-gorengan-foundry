"""Text measurement/wrapping with the real brand font, emitted as SVG <text>.

Markup: wrap words in *asterisks* to highlight them (gold by default).
"""
from __future__ import annotations

import re
from functools import lru_cache
from xml.sax.saxutils import escape

from PIL import ImageFont

from ..brand import font_file

FAMILY = "Plus Jakarta Sans, Inter, DejaVu Sans, sans-serif"


@lru_cache(maxsize=256)
def pil_font(size: int, weight: int = 800) -> ImageFont.FreeTypeFont:
    path = font_file()
    if path is None:
        return ImageFont.load_default(size)
    f = ImageFont.truetype(str(path), size)
    try:
        f.set_variation_by_axes([weight])
    except (OSError, AttributeError, ValueError):
        pass
    return f


def tokens(text: str) -> list[tuple[str, bool]]:
    """Split into (word, highlighted). Punctuation glued to a highlight stays on the same token
    (rendered as a separate span with no space) via the U+2060 word-joiner marker."""
    out: list[tuple[str, bool]] = []
    for part in re.split(r"(\*[^*]+\*)", text or ""):
        hl = part.startswith("*") and part.endswith("*") and len(part) > 2
        body = part[1:-1] if hl else part
        words = body.split()
        if words and out and body[:1] not in (" ", "\n", "\t") and not hl:
            words[0] = "\u2060" + words[0]
        for w in words:
            out.append((w, hl))
    return out


def width(s: str, size: int, weight: int = 800, tracking: float = 0.0) -> float:
    s = s.replace(" \u2060", "").replace("\u2060", "")
    return pil_font(size, weight).getlength(s) + tracking * size * max(len(s) - 1, 0)


def wrap(text: str, size: int, max_w: float, weight: int = 800) -> list[list[tuple[str, bool]]]:
    lines, cur = [], []
    space = width(" ", size, weight)
    cur_w = 0.0
    for w, hl in tokens(text):
        ww = width(w, size, weight)
        if w.startswith("\u2060") and cur:
            cur.append((w, hl))
            cur_w += ww
            continue
        if cur and cur_w + space + ww > max_w:
            lines.append(cur)
            cur, cur_w = [], 0.0
        cur.append((w, hl))
        cur_w = ww if len(cur) == 1 else cur_w + space + ww
    if cur:
        lines.append(cur)
    return lines


def fit(text: str, max_w: float, max_lines: int, size_max: int, size_min: int,
        weight: int = 800) -> tuple[int, list]:
    size = size_max
    while size > size_min:
        lines = wrap(text, size, max_w, weight)
        if len(lines) <= max_lines and all(line_width(l, size, weight) <= max_w for l in lines):
            return size, lines
        size -= 2
    return size_min, wrap(text, size_min, max_w, weight)[:max_lines]


def line_width(line, size: int, weight: int = 800) -> float:
    return width(" ".join(w for w, _ in line), size, weight)


def svg_lines(lines, x: float, y: float, size: int, weight: int = 800, fill: str = "#FAFDFF",
              hl_fill: str = "#FFCD35", line_height: float = 1.12, anchor: str = "start",
              tracking: str | None = None, extra: str = "") -> tuple[str, float]:
    """Return (svg, y_after). y is the top of the first line."""
    out = []
    ls = f' letter-spacing="{tracking}"' if tracking else ""
    baseline = y + size * 0.92
    for line in lines:
        spans = []
        for i, (w, hl) in enumerate(line):
            nxt_glued = i < len(line) - 1 and line[i + 1][0].startswith("\u2060")
            t = escape(w.replace("\u2060", "")) + (" " if i < len(line) - 1 and not nxt_glued else "")
            spans.append(f'<tspan fill="{hl_fill}">{t}</tspan>' if hl else t)
        out.append(f'<text x="{x:.1f}" y="{baseline:.1f}" font-family="{FAMILY}" font-weight="{weight}" '
                   f'font-size="{size}" fill="{fill}" text-anchor="{anchor}"{ls}{extra}>{"".join(spans)}</text>')
        baseline += size * line_height
    return "".join(out), y + size * line_height * len(lines)


def block(text: str, x: float, y: float, max_w: float, size: int, weight: int = 500, fill: str = "#FAFDFF",
          max_lines: int = 99, line_height: float = 1.38, anchor: str = "start",
          hl_fill: str = "#FFCD35", size_min: int | None = None) -> tuple[str, float]:
    if size_min:
        size, lines = fit(text, max_w, max_lines, size, size_min, weight)
    else:
        lines = wrap(text, size, max_w, weight)[:max_lines]
    return svg_lines(lines, x, y, size, weight, fill, hl_fill, line_height, anchor)


def label(text: str, x: float, y: float, size: int = 24, fill: str = "#FF7182", weight: int = 800,
          anchor: str = "start") -> str:
    return (f'<text x="{x}" y="{y + size * 0.9:.1f}" font-family="{FAMILY}" font-weight="{weight}" '
            f'font-size="{size}" fill="{fill}" letter-spacing="0.15em" text-anchor="{anchor}">'
            f'{escape(text.upper())}</text>')
