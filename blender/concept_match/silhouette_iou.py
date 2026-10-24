"""Replica plan acceptance (2026-10-20): stadium silhouette IoU of a drone render against its frame.

Model silhouette: the flat Workbench mask of the bowl from the exact solved camera (drone_masks.py). Frame silhouette:
the stadium pixels of the frame inside a band of +-BAND (15) px round the model silhouette (inside the band's inner edge
counts as stadium, outside its outer edge as background), by a colour model learned from the same frame (stadium
interior against a ring outside the band); then hole filling and the largest component. Prints the IoU per camera and writes an outline overlay (internal: frame inside).
Run from the repo root (gis venv):
  ~/.venvs/gis/bin/python blender/concept_match/silhouette_iou.py <mask dir> [out dir]
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
FRAMES = {"D01": "000645.000", "D02": "000714.767", "D03": "000617.567"}
BAND = 15


def frame_silhouette(img, model):
    """Stadium pixels of the frame in the band round the model silhouette, by a colour model learned from this frame:
    RGB histograms (16 bins a channel) of the pixels well inside the silhouette (stadium) and of a ring outside the
    band (background); a band pixel is stadium where its smoothed stadium probability is over one half."""
    inner = ndimage.binary_erosion(model, iterations=BAND); outer = ndimage.binary_dilation(model, iterations=BAND)
    ring = ndimage.binary_dilation(model, iterations=3 * BAND) & ~outer
    q = (img.astype(int) // 16); key = q[..., 0] * 256 + q[..., 1] * 16 + q[..., 2]
    hs = np.bincount(key[inner], minlength=4096) + 0.5; hb = np.bincount(key[ring], minlength=4096) + 0.5
    hs, hb = hs / hs.sum(), hb / hb.sum()
    p = (hs / (hs + hb))[key]; p = ndimage.gaussian_filter(p, 2.0)
    sil = inner | ((p > 0.5) & outer)
    sil = ndimage.binary_opening(sil, iterations=2); sil = ndimage.binary_fill_holes(sil)
    lab, n = ndimage.label(sil)
    if n > 1: sil = lab == (np.argmax(np.bincount(lab.ravel())[1:]) + 1)
    return ndimage.binary_fill_holes(ndimage.binary_closing(sil, iterations=3))


def main():
    mdir = Path(sys.argv[1]); out = Path(sys.argv[2]) if len(sys.argv) > 2 else None; res = {}
    for cid, fr in FRAMES.items():
        mp = mdir / f"{cid}_stadium_mask.png"
        if not mp.exists(): continue
        model = np.asarray(Image.open(mp).convert("L")) > 127
        img = np.asarray(Image.open(ROOT / f"research/frames/JWNowpO44rw/JWNowpO44rw_{fr}.jpg").convert("RGB").resize(model.shape[::-1]))
        sil = frame_silhouette(img, model)
        iou = (model & sil).sum() / (model | sil).sum()
        res[cid] = {"iou": round(float(iou), 4), "model_px": int(model.sum()), "frame_px": int(sil.sum()),
                    "model_only_px": int((model & ~sil).sum()), "frame_only_px": int((sil & ~model).sum())}
        if out:
            out.mkdir(parents=True, exist_ok=True); o = img.copy()
            em = model ^ ndimage.binary_erosion(model, iterations=2); ef = sil ^ ndimage.binary_erosion(sil, iterations=2)
            o[em] = (255, 0, 255); o[ef] = (0, 255, 255)
            Image.fromarray(o).save(out / f"{cid}_silhouette_internal.jpg", quality=90)
    print(json.dumps(res, indent=1))
    return res


if __name__ == "__main__":
    main()
