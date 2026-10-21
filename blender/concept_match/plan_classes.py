"""Replica plan pass C (2026-10-21): plan of the current layout in the as-built trace classes, for the change list.

Renders the scene from straight above (orthographic, Workbench, flat light, each material in its base colour) over the
trace extent at 1 m per pixel, then classifies the pixels with asbuilt_trace.classify (the same rules as the frames).
Run from the repo root:
  ~/.venvs/bpy/bin/python blender/concept_match/plan_classes.py <out png> [blend] [state]
Writes <out> (8-bit class labels, row 0 = north edge) and <out>_colour.png (the flat plan render).
"""
import os, sys
from pathlib import Path
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "blender/concept_match")); sys.path.insert(0, str(ROOT / "blender"))
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
OUT = Path(args[0]); BLEND = args[1] if len(args) > 1 else "blender/out/talanta_site.blend"
bpy.ops.wm.open_mainfile(filepath=str(ROOT / BLEND))
s = bpy.context.scene
if len(args) > 2:
    import scene_state; scene_state.set_state(s, args[2])
import asbuilt_trace as T

for m in bpy.data.materials:  # Workbench MATERIAL colour = the base colour the renders start from
    if m.node_tree and "Principled BSDF" in m.node_tree.nodes:
        bc = m.node_tree.nodes["Principled BSDF"].inputs["Base Color"]
        if not bc.is_linked: m.diffuse_color = tuple(bc.default_value)
        else:
            src = bc.links[0].from_node
            if src.type == "MIX" and not src.inputs[6].is_linked: m.diffuse_color = tuple(src.inputs[6].default_value)
            elif src.type == "VALTORGB": m.diffuse_color = tuple(src.color_ramp.elements[0].color)
for m in bpy.data.materials:  # the terrain colour comes from linked nodes; it renders as grass
    if m.name.startswith("terrain_site") or m.name == "ground": m.diffuse_color = (0.10, 0.25, 0.06, 1)
for o in s.objects:
    if o.type == "LIGHT" or any(c.name in ("atmosphere", "night_lights") for c in o.users_collection): o.hide_render = True
cam = bpy.data.objects.new("plan_cam", bpy.data.cameras.new("plan_cam")); s.collection.objects.link(cam)
cam.data.type = "ORTHO"; cam.data.ortho_scale = 2 * T.EXT; cam.data.clip_start, cam.data.clip_end = 1, 5000
cam.location = (0, 0, 1500); cam.rotation_euler = (0, 0, 0)  # looking down, image up = Blender +y = north
s.camera = cam
s.render.engine = "BLENDER_WORKBENCH"
sh = s.display.shading; sh.light = "FLAT"; sh.color_type = "MATERIAL"
sh.show_cavity = False; sh.show_shadows = False; sh.show_object_outline = False
s.view_settings.view_transform = "Standard"; s.view_settings.look = "None"; s.view_settings.exposure = 0
w = bpy.data.worlds.new("black"); s.world = w; w.color = (0, 0, 0)
n = int(2 * T.EXT / T.CELL)
s.render.resolution_x = s.render.resolution_y = n; s.render.resolution_percentage = 100
s.render.image_settings.file_format = "PNG"; s.render.filepath = str(OUT)[:-4] + "_colour.png"
bpy.ops.render.render(write_still=True)
from PIL import Image
rgb = np.asarray(Image.open(s.render.filepath).convert("RGB"))
lab = T.classify(rgb); lab[rgb.max(-1) < 8] = 0
Image.fromarray(lab).save(OUT); print("PLAN", OUT, np.bincount(lab.ravel(), minlength=len(T.CLASSES)).tolist(), flush=True)
