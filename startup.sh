#!/usr/bin/env bash
set -euo pipefail
BASE=/workspace/ComfyUI
mkdir -p "$BASE/models" "$BASE/input" "$BASE/output" "$BASE/temp" "$BASE/user/default/workflows"
for d in models input output temp; do
  if [ ! -L "/opt/ComfyUI/$d" ]; then
    if [ -d "/opt/ComfyUI/$d" ]; then cp -an "/opt/ComfyUI/$d/." "$BASE/$d/"; fi
    rm -rf "/opt/ComfyUI/$d"
    ln -s "$BASE/$d" "/opt/ComfyUI/$d"
  fi
done
cp -n /opt/template/Minimax_H3_ref2va.json "$BASE/user/default/workflows/Minimax_H3_ref2va.json"
cp -n /opt/template/Minimax_H3_ref2va_original.json "$BASE/user/default/workflows/Minimax_H3_ref2va_original.json"
# ComfyUI user directory must also point to persistent storage, otherwise saved workflows may be invisible.
mkdir -p /opt/ComfyUI/user/default/workflows
cp -n /opt/template/Minimax_H3_ref2va.json /opt/ComfyUI/user/default/workflows/Minimax_H3_ref2va.json
if [ "${DOWNLOAD_MODELS:-1}" = "1" ]; then /opt/template/download_models.sh; fi
cd /opt/ComfyUI
exec python main.py --listen 0.0.0.0 --port 8188 --user-directory "$BASE/user"
