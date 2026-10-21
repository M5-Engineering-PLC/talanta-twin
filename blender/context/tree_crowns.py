"""Pass D (replica plan 2026-10-20): irregular clustered tree crowns, no lollipops.

The forest scatter prototypes (tree_protos: tree_0_round, tree_1_acacia, tree_2_eucalyptus), the site tree copies
(site_trees_protos: st_*) and the suburb trees (suburbs_proto_*: suburbs_broad, _jacaranda, _eucalyptus) carry one to
three smooth ellipsoid crowns on a trunk, which read as lollipops in D01-D03 and L06/L07. Each crown blob is replaced,
in place on the shared mesh (so every instance changes), by a cluster of 6 to 14 lumpy sub-crowns spread through the
old ellipsoid (biased up and out), each an icosphere with a low-frequency random displacement. Trunk, materials and
the overall crown size stay. The canopy.py variants (lobed crowns with leaf cards) are already irregular and kept.
Also plants clustered trees on the tree cells of the as-built trace (blender/data/asbuilt_classes.png) where the model
has no trees: the forest edges and tree groups the drone frames show (both states; collection trace_trees).
Run from the repo root: ~/.venvs/bpy/bin/python blender/context/tree_crowns.py
"""
import json, math, os
from pathlib import Path
import numpy as np
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

ROOT = Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=os.environ.get("TALANTA_SITE_BLEND", str(ROOT / "blender/out/talanta_site.blend")))
scene = bpy.context.scene
rng = np.random.default_rng(2110)
CLAIM = "estimated: crown form by eye from the drone frames (clustered, irregular); positions unchanged"


def lumpy(bm, c, r, mat, subdiv=2):
    """Icosphere at c with radii r (x, y, z) and a smooth random displacement of up to +-18 %."""
    g = bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=1.0)
    k = rng.normal(size=(3, 3)); ph = rng.uniform(0, 2 * math.pi, 3)
    for v in g["verts"]:
        d = v.co.normalized(); n = sum(math.sin(k[i] @ np.array(d) * 2.2 + ph[i]) for i in range(3)) / 3
        s = 1 + 0.18 * n
        v.co = Vector((c[0] + d.x * r[0] * s, c[1] + d.y * r[1] * s, c[2] + d.z * r[2] * s))
    for f in {f for v in g["verts"] for f in v.link_faces}: f.material_index = mat; f.smooth = True


def cluster(bm, c, r, mat):
    vol = r[0] * r[1] * r[2]; n = int(np.clip(6 + vol / 6, 6, 14))
    for _ in range(n):
        d = rng.normal(size=3); d /= np.linalg.norm(d); d[2] = abs(d[2]) * 0.8 + 0.1  # up and out
        t = rng.uniform(0.25, 0.62)
        cc = (c[0] + d[0] * r[0] * t, c[1] + d[1] * r[1] * t, c[2] + d[2] * r[2] * t - r[2] * 0.1)
        sr = np.mean(r) * rng.uniform(0.36, 0.55)
        lumpy(bm, cc, (sr * rng.uniform(0.85, 1.2), sr * rng.uniform(0.85, 1.2), sr * rng.uniform(0.7, 1.0) * max(r[2] / np.mean(r), 0.6)), mat)


def recrown(me):
    """Replace every crown component (horizontal extent over 1.2 m) of mesh me by a cluster."""
    bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
    seen, comps = set(), []
    for v in bm.verts:
        if v.index in seen: continue
        stack, comp = [v], []
        seen.add(v.index)
        while stack:
            u = stack.pop(); comp.append(u)
            for e in u.link_edges:
                w = e.other_vert(u)
                if w.index not in seen: seen.add(w.index); stack.append(w)
        comps.append(comp)
    crowns, gone = [], []
    for comp in comps:  # measure everything first, then delete, then add
        P = np.array([tuple(v.co) for v in comp]); lo, hi = P.min(0), P.max(0)
        if max(hi[0] - lo[0], hi[1] - lo[1]) < 1.2: continue  # trunk
        mats = [f.material_index for v in comp for f in v.link_faces] or [0]
        crowns.append(((lo + hi) / 2, (hi - lo) / 2, max(set(mats), key=mats.count))); gone += comp
    bmesh.ops.delete(bm, geom=gone, context="VERTS")
    for c, r, mat in crowns: cluster(bm, c, r, mat)
    n = len(crowns)
    bm.to_mesh(me); bm.free()
    return n


done = {}
for o in list(bpy.data.objects):
    nm = o.name; cols = {c.name for c in o.users_collection}
    if o.type != "MESH": continue
    if not (cols & {"tree_protos", "site_trees_protos"} or nm.startswith("suburbs_proto") or any(c.startswith("suburbs_proto_") for c in cols)): continue
    if o.data.name in done or "tank" in o.name: continue  # suburb water tanks share the suburbs_proto collections
    done[o.data.name] = recrown(o.data); o.data["claim"] = CLAIM

# --- trees on the traced tree cells where the model has none (both states)
from PIL import Image
from scipy import ndimage
LAB = np.asarray(Image.open(ROOT / "blender/data/asbuilt_classes.png")); META = json.loads((ROOT / "blender/data/asbuilt_classes.json").read_text())
EXT, CELL = META["extent_m"][1], META["cell_m"]; TREE = META["classes"].index("tree")
terr = bpy.data.objects["terrain_site"]; dg = bpy.context.evaluated_depsgraph_get(); tm = terr.evaluated_get(dg).to_mesh()
bvh = BVHTree.FromPolygons([terr.matrix_world @ v.co for v in tm.vertices], [p.vertices[:] for p in tm.polygons]); terr.evaluated_get(dg).to_mesh_clear()
TP = []  # tree positions already in the model, plan only: point clouds of the scatter objects, and placed copies
for o in scene.objects:
    if o.type != "MESH" or o.name.startswith("trace_tree") or o.data.name in done: continue
    if not ("tree" in o.name or "euc" in o.name or "canopy" in o.name or "palm" in o.name): continue
    if o.modifiers: TP += [tuple(o.matrix_world @ v.co)[:2] for v in o.data.vertices]
    else: TP.append(tuple(o.location)[:2])
existing = KDTree(len(TP) + 1)
for i, (x_, y_) in enumerate(TP): existing.insert((x_, y_, 0), i)
existing.balance(); k = len(TP)
mask = ndimage.binary_opening(LAB == TREE, iterations=2)
cells = np.argwhere(mask); rng.shuffle(cells)
col = bpy.data.collections.get("trace_trees") or bpy.data.collections.new("trace_trees")
if col.name not in scene.collection.children: scene.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)
src = [bpy.data.objects[n] for n in ("tree_0_round", "tree_2_eucalyptus", "tree_1_acacia") if n in bpy.data.objects]
placed = []
for r, c in cells:
    x, z = -EXT + (c + 0.5) * CELL, -EXT + (r + 0.5) * CELL
    if existing.find((x, -z, 0))[2] < 6.0: continue
    if placed and min(np.hypot(px - x, pz - z) for px, pz in placed[-200:]) < 6.0: continue
    hit = bvh.ray_cast(Vector((x, -z, 3000.0)), Vector((0, 0, -1)))
    if hit[0] is None: continue
    w_ = np.array([0.45, 0.4, 0.15])[:len(src)]; s_ = src[int(rng.choice(len(src), p=w_ / w_.sum()))]
    o = bpy.data.objects.new(f"trace_tree_{len(placed):04d}", s_.data); col.objects.link(o)
    sc = rng.uniform(1.5, 2.2)  # the frames show large mature canopies; o.scale = (sc, sc, sc * rng.uniform(0.9, 1.2)); o.rotation_euler.z = rng.uniform(0, 2 * math.pi)
    o.location = (x, -z, hit[0].z - 0.3); o["claim"] = "derived (tree cells of the as-built trace); species and size estimated"
    placed.append((x, z))
    if len(placed) >= 1500: break
print("TREE_CROWNS " + json.dumps({"recrowned": done, "existing_trees": k, "trace_trees": len(placed)}), flush=True)
bpy.ops.wm.save_mainfile()
