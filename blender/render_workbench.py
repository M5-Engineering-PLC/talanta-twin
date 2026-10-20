"""Stage 01: Workbench renders of the blockout from the frozen critic cameras.

Run from the repo root:
  ~/.venvs/bpy/bin/python blender/render_workbench.py <pass_dir> C01,C02,C03,C04,C05
"""
import json, sys, time
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender/scripts"))
from cameras import load_cameras, apply_render_settings

out = ROOT / (sys.argv[-2] if len(sys.argv) > 2 else "blender/renders/pass_01")
ids = (sys.argv[-1] if len(sys.argv) > 2 else "C01,C02,C03,C04,C05").split(",")
out.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT / "blender/out/talanta_blockout.blend"))
s = bpy.context.scene
m, cams = load_cameras(s, ROOT / "app/cameras/manifest.json")
apply_render_settings(s, m, look_check=True)
s.render.engine = "BLENDER_WORKBENCH"
sh = s.display.shading
sh.light = "STUDIO"; sh.color_type = "MATERIAL"
sh.show_cavity = True; sh.cavity_type = "BOTH"
sh.show_shadows = True; sh.show_object_outline = True
s.display.shadow_focus = 0.2
s.view_settings.view_transform = "Standard"
w = bpy.data.worlds.new("bg"); s.world = w; w.color = (0.78, 0.82, 0.86)
times = []
for cid in ids:
    s.camera = cams[cid]
    s.render.filepath = str(out / f"{cid}_workbench.png")
    t0 = time.time(); bpy.ops.render.render(write_still=True); dt = time.time() - t0
    times.append({"camera": cid, "engine": "workbench", "seconds": round(dt, 1)})
    print(cid, f"{dt:.1f} s")
(out / "times_workbench.json").write_text(json.dumps(times, indent=1) + "\n")
