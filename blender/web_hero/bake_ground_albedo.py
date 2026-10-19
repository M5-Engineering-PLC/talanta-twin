"""Re-bake the albedo maps of the 24 ground tiles from the baked web hero scene (L3b, PLAN.md section 12).

Run from the repo root:  ~/.venvs/bpy/bin/python blender/web_hero/bake_ground_albedo.py
Needs blender/out/web_hero/talanta_web_baked.blend (branch assets/web_hero_v1_bake). That file keeps each ground
tile's material copy with its bake_target node and the "lightmap" UV set, so the albedo lands on the same UVs as
the shipped lightmaps. Same settings as the albedo pass of bake_lightmaps.py: DIFFUSE colour only, 4 samples,
margin 2, 1024 px, 8-bit sRGB PNG. Albedo has no lighting, so the light preset does not matter.
Writes blender/out/web_hero/maps/ground_NN_albedo.png. node/patch_ground_albedo.mjs puts them into the site GLB.
"""
import sys, time
from pathlib import Path
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "blender/out/web_hero"
MAPS = OUT / "maps"
MAPS.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(OUT / "talanta_web_baked.blend"))
s = bpy.context.scene

groups = {}
for o in bpy.data.objects:
    g = o.get("bake_group", "")
    if o.type == "MESH" and g.startswith("ground_"): groups.setdefault(g, []).append(o)
print("ground groups:", len(groups), sorted(groups)[:3], "...", flush=True)


def srgb(x):
    x = np.clip(x, 0, 1); return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)


c = s.cycles; c.device = "CPU"; c.use_adaptive_sampling = False; c.use_denoising = False; c.samples = 4
s.render.engine = "CYCLES"; s.render.bake.margin = 2; s.render.bake.margin_type = "EXTEND"; s.render.bake.target = "IMAGE_TEXTURES"
t_all = time.time()
for gname in sorted(groups):
    obs = groups[gname]; size = int(obs[0].get("bake_size", 1024))
    im = bpy.data.images.new(f"{gname}_albedo_rebake", size, size, alpha=False, float_buffer=True)
    for o in obs:
        for slot in o.material_slots:
            if slot.material is None: continue
            nd = slot.material.node_tree.nodes["bake_target"]; nd.image = im; slot.material.node_tree.nodes.active = nd
    bpy.ops.object.select_all(action="DESELECT")
    for o in obs: o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    t0 = time.time()
    bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"}, use_clear=True, margin=2)
    w, h = im.size; px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px); px = px.reshape(h, w, 4)[..., :3]
    out = bpy.data.images.new(f"{gname}_albedo_8bit", w, h, alpha=False)
    out.colorspace_settings.name = "Non-Color"  # values written are already encoded
    out.pixels.foreach_set(np.concatenate([srgb(px), np.ones((h, w, 1))], -1).astype(np.float32).ravel())
    out.filepath_raw = str(MAPS / f"{gname}_albedo.png"); out.file_format = "PNG"; out.save()
    print(f"{gname}: {time.time() - t0:.1f} s, mean albedo {np.round(px.reshape(-1, 3).mean(0), 3).tolist()}", flush=True)
print(f"done: {len(groups)} ground albedo maps in {time.time() - t_all:.0f} s")
