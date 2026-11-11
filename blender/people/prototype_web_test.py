"""Verify that the prototype web GLBs retain skinning, UVs and a near-LOD budget."""
import json
import struct
import sys
from pathlib import Path

out = Path(sys.argv[1])
for name in ("Female_Adult_01", "Male_Adult_01"):
    asset = out / f"{name}.glb"
    data = asset.read_bytes()
    chunk_size, chunk_type = struct.unpack_from("<II", data, 12)
    assert chunk_type == 0x4E4F534A
    gltf = json.loads(data[20:20 + chunk_size])
    primitives = [p for mesh in gltf["meshes"] for p in mesh["primitives"]]
    assert gltf["skins"] and gltf["textures"]
    assert all({"JOINTS_0", "WEIGHTS_0", "TEXCOORD_0"} <= p["attributes"].keys() for p in primitives)
    triangles = sum(gltf["accessors"][p["indices"]]["count"] // 3 for p in primitives)
    assert 5500 <= triangles <= 6000, (name, triangles)
    assert asset.stat().st_size < 2_000_000, (name, asset.stat().st_size)
    if "--animated" in sys.argv:
        clips = {clip["name"]: clip for clip in gltf["animations"]}
        required = {"Idle_Loop", "Sitting_Idle_Loop"}
        if "--sprint" in sys.argv:
            required.add("Sprint_Loop")
        assert required <= clips.keys()
        for clip_name in sorted(required):
            clip = clips[clip_name]
            joints = set(gltf["skins"][0]["joints"])
            rotations = [channel for channel in clip["channels"]
                         if channel["target"]["path"] == "rotation" and channel["target"]["node"] in joints]
            assert len(rotations) >= 12, (clip_name, "missing joint animation")
            timelines = [gltf["accessors"][sampler["input"]] for sampler in clip["samplers"]]
            assert max(time["max"][0] - time["min"][0] for time in timelines) > .5, (clip_name, "empty clip")
    print(f"{name}: {triangles} triangles, {asset.stat().st_size:,} bytes")
