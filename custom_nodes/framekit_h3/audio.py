"""FFmpeg loudness finishing; stereo is processed together, never per channel."""
import json
import math
import shutil
import subprocess
import numpy as np


def ffmpeg():
    executable = shutil.which("ffmpeg")
    if not executable:
        try:
            import imageio_ffmpeg
            executable = imageio_ffmpeg.get_ffmpeg_exe()
        except ImportError as exc:
            raise RuntimeError("NEXUS requires FFmpeg") from exc
    return executable


def run_ffmpeg(arguments, data=None):
    result = subprocess.run([ffmpeg(), "-hide_banner", "-nostdin", *arguments],
                            input=data, capture_output=True)
    if result.returncode:
        raise RuntimeError("NEXUS FFmpeg: " + result.stderr.decode("utf-8", "replace")[-3000:])
    return result


def loudness(data, sample_rate, target_lufs=-16.0, peak_db=-1.5):
    channels = data.shape[0]
    result = run_ffmpeg(["-f","f32le","-ar",str(sample_rate),"-ac",str(channels),
                         "-i","pipe:0","-af",f"loudnorm=I={target_lufs}:TP={peak_db}:LRA=11:print_format=json","-f","null","-"],
                        data.T.astype("<f4").tobytes())
    text = result.stderr.decode("utf-8", "replace")
    return json.loads(text[text.rfind("{"):text.rfind("}")+1])


def finish_audio(data, sample_rate, mode="normalize", target_lufs=-16.0,
                 peak_db=-1.5, gain_db=0.0, fade_ms=0):
    data = np.asarray(data, dtype=np.float32)
    if data.ndim != 2 or data.shape[0] not in (1,2) or data.shape[1] == 0:
        raise ValueError("NEXUS audio must be non-empty mono or stereo")
    if not np.isfinite(data).all():
        raise ValueError("Generated audio contains NaN or infinity")
    if not 8000 <= int(sample_rate) <= 192000:
        raise ValueError("Unsupported audio sample rate")
    if mode not in ("normalize", "gain", "off"):
        raise ValueError("Unknown audio mode")
    if not (-36 <= target_lufs <= -9 and -9 <= peak_db <= -0.5 and -24 <= gain_db <= 24):
        raise ValueError("Audio settings are outside their supported range")
    if not 0 <= fade_ms <= 2000:
        raise ValueError("Fade must be between 0 and 2000 ms")
    filters = []
    measured = None
    if mode == "normalize" and np.max(np.abs(data)) > 1e-8:
        measured = loudness(data, sample_rate, target_lufs, peak_db)
        if math.isfinite(float(measured["input_i"])):
            filters.append(
                f"loudnorm=I={target_lufs}:TP={peak_db}:LRA=11:"
                f"measured_I={measured['input_i']}:measured_TP={measured['input_tp']}:"
                f"measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}:"
                f"offset={measured['target_offset']}:linear=true")
    elif mode == "gain":
        filters.extend([f"volume={gain_db}dB",
                        f"alimiter=limit={10**(peak_db/20)}:level=false:latency=true"])
    if fade_ms:
        filters.append(f"afade=t=in:st=0:d={fade_ms/1000:.3f}")
    if not filters:
        return data.copy(), measured
    channels = data.shape[0]
    result = run_ffmpeg(["-f","f32le","-ar",str(sample_rate),"-ac",str(channels),
                         "-i","pipe:0","-af",",".join(filters),"-ar",str(sample_rate),
                         "-ac",str(channels),"-f","f32le","pipe:1"],
                        data.T.astype("<f4").tobytes())
    processed = np.frombuffer(result.stdout, dtype="<f4").reshape(-1,channels).T.copy()
    # Resampling may change the last few samples; retain the original timeline.
    processed = processed[:, :data.shape[1]]
    if processed.shape[1] < data.shape[1]:
        processed = np.pad(processed, ((0,0),(0,data.shape[1]-processed.shape[1])))
    return processed, measured
