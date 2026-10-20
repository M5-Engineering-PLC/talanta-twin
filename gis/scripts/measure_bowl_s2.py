"""W4 (partial): measure the stadium roof ellipse and the construction timeline from the
Sentinel-2 clips in gis/raw/sentinel2 (run fetch_sentinel2.py first).

For each clear scene and three brightness thresholds, take the bright component that
covers the roof ring, fill it, and fit an ellipse from second moments. Report the spread
across scenes and thresholds as the error. 10 m pixels limit this to a check, not a survey.

Outputs: gis/derived/bowl_s2_measurements.csv, gis/derived/bowl_s2_timeline.csv,
gis/derived/bowl_s2_timeline.png, gis/derived/bowl_s2_summary.json, gis/derived/bowl_outline_s2.geojson
"""
import csv, glob, json, sys
from pathlib import Path
import numpy as np, rasterio
from scipy import ndimage as nd
sys.path.insert(0, str(Path(__file__).parent))
from _aoi import centre_utm, CRS

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "derived"
THRESH = (2000, 2500, 3000)  # mean reflectance of B02-B04, scaled x10000
R_MAX = 260  # m from centre that the roof may reach

def load(f):
    with rasterio.open(f) as s:
        a = s.read().astype(float); tr = s.transform
    # Element 84 COGs already remove the +1000 BOA offset (earthsearch:boa_offset_applied).
    vis = a[:3].mean(0)
    rows, cols = np.indices(vis.shape)
    X = tr.c + (cols + 0.5) * tr.a; Y = tr.f + (rows + 0.5) * tr.e
    return vis, X, Y

def fit(vis, X, Y, t):
    cx, cy = centre_utm()
    near = np.hypot(X - cx, Y - cy) < R_MAX
    m = (vis > t) & near
    lab, n = nd.label(m)
    if n == 0: return None
    sizes = nd.sum(m, lab, range(1, n + 1)); k = int(np.argmax(sizes)) + 1
    roof = lab == k
    filled = nd.binary_fill_holes(roof)
    if filled.sum() < 50: return None
    x, y = X[filled], Y[filled]; mx, my = x.mean(), y.mean()
    ev, evec = np.linalg.eigh(np.cov(np.vstack([x - mx, y - my])))
    az = (90 - np.degrees(np.arctan2(evec[1, 1], evec[0, 1]))) % 180
    # Extent along each axis (pixel centres, plus one pixel), for a shape that is not a true ellipse.
    p1 = (x - mx) * evec[0, 1] + (y - my) * evec[1, 1]; p0 = (x - mx) * evec[0, 0] + (y - my) * evec[1, 0]
    return dict(t=t, cx=mx, cy=my, major=4 * np.sqrt(ev[1]), minor=4 * np.sqrt(ev[0]), azimuth=az,
                extent_major=np.ptp(p1) + 10, extent_minor=np.ptp(p0) + 10,
                filled_m2=filled.sum() * 100, roof_m2=roof.sum() * 100, inner_m2=(filled & ~roof).sum() * 100)

def main():
    OUT.mkdir(exist_ok=True)
    files = sorted(glob.glob(str(ROOT / "raw" / "sentinel2" / "*.tif")))
    rows, tl = [], []
    cx, cy = centre_utm()
    for f in files:
        date = Path(f).name[:10]
        vis, X, Y = load(f)
        r = np.hypot(X - cx, Y - cy)
        ring = (r > 60) & (r < 130)  # roof band of the final bowl
        tl.append(dict(date=date, ring_bright_frac=round(float((vis[ring] > 2500).mean()), 3),
                       ring_mean_vis=round(float(vis[ring].mean()))))
        for t in THRESH:
            e = fit(vis, X, Y, t)
            if e: rows.append(dict(date=date, **{k: round(v, 2) for k, v in e.items()}))
    with open(OUT / "bowl_s2_measurements.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, list(rows[0])); w.writeheader(); w.writerows(rows)
    with open(OUT / "bowl_s2_timeline.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, list(tl[0])); w.writeheader(); w.writerows(tl)
    # Final geometry: scenes after the roof ring is complete (bright fraction >= 0.8).
    done = {d["date"] for d in tl if d["ring_bright_frac"] >= 0.8}
    fin = [r for r in rows if r["date"] in done and 200 < r["major"] < 330]
    def stat(k):
        v = np.array([r[k] for r in fin]); return dict(median=round(float(np.median(v)), 1),
            p05=round(float(np.percentile(v, 5)), 1), p95=round(float(np.percentile(v, 95)), 1))
    from pyproj import Transformer
    s = {k: stat(k) for k in ["major", "minor", "extent_major", "extent_minor", "azimuth", "cx", "cy", "filled_m2", "inner_m2"]}
    lon, lat = Transformer.from_crs(CRS, "EPSG:4326", always_xy=True).transform(s["cx"]["median"], s["cy"]["median"])
    s.update(centre_lonlat=[round(lon, 6), round(lat, 6)], n_scenes=len(done), n_fits=len(fin),
             first_complete=min(done) if done else None, scenes=sorted(done))
    (OUT / "bowl_s2_summary.json").write_text(json.dumps(s, indent=1))
    # Ellipse outline for overlays (EPSG:32737).
    a, b, th = s["major"]["median"] / 2, s["minor"]["median"] / 2, np.radians(90 - s["azimuth"]["median"])
    u = np.linspace(0, 2 * np.pi, 73)
    px = s["cx"]["median"] + a * np.cos(u) * np.cos(th) - b * np.sin(u) * np.sin(th)
    py = s["cy"]["median"] + a * np.cos(u) * np.sin(th) + b * np.sin(u) * np.cos(th)
    gj = {"type": "FeatureCollection", "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:EPSG::32737"}},
          "features": [{"type": "Feature", "properties": {"source": "Sentinel-2 L2A, ellipse fit", "error_m": "about 10-20"},
                        "geometry": {"type": "Polygon", "coordinates": [[[round(x, 1), round(y, 1)] for x, y in zip(px, py)]]}}]}
    (OUT / "bowl_outline_s2.geojson").write_text(json.dumps(gj))
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, datetime as dt
    d = [dt.date.fromisoformat(x["date"]) for x in tl]
    fig, ax = plt.subplots(figsize=(9, 3.2))
    ax.plot(d, [x["ring_bright_frac"] for x in tl], "o-", ms=3, color="#3b6ea8")
    ax.axvline(dt.date(2024, 3, 1), color="#999", ls="--", lw=1); ax.text(dt.date(2024, 3, 10), 0.92, "groundbreaking 1 Mar 2024", fontsize=8, color="#555")
    ax.set_ylabel("bright share of roof ring"); ax.set_ylim(0, 1); ax.grid(alpha=.3)
    ax.set_title("Talanta roof ring brightness, Sentinel-2 L2A clear scenes", fontsize=10)
    fig.tight_layout(); fig.savefig(OUT / "bowl_s2_timeline.png", dpi=110)
    print(json.dumps({k: s[k] for k in ["major", "minor", "extent_major", "extent_minor", "inner_m2", "azimuth", "centre_lonlat", "n_scenes", "n_fits", "first_complete"]}, indent=1))

if __name__ == "__main__":
    main()
