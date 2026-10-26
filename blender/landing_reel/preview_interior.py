"""16-sample previews of the interior (engineering/interior_plan_2026-10-26.md) from the planned chapter 3 and 4 camera
points, in the hero_artistic day look of L07 (10:30, daylight_artistic), haze volume off.

Run from the repo root (TALANTA_SITE_BLEND=$PWD/blender/out/frozen_FK_interior.blend):
  blender -b --factory-startup --python-exit-code 1 --python blender/landing_reel/preview_interior.py -- <out_dir> <part>
The poses come from blender/out/interior_build_log.json (the chapter 3 entry) until part 4 writes the chapter paths.
Each pose: Blender position, Blender aim point, exposure change in EV. Internal check images only. People, vehicles
and lighting are illustrative (Visualization).
"""
import json, math, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARGV = sys.argv[sys.argv.index("--") + 1:]
out, PART = ROOT / ARGV[0], ARGV[1]
out.mkdir(parents=True, exist_ok=True)
E = json.loads((ROOT / "blender/out/interior_build_log.json").read_text())["entry"]
PAD, yF = E["pad"], E["floor_y_pad"]
(px, pz), (nx, nz) = E["wall_point_app_xz"], E["normal_out"]
tx, tz = -nz, nx  # tangent (app x, z)
EYE = PAD + yF + 1.6
Bp = lambda x, z, h: (x, -z, h)  # app (x, z) and Blender height -> Blender
at_n = lambda n, t=0.0: (px + nx * n + tx * t, pz + nz * n + tz * t)
POSES = {
    "concourse": [
        ("p1_outer_along", Bp(*at_n(5.6 + 5.0, 18.0), EYE), Bp(*at_n(5.6 + 3.0, 0.0), EYE - 0.3), 0.0),
        ("p2_outer_to_entry", Bp(*at_n(5.6 + 4.8, 0.0), EYE), Bp(*at_n(-10.0), EYE - 0.6), 0.0),
        ("p3_inner_from_entry", Bp(*at_n(-1.0), EYE), Bp(*at_n(-30.0), EYE - 3.0), 0.0),
        ("p4_aisle_head", Bp(*at_n(-(E["r_wall"] - E["r_front"]) + 0.8), EYE), (0.0, 0.0, PAD + 2.0), 0.0),
        ("p5_bowl_to_concourse", Bp(*at_n(-(E["r_wall"] - E["r_front"]) - 11.0, -14.0), PAD + 8.5), Bp(*at_n(0.0), PAD + yF + 2.5), 0.0),
    ],
}[PART]

src = (ROOT / "blender/render_cycles.py").read_text()
head = src.split("t0 = time.time(); bpy.ops.render.render(write_still=True)")[0]
sys.argv = [sys.argv[0], str(out.relative_to(ROOT)), "L07", "daylight_artistic", "hero_artistic"]
g = {"__file__": str(ROOT / "blender/render_cycles.py"), "__name__": "render_cycles_setup"}
exec(compile(head, "render_cycles.py (setup)", "exec"), g)
import bpy
from mathutils import Matrix, Vector
s = bpy.context.scene
hz = bpy.data.objects.get("haze_volume")  # haze volume off (the interior sits inside its box); passes from the main layer
if hz is not None: hz.hide_render = True
pl = s.view_layers.get("passes_no_haze")
tree = s.compositing_node_group if hasattr(s, "compositing_node_group") else s.node_tree
if pl is not None:
    main_rl = next(n for n in tree.nodes if n.type == "R_LAYERS" and n.layer == s.view_layers[0].name)
    for n in [n for n in tree.nodes if n.type == "R_LAYERS" and n.layer == pl.name]:
        for o in n.outputs:
            for lk in list(o.links): tree.links.new(main_rl.outputs[o.name], lk.to_socket)
        tree.nodes.remove(n)
    s.view_layers.remove(pl)
s.cycles.samples = 16; s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 960, 540, 100
s.render.use_persistent_data = True; s.render.image_settings.file_format = "PNG"
cam = s.camera; ev0 = s.view_settings.exposure
log = {"part": PART, "scene": str(Path(bpy.data.filepath).name), "samples": 16, "resolution": [960, 540], "frames": []}
for name, pos, aim, dev in POSES:
    loc, tgt = Vector(pos), Vector(aim)
    cam.matrix_world = Matrix.Translation(loc) @ (tgt - loc).to_track_quat("-Z", "Y").to_matrix().to_4x4()
    s.view_settings.exposure = ev0 + dev
    s.render.filepath = str(out / f"{PART}_{name}.png")
    t0 = time.time(); bpy.ops.render.render(write_still=True); dt = round(time.time() - t0, 1)
    log["frames"].append({"name": name, "pos": [round(x, 2) for x in pos], "aim": [round(x, 2) for x in aim], "ev": dev, "seconds": dt})
    print("preview", name, dt, "s", flush=True)
(out / f"preview_log_{PART}.json").write_text(json.dumps(log, indent=1) + "\n")
