"""Stage 03, detail sheets RF and SR: the finished site and the roof/facade night fixtures.

Opens blender/out/talanta_scene.blend (build_scene.py) and adds, from blender/data/site_plan.json
(gis/scripts/export_site_plan.py) and the ledger:
- Ngong Road as a finished dual carriageway (lead review correction 3, frame JWNowpO44rw 07:04): lanes, edge and
  lane markings, a central reserve with a concrete barrier, kerbs, drains, footpaths and a murram service strip.
- the two training tracks with lanes and grass infields, the SE training pitch, pitch markings and track masts
  (finished state from the design model, lead review correction 1),
- palm avenues along the forecourt paths (correction 2), broad-crowned trees in clumps, shrubs and flower beds,
  raised planters, flag masts, light masts, path lights, bollards, a jet deck, a plain boundary fence, blank sign
  frames, two generic entrance canopies (correction 8) and car-park bay lines,
- the dark border round the roof opening (RF26) and the night fixtures RF25, RF31, RF38-RF41. Night fixtures are
  off by day; blender/render_cycles.py switches them on for the night sun state. Night lighting is a Visualization
  of the effect seen in the frames, not a lighting layout.
No frames, Google Earth imagery or concept images are used as textures (AGENTS.md rule 2). No gates, exits,
security cameras or control rooms (rule 8).
Saves blender/out/talanta_site.blend (render_cycles.py opens it).
Run from the repo root: ~/.venvs/bpy/bin/python blender/build_site_detail.py
"""
import csv, json, math
from pathlib import Path
import numpy as np
import bpy, bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[1]
L = {r["name"]: r for r in csv.DictReader(open(ROOT / "gis/parameter_ledger.csv"))}
V = lambda k: float(L[k + "_blockout"]["value"]) if k + "_blockout" in L else float(L[k]["value"])
S = lambda k: L[k]["value"]
P = json.loads((ROOT / "blender/data/site_plan.json").read_text())
RG = json.loads((ROOT / "blender/out/bowl_rings.json").read_text())
PAD = RG["pad"]
rng = np.random.default_rng(31)

bpy.ops.wm.open_mainfile(filepath=str(ROOT / "blender/out/talanta_scene.blend"))
scene = bpy.context.scene
for nm in ("warmup_track", "training_field_sw", "training_pitch_se", "north_plaza", "site_pad"):
    if nm in bpy.data.objects: bpy.data.objects[nm].hide_render = True; bpy.data.objects[nm].hide_viewport = True


def coll(name):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name); scene.collection.children.link(c)
    return c


def srgb(h):
    h = h.lstrip("#"); return tuple(((int(h[i:i + 2], 16) / 255 + 0.055) / 1.055) ** 2.4 for i in (0, 2, 4))


def mat(name, hex_, rough=0.8, metal=0.0, night=None, emit_hex=None, alpha=None):
    """Principled material from a sheet hex. night = emission strength switched on for the night sun state."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*srgb(hex_), 1); p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal; m.diffuse_color = (*srgb(hex_), 1)
    if night is not None:
        p.inputs["Emission Color"].default_value = (*srgb(emit_hex or hex_), 1); p.inputs["Emission Strength"].default_value = 0.0
        p.label = f"night:{night}"
    if alpha is not None: p.inputs["Alpha"].default_value = alpha
    return m


def mesh_obj(name, verts, faces, materials, collection, claim, uvs=None, mat_idx=None, smooth=False):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.validate(); me.update()
    for m_ in (materials if isinstance(materials, list) else [materials]): me.materials.append(m_)
    if mat_idx is not None: me.polygons.foreach_set("material_index", mat_idx)
    if uvs is not None:
        uvl = me.uv_layers.new(name="UVMap")
        for poly in me.polygons:
            for li in poly.loop_indices: uvl.data[li].uv = uvs[me.loops[li].vertex_index]
    if smooth:
        for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); coll(collection).objects.link(o); o["claim"] = claim
    return o


# ---------------------------------------------------------------- terrain height (local x, z south -> Blender z)
dg = bpy.context.evaluated_depsgraph_get()
BVH = [BVHTree.FromObject(bpy.data.objects[n], dg) for n in ("terrain_site", "terrain_far") if n in bpy.data.objects]
def hT(x, z):
    for b in BVH:
        hit = b.ray_cast(Vector((x, -z, 3000)), Vector((0, 0, -1)))
        if hit[0]: return hit[0].z
    return PAD
def B(x, z, dy=0.0): return (x, -z, hT(x, z) + dy)

# ---------------------------------------------------------------- Ngong Road (SR19-SR23, SR27-SR29; correction 3)
NG = P["ngong"]; mid = np.array(NG["mid"], float)
t = np.gradient(mid, axis=0); t /= np.linalg.norm(t, axis=1)[:, None]; nrm = np.stack([-t[:, 1], t[:, 0]], 1)
half_cw = NG["half_carriageway"]; m2 = NG["median_w"] / 2
KH, LW = V("ngong.kerb_h"), V("ngong.lane_w")
ASPH = mat("ngong_asphalt", "#424541", 0.88); KERB = mat("kerb_concrete", "#8B877D", 0.85)
DRAIN = mat("drain_channel", "#827C70", 0.9); FOOT = mat("footpath_paving", "#B9B3A5", 0.85)
MURR = mat("service_murram", "#8B4A2B", 0.95); MED = mat("median_concrete", "#A8A69E", 0.85)
PAINT = mat("road_paint", "#E7E6DF", 0.55)
r0 = half_cw + V("ngong.kerb_w"); r1 = r0 + V("ngong.drain_w"); r2 = r1 + V("ngong.footpath_w"); r3 = r2 + V("ngong.service_w")
# bands: (offset from, offset to, height above terrain, material index); carriageway split per lane to follow the ground
LIFT = 0.4
bands = [(-m2, m2, LIFT + 0.15, 4)]
for sg in (1, -1):
    edges = [m2] + [m2 + k * LW for k in range(1, int(NG["lanes_per_dir"]) + 1)] + [half_cw]
    for a_, b_ in zip(edges, edges[1:]): bands.append((sg * a_, sg * b_, LIFT, 0))
    bands += [(sg * half_cw, sg * r0, LIFT + KH, 1), (sg * r0, sg * r1, LIFT - 0.05, 2), (sg * r1, sg * r2, LIFT + KH, 3), (sg * r2, sg * r3, LIFT - 0.1, 5)]
verts, faces, midx = [], [], []
H = {}
def vtx(i, off, dy):
    key = (i, round(off, 3), round(dy, 3))
    if key not in H:
        x, z = mid[i] + nrm[i] * off; H[key] = len(verts); verts.append(B(x, z, dy))
    return H[key]
for a_, b_, dy, mi in bands:
    lo, hi = sorted((a_, b_))
    for i in range(len(mid) - 1):
        q = [vtx(i, lo, dy), vtx(i + 1, lo, dy), vtx(i + 1, hi, dy), vtx(i, hi, dy)]
        faces.append(q); midx.append(mi)
# kerb faces (vertical) at the carriageway and footpath edges
for sg in (1, -1):
    for off, d0, d1 in ((half_cw, LIFT, LIFT + KH), (r1, LIFT - 0.05, LIFT + KH), (r0, LIFT - 0.05, LIFT + KH)):
        for i in range(len(mid) - 1):
            faces.append([vtx(i, sg * off, d0), vtx(i + 1, sg * off, d0), vtx(i + 1, sg * off, d1), vtx(i, sg * off, d1)]); midx.append(1)
ng = mesh_obj("ngong_road", verts, faces, [ASPH, KERB, DRAIN, FOOT, MED, MURR], "context", "estimated (detail sheets SR19-SR29; lead correction 3, frame 07:04); centreline OSM", mat_idx=midx)
# central concrete barrier: a safety-shape section swept along the median
sec = [(-0.30, 0), (-0.17, 0.25), (-0.09, V("ngong.barrier_h")), (0.09, V("ngong.barrier_h")), (0.17, 0.25), (0.30, 0)]
verts, faces = [], []
for i in range(len(mid)):
    hb = hT(*mid[i]) + LIFT + 0.15
    for su, sy in sec: x, z = mid[i] + nrm[i] * su; verts.append((x, -z, hb + sy))
for i in range(len(mid) - 1):
    for k in range(len(sec) - 1):
        a0 = i * len(sec) + k; faces.append([a0, a0 + 1, a0 + 1 + len(sec), a0 + len(sec)])
mesh_obj("ngong_barrier", verts, faces, [mat("barrier_concrete", "#BDBBB3", 0.8)], "context", "estimated (detail sheet SR29; frame 07:04)", smooth=True)
# markings: solid edge lines and dashed lane lines (SR21, SR22)
seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(mid, axis=0), axis=1))]
def at(s, off):
    i = min(int(np.searchsorted(seg, s)) - 1, len(mid) - 2); i = max(i, 0); f = (s - seg[i]) / (seg[i + 1] - seg[i])
    p = mid[i] * (1 - f) + mid[i + 1] * f; n_ = nrm[i] * (1 - f) + nrm[i + 1] * f; return p + n_ * off
verts, faces = [], []
def stripe(s0, s1, off, w):
    for s_ in np.arange(s0, s1, 5.0):
        e = min(s_ + 5.0, s1); b0 = len(verts)
        for ss, oo in ((s_, off - w / 2), (e, off - w / 2), (e, off + w / 2), (s_, off + w / 2)):
            x, z = at(ss, oo); verts.append(B(x, z, LIFT + 0.03))
        faces.append([b0, b0 + 1, b0 + 2, b0 + 3])
lw_, dl, dgp = V("ngong.line_w"), V("ngong.dash_len"), V("ngong.dash_gap")
for sg in (1, -1):
    stripe(0, seg[-1], sg * (m2 + 0.3), lw_); stripe(0, seg[-1], sg * (half_cw - 0.3), lw_)
    for k in range(1, int(NG["lanes_per_dir"])):
        for s_ in np.arange(0, seg[-1] - dl, dl + dgp): stripe(s_, s_ + dl, sg * (m2 + k * LW), lw_)
mesh_obj("ngong_markings", verts, faces, [PAINT], "context", "estimated (detail sheets SR21, SR22)")

# ---------------------------------------------------------------- sport surfaces (SR42-SR47; correction 1)
def stadium_pts(R, Sx, n_arc=40, n_str=20):
    """Closed stadium outline (along, across) about the centre: straights of half-length Sx, end radius R."""
    pts = []
    for k in range(n_str): pts.append((-Sx + 2 * Sx * k / n_str, -R))
    for k in range(n_arc): a = -math.pi / 2 + math.pi * k / n_arc; pts.append((Sx + R * math.cos(a), R * math.sin(a)))
    for k in range(n_str): pts.append((Sx - 2 * Sx * k / n_str, R))
    for k in range(n_arc): a = math.pi / 2 + math.pi * k / n_arc; pts.append((-Sx + R * math.cos(a), R * math.sin(a)))
    return pts
def frame_of(d):
    c, a = np.array(d["c"]), np.array(d["axis"]); e = np.array([-a[1], a[0]]); return c, a, e
def to_xz(c, a, e, al, ac): p = c + a * al + e * ac; return float(p[0]), float(p[1])
TRK = mat("track_surface", "#9A493D", 0.85)
tn_ = TRK.node_tree.nodes; tl_ = TRK.node_tree.links
uvn = tn_.new("ShaderNodeUVMap"); sep = tn_.new("ShaderNodeSeparateXYZ"); tl_.new(uvn.outputs["UV"], sep.inputs[0])
NL = int(V("site.track.lanes"))
mul = tn_.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = NL; tl_.new(sep.outputs["Y"], mul.inputs[0])
rnd = tn_.new("ShaderNodeMath"); rnd.operation = "ROUND"; tl_.new(mul.outputs[0], rnd.inputs[0])
dif = tn_.new("ShaderNodeMath"); dif.operation = "SUBTRACT"; tl_.new(mul.outputs[0], dif.inputs[0]); tl_.new(rnd.outputs[0], dif.inputs[1])
ab = tn_.new("ShaderNodeMath"); ab.operation = "ABSOLUTE"; tl_.new(dif.outputs[0], ab.inputs[0])
ln = tn_.new("ShaderNodeMath"); ln.operation = "LESS_THAN"; ln.inputs[1].default_value = 0.05 / V("site.track.lane_w"); tl_.new(ab.outputs[0], ln.inputs[0])
mx = tn_.new("ShaderNodeMix"); mx.data_type = "RGBA"; tl_.new(ln.outputs[0], mx.inputs[0])
mx.inputs[6].default_value = (*srgb("#9A493D"), 1); mx.inputs[7].default_value = (*srgb("#EDEBE4"), 1)
tl_.new(mx.outputs[2], tn_["Principled BSDF"].inputs["Base Color"])
def striped_grass(name, stripe_w=5.0):
    """Mowing stripes along UV x plus the pass K variation (blender/grass_look.py, K4)."""
    import sys; sys.path.insert(0, str(ROOT / "blender")); import grass_look
    return grass_look.build(mat(name, grass_look.STRIPE[0], 0.85), stripe_w)
GR = striped_grass("training_grass")
def fan(name, outline, c, a, e, dy, material, claim):
    """Filled outline draped on the terrain; UV = metres along/across the axis (for stripes)."""
    verts = [B(*to_xz(c, a, e, 0, 0), dy)]; uvs = [(0, 0)]
    for al, ac in outline: verts.append(B(*to_xz(c, a, e, al, ac), dy)); uvs.append((al, ac))
    n = len(outline); faces = [[0, 1 + k, 1 + (k + 1) % n] for k in range(n)]
    # subdivide radially so the fill follows the ground
    me = bmesh.new(); vs = [me.verts.new(v) for v in verts]
    uvl = me.loops.layers.uv.new("UVMap")
    for f in faces:
        ff = me.faces.new([vs[i] for i in f])
        for lp, i in zip(ff.loops, f): lp[uvl].uv = uvs[i]
    bmesh.ops.subdivide_edges(me, edges=me.edges[:], cuts=6, use_grid_fill=True)
    for v in me.verts:
        v.co.z = hT(v.co.x, -v.co.y) + dy
    m_ = bpy.data.meshes.new(name); me.to_mesh(m_); me.free(); m_.materials.append(material)
    o = bpy.data.objects.new(name, m_); coll("sport").objects.link(o); o["claim"] = claim; return o
LINE = mat("pitch_line", "#F3F1E9", 0.6)
lines_v, lines_f = [], []
def seg_line(c, a, e, p0, p1, dy, w=0.12):
    d = np.subtract(p1, p0); Ld = np.linalg.norm(d)
    if Ld < 1e-6: return
    d /= Ld; n_ = np.array([-d[1], d[0]]) * w / 2
    for s0 in np.arange(0, Ld, 4.0):
        s1 = min(s0 + 4.0, Ld); b0 = len(lines_v)
        for (s, o) in ((s0, -1), (s1, -1), (s1, 1), (s0, 1)):
            al, ac = np.add(p0, d * s) + n_ * o; lines_v.append(B(*to_xz(c, a, e, al, ac), dy))
        lines_f.append([b0, b0 + 1, b0 + 2, b0 + 3])
def poly_line(c, a, e, pts, dy, closed=False):
    for p0, p1 in zip(pts, pts[1:] + ([pts[0]] if closed else [])): seg_line(c, a, e, p0, p1, dy)
def markings(c, a, e, Lp, Wp, dy):
    """IFAB Law 1 lines for a Lp x Wp pitch (same layout as the main pitch, build_bowl_detail.py)."""
    hl, hw = Lp / 2, Wp / 2
    poly_line(c, a, e, [(-hl, -hw), (hl, -hw), (hl, hw), (-hl, hw)], dy, True); seg_line(c, a, e, (0, -hw), (0, hw), dy)
    poly_line(c, a, e, [(9.15 * math.cos(2 * math.pi * k / 48), 9.15 * math.sin(2 * math.pi * k / 48)) for k in range(48)], dy, True)
    for sg in (1, -1):
        poly_line(c, a, e, [(sg * hl, -20.16), (sg * (hl - 16.5), -20.16), (sg * (hl - 16.5), 20.16), (sg * hl, 20.16)], dy)
        poly_line(c, a, e, [(sg * hl, -9.16), (sg * (hl - 5.5), -9.16), (sg * (hl - 5.5), 9.16), (sg * hl, 9.16)], dy)
mastpts = []
for d in P["tracks"]:
    c, a, e = frame_of(d); R0 = d["W"] / 2; Sx = (d["L"] - d["W"]) / 2; band = NL * V("site.track.lane_w") + 0.6
    rows = [R0 - k * (band / NL) for k in range(NL + 1)]
    out = [stadium_pts(r, Sx) for r in rows]; n = len(out[0])
    verts, faces, uvs = [], [], []
    for k, ring_ in enumerate(out):
        for al, ac in ring_: verts.append(B(*to_xz(c, a, e, al, ac), 0.18)); uvs.append((0, k / NL))
    for k in range(NL):
        for i in range(n): faces.append([k * n + i, k * n + (i + 1) % n, (k + 1) * n + (i + 1) % n, (k + 1) * n + i])
    mesh_obj(d["name"], verts, faces, [TRK], "sport", "outline measured (W1b); lanes estimated (detail sheet SR43); finished state (design model)", uvs=uvs)
    fan(d["name"] + "_infield", stadium_pts(R0 - band - 0.3, Sx), c, a, e, 0.16, GR, "estimated (detail sheet SR44; design model)")
    Lp, Wp = (105, 68) if 2 * (R0 - band) > 75 else (100, 64)
    markings(c, a, e, Lp, Wp, 0.2)
    for sl in (1, -1):
        for sc in (1, -1): mastpts.append(to_xz(c, a, e, sl * (Sx + R0 * 0.55), sc * (R0 + 5)))
d = P["pitch_se"]; c, a, e = frame_of(d)
fan("training_pitch_se_turf", [(d["L"] / 2 * math.cos(2 * math.pi * k / 4 + math.pi / 4) * math.sqrt(2), d["W"] / 2 * math.sin(2 * math.pi * k / 4 + math.pi / 4) * math.sqrt(2)) for k in range(4)],
    c, a, e, 0.16, GR, "outline measured (W1b); finished grass (detail sheet SR45)")
markings(c, a, e, 105, 68, 0.2)
for sl in (1, -1):
    for sc in (1, -1): mastpts.append(to_xz(c, a, e, sl * (d["L"] / 2 - 10), sc * (d["W"] / 2 + 3)))
mesh_obj("training_pitch_lines", lines_v, lines_f, [LINE], "sport", "IFAB Law 1 (derived); positions on the W1b outlines")

# ---------------------------------------------------------------- prototypes for instancing
protos = coll("site_protos"); protos.hide_render = True; protos.hide_viewport = True
def proto(name, bm, materials):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m_ in materials: me.materials.append(m_)
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); protos.objects.link(o); return o
def cyl(bm, r0, r1, h, z0=0.0, seg=8, xy=(0, 0)):
    return bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r0, radius2=r1, depth=h, matrix=Matrix.Translation((xy[0], xy[1], z0 + h / 2)))
def boxm(bm, sx, sy, sz, c):
    g = bmesh.ops.create_cube(bm, size=1); bmesh.ops.scale(bm, vec=(sx, sy, sz), verts=g["verts"]); bmesh.ops.translate(bm, vec=c, verts=g["verts"]); return g
def set_mat(g, idx):
    for f in {f for v in g["verts"] for f in v.link_faces}: f.material_index = idx
# palm (SR38; correction 2): slightly curved ringed trunk, a crown of drooping fronds
PH = V("site.palm.h")
TRUNK = mat("palm_trunk", "#715A42", 0.9); FROND = mat("palm_frond", "#48673D", 0.7)
fr = FROND.node_tree.nodes; fp = fr["Principled BSDF"]
if "Subsurface Weight" in fp.inputs: fp.inputs["Subsurface Weight"].default_value = 0.0
bm = bmesh.new()
segs_ = 8
for k in range(segs_):
    z0 = PH * k / segs_; r_ = 0.2 - 0.06 * k / segs_; bx = 0.25 * (k / segs_) ** 2
    g = cyl(bm, r_, r_ * 0.92, PH / segs_, z0, 7, (bx, 0)); set_mat(g, 0)
top = Vector((0.25, 0, PH))
for k in range(16):
    az = 2 * math.pi * k / 16 + rng.uniform(-0.15, 0.15); el = rng.uniform(0.15, 0.6) if k % 2 else rng.uniform(-0.1, 0.3)
    Lf = rng.uniform(3.0, 4.0); n_ = 6; vs = []
    for i in range(n_ + 1):
        s = i / n_; rr = Lf * s; z = math.sin(el) * rr - 1.4 * s * s * Lf / 3.5
        w = 0.55 * math.sin(math.pi * min(s * 1.15, 1.0)) + 0.04
        cx, cy = math.cos(az) * rr * math.cos(el), math.sin(az) * rr * math.cos(el)
        px, py = -math.sin(az) * w, math.cos(az) * w
        vs.append([bm.verts.new(top + Vector((cx + px, cy + py, z - 0.12 * w))), bm.verts.new(top + Vector((cx, cy, z + 0.05))), bm.verts.new(top + Vector((cx - px, cy - py, z - 0.12 * w)))])
    for i in range(n_):
        for j in range(2):
            f = bm.faces.new([vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]]); f.material_index = 1
g = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.45); bmesh.ops.translate(bm, vec=top, verts=g["verts"]); set_mat(g, 1)
palm = proto("sp_0_palm", bm, [TRUNK, FROND])
# trees from build_scene.py prototypes, plus a jacaranda-like variant (SR40, optional seasonal detail)
tp = {o.name: o for o in bpy.data.collections["tree_protos"].objects}
def copy_proto(src, name, leaf=None):
    me = src.data.copy(); me.name = name
    if leaf: me.materials[0] = leaf
    o = bpy.data.objects.new(name, me); protos.objects.link(o); return o
t_round = copy_proto(tp["tree_0_round"], "st_0_round"); t_acacia = copy_proto(tp["tree_1_acacia"], "st_1_acacia")
t_euc = copy_proto(tp["tree_2_eucalyptus"], "st_2_eucalyptus")
t_jac = copy_proto(tp["tree_0_round"], "st_3_jacaranda", mat("jacaranda_leaf", "#A58CCB", 0.8))
for o, hx in ((t_round, "#36583B"), (t_acacia, "#3F5E36")):  # SR39 leaves, a little lighter than the far forest
    m_ = o.data.materials[0].copy(); m_.name = o.name + "_leaf"; m_.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*srgb(hx), 1); o.data.materials[0] = m_
# shrubs (SR09) green and flowering red (design model)
def shrub(name, hexes):
    bm = bmesh.new(); g = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.6)
    for v in g["verts"]: v.co.z = v.co.z * 0.7 + 0.35
    return proto(name, bm, [mat(name + "_m", hexes, 0.8)])
sh_g, sh_r = shrub("sh_0_green", "#48633D"), shrub("sh_1_red", S("site.bed.flower_rgb"))
# masts and lights (SR15-SR17, RF41)
WHITE_METAL = mat("mast_white", "#E9E8E3", 0.35, 0.3); GREYP = mat("pole_grey", "#626967", 0.5, 0.6)
LAMP = mat("night_lamp_warm", "#F5F3E8", 0.3, night=30.0, emit_hex="#FFE2B0"); FLOOD = mat("night_flood", "#E8E8E2", 0.3, night=60.0, emit_hex="#FFFFFF")
FLAG = mat("flag_plain", "#D6D1C5", 0.8)
bm = bmesh.new(); MH = V("site.masts.h")
g = cyl(bm, 0.45, 0.25, MH, 0, 10); set_mat(g, 0); g = boxm(bm, 2.6, 1.2, 1.2, (0, 0, MH + 0.2)); set_mat(g, 1)
lmast = proto("lm_lightmast", bm, [WHITE_METAL, FLOOD])
bm = bmesh.new(); TH = V("site.track.mast_h")
g = cyl(bm, 0.35, 0.2, TH, 0, 8); set_mat(g, 0); g = boxm(bm, 3.0, 0.8, 1.6, (0, 0, TH + 0.2)); set_mat(g, 1)
tmast = proto("tm_trackmast", bm, [WHITE_METAL, FLOOD])
bm = bmesh.new(); fw, fh = V("site.flag.w"), V("site.flag.h")
g = cyl(bm, 0.12, 0.08, MH, 0, 8); set_mat(g, 0)
vs = []
for i in range(9):
    s = i / 8; x = 0.1 + fw * s; y = 0.25 * math.sin(s * 2.2 * math.pi) * s
    vs.append((bm.verts.new((x, y, MH - 0.3)), bm.verts.new((x, y, MH - 0.3 - fh))))
for i in range(8):
    f = bm.faces.new([vs[i][0], vs[i + 1][0], vs[i + 1][1], vs[i][1]]); f.material_index = 1
fmast = proto("fm_flagmast", bm, [WHITE_METAL, FLAG])
bm = bmesh.new(); PLH = V("site.pathlight.h")
g = cyl(bm, 0.08, 0.06, PLH, 0, 6); set_mat(g, 0); g = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.28); bmesh.ops.translate(bm, vec=(0, 0, PLH + 0.1), verts=g["verts"]); set_mat(g, 1)
plight = proto("pl_pathlight", bm, [GREYP, LAMP])
bm = bmesh.new(); g = cyl(bm, 0.1, 0.1, V("site.bollard.h"), 0, 8)
bollard = proto("bo_bollard", bm, [mat("bollard_grey", "#777B78", 0.6, 0.4)])
SPRAY = mat("jet_spray", "#D6E3E6", 0.1, alpha=0.45)
bm = bmesh.new(); g = cyl(bm, 0.06, 0.015, V("site.jets.h"), 0, 6)
jet = proto("je_jet", bm, [SPRAY])

def scatter(name, pts, objs, claim, rot_rand=True, scale=None, tilt=0.0, pick=None, collection="site"):
    """Instance prototypes on draped points. pts: (x, z) local; pick: prototype index per point."""
    n = len(pts)
    if n == 0: return
    me = bpy.data.meshes.new(name + "_pts"); me.from_pydata([B(x, z) for x, z in pts], [], []); me.update()
    pk = np.zeros(n, int) if pick is None else np.asarray(pick, int)
    me.attributes.new("proto", "INT", "POINT").data.foreach_set("value", pk.tolist())
    sc = np.ones(n) if scale is None else np.asarray(scale, float)
    me.attributes.new("sc3", "FLOAT_VECTOR", "POINT").data.foreach_set("vector", np.repeat(sc, 3).tolist())
    rz = rng.uniform(0, 2 * math.pi, n) if rot_rand else np.zeros(n)
    rot = np.stack([rng.uniform(-tilt, tilt, n), rng.uniform(-tilt, tilt, n), rz], 1)
    me.attributes.new("rot3", "FLOAT_VECTOR", "POINT").data.foreach_set("vector", rot.ravel().tolist())
    o = bpy.data.objects.new(name, me); coll(collection).objects.link(o); o["claim"] = claim
    pc = bpy.data.collections.new(name + "_protos"); protos.children.link(pc)
    for ob in objs: pc.objects.link(ob)
    gn = bpy.data.node_groups.new(name + "_scatter", "GeometryNodeTree")
    gn.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    gn.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N_, L_ = gn.nodes, gn.links
    gi, go = N_.new("NodeGroupInput"), N_.new("NodeGroupOutput")
    ci = N_.new("GeometryNodeCollectionInfo"); ci.inputs["Collection"].default_value = pc
    ci.inputs["Separate Children"].default_value = True; ci.inputs["Reset Children"].default_value = True
    iop = N_.new("GeometryNodeInstanceOnPoints"); iop.inputs["Pick Instance"].default_value = True
    na = {}
    for key, dt in (("proto", "INT"), ("sc3", "FLOAT_VECTOR"), ("rot3", "FLOAT_VECTOR")):
        x_ = N_.new("GeometryNodeInputNamedAttribute"); x_.data_type = dt; x_.inputs["Name"].default_value = key; na[key] = x_
    L_.new(gi.outputs[0], iop.inputs["Points"]); L_.new(ci.outputs["Instances"], iop.inputs["Instance"])
    L_.new(na["proto"].outputs["Attribute"], iop.inputs["Instance Index"]); L_.new(na["sc3"].outputs["Attribute"], iop.inputs["Scale"])
    L_.new(na["rot3"].outputs["Attribute"], iop.inputs["Rotation"]); L_.new(iop.outputs["Instances"], go.inputs[0])
    o.modifiers.new("scatter", "NODES").node_group = gn
    return o

palms = P["palms"]
scatter("palms", palms, [palm], "positions estimated (detail sheet SR38; lead correction 2: palms along the forecourt paths)", scale=rng.uniform(0.85, 1.2, len(palms)), tilt=0.06)
tr = P["trees"]
scatter("site_trees", [(x, z) for x, z, _, _ in tr], [t_round, t_acacia, t_euc, t_jac], "positions estimated (detail sheet SR39, SR40; design model)",
        scale=[s for *_, s in tr], pick=[k for _, _, k, _ in tr])
shr = P["shrubs"]
scatter("shrubs", shr, [sh_g, sh_r], "estimated (detail sheet SR08, SR09; design model)", scale=rng.uniform(0.6, 1.4, len(shr)), pick=(rng.random(len(shr)) < 0.45).astype(int))
scatter("light_masts", P["lightmasts"], [lmast], "positions estimated (ledger site.masts.*; RF41)", rot_rand=False)
scatter("track_masts", mastpts, [tmast], "estimated (design model; detail sheet SR42)", rot_rand=False)
scatter("flag_masts", P["flagmasts"], [fmast], "positions estimated (ledger site.masts.forecourt_rows; SR15, SR16)", rot_rand=False)
scatter("path_lights", P["pathlights"], [plight], "estimated (detail sheet SR17)", rot_rand=False)
scatter("bollards", P["bollards"], [bollard], "estimated (detail sheet SR18)", rot_rand=False)
scatter("jets", P["jets"], [jet], "estimated (ledger site.jets.*; SR13: jets on a paved deck)", rot_rand=False, collection="site")

# ---------------------------------------------------------------- planters (SR07)
PW = mat("planter_wall", "#66574A", 0.85); SOIL = mat("planter_soil", "#3B2E24", 0.95)
verts, faces, midx = [], [], []
for x, z, r in P["planters"]:
    h0 = hT(x, z); ph = V("site.planter.h"); n = 40; b0 = len(verts)
    for k in range(n):
        a = 2 * math.pi * k / n
        for rr, hh in ((r, 0), (r, ph), (r - 0.4, ph), (r - 0.4, ph - 0.1)):
            verts.append((x + rr * math.cos(a), -(z + rr * math.sin(a)), h0 + hh))
    for k in range(n):
        a0, a1 = b0 + 4 * k, b0 + 4 * ((k + 1) % n)
        for j in range(3): faces.append([a0 + j, a1 + j, a1 + j + 1, a0 + j + 1]); midx.append(0)
    cidx = len(verts); verts.append((x, -z, h0 + ph - 0.1))
    for k in range(n): faces.append([cidx, b0 + 4 * k + 3, b0 + 4 * ((k + 1) % n) + 3]); midx.append(1)
mesh_obj("planters", verts, faces, [PW, SOIL], "site", "estimated (ledger site.planter.*; detail sheet SR07)", mat_idx=midx)

# ---------------------------------------------------------------- boundary fence (SR34, SR35): plain palisade panels
FEN = mat("fence_palisade", "#9EA19D", 0.5, 0.6)
fn_, fl_ = FEN.node_tree.nodes, FEN.node_tree.links
uvn = fn_.new("ShaderNodeUVMap"); sp_ = fn_.new("ShaderNodeSeparateXYZ"); fl_.new(uvn.outputs["UV"], sp_.inputs[0])
d5 = fn_.new("ShaderNodeMath"); d5.operation = "DIVIDE"; d5.inputs[1].default_value = 0.15; fl_.new(sp_.outputs["X"], d5.inputs[0])
fr_ = fn_.new("ShaderNodeMath"); fr_.operation = "FRACT"; fl_.new(d5.outputs[0], fr_.inputs[0])
bar = fn_.new("ShaderNodeMath"); bar.operation = "LESS_THAN"; bar.inputs[1].default_value = 0.35; fl_.new(fr_.outputs[0], bar.inputs[0])
rail = fn_.new("ShaderNodeMath"); rail.operation = "GREATER_THAN"; rail.inputs[1].default_value = 0.94; fl_.new(sp_.outputs["Y"], rail.inputs[0])
mxm = fn_.new("ShaderNodeMath"); mxm.operation = "MAXIMUM"; fl_.new(bar.outputs[0], mxm.inputs[0]); fl_.new(rail.outputs[0], mxm.inputs[1])
fl_.new(mxm.outputs[0], fn_["Principled BSDF"].inputs["Alpha"])
verts, faces, uvs = [], [], []
FH = V("site.fence.h")
for line in P["fence"]:
    pts = np.array(line); dd = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    ss = np.arange(0, dd[-1], 3.0).tolist() + [dd[-1]]
    xs, zs = np.interp(ss, dd, pts[:, 0]), np.interp(ss, dd, pts[:, 1]); b0 = len(verts)
    for s, x, z in zip(ss, xs, zs):
        h0 = hT(x, z); verts += [(x, -z, h0), (x, -z, h0 + FH)]; uvs += [(s, 0), (s, 1)]
    for k in range(len(ss) - 1): faces.append([b0 + 2 * k, b0 + 2 * k + 2, b0 + 2 * k + 3, b0 + 2 * k + 1])
mesh_obj("boundary_fence", verts, faces, [FEN], "site", "estimated (detail sheets SR34, SR35); W1b site boundary; breaks only where OSM roads and the avenues cross", uvs=uvs)

# ---------------------------------------------------------------- generic boxes: sign frames, canopies (SR48-SR51)
def box_verts(cx, cy, cz, sx, sy, sz, yaw):
    cs, sn = math.cos(yaw), math.sin(yaw); out = []
    for dz in (-0.5, 0.5):
        for dx, dy in ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5)):
            x, y = dx * sx, dy * sy; out.append((cx + x * cs - y * sn, cy + x * sn + y * cs, cz + dz * sz))
    return out
BOXF = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
def boxes(name, items, materials, claim, collection="site"):
    verts, faces, midx = [], [], []
    for (cx, cy, cz, sx, sy, sz, yaw, mi) in items:
        b0 = len(verts); verts += box_verts(cx, cy, cz, sx, sy, sz, yaw)
        for f in BOXF: faces.append([b0 + i for i in f]); midx.append(mi)
    return mesh_obj(name, verts, faces, materials, collection, claim, mat_idx=midx)
items = []
SW_, SH_, SP_ = V("site.sign.w"), V("site.sign.h"), V("site.sign.post_h")
for x, z, deg in P["signs"]:
    yaw = math.atan2(-math.sin(math.radians(deg)), math.cos(math.radians(deg))); h0 = hT(x, z)
    items.append((x, -z, h0 + SP_ + SH_ / 2, SW_, 0.5, SH_, yaw, 0))
    items.append((x + 0.01 * math.sin(yaw), -z - 0.01 * math.cos(yaw), h0 + SP_ + SH_ / 2, SW_ - 0.6, 0.56, SH_ - 0.6, yaw, 1))
    for sg in (-1, 1): items.append((x + sg * SW_ * 0.3 * math.cos(yaw), -z + sg * SW_ * 0.3 * math.sin(yaw), h0 + SP_ / 2, 0.5, 0.5, SP_, yaw, 0))
boxes("sign_frames", items, [mat("sign_frame", "#5C625F", 0.6, 0.5), mat("sign_blank", "#D9D9D6", 0.7)], "estimated (detail sheet SR50; lead correction 3: blank faces)")
items = []
CW, CD, CH = V("site.canopy.w"), V("site.canopy.d"), V("site.canopy.h")
for x, z, deg in P["canopies"]:
    yaw = -math.radians(deg); h0 = hT(x, z)
    items.append((x, -z, h0 + CH + 0.2, CW, CD, 0.4, yaw, 0)); items.append((x, -z, h0 + CH + 0.42, CW - 0.3, CD - 0.3, 0.06, yaw, 1))
    for i in (-1, 0, 1):
        for j in (-1, 1):
            px, py = i * (CW / 2 - 1.5), j * (CD / 2 - 1.0)
            items.append((x + px * math.cos(yaw) - py * math.sin(yaw), -z + px * math.sin(yaw) + py * math.cos(yaw), h0 + CH / 2, 0.45, 0.45, CH, yaw, 0))
boxes("entrance_canopies", items, [mat("canopy_pale", "#D0CEC7", 0.6), mat("canopy_roof", "#6E6A60", 0.7)], "estimated (detail sheets SR48, SR51; generic canopies, no layout detail)")
# car-park bay lines (SR33)
verts, faces = [], []
bw, bd = V("site.parking.bay_w"), V("site.parking.bay_d")
for cx, cz, tx, tz in P["bays"]:
    t_ = np.array([tx, tz]); n_ = np.array([-tz, tx])
    for sgn in (-0.5,):
        p0 = np.array([cx, cz]) + t_ * sgn * bw - n_ * bd / 2; p1 = p0 + n_ * bd; w = t_ * 0.05; b0 = len(verts)
        for q in (p0 - w, p1 - w, p1 + w, p0 + w): verts.append(B(q[0], q[1], 0.22))
        faces.append([b0, b0 + 1, b0 + 2, b0 + 3])
mesh_obj("parking_lines", verts, faces, [mat("bay_paint", "#D8D7CE", 0.6)], "site", "estimated (detail sheet SR33); aisles OSM")

# ---------------------------------------------------------------- roof opening border (RF26) and night fixtures
N, dirs, prof = RG["N"], RG["dirs"], RG["prof"]
def ringpt(i, r, y): return (dirs[i][0] * r, -dirs[i][1] * r, y + PAD)
TH_ = V("bowl.opening.trim_h")
verts, faces = [], []
for i in range(N):
    r, y = prof[i][-1]; verts += [ringpt(i, r - 0.15, y - 0.05), ringpt(i, r + 0.4, y - TH_)]
for i in range(N):
    a0, a1 = 2 * i, 2 * ((i + 1) % N); faces.append([a0, a1, a1 + 1, a0 + 1])
mesh_obj("opening_trim", verts, faces, [mat("opening_trim_dark", "#333438", 0.7)], "facade_detail", "estimated (detail sheet RF26)")
def ring_points(r_of, y_of, spacing):
    """Points at an even spacing (m) along the closed ring through the N profile directions."""
    pts = np.array([ringpt(i, r_of(i), y_of(i)) for i in range(N)] + [ringpt(0, r_of(0), y_of(0))])
    d_ = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
    ss = np.arange(0, d_[-1], spacing)
    return [Vector((np.interp(s_, d_, pts[:, 0]), np.interp(s_, d_, pts[:, 1]), np.interp(s_, d_, pts[:, 2]))) for s_ in ss]
def light_cubes(name, pts, mats_cycle, size, claim):
    verts, faces, midx = [], [], []
    for k, p in enumerate(pts):
        b0 = len(verts); verts += box_verts(p.x, p.y, p.z, size, size, size, 0)
        for f in BOXF: faces.append([b0 + i for i in f]); midx.append(k % len(mats_cycle))
    return mesh_obj(name, verts, faces, mats_cycle, "night_lights", claim, mat_idx=midx)
jw = RG.get("j_fascia", RG["j_wall"])  # fascia line (fins now run up the shoulder to it)
light_cubes("night_fascia_points", ring_points(lambda i: prof[i][jw][0] + 0.45, lambda i: prof[i][jw][1] + 0.4, V("bowl.night.fascia_spacing")),
            [mat("night_fascia_white", "#D8D8D4", 0.4, night=40.0, emit_hex="#FFFFFF"), mat("night_fascia_cyan", "#D8D8D4", 0.4, night=40.0, emit_hex="#32C6FF"),
             mat("night_fascia_violet", "#D8D8D4", 0.4, night=40.0, emit_hex="#B35CFF")],  # grey housings by day, colour only when lit,
            0.35, "Visualization (detail sheet RF25, frame 11:48)")
light_cubes("night_opening_row", ring_points(lambda i: prof[i][-1][0] + 0.6, lambda i: prof[i][-1][1] - 0.6, V("bowl.night.ring_spacing")),
            [mat("night_ring_white", "#FFF0CF", 0.4, night=60.0)], 0.3, "Visualization (detail sheet RF31, frame 11:48)")
# RF38 coloured wash lights at the base, RF39 shield lights: spot lamps, energy set at night only
rPl = RG["rPl"]; wash_cols = ["#00C878", "#FFFFFF", "#E12832"]
def spot(name, loc, aim, rgb, size_deg, night_energy):
    ld = bpy.data.lights.new(name, "SPOT"); ld.energy = 0.0; ld.color = srgb(rgb); ld.spot_size = math.radians(size_deg); ld.spot_blend = 0.6
    ld.shadow_soft_size = 0.3; o = bpy.data.objects.new(name, ld); coll("night_lights").objects.link(o)
    o.location = loc; d_ = (Vector(aim) - Vector(loc)).normalized(); o.rotation_euler = d_.to_track_quat("-Z", "Y").to_euler()
    o["night_energy"] = night_energy; o["claim"] = "Visualization (night effect)"
k_ = 0
for p in ring_points(lambda i: rPl[i] + 2.5, lambda i: 0.3, V("bowl.night.wash_spacing")):
    r_ = math.hypot(p.x, p.y); inward = Vector((-p.x / r_, -p.y / r_, 0))
    spot(f"night_wash_{k_:03d}", p, p + inward * 6 + Vector((0, 0, 30)), wash_cols[k_ % 3], 50, 8000.0); k_ += 1
axisA = math.radians(-RG["bearing"]); ymid = (V("bowl.shield.blockout_y0") + V("bowl.shield.blockout_y1")) / 2
for k in range(int(V("bowl.shields.count"))):
    th = axisA - math.pi / 2 + k * 2 * math.pi / int(V("bowl.shields.count")); i = int(round(th / (2 * math.pi) * N)) % N
    pr = prof[i]; r_ = np.interp(ymid, [q[1] for q in pr[2:jw + 1]], [q[0] for q in pr[2:jw + 1]])
    c_ = Vector(ringpt(i, r_, ymid)); out_ = Vector((dirs[i][0], -dirs[i][1], 0))
    spot(f"night_shield_{k}", c_ + out_ * 45 + Vector((0, 0, -ymid + PAD + 1.0)), c_, "#FFFFFF", 28, 40000.0)
# RF40: the membrane glows softly from below at night (the bowl lights through the PTFE)
mm = bpy.data.materials.get("membrane_pbr")
if mm:
    n_, l_ = mm.node_tree.nodes, mm.node_tree.links
    em = n_.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*srgb("#DDE8D9"), 1); em.inputs["Strength"].default_value = 0.0; em.label = "night:0.8"
    out = n_["Material Output"]; prev = out.inputs["Surface"].links[0].from_socket
    add = n_.new("ShaderNodeAddShader"); l_.new(prev, add.inputs[0]); l_.new(em.outputs[0], add.inputs[1]); l_.new(add.outputs[0], out.inputs["Surface"])

# Pass 2 and 3 context modules (blender/context/, lead order 2026-10-18), then the CC0 surfaces last
import sys, time as _time
sys.path.insert(0, str(ROOT / "blender"))
from context import forecourt, horizon, suburbs, canopy
from context import traffic as traffic_context
import materials_pbr
context_reports = {}
for _name, _build in (("forecourt", forecourt.build), ("horizon", horizon.build), ("suburbs", suburbs.build),
                      ("traffic", traffic_context.build), ("canopy", canopy.build)):
    _t = _time.time(); context_reports[_name] = _build(scene, ROOT); print(f"context {_name}: {_time.time() - _t:.1f} s", flush=True)


def place_canopy_slots():
    """canopy.py swaps scatter instances only. Put its palm variants on the forecourt palm_slot_* empties and its
    broadleaf variants on the horizon tree_slot_* crown proxies (proxies hidden). Linked meshes, seeded choice."""
    import random
    lib = bpy.data.collections["canopy_variants"]; rng = random.Random(704)
    coll_ = bpy.data.collections.new("canopy_slots"); scene.collection.children.link(coll_)
    coll_["claim"] = canopy.CLAIM + "; slot positions from forecourt_layout.json and horizon.py"
    def variant(name):
        o = bpy.data.objects["canopy_" + name + "_high"]; zs = [v.co.z for v in o.data.vertices]
        return o, max(zs) - min(zs), min(zs)
    palms = [variant("palm_00"), variant("palm_01")]
    broad = [variant("broadleaf_%02d" % i) for i in range(7)]
    n_p = n_t = 0
    for ob in sorted((o for o in scene.objects if o.name.startswith("palm_slot_")), key=lambda o: o.name):
        src, h0, z0 = rng.choice(palms); k = ob["height_m"] / h0
        o = bpy.data.objects.new("canopy_" + ob.name, src.data); coll_.objects.link(o)
        o.location = ob.matrix_world.translation - Vector((0, 0, z0 * k)); o.scale = (k, k, k)
        o.rotation_euler = (0, 0, rng.uniform(0, 2 * math.pi)); o["claim"] = ob["claim"]; o["web_lod"] = src["web_lod"]; n_p += 1
    for ob in sorted((o for o in scene.objects if o.name.startswith("tree_slot_")), key=lambda o: o.name):
        w = [ob.matrix_world @ v.co for v in ob.data.vertices]; base, top = w[0], w[1]
        rad = max((v - top).xy.length for v in w[2:])
        src, h0, z0 = rng.choice(broad); k = (top.z - base.z + 0.8) / h0
        xs = [v.co.x for v in src.data.vertices]; kxy = max(k, rad / max(1e-3, (max(xs) - min(xs)) / 2))
        o = bpy.data.objects.new("canopy_" + ob.name, src.data); coll_.objects.link(o)
        o.location = (base.x, base.y, base.z - 0.8 - z0 * k); o.scale = (kxy, kxy, k)
        o.rotation_euler = (0, 0, rng.uniform(0, 2 * math.pi)); o["claim"] = ob.get("claim", canopy.CLAIM); o["web_lod"] = src["web_lod"]
        ob.hide_render = True; ob.hide_viewport = True; n_t += 1
    return {"palm_slots": n_p, "tree_slots": n_t}


context_reports["canopy_slots"] = place_canopy_slots()
from context import far_land  # pass 2 lead review: far-land structure, murram car park, facade windows
context_reports["far_land"] = far_land.build(scene, ROOT)
_t = _time.time(); _pbr = materials_pbr.apply(scene, ROOT); print(f"materials_pbr: {_time.time() - _t:.1f} s", flush=True)
context_reports["site_ground_detail"] = far_land.detail_site_ground(ROOT)
context_reports["materials_pbr"] = {"textured": sum(r["action"] == "textured" for r in _pbr["materials"])}
(ROOT / "blender/data/context_build_report.json").write_text(json.dumps(context_reports, indent=1, sort_keys=True, default=str) + "\n")

bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / "blender/out/talanta_site.blend"))
print(json.dumps({"ngong_pts": len(mid), "palms": len(palms), "trees": len(tr), "shrubs": len(shr), "light_masts": len(P["lightmasts"]), "track_masts": len(mastpts),
                  "path_lights": len(P["pathlights"]), "wash_spots": k_, "pitch_line_quads": len(lines_f)}))
