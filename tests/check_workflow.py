import hashlib
import json
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[1]
path = root/"workflows/Minimax_H3_ref2va.json"
current = json.loads(path.read_text(encoding="utf-8"))
original = json.loads(subprocess.check_output(["git","show","f3c879a:workflows/Minimax_H3_ref2va.json"],cwd=root))
assert current["links"] == original["links"]
assert {n["id"] for n in current["nodes"]} == {n["id"] for n in original["nodes"]}
before = {n["id"]:n for n in original["nodes"]}
after = {n["id"]:n for n in current["nodes"]}
for n in current["nodes"]:
    assert not n["type"].startswith("Pixaroma")
    old = before[n["id"]]
    for field in ("pos","mode","order"):
        assert n.get(field) == old.get(field), (n["id"],field)
    if not old["type"].startswith("Pixaroma"):
        assert n == old, n["id"]
assert after[239]["widgets_values"][0] == before[239]["properties"]["promptState"]["text"]
assert json.loads(after[234]["widgets_values"][0])["seconds"] == 15
for node_id in (228,246):
    assert after[node_id]["widgets_values"][-4:] == ["normalize",-16,-1.5,0]
digest = hashlib.sha256(path.read_bytes()).hexdigest()
assert digest in (root/"WORKFLOW_SHA256.txt").read_text()
links = {link[0]:link for link in current["links"]}
for node in current["nodes"]:
    for slot,item in enumerate(node.get("inputs",[])):
        if item.get("link") is not None:
            link=links[item["link"]]
            assert (link[3],link[4])==(node["id"],slot)
            assert link[5]==item["type"]
            source=after[link[1]]["outputs"][link[2]]
            assert source["type"]==link[5]
print("Workflow migration passed: model/sampler values, prompt, 15 seconds, positions, modes and all links preserved")
