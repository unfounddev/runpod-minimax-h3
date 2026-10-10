#!/usr/bin/env bash
set -euo pipefail
M=/workspace/ComfyUI/models
mkdir -p "$M/diffusion_models/h3" "$M/text_encoders" "$M/vae" "$M/loras"
fetch() { local url="$1" dest="$2"; if [ -s "$dest" ]; then echo "Exists: $dest"; return; fi; echo "Downloading: $dest"; curl -fL --retry 5 --retry-delay 5 -C - "$url" -o "$dest.part" && mv "$dest.part" "$dest"; }
BASE=https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main
fetch "$BASE/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors" "$M/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"
fetch "$BASE/vae/minimax_h3_video_vae_fp16.safetensors" "$M/vae/minimax_h3_video_vae_fp16.safetensors"
fetch "$BASE/vae/minimax_h3_audio_vae_fp32.safetensors" "$M/vae/minimax_h3_audio_vae_fp32.safetensors"
SINGULARITY_MODEL_URL="${SINGULARITY_MODEL_URL:-https://huggingface.co/WarmBloodAban/Minimax-h3_Singularity/resolve/main/Minimax-h3_Singularity_ref2va_v1.3_int8.safetensors}"
TURBO_LORA_URL="${TURBO_LORA_URL:-https://huggingface.co/lightx2v/Minimax-h3-Turbo/resolve/main/minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors}"
if [ -n "${SINGULARITY_MODEL_URL:-}" ]; then fetch "$SINGULARITY_MODEL_URL" "$M/diffusion_models/h3/Minimax-h3_Singularity_ref2va_v1.3_int8.safetensors"; else echo 'WARNING: SINGULARITY_MODEL_URL not set'; fi
if [ -n "${TURBO_LORA_URL:-}" ]; then fetch "$TURBO_LORA_URL" "$M/loras/minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors"; else echo 'WARNING: TURBO_LORA_URL not set'; fi
