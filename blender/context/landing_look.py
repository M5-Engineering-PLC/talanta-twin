"""Pass E (replica plan 2026-10-20): the landing look, finished state only (L06 dusk, L07 day, the web bundle).

Adds to blender/out/talanta_site.blend (after context_fix.py):
- warm uplights on the facade at dusk: spot lamps round the facade foot, two per lattice bay, aimed up the louvres
  (3000 K). They carry night_energy and dusk_energy, so render_cycles.py lights them at dusk (presets with
  "fixtures") and at night; the RF38 coloured wash keeps its night colours but gets dusk_energy 0 (warm at dusk).
- a warm glow in the set-back ground floor under the ring beam: an emission on the recess material, on only at dusk
  and night ("night:" label, as the other night fixtures). No doors, gates, exits or signs.
- people (collection people_visualization) on the finished plaza and path surfaces, denser toward the bowl, and parked
  cars (collection parked_cars_visualization) along the bay lines of the east car park. Generic low-poly figures and
  cars. Visualization: not a crowd count, not an evacuation or safety simulation, not real occupancy.
Both collections are finished-state only (blender/scene_state.py).
Run from the repo root: ~/.venvs/bpy/bin/python blender/context/landing_look.py
"""
import json, math, os
from pathlib import Path
import numpy as np
import bpy, bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=os.environ.get("TALANTA_SITE_BLEND", str(ROOT / "blender/out/talanta_site.blend")))
scene = bpy.context.scene
rng = np.random.default_rng(2112)
RG = json.loads((ROOT / "blender/out/bowl_rings.json").read_text())
VIS = "Visualization: generic figures and cars for the landing look; not a crowd count, occupancy or safety simulation"
report = {}


def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in scene.collection.children: scene.collection.children.link(c)
    for o in list(c.objects): bpy.data.objects.remove(o)
    c["claim"] = VIS; return c


def srgb(h):
    h = h.lstrip("#"); return tuple(((int(h[i:i + 2], 16) / 255 + 0.055) / 1.055) ** 2.4 for i in (0, 2, 4))


def mat(name, hx, rough=0.7):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*srgb(hx), 1); p.inputs["Roughness"].default_value = rough; m.diffuse_color = (*srgb(hx), 1)
    return m


# 1. warm uplights, two per bay round the facade foot
N, dirs, rPl, prof = RG["N"], RG["dirs"], RG["rPl"], RG["prof"]
up_col = bpy.data.collections.get("night_lights")
for o in [o for o in bpy.data.objects if o.name.startswith("dusk_uplight_")]: bpy.data.objects.remove(o)
K = 48; pts = []
# outside the widest ring of the facade (the ring beam and barrel overhang the plinth), so the light grazes the louvres
JF = RG.get("j_fascia", len(prof[0]) - 1); rOut = [max(q[0] for q in prof[i][:JF + 1]) + 2.0 for i in range(N)]
ring = np.array([[dirs[i][0] * rOut[i], dirs[i][1] * rOut[i]] for i in range(N)] + [[dirs[0][0] * rOut[0], dirs[0][1] * rOut[0]]])
d_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(ring, axis=0), axis=1))]
for k in range(K):
    s_ = d_[-1] * (k + 0.5) / K; x, z = np.interp(s_, d_, ring[:, 0]), np.interp(s_, d_, ring[:, 1])
    ld = bpy.data.lights.new(f"dusk_uplight_{k:02d}", "SPOT"); ld.energy = 0.0; ld.color = (1.0, 0.72, 0.42)  # about 3000 K
    ld.spot_size = math.radians(48); ld.spot_blend = 0.8; ld.shadow_soft_size = 0.4
    o = bpy.data.objects.new(ld.name, ld); (up_col or scene.collection).objects.link(o)
    o.location = (x, -z, RG["pad"] + 0.4); r_ = math.hypot(x, z); aim = Vector((x - 4 * x / r_, -(z - 4 * z / r_), RG["pad"] + 40))
    o.rotation_euler = (aim - o.location).normalized().to_track_quat("-Z", "Y").to_euler()
    o["night_energy"] = 30000.0; o["dusk_energy"] = 30000.0; o["claim"] = "Visualization (dusk uplight, warm white)"
for o in bpy.data.objects:
    if o.name.startswith("night_wash_"): o["dusk_energy"] = 0.0
report["uplights"] = K

# 2. warm glow in the ground-floor recess (dusk and night only)
rm = bpy.data.materials.get("concrete_recess_dark_pbr")
if rm and not rm.get("pass_e_glow"):
    n_, l_ = rm.node_tree.nodes, rm.node_tree.links
    em = n_.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*srgb("#FFB46A"), 1); em.inputs["Strength"].default_value = 0.0
    em.label = "night:2.5"; out = n_["Material Output"]; prev = out.inputs["Surface"].links[0].from_socket
    add = n_.new("ShaderNodeAddShader"); l_.new(prev, add.inputs[0]); l_.new(em.outputs[0], add.inputs[1]); l_.new(add.outputs[0], out.inputs["Surface"])
    rm["pass_e_glow"] = "Visualization (warm glow in the recess at dusk and night)"; report["recess_glow"] = True

# 3. people on the finished plaza and path surfaces
SURF = [o for o in bpy.data.objects if o.type == "MESH" and (o.name in ("fp_plaza", "fp_paths", "north_plaza") or o.name.startswith("fc_path_") and "kerb" not in o.name)]
tris = []
dg = bpy.context.evaluated_depsgraph_get()
for o in SURF:
    me = o.evaluated_get(dg).to_mesh(); me.calc_loop_triangles(); M = o.matrix_world
    for t in me.loop_triangles:
        a, b, c = (M @ me.vertices[i].co for i in t.vertices)
        if t.normal.z < 0.8: continue
        tris.append((a, b, c, ((b - a).cross(c - a)).length / 2))
    o.evaluated_get(dg).to_mesh_clear()
pc = coll("people_visualization"); nppl = 0
if tris:
    area = np.array([t[3] for t in tris]); cen = np.array([[(t[0].x + t[1].x + t[2].x) / 3, (t[0].y + t[1].y + t[2].y) / 3] for t in tris])
    w = area / (1 + (np.hypot(cen[:, 0], cen[:, 1]) / 150) ** 2); w /= w.sum()
    cloth = [mat(f"people_cloth_{i}", h) for i, h in enumerate(("#F2F2EE", "#1E1F22", "#B8202C", "#2A5C9A", "#E3B23C", "#3E7D4C", "#7A4E9C"))]
    skin = mat("people_skin", "#6B4A35")
    bm = bmesh.new(); midx = []
    for _ in range(2600):
        a, b, c, _a = tris[int(rng.choice(len(tris), p=w))]
        u, v = rng.random(2); u, v = (1 - u, 1 - v) if u + v > 1 else (u, v); p = a + (b - a) * u + (c - a) * v
        h = rng.uniform(1.55, 1.85); ci = int(rng.integers(len(cloth)))
        g = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.21, radius2=0.17, depth=h * 0.82)
        for vv in g["verts"]: vv.co += Vector((p.x, p.y, p.z + h * 0.41))
        for f in {f for vv in g["verts"] for f in vv.link_faces}: f.material_index = ci
        g = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.12)
        for vv in g["verts"]: vv.co += Vector((p.x, p.y, p.z + h * 0.9))
        for f in {f for vv in g["verts"] for f in vv.link_faces}: f.material_index = len(cloth)
        nppl += 1
    me = bpy.data.meshes.new("people_visualization"); bm.to_mesh(me); bm.free()
    for m_ in cloth + [skin]: me.materials.append(m_)
    o = bpy.data.objects.new("people_visualization", me); pc.objects.link(o); o["claim"] = VIS
report["people"] = nppl

# 4. parked cars along the east car park bay lines
cc = coll("parked_cars_visualization"); ncar = 0
paints = [mat(f"parked_paint_{i}", h, 0.35) for i, h in enumerate(("#EBE9DF", "#282A2D", "#B23C32", "#365B85", "#8D9A81", "#D0D3D5", "#C9CCCF", "#191B1D"))]
glass = mat("parked_glass", "#1D262C", 0.15)
bm = bmesh.new()
for o in [o for o in bpy.data.objects if o.name.startswith("ge_east_hardstanding_bayline_")]:
    vs = [o.matrix_world @ v.co for v in o.data.vertices]
    if len(vs) < 2: continue
    P = np.array([tuple(v) for v in vs]); c0 = P.mean(0); _, _, Vt = np.linalg.svd(P[:, :2] - c0[:2]); ax = Vt[0]; nrm = np.array([-ax[1], ax[0]])
    t = (P[:, :2] - c0[:2]) @ ax; z0 = float(np.median(P[:, 2]))
    for s_ in np.arange(t.min() + 2, t.max() - 2, 2.6):
        for side in (-1, 1):
            if rng.random() > 0.72: continue
            x, y = c0[:2] + ax * s_ + nrm * side * 2.6; L_, W_, H_ = rng.uniform(4.2, 4.8), 1.8, rng.uniform(1.4, 1.6)
            ci = int(rng.integers(len(paints)))
            for (cx, cy, cz, sx, sy, sz, mi) in ((0, 0, 0.55, W_, L_, 0.75, ci), (0, -0.2, 1.1, W_ * 0.9, L_ * 0.55, H_ - 0.95, len(paints))):
                g = bmesh.ops.create_cube(bm, size=1.0)
                for vv in g["verts"]:
                    lx, ly, lz = vv.co.x * sx + cx, vv.co.y * sy + cy, vv.co.z * sz + cz
                    vv.co = Vector((x + lx * nrm[0] + ly * ax[0], y + lx * nrm[1] + ly * ax[1], z0 + 0.05 + lz))
                for f in {f for vv in g["verts"] for f in vv.link_faces}: f.material_index = mi
            ncar += 1
me = bpy.data.meshes.new("parked_cars_visualization"); bm.to_mesh(me); bm.free()
for m_ in paints + [glass]: me.materials.append(m_)
o = bpy.data.objects.new("parked_cars_visualization", me); cc.objects.link(o); o["claim"] = VIS
report["parked_cars"] = ncar
print("LANDING_LOOK " + json.dumps(report), flush=True)
bpy.ops.wm.save_mainfile()
