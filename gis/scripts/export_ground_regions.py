"""Stage 02b: ground regions and road centrelines for the Blender look pass (lead review fix 5).

Writes, in the local twin frame (x east, z south, origin = W1b pitch centre):
- blender/textures/site_regions.png: 1 m/px mask over +-700 m, drawn here from the W1b outlines only (no imagery).
  R = red murram (inside the W1b site boundary), G = light concrete paving (concourse ring round the measured
  plinth, width bowl.ground.concourse_w, and the measured north plaza). Pitches, track and roads sit on top as
  their own objects. Row 0 is north (z = -700).
- blender/data/road_lines.json: centrelines of trunk to tertiary roads within 1.5 km, for lane markings.
Run: ~/.venvs/gis/bin/python gis/scripts/export_ground_regions.py
"""
import csv, json
from pathlib import Path
import geopandas as gpd, shapely
from shapely.geometry import Polygon
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
NORM = ROOT / "gis/measurements/normalized"
L = {r["name"]: r for r in csv.DictReader(open(ROOT / "gis/parameter_ledger.csv"))}
OX, OY = json.loads((ROOT / "app/public/data/manifest.json").read_text())["origin_utm"]
HALF = 700


def ring(fn):
    return [(float(r["x_east"]), float(r["z_south"])) for r in csv.DictReader(open(NORM / fn))]


def px(pts):
    return [(x + HALF, z + HALF) for x, z in pts]


def mask(polys, blur=1.5):
    im = Image.new("L", (2 * HALF, 2 * HALF), 0); d = ImageDraw.Draw(im)
    for p in polys:
        for g in getattr(p, "geoms", [p]): d.polygon(px(list(g.exterior.coords)), fill=255)
    return im.filter(ImageFilter.GaussianBlur(blur))


site = Polygon(ring("site_boundary_w1b_2026-10-16.csv"))
plinth = Polygon(ring("bowl_plinth_w1b_2026-10-17.csv"))
conc = plinth.buffer(float(L["bowl.ground.concourse_w"]["value"]), join_style="round").intersection(site)
plaza = Polygon(ring("north_plaza_w1b_2026-10-17.csv"))
R = mask([site]); G = mask([conc, plaza])
out = ROOT / "blender/textures/site_regions.png"
Image.merge("RGB", (R, G, Image.new("L", R.size, 0))).save(out)

r = gpd.read_file(ROOT / "gis/derived/roads.gpkg"); r = r[(r.subtype == "road") & r["class"].isin(["trunk", "primary", "secondary", "tertiary"])]
lines = []
for cls, g in zip(r["class"], r.geometry):
    for part in getattr(g, "geoms", [g]):
        pts = [(round(x - OX, 2), round(-(y - OY), 2)) for x, y in part.coords]
        if min(x * x + z * z for x, z in pts) < 1500 ** 2: lines.append({"class": cls, "pts": pts})
(ROOT / "blender/data/road_lines.json").write_text(json.dumps(lines))
print(out, "site", round(site.area), "m2; concourse+plaza", round(conc.union(plaza).area), "m2;", len(lines), "road lines")
