"""Stage 00 check: every critic camera loads in Blender and frames its target at the centre.
Run from the repo root: ~/.venvs/bpy/bin/python blender/scripts/check_cameras.py"""
import sys, math; sys.path.insert(0, 'blender/scripts')
import bpy
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
from cameras import load_cameras, to_blender, apply_render_settings
bpy.ops.wm.read_factory_settings(use_empty=True)
s = bpy.context.scene
m, cams = load_cameras(s, 'app/cameras/manifest.json'); apply_render_settings(s, m)
bad = 0
for c in m['cameras']:
    ob = cams[c['id']]; bpy.context.view_layer.update()
    v = world_to_camera_view(s, ob, to_blender(c['target']))
    ok = abs(v.x - 0.5) < 1e-4 and abs(v.y - 0.5) < 1e-4 and v.z > 0
    vf = math.degrees(ob.data.angle_y) if ob.data.type == 'PERSP' else None
    bad += not ok
    print(c['id'], ob.data.type, 'target at centre' if ok else f'FAIL {tuple(v)}', f'vfov {vf:.2f}' if vf else '')
for k in ("C06","C10","C12"):
    f = cams[k].data.view_frame(scene=s); print(k, "rendered vfov", round(math.degrees(2*math.atan(abs(f[0].y)/abs(f[0].z))),2))
sys.exit(bad)
