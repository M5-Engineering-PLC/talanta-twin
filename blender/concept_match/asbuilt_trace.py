"""Replica plan pass C (2026-10-21): as-built ground classes traced from the drone frames through the solved cameras.

Each frame (JWNowpO44rw 000645.000 = D01, 000714.767 = D02, 000617.567 = D03, 1280 x 720) is split into surface
classes by hue and brightness (classify()). A 1 m plan grid round the bowl (app frame: x east, z south) is set on the
terrain (terrain_grid.npz from drone_masks.py) and projected into every frame with the exact solved camera
(app/cameras/manifest.json). A cell takes the class of the frame that sees it with the smallest ground footprint (at
most MAX_FOOT m per pixel); cells under the stadium mask (drone_masks.py, dilated) or outside every frame stay unknown.
A 5 x 5 majority filter removes pixel noise. The result is a label map and class outlines, our own vector data: no
frame pixel is stored or used as a texture (AGENTS.md rule 2).
Run from the repo root (gis venv):
  ~/.venvs/gis/bin/python blender/concept_match/asbuilt_trace.py <mask dir> <out label png> [current plan png]
Writes the label map (8-bit, value = class index, row 0 = north edge), <label>.json (extent, classes, coverage per
camera, outlines per class) and, with a current-layout plan (plan_classes.py), the change list.
"""
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
CLASSES = ["unknown", "grass", "murram", "laterite", "paved", "tree", "white"]
FRAMES = {"D01": "000645.000", "D02": "000714.767", "D03": "000617.567"}
EXT, CELL, MAX_FOOT = 450.0, 1.0, 2.5


def classify(rgb):
    """Class index per pixel of an sRGB uint8 image: hue (deg), saturation and brightness rules read from the frames."""
    a = rgb.astype(float); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mx, mn = a.max(-1), a.min(-1); ch = mx - mn; lum = a.mean(-1)
    hue = np.degrees(np.arctan2(math.sqrt(3) * (g - b), 2 * r - g - b))  # -180..180, red 0, yellow 60, green 120
    out = np.zeros(r.shape, np.uint8)
    grey = ch < 22
    out[grey & (lum > 60)] = CLASSES.index("paved")
    out[(lum > 195) & (ch < 45)] = CLASSES.index("white")
    col = ~grey & (lum <= 195)
    green = col & (hue >= 36) & (hue < 170)
    out[green & (lum >= 70)] = CLASSES.index("grass")
    out[(lum < 80) & (hue >= 36) & (hue < 170)] = CLASSES.index("tree")
    earth = col & ((hue < 36) & (hue > -60))
    out[earth & (lum < 110)] = CLASSES.index("murram")
    out[earth & (lum >= 110)] = CLASSES.index("laterite")
    return out


def camera(cid):
    m = json.loads((ROOT / "app/cameras/manifest.json").read_text())
    c = next(c for c in m["cameras"] if c["id"] == cid)
    C, T = np.array(c["position"], float), np.array(c["target"], float)
    fwd = (T - C) / np.linalg.norm(T - C); right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right); up = np.cross(right, fwd)
    return C, fwd, right, up, c["focal_length_mm"] / m["sensor_width_mm"] * 1280


def main():
    mdir = Path(sys.argv[1]); out = ROOT / sys.argv[2] if not Path(sys.argv[2]).is_absolute() else Path(sys.argv[2])
    tg = np.load(mdir / "terrain_grid.npz"); th = tg["h"]; tx0, tz0, ts = float(tg["x0"]), float(tg["z0"]), float(tg["step"])
    n = int(2 * EXT / CELL); c1 = -EXT + CELL * (np.arange(n) + 0.5)
    X, Z = np.meshgrid(c1, c1)  # row = z (north first: z south positive, so row 0 = most negative z = north)
    Y = ndimage.map_coordinates(th, [(Z - tz0) / ts, (X - tx0) / ts], order=1, mode="nearest")
    P = np.stack([X, Y, Z], -1)
    medians = {}; best_foot = np.full(X.shape, np.inf); lab = np.zeros(X.shape, np.uint8); src = np.zeros(X.shape, np.uint8); cov = {}
    for k, (cid, fr) in enumerate(FRAMES.items()):
        img = np.asarray(Image.open(ROOT / f"research/frames/JWNowpO44rw/JWNowpO44rw_{fr}.jpg").convert("RGB").resize((1280, 720)))
        cls = classify(img)
        medians[cid] = {c: np.median(img[(cls == i) & (np.arange(720)[:, None] >= 300)], 0).astype(int).tolist() for i, c in enumerate(CLASSES) if c in ("grass", "murram", "laterite", "paved")}
        mask = np.asarray(Image.open(mdir / f"{cid}_stadium_mask.png").convert("L")) > 127
        mask = ndimage.binary_dilation(mask, iterations=4)
        C, fwd, right, up, f = camera(cid)
        d = P - C; z = d @ fwd; u = 640 + f * (d @ right) / z; v = 360 - f * (d @ up) / z
        dist = np.linalg.norm(d, axis=-1); sin_el = np.abs(d[..., 1]) / dist
        foot = dist / f / np.maximum(sin_el, 0.05)  # metres of ground per pixel along the view
        ui, vi = np.round(u).astype(int), np.round(v).astype(int)
        ok = (z > 1) & (ui >= 0) & (ui < 1280) & (vi >= 0) & (vi < 720) & (foot < MAX_FOOT)
        ok[ok] &= ~mask[vi[ok], ui[ok]]
        c_ = np.zeros(X.shape, np.uint8); c_[ok] = cls[vi[ok], ui[ok]]
        take = ok & (c_ > 0) & (foot < best_foot)
        lab[take] = c_[take]; best_foot[take] = foot[take]; src[take] = k + 1
        cov[cid] = {"frame": fr, "cells_seen": int(ok.sum()), "cells_taken": int(take.sum())}
    # 5 x 5 majority over the known classes (unknown cells next to known ones are filled)
    votes = np.stack([ndimage.uniform_filter((lab == i).astype(np.float32), 5) for i in range(len(CLASSES))])
    votes[0] *= 0.5
    lab = votes.argmax(0).astype(np.uint8)
    out.parent.mkdir(parents=True, exist_ok=True); Image.fromarray(lab).save(out)
    meta = {"extent_m": [-EXT, EXT, -EXT, EXT], "cell_m": CELL, "rows": "row 0 = north edge (z = -450), z south",
            "classes": CLASSES, "frames": cov, "max_ground_footprint_m_per_px": MAX_FOOT,
            "area_m2": {c: int((lab == i).sum() * CELL * CELL) for i, c in enumerate(CLASSES)},
            "method": "frame pixels classified by hue/brightness, plan cells projected through the solved drone cameras; "
                      "finest ground footprint wins; 5x5 majority filter (blender/concept_match/asbuilt_trace.py)"}
    meta["outlines"] = outlines(lab)
    meta["south_west"] = south_west(lab)
    meta["class_median_srgb"] = medians
    if len(sys.argv) > 3: meta["changes"] = changes(lab, np.asarray(Image.open(sys.argv[3])))
    Path(str(out)[:-4] + ".json").write_text(json.dumps(meta, indent=1) + "\n")
    print(json.dumps({k: v for k, v in meta.items() if k not in ("outlines", "changes")}, indent=1))
    for c in meta.get("changes", []): print(c)


def outlines(lab, min_area=150.0, tol=1.0):
    """Polygons per class (app x, z in metres) from row runs, unioned and simplified."""
    from shapely.geometry import box
    from shapely.ops import unary_union
    res = {}
    for i, c in enumerate(CLASSES):
        if c in ("unknown", "white", "tree"): continue
        boxes = []
        for r in range(lab.shape[0]):
            row = lab[r] == i
            if not row.any(): continue
            e = np.flatnonzero(np.diff(np.concatenate([[0], row.astype(np.int8), [0]])))
            for a, b in zip(e[::2], e[1::2]):
                boxes.append(box(-EXT + a * CELL, -EXT + r * CELL, -EXT + b * CELL, -EXT + (r + 1) * CELL))
        g = unary_union(boxes).simplify(tol)
        polys = [g] if g.geom_type == "Polygon" else list(getattr(g, "geoms", []))
        res[c] = [[[round(x, 1), round(z, 1)] for x, z in p.exterior.coords] for p in polys if p.area >= min_area]
    return res


def _component(lab, cls, near):
    """The connected cells of a class at (or nearest to) app point near; centre, unit long axis, length and width
    (1st to 99th percentile along the principal axes)."""
    cc, _ = ndimage.label(lab == cls); r, c = int(near[1] + EXT), int(near[0] + EXT); j = cc[r, c]
    if j == 0:
        ii = ndimage.distance_transform_edt(cc == 0, return_indices=True)[1]; j = cc[ii[0][r, c], ii[1][r, c]]
    rr, cl = np.nonzero(cc == j); P = np.stack([cl - EXT + 0.5, rr - EXT + 0.5], 1) * CELL; mu = P.mean(0)
    _, _, Vt = np.linalg.svd(P - mu, full_matrices=False); pr = (P - mu) @ Vt.T
    lo, hi = np.percentile(pr, 1, 0), np.percentile(pr, 99, 0); ctr = mu + ((hi + lo) / 2) @ Vt
    ax = Vt[0] if Vt[0][1] >= 0 else -Vt[0]
    return {"centre_xz": [round(float(v), 1) for v in ctr], "axis_xz": [round(float(v), 4) for v in ax],
            "len_m": round(float(hi[0] - lo[0]), 1), "wid_m": round(float(hi[1] - lo[1]), 1), "cells": int(len(rr))}


def south_west(lab):
    """The south-west foreground of D02: the lawn pitch inside the loop road, and the stand with the white roof west of
    it (seed points from the D02 frame read through the solved camera)."""
    lawn = _component(lab, CLASSES.index("grass"), (-110, 180))
    stand = _component(lab, CLASSES.index("white"), (-200, 125))
    # loop road width: paved share of the cells in 2 m bands round the lawn, cut where it falls under half
    cc, _ = ndimage.label(lab == CLASSES.index("grass")); r, c = int(180 + EXT), int(-110 + EXT)
    dist = ndimage.distance_transform_edt(cc != cc[r, c]) * CELL; road_w = 0.0
    for d0 in np.arange(0, 30, 2):
        band = (dist > d0) & (dist <= d0 + 2); share = (lab[band] == CLASSES.index("paved")).mean()
        if share < 0.5: break
        road_w = d0 + 2
    return {"lawn_centre_xz": lawn["centre_xz"], "lawn_axis_xz": lawn["axis_xz"], "lawn_len_m": lawn["len_m"],
            "lawn_wid_m": lawn["wid_m"], "loop_road_w_m": max(road_w, 8.0), "loop_corner_r_m": 18.0,
            "loop_note": "road width from the paved share round the lawn (at least 8 m); corner radius by eye from 000714.767",
            "stand": {"centre_xz": stand["centre_xz"], "axis_xz": stand["axis_xz"], "len_m": stand["len_m"],
                      "depth_m": min(stand["wid_m"], 18.0), "note": "white roof cells west of the loop; depth capped at 18 m"}}


def changes(lab, cur, min_area=400):
    """Connected areas where the frames and the current layout plan disagree, largest first."""
    out = []
    for i, c in enumerate(CLASSES):
        if c in ("unknown", "white"): continue
        diff = (lab == i) & (cur != i) & (cur > 0)
        cc, n = ndimage.label(diff)
        for j, sl in enumerate(ndimage.find_objects(cc), 1):
            m = cc[sl] == j; area = int(m.sum() * CELL * CELL)
            if area < min_area: continue
            rr, ccx = np.nonzero(m); zc = -EXT + (sl[0].start + rr.mean() + 0.5) * CELL; xc = -EXT + (sl[1].start + ccx.mean() + 0.5) * CELL
            was = np.bincount(cur[sl][m], minlength=len(CLASSES)).argmax()
            brg = (math.degrees(math.atan2(xc, -zc)) + 360) % 360
            out.append({"frames": c, "model": CLASSES[was], "area_m2": area, "centre_xz": [round(xc), round(zc)],
                        "bearing_deg": round(brg), "distance_m": round(math.hypot(xc, zc))})
    return sorted(out, key=lambda d: -d["area_m2"])


if __name__ == "__main__":
    main()
