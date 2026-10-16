"""W1: Overture Maps (release in _overture.REL) for the 3 km box.

Overture merges OpenStreetMap (ODbL), Google Open Buildings and Microsoft footprints
(CDLA/ODbL), and other sources. It stands in for direct OSM downloads, which this
environment cannot reach. Each feature keeps its `sources` so licence and origin stay
traceable. Output: gis/raw/overture/<theme>_<type>.gpkg in EPSG:32737.
"""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from _overture import read, REL
from _aoi import box_lonlat, CRS

OUT = Path(__file__).resolve().parents[1] / "raw" / "overture"
LAYERS = [("buildings", "building"), ("buildings", "building_part"), ("transportation", "segment"),
          ("base", "land_use"), ("base", "infrastructure"), ("base", "land"), ("base", "water"),
          ("places", "place")]

def flat(g):
    for c in g.columns:
        if c != "geometry" and g[c].dtype == object:
            g[c] = g[c].apply(lambda v: v if v is None or isinstance(v, str) else json.dumps(v, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)))
    return g

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    bb = box_lonlat()
    for theme, typ in LAYERS:
        g = read(theme, typ, bb).to_crs(CRS)
        flat(g).to_file(OUT / f"{theme}_{typ}.gpkg", driver="GPKG")
        print(theme, typ, len(g))
    (OUT / "RELEASE.txt").write_text(f"Overture Maps release {REL}, bbox lon/lat {bb}\n")
