"""Step R (Munene, 2026-10-20): the Rubis petrol station on Ngong Road at Dagoretti Corner (blender/data/rubis_station.json).

Position from OpenStreetMap (node 30092080, forecourt loop way 654718658, shop way 1242664906); sizes estimated.
Builds collection rubis_station: forecourt slab inside the OSM loop, canopy (columns, roof, fascia), three pump islands
with dispensers, and a pylon sign. The shop (OSM way 1242664906) is already in the context buildings.
Brand: the red fascia band and the pylon panel are tagged internal_only (internal stills only). The public export
skips them, which leaves a plain white canopy. No text on any object.
Run after background_b.py: TALANTA_SITE_BLEND=<blend> ~/.venvs/bpy/bin/python blender/context/rubis_station.py
"""
import json, math, os
from pathlib import Path
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[2]
D = json.loads((ROOT / "blender/data/rubis_station.json").read_text())
CLAIM = "Rubis station: position from OSM (node 30092080, ways 654718658, 1242664906); sizes estimated (step R)"
bpy.ops.wm.open_mainfile(filepath=os.environ.get("TALANTA_SITE_BLEND", str(ROOT / "blender/out/talanta_site.blend")))
scene = bpy.context.scene
col = bpy.data.collections.get("rubis_station") or bpy.data.collections.new("rubis_station")
if col.name not in scene.collection.children: scene.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)

terr = bpy.data.objects["terrain_site"]
dg = bpy.context.evaluated_depsgraph_get()
tm = terr.evaluated_get(dg).to_mesh()
bvh = BVHTree.FromPolygons([terr.matrix_world @ v.co for v in tm.vertices], [p.vertices[:] for p in tm.polygons])
terr.evaluated_get(dg).to_mesh_clear()


def ground(x, z):
    hit = bvh.ray_cast(Vector((x, -z, 3000.0)), Vector((0, 0, -1)))
    return hit[0].z if hit[0] is not None else 0.0


def srgb(h):
    h = h.lstrip("#"); return tuple(((int(h[i:i + 2], 16) / 255 + 0.055) / 1.055) ** 2.4 for i in (0, 2, 4))


def mat(name, hx, rough=0.6, emit=None):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*srgb(hx), 1); p.inputs["Roughness"].default_value = rough
    if emit:  # off by day; render_cycles.py switches "night:" nodes on for night and fixture presets
        em = m.node_tree.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*srgb(hx), 1)
        em.inputs["Strength"].default_value = 0.0; em.label = f"night:{emit}"
        add = m.node_tree.nodes.new("ShaderNodeAddShader"); out = m.node_tree.nodes["Material Output"]
        m.node_tree.links.new(p.outputs[0], add.inputs[0]); m.node_tree.links.new(em.outputs[0], add.inputs[1])
        m.node_tree.links.new(add.outputs[0], out.inputs[0])
    m.diffuse_color = (*srgb(hx), 1); m["claim"] = CLAIM
    return m


SLAB = mat("rubis_forecourt_concrete", "#A8A49C", 0.8)
WHITE = mat("rubis_canopy_white", "#EDEDEA", 0.45)
SOFFIT = mat("rubis_canopy_soffit", "#F4F1E8", 0.5, emit=6)
STEEL = mat("rubis_column_grey", "#9A9DA0", 0.4)
ISLAND = mat("rubis_island_kerb", "#C8C4BA", 0.7)
PUMP = mat("rubis_dispenser", "#D9D9D6", 0.4)
BRAND = mat("rubis_brand_red_internal", "#D2232A", 0.5)
BRAND2 = mat("rubis_brand_yellow_internal", "#F2B705", 0.5)


def obj(name, v, f, mats, mi=None, internal=False):
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], f); me.validate()
    bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free(); me.update()  # the app frame is mirrored
    for m in mats: me.materials.append(m)
    if mi: me.polygons.foreach_set("material_index", mi)
    o = bpy.data.objects.new(name, me); col.objects.link(o); o["claim"] = CLAIM; o["sources"] = "blender/data/rubis_station.json"
    if internal: o["internal_only"] = "brand mark: internal stills only, skipped by the public export (Munene, step R)"
    return o


C = D["canopy"]; cx, cz = C["centre_xz"]; th = math.radians(C["bearing_deg_xz"]); ca, sa = math.cos(th), math.sin(th)
def loc(u, w):  # canopy frame (u along the road, w across) -> app (x, z)
    return cx + u * ca - w * sa, cz + u * sa + w * ca


def box(name, u0, u1, w0, w1, z0, z1, m, internal=False, frame=loc):
    v = []
    for z in (z0, z1):
        for u, w in ((u0, w0), (u1, w0), (u1, w1), (u0, w1)):
            x, zz = frame(u, w); v.append((x, -zz, z))
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return obj(name, v, f, [m], internal=internal)


g0 = ground(cx, cz) + 0.12
# forecourt slab: the OSM loop closed along the road kerb
loop = D["forecourt_loop_xz"]
v = [(x, -z, ground(x, z) + 0.1) for x, z in loop]
obj("rubis_forecourt", v, [tuple(range(len(v)))[::-1]], [SLAB])
# canopy
L, W, H, F = C["length_m"], C["depth_m"], C["clear_height_m"], C["fascia_m"]
box("rubis_canopy_roof", -L / 2, L / 2, -W / 2, W / 2, g0 + H, g0 + H + F, WHITE)
box("rubis_canopy_soffit", -L / 2 + 0.2, L / 2 - 0.2, -W / 2 + 0.2, W / 2 - 0.2, g0 + H - 0.05, g0 + H, SOFFIT)
for k, u in enumerate((-L / 3, 0.0, L / 3)):
    box(f"rubis_column_{k}", u - 0.2, u + 0.2, -0.2, 0.2, g0, g0 + H, STEEL)
# brand band round the fascia (internal only): a thin skin 2 cm proud of the fascia, lower half red, top edge yellow
e = 0.02
for nm, z0, z1, m in (("red", g0 + H + 0.15, g0 + H + 0.65, BRAND), ("yellow", g0 + H + 0.68, g0 + H + 0.82, BRAND2)):
    for side, (u0, u1, w0, w1) in enumerate(((-L / 2 - e, L / 2 + e, -W / 2 - e, -W / 2), (-L / 2 - e, L / 2 + e, W / 2, W / 2 + e),
                                             (-L / 2 - e, -L / 2, -W / 2, W / 2), (L / 2, L / 2 + e, -W / 2, W / 2))):
        box(f"rubis_fascia_brand_{nm}_{side}", u0, u1, w0, w1, z0, z1, m, internal=True)
# pump islands and dispensers
P = D["pump_islands"]
for k, u in enumerate((-L / 3, 0.0, L / 3)):
    box(f"rubis_island_{k}", u - P["length_m"] / 2, u + P["length_m"] / 2, -P["width_m"] / 2, P["width_m"] / 2, g0, g0 + 0.18, ISLAND)
    for j, du in enumerate((-1.2, 1.2)):
        box(f"rubis_dispenser_{k}_{j}", u + du - 0.45, u + du + 0.45, -0.3, 0.3, g0 + 0.18, g0 + 2.1, PUMP)
# shop: the OSM shop footprint (way 1242664906) is already a block in the context build; not duplicated here
# pylon sign by the road (panel internal only; the post stays)
px, pz = loc(-L / 2 - 6, -W / 2 - 3)
def pfr(u, w): return px + u * ca - w * sa, pz + u * sa + w * ca
gp = ground(px, pz)
box("rubis_pylon_post", -0.6, 0.6, -0.25, 0.25, gp, gp + 7.5, STEEL, frame=pfr)
box("rubis_pylon_panel", -1.0, 1.0, -0.3, 0.3, gp + 4.0, gp + 7.2, BRAND, internal=True, frame=pfr)

n = len(col.objects); ni = sum(1 for o in col.objects if "internal_only" in o.keys())
print("RUBIS " + json.dumps({"objects": n, "internal_only": ni, "canopy_centre_xz": [cx, cz], "ground": round(g0, 2)}), flush=True)
bpy.ops.wm.save_mainfile()
