"""Stage the verified local Kenya and Spain player assets for match integration."""
import argparse
import hashlib
import json
import shutil
import struct
from pathlib import Path


def check_asset(path):
    data = path.read_bytes()
    magic, version, total, chunk_length, chunk_type = struct.unpack_from("<4sIIII", data)
    if (magic, version, total, chunk_type) != (b"glTF", 2, len(data), 0x4E4F534A):
        raise ValueError(f"Invalid GLB: {path}")
    model = json.loads(data[20:20 + chunk_length])
    clips = {clip["name"] for clip in model.get("animations", [])}
    if not {"Idle_Loop", "Sprint_Loop"} <= clips or not model.get("skins"):
        raise ValueError(f"Missing skin or match clips: {path}")
    triangles = sum(model["accessors"][p["indices"]]["count"] // 3
                    for mesh in model["meshes"] for p in mesh["primitives"])
    if triangles > 6000:
        raise ValueError(f"Near-detail budget exceeded: {path}")
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data),
            "triangles": triangles, "clips": sorted(clips)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kenya", type=Path)
    parser.add_argument("spain", type=Path)
    parser.add_argument("license", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    sources = {"kenya-white": args.kenya, "spain-red": args.spain}
    entries = {role: check_asset(path) for role, path in sources.items()}
    if entries["kenya-white"]["sha256"] == entries["spain-red"]["sha256"]:
        raise ValueError("The two kit variants must use different assets")
    notice = args.license.read_bytes()
    if b"Copyright (c) 2020 Microsoft" not in notice or b"MIT License" not in notice:
        raise ValueError("Missing Rocketbox MIT notice")
    args.output.mkdir(parents=True, exist_ok=True)
    for role, source in sources.items():
        entries[role]["file"] = f"{role}.glb"
        shutil.copyfile(source, args.output / entries[role]["file"])
    (args.output / "LICENSE.md").write_bytes(notice)
    (args.output / "manifest.json").write_text(
        json.dumps({"players": entries}, indent=2) + "\n", encoding="utf-8")
    print("Staged two match kits with standing and sprint clips")


if __name__ == "__main__":
    main()
