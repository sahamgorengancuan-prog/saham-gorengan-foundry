"""Fast checks for copy compliance, platform enrichment and text layout.  Run: python -m pytest tests -q"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.environ.setdefault("SGMW_ROOT", tempfile.mkdtemp(prefix="sgmw_test_"))
sys.path.insert(0, str(ROOT))

import shutil  # noqa: E402

shutil.copytree(ROOT / "brand", Path(os.environ["SGMW_ROOT"]) / "brand", dirs_exist_ok=True)

from sgmw import qa  # noqa: E402
from sgmw.brand import compliance_issues  # noqa: E402
from sgmw.config import DEFAULT_SETTINGS  # noqa: E402
from sgmw.render import mascot, text  # noqa: E402


def test_banned_phrase_and_disclaimer():
    errs = compliance_issues("Saham ini pasti cuan besok!")
    msgs = " ".join(e["msg"] for e in errs)
    assert "pasti cuan" in msgs and "disclaimer" in msgs
    assert not compliance_issues("Materi edukasi, bukan ajakan beli/jual.")


def test_premium_price_guard():
    assert any("not an official package" in i["msg"] for i in
               compliance_issues("SG Premium cuma Rp150.000! Konten edukasi."))
    assert not compliance_issues("SG Premium Rp200.000/bulan. Konten edukasi.")


def _ctx():
    return {"settings": DEFAULT_SETTINGS, "slug": "contoh-slug-sg", "assets": {},
            "article_url": "https://sahamgorengan.id/insight/contoh-slug-sg/"}


def test_instagram_enrichment_limits_hashtags_and_adds_disclaimer():
    post = {"platform": "instagram", "kind": "carousel", "assets": [], "caption": "Hook singkat",
            "hashtags": ["#Saham Gorengan", "ihsg", "ihsg", "a", "b", "c", "d", "e"]}
    p, issues = qa.enrich(post, _ctx())
    assert len(p["hashtags"]) == 5 and "sahamgorengan" in p["hashtags"]
    assert "bukan ajakan beli" in p["caption"].lower()
    assert any("2-10 images" in i["msg"] for i in issues)


def test_youtube_title_and_utm():
    post = {"platform": "youtube", "kind": "short", "asset": "x", "title": "Kenapa ARA?", "description": "Isi",
            "tags": ["saham", "saham", "ihsg"]}
    p, _ = qa.enrich(post, _ctx())
    assert p["title"].endswith("#Shorts")
    assert "utm_source=youtube" in p["description"]
    assert p["tags"] == ["saham", "ihsg"]


def test_facebook_link_gets_utm():
    p, _ = qa.enrich({"platform": "facebook", "kind": "link", "message": "Halo"}, _ctx())
    assert "utm_source=facebook" in p["link"] and "utm_campaign=sg-contoh-slug-sg" in p["link"]


def test_text_wrap_respects_width():
    lines = text.wrap("Kenapa *saham gorengan* bisa ARA lalu ARB dalam seminggu?", 60, 500)
    assert all(text.line_width(l, 60) <= 500 for l in lines[:-1])
    assert any(hl for line in lines for _, hl in line)


def test_mascot_rejects_unknown_pose():
    try:
        mascot.mascot_group("moonwalk")
    except ValueError:
        return
    raise AssertionError("expected ValueError")


def test_dhash_distance():
    assert qa.hamming("ffff", "fffe") == 1
