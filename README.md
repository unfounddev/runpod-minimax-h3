# MiniMax H3 Ref2VA — FRAMEKIT Runpod image

## Components
- PyTorch 2.10.0 / CUDA 13.0 / cuDNN 9 base image.
- `/opt/ComfyUI`: ComfyUI Core pinned to `3c1b7a17` (v0.39.2).
- `/opt/ComfyUI/custom_nodes/framekit_h3`: independent FRAMEKIT controls.
- System FFmpeg and ComfyUI's Python packages; no Pixaroma installation. UI styling adapted under the included Pixaroma MIT license.
- `/opt/template`: startup, model downloader and CPU smoke check.
- `/workspace/ComfyUI`: persistent models, input, output, temp and user files.
- HTTP port `8188`; `--user-directory /workspace/ComfyUI/user`.
- File Browser 2.63.23 on HTTP `8080`, with a default admin account.

## File Browser
Expose HTTP ports `8188` (ComfyUI) and `8080` (File Browser) in the Runpod template.
Leave the container start command empty. The image uses official File Browser
2.63.23 with its familiar username/password login and file management interface.
Set these environment variables in the Runpod template:

- `FILE_BROWSER_USERNAME=admin`
- `FILE_BROWSER_PASSWORD=adminadmin12`

These are also the image defaults. Override them before the first startup to
create a different account. File Browser initializes the account once; restarting
the container preserves passwords changed in the UI. Changing environment variables
after initialization does not overwrite existing accounts.
`ENABLE_FILE_BROWSER=0` disables this service. The UI opens `/workspace`, including
`ComfyUI/input` for images, `ComfyUI/models/loras` for LoRA files and
`ComfyUI/output` for generated clips. The database is stored outside the served
folder at `/var/lib/framekit-filebrowser/filebrowser.db`. Container-only data is
lost when the Pod/container storage is discarded. HTTP port 8080 is served behind
Runpod's HTTPS proxy; no extra `?direct=1` parameter is required by File Browser.

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

## FRAMEKIT controls
The migrated workflow replaces the eight Pixaroma node types it used:
Sizes, Duration, Prompt, Save MP4, Run Timer, Label and Note. Native ComfyUI LoadImage replaces the custom image loader.
It retains model/LoRA/sampler settings, reference connections, bypass modes,
seeds, node positions, duration selection and the actual saved prompt.

Sizes has standard 0.1–1.0 MP presets (approximate area after 32-pixel snapping) and Portrait/Landscape buttons; Duration
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
The image build checks FRAMEKIT registrations and legacy compatibility, H3 settings, image decoding,
stereo loudness, silence, limiting, real H.264/AAC output and workflow metadata.
No GPU or model weights are needed for those CPU checks. GPU inference and
actual model downloads still need a Pod test. `WORKFLOW_SHA256.txt` records the
migrated GitHub JSON, not the old V6 file.

## Manager, restart and Runpod proxy
ComfyUI-Manager 4.2.2 is installed through ComfyUI's pinned manager_requirements.txt.
The familiar Manager UI is enabled, including its Restart action. Restart replaces
only the ComfyUI process; it does not stop the Pod or remove its container files.
Default Manager security remains normal; unrestricted git URL/pip installation is
not enabled. Its configuration is stored in /workspace/ComfyUI/user/__manager.

Runpod Console links can open ComfyUI's root document directly. The exception is
limited to GET / navigation on a Runpod proxy domain; cross-site API requests and
writes remain rejected. File Browser uses its own username/password JSON login
and token-authenticated uploads. Its smoke check exercises login, upload and
download with Runpod HTTPS proxy headers, incorrect passwords and anonymous access.

## FRAMEKIT appearance
Click the gear on a FRAMEKIT node (or right-click → FRAMEKIT appearance).
Button/accent, title and body colors are saved per node in the workflow. Label
font size can also be changed. The workflow now uses ordinary ComfyUI Load Image,
so there is only one image preview. Old NEXUS IDs remain as legacy aliases.
