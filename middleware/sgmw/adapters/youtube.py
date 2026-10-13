"""YouTube Data API v3: OAuth (PKCE, offline) + resumable Shorts upload + captions.

Setup (UI > Credentials > YouTube): paste OAuth Client ID/Secret (Google Cloud,
type "Desktop app" or "Web app" with the redirect URI below), click "Get consent
URL", sign in with the Saham Gorengan channel owner, then either let the browser
hit the loopback callback (SSH tunnel to 127.0.0.1:18790) or paste the final
redirected URL back into the UI. The refresh token is stored encrypted.

Note: uploads from API projects that have not passed YouTube's API compliance
audit are locked to private. The receipt reports this explicitly.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import time
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests

from .. import vault

AUTH = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN = "https://oauth2.googleapis.com/token"
API = "https://www.googleapis.com/youtube/v3"
UPLOAD = "https://www.googleapis.com/upload/youtube/v3"
SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube.readonly",
          "https://www.googleapis.com/auth/youtube.force-ssl"]


class YouTubeError(RuntimeError):
    def __init__(self, msg, transient=False):
        super().__init__(msg)
        self.transient = transient


class YouTube:
    _cache: dict = {}

    def __init__(self, settings: dict, creds: dict | None = None):
        self.s = settings["youtube"]
        self.c = creds if creds is not None else vault.get("youtube")

    # ---------- OAuth ----------
    PENDING_TTL = 1800   # consent URLs stay valid 30 min
    PENDING_KEEP = 5     # clicking "get consent URL" twice must not invalidate the first tab

    @staticmethod
    def _pending(c: dict) -> dict:
        """{state: {verifier, created}} of recent consent URLs (accepts the old single-entry format)."""
        p = c.get("pending") or {}
        if "state" in p and "verifier" in p:
            p = {p["state"]: {"verifier": p["verifier"], "created": p.get("created", 0)}}
        now = time.time()
        return {k: v for k, v in p.items() if isinstance(v, dict) and now - v.get("created", 0) <= YouTube.PENDING_TTL}

    def auth_url(self) -> str:
        if not (self.c.get("client_id") and self.c.get("client_secret")):
            raise YouTubeError("save Client ID + Client Secret first")
        verifier = secrets.token_urlsafe(64)
        challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        state = secrets.token_urlsafe(16)
        pend = self._pending(vault.get("youtube"))
        pend[state] = {"verifier": verifier, "created": int(time.time())}
        pend = dict(sorted(pend.items(), key=lambda kv: kv[1]["created"])[-self.PENDING_KEEP:])
        vault.put("youtube", {"pending": pend})
        return AUTH + "?" + urlencode({
            "client_id": self.c["client_id"], "redirect_uri": self.s["redirect_uri"], "response_type": "code",
            "scope": " ".join(SCOPES), "access_type": "offline", "prompt": "consent", "include_granted_scopes": "true",
            "state": state, "code_challenge": challenge, "code_challenge_method": "S256"})

    def finish(self, code_or_url: str, state: str | None = None) -> dict:
        """Exchange the code. Idempotent: a reload of the callback tab, or pasting the same URL into the UI
        after the browser already completed it, returns the connected channel instead of an error."""
        c = vault.get("youtube")
        pend = self._pending(c)
        code = code_or_url.strip()
        if code.startswith("http"):
            q = parse_qs(urlparse(code).query)
            if "error" in q:
                raise YouTubeError("Google returned error: " + q["error"][0])
            code, state = q.get("code", [""])[0], q.get("state", [state])[0]
        if state and state == c.get("last_state") and c.get("refresh_token"):
            return {**(c.get("derived") or {}), "note": "already connected with this consent (callback reused)"}
        if not code:
            raise YouTubeError("no code in the pasted text; paste the full redirected URL")
        if not state and len(pend) == 1:  # bare code pasted: only one consent URL is outstanding
            state = next(iter(pend))
        entry = pend.get(state or "")
        if not entry:
            hint = (" YouTube is already connected (" + (c.get("derived") or {}).get("channel_title", "?") +
                    "); nothing to do." if c.get("refresh_token") else "")
            raise YouTubeError("this consent link is unknown or older than 30 min: click 'Save & get consent URL' "
                               "once and use that newest link." + hint)
        r = requests.post(TOKEN, data={
            "code": code, "client_id": c["client_id"], "client_secret": c["client_secret"],
            "redirect_uri": self.s["redirect_uri"], "grant_type": "authorization_code",
            "code_verifier": entry["verifier"]}, timeout=30)
        tok = r.json() if r.headers.get("content-type", "").startswith("application/json") else {}
        if not r.ok or "refresh_token" not in tok:
            raise YouTubeError(f"token exchange failed: {tok.get('error_description') or tok.get('error') or r.status_code}"
                               " (no refresh_token: revoke app access at myaccount.google.com and retry)")
        vault.put("youtube", {"refresh_token": tok["refresh_token"], "pending": None, "last_state": state,
                              "granted_scopes": tok.get("scope", "")})
        self.c = vault.get("youtube")
        YouTube._cache.clear()
        return self.derive()

    def access_token(self) -> str:
        cached = YouTube._cache.get("tok")
        if cached and cached[1] > time.time() + 60:
            return cached[0]
        if not self.c.get("refresh_token"):
            raise YouTubeError("YouTube not authorised yet")
        r = requests.post(TOKEN, data={"client_id": self.c["client_id"], "client_secret": self.c["client_secret"],
                                       "refresh_token": self.c["refresh_token"], "grant_type": "refresh_token"},
                          timeout=30)
        tok = r.json() if r.ok else {}
        if "access_token" not in tok:
            raise YouTubeError("refresh failed (token revoked/expired? re-run consent)", transient=r.status_code >= 500)
        YouTube._cache["tok"] = (tok["access_token"], time.time() + int(tok.get("expires_in", 3600)))
        return tok["access_token"]

    def _h(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token()}"}

    def derive(self) -> dict:
        r = requests.get(f"{API}/channels", params={"part": "snippet,status,contentDetails", "mine": "true"},
                         headers=self._h(), timeout=30)
        items = (r.json() or {}).get("items", []) if r.ok else []
        if not items:
            raise YouTubeError("no channel on this Google account (pick the brand account in the consent screen)")
        ch = items[0]
        derived = {"channel_id": ch["id"], "channel_title": ch["snippet"]["title"],
                   "custom_url": ch["snippet"].get("customUrl"), "verified_at": int(time.time()),
                   "long_uploads": ch.get("status", {}).get("longUploadsStatus")}
        vault.put("youtube", {"derived": derived})
        return derived

    # ---------- upload ----------
    def upload_short(self, post: dict, video: Path, receipt: dict, srt: Path | None = None) -> dict:
        if receipt.get("video_id"):
            return receipt
        p = post["payload"]
        size = video.stat().st_size
        if not receipt.get("session"):
            body = {"snippet": {"title": p["title"], "description": p["description"], "tags": p.get("tags", []),
                                "categoryId": p.get("category_id", "27"), "defaultLanguage": "id",
                                "defaultAudioLanguage": "id"},
                    "status": {"privacyStatus": p.get("privacy", "public"),
                               "selfDeclaredMadeForKids": bool(p.get("made_for_kids", False)),
                               "containsSyntheticMedia": bool(p.get("synthetic_media", False)),
                               "embeddable": True, "publicStatsViewable": True, "license": "youtube"}}
            r = requests.post(f"{UPLOAD}/videos", params={"uploadType": "resumable", "part": "snippet,status"},
                              headers={**self._h(), "Content-Type": "application/json; charset=UTF-8",
                                       "X-Upload-Content-Length": str(size), "X-Upload-Content-Type": "video/mp4"},
                              data=json.dumps(body), timeout=60)
            if r.status_code != 200 or "Location" not in r.headers:
                raise YouTubeError(f"resumable init failed HTTP {r.status_code}: {r.text[:200]}",
                                   transient=r.status_code >= 500 or r.status_code == 429)
            receipt["session"] = r.headers["Location"]
        offset = 0
        q = requests.put(receipt["session"], headers={**self._h(), "Content-Range": f"bytes */{size}"}, timeout=60)
        if q.status_code in (200, 201):
            res = q.json()
        else:
            if q.status_code == 308 and q.headers.get("Range"):
                offset = int(q.headers["Range"].split("-")[1]) + 1
            elif q.status_code not in (308,):
                receipt.pop("session", None)
                raise YouTubeError(f"upload session invalid HTTP {q.status_code}", transient=True)
            with open(video, "rb") as f:
                f.seek(offset)
                r = requests.put(receipt["session"], data=f, timeout=1800, headers={
                    **self._h(), "Content-Length": str(size - offset), "Content-Type": "video/mp4",
                    "Content-Range": f"bytes {offset}-{size - 1}/{size}"})
            if r.status_code not in (200, 201):
                raise YouTubeError(f"upload failed HTTP {r.status_code}: {r.text[:200]}",
                                   transient=r.status_code >= 500 or r.status_code in (308, 429))
            res = r.json()
        vid = res["id"]
        receipt.update(video_id=vid, url=f"https://www.youtube.com/shorts/{vid}")
        receipt.pop("session", None)
        st = res.get("status", {})
        if p.get("privacy", "public") == "public" and st.get("privacyStatus") == "private":
            receipt["warning"] = ("YouTube locked the upload to private: the Google Cloud API project is not audited. "
                                  "Request the YouTube API Services audit, or set it public manually in Studio.")
        if srt and srt.exists() and self.s.get("upload_captions", True):
            try:
                receipt["caption_id"] = self.upload_captions(vid, srt)
            except YouTubeError as e:
                receipt["caption_error"] = str(e)
        return receipt

    def upload_captions(self, video_id: str, srt: Path) -> str:
        boundary = "sg" + secrets.token_hex(8)
        meta = json.dumps({"snippet": {"videoId": video_id, "language": "id", "name": "Bahasa Indonesia",
                                       "isDraft": False}})
        body = (f"--{boundary}\r\nContent-Type: application/json; charset=UTF-8\r\n\r\n{meta}\r\n"
                f"--{boundary}\r\nContent-Type: application/octet-stream\r\n\r\n").encode() + srt.read_bytes() + \
            f"\r\n--{boundary}--\r\n".encode()
        r = requests.post(f"{UPLOAD}/captions", params={"uploadType": "multipart", "part": "snippet"},
                          headers={**self._h(), "Content-Type": f"multipart/related; boundary={boundary}"},
                          data=body, timeout=120)
        if not r.ok:
            raise YouTubeError(f"caption upload HTTP {r.status_code}: {r.text[:160]}")
        return r.json().get("id", "")
