"""W1: Google Open Buildings 2.5D Temporal (v1, CC BY 4.0) for the 3 km box, 2016-2023.

Reads the yearly 0.5 m rasters (bands: fractional count, height in m, presence) through
HTTPS range requests and writes gis/raw/open_buildings_temporal/<year>.tif (EPSG:32737).
The last epoch is 2023-06-30, before the stadium groundbreaking (1 Mar 2024), so this data
covers the near ring only, not the bowl.
"""
import json, sys, urllib.request
from pathlib import Path
import numpy as np, rasterio
from rasterio.windows import from_bounds
from rasterio.transform import Affine
sys.path.insert(0, str(Path(__file__).parent))
from _aoi import box_utm, gdal_env

gdal_env()
GCS = "https://storage.googleapis.com/open-buildings-temporal-data"
OUT = Path(__file__).resolve().parents[1] / "raw" / "open_buildings_temporal"

def manifests(year):
    u = f"https://storage.googleapis.com/storage/v1/b/open-buildings-temporal-data/o?prefix=v1/manifests/&maxResults=5000&fields=items(name)"
    names = [i["name"] for i in json.load(urllib.request.urlopen(u, timeout=60))["items"]]
    return [n for n in names if f"EPSG_32737_{year}_06_30" in n]

def tiles(year):
    x0, y0, x1, y1 = box_utm()
    for m in manifests(year):
        d = json.load(urllib.request.urlopen(f"{GCS}/{m}", timeout=120))
        pre = d["uriPrefix"].replace("gs://open-buildings-temporal-data", GCS)
        for s in d["tilesets"][0]["sources"]:
            a = s["affineTransform"]; w, h = s["dimensions"]["width"], s["dimensions"]["height"]
            tx0, ty1 = a["translateX"], a["translateY"]; tx1, ty0 = tx0 + w * a["scaleX"], ty1 + h * a["scaleY"]
            if tx0 < x1 and tx1 > x0 and ty0 < y1 and ty1 > y0:
                yield pre + s["uris"][0]

def run(year):
    x0, y0, x1, y1 = box_utm()
    res = 0.5
    W, H = int((x1 - x0) / res), int((y1 - y0) / res)
    out = np.full((3, H, W), -99.0, dtype=np.float32)
    dst_tr = Affine(res, 0, x0, 0, -res, y1)
    found = 0
    for url in tiles(year):
        found += 1
        with rasterio.open("/vsicurl/" + url) as s:
            ix0, iy0 = max(x0, s.bounds.left), max(y0, s.bounds.bottom)
            ix1, iy1 = min(x1, s.bounds.right), min(y1, s.bounds.top)
            win = from_bounds(ix0, iy0, ix1, iy1, s.transform).round_offsets().round_lengths()
            a = s.read(window=win).astype(np.float32)
            c0, r0 = int(round((ix0 - x0) / res)), int(round((y1 - iy1) / res))
            out[:, r0:r0 + a.shape[1], c0:c0 + a.shape[2]] = a[:, :H - r0, :W - c0]
    if not found:
        print(year, "no tiles"); return
    OUT.mkdir(parents=True, exist_ok=True)
    with rasterio.open(OUT / f"{year}.tif", "w", driver="GTiff", width=W, height=H, count=3, dtype="float32",
                       crs="EPSG:32737", transform=dst_tr, nodata=-99.0, compress="deflate", predictor=3, tiled=True) as o:
        o.write(out); o.descriptions = ("building_fractional_count", "building_height", "building_presence")
    print(year, found, "tiles")

if __name__ == "__main__":
    for y in (sys.argv[1:] or range(2016, 2024)):
        run(int(y))
