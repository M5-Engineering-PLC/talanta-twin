"""WITHDRAWN 2026-10-23 (engineering/layout_audit_01/LEAD_REVIEW.md, revision 2): the dusk image is AI-generated, so this
layout has no evidence. Pass I (blender/context/layout_pass_i.py) replaces this script in the chain. Kept for the record.

Pass F (lead order 2026-10-22): the final layout, finished state, from the dusk aerial photo and the GE trace.

Adds to the scene (default blender/out/talanta_site.blend, or TALANTA_SITE_BLEND), all from blender/data/layout_final.json:
- the west dual carriageway from Ngong Road south past the bowl, with a median, verge and lamp rows;
- the railway beside it (two tracks on ballast, plain rails and sleepers), the station platform with two plain
  canopies, and the footbridge over the road and tracks with three stair towers (plain masses, no signs);
- the north-west car park between the plaza and the west road, and the far west lot inside the loop road (it replaces
  the lawn pitch), both asphalt with marked bay rows, lamp rows and parked cars (Visualization);
- murram planting beds with planted wedges in the spine between the plaza and the car park;
- the road between the training pitches, from the north-east road to the bowl apron;
- the forecourt footpaths and beds in murram (red laterite) with planted wedges, not pale paving; the NE track ring in
  dark asphalt grey as in the photo; the old OSM footways inside the W1b site boundary are dropped (the photo shows the
  murram paths and the modelled roads only);
- the white-box cars of the east hardstanding (pass E) and of the Ngong Road traffic (pass D) become the same low-poly
  car figures (Visualization), long vehicles plain buses.
What the new layout covers is cleared in the finished state only: finished-only objects are cut or hidden in place;
shared objects get a cut copy (state_only "finished") and keep the uncut original for the asbuilt state
(blender/scene_state.py). Everything is estimated (+-15 m near the photo camera, +-30 m far). Visualization: the cars
are generic figures, not real occupancy. No gate, turnstile, exit or access detail; no signs (AGENTS.md rule 8).
Run from the repo root: ~/.venvs/bpy/bin/python blender/context/layout_final.py
"""
import json, math, os
from pathlib import Path
import numpy as np
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import delaunay_2d_cdt

ROOT = Path(__file__).resolve().parents[2]
D = json.loads((ROOT / "blender/data/layout_final.json").read_text())
CLAIM = "estimated (pass F: dusk photo 2026-10-17 back-projected through camera P01, +-15 m near, +-30 m far)"
VIS = "Visualization: generic parked and moving cars for the final layout; not a count, occupancy or traffic study"
rng = np.random.default_rng(2210)
bpy.ops.wm.open_mainfile(filepath=os.environ.get("TALANTA_SITE_BLEND", str(ROOT / "blender/out/talanta_site.blend")))
scene = bpy.context.scene
report = {}


def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in scene.collection.children: scene.collection.children.link(c)
    for o in list(c.objects): bpy.data.objects.remove(o)
    return c


COL = coll("layout_final")
CARS = coll("layout_final_cars_visualization")

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
    p.inputs["Metallic"].default_value = metal; m.diffuse_color = (*srgb(hx), 1); m["claim"] = CLAIM
    return m


ASPH = bpy.data.materials.get("ngong_asphalt") or mat("lf_asphalt", "#2E3033", 0.8)
CP_ASPH = bpy.data.materials.get("ge_carpark_asphalt") or mat("lf_cp_asphalt", "#2B2C2F", 0.85)
PAINT = bpy.data.materials.get("road_paint") or mat("lf_paint", "#E4E2D8", 0.6)
KERB = bpy.data.materials.get("fc_kerb") or mat("lf_kerb", "#AAA48F", 0.8)
GRASS = bpy.data.materials.get("fc_grass") or mat("lf_grass", "#4F6E3B", 0.9)
PAVE = bpy.data.materials.get("fc_paving") or mat("lf_paving", "#B8B09C", 0.8)
MURRAM = bpy.data.materials.get("fc_murram") or mat("lf_murram", "#8E4A30", 0.95)
POLE = bpy.data.materials.get("pole_grey") or mat("lf_pole", "#5F6866", 0.5, 0.6)
LAMP = bpy.data.materials.get("night_lamp_warm") or mat("lf_lamp", "#FFE2B0", 0.4)
STEEL = bpy.data.materials.get("rail_steel") or mat("lf_rail_steel", "#C4C6C8", 0.35, 0.9)
BALLAST = mat("lf_ballast", "#6E665C", 0.95)
SLEEPER = mat("lf_sleeper", "#8B8579", 0.9)
CONC = mat("lf_platform_concrete", "#B9B4A8", 0.85)
ROOFG = mat("lf_canopy_roof", "#C9CCCF", 0.45, 0.3)
STRUCT = mat("lf_structure_white", "#E2E2DC", 0.5)
SCREEN = mat("lf_bridge_screen", "#9FA8AD", 0.3, 0.2)
GLASS = bpy.data.materials.get("parked_glass") or mat("parked_glass", "#1D262C", 0.15)
TRACKG = mat("lf_track_asphalt", "#3B3D40", 0.85)


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
    p.inputs["Roughness"].default_value = 0.95; m.diffuse_color = (*srgb("#7A4A30"), 1); m["claim"] = CLAIM
    return m


BEDS = bed_material()


def obj(name, verts, faces, mats, collection=None, claim=CLAIM, mat_idx=None, smooth=False):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.validate(); me.update()
    for m in mats: me.materials.append(m)
    if mat_idx is not None:
        for p, i in zip(me.polygons, mat_idx): p.material_index = i
    if smooth:
        for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); (collection or COL).objects.link(o)
    o["claim"] = claim; o["state_only"] = "finished"
    return o


def resample(pts, step):
    P = np.array(pts, float); d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    s = np.linspace(0, d[-1], max(2, int(d[-1] / step) + 1))
    return np.c_[np.interp(s, d, P[:, 0]), np.interp(s, d, P[:, 1])], s


def frames(pts, step=3.0):
    """Resampled centre line with unit tangents and left normals (plan x, z)."""
    P, s = resample(pts, step); T = np.gradient(P, axis=0); T /= np.linalg.norm(T, axis=1)[:, None]
    N = np.c_[-T[:, 1], T[:, 0]]
    return P, T, N, s


def ribbon(name, pts, a, b, material, lift=0.12, step=3.0, collection=None, height=None):
    """Strip between offsets a and b (m, along the left normal) of the centre line, draped on the ground."""
    P, T, N, _ = frames(pts, step); v, f = [], []
    for p, n in zip(P, N):
        for off in (a, b):
            x, z = p + n * off; v.append((x, -z, (ground(x, z) if height is None else height) + lift))
    for i in range(len(P) - 1): f.append((2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1))
    return obj(name, v, f, [material], collection)


def inside(p, ring):
    x, y = p; yes = False
    for (ax, ay), (bx, by) in zip(ring, ring[1:] + ring[:1]):
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax: yes = not yes
    return yes


def surface(name, ring, material, lift=0.12, step=4.0, collection=None):
    """Polygon draped on the ground: boundary plus an interior grid, constrained Delaunay, outside triangles dropped."""
    R = [tuple(map(float, p)) for p in ring]
    B, _ = resample(R + [R[0]], step); B = [tuple(p) for p in B[:-1]]
    xs, zs = [p[0] for p in R], [p[1] for p in R]
    pts = list(B)
    for x in np.arange(min(xs) + step / 2, max(xs), step):
        for z in np.arange(min(zs) + step / 2, max(zs), step):
            if inside((x, z), R) and min(math.dist((x, z), q) for q in B) > step * 0.4: pts.append((x, z))
    edges = [(i, (i + 1) % len(B)) for i in range(len(B))]
    out = delaunay_2d_cdt([Vector(p) for p in pts], edges, [], 0, 1e-4)
    V2, F2 = out[0], out[2]
    keep = [f for f in F2 if inside(tuple(sum((V2[i] for i in f), Vector((0, 0))) / 3), R)]
    v = [(p.x, -p.y, ground(p.x, p.y) + lift) for p in V2]
    return obj(name, v, [tuple(f) for f in keep], [material], collection)


def box_faces(b):
    return [(b, b + 1, b + 2, b + 3), (b + 4, b + 7, b + 6, b + 5), (b, b + 4, b + 5, b + 1), (b + 1, b + 5, b + 6, b + 2),
            (b + 2, b + 6, b + 7, b + 3), (b + 3, b + 7, b + 4, b)]


def oriented_box(v, f, c, u, w, L, W, z0, z1):
    """Box centred on plan point c (x, z), long axis u, short axis w (unit plan vectors), from height z0 to z1."""
    b = len(v)
    for zz in (z0, z1):
        for su, sw in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            x, z = c + u * su * L / 2 + w * sw * W / 2; v.append((x, -z, zz))
    f += box_faces(b)


def lamp(v, f, mi, x, z, h=10.0, arm=None):
    g = ground(x, z); b = len(v)
    for k in range(6):
        a = 2 * math.pi * k / 6; v += [(x + 0.13 * math.cos(a), -z + 0.13 * math.sin(a), g), (x + 0.08 * math.cos(a), -z + 0.08 * math.sin(a), g + h)]
    for k in range(6):
        k2 = (k + 1) % 6; f.append((b + 2 * k, b + 2 * k2, b + 2 * k2 + 1, b + 2 * k + 1)); mi.append(0)
    oriented_box(v, f, np.array([x, z]), np.array([1.0, 0]), np.array([0, 1.0]), 0.8, 0.4, g + h, g + h + 0.22); mi += [1] * 6


# ---------------------------------------------------------------- clearing
def zone_strip(pts, half, step=3.0):
    P, T, N, _ = frames(pts, step)
    return [tuple(p + n * half) for p, n in zip(P, N)] + [tuple(p - n * half) for p, n in zip(P[::-1], N[::-1])]


WR, RL, ST = D["west_road"], D["railway"], D["station"]
ZONES = [zone_strip(WR["centre"], WR["width_m"] / 2 + WR["verge_east_m"] + 1.0),
         zone_strip(RL["centre"], RL["ballast_width_m"] / 2 + 1.0),
         [(ST["forecourt"]["x"][1], ST["forecourt"]["z"][0]), (ST["platform"]["x"][0] - 1, ST["forecourt"]["z"][0]),
          (ST["platform"]["x"][0] - 1, ST["platform"]["z"][1] + 2), (ST["forecourt"]["x"][1], ST["platform"]["z"][1] + 2)],
         D["carpark_north_west"]["ring"], D["spine_beds"]["ring"], D["carpark_south_west"]["ring"],
         zone_strip(D["road_between_pitches"]["centre"], D["road_between_pitches"]["width_m"] / 2 + 1.0)]
FB = D["footbridge"]
for t in FB["towers"]: ZONES.append([(t[0] - 5, t[1] - 6), (t[0] + 5, t[1] - 6), (t[0] + 5, t[1] + 6), (t[0] - 5, t[1] + 6)])
ZB = [(min(p[0] for p in r), max(p[0] for p in r), min(p[1] for p in r), max(p[1] for p in r)) for r in ZONES]


import csv as _csv
SITE = [(float(r["x_east"]), float(r["z_south"])) for r in _csv.DictReader(open(ROOT / "gis/measurements/normalized/site_boundary_w1b_2026-10-16.csv"))]


def in_zones(x, z):
    for (x0, x1, z0, z1), r in zip(ZB, ZONES):
        if x0 <= x <= x1 and z0 <= z <= z1 and inside((x, z), r): return True
    return False


KEEP = {"terrain_site", "terrain_far", "ngong_road", "ngong_markings", "suburbs_buildings", "buildings",
        "sw_loop_road", "ge_apron_ring", "training_pitch_se_turf", "warmup_track_ne", "warmup_track_ne_infield", "ge_road_north_east"}
SKIP_COLL = {"layout_final", "layout_final_cars_visualization", "shell", "facade_detail", "roof_detail", "bowl_detail", "tiers",
             "plinth", "night_lights", "bowl_protos", "site_protos", "site_trees_protos"}
# Finished-only collections and prefixes (blender/scene_state.py): those objects are cut in place
import sys
sys.path.insert(0, str(ROOT / "blender")); import scene_state as SS


def finished_only(o): return SS._finished_only(o)


cut_report = {"hidden": [], "cut": [], "copied": []}


def cut_mesh(o, name=None):
    """Delete faces (or loose vertices) whose centre lies in a zone; returns the count removed."""
    bm = bmesh.new(); bm.from_mesh(o.data); M = o.matrix_world
    if len(bm.faces):
        if o.name.startswith(("roads", "road_markings")):  # long road quads: drop a face when any corner is in a zone
            # and the old OSM footways inside the W1b site, which the photo does not show (the site roads are modelled)
            dead = [fc for fc in bm.faces if any(in_zones((M @ vv.co).x, -(M @ vv.co).y) or inside(((M @ vv.co).x, -(M @ vv.co).y), SITE) for vv in fc.verts)]
        else:
            dead = [fc for fc in bm.faces if in_zones(*(lambda c: (c.x, -c.y))(M @ fc.calc_center_median()))]
        bmesh.ops.delete(bm, geom=dead, context="FACES"); n = len(dead)
    else:
        dead = [vv for vv in bm.verts if in_zones((M @ vv.co).x, -(M @ vv.co).y)]
        bmesh.ops.delete(bm, geom=dead, context="VERTS"); n = len(dead)
    bm.to_mesh(o.data); bm.free(); o.data.update()
    return n


def bbox_plan(o):
    if o.name.startswith(("roads", "road_markings")): return -1e4, 1e4, -1e4, 1e4  # always considered (site footways)
    bb = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return min(v.x for v in bb), max(v.x for v in bb), min(-v.y for v in bb), max(-v.y for v in bb)


def hide_finished(o):
    if finished_only(o): o["state_hide_render"] = True; o.hide_render = True
    else: o["state_only"] = "asbuilt"
    cut_report["hidden"].append(o.name)


for o in list(scene.objects):
    if o.type != "MESH" or o.name in KEEP or o.get("state_only"): continue
    if any(c.name in SKIP_COLL or c.name in SS.ONLY_ASBUILT for c in o.users_collection): continue
    if o.get("state_hide_render", o.hide_render): continue  # hidden in both states already
    x0, x1, z0, z1 = bbox_plan(o)
    if not any(x1 >= a and x0 <= b and z1 >= c and z0 <= d for a, b, c, d in ZB): continue
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    small = (x1 - x0) < 30 and (z1 - z0) < 30
    if o.name in ("sw_lawn",) or o.name.startswith(("sw_pitch_lines", "sw_stand", "fc_west_lawn", "fc_edge_bed_west", "fc_path_west")):
        hide_finished(o); continue
    if small:
        if in_zones(cx, cz): hide_finished(o)
        continue
    # large merged meshes: cut in place if finished-only, else cut a copy for the finished state
    if finished_only(o):
        n = cut_mesh(o)
        if n: cut_report["cut"].append([o.name, n])
    else:
        c = o.copy(); c.data = o.data.copy(); c.name = o.name + "_final"
        for cl in o.users_collection: cl.objects.link(c)
        n = cut_mesh(c)
        if n:
            c["state_only"] = "finished"; o["state_only"] = "asbuilt"; cut_report["copied"].append([o.name, n])
        else: bpy.data.objects.remove(c)
report["clearing"] = {"hidden": len(cut_report["hidden"]), "cut": cut_report["cut"], "copied": cut_report["copied"]}

# ---------------------------------------------------------------- west road
W2 = WR["width_m"] / 2; MED = WR["median_m"] / 2
ribbon("lf_west_road", WR["centre"], -W2, W2, ASPH, 0.14)
ribbon("lf_west_road_median", WR["centre"], -MED, MED, KERB, 0.32)
ribbon("lf_west_road_verge_east", WR["centre"], W2 + 0.3, W2 + WR["verge_east_m"], GRASS, 0.18)
ribbon("lf_west_road_kerb_east", WR["centre"], W2, W2 + 0.3, KERB, 0.26)
ribbon("lf_west_road_kerb_west", WR["centre"], -W2 - 0.3, -W2, KERB, 0.26)
v, f = [], []
P, T, N, s = frames(WR["centre"], 1.0)
lane = (W2 - MED) / 2
for side in (-1, 1):
    for off in (MED + lane,):  # lane divider, dashed 3 m on 6 m
        for i in range(len(P) - 3):
            if int(s[i]) % 9 >= 3: continue
            b = len(v)
            for k in (i, i + 3):
                for d_ in (-0.08, 0.08):
                    x, z = P[k] + N[k] * side * (off + d_); v.append((x, -z, ground(x, z) + 0.17))
            f.append((b, b + 2, b + 3, b + 1))
    for off in (W2 - 0.5, MED + 0.4):  # edge lines
        for i in range(0, len(P) - 3, 3):
            b = len(v)
            for k in (i, i + 3):
                for d_ in (-0.08, 0.08):
                    x, z = P[k] + N[k] * side * (off + d_); v.append((x, -z, ground(x, z) + 0.17))
            f.append((b, b + 2, b + 3, b + 1))
obj("lf_west_road_markings", v, f, [PAINT])
v, f, mi = [], [], []
P, T, N, s = frames(WR["centre"], WR["lamp_spacing_m"])
for p, n in zip(P, N):
    lamp(v, f, mi, *(p + n * (W2 + 2.0)), 11.0); lamp(v, f, mi, *(p), 11.0)
obj("lf_west_road_lamps", v, f, [POLE, LAMP], mat_idx=mi)

# ---------------------------------------------------------------- railway and station
half_b = RL["ballast_width_m"] / 2
ribbon("lf_rail_ballast", RL["centre"], -half_b, half_b, BALLAST, 0.25)
v, f, vs, fs = [], [], [], []
P, T, N, s = frames(RL["centre"], 0.65)
for tr in (-RL["track_spacing_m"] / 2, RL["track_spacing_m"] / 2):
    for g_ in (-RL["gauge_m"] / 2, RL["gauge_m"] / 2):  # rails: thin raised strips
        b0 = len(v)
        for p, n in zip(P[::4], N[::4]):
            for d_ in (-0.04, 0.04):
                x, z = p + n * (tr + g_ + d_); h = ground(*(p + n * tr)) + 0.25 + 0.36; v.append((x, -z, h))
        for i in range((len(v) - b0) // 2 - 1): f.append((b0 + 2 * i, b0 + 2 * i + 2, b0 + 2 * i + 3, b0 + 2 * i + 1))
    for p, n, t in zip(P, N, T):  # sleepers every 0.65 m
        c = p + n * tr; g = ground(*c) + 0.25
        oriented_box(vs, fs, c, n, t, 2.2, 0.25, g + 0.12, g + 0.24)
obj("lf_rail_rails", v, f, [STEEL])
obj("lf_rail_sleepers", vs, fs, [SLEEPER])
pf = ST["platform"]; (px0, px1), (pz0, pz1) = pf["x"], pf["z"]
gpl = max(ground((px0 + px1) / 2, z) for z in np.linspace(pz0, pz1, 9))
v, f = [], []; oriented_box(v, f, np.array([(px0 + px1) / 2, (pz0 + pz1) / 2]), np.array([0, 1.0]), np.array([1.0, 0]), pz1 - pz0, px1 - px0, gpl - 1.5, gpl + pf["height_m"])
obj("lf_station_platform", v, f, [CONC])
fc_ = ST["forecourt"]
surface("lf_station_forecourt", [(fc_["x"][0], fc_["z"][0]), (fc_["x"][1], fc_["z"][0]), (fc_["x"][1], fc_["z"][1]), (fc_["x"][0], fc_["z"][1])], PAVE, 0.16)
v, f, mi = [], [], []
cw, chh = ST["canopy_width_m"], ST["canopy_height_m"]; cx = (px0 + px1) / 2
for cn in ST["canopies"]:
    z0, z1 = cn["z"]
    oriented_box(v, f, np.array([cx, (z0 + z1) / 2]), np.array([0, 1.0]), np.array([1.0, 0]), z1 - z0, cw, gpl + pf["height_m"] + chh, gpl + pf["height_m"] + chh + 0.45); mi += [0] * 6
    for zz in np.arange(z0 + 3, z1 - 2, 9.0):
        oriented_box(v, f, np.array([cx, zz]), np.array([1.0, 0]), np.array([0, 1.0]), 0.35, 0.35, gpl + pf["height_m"], gpl + pf["height_m"] + chh); mi += [1] * 6
obj("lf_station_canopies", v, f, [ROOFG, STRUCT], mat_idx=mi)
# footbridge: deck, side screens and roof from the east tower to the west tower; stair towers
E, Wt = np.array(FB["east"], float), np.array(FB["west"], float)
u = (Wt - E) / np.linalg.norm(Wt - E); w = np.array([-u[1], u[0]]); Lb = float(np.linalg.norm(Wt - E))
groad = max(ground(*p) for p in np.linspace(E, Wt, 12)) + 0.15
dk = groad + FB["deck_clearance_m"]; bw = FB["width_m"]; mid = (E + Wt) / 2
v, f, mi = [], [], []
oriented_box(v, f, mid, u, w, Lb, bw, dk, dk + 0.6); mi += [0] * 6
for sd in (-1, 1):
    oriented_box(v, f, mid + w * sd * (bw / 2 - 0.1), u, w, Lb, 0.12, dk + 0.6, dk + 3.0); mi += [1] * 6
oriented_box(v, f, mid, u, w, Lb + 0.6, bw + 0.6, dk + 3.0, dk + 3.3); mi += [0] * 6
for t in FB["towers"]:
    c = np.array(t, float); g = ground(*c)
    oriented_box(v, f, c, u, w, 6.0, 9.0, g, dk + 3.3); mi += [0] * 6
for k in np.linspace(0.12, 0.88, 6):  # piers
    c = E + (Wt - E) * k; g = ground(*c)
    oriented_box(v, f, c, u, w, 0.6, 0.6, g, dk); mi += [0] * 6
obj("lf_footbridge", v, f, [STRUCT, SCREEN], mat_idx=mi)
report["footbridge"] = {"length_m": round(Lb, 1), "deck_m_above_road": FB["deck_clearance_m"]}


# ---------------------------------------------------------------- car parks
PAINTS = [("#E9E9E6", 0.33), ("#B9BCBF", 0.2), ("#6A6E72", 0.12), ("#141518", 0.15), ("#1F2F4F", 0.06), ("#8C1C1C", 0.05),
          ("#C8B897", 0.05), ("#2F4A36", 0.04)]
CPM = [mat(f"lf_car_paint_{i}", h, 0.3, 0.5) for i, (h, _) in enumerate(PAINTS)]
CPW = np.array([w_ for _, w_ in PAINTS]); CPW /= CPW.sum()
car_bm = {"v": [], "f": [], "mi": []}


def car(x, z, ang, ci=None):
    """Low-poly car (body, glass cabin, painted roof), front along ang (radians, plan), sitting on the ground."""
    if ci is None: ci = int(rng.choice(len(CPM), p=CPW))
    u = np.array([math.cos(ang), math.sin(ang)]); w = np.array([-u[1], u[0]]); g = ground(x, z) + 0.14
    L_, W_ = rng.uniform(4.2, 4.9), rng.uniform(1.75, 1.9); c = np.array([x, z])
    v, f, mi = car_bm["v"], car_bm["f"], car_bm["mi"]
    oriented_box(v, f, c, u, w, L_, W_, g + 0.25, g + 0.95); mi += [ci] * 6
    oriented_box(v, f, c - u * 0.25, u, w, L_ * 0.55, W_ * 0.9, g + 0.95, g + 1.38); mi += [len(CPM)] * 6
    oriented_box(v, f, c - u * 0.25, u, w, L_ * 0.5, W_ * 0.86, g + 1.38, g + 1.45); mi += [ci] * 6
    oriented_box(v, f, c, u, w, L_ * 0.82, W_ * 0.96, g, g + 0.3); mi += [len(CPM) + 1] * 6


TYRE = mat("lf_tyre", "#111111", 0.8)


def car_park(name, ring, fill, axis_deg=0.0, module=16.5):
    surface(name, ring, CP_ASPH, 0.15)
    v, f = [], []; xs = [p[0] for p in ring]; zs = [p[1] for p in ring]
    a = math.radians(axis_deg); u = np.array([math.sin(a), math.cos(a)]); w = np.array([u[1], -u[0]])  # rows along u
    cen = np.array([np.mean(xs), np.mean(zs)]); ext = max(max(xs) - min(xs), max(zs) - min(zs))
    ncar = 0; lam = []
    for k in np.arange(-ext, ext, module):  # module: bay 5 m | aisle 6.5 m | bay 5 m
        for side, off in ((-1, k + 2.5), (1, k + module - 2.5)):
            for t in np.arange(-ext, ext, 2.6):
                c = cen + w * off + u * t
                ends = [c + w * 2.5 * sg + u * dt for sg in (-1, 1) for dt in (-1.3, 1.3)]
                if not all(inside(tuple(e), ring) for e in ends): continue
                # stall line on the stall's start edge, from the row's back line to the aisle
                for e0, e1 in ((c - u * 1.3 - w * 2.5, c - u * 1.3 + w * 2.5),):
                    b = len(v); g = ground(*c) + 0.19
                    for e in (e0, e1):
                        for d_ in (-0.06, 0.06):
                            q = e + u * d_; v.append((q[0], -q[1], g))
                    f.append((b, b + 1, b + 3, b + 2))
                if rng.random() < fill:
                    car(*(c + w * rng.uniform(-0.15, 0.15)), math.atan2(w[1], w[0]) * (1 if side > 0 else 1) + (0 if side > 0 else math.pi) + rng.normal(0, 0.03)); ncar += 1
        lam.append(cen + w * (k + module / 2))
    obj(name + "_bays", v, f, [PAINT])
    v, f, mi = [], [], []
    for l0 in lam:  # lamp row down each aisle every 30 m
        for t in np.arange(-ext, ext, 30.0):
            q = l0 + u * t
            if inside(tuple(q), ring) and all(inside(tuple(q + d_), ring) for d_ in (u * 4, -u * 4)): lamp(v, f, mi, *q, 10.0)
    if v: obj(name + "_lamps", v, f, [POLE, LAMP], mat_idx=mi)
    return ncar


cpn = D["carpark_north_west"]; cps = D["carpark_south_west"]
report["cars_north_west"] = car_park("lf_carpark_north_west", cpn["ring"], cpn["fill"], cpn["aisle_axis_deg"], cpn["module_m"])
report["cars_south_west"] = car_park("lf_carpark_south_west", cps["ring"], cps["fill"], cps["aisle_axis_deg"], cps["module_m"])
ribbon("lf_carpark_south_west_planted_strip", cps["planted_strip"], -2.5, 2.5, BEDS, 0.24)
surface("lf_spine_beds", D["spine_beds"]["ring"], BEDS, 0.2)

# a few moving cars on the west road (Visualization), two lanes each way
P, T, N, s = frames(WR["centre"], 1.0)
for i in rng.choice(len(P), 26, replace=False):
    side = rng.choice([-1, 1]); lane_off = MED + lane * (0.5 + rng.integers(2))
    x, z = P[i] + N[i] * side * lane_off; ang = math.atan2(T[i][1], T[i][0]) + (0 if side < 0 else math.pi)
    car(x, z, ang)
report["cars_moving"] = 26

# replace the white-box cars of the east hardstanding (pass E) with the same car figures, same places
old = bpy.data.objects.get("parked_cars_visualization")
if old:
    n_old = 0
    # pass E wrote two boxes per car (body, cabin) in order: read the body boxes (every 16 vertices)
    co = np.array([tuple(old.matrix_world @ vv.co) for vv in old.data.vertices])
    for k in range(0, len(co) - 15, 16):
        body = co[k:k + 8, :2]; cxy = body.mean(0)
        _, _, Vt = np.linalg.svd(body - cxy); ax_ = Vt[0]  # long axis of the body box (Blender x, y)
        car(cxy[0], -cxy[1], math.atan2(-ax_[1], ax_[0])); n_old += 1
    old["state_hide_render"] = True; old.hide_render = True
    report["cars_east_replaced"] = n_old
# Ngong Road traffic (pass D boxes, two per car) -> the same car figures, and plain buses for the long boxes
tr = bpy.data.objects.get("traffic_Visualization")  # the uncut original: eight vertices per box, in order
if tr:
    co = np.array([tuple(tr.matrix_world @ vv.co) for vv in tr.data.vertices]); n_tr = n_bus = 0
    boxes = co[: len(co) // 8 * 8].reshape(-1, 8, 3)
    # traffic.py writes each vehicle as body, cabin, (bus skirt), four wheels: a body is a large box after a small one
    big = [float(np.ptp(bx[:, 0])) ** 2 + float(np.ptp(bx[:, 1])) ** 2 > 9.0 for bx in boxes]
    for k, b in enumerate(boxes):
        if not big[k] or (k > 0 and big[k - 1]): continue
        xy = b[:, :2]; c = xy.mean(0)
        if in_zones(c[0], -c[1]): continue
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
    trf = bpy.data.objects.get("traffic_Visualization_final")
    if trf: trf["state_hide_render"] = True; trf.hide_render = True
    report["traffic_figures"] = {"cars": n_tr, "buses": n_bus}
me = bpy.data.meshes.new("layout_final_cars_visualization"); me.from_pydata(car_bm["v"], [], car_bm["f"]); me.update()
for m in CPM + [GLASS, TYRE]: me.materials.append(m)
for p, i in zip(me.polygons, car_bm["mi"]): p.material_index = i
o = bpy.data.objects.new("layout_final_cars_visualization", me); CARS.objects.link(o); o["claim"] = VIS; o["state_only"] = "finished"
report["boxes_total"] = len(car_bm["mi"]) // 6

# ---------------------------------------------------------------- east: road between the training pitches
rb = D["road_between_pitches"]
ribbon("lf_road_between_pitches", rb["centre"], -rb["width_m"] / 2, rb["width_m"] / 2, ASPH, 0.16)
ribbon("lf_road_between_pitches_kerb_n", rb["centre"], rb["width_m"] / 2, rb["width_m"] / 2 + 0.3, KERB, 0.24)
ribbon("lf_road_between_pitches_kerb_s", rb["centre"], -rb["width_m"] / 2 - 0.3, -rb["width_m"] / 2, KERB, 0.24)

# ---------------------------------------------------------------- surfaces: murram paths and beds, NE track ring
recol = []
for name, m in (("fp_paths", MURRAM), ("fp_beds", BEDS)):
    o = bpy.data.objects.get(name)
    if o:
        o.data.materials.clear(); o.data.materials.append(m); recol.append(name)
# fc_murram (forecourt paths, step L) rendered pale beige through its legacy mix; the photo's paths are red laterite
fm = bpy.data.materials.get("fc_murram")
if fm and not fm.get("lf_red"):
    nt = fm.node_tree; p = nt.nodes["Principled BSDF"]
    for l in list(p.inputs["Base Color"].links): nt.links.remove(l)
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.6
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].color = (*srgb("#7C412D"), 1); ramp.color_ramp.elements[1].color = (*srgb("#A0593C"), 1)
    ramp.color_ramp.elements[0].position = 0.3; ramp.color_ramp.elements[1].position = 0.7
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"]); nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"])
    fm["lf_red"] = "pass F: red laterite as in the dusk photo"; recol.append("fc_murram")
t = bpy.data.objects.get("warmup_track_ne")
if t:
    for i, m in enumerate(t.data.materials):
        if m and m.name == "track_surface": t.data.materials[i] = TRACKG; recol.append("warmup_track_ne")
report["recoloured"] = sorted(set(recol))
for o in COL.objects: o["claim"] = o.get("claim", CLAIM)
print("LAYOUT_FINAL " + json.dumps(report), flush=True)
(ROOT / "blender/out/layout_final_report.json").write_text(json.dumps({"report": report, "hidden": cut_report["hidden"]}, indent=1))
bpy.ops.wm.save_mainfile()
