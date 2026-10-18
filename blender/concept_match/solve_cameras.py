"""Pass 1 framing: refine the C19 and C20 poses so the stadium sits in the frame as in lead renders 06 and 07.

Measured on the concept images (1600 x 900, by hand, engineering/plan_concept_match_2026-10-17.md):
the stadium bounding box (x0, y0, x1, y1 as fractions of the frame, y from the top) and the sky band (the
fraction of the frame height above the land horizon). Starting poses and focal lengths are Sol's. The bearing
and focal length stay fixed; the solver moves the camera distance and height, the aim height and a small yaw.
The stadium box is the projection of the plinth, shell and facade_detail meshes. The horizon is a profile of
land elevation angle against azimuth, ray cast once from the start position (haze box hidden); the sky band of
each trial pose follows from it in closed form, and the final pose is checked with direct ray casts. Writes the poses to app/cameras/manifest.json (C19 and C20 only)
and the residuals to blender/data/concept_cameras.json.
Run: ~/.venvs/bpy/bin/python blender/concept_match/solve_cameras.py [dry]
"""
import json, math, sys
from pathlib import Path
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "app/cameras/manifest.json"
W, H, SENSOR = 960, 540, 36.0
TARGETS = {  # concept frame measurements and Sol's starting poses (app frame: x east, y up, z south)
    "C19": {"concept": "research/concepts/2026-10-17/06_lead_ne_to_ngong_hills.jpg",
            "bbox": [550 / 1600, 300 / 900, 1135 / 1600, 535 / 900], "sky": 0.15,
            "position": [485, 165, -445], "target": [10, 30, 11], "focal": 35},
    "C20": {"concept": "research/concepts/2026-10-17/07_lead_ssw_to_lavington.jpg",
            "bbox": [447 / 1600, 312 / 900, 1063 / 1600, 582 / 900], "sky": 0.16,
            "position": [-180, 165, 650], "target": [20, 30, 5], "focal": 38},
}
STADIUM_COLS = ("plinth", "shell", "facade_detail")


def app_to_bl(p): return np.array([p[0], -p[2], p[1]], float)
def bl_to_app(p): return [round(float(p[0]), 2), round(float(p[2]), 2), round(float(-p[1]), 2)]


bpy.ops.wm.open_mainfile(filepath=str(ROOT / "blender/out/talanta_site.blend"))
scene = bpy.context.scene
for name in ("haze_volume",):
    if name in bpy.data.objects: bpy.data.objects[name].hide_viewport = True; bpy.data.objects[name].hide_render = True
dg = bpy.context.evaluated_depsgraph_get()
pts = []
for cn in STADIUM_COLS:
    for o in bpy.data.collections[cn].all_objects:
        if o.type not in ("MESH", "CURVE"): continue
        me = o.evaluated_get(dg).to_mesh()
        co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co)
        M = np.array(o.matrix_world); pts.append(co.reshape(-1, 3) @ M[:3, :3].T + M[:3, 3])
        o.evaluated_get(dg).to_mesh_clear()
PTS = np.concatenate(pts)
print("stadium points", len(PTS))


def basis(P, T):
    f = T - P; f /= np.linalg.norm(f)
    r = np.cross(f, [0, 0, 1.0]); r /= np.linalg.norm(r); u = np.cross(r, f)
    return f, r, u


def bbox(P, T, lens):
    f, r, u = basis(P, T); d = PTS - P; z = d @ f
    k = lens / (SENSOR / 2)
    x = 0.5 + 0.5 * (d @ r) / z * k
    y = 0.5 - 0.5 * (d @ u) / z * k * W / H
    return np.array([x.min(), y.min(), x.max(), y.max()])


def ray(P, f, r, u, lens, sx, sy):
    t = (SENSOR / 2) / lens
    v = f + r * (2 * sx - 1) * t + u * (1 - 2 * sy) * t * H / W
    from mathutils import Vector
    hit = scene.ray_cast(dg, Vector(P), Vector(v / np.linalg.norm(v)), distance=1e6)
    return hit[0]


def sky_band(P, T, lens, cols=24):
    """Mean fraction of the frame height above the first land hit, over evenly spaced columns."""
    f, r, u = basis(P, T); out = []
    for i in range(cols):
        sx = (i + 0.5) / cols; lo, hi = 0.0, 1.0   # lo: sky, hi: land
        if ray(P, f, r, u, lens, sx, 0.0): out.append(0.0); continue
        if not ray(P, f, r, u, lens, sx, 1.0): out.append(1.0); continue
        for _ in range(11):
            m = 0.5 * (lo + hi)
            if ray(P, f, r, u, lens, sx, m): hi = m
            else: lo = m
        out.append(hi)
    return float(np.mean(out))


def horizon_profile(P, centre_deg, half=50, step=0.5):
    """Land horizon elevation (deg) for azimuths (deg, ccw from east) around centre_deg, seen from P."""
    from mathutils import Vector
    az = np.arange(centre_deg - half, centre_deg + half + step, step); el = []
    for a in az:
        lo, hi = -30.0, 15.0   # lo: land, hi: sky
        for _ in range(12):
            m = 0.5 * (lo + hi); ar, er = math.radians(a), math.radians(m)
            v = Vector((math.cos(er) * math.cos(ar), math.cos(er) * math.sin(ar), math.sin(er)))
            if scene.ray_cast(dg, Vector(P), v, distance=1e6)[0]: lo = m
            else: hi = m
        el.append(hi)
    return az, np.array(el)


def sky_fast(P, T, lens, prof, cols=96):
    az, el = prof; f, r, u = basis(P, T); t = (SENSOR / 2) / lens
    sx = (np.arange(cols) + 0.5) / cols; sy = np.linspace(0, 1, H + 1)
    v = (f[None, None] + r[None, None] * ((2 * sx - 1) * t)[None, :, None]
         + u[None, None] * ((1 - 2 * sy) * t * H / W)[:, None, None])
    v /= np.linalg.norm(v, axis=-1, keepdims=True)
    ve = np.degrees(np.arcsin(v[..., 2])); va = np.degrees(np.arctan2(v[..., 1], v[..., 0]))
    va = az[0] + (va - az[0]) % 360
    land = ve < np.interp(va, az, el)
    first = np.where(land.any(0), land.argmax(0), H) / H
    return float(first.mean())


def pose(q, base):
    """q = (log distance scale, height offset m, aim height offset m, yaw deg) -> camera P, target T."""
    P0, T0 = app_to_bl(base["position"]), app_to_bl(base["target"])
    hor = P0[:2] - T0[:2]
    P = np.array([*(T0[:2] + hor * math.exp(q[0])), P0[2] + q[1]])
    T = T0.copy(); T[2] += q[2]
    a = math.radians(q[3]); c, s = math.cos(a), math.sin(a)
    dv = T[:2] - P[:2]; T[:2] = P[:2] + np.array([c * dv[0] - s * dv[1], s * dv[0] + c * dv[1]])
    return P, T


def evaluate(P, T, lens, prof=None):
    b = bbox(P, T, lens)
    return {"bbox": b, "width": b[2] - b[0], "cx": (b[0] + b[2]) / 2, "cy": (b[1] + b[3]) / 2,
            "height": b[3] - b[1], "sky": sky_fast(P, T, lens, prof) if prof else sky_band(P, T, lens)}


def cost(q, base, prof):
    tb = np.array(base["bbox"]); P, T = pose(q, base); e = evaluate(P, T, base["focal"], prof)
    return (((e["width"] - (tb[2] - tb[0])) / 0.01) ** 2 + ((e["cx"] - (tb[0] + tb[2]) / 2) / 0.01) ** 2
            + ((e["cy"] - (tb[1] + tb[3]) / 2) / 0.01) ** 2 + ((e["sky"] - base["sky"]) / 0.01) ** 2
            + 0.25 * ((e["height"] - (tb[3] - tb[1])) / 0.01) ** 2), e


def nelder_mead(fn, x0, step, iters=90):
    pts = [np.array(x0, float)] + [np.array(x0, float) + np.eye(len(x0))[i] * step[i] for i in range(len(x0))]
    val = [fn(p)[0] for p in pts]
    for _ in range(iters):
        o = np.argsort(val); pts = [pts[i] for i in o]; val = [val[i] for i in o]
        c = np.mean(pts[:-1], 0); xr = c + (c - pts[-1]); fr = fn(xr)[0]
        if fr < val[0]:
            xe = c + 2 * (c - pts[-1]); fe = fn(xe)[0]
            pts[-1], val[-1] = (xe, fe) if fe < fr else (xr, fr)
        elif fr < val[-2]: pts[-1], val[-1] = xr, fr
        else:
            xc = c + 0.5 * (pts[-1] - c); fc = fn(xc)[0]
            if fc < val[-1]: pts[-1], val[-1] = xc, fc
            else:
                pts = [pts[0]] + [pts[0] + 0.5 * (p - pts[0]) for p in pts[1:]]; val = [val[0]] + [fn(p)[0] for p in pts[1:]]
    i = int(np.argmin(val)); return pts[i], val[i]


report = {}
for cid, base in TARGETS.items():
    P0, T0 = pose([0, 0, 0, 0], base)
    prof = horizon_profile(P0, math.degrees(math.atan2(*(T0 - P0)[1::-1])))
    e0 = evaluate(P0, T0, base["focal"])
    print(cid, "start", np.round(e0["bbox"], 3), "sky ray %.3f fast %.3f" % (e0["sky"], sky_fast(P0, T0, base["focal"], prof)), flush=True)
    q, c = nelder_mead(lambda q: cost(q, base, prof), [0, 0, 0, 0], [0.08, 15, 8, 1.5], iters=200)
    P, T = pose(q, base); c, e = cost(q, base, prof); e = evaluate(P, T, base["focal"])  # final check by ray casts
    tb = base["bbox"]
    report[cid] = {"concept": base["concept"], "focal_length_mm": base["focal"],
                   "start": {"position": base["position"], "target": base["target"], "bbox": np.round(e0["bbox"], 4).tolist(), "sky": round(e0["sky"], 4)},
                   "solved": {"position": bl_to_app(P), "target": bl_to_app(T), "bbox": np.round(e["bbox"], 4).tolist(), "sky": round(e["sky"], 4),
                              "width": round(e["width"], 4), "cy": round(e["cy"], 4)},
                   "concept_bbox": np.round(tb, 4).tolist(), "concept_sky": base["sky"], "cost": round(float(c), 3), "q": np.round(q, 4).tolist()}
    print(cid, json.dumps(report[cid]))

(ROOT / "blender/data/concept_cameras.json").write_text(json.dumps(report, indent=1) + "\n")
if "dry" not in sys.argv:
    txt = MANIFEST.read_text(); m = json.loads(txt)
    for c in m["cameras"]:
        if c["id"] in report:
            s = report[c["id"]]["solved"]
            c["position"], c["target"] = s["position"], s["target"]
            c["focal_length_mm"] = report[c["id"]]["focal_length_mm"]
            c["vfov_deg"] = round(math.degrees(2 * math.atan(SENSOR / 2 * 9 / 16 / c["focal_length_mm"])), 3)
            c["sun"] = {"date": "2026-01-15", "time_eat": "07:30" if c["id"] == "C19" else "17:30",
                        "kind": "morning golden" if c["id"] == "C19" else "evening golden"}
            c["note"] = ("pass 1: Sol's start pose, solved to the concept stadium box and sky band "
                         "(blender/concept_match/solve_cameras.py, residuals in blender/data/concept_cameras.json)")
    MANIFEST.write_text(json.dumps(m, indent=1) + ("\n" if txt.endswith("\n") else ""))
