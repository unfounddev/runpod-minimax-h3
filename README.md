# MiniMax H3 Ref2VA — Runpod template (V6)

## Source of truth
`workflows/Minimax_H3_ref2va.json` is a byte-for-byte copy of the user-supplied workflow. No node, connection, bypass, seed, prompt, or LoRA value has been changed. SHA-256 recorded in `WORKFLOW_SHA256.txt`.

## Components
- `/opt/ComfyUI`: ComfyUI Core pinned to commit `3c1b7a17`.
- `/opt/ComfyUI/custom_nodes/ComfyUI-Pixaroma`: only custom node pack, pinned to `e464839a`.
- `/opt/template`: startup, downloader, and unmodified workflow installed by Dockerfile.
- `/workspace/ComfyUI`: models, input, output, temp and user workflow storage. ComfyUI runs with `--user-directory /workspace/ComfyUI/user`.
- ComfyUI web UI: HTTP port `8188`.

## Models downloaded on first Pod start
1. `diffusion_models/h3/Minimax-h3_Singularity_ref2va_v1.3_int8.safetensors`
2. `text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`
3. `vae/minimax_h3_video_vae_fp16.safetensors`
4. `vae/minimax_h3_audio_vae_fp32.safetensors`
5. `loras/minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors`

The two optional bypassed LoRA nodes (`HMBreastsV2.safetensors`, `H3_ta86_inkriot.safetensors`) remain in the workflow but their weights are **not** downloaded. Enabling those nodes requires separately supplying the weights.

## GitHub and Runpod
1. Upload all files including the hidden `.github/workflows/build.yml` folder into the **repository root** on branch `main`.
2. Check GitHub Actions for successful Docker build. Build success does not guarantee model downloads or GPU inference.
3. Set the published GHCR package visibility to **public** before using it as a public Runpod template.
4. Use image `ghcr.io/unfounddev/runpod-minimax-h3:latest`, HTTP port `8188`, mount `/workspace` (persistent volume if needed), `DOWNLOAD_MODELS=1`.
5. Allow for tens of GB of downloads; reserve at least ~70 GB free for model weights plus more for outputs. Verify Runpod disk sizing before launching.
6. Load workflow, supply your own reference image/audio files and enable the required bypassed input nodes before running. This package does not include the example input media.

## Not yet validated
- Docker base tag, upstream Git commit compatibility, Python dependencies and GPU inference need a real CI build and Pod test.
- Hugging Face model URLs, permissions and downloaded file integrity need verification during the first start. Downloader resumes `.part` files but currently only checks non-empty completed files, not hashes.
- Review model, LoRA and node licenses before making a commercial/public template.
