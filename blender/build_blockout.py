"""Stage 01: Blender blockout of the fully built stadium, from the parameter ledger.

Reads gis/parameter_ledger.csv and the normalized W1b outlines in gis/measurements/normalized/
(gis/scripts/normalize_shapes.py). Builds named
collections: plinth, shell (facade and roof), tiers, pitch, forecourt, sport, ground.
Every object carries its sources and a claim level ("measured" or "estimated") as custom
properties, and the glTF export keeps them as extras.

Shell plan: ground edge = design plinth ring; widest point of the facade = design roof outer ring;
roof opening = design roof inner ring. The design rings are concentric superellipses fitted to the
W1b traces (gis/scripts/fit_design_plan.py), roof rings corrected for the relief shift of the oblique image. Heights are estimates (ledger) until stage 01b.

Run from the repo root:
  ~/.venvs/bpy/bin/python blender/build_blockout.py            (build, save .blend, export glb)
App frame (x east, y up, z south) -> Blender (x, -z, y). Geometry sits on the site pad.
"""
import csv, json, math, os, sys
from pathlib import Path
import bpy, bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender/scripts"))
N = 240

# ---------------------------------------------------------------- inputs
L = {r["name"]: r for r in csv.DictReader(open(ROOT / "gis/parameter_ledger.csv"))}
V = lambda k: float(L[k + "_blockout"]["value"]) if k + "_blockout" in L else float(L[k]["value"])  # Blender overrides
WITHDRAWN = lambda k: k in L and L[k]["status"].startswith("withdrawn")  # kept in the ledger as evidence, not read
VO = lambda k, d: V(k) if ((k in L and not WITHDRAWN(k)) or k + "_blockout" in L) else d  # optional row (profile fit), else the old estimate
MAN = json.loads((ROOT / "app/public/data/manifest.json").read_text())
PAD = MAN["features"]["site_pad_y"]


def outline(fn, shift=(0.0, 0.0)):
    """Normalized W1b ring (gis/measurements/normalized/, local x east, z south) minus a relief shift (x, z)."""
    return [(float(r["x_east"]) - shift[0], float(r["z_south"]) - shift[1])
            for r in csv.DictReader(open(ROOT / "gis/measurements/normalized" / fn))]


def ray_radius(ring, ux, uz):
    best = 0.0
    for i in range(len(ring)):
        (ax, az), (bx, bz) = ring[i], ring[(i + 1) % len(ring)]
        ex, ez = bx - ax, bz - az
        den = ux * ez - uz * ex
        if abs(den) < 1e-12: continue
        t = (ax * ez - az * ex) / den
        s = (ax * uz - az * ux) / den
        if t > 0 and -1e-9 <= s <= 1 + 1e-9: best = max(best, t)
    return best


def smooth(r, k=2):
    n = len(r); return [sum(r[(i + j) % n] for j in range(-k, k + 1)) / (2 * k + 1) for i in range(n)]


def rounded_rect(hl, hw, rad, bearing, steps=8):
    pts = []
    for cx, cz, a0 in [(hw - rad, -(hl - rad), -math.pi / 2), (hw - rad, hl - rad, 0), (-(hw - rad), hl - rad, math.pi / 2), (-(hw - rad), -(hl - rad), math.pi)]:
        for k in range(steps + 1):
            a = a0 + k / steps * math.pi / 2; pts.append((cx + rad * math.cos(a), cz + rad * math.sin(a)))
    b = math.radians(bearing); c, s = math.cos(b), math.sin(b)
    return [(x * c - z * s, x * s + z * c) for x, z in pts]


B = lambda x, y, z: (x, -z, y)  # app frame -> Blender

# ---------------------------------------------------------------- scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
COLS = {}


def coll(name):
    if name not in COLS:
        c = bpy.data.collections.new(name); scene.collection.children.link(c); COLS[name] = c
    return COLS[name]


MATS = {}


def mat(name, rgb, rough=0.6, metal=0.0):
    if name in MATS: return MATS[name]
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough; p.inputs["Metallic"].default_value = metal
    m.diffuse_color = (*rgb, 1)
    MATS[name] = m; return m


def obj(name, collection, verts, faces, material, status, sources, smooth_shade=False):
    me = bpy.data.meshes.new(name); me.from_pydata([B(*v) for v in verts], [], faces); me.validate(); me.update()
    if smooth_shade:
        for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); coll(collection).objects.link(o)
    o.data.materials.append(material)
    o["claim"] = status; o["sources"] = sources
    return o


def flat(name, collection, ring, y, material, status, sources):
    bm = bmesh.new()
    vs = [bm.verts.new(B(x, y, z)) for x, z in ring]
    f = bm.faces.new(vs); f.normal_update()
    if f.normal.z < 0: f.normal_flip()
    bmesh.ops.triangulate(bm, faces=[f])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); coll(collection).objects.link(o); o.data.materials.append(material)
    o["claim"] = status; o["sources"] = sources
    return o


# ---------------------------------------------------------------- plan rings (polar, N directions)
shift = (V("roof.relief_shift_x"), V("roof.relief_shift_z"))
# Design plan: symmetric superellipses fitted to the W1b traces (gis/scripts/fit_design_plan.py, ledger
# bowl.plan.*). The roof rings are already relief-corrected there, so no shift here.
plinth = outline("bowl_plinth_design_2026-10-17.csv")
roof_out = outline("bowl_roof_outer_design_2026-10-17.csv")
roof_in = outline("bowl_roof_inner_design_2026-10-17.csv")
bearing = V("pitch.bearing")
dirs = [(math.cos(2 * math.pi * i / N), math.sin(2 * math.pi * i / N)) for i in range(N)]
rPl = smooth([ray_radius(plinth, ux, uz) for ux, uz in dirs])
rRo_meas = smooth([ray_radius(roof_out, ux, uz) for ux, uz in dirs])
# The 12-point roof-top trace cuts the corners, so in places it falls well inside the plinth.
# The measured ends lean in by about 1.4 m, so allow up to LEAN_IN m; beyond that, clamp to
# plinth - LEAN_IN (estimated). This also keeps the back wall (plinth - back_setback) inside the shell.
LEAN_IN = 4.0
rRo = smooth([max(a, b - LEAN_IN) for a, b in zip(rRo_meas, rPl)], 6)
CLAMPED = sum(a < b - LEAN_IN for a, b in zip(rRo_meas, rPl))
rRi = smooth([ray_radius(roof_in, ux, uz) for ux, uz in dirs])
seat0 = rounded_rect(V("bowl.seat_start.half_long"), V("bowl.seat_start.half_wide"), V("bowl.seat_start.corner_r"), bearing)
rIn = [ray_radius(seat0, ux, uz) for ux, uz in dirs]
rBack = [r - V("bowl.back_setback") for r in rPl]

plinthH = V("bowl.plinth_h")
topY, openY, sag = V("bowl.roof_top_y"), V("bowl.opening_y"), V("bowl.roof_sag")
R = V("bowl.profile.shoulder_r")
facadeInset = V("bowl.facade_inset")
# Side profile fitted to the drone frames (gis/scripts/profile_fit/fit2.py; ledger rows "derived" where the
# leave-one-frame-out spread passed). Rows that are absent keep the earlier estimates: wall top yW = topY - R,
# a circular shoulder of radius R, no bulge, the foot from the plinth inset.
yW = VO("bowl.profile.wall_top_y", topY - R)
Rh, Rv = VO("bowl.profile.shoulder_rh", R), VO("bowl.profile.shoulder_rv", R)
topY = yW + Rv
openY, sag = VO("bowl.profile.opening_y", openY), VO("bowl.profile.roof_sag", sag)
dF, wbulge = VO("bowl.profile.foot_inset", None), VO("bowl.profile.wall_bulge", 0.0)


def foot_r(i):
    return rRo[i] - dF if dF is not None else min(rPl[i] + V("bowl.plinth_inset") - facadeInset, rRo[i])

# Profile (radius, height) at direction i, from the ground edge to the opening.
def profile(i):
    p = [(rPl[i], 0.0), (rPl[i], plinthH)]
    # facade foot vs plinth face as in bowl.js (estimated), never outside the widest ring
    r0 = foot_r(i)
    # Wall: straight (plus the fitted bulge) from the foot to the widest ring at the wall top yW, then the
    # shoulder, a quarter ellipse (Rh across, Rv up) onto the crest.
    yR = yW
    for k in range(1, 13):
        f = k / 12; p.append((r0 + (rRo[i] - r0) * f + wbulge * math.sin(math.pi * f), plinthH + (yR - plinthH) * f))
    for k in range(1, 13):  # shoulder: quarter ellipse inward to the crest
        a = k / 12 * math.pi / 2; p.append((rRo[i] - Rh * (1 - math.cos(a)), yR + Rv * math.sin(a)))
    rc = rRo[i] - Rh
    for k in range(1, 11):  # roof: crest to opening, with a sag
        t = k / 10; p.append((rc + (rRi[i] - rc) * t, topY + (openY - topY) * t - sag * math.sin(t * math.pi)))
    return p


PROF = [profile(i) for i in range(N)]
NP = len(PROF[0]); J_FACADE = 26  # index of the crest: facade = [0..26], roof = [26..]
Y = lambda y: y + PAD


def loft(name, collection, j0, j1, material, status, sources):
    verts, faces = [], []
    cols = j1 - j0 + 1
    for i in range(N):
        ux, uz = dirs[i]
        for j in range(j0, j1 + 1):
            r, y = PROF[i][j]; verts.append((ux * r, Y(y), uz * r))
    for i in range(N):
        i2 = (i + 1) % N
        for j in range(cols - 1):
            a, b = i * cols + j, i2 * cols + j
            faces.append((a, b, b + 1, a + 1))
    return obj(name, collection, verts, faces, material, status, sources, True)


WHITE = mat("white_shell", (0.85, 0.85, 0.83), 0.5)
MEMB = mat("membrane", (0.92, 0.92, 0.9), 0.7)
CONC = mat("concrete", (0.62, 0.6, 0.56), 0.9)
GLASS = mat("plinth_glass", (0.12, 0.14, 0.16), 0.2, 0.3)
GRASS = mat("grass", (0.2, 0.36, 0.14), 0.95)
PAVE = mat("paving", (0.7, 0.67, 0.62), 0.9)
EARTH = mat("earth", (0.45, 0.3, 0.2), 1.0)
TRACK = mat("track", (0.55, 0.24, 0.17), 0.9)
GROUND = mat("ground", (0.36, 0.34, 0.28), 1.0)
GREEN, RED = mat("seat_green", (0.09, 0.3, 0.15), 0.6), mat("seat_red", (0.45, 0.06, 0.07), 0.6)

SRC_PL = "design plan bowl_plinth_design_2026-10-17.csv (superellipse fit to the W1b trace); plinth_h, facade_inset (estimated)"
SRC_SH = "design plan: superellipse fits to the W1b plinth, roof_outer, roof_inner traces (relief-corrected; ledger bowl.plan.*); heights roof_top_y, opening_y, profile.shoulder_r and the near-vertical wall (estimated, by eye against JWNowpO44rw 07:04)"
# Base (stage 02b, by eye from JWNowpO44rw 12:12, 12:16, 12:40; estimated): a light concrete step on the measured
# plinth outline, a shaded wall set back behind white columns, and a light band under the louvres.
STEP, REC, BAND = V("bowl.base.step_h"), V("bowl.base.recess"), V("bowl.base.band_h")
LIGHT = mat("concrete_light", (0.78, 0.77, 0.74), 0.85)
SHADE = mat("concrete_shade", (0.42, 0.41, 0.39), 0.9)
SRC_BASE = "design plan bowl_plinth_design_2026-10-17.csv (outline, fitted to W1b); ledger bowl.base.*, plinth_h (estimated, by eye from 12:12, 12:16, 12:40)"


def ring_band(name, collection, rings, material, status, sources):
    """Rings of (radius list, y) joined in order round the N directions."""
    v, f = [], []; nr = len(rings)
    for i in range(N):
        ux, uz = dirs[i]
        for rr, y in rings: v.append((ux * rr[i], Y(y), uz * rr[i]))
    for i in range(N):
        a, b = nr * i, nr * ((i + 1) % N)
        for k in range(nr - 1): f.append((a + k, b + k, b + k + 1, a + k + 1))
    return obj(name, collection, v, f, material, status, sources)


rRec = [r - REC for r in rPl]
plinth_o = ring_band("plinth", "plinth", [(rPl, 0.0), (rPl, STEP), (rRec, STEP)], LIGHT, "plan measured, height estimated", SRC_BASE)
ring_band("base_recess", "plinth", [(rRec, STEP), (rRec, plinthH - BAND)], SHADE, "estimated", SRC_BASE)
ring_band("base_band", "plinth", [(rRec, plinthH - BAND), (rPl, plinthH - BAND), (rPl, plinthH)], LIGHT, "estimated", SRC_BASE)
# white columns at an even spacing along the plinth outline, just behind the band face
cw, csp = V("bowl.base.column_w") / 2, V("bowl.base.column_spacing")
ring = [(dirs[i][0] * rPl[i], dirs[i][1] * rPl[i]) for i in range(N)]
seg = [math.dist(ring[i], ring[(i + 1) % N]) for i in range(N)]
v, f = [], []; acc, nxt = 0.0, 0.0
for i in range(N):
    while nxt <= acc + seg[i]:
        t = (nxt - acc) / seg[i]; a, b = ring[i], ring[(i + 1) % N]
        px, pz = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        tx, tz = (b[0] - a[0]) / seg[i], (b[1] - a[1]) / seg[i]; nx_, nz_ = tz, -tx  # outward for an anticlockwise ring
        if nx_ * px + nz_ * pz < 0: nx_, nz_ = -nx_, -nz_
        cx, cz = px - nx_ * (cw + 0.3), pz - nz_ * (cw + 0.3)
        base = len(v)
        for y in (STEP, plinthH - BAND):
            for su, so in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                v.append((cx + tx * su * cw + nx_ * so * cw, Y(y), cz + tz * su * cw + nz_ * so * cw))
        for k in range(4): f.append((base + k, base + (k + 1) % 4, base + 4 + (k + 1) % 4, base + 4 + k))
        nxt += csp
    acc += seg[i]
obj("base_columns", "plinth", v, f, WHITE, "estimated", SRC_BASE)
# Louvred wall (stage 02b, by eye from JWNowpO44rw 10:28 and 12:12-12:16): thin horizontal fins, sloping
# down outward, over a dark recessed backing. The fins' outer edges lie on the wall line of profile();
# above the wall the solid white shoulder (fascia) runs onto the roof. All fin values estimated.
J_WALL = 13  # profile index of the wall top yR = yW
yR = PROF[0][J_WALL][1]
# The fins carry on up the shoulder to a thin fascia line (12:12): the profile point on the shoulder
# nearest to topY - fin.fascia_h. Above it the solid white fascia runs onto the roof.
J_F = min(range(J_WALL, J_FACADE), key=lambda j: abs(PROF[0][j][1] - (topY - V("bowl.fin.fascia_h"))))
yF = PROF[0][J_F][1]
R0 = [foot_r(i) for i in range(N)]


def rw(i, y):
    """Outer face radius at height y: the straight wall, then the shoulder arc."""
    if y <= yR:
        f = (y - plinthH) / (yR - plinthH); return R0[i] + (rRo[i] - R0[i]) * f + wbulge * math.sin(math.pi * f)
    return rRo[i] - Rh * (1 - math.cos(math.asin(min((y - yR) / Rv, 1.0))))
FIN_P, FIN_D, FIN_DROP, BACK = V("bowl.fin.pitch"), V("bowl.fin.depth"), V("bowl.fin.drop"), V("bowl.fin.backing_inset")
VOID = mat("facade_void", (0.05, 0.05, 0.055), 0.8)
SRC_FIN = "ledger bowl.fin.* (estimated, by eye from JWNowpO44rw 10:28, 12:12-12:16); wall line from W1b rings"
# soffit: flat ring from the plinth top in to the backing
v, f = [], []
for i in range(N):
    ux, uz = dirs[i]; rf = R0[i] - BACK; v += [(ux * rPl[i], Y(plinthH), uz * rPl[i]), (ux * rf, Y(plinthH), uz * rf)]
for i in range(N):
    a, b = 2 * i, 2 * ((i + 1) % N); f.append((a, a + 1, b + 1, b))
obj("soffit", "plinth", v, f, WHITE, "estimated", SRC_PL)
# backing: the wall line and shoulder pushed in by BACK, from the plinth top to the fascia line, closed by a cap
v, f = [], []
BY = [PROF[0][j][1] for j in range(1, J_F + 1)]  # every wall row, so the backing follows the fitted bulge
nb = len(BY) + 1
for i in range(N):
    ux, uz = dirs[i]
    for y in BY:
        r = rw(i, y) - BACK; v.append((ux * r, Y(y), uz * r))
    r = rw(i, yF); v.append((ux * r, Y(yF), uz * r))
for i in range(N):
    a, b = nb * i, nb * ((i + 1) % N); f += [(a + k, b + k, b + k + 1, a + k + 1) for k in range(nb - 1)]
obj("facade_backing", "shell", v, f, VOID, "estimated", SRC_FIN)
v, f = [], []
nf = int((yF - FIN_DROP - plinthH - 0.4) / FIN_P) + 1
for k in range(nf):
    y = plinthH + 0.4 + k * FIN_P; base = len(v)
    for i in range(N):
        ux, uz = dirs[i]; ro = rw(i, y); ri = ro - FIN_D
        v += [(ux * ri, Y(y + FIN_DROP), uz * ri), (ux * ro, Y(y), uz * ro)]
    for i in range(N):
        a, b = base + 2 * i, base + 2 * ((i + 1) % N); f.append((a, b, b + 1, a + 1))
obj("louvre_fins", "shell", v, f, WHITE, "estimated", SRC_FIN)
# facade object = the solid fascia from the fascia line over the shoulder to the crest; its widest ring is rRo (geometry gate)
facade = loft("facade", "shell", J_F, J_FACADE, WHITE, "plan fitted to measured traces, heights estimated", SRC_SH)
# the roof itself (cushions on the fitted roof surface) is built after surf(), below the roof ribs

# ---------------------------------------------------------------- tiers (stepped rake)
tiers = [("lower", GREEN), ("middle", RED), ("upper", RED)]
at = lambda i, t: rIn[i] + (rBack[i] - rIn[i]) * t
for tn, m in tiers:
    t0, t1, y0, y1, rows = (V(f"bowl.tier_{tn}.{k}") for k in ("t0", "t1", "y0", "y1", "rows"))
    rows = int(rows); verts, faces = [], []
    for k in range(rows):
        ta, tb = t0 + (t1 - t0) * k / rows, t0 + (t1 - t0) * (k + 1) / rows
        ya, yb = y0 + (y1 - y0) * k / rows, y0 + (y1 - y0) * (k + 1) / rows
        base = len(verts)
        for i in range(N):
            ux, uz = dirs[i]
            for t, y in ((ta, ya), (tb, ya), (tb, yb)):
                verts.append((ux * at(i, t), Y(y), uz * at(i, t)))
        for i in range(N):
            a, b = base + 3 * i, base + 3 * ((i + 1) % N)
            faces += [(a, b, b + 1, a + 1), (a + 1, b + 1, b + 2, a + 2)]
    obj(f"tier_{tn}", "tiers", verts, faces, m, "estimated", f"ledger bowl.tier_{tn}.* (estimated); seat start bowl.seat_start.* (estimated)")
# back wall and bands between tiers (concrete)
v, f = [], []
for i in range(N):
    ux, uz = dirs[i]; v += [(ux * rBack[i], Y(0), uz * rBack[i]), (ux * rBack[i], Y(V("bowl.back_wall_h")), uz * rBack[i])]
for i in range(N):
    a, b = 2 * i, 2 * ((i + 1) % N); f.append((a, b, b + 1, a + 1))
obj("back_wall", "tiers", v, f, CONC, "estimated", "ledger bowl.back_wall_h, bowl.back_setback (estimated)")
for nm, ta, ya, yb, m in [("vip_glass", V("bowl.tier_middle.t0"), V("bowl.band.vip_glass_y0"), V("bowl.band.vip_glass_y1"), GLASS),
                          ("band_lower", V("bowl.tier_lower.t1"), V("bowl.tier_lower.y1"), V("bowl.band.vip_glass_y0"), CONC),
                          ("band_middle", V("bowl.tier_middle.t1"), V("bowl.tier_middle.y1"), V("bowl.band.upper_front_y1"), CONC),
                          ("pitch_wall", 0.0, 0.0, V("bowl.band.base_wall_h"), CONC)]:
    v, f = [], []
    for i in range(N):
        ux, uz = dirs[i]; r = at(i, ta); v += [(ux * r, Y(ya), uz * r), (ux * r, Y(yb), uz * r)]
    for i in range(N):
        a, b = 2 * i, 2 * ((i + 1) % N); f.append((a, b, b + 1, a + 1))
    obj(nm, "tiers", v, f, m, "estimated", "ledger bowl.band.* (estimated)")

# ---------------------------------------------------------------- facade details (stage 02 pass 2; all estimated)
# Diamond lattice, rings, roof ribs, opening ring beam, eight shields. Counts and
# sizes come from the ledger rows that bowl.js uses (estimated, from frames as look references).
import numpy as np
from mathutils import Vector


def surf(theta, jf, off=0.0):
    """Point on the shell profile at angle theta (rad) and fractional profile index jf, pushed out by off."""
    fi = (theta / (2 * math.pi)) % 1 * N
    i0 = int(fi) % N; i1 = (i0 + 1) % N; fi -= int(fi)
    j0 = min(max(int(math.floor(jf)), 2), NP - 2); j1 = j0 + 1; fj = jf - j0  # below j=2: extend the wall line down
    def rp(i): return [PROF[i][j0][k] * (1 - fj) + PROF[i][j1][k] * fj for k in (0, 1)]
    a, b = rp(i0), rp(i1)
    r = a[0] * (1 - fi) + b[0] * fi + off; y = a[1] * (1 - fi) + b[1] * fi
    return Vector(B(math.cos(theta) * r, Y(y), math.sin(theta) * r))


def j_at_height(y):
    p = PROF[0]
    if y < p[2][1]: return 2 + (y - p[2][1]) / (p[3][1] - p[2][1])
    for j in range(2, J_FACADE):
        if p[j][1] <= y <= p[j + 1][1]: return j + (y - p[j][1]) / (p[j + 1][1] - p[j][1])
    return J_FACADE


def curve_obj(name, collection, splines, depth, material, closed=False, status="estimated", sources=""):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = depth; cu.bevel_resolution = 1
    for pts in splines:
        sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
        for k, v in enumerate(pts): sp.points[k].co = (v.x, v.y, v.z, 1)
        sp.use_cyclic_u = closed
    o = bpy.data.objects.new(name, cu); coll(collection).objects.link(o); o.data.materials.append(material)
    o["claim"] = status; o["sources"] = sources
    return o


def outward(theta):
    return Vector((math.cos(theta), -math.sin(theta), 0.0))


def sweep(name, collection, paths, section, material, sources, status="estimated", smooth_shade=False):
    """Sweep a 2D section (side, out) along each path of (point, theta, scale); side is across the path on the
    facade, out is radial. scale (optional) multiplies the section. Open ends."""
    verts, faces = [], []
    ns = len(section)
    for path in paths:
        base = len(verts)
        for k, (p, th, *sc) in enumerate(path):
            sc = sc[0] if sc else (1.0, 1.0)
            q = path[min(k + 1, len(path) - 1)][0] - path[max(k - 1, 0)][0]
            o = outward(th); side = q.cross(o).normalized()
            for su, so in section: verts.append(p + side * (su * sc[0]) + o * (so * sc[1]))
        for k in range(len(path) - 1):
            for m in range(ns):
                a0 = base + k * ns + m; a1 = base + k * ns + (m + 1) % ns
                faces.append((a0, a1, a1 + ns, a0 + ns))
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.validate(); me.update()
    if smooth_shade:
        for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); coll(collection).objects.link(o); o.data.materials.append(material)
    o["claim"] = status; o["sources"] = sources
    return o


# Diamond lattice: flat-faced members of trapezoid section standing proud of the fins, from the bottom of the
# louvred band to the fascia (by eye from 12:12-12:16; one diamond spans the band height, 07:04 count).
K = int(V("bowl.profile.lattice_members_704"))
lw, ld = V("bowl.lattice.section_w") / 2, V("bowl.lattice.section_d")
LSEC = [(-lw, -0.1), (lw, -0.1), (lw * 0.3, ld), (-lw * 0.3, ld)]
J_LO = j_at_height(plinthH + 0.2)
sp = []
for k in range(K):
    for sg in (1, -1):
        th0 = 2 * math.pi * k / K; d = sg * 2 * math.pi / K
        sp.append([(surf(th0 + d * (j - J_LO) / (J_F - J_LO), j, 0), th0 + d * (j - J_LO) / (J_F - J_LO)) for j in np.linspace(J_LO, J_F, 48)])
sweep("lattice", "facade_detail", sp, LSEC, WHITE, "ledger bowl.lattice.section_*, bowl.profile.lattice_members_704 (estimated)")
rings = [[surf(2 * math.pi * i / N, j, 0.3) for i in range(N)] for j in (J_LO, float(J_F))]
curve_obj("lattice_rings", "facade_detail", rings, V("bowl.lattice.ring_r"), WHITE, closed=True, sources="ledger bowl.lattice.ring_r (estimated)")
nrib = int(VO("bowl.roof.cushion_bays", V("bowl.roof.ribs")))  # topside ribs bound the cushion bays (001221.500, 001224.500)
# ribs half sunk into the membrane (stage 02b: 12:40 shows a smooth membrane with faint seams, not raised tubes)
ribs = [[surf(2 * math.pi * k / nrib, j, 0) + Vector((0, 0, 0.1 - V("bowl.roof.rib_r"))) for j in np.linspace(J_FACADE, NP - 1, 14)] for k in range(nrib)]
curve_obj("roof_ribs", "facade_detail", ribs, V("bowl.roof.rib_r"), WHITE, sources="ledger bowl.roof.ribs (estimated)")
# Cushion roof (JWNowpO44rw 001221.500 to 001239.267): between each pair of radial ribs, rows of inflated
# cushions from the crest to the opening. Each cushion is a patch of the fitted roof surface lifted by
# bowl.roof.cushion_bulge * sin(pi u) sin(pi v), so the seams at the ribs and between rows stay on the surface
# and the bulges catch the light. Rows and bulge: ledger (estimated, by eye from the frames).
NROW, HB = int(VO("bowl.roof.cushion_rows", 8)), VO("bowl.roof.cushion_bulge", 0.45)
NU, NV = 6, 4
cv, cf = [], []
for k in range(nrib):
    ta, tb = 2 * math.pi * k / nrib, 2 * math.pi * (k + 1) / nrib
    for jr in range(NROW):
        ja = J_FACADE + (NP - 1 - J_FACADE) * jr / NROW; jb = J_FACADE + (NP - 1 - J_FACADE) * (jr + 1) / NROW
        base = len(cv)
        for a in range(NU + 1):
            for b in range(NV + 1):
                q = surf(ta + (tb - ta) * a / NU, ja + (jb - ja) * b / NV, 0)
                q.z += HB * math.sin(math.pi * a / NU) * math.sin(math.pi * b / NV)
                cv.append(tuple(q))
        for a in range(NU):
            for b in range(NV):
                i0 = base + a * (NV + 1) + b; cf.append((i0, i0 + NV + 1, i0 + NV + 2, i0 + 1))
me = bpy.data.meshes.new("roof"); me.from_pydata(cv, [], cf); me.validate(); me.update()  # cv already in Blender coordinates
for p_ in me.polygons: p_.use_smooth = True
roof = bpy.data.objects.new("roof", me); coll("shell").objects.link(roof); me.materials.append(MEMB)
roof["claim"] = "plan measured, profile derived from frames, cushions estimated"
roof["sources"] = SRC_SH + "; cushions: ledger bowl.roof.ribs, bowl.roof.cushion_rows, bowl.roof.cushion_bulge (by eye from 001221.500-001239.267)"
curve_obj("ring_beam", "facade_detail", [[surf(2 * math.pi * i / N, NP - 1, 0) for i in range(N)]], V("bowl.roof.ring_beam_r"), WHITE, closed=True, sources="ledger bowl.roof.ring_beam_r (estimated)")

# Shield image painted here from simple shapes (our own drawing, not a frame), per the lead's description
# checked against 12:12, 12:16 and 10:28: red field, black crescent lobes on the left and right edges, a white
# vertical spine, a white central boss and broad white leaf shapes above and below it. Red from the ledger.
def shield_png(path, w=512, h=1024):
    yy, xx = np.mgrid[0:h, 0:w]; u = (xx + 0.5) / w * 2 - 1; v = (yy + 0.5) / h * 2 - 1
    au, av = np.abs(u), np.abs(v)
    outline = au <= np.clip(1 - av ** 2, 0, 1) ** 0.62
    hexr = L["bowl.shield.red"]["value"].lstrip("#"); red = [int(hexr[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    white = [0.95, 0.95, 0.93, 1]
    img = np.zeros((h, w, 4)); img[outline] = [*red, 1]
    crescent = outline & (au >= 1 - 0.4 * np.sqrt(np.clip(1 - (v / 0.56) ** 2, 0, 1)))
    img[crescent] = [0.04, 0.04, 0.04, 1]
    img[outline & (au < 0.014) & (av < 0.97)] = white  # spine
    t = np.clip((av - 0.16) / 0.78, 0, 1)  # leaves above and below the boss, pointed at both ends
    lw = 0.085 * np.sin(np.pi * t) ** 0.7
    img[outline & (av > 0.16) & (av < 0.94) & (np.abs(au - 0.115) < lw)] = white
    img[(u / 0.18) ** 2 + (v / 0.13) ** 2 <= 1] = white  # boss
    # RF13 (12:12): a narrow pale rim follows the outline; width from the ledger, as a fraction of the half-width
    f = float(L["bowl.shield.rim"]["value"]) / (float(L["bowl.shield.width"]["value"]) / 2)
    edge = np.clip(1 - av ** 2, 0, 1) ** 0.62
    img[outline & (au > edge - f)] = [0.906, 0.902, 0.878, 1]
    im = bpy.data.images.new("shield", w, h, alpha=True); im.pixels.foreach_set(img[::-1].ravel().astype(np.float32))
    im.filepath_raw = str(path); im.file_format = "PNG"; im.save()
    return im


(ROOT / "blender/textures").mkdir(exist_ok=True)
sh_img = shield_png(ROOT / "blender/textures/shield.png")
sm = bpy.data.materials.new("shield_paint")
try: sm.use_nodes = True
except Exception: pass
nt = sm.node_tree; pb = nt.nodes["Principled BSDF"]; tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = sh_img
nt.links.new(tx.outputs["Color"], pb.inputs["Base Color"]); nt.links.new(tx.outputs["Alpha"], pb.inputs["Alpha"])
pb.inputs["Roughness"].default_value = 0.45; sm.diffuse_color = (0.7, 0.1, 0.1, 1)
SPEAR = mat("spear_white", (0.92, 0.92, 0.9), 0.35)
axisA = math.radians(-bearing); sw = V("bowl.shield.width")
sy0, sy1 = V("bowl.shield.blockout_y0"), V("bowl.shield.blockout_y1")
hs = VO("bowl.shield.centre_y", None)
if hs is not None:  # fitted shield centre: move the whole shield (height kept), limited so the tip stays under the
    # fascia line and the foot above the plinth; a clamp on the tip alone would shrink the shield and move its centre
    d_ = hs - (sy0 + sy1) / 2
    lo_, hi_ = plinthH + 0.2 - sy0, yF - 0.5 - sy1
    if lo_ > hi_:
        raise ValueError(f"shield ({sy1 - sy0:.2f} m) does not fit between the plinth ({plinthH + 0.2:.2f} m) and the fascia "
                         f"line ({yF - 0.5:.2f} m): no translation satisfies both bounds")
    d_ = max(min(d_, hi_), lo_)
    sy0, sy1 = sy0 + d_, sy1 + d_
bulge, soff = V("bowl.shield.bulge"), V("bowl.shield.offset")
span, bl, br, srad = V("bowl.spear.span_shields"), V("bowl.spear.blade_len"), V("bowl.spear.blade_r"), V("bowl.spear.radius")
tip_y = yF - V("bowl.spear.tip_below_fascia")
verts, faces, uvs, spear_paths = [], [], [], []
for k in range(int(V("bowl.shields.count"))):
    th = axisA - math.pi / 2 + k * 2 * math.pi / int(V("bowl.shields.count"))
    rc = surf(th, j_at_height((sy0 + sy1) / 2)).xy.length; half = sw / 2 / rc
    nu, nv = 16, 32; base = len(verts)
    for a in range(nu + 1):
        for b in range(nv + 1):
            uu, vv = 2 * a / nu - 1, 2 * b / nv - 1
            y = sy0 + (sy1 - sy0) * b / nv
            verts.append(surf(th + half * uu, j_at_height(y), soff + bulge * (1 - uu * uu) * (1 - vv * vv))); uvs.append((a / nu, b / nv))
    for a in range(nu):
        for b in range(nv):
            k0 = base + a * (nv + 1) + b; k1 = k0 + nv + 1; faces.append((k0, k1, k1 + 1, k0 + 1))
    # two crossed spears behind the shield: butt below the shield's lower edge, blade tip just under the fascia
    for sg in (1, -1):
        t0, t1 = th - sg * half * span, th + sg * half * span; y0 = max(sy0 - 0.5, plinthH + 0.2)  # butt below the shield foot, just above the soffit
        n = 160; pts = []
        for f in np.linspace(0, 1, n):
            y = y0 + (tip_y - y0) * f; t = t0 + (t1 - t0) * f
            pts.append([surf(t, j_at_height(y), V("bowl.spear.offset")), t])
        L_ = sum((pts[q + 1][0] - pts[q][0]).length for q in range(n - 1)); acc = 0.0
        for q in range(n):
            if q: acc += (pts[q][0] - pts[q - 1][0]).length
            m = L_ - acc  # distance from the tip
            if m <= bl:
                x = min(max(m / bl, 0.0), 1.0); r = max(br * max(math.sin(math.pi * x), 0.0) ** 0.8, srad * 0.85 if x > 0.9 else 0.0); squash = 0.55
            else:
                r = srad * min(1.0, 0.25 + 0.75 * acc / 2.5); squash = 1.0
            pts[q].append((r, r * squash))
        spear_paths.append(pts)
me = bpy.data.meshes.new("shields"); me.from_pydata(verts, [], faces); me.update()
for p in me.polygons: p.use_smooth = True
uvl = me.uv_layers.new(name="UVMap")
for poly in me.polygons:
    for li in poly.loop_indices: uvl.data[li].uv = uvs[me.loops[li].vertex_index]
so = bpy.data.objects.new("shields", me); coll("facade_detail").objects.link(so); me.materials.append(sm)
so["claim"] = "estimated"; so["sources"] = "ledger bowl.shield.blockout_y0/y1, width, bulge (estimated, by eye from 12:12, 12:16, 12:40; count from design facts)"
circ = [(math.cos(2 * math.pi * q / 12), math.sin(2 * math.pi * q / 12)) for q in range(12)]
sweep("spears", "facade_detail", spear_paths, circ, SPEAR, "ledger bowl.spear.* (estimated, by eye from 10:28, 12:12, 00:16)", smooth_shade=True)

# ---------------------------------------------------------------- pitch and site surfaces
pz = outline("pitch_zone_w1b_2026-10-16.csv")
flat("pitch_zone", "pitch", pz, Y(0.05), EARTH, "measured", "W1b pitch_zone_w1b_2026-10-16.csv")
pl, pw = V("pitch.length"), V("pitch.width")
flat("pitch", "pitch", rounded_rect(pl / 2, pw / 2, 0.01, bearing, 1), Y(0.08), GRASS, "estimated", "pitch.length, pitch.width (estimated 105 x 68 m)")
flat("north_plaza", "forecourt", outline("north_plaza_w1b_2026-10-17.csv"), Y(0.15), PAVE, "measured", "W1b north_plaza_w1b_2026-10-17.csv")
flat("training_pitch_se", "sport", outline("training_pitch_se_w1b_2026-10-17.csv"), Y(0.1), GRASS, "measured", "W1b training_pitch_se_w1b_2026-10-17.csv")
flat("warmup_track", "sport", outline("warmup_track_w1b_2026-10-17.csv"), Y(0.1), TRACK, "measured outline (6 points)", "W1b warmup_track_w1b_2026-10-17.csv")
flat("training_field_sw", "sport", outline("training_pitch_sw_w1b_2026-10-17.csv"), Y(0.1), EARTH, "measured outline; surface estimated", "W1b training_pitch_sw_w1b_2026-10-17.csv")
flat("site_pad", "ground", outline("site_boundary_w1b_2026-10-16.csv"), Y(0.0), GROUND, "measured outline; flat pad estimated", "W1b site_boundary_w1b_2026-10-16.csv; GLO-30 pad height")

# ---------------------------------------------------------------- outputs
os.makedirs(ROOT / "blender/out", exist_ok=True)
# Polar rings and the shell profile, for blender/build_bowl_detail.py (same geometry, no recomputation)
(ROOT / "blender/out/bowl_rings.json").write_text(json.dumps({
    "N": N, "pad": PAD, "dirs": dirs, "rPl": rPl, "rRo": rRo, "rRi": rRi, "rIn": rIn, "rBack": rBack,
    "prof": PROF, "j_facade": J_FACADE, "j_wall": J_WALL, "j_fascia": J_F, "bearing": bearing}))
blend = ROOT / "blender/out/talanta_blockout.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
glb = ROOT / "app/public/data/blockout.glb"
bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", export_extras=True, export_cameras=False, export_lights=False, export_apply=True)
tri = 0
for o in scene.objects:
    if o.type == "MESH": o.data.calc_loop_triangles(); tri += len(o.data.loop_triangles)
print(json.dumps({"roof_outer_clamped_dirs": CLAMPED, "blend": str(blend), "blend_mb": round(blend.stat().st_size / 2**20, 2), "glb": str(glb), "glb_mb": round(glb.stat().st_size / 2**20, 2), "triangles": tri,
                  "collections": {k: [o.name for o in c.objects] for k, c in COLS.items()}}, indent=1))
