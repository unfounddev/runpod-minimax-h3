import hashlib
import json
import os
import subprocess
import tempfile
import threading
from fractions import Fraction

import folder_paths
import numpy as np
from PIL import Image, ImageOps

from .audio import ffmpeg, finish_audio
from .settings import SIZE_DEFAULT, DURATION_DEFAULT, duration, size

CATEGORY = "FRAMEKIT H3"


class NEXUSDuration:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"state": ("STRING", {"default": json.dumps(DURATION_DEFAULT)})}}
    RETURN_TYPES = ("INT", "FLOAT")
    RETURN_NAMES = ("frames", "seconds")
    FUNCTION = "run"
    CATEGORY = CATEGORY

    def run(self, state):
        return duration(state)


class NEXUSSizes:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"state": ("STRING", {"default": json.dumps(SIZE_DEFAULT)})}}
    RETURN_TYPES = ("INT", "INT")
    RETURN_NAMES = ("width", "height")
    FUNCTION = "run"
    CATEGORY = CATEGORY

    def run(self, state):
        return size(state)


class NEXUSLoadImage:
    @classmethod
    def INPUT_TYPES(cls):
        input_dir = folder_paths.get_input_directory()
        files = [os.path.relpath(os.path.join(root, name), input_dir).replace(os.sep, "/")
                 for root, _, names in os.walk(input_dir) for name in names]
        files = folder_paths.filter_files_content_types(files, ["image"])
        return {"required": {"image": (sorted(files), {"image_upload": True})}}
    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("image", "mask")
    FUNCTION = "load"
    CATEGORY = CATEGORY

    @classmethod
    def VALIDATE_INPUTS(cls, image):
        return True if folder_paths.exists_annotated_filepath(image) else "Image file does not exist"

    @classmethod
    def IS_CHANGED(cls, image):
        with open(folder_paths.get_annotated_filepath(image), "rb") as file:
            return hashlib.sha256(file.read()).hexdigest()

    def load(self, image):
        import torch
        with Image.open(folder_paths.get_annotated_filepath(image)) as source:
            source = ImageOps.exif_transpose(source)
            rgb = np.asarray(source.convert("RGB"), dtype=np.float32) / 255
            mask = (1-np.asarray(source.getchannel("A"), dtype=np.float32)/255
                    if "A" in source.getbands() else np.zeros(rgb.shape[:2], dtype=np.float32))
        return torch.from_numpy(rgb).unsqueeze(0), torch.from_numpy(mask).unsqueeze(0)


class NEXUSPrompt:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"text": ("STRING", {"default": "", "multiline": True})},
                "optional": {"text_in": ("STRING", {"forceInput": True})}}
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "run"
    CATEGORY = CATEGORY

    def run(self, text, text_in=None):
        return (text if text_in is None else text_in,)


class NEXUSLabel:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"text": ("STRING", {"default": "MiniMax H3", "multiline": True})}}
    RETURN_TYPES = ()
    FUNCTION = "run"
    CATEGORY = CATEGORY

    def run(self, text):
        return ()


class NEXUSNote(NEXUSLabel):
    pass


class NEXUSRunTimer:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}
    RETURN_TYPES = ()
    FUNCTION = "run"
    CATEGORY = CATEGORY
    OUTPUT_NODE = True

    def run(self):
        return {"ui": {}, "result": ()}

    @classmethod
    def IS_CHANGED(cls):
        return float("nan")


_save_lock = threading.Lock()


class NEXUSSaveMP4:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {
            "fps": ("FLOAT", {"default": 24, "min": 1, "max": 120, "step": 1}),
            "filename_prefix": ("STRING", {"default": "Video"}),
            "save_mode": (["save", "preview"],),
            "trim_to_audio": ("BOOLEAN", {"default": False}),
            "audio_fade_ms": ("INT", {"default": 0, "min": 0, "max": 2000, "step": 10}),
            "audio_mode": (["normalize", "gain", "off"],),
            "target_lufs": ("FLOAT", {"default": -16, "min": -36, "max": -9, "step": 1}),
            "peak_db": ("FLOAT", {"default": -1.5, "min": -9, "max": -0.5, "step": 0.5}),
            "gain_db": ("FLOAT", {"default": 0, "min": -24, "max": 24, "step": 1})},
            "optional": {"video_frames": ("IMAGE",), "audio": ("AUDIO",), "video": ("VIDEO",)},
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"}}
    RETURN_TYPES = ()
    FUNCTION = "save"
    CATEGORY = CATEGORY
    OUTPUT_NODE = True

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    def save(self, fps, filename_prefix, save_mode="save", trim_to_audio=False,
             audio_fade_ms=0, audio_mode="normalize", target_lufs=-16, peak_db=-1.5,
             gain_db=0, video_frames=None, audio=None, video=None,
             prompt=None, extra_pnginfo=None):
        if video is not None and video_frames is None:
            components = video.get_components()
            video_frames = components.images
            fps = float(components.frame_rate)
            if audio is None:
                audio = components.audio
        if video_frames is None or video_frames.ndim != 4 or video_frames.shape[0] == 0 or video_frames.shape[-1] != 3:
            raise ValueError("Connect RGB video frames to FRAMEKIT Save MP4")
        _, h, w, _ = video_frames.shape
        if w % 2 or h % 2:
            raise ValueError("MP4 dimensions must be even")
        if save_mode not in ("save", "preview"):
            raise ValueError("Invalid save mode")
        base = folder_paths.get_output_directory() if save_mode == "save" else folder_paths.get_temp_directory()
        with _save_lock:
            folder, name, counter, subfolder, _ = folder_paths.get_save_image_path(filename_prefix, base, w, h)
            if os.path.commonpath([os.path.realpath(base), os.path.realpath(folder)]) != os.path.realpath(base):
                raise ValueError("Output must stay inside the ComfyUI output folder")
            while True:
                filename = f"{name}_{counter:05}.mp4"
                path = os.path.join(folder, filename)
                try:
                    with open(path, "xb"):
                        pass
                    break
                except FileExistsError:
                    counter += 1
        try:
            with tempfile.TemporaryDirectory(prefix="framekit-") as temporary:
                cmd = [ffmpeg(), "-hide_banner", "-loglevel", "error", "-y",
                       "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
                       "-r", str(Fraction(str(float(fps)))), "-i", "pipe:0"]
                report = "No audio connected"
                if audio is not None:
                    samples = audio["waveform"].detach().float().cpu().numpy()
                    if samples.ndim == 3:
                        if samples.shape[0] != 1:
                            raise ValueError("Save one audio/video batch at a time")
                        samples = samples[0]
                    rate = int(audio["sample_rate"])
                    processed, measured = finish_audio(samples, rate, audio_mode, target_lufs, peak_db, gain_db, audio_fade_ms)
                    raw_path = os.path.join(temporary, "audio.f32")
                    processed.T.astype("<f4").tofile(raw_path)
                    cmd += ["-f","f32le","-ar",str(rate),"-ac",str(processed.shape[0]),"-i",raw_path]
                    report = f"Audio: {audio_mode}"
                    if measured:
                        report += f" | input {measured['input_i']} LUFS | target {target_lufs:g} LUFS"
                metadata = {}
                if extra_pnginfo:
                    metadata.update(extra_pnginfo)
                if prompt:
                    metadata["prompt"] = prompt
                # JSON generated by ComfyUI can contain NaN cache markers. Convert them to null.
                def clean(value):
                    if isinstance(value, float) and not np.isfinite(value):
                        return None
                    if isinstance(value, dict):
                        return {k:clean(v) for k,v in value.items()}
                    if isinstance(value, (list,tuple)):
                        return [clean(v) for v in value]
                    return value
                if metadata:
                    meta_path = os.path.join(temporary, "metadata.txt")
                    def escape(value):
                        return "".join("\\"+c if c in "\\=;#\n" else c for c in value)
                    with open(meta_path, "w", encoding="utf-8") as file:
                        file.write(";FFMETADATA1\n")
                        for key,value in metadata.items():
                            file.write(escape(key)+"="+escape(json.dumps(clean(value),ensure_ascii=False))+"\n")
                    cmd += ["-i", meta_path, "-map_metadata", "2" if audio is not None else "1"]
                cmd += ["-map","0:v:0","-c:v","libx264","-crf","18","-pix_fmt","yuv420p"]
                if audio is not None:
                    cmd += ["-map","1:a:0","-c:a","aac","-b:a","192k"]
                    if trim_to_audio:
                        cmd += ["-shortest"]
                cmd += ["-movflags","use_metadata_tags+faststart",path]
                process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL)
                errors = []
                def drain():
                    errors.append(process.stderr.read())
                thread = threading.Thread(target=drain, daemon=True)
                thread.start()
                try:
                    import comfy.model_management
                    for frame in video_frames:
                        comfy.model_management.throw_exception_if_processing_interrupted()
                        process.stdin.write((frame.detach().float().cpu().numpy().clip(0,1)*255).astype(np.uint8).tobytes())
                except BrokenPipeError:
                    pass
                except BaseException:
                    process.kill()
                    raise
                finally:
                    try:
                        process.stdin.close()
                    except OSError:
                        pass
                    process.wait()
                    thread.join()
                if process.returncode:
                    raise RuntimeError(b"".join(errors).decode("utf-8","replace"))
        except BaseException:
            if os.path.exists(path):
                os.remove(path)
            raise
        # Match ComfyUI PreviewVideo: standard media output for Queue and Assets.
        clip = {"filename": filename, "subfolder": subfolder,
                "type": "output" if save_mode == "save" else "temp",
                "format": "video/mp4"}
        return {"ui": {"images": [clip], "animated": (True,), "text": [report]}, "result": ()}



NODE_CLASS_MAPPINGS = {cls.__name__:cls for cls in (NEXUSDuration, NEXUSSizes,
    NEXUSLoadImage, NEXUSPrompt, NEXUSSaveMP4, NEXUSLabel, NEXUSNote, NEXUSRunTimer)}
# Keep old workflows loadable while new workflows use the FRAMEKIT names.
for name, cls in list(NODE_CLASS_MAPPINGS.items()):
    cls.CATEGORY = "FRAMEKIT H3/Legacy"
    if name != "NEXUSLoadImage":
        new_name = name.replace("NEXUS", "FRAMEKIT")
        NODE_CLASS_MAPPINGS[new_name] = type(new_name, (cls,), {"CATEGORY": CATEGORY})
NODE_DISPLAY_NAME_MAPPINGS = {name: "FRAMEKIT · " + name.replace("NEXUS", "").replace("FRAMEKIT", "")
    .replace("SaveMP4", "Save MP4").replace("LoadImage", "Load Image").replace("RunTimer", "Run Timer")
    + (" (legacy)" if name.startswith("NEXUS") else "") for name in NODE_CLASS_MAPPINGS}
