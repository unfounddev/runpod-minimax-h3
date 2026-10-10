# MiniMax H3 Ref2VA — Runpod template (validation pending)

Based on the provided 30-node workflow. Only **ComfyUI Core** and **ComfyUI-Pixaroma** are required by its nodes; no KJNodes, Civicomfy or RunpodDirect. ComfyUI Manager is optional and not installed.

## Contents
- `workflows/Minimax_H3_ref2va_original.json`: exact user-provided workflow, unchanged.
- `workflows/Minimax_H3_ref2va.json`: deployment-ready default. Removes two **bypassed, strength-zero** LoRA loader nodes referencing unavailable `HMBreastsV2.safetensors` and `H3_ta86_inkriot.safetensors`; rewires Turbo directly to Sigma Shift. Reference image/audio filenames are placeholders; supply your own before running.
- `Dockerfile`: ComfyUI plus Pixaroma only.
- `startup.sh`: persistent data in `/workspace/ComfyUI`, automatic model downloads before ComfyUI starts.
- `download_models.sh`: five selected model files; no weights stored in GitHub or Docker image.

## Runpod template settings
- Container image: `ghcr.io/unfounddev/runpod-minimax-h3:latest` **after GitHub Actions build succeeds and GHCR package is made public**.
- HTTP port: `8188`; volume mount: `/workspace`.
- `DOWNLOAD_MODELS=1` by default. Set to `0` only if weights are already present.
- At least 70 GB free persistent space recommended for models and outputs; increase for long video jobs. A 32 GB VRAM RTX 5090 was used before, but this image is not yet GPU-tested.
- First boot downloads tens of GB and may take a long time. Wait for model downloads before opening ComfyUI.

## Important limitations
- **Not yet built or deployed**. Base image tag, upstream commits and dependencies still require a real GitHub Actions build and clean GPU Pod test.
- Workflow includes bypassed reference image and optional audio nodes; upload your own images/audio and enable relevant nodes before execution.
- Check licenses and commercial/public-template terms of MiniMax H3, Singularity, LightX2V, Pixaroma before publishing.
- This is not an official MiniMax or Pixaroma image.
