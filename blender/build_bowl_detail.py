"""Stage 03 (facade and bowl specialist): bowl interior detail on top of the blockout.

Opens blender/out/talanta_blockout.blend and the rings it wrote (blender/out/bowl_rings.json), adds:
- A. seats: one instanced seat per 0.5 m along every row, coloured by tier with the speckle mix seen in the frames,
     on pale grey concrete treads; radial aisles with half-steps and a centre handrail;
- B. pitch: mowing stripes, FIFA Law 1 markings on the estimated 105 x 68 m pitch, goals; grass run-off;
- C. roof underside: radial ribs with tension cables and struts, ring purlins, catwalk ring with hangers and floodlights;
- D. white VIP columns and bands; the upper gallery walkway with its railing (the 10:55 view), the colonnade with
     the louvred screen up to the roof, and video boards at both ends.
Saves blender/out/talanta_detail.blend (build_scene.py opens it). The web glTF stays the light blockout.
Sizes and colours: ledger rows bowl.seat.*, bowl.aisle.*, bowl.tread.*, pitch.* (estimated, by eye from the
named JWNowpO44rw frames; markings from the Laws of the Game). Frames are references only (AGENTS.md rule 2).
No exits, vomitories or other security detail (AGENTS.md rule 8).
Run from the repo root: ~/.venvs/bpy/bin/python blender/build_bowl_detail.py
"""
import csv, json, math
from pathlib import Path
import numpy as np
import bpy, bmesh
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[1]
L = {r["name"]: r for r in csv.DictReader(open(ROOT / "gis/parameter_ledger.csv"))}
V = lambda k: float(L[k + "_blockout"]["value"]) if k + "_blockout" in L else float(L[k]["value"])  # Blender overrides
G = json.loads((ROOT / "blender/out/bowl_rings.json").read_text())
N, PAD, dirs = G["N"], G["pad"], G["dirs"]
rIn, rBack = np.array(G["rIn"]), np.array(G["rBack"])
rng = np.random.default_rng(303)

bpy.ops.wm.open_mainfile(filepath=str(ROOT / "blender/out/talanta_blockout.blend"))
scene = bpy.context.scene
B = lambda x, y, z: (x, -z, y + PAD)  # app frame (pad-relative height) -> Blender


def coll(name):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name); scene.collection.children.link(c)
    return c


def srgb(h):
    return tuple(((int(h[i:i + 2], 16) / 255 + 0.055) / 1.055) ** 2.4 for i in (1, 3, 5))


def principled(name, rgb, rough=0.6, metal=0.0):
    m = bpy.data.materials.new(name)
    try: m.use_nodes = True
    except Exception: pass
    p = m.node_tree.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough; p.inputs["Metallic"].default_value = metal
    m.diffuse_color = (*rgb, 1)
    return m


def mesh_obj(name, collection, verts, faces, material, claim, sources, smooth=False):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.validate(); me.update()
    if smooth:
        for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(name, me); coll(collection).objects.link(o); o.data.materials.append(material)
    o["claim"], o["sources"] = claim, sources
    return o


def tube_obj(name, collection, paths, r, material, claim, sources, closed=False):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = 2; cu.use_fill_caps = True
    for pts in paths:
        sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
        for k, v in enumerate(pts): sp.points[k].co = (*v, 1)
        sp.use_cyclic_u = closed
    o = bpy.data.objects.new(name, cu); coll(collection).objects.link(o); o.data.materials.append(material)
    o["claim"], o["sources"] = claim, sources
    return o


def box(v, f, corners):
    """Append a box given its 8 corners (bottom 4 then top 4, same winding)."""
    b = len(v); v += corners
    f += [(b, b + 1, b + 2, b + 3), (b + 4, b + 7, b + 6, b + 5)] + [(b + k, b + 4 + k, b + 4 + (k + 1) % 4, b + (k + 1) % 4) for k in range(4)]


at = lambda i, t: rIn[i] + (rBack[i] - rIn[i]) * t
SRC_SEAT = "ledger bowl.seat.*, bowl.aisle.*, bowl.tier_*.* (estimated, by eye from JWNowpO44rw 00:46, 02:00, 08:00, 09:12)"

# ---------------------------------------------------------------- A. treads, aisles, seats
TREAD = principled("tread_concrete", srgb(L["bowl.tread.colour"]["value"]), 0.85)
for tn in ("lower", "middle", "upper"):
    o = bpy.data.objects[f"tier_{tn}"]; o.data.materials.clear(); o.data.materials.append(TREAD)

# aisle angles: every bowl.aisle.spacing m of arc along the front (seat start) ring
front = [(dirs[i][0] * rIn[i], dirs[i][1] * rIn[i]) for i in range(N)]
arc = np.concatenate([[0], np.cumsum([math.dist(front[i], front[(i + 1) % N]) for i in range(N)])])
n_ais = int(round(arc[-1] / V("bowl.aisle.spacing")))
ais_th = np.array([2 * math.pi * np.interp((k + 0.5) * arc[-1] / n_ais, arc, np.arange(N + 1)) / N for k in range(n_ais)])
half_aisle = V("bowl.aisle.width") / 2


def ring_at(t):
    """Row line at tier fraction t: arrays of (angle, app x, app z) densified to about 0.25 m."""
    th = np.linspace(0, 2 * math.pi, N + 1)
    r = np.array([at(i % N, t) for i in range(N + 1)])
    x, z = np.cos(th) * r, np.sin(th) * r
    seg = np.hypot(np.diff(x), np.diff(z)); s = np.concatenate([[0], np.cumsum(seg)])
    ss = np.arange(0, s[-1], 0.25)
    return np.interp(ss, s, th), np.interp(ss, s, x), np.interp(ss, s, z), s[-1]


def angdist(a, b):
    return np.abs((a - b + math.pi) % (2 * math.pi) - math.pi)


pitch_s = V("bowl.seat_pitch")
P, ROT, COL = [], [], []
cols = {"g": srgb(L["bowl.seat.green_hex"]["value"]), "r": srgb(L["bowl.seat.red_hex"]["value"]), "d": srgb(L["bowl.seat.dark_hex"]["value"])}
sv, sf, rails = [], [], []
for tn in ("lower", "middle", "upper"):
    t0, t1, y0, y1, rows = (V(f"bowl.tier_{tn}.{k}") for k in ("t0", "t1", "y0", "y1", "rows")); rows = int(rows)
    for k in range(rows):
        ta, tb = t0 + (t1 - t0) * k / rows, t0 + (t1 - t0) * (k + 1) / rows
        ya, yb = y0 + (y1 - y0) * k / rows, y0 + (y1 - y0) * (k + 1) / rows
        th, x, z, length = ring_at(ta + 0.55 * (tb - ta))
        # seats every seat_pitch m along the row, none within half an aisle of an aisle line
        idx = np.arange(0, len(th), int(round(pitch_s / 0.25)))
        r_row = np.hypot(x[idx], z[idx])
        gap = np.min(angdist(th[idx][:, None], ais_th[None, :]), axis=1) * r_row
        idx = idx[gap > half_aisle + pitch_s / 2]
        f = k / max(rows - 1, 1); u = rng.random(len(idx))
        if tn == "lower": c = np.where(u < V("bowl.seat.mix_lower_red_top") * np.clip((f - 0.6) / 0.4, 0, 1), "r", "g")
        elif tn == "middle": c = np.where(u < V("bowl.seat.mix_middle_green"), "g", "r")
        else: c = np.where(u < 0.12 + (V("bowl.seat.mix_upper_dark_top") - 0.12) * f * f, "d", "r")
        for q, cc in zip(idx, c):
            nx, nz = -x[q], -z[q]; n = math.hypot(nx, nz)  # face the bowl centre
            P.append(B(x[q], ya, z[q])); ROT.append((0.0, 0.0, math.atan2(-nz / n, nx / n) - math.pi / 2)); COL.append((*cols[cc], 1.0))
        # aisle half-steps: a block half a riser high over the back half of each tread
        for a in ais_th:
            i0 = int(round(a / (2 * math.pi) * N)) % N
            ux, uz = dirs[i0]; tx, tz = -uz, ux
            rm, rb = at(i0, (ta + tb) / 2), at(i0, tb); ym = ya + (yb - ya) / 2; w = half_aisle
            corners = []
            for yy in (ya, ym):
                for rr, ss in ((rm, -w), (rm, w), (rb, w), (rb, -w)):
                    corners.append(B(ux * rr + tx * ss, yy, uz * rr + tz * ss))
            box(sv, sf, corners)
    for a in ais_th:  # centre handrail up each aisle, 0.9 m above the nosings
        i0 = int(round(a / (2 * math.pi) * N)) % N; ux, uz = dirs[i0]
        pts = [B(ux * at(i0, t0 + (t1 - t0) * k / rows), y0 + (y1 - y0) * k / rows + 0.9, uz * at(i0, t0 + (t1 - t0) * k / rows)) for k in range(rows + 1)]
        rails.append(pts)
mesh_obj("aisle_steps", "bowl_detail", sv, sf, TREAD, "estimated", SRC_SEAT)
RAIL = principled("rail_steel", (0.55, 0.56, 0.57), 0.35, 0.8)
tube_obj("aisle_rails", "bowl_detail", rails, 0.03, RAIL, "estimated", SRC_SEAT)

# seat prototype in metres, front towards +Y: pedestal, pan, back (shape estimated, 08:00)
bm = bmesh.new()
sw = V("bowl.seat.width") / 2; ph = V("bowl.seat.pan_h")
for (cx, cy, cz, hx, hy, hz, tilt) in [(0, -0.05, ph / 2, 0.03, 0.14, ph / 2, 0), (0, 0.02, ph, sw, 0.2, 0.025, 0.05), (0, -0.2, ph + 0.22, sw, 0.025, 0.22, -0.18)]:
    g = bmesh.ops.create_cube(bm, size=1.0)
    for v in g["verts"]:
        v.co.x *= 2 * hx; v.co.y *= 2 * hy; v.co.z *= 2 * hz
        v.co = Matrix.Rotation(tilt, 3, "X") @ v.co; v.co.x += cx; v.co.y += cy; v.co.z += cz
seat_me = bpy.data.meshes.new("seat_proto"); bm.to_mesh(seat_me); bm.free()
SEATM = bpy.data.materials.new("seat_plastic")
try: SEATM.use_nodes = True
except Exception: pass
sn, sl = SEATM.node_tree.nodes, SEATM.node_tree.links
sa = sn.new("ShaderNodeAttribute"); sa.attribute_type = "INSTANCER"; sa.attribute_name = "seatcol"
sl.new(sa.outputs["Color"], sn["Principled BSDF"].inputs["Base Color"]); sn["Principled BSDF"].inputs["Roughness"].default_value = 0.4
SEATM.diffuse_color = (0.6, 0.1, 0.1, 1)
seat_me.materials.append(SEATM)
protos = coll("bowl_protos"); protos.hide_render = True; protos.hide_viewport = True
seat_o = bpy.data.objects.new("seat_proto", seat_me); protos.objects.link(seat_o)

pm = bpy.data.meshes.new("seat_points"); pm.from_pydata(P, [], [])
pm.attributes.new("rot", "FLOAT_VECTOR", "POINT").data.foreach_set("vector", np.array(ROT, np.float32).ravel())
pm.attributes.new("seatcol", "FLOAT_COLOR", "POINT").data.foreach_set("color", np.array(COL, np.float32).ravel())
so = bpy.data.objects.new("seats", pm); coll("bowl_detail").objects.link(so)
so["claim"], so["sources"] = "estimated (positions from the tier rows; colours by eye)", SRC_SEAT
gn = bpy.data.node_groups.new("seat_scatter", "GeometryNodeTree")
gn.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
gn.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
gi, go = gn.nodes.new("NodeGroupInput"), gn.nodes.new("NodeGroupOutput")
oi = gn.nodes.new("GeometryNodeObjectInfo"); oi.inputs["Object"].default_value = seat_o
ra = gn.nodes.new("GeometryNodeInputNamedAttribute"); ra.data_type = "FLOAT_VECTOR"; ra.inputs["Name"].default_value = "rot"
iop = gn.nodes.new("GeometryNodeInstanceOnPoints")
gn.links.new(gi.outputs[0], iop.inputs["Points"]); gn.links.new(oi.outputs["Geometry"], iop.inputs["Instance"])
gn.links.new(ra.outputs["Attribute"], iop.inputs["Rotation"]); gn.links.new(iop.outputs["Instances"], go.inputs[0])
so.modifiers.new("seats", "NODES").node_group = gn
print("seats:", len(P), "aisles per ring:", n_ais)

# ---------------------------------------------------------------- B. pitch
b = math.radians(G["bearing"]); cb, sb = math.cos(b), math.sin(b)
rot = lambda x, z: (x * cb - z * sb, x * sb + z * cb)  # pitch local (x across, z along) -> app, as rounded_rect()
hl, hw = V("pitch.length") / 2, V("pitch.width") / 2
YM = 0.1
turf = bpy.data.materials.new("pitch_turf")
try: turf.use_nodes = True
except Exception: pass
tn_, tl_ = turf.node_tree.nodes, turf.node_tree.links
tco = tn_.new("ShaderNodeTexCoord"); dp = tn_.new("ShaderNodeVectorMath"); dp.operation = "DOT_PRODUCT"
ax = rot(0, 1); dp.inputs[1].default_value = (ax[0], -ax[1], 0)  # along-pitch axis in Blender
tl_.new(tco.outputs["Object"], dp.inputs[0])
nstr = V("pitch.mow_stripes")
dv = tn_.new("ShaderNodeMath"); dv.operation = "DIVIDE"; dv.inputs[1].default_value = 2 * hl / nstr; tl_.new(dp.outputs["Value"], dv.inputs[0])
fl = tn_.new("ShaderNodeMath"); fl.operation = "FLOOR"; tl_.new(dv.outputs[0], fl.inputs[0])
md = tn_.new("ShaderNodeMath"); md.operation = "FLOORED_MODULO"; md.inputs[1].default_value = 2; tl_.new(fl.outputs[0], md.inputs[0])
nz = tn_.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 0.6; tl_.new(tco.outputs["Object"], nz.inputs["Vector"])
mx = tn_.new("ShaderNodeMix"); mx.data_type = "RGBA"; tl_.new(md.outputs[0], mx.inputs[0])
mx.inputs[6].default_value = (0.055, 0.15, 0.035, 1); mx.inputs[7].default_value = (0.085, 0.21, 0.05, 1)
mx2 = tn_.new("ShaderNodeMix"); mx2.data_type = "RGBA"; mx2.blend_type = "OVERLAY"; mx2.inputs[0].default_value = 0.25
tl_.new(mx.outputs[2], mx2.inputs[6]); tl_.new(nz.outputs["Color"], mx2.inputs[7])
tl_.new(mx2.outputs[2], tn_["Principled BSDF"].inputs["Base Color"]); tn_["Principled BSDF"].inputs["Roughness"].default_value = 0.9
turf.diffuse_color = (0.08, 0.2, 0.05, 1)
po = bpy.data.objects["pitch"]; po.data.materials.clear(); po.data.materials.append(turf)
pz = bpy.data.objects["pitch_zone"]; pz.data.materials.clear(); pz.data.materials.append(principled("runoff_grass", (0.06, 0.16, 0.04), 0.9))

LW = 0.12
mv, mf = [], []


def stripe(pts, closed=False):
    """Thin white band of width LW along a polyline in pitch-local (x, z)."""
    n = len(pts)
    for k in range(n if closed else n - 1):
        (x0, z0), (x1, z1) = pts[k], pts[(k + 1) % n]
        dx, dz = x1 - x0, z1 - z0; d = math.hypot(dx, dz) or 1; ox, oz = -dz / d * LW / 2, dx / d * LW / 2
        b0 = len(mv)
        for (px, pz_) in ((x0 - ox, z0 - oz), (x0 + ox, z0 + oz), (x1 + ox, z1 + oz), (x1 - ox, z1 - oz)):
            ax_, az_ = rot(px, pz_); mv.append(B(ax_, YM, az_))
        mf.append((b0, b0 + 1, b0 + 2, b0 + 3))


def arc(cx, cz, r, a0, a1, n=48):
    return [(cx + r * math.cos(a), cz + r * math.sin(a)) for a in np.linspace(a0, a1, n)]


stripe([(-hw, -hl), (hw, -hl), (hw, hl), (-hw, hl)], closed=True)
stripe([(-hw, 0), (hw, 0)])
stripe(arc(0, 0, 9.15, 0, 2 * math.pi, 96), closed=True)
stripe(arc(0, 0, 0.15, 0, 2 * math.pi, 12), closed=True)
for sg in (-1, 1):
    gl = sg * hl
    stripe([(-20.16, gl), (-20.16, gl - sg * 16.5), (20.16, gl - sg * 16.5), (20.16, gl)])
    stripe([(-9.16, gl), (-9.16, gl - sg * 5.5), (9.16, gl - sg * 5.5), (9.16, gl)])
    spot = gl - sg * 11; stripe(arc(0, spot, 0.15, 0, 2 * math.pi, 12), closed=True)
    da = math.acos(5.5 / 9.15)  # arc outside the penalty area
    mid = -math.pi / 2 if sg > 0 else math.pi / 2
    stripe(arc(0, spot, 9.15, mid - (math.pi / 2 - da), mid + (math.pi / 2 - da), 32))
    for cx in (-hw, hw):
        a0 = math.atan2(-sg, -math.copysign(1, cx)); stripe(arc(cx, gl, 1.0, a0 - math.pi / 4, a0 + math.pi / 4, 12))
LINE = principled("line_paint", (0.8, 0.8, 0.78), 0.8)
mesh_obj("pitch_markings", "pitch", mv, mf, LINE, "estimated (Laws of the Game on the estimated pitch size)", "ledger pitch.markings, pitch.length, pitch.width")
goals = []
for sg in (-1, 1):
    gl = sg * hl; back = gl + sg * 2.0
    for p in ([(-3.66, gl, 0), (-3.66, gl, 2.44), (3.66, gl, 2.44), (3.66, gl, 0)],
              [(-3.66, gl, 2.44), (-3.66, back, 1.8), (-3.66, back, 0)], [(3.66, gl, 2.44), (3.66, back, 1.8), (3.66, back, 0)],
              [(-3.66, back, 1.8), (3.66, back, 1.8)]):
        goals.append([B(rot(x, z)[0], y + YM, rot(x, z)[1]) for x, z, y in p])
tube_obj("goals", "pitch", goals, 0.06, principled("goal_white", (0.85, 0.85, 0.85), 0.3), "estimated (Laws of the Game goal size)", "ledger pitch.markings")

# ---------------------------------------------------------------- C. roof underside (by eye from 10:04, 09:12; estimated)
PROF, JF = G["prof"], G["j_facade"]; NP = len(PROF[0])


def surf(theta, jf, down=0.0):
    """Point on the shell profile at angle theta and fractional profile index jf, dropped `down` m (Blender)."""
    fi = (theta / (2 * math.pi)) % 1 * N; i0 = int(fi) % N; i1 = (i0 + 1) % N; fi -= int(fi)
    j0 = min(int(jf), NP - 2); fj = jf - j0
    r = sum(PROF[i][j][0] * wi * wj for i, wi in ((i0, 1 - fi), (i1, fi)) for j, wj in ((j0, 1 - fj), (j0 + 1, fj)))
    y = sum(PROF[i][j][1] * wi * wj for i, wi in ((i0, 1 - fi), (i1, fi)) for j, wj in ((j0, 1 - fj), (j0 + 1, fj)))
    return B(math.cos(theta) * r, y - down, math.sin(theta) * r)


STEEL = principled("roof_steel_white", (0.78, 0.78, 0.76), 0.4, 0.1)
SRC_ROOF = "ledger bowl.roofsteel.*, bowl.catwalk.*, bowl.floodlights.* (estimated, by eye from JWNowpO44rw 10:04, 10:38 and the 10:55 view)"
# Tension cable roof (10:38, 10:55): radial ribs from the rim to the opening ring, each with a dark tension cable
# sagging below it and vertical struts between them; ring purlins between the ribs.
KR, dr = int(V("bowl.roofsteel.ribs")), V("bowl.roofsteel.drop")
J0, J1 = JF + 1.0, NP - 1.3
prim, cables, struts = [], [], []
sag = V("bowl.roofsteel.cable_sag")
for k in range(KR):
    th = 2 * math.pi * (k + 0.5) / KR
    js = np.linspace(J0, J1, 40)
    prim.append([surf(th, j, dr) for j in js])
    cab = [surf(th, j, dr + sag * math.sin(math.pi * (j - J0) / (J1 - J0))) for j in js]
    cables.append(cab)
    for q in range(5, 40, 6): struts.append([prim[-1][q], cab[q]])
tube_obj("roof_ribs_under", "roof_detail", prim, V("bowl.roofsteel.member_r"), STEEL, "estimated", SRC_ROOF)
CABLE = principled("cable_dark", (0.05, 0.05, 0.055), 0.4, 0.8)
tube_obj("roof_cables", "roof_detail", cables, 0.06, CABLE, "estimated", SRC_ROOF)
tube_obj("roof_struts", "roof_detail", struts, 0.08, STEEL, "estimated", SRC_ROOF)
nring = int(V("bowl.roofsteel.purlin_rings"))
purl = [[surf(2 * math.pi * i / (4 * N), j, 0.45) for i in range(4 * N)] for j in np.linspace(J0, J1, nring)]
tube_obj("roof_purlins", "roof_detail", purl, 0.13, STEEL, "estimated", SRC_ROOF, closed=True)
# catwalk ring near the opening: deck, two handrails, hangers to the primaries, floodlight heads on the inner side
jc, cd, cw = NP - 1.6, V("bowl.catwalk.drop"), V("bowl.catwalk.width") / 2
cv_, cf_ = [], []
ring_c = [surf(2 * math.pi * i / (2 * N), jc, cd) for i in range(2 * N)]
for i in range(2 * N):
    th = 2 * math.pi * i / (2 * N); ux, uy = math.cos(th), -math.sin(th); x, y, z = ring_c[i]
    cv_ += [(x - ux * cw, y - uy * cw, z), (x + ux * cw, y + uy * cw, z)]
for i in range(2 * N):
    a, b_ = 2 * i, 2 * ((i + 1) % (2 * N)); cf_.append((a, b_, b_ + 1, a + 1))
mesh_obj("catwalk_deck", "roof_detail", cv_, cf_, principled("catwalk_grating", (0.45, 0.46, 0.46), 0.6, 0.6), "estimated", SRC_ROOF)
rails_c = []
for off in (-cw, cw):
    pts = []
    for i in range(2 * N):
        th = 2 * math.pi * i / (2 * N); x, y, z = ring_c[i]; pts.append((x + math.cos(th) * off, y - math.sin(th) * off, z + 1.1))
    rails_c.append(pts)
tube_obj("catwalk_rails", "roof_detail", rails_c, 0.04, STEEL, "estimated", SRC_ROOF, closed=True)
hang = [[surf(2 * math.pi * (k + 0.5) / KR, jc, cd), surf(2 * math.pi * (k + 0.5) / KR, jc, dr)] for k in range(KR)]
tube_obj("catwalk_hangers", "roof_detail", [[(x, y, z) for x, y, z in h] for h in hang], 0.05, STEEL, "estimated", SRC_ROOF)
fv, ff = [], []
length = sum(math.dist(ring_c[i], ring_c[(i + 1) % (2 * N)]) for i in range(2 * N))
nfl = int(length / V("bowl.floodlights.spacing"))
for q in range(nfl):
    th = 2 * math.pi * q / nfl; x, y, z = surf(th, jc, cd + 0.4)
    ux, uy = math.cos(th), -math.sin(th); tx, ty = -uy, ux; cx, cy = x - ux * (cw + 0.3), y - uy * (cw + 0.3)
    corners = []
    for zz, inset in ((z - 0.35, 0.05), (z + 0.3, 0.0)):  # head tilted down towards the pitch
        for su, so in ((-0.35, -0.2), (0.35, -0.2), (0.35, 0.2), (-0.35, 0.2)):
            corners.append((cx + tx * su + ux * (so - inset * 4), cy + ty * su + uy * (so - inset * 4), zz))
    box(fv, ff, corners)
mesh_obj("floodlights", "roof_detail", fv, ff, principled("floodlight_head", (0.12, 0.12, 0.13), 0.35, 0.6), "estimated", SRC_ROOF)
print("roof ribs:", len(prim), "floodlights:", nfl)

# ---------------------------------------------------------------- D. VIP band and upper colonnade (09:12, 08:00; estimated)
WHITE_P = principled("paint_white", (0.8, 0.8, 0.78), 0.5)
for nm in ("band_lower", "band_middle", "pitch_wall"):
    o = bpy.data.objects[nm]; o.data.materials.clear(); o.data.materials.append(WHITE_P)


def columns(name, r_fn, y0, y1_fn, spacing, r, sources):
    ring = [(dirs[i][0] * r_fn(i), dirs[i][1] * r_fn(i)) for i in range(N)]
    seg = [math.dist(ring[i], ring[(i + 1) % N]) for i in range(N)]; tot = sum(seg)
    paths, acc, nxt = [], 0.0, spacing / 2
    for i in range(N):
        while nxt <= acc + seg[i]:
            f = (nxt - acc) / seg[i]; a, b_ = ring[i], ring[(i + 1) % N]
            x, z = a[0] + (b_[0] - a[0]) * f, a[1] + (b_[1] - a[1]) * f
            paths.append([B(x, y0, z), B(x, y1_fn(i), z)]); nxt += spacing
        acc += seg[i]
    return tube_obj(name, "bowl_detail", paths, r, WHITE_P, "estimated", sources)


tm0 = V("bowl.tier_middle.t0") - 0.012
columns("vip_columns", lambda i: at(i, tm0), V("bowl.tier_lower.y1"), lambda i: V("bowl.band.vip_glass_y1"), V("bowl.vip.column_spacing"), V("bowl.vip.column_r"),
        "ledger bowl.vip.*, bowl.band.* (estimated, by eye from JWNowpO44rw 09:12)")


def roof_under_at(i, r):
    """Height (pad-relative) of the roof underside at radius r in direction i."""
    p = PROF[i]
    for j in range(JF, NP - 1):
        (ra, ya), (rb, yb) = p[j], p[j + 1]
        if (ra - r) * (rb - r) <= 0 and ra != rb: return ya + (yb - ya) * (r - ra) / (rb - ra)
    return p[JF][1]


yU = V("bowl.tier_upper.y1")
GW, RH = V("bowl.gallery.width"), V("bowl.gallery.rail_h")
yG = yU + 0.3  # gallery deck just above the top row (10:55)
rCol = lambda i: rBack[i] + GW + 0.3
columns("colonnade", rCol, yG, lambda i: roof_under_at(i, rCol(i)) - 0.3, V("bowl.colonnade.spacing"), 0.5,
        "ledger bowl.colonnade.spacing (estimated, by eye from JWNowpO44rw 08:00 and the 10:55 view)")
# Upper gallery walkway (the 10:55 view): deck from the back of the upper tier out to the colonnade, white
# railing on the bowl side (posts, top and mid rails). Estimated, by eye.
SRC_GAL = "ledger bowl.gallery.* (estimated, by eye from JWNowpO44rw 10:55, Munene's screenshot)"
gv, gf = [], []
for i in range(N):
    ux, uz = dirs[i]; gv += [B(ux * rBack[i], yG, uz * rBack[i]), B(ux * (rBack[i] + GW + 0.8), yG, uz * (rBack[i] + GW + 0.8))]
for i in range(N):
    a, b_ = 2 * i, 2 * ((i + 1) % N); gf.append((a, b_, b_ + 1, a + 1))
mesh_obj("gallery_deck", "bowl_detail", gv, gf, TREAD, "estimated", SRC_GAL)
rr = lambda i: rBack[i] + 0.1
dense = [(dirs[i % N][0] * rr(i % N), dirs[i % N][1] * rr(i % N)) for i in range(N)]
tube_obj("gallery_rails", "bowl_detail", [[B(x, yG + h, z) for x, z in dense] for h in (RH, RH / 2)], 0.04, WHITE_P, "estimated", SRC_GAL, closed=True)
columns("gallery_posts", rr, yG, lambda i: yG + RH, V("bowl.gallery.post_spacing"), 0.03, SRC_GAL)
# louvred screen between the colonnade columns: from the gallery up to the roof underside
lv, lf = [], []
for i in range(N):
    ux, uz = dirs[i]; r = rCol(i) + 0.4
    lv += [B(ux * r, yG, uz * r), B(ux * r, roof_under_at(i, r) - 0.3, uz * r)]
for i in range(N):
    a, b_ = 2 * i, 2 * ((i + 1) % N); lf.append((a, b_, b_ + 1, a + 1))
scr = bpy.data.materials.new("colonnade_louvre")
try: scr.use_nodes = True
except Exception: pass
cn, cl = scr.node_tree.nodes, scr.node_tree.links
wv = cn.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "Z"; wv.inputs["Scale"].default_value = 0.08
cco = cn.new("ShaderNodeTexCoord"); cl.new(cco.outputs["Object"], wv.inputs["Vector"])
crp = cn.new("ShaderNodeValToRGB"); crp.color_ramp.elements[0].color = (0.06, 0.06, 0.07, 1); crp.color_ramp.elements[1].color = (0.75, 0.75, 0.73, 1)
crp.color_ramp.elements[0].position = 0.35; crp.color_ramp.elements[1].position = 0.55
cl.new(wv.outputs["Fac"], crp.inputs["Fac"]); cl.new(crp.outputs["Color"], cn["Principled BSDF"].inputs["Base Color"])
scr.diffuse_color = (0.5, 0.5, 0.5, 1)
mesh_obj("colonnade_screen", "bowl_detail", lv, lf, scr, "estimated", "back of the louvred facade seen from inside (estimated, by eye from 08:00)")

# Video boards under the roof at the north and south ends of the pitch axis (10:38, 10:55; estimated, no content)
bw, bh = V("bowl.screen.width") / 2, V("bowl.screen.height")
bv, bf, bh_ = [], [], []
for sg in (1, -1):
    ex, ez = rot(0, sg)  # along-pitch direction in the app frame
    th = math.atan2(ez, ex); i0 = int(round(th / (2 * math.pi) * N)) % N
    t0u, t1u, y0u, y1u = (V(f"bowl.tier_upper.{k}") for k in ("t0", "t1", "y0", "y1"))
    seat_y = lambda r: y0u + (y1u - y0u) * min(max(((r - rIn[i0]) / (rBack[i0] - rIn[i0]) - t0u) / (t1u - t0u), 0), 1)
    r = rBack[i0] - 4
    while roof_under_at(i0, r) - 0.8 - bh < seat_y(r) + 4: r -= 1  # hang it in until it clears the rows below by 4 m
    top = roof_under_at(i0, r) - 0.8
    print(f"video board at {rBack[i0] - r:.0f} m in from the back of the upper tier, clearance {top - bh - seat_y(r):.1f} m")
    print(f"video board {'S' if sg > 0 else 'N'}: top {top:.1f} m, bottom {top - bh:.1f} m, top row {V('bowl.tier_upper.y1'):.1f} m")
    ux, uz = dirs[i0]; tx, tz = -uz, ux
    corners = []
    for yy in (top - bh, top):
        for su, so in ((-bw, -0.4), (bw, -0.4), (bw, 0.4), (-bw, 0.4)):
            corners.append(B(ux * (r + so) + tx * su, yy, uz * (r + so) + tz * su))
    box(bv, bf, corners)
    for su in (-bw * 0.7, bw * 0.7):
        bh_.append([B(ux * r + tx * su, top, uz * r + tz * su), B(ux * r + tx * su, roof_under_at(i0, r) + 0.5, uz * r + tz * su)])
mesh_obj("video_boards", "bowl_detail", bv, bf, principled("screen_black", (0.015, 0.015, 0.018), 0.15, 0.2), "estimated", "ledger bowl.screen.* (estimated, by eye from 10:38, 10:55)")
tube_obj("video_board_hangers", "bowl_detail", bh_, 0.1, STEEL, "estimated", "ledger bowl.screen.* (estimated)")

bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / "blender/out/talanta_detail.blend"))
print("saved talanta_detail.blend")
