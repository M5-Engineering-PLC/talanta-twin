"""Pass 1 framing: refine the C19 and C20 poses so the stadium sits in the frame as in lead renders 06 and 07.

Measured on the concept images (1600 x 900, by hand, engineering/plan_concept_match_2026-10-17.md):
the stadium bounding box (x0, y0, x1, y1 as fractions of the frame, y from the top) and the sky band (the
fraction of the frame height above the land horizon). Starting poses and focal lengths are Sol's. The bearing
and focal length stay fixed; the solver moves the camera distance and height, the aim height and a small yaw.
The stadium box is the projection of the plinth, shell and facade_detail meshes. The horizon is a profile of
land elevation angle against azimuth, ray cast once from the start position (haze box hidden); the sky band of
each trial pose follows from it in closed form, and the final pose is checked with direct ray casts. Writes the poses to app/cameras/manifest.json (C19 and C20 only)
and the residuals to blender/data/concept_cameras.json.
Run: ~/.venvs/bpy/bin/python blender/concept_match/solve_cameras.py [dry|check] [landing|drone]
"landing" solves the landing cameras L06 and L07 to the 2026-10-18 landing mockups 06 and 07 instead (Munene,
2026-10-19: the landing frame mirrors the mockups). They start from the C19 and C20 poses, are added to the manifest
as new cameras, and leave C19 and C20 unchanged. Residuals go to blender/data/landing_cameras.json.
"drone" solves D01 and D02 to two as-built drone frames the same way, for the environment pass (internal only).
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
# Landing mockups (branch munene/CAM-01-landing-option, product/landing-concepts/2026-10-18/, 1672 x 941, by hand on a
# 50 px grid, 2026-10-19). The images include the header bar, as the app draws it over the full-window canvas.
LANDING_TARGETS = {
    "L06": {"concept": "product/landing-concepts/2026-10-18/06-hillside-landing-mockup.png", "from": "C19",
            "bbox": [343 / 1672, 388 / 941, 1337 / 1672, 708 / 941], "sky": 0.33,
            "position": [511.17, 146.14, -470.13], "target": [11.49, 9.91, 12.55], "focal": 35},
    "L07": {"concept": "product/landing-concepts/2026-10-18/07-cityside-landing-mockup.png", "from": "C20",
            "bbox": [500 / 1672, 360 / 941, 1370 / 1672, 705 / 941], "sky": 0.25,
            "position": [-170.06, 144.41, 617.95], "target": [23.05, 22.01, 5.95], "focal": 38},
}
for t, (name, sun, seed) in zip(LANDING_TARGETS.values(), (
        ("Landing Hillside", {"date": "2026-01-15", "time_eat": "17:30", "kind": "evening golden"}, 6),     # mockup 06 Sunset
        ("Landing Cityside", {"date": "2026-01-15", "time_eat": "12:30", "kind": "neutral daylight"}, 7))):  # mockup 07 Daylight
    t.update(name=name, sun=sun, seed=seed, purpose=f"landing view and backdrop still, framed as {Path(t['concept']).stem}; the mockup is internal only")
# Environment pass (2026-10-19): as-built drone frames of JWNowpO44rw (January 2026), DJI 24 mm equivalent, measured by
# hand on a 40 px grid. Internal only: the cameras exist to compare the environment with the footage.
DRONE_TARGETS = {
    "D01": {"concept": "research/frames/JWNowpO44rw/JWNowpO44rw_000645.000.jpg", "from": "C19",
            "bbox": [455 / 1280, 172 / 720, 982 / 1280, 362 / 720], "sky": 0.18,
            "position": [170, 110, -430], "target": [0, 10, 0], "focal": 24,  # north plaza and Ngong Road in front
            "landmarks": [[[2.2, 205.3], [860 / 1280, 437 / 720]], [[2.2, 182.0], [818 / 1280, 404 / 720]], [[2.2, 229.0], [905 / 1280, 480 / 720]]],
            "name": "Drone 000645.000", "seed": 31, "sun": {"date": "2026-01-15", "time_eat": "10:30", "kind": "daylight"},
            "purpose": "environment check against drone frame 000645.000 (north of the site over Ngong Road, looking SSW); internal only"},
    "D02": {"concept": "research/frames/JWNowpO44rw/JWNowpO44rw_000714.767.jpg", "from": "C20",
            "bbox": [405 / 1280, 230 / 720, 946 / 1280, 440 / 720], "sky": 0.25,
            "position": [-170.06, 144.41, 617.95], "target": [23.05, 22.01, 5.95], "focal": 24,
            # south of the bowl over the forest, the city behind: the plaza in front is the south plaza, not yet in the
            # model, so no landmarks; the stadium box alone fixes this pose
            "name": "Drone 000714.767", "seed": 32, "sun": {"date": "2026-01-15", "time_eat": "10:30", "kind": "daylight"},
            "purpose": "environment check against drone frame 000714.767 (south of the bowl over the forest, looking N to the city); internal only"},
    # overview frame: east of the bowl looking W, Ngong Road running away at the top right. Landmarks: the W1b north plaza
    # (its round bed, right of the bowl) and the W1b warm-up track (right foreground). The eye-shaped paving in the
    # foreground is an east approach, not the W1b plaza.
    "D03": {"concept": "research/frames/JWNowpO44rw/JWNowpO44rw_000617.567.jpg", "from": "C20",
            "bbox": [345 / 1280, 40 / 720, 880 / 1280, 280 / 720], "sky": 0.0,
            "position": [520, 330, -20], "target": [0, 0, 0], "focal": 24,
            "landmarks": [[[-15, 205], [985 / 1280, 195 / 720]], [[171, 123], [940 / 1280, 370 / 720]]],
            "name": "Drone 000617.567", "seed": 33, "sun": {"date": "2026-01-15", "time_eat": "10:30", "kind": "daylight"},
            "purpose": "environment check against overview frame 000617.567 (east of the bowl, looking W); internal only"},
}
# Orientation test (dry only): the overview frame 000617.567 against W1b-measured landmarks (blender x east, y north):
# the eye-shaped plaza (centroid 15 m W, 205 m N) and the warm-up track (171 m E, 123 m N). "B" mirrors east and west.
_ov = {"concept": "research/frames/JWNowpO44rw/JWNowpO44rw_000617.567.jpg", "from": "C19",
       "bbox": [345 / 1280, 40 / 720, 880 / 1280, 280 / 720], "sky": 0.0,
       "position": [0, 330, -420], "target": [0, 0, -60], "focal": 24}
ORIENT_TARGETS = {
    "O_A": {**_ov, "landmarks": [[[-15, 205], [600 / 1280, 400 / 720]], [[171, 123], [940 / 1280, 370 / 720]]]},
    "O_B": {**_ov, "landmarks": [[[15, 205], [600 / 1280, 400 / 720]], [[-171, 123], [940 / 1280, 370 / 720]]]},
    "O_C": {**_ov, "landmarks": [[[-15, -205], [600 / 1280, 400 / 720]], [[171, -123], [940 / 1280, 370 / 720]]]},  # north-south flip
    "O_D": {**_ov, "landmarks": [[[15, -205], [600 / 1280, 400 / 720]], [[-171, -123], [940 / 1280, 370 / 720]]]},  # 180 deg turn
}
if __import__("os").environ.get("ORIENT_ONLY"):
    ORIENT_TARGETS = {k: v for k, v in ORIENT_TARGETS.items() if k in __import__("os").environ["ORIENT_ONLY"].split(",")}
MODE = next((m for m in ("landing", "drone", "orient") if m in sys.argv), None)
LANDING = MODE is not None
if MODE: TARGETS = {"landing": LANDING_TARGETS, "drone": DRONE_TARGETS, "orient": ORIENT_TARGETS}[MODE]
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
if "orient" in sys.argv or "drone" in sys.argv: PTS = PTS[::50]  # a bounding box needs far fewer points; keeps the 48-start test quick
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


def ground(xy):
    """Blender ground point under (x, y): the first hit of a ray down from 2 km."""
    from mathutils import Vector
    hit = scene.ray_cast(dg, Vector((xy[0], xy[1], 2000.0)), Vector((0, 0, -1)), distance=1e5)
    return np.array([xy[0], xy[1], hit[1].z if hit[0] else 0.0])


def landmark_cost(P, T, base):
    if not base.get("landmarks"): return 0.0
    f, r, u = basis(P, T); k = base["focal"] / (SENSOR / 2); out = 0.0
    for pt, (ux, uy) in base["_lm"]:
        d = pt - P; z = d @ f
        x = 0.5 + 0.5 * (d @ r) / z * k; y = 0.5 - 0.5 * (d @ u) / z * k * W / H
        out += ((x - ux) / 0.01) ** 2 + ((y - uy) / 0.01) ** 2
    return out


def cost(q, base, prof):
    tb = np.array(base["bbox"]); P, T = pose(q, base); e = evaluate(P, T, base["focal"], prof)
    return (landmark_cost(P, T, base) + ((e["width"] - (tb[2] - tb[0])) / 0.01) ** 2 + ((e["cx"] - (tb[0] + tb[2]) / 2) / 0.01) ** 2
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


def best_start(cid, base):
    """With landmarks, try 24 start bearings round the target (same distance and height) and keep the best solve."""
    if not base.get("landmarks"): return base
    base["_lm"] = [(ground(xy), uv) for xy, uv in base["landmarks"]]
    P0, T0 = app_to_bl(base["position"]), app_to_bl(base["target"]); hor = P0[:2] - T0[:2]; best = None
    for i in range(24):
        a = math.radians(15 * i); c_, s_ = math.cos(a), math.sin(a)
        trial = {**base, "position": bl_to_app(np.array([T0[0] + c_ * hor[0] - s_ * hor[1], T0[1] + s_ * hor[0] + c_ * hor[1], P0[2]]))}
        Ps, Ts = pose([0, 0, 0, 0], trial)
        prof = horizon_profile(Ps, math.degrees(math.atan2(*(Ts - Ps)[1::-1])))
        q, c = nelder_mead(lambda q: cost(q, trial, prof), [0, 0, 0, 0], [0.08, 15, 8, 1.5], iters=120)
        print(cid, "bearing start", 15 * i, "cost %.2f" % c, flush=True)
        if best is None or c < best[0]: best = (c, trial)
    return best[1]


if "check" in sys.argv:
    # python ... solve_cameras.py check drone: score each target at its fixed manifest camera, no solve, no writes
    # (geometry pass 4: the drone checks before and after a shape change). Same cost as the solve.
    man = {c["id"]: c for c in json.loads(MANIFEST.read_text())["cameras"]}
    out = {}
    for cid, base in TARGETS.items():
        cam = man[cid]; base = {**base, "position": cam["position"], "target": cam["target"]}
        if base.get("landmarks"): base["_lm"] = [(ground(xy), uv) for xy, uv in base["landmarks"]]
        P0, T0 = pose([0, 0, 0, 0], base)
        prof = horizon_profile(P0, math.degrees(math.atan2(*(T0 - P0)[1::-1])))
        c, e = cost([0, 0, 0, 0], base, prof)
        out[cid] = {"cost": round(float(c), 3), "bbox": np.round(e["bbox"], 4).tolist(), "target_bbox": np.round(base["bbox"], 4).tolist(),
                    "sky": round(e["sky"], 4), "landmarks": round(float(landmark_cost(P0, T0, base)), 3)}
        print("CHECK", cid, json.dumps(out[cid]), flush=True)
    sys.exit(0)

report = {}
for cid, base in TARGETS.items():
    base = best_start(cid, base)
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

(ROOT / "blender/data" / (f"{MODE}_cameras.json" if MODE else "concept_cameras.json")).write_text(json.dumps(report, indent=1) + "\n")
if LANDING and "dry" not in sys.argv:
    txt = MANIFEST.read_text(); m = json.loads(txt)
    m["cameras"] = [c for c in m["cameras"] if c["id"] not in report]
    for cid, r in report.items():
        src = next(c for c in m["cameras"] if c["id"] == TARGETS[cid]["from"])
        t = TARGETS[cid]
        c = {**src, "id": cid, "name": t["name"], "purpose": t["purpose"],
             "position": r["solved"]["position"], "target": r["solved"]["target"], "focal_length_mm": r["focal_length_mm"],
             "vfov_deg": round(math.degrees(2 * math.atan(SENSOR / 2 * 9 / 16 / r["focal_length_mm"])), 3),
             "sun": t["sun"], "seed": t["seed"],
             "note": f"solved to the stadium box and sky band of {Path(t['concept']).name} "
                     f"(blender/concept_match/solve_cameras.py {MODE}, residuals in blender/data/{MODE}_cameras.json)"}
        m["cameras"].insert(m["cameras"].index(src) + 1, c)
    MANIFEST.write_text(json.dumps(m, indent=1) + ("\n" if txt.endswith("\n") else ""))
if not LANDING and "dry" not in sys.argv:
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
