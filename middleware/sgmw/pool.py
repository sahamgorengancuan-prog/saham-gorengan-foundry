"""Keyword pool: accumulates Ubersuggest research across days.

Ubersuggest plans can be capped at a few reports per day, so every research call
is merged here and the daily run picks the best *unused* opportunity instead of
re-querying. Score favours very high volume + low SEO difficulty + low paid
competition + informational intent.
"""
from __future__ import annotations

import json
import math
import os
from datetime import date

from . import store
from .config import STATE

POOL = STATE / "keyword_pool.json"
INTENT_W = {"Informational": 1.0, "Commercial": 0.8, "Transactional": 0.6, "Navigational": 0.3, None: 0.7}


def load() -> dict:
    return json.loads(POOL.read_text(encoding="utf-8")) if POOL.exists() else {}


def save(pool: dict) -> None:
    POOL.parent.mkdir(parents=True, exist_ok=True)
    tmp = POOL.with_suffix(".tmp")
    tmp.write_text(json.dumps(pool, ensure_ascii=False, indent=1), encoding="utf-8")
    os.replace(tmp, POOL)


def add(rows: list[dict], source: str = "ubersuggest", cluster: str = "") -> dict:
    """rows: Ubersuggest items {keyword, volume, sd, pd, cpc, competition, search_intent} (metrics optional)."""
    pool = load()
    today = date.today().isoformat()
    added = updated = 0
    for r in rows:
        k = (r.get("keyword") or "").strip().lower()
        if not k:
            continue
        cur = pool.get(k, {"first_seen": today, "source": source, "cluster": cluster})
        has_metrics = r.get("volume") is not None
        if has_metrics:
            cur.update({"volume": r.get("volume"), "sd": r.get("sd"), "pd": r.get("pd"), "cpc": r.get("cpc"),
                        "competition": r.get("competition"), "intent": r.get("search_intent"), "metrics_at": today})
        elif "volume" not in cur:
            cur.setdefault("volume", None)
        if r.get("question"):
            cur["question"] = True
        cur["last_seen"] = today
        if k in pool:
            updated += 1
        else:
            added += 1
        pool[k] = cur
    save(pool)
    return {"added": added, "updated": updated, "total": len(pool)}


def score(e: dict) -> float:
    v, sd = e.get("volume"), e.get("sd")
    if v is None or sd is None:
        return 0.0
    comp = e.get("competition") or 0
    return round(v * (1 - min(sd, 100) / 100) ** 2 * (1 - 0.3 * comp) * INTENT_W.get(e.get("intent"), 0.7), 1)


def used_keywords() -> set[str]:
    out = set()
    for j in store.history(3650)["jobs"]:
        for k in (j.get("primary_keyword"), j.get("question")):
            if k:
                out.add(k.strip().lower())
    for k, e in load().items():
        if e.get("used_on"):
            out.add(k)
    return out


def top(n: int = 40, max_sd: int = 35, min_volume: int = 500, include_unmeasured: bool = False) -> list[dict]:
    used = used_keywords()
    rows = []
    for k, e in load().items():
        if k in used:
            continue
        if e.get("volume") is None:
            if include_unmeasured:
                rows.append({"keyword": k, **e, "score": 0})
            continue
        if (e.get("sd") or 0) > max_sd or (e.get("volume") or 0) < min_volume:
            continue
        rows.append({"keyword": k, **e, "score": score(e)})
    rows.sort(key=lambda r: -r["score"])
    vols = sorted((r["volume"] for r in rows if r.get("volume")), reverse=True)
    if vols:
        q75 = vols[max(0, math.ceil(len(vols) * 0.25) - 1)]
        for r in rows:
            r["tier"] = "very_high" if (r.get("volume") or 0) >= max(q75, 1000) else "high" if (r.get("volume") or 0) >= 500 else "mid"
    return rows[:n]


def mark_used(keyword: str, day: str) -> None:
    pool = load()
    k = keyword.strip().lower()
    pool.setdefault(k, {"first_seen": day})["used_on"] = day
    save(pool)
