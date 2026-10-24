"""Pass K, K2 (engineering/cloud_pass_k_2026-10-24.md, 2026-10-24): the south plaza, finished state only.

D02 (JWNowpO44rw_000714.767) shows a broad pale plaza south of the bowl, east of the south-west grass loop, with a round
bed in the centre and long axial beds. The model had lawn and paths there; no plaza object existed in any state.
From blender/data/plaza_south_k.json (outline and beds: estimate from a camera solve, +-25 m) it builds:
- the paving, draped on the ground, its north edge on the outer edge of ge_apron_ring so it joins the outer apron;
- a kerb round the paving edge away from the apron;
- the round bed (a murram ring round a planted centre) and the two axial beds, raised with kerbs, as in the north
  plaza (forecourt_layout.json central_round_bed, axial_bed_north, axial_bed_south).
Paving finish and planting are inference. In the finished state only, the lawn, paths, beds, shrubs, flowers and trees
that overlap the plaza are hidden or cut (cut copies keep the uncut originals for the asbuilt state, as in pass I,
blender/scene_state.py). The south-west grass loop and its road stay as they are. No people are added (K1: the crowd
density does not change in this pass).
Run from the repo root after landmarks_pass_j.py: TALANTA_SITE_BLEND=blender/out/step_FK.blend ~/.venvs/bpy/bin/python blender/context/plaza_south_k.py
"""
import json, math, os, sys
from pathlib import Path
import numpy as np
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import delaunay_2d_cdt

ROOT = Path(__file__).resolve().parents[2]
D = json.loads((ROOT / "blender/data/plaza_south_k.json").read_text())
bpy.ops.wm.open_mainfile(filepath=os.environ.get("TALANTA_SITE_BLEND", str(ROOT / "blender/out/talanta_site.blend")))
scene = bpy.context.scene
sys.path.insert(0, str(ROOT / "blender")); import scene_state as SS
report = {}
SRC = D["source"]; L = D["labels"]
CLAIM = lambda what: f"south plaza {what}: {L[what]}; source {SRC} (camera solve D02, +-{D['camera_solve']['uncertainty_m']} m)"


def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in scene.collection.children: scene.collection.children.link(c)
    for o in list(c.objects): bpy.data.objects.remove(o)
    return c


COL = coll("plaza_south_k")

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


def mat(name, hx, rough=0.85):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*srgb(hx), 1); p.inputs["Roughness"].default_value = rough; m.diffuse_color = (*srgb(hx), 1)
    return m


# the north plaza materials (forecourt.py), so the two plazas read alike
PAVE = bpy.data.materials.get("fc_paving") or mat("pk_paving", "#B9B3A5")
KERB = bpy.data.materials.get("fc_kerb") or mat("pk_kerb", "#A9A396", 0.8)
MURRAM = bpy.data.materials.get("fc_murram") or mat("pk_murram", "#8E4A30", 0.95)
PLANT = bpy.data.materials.get("fc_planting") or mat("pk_planting", "#4D653D", 0.9)


def obj(name, verts, faces, mats, claim):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.validate(); me.update()
    for m in mats: me.materials.append(m)
    o = bpy.data.objects.new(name, me); COL.objects.link(o); o["claim"] = claim; o["state_only"] = "finished"
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


def kerb(name, B, z_of, h, claim, closed=True):
    """Kerb wall along boundary points B (app x, z): from the ground to z_of(x, z) + h."""
    v, f = [], []
    for (x, z) in B: v += [(x, -z, ground(x, z) - 0.05), (x, -z, z_of(x, z) + h)]
    n = len(B)
    for i in range(n if closed else n - 1):
        j = (i + 1) % n; f.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
    return obj(name, v, f, [KERB], claim)


def area(R): return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(R, R[1:] + R[:1]))) / 2


# ---------------------------------------------------------------- outline, joined to the outer apron
OUT = [tuple(p) for p in D["outline"]]
apron = bpy.data.objects.get("ge_apron_ring")
x_from, x_to = D["north_edge_x"]
north = []
if apron:  # outer edge of the apron (vertex pairs inner, outer; site_layout_ge.py), south side, between x_from and x_to
    M = apron.matrix_world; vs = apron.data.vertices
    outer = [(M @ vs[i].co) for i in range(1, len(vs), 2)]
    north = sorted([(p.x, -p.y + 0.5) for p in outer if -p.y > 0 and x_from <= p.x <= x_to], key=lambda q: q[0])
# outline: the apron edge from west to east, then the solved east, south and west points (the three north points dropped)
PLAZA = (north + OUT[3:]) if len(north) >= 3 else OUT
# keep the south-west grass loop and its road as they are: the west edge stops at the loop road's outer east edge
# (track_sw; the solved west edge at x -64 lies about 12 m inside it, within the +-25 m of the solve)
LOOP = [bpy.data.objects.get(n) for n in D["loop_objects"]]
loop_edge = {}
for lo in [o for o in LOOP if o is not None]:
    M = lo.matrix_world
    for v in lo.data.vertices:
        w = M @ v.co; k = int((-w.y) // 2)
        loop_edge[k] = max(loop_edge.get(k, -1e9), w.x)
clipped = 0
if loop_edge:
    zs = sorted(loop_edge); edge = lambda z: np.interp(z, [2 * k + 1 for k in zs], [loop_edge[k] for k in zs], left=-1e9, right=-1e9)
    R = [tuple(p) for p in resample(PLAZA + [PLAZA[0]], 2.0)[:-1]]
    PLAZA = []
    for x, z in R:
        e = edge(z) + D["loop_gap_m"]
        if x < e: x = e; clipped += 1
        PLAZA.append((float(x), z))
report["west_edge_clipped_to_loop"] = clipped
if area(PLAZA) < 1: raise SystemExit("south plaza outline is degenerate")

# ---------------------------------------------------------------- beds (outlines in the app plan)
RB = D["round_bed"]; (bx, bz), br = RB["centre"], RB["radius_m"]
circle = lambda r_, n=48: [(bx + r_ * math.cos(t), bz + r_ * math.sin(t)) for t in np.linspace(0, 2 * math.pi, n, endpoint=False)]


def strip(line, w):
    (ax, az), (cx, cz) = line; Lx, Lz = cx - ax, cz - az; n = math.hypot(Lx, Lz); ux, uz = -Lz / n * w / 2, Lx / n * w / 2
    return [(ax + ux, az + uz), (cx + ux, cz + uz), (cx - ux, cz - uz), (ax - ux, az - uz)]


AX = {b["name"]: strip(b["line"], b["width_m"]) for b in D["axial_beds"]}
BEDS_PLAN = [circle(br)] + list(AX.values())

# ---------------------------------------------------------------- clearing (finished state only)
SKIP_COLL = {"plaza_south_k", "layout_pass_i", "layout_cars_visualization", "shell", "facade_detail", "roof_detail", "bowl_detail",
             "tiers", "plinth", "night_lights", "bowl_protos", "site_protos", "site_trees_protos", "atmosphere",
             "people_visualization", "people_figures_visualization", "people_protos", "landmarks_pass_j", "trace_sw_finished"}
KEEP = {"terrain_site", "terrain_far", "ge_apron_ring", "suburbs_buildings", "buildings", "haze_volume", "site_pad",
        "sw_lawn", "sw_loop_road", "pi_sw_grass", "track_sw", "track_sw_infield", "track_masts", "training_field_sw"}
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


CLEAR = D["clear_tree_m"]
px0, px1 = min(p[0] for p in PLAZA) - CLEAR, max(p[0] for p in PLAZA) + CLEAR
pz0, pz1 = min(p[1] for p in PLAZA) - CLEAR, max(p[1] for p in PLAZA) + CLEAR
in_plaza = lambda x, z, buf=0.0: px0 <= x <= px1 and pz0 <= z <= pz1 and near((x, z), PLAZA, buf)
is_tree = lambda o: len(o.data.polygons) == 0 or any(k in o.name for k in ("tree", "euc", "palm", "crown", "canopy", "shrub", "flower"))
for o in candidates():
    x0, x1, z0, z1 = bbox_plan(o)
    if x1 < px0 or x0 > px1 or z1 < pz0 or z0 > pz1: continue
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2; small = (x1 - x0) < 30 and (z1 - z0) < 30
    if small:  # single trees, lamps, plants
        if in_plaza(cx, cz, CLEAR if is_tree(o) else 0.0): mark_finished_hidden(o, "south plaza")
        continue
    buf = CLEAR if len(o.data.polygons) == 0 else 0.0  # scatter point clouds (trees, shrubs) get the margin
    cut_object(o, lambda x, z, b=buf: in_plaza(x, z, b), "south plaza")

# ---------------------------------------------------------------- surfaces
lift = D["lift_m"]; K = D["kerb"]
pave, B = surface("pk_south_plaza", PLAZA, PAVE, lift["paving"], CLAIM("outline") + "; finish " + L["paving_finish"], step=4.0)
# kerb on the free edge only: not along the apron join (the first len(north) points)
nfree = [p for p in B if not (north and min(math.dist(p, q) for q in north) < 2.0)]
kerb("pk_south_plaza_kerb", nfree, lambda x, z: ground(x, z) + lift["paving"], 0.0, CLAIM("kerbs"), closed=False)
for nm, R, m in [("pk_round_bed_ring", circle(br), MURRAM)] + [(f"pk_axial_bed_{k}", v, MURRAM) for k, v in AX.items()]:
    gtop = max(ground(*p) for p in resample(R + [R[0]], 2.0)) + lift["bed"]
    top, Bb = surface(nm, R, m, 0.0, CLAIM("round_bed" if "round" in nm else "axial_beds") + "; planting " + L["planting"], step=2.0, height=gtop)
    kerb(nm + "_kerb", Bb, lambda x, z, g=gtop: g, 0.01, CLAIM("kerbs"))
    if "round" in nm:  # planted centre inside the murram ring
        surface("pk_round_bed_planting", circle(br - RB["murram_ring_m"]), PLANT, 0.0, CLAIM("planting"), step=2.0, height=gtop + 0.02)
report["south_plaza"] = {"area_m2": round(area(PLAZA)), "apron_edge_points": len(north), "outline_points": len(PLAZA), "west_edge_clipped_points": clipped,
                         "round_bed_centre": [bx, bz], "round_bed_r_m": br, "axial_beds": {k: [list(map(round, p)) for p in v] for k, v in AX.items()},
                         "extent_x": [round(min(p[0] for p in PLAZA)), round(max(p[0] for p in PLAZA))],
                         "extent_z": [round(min(p[1] for p in PLAZA)), round(max(p[1] for p in PLAZA))]}
SS.set_state(scene, "finished")
report["clearing"] = {"hidden": len(cut_report["hidden"]), "hidden_names": [h[0] for h in cut_report["hidden"]][:40],
                      "cut": cut_report["cut"], "copied": cut_report["copied"]}
print("PLAZA_SOUTH_K " + json.dumps(report), flush=True)
(ROOT / "blender/out/plaza_south_k_report.json").write_text(json.dumps(report, indent=1))
bpy.ops.wm.save_mainfile()
