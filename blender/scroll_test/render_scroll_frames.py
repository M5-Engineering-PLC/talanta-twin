"""Scroll-scrub test (option 1, 2026-10-25): a short Cycles frame sequence in the approved hero_artistic look, for a
landing page that plays frames as the visitor scrolls. Test only: it measures time per frame, frame size and flicker.

Run from the repo root (TALANTA_SITE_BLEND=$PWD/blender/out/frozen_FK.blend):
  blender -b --factory-startup --python-exit-code 1 --python blender/scroll_test/render_scroll_frames.py -- \
      <out_dir> [frames=24] [arc_deg=30] [cam=L07] [preset=daylight_artistic] [scale=50]
      [only=0-4] [samples=128] [haze=1] [persistent=1] [res=720x1280] [chapter=ch1_arrival] [shift_x=0.151] [pick=0,48,96]
Reel cost levers (R3 step 2, 2026-10-25): only renders a range of the frames-long orbit (same camera positions);
samples overrides the sample count; haze=0 leaves out the volumetric haze box and its pass layer (passes_no_haze),
so the look layer's compositor aerial haze (mist pass of the main layer) is the only haze; persistent=0 turns off
persistent data; res sets the pixel size (portrait: the vertical field of view of the 16:9 frame is kept).
Walkthrough chapters (2026-10-25): chapter=<id> takes the camera poses from blender/landing_reel/chapters.json
(blender/landing_reel/paths.py) instead of the orbit, frames is then the chapter's frame count; shift_x shifts the lens
(the portrait cut's 9:16 window of the L07 frame). Chapters 3 and 4 (interior, waypoint splines) take the lens of
lens_camera and need TALANTA_SITE_BLEND=blender/out/frozen_FK_interior.blend and haze=0 (the haze box spans the bowl).
The scene setup is render_cycles.py up to its render call (camera, sky preset, hero_artistic prepare, look layer and
finish), so each frame matches the hero_artistic_04 still of that camera. The camera then orbits the camera target
about the vertical by arc_deg over the frames (same height, distance and pitch), frame 0 being the camera itself.
scale is the percent of 3840 x 2160. People, cars and lights are Visualization, as in the stills.
"""
import json, math, os, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
out = ROOT / ARGV[0]
kw = dict(a.split("=", 1) for a in ARGV[1:])
N, ARC = int(kw.get("frames", 24)), float(kw.get("arc_deg", 30))
CAM, PRESET, SCALE = kw.get("cam", "L07"), kw.get("preset", "daylight_artistic"), int(kw.get("scale", 50))
CHAPTER = None
if "chapter" in kw:
    sys.path.insert(0, str(ROOT / "blender/landing_reel")); import paths
    CHAPTER = paths.chapter(kw["chapter"]); N = paths.frames(CHAPTER)
    CAM = CHAPTER.get("from") or CHAPTER.get("to") or CHAPTER.get("lens_camera")  # chapters 3, 4: the lens of that camera
ONLY = [int(x) for x in kw.get("only", f"0-{N - 1}").split("-")]
HAZE, PERSIST = kw.get("haze", "1") == "1", kw.get("persistent", "1") == "1"
out.mkdir(parents=True, exist_ok=True)

src = (ROOT / "blender/render_cycles.py").read_text()
head = src.split("t0 = time.time(); bpy.ops.render.render(write_still=True)")[0]
sys.argv = [sys.argv[0], str(out.relative_to(ROOT)), CAM, PRESET, "hero_artistic"]
g = {"__file__": str(ROOT / "blender/render_cycles.py"), "__name__": "render_cycles_setup"}
t_setup = time.time()
exec(compile(head, "render_cycles.py (setup)", "exec"), g)
t_setup = time.time() - t_setup

import bpy
from mathutils import Matrix, Vector
s = bpy.context.scene
s.render.resolution_percentage = SCALE
s.render.image_settings.file_format = "PNG"
# only the camera moves: keep the synced scene and BVH between frames (the dry run spent about 2 min per frame on sync)
s.render.use_persistent_data = PERSIST
if "samples" in kw: s.cycles.samples = int(kw["samples"])
if not HAZE:
    hz = bpy.data.objects.get("haze_volume")
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
cam = s.camera
if "res" in kw:
    # keep the vertical field of view of the 16:9 frame (portrait cut: the same height of view, narrower)
    import math as _m
    w0, h0 = s.render.resolution_x, s.render.resolution_y
    vfov = 2 * _m.atan(_m.tan(cam.data.angle / 2) * h0 / w0) if cam.data.sensor_fit != "VERTICAL" else cam.data.angle
    s.render.resolution_x, s.render.resolution_y = map(int, kw["res"].split("x")); s.render.resolution_percentage = 100
    cam.data.sensor_fit = "VERTICAL"; cam.data.angle = vfov
if "shift_x" in kw: cam.data.shift_x = float(kw["shift_x"])
bpy.context.view_layer.update()
M0 = cam.matrix_world.copy()
if CHAPTER is not None and CHAPTER.get("from") == CAM:  # check: frame 0 of a chapter that starts on a camera is that camera
    (px, py, pz), (qx, qy, qz) = paths.pose(CHAPTER, 0); loc, aim = Vector((px, -pz, py)), Vector((qx, -qz, qy))
    M = Matrix.Translation(loc) @ (aim - loc).to_track_quat("-Z", "Y").to_matrix().to_4x4()
    print("chapter frame 0 vs camera", CAM, "max matrix difference", max(abs(M[r][c] - M0[r][c]) for r in range(4) for c in range(4)), flush=True)
m = json.loads((ROOT / "app/cameras/manifest.json").read_text())
tx, ty, tz = next(c for c in m["cameras"] if c["id"] == CAM)["target"]
pivot = Vector((tx, -tz, ty))  # app (x, y, z) -> Blender (x, -z, y)

pct = s.render.resolution_percentage
log = {"chapter": kw.get("chapter"), "camera": CAM, "preset": PRESET, "frames": N, "arc_deg": ARC, "resolution": [s.render.resolution_x * pct // 100,
       s.render.resolution_y * pct // 100], "samples": s.cycles.samples, "adaptive_threshold": s.cycles.adaptive_threshold,
       "denoiser": s.cycles.denoiser, "persistent_data": PERSIST, "haze_volume": HAZE, "only": ONLY,
       "view_layers": [v.name for v in s.view_layers], "seed": s.cycles.seed, "scene": os.environ.get("TALANTA_SITE_BLEND"),
       "setup_seconds": round(t_setup, 1), "frame_seconds": []}
# resume after a container restart: keep the frames already written and their times
prev = out / "scroll_log.json"
if prev.exists():
    log["frame_seconds"] = json.loads(prev.read_text()).get("frame_seconds", [])
done = ONLY[0]
while done <= ONLY[1] and (out / f"frame_{done:03d}.png").exists():
    done += 1
log["frame_seconds"] = log["frame_seconds"][:done - ONLY[0]]
log["resumed_at_frame"] = done if done > ONLY[0] else None
PICK = [int(x) for x in kw["pick"].split(",")] if "pick" in kw else None  # preview strips: these frames only
for i in (PICK if PICK else range(done, ONLY[1] + 1)):
    ang = math.radians(ARC * i / max(N - 1, 1))
    R = Matrix.Translation(pivot) @ Matrix.Rotation(ang, 4, "Z") @ Matrix.Translation(-pivot)
    cam.matrix_world = R @ M0
    if CHAPTER is not None:  # the chapter's pose, app frame (x, y, z) -> Blender (x, -z, y)
        (px, py, pz), (qx, qy, qz) = paths.pose(CHAPTER, i)
        loc, aim = Vector((px, -pz, py)), Vector((qx, -qz, qy))
        cam.matrix_world = Matrix.Translation(loc) @ (aim - loc).to_track_quat("-Z", "Y").to_matrix().to_4x4()
    s.render.filepath = str(out / f"frame_{i:03d}.png")
    t0 = time.time(); bpy.ops.render.render(write_still=True); dt = time.time() - t0
    log["frame_seconds"].append(round(dt, 1))
    print(f"scroll frame {i + 1}/{N} {dt:.1f} s", flush=True)
    (out / "scroll_log.json").write_text(json.dumps(log, indent=1) + "\n")
log["total_render_seconds"] = round(sum(log["frame_seconds"]), 1)
(out / "scroll_log.json").write_text(json.dumps(log, indent=1) + "\n")
print("scroll done", json.dumps(log))
