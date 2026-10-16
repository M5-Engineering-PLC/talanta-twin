"""W2 (first pass): near-ring layers from the W1 downloads, all in EPSG:32737.

- derived/near_ring_buildings.gpkg: Overture footprints in the 3 km box, minus the bowl,
  with a height. Height comes from Open Buildings 2.5D Temporal 2023 (median of the 0.5 m
  height raster inside the footprint), else OSM num_floors x 3.2 m, else a default by area.
  `height_src` says which. The 2023 epoch predates Talanta works.
- derived/roads.gpkg: road and rail segments with class, name and surface.
- derived/heightmap_*.png: 16-bit heightmaps from GLO-30, with a JSON sidecar for scale.
"""
import json, sys
from pathlib import Path
import numpy as np, geopandas as gpd, rasterio
from rasterio.features import rasterize
from PIL import Image
sys.path.insert(0, str(Path(__file__).parent))
from _aoi import box_utm

ROOT = Path(__file__).resolve().parents[1]; RAW = ROOT / "raw"; OUT = ROOT / "derived"

def first(js, key):
    try:
        v = json.loads(js) if isinstance(js, str) else js
        return v.get(key) if isinstance(v, dict) else v[0].get(key)
    except Exception:
        return None

def buildings():
    b = gpd.read_file(RAW / "overture" / "buildings_building.gpkg")
    bowl = gpd.read_file(OUT / "bowl_outline_s2.geojson").to_crs(b.crs).geometry[0]
    b = b[~b.intersects(bowl)].copy()
    b["dataset"] = b.sources.apply(lambda s: first(s, "dataset"))
    b["name"] = b.names.apply(lambda s: first(s, "primary"))
    h = np.full(len(b), np.nan)
    obt = RAW / "open_buildings_temporal" / "2023.tif"
    if obt.exists():
        with rasterio.open(obt) as s:
            hgt = s.read(2); pres = s.read(3)
            ids = rasterize(((g, i + 1) for i, g in enumerate(b.geometry)), out_shape=hgt.shape,
                            transform=s.transform, fill=0, dtype="int32")
        ok = (ids > 0) & (pres > 0.5) & (hgt > 0)
        idx, val = ids[ok] - 1, hgt[ok]
        order = np.argsort(idx); idx, val = idx[order], val[order]
        cuts = np.flatnonzero(np.diff(idx)) + 1
        for grp_i, grp_v in zip(np.split(idx, cuts), np.split(val, cuts)):
            if len(grp_i): h[grp_i[0]] = np.median(grp_v)
    src = np.where(~np.isnan(h), "open_buildings_2023", "")
    fl = b.num_floors.to_numpy(dtype=float)
    use = np.isnan(h) & ~np.isnan(fl); h[use] = fl[use] * 3.2; src[use] = "osm_floors"
    rest = np.isnan(h); area = b.area.to_numpy()
    h[rest] = np.where(area[rest] > 600, 9.0, 4.0); src[rest] = "default_by_area"
    b["height_m"] = np.round(h, 1); b["height_src"] = src
    keep = ["id", "name", "class", "dataset", "height_m", "height_src", "geometry"]
    b[keep].to_file(OUT / "near_ring_buildings.gpkg", driver="GPKG")
    print("buildings", len(b), dict(zip(*np.unique(src, return_counts=True))))

def roads():
    r = gpd.read_file(RAW / "overture" / "transportation_segment.gpkg")
    r["name"] = r.names.apply(lambda s: first(s, "primary"))
    r["surface"] = r.road_surface.apply(lambda s: first(s, "value"))
    r[["id", "subtype", "class", "name", "surface", "geometry"]].to_file(OUT / "roads.gpkg", driver="GPKG")
    print("roads", len(r))

def heightmaps():
    for f in sorted((RAW / "dem").glob("*.tif")):
        with rasterio.open(f) as s:
            a = s.read(1); b = s.bounds
        lo, hi = float(a.min()), float(a.max())
        Image.fromarray(np.round((a - lo) / (hi - lo) * 65535).astype(np.uint16)).save(OUT / f"heightmap_{f.stem}.png")
        (OUT / f"heightmap_{f.stem}.json").write_text(json.dumps(dict(
            crs="EPSG:32737", bounds=[b.left, b.bottom, b.right, b.top], min_m=round(lo, 2), max_m=round(hi, 2),
            pixel_m=round((b.right - b.left) / a.shape[1], 2), source="Copernicus GLO-30 DSM (2011-2015), bilinear",
            note="DSM: includes trees and buildings; predates the stadium"), indent=1))
        print("heightmap", f.stem, a.shape, lo, hi)

if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    roads(); heightmaps(); buildings()
