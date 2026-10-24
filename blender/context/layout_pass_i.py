"""Pass I (engineering/layout_audit_01/LEAD_REVIEW.md, revision 2, 2026-10-23): the layout fix, finished state only.

Pass F (layout_final.py) took its layout from research/reference/dusk_aerial_finished_2026-10-17.jpg, which is an
AI-generated image. Pass I withdraws that layout: this script replaces layout_final.py in the chain and runs on step_FE,
so the west road, railway, station, footbridge, both car parks, the spine beds, the road between the pitches and the
dark track recolour are not built, and every object pass F hid or cut is back uncut (west forecourt lawn and paths,
sw_lawn, sw_stand, the trees, the fence, the facade apron, the OSM roads, the traffic, the terracotta track ring).
It adds, from blender/data/layout_pass_i.json:
- the east approach (audit fix 3): a pale paved area between the training pitches with a raised planted island (a long
  pointed lens since pass K, K3; it was a four-corner diamond), its
  west edge on the outer edge of the bowl apron and its east end open to the peripheral route; no lanes, no cars;
- the junction with the peripheral route ge_road_north_east (audit fix 6): the road surface stops at the paved edge,
  and no tree stands in the approach or the junction;
- the south-west area (audit fix 1): grass inside the loop road, no pitch markings; the loop road stays.
It keeps the pass F changes that other sources support: the red murram forecourt paths and beds, the old OSM footways
dropped inside the W1b site (drone frames 000645.000, 000659.633), and the car figures for the east hardstanding
and the Ngong Road traffic (Visualization). No vehicle route crosses the north plaza or enters the bowl.
Shared objects get a cut copy (state_only "finished") and keep the uncut original for the asbuilt state
(blender/scene_state.py); the asbuilt state does not change.
Run from the repo root: TALANTA_SITE_BLEND=blender/out/step_FI.blend ~/.venvs/bpy/bin/python blender/context/layout_pass_i.py
"""
import csv, json, math, os, sys
from pathlib import Path
import numpy as np
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import delaunay_2d_cdt

ROOT = Path(__file__).resolve().parents[2]
D = json.loads((ROOT / "blender/data/layout_pass_i.json").read_text())
VIS = "Visualization: generic parked and moving cars; not a count, occupancy or traffic study"
rng = np.random.default_rng(2310)
bpy.ops.wm.open_mainfile(filepath=os.environ.get("TALANTA_SITE_BLEND", str(ROOT / "blender/out/talanta_site.blend")))
scene = bpy.context.scene
sys.path.insert(0, str(ROOT / "blender")); import scene_state as SS
report = {}


def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in scene.collection.children: scene.collection.children.link(c)
    for o in list(c.objects): bpy.data.objects.remove(o)
    return c


COL = coll("layout_pass_i")
CARS = coll("layout_cars_visualization")

# ---------------------------------------------------------------- ground
dg = bpy.context.evaluated_depsgraph_get()
BVH = []
for tn in ("terrain_site", "terrain_far"):
    t = bpy.data.objects.get(tn)
    if not t: continue
    tm = t.evaluated_get(dg).to_mesh()
    BVH.append(BVHTree.FromPolygons([t.matrix_world @ v.co for v in tm.vertices], [p.vertices[:] for p in tm.polygons]))
    t.evaluated_get(dg).to_mesh_clear()


def ground(x, z):
    for b in BVH:
        hit = b.ray_cast(Vector((x, -z, 3000.0)), Vector((0, 0, -1)))
        if hit[0] is not None: return hit[0].z
    return 0.0


def srgb(h):
    h = h.lstrip("#"); return tuple(((int(h[i:i + 2], 16) / 255 + 0.055) / 1.055) ** 2.4 for i in (0, 2, 4))


def mat(name, hx, rough=0.85, metal=0.0):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*srgb(hx), 1); p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal; m.diffuse_color = (*srgb(hx), 1)
    return m


PAVE = bpy.data.materials.get("fc_paving") or mat("pi_paving", "#C9C2B6")  # the ge_apron_ring material
KERB = bpy.data.materials.get("fc_kerb") or mat("pi_kerb", "#AAA48F", 0.8)
GRASS = bpy.data.materials.get("fc_grass") or mat("pi_grass", "#4F6E3B", 0.9)
MURRAM = bpy.data.materials.get("fc_murram") or mat("pi_murram", "#8E4A30", 0.95)
GLASS = bpy.data.materials.get("parked_glass") or mat("parked_glass", "#1D262C", 0.15)


def bed_material():
    """Murram bed with planted wedges: a red laterite base broken by dark green planted strips (stretched noise)."""
    m = bpy.data.materials.get("lf_murram_bed")
    if m: return m
    m = bpy.data.materials.new("lf_murram_bed"); m.use_nodes = True; nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (0.35, 0.09, 1.0)
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 3.0; nz.inputs["Detail"].default_value = 3.0
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].position = 0.5; ramp.color_ramp.elements[1].position = 0.56
    ramp.color_ramp.elements[0].color = (*srgb("#7A4632"), 1); ramp.color_ramp.elements[1].color = (*srgb("#3A5230"), 1)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.95; m.diffuse_color = (*srgb("#7A4A30"), 1)
    return m


BEDS = bed_material()


def obj(name, verts, faces, mats, claim, collection=None, mat_idx=None):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.validate(); me.update()
    for m in mats: me.materials.append(m)
    if mat_idx is not None:
        for p, i in zip(me.polygons, mat_idx): p.material_index = i
    o = bpy.data.objects.new(name, me); (collection or COL).objects.link(o)
    o["claim"] = claim; o["state_only"] = "finished"
    return o


def inside(p, ring):
    x, y = p; yes = False
    for (ax, ay), (bx, by) in zip(ring, ring[1:] + ring[:1]):
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax: yes = not yes
    return yes


def seg_dist(p, a, b):
    a, b, p = np.asarray(a, float), np.asarray(b, float), np.asarray(p, float); d = b - a
    t = np.clip(np.dot(p - a, d) / max(np.dot(d, d), 1e-9), 0, 1)
    return float(np.linalg.norm(p - a - t * d))


def near(p, ring, buf):
    """Inside the ring, or within buf metres of its edge."""
    return inside(p, ring) or (buf > 0 and min(seg_dist(p, a, b) for a, b in zip(ring, ring[1:] + ring[:1])) <= buf)


def resample(pts, step):
    P = np.array(pts, float); d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    s = np.linspace(0, d[-1], max(2, int(d[-1] / step) + 1))
    return np.c_[np.interp(s, d, P[:, 0]), np.interp(s, d, P[:, 1])]


def surface(name, ring, material, lift, claim, step=4.0, height=None):
    """Polygon draped on the ground (or flat at height): boundary plus an interior grid, constrained Delaunay."""
    R = [tuple(map(float, p)) for p in ring]
    B = [tuple(p) for p in resample(R + [R[0]], step)[:-1]]
    xs, zs = [p[0] for p in R], [p[1] for p in R]
    pts = list(B)
    for x in np.arange(min(xs) + step / 2, max(xs), step):
        for z in np.arange(min(zs) + step / 2, max(zs), step):
            if inside((x, z), R) and min(math.dist((x, z), q) for q in B) > step * 0.4: pts.append((x, z))
    out = delaunay_2d_cdt([Vector(p) for p in pts], [(i, (i + 1) % len(B)) for i in range(len(B))], [], 0, 1e-4)
    V2, F2 = out[0], out[2]
    keep = [f for f in F2 if inside(tuple(sum((V2[i] for i in f), Vector((0, 0))) / 3), R)]
    v = [(p.x, -p.y, (ground(p.x, p.y) if height is None else height) + lift) for p in V2]
    return obj(name, v, [tuple(f) for f in keep], [material], claim), B


# ---------------------------------------------------------------- east approach outline
EA = D["east_approach"]; CLAIM_EA = EA["claim"] + "; source " + EA["source"]
apron = bpy.data.objects.get("ge_apron_ring")
(ex0, ez0), (ex1, ez1), (ex2, ez2), (ex3, ez3) = EA["ring"]  # SW, NW, NE, SE corners as in the review
west = []
if apron:  # outer edge of the apron between the two west corners (vertex pairs inner, outer; see site_layout_ge.py)
    M = apron.matrix_world; vs = apron.data.vertices
    outer = [(M @ vs[i].co) for i in range(1, len(vs), 2)]
    west = sorted([(p.x - 0.5, -p.y) for p in outer if p.x > 0 and ez1 - 6 <= -p.y <= ez0 + 6], key=lambda q: -q[1])
# outline: south-west corner, along the apron edge to the north-west corner, then the review's two east corners
APPROACH = (west or [(ex0, ez0), (ex1, ez1)]) + [(ex2, ez2), (ex3, ez3)]
ROAD = bpy.data.objects.get("ge_road_north_east")


def island_ring(spec):
    """Pass K (K3): long pointed lens between the two tips; half-width (W / 2) * 4t(1 - t) along the axis (parabolic
    sides, pointed tips, widest at the middle). Returns spec["points"] points, counter-clockwise in the app plan."""
    (ax_, az_), (bx_, bz_) = spec["tips"]; W = spec["max_width_m"]; n = spec["points"] // 2
    L = math.hypot(bx_ - ax_, bz_ - az_); ux, uz = (bx_ - ax_) / L, (bz_ - az_) / L; vx, vz = -uz, ux
    ts = [k / n for k in range(n + 1)]
    side = lambda t, s: (ax_ + ux * L * t + vx * s * W / 2 * 4 * t * (1 - t), az_ + uz * L * t + vz * s * W / 2 * 4 * t * (1 - t))
    R = [side(t, 1) for t in ts] + [side(t, -1) for t in reversed(ts[1:-1])]
    return R if sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(R, R[1:] + R[:1])) > 0 else R[::-1]


ISL = island_ring(EA["island"]); CLEAR = EA["tree_clear_m"]


def in_approach(x, z, buf=0.0): return near((x, z), APPROACH, buf)


# ---------------------------------------------------------------- clearing (finished state only)
SKIP_COLL = {"layout_pass_i", "layout_cars_visualization", "shell", "facade_detail", "roof_detail", "bowl_detail", "tiers",
             "plinth", "night_lights", "bowl_protos", "site_protos", "site_trees_protos", "atmosphere",
             "people_visualization"}  # people may stand on the approach; whole figures are not cut
KEEP = {"terrain_site", "terrain_far", "ge_apron_ring", "suburbs_buildings", "buildings", "warmup_track_ne",
        "warmup_track_ne_infield", "training_pitch_se_turf", "haze_volume", "site_pad"}
cut_report = {"hidden": [], "cut": [], "copied": []}


def mark_finished_hidden(o, why):
    if SS._finished_only(o): o["state_hide_render"] = True; o.hide_render = True
    else: o["state_only"] = "asbuilt"
    cut_report["hidden"].append([o.name, why])


def cut_object(o, test, why):
    """Delete faces (centre test) or loose vertices (point clouds) that pass test(x, z). Finished-only objects are cut
    in place; shared objects get a cut copy for the finished state and keep the uncut original for asbuilt."""
    def run(target):
        bm = bmesh.new(); bm.from_mesh(target.data); M = target.matrix_world
        if len(bm.faces):
            dead = [fc for fc in bm.faces if test(*(lambda c: (c.x, -c.y))(M @ fc.calc_center_median()))]
            bmesh.ops.delete(bm, geom=dead, context="FACES")
        else:
            dead = [vv for vv in bm.verts if test((M @ vv.co).x, -(M @ vv.co).y)]
            bmesh.ops.delete(bm, geom=dead, context="VERTS")
        bm.to_mesh(target.data); bm.free(); target.data.update(); return len(dead)
    if SS._finished_only(o):
        n = run(o)
        if n: cut_report["cut"].append([o.name, n, why])
        return n
    c = o.copy(); c.data = o.data.copy(); c.name = o.name + "_final"
    for cl in o.users_collection: cl.objects.link(c)
    n = run(c)
    if n: c["state_only"] = "finished"; o["state_only"] = "asbuilt"; cut_report["copied"].append([o.name, n, why])
    else: bpy.data.objects.remove(c)
    return n


def bbox_plan(o):
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return min(v.x for v in bb), max(v.x for v in bb), min(-v.y for v in bb), max(-v.y for v in bb)


def candidates():
    for o in list(scene.objects):
        if o.type != "MESH" or o.name in KEEP or o.get("state_only") == "asbuilt": continue
        if any(c.name in SKIP_COLL or c.name in SS.ONLY_ASBUILT for c in o.users_collection): continue
        if o.get("state_hide_render", o.hide_render): continue  # hidden in both states already
        yield o


ax0, ax1 = min(p[0] for p in APPROACH) - CLEAR, max(p[0] for p in APPROACH) + CLEAR
az0, az1 = min(p[1] for p in APPROACH) - CLEAR, max(p[1] for p in APPROACH) + CLEAR
is_tree = lambda o: len(o.data.polygons) == 0 or any(k in o.name for k in ("tree", "euc", "palm", "crown", "canopy", "shrub"))
for o in candidates():
    x0, x1, z0, z1 = bbox_plan(o)
    if x1 < ax0 or x0 > ax1 or z1 < az0 or z0 > az1: continue
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2; small = (x1 - x0) < 30 and (z1 - z0) < 30
    if o == ROAD: continue  # handled below: the road stops at the paved edge
    if small:  # single trees, lamps, plants: out of the approach and the junction
        if in_approach(cx, cz, CLEAR if is_tree(o) else 0.0): mark_finished_hidden(o, "east approach")
        continue
    buf = CLEAR if len(o.data.polygons) == 0 else 0.0  # scatter point clouds (trees, shrubs, palms) get the margin
    cut_object(o, lambda x, z, b=buf: ax0 <= x <= ax1 and az0 <= z <= az1 and in_approach(x, z, b), "east approach")
if ROAD:
    report["road_cut_faces"] = cut_object(ROAD, lambda x, z: in_approach(x, z), "east approach junction")

# old OSM footways inside the W1b site boundary (kept from pass F, source now the drone frames 000645.000, 000659.633)
SITE = [(float(r["x_east"]), float(r["z_south"])) for r in csv.DictReader(open(ROOT / "gis/measurements/normalized/site_boundary_w1b_2026-10-16.csv"))]
for name in ("roads", "road_markings"):
    o = bpy.data.objects.get(name)
    if not o: continue
    c = o.copy(); c.data = o.data.copy(); c.name = name + "_final"
    for cl in o.users_collection: cl.objects.link(c)
    bm = bmesh.new(); bm.from_mesh(c.data); M = c.matrix_world
    dead = [fc for fc in bm.faces if any(inside(((M @ vv.co).x, -(M @ vv.co).y), SITE) for vv in fc.verts)]
    bmesh.ops.delete(bm, geom=dead, context="FACES"); bm.to_mesh(c.data); bm.free(); c.data.update()
    if dead: c["state_only"] = "finished"; o["state_only"] = "asbuilt"; cut_report["copied"].append([name, len(dead), "OSM footways inside W1b"])
    else: bpy.data.objects.remove(c)

# ---------------------------------------------------------------- east approach surfaces
pave, _ = surface("pi_east_approach", APPROACH, PAVE, 0.05, CLAIM_EA, step=4.0)
# raised planted island: kerb walls round a planted top, a level top at the highest ground under it plus the kerb
gtop = max(ground(*p) for p in resample(ISL + [ISL[0]], 2.0)) + 0.05 + EA["island_kerb_m"]
CLAIM_ISL = EA["island"]["claim"] + "; " + EA["island_kerb_claim"] + "; source " + EA["island"]["source"]
top, B = surface("pi_east_approach_island", ISL, BEDS, 0.0, CLAIM_ISL, step=2.0, height=gtop)
v, f = [], []
for (x, z) in B: v += [(x, -z, ground(x, z) + 0.02), (x, -z, gtop + 0.01)]
n = len(B)
for i in range(n): j = (i + 1) % n; f.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
obj("pi_east_approach_island_kerb", v, f, [KERB], CLAIM_ISL)
area = lambda R: abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(R, R[1:] + R[:1]))) / 2
report["east_approach"] = {"area_m2": round(area(APPROACH)), "island_area_m2": round(area(ISL)), "island_points": len(ISL), "west_edge_points": len(west)}

# ---------------------------------------------------------------- south-west: grass inside the loop road, no markings
SW = D["south_west_grass"]; CLAIM_SW = SW["claim"] + "; source " + SW["source"]
hidden_lines = []
for o in list(scene.objects):
    if o.type == "MESH" and o.name.startswith("sw_pitch_lines") and not o.get("state_only") == "asbuilt":
        mark_finished_hidden(o, "south-west: no pitch markings (LEAD_REVIEW item 3)"); hidden_lines.append(o.name)
# the merged training pitch lines (sport) also mark this lawn: cut them inside the lawn (sw_lawn box, or the ring)
lawn = bpy.data.objects.get("sw_lawn")
lb = bbox_plan(lawn) if lawn else None
in_sw = lambda x, z: inside((x, z), SW["ring"]) or (lb is not None and lb[0] <= x <= lb[1] and lb[2] <= z <= lb[3])
for o in list(scene.objects):
    if o.type == "MESH" and o.name.startswith("training_pitch_lines") and o.get("state_only") != "asbuilt":
        n = cut_object(o, in_sw, "south-west: no pitch markings (LEAD_REVIEW item 3)")
        if n: hidden_lines.append(f"{o.name} ({n} faces)")
SS.set_state(scene, "finished")
grass_cover = []  # visible lawn objects in the finished state that cover the ring centre
cx, cz = np.mean([p[0] for p in SW["ring"]]), np.mean([p[1] for p in SW["ring"]])
hit = None
for o in scene.objects:
    if o.type != "MESH" or o.hide_render or not len(o.data.polygons): continue
    x0, x1, z0, z1 = bbox_plan(o)
    if x0 <= cx <= x1 and z0 <= cz <= z1 and any(m and ("grass" in m.name or "lawn" in m.name or "turf" in m.name) for m in o.data.materials):
        grass_cover.append(o.name)
if not grass_cover:
    surface("pi_sw_grass", SW["ring"], GRASS, 0.1, CLAIM_SW, step=4.0); grass_cover.append("pi_sw_grass (new)")
report["south_west"] = {"grass": grass_cover, "markings_hidden": hidden_lines}

# ---------------------------------------------------------------- north-west: west forecourt lawn and paths shown
NW = D["north_west_lawn"]
report["north_west"] = {n: [o.name for o in scene.objects if o.name.startswith(n) and not o.hide_render][:3] for n in NW["objects"]}

# ---------------------------------------------------------------- kept from pass F: red murram paths and beds
recol = []
for name, m in (("fp_paths", MURRAM), ("fp_beds", BEDS)):
    o = bpy.data.objects.get(name)
    if o: o.data.materials.clear(); o.data.materials.append(m); recol.append(name)
fm = bpy.data.materials.get("fc_murram")
if fm and not fm.get("lf_red"):  # fc_murram rendered pale beige through its legacy mix; the frames show red laterite
    nt = fm.node_tree; p = nt.nodes["Principled BSDF"]
    for l in list(p.inputs["Base Color"].links): nt.links.remove(l)
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.6
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (*srgb("#7C412D"), 1); ramp.color_ramp.elements[1].color = (*srgb("#A0593C"), 1)
    ramp.color_ramp.elements[0].position = 0.3; ramp.color_ramp.elements[1].position = 0.7
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])
    fm["lf_red"] = "pass I: red laterite as in the drone frames 000645.000, 000659.633"; recol.append("fc_murram")
report["recoloured"] = recol

# ---------------------------------------------------------------- kept from pass F: car figures (Visualization)
PAINTS = [("#E9E9E6", 0.33), ("#B9BCBF", 0.2), ("#6A6E72", 0.12), ("#141518", 0.15), ("#1F2F4F", 0.06), ("#8C1C1C", 0.05),
          ("#C8B897", 0.05), ("#2F4A36", 0.04)]
CPM = [mat(f"lf_car_paint_{i}", h, 0.3, 0.5) for i, (h, _) in enumerate(PAINTS)]
CPW = np.array([w_ for _, w_ in PAINTS]); CPW /= CPW.sum()
TYRE = mat("lf_tyre", "#111111", 0.8)
car_bm = {"v": [], "f": [], "mi": []}


def box_faces(b):
    return [(b, b + 1, b + 2, b + 3), (b + 4, b + 7, b + 6, b + 5), (b, b + 4, b + 5, b + 1), (b + 1, b + 5, b + 6, b + 2),
            (b + 2, b + 6, b + 7, b + 3), (b + 3, b + 7, b + 4, b)]


def oriented_box(v, f, c, u, w, L, W, z0, z1):
    b = len(v)
    for zz in (z0, z1):
        for su, sw in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            x, z = c + u * su * L / 2 + w * sw * W / 2; v.append((x, -z, zz))
    f += box_faces(b)


def car(x, z, ang, ci=None):
    """Low-poly car (body, glass cabin, painted roof, tyres), front along ang (radians, plan), sitting on the ground."""
    if ci is None: ci = int(rng.choice(len(CPM), p=CPW))
    u = np.array([math.cos(ang), math.sin(ang)]); w = np.array([-u[1], u[0]]); g = ground(x, z) + 0.14
    L_, W_ = rng.uniform(4.2, 4.9), rng.uniform(1.75, 1.9); c = np.array([x, z])
    v, f, mi = car_bm["v"], car_bm["f"], car_bm["mi"]
    oriented_box(v, f, c, u, w, L_, W_, g + 0.25, g + 0.95); mi += [ci] * 6
    oriented_box(v, f, c - u * 0.25, u, w, L_ * 0.55, W_ * 0.9, g + 0.95, g + 1.38); mi += [len(CPM)] * 6
    oriented_box(v, f, c - u * 0.25, u, w, L_ * 0.5, W_ * 0.86, g + 1.38, g + 1.45); mi += [ci] * 6
    oriented_box(v, f, c, u, w, L_ * 0.82, W_ * 0.96, g, g + 0.3); mi += [len(CPM) + 1] * 6


old = bpy.data.objects.get("parked_cars_visualization")  # pass E white boxes, two boxes (16 vertices) per car
if old:
    n_old = n_skip = 0
    co = np.array([tuple(old.matrix_world @ vv.co) for vv in old.data.vertices])
    for k in range(0, len(co) - 15, 16):
        body = co[k:k + 8, :2]; cxy = body.mean(0)
        if in_approach(cxy[0], -cxy[1]): n_skip += 1; continue  # no cars on the east approach
        _, _, Vt = np.linalg.svd(body - cxy); ax_ = Vt[0]
        car(cxy[0], -cxy[1], math.atan2(-ax_[1], ax_[0])); n_old += 1
    old["state_hide_render"] = True; old.hide_render = True
    report["cars_east_replaced"] = n_old; report["cars_east_dropped_on_approach"] = n_skip
tr = bpy.data.objects.get("traffic_Visualization")  # pass D boxes, eight vertices per box, in order
if tr:
    co = np.array([tuple(tr.matrix_world @ vv.co) for vv in tr.data.vertices]); n_tr = n_bus = 0
    boxes = co[: len(co) // 8 * 8].reshape(-1, 8, 3)
    # traffic.py writes each vehicle as body, cabin, (bus skirt), four wheels: a body is a large box after a small one
    big = [float(np.ptp(bx[:, 0])) ** 2 + float(np.ptp(bx[:, 1])) ** 2 > 9.0 for bx in boxes]
    for k, b in enumerate(boxes):
        if not big[k] or (k > 0 and big[k - 1]): continue
        xy = b[:, :2]; c = xy.mean(0)
        _, sv, Vt = np.linalg.svd(xy - c); ax_ = Vt[0]; L_ = float(np.ptp((xy - c) @ ax_)); W_ = float(np.ptp((xy - c) @ Vt[1]))
        if L_ < 6.0:
            car(c[0], -c[1], math.atan2(-ax_[1], ax_[0])); n_tr += 1
        else:  # matatu (7 m) or bus (11 m): plain body, a dark glass band, pale roof
            g = ground(c[0], -c[1]) + 0.14; Hh = 2.7 if L_ < 9 else 3.2
            u = np.array([ax_[0], -ax_[1]]); w = np.array([-u[1], u[0]]); cc = np.array([c[0], -c[1]])
            v_, f_, mi_ = car_bm["v"], car_bm["f"], car_bm["mi"]; ci = 0 if L_ >= 9 else int(rng.choice(len(CPM), p=CPW))
            oriented_box(v_, f_, cc, u, w, L_, W_, g + 0.3, g + Hh * 0.55); mi_ += [ci] * 6
            oriented_box(v_, f_, cc, u, w, L_ - 0.2, W_ - 0.04, g + Hh * 0.55, g + Hh * 0.9); mi_ += [len(CPM)] * 6
            oriented_box(v_, f_, cc, u, w, L_, W_, g + Hh * 0.9, g + Hh); mi_ += [ci] * 6
            oriented_box(v_, f_, cc, u, w, L_ * 0.85, W_ * 0.96, g, g + 0.32); mi_ += [len(CPM) + 1] * 6
            n_bus += 1
    tr["state_only"] = "asbuilt"
    report["traffic_figures"] = {"cars": n_tr, "buses": n_bus}
me = bpy.data.meshes.new("layout_cars_visualization"); me.from_pydata(car_bm["v"], [], car_bm["f"]); me.update()
for m in CPM + [GLASS, TYRE]: me.materials.append(m)
for p, i in zip(me.polygons, car_bm["mi"]): p.material_index = i
o = bpy.data.objects.new("layout_cars_visualization", me); CARS.objects.link(o); o["claim"] = VIS; o["state_only"] = "finished"

# ---------------------------------------------------------------- checks
# no vehicle route across the north plaza or into the bowl (audit fix 9): nothing in this pass adds one
SS.set_state(scene, "finished")
report["clearing"] = {"hidden": len(cut_report["hidden"]), "cut": cut_report["cut"], "copied": cut_report["copied"]}
print("LAYOUT_PASS_I " + json.dumps(report), flush=True)
(ROOT / "blender/out/layout_pass_i_report.json").write_text(json.dumps({"report": report, "hidden": cut_report["hidden"]}, indent=1))
bpy.ops.wm.save_mainfile()
