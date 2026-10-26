"""Write the camera waypoints of walkthrough chapters 3 and 4 into blender/landing_reel/chapters.json.

Run from the repo root:
  blender -b blender/out/frozen_FK_interior.blend --factory-startup --python-exit-code 1 \
      --python blender/landing_reel/make_interior_paths.py
Chapter 3 "Going in": waypoints in the local frame of the chapter 3 entry (blender/out/interior_build_log.json): along
the outer concourse, a turn into the entry passage, through it, across the inner concourse to the aisle head, then a
last look across the bowl to the north stand (the aim keeps the tunnel placeholder on the west side out of the frame).
Chapter 4 "A lap of the bowl": one closed loop at the middle of the lower tier (tier fraction 0.19), 3 m above the
stand surface (ray cast on the seats and treads, smoothed over about 7 m), looking ahead and 50 deg inwards, 10 deg
down. Waypoints are in the app frame (x east, y = Blender height, z south), as paths.py reads them.
"""
import json, math
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
SPEC_F = ROOT / "blender/landing_reel/chapters.json"
E = json.loads((ROOT / "blender/out/interior_build_log.json").read_text())["entry"]
G = json.loads((ROOT / "blender/out/bowl_rings.json").read_text()); N = G["N"]
PAD, yF = E["pad"], E["floor_y_pad"]
(px, pz), (nx, nz) = E["wall_point_app_xz"], E["normal_out"]
tx, tz = -nz, nx
EYE = PAD + yF + 1.6
DW = E["r_wall"] - E["r_front"]  # inner concourse depth at the entry
r2 = lambda v: [round(float(c), 2) for c in v]
app = lambda n, t, h: r2([px + nx * n + tx * t, h, pz + nz * n + tz * t])

# chapter 3: (camera n, t, height), (aim n, t, height) in the entry frame (n outwards from the back wall, t along it)
# the outer concourse leg runs at n 9.0, between the column line (n about 7.0) and the outer wall (n 11.6), then turns
# wide into the passage axis (preview 2026-10-26: at n 6.6 the camera met a column and the side of the entry block)
ch3 = [((9.0, 17.0, EYE), (8.6, 5.0, EYE - 0.2)),
       ((9.0, 6.0, EYE), (4.0, 0.0, EYE - 0.3)),
       ((7.6, 0.0, EYE), (-6.0, 0.0, EYE - 0.4)),  # n set by ray cast below
       ((2.7, 0.0, EYE), (-14.0, 0.0, EYE - 0.8)),
       ((-2.0, 0.0, EYE), (-22.0, 0.0, EYE - 2.5)),
       ((-DW + 2.5, 0.0, EYE), None),
       ((-DW + 0.7, 0.0, EYE), None)]
far = r2([0.0, PAD + 12.0, -60.0])  # the north stand, across the pitch
s = bpy.context.scene; dg = bpy.context.evaluated_depsgraph_get()


def outer_n(t, frac=0.81, h=EYE):
    """n of the point at fraction frac across the outer concourse at tangent offset t: the back wall and the outer wall
    are found by ray casts along the wall normal, because the ring curves away from the straight tangent line. 0.81
    puts the camera between the column line (0.62 of the depth) and the outer wall."""
    o = Vector((px + nx * 5.6 + tx * t, -(pz + nz * 5.6 + tz * t), h))
    d_out, d_in = Vector((nx, -nz, 0)), Vector((-nx, nz, 0))
    hit_o, lo, *_ = s.ray_cast(dg, o, d_out, distance=30); hit_i, li, *_ = s.ray_cast(dg, o, d_in, distance=30)
    n_o = 5.6 + ((lo - o).length if hit_o else 5.6); n_i = 5.6 - ((li - o).length if hit_i else 5.4)
    return n_i + (n_o - n_i) * frac


ch3[0] = ((outer_n(17.0), 17.0, EYE), (outer_n(5.0), 5.0, EYE - 0.2))
ch3[1] = ((outer_n(6.0), 6.0, EYE), (5.4, 0.0, EYE - 0.2))  # aim at the passage mouth
ch3[2] = ((outer_n(0.0, 0.78), 0.0, EYE), ch3[2][1])  # on the passage axis, about 3.5 m before the mouth
pos3 = [app(*c) for c, _ in ch3]
aim3 = [app(*a) if a else far for _, a in ch3]

# chapter 4: the lap
TH = 2 * math.pi * np.arange(N + 1) / N
rof = lambda arr, th: float(np.interp(th % (2 * math.pi), TH, np.append(arr, arr[0])))
T_LAP, H_LAP, LOOK, DOWN, K = 0.19, 3.0, 50.0, 10.0, 960
th0 = math.atan2(pz, px)
ths = th0 + 2 * math.pi * np.arange(K) / K
xz = [(math.cos(t) * (rof(G["rIn"], t) + (rof(G["rBack"], t) - rof(G["rIn"], t)) * T_LAP),
       math.sin(t) * (rof(G["rIn"], t) + (rof(G["rBack"], t) - rof(G["rIn"], t)) * T_LAP)) for t in ths]
hs = []
for x, z in xz:
    hit, loc, *_ = s.ray_cast(dg, Vector((x, -z, PAD + 30.0)), Vector((0, 0, -1)))
    hs.append(loc.z if hit else PAD)
hs = np.array(hs); w = 15
hs_s = np.array([hs[(np.arange(i - w, i + w + 1)) % K].mean() for i in range(K)]) + H_LAP
pos4, aim4 = [], []
for i in range(0, K, 15):
    x, z = xz[i]; h = hs_s[i]; a = ths[i] + math.pi / 2 + math.radians(LOOK)
    pos4.append(r2([x, h, z]))
    aim4.append(r2([x + 20 * math.cos(a), h - 20 * math.tan(math.radians(DOWN)), z + 20 * math.sin(a)]))

spec = json.loads(SPEC_F.read_text())
spec["chapters"] = [c for c in spec["chapters"] if c["id"] not in ("ch3_going_in", "ch4_bowl_lap")]
spec["chapters"] += [
    {"id": "ch3_going_in", "seconds": 10, "light": "daylight_artistic (2026-01-15 10:30)", "lens_camera": "L07",
     "move": "from the enclosed outer concourse (slat ceiling, LED lines, white columns, closed kiosk shutters) along "
             "the concourse, a turn into the entry passage in the back wall, through it and across the open inner "
             "concourse to the head of lower-tier aisle 4 of 27 (south-east, 62.9 deg from east towards south); the "
             "last look goes across the pitch to the north stand; eye height 1.6 m; ease in and out; the last 12 "
             "frames hold for the cut to chapter 4",
     "ease": "in_out", "hold_frames": 12, "pos": pos3, "aim": aim3},
    {"id": "ch4_bowl_lap", "seconds": 10, "light": "daylight_artistic (2026-01-15 10:30)", "lens_camera": "L07",
     "move": "one closed lap at the middle of the lower tier (tier fraction 0.19), 3 m above the seats (ray cast, "
             "smoothed over about 7 m), looking ahead and 50 deg inwards and 10 deg down; it starts at the chapter 3 "
             "entry angle and the last frame joins the first, so the lap can loop",
     "closed": True, "pos": pos4, "aim": aim4},
]
spec["interior_rules"] = ["Chapters 3 and 4 (engineering/interior_plan_2026-10-26.md): no exit, exit sign, sign with text, "
                          "control or security room, camera position, player tunnel interior or back-of-house space is "
                          "modelled; the concourse is generic where no frame shows it. Portrait cuts: the same paths "
                          "and vertical field of view at 720 x 1280, lens not shifted (shift_x 0)."]
SPEC_F.write_text(json.dumps(spec, indent=1) + "\n")
print("paths ch3", len(pos3), "waypoints; ch4", len(pos4), "waypoints; lap height range",
      round(float(hs_s.min() - PAD), 2), "to", round(float(hs_s.max() - PAD), 2), "m above the pad")
