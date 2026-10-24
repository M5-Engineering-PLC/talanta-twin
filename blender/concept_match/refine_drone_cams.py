"""Replica plan pass C (2026-10-21): refine a solved drone camera on the stadium silhouette.

The bowl (blender/out/bowl_rings.json, every ring of the fitted profile) is near convex, so its silhouette from a
camera is the convex hull of its projected ring points (IoU 0.98 or better against the rendered mask). Starting from
the solved camera in app/cameras/manifest.json, the position, yaw, pitch, roll and focal length are adjusted to minimise
the symmetric chamfer distance between that hull and the frame silhouette (silhouette_iou.frame_silhouette, colour
model of the same frame, band BAND px round the hull). Two rounds: the frame silhouette is re-cut round the first fit.
Prints the IoU before and after; with --write it updates the camera in the manifest (position, target, focal length)
and notes the refinement in its "note".
Run from the repo root (gis venv):
  ~/.venvs/gis/bin/python blender/concept_match/refine_drone_cams.py D01 [D02 D03] [--write]
"""
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
from scipy.optimize import minimize
from scipy.spatial import ConvexHull

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "blender/concept_match"))
import silhouette_iou as SI

W, H, BAND = 1280, 720, 40
R = json.loads((ROOT / "blender/out/bowl_rings.json").read_text()); P = np.array(R["prof"])
th = 2 * np.pi * np.arange(R["N"]) / R["N"]
PTS = np.stack([np.cos(th)[:, None] * P[:, :, 0], P[:, :, 1] + R["pad"], np.sin(th)[:, None] * P[:, :, 0]], -1).reshape(-1, 3)
MAN = ROOT / "app/cameras/manifest.json"; M = json.loads(MAN.read_text())


def basis(yaw, pitch, roll):
    fwd = np.array([math.cos(pitch) * math.cos(yaw), math.sin(pitch), math.cos(pitch) * math.sin(yaw)])
    right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right); up = np.cross(right, fwd)
    cr, sr = math.cos(roll), math.sin(roll)
    return fwd, cr * right + sr * up, -sr * right + cr * up


def hull(x):
    C, (yaw, pitch, roll, lf) = x[:3], x[3:]; fwd, right, up = basis(yaw, pitch, roll); f = math.exp(lf)
    d = PTS - C; z = d @ fwd; uv = np.stack([W / 2 + f * (d @ right) / z, H / 2 - f * (d @ up) / z], 1)
    poly = uv[ConvexHull(uv).vertices]; im = Image.new("L", (W, H)); ImageDraw.Draw(im).polygon([tuple(p) for p in poly], fill=255)
    return np.asarray(im) > 127, poly


def edge(m): return m ^ ndimage.binary_erosion(m)


def refine(cid):
    c = next(c for c in M["cameras"] if c["id"] == cid); C = np.array(c["position"], float); T = np.array(c["target"], float)
    d = (T - C) / np.linalg.norm(T - C); yaw, pitch = math.atan2(d[2], d[0]), math.asin(d[1])
    x0 = np.array([*C, yaw, pitch, 0.0, math.log(c["focal_length_mm"] / M["sensor_width_mm"] * W)])
    fr = SI.FRAMES[cid]; img = np.asarray(Image.open(ROOT / f"research/frames/JWNowpO44rw/JWNowpO44rw_{fr}.jpg").convert("RGB").resize((W, H)))
    SI.BAND = BAND
    m0, _ = hull(x0); sil = SI.frame_silhouette(img, m0); iou0 = (m0 & sil).sum() / (m0 | sil).sum()
    x = x0.copy()
    for rnd in range(2):
        dt = ndimage.distance_transform_edt(~edge(sil)); fe = np.argwhere(edge(sil))[::3]
        scale = np.array([5, 5, 5, 0.01, 0.01, 0.01, 0.02])

        def cost(s):
            m, poly = hull(x0 + s * scale)
            he = edge(m); a = dt[he].mean() if he.any() else 1e3
            b = ndimage.distance_transform_edt(~he)[fe[:, 0], fe[:, 1]].mean()
            return a + b
        r = minimize(cost, (x - x0) / scale, method="Powell", options={"maxiter": 3000, "xtol": 1e-2, "ftol": 1e-3})
        x = x0 + r.x * scale; m1, _ = hull(x); sil = SI.frame_silhouette(img, m1)
    iou1 = (m1 & sil).sum() / (m1 | sil).sum(); m0b, _ = hull(x0); iou0b = (m0b & sil).sum() / (m0b | sil).sum()
    fwd, right, up = basis(*x[3:6]); f_mm = math.exp(x[6]) * M["sensor_width_mm"] / W
    out = {"cid": cid, "iou_solved": round(float(iou0b), 4), "iou_refined": round(float(iou1), 4), "chamfer_px": round(float(r.fun) / 2, 2),
           "moved_m": round(float(np.linalg.norm(x[:3] - x0[:3])), 2), "yaw_deg": round(math.degrees(x[3] - x0[3]), 3),
           "pitch_deg": round(math.degrees(x[4] - x0[4]), 3), "roll_deg": round(math.degrees(x[5]), 3),
           "focal_mm": [round(c["focal_length_mm"], 2), round(f_mm, 2)],
           "position": [round(float(v), 2) for v in x[:3]], "target": [round(float(v), 2) for v in x[:3] + fwd * 400]}
    return out, c


if __name__ == "__main__":
    write = "--write" in sys.argv
    for cid in [a for a in sys.argv[1:] if not a.startswith("--")]:
        o, c = refine(cid); print(json.dumps(o), flush=True)
        if write and o["iou_refined"] > o["iou_solved"]:
            c["position"], c["target"], c["focal_length_mm"] = o["position"], o["target"], round(o["focal_mm"][1], 3)
            if abs(o["roll_deg"]) > 1e-3: c["roll_deg"] = o["roll_deg"]
            c["vfov_deg"] = round(math.degrees(2 * math.atan(M["sensor_width_mm"] * H / W / 2 / c["focal_length_mm"])), 3)
            c["note"] = c.get("note", "") + (f"; refined 2026-10-21 on the stadium silhouette (blender/concept_match/refine_drone_cams.py: "
                                             f"IoU {o['iou_solved']} -> {o['iou_refined']}, moved {o['moved_m']} m)")
    if write: MAN.write_text(json.dumps(M, indent=1) + "\n")
