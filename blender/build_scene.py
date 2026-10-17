"""Stage 02: look-pass scene. Blockout + context + PBR materials + sun/sky + haze.

Opens blender/out/talanta_blockout.blend and adds:
- terrain (GLO-30 grids from app/public/data, with the Sentinel-2 ground colour; 3 rings with holes),
- buildings (Overture footprints, heights per buildings_src), roads, trees (Sentinel-2 NDVI points),
- physically based materials for the white shell, membrane, concrete, glass, seats, grass and paving,
- a sky + sun lamp for a manifest sun state, and a thin world-volume haze.
No frames, Google Earth imagery or concept renders are used as textures (AGENTS.md rule 2).
Saves blender/out/talanta_scene.blend.
Run from the repo root: ~/.venvs/bpy/bin/python blender/build_scene.py
"""
import json, math, sys
from pathlib import Path
from array import array
import bpy, bmesh

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "app/public/data"
sys.path.insert(0, str(ROOT / "blender/scripts"))
MAN = json.loads((DATA / "manifest.json").read_text())
R_EARTH = 6371000.0

bpy.ops.wm.open_mainfile(filepath=str(ROOT / "blender/out/talanta_blockout.blend"))
scene = bpy.context.scene


def coll(name):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name); scene.collection.children.link(c)
    return c


def f32(name):
    a = array("f"); a.frombytes((DATA / name).read_bytes()); return a


def u32(name):
    a = array("I"); a.frombytes((DATA / name).read_bytes()); return a


def nodes_mat(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    return m, m.node_tree.nodes, m.node_tree.links


# ---------------------------------------------------------------- materials (procedural only)
def principled(name, rgb, rough, metal=0.0, coat=0.0, noise_rough=0.0, noise_scale=0.5, bump=0.0, spec=0.5):
    m, n, l = nodes_mat(name)
    p = n.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*rgb, 1)
    p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal
    if "Coat Weight" in p.inputs: p.inputs["Coat Weight"].default_value = coat
    if "Specular IOR Level" in p.inputs: p.inputs["Specular IOR Level"].default_value = spec
    if noise_rough or bump:
        tc = n.new("ShaderNodeTexCoord"); nz = n.new("ShaderNodeTexNoise")
        nz.inputs["Scale"].default_value = noise_scale; nz.inputs["Detail"].default_value = 6
        l.new(tc.outputs["Object"], nz.inputs["Vector"])
        if noise_rough:
            mr = n.new("ShaderNodeMapRange")
            mr.inputs["To Min"].default_value = rough - noise_rough; mr.inputs["To Max"].default_value = rough + noise_rough
            l.new(nz.outputs["Fac"], mr.inputs["Value"]); l.new(mr.outputs["Result"], p.inputs["Roughness"])
        if bump:
            b = n.new("ShaderNodeBump"); b.inputs["Strength"].default_value = bump
            l.new(nz.outputs["Fac"], b.inputs["Height"]); l.new(b.outputs["Normal"], p.inputs["Normal"])
    m.diffuse_color = (*rgb, 1)
    return m


def image_mat(name, img_file):
    m, n, l = nodes_mat(name)
    p = n.get("Principled BSDF"); p.inputs["Roughness"].default_value = 0.95
    if "Specular IOR Level" in p.inputs: p.inputs["Specular IOR Level"].default_value = 0.25
    t = n.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(str(DATA / img_file)); t.extension = "EXTEND"
    t.interpolation = "Cubic"
    l.new(t.outputs["Color"], p.inputs["Base Color"])
    return m


def attr_mat(name, attr, rough=0.9):
    m, n, l = nodes_mat(name)
    p = n.get("Principled BSDF"); p.inputs["Roughness"].default_value = rough
    a = n.new("ShaderNodeAttribute"); a.attribute_name = attr
    l.new(a.outputs["Color"], p.inputs["Base Color"])
    return m


# Replace the blockout's flat materials with PBR versions of the same identities.
PBR = {
    "white_shell": principled("white_shell_pbr", (0.80, 0.80, 0.78), 0.32, 0.0, coat=0.2, noise_rough=0.06, noise_scale=0.08),
    "membrane": principled("membrane_pbr", (0.86, 0.86, 0.83), 0.55, 0.0, noise_rough=0.08, noise_scale=0.05),
    "concrete": principled("concrete_pbr", (0.55, 0.53, 0.50), 0.85, 0.0, noise_rough=0.05, noise_scale=0.6, bump=0.05),
    "plinth_glass": principled("glass_pbr", (0.04, 0.05, 0.06), 0.06, 0.0, spec=0.6),
    "grass": principled("grass_pbr", (0.10, 0.22, 0.06), 0.85, 0.0, noise_rough=0.05, noise_scale=0.3, bump=0.1),
    "paving": principled("paving_pbr", (0.55, 0.52, 0.47), 0.8, 0.0, noise_rough=0.08, noise_scale=0.4, bump=0.05),
    "earth": principled("earth_pbr", (0.32, 0.19, 0.11), 0.95),
    "track": principled("track_pbr", (0.42, 0.15, 0.09), 0.8),
    "seat_green": principled("seat_green_pbr", (0.04, 0.22, 0.10), 0.4, spec=0.6),
    "seat_red": principled("seat_red_pbr", (0.38, 0.03, 0.04), 0.4, spec=0.6),
}
for o in scene.objects:
    if o.type == "MESH":
        for slot in o.material_slots:
            if slot.material and slot.material.name in PBR: slot.material = PBR[slot.material.name]
if "site_pad" in bpy.data.objects: bpy.data.objects["site_pad"].hide_render = True

# ---------------------------------------------------------------- terrain (3 rings, inner holes)
def terrain(meta, ground, hole, name):
    h = f32(meta["file"]); nx, nz, x0, z0, dx, dz = meta["nx"], meta["nz"], meta["x0"], meta["z0"], meta["dx"], meta["dz"]
    me = bpy.data.meshes.new(name); bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    vs = []
    for r in range(nz):
        for c in range(nx):
            x = x0 + (c + 0.5) * dx; z = z0 + (r + 0.5) * dz
            y = h[r * nx + c] - (x * x + z * z) / (2 * R_EARTH)
            vs.append(bm.verts.new((x, -z, y)))
    def inside(x, z):
        return hole and hole[0] < x < hole[1] and hole[2] < z < hole[3]
    for r in range(nz - 1):
        for c in range(nx - 1):
            xc = x0 + (c + 1) * dx; zc = z0 + (r + 1) * dz
            if inside(xc, zc): continue
            q = [vs[r * nx + c], vs[(r + 1) * nx + c], vs[(r + 1) * nx + c + 1], vs[r * nx + c + 1]]
            f = bm.faces.new(q)
            for lp in f.loops:
                X, Y = lp.vert.co.x, -lp.vert.co.y
                lp[uv].uv = ((X - ground["x0"]) / ground["size"], 1 - (Y - ground["z0"]) / ground["size"])
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); coll("context").objects.link(o)
    o.data.materials.append(image_mat(name + "_mat", ground["file"]))
    o["claim"] = "measured (GLO-30 DEM, Sentinel-2 colour)"
    return o


T, G = MAN["terrain"], MAN["ground"]
box = lambda t, pad: (t["x0"] + pad, t["x0"] + (t["nx"] - 1) * t["dx"] - pad, t["z0"] + pad, t["z0"] + (t["nz"] - 1) * t["dz"] - pad)
terrain(T[0], G[0], None, "terrain_site")
terrain(T[1], G[1], box(T[0], 0), "terrain_far")
terrain(T[2], G[2], box(T[1], 0), "terrain_horizon")

# ---------------------------------------------------------------- buildings and roads
def mesh_from(name, pos, idx, col=None, colname="col", normalize=255.0):
    me = bpy.data.meshes.new(name)
    nv = len(pos) // 3
    me.vertices.add(nv); me.vertices.foreach_set("co", [c for i in range(nv) for c in (pos[3 * i], -pos[3 * i + 2], pos[3 * i + 1])])
    nt = len(idx) // 3
    me.loops.add(nt * 3); me.loops.foreach_set("vertex_index", idx)
    me.polygons.add(nt); me.polygons.foreach_set("loop_start", list(range(0, nt * 3, 3)))
    me.update(); me.validate()
    if col is not None:
        a = me.color_attributes.new(colname, "FLOAT_COLOR", "POINT")
        vals = []
        for i in range(nv): vals += [col[3 * i] / normalize, col[3 * i + 1] / normalize, col[3 * i + 2] / normalize, 1.0]
        a.data.foreach_set("color", vals)
    return me


bpos, bidx = f32(MAN["buildings"]["pos"]), u32(MAN["buildings"]["idx"])
bcol = array("B"); bcol.frombytes((DATA / MAN["buildings"]["col"]).read_bytes())
bo = bpy.data.objects.new("buildings", mesh_from("buildings", bpos, bidx, bcol)); coll("context").objects.link(bo)
bo.data.materials.append(attr_mat("buildings_mat", "col", 0.85)); bo["claim"] = "footprints Overture; heights mixed (see manifest height_src)"
rpos, ridx, rw = f32(MAN["roads"]["pos"]), u32(MAN["roads"]["idx"]), f32(MAN["roads"]["w"])
rc = []
for w in rw: rc += [0.42, 0.41, 0.40] if w >= 9 else [0.45, 0.36, 0.28] if w <= 3 else [0.44, 0.42, 0.40]
ro = bpy.data.objects.new("roads", mesh_from("roads", rpos, ridx, rc, normalize=1.0)); coll("context").objects.link(ro)
ro.location.z = 0.15
ro.data.materials.append(attr_mat("roads_mat", "col", 0.9)); ro["claim"] = "OpenStreetMap via Overture"

# ---------------------------------------------------------------- trees (instances on points)
tr = f32(MAN["trees"]["file"])
pts, sc = [], []
for i in range(0, len(tr), 4):
    x, y, z, s = tr[i], tr[i + 1], tr[i + 2], tr[i + 3]
    if x * x + z * z < 4000 ** 2: pts.append((x, -z, y - 0.5)); sc.append(s)
tme = bpy.data.meshes.new("tree_points"); tme.from_pydata(pts, [], [])
sa = tme.attributes.new("tscale", "FLOAT", "POINT"); sa.data.foreach_set("value", sc)
tobj = bpy.data.objects.new("trees", tme); coll("context").objects.link(tobj); tobj["claim"] = "positions Sentinel-2 NDVI; shapes estimated"
# prototype: trunk + two crowns (acacia-like flat-ish crown), unit scale ~ 1 m -> scaled per point
bm = bmesh.new()
# metres, same proportions as makeTrees() in context.js: trunk 4.6 m, main crown r 3 m, second crown r 1.9 m
bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.34, radius2=0.22, depth=4.6, matrix=__import__("mathutils").Matrix.Translation((0, 0, 2.3)))
for (cx, cy, cz, r, sz) in [(0, 0, 6.2, 3.0, 0.87), (1.7, -0.9, 4.9, 1.9, 0.9)]:
    g = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
    for v in g["verts"]: v.co.z *= sz; v.co.x += cx; v.co.y += cy; v.co.z += cz
proto_me = bpy.data.meshes.new("tree_proto"); bm.to_mesh(proto_me); bm.free()
for p in proto_me.polygons: p.use_smooth = True
proto = bpy.data.objects.new("tree_proto", proto_me); coll("context").objects.link(proto); proto.hide_render = True; proto.hide_viewport = True
leaf = principled("tree_leaf", (0.06, 0.13, 0.04), 0.8, noise_rough=0.1, noise_scale=3, bump=0.3)
proto_me.materials.append(leaf)
gn = bpy.data.node_groups.new("tree_scatter", "GeometryNodeTree")
try:
    gn.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    gn.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
except Exception:
    pass
N_ = gn.nodes; L_ = gn.links
gi, go = N_.new("NodeGroupInput"), N_.new("NodeGroupOutput")
oi = N_.new("GeometryNodeObjectInfo"); oi.inputs["Object"].default_value = proto
na = N_.new("GeometryNodeInputNamedAttribute"); na.data_type = "FLOAT"; na.inputs["Name"].default_value = "tscale"
rnd = N_.new("FunctionNodeRandomValue"); rnd.data_type = "FLOAT"; rnd.inputs["Max"].default_value = 6.283
cr = N_.new("ShaderNodeCombineXYZ"); L_.new(rnd.outputs["Value"], cr.inputs["Z"])
iop = N_.new("GeometryNodeInstanceOnPoints")
L_.new(gi.outputs[0], iop.inputs["Points"]); L_.new(oi.outputs["Geometry"], iop.inputs["Instance"])
L_.new(na.outputs["Attribute"], iop.inputs["Scale"]); L_.new(cr.outputs["Vector"], iop.inputs["Rotation"])
L_.new(iop.outputs["Instances"], go.inputs[0])
mod = tobj.modifiers.new("scatter", "NODES"); mod.node_group = gn
print("trees within 4 km:", len(pts), "scale range", round(min(sc), 2), round(max(sc), 2))

# ---------------------------------------------------------------- world: sky + haze (set per render in render_cycles.py)
w = bpy.data.worlds.new("sky"); scene.world = w
try: w.use_nodes = True
except Exception: pass
n, l = w.node_tree.nodes, w.node_tree.links
sky = n.new("ShaderNodeTexSky"); sky.name = "sky"
sky.sky_type = "MULTIPLE_SCATTERING"; sky.sun_disc = False; sky.altitude = 1800; sky.aerosol_density = 2.0
l.new(sky.outputs["Color"], n["Background"].inputs["Color"])
n["Background"].inputs["Strength"].default_value = 0.35
vol = n.new("ShaderNodeVolumeScatter"); vol.name = "haze"; vol.inputs["Density"].default_value = 3e-5; vol.inputs["Anisotropy"].default_value = 0.6
l.new(vol.outputs["Volume"], n["World Output"].inputs["Volume"])
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); scene.collection.objects.link(sun)
sun.data.angle = math.radians(0.53)

bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / "blender/out/talanta_scene.blend"))
tri = 0
for o in scene.objects:
    if o.type == "MESH": o.data.calc_loop_triangles(); tri += len(o.data.loop_triangles)
print("saved talanta_scene.blend; mesh triangles (excl. tree instances):", tri)
