"""Pass metrics and side-by-side sheets for the concept match (engineering/plan_concept_match_2026-10-17.md).

For each camera: render, concept (06 or 07) and the closest historian keep frame, all at 960 x 540.
Numbers per frozen crop: mean and spread of CIELAB colour for render and concept, the colour difference of the
means (Delta E 1976), and edge density (share of pixels whose Sobel gradient of L* exceeds EDGE_T). Whole frame:
stadium bounding-box error (geometric projection vs the hand-measured concept box), horizon height (sky band),
the image direction of cast shadows, and highlight clipping (share of pixels with a channel at 250 or more).
The concept shadow direction is read by eye and marked so. Internal only: concepts and frames never leave the repo.
Run: ~/.venvs/gis/bin/python blender/concept_match/metrics.py <pass_dir>
"""
import csv, json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
W, H = 960, 540
EDGE_T = 6.0  # L* units per pixel (Sobel / 8)
CROPS = {  # frozen crops (x0, y0, x1, y1 as frame fractions, y from the top), drawn on the concept frames
    "C19": {"roof": [0.36, 0.34, 0.70, 0.45], "facade": [0.37, 0.45, 0.68, 0.57], "bowl": [0.45, 0.355, 0.62, 0.40],
            "forecourt": [0.20, 0.62, 0.45, 0.78], "road": [0.35, 0.80, 0.55, 0.90], "canopy": [0, 0.28, 0.30, 0.45],
            "suburbs": [0.72, 0.70, 1, 1], "horizon": [0, 0.13, 1, 0.22]},
    "C20": {"roof": [0.29, 0.35, 0.65, 0.48], "facade": [0.30, 0.50, 0.65, 0.62], "bowl": [0.39, 0.37, 0.55, 0.42],
            "forecourt": [0.25, 0.55, 0.55, 0.70], "road": [0, 0.38, 0.28, 0.46], "canopy": [0, 0.72, 1, 1],
            "suburbs": [0, 0.18, 1, 0.35], "horizon": [0, 0.10, 1, 0.20]},
}
SHEET = {  # render file stem, concept, closest keep frame (as-built aerial with the same subject and side)
    "C19": ("C19_morning_golden_check", "research/concepts/2026-10-17/06_lead_ne_to_ngong_hills.jpg",
            "research/frames/JWNowpO44rw/JWNowpO44rw_000641.633.jpg"),
    "C20": ("C20_evening_golden_check", "research/concepts/2026-10-17/07_lead_ssw_to_lavington.jpg",
            "research/frames/JWNowpO44rw/JWNowpO44rw_001244.833.jpg"),
}
CONCEPT_SHADOW_DEG = {"C19": 205, "C20": 340}  # by eye from palm and tree shadows (image angle, 0 = right, ccw)


def load(p): return np.asarray(Image.open(p).convert("RGB").resize((W, H), Image.LANCZOS), float) / 255


def lab(rgb):
    c = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    xyz = c @ np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]).T
    xyz /= [0.95047, 1.0, 1.08883]
    f = np.where(xyz > 216 / 24389, np.cbrt(xyz), (24389 / 27 * xyz + 16) / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def edges(L): return np.hypot(ndimage.sobel(L, 1), ndimage.sobel(L, 0)) / 8 > EDGE_T


def crop(a, b): x0, y0, x1, y1 = b; return a[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)]


def sky_band_concept(cid): return {"C19": 0.15, "C20": 0.16}[cid]


def main(pdir):
    pdir = ROOT / pdir; cams = json.loads((ROOT / "blender/data/concept_cameras.json").read_text())
    log = {}
    for line in (pdir / "render_log.jsonl").read_text().splitlines():
        r = json.loads(line); log[r["camera"]] = r
    rows = []
    for cid, (stem, cpath, kpath) in SHEET.items():
        rimg, cimg, kimg = load(pdir / f"{stem}.png"), load(ROOT / cpath), load(ROOT / kpath)
        rl, cl = lab(rimg), lab(cimg); re_, ce = edges(rl[..., 0]), edges(cl[..., 0])
        for name, b in CROPS[cid].items():
            a, c = crop(rl, b).reshape(-1, 3), crop(cl, b).reshape(-1, 3)
            ma, mc = a.mean(0), c.mean(0)
            rows.append({"camera": cid, "metric": f"crop:{name}",
                         "render": "L %.1f a %.1f b %.1f sdL %.1f edges %.3f" % (*ma, a[:, 0].std(), crop(re_, b).mean()),
                         "concept": "L %.1f a %.1f b %.1f sdL %.1f edges %.3f" % (*mc, c[:, 0].std(), crop(ce, b).mean()),
                         "difference": "dE76 %.1f dL %.1f dEdges %+.3f" % (np.linalg.norm(ma - mc), ma[0] - mc[0], crop(re_, b).mean() - crop(ce, b).mean())})
        s = cams[cid]["solved"]; cb = cams[cid]["concept_bbox"]
        err = np.abs(np.array(s["bbox"]) - np.array(cb))
        rows.append({"camera": cid, "metric": "stadium_bbox (x0 y0 x1 y1, frame fractions)", "render": " ".join("%.3f" % v for v in s["bbox"]),
                     "concept": " ".join("%.3f" % v for v in cb),
                     "difference": "mean abs %.3f, max %.3f (%.0f px at 960)" % (err.mean(), err.max(), err.max() * W)})
        rows.append({"camera": cid, "metric": "horizon (sky band, share of height)", "render": "%.3f" % s["sky"],
                     "concept": "%.3f" % sky_band_concept(cid), "difference": "%+.3f" % (s["sky"] - sky_band_concept(cid))})
        sh = log[cid].get("shadow_image_deg"); csh = CONCEPT_SHADOW_DEG[cid]
        rows.append({"camera": cid, "metric": "shadow direction (image deg, 0 = right, ccw)", "render": "%.0f" % sh if sh is not None else "",
                     "concept": ("%.0f (by eye)" % csh) if csh is not None else "not read",
                     "difference": "%+.0f" % (((sh - csh + 180) % 360) - 180) if sh is not None and csh is not None else ""})
        rc, cc = (rimg.max(-1) >= 250 / 255).mean(), (cimg.max(-1) >= 250 / 255).mean()
        rows.append({"camera": cid, "metric": "highlight clipping (share >= 250)", "render": "%.4f" % rc, "concept": "%.4f" % cc, "difference": "%+.4f" % (rc - cc)})
        rows.append({"camera": cid, "metric": "render time (s)", "render": "%.0f" % log[cid]["seconds"], "concept": "", "difference": ""})
        # sheet: render | concept | keep frame, crops outlined on the render and the concept
        tiles = []
        for img, label in ((rimg, f"{cid} render (Visualization)"), (cimg, "concept " + Path(cpath).stem[:2] + " (theme only)"),
                           (kimg, "historian keep " + Path(kpath).stem.split("_")[1] + " (geometry truth)")):
            t = Image.fromarray((img * 255).astype(np.uint8)); d = ImageDraw.Draw(t)
            if img is not kimg:
                for name, b in CROPS[cid].items():
                    d.rectangle([b[0] * W, b[1] * H, b[2] * W - 1, b[3] * H - 1], outline=(255, 230, 0)); d.text((b[0] * W + 3, b[1] * H + 2), name, fill=(255, 230, 0))
                bb = s["bbox"] if img is rimg else cb
                d.rectangle([bb[0] * W, bb[1] * H, bb[2] * W, bb[3] * H], outline=(0, 220, 255), width=2)
            d.rectangle([0, 0, 8 * len(label) + 12, 18], fill=(0, 0, 0)); d.text((6, 4), label, fill=(255, 255, 255))
            tiles.append(t)
        sheet = Image.new("RGB", (3 * W, H)); [sheet.paste(t, (i * W, 0)) for i, t in enumerate(tiles)]
        sheet.save(pdir / f"{cid}_side_by_side.jpg", quality=88)
    with open(pdir / "metrics.csv", "w", newline="") as f:
        w = csv.DictWriter(f, ["camera", "metric", "render", "concept", "difference"], lineterminator="\n"); w.writeheader(); w.writerows(rows)
    print(f"{len(rows)} rows -> {pdir / 'metrics.csv'}")


if __name__ == "__main__":
    main(sys.argv[1])
