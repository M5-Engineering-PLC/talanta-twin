"""Pass C (replica plan 2026-10-20): as-built ground from the drone frames, and the south-west from the trace.

Adds to blender/out/talanta_site.blend (after the step F context steps):
- collection asbuilt_ground: the traced as-built surfaces (blender/data/asbuilt_classes.png, from
  blender/concept_match/asbuilt_trace.py through the solved D01-D03 cameras) as one mesh of 1 m cells on the terrain:
  patchy grass, murram (dark red earth), laterite (bare plazas and paths), asphalt/concrete. Cells under trees and white
  roofs take the nearest ground class; public roads are left to the context roads. Shown only in the asbuilt state
  (blender/scene_state.py).
- the south-west from the trace, in both states (the frames win over the old layout): the old track_sw, its infield
  and training_field_sw are removed; collection trace_sw_finished holds the finished look of the traced layout (lawn
  pitch with lines, asphalt loop road round it); collection trace_structures holds the stand with the white roof west
  of the loop (plain masses: seating rake, roof, columns; no gates, exits or signs).
Our own geometry and colours only: no frame pixel is used as a texture (AGENTS.md rule 2).
Run from the repo root: ~/.venvs/bpy/bin/python blender/context/asbuilt_ground.py
"""
import json, math, os
from pathlib import Path
import numpy as np
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
LAB = np.asarray(Image.open(ROOT / "blender/data/asbuilt_classes.png"))
META = json.loads((ROOT / "blender/data/asbuilt_classes.json").read_text())
SW = META["south_west"]
CLAIM = "derived (traced from drone frames JWNowpO44rw 000645.000, 000714.767, 000617.567 through the solved cameras; +-3 m near, +-8 m far)"
bpy.ops.wm.open_mainfile(filepath=os.environ.get("TALANTA_SITE_BLEND", str(ROOT / "blender/out/talanta_site.blend")))
scene = bpy.context.scene


def coll(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in scene.collection.children: scene.collection.children.link(c)
    for o in list(c.objects): bpy.data.objects.remove(o)
    return c


def bvh_of(names):
    dg = bpy.context.evaluated_depsgraph_get(); V, F = [], []
    for n in names:
        o = bpy.data.objects.get(n)
        if o is None or o.type != "MESH": continue
        me = o.evaluated_get(dg).to_mesh(); b = len(V)
        V += [o.matrix_world @ v.co for v in me.vertices]; F += [[b + i for i in p.vertices] for p in me.polygons]
        o.evaluated_get(dg).to_mesh_clear()
    return BVHTree.FromPolygons(V, F) if F else None


GROUND = bvh_of(["terrain_site", "site_pad"])
ROADS = bvh_of(["roads", "ngong_road"])


def ground(x, z):
    """Top ground height (Blender z) under app (x, z)."""
    hit = GROUND.ray_cast(Vector((x, -z, 3000.0)), Vector((0, 0, -1)))
    return hit[0].z if hit[0] is not None else 0.0


def on_road(x, z, h):
    if ROADS is None: return False
    hit = ROADS.ray_cast(Vector((x, -z, h + 5.0)), Vector((0, 0, -1)), 6.0)
    return hit[0] is not None


def lin(hx):
    h = hx.lstrip("#"); return tuple(((int(h[i:i + 2], 16) / 255 + 0.055) / 1.055) ** 2.4 for i in (0, 2, 4))


def varied(name, a, b, rough, scale):
    """Principled material, base colour mixed between a and b (linear RGB) by world-space noise."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial"); p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tc = nt.nodes.new("ShaderNodeTexCoord"); nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = scale
    nz.inputs["Detail"].default_value = 6.0; nz.inputs["Roughness"].default_value = 0.6
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].position = 0.35; ramp.color_ramp.elements[1].position = 0.65
    ramp.color_ramp.elements[0].color = (*a, 1); ramp.color_ramp.elements[1].color = (*b, 1)
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"]); nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], p.inputs["Base Color"]); nt.links.new(p.outputs[0], out.inputs[0])
    p.inputs["Roughness"].default_value = rough; m.diffuse_color = (*a, 1); m["claim"] = "estimated (colour by eye from the frame class medians)"
    return m


# as-built surface set (linear albedo; frame medians in META["class_median_srgb"], tuned in the D renders)
MATS = {"grass": varied("asbuilt_grass_patchy", (0.150, 0.140, 0.060), (0.250, 0.200, 0.100), 0.95, 0.08),
        "murram": varied("asbuilt_murram", (0.085, 0.030, 0.018), (0.140, 0.060, 0.035), 0.95, 0.05),
        "laterite": varied("asbuilt_laterite", (0.360, 0.230, 0.160), (0.440, 0.300, 0.220), 0.9, 0.04),
        "paved": varied("asbuilt_asphalt", (0.130, 0.125, 0.120), (0.170, 0.165, 0.155), 0.85, 0.1)}
NAMES = META["classes"]; KEEP = [NAMES.index(c) for c in MATS]

# --- as-built mesh: one quad per known cell; tree and white cells take the nearest ground class
EXT, CELL = META["extent_m"][1], META["cell_m"]
lab = LAB.copy(); known = np.isin(lab, KEEP)
fill = (lab == NAMES.index("tree")) | (lab == NAMES.index("white"))
idx = ndimage.distance_transform_edt(~known, return_indices=True)[1]
lab[fill] = lab[idx[0], idx[1]][fill]; known = np.isin(lab, KEEP)
n = lab.shape[0]; LIFT = 0.12
vid = -np.ones((n + 1, n + 1), np.int64); verts, faces, fmat = [], [], []


def vert(r, c):
    if vid[r, c] < 0:
        x, z = -EXT + c * CELL, -EXT + r * CELL
        vid[r, c] = len(verts); verts.append((x, -z, ground(x, z) + LIFT))
    return int(vid[r, c])


skipped = 0
for r, c in zip(*np.nonzero(known)):
    x, z = -EXT + (c + 0.5) * CELL, -EXT + (r + 0.5) * CELL
    h = ground(x, z)
    if on_road(x, z, h): skipped += 1; continue
    faces.append((vert(r + 1, c), vert(r + 1, c + 1), vert(r, c + 1), vert(r, c)))  # counter-clockwise from above
    fmat.append(KEEP.index(int(lab[r, c])))
ab = coll("asbuilt_ground")
me = bpy.data.meshes.new("asbuilt_ground"); me.from_pydata(verts, [], faces); me.validate(); me.update()
for k in MATS: me.materials.append(MATS[k])
me.polygons.foreach_set("material_index", fmat); me.update()
o = bpy.data.objects.new("asbuilt_ground", me); ab.objects.link(o); o["claim"] = CLAIM; o["sources"] = "blender/data/asbuilt_classes.png"

# --- south-west from the trace (both states): remove the old track and training field there
removed = [nm for nm in ("track_sw", "track_sw_infield", "training_field_sw") if nm in bpy.data.objects]
for nm in removed: bpy.data.objects.remove(bpy.data.objects[nm])
cx, cz = SW["lawn_centre_xz"]; ux, uz = SW["lawn_axis_xz"]; L_, W_ = SW["lawn_len_m"], SW["lawn_wid_m"]
vx, vz = -uz, ux  # across the pitch


def rrect(half_l, half_w, rad, nseg=6):
    """Rounded rectangle round the lawn centre, local (along, across) then app (x, z), counter-clockwise."""
    pts = []
    for (sa, sw_), a0 in (((1, 1), 0), ((-1, 1), 90), ((-1, -1), 180), ((1, -1), 270)):
        ca, cw = sa * (half_l - rad), sw_ * (half_w - rad)
        for k in range(nseg + 1):
            t = math.radians(a0 + 90 * k / nseg); pts.append((ca + rad * math.cos(t), cw + rad * math.sin(t)))
    return [(cx + a * ux + w * vx, cz + a * uz + w * vz) for a, w in pts]


def flat(name, ring, inner, material, col, lift):
    """Planar band (ring minus inner) or disc (inner None) draped on the ground."""
    V = [(x, -z, ground(x, z) + lift) for x, z in ring]; F = []
    if inner is None:
        c0 = (sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring)); V.append((c0[0], -c0[1], ground(*c0) + lift))
        F = [(len(ring), i, (i + 1) % len(ring)) for i in range(len(ring))]
    else:
        V += [(x, -z, ground(x, z) + lift) for x, z in inner]; m_ = len(ring)
        F = [(i, (i + 1) % m_, m_ + (i + 1) % m_, m_ + i) for i in range(m_)]
    me = bpy.data.meshes.new(name); me.from_pydata(V, [], F); me.validate(); me.update(); me.materials.append(material)
    ob = bpy.data.objects.new(name, me); col.objects.link(ob); ob["claim"] = CLAIM; ob["sources"] = "blender/data/asbuilt_classes.json south_west"
    return ob


def mat(name, rgb, rough):
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True; p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough; m.diffuse_color = (*rgb, 1)
    return m


fin = coll("trace_sw_finished")
LAWN = bpy.data.materials.get("training_grass") or mat("sw_lawn", lin("#4E7A35"), 0.95)
ROAD = bpy.data.materials.get("roads_mat") or mat("sw_asphalt", lin("#3A3A3C"), 0.9)
LINE = bpy.data.materials.get("line_paint") or mat("sw_line", lin("#E8E8E2"), 0.6)
RW, RAD = SW["loop_road_w_m"], SW["loop_corner_r_m"]
lawn_ring = rrect(L_ / 2, W_ / 2, RAD - RW if RAD > RW + 2 else 2.0)
flat("sw_lawn", lawn_ring, None, LAWN, fin, 0.10)
flat("sw_loop_road", rrect(L_ / 2 + RW, W_ / 2 + RW, RAD), lawn_ring, ROAD, fin, 0.10)
# pitch lines: touchline box 105 x 68 m (or smaller to fit), halfway line, centre circle (0.12 m wide paint)
pl, pw = min(105.0, L_ - 6), min(68.0, W_ - 6); lw = 0.12
box_o, box_i = rrect(pl / 2 + lw / 2, pw / 2 + lw / 2, 0.2, 1), rrect(pl / 2 - lw / 2, pw / 2 - lw / 2, 0.1, 1)
flat("sw_pitch_lines_box", box_o, box_i, LINE, fin, 0.13)
half = [(cx + a * ux + w * vx, cz + a * uz + w * vz) for a, w in ((lw / 2, -pw / 2), (lw / 2, pw / 2), (-lw / 2, pw / 2), (-lw / 2, -pw / 2))]
flat("sw_pitch_lines_half", half, None, LINE, fin, 0.13)
circ = lambda r_: [(cx + r_ * math.cos(t) * ux + r_ * math.sin(t) * vx, cz + r_ * math.cos(t) * uz + r_ * math.sin(t) * vz) for t in np.linspace(0, 2 * math.pi, 64, endpoint=False)]
flat("sw_pitch_lines_circle", circ(9.15 + lw / 2), circ(9.15 - lw / 2), LINE, fin, 0.13)

# --- the stand with the white roof (both states): rake of seats facing the loop, roof on a back row of columns
st = coll("trace_structures"); S_ = SW["stand"]
sx, sz = S_["centre_xz"]; ax, az = S_["axis_xz"]; slen, sdep = S_["len_m"], S_["depth_m"]
fx, fz = cx - sx, cz - sz
nx, nz = (-az, ax) if (-az * fx + ax * fz) > 0 else (az, -ax)  # unit normal toward the pitch
SEAT = bpy.data.materials.get("seat_red_pbr") or mat("sw_seat", (0.38, 0.03, 0.04), 0.4)
WHITE = bpy.data.materials.get("white_shell_pbr") or mat("sw_white", (0.8, 0.8, 0.78), 0.32)
CONC = bpy.data.materials.get("concrete_pbr") or mat("sw_concrete", (0.55, 0.53, 0.5), 0.85)
g0 = ground(sx, sz)


def P(a, d, y):  # along the stand, toward the pitch (from the stand centre), height above the stand ground
    return (sx + a * ax + d * nx, -(sz + a * az + d * nz), g0 + y)


rise, tread = 0.42, 0.85; rows = max(6, min(16, round((sdep - 4.5) / tread)))  # roof depth from the trace, 4.5 m of it overhang and back
dep = rows * tread; V, F = [], []
for i in range(rows + 1):
    d = dep / 2 - i * tread; y = 0.6 + i * rise
    V += [P(-slen / 2, d, y), P(slen / 2, d, y)]
    if i < rows: V += [P(-slen / 2, d, y + rise), P(slen / 2, d, y + rise)]  # riser, then the next tread
k = len(V) - 2; V += [P(-slen / 2, dep / 2, 0), P(slen / 2, dep / 2, 0), P(-slen / 2, -dep / 2, 0), P(slen / 2, -dep / 2, 0)]
F = [(j, j + 1, j + 3, j + 2) for j in range(0, k, 2)]
fb = len(V) - 4; F += [(fb, fb + 1, 1, 0), (k, k + 1, fb + 3, fb + 2)]
me = bpy.data.meshes.new("sw_stand_rake"); me.from_pydata(V, [], F); me.validate(); me.update(); me.materials.append(SEAT)
ob = bpy.data.objects.new("sw_stand_rake", me); st.objects.link(ob); ob["claim"] = CLAIM
top = 0.6 + rows * rise; roof_y = top + 3.2; over = 3.0
rv = [P(-slen / 2 - 1, -dep / 2 - 1.5, roof_y + 0.6), P(slen / 2 + 1, -dep / 2 - 1.5, roof_y + 0.6),
      P(slen / 2 + 1, dep / 2 + over, roof_y - 0.4), P(-slen / 2 - 1, dep / 2 + over, roof_y - 0.4)]
rv += [(x, y, z + 0.35) for x, y, z in rv]
rf = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
me = bpy.data.meshes.new("sw_stand_roof"); me.from_pydata(rv, [], rf); me.validate(); me.update(); me.materials.append(WHITE)
ob = bpy.data.objects.new("sw_stand_roof", me); st.objects.link(ob); ob["claim"] = CLAIM
cv, cf = [], []
for a in np.linspace(-slen / 2, slen / 2, 7):
    for x0, y0, z0 in (P(a, -dep / 2 - 0.8, 0),):
        b = len(cv); r_ = 0.25
        cv += [(x0 - r_, y0 - r_, z0), (x0 + r_, y0 - r_, z0), (x0 + r_, y0 + r_, z0), (x0 - r_, y0 + r_, z0)]
        cv += [(x0 - r_, y0 - r_, z0 + roof_y + 0.6), (x0 + r_, y0 - r_, z0 + roof_y + 0.6), (x0 + r_, y0 + r_, z0 + roof_y + 0.6), (x0 - r_, y0 + r_, z0 + roof_y + 0.6)]
        cf += [(b + q, b + (q + 1) % 4, b + 4 + (q + 1) % 4, b + 4 + q) for q in range(4)]
me = bpy.data.meshes.new("sw_stand_columns"); me.from_pydata(cv, [], cf); me.validate(); me.update(); me.materials.append(WHITE)
ob = bpy.data.objects.new("sw_stand_columns", me); st.objects.link(ob); ob["claim"] = CLAIM

print("ASBUILT_GROUND " + json.dumps({"cells": len(faces), "verts": len(verts), "road_cells_skipped": skipped,
                                       "removed": removed, "stand_centre_xz": [sx, sz], "lawn_centre_xz": [cx, cz]}), flush=True)
bpy.ops.wm.save_mainfile()
