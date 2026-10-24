"""web_hero_v2 (2026-10-20): prepare blender/out/web_hero/maps/ and maps/stages.json for a partial re-bake.

The v1 maps were lost; maps decoded from the v1 GLBs (node/extract_v1_maps.mjs) stand in for the groups that did
not change. This script
1. deletes every stage entry that holds a changed group (bowl: stadium_*, roof; forecourt; ground tiles 05, 06, 09,
   10 under the bowl and plaza), so bake_lightmaps.py bakes them again;
2. writes stage entries for the unchanged batches in the v2 batch layout (bake_lightmaps.py BATCHES), with the v1
   object signatures, marked as extracted, so bake_lightmaps.py skips them;
3. copies the extracted PNGs into maps/ (never over a map baked since).
AO is listed only for the groups whose AO the export ships; albedo only where the extracted set has it.
Run from the repo root: python3 blender/web_hero/migrate_stages_v2.py
"""
import json, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAPS = ROOT / "blender/out/web_hero/maps"
EXT = ROOT / "blender/out/web_hero/maps_v1_extracted"
st = json.loads((MAPS / "stages.json").read_text())
assert st["key"] == {"samples": 128, "test": False, "light": "morning_golden"}, st["key"]
done = st["done"]

# per-group v1 signature from the batch entries
sig = {}
for tag, rec in done.items():
    if ":" not in tag or "sig" not in rec: continue
    for g, s_ in zip(tag.split(":")[1].split("+"), rec["sig"]): sig[g] = s_

CHANGED = {"stadium_shell", "stadium_fins", "stadium_ornament", "roof", "forecourt", "ground_05", "ground_06", "ground_09", "ground_10"}
removed = [t for t in done if ":" in t and set(t.split(":")[1].split("+")) & CHANGED]
for t in removed: del done[t]
removed += [t for t in list(done) if t in CHANGED]
for t in CHANGED: done.pop(t, None)  # their light scales come from the new bake

rest = [f"ground_{k:02d}" for k in range(12) if k not in (5, 6, 9, 10)]
KEEP = {"light": [["sport", "roads", "site_built"], ["suburbs", "traffic"], rest,
                  [f"ground_{k:02d}" for k in range(12, 16)], [f"ground_{k:02d}" for k in range(16, 24)]],
        "ao": [["suburbs", "traffic"]]}
added = []
for kind, batches in KEEP.items():
    for b in batches:
        missing = [g for g in b if not (EXT / f"{g}_{kind}.png").exists()]
        assert not missing, (kind, missing)
        tag = f"{kind}:{'+'.join(b)}"
        done[tag] = {"seconds": 0.0, "samples": 64 if kind == "ao" else 128, "sig": [sig[g] for g in b],
                     "source": "decoded from the web_hero_v1 GLB KTX2 textures (lossy), 2026-10-20"}
        added.append(tag)
copied = 0
for f in sorted(EXT.glob("*.png")):
    dst = MAPS / f.name
    g = f.stem.rsplit("_", 1)[0]
    if g in CHANGED or dst.exists(): continue
    shutil.copy2(f, dst); copied += 1
(MAPS / "stages.json").write_text(json.dumps(st, indent=1) + "\n")
print(json.dumps({"removed": removed, "added": added, "copied_pngs": copied}, indent=1))
