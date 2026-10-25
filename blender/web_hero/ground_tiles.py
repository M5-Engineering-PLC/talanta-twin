"""Web hero ground tiles: orthographic top-down Cycles renders of the site ground under the 07:30 golden sun.

Run from the repo root:  ~/.venvs/bpy/bin/python blender/web_hero/ground_tiles.py <out_dir> [samples] [test]
The camera sees only ground surfaces (terrain with its paving, grass and murram materials, roads with their lane
markings, parking lines, pitch, apron and sport surfaces, the flat forecourt meshes). Everything else (trees and
other instanced sets, buildings, suburbs, traffic, the stadium) is invisible to the camera but still casts its
shadow, so the tiles carry the canopy and building shadows of 07:30. Light and look as the approved morning_golden
preset (AgX, -1 EV). Level 0: 0.25 m/px within 640 m of the stadium centre (5 x 5 tiles of 256 m); level 1:
0.5 m/px to 1536 m (6 x 6 tiles of 512 m). Each tile is 1024 x 1024 px. Writes <out_dir>/ground/L<level>_<i>_<j>.png
and <out_dir>/ground/tiles_png.json (x0, z0 = the tile's west and north edges in the app frame, size in m, level);
post_glb.mjs converts the tiles to KTX2 and writes tiles.json. Internal build step; no frame is used as a texture.
"""
import json, math, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, setup_morning, write_json

# script arguments only: under the blender binary they follow "--" (Blender's own, e.g. --python-exit-code 1, come first)
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
OUTD = ROOT / ARGV[0] / "ground"
args = [a for a in ARGV[1:] if a.isdigit()]
SAMPLES = int(args[0]) if args else 32
TEST = "test" in sys.argv
g = setup_morning()
import bpy
from mathutils import Vector

s = bpy.context.scene
PAD = g["PAD"] if "PAD" in g else json.loads((ROOT / "app/public/data/manifest.json").read_text())["features"]["site_pad_y"]
GROUND_COLS = {"pitch": {"pitch_zone", "pitch", "pitch_markings", "pitch_apron"}, "sport": None,
               "context": {"terrain_site", "road_markings", "ngong_road", "ngong_markings"}, "site": {"parking_lines"},
               "horizon_context": {"racecourse_infield", "racecourse_track"}}


# collections whose flat meshes (under 1 m tall) are ground: forecourt.py, and for web_hero_v2 the site layout, the plaza
# finish, passes I and K and the south-west grass loop, so the tiles carry their colour under the GLB meshes
FLAT_COLS = {"forecourt_context", "site_layout_ge", "finish_plaza", "layout_pass_i", "plaza_south_k", "trace_sw_finished"}


def is_ground(o):
    cols = {c.name for c in o.users_collection}
    name = o.name.removesuffix("_final")  # the finished-state cut copies of passes I and K (road_markings_final)
    for cn, names in GROUND_COLS.items():
        if cn in cols and (names is None or name in names): return True
    # (linked copies of flower and shrub prototypes are planting, not ground: they stay shadow-only)
    if cols & FLAT_COLS and o.type == "MESH" and o.data.users == 1 and not any(m.type == "NODES" for m in o.modifiers):
        bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
        return max(v.z for v in bb) - min(v.z for v in bb) < 1.0  # paths, kerbs, beds, plaza
    return False


ground, shadow_only = [], 0
for o in s.objects:
    if o.hide_render: continue
    if is_ground(o): ground.append(o.name); continue
    o.visible_camera = False; o.visible_glossy = False; o.visible_transmission = False; shadow_only += 1  # still casts shadows
if "haze_volume" in bpy.data.objects: bpy.data.objects["haze_volume"].hide_render = True

cam_d = bpy.data.cameras.new("ground_ortho"); cam_d.type = "ORTHO"; cam_d.clip_start = 1.0; cam_d.clip_end = 2000.0
cam = bpy.data.objects.new("ground_ortho", cam_d); s.collection.objects.link(cam); s.camera = cam
cam.rotation_euler = (0.0, 0.0, 0.0)  # looking straight down (-Z), image up = +Y = north
RES = 256 if TEST else 1024
s.render.resolution_x = s.render.resolution_y = RES; s.render.resolution_percentage = 100
c = s.cycles; c.samples = SAMPLES; c.use_adaptive_sampling = True; c.use_denoising = True; c.denoiser = "OPENIMAGEDENOISE"
# top-down ground colour: two diffuse bounces carry the sky and bounce light; deeper paths only cost time
c.max_bounces, c.diffuse_bounces, c.glossy_bounces, c.transmission_bounces, c.transparent_max_bounces = 4, 2, 1, 1, 4
c.caustics_reflective = c.caustics_refractive = False
s.render.film_transparent = False
s.render.image_settings.file_format = "PNG"; s.render.image_settings.color_mode = "RGB"
OUTD.mkdir(parents=True, exist_ok=True)

LEVELS = [(0, 0.25, 5), (1, 0.5, 6)]  # level, m per px, tiles per side (centred on the stadium)
if TEST: LEVELS = [(0, 0.25, 1), (1, 0.5, 1)]
KW = dict(x.split("=", 1) for x in ARGV[1:] if "=" in x)
if "levels" in KW: LEVELS = [L for L in LEVELS if str(L[0]) in KW["levels"].split(",")]  # v2: levels=0 re-renders level 0 only
tiles, t_all = [], time.time()
for level, mpp, n in LEVELS:
    size = mpp * 1024
    for i in range(n):        # west to east
        for j in range(n):    # north to south
            x0 = (i - n / 2) * size; z0 = (j - n / 2) * size       # app frame: x east, z south
            cx, cz = x0 + size / 2, z0 + size / 2
            cam.location = (cx, -cz, PAD + 600.0); cam_d.ortho_scale = size
            name = f"L{level}_{i}_{j}.png"; t0 = time.time()
            s.render.filepath = str(OUTD / name); bpy.ops.render.render(write_still=True)
            tiles.append({"file": name, "x0": x0, "z0": z0, "size": size, "level": level, "m_per_px": size / RES,
                          "seconds": round(time.time() - t0, 1)})
            print("tile", name, tiles[-1]["seconds"], "s", flush=True)
# reuse=<bundle ground dir>: tiles of the other levels come from an earlier bundle as KTX2 (post_glb.mjs copies them)
if "reuse" in KW:
    prev = json.loads((ROOT / KW["reuse"] / "tiles.json").read_text())
    done_levels = {L[0] for L in LEVELS}
    for t in prev["tiles"]:
        if t["level"] in done_levels: continue
        tiles.append({**t, "ktx2": str((ROOT / KW["reuse"] / t["file"]).resolve()), "reused_from": KW["reuse"]})
write_json(OUTD / "tiles_png.json", {"frame": "app (x east, z south); x0, z0 = west and north edges of the tile in m",
                                     "sun": "morning_golden 07:30 EAT 2026-01-15", "look": "AgX, -1 EV (approved morning)",
                                     "samples": SAMPLES, "resolution_px": RES, "ground_objects": sorted(ground),
                                     "shadow_only_objects": shadow_only, "tiles": tiles, "seconds": round(time.time() - t_all, 1)})
print("ground tiles:", len(tiles), round(time.time() - t_all, 1), "s")
