# MiniMax H3 Ref2VA — NEXUS Runpod image

## Components
- PyTorch 2.10.0 / CUDA 13.0 / cuDNN 9 base image.
- `/opt/ComfyUI`: ComfyUI Core pinned to `3c1b7a17` (v0.39.2).
- `/opt/ComfyUI/custom_nodes/nexus_h3`: independent NEXUS controls.
- System FFmpeg and ComfyUI's Python packages; no Pixaroma installation.
- `/opt/template`: startup, model downloader and CPU smoke check.
- `/workspace/ComfyUI`: persistent models, input, output, temp and user files.
- HTTP port `8188`; `--user-directory /workspace/ComfyUI/user`.
- Copyparty 1.20.25 file manager on HTTP `8080`, when credentials are configured.

## File manager
Expose HTTP ports `8188` (ComfyUI) and `8080` (File manager) in the Runpod template.
Leave the container start command empty. In Runpod, create a Secret and bind it
to environment variable `FILE_BROWSER_PASSWORD`. Use a unique password of
12–128 letters, numbers or `!@$_.+-`. The username defaults to `admin`; override
it with `FILE_BROWSER_USERNAME` (letters, numbers, underscore, hyphen).
Without a password the file manager stays disabled and ComfyUI still starts.
`ENABLE_FILE_BROWSER=0` also disables it.

After deploying the new image, open Connect → HTTP Service 8080 and log in.
It serves `/workspace`: upload LoRAs into `ComfyUI/models/loras`, main weights
into `ComfyUI/models/diffusion_models/h3`, and download clips from `ComfyUI/output`.
Uploads can resume after a network interruption. Refresh ComfyUI's model list
after uploading, or restart ComfyUI. The manager starts before model downloads.
No anonymous file access is granted. Its private configuration stays outside
the served directory, and symlinks cannot escape the workspace. Model files
remain temporary if no volume is attached; a file manager does not add storage.

## Workflow comes from GitHub
Workflow JSON is not baked into the image. Every Pod start downloads
`workflows/Minimax_H3_ref2va.json` from this repository's `main` branch into
`/workspace/ComfyUI/user/default/workflows/GitHub/Minimax_H3_ref2va.json`.
Only that managed copy is refreshed. Save personal changes under another name
outside the GitHub subfolder. A failed download keeps the previous file and
prints a warning; ComfyUI can still open for manual workflow import.

Set `DOWNLOAD_WORKFLOW=0` to disable refresh. `WORKFLOW_URL` can override the
raw JSON URL. Restart the Pod or manually import new JSON to use a GitHub edit;
an already-open canvas does not update itself. GitHub raw caching can delay
visibility of a just-pushed edit briefly.

Changes limited to JSON, its checksum or README skip image builds. Changes to
custom node code, dependencies, startup or Dockerfile need a build and a Pod
using the new image. Existing Pods keep their existing image.

## NEXUS controls
The migrated workflow replaces the eight Pixaroma node types it used:
Sizes, Duration, Load Image, Prompt, Save MP4, Run Timer, Label and Note.
It retains model/LoRA/sampler settings, reference connections, bypass modes,
seeds, node positions, duration selection and the actual saved prompt.

Sizes has the original resolution list and Portrait/Landscape buttons; Duration
has the original second buttons and H3 frame-count readout. Prompt/image/video
previews stay on their respective nodes. Native ComfyUI still owns the canvas,
Queue/Run and model nodes. This is not a copy of every Pixaroma feature.

Both A/B Save MP4 nodes default to two-pass loudness normalization:
`audio_mode=normalize`, `target_lufs=-16`, `peak_db=-1.5`, `gain_db=0`.
Use `gain` for manual dB adjustment with a limiter, or `off` to compare raw decoded
audio. Fade defaults to 0. Stereo keeps its balance and timing. These controls
do not regenerate missing dialogue or fix model-generated distortion. Audition
real H3 clips on the Pod before judging the final sound.

## Model downloads
With `DOWNLOAD_MODELS=1` (default), startup downloads:
1. `diffusion_models/h3/Minimax-h3_Singularity_ref2va_v1.3_int8.safetensors`
2. `text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`
3. `vae/minimax_h3_video_vae_fp16.safetensors`
4. `vae/minimax_h3_audio_vae_fp32.safetensors`
5. `loras/minimax_h3_ref2v_turbo_8step_v1.0_768p_comfyui_bf16.safetensors`

Optional bypassed LoRA weights and reference media are not included.

## Runpod
Use `ghcr.io/unfounddev/runpod-minimax-h3:latest`, HTTP port `8188`, and mount
`/workspace`. The package must be public or Runpod needs registry credentials.
Reserve at least about 70 GB for weights plus output storage. Open the GitHub
workflow, upload references and enable the desired input nodes.

## Validation
The build also verifies the file manager's authentication and real upload/download.
The image build checks all eight registrations, H3 settings, image decoding,
stereo loudness, silence, limiting, real H.264/AAC output and workflow metadata.
No GPU or model weights are needed for those CPU checks. GPU inference and
actual model downloads still need a Pod test. `WORKFLOW_SHA256.txt` records the
migrated GitHub JSON, not the old V6 file.
