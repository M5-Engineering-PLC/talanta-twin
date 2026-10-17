"""Stage 01: Blender blockout of the fully built stadium, from the parameter ledger.

Reads gis/parameter_ledger.csv and the normalized W1b outlines in gis/measurements/normalized/
(gis/scripts/normalize_shapes.py). Builds named
collections: plinth, shell (facade and roof), tiers, pitch, forecourt, sport, ground.
Every object carries its sources and a claim level ("measured" or "estimated") as custom
properties, and the glTF export keeps them as extras.

Shell plan: ground edge = W1b plinth outline; widest point of the facade = W1b roof outer ring;
roof opening = W1b roof inner ring. The two roof rings are corrected for the relief shift
of the oblique image. Heights are estimates (ledger) until stage 01b.

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
V = lambda k: float(L[k]["value"])
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
plinth = outline("bowl_plinth_w1b_2026-10-17.csv")
roof_out = outline("roof_outer_w1b_2026-10-17.csv", shift)
roof_in = outline("roof_inner_w1b_2026-10-17.csv", shift)
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

plinthH, bulgeY = V("bowl.plinth_h"), V("bowl.bulge_y")
topY, openY, shoulderW, sag = V("bowl.roof_top_y"), V("bowl.opening_y"), V("bowl.shoulder_w"), V("bowl.roof_sag")
facadeInset = V("bowl.facade_inset")

# Profile (radius, height) at direction i, from the ground edge to the opening.
def profile(i):
    p = [(rPl[i], 0.0), (rPl[i], plinthH)]
    # facade foot vs plinth face as in bowl.js (estimated), never outside the widest ring
    r0 = min(rPl[i] + V("bowl.plinth_inset") - facadeInset, rRo[i])
    for k in range(1, 13):  # lean out to the widest point (roof outer ring) at bulgeY
        f = k / 12; p.append((r0 + (rRo[i] - r0) * math.sin(f * math.pi / 2), plinthH + (bulgeY - plinthH) * f))
    for k in range(1, 13):  # shoulder: quarter ellipse inward to the crest
        a = k / 12 * math.pi / 2; p.append((rRo[i] - shoulderW * (1 - math.cos(a)), bulgeY + (topY - bulgeY) * math.sin(a)))
    rc = rRo[i] - shoulderW
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

SRC_PL = "W1b bowl_plinth_w1b_2026-10-17.csv (measured); plinth_h, facade_inset (estimated)"
SRC_SH = "W1b plinth, roof_outer, roof_inner (measured, relief-corrected); heights bulge_y, roof_top_y, opening_y, shoulder_w (estimated)"
plinth_o = loft("plinth", "plinth", 0, 1, GLASS, "plan measured, height estimated", SRC_PL)
# soffit: flat ring from the plinth top in to the facade foot
v, f = [], []
for i in range(N):
    ux, uz = dirs[i]; rf = PROF[i][2][0]; v += [(ux * rPl[i], Y(plinthH), uz * rPl[i]), (ux * rf, Y(plinthH), uz * rf)]
for i in range(N):
    a, b = 2 * i, 2 * ((i + 1) % N); f.append((a, a + 1, b + 1, b))
obj("soffit", "plinth", v, f, WHITE, "estimated", SRC_PL)
facade = loft("facade", "shell", 2, J_FACADE, WHITE, "plan measured, heights estimated", SRC_SH)
roof = loft("roof", "shell", J_FACADE, NP - 1, MEMB, "plan measured, heights estimated", SRC_SH)

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
blend = ROOT / "blender/out/talanta_blockout.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
glb = ROOT / "app/public/data/blockout.glb"
bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", export_extras=True, export_cameras=False, export_lights=False, export_apply=True)
tri = 0
for o in scene.objects:
    if o.type == "MESH": o.data.calc_loop_triangles(); tri += len(o.data.loop_triangles)
print(json.dumps({"roof_outer_clamped_dirs": CLAMPED, "blend": str(blend), "blend_mb": round(blend.stat().st_size / 2**20, 2), "glb": str(glb), "glb_mb": round(glb.stat().st_size / 2**20, 2), "triangles": tri,
                  "collections": {k: [o.name for o in c.objects] for k, c in COLS.items()}}, indent=1))
