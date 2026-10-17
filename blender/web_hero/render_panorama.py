"""Web hero step 2: 360-degree equirectangular HDR environment at 07:35 for the three.js app.

Run from the repo root:  ~/.venvs/bpy/bin/python blender/web_hero/render_panorama.py [samples] [width]
Camera 150 m above the pitch centre, CPU Cycles, same morning sun and sky as render_cycles.py C06 morning.
The stadium (plinth, shell, facade detail, tiers, bowl and roof detail, pitch, night fixtures) is hidden,
so the app can place the GLB inside the panorama. Writes app/public/env/talanta_0735.hdr (Radiance HDR,
linear, no exposure or tone mapping) and talanta_0735_2048.hdr, plus blender/out/web_hero/panorama_log.json.
"""
import math, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, OUT, setup_morning, sun_vector_app, write_json

args = [a for a in sys.argv[1:] if a.isdigit()]
SAMPLES = int(args[0]) if args else 128
W = int(args[1]) if len(args) > 1 else 4096
g = setup_morning()
import bpy

s = bpy.context.scene
HIDE = ("plinth", "shell", "facade_detail", "tiers", "bowl_detail", "roof_detail", "pitch", "night_lights", "bowl_protos")
hidden = []
for c in bpy.data.collections:
    if c.name in HIDE:
        for o in c.all_objects:
            if not o.hide_render: o.hide_render = True; hidden.append(o.name)
cam_d = bpy.data.cameras.new("pano"); cam_d.type = "PANO"
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
env = ROOT / "app/public/env"; env.mkdir(parents=True, exist_ok=True)
t0 = time.time(); s.render.filepath = str(env / "talanta_0735.hdr"); bpy.ops.render.render(write_still=True); sec = time.time() - t0
# 2048 px version from the full render (box filter), so both files show the same light
im = bpy.data.images.load(str(env / "talanta_0735.hdr")); im.scale(2048, 1024)
im.filepath_raw = str(env / "talanta_0735_2048.hdr"); im.file_format = "HDR"; im.save()
el, az = g["el"], g["az"]
write_json(OUT / "panorama_log.json", {
    "file": "app/public/env/talanta_0735.hdr", "file_2048": "app/public/env/talanta_0735_2048.hdr",
    "resolution": [W, W // 2], "samples": SAMPLES, "seconds": round(sec, 1),
    "camera_app": [0.0, PAD + 150.0, 0.0], "centre_of_image_looks": "north (-z app)", "projection": "equirectangular",
    "sun_elevation_deg": round(el, 2), "sun_azimuth_deg": round(az, 2), "sun_dir_app": sun_vector_app(el, az),
    "colour": "linear Rec.709, no exposure, no tone mapping (render_cycles uses AgX at -1 EV for the morning look)",
    "hidden": sorted(set(hidden))})
print({"seconds": round(sec, 1)})
