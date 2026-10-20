"""Stage 02: look-pass scene. Blockout + context + PBR materials + sun/sky + haze.

Opens blender/out/talanta_detail.blend (blockout + bowl detail, build_bowl_detail.py) and adds:
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

bpy.ops.wm.open_mainfile(filepath=str(ROOT / "blender/out/talanta_detail.blend"))  # blockout + bowl detail
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
    "concrete_light": principled("concrete_light_pbr", (0.66, 0.65, 0.62), 0.85, 0.0, noise_rough=0.05, noise_scale=0.6, bump=0.03),
    "concrete_shade": principled("concrete_shade_pbr", (0.36, 0.35, 0.33), 0.9),
    "concrete": principled("concrete_pbr", (0.55, 0.53, 0.50), 0.85, 0.0, noise_rough=0.05, noise_scale=0.6, bump=0.05),
    "plinth_glass": principled("glass_pbr", (0.04, 0.05, 0.06), 0.06, 0.0, spec=0.6),
    "grass": principled("grass_pbr", (0.10, 0.22, 0.06), 0.85, 0.0, noise_rough=0.05, noise_scale=0.3, bump=0.1),
    "paving": principled("paving_pbr", (0.55, 0.52, 0.47), 0.8, 0.0, noise_rough=0.08, noise_scale=0.4, bump=0.05),
    "earth": principled("earth_pbr", (0.32, 0.19, 0.11), 0.95),
    "track": principled("track_pbr", (0.42, 0.15, 0.09), 0.8),
    "seat_green": principled("seat_green_pbr", (0.04, 0.22, 0.10), 0.4, spec=0.6),
    "seat_red": principled("seat_red_pbr", (0.38, 0.03, 0.04), 0.4, spec=0.6),
    "spear_white": principled("spear_pbr", (0.82, 0.82, 0.80), 0.3, 0.0, coat=0.2),
    # facade spec 2026-10-20: the lattice has its own copy of the shell white (bevel cap in hero_artistic.py); the
    # set-back ground floor under the ring beam reads dark
    "white_shell_lattice": principled("white_shell_lattice_pbr", (0.80, 0.80, 0.78), 0.32, 0.0, coat=0.2, noise_rough=0.06, noise_scale=0.08),
    "concrete_recess_dark": principled("concrete_recess_dark_pbr", (0.12, 0.12, 0.115), 0.9),
}
# Membrane (stage 02b fix 6, by eye from 12:40): faint radial seams at the rib spacing and slight
# panel-to-panel brightness variation, from the angle round the bowl centre (object coordinates).
mm = PBR["membrane"]; mn, ml = mm.node_tree.nodes, mm.node_tree.links
mco = mn.new("ShaderNodeTexCoord"); msx = mn.new("ShaderNodeSeparateXYZ"); ml.new(mco.outputs["Object"], msx.inputs[0])
ang = mn.new("ShaderNodeMath"); ang.operation = "ARCTAN2"; ml.new(msx.outputs["Y"], ang.inputs[0]); ml.new(msx.outputs["X"], ang.inputs[1])
_LR = {r["name"]: r["value"] for r in __import__("csv").DictReader(open(ROOT / "gis/parameter_ledger.csv"))}
NRIB = float(_LR.get("bowl.roof.cushion_bays", _LR["bowl.roof.ribs"]))  # seams at the topside ribs (cushion bays)
pa = mn.new("ShaderNodeMath"); pa.operation = "MULTIPLY"; pa.inputs[1].default_value = NRIB / (2 * math.pi); ml.new(ang.outputs[0], pa.inputs[0])
fr = mn.new("ShaderNodeMath"); fr.operation = "FRACT"; ml.new(pa.outputs[0], fr.inputs[0])
sd = mn.new("ShaderNodeMath"); sd.operation = "SUBTRACT"; sd.inputs[1].default_value = 0.5; ml.new(fr.outputs[0], sd.inputs[0])
sa = mn.new("ShaderNodeMath"); sa.operation = "ABSOLUTE"; ml.new(sd.outputs[0], sa.inputs[0])
seam = mn.new("ShaderNodeMapRange"); seam.inputs["From Min"].default_value = 0.44; seam.inputs["From Max"].default_value = 0.5
seam.inputs["To Min"].default_value = 1.0; seam.inputs["To Max"].default_value = 0.93; ml.new(sa.outputs[0], seam.inputs["Value"])
fl = mn.new("ShaderNodeMath"); fl.operation = "FLOOR"; ml.new(pa.outputs[0], fl.inputs[0])
wn = mn.new("ShaderNodeTexWhiteNoise"); wn.noise_dimensions = "1D"; ml.new(fl.outputs[0], wn.inputs["W"])
pv = mn.new("ShaderNodeMapRange"); pv.inputs["To Min"].default_value = 0.96; pv.inputs["To Max"].default_value = 1.02; ml.new(wn.outputs["Value"], pv.inputs["Value"])
mul = mn.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; ml.new(seam.outputs[0], mul.inputs[0]); ml.new(pv.outputs[0], mul.inputs[1])
mcol = mn.new("ShaderNodeMix"); mcol.data_type = "RGBA"; mcol.blend_type = "MULTIPLY"; mcol.inputs[0].default_value = 1.0
mcol.inputs[6].default_value = (0.86, 0.86, 0.83, 1); ml.new(mul.outputs[0], mcol.inputs[7]); ml.new(mcol.outputs[2], mn["Principled BSDF"].inputs["Base Color"])
# PTFE membrane lets daylight through: the underside glows (stage 03, by eye from JWNowpO44rw 10:04)
mtr = mn.new("ShaderNodeBsdfTranslucent"); ml.new(mcol.outputs[2], mtr.inputs["Color"])
mms = mn.new("ShaderNodeMixShader"); mms.inputs[0].default_value = 0.35
ml.new(mn["Principled BSDF"].outputs[0], mms.inputs[1]); ml.new(mtr.outputs[0], mms.inputs[2]); ml.new(mms.outputs[0], mn["Material Output"].inputs["Surface"])
# The louvred wall is real fin geometry over a dark backing (build_blockout.py, stage 02b), so no louvre texture.
PBR["facade_void"] = principled("facade_void_pbr", (0.035, 0.036, 0.04), 0.75)
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
ts = terrain(T[0], G[0], None, "terrain_site")
# Ground regions. Stage 03 (detail sheets SR, lead review correction 1): the finished landscape, not the
# construction site. Inside the W1b site boundary the 10 m Sentinel-2 colour (which also paints the white roof onto
# the ground) is replaced by mown lawn, pale stone paving with shallow joints and a darker edge band, red flower
# beds, a wet jet deck and car-park asphalt. Masks at 0.5 m/px from gis/scripts/export_site_plan.py (W1b outlines,
# OSM and the estimated layout only; no imagery). Tracks, pitches, Ngong Road and furniture are objects
# (blender/build_site_detail.py).
def srgb(h):
    return tuple(((int(h[i:i + 2], 16) / 255 + 0.055) / 1.055) ** 2.4 for i in (1, 3, 5))


tm = ts.data.materials[0]; tn, tl = tm.node_tree.nodes, tm.node_tree.links
img = [x for x in tn if x.type == "TEX_IMAGE"][0]; pbsdf = tn["Principled BSDF"]
tco = tn.new("ShaderNodeTexCoord"); mp = tn.new("ShaderNodeMapping")
mp.inputs["Location"].default_value = (0.5, 0.5, 0); mp.inputs["Scale"].default_value = (1 / 1400, 1 / 1400, 1)
tl.new(tco.outputs["Object"], mp.inputs["Vector"])
def mask_img(fn):
    mk = tn.new("ShaderNodeTexImage"); mk.image = bpy.data.images.load(str(ROOT / "blender/textures" / fn))
    mk.image.colorspace_settings.name = "Non-Color"; mk.extension = "CLIP"; tl.new(mp.outputs["Vector"], mk.inputs["Vector"])
    sep = tn.new("ShaderNodeSeparateColor"); tl.new(mk.outputs["Color"], sep.inputs["Color"]); return sep
M1, M2, M3 = mask_img("site_regions.png"), mask_img("site_regions2.png"), mask_img("site_regions3.png")
def noise(scale, detail=4):
    nz = tn.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = detail
    tl.new(tco.outputs["Object"], nz.inputs["Vector"]); return nz
def mixc(fac, a_, b_):
    m_ = tn.new("ShaderNodeMix"); m_.data_type = "RGBA"
    for sock, val in ((6, a_), (7, b_)):
        if isinstance(val, tuple): m_.inputs[sock].default_value = (*val, 1)
        else: tl.new(val, m_.inputs[sock])
    if isinstance(fac, float): m_.inputs[0].default_value = fac
    else: tl.new(fac, m_.inputs[0])
    return m_.outputs[2]
LG = {r["name"]: r["value"] for r in __import__("csv").DictReader(open(ROOT / "gis/parameter_ledger.csv"))}
lawn = mixc(noise(0.05).outputs["Fac"], srgb("#3F6331"), srgb("#52713E"))  # SR10 turf, mown (design model)
lawn = mixc(noise(0.6, 6).outputs["Fac"], lawn, srgb("#5E7A45"))
# SR02 paving: muted stone panels (joint spacing from the ledger) with slight panel-to-panel tone, shallow joints
brk = tn.new("ShaderNodeTexBrick"); J = float(LG["site.paving.joint"])
brk.inputs["Scale"].default_value = 1 / J; brk.inputs["Mortar Size"].default_value = 0.03; brk.offset = 0.5; brk.squash = 1.0
brk.inputs["Brick Width"].default_value = 1.0; brk.inputs["Row Height"].default_value = 1.0
tl.new(tco.outputs["Object"], brk.inputs["Vector"])
brk.inputs["Color1"].default_value = (*srgb(LG["site.paving.rgb"]), 1); brk.inputs["Color2"].default_value = (*srgb("#ABA597"), 1); brk.inputs["Bias"].default_value = 0.0
brk.inputs["Mortar"].default_value = (*srgb("#7F796F"), 1)
pave = mixc(0.25, brk.outputs["Color"], srgb("#C2BCB0"))  # slight lift towards render 06, joints kept
pave = mixc(noise(0.015, 3).outputs["Fac"], pave, srgb("#ADA699"))  # broad tone drift across the forecourt
pave = mixc(M3.outputs["Red"], pave, srgb("#9C9488"))  # SR06 entrance apron next to the facade, low contrast
pave = mixc(M2.outputs["Red"], pave, srgb("#81796D"))  # SR03 darker edge band
pave = mixc(M2.outputs["Green"], pave, srgb("#8E8A82"))  # SR13 wet jet deck
fl = tn.new("ShaderNodeMapRange"); fl.inputs["From Min"].default_value = 0.45; fl.inputs["From Max"].default_value = 0.6
tl.new(noise(1.2, 3).outputs["Fac"], fl.inputs["Value"])
bed = mixc(fl.outputs["Result"], srgb("#49643A"), srgb(LG["site.bed.flower_rgb"]))  # SR08 beds: red flowers in green
asph = mixc(noise(0.5).outputs["Fac"], srgb("#3A3C3A"), srgb("#4A4C49"))  # SR32 car-park asphalt
col = mixc(M1.outputs["Red"], img.outputs["Color"], lawn)
col = mixc(M1.outputs["Blue"], col, bed)
col = mixc(M1.outputs["Green"], col, pave)
col = mixc(M2.outputs["Blue"], col, asph)
tl.new(col, pbsdf.inputs["Base Color"])
rg = tn.new("ShaderNodeMapRange"); rg.inputs["To Min"].default_value = 0.82; rg.inputs["To Max"].default_value = 1.0
tl.new(noise(0.3).outputs["Fac"], rg.inputs["Value"])
wet = tn.new("ShaderNodeMapRange"); wet.inputs["To Min"].default_value = 1.0; wet.inputs["To Max"].default_value = 0.12
tl.new(M2.outputs["Green"], wet.inputs["Value"])
rmul = tn.new("ShaderNodeMath"); rmul.operation = "MULTIPLY"; tl.new(rg.outputs["Result"], rmul.inputs[0]); tl.new(wet.outputs["Result"], rmul.inputs[1])
tl.new(rmul.outputs[0], pbsdf.inputs["Roughness"])
bmp = tn.new("ShaderNodeBump"); bmp.inputs["Strength"].default_value = 0.15; tl.new(noise(1.5, 6).outputs["Fac"], bmp.inputs["Height"])
jb = tn.new("ShaderNodeMath"); jb.operation = "MULTIPLY"; tl.new(brk.outputs["Fac"], jb.inputs[0]); tl.new(M1.outputs["Green"], jb.inputs[1])
bmp2 = tn.new("ShaderNodeBump"); bmp2.inputs["Strength"].default_value = 0.3; bmp2.invert = True
tl.new(jb.outputs[0], bmp2.inputs["Height"]); tl.new(bmp.outputs["Normal"], bmp2.inputs["Normal"])
tl.new(bmp2.outputs["Normal"], pbsdf.inputs["Normal"])
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
# Roofs (Stage 03 checklist, suburbs; by eye from JWNowpO44rw 07:04): up-facing faces take red and brown tile or
# iron-sheet colours, picked per 9 m cell so neighbouring houses differ; a share keeps a grey concrete roof.
LGs = {r["name"]: r["value"] for r in __import__("csv").DictReader(open(ROOT / "gis/parameter_ledger.csv"))}
bm_ = bpy.data.materials["buildings_mat"]; bn, bl = bm_.node_tree.nodes, bm_.node_tree.links
geo = bn.new("ShaderNodeNewGeometry"); sxyz = bn.new("ShaderNodeSeparateXYZ"); bl.new(geo.outputs["Normal"], sxyz.inputs[0])
up = bn.new("ShaderNodeMath"); up.operation = "GREATER_THAN"; up.inputs[1].default_value = 0.6; bl.new(sxyz.outputs["Z"], up.inputs[0])
sc = bn.new("ShaderNodeVectorMath"); sc.operation = "SCALE"; sc.inputs["Scale"].default_value = 1 / 9; bl.new(geo.outputs["Position"], sc.inputs[0])
fl9 = bn.new("ShaderNodeVectorMath"); fl9.operation = "FLOOR"; bl.new(sc.outputs[0], fl9.inputs[0])
wn9 = bn.new("ShaderNodeTexWhiteNoise"); wn9.noise_dimensions = "3D"; bl.new(fl9.outputs[0], wn9.inputs["Vector"])
ramp = bn.new("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "CONSTANT"
pal = LGs["site.roof_palette"].split(",") + ["#9A9A96"]
els = ramp.color_ramp.elements
while len(els) < len(pal): els.new(0.5)
for i_, h_ in enumerate(pal):
    els[i_].position = i_ / len(pal); els[i_].color = (*srgb(h_), 1)
bl.new(wn9.outputs["Value"], ramp.inputs["Fac"])
rmx = bn.new("ShaderNodeMix"); rmx.data_type = "RGBA"; bl.new(up.outputs[0], rmx.inputs[0])
bl.new(bn["Attribute"].outputs["Color"], rmx.inputs[6]); bl.new(ramp.outputs["Color"], rmx.inputs[7])
bl.new(rmx.outputs[2], bn["Principled BSDF"].inputs["Base Color"])
rpos, ridx, rw = f32(MAN["roads"]["pos"]), u32(MAN["roads"]["idx"]), f32(MAN["roads"]["w"])
import numpy as np
SITE = np.array([(float(r["x_east"]), float(r["z_south"])) for r in __import__("csv").DictReader(open(ROOT / "gis/measurements/normalized/site_boundary_w1b_2026-10-16.csv"))])
def in_site(x, z):
    """Even-odd point-in-polygon test against the W1b site boundary (arrays of local x, z)."""
    x, z = np.asarray(x, float), np.asarray(z, float); ins = np.zeros(x.shape, bool)
    xa, za, xb, zb = SITE[:, 0], SITE[:, 1], np.roll(SITE[:, 0], -1), np.roll(SITE[:, 1], -1)
    for x0, z0, x1, z1 in zip(xa, za, xb, zb):
        c = ((z0 > z) != (z1 > z)) & (x < (x1 - x0) * (z - z0) / ((z1 - z0) or 1e-9) + x0); ins ^= c
    return ins
rc = []  # asphalt for carriageways, dusty murram for footways and tracks outside the site (look estimate)
# Inside the site every road is finished asphalt (lead review correction 1; the frames show construction state).
P_ = np.array(rpos).reshape(-1, 3); site_v = in_site(P_[:, 0], P_[:, 2])
for w, ins in zip(rw, site_v): rc += [0.075, 0.075, 0.078] if (w >= 4 or ins) else [0.33, 0.2, 0.13]
ro = bpy.data.objects.new("roads", mesh_from("roads", rpos, ridx, rc, normalize=1.0)); coll("context").objects.link(ro)
ro.location.z = 0.15
ro.data.materials.append(attr_mat("roads_mat", "col", 0.9)); ro["claim"] = "OpenStreetMap via Overture"
rm = bpy.data.materials["roads_mat"]; rn, rl = rm.node_tree.nodes, rm.node_tree.links
rnz = rn.new("ShaderNodeTexNoise"); rnz.inputs["Scale"].default_value = 0.4; rco = rn.new("ShaderNodeTexCoord"); rl.new(rco.outputs["Object"], rnz.inputs["Vector"])
rmr = rn.new("ShaderNodeMapRange"); rmr.inputs["To Min"].default_value = 0.8; rmr.inputs["To Max"].default_value = 1.25; rl.new(rnz.outputs["Fac"], rmr.inputs["Value"])
rmu = rn.new("ShaderNodeMix"); rmu.data_type = "RGBA"; rmu.blend_type = "MULTIPLY"; rmu.inputs[0].default_value = 1.0
rl.new(rn["Attribute"].outputs["Color"], rmu.inputs[6]); rl.new(rmr.outputs["Result"], rmu.inputs[7]); rl.new(rmu.outputs[2], rn["Principled BSDF"].inputs["Base Color"])
# Lane markings: white centre dashes (3 m on, 6 m off, 0.18 m wide) on trunk to tertiary roads within 1.5 km
# (OSM centrelines from gis/scripts/export_ground_regions.py), dropped onto the road surface.
from mathutils.bvhtree import BVHTree
from mathutils import Vector as Vec
dg = bpy.context.evaluated_depsgraph_get(); bvh = BVHTree.FromObject(ro, dg)
mv, mf = [], []
for ln in json.loads((ROOT / "blender/data/road_lines.json").read_text()):
    if ln.get("name") == "Ngong Road": continue  # Ngong Road is rebuilt as a dual carriageway in build_site_detail.py
    P = [Vec((x, -z, 0)) for x, z in ln["pts"]]
    for a_, b_ in zip(P, P[1:]):
        d_ = b_ - a_; L_ = d_.length
        if L_ < 1: continue
        t_, n_ = d_.normalized(), Vec((-d_.y, d_.x, 0)).normalized() * 0.09
        k_ = 0.0
        while k_ + 3 <= L_:
            q0, q1 = a_ + t_ * k_, a_ + t_ * (k_ + 3)
            h = [bvh.ray_cast(Vec((q.x, q.y, 3000)), Vec((0, 0, -1))) for q in (q0, q1)]
            if all(x[0] for x in h):
                z0, z1 = h[0][0].z + ro.location.z + 0.04, h[1][0].z + ro.location.z + 0.04; b0 = len(mv)
                mv += [(q0.x - n_.x, q0.y - n_.y, z0), (q0.x + n_.x, q0.y + n_.y, z0), (q1.x + n_.x, q1.y + n_.y, z1), (q1.x - n_.x, q1.y - n_.y, z1)]
                mf.append((b0, b0 + 1, b0 + 2, b0 + 3))
            k_ += 9
mme = bpy.data.meshes.new("road_markings"); mme.from_pydata(mv, [], mf); mme.update()
mo = bpy.data.objects.new("road_markings", mme); coll("context").objects.link(mo)
mo.data.materials.append(principled("marking_paint", (0.75, 0.75, 0.72), 0.6)); mo["claim"] = "look estimate on OSM centrelines"
print("lane dashes:", len(mf))

# ---------------------------------------------------------------- trees (instances on points)
# Stage 02b fix 7 (by eye from JWNowpO44rw 12:40; look only): the NDVI points sit on a near-regular grid and
# read as an even carpet. Keep the densest 40 m cells (wooded belts and forest, kept almost whole); elsewhere cut
# clearings with a low-frequency noise so trees stand in clumps. Positions are jittered off the grid, and each tree
# gets its own type (eucalyptus-heavy in belts), size and crown proportions. Seeded.
rng = np.random.default_rng(17)
tr = np.frombuffer((DATA / MAN["trees"]["file"]).read_bytes(), np.float32).reshape(-1, 4)
tr = tr[np.hypot(tr[:, 0], tr[:, 2]) < 4000]
tr = tr[~in_site(tr[:, 0], tr[:, 2])]  # the finished site is planted to the design layout (build_site_detail.py)
cell = np.floor(tr[:, [0, 2]] / 40).astype(int)
_, inv, cnt = np.unique(cell, axis=0, return_inverse=True, return_counts=True)
belt = cnt[inv.ravel()] >= 32
X, Z = tr[:, 0], tr[:, 2]
n = np.zeros(len(tr))
for wl in (130, 190, 260):
    a, ph = rng.uniform(0, np.pi, 2), rng.uniform(0, 2 * np.pi, 2)
    n += np.sin((X * np.cos(a[0]) + Z * np.sin(a[0])) * 2 * np.pi / wl + ph[0]) * np.sin((X * np.cos(a[1]) + Z * np.sin(a[1])) * 2 * np.pi / wl + ph[1])
n /= 1.5
keep_p = np.where(belt, 0.95, np.clip((n + 0.15) / 0.5, 0, 1) * 0.9)
keep = rng.random(len(tr)) < keep_p
tr, belt = tr[keep], belt[keep]; k = len(tr)
jit = rng.uniform(-4, 4, (k, 2))
proto = np.where(belt, rng.choice([0, 2], k, p=[0.3, 0.7]), rng.choice([0, 1, 2], k, p=[0.5, 0.35, 0.15]))
size = tr[:, 3] * rng.uniform(0.75, 1.3, k)
sx, sy, sz = size * rng.uniform(0.8, 1.25, k), size * rng.uniform(0.8, 1.25, k), size * rng.uniform(0.8, 1.3, k)
pts = [(float(x + j[0]), float(-(z + j[1])), float(y - 0.5)) for (x, y, z, _), j in zip(tr, jit)]
tme = bpy.data.meshes.new("tree_points"); tme.from_pydata(pts, [], [])
tme.attributes.new("proto", "INT", "POINT").data.foreach_set("value", proto.astype(int).tolist())
tme.attributes.new("tscale3", "FLOAT_VECTOR", "POINT").data.foreach_set("vector", np.stack([sx, sy, sz], 1).ravel().tolist())
tobj = bpy.data.objects.new("trees", tme); coll("context").objects.link(tobj); tobj["claim"] = "positions Sentinel-2 NDVI (thinned into clumps, jittered); shapes estimated"
# Three tree prototypes in metres (shapes estimated; P3 "tree variety"): flat-top acacia, tall eucalyptus,
# and the round two-crown tree from makeTrees() in context.js. Names sort in index order (proto attribute 0-2).
from mathutils import Matrix
protos = coll("tree_protos"); protos.hide_render = True
def make_proto(name, trunk_h, trunk_r, crowns, leaf_rgb):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=trunk_r, radius2=trunk_r * 0.65, depth=trunk_h, matrix=Matrix.Translation((0, 0, trunk_h / 2)))
    for (cx, cy, cz, rx, rz) in crowns:
        g = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1)
        for v in g["verts"]: v.co.x = v.co.x * rx + cx; v.co.y = v.co.y * rx + cy; v.co.z = v.co.z * rz + cz
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    me.materials.append(principled(name + "_leaf", leaf_rgb, 0.8, noise_rough=0.1, noise_scale=3, bump=0.3))
    o = bpy.data.objects.new(name, me); protos.objects.link(o); return o
make_proto("tree_0_round", 4.6, 0.34, [(0, 0, 6.2, 3.0, 2.6), (1.7, -0.9, 4.9, 1.9, 1.7)], (0.06, 0.13, 0.04))
make_proto("tree_1_acacia", 5.5, 0.3, [(0, 0, 6.6, 4.6, 1.1), (1.8, 1.2, 6.2, 2.6, 0.8)], (0.08, 0.14, 0.05))
make_proto("tree_2_eucalyptus", 9.0, 0.32, [(0, 0, 11.5, 2.2, 4.2), (0.6, 0.4, 8.2, 1.6, 2.2)], (0.09, 0.13, 0.08))
gn = bpy.data.node_groups.new("tree_scatter", "GeometryNodeTree")
try:
    gn.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    gn.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
except Exception:
    pass
N_ = gn.nodes; L_ = gn.links
gi, go = N_.new("NodeGroupInput"), N_.new("NodeGroupOutput")
ci = N_.new("GeometryNodeCollectionInfo"); ci.inputs["Collection"].default_value = protos
ci.inputs["Separate Children"].default_value = True; ci.inputs["Reset Children"].default_value = True
pick = N_.new("GeometryNodeInputNamedAttribute"); pick.data_type = "INT"; pick.inputs["Name"].default_value = "proto"
na = N_.new("GeometryNodeInputNamedAttribute"); na.data_type = "FLOAT_VECTOR"; na.inputs["Name"].default_value = "tscale3"
rnd = N_.new("FunctionNodeRandomValue"); rnd.data_type = "FLOAT"; rnd.inputs["Max"].default_value = 6.283
cr = N_.new("ShaderNodeCombineXYZ"); L_.new(rnd.outputs["Value"], cr.inputs["Z"])
iop = N_.new("GeometryNodeInstanceOnPoints")
L_.new(gi.outputs[0], iop.inputs["Points"]); L_.new(ci.outputs["Instances"], iop.inputs["Instance"])
iop.inputs["Pick Instance"].default_value = True; L_.new(pick.outputs["Attribute"], iop.inputs["Instance Index"])
L_.new(na.outputs["Attribute"], iop.inputs["Scale"]); L_.new(cr.outputs["Vector"], iop.inputs["Rotation"])
L_.new(iop.outputs["Instances"], go.inputs[0])
mod = tobj.modifiers.new("scatter", "NODES"); mod.node_group = gn
print("trees within 4 km:", len(pts), "of which in belts:", int(belt.sum()), "size range", round(float(size.min()), 2), round(float(size.max()), 2))

# ---------------------------------------------------------------- world: sky + haze (set per render in render_cycles.py)
w = bpy.data.worlds.new("sky"); scene.world = w
try: w.use_nodes = True
except Exception: pass
n, l = w.node_tree.nodes, w.node_tree.links
sky = n.new("ShaderNodeTexSky"); sky.name = "sky"
sky.sky_type = "MULTIPLE_SCATTERING"; sky.sun_disc = False; sky.altitude = 1800; sky.aerosol_density = 2.0
l.new(sky.outputs["Color"], n["Background"].inputs["Color"])
n["Background"].inputs["Strength"].default_value = 0.35
# Stage 02b fix 8: cheap cloud background (the lead's fallback; Poly Haven is not reachable from the cloud session).
# Camera rays only: a procedural cumulus layer on a plane 2 km up, faded into the haze at the horizon. Lighting
# still comes from the physical sky and the sun lamp. Look only, no volumes.
cco = n.new("ShaderNodeTexCoord"); csx = n.new("ShaderNodeSeparateXYZ"); l.new(cco.outputs["Generated"], csx.inputs[0])
cz = n.new("ShaderNodeMath"); cz.operation = "MAXIMUM"; cz.inputs[1].default_value = 0.02; l.new(csx.outputs["Z"], cz.inputs[0])
cux, cuy = n.new("ShaderNodeMath"), n.new("ShaderNodeMath"); cux.operation = cuy.operation = "DIVIDE"
l.new(csx.outputs["X"], cux.inputs[0]); l.new(cz.outputs[0], cux.inputs[1]); l.new(csx.outputs["Y"], cuy.inputs[0]); l.new(cz.outputs[0], cuy.inputs[1])
cuv = n.new("ShaderNodeCombineXYZ"); l.new(cux.outputs[0], cuv.inputs["X"]); l.new(cuy.outputs[0], cuv.inputs["Y"])
def wnoise(scale, detail, rough):
    nz = n.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale; nz.inputs["Detail"].default_value = detail
    nz.inputs["Roughness"].default_value = rough; l.new(cuv.outputs[0], nz.inputs["Vector"]); return nz
cov = n.new("ShaderNodeMapRange"); cov.inputs["From Min"].default_value = 0.5; cov.inputs["From Max"].default_value = 0.64
l.new(wnoise(1.6, 8, 0.62).outputs["Fac"], cov.inputs["Value"])
fade = n.new("ShaderNodeMapRange"); fade.inputs["From Min"].default_value = 0.004; fade.inputs["From Max"].default_value = 0.05; fade.inputs["To Max"].default_value = 0.9
l.new(csx.outputs["Z"], fade.inputs["Value"])
lp_ = n.new("ShaderNodeLightPath")
cm1 = n.new("ShaderNodeMath"); cm1.operation = "MULTIPLY"; l.new(cov.outputs[0], cm1.inputs[0]); l.new(fade.outputs[0], cm1.inputs[1])
cm2 = n.new("ShaderNodeMath"); cm2.operation = "MULTIPLY"; l.new(cm1.outputs[0], cm2.inputs[0]); l.new(lp_.outputs["Is Camera Ray"], cm2.inputs[1])
lum = n.new("ShaderNodeRGBToBW"); l.new(sky.outputs["Color"], lum.inputs[0])
shade = n.new("ShaderNodeMapRange"); shade.inputs["To Min"].default_value = 0.85; shade.inputs["To Max"].default_value = 2.2
l.new(wnoise(4.0, 4, 0.5).outputs["Fac"], shade.inputs["Value"])
cv = n.new("ShaderNodeMath"); cv.operation = "MULTIPLY"; l.new(lum.outputs[0], cv.inputs[0]); l.new(shade.outputs[0], cv.inputs[1])
ccol = n.new("ShaderNodeCombineColor"); [l.new(cv.outputs[0], ccol.inputs[k]) for k in range(3)]
cmix = n.new("ShaderNodeMix"); cmix.data_type = "RGBA"; l.new(cm2.outputs[0], cmix.inputs[0])
l.new(sky.outputs["Color"], cmix.inputs[6]); l.new(ccol.outputs[0], cmix.inputs[7]); l.new(cmix.outputs[2], n["Background"].inputs["Color"])
# Haze: a finite volume box (50 x 50 km, 3.2 km high). A world volume renders black in Cycles here.
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 1500)); hb = bpy.context.object
hb.name = "haze_volume"; hb.scale = (50000, 50000, 3200)
for c_ in list(hb.users_collection): c_.objects.unlink(hb)
coll("atmosphere").objects.link(hb)
hm, hn, hl = nodes_mat("haze")
for x in list(hn):
    if x.type != "OUTPUT_MATERIAL": hn.remove(x)
vol = hn.new("ShaderNodeVolumeScatter"); vol.name = "haze"; vol.inputs["Density"].default_value = 2e-5; vol.inputs["Anisotropy"].default_value = 0.6
hl.new(vol.outputs["Volume"], hn["Material Output"].inputs["Volume"]); hb.data.materials.append(hm)
hb["claim"] = "look only: aerial haze"
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN")); scene.collection.objects.link(sun)
sun.data.angle = math.radians(0.53)

bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / "blender/out/talanta_scene.blend"))
tri = 0
for o in scene.objects:
    if o.type == "MESH": o.data.calc_loop_triangles(); tri += len(o.data.loop_triangles)
print("saved talanta_scene.blend; mesh triangles (excl. tree instances):", tri)
