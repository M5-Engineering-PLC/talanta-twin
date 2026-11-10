"""Compare two bakes of the same lightmap set (for example the Kaggle GPU test against the cloud CPU sub-run).

Run:  python3 blender/kaggle/compare_maps.py <maps_dir_a> <maps_dir_b>
Each dir holds <group>_{light,ao,albedo}.png and stages.json. Light maps are decoded to linear light (sRGB decode times
the group's light_scale from its stages.json), so a different light scale does not count as a difference. Per map:
the mean of the linear values, the mean absolute difference as a percent of the mean, and the 99th percentile of the
absolute difference. Pass (light): mean difference 3 % or less and mean values within 2 % (noise only, same light);
ao and albedo: mean absolute difference 2 of 255 or less.
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

A, Bd = Path(sys.argv[1]), Path(sys.argv[2])
scale = lambda d: {k.split(":", 1)[-1]: v["light_scale"] for k, v in json.loads((d / "stages.json").read_text())["done"].items()
                   if isinstance(v, dict) and "light_scale" in v}
sa, sb = scale(A), scale(Bd)
lin = lambda x: np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)
rows, ok = [], True
for fa in sorted(A.glob("*.png")):
    fb = Bd / fa.name
    if not fb.exists(): continue
    a = np.asarray(Image.open(fa).convert("RGB"), np.float32) / 255; b = np.asarray(Image.open(fb).convert("RGB"), np.float32) / 255
    if a.shape != b.shape: rows.append((fa.name, "size differs", a.shape, b.shape)); ok = False; continue
    g, kind = fa.stem.rsplit("_", 1)
    if kind == "light" and g in sa and g in sb:
        la, lb = lin(a) * sa[g], lin(b) * sb[g]; m = (la.mean() + lb.mean()) / 2
        d = np.abs(la - lb); r = (fa.name, round(float(la.mean()), 4), round(float(lb.mean()), 4), round(100 * float(d.mean()) / m, 2), round(float(np.percentile(d, 99)), 4))
        ok &= r[3] <= 3.0 and abs(r[1] - r[2]) / m <= 0.02
    else:
        d = np.abs(a - b) * 255; r = (fa.name, round(float(a.mean() * 255), 2), round(float(b.mean() * 255), 2), round(float(d.mean()), 2), round(float(np.percentile(d, 99)), 2))
        ok &= r[3] <= 2.0
    rows.append(r)
print("map | mean A | mean B | mean abs diff (light: % of mean; others: of 255) | p99 abs diff")
for r in rows: print(" | ".join(str(x) for x in r))
print("PASS" if ok and rows else "FAIL", f"({len(rows)} maps compared)")
