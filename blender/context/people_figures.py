"""Pass H (lead order 2026-10-22): people as CC0 low-poly human figures, finished state only (Visualization).

Replaces the stick figures of pass E (people_visualization: a cone and a ball each) with the ten posed figures of
Quaternius "Background Posed Humans" (CC0 1.0; blender/assets/CREDITS.md; fetch with
blender/assets/fetch_people_quaternius.sh): men and women standing, walking, hands on hips, waving, looking up.
They are instanced with geometry nodes on points scattered over the finished plaza, path and apron surfaces, denser
toward the bowl and the plaza. The crowd density and the grouping are an artistic Visualization choice, not taken from
any source (pass K, 2026-10-24). Each person gets a height, a heading, and
shirt, trouser and skin colours from seeded palettes (instancer attributes read by the figure materials).
Visualization: not a crowd count, occupancy or evacuation / safety simulation.
Run from the repo root after layout_pass_i.py (pass I; layout_final.py before it): ~/.venvs/bpy/bin/python blender/context/people_figures.py
"""
import json, math, os
from pathlib import Path
import numpy as np
import bpy

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "blender/assets/people"
VIS = "Visualization: CC0 Quaternius posed figures for the finished look; not a crowd count, occupancy or safety simulation"
bpy.ops.wm.open_mainfile(filepath=os.environ.get("TALANTA_SITE_BLEND", str(ROOT / "blender/out/talanta_site.blend")))
scene = bpy.context.scene
rng = np.random.default_rng(2213)
report = {}


def coll(name, clear=True):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in scene.collection.children: scene.collection.children.link(c)
    if clear:
        for o in list(c.objects): bpy.data.objects.remove(o)
    return c


def srgb(h):
    h = h.lstrip("#"); return tuple(((int(h[i:i + 2], 16) / 255 + 0.055) / 1.055) ** 2.4 for i in (0, 2, 4))


# ---------------------------------------------------------------- figure prototypes
FIG = [  # file, sex, weight in the crowd
    ("Male_Standing", "m", 0.16), ("Male_Walking", "m", 0.17), ("Male_Standing_Hips", "m", 0.05), ("Male_Standing_Waving", "m", 0.02),
    ("Male_LookingUp", "m", 0.04), ("Female_Standing", "f", 0.16), ("Female_Walking", "f", 0.17), ("Female_Standing_Hips", "f", 0.05),
    ("Woman_Standing_Waving", "f", 0.02), ("Female_LookingUp", "f", 0.04)]
REF_H = {}  # standing height in source units per sex, so raised arms stay above the head


def attr_mat(name, attr, fallback, rough=0.8):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    p.inputs["Roughness"].default_value = rough; m.diffuse_color = (*srgb(fallback), 1)
    if attr:
        a = nt.nodes.new("ShaderNodeAttribute"); a.attribute_type = "INSTANCER"; a.attribute_name = attr
        nt.links.new(a.outputs["Color"], p.inputs["Base Color"])
    else:
        p.inputs["Base Color"].default_value = (*srgb(fallback), 1)
    m["claim"] = VIS
    return m


MATS = {"Skin": attr_mat("hum_skin", "skin", "#5C3B2A", 0.6), "Shirt": attr_mat("hum_shirt", "shirt", "#D8D8D4"),
        "Pants": attr_mat("hum_pants", "pants", "#2B3445"), "Shoes": attr_mat("hum_shoes", None, "#1A1A1A", 0.5),
        "Hair": attr_mat("hum_hair", None, "#141110", 0.7)}
PROTO = coll("people_protos"); PROTO.hide_render = True
lc = bpy.context.view_layer.layer_collection.children.get("people_protos")
if lc: lc.hide_viewport = True
protos = []
for fname, sex, _ in FIG:
    path = ASSETS / f"{fname}.blend"
    if not path.exists(): raise SystemExit(f"missing {path}: run blender/assets/fetch_people_quaternius.sh")
    with bpy.data.libraries.load(str(path), link=False) as (src, dst): dst.meshes = list(src.meshes)
    me = dst.meshes[0]; me.name = f"person_{fname}"
    co = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    ref = {"m": "Male_Standing", "f": "Female_Standing"}[sex]
    if fname == ref or sex not in REF_H: REF_H[sex] = float(np.ptp(co[:, 2])) if fname == ref else REF_H.get(sex, float(np.ptp(co[:, 2])))
    protos.append((me, co, sex))
for me, co, sex in protos:
    s = 1.0 / REF_H[sex]  # instance scale = the person's height in metres
    c = co.copy(); c[:, 0] -= np.median(co[:, 0]); c[:, 1] -= np.median(co[:, 1]); c[:, 2] -= co[:, 2].min(); c *= s
    me.vertices.foreach_set("co", c.ravel()); me.update()
    for i, m in enumerate(me.materials):
        me.materials[i] = MATS.get(m.name.split(".")[0], MATS["Shirt"]) if m else MATS["Shirt"]
    o = bpy.data.objects.new(me.name, me); PROTO.objects.link(o)
    for p in me.polygons: p.use_smooth = False
report["protos"] = [p[0].name for p in protos]

# ---------------------------------------------------------------- points on the finished walking surfaces
import sys
sys.path.insert(0, str(ROOT / "blender")); import scene_state as SS
SS.set_state(scene, "finished")
def walk_surface(o):
    n = o.name
    if o.type != "MESH" or o.hide_render or "kerb" in n: return 0.0
    if n in ("fp_plaza", "fp_paths", "ge_apron_ring") or n.startswith(("fc_central", "fc_axial", "fc_facade_apron", "fc_plaza", "fc_path_")): return 1.0
    return 0.0
tris, wts = [], []
dg = bpy.context.evaluated_depsgraph_get()
for o in list(scene.objects):
    k = walk_surface(o)
    if not k: continue
    me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); M = o.matrix_world
    for t in me.loop_triangles:
        a, b, c = (np.array(M @ me.vertices[i].co) for i in t.vertices)
        nz = np.cross(b - a, c - a); ar = np.linalg.norm(nz) / 2
        if ar < 1e-3 or nz[2] / (2 * ar) < 0.8: continue
        cen = (a + b + c) / 3; r = math.hypot(cen[0], cen[1])
        tris.append((a, b, c)); wts.append(k * ar / (1 + (r / 160) ** 2))
    o.evaluated_get(dg).to_mesh_clear()
wts = np.array(wts); wts /= wts.sum()
N = int(os.environ.get("TALANTA_PEOPLE", "4200"))
pts = []
for i in rng.choice(len(tris), N, p=wts):
    a, b, c = tris[i]; u, v = rng.random(2)
    if u + v > 1: u, v = 1 - u, 1 - v
    pts.append(a + (b - a) * u + (c - a) * v)
P = np.array(pts)
# small groups: a third of the people stand near another person (artistic choice)
for i in rng.choice(N, N // 3, replace=False):
    j = int(rng.integers(N)); P[i, :2] = P[j, :2] + rng.normal(0, 0.9, 2)
fw = np.array([w for _, _, w in FIG]); fw /= fw.sum()
fig = rng.choice(len(FIG), N, p=fw)
male = np.array([FIG[k][1] == "m" for k in fig])
height = np.where(male, rng.normal(1.74, 0.07, N), rng.normal(1.62, 0.06, N)).clip(1.45, 1.95)
yaw = rng.uniform(0, 2 * math.pi, N)
walk = np.array(["Walking" in FIG[k][0] for k in fig])  # walkers head roughly to or from the bowl
toward = np.arctan2(-P[:, 1], -P[:, 0]) + rng.choice([0, math.pi], N) + rng.normal(0, 0.5, N)
yaw = np.where(walk, toward - math.pi / 2, yaw)
SHIRT = ["#F2F2EE", "#1C1D20", "#B8202C", "#1E6B3A", "#2A5C9A", "#E3B23C", "#7A7F86", "#6E1F2E", "#E06A2B", "#9DC3E6", "#3C2F5C"]
SW = np.array([0.18, 0.14, 0.14, 0.12, 0.1, 0.06, 0.08, 0.05, 0.04, 0.05, 0.04]); SW /= SW.sum()
PANTS = ["#23304A", "#151517", "#3C3F44", "#7D6A4F", "#E8E4DA", "#2E4A6B"]; PW = np.array([0.32, 0.28, 0.14, 0.12, 0.06, 0.08])
SKIN = ["#3B281F", "#4A3226", "#5C3B2A", "#6B4A35", "#7E5A42"]; KW = np.array([0.2, 0.28, 0.27, 0.17, 0.08])
pick = lambda pal, w: np.array([(*srgb(pal[i]), 1.0) for i in rng.choice(len(pal), N, p=w / w.sum())], np.float32)

old = bpy.data.objects.get("people_visualization")
if old: old["state_hide_render"] = True; old.hide_render = True
pc = coll("people_figures_visualization")
pm = bpy.data.meshes.new("people_figures_points"); pm.from_pydata([tuple(p) for p in P], [], [])
for name, kind, data in (("proto", "INT", fig.astype(np.int32)), ("height", "FLOAT", height.astype(np.float32)), ("yaw", "FLOAT", yaw.astype(np.float32))):
    pm.attributes.new(name, kind, "POINT").data.foreach_set("value", data)
for name, pal, w in (("shirt", SHIRT, SW), ("pants", PANTS, PW), ("skin", SKIN, KW)):
    pm.attributes.new(name, "FLOAT_COLOR", "POINT").data.foreach_set("color", pick(pal, w).ravel())
po = bpy.data.objects.new("people_figures_visualization", pm); pc.objects.link(po)
po["claim"] = VIS; po["state_only"] = "finished"
gn = bpy.data.node_groups.new("people_scatter", "GeometryNodeTree")
gn.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
gn.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
nd, lk = gn.nodes, gn.links
gi, go = nd.new("NodeGroupInput"), nd.new("NodeGroupOutput")
ci = nd.new("GeometryNodeCollectionInfo"); ci.inputs["Collection"].default_value = PROTO
ci.inputs["Separate Children"].default_value = True; ci.inputs["Reset Children"].default_value = True
iop = nd.new("GeometryNodeInstanceOnPoints"); iop.inputs["Pick Instance"].default_value = True
def named(name, dtype):
    n = nd.new("GeometryNodeInputNamedAttribute"); n.data_type = dtype; n.inputs["Name"].default_value = name; return n
pa, ha, ya = named("proto", "INT"), named("height", "FLOAT"), named("yaw", "FLOAT")
comb = nd.new("ShaderNodeCombineXYZ")
lk.new(ya.outputs["Attribute"], comb.inputs["Z"])
lk.new(gi.outputs[0], iop.inputs["Points"]); lk.new(ci.outputs[0], iop.inputs["Instance"])
lk.new(pa.outputs["Attribute"], iop.inputs["Instance Index"]); lk.new(comb.outputs[0], iop.inputs["Rotation"])
lk.new(ha.outputs["Attribute"], iop.inputs["Scale"]); lk.new(iop.outputs[0], go.inputs[0])
po.modifiers.new("people", "NODES").node_group = gn
report["people"] = N
report["by_figure"] = {FIG[k][0]: int((fig == k).sum()) for k in range(len(FIG))}
SS.set_state(scene, "finished")
print("PEOPLE_FIGURES " + json.dumps(report), flush=True)
bpy.ops.wm.save_mainfile()
