#!/usr/bin/env bash
# Idempotent install/upgrade of the SG middleware on the VPS (runs as mcpagent, no root needed).
#   bash deploy/setup.sh [/srv/localmcpcoder-work/sg-middleware]
set -euo pipefail
DEST="${1:-/srv/localmcpcoder-work/sg-middleware}"
SRC="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$DEST"
if [ "$SRC" != "$DEST" ]; then
  # Code only: never touch state/, inbox/, logs/, .venv/, fonts or reference art.
  rsync -a --delete \
    --exclude '.venv/' --exclude 'state/' --exclude 'inbox/' --exclude 'logs/' --exclude '__pycache__/' \
    --exclude 'brand/fonts/' --exclude 'brand/reference/' --exclude 'brand/mascot/*.png' \
    --exclude 'brand/mascot/*.svg' --exclude 'brand/props/' --exclude 'brand/music/' \
    "$SRC/" "$DEST/"
fi
cd "$DEST"
[ -x .venv/bin/python ] || python3 -m venv .venv
.venv/bin/pip install -q --disable-pip-version-check -r requirements.txt
mkdir -p brand/fonts brand/reference brand/music state inbox logs
chmod 700 state
F="brand/fonts/PlusJakartaSans[wght].ttf"
[ -s "$F" ] || curl -fsSL -o "$F" "https://github.com/google/fonts/raw/main/ofl/plusjakartasans/PlusJakartaSans%5Bwght%5D.ttf"
for a in logo-ksg.png hero-bull-refined.webp faq-bull.webp community-bull-phone.webp premium-bull-phone.webp; do
  [ -s "brand/reference/$a" ] || curl -fsSL -o "brand/reference/$a" "https://sahamgorengan.id/assets/$a" || true
done
.venv/bin/python app.py brand-export
.venv/bin/python app.py secrets >/dev/null
.venv/bin/python -m compileall -q sgmw app.py
echo "SETUP_OK $DEST"
