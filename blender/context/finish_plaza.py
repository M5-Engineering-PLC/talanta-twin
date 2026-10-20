"""Step F (Munene's goal, 2026-10-20: a finish like for like with landing mockups 06 and 07).

The mockups show a wide light plaza round the bowl, a ring of planting beds with shrubs, flowers and trees at its
edge, radiating paths through the lawns and lamp rows. None of that is measured. This step builds it only on
unmeasured ground: a quad is built only where a ray from above lands on the bare site terrain or a lawn, never on a
road, track, pitch, training field or an existing paved or planted surface (W1b, OSM and GE features stay as they are).
- plaza: from the apron ring (18 m out from the plinth) to 32 m, fc_paving
- beds: 32 to 40 m, fc_planting with shrub and flower clumps and trees, broken by a path every 15 deg
- radiating paths: 5 m wide from 40 m outward until they meet a measured feature (max 70 m)
- lamps: a ring at 31 m every 14 m (night_lamp_warm)
- the as-built red murram path surface is pulled toward a warm light paving tone (look only; the paths stay where
  the frames put them)
Everything here is estimated (layout by eye from the mockups' look; nothing traced from them, AGENTS.md rule 2).
Run after rubis_station.py, then run tree_rules.py again (it clears scatter trees off the new paving):
  TALANTA_SITE_BLEND=<blend> ~/.venvs/bpy/bin/python blender/context/finish_plaza.py
"""
import json, math, os
from pathlib import Path
import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[2]
RG = json.loads((ROOT / "blender/out/bowl_rings.json").read_text())
CLAIM = "estimated (step F: plaza, beds and paths in the mockups' look on unmeasured ground; not measured)"
rng = np.random.default_rng(2020)
bpy.ops.wm.open_mainfile(filepath=os.environ.get("TALANTA_SITE_BLEND", str(ROOT / "blender/out/talanta_site.blend")))
scene = bpy.context.scene
col = bpy.data.collections.get("finish_plaza") or bpy.data.collections.new("finish_plaza")
if col.name not in scene.collection.children: scene.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)

SCAT = ("trees", "palms", "site_trees", "fc_retained_site_trees", "fc_retained_palms", "shrubs", "fc_retained_shrubs", "haze_volume")
hidden = [o for o in scene.objects if o.name in SCAT or o.name.startswith(("night_", "ge_apron_lamp", "ge_road_north_east_lamp"))]
for o in hidden: o.hide_viewport = True
dg = bpy.context.evaluated_depsgraph_get()
terr = bpy.data.objects["terrain_site"]; tm = terr.evaluated_get(dg).to_mesh()
bvh = BVHTree.FromPolygons([terr.matrix_world @ v.co for v in tm.vertices], [p.vertices[:] for p in tm.polygons])
terr.evaluated_get(dg).to_mesh_clear()


def ground(x, y):
    h = bvh.ray_cast(Vector((x, y, 3000.0)), Vector((0, 0, -1))); return h[0].z if h[0] is not None else 0.0


FREE_MATS = ("terrain_site_mat", "fc_grass")


def free(x, y):
    """True on bare site terrain or lawn (Blender frame x, y)."""
    hit, loc, _, idx, ob, _ = scene.ray_cast(dg, Vector((x, y, 500.0)), Vector((0, 0, -1)), distance=1000.0)
    if not hit or ob.type != "MESH" or not ob.material_slots: return False
    m = ob.material_slots[ob.data.polygons[idx].material_index].material
    return bool(m) and m.name.startswith(FREE_MATS)


PAVE = bpy.data.materials["fc_paving"]; BEDM = bpy.data.materials["fc_planting"]
LAMP = bpy.data.materials.get("night_lamp_warm"); POLE = bpy.data.materials.get("pole_grey") or bpy.data.materials["fc_kerb"]


def mesh(name, v, f, m, lift=0.0):
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], f); me.validate(); me.update(); me.materials.append(m)
    o = bpy.data.objects.new(name, me); col.objects.link(o); o["claim"] = CLAIM; return o


N = RG["N"]; dirs = RG["dirs"]; rPl = RG["rPl"]
P0, P1, B1 = 18.0, 32.0, 40.0
PATH_EVERY = N // 24  # every 15 deg
report = {}


def band(name, r0, r1, material, lift, skip=lambda i: False):
    v, f, n = [], [], 0
    for i in range(N):
        j = (i + 1) % N
        if skip(i): continue
        ok = all(free(dirs[k][0] * (rPl[k] + rr), -dirs[k][1] * (rPl[k] + rr)) for k in (i, j) for rr in (r0 + 0.5, (r0 + r1) / 2, r1 - 0.5))
        if not ok: continue
        b = len(v)
        for k in (i, j):
            for rr in (r0, r1):
                x, y = dirs[k][0] * (rPl[k] + rr), -dirs[k][1] * (rPl[k] + rr); v.append((x, y, ground(x, y) + lift))
        f.append((b, b + 2, b + 3, b + 1)); n += 1
    mesh(name, v, f, material); return n


is_path = lambda i: i % PATH_EVERY in (0, PATH_EVERY - 1)
report["plaza_quads"] = band("fp_plaza", P0 - 0.5, P1, PAVE, 0.08)
report["bed_quads"] = band("fp_beds", P1, B1, BEDM, 0.1, skip=is_path)

# radiating paths
v, f, npaths = [], [], 0
for i in range(0, N, PATH_EVERY):
    ux, uz = dirs[i]; nx, ny = uz, ux  # Blender frame normal of the radial (x, -z) direction
    r0 = rPl[i] + P1; L = 0.0
    while L < 70.0 and free(ux * (r0 + L + 4), -uz * (r0 + L + 4)): L += 4.0
    if L < 8.0: continue
    b = len(v)
    for rr in np.arange(r0, r0 + L + 0.1, 4.0):
        for s in (-2.5, 2.5):
            x, y = ux * rr + nx * s, -uz * rr + ny * s; v.append((x, y, ground(x, y) + 0.09))
    m = (len(v) - b) // 2
    for k in range(m - 1): f.append((b + 2 * k, b + 2 * k + 1, b + 2 * k + 3, b + 2 * k + 2))
    npaths += 1
mesh("fp_paths", v, f, PAVE); report["paths"] = npaths
dg = bpy.context.evaluated_depsgraph_get()  # the new plaza, beds and paths are hit from here on

# planting: shrubs, flowers and trees in the beds (linked copies of the existing prototypes)
SHRUB = [bpy.data.objects[n] for n in ("sh_0_green", "sh_1_red") if n in bpy.data.objects]
FLOWER = []
for k, hx in enumerate(((0.75, 0.08, 0.1), (0.95, 0.72, 0.08), (0.75, 0.25, 0.6), (0.92, 0.9, 0.86))):
    m = bpy.data.materials.get(f"fp_flower_{k}") or bpy.data.materials.new(f"fp_flower_{k}"); m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*hx, 1); m["claim"] = CLAIM
    me = SHRUB[0].data.copy(); me.name = f"fp_flower_mesh_{k}"; me.materials.clear(); me.materials.append(m); FLOWER.append(me)
TREES = [bpy.data.objects[n] for n in bpy.data.objects.keys() if n.startswith("canopy_broadleaf_") and n.endswith("_high")]
JAC = [bpy.data.objects[n] for n in ("canopy_jacaranda_high",) if n in bpy.data.objects]
PALM = [bpy.data.objects[n] for n in ("sp_0_palm",) if n in bpy.data.objects]


def put(name, src_data, x, y, s, zs=1.0):
    o = bpy.data.objects.new(name, src_data); col.objects.link(o)
    o.location = (x, y, ground(x, y) + 0.1); o.scale = (s, s, s * zs); o.rotation_euler.z = rng.uniform(0, 2 * math.pi)
    o["claim"] = CLAIM; return o


ns = nf = nt = 0
for i in range(N):
    if is_path(i): continue
    ux, uz = dirs[i]
    rr = rPl[i] + rng.uniform(P1 + 1.5, B1 - 1.5); x, y = ux * rr, -uz * rr
    # only where a bed quad was built: the ray lands on the bed itself
    hit, loc, _, idx, ob, _ = scene.ray_cast(dg, Vector((x, y, 500.0)), Vector((0, 0, -1)), distance=1000.0)
    if not (hit and ob.name == "fp_beds"): continue
    for _ in range(3):
        jx, jy = x + rng.uniform(-2.5, 2.5), y + rng.uniform(-2.5, 2.5)
        if rng.random() < 0.55: put(f"fp_shrub_{ns:04d}", SHRUB[int(rng.integers(len(SHRUB)))].data, jx, jy, rng.uniform(0.8, 1.4), 0.7); ns += 1
        else: put(f"fp_flower_{nf:04d}", FLOWER[int(rng.integers(len(FLOWER)))], jx, jy, rng.uniform(0.5, 0.8), 0.45); nf += 1
    if i % 3 == 0 and TREES:
        pool = PALM if (PALM and rng.random() < 0.12) else JAC if (JAC and rng.random() < 0.1) else TREES
        src = pool[int(rng.integers(len(pool)))]; h = rng.uniform(7, 12) if pool is not PALM else rng.uniform(9, 13)
        o = put(f"fp_tree_{nt:03d}", src.data, x, y, h / max(src.dimensions.z, 0.1)); nt += 1
report.update(shrubs=ns, flowers=nf, trees=nt)

# lamp ring at 31 m every 14 m
nl = 0; acc = 0.0
for i in range(N):
    ux, uz = dirs[i]; j = (i + 1) % N
    acc += math.dist((dirs[i][0] * rPl[i], dirs[i][1] * rPl[i]), (dirs[j][0] * rPl[j], dirs[j][1] * rPl[j])) * (rPl[i] + 31) / rPl[i]
    if acc < 14.0: continue
    acc = 0.0; x, y = ux * (rPl[i] + 31), -uz * (rPl[i] + 31)
    hit, loc, _, idx, ob, _ = scene.ray_cast(dg, Vector((x, y, 500.0)), Vector((0, 0, -1)), distance=1000.0)
    if not (hit and ob.name in ("fp_plaza", "ge_apron_ring") or free(x, y)): continue
    g = ground(x, y); v, f = [], []
    for k in range(8):
        a = 2 * math.pi * k / 8; v += [(x + 0.1 * math.cos(a), y + 0.1 * math.sin(a), g), (x + 0.07 * math.cos(a), y + 0.07 * math.sin(a), g + 7.0)]
    for k in range(8): k2 = (k + 1) % 8; f.append((2 * k, 2 * k2, 2 * k2 + 1, 2 * k + 1))
    b = len(v)
    for zz in (7.0, 7.3):
        for dx, dy in ((-0.3, -0.3), (0.3, -0.3), (0.3, 0.3), (-0.3, 0.3)): v.append((x + dx, y + dy, g + zz))
    f += [(b, b + 1, b + 2, b + 3), (b + 4, b + 5, b + 6, b + 7)] + [(b + k, b + (k + 1) % 4, b + 4 + (k + 1) % 4, b + 4 + k) for k in range(4)]
    o = mesh(f"fp_lamp_{nl:03d}", v, f, POLE)
    if LAMP:
        o.data.materials.append(LAMP)
        for p in o.data.polygons[8:]: p.material_index = 1
    nl += 1
report["lamps"] = nl

# as-built murram paths: warm light paving tone (look only)
m = bpy.data.materials["fc_murram"]
if not m.get("step_f_tint"):
    p = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    mix = m.node_tree.nodes.new("ShaderNodeMixRGB"); mix.inputs[0].default_value = 0.75
    mix.inputs[2].default_value = (0.62, 0.55, 0.47, 1); mix.label = "step F: light paving tone"
    if p.inputs["Base Color"].links:
        m.node_tree.links.new(p.inputs["Base Color"].links[0].from_socket, mix.inputs[1])
    else:
        mix.inputs[1].default_value = p.inputs["Base Color"].default_value
    m.node_tree.links.new(mix.outputs[0], p.inputs["Base Color"]); m["step_f_tint"] = True

for o in hidden: o.hide_viewport = False
print("FINISH_PLAZA " + json.dumps(report), flush=True)
bpy.ops.wm.save_mainfile()
