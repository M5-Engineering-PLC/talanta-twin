"""Pass K, K4 (engineering/cloud_pass_k_2026-10-24.md): re-apply the training grass look on an existing scene.

build_site_detail.py builds `training_grass` with blender/grass_look.py. Scenes built before pass K (step_FE to step_FJ)
carry the old saturated stripes, so the step_FK chain runs this once. Both states: the material is shared by the
training pitches (stripes), the warm-up track infield and the south-west lawn (no UV, no stripes, no markings).
Run from the repo root: TALANTA_SITE_BLEND=blender/out/step_FK.blend ~/.venvs/bpy/bin/python blender/context/grass_k.py
"""
import json, os, sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "blender")); import grass_look
bpy.ops.wm.open_mainfile(filepath=os.environ.get("TALANTA_SITE_BLEND", str(ROOT / "blender/out/talanta_site.blend")))
m = bpy.data.materials.get("training_grass")
if m is None: raise SystemExit("no training_grass material in this scene")
grass_look.build(m)
users = sorted(o.name for o in bpy.data.objects if o.type == "MESH" and any(s is m for s in o.data.materials))
print("GRASS_K " + json.dumps({"material": m.name, "users": users}), flush=True)
bpy.ops.wm.save_mainfile()
