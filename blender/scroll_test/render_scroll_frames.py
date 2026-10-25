"""Scroll-scrub test (option 1, 2026-10-25): a short Cycles frame sequence in the approved hero_artistic look, for a
landing page that plays frames as the visitor scrolls. Test only: it measures time per frame, frame size and flicker.

Run from the repo root (TALANTA_SITE_BLEND=$PWD/blender/out/frozen_FK.blend):
  blender -b --factory-startup --python-exit-code 1 --python blender/scroll_test/render_scroll_frames.py -- \
      <out_dir> [frames=24] [arc_deg=30] [cam=L07] [preset=daylight_artistic] [scale=50]
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
s.render.use_persistent_data = True
cam = s.camera
bpy.context.view_layer.update()
M0 = cam.matrix_world.copy()
m = json.loads((ROOT / "app/cameras/manifest.json").read_text())
tx, ty, tz = next(c for c in m["cameras"] if c["id"] == CAM)["target"]
pivot = Vector((tx, -tz, ty))  # app (x, y, z) -> Blender (x, -z, y)

log = {"camera": CAM, "preset": PRESET, "frames": N, "arc_deg": ARC, "resolution": [s.render.resolution_x * SCALE // 100,
       s.render.resolution_y * SCALE // 100], "samples": s.cycles.samples, "adaptive_threshold": s.cycles.adaptive_threshold,
       "denoiser": s.cycles.denoiser, "persistent_data": True, "seed": s.cycles.seed, "scene": os.environ.get("TALANTA_SITE_BLEND"),
       "setup_seconds": round(t_setup, 1), "frame_seconds": []}
# resume after a container restart: keep the frames already written and their times
prev = out / "scroll_log.json"
if prev.exists():
    log["frame_seconds"] = json.loads(prev.read_text()).get("frame_seconds", [])
done = 0
while done < N and (out / f"frame_{done:03d}.png").exists():
    done += 1
log["frame_seconds"] = log["frame_seconds"][:done]
log["resumed_at_frame"] = done if done else None
for i in range(done, N):
    ang = math.radians(ARC * i / max(N - 1, 1))
    R = Matrix.Translation(pivot) @ Matrix.Rotation(ang, 4, "Z") @ Matrix.Translation(-pivot)
    cam.matrix_world = R @ M0
    s.render.filepath = str(out / f"frame_{i:03d}.png")
    t0 = time.time(); bpy.ops.render.render(write_still=True); dt = time.time() - t0
    log["frame_seconds"].append(round(dt, 1))
    print(f"scroll frame {i + 1}/{N} {dt:.1f} s", flush=True)
    (out / "scroll_log.json").write_text(json.dumps(log, indent=1) + "\n")
log["total_render_seconds"] = round(sum(log["frame_seconds"]), 1)
(out / "scroll_log.json").write_text(json.dumps(log, indent=1) + "\n")
print("scroll done", json.dumps(log))
