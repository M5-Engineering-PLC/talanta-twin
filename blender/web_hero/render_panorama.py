"""Web hero step 2: 360-degree equirectangular HDR environment for the three.js app.

Run from the repo root:
  ~/.venvs/bpy/bin/python blender/web_hero/render_panorama.py [samples] [width] [preset=morning_golden|evening_golden]
                                                             [near=<m>] [out=<dir>]
Camera 150 m above the pitch centre, CPU Cycles, the approved golden sun and sky (morning_golden 07:30 by default,
evening_golden 17:30). The stadium (plinth, shell, facade detail, tiers, bowl and roof detail, pitch, night fixtures)
is hidden, so the app can place the GLB inside the panorama. near=<m> also removes everything within <m> of the
stadium centre in plan (objects wholly inside are hidden; objects crossing the circle get a geometry-nodes cut of
their points and instances), so the panorama carries only the far context (hills, racecourse, city, CBD) and the GLBs
carry the rest. Writes Radiance HDR (linear, no exposure or tone mapping) at full width and 2048 px, plus a log.
Default output: app/public/env/talanta_0735.hdr (the original single morning panorama).
"""
import math, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, OUT, setup_morning, sun_vector_app, write_json

args = [a for a in sys.argv[1:] if a.isdigit()]
KW = dict(a.split("=", 1) for a in sys.argv[1:] if "=" in a)
SAMPLES = int(args[0]) if args else 128
W = int(args[1]) if len(args) > 1 else 4096
PRESET = KW.get("preset", "morning_golden")
NEAR = float(KW["near"]) if "near" in KW else None
g = setup_morning(preset=PRESET)
import bpy

s = bpy.context.scene
HIDE = ("plinth", "shell", "facade_detail", "tiers", "bowl_detail", "roof_detail", "pitch", "night_lights", "bowl_protos")
hidden = []
for c in bpy.data.collections:
    if c.name in HIDE:
        for o in c.all_objects:
            if o is not None and not o.hide_render: o.hide_render = True; hidden.append(o.name)


def near_cut(radius):
    """Hide objects within radius (plan) of the origin. Meshes that cross the circle get their own copy of the mesh
    with every vertex inside it deleted (bmesh; faces go with their vertices). That also cuts geometry-nodes point
    scatters (their instances sit on mesh points, attributes kept). A geometry-nodes cut evaluated right in the
    viewport but removed the whole mesh at render time, so the cut is made on the data. Curves are left whole."""
    import bmesh
    import numpy as np
    from mathutils import Vector
    n_hide = n_cut = 0
    for o in s.objects:
        if o.hide_render or o.type not in ("MESH", "CURVE", "EMPTY"): continue
        if o.type == "EMPTY":
            if o.instance_type == "COLLECTION" and Vector(o.matrix_world.translation[:2]).length < radius: o.hide_render = True; n_hide += 1
            continue
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        if max(Vector(v[:2]).length for v in bb) < radius:
            o.hide_render = True; n_hide += 1; continue
        if o.type != "MESH": continue
        xs, ys = [v.x for v in bb], [v.y for v in bb]
        if Vector((min(max(0.0, min(xs)), max(xs)), min(max(0.0, min(ys)), max(ys)))).length >= radius: continue
        o.data = o.data.copy()
        co = np.empty(len(o.data.vertices) * 3); o.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
        M = np.array(o.matrix_world); w = co @ M[:3, :3].T + M[:3, 3]
        inside = np.hypot(w[:, 0], w[:, 1]) < radius
        if not inside.any(): continue
        bm = bmesh.new(); bm.from_mesh(o.data); bm.verts.ensure_lookup_table()
        bmesh.ops.delete(bm, geom=[bm.verts[i] for i in np.nonzero(inside)[0]], context="VERTS")
        bm.to_mesh(o.data); bm.free(); o.data.update(); n_cut += 1
    return n_hide, n_cut


cut = near_cut(NEAR) if NEAR else None
cam_d = bpy.data.cameras.new("pano"); cam_d.type = "PANO"
cam_d.clip_start, cam_d.clip_end = 1.0, 100000.0  # a new camera clips at 1 km, which cut the far land out of the panorama
try: cam_d.panorama_type = "EQUIRECTANGULAR"
except AttributeError: cam_d.cycles.panorama_type = "EQUIRECTANGULAR"
cam = bpy.data.objects.new("pano", cam_d); s.collection.objects.link(cam)
import json
PAD = json.loads((ROOT / "app/public/data/manifest.json").read_text())["features"]["site_pad_y"]
cam.location = (0.0, 0.0, PAD + 150.0)
# Blender equirect: image centre looks along the camera's -Z; rotate so the centre looks north (+Y) and up is +Z.
cam.rotation_euler = (math.radians(90), 0.0, 0.0)
s.camera = cam
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = W, W // 2, 100
c = s.cycles; c.samples = SAMPLES; c.use_adaptive_sampling = True; c.use_denoising = True; c.denoiser = "OPENIMAGEDENOISE"
s.view_settings.view_transform = "Standard"; s.view_settings.exposure = 0.0; s.view_settings.look = "None"
s.render.image_settings.file_format = "HDR"
if "out" in KW:  # bundle: the full panorama as half-float OpenEXR (DWAB), far smaller than Radiance HDR at 8K
    s.render.image_settings.file_format = "OPEN_EXR"; s.render.image_settings.color_depth = "16"; s.render.image_settings.exr_codec = "DWAB"
hhmm = g["st"]["time_eat"].replace(":", "")
if "out" in KW:
    env = ROOT / KW["out"]; stem = f"talanta_pano_{hhmm}"
else:
    env = ROOT / "app/public/env"; stem = "talanta_0735"
env.mkdir(parents=True, exist_ok=True)
full = env / (f"{stem}.exr" if "out" in KW else f"{stem}.hdr")
t0 = time.time(); s.render.filepath = str(full); bpy.ops.render.render(write_still=True); sec = time.time() - t0
prev_dir = OUT / "pano_preview" if "out" in KW else env; prev_dir.mkdir(parents=True, exist_ok=True)
# preview for review only: the same render through AgX at the preset's exposure, 2048 px JPEG
rr = bpy.data.images["Render Result"]; s.view_settings.view_transform = "AgX"; s.view_settings.exposure = -1.0 if PRESET == "morning_golden" else -1.7  # approved pass 1 looks
s.render.image_settings.file_format = "JPEG"; s.render.image_settings.quality = 88
rr.save_render(str(prev_dir / f"{stem}_preview.jpg"), scene=s)
pv = bpy.data.images.load(str(prev_dir / f"{stem}_preview.jpg")); pv.scale(2048, 1024); pv.save()
# 2048 px version from the full render (box filter), so both files show the same light
im = bpy.data.images.load(str(full)); im.scale(2048, 1024)
im.filepath_raw = str(env / f"{stem}_2048.hdr"); im.file_format = "HDR"; im.save()
el, az = g["el"], g["az"]
write_json((env if "out" in KW else OUT) / f"panorama_log{'_' + hhmm if 'out' in KW else ''}.json", {
    "file": str(full.relative_to(ROOT)), "file_2048": str((env / f"{stem}_2048.hdr").relative_to(ROOT)),
    "preset": PRESET, "resolution": [W, W // 2], "samples": SAMPLES, "seconds": round(sec, 1),
    "near_cut_m": NEAR, "near_cut_objects": {"hidden": cut[0], "cut": cut[1]} if cut else None,
    "camera_app": [0.0, PAD + 150.0, 0.0], "centre_of_image_looks": "north (-z app)", "projection": "equirectangular",
    "sun_elevation_deg": round(el, 2), "sun_azimuth_deg": round(az, 2), "sun_dir_app": sun_vector_app(el, az),
    "colour": "linear Rec.709, no exposure, no tone mapping (render_cycles uses AgX at -1 EV for the morning look)",
    "hidden": sorted(set(hidden))})
print({"seconds": round(sec, 1), "near_cut": cut})
