"""W1: Sentinel-2 L2A time series for the 3 km box (tile 37MBU) from the public AWS COG bucket.

Lists every scene, scores cloud over the site core with the SCL band, and saves the
10 m bands B02 B03 B04 B08 for clear scenes. Output: gis/raw/sentinel2/<date>.tif and
gis/raw/sentinel2/scenes.csv. Copernicus Sentinel data, free and open; credit required.
"""
import csv, json, sys, urllib.request, re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import numpy as np, rasterio
from rasterio.windows import from_bounds
sys.path.insert(0, str(Path(__file__).parent))
from _aoi import box_utm, gdal_env

gdal_env()
BUCKET = "https://sentinel-cogs.s3.us-west-2.amazonaws.com"
PREFIX = "sentinel-s2-l2a-cogs/37/M/BU"
OUT = Path(__file__).resolve().parents[1] / "raw" / "sentinel2"
CLEAR = {4, 5, 6, 7}  # vegetation, bare, water, unclassified
START = (int(sys.argv[1]) if len(sys.argv) > 1 else 2023)

def ls(prefix):
    out, token = [], ""
    while True:
        u = f"{BUCKET}/?list-type=2&delimiter=/&prefix={prefix}" + (f"&continuation-token={token}" if token else "")
        x = urllib.request.urlopen(u, timeout=60).read().decode()
        out += re.findall(r"<Prefix>([^<]*)</Prefix>", x)[1:]
        m = re.search(r"<NextContinuationToken>([^<]*)", x)
        if not m: return out
        token = urllib.parse.quote(m.group(1))

def scene_dirs():
    for y in range(START, 2027):
        for m in range(1, 13):
            yield from ls(f"{PREFIX}/{y}/{m}/")

def score(d):
    name = d.rstrip("/").split("/")[-1]
    try:
        meta = json.load(urllib.request.urlopen(f"{BUCKET}/{d}{name}.json", timeout=60))
        cc = meta["properties"].get("eo:cloud_cover", 100)
        if cc > 60:
            return dict(scene=name, date=meta["properties"]["datetime"][:10], tile_cloud=cc, site_clear=None)
        with rasterio.open(f"/vsicurl/{BUCKET}/{d}SCL.tif") as s:
            a = s.read(1, window=from_bounds(*box_utm(500), s.transform))
        clear = float(np.isin(a, list(CLEAR)).mean())
        return dict(scene=name, date=meta["properties"]["datetime"][:10], tile_cloud=cc, site_clear=round(clear, 3))
    except Exception as e:
        return dict(scene=name, date="", tile_cloud=None, site_clear=None, error=str(e)[:80])

def save(row):
    d = f"{PREFIX}/{int(row['date'][:4])}/{int(row['date'][5:7])}/{row['scene']}/"
    dst = OUT / f"{row['date']}_{row['scene']}.tif"
    if dst.exists(): return
    bands = []
    for b in ["B02", "B03", "B04", "B08"]:
        with rasterio.open(f"/vsicurl/{BUCKET}/{d}{b}.tif") as s:
            w = from_bounds(*box_utm(), s.transform).round_offsets().round_lengths()
            bands.append(s.read(1, window=w)); tr = s.window_transform(w); crs = s.crs
    with rasterio.open(dst, "w", driver="GTiff", width=bands[0].shape[1], height=bands[0].shape[0],
                       count=4, dtype=bands[0].dtype, crs=crs, transform=tr, compress="deflate") as o:
        for i, a in enumerate(bands, 1): o.write(a, i)
        o.descriptions = ("B02", "B03", "B04", "B08")

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    dirs = list(scene_dirs()); print(len(dirs), "scenes")
    with ThreadPoolExecutor(16) as ex: rows = list(ex.map(score, dirs))
    rows.sort(key=lambda r: r["scene"])
    with open(OUT / "scenes.csv", "w", newline="") as f:
        w = csv.DictWriter(f, ["scene", "date", "tile_cloud", "site_clear", "error"]); w.writeheader(); w.writerows(rows)
    good = [r for r in rows if r.get("site_clear") and r["site_clear"] >= 0.98]
    print(len(good), "clear scenes over site")
    with ThreadPoolExecutor(8) as ex: list(ex.map(save, good))
