"""Brand kit access + copy compliance checks shared by renderers, QA and prompts."""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from .config import BRAND_DIR, ROOT


@lru_cache(maxsize=1)
def brand() -> dict:
    return json.loads((BRAND_DIR / "brand.json").read_text(encoding="utf-8"))


def color(name: str) -> str:
    return brand()["palette"][name]


def font_file() -> Path | None:
    """Brand font if installed, else a sane fallback (Inter, then DejaVu)."""
    for rel in brand()["typography"]["font_files"]:
        p = ROOT / rel
        if p.exists():
            return p
    for p in (Path("/usr/local/share/fonts/teka/Inter.ttf"),
              Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
              Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")):
        if p.exists():
            return p
    return None


def fontconfig_file() -> Path:
    """fontconfig file that exposes brand/fonts to rsvg-convert without a system install."""
    cache = ROOT / "state" / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    conf = cache / "fonts.conf"
    body = ('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig>'
            '<include ignore_missing="yes">/etc/fonts/fonts.conf</include>'
            f'<dir>{BRAND_DIR / "fonts"}</dir><cachedir>{cache / "fc"}</cachedir></fontconfig>')
    if not conf.exists() or conf.read_text() != body:
        conf.write_text(body)
    return conf


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower())


def compliance_issues(text: str, require_disclaimer: bool = True) -> list[dict]:
    """Return [{'level': 'error'|'warn', 'msg': ...}] for marketing copy."""
    c = brand()["compliance"]
    t = _norm(text)
    issues = []
    for phrase in c["banned_phrases"]:
        if re.search(r"(?<![a-z])" + re.escape(phrase) + r"(?![a-z])", t):
            issues.append({"level": "error", "msg": f"banned phrase: '{phrase}'"})
    if require_disclaimer and not any(d in t for d in c["required_disclaimer_any"]):
        issues.append({"level": "error", "msg": "missing disclaimer (e.g. 'bukan ajakan beli/jual')"})
    # Premium price must match the official packages when mentioned.
    if "premium" in t:
        allowed = {f"{v:,}".replace(",", ".") for v in c["premium_packages_idr"].values()}
        allowed |= {str(v // 1000) + "rb" for v in c["premium_packages_idr"].values()}
        for m in re.findall(r"rp\s?([\d.]+)", t):
            if m.strip(".") and m.strip(".") not in allowed:
                issues.append({"level": "warn", "msg": f"premium price Rp{m} is not an official package"})
    if re.search(r"\b(beli|buy|hajar|serok|borong)\b[^.\n]{0,24}\b[A-Z]{4}\b", text or ""):
        issues.append({"level": "warn", "msg": "possible ticker call-to-action; only allowed in pillar 'rekomendasi' "
                                               "with dated data"})
    return issues


def ensure_disclaimer(text: str, short: bool = False) -> str:
    c = brand()["compliance"]
    if any(d in _norm(text) for d in c["required_disclaimer_any"]):
        return text
    return text.rstrip() + "\n\n" + (c["short_disclaimer"] if short else c["default_disclaimer"])
