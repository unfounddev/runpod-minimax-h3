"""CPU integration check: the actual node pack must load and encode audible MP4."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument("--comfy", required=True)
parser.add_argument("--pack", required=True)
parser.add_argument("--workflow")
opts = parser.parse_args()
sys.path.insert(0, str(Path(opts.comfy).resolve()))
from comfy.cli_args import args
args.cpu = True
import folder_paths
import numpy as np
import torch
from PIL import Image

spec = importlib.util.spec_from_file_location("framekit_h3", Path(opts.pack)/"__init__.py",
                                             submodule_search_locations=[opts.pack])
pack = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pack
spec.loader.exec_module(pack)
from framekit_h3.settings import duration, size, SIZE_DEFAULT
from framekit_h3.audio import finish_audio, loudness, run_ffmpeg

assert len(pack.NODE_CLASS_MAPPINGS) == 15
for cls in pack.NODE_CLASS_MAPPINGS.values():
    cls.INPUT_TYPES()
assert duration('{"seconds":5}') == (124,124/24)
assert duration('{"seconds":15}')[0] == 362
assert size(json.dumps(SIZE_DEFAULT)) == (1344,768)
assert size(json.dumps({**SIZE_DEFAULT,"orientation":"portrait"})) == (768,1344)
assert 'mp' not in SIZE_DEFAULT
for index in range(len(SIZE_DEFAULT['sizes'])):
    w,h=size({**SIZE_DEFAULT,'selected':index})
    assert w%32==h%32==0
    assert size({**SIZE_DEFAULT,'selected':index,'orientation':'portrait'})==(h,w)
assert size({'sizes': [[965, 547]], 'selected': 0, 'snap': 8}) == (960, 544)
for seconds in (-1,0,16,float("nan")):
    try:
        duration(json.dumps({"seconds":seconds}))
        raise AssertionError("Invalid duration accepted")
    except ValueError:
        pass

rate = 48000
t = np.arange(rate*3,dtype=np.float32)/rate
signal = np.stack([0.015*np.sin(2*np.pi*440*t),0.008*np.sin(2*np.pi*660*t)])
processed, original = finish_audio(signal,rate)
measured = loudness(processed,rate)
assert float(measured["input_i"])-float(original["input_i"]) > 10, (original,measured)
assert abs(float(measured["input_i"])+16) < 0.5, measured
assert float(measured["input_tp"]) <= -1.0, measured
assert processed.shape == signal.shape
assert np.array_equal(finish_audio(signal,rate,mode="off")[0], signal)
silence = np.zeros_like(signal)
assert not finish_audio(silence,rate)[0].any()
limited,_ = finish_audio(signal*30,rate,mode="gain",gain_db=12)
assert np.max(np.abs(limited)) <= 10**(-1.5/20)+0.001

with tempfile.TemporaryDirectory(prefix="nexus-test-") as temporary:
    folder_paths.set_output_directory(temporary)
    folder_paths.set_temp_directory(temporary)
    folder_paths.input_directory = temporary
    Image.new("RGBA",(64,64),(255,80,40,128)).save(Path(temporary)/"reference.png")
    load = pack.NODE_CLASS_MAPPINGS["NEXUSLoadImage"]()
    assert "reference.png" in load.INPUT_TYPES()["required"]["image"][0]
    image,mask = load.load("reference.png")
    assert tuple(image.shape)==(1,64,64,3) and abs(float(mask.mean())-127/255)<0.001
    save = pack.NODE_CLASS_MAPPINGS["NEXUSSaveMP4"]()
    frames = image.repeat(72,1,1,1)
    audio = {"waveform":torch.from_numpy(signal).unsqueeze(0),"sample_rate":rate}
    result = save.save(24,"nexus-smoke",video_frames=frames,audio=audio,
                       prompt={"cache":float("nan")},extra_pnginfo={"workflow":{"nodes":[],"links":[]}})
    from comfy_execution.jobs import get_outputs_summary, count_previewable_outputs
    count, preview = get_outputs_summary({"228": result["ui"]})
    assert count == 1 and preview["filename"].endswith(".mp4")
    assert preview["type"] == "output" and preview["mediaType"] == "images"
    assert count_previewable_outputs({"228": result["ui"]}) == 1
    assert result["ui"]["animated"] == (True,)
    assert preview["format"] == "video/mp4"
    filename = result["ui"]["images"][0]["filename"]
    path = Path(temporary)/filename
    decoded = run_ffmpeg(["-i",str(path),"-vn","-f","f32le","-ac","2","-ar",str(rate),"pipe:1"])
    samples = np.frombuffer(decoded.stdout,dtype="<f4").reshape(-1,2).T
    final = loudness(samples,rate)
    assert abs(float(final["input_i"])+16) < 0.6,final
    import av
    with av.open(str(path)) as video:
        assert video.streams.video[0].width == 64
        assert video.streams.audio[0].sample_rate == rate
        assert abs(video.duration/1_000_000-3) < 0.1
        assert json.loads(video.metadata["prompt"])["cache"] is None
        assert "workflow" in video.metadata
    other = save.save(24,"nexus-smoke",video_frames=frames,audio=None,save_mode="preview")
    assert other["ui"]["images"][0]["filename"] != filename
    assert other["ui"]["images"][0]["type"] == "temp"

print("FRAMEKIT smoke passed: 7 nodes + 8 legacy aliases, 32-pixel sizes, H3, audio, MP4 and metadata")

if opts.workflow:
    workflow=json.loads(Path(opts.workflow).read_text(encoding="utf-8"))
    nodes={node["id"]:node for node in workflow["nodes"]}
    assert len(nodes)==len(workflow["nodes"])
    for link in workflow["links"]:
        ident,source,source_slot,target,target_slot,kind=link
        output=nodes[source]["outputs"][source_slot]
        entry=nodes[target]["inputs"][target_slot]
        assert ident in output["links"] and entry["link"]==ident,link
    for node in nodes.values():
        if node["type"].startswith("FRAMEKIT"):
            cls=pack.NODE_CLASS_MAPPINGS[node["type"]]
            inputs=cls.INPUT_TYPES().get("required",{})
            widget_names=[name for name,spec in inputs.items()
                if isinstance(spec[0],list) or spec[0] in ("STRING","INT","FLOAT","BOOLEAN")]
            values=node.get("widgets_values",[])
            assert len(values)==len(widget_names),(node["id"],widget_names,values)
            options=dict(zip(widget_names,values))
            if node["type"]=="FRAMEKITSizes":assert cls().run(**options)==(960,544)
            if node["type"]=="FRAMEKITDuration":assert cls().run(**options)[0]==362
            if node["type"]=="FRAMEKITSaveMP4":
                assert options["audio_mode"]=="normalize" and options["target_lufs"]==-16
    assert all(not n["type"].startswith("NEXUS") for n in nodes.values())
    print("Workflow smoke passed: links, slot positions, FRAMEKIT widget values and output paths")
