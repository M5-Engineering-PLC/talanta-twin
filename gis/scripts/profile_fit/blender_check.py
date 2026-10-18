"""Blender silhouette check of the rebuilt blockout from solved frame cameras (pinhole; the fit's k1 is ignored, so
use frames where the stadium sits near the image centre). Renders shell + facade detail as a flat white mask with
Workbench at 1280 x 720 and writes <out>/sil_<frame>.png plus the mask IoU against the seg2.py mask.
Run: ~/.venvs/bpy/bin/python gis/scripts/profile_fit/blender_check.py <state.json> <mask dir> <out dir> <frame> [<frame> ...]
"""
import json, math, sys
from pathlib import Path
import bpy, numpy as np
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[3]
state, maskdir, out = json.load(open(sys.argv[1])), Path(sys.argv[2]), Path(sys.argv[3]); frames = sys.argv[4:]
PAD = json.loads((ROOT / "app/public/data/manifest.json").read_text())["features"]["site_pad_y"]
bpy.ops.wm.open_mainfile(filepath=str(ROOT / "blender/out/talanta_blockout.blend"))
s = bpy.context.scene
keep = {"shell", "facade_detail"}
for o in s.objects:
    o.hide_render = not any(c.name in keep for c in o.users_collection)
s.render.engine = "BLENDER_WORKBENCH"; s.display.shading.light = "FLAT"; s.display.shading.color_type = "SINGLE"
s.display.shading.single_color = (1, 1, 1)
if s.world is None: s.world = bpy.data.worlds.new("black")
s.world.color = (0, 0, 0); s.display.shading.background_type = "WORLD"
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 1280, 720, 100
s.view_settings.view_transform = "Standard"; s.render.film_transparent = False
cam = bpy.data.objects.new("fitcam", bpy.data.cameras.new("fitcam")); s.collection.objects.link(cam); s.camera = cam
B = lambda v: Vector((v[0], -v[2], v[1]))
res = {}
for f in frames:
    tx, ty, tz, az, el, d, fpx, roll = state["final"]["cams"][f][:8]
    az, el, roll = map(math.radians, (az, el, roll))
    fwd = -np.array([math.cos(el) * math.cos(az), math.sin(el), math.cos(el) * math.sin(az)])
    C = np.array([tx, ty, tz]) - fwd * d
    right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right); up = np.cross(right, fwd)
    cr, sr = math.cos(roll), math.sin(roll); right, up = cr * right + sr * up, -sr * right + cr * up
    X, Y, Z = B(right), B(up), B(-fwd)
    M = Matrix(((X.x, Y.x, Z.x, 0), (X.y, Y.y, Z.y, 0), (X.z, Y.z, Z.z, 0), (0, 0, 0, 1)))
    M.translation = B((C[0], C[1] + PAD, C[2])); cam.matrix_world = M
    cam.data.sensor_fit = "HORIZONTAL"; cam.data.sensor_width = 36.0; cam.data.lens = fpx * 36.0 / 1280; cam.data.clip_end = 1e5
    s.render.filepath = str(out / f"sil_{f}.png"); bpy.ops.render.render(write_still=True)
    im = bpy.data.images.load(s.render.filepath); px = np.empty(1280 * 720 * 4, np.float32); im.pixels.foreach_get(px)
    sil = px.reshape(720, 1280, 4)[::-1, :, 0] > 0.5
    mk = np.load(maskdir / f"mask_{f}.npy")
    res[f] = round(float((sil & mk).sum() / max(1, (sil | mk).sum())), 3)
    np.save(out / f"sil_{f}.npy", sil)
print("BLENDER_SIL_IOU " + json.dumps(res))
