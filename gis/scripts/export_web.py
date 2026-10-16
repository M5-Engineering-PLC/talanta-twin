"""Export the geodata to compact files for the three.js app (app/public/data/).

Local frame: origin at the pitch centre from W1b (measurements/pitch_zone_w1b_*.csv),
x = east (m), z = south (m), y = up (m, relative to the ground at the origin).
Writes binary meshes (little-endian Float32 / Uint32) and a manifest.json.
"""
import glob, json, sys
from pathlib import Path
import numpy as np, geopandas as gpd, pandas as pd, rasterio, shapely
from rasterio.windows import from_bounds
from rasterio.enums import Resampling
from scipy import ndimage as nd
sys.path.insert(0, str(Path(__file__).parent))
from _aoi import gdal_env, CRS
gdal_env()

ROOT = Path(__file__).resolve().parents[1]; RAW = ROOT / "raw"; DER = ROOT / "derived"
OUT = ROOT.parent / "app" / "public" / "data"
S2 = "/vsicurl/https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/37/M/BU/"

def wgs_poly(csv):
    d = pd.read_csv(ROOT / "measurements" / csv)
    return gpd.GeoSeries([shapely.Polygon(zip(d.lon, d.lat))], crs=4326).to_crs(CRS)[0]

PITCH = wgs_poly("pitch_zone_w1b_2026-10-16.csv")
SITE = wgs_poly("site_boundary_w1b_2026-10-16.csv")
OX, OY = PITCH.centroid.x, PITCH.centroid.y

def loc(x, y):  # UTM -> local x, z
    return np.asarray(x) - OX, -(np.asarray(y) - OY)

def ring(g):
    x, y = np.array(g.coords).T; lx, lz = loc(x, y)
    return [[round(float(a), 2), round(float(b), 2)] for a, b in zip(lx, lz)]

# ---------- terrain ----------
class Grid:
    def __init__(self, f, sigma, name):
        with rasterio.open(f) as s:
            self.h = nd.gaussian_filter(s.read(1).astype(np.float64), sigma); self.tr = s.transform; self.b = s.bounds
        self.name = name
    def sample(self, x, y):
        c, r = ~self.tr * (np.asarray(x), np.asarray(y))
        return nd.map_coordinates(self.h, [r - 0.5, c - 0.5], order=1, mode="nearest")

site = Grid(RAW / "dem" / "glo30_site_3km_10m.tif", 2.5, "site")
GROUND0 = float(site.sample([OX], [OY])[0])
# Grade the stadium plot: the 2011-15 DSM predates the works.
pad = float(np.median(site.sample(*np.array(SITE.exterior.coords).T)))

def plot_mask(grid, buffer_m=0):
    rows, cols = np.indices(grid.h.shape)
    X = grid.tr.c + (cols + 0.5) * grid.tr.a; Y = grid.tr.f + (rows + 0.5) * grid.tr.e
    return shapely.contains_xy(SITE.buffer(buffer_m), X, Y), X, Y

def terrain_file(grid, name, flatten):
    h = grid.h.copy()
    if flatten:
        inner, X, Y = plot_mask(grid); d = shapely.distance(SITE, shapely.points(X, Y))
        w = np.clip(1 - d / 60, 0, 1); w[inner] = 1
        h = h * (1 - w) + pad * w
    hh = (h - GROUND0).astype(np.float32)
    hh.tofile(OUT / f"terrain_{name}.bin")
    x0, z0 = loc(grid.b.left, grid.b.top)
    return dict(file=f"terrain_{name}.bin", nx=h.shape[1], nz=h.shape[0], x0=float(x0), z0=float(z0),
                dx=grid.tr.a, dz=-grid.tr.e, min=float(hh.min()), max=float(hh.max()))

def site_h(x, y):  # graded site heights relative to origin
    x = np.asarray(x); y = np.asarray(y); h = site.sample(x, y)
    d = shapely.distance(SITE, shapely.points(x, y)); w = np.clip(1 - d / 60, 0, 1)
    w[shapely.contains_xy(SITE, x, y)] = 1
    return h * (1 - w) + pad * w - GROUND0

# ---------- ground colour ----------
def ground_colour(half, res, name, scenes):
    from _aoi import box_utm
    b = (OX - half, OY - half, OX + half, OY + half); n = int(2 * half / res)
    stack = []
    for sc in scenes:
        y, m = sc[10:14], int(sc[14:16])
        with rasterio.open(f"{S2}{y}/{m}/{sc}/TCI.tif") as s:
            stack.append(s.read(window=from_bounds(*b, s.transform), out_shape=(3, n, n), resampling=Resampling.average).astype(float))
    a = np.median(np.stack(stack), 0)
    a = nd.gaussian_filter(a, (0, 0.8, 0.8))
    # Stylise: lift shadows, warm the mids, compress saturation slightly (painted-relief look).
    a = a / 255.0; lum = a.mean(0, keepdims=True)
    a = lum + (a - lum) * 0.8
    a = np.clip(a * 1.12 + 0.05, 0, 1) ** 0.92
    a[0] *= 1.02; a[2] *= 0.97
    from PIL import Image
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8).transpose(1, 2, 0)).save(OUT / f"ground_{name}.jpg", quality=88)
    x0, z0 = loc(b[0], b[3])
    return dict(file=f"ground_{name}.jpg", x0=float(x0), z0=float(z0), size=2 * half)

LATE = ["S2A_37MBU_20261001_0_L2A", "S2B_37MBU_20260924_0_L2A", "S2C_37MBU_20260919_0_L2A", "S2B_37MBU_20260904_0_L2A", "S2C_37MBU_20260909_0_L2A"]

# ---------- meshes ----------
def tri_poly(p):
    t = shapely.constrained_delaunay_triangles(p)
    out = []
    for g in t.geoms:
        c = np.array(g.exterior.coords)[:3]; out.append(c)
    return out

def buildings():
    b = gpd.read_file(DER / "near_ring_buildings.gpkg")
    b = b[~b.intersects(SITE)]
    pos, col, idx = [], [], []; n = 0
    rng = np.random.default_rng(7)
    base_h = site_h(b.geometry.centroid.x, b.geometry.centroid.y)
    for (g, h, src), y0 in zip(zip(b.geometry, b.height_m, b.height_src), base_h):
        for p in getattr(g, "geoms", [g]):
            p = p.simplify(0.4)
            if p.is_empty or p.area < 8: continue
            top = y0 + max(float(h), 2.5)
            tone = rng.uniform(0.86, 1.0)
            roof = np.array([0.80, 0.76, 0.70]) * tone if h < 12 else np.array([0.86, 0.85, 0.83]) * tone
            wall = roof * 0.9
            for c in tri_poly(p):
                lx, lz = loc(c[:, 0], c[:, 1])
                for i in (0, 2, 1):  # winding for +y normal with z = south
                    pos.append((lx[i], top, lz[i])); col.append(roof)
                idx += [n, n + 1, n + 2]; n += 3
            for rg in [p.exterior] + list(p.interiors):
                c = np.array(rg.coords); lx, lz = loc(c[:, 0], c[:, 1])
                for i in range(len(c) - 1):
                    q = [(lx[i], y0 - 1, lz[i]), (lx[i + 1], y0 - 1, lz[i + 1]), (lx[i + 1], top, lz[i + 1]), (lx[i], top, lz[i])]
                    pos += q; col += [wall * 0.8, wall * 0.8, wall, wall]
                    idx += [n, n + 2, n + 1, n, n + 3, n + 2]; n += 4
    np.array(pos, np.float32).tofile(OUT / "buildings_pos.bin")
    (np.array(col) * 255).astype(np.uint8).tofile(OUT / "buildings_col.bin")
    np.array(idx, np.uint32).tofile(OUT / "buildings_idx.bin")
    print("buildings", len(b), "verts", n)
    return dict(pos="buildings_pos.bin", col="buildings_col.bin", idx="buildings_idx.bin", count=len(b))

WIDTH = dict(trunk=16, primary=14, secondary=12, tertiary=9, residential=6, unclassified=6, service=4,
             living_street=5, pedestrian=4, footway=2, path=1.5, cycleway=2, track=3, steps=2, unknown=4)

def roads():
    r = gpd.read_file(DER / "roads.gpkg"); r = r[r.subtype == "road"]
    out = []
    for cls, grp in r.groupby("class"):
        w = WIDTH.get(cls, 4); poly = shapely.union_all(grp.geometry.buffer(w / 2, cap_style="flat")).simplify(0.5)
        out.append((cls, w, poly))
    pos, idx = [], []; n = 0; cls_id = []
    order = sorted(out, key=lambda t: t[1])
    for k, (cls, w, poly) in enumerate(order):
        for p in getattr(poly, "geoms", [poly]):
            for c in tri_poly(p):
                ys = site_h(c[:, 0], c[:, 1]) + 0.25 + 0.02 * k
                lx, lz = loc(c[:, 0], c[:, 1])
                for i in (0, 2, 1): pos.append((lx[i], ys[i], lz[i])); cls_id.append(w)
                idx += [n, n + 1, n + 2]; n += 3
    np.array(pos, np.float32).tofile(OUT / "roads_pos.bin"); np.array(cls_id, np.float32).tofile(OUT / "roads_w.bin")
    np.array(idx, np.uint32).tofile(OUT / "roads_idx.bin"); print("roads verts", n)
    named = r[r.name.notna()]; labels = []
    for nm, grp in named.groupby("name"):
        L = shapely.line_merge(shapely.union_all(grp.geometry)); 
        if L.length < 400: continue
        p = L.interpolate(0.5, normalized=True); lx, lz = loc(p.x, p.y)
        labels.append(dict(text=nm, x=round(float(lx), 1), z=round(float(lz), 1), y=float(site_h([p.x], [p.y])[0]) + 2, kind="road"))
    return dict(pos="roads_pos.bin", idx="roads_idx.bin", w="roads_w.bin"), labels

def trees():
    from _aoi import box_utm
    files = sorted(glob.glob(str(RAW / "sentinel2" / "2026-*.tif")))[-6:]
    st = []
    for f in files:
        with rasterio.open(f) as s: a = s.read().astype(float); tr = s.transform
        st.append((a[3] - a[2]) / (a[3] + a[2] + 1e-6))
    ndvi = np.median(np.stack(st), 0)
    rows, cols = np.nonzero(ndvi > 0.55)
    X = tr.c + (cols + 0.5) * tr.a; Y = tr.f + (rows + 0.5) * tr.e
    v = ndvi[rows, cols]
    rng = np.random.default_rng(3)
    reps = np.clip(((v - 0.5) * 6).astype(int) + 1, 1, 3)
    X = np.repeat(X, reps) + rng.uniform(-5, 5, reps.sum()); Y = np.repeat(Y, reps) + rng.uniform(-5, 5, reps.sum())
    keep = ~shapely.contains_xy(SITE.buffer(-15), X, Y)
    bl = shapely.union_all(gpd.read_file(DER / "near_ring_buildings.gpkg").geometry.buffer(2))
    rd = shapely.union_all(gpd.read_file(DER / "roads.gpkg").geometry.buffer(5))
    keep &= ~shapely.contains_xy(bl, X, Y) & ~shapely.contains_xy(rd, X, Y)
    X, Y = X[keep], Y[keep]; H = site_h(X, Y); lx, lz = loc(X, Y)
    s = rng.uniform(0.7, 1.35, len(X))
    np.stack([lx, H, lz, s], 1).astype(np.float32).tofile(OUT / "trees.bin"); print("trees", len(X))
    return dict(file="trees.bin", count=int(len(X)))

def features():
    ob = gpd.read_file(RAW / "overture" / "buildings_building.gpkg")
    bowl = ob[ob.contains(PITCH.centroid.buffer(1)) | ob.intersects(PITCH.buffer(60))]
    bowl = bowl.assign(a=bowl.area).sort_values("a").iloc[-1].geometry
    lu = gpd.read_file(RAW / "overture" / "base_land_use.gpkg")
    sport = lu[lu["class"].isin(["pitch", "track"]) & lu.intersects(SITE) & ~lu.intersects(PITCH.centroid)]
    pitches = [dict(kind=r["class"], ring=ring(g.exterior), area=round(g.area))
               for _, r in sport.iterrows() for g in getattr(r.geometry, "geoms", [r.geometry])]
    xs, ys = np.array(PITCH.exterior.coords).T
    ang = np.degrees(np.arctan2(*(np.array([xs[1] - xs[0], ys[1] - ys[0]])))) % 180
    return dict(bowl_outer=ring(bowl.exterior), bowl_hole=ring(bowl.interiors[0]) if len(bowl.interiors) else None,
                pitch_zone=ring(PITCH.exterior), pitch_bearing_deg=round(float(ang), 2), site=ring(SITE.exterior),
                sport=pitches, site_pad_y=round(pad - GROUND0, 2))

def place_labels():
    out = []
    fixed = [("Ngong Road Forest Sanctuary", 36.7420, -1.3120, "area"), ("Ngong Racecourse", 36.7340, -1.3115, "area"),
             ("Kibera", 36.7830, -1.3130, "area"), ("Jamhuri Park", 36.7650, -1.3075, "area"),
             ("Kilimani", 36.7840, -1.2890, "area"), ("Nairobi CBD", 36.8219, -1.2864, "far"),
             ("Ngong Hills · Lamwia", 36.6386, -1.4203, "peak"), ("Ngong Hills", 36.6377, -1.3968, "peak"),
             ("Ngong", 36.6620, -1.3540, "far"), ("Wilson Airport", 36.8148, -1.3217, "far")]
    # Summits found as local maxima of GLO-30 in the horizon clip (2,441 m and 2,385 m).
    from pyproj import Transformer
    t = Transformer.from_crs(4326, CRS, always_xy=True)
    hz = Grid(RAW / "dem" / "glo30_horizon_40km_100m.tif", 0, "h")
    for nm, lon, lat, k in fixed:
        x, y = t.transform(lon, lat); lx, lz = loc(x, y)
        h = float(hz.sample([x], [y])[0]); out.append(dict(text=nm, x=round(float(lx)), z=round(float(lz)), y=round(h - GROUND0 + 15), kind=k, elev=round(h)))
    return out

if __name__ == "__main__" and sys.argv[1:] == ["ground"]:
    m = json.loads((OUT / "manifest.json").read_text())
    m["ground"] = [ground_colour(1500, 5, "site", LATE), ground_colour(6000, 20, "far", LATE[:3]), ground_colour(20000, 80, "horizon", LATE[:3])]
    (OUT / "manifest.json").write_text(json.dumps(m)); sys.exit()

if __name__ == "__main__" and sys.argv[1:] == ["labels"]:
    m = json.loads((OUT / "manifest.json").read_text())
    m["labels"] = [l for l in m["labels"] if l["kind"] == "road"] + place_labels()
    (OUT / "manifest.json").write_text(json.dumps(m)); print([l for l in m["labels"] if l["kind"] == "peak"]); sys.exit()

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    m = dict(origin_utm=[round(OX, 2), round(OY, 2)], crs=CRS, ground_elev_m=round(GROUND0, 1),
             origin_lonlat=None, sources={})
    from pyproj import Transformer
    lon, lat = Transformer.from_crs(CRS, 4326, always_xy=True).transform(OX, OY); m["origin_lonlat"] = [round(lon, 6), round(lat, 6)]
    m["terrain"] = [terrain_file(site, "site", True),
                    terrain_file(Grid(RAW / "dem" / "glo30_far_12km_30m.tif", 1.2, "far"), "far", False),
                    terrain_file(Grid(RAW / "dem" / "glo30_horizon_40km_100m.tif", 0.8, "hz"), "horizon", False)]
    m["ground"] = [ground_colour(1500, 5, "site", LATE), ground_colour(6000, 20, "far", LATE[:3]), ground_colour(20000, 80, "horizon", LATE[:3])]
    m["buildings"] = buildings()
    m["roads"], road_labels = roads()
    m["trees"] = trees()
    m["features"] = features()
    m["labels"] = road_labels + place_labels()
    m["timeline"] = pd.read_csv(DER / "bowl_s2_timeline.csv").to_dict("records")
    (OUT / "manifest.json").write_text(json.dumps(m))
    print("done", m["ground_elev_m"], m["origin_lonlat"])
