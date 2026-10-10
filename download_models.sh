#!/usr/bin/env bash
set -euo pipefail
M=/workspace/ComfyUI/models
mkdir -p "$M/diffusion_models/h3" "$M/text_encoders" "$M/vae" "$M/loras"
fetch() {
  local url="$1" dest="$2" tmp
  tmp="${dest}.part"
  if [ -s "$dest" ]; then echo "Already present: $dest"; return; fi
  echo "Downloading $(basename "$dest")"
  curl --fail --location --retry 5 --retry-delay 5 --continue-at - "$url" --output "$tmp"
  test -s "$tmp" || { echo "Empty download: $dest" >&2; return 1; }
  mv "$tmp" "$dest"
}
BASE=https://huggingface.co/Comfy-Org/MiniMax-H3/resolve/main
fetch "${SINGULARITY_MODEL_URL:-https://huggingface.co/WarmBloodAban/Minimax-h3_Singularity/resolve/main/Minimax-h3_Singularity_ref2va_v1.3_int8.safetensors}" "$M/diffusion_models/h3/Minimax-h3_Singularity_ref2va_v1.3_int8.safetensors"
fetch "$BASE/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors" "$M/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"
fetch "$BASE/vae/minimax_h3_video_vae_fp16.safetensors" "$M/vae/minimax_h3_video_vae_fp16.safetensors"
fetch "$BASE/vae/minimax_h3_audio_vae_fp32.safetensors" "$M/vae/minimax_h3_audio_vae_fp32.safetensors"
fetch "${TURBO_LORA_URL:-https://huggingface.co/lightx2v/Minimax-h3-Turbo/resolve/main/minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors}" "$M/loras/minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors"
echo 'Model downloads completed.'
