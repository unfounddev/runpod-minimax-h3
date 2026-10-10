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

# GitHub owns this copy; personal workflows stay outside the GitHub subfolder.
if [ "${DOWNLOAD_WORKFLOW:-1}" = "1" ]; then
  WF_DIR="$BASE/user/default/workflows/GitHub"
  mkdir -p "$WF_DIR"
  WF_URL="${WORKFLOW_URL:-https://raw.githubusercontent.com/unfounddev/runpod-minimax-h3/main/workflows/Minimax_H3_ref2va.json}"
  WF_TMP="$(mktemp "$WF_DIR/.workflow.XXXXXX")"
  if curl --fail --location --silent --show-error --retry 3 --connect-timeout 15 --max-time 120 \
      -H 'Cache-Control: no-cache' "$WF_URL" -o "$WF_TMP" \
      && python - "$WF_TMP" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as file:
    workflow = json.load(file)
if not isinstance(workflow.get("nodes"), list) or not isinstance(workflow.get("links"), list):
    raise ValueError("Downloaded file is not a ComfyUI workflow")
if any(n.get("type", "").startswith("Pixaroma") for n in workflow["nodes"]):
    raise ValueError("This image requires the FRAMEKIT workflow")
PY
  then
    mv "$WF_TMP" "$WF_DIR/Minimax_H3_ref2va.json"
    echo "FRAMEKIT workflow refreshed from GitHub."
  else
    rm -f "$WF_TMP"
    echo "WARNING: Workflow refresh failed; keeping the previous GitHub copy. You can import JSON manually." >&2
  fi
fi

if [ "${DOWNLOAD_MODELS:-1}" = "1" ]; then
  "$TEMPLATE/download_models.sh"
fi

mkdir -p "$BASE/user/__manager"
if [ ! -f "$BASE/user/__manager/config.ini" ]; then
  printf '[default]\nuse_uv = False\nsecurity_level = normal\nnetwork_mode = public\nallow_git_url_install = False\nallow_pip_install = False\n' > "$BASE/user/__manager/config.ini"
fi

cd "$APP"
exec python main.py --listen 0.0.0.0 --port 8188 --user-directory "$BASE/user" --enable-manager --enable-manager-legacy-ui
