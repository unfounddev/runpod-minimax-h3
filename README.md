# Runpod MiniMax H3 Ref2VA (draft)

This repository packages the provided `Minimax_H3_ref2va.json` workflow with ComfyUI and its custom nodes.

**NOT YET VALIDATED. Do not publish the Runpod template until the image builds and a clean GPU deployment passes.**

## Requirements
- GPU with sufficient VRAM (RTX 5090 32 GB was used previously; not a guarantee for all resolutions/durations).
- Port 8188 HTTP, volume mounted at `/workspace`, recommended 100 GB+ free space for models and outputs.
- Set `DOWNLOAD_MODELS=1` to fetch models at startup. This can take significant time.
- Singularity and Turbo download URLs are preconfigured from the links supplied by the workflow owner. You may override them with `SINGULARITY_MODEL_URL` and `TURBO_LORA_URL`. Verify model terms before public release.
- Optional zero-strength LoRAs (`HMBreastsV2.safetensors`, `H3_ta86_inkriot.safetensors`) are not included; they may show as missing in dropdowns until installed or changed.
- Upload your own reference images and optional audio; the workflow points to example files not bundled in this repository.

## Notes
- GitHub Actions publishes `ghcr.io/unfounddev/runpod-minimax-h3:latest` when a build succeeds.
- GHCR package must be public before Runpod can pull without credentials.
- Original diffusion model linked in workflow notes differs from selected Singularity diffusion model.
- License/redistribution requirements for the model and third-party components must be checked before public release.
- No claim of working deployment until tested.


## Model downloads on startup
By default `DOWNLOAD_MODELS=1`, so the startup script downloads the five core models to `/workspace/ComfyUI/models` before launching ComfyUI. Set `DOWNLOAD_MODELS=0` to skip. Downloads can take considerable time and disk space (~40 GB). Persistent storage is recommended.

**Optional LoRA caveat:** The supplied workflow references `HMBreastsV2.safetensors` and `H3_ta86_inkriot.safetensors` at strength 0. These files are **not** included in the automatic downloads because their sources have not been provided. Even at strength 0, loader nodes may require files to exist. Disable/bypass those loader nodes or provide the files separately before execution.
