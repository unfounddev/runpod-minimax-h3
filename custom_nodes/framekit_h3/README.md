# FRAMEKIT H3 Controls

Controls for the MiniMax H3 workflow: standard 0.1–1.0 MP sizes, portrait/landscape,
seconds/frame counts, prompt, MP4 playback/audio finishing, labels, notes and run timer.
The workflow uses native ComfyUI LoadImage, with a single native preview.

Every FRAMEKIT node has an appearance gear and a right-click appearance menu.
Choose button/accent, title and body colors. Label font size can also be changed.
Appearance is saved in the workflow. Size labels show nominal MP; dimensions are
snapped to 32 pixels for H3, so actual area is approximately the displayed MP.

Picker and chip styling is adapted from Pixaroma under the MIT license, included
in THIRD_PARTY_LICENSE.txt. No Pixaroma backend or package installation is required.
Old NEXUS class IDs remain available under FRAMEKIT H3/Legacy for old workflows.

Audio finishing defaults to two-pass -16 LUFS / -1.5 dBTP normalization, with
manual gain/limiter and off modes. This does not regenerate missing dialogue.
