"""Stage 03 (detail sheets RF and SR): finished-state site plan for the Blender build.

Lead review of the detail sheets (engineering/detail_sheets/00_README_and_lead_review.md): build the finished
landscape, not the construction site. Treatment comes from the physical design model (JWNowpO44rw 04:45, 05:12,
05:16) and the lead renders 06 and 07 as look references; positions come from the W1b outlines and OSM only.
Every layout value here is "estimated (detail sheet <id>)" or "estimated (design model)" in the ledger.
No gates, exits, security cameras or control rooms (AGENTS.md rule 8): entrances are generic canopies and paving.

Writes, in the local twin frame (x east, z south, origin = W1b pitch centre):
- blender/textures/site_regions.png, 0.5 m/px over +-700 m. R = lawn, G = paving, B = planting beds.
- blender/textures/site_regions2.png, same grid. R = paving edge band (SR03), G = wet jet deck (SR13), B = parking asphalt.
- blender/textures/site_regions3.png, same grid. R = entrance apron beside the plinth (SR06).
- blender/data/site_plan.json: Ngong Road median line, paths, palms, trees, shrubs, planters, masts, lights,
  bollards, jets, canopies, sign frames, fence, parking bays, tracks and the SE pitch.
- blender/data/road_lines.json: trunk to tertiary centrelines within 1.5 km (now with names), for lane dashes.
Run: ~/.venvs/gis/bin/python gis/scripts/export_site_plan.py
"""
import csv, json, math
from pathlib import Path
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon, LineString, Point, MultiLineString
from shapely.ops import linemerge, unary_union
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
NORM = ROOT / "gis/measurements/normalized"
L = {r["name"]: r for r in csv.DictReader(open(ROOT / "gis/parameter_ledger.csv"))}
V = lambda k: float(L[k]["value"])
OX, OY = json.loads((ROOT / "app/public/data/manifest.json").read_text())["origin_utm"]
HALF, RES = 700, 0.5
rng = np.random.default_rng(23)


def ring(fn):
    return [(float(r["x_east"]), float(r["z_south"])) for r in csv.DictReader(open(NORM / fn))]


site = Polygon(ring("site_boundary_w1b_2026-10-16.csv"))
plinth = Polygon(ring("bowl_plinth_design_2026-10-17.csv"))  # design plan (fit_design_plan.py)
plaza = Polygon(ring("north_plaza_w1b_2026-10-17.csv"))
track_ne = Polygon(ring("warmup_track_w1b_2026-10-17.csv"))
track_sw = Polygon(ring("training_pitch_sw_w1b_2026-10-17.csv"))
pitch_se = Polygon(ring("training_pitch_se_w1b_2026-10-17.csv"))
conc = plinth.buffer(V("bowl.ground.concourse_w"), join_style="round").intersection(site)
b = math.radians(V("pitch.bearing"))
NAX = np.array([math.sin(b), -math.cos(b)])  # north along the pitch axis, in (x, z)
EAX = np.array([math.cos(b), math.sin(b)])   # across, to the east
def local(along, across):
    p = NAX * along + EAX * across; return float(p[0]), float(p[1])
def ray_r(poly, d):
    far = LineString([(0, 0), (d[0] * 2000, d[1] * 2000)]); x = far.intersection(poly.exterior)
    pts = [x] if x.geom_type == "Point" else list(getattr(x, "geoms", []))
    return max(math.hypot(p.x, p.y) for p in pts)
rN = ray_r(plinth, NAX)

# ---------------------------------------------------------------- roads from OSM
R = gpd.read_file(ROOT / "gis/derived/roads.gpkg"); R = R[R.subtype == "road"]
def loc_line(g):
    return [LineString([(x - OX, -(y - OY)) for x, y in p.coords]) for p in getattr(g, "geoms", [g])]
ngong = [l for nm, g in zip(R["name"], R.geometry) if str(nm) == "Ngong Road" for l in loc_line(g)]
ngong = [l for l in ngong if l.distance(Point(0, 0)) < 1700]
service = [l for c, g in zip(R["class"], R.geometry) if c == "service" for l in loc_line(g)]
site_roads = [l for l in service + [l for c, g in zip(R["class"], R.geometry) if c in ("tertiary", "unclassified") for l in loc_line(g)] if l.intersects(site.buffer(30))]
road_buf = unary_union([l.buffer(5) for l in site_roads])

# Ngong Road median (SR19-SR23 under lead correction 3, frame 07:04): OSM maps the two carriageways as separate
# ways; the median is the midpoint between them, sampled every 5 m and smoothed.
m = linemerge(unary_union(ngong)); parts = sorted(getattr(m, "geoms", [m]), key=lambda g: -g.length)
A, B = parts[0], parts[1]
mid = []
for s in np.arange(0, A.length, 5.0):
    p = A.interpolate(s); q = B.interpolate(B.project(p))
    if p.distance(q) < 45: mid.append(((p.x + q.x) / 2, (p.y + q.y) / 2))
mid = np.array(mid)
if np.hypot(*(mid[0] - mid[-1])) and mid[0, 0] > mid[-1, 0]: mid = mid[::-1]
k = 5; sm = np.array([mid[max(0, i - k):i + k + 1].mean(0) for i in range(len(mid))])
sm = sm[np.hypot(sm[:, 0], sm[:, 1]) < 1500]
ngong_mid = LineString(sm)
NG = {k_: V(f"ngong.{k_}") for k_ in ("lanes_per_dir", "lane_w", "median_w", "edge_strip_w", "kerb_w", "drain_w", "footpath_w", "service_w")}
ng_half_cw = NG["median_w"] / 2 + NG["lanes_per_dir"] * NG["lane_w"] + NG["edge_strip_w"]
ng_half = ng_half_cw + NG["kerb_w"] + NG["drain_w"] + NG["footpath_w"] + NG["service_w"]
ngong_buf = ngong_mid.buffer(ng_half + 1)

# ---------------------------------------------------------------- sport and parking (obstacles for paths and trees)
def rect_of(poly):
    r = poly.minimum_rotated_rectangle; c = list(r.exterior.coords)[:4]
    e = [(c[(i + 1) % 4][0] - c[i][0], c[(i + 1) % 4][1] - c[i][1]) for i in range(2)]
    lens = [math.hypot(*v) for v in e]; li = int(np.argmax(lens)); ax = e[li]
    return {"c": [r.centroid.x, r.centroid.y], "L": max(lens), "W": min(lens), "axis": [ax[0] / lens[li], ax[1] / lens[li]]}
tracks = [dict(rect_of(track_ne), name="warmup_track_ne"), dict(rect_of(track_sw), name="track_sw")]
pse = dict(rect_of(pitch_se), name="training_pitch_se")
lots = []
from shapely.geometry import box as sbox
for bx in [sbox(280, -200, 410, -45), sbox(350, -30, 470, 80)]:  # the two OSM parking-aisle groups east of the warm-up track
    segs = [l.intersection(bx) for l in service if l.intersects(bx) and l.intersection(bx).length > 15 and not l.is_ring]
    segs = [g for s_ in segs for g in getattr(s_, "geoms", [s_]) if g.geom_type == "LineString"]
    hull = unary_union(segs).convex_hull.buffer(3, join_style="mitre")
    lots.append({"poly": hull, "aisles": segs})
park = unary_union([l["poly"] for l in lots])
sport = unary_union([track_ne, track_sw, pitch_se]).buffer(6)
obst = unary_union([sport, park.buffer(4), road_buf, ngong_buf])

# ---------------------------------------------------------------- forecourt paving and paths (design model, 06)
FW = V("site.forecourt.width"); plazaC = rN + V("site.plaza.offset")
band = Polygon([local(rN - 10, -FW / 2), local(rN - 10, FW / 2), local(plazaC, FW / 2), local(plazaC, -FW / 2)])
paths = []  # {"pts", "w", "kind"}
# main avenue from the plaza to the Ngong Road footpath, and two diagonals from the plaza corners (SR04, 06)
foot_edge = ngong_mid.buffer(ng_half_cw + NG["kerb_w"] + NG["drain_w"] + NG["footpath_w"])
def to_road(p0, d, w, kind):
    ray = LineString([p0, (p0[0] + d[0] * 400, p0[1] + d[1] * 400)])
    x = ray.intersection(foot_edge)
    if x.is_empty: return
    s = ray.project(Point(list(x.coords)[0] if x.geom_type != "MultiLineString" else list(x.geoms[0].coords)[0]))
    paths.append({"pts": [list(p0), [p0[0] + d[0] * s, p0[1] + d[1] * s]], "w": w, "kind": kind})
pN = local(plazaC + 40, 0)
to_road(pN, NAX, V("site.avenue.w"), "avenue")
for sg in (-1, 1):
    d = NAX * math.cos(math.radians(40)) + EAX * sg * math.sin(math.radians(40))
    to_road(local(plazaC + 25, sg * 40), d, V("site.path.radial_w"), "diagonal")
# radial walks round the bowl, 16 bearings, kept from the concourse edge to the first obstacle (SR04)
rc = ray_r(conc, NAX)
for kk in range(16):
    a = 2 * math.pi * (kk + 0.5) / 16; d = NAX * math.cos(a) + EAX * math.sin(a)
    r0 = ray_r(conc, d) - 2
    seg = LineString([(d[0] * r0, d[1] * r0), (d[0] * 900, d[1] * 900)]).intersection(site.buffer(-10))
    seg = getattr(seg, "geoms", [seg])[0] if not seg.is_empty else seg
    if seg.is_empty: continue
    cut = seg.difference(unary_union([obst, plaza.buffer(5), band.buffer(5)]))
    cut = [g for g in getattr(cut, "geoms", [cut]) if not g.is_empty]
    if not cut: continue
    g = min(cut, key=lambda g: Point(0, 0).distance(g))
    if g.length > 25 and Point(0, 0).distance(g) < r0 + 3: paths.append({"pts": [list(c) for c in g.coords], "w": V("site.path.radial_w"), "kind": "radial"})
# curved walk on a ring round the bowl (SR05)
ringp = plinth.buffer(V("site.path.ring_offset"), join_style="round").exterior
cut = ringp.difference(unary_union([obst, plaza.buffer(4), band.buffer(4)]))
for g in getattr(cut, "geoms", [cut]):
    if g.length > 30: paths.append({"pts": [list(c) for c in g.simplify(0.5).coords], "w": V("site.path.ring_w"), "kind": "ring"})
path_poly = unary_union([LineString(p["pts"]).buffer(p["w"] / 2, cap_style="flat") for p in paths])
# jet deck (SR11-SR13: frames show jets across a paved apron, no basin; lead rule 9 keeps the frame reading)
poolC = rN + V("site.pool.offset"); PL_, PW_ = V("site.pool.length"), V("site.pool.width")
deck = Polygon([local(poolC - PW_ / 2, -PL_ / 2), local(poolC - PW_ / 2, PL_ / 2), local(poolC + PW_ / 2, PL_ / 2), local(poolC + PW_ / 2, -PL_ / 2)])
jets = []
for row in (-V("site.jets.row_offset"), V("site.jets.row_offset")):
    n = int(V("site.jets.per_row"))
    for i in range(n): jets.append(local(poolC + row, -PL_ / 2 + 3 + i * (PL_ - 6) / (n - 1)))
# entrance aprons with generic canopies at the plaza's road side (SR48, SR49, SR51; no layout detail)
canopies, aprons = [], []
for sg in (-1, 1):
    c = local(plazaC + 52, sg * 28); canopies.append([c[0], c[1], math.degrees(b)])
    aprons.append(Point(c).buffer(16, join_style="mitre"))
pave = unary_union([conc, plaza, band.intersection(site), path_poly, deck] + aprons).difference(park).intersection(site.union(foot_edge))
# planting beds alongside the avenue, diagonals and ring walk (design model: red flower beds by the paths; SR08)
beds = unary_union([LineString(p["pts"]).buffer(p["w"] / 2 + 1.2 + V("site.bed.w"), cap_style="flat").difference(LineString(p["pts"]).buffer(p["w"] / 2 + 1.2, cap_style="flat"))
                    for p in paths])
planters = [[*local(plazaC, 0), V("site.planter.r")]]
avenue_lines = [LineString(p["pts"]) for p in paths if p["kind"] in ("avenue", "diagonal", "radial")]
for p in paths:
    if p["kind"] != "ring": continue
    for al in avenue_lines:
        x = LineString(p["pts"]).intersection(al)
        for q in getattr(x, "geoms", [x]):
            if q.geom_type == "Point" and all(math.dist((q.x, q.y), pl[:2]) > 20 for pl in planters): planters.append([q.x, q.y, V("site.planter.r")])
beds = unary_union([beds] + [Point(p[:2]).buffer(p[2] + 2.5).difference(Point(p[:2]).buffer(p[2] + 0.5)) for p in planters[1:]])
beds = beds.difference(pave).difference(obst).intersection(site)
lawn = site.difference(pave).difference(beds).difference(park)

# ---------------------------------------------------------------- planting (design model: palm avenues, clumped broad crowns)
free = lambda x, z, r=1.5: not (obst.contains(Point(x, z)) or pave.buffer(r).contains(Point(x, z)) or not site.contains(Point(x, z)))
def along(line, step, off, start=0.0):
    ls = LineString(line); out = []
    for s in np.arange(start, ls.length, step):
        p = ls.interpolate(s); q = ls.interpolate(min(s + 1, ls.length)); p0 = ls.interpolate(max(s - 1, 0))
        t = np.array([q.x - p0.x, q.y - p0.y]); t /= (np.linalg.norm(t) or 1); nrm = np.array([-t[1], t[0]])
        out.append((p.x + nrm[0] * off, p.y + nrm[1] * off, t))
    return out
palms, pathlights = [], []
for p in paths:
    sp = V("site.palm.spacing") if p["kind"] in ("avenue", "diagonal") else V("site.palm.spacing") * 1.5
    for sg in (-1, 1):
        for x, z, _ in along(p["pts"], sp, sg * (p["w"] / 2 + 2.2), 4.0):
            if not obst.contains(Point(x, z)) and site.buffer(5).contains(Point(x, z)) and not conc.contains(Point(x, z)) and not plaza.contains(Point(x, z)): palms.append([round(x, 2), round(z, 2)])
    for i, (x, z, _) in enumerate(along(p["pts"], V("site.pathlight.spacing"), (p["w"] / 2 + 0.6), 7.0)):
        if i % 2: x, z = 2 * along(p["pts"], V("site.pathlight.spacing"), 0, 7.0)[i][0] - x, 2 * along(p["pts"], V("site.pathlight.spacing"), 0, 7.0)[i][1] - z
        if not obst.contains(Point(x, z)): pathlights.append([round(x, 2), round(z, 2)])
# palms round the concourse edge facing the forecourt (06, 07: a palm ring at the concourse edge)
for x, z, _ in along(list(conc.exterior.coords), V("site.palm.spacing") * 1.25, 0):
    if not obst.buffer(2).contains(Point(x, z)) and not plaza.buffer(3).contains(Point(x, z)) and not band.contains(Point(x, z)) and site.buffer(-3).contains(Point(x, z)):
        palms.append([round(x, 2), round(z, 2)])
# broad-crowned trees in clumps on the lawns, a belt inside the boundary, rows round the car parks (SR39, design model)
trees = []
X, Z = np.meshgrid(np.arange(-400, 500, V("site.tree.spacing")), np.arange(-380, 340, V("site.tree.spacing")))
X = X.ravel() + rng.uniform(-3.5, 3.5, X.size); Z = Z.ravel() + rng.uniform(-3.5, 3.5, Z.size)
nz = np.zeros(X.size)
for wl in (90, 140):
    a = rng.uniform(0, np.pi, 2); ph = rng.uniform(0, 2 * np.pi, 2)
    nz += np.sin((X * np.cos(a[0]) + Z * np.sin(a[0])) * 2 * np.pi / wl + ph[0]) * np.sin((X * np.cos(a[1]) + Z * np.sin(a[1])) * 2 * np.pi / wl + ph[1])
lawn_in = lawn.buffer(-4)
for x, z, n_ in zip(X, Z, nz):
    if n_ > -0.1 and lawn_in.contains(Point(x, z)) and not road_buf.contains(Point(x, z)):
        trees.append([round(float(x), 2), round(float(z), 2), int(rng.choice([0, 1, 3], p=[0.62, 0.36, 0.02])), round(float(rng.uniform(0.85, 1.3)), 2)])
for x, z, _ in along(list(site.exterior.coords), V("site.tree.spacing"), 0):
    q = Point(x, z); c = site.centroid; d = np.array([c.x - x, c.y - z]); d = d / np.linalg.norm(d) * 7
    if lawn.contains(Point(x + d[0], z + d[1])) and not road_buf.contains(Point(x + d[0], z + d[1])):
        trees.append([round(x + d[0], 2), round(z + d[1], 2), 0, round(float(rng.uniform(0.9, 1.25)), 2)])
for lot in lots:
    for x, z, _ in along(list(lot["poly"].exterior.coords), 11.0, 0):
        if site.buffer(10).contains(Point(x, z)) and not road_buf.buffer(-2).contains(Point(x, z)): trees.append([round(x, 2), round(z, 2), 0, 0.9])
shrubs = []
bx0, bz0, bx1, bz1 = beds.bounds
cand = np.stack([rng.uniform(bx0, bx1, 20000), rng.uniform(bz0, bz1, 20000)], 1)
for x, z in cand:
    if len(shrubs) >= 2500: break
    if beds.contains(Point(x, z)): shrubs.append([round(float(x), 2), round(float(z), 2)])
for pl in planters:  # shrubs and a small tree in each raised planter
    for k_ in range(9):
        a = rng.uniform(0, 2 * np.pi); r_ = rng.uniform(0, pl[2] - 1.2); shrubs.append([round(pl[0] + r_ * math.cos(a), 2), round(pl[1] + r_ * math.sin(a), 2)])

# ---------------------------------------------------------------- masts, lights, bollards, fence, sign frames
lightmasts = []
ext = LineString(site.exterior.coords); c0 = site.centroid
for s in np.arange(20, ext.length, V("site.masts.spacing")):
    p = ext.interpolate(s); d = np.array([c0.x - p.x, c0.y - p.y]); d = d / np.linalg.norm(d) * V("site.masts.inset")
    q = (p.x + d[0], p.y + d[1])
    if not sport.contains(Point(q)) and not park.contains(Point(q)): lightmasts.append([round(q[0], 2), round(q[1], 2)])
flagmasts = [list(local(rN + 20 + kk * 38, sg * 70)) for sg in (-1, 1) for kk in range(int(V("site.masts.forecourt_rows")))]
bollards = []
for p in paths:
    if p["kind"] != "avenue": continue
    end = np.array(p["pts"][-1]); t = (end - np.array(p["pts"][0])); t /= np.linalg.norm(t); nrm = np.array([-t[1], t[0]])
    for k_ in np.arange(-p["w"] / 2 - 6, p["w"] / 2 + 6.01, V("site.bollard.spacing")):
        q = end - t * 1.0 + nrm * k_; bollards.append([round(float(q[0]), 2), round(float(q[1]), 2)])
cross = unary_union([l for l in site_roads] + [LineString(p["pts"]) for p in paths if p["kind"] in ("avenue", "diagonal")])
fence = ext.difference(cross.buffer(V("site.fence.gap") / 2))
fence = [[[round(x, 2), round(z, 2)] for x, z in g.coords] for g in getattr(fence, "geoms", [fence]) if g.length > 3]
signs = []  # blank billboard frames on the Ngong Road verge (lead correction 3; SR50)
for xs in (-260, 120, 470):
    s = ngong_mid.project(Point(xs, -400)); p = ngong_mid.interpolate(s); q = ngong_mid.interpolate(s + 2)
    t = np.array([q.x - p.x, q.y - p.y]); t /= np.linalg.norm(t); nrm = np.array([-t[1], t[0]])
    if nrm[1] < 0: nrm = -nrm  # stadium side (south)
    o = np.array([p.x, p.y]) + nrm * (ng_half - NG["service_w"] / 2)
    signs.append([round(float(o[0]), 2), round(float(o[1]), 2), round(math.degrees(math.atan2(t[1], t[0])), 2)])
bays = []
for lot in lots:
    for a in lot["aisles"]:
        if a.length < 40: continue
        for x, z, t in along(list(a.coords), V("site.parking.bay_w"), 0, 3.0):
            nrm = np.array([-t[1], t[0]])
            for sg in (-1, 1):
                c = np.array([x, z]) + sg * nrm * (3.0 + V("site.parking.bay_d") / 2)
                if lot["poly"].contains(Point(*c)): bays.append([round(float(c[0]), 2), round(float(c[1]), 2), round(float(t[0]), 4), round(float(t[1]), 4)])

# ---------------------------------------------------------------- masks
N = int(2 * HALF / RES)
def px(pts): return [((x + HALF) / RES, (z + HALF) / RES) for x, z in pts]
def mask(geom, blur=1.0):
    im = Image.new("L", (N, N), 0); d = ImageDraw.Draw(im)
    for g in getattr(geom, "geoms", [geom]):
        if g.is_empty or g.geom_type != "Polygon": continue
        d.polygon(px(list(g.exterior.coords)), fill=255)
        for h in g.interiors: d.polygon(px(list(h.coords)), fill=0)
    return im.filter(ImageFilter.GaussianBlur(blur))
edge = pave.boundary.buffer(V("site.paving.edge_w")).intersection(site)
Image.merge("RGB", (mask(lawn), mask(pave), mask(beds))).save(ROOT / "blender/textures/site_regions.png")
Image.merge("RGB", (mask(edge, 0.6), mask(deck), mask(park))).save(ROOT / "blender/textures/site_regions2.png")
apron = plinth.buffer(V("site.apron.depth")).difference(plinth).intersection(pave)  # SR06 entrance apron, low contrast
Image.merge("RGB", (mask(apron, 4.0), Image.new("L", (N, N), 0), Image.new("L", (N, N), 0))).save(ROOT / "blender/textures/site_regions3.png")

# road centrelines for lane dashes (Ngong Road gets its own markings in blender/build_site_detail.py)
lines = []
for cls, nm, g in zip(R["class"], R["name"], R.geometry):
    if cls not in ("trunk", "primary", "secondary", "tertiary"): continue
    for l in loc_line(g):
        pts = [(round(x, 2), round(z, 2)) for x, z in l.coords]
        if min(x * x + z * z for x, z in pts) < 1500 ** 2: lines.append({"class": cls, "name": None if str(nm) == "nan" else str(nm), "pts": pts})
(ROOT / "blender/data/road_lines.json").write_text(json.dumps(lines))

plan = {
    "frame": "local twin frame, x east, z south (m)", "bearing_deg": math.degrees(b), "rN": rN,
    "ngong": {"mid": [[round(x, 2), round(z, 2)] for x, z in sm], **NG, "half_carriageway": ng_half_cw, "half": ng_half},
    "paths": paths, "palms": palms, "trees": trees, "shrubs": shrubs, "planters": planters, "pathlights": pathlights,
    "lightmasts": lightmasts, "flagmasts": flagmasts, "bollards": bollards, "fence": fence, "signs": signs,
    "jets": [[round(x, 2), round(z, 2)] for x, z in jets], "canopies": canopies, "bays": bays,
    "lots": [[[round(x, 2), round(z, 2)] for x, z in l["poly"].exterior.coords] for l in lots],
    "tracks": tracks, "pitch_se": pse,
}
(ROOT / "blender/data/site_plan.json").write_text(json.dumps(plan))
print({k: len(v) for k, v in plan.items() if isinstance(v, list)}, "ngong mid pts", len(sm), "half", round(ng_half, 1),
      "areas m2: lawn", round(lawn.area), "pave", round(pave.area), "beds", round(beds.area), "park", round(park.area))
