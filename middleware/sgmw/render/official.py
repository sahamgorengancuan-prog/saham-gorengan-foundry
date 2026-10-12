"""Official Bull artwork from sahamgorengan.id used as-is (100% on-model).

Files are downloaded by deploy/setup.sh into brand/reference/ (transparent WebP,
1050x1050). Use them through a mascot spec: {"source": "official", "art": "hero"}.
If a file is missing the renderers fall back to the vector rig.
"""
from __future__ import annotations

import base64
import io
from functools import lru_cache

from PIL import Image

from ..config import BRAND_DIR

OFFICIAL = {
    "hero": "hero-bull-refined.webp",          # fist pump at a trading desk (laptop + chart monitors)
    "faq": "faq-bull.webp",
    "community": "community-bull-phone.webp",
    "premium": "premium-bull-phone.webp",
}


def path(name: str):
    f = OFFICIAL.get(name)
    p = BRAND_DIR / "reference" / f if f else None
    return p if p and p.exists() else None


def available() -> list[str]:
    return [k for k in OFFICIAL if path(k)]


@lru_cache(maxsize=32)
def image(name: str, height: int) -> Image.Image | None:
    """Alpha-trimmed RGBA image scaled to `height` px."""
    p = path(name)
    if not p:
        return None
    im = Image.open(p).convert("RGBA")
    bbox = im.split()[3].point(lambda v: 255 if v > 8 else 0).getbbox()
    if bbox:
        im = im.crop(bbox)
    w = max(1, round(im.width * height / im.height))
    return im.resize((w, height), Image.LANCZOS)


@lru_cache(maxsize=32)
def data_uri(name: str, height: int) -> tuple[str, int, int] | None:
    im = image(name, height)
    if im is None:
        return None
    buf = io.BytesIO()
    im.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(), im.width, im.height


def place(name: str, x: float, y: float, height: float, flip: bool = False) -> str | None:
    """SVG <image> with bottom-centre at (x, y). Rendered at 1.5x for crisp output."""
    got = data_uri(name, int(height * 1.5))
    if not got:
        return None
    uri, w, h = got
    dw, dh = w * height / h, height
    tf = f' transform="translate({2 * x:.1f},0) scale(-1,1)"' if flip else ""
    return (f'<image href="{uri}" x="{x - dw / 2:.1f}" y="{y - dh:.1f}" width="{dw:.1f}" height="{dh:.1f}"'
            f' preserveAspectRatio="xMidYMax meet"{tf}/>')
