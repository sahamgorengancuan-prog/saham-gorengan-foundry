"""Meta Graph API: Facebook Page + Instagram professional account.

Input (once, via UI): System User access token + App ID + App Secret.
Everything else is derived: token validity/scopes/expiry (debug_token), system user
id, Page id + Page token (/me/accounts), linked Instagram account id + username,
and which token the IG endpoints accept. All calls carry appsecret_proof and send
tokens in the Authorization header (never in URLs/logs).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
import time

import requests

from .. import vault

REQUIRED_SCOPES = {"pages_show_list", "pages_read_engagement", "pages_manage_posts", "instagram_basic",
                   "instagram_content_publish"}
NICE_SCOPES = {"business_management", "instagram_manage_comments", "publish_video", "pages_manage_engagement"}
TRANSIENT = {1, 2, 4, 17, 32, 341, 368, 613, 9007}


class MetaError(RuntimeError):
    def __init__(self, msg, code=None, transient=False):
        super().__init__(msg)
        self.code, self.transient = code, transient


class Pending(Exception):
    """Container still processing: retry soon without counting an attempt."""
    def __init__(self, msg, receipt=None, wait=60):
        super().__init__(msg)
        self.receipt, self.wait = receipt or {}, wait


def _clean(s: str) -> str:
    return re.sub(r"(access_token|appsecret_proof|input_token)=[^&\s]+", r"\1=***", s)


class Meta:
    def __init__(self, settings: dict, creds: dict | None = None):
        self.s = settings["meta"]
        self.base = f"https://graph.facebook.com/{self.s['graph_version']}"
        self.c = creds if creds is not None else vault.get("meta")

    # ---------- low level ----------
    def proof(self, token: str) -> str:
        return hmac.new(self.c["app_secret"].encode(), token.encode(), hashlib.sha256).hexdigest()

    def call(self, method: str, path: str, token: str, params: dict | None = None, timeout: int = 60,
             base: str | None = None) -> dict:
        params = dict(params or {})
        if self.c.get("app_secret"):
            params["appsecret_proof"] = self.proof(token)
        url = (base or self.base) + "/" + path.lstrip("/")
        headers = {"Authorization": f"OAuth {token}"}
        try:
            if method == "GET":
                r = requests.get(url, params=params, headers=headers, timeout=timeout)
            else:
                r = requests.post(url, data=params, headers=headers, timeout=timeout)
        except requests.RequestException as e:
            raise MetaError(_clean(f"network error: {type(e).__name__}"), transient=True)
        try:
            data = r.json()
        except ValueError:
            raise MetaError(f"non-JSON response HTTP {r.status_code}", transient=r.status_code >= 500)
        if r.status_code >= 400 or "error" in data:
            e = data.get("error", {})
            code = e.get("code")
            msg = _clean(f"Graph error {code}/{e.get('error_subcode')}: {e.get('message', '')[:240]}")
            raise MetaError(msg, code, bool(e.get("is_transient")) or code in TRANSIENT or r.status_code >= 500)
        return data

    # ---------- derive ----------
    def derive(self) -> dict:
        c = self.c
        for k in ("system_user_token", "app_id", "app_secret"):
            if not c.get(k):
                raise MetaError(f"missing {k}")
        tok = c["system_user_token"]
        app_token = f"{c['app_id']}|{c['app_secret']}"
        try:
            r = requests.get(f"{self.base}/debug_token", params={"input_token": tok},
                             headers={"Authorization": f"OAuth {app_token}"}, timeout=30)
            dbg = (r.json() or {}).get("data", {}) if r.ok else {}
        except (requests.RequestException, ValueError) as e:
            raise MetaError(f"debug_token failed: {type(e).__name__}", transient=True)
        if not dbg.get("is_valid"):
            raise MetaError("system user token invalid or not issued for this App ID/Secret")
        if str(dbg.get("app_id")) != str(c["app_id"]):
            raise MetaError("token belongs to a different app")
        scopes = set(dbg.get("scopes", []))
        me = self.call("GET", "me", tok, {"fields": "id,name"})
        pages = self.call("GET", "me/accounts", tok, {
            "fields": "id,name,access_token,tasks,instagram_business_account{id,username,name}", "limit": 100})
        want = self.s["expected_page_name"].lower()
        cands = pages.get("data", [])
        if c.get("page_id"):
            cands = [p for p in cands if p["id"] == str(c["page_id"])]
        else:
            cands = [p for p in cands if want in p.get("name", "").lower()] or cands
        if not cands:
            raise MetaError("no Facebook Page assigned to this system user (Business Settings > System users > "
                            "Assign assets > Page, full control)")
        page = cands[0]
        page_token = page.get("access_token")
        if not page_token:
            page_token = self.call("GET", page["id"], tok, {"fields": "access_token"}).get("access_token")
        ig = page.get("instagram_business_account") or {}
        ig_token_source = None
        if ig.get("id"):
            for src, t in (("system_user", tok), ("page", page_token)):
                try:
                    info = self.call("GET", ig["id"], t, {"fields": "id,username"})
                    ig["username"] = info.get("username", ig.get("username"))
                    ig_token_source = src
                    break
                except MetaError:
                    continue
        warnings = []
        missing = sorted(REQUIRED_SCOPES - scopes)
        if missing:
            warnings.append("missing scopes: " + ", ".join(missing))
        exp_ig = self.s["expected_ig_username"].lower()
        if ig.get("username") and ig["username"].lower() != exp_ig:
            warnings.append(f"Instagram is @{ig['username']}, expected @{exp_ig}")
        if not ig.get("id"):
            warnings.append("Page has no linked Instagram professional account")
        derived = {
            "system_user_id": me.get("id"), "system_user_name": me.get("name"),
            "token_type": dbg.get("type"), "expires_at": dbg.get("expires_at") or 0,
            "data_access_expires_at": dbg.get("data_access_expires_at") or 0,
            "scopes": sorted(scopes), "page_id": page["id"], "page_name": page.get("name"),
            "page_tasks": page.get("tasks", []), "page_token": page_token,
            "ig_user_id": ig.get("id"), "ig_username": ig.get("username"), "ig_token_source": ig_token_source,
            "warnings": warnings, "verified_at": int(time.time()),
        }
        vault.put("meta", {"derived": derived})
        return derived

    # ---------- helpers ----------
    @property
    def d(self) -> dict:
        d = self.c.get("derived") or {}
        if not d.get("page_id"):
            raise MetaError("Meta not derived yet: open UI > Credentials > Meta > Save & derive")
        return d

    def ig_token(self) -> str:
        return self.d["page_token"] if self.d.get("ig_token_source") == "page" else self.c["system_user_token"]

    def _ig_wait(self, container: str, receipt: dict, key: str) -> None:
        st = self.call("GET", container, self.ig_token(), {"fields": "status_code,status"})
        code = st.get("status_code")
        if code in ("FINISHED", "PUBLISHED"):
            return
        if code == "IN_PROGRESS":
            raise Pending(f"{key} container {container} processing", receipt, 45)
        receipt.pop(key, None)  # ERROR/EXPIRED: recreate next attempt
        raise MetaError(f"Instagram container {code}: {st.get('status', '')[:200]}")

    # ---------- Instagram ----------
    def publish_instagram(self, post: dict, urls: dict, receipt: dict) -> dict:
        """urls: asset_id -> public URL. receipt is persisted between attempts (idempotency)."""
        if receipt.get("media_id"):
            return receipt
        ig = self.d.get("ig_user_id")
        if not ig:
            raise MetaError("no Instagram account linked")
        p = post["payload"]
        tok = self.ig_token()
        kind = post["kind"]
        if "container" not in receipt:
            if kind == "image":
                params = {"image_url": urls[p["asset"]], "caption": p["caption"]}
                if p.get("alt_texts"):
                    params["alt_text"] = p["alt_texts"][0]
                receipt["container"] = self.call("POST", f"{ig}/media", tok, params)["id"]
            elif kind == "carousel":
                kids = receipt.setdefault("children", {})
                alts = p.get("alt_texts") or []
                for i, aid in enumerate(p["assets"]):
                    if aid not in kids:
                        prm = {"image_url": urls[aid], "is_carousel_item": "true"}
                        if i < len(alts) and alts[i]:
                            prm["alt_text"] = alts[i]
                        kids[aid] = self.call("POST", f"{ig}/media", tok, prm)["id"]
                for aid, cid in kids.items():
                    self._ig_wait(cid, receipt, f"child_{aid}")
                receipt["container"] = self.call("POST", f"{ig}/media", tok, {
                    "media_type": "CAROUSEL", "caption": p["caption"],
                    "children": ",".join(kids[a] for a in p["assets"])})["id"]
            elif kind == "reel":
                prm = {"media_type": "REELS", "video_url": urls[p["asset"]], "caption": p["caption"],
                       "share_to_feed": "true" if p.get("share_to_feed", True) else "false"}
                if p.get("cover") and urls.get(p["cover"]):
                    prm["cover_url"] = urls[p["cover"]]
                receipt["container"] = self.call("POST", f"{ig}/media", tok, prm, timeout=120)["id"]
            else:
                raise MetaError(f"unsupported instagram kind {kind}")
        try:
            self._ig_wait(receipt["container"], receipt, "container")
        except Pending as pe:
            pe.receipt = receipt
            raise
        res = self.call("POST", f"{ig}/media_publish", tok, {"creation_id": receipt["container"]})
        receipt["media_id"] = res["id"]
        try:
            info = self.call("GET", res["id"], tok, {"fields": "permalink,shortcode,timestamp"})
            receipt["url"] = info.get("permalink")
        except MetaError:
            pass
        if p.get("first_comment"):
            try:
                receipt["first_comment_id"] = self.call("POST", f"{res['id']}/comments", tok,
                                                        {"message": p["first_comment"]})["id"]
            except MetaError as e:
                receipt["first_comment_error"] = str(e)
        return receipt

    def quota(self) -> dict:
        ig = self.d.get("ig_user_id")
        return self.call("GET", f"{ig}/content_publishing_limit", self.ig_token(),
                         {"fields": "quota_usage,config"}) if ig else {}

    # ---------- Facebook Page ----------
    def publish_facebook(self, post: dict, urls: dict, receipt: dict) -> dict:
        if receipt.get("post_id"):
            return receipt
        d = self.d
        page, tok = d["page_id"], d["page_token"]
        p = post["payload"]
        kind = post["kind"]
        if kind == "photos":
            ids = p["assets"]
            if len(ids) == 1:
                r = self.call("POST", f"{page}/photos", tok, {"url": urls[ids[0]], "message": p["message"],
                                                              "published": "true"})
                receipt["post_id"] = r.get("post_id") or r["id"]
            else:
                media = receipt.setdefault("media", {})
                for aid in ids:
                    if aid not in media:
                        media[aid] = self.call("POST", f"{page}/photos", tok, {"url": urls[aid], "published": "false"})["id"]
                attached = json.dumps([{"media_fbid": media[a]} for a in ids])
                r = self.call("POST", f"{page}/feed", tok, {"message": p["message"], "attached_media": attached})
                receipt["post_id"] = r["id"]
        elif kind == "link":
            r = self.call("POST", f"{page}/feed", tok, {"message": p["message"], "link": p["link"]})
            receipt["post_id"] = r["id"]
        elif kind == "reel":
            if "video_id" not in receipt:
                start = self.call("POST", f"{page}/video_reels", tok, {"upload_phase": "start"})
                receipt["video_id"], receipt["upload_url"] = start["video_id"], start["upload_url"]
            if not receipt.get("uploaded"):
                r = requests.post(receipt["upload_url"], timeout=180, headers={
                    "Authorization": f"OAuth {tok}", "file_url": urls[p["asset"]]})
                if not r.ok or not (r.json() or {}).get("success"):
                    raise MetaError(f"reel upload failed HTTP {r.status_code}", transient=r.status_code >= 500)
                receipt["uploaded"] = True
            if not receipt.get("finished"):
                self.call("POST", f"{page}/video_reels", tok, {
                    "upload_phase": "finish", "video_id": receipt["video_id"], "video_state": "PUBLISHED",
                    "description": p["message"]})
                receipt["finished"] = True
            st = self.call("GET", receipt["video_id"], tok, {"fields": "status"}).get("status", {})
            vs = st.get("video_status")
            if vs in ("processing", "uploading") or (st.get("publishing_phase") or {}).get("status") == "in_progress":
                raise Pending("facebook reel processing", receipt, 60)
            if vs == "error":
                raise MetaError("facebook reel processing error")
            receipt["post_id"] = receipt["video_id"]
            receipt["url"] = f"https://www.facebook.com/reel/{receipt['video_id']}"
        else:
            raise MetaError(f"unsupported facebook kind {kind}")
        if "url" not in receipt:
            try:
                receipt["url"] = self.call("GET", receipt["post_id"], tok, {"fields": "permalink_url"}).get("permalink_url")
            except MetaError:
                receipt["url"] = f"https://www.facebook.com/{receipt['post_id']}"
        return receipt
