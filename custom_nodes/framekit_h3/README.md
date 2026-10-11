# FRAMEKIT H3 Controls

Controls for the MiniMax H3 workflow: pixel sizes divisible by 32, portrait/landscape,
seconds/frame counts, prompt, MP4 playback/audio finishing, labels, notes and run timer.
The workflow uses native ComfyUI LoadImage, with a single native preview.

Change all FRAMEKIT node colors in ComfyUI Settings > FRAMEKIT > Appearance.
Header, body, accent colors and label font size are saved in user settings.
Size labels show pixels, including 1344 × 768 for Turbo 768p (or 768 × 1344
in portrait). Custom sizes must be divisible by 32. Legacy size states are migrated.

Picker and chip styling is adapted from Pixaroma under the MIT license, included
in THIRD_PARTY_LICENSE.txt. No Pixaroma backend or package installation is required.
Old NEXUS class IDs remain available under FRAMEKIT H3/Legacy for old workflows.

Audio finishing defaults to two-pass -16 LUFS / -1.5 dBTP normalization, with
manual gain/limiter and off modes. This does not regenerate missing dialogue.
