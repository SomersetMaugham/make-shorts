#!/bin/bash
# List the narration files that changed in script-to-motion since they were copied (SOURCE.md). Never overwrites:
# read the upstream diff, then port it by hand (wave.mjs carries a local change).
#   bash scripts/narration/sync_upstream.sh [<script-to-motion dir>]
HERE="$(cd "$(dirname "$0")" && pwd)"
UP="${1:-$HOME/.claude/skills/script-to-motion}"; UP="$(cd "$UP" && pwd -P)"
grep -E '^- `[^`]+`  [0-9a-f]{64}' "$HERE/SOURCE.md" | while read -r _ f h; do
  f=${f//\`/}; now=$(shasum -a 256 "$UP/scripts/$f" 2>/dev/null | cut -c1-64)
  if [ -z "$now" ]; then echo "GONE upstream: $f"; elif [ "$now" != "$h" ]; then echo "CHANGED upstream: $f  (diff \"$UP/scripts/$f\" \"$HERE/$f\")"; fi
done
echo "checked against $UP"
