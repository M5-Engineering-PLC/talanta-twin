"""Step L (Munene, 2026-10-19): site layout from the Google Earth screenshot (blender/data/site_layout_ge.json).

Adds to blender/out/talanta_site.blend, after build_site_detail.py:
- a paved apron ring round the bowl (the light band round the roof outline in the screenshot),
- the curved road from the north plaza round the warm-up track and down the east side, with lamp rows,
- the two long dark-roofed buildings on the east side (plain masses, no openings or signs),
- the east hardstanding as a car park: bay rows, lawn islands with trees, lamp rows.
Everything is estimated (by eye from the GE screenshot, +-10 m). W1b and OSM features are not moved. The landing
mockups set the look only. No gates, turnstiles, exits or access detail (AGENTS.md rule 8).
Run from the repo root: ~/.venvs/bpy/bin/python blender/context/site_layout_ge.py
"""
import json, math
from pathlib import Path
import numpy as np
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[2]
D = json.loads((ROOT / "blender/data/site_layout_ge.json").read_text())
RG = json.loads((ROOT / "blender/out/bowl_rings.json").read_text())
CLAIM = "estimated (by eye from the GE screenshot of 26 Dec 2025, +-10 m; step L)"
rng = np.random.default_rng(1910)

import os
bpy.ops.wm.open_mainfile(filepath=os.environ.get("TALANTA_SITE_BLEND", str(ROOT / "blender/out/talanta_site.blend")))
scene = bpy.context.scene
col = bpy.data.collections.get("site_layout_ge") or bpy.data.collections.new("site_layout_ge")
if col.name not in scene.collection.children: scene.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)

T = D["transform"]
def px2m(p): return ((p[0] - T["px0"]) / T["px_per_m"], (p[1] - T["py0"]) / T["px_per_m"])  # app x east, z south

terr = bpy.data.objects["terrain_site"]
dg = bpy.context.evaluated_depsgraph_get()
tm = terr.evaluated_get(dg).to_mesh()
bvh = BVHTree.FromPolygons([terr.matrix_world @ v.co for v in tm.vertices], [p.vertices[:] for p in tm.polygons])
terr.evaluated_get(dg).to_mesh_clear()


def ground(x, z):
    """Terrain height (Blender z) under app (x, z)."""
    hit = bvh.ray_cast(Vector((x, -z, 3000.0)), Vector((0, 0, -1)))
    return hit[0].z if hit[0] is not None else 0.0


def srgb(h):
    h = h.lstrip("#"); return tuple(((int(h[i:i + 2], 16) / 255 + 0.055) / 1.055) ** 2.4 for i in (0, 2, 4))


def mat(name, hx, rough=0.85, emit=None):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*srgb(hx), 1); p.inputs["Roughness"].default_value = rough
    m.diffuse_color = (*srgb(hx), 1); m["claim"] = CLAIM
    return m


def obj(name, verts, faces, material, extra_mats=()):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.validate(); me.update()
    me.materials.append(material)
    for em in extra_mats: me.materials.append(em)
    o = bpy.data.objects.new(name, me); col.objects.link(o); o["claim"] = CLAIM; o["sources"] = "blender/data/site_layout_ge.json"
    return o


PAVE = bpy.data.materials.get("fc_paving") or mat("ge_paving", "#C9C2B6")
ROAD = bpy.data.materials.get("roads_mat") or mat("ge_asphalt", "#3A3A3C", 0.9)
PARK = mat("ge_carpark_asphalt", "#4A4A4C", 0.9)
LINE = bpy.data.materials.get("line_paint") or mat("ge_line", "#E8E8E2", 0.6)
LAWN = bpy.data.materials.get("fc_grass") or mat("ge_lawn", "#4E7A35", 0.95)
KERB = bpy.data.materials.get("fc_kerb") or mat("ge_kerb", "#B9B4AA")
POLE = bpy.data.materials.get("pole_grey") or mat("ge_pole", "#8A8D90", 0.5)
LAMP = bpy.data.materials.get("night_lamp_warm") or mat("ge_lamp", "#FFE2B0", 0.4)
LIFT = 0.06  # surfaces sit just over the terrain


def ribbon(name, pts, width, material, lift=LIFT, step=4.0):
    """Strip of the given width along an app-frame polyline, draped on the terrain."""
    dense = []
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(1, int(math.dist(a, b) / step))
        dense += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n)]
    dense.append(pts[-1]); v, f = [], []
    for i, (x, z) in enumerate(dense):
        a, b = dense[max(i - 1, 0)], dense[min(i + 1, len(dense) - 1)]
        tx, tz = b[0] - a[0], b[1] - a[1]; L = math.hypot(tx, tz) or 1; nx, nz = -tz / L, tx / L
        for s in (-1, 1):
            px, pz = x + nx * s * width / 2, z + nz * s * width / 2; v.append((px, -pz, ground(px, pz) + lift))
    for i in range(len(dense) - 1): f.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
    return obj(name, v, f, material), dense


def lamp(name, x, z, h=9.0):
    g = ground(x, z); v, f = [], []
    for k in range(8):
        a = 2 * math.pi * k / 8; v += [(x + 0.12 * math.cos(a), -z + 0.12 * math.sin(a), g), (x + 0.08 * math.cos(a), -z + 0.08 * math.sin(a), g + h)]
    for k in range(8):
        k2 = (k + 1) % 8; f.append((2 * k, 2 * k2, 2 * k2 + 1, 2 * k + 1))
    base = len(v)
    for dx, dy in ((-0.35, -0.35), (0.35, -0.35), (0.35, 0.35), (-0.35, 0.35)): v.append((x + dx, -z + dy, g + h))
    for dx, dy in ((-0.35, -0.35), (0.35, -0.35), (0.35, 0.35), (-0.35, 0.35)): v.append((x + dx, -z + dy, g + h + 0.25))
    f += [(base, base + 1, base + 2, base + 3), (base + 4, base + 5, base + 6, base + 7)]
    for k in range(4): f.append((base + k, base + (k + 1) % 4, base + 4 + (k + 1) % 4, base + 4 + k))
    o = obj(name, v, f, POLE, (LAMP,))
    for p in o.data.polygons[8:]: p.material_index = 1   # the head carries the night lamp material
    return o


def lamps_along(prefix, dense, spacing, offset):
    acc, nxt, k = 0.0, 0.0, 0
    for a, b in zip(dense[:-1], dense[1:]):
        L = math.dist(a, b)
        while nxt <= acc + L:
            t = (nxt - acc) / L; x, z = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            nx, nz = -(b[1] - a[1]) / L, (b[0] - a[0]) / L
            for s in (-1, 1): lamp(f"{prefix}_{k:03d}", x + nx * s * offset, z + nz * s * offset); k += 1
            nxt += spacing
        acc += L
    return k


# trees: linked copies of the canopy variants (canopy.py) with a jitter in scale, turn and tint variant
TREE_SRC = [o for o in bpy.data.objects if o.name.startswith("canopy_broadleaf_") and o.name.endswith("_high")]
EUC = [o for o in bpy.data.objects if o.name.startswith("canopy_eucalyptus_") and o.name.endswith("_high")]
def tree(name, x, z, h, pool=None):
    pool = pool or TREE_SRC; src = pool[int(rng.integers(len(pool)))]; o = bpy.data.objects.new(name, src.data); col.objects.link(o)
    s = h / max(src.dimensions.z, 0.1); o.scale = (s, s, s * rng.uniform(0.9, 1.1)); o.rotation_euler.z = rng.uniform(0, 2 * math.pi)
    o.location = (x, -z, ground(x, z)); o["claim"] = CLAIM; return o


report = {}
# 1. apron ring round the bowl
rPl, dirs = RG["rPl"], RG["dirs"]; off = D["apron_ring"]["offset_m"]; v, f = [], []
for (ux, uz), r in zip(dirs, rPl):
    for rr in (r - 0.5, r + off):
        x, z = ux * rr, uz * rr; v.append((x, -z, ground(x, z) + 0.03))
N = len(dirs)
for i in range(N): j = (i + 1) % N; f.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
obj("ge_apron_ring", v, f, PAVE)  # LIFT: the forecourt and plaza surfaces from build_site_detail sit above it; report["apron_ring_m"] = off
ring_pts = [(ux * (r + off - 2), uz * (r + off - 2)) for (ux, uz), r in zip(dirs, rPl)][::4]
report["apron_lamps"] = 0
for k, (x, z) in enumerate(ring_pts): lamp(f"ge_apron_lamp_{k:03d}", x, z, 8.0); report["apron_lamps"] += 1

# 2. roads with lamp rows
for rd in D["roads"]:
    pts = [px2m(p) for p in rd["px"]]
    _, dense = ribbon(rd["name"], pts, rd["width_m"], ROAD)
    report[rd["name"]] = {"length_m": round(sum(math.dist(a, b) for a, b in zip(pts[:-1], pts[1:]))), "lamps": lamps_along(rd["name"] + "_lamp", dense, 30.0, rd["width_m"] / 2 + 1.5)}
    # eucalyptus rows on both verges (step T: roadside eucalyptus, JWNowpO44rw 000612.433), on a lawn verge strip
    nt = 0
    for side in (-1, 1):
        acc, nxt = 0.0, 7.0
        for a, b in zip(dense[:-1], dense[1:]):
            L = math.dist(a, b)
            while nxt <= acc + L:
                t = (nxt - acc) / L; x, z = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                nx, nz = -(b[1] - a[1]) / L, (b[0] - a[0]) / L; o_ = rd["width_m"] / 2 + 4.5
                tree(f"{rd['name']}_euc_{nt:03d}", x + nx * side * o_, z + nz * side * o_, rng.uniform(14, 22), EUC); nt += 1
                nxt += rng.uniform(11, 16)
            acc += L
    report[rd["name"]]["eucalyptus"] = nt

# 3. buildings: plain boxes on the terrain
for b in D["buildings"]:
    (x0, z0), (x1, z1) = map(px2m, b["px_axis"]); L = math.dist((x0, z0), (x1, z1)); ux, uz = (x1 - x0) / L, (z1 - z0) / L
    nx, nz = -uz, ux; w = b["width_m"] / 2; g = min(ground(x0, z0), ground(x1, z1)); h = b["height_m"]
    c = [(x0 + nx * w, z0 + nz * w), (x1 + nx * w, z1 + nz * w), (x1 - nx * w, z1 - nz * w), (x0 - nx * w, z0 - nz * w)]
    v = [(x, -z, g) for x, z in c] + [(x, -z, g + h) for x, z in c]
    f = [(0, 1, 2, 3)[::-1], (4, 5, 6, 7)] + [(k, (k + 1) % 4, 4 + (k + 1) % 4, 4 + k) for k in range(4)]
    o = obj(b["name"], v, f, mat("ge_wall_pale", "#D9D4C8"), (mat(b["name"] + "_roof", b["roof_hex"], 0.6),))
    o.data.polygons[1].material_index = 1
    report[b["name"]] = {"length_m": round(L), "width_m": b["width_m"]}

# 4. car park: asphalt polygon, bay rows with lawn islands and trees, lamp rows
def inside(pt, poly):
    x, z = pt; c = False
    for (x1, z1), (x2, z2) in zip(poly, poly[1:] + poly[:1]):
        if (z1 > z) != (z2 > z) and x < x1 + (z - z1) * (x2 - x1) / (z2 - z1): c = not c
    return c
for cp in D["car_parks"]:
    poly = [px2m(p) for p in cp["px"]]
    cx = sum(p[0] for p in poly) / len(poly); cz = sum(p[1] for p in poly) / len(poly)
    bm = bmesh.new(); vs = [bm.verts.new((x, -z, ground(x, z) + LIFT)) for x, z in poly]; bm.faces.new(vs)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=6, use_grid_fill=True)
    me = bpy.data.meshes.new(cp["name"]); bm.to_mesh(me); bm.free()
    for vv in me.vertices: vv.co.z = ground(vv.co.x, -vv.co.y) + LIFT
    me.materials.append(PARK); o = bpy.data.objects.new(cp["name"], me); col.objects.link(o); o["claim"] = CLAIM
    a = math.radians(cp["row_bearing_deg"]); ux, uz = math.sin(a), -math.cos(a); nx, nz = -uz, ux  # rows along the bearing
    sp = cp["row_spacing_m"]; trees = lamps = islands = 0
    for k in range(-12, 13):
        line = [(cx + nx * k * sp + ux * t, cz + nz * k * sp + uz * t) for t in np.arange(-200, 200, 4.0)]
        seg = [p for p in line if inside(p, poly)]
        if len(seg) < 4: continue
        if k % 2 == 0:   # lawn island with a tree row
            ribbon(f"{cp['name']}_island_{k:+03d}", [seg[0], seg[-1]], 2.4, LAWN, lift=LIFT + 0.12)
            for p in seg[1:-1:2]: tree(f"{cp['name']}_tree_{trees:03d}", p[0], p[1], rng.uniform(7, 10)); trees += 1
            islands += 1
        else:            # bay line: a painted stripe down the middle of the aisle row
            ribbon(f"{cp['name']}_bayline_{k:+03d}", [seg[0], seg[-1]], 0.15, LINE, lift=LIFT + 0.02)
            for p in seg[::8]: lamp(f"{cp['name']}_lamp_{lamps:03d}", p[0], p[1], 9.0); lamps += 1
    report[cp["name"]] = {"islands": islands, "trees": trees, "lamps": lamps, "area_m2": round(abs(sum(x1 * z2 - x2 * z1 for (x1, z1), (x2, z2) in zip(poly, poly[1:] + poly[:1]))) / 2)}

print("SITE_LAYOUT_GE " + json.dumps(report), flush=True)
bpy.ops.wm.save_mainfile()
