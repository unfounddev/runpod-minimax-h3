# NEXUS H3 Controls

Independent controls for the current MiniMax H3 workflow. No Pixaroma imports,
assets, registration names, or runtime dependency.

- Sizes: portrait/landscape, the existing 14 resolution presets, favorites,
  collapse, editable size list, and pixel snapping.
- Duration: second buttons, editable allowed durations, custom seconds, and
  the actual H3 frame count. H3 uses 24 fps and 17*n+5 frames.
- Load Image: uploaded/selected image with preview; RGB and inverse alpha mask.
- Prompt: large editor, copy/clear, character count and optional text input.
- Save MP4: H.264/AAC, on-node playback, filename, temporary preview/save,
  optional audio trim/fade, and workflow metadata embedded for drag-back.
- Audio finishing inside each Save MP4: two-pass loudness normalization (default
  -16 LUFS, -1.5 dBTP), manual dB with limiter, or off. Silence stays silent.
- Label/Note: preserved text; double-click to edit.
- Run Timer: elapsed wall time for the current browser's ComfyUI run.

The package uses ComfyUI's existing Python dependencies and system FFmpeg.
GPU/model generation is unchanged. The loudness target is a starting point;
the loudness of actual dialogue and ambience still needs listening on a Pod.
