"""Unbaked preview (lead, 2026-10-20): stage the current scene for export_web.py with no lightmaps, for app testing only.

Opens the scene like the bake does (common.setup_morning: morning_golden sun, internal_only parts hidden), skips the
bake, and saves blender/out/web_hero/<base>/talanta_web_baked.blend with a bake log that lists no groups, so
export_web.py writes plain materials (base colour, roughness, metallic) and no lightmap UVs. Level of detail and
instancing are export_web.py's own (as web_hero_v1). Not a release and not web_hero_v2.
Run from the repo root:
  TALANTA_SITE_BLEND=blender/out/step_FX.blend ~/.venvs/bpy/bin/python blender/web_hero/stage_unbaked.py base=preview_g
  ~/.venvs/bpy/bin/python blender/web_hero/export_web.py base=preview_g unbaked
  node blender/web_hero/node/post_glb.mjs base=preview_g bundle=web_preview_g
"""
import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUT, setup_morning, sun_vector_app, write_json
import bpy

base = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("base=")), "preview_g")
D = OUT / base; D.mkdir(parents=True, exist_ok=True)
g = setup_morning()
el, az = g["el"], g["az"]
for o in bpy.data.objects:  # no bake: drop any group tags a scene might carry
    if "bake_group" in o.keys(): del o["bake_group"]
st = g["st"]
write_json(D / "bake_log.json", {"unbaked": True, "groups": {}, "samples": 0, "date": st["date"], "time_eat": st["time_eat"],
                                 "sun_elevation_deg": el, "sun_azimuth_deg": az, "sun_dir_app": sun_vector_app(el, az),
                                 "source": os.environ.get("TALANTA_SITE_BLEND", "blender/out/talanta_site.blend"),
                                 "note": "unbaked preview for app testing: no lightmaps, plain materials"})
bpy.ops.wm.save_as_mainfile(filepath=str(D / "talanta_web_baked.blend"), compress=True)
print("STAGED", D, flush=True)
