# SG Publisher Middleware

Daily pipeline for Saham Gorengan: **LLM (scheduled Claude routine or ChatGPT) → bundle → render → QA/enrich →
schedule → Web · Instagram · Facebook · YouTube**. The middleware holds **no LLM API key**; it renders brand
assets deterministically, enforces platform/compliance rules, and posts.

```
Claude routine (19:00 WIB) ──┐  Ubersuggest research → question gap → creative brief
ChatGPT (manual/GPT)  ───────┤  writes inbox/<day>-<slug>/bundle.json (content as data)
                             ▼
              app.py ingest ─► render (cards SVG→PNG, article HTML, animated short MP4 + VO + SRT)
                             ─► QA & enrich (lengths, hashtags, UTM, disclaimer, media spec, SEO, dup-art)
                             ─► schedule (WIB slots) ─► scheduler loop (60 s)
                                   ├─ web: SSH Jagoan Hosting (static or WordPress bridge) + media hosting
                                   ├─ instagram/facebook: Graph API (System User → derived Page/IG)
                                   └─ youtube: OAuth refresh token → resumable upload + captions
```

## Run (VPS, as mcpagent)
```bash
cd /srv/localmcpcoder-work/sg-middleware
bash deploy/setup.sh .            # venv, deps, fonts, brand references, mascot export
.venv/bin/python app.py ensure    # API + UI on 127.0.0.1:18790 (/ui, /api/docs) + scheduler
.venv/bin/python app.py secrets --show   # UI login + API bearer token (local only)
```
UI access: `ssh -L 18790:127.0.0.1:18790 <vps>` then http://127.0.0.1:18790/ui/ (or the VPS desktop :88).

## One-time credential setup (UI › Credentials)
| Target | You provide | Middleware derives |
|---|---|---|
| Facebook + Instagram | System User token, App ID, App Secret | token validity/scopes/expiry, system user id, Page id + Page token, linked IG id/username, which token IG accepts |
| YouTube | OAuth Client ID + Secret, one consent click | refresh token, channel id/title |
| Website | SSH host/port/user, docroot (deploy key can be generated; host key pinned) | atomic upload, sha256 check, public read-back, sitemap-insight.xml |

Every platform starts in **dry_run**. Verify, run a test, then switch to **live** on the Dashboard.

## Files
- `prompts/PIPELINE_DAILY.md` — default daily prompt (+ `KEYWORD_RESEARCH.md`, `CREATIVE_DIRECTION.md`, `CHATGPT.md`)
- `brand/BRAND_KIT.md`, `brand/brand.json` — aesthetic + compliance source of truth
- `sgmw/render/` — mascot rig, props, card templates, article, video
- `schemas/bundle.schema.json` — contract between the LLM and the middleware
- `deploy/` — setup script and optional systemd unit
