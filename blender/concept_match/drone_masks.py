"""Replica plan pass C (2026-10-21): stadium masks from the solved drone cameras and a terrain height grid.

Renders a flat white mask of the bowl (shell, facade detail, plinth, shields) from D01, D02 and D03 with Workbench at
the frame size (1280 x 720), for the silhouette IoU check (silhouette_iou.py) and to keep the stadium out of the ground
trace (asbuilt_trace.py). Also samples the terrain under a 2 m grid (app frame: x east, z south) for the trace.
Run from the repo root:
  ~/.venvs/bpy/bin/python blender/concept_match/drone_masks.py <out dir> [blend]
Writes <out>/D0N_stadium_mask.png and <out>/terrain_grid.npz (x0, z0, step, h[iz, ix], app y up).
"""
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "blender/scripts"))
from cameras import load_cameras

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
OUT = ROOT / args[0]; BLEND = args[1] if len(args) > 1 else "blender/out/talanta_site.blend"
OUT.mkdir(parents=True, exist_ok=True)
KEEP = {"shell", "facade_detail", "plinth", "shields"}

bpy.ops.wm.open_mainfile(filepath=str(ROOT / BLEND))
s = bpy.context.scene

# terrain grid first (needs the terrain visible)
terr = bpy.data.objects["terrain_site"]; dg = bpy.context.evaluated_depsgraph_get()
tm = terr.evaluated_get(dg).to_mesh()
bvh = BVHTree.FromPolygons([terr.matrix_world @ v.co for v in tm.vertices], [p.vertices[:] for p in tm.polygons])
terr.evaluated_get(dg).to_mesh_clear()
STEP, EXT = 2.0, 900.0
xs = np.arange(-EXT, EXT + STEP, STEP); zs = np.arange(-EXT, EXT + STEP, STEP)
h = np.full((len(zs), len(xs)), np.nan, np.float32)
for iz, z in enumerate(zs):
    for ix, x in enumerate(xs):
        hit = bvh.ray_cast(Vector((x, -z, 3000.0)), Vector((0, 0, -1)))
        if hit[0] is not None: h[iz, ix] = hit[0].z
np.savez_compressed(OUT / "terrain_grid.npz", x0=xs[0], z0=zs[0], step=STEP, h=h)
print("TERRAIN", np.nanmin(h), np.nanmax(h), np.isnan(h).mean(), flush=True)

_, cams = load_cameras(s, ROOT / "app/cameras/manifest.json")
for o in s.objects:  # every type: the context also holds collection instances
    if o.type != "CAMERA": o.hide_render = not ({c.name for c in o.users_collection} & KEEP)
s.render.engine = "BLENDER_WORKBENCH"
sh = s.display.shading; sh.light = "FLAT"; sh.color_type = "SINGLE"; sh.single_color = (1, 1, 1)
sh.show_cavity = False; sh.show_shadows = False; sh.show_object_outline = False
s.view_settings.view_transform = "Standard"; s.view_settings.exposure = 0; s.view_settings.look = "None"
w = bpy.data.worlds.new("black"); s.world = w; w.color = (0, 0, 0)
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 1280, 720, 100
s.render.film_transparent = False; s.render.image_settings.file_format = "PNG"
for cid in ("D01", "D02", "D03"):
    s.camera = cams[cid]; s.render.filepath = str(OUT / f"{cid}_stadium_mask.png")
    bpy.ops.render.render(write_still=True); print("MASK", cid, flush=True)
