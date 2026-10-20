"""Normalize the W1b outlines in gis/measurements/ into gis/measurements/normalized/.

The raw CSVs stay as Munene's record. Each normalized ring is:
- closed once (no repeated closing vertex), with consecutive duplicates removed;
- valid: a ring that crosses itself (clicked out of order) is reordered by angle round its vertex mean;
- wound anticlockwise seen from above (east-north), starting at its northernmost vertex;
- densified so no edge is longer than STEP m, keeping every original vertex (flag original=1).
Columns: vertex, lon, lat, x_east, z_south (local twin frame), original.
Run: ~/.venvs/gis/bin/python gis/scripts/normalize_shapes.py
"""
import csv, json, math
from pathlib import Path
from pyproj import Transformer
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[2]
MEAS = ROOT / "gis/measurements"
OUT = MEAS / "normalized"
STEP = 2.0
OX, OY = json.loads((ROOT / "app/public/data/manifest.json").read_text())["origin_utm"]
fwd = Transformer.from_crs(4326, 32737, always_xy=True)
inv = Transformer.from_crs(32737, 4326, always_xy=True)
OUT.mkdir(exist_ok=True)
report = []
for fn in sorted(MEAS.glob("*_w1b_*.csv")):
    rows = list(csv.DictReader(open(fn)))
    if "clicked_order" in rows[0]:  # bowl plinth: rebuild from the click order, then normalize here
        rows = sorted(rows[:-1], key=lambda r: int(r["clicked_order"]))
    pts = [fwd.transform(float(r["lon"]), float(r["lat"])) for r in rows]
    pts = [(x - OX, y - OY) for x, y in pts]  # east, north
    clean = []
    for p in pts:
        if not clean or math.dist(p, clean[-1]) > 0.01: clean.append(p)
    if len(clean) > 2 and math.dist(clean[0], clean[-1]) < 0.01: clean.pop()
    fixed = ""
    if not Polygon(clean).is_valid:
        cx = sum(p[0] for p in clean) / len(clean); cy = sum(p[1] for p in clean) / len(clean)
        clean.sort(key=lambda p: math.atan2(p[1] - cy, p[0] - cx)); fixed = "reordered"
    P = Polygon(clean)
    assert P.is_valid, fn.name
    if not P.exterior.is_ccw: clean.reverse()
    k = max(range(len(clean)), key=lambda i: clean[i][1]); clean = clean[k:] + clean[:k]
    dense = []
    for i, a in enumerate(clean):
        b = clean[(i + 1) % len(clean)]
        n = max(1, math.ceil(math.dist(a, b) / STEP))
        for j in range(n):
            t = j / n; dense.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, j == 0))
    with open(OUT / fn.name, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n"); w.writerow(["vertex", "lon", "lat", "x_east", "z_south", "original"])
        for i, (x, y, o) in enumerate(dense, 1):
            lon, lat = inv.transform(x + OX, y + OY)
            w.writerow([i, round(lon, 9), round(lat, 9), round(x, 3), round(-y, 3), int(o)])
    Q = Polygon([(x, y) for x, y, _ in dense])
    report.append((fn.name, len(rows), len(clean), len(dense), round(P.area), round(Q.area), fixed))
for r in report:
    print(f"{r[0]}: {r[1]} raw rows, {r[2]} vertices, {r[3]} after densify; area {r[4]} -> {r[5]} m2 {r[6]}")
