#!/usr/bin/env bash
set -euo pipefail

URLS_FILE="${1:?Usage: $0 <urls.txt> <out_dir>}"
OUT_DIR="${2:?Usage: $0 <urls.txt> <out_dir>}"

mkdir -p "$OUT_DIR"

# Pick an ARM-native Chrome/Chromium if available (adjust if needed)
CANDIDATES=(
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
  "/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta"
  "/Applications/Chromium.app/Contents/MacOS/Chromium"
  "google-chrome"
  "chromium"
  "chromium-browser"
)
for c in "${CANDIDATES[@]}"; do
  if command -v "$c" >/dev/null 2>&1 || [ -x "$c" ]; then
    CHROME="$c"
    break
  fi
done
: "${CHROME:?Could not find Chrome/Chromium binary. Install Chrome or set CHROME env var.}"

# Use a fresh tmp profile to silence GCM/phone registration + allocator reuse
PROFILE_DIR="$(mktemp -d)"
cleanup() { rm -rf "$PROFILE_DIR" || true; }
trap cleanup EXIT

# Render each URL
i=0
while IFS= read -r url; do
  # skip blanks/comments
  [[ -z "$url" || "$url" =~ ^# ]] && continue
  slug="$(basename "$url")"
  outfile="$OUT_DIR/${slug}.pdf"
  echo "Printing $url -> $outfile"

  "$CHROME" \
    --headless=new \
    --user-data-dir="$PROFILE_DIR" \
    --no-first-run --no-default-browser-check \
    --disable-features=Translate,BackForwardCache \
    --disable-background-networking --disable-sync \
    --disable-gpu --disable-dev-shm-usage --no-sandbox \
    --print-to-pdf="$outfile" \
    --virtual-time-budget=15000 \
    "$url"

  # tiny delay to be gentle
  sleep 0.5
  i=$((i+1))
done < "$URLS_FILE"

echo "Done. PDFs in: $OUT_DIR"

