"""Pass D (replica plan 2026-10-20): context look against the drone frames and landing mockups 06/07.

Adds to blender/out/talanta_site.blend (after tree_crowns.py):
- Far land green with blue-grey hills, no beige band (L06): the Sentinel-2 dry-season tone of the far-land materials
  is turned toward green by a Colour blend (keeps the brightness structure of the imagery and its grade); the hills and
  far layers of terrain_horizon get their own copy of the material turned toward blue-grey.
- City darker and varied (L07, D02): suburb walls, OSM building facades, the background_b blocks and the horizon towers
  are darkened, with a per-building tone spread from a 60 m world noise.
- L07 (Visualization, estimated): denser mid-rise in the view of L07 (bearings -10 to 38 deg, 1.2 to 4.5 km) and a
  taller tower cluster at its right edge, toward the Kileleshwa and Lavington apartment towers (about 40 deg, 3.5 km;
  the CBD and Upper Hill lie at 75 and 85 deg, outside the L07 frame), with tree cover between. Collection
  context_l07_visualization. Heights and positions are estimated, not surveyed.
Run from the repo root: ~/.venvs/bpy/bin/python blender/context/context_fix.py
"""
import json, math, os, sys
from pathlib import Path
import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=os.environ.get("TALANTA_SITE_BLEND", str(ROOT / "blender/out/talanta_site.blend")))
scene = bpy.context.scene
rng = np.random.default_rng(2111)
report = {}


def base_link(m):
    pb = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    return pb, (pb.inputs["Base Color"].links[0].from_socket if pb and pb.inputs["Base Color"].is_linked else None)


def tint(m, colour, fac, mult=1.0, spread=0.0):
    """Base colour -> Colour blend toward colour (fac), times mult, times a 60 m world noise in 1 +- spread."""
    if m is None or not m.use_nodes or m.get("pass_d_tint"): return False
    pb, src = base_link(m)
    if pb is None: return False
    nt = m.node_tree
    if src is None:
        rgb = Vector(pb.inputs["Base Color"].default_value[:3]); lum = rgb.dot(Vector((0.2126, 0.7152, 0.0722)))
        c = Vector(colour); c = c * (lum / max(c.dot(Vector((0.2126, 0.7152, 0.0722))), 1e-4))
        new = rgb.lerp(c, fac) * mult; pb.inputs["Base Color"].default_value = (*new, 1); m["pass_d_tint"] = True; return True
    mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.blend_type = "COLOR"; mx.inputs[0].default_value = fac
    nt.links.new(src, mx.inputs[6]); mx.inputs[7].default_value = (*colour, 1)
    out = mx.outputs[2]
    if mult != 1.0 or spread:
        mu = nt.nodes.new("ShaderNodeMix"); mu.data_type = "RGBA"; mu.blend_type = "MULTIPLY"; mu.inputs[0].default_value = 1.0
        nt.links.new(out, mu.inputs[6])
        if spread:
            tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1 / 60
            nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
            mr = nt.nodes.new("ShaderNodeMapRange"); mr.inputs["To Min"].default_value = mult * (1 - spread); mr.inputs["To Max"].default_value = mult * (1 + spread)
            nt.links.new(nz.outputs["Fac"], mr.inputs["Value"]); nt.links.new(mr.outputs[0], mu.inputs[7])
        else: mu.inputs[7].default_value = (mult, mult, mult, 1)
        out = mu.outputs[2]
    nt.links.new(out, pb.inputs["Base Color"]); m["pass_d_tint"] = True
    return True


# 1. far land: green near, blue-grey hills and far layers
GREEN, BLUE_GREY = (0.10, 0.20, 0.06), (0.30, 0.36, 0.44)
fl = {}
for mn in ("far_land_band_mat", "terrain_far_mat"): fl[mn] = tint(bpy.data.materials.get(mn), GREEN, 0.95, 0.6)
th = bpy.data.materials.get("terrain_horizon_mat")
if th is not None:
    fl["terrain_horizon_mat"] = tint(th, GREEN, 0.95, 0.6)
    hills = th.copy(); hills.name = "terrain_horizon_hills_mat"; hills["pass_d_tint"] = False
    nt = hills.node_tree; pb, src = base_link(hills)
    for lk in list(pb.inputs["Base Color"].links): nt.links.remove(lk)
    # rewire the hills copy from the green blend's input (the graded imagery) to a blue-grey blend
    mx = next(n for n in nt.nodes if n.type == "MIX" and n.blend_type == "COLOR")
    nt.links.new(mx.outputs[2], pb.inputs["Base Color"]); mx.inputs[7].default_value = (*BLUE_GREY, 1); mx.inputs[0].default_value = 0.85
    for on in ("terrain_horizon_hills", "terrain_horizon_far"):
        o = bpy.data.objects.get(on)
        if o: o.data.materials[0] = hills
    fl["terrain_horizon_hills_mat"] = True
report["far_land"] = fl

# 2. city darker and varied
WARM_GREY = (0.42, 0.40, 0.37)
dk = []
for m in bpy.data.materials:
    n = m.name
    if n.startswith("suburbs_wall_") or n in ("buildings_mat",) or n.startswith("bg_wall_") or n.startswith("horizon_city_") or n.startswith("far_land_facade"):
        if tint(m, WARM_GREY, 0.25, 0.68, spread=0.22): dk.append(n)
report["city_darkened"] = dk

# 3. L07 mid-rise, tower cluster and trees (Visualization)
col = bpy.data.collections.get("context_l07_visualization") or bpy.data.collections.new("context_l07_visualization")
if col.name not in scene.collection.children: scene.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)
grounds = [o for o in (bpy.data.objects.get(n) for n in ("terrain_far", "terrain_horizon", "terrain_site")) if o]
dg = bpy.context.evaluated_depsgraph_get(); V, F = [], []
for o in grounds:
    me = o.evaluated_get(dg).to_mesh(); b = len(V)
    V += [o.matrix_world @ v.co for v in me.vertices]; F += [[b + i for i in p.vertices] for p in me.polygons]; o.evaluated_get(dg).to_mesh_clear()
bvh = BVHTree.FromPolygons(V, F)


def ground(x, y):
    hit = bvh.ray_cast(Vector((x, y, 5000.0)), Vector((0, 0, -1)))
    return hit[0].z if hit[0] is not None else 0.0


mats = [m for m in bpy.data.materials if m.name.startswith("horizon_city_")] or [bpy.data.materials.new("l07_block")]
CLAIM = "Visualization: generic mid-rise and towers placed for the L07 view; positions and heights estimated, not surveyed"


def block(name, x, y, w, d, h, rot, mat):
    g = ground(x, y); c, s = math.cos(rot), math.sin(rot)
    pts = [(-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2)]
    vs = [(x + c * a - s * b, y + s * a + c * b, g - 1.0) for a, b in pts] + [(x + c * a - s * b, y + s * a + c * b, g + h) for a, b in pts]
    fs = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    me = bpy.data.meshes.new(name); me.from_pydata(vs, [], fs); me.materials.append(mat)
    o = bpy.data.objects.new(name, me); col.objects.link(o); o["claim"] = CLAIM; o["estimated_height_m"] = round(h, 1); return o


placed = []
def free(x, y, r):
    return all(math.hypot(x - a, y - b) > r + rb for a, b, rb in placed)


nb = 0
for _ in range(4000):  # mid-rise: 6 to 14 storeys, in view, 1.2 to 4.5 km out
    if nb >= 140: break
    brg = math.radians(rng.uniform(-10, 38)); dist = 1200 + 3300 * rng.random() ** 0.8
    x, y = dist * math.sin(brg), dist * math.cos(brg); w, d = rng.uniform(16, 34), rng.uniform(14, 26)
    if not free(x, y, max(w, d) * 0.8): continue
    block(f"l07_midrise_{nb:03d}", x, y, w, d, rng.uniform(20, 45), rng.uniform(0, math.pi), mats[nb % len(mats)])
    placed.append((x, y, max(w, d) * 0.8)); nb += 1
nt_ = 0
cb, cd = math.radians(40), 3500.0; cx, cy = cd * math.sin(cb), cd * math.cos(cb)
for _ in range(2000):  # tower cluster: 60 to 140 m
    if nt_ >= 22: break
    x, y = cx + rng.normal(0, 260), cy + rng.normal(0, 200); w = rng.uniform(22, 36)
    if not free(x, y, w * 0.8): continue
    block(f"l07_tower_{nt_:02d}", x, y, w, w * rng.uniform(0.7, 1.0), rng.uniform(60, 140), rng.uniform(0, math.pi), mats[(nt_ * 3) % len(mats)])
    placed.append((x, y, w * 0.8)); nt_ += 1
tsrc = [bpy.data.objects[n] for n in ("tree_0_round", "tree_1_acacia", "tree_2_eucalyptus") if n in bpy.data.objects]
ntr = 0
for _ in range(20000):  # tree cover between the blocks
    if ntr >= 1400 or not tsrc: break
    brg = math.radians(rng.uniform(-12, 40)); dist = 700 + 3000 * rng.random() ** 0.7
    x, y = dist * math.sin(brg), dist * math.cos(brg)
    if not free(x, y, 4): continue
    s_ = tsrc[int(rng.integers(len(tsrc)))]; o = bpy.data.objects.new(f"l07_tree_{ntr:04d}", s_.data); col.objects.link(o)
    sc = rng.uniform(1.0, 1.7); o.scale = (sc, sc, sc); o.rotation_euler.z = rng.uniform(0, 6.283); o.location = (x, y, ground(x, y) - 0.3)
    o["claim"] = CLAIM; ntr += 1
report["l07"] = {"midrise": nb, "towers": nt_, "trees": ntr, "tower_cluster_bearing_deg": 40, "tower_cluster_distance_m": cd}
print("CONTEXT_FIX " + json.dumps(report), flush=True)
bpy.ops.wm.save_mainfile()
