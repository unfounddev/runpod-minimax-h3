"""Settings shared by the controls and their tests. No model dependencies."""
import json
import math

SIZES = [[608,352],[736,416],[864,480],[960,544],[1056,608],[1152,640],
         [1216,672],[1280,736],[1344,768],[1376,768],[1504,832],[1664,928],
         [1824,1024],[1920,1088]]
SIZE_DEFAULT = {"sizes": SIZES, "selected": 6, "orientation": "landscape", "snap": 32}
DURATION_DEFAULT = {"seconds": 5, "values": [3,4,5,6,7,8,9,10,12,15]}


def parse_state(value):
    state = json.loads(value) if isinstance(value, str) else value
    if not isinstance(state, dict):
        raise ValueError("NEXUS settings must be a JSON object")
    return state


def duration(state):
    seconds = float(parse_state(state).get("seconds", 5))
    if not math.isfinite(seconds) or not 0 < seconds <= 15:
        raise ValueError("H3 duration must be greater than 0 and at most 15 seconds")
    # H3 accepts 17*n+5 frames at 24 fps. Half-up rounding matches the UI.
    raw = max(5, math.floor(seconds * 24 + 0.5))
    frames = raw + (5 - raw) % 17
    return frames, frames / 24


def size(state):
    state = parse_state(state)
    pairs = state.get("sizes", SIZES)
    index = int(state.get("selected", 6))
    if not pairs or not 0 <= index < len(pairs):
        raise ValueError("Choose a valid video size")
    a, b = sorted(map(int, pairs[index]))
    w, h = (b, a) if state.get("orientation", "landscape") == "landscape" else (a, b)
    step = int(state.get("snap", 32))
    if step not in (8,16,32,64):
        raise ValueError("Size snap must be 8, 16, 32 or 64 pixels")
    w, h = (math.floor(n / step + 0.5) * step for n in (w, h))
    if not (64 <= w <= 4096 and 64 <= h <= 4096):
        raise ValueError("Video dimensions must be between 64 and 4096 pixels")
    return w, h
