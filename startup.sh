#!/usr/bin/env bash
set -euo pipefail

# Application is baked into /opt/ComfyUI; writable data lives in /workspace/ComfyUI.
APP=/opt/ComfyUI
BASE=/workspace/ComfyUI
TEMPLATE=/opt/template
mkdir -p "$BASE/models" "$BASE/input" "$BASE/output" "$BASE/temp" "$BASE/user/default/workflows"

# Use one canonical writable location for models/input/output/temp.
for d in models input output temp; do
  target="$BASE/$d"
  source="$APP/$d"
  if [ -L "$source" ]; then
    current="$(readlink "$source")"
    if [ "$current" != "$target" ]; then
      echo "ERROR: $source is a symlink to $current, expected $target" >&2
      exit 1
    fi
  else
    if [ -d "$source" ]; then cp -an "$source/." "$target/"; fi
    rm -rf "$source"
    ln -s "$target" "$source"
  fi
done

# --user-directory points to /workspace, so there is no duplicate /opt user copy.
cp -n "$TEMPLATE/Minimax_H3_ref2va.json" "$BASE/user/default/workflows/Minimax_H3_ref2va.json"

if [ "${DOWNLOAD_MODELS:-1}" = "1" ]; then
  "$TEMPLATE/download_models.sh"
fi

cd "$APP"
exec python main.py --listen 0.0.0.0 --port 8188 --user-directory "$BASE/user"
