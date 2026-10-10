#!/usr/bin/env bash
set -euo pipefail
mkdir -p /workspace/ComfyUI/{models,input,output,temp,user/default/workflows}
for d in models input output temp; do rm -rf "/opt/ComfyUI/$d"; ln -s "/workspace/ComfyUI/$d" "/opt/ComfyUI/$d"; done
cp -n /opt/ComfyUI/user/default/workflows/Minimax_H3_ref2va.json /workspace/ComfyUI/user/default/workflows/Minimax_H3_ref2va.json
if [ "${DOWNLOAD_MODELS:-1}" = 1 ]; then /opt/download_models.sh; fi
cd /opt/ComfyUI
exec python main.py --listen 0.0.0.0 --port 8188
