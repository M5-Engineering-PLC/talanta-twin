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
# Barrel anchor (geometry pass 4, gis/scripts/profile_fit/fit4_convex.py): "top" puts the wall top on the measured
# roof outer ring rRo with the bulge outside it; "widest" puts the widest ring of a convex barrel on rRo, so the
# junction and the foot sit wbulge inside it.
ANCHOR = L["bowl.profile.bulge_anchor_blockout"]["value"] if "bowl.profile.bulge_anchor_blockout" in L else "top"
rT = [r - max(wbulge, 0.0) for r in rRo] if ANCHOR == "widest" else list(rRo)


def foot_r(i):
    return rT[i] - dF if dF is not None else min(rPl[i] + V("bowl.plinth_inset") - facadeInset, rT[i])

# Profile (radius, height) at direction i, from the ground edge to the opening.
def profile(i):
    p = [(rPl[i], 0.0), (rPl[i], plinthH)]
    # facade foot vs plinth face as in bowl.js (estimated), never outside the widest ring
    r0 = foot_r(i)
    # Wall: straight (plus the fitted bulge) from the foot to the widest ring at the wall top yW, then the
    # shoulder, a quarter ellipse (Rh across, Rv up) onto the crest.
    yR = yW
    for k in range(1, 13):
        f = k / 12; p.append((r0 + (rT[i] - r0) * f + wbulge * math.sin(math.pi * f), plinthH + (yR - plinthH) * f))
    for k in range(1, 13):  # shoulder: quarter ellipse inward to the crest
        a = k / 12 * math.pi / 2; p.append((rT[i] - Rh * (1 - math.cos(a)), yR + Rv * math.sin(a)))
    rc = rT[i] - Rh
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
# Base (facade spec 2026-10-20, engineering/facade_spec_2026-10-20.md, rules 5 and 10; estimated): a light concrete
# step on the measured plinth outline, a white ring beam (bowl.base.ring_beam_h) under the lowest louvre, and under it
# a set-back ground floor in shadow with white piers, one per lattice bay (placed after the lattice bays are known,
# below). Not a continuous colonnade; no gates, exits or signs.
STEP, REC, BAND = V("bowl.base.step_h"), V("bowl.base.recess_depth"), V("bowl.base.ring_beam_h")
LIGHT = mat("concrete_light", (0.78, 0.77, 0.74), 0.85)
RECESS = mat("concrete_recess_dark", (0.16, 0.16, 0.155), 0.9)
SRC_BASE = ("design plan bowl_plinth_design_2026-10-17.csv (outline, fitted to W1b); ledger bowl.base.* (estimated, by eye "
            "from 001216.000, 001221.500, 000714.767), plinth_h")


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
ring_band("base_recess", "plinth", [(rRec, STEP), (rRec, plinthH - BAND)], RECESS, "estimated", SRC_BASE)
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
        f = (y - plinthH) / (yR - plinthH); return R0[i] + (rT[i] - R0[i]) * f + wbulge * math.sin(math.pi * f)
    return rT[i] - Rh * (1 - math.cos(math.asin(min((y - yR) / Rv, 1.0))))
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
FIN0 = 0.05  # lowest fin sits on the ring beam (facade spec 2026-10-20 rule 5; was 0.4 m, which left a dark band)
nf = int((yF - FIN_DROP - plinthH - FIN0) / FIN_P) + 1
for k in range(nf):
    y = plinthH + FIN0 + k * FIN_P; base = len(v)
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


# Diamond lattice (facade spec 2026-10-20, rules 1-5): K slim flat ribs per direction, square edges, standing
# bowl.lattice.section_d proud of the louvre faces. The top V points sit under the fascia line at equal arc length
# round the fascia (bay = perimeter / K), the first on the shield 0 axis; the bottom points sit directly below them
# on the ring beam. Each rib runs from a top V point to the bottom point one bay along, so two ribs cross in an X
# at mid-height between two V points. Joints are sharp mitres: each rib is clipped to its own bay by the vertical
# line through the V points at its ends and by the horizontal lines of the fascia and the ring beam, so the two
# ribs of a V meet on one line and never overlap in a round fork.
K = int(V("bowl.profile.lattice_members_704"))
lw, ld = V("bowl.lattice.section_w") / 2, V("bowl.lattice.section_d")
LAT = mat("white_shell_lattice", (0.85, 0.85, 0.83), 0.5)  # own material: hero_artistic.py keeps its bevel <= 0.03 m
Y_LO, Y_TOP = plinthH, yF
TH0 = math.radians(-bearing) - math.pi / 2  # shield 0 (shields loop below)
_th = TH0 + np.linspace(0, 2 * math.pi, 4801)


def _ring_len(y, th=_th):
    q = np.array([tuple(surf(t, j_at_height(y))) for t in th]); return np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(q, axis=0), axis=1))])


_cum = _ring_len(Y_TOP); _ucum = K * _cum / _cum[-1]
BAY = _cum[-1] / K


def th_u(u):
    """Angle of lattice coordinate u (bays from shield 0 along the fascia, equal arc length)."""
    return TH0 + float(np.interp(u % K, _ucum, _th - TH0))


_yy = np.linspace(Y_LO, Y_TOP, 24)
_mm = [_ring_len(y, TH0 + np.linspace(0, 2 * math.pi, 721))[-1] / K for y in _yy]
m_y = lambda y: float(np.interp(y, _yy, _mm))  # metres per bay unit at height y


def rib(ua, ub, off, n=40):
    """Mesh pieces (verts, faces) of one rib from the bottom point ua to the top V point ub (ub = ua +- 1)."""
    H = Y_TOP - Y_LO; du = ub - ua
    u_lo, u_hi = min(ua, ub), max(ua, ub)

    def pt(t, s):
        y = Y_LO + H * t; m = m_y(y); tx, ty = m * du, H; L_ = math.hypot(tx, ty); tx, ty = tx / L_, ty / L_
        return ua + du * t + s * lw * (-ty) / m, y + s * lw * tx

    def inside(t, s):
        u, y = pt(t, s); e = 1e-9
        return u_lo - e <= u <= u_hi + e and Y_LO - e <= y <= Y_TOP + e

    def span(s):
        if s == 0: return 0.0, 1.0
        ts = np.linspace(0, 1, 2001); ok = [inside(t, s) for t in ts]; i0 = ok.index(True); i1 = len(ok) - 1 - ok[::-1].index(True)
        def edge(a, b):  # a inside, b outside
            for _ in range(40):
                c = (a + b) / 2
                if inside(c, s): a = c
                else: b = c
            return a
        t0 = edge(ts[i0], ts[i0 - 1]) if i0 > 0 else 0.0
        t1 = edge(ts[i1], ts[i1 + 1]) if i1 < len(ts) - 1 else 1.0
        return t0, t1

    lines = []
    for s in (-1, 0, 1):
        t0, t1 = span(s); row = []
        for t in np.linspace(t0, t1, n):
            u, y = pt(t, s); th = th_u(u); j = j_at_height(y)
            row.append((tuple(surf(th, j, off)), tuple(surf(th, j, -0.3))))
        lines.append(row)
    v = [p for row in lines for pair in row for p in pair]  # index: ((line * n) + k) * 2 + (0 front, 1 back)
    I = lambda l, k, b: (l * n + k) * 2 + b
    f = []
    for k in range(n - 1):
        for l in (0, 1):
            f.append((I(l, k, 0), I(l + 1, k, 0), I(l + 1, k + 1, 0), I(l, k + 1, 0)))
            f.append((I(l, k + 1, 1), I(l + 1, k + 1, 1), I(l + 1, k, 1), I(l, k, 1)))
        f.append((I(0, k, 1), I(0, k, 0), I(0, k + 1, 0), I(0, k + 1, 1)))
        f.append((I(2, k + 1, 1), I(2, k + 1, 0), I(2, k, 0), I(2, k, 1)))
    for k in (0, n - 1):
        for l in (0, 1):
            f.append((I(l, k, 0), I(l + 1, k, 0), I(l + 1, k, 1), I(l, k, 1)))
    return v, f


lv, lf = [], []
for k in range(K):
    for sg, off in ((1, ld), (-1, ld - 0.008)):  # falling ribs 8 mm behind the rising ones, so the X crossings never z-fight
        v, f = rib(k, k + sg, off); b0 = len(lv); lv += v; lf += [tuple(b0 + q for q in face) for face in f]
me = bpy.data.meshes.new("lattice"); me.from_pydata(lv, [], lf); me.validate(); me.update()
bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
lo = bpy.data.objects.new("lattice", me); coll("facade_detail").objects.link(lo); me.materials.append(LAT)
lo["claim"] = "estimated"; lo["sources"] = ("ledger bowl.profile.lattice_members_704, bowl.lattice.section_w, bowl.lattice.section_d "
                                            "(2026-10-20 rows, engineering/facade_spec_2026-10-20.md)")
# Ring beam (spec rule 5): white band bowl.base.ring_beam_h high under the lowest louvre, its face on the wall line
# at the foot (never inside the plinth face), from the recess wall out
rBeam = [max(rPl[i], rw(i, plinthH)) for i in range(N)]
ring_band("base_band", "plinth", [(rRec, plinthH - BAND), (rBeam, plinthH - BAND), (rBeam, plinthH), (rRec, plinthH)], WHITE, "estimated", SRC_BASE)
# White piers under the ring beam, one per bay under the bottom points (spec rule 10); kept as "base_columns" for
# the web_hero bake groups
cw = V("bowl.base.column_w") / 2
v, f = [], []
for k in range(K):
    th = th_u(k); ux, uz = math.cos(th), math.sin(th)
    i = int(round(th / (2 * math.pi) * N)) % N; r0 = rBeam[i] - cw - 0.3
    tx, tz = -uz, ux; base = len(v)
    for y in (0.0, plinthH - BAND):  # from the ground: where the wall overhangs, the pier stands outside the plinth step
        for su, so in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            v.append((ux * r0 + tx * su * cw + ux * so * cw, Y(y), uz * r0 + tz * su * cw + uz * so * cw))
    f += [(base + q, base + (q + 1) % 4, base + 4 + (q + 1) % 4, base + 4 + q) for q in range(4)]
obj("base_columns", "plinth", v, f, WHITE, "estimated", SRC_BASE)
print("LATTICE " + json.dumps({"K": K, "bay_m": round(BAY, 2), "fascia_perimeter_m": round(_cum[-1], 1), "y_lo": round(Y_LO, 2),
                                "y_top": round(Y_TOP, 2), "beam_out_of_plinth_m": round(max(a - b for a, b in zip(rBeam, rPl)), 2)}), flush=True)
nrib = int(VO("bowl.roof.cushion_bays", V("bowl.roof.ribs")))  # topside ribs bound the cushion bays (001221.500, 001224.500)
# ribs half sunk into the membrane (stage 02b: 12:40 shows a smooth membrane with faint seams, not raised tubes)
ribs = [[surf(2 * math.pi * k / nrib, j, 0) + Vector((0, 0, 0.1 - V("bowl.roof.rib_r"))) for j in np.linspace(J_FACADE, NP - 1, 14)] for k in range(nrib)]
curve_obj("roof_ribs", "facade_detail", ribs, V("bowl.roof.rib_r"), WHITE, sources="ledger bowl.roof.ribs (estimated)")
# Cushion roof (JWNowpO44rw 001221.500 to 001239.267): between each pair of radial ribs, rows of inflated
# cushions from the crest to the opening. Each cushion is a patch of the fitted roof surface lifted by
# bowl.roof.cushion_bulge * sin(pi u) sin(pi v), so the seams at the ribs and between rows stay on the surface
# and the bulges catch the light. Rows and bulge: ledger (estimated, by eye from the frames).
NROW, HB = int(VO("bowl.roof.cushion_rows", 8)), VO("bowl.roof.cushion_bulge", 0.45)
NU, NV = 8, 6
# pillow shape: an exponent under 1 flattens the top and steepens the seams (inflated cushions, 001033.567, 001232.600)
PILLOW = VO("bowl.roof.cushion_pillow", 1.0)
# roof_fix_01 (pass B, 2026-10-21): D03 000617.567 shows two cushion columns in each topside-rib bay (seam pitch half
# the rib pitch on the solved camera), so each bay is split (ledger bowl.roof.cushion_cols_per_bay)
NCOL = nrib * int(VO("bowl.roof.cushion_cols_per_bay", 1))
cv, cf = [], []
for k in range(NCOL):
    ta, tb = 2 * math.pi * k / NCOL, 2 * math.pi * (k + 1) / NCOL
    for jr in range(NROW):
        ja = J_FACADE + (NP - 1 - J_FACADE) * jr / NROW; jb = J_FACADE + (NP - 1 - J_FACADE) * (jr + 1) / NROW
        base = len(cv)
        for a in range(NU + 1):
            for b in range(NV + 1):
                q = surf(ta + (tb - ta) * a / NU, ja + (jb - ja) * b / NV, 0)
                q.z += HB * (math.sin(math.pi * a / NU) * math.sin(math.pi * b / NV)) ** PILLOW
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

# Shield image: our own drawing from simple shapes (blender/shield_paint.py), never a frame pixel. Paint colours and the
# lens outline from the ledger (pass A, 2026-10-21: bowl.shield.red, black, outline_a/_b tuned in F16 renders against 001216.000).
def shield_png(path, w=512, h=1024):
    sys.path.insert(0, str(ROOT / "blender")); import shield_paint
    img = shield_paint.draw(w, h, L["bowl.shield.red"]["value"], L["bowl.shield.black"]["value"],
                            V("bowl.shield.outline_a"), V("bowl.shield.outline_b"))
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
pb.inputs["Roughness"].default_value = V("bowl.shield.roughness"); pb.inputs["Metallic"].default_value = 0.0  # matte paint
pb.inputs["Specular IOR Level"].default_value = VO("bowl.shield.specular", 0.5)  # pass A: low sheen, no sky veil on the red
sm.diffuse_color = (0.42, 0.06, 0.12, 1)
SPEAR = mat("spear_white", (0.92, 0.92, 0.9), 0.35)
axisA = math.radians(-bearing); sw = V("bowl.shield.width")
# facade spec 2026-10-20 rule 6: each shield is centred on a V line (every third bay), its top at the top V point
# under the fascia and its foot at the bottom point on the ring beam (supersedes blockout_y0/y1 and centre_y)
sy0, sy1 = Y_LO, Y_TOP
NSH = int(V("bowl.shields.count")); SH_EVERY = K // NSH
bulge, soff = V("bowl.shield.bulge"), V("bowl.shield.offset")
span, bl, br, srad = V("bowl.spear.span_shields"), V("bowl.spear.blade_len"), V("bowl.spear.blade_r"), V("bowl.spear.radius")
BW = V("bowl.spear.blade_width_ratio") * srad  # blade half-width: max blade width = ratio x shaft diameter
tip_y = yF - V("bowl.spear.tip_below_fascia")
verts, faces, uvs, spear_paths = [], [], [], []
for k in range(NSH):
    th = th_u(k * SH_EVERY)
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
            if m <= bl:  # leaf blade (pass A, 2026-10-20): pointed tip, widest 62 % of the way down, flat
                x = min(max(m / bl, 0.0), 1.0)
                r = BW * (x / 0.62) ** 0.85 if x <= 0.62 else srad + (BW - srad) * math.cos((x - 0.62) / 0.38 * math.pi / 2)
                pts[q].append((r, min(r, srad) * 0.6)); continue
            r = srad * min(1.0, 0.25 + 0.75 * acc / 2.5)
            pts[q].append((r, r))
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
