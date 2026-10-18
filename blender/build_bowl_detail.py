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
No exit signs, routing, control rooms, CCTV, access control or gate hardware (AGENTS.md rule 8). The interior pass (IT03)
adds generic portal openings with blank panels as seen in the tour frames; they carry no signage or egress meaning.
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
TONES, TONE_W = {}, {}
for tn_ in ("lower", "middle", "upper"):
    hx = L[f"bowl.seat.{tn_}_tones"]["value"].split(";"); TONES[tn_] = np.array([f"{tn_}{j}" for j in range(len(hx))])
    TONE_W[tn_] = np.array([float(w) for w in L[f"bowl.seat.{tn_}_tone_weights"]["value"].split(";")])
    for j, h in enumerate(hx): cols[f"{tn_}{j}"] = srgb(h)
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
        # IT01-IT03, IT05 (detail sheet 05, frames 000945.200, 002144.300): three seeded tones per tier; the middle tier
        # keeps the green flecks (002144.300 confirms them), denser in its lower rows
        tone = TONES[tn][np.searchsorted(np.cumsum(TONE_W[tn]), rng.random(len(idx)) * 0.9999)]
        if tn == "lower": c = np.where(u < V("bowl.seat.mix_lower_red_top") * np.clip((f - 0.6) / 0.4, 0, 1), "r", tone)
        elif tn == "middle": c = np.where(u < V("bowl.seat.mix_middle_green") * 2 * (1 - f), "g", tone)
        else: c = tone
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
if "bowl.roof.cushion_bays" in L and KR % int(V("bowl.roof.cushion_bays")) != 0:
    raise ValueError("bowl.roofsteel.ribs must be a multiple of bowl.roof.cushion_bays (topside ribs sit on primaries)")
J0, J1 = JF + 1.0, NP - 1.3
prim, cables, struts = [], [], []
sag = V("bowl.roofsteel.cable_sag")
for k in range(KR):
    th = 2 * math.pi * k / KR  # every other primary lies under a topside rib (bowl.roof.cushion_bays = KR / 2)
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
hang = [[surf(2 * math.pi * k / KR, jc, cd), surf(2 * math.pi * k / KR, jc, dr)] for k in range(KR)]
tube_obj("catwalk_hangers", "roof_detail", [[(x, y, z) for x, y, z in h] for h in hang], 0.05, STEEL, "estimated", SRC_ROOF)
fv, ff = [], []
length = sum(math.dist(ring_c[i], ring_c[(i + 1) % (2 * N)]) for i in range(2 * N))
nfl = KR * int(V("bowl.floodlights.per_bay")) if "bowl.floodlights.per_bay" in L else int(length / V("bowl.floodlights.spacing"))
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
# IT13 (002144.300; sheet 05 wins over BS18): the concourse runs bowl.concourse.depth m back under the middle tier; its
# white round columns stand near the back, from the concourse floor to the underside of the middle tier
CD = V("bowl.concourse.depth")
t0m_, t1m_, y0m_, y1m_ = (V(f"bowl.tier_middle.{k}") for k in ("t0", "t1", "y0", "y1"))
def mid_under(i, r):
    """Height (pad-relative) of the middle tier's surface over radius r (the concourse ceiling), less a 0.6 m slab."""
    t = (r - rIn[i]) / (rBack[i] - rIn[i]); return y0m_ + (y1m_ - y0m_) * min(max((t - t0m_) / (t1m_ - t0m_), 0), 1) - 0.6
columns("vip_columns", lambda i: at(i, tm0) + CD - 1.5, V("bowl.tier_lower.y1"), lambda i: mid_under(i, at(i, tm0) + CD - 1.5),
        V("bowl.vip.column_spacing"), V("bowl.vip.column_r"), "ledger bowl.vip.*, bowl.concourse.depth (estimated, IT13, frame 002144.300)")


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
for sg in (1, -1):
    bv, bf, bh_ = [], [], []
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
    end = "S" if sg > 0 else "N"  # one object per end, so a camera standing at one end can hide it (blender/data/camera_hides.json)
    mesh_obj(f"video_board_{end}", "bowl_detail", bv, bf, principled("screen_black", (0.015, 0.015, 0.018), 0.15, 0.2), "estimated", "ledger bowl.screen.* (estimated, by eye from 10:38, 10:55)")
    tube_obj(f"video_board_hangers_{end}", "bowl_detail", bh_, 0.1, STEEL, "estimated", "ledger bowl.screen.* (estimated)")

# ---------------------------------------------------------------- E. detail sheet BS (group 2, with the lead review)
SRC_BS = "detail sheet BS (engineering/detail_sheets/02_bowl_seats.md) with the lead review"
# Speaker clusters (BS30; lead review correction 4, frame 02:00): curved white line arrays with dark grilles, a J of
# boxes bending down towards the stands, hung by chains from a white steel frame under the roof above the upper tier.
SPK_W = principled("speaker_white", srgb("#E4E4E0"), 0.45, 0.1); SPK_G = principled("speaker_grille", srgb("#171819"), 0.6, 0.2)
ne, ew, eh, ed = int(V("bowl.speaker.elements")), V("bowl.speaker.el_w"), V("bowl.speaker.el_h"), V("bowl.speaker.el_d")
nsp = int(V("bowl.speaker.count")); t0u = V("bowl.tier_upper.t0"); y0u, y1u = V("bowl.tier_upper.y0"), V("bowl.tier_upper.y1")
wv_, wf_, gv_, gf_, ch_ = [], [], [], [], []
for k in range(nsp):
    th = 2 * math.pi * (k + 0.25) / nsp; i0 = int(round(th / (2 * math.pi) * N)) % N
    ux, uz = dirs[i0]; tx, tz = -uz, ux
    r = at(i0, t0u + V("bowl.speaker.t_over_tier") * (1 - t0u)); top = roof_under_at(i0, r) - V("bowl.speaker.drop")
    # J curve in the radial plane: each element turns a little more towards the stands (outward, away from the pitch)
    p_r, p_y, ang = r, top, 0.0
    for e in range(ne):
        ang += math.radians(3 + 4 * e)  # splay grows down the array
        dr_, dy_ = math.sin(ang) * eh, -math.cos(ang) * eh
        cr, cy = p_r + dr_ / 2, p_y + dy_ / 2; p_r += dr_; p_y += dy_
        nr, ny = math.cos(ang), math.sin(ang)  # front face normal (outward and slightly up)
        def cpt(su, sn_, sv):  # across, front/back, along the array
            rr = cr + nr * sn_ + math.sin(ang) * sv; yy = cy + ny * sn_ - math.cos(ang) * sv
            return B(ux * rr + tx * su, yy, uz * rr + tz * su)
        hw_, hd_, hh_ = ew / 2, ed / 2, eh / 2 * 0.96
        box(wv_, wf_, [cpt(-hw_, -hd_, -hh_), cpt(hw_, -hd_, -hh_), cpt(hw_, hd_, -hh_), cpt(-hw_, hd_, -hh_),
                       cpt(-hw_, -hd_, hh_), cpt(hw_, -hd_, hh_), cpt(hw_, hd_, hh_), cpt(-hw_, hd_, hh_)])
        gi_ = hw_ * 0.78; b0 = len(gv_)  # dark grille set just proud of the front face
        gv_ += [cpt(-gi_, hd_ + 0.02, -hh_ * 0.8), cpt(gi_, hd_ + 0.02, -hh_ * 0.8), cpt(gi_, hd_ + 0.02, hh_ * 0.8), cpt(-gi_, hd_ + 0.02, hh_ * 0.8)]
        gf_.append((b0, b0 + 1, b0 + 2, b0 + 3))
    # hanging frame and chains
    fw_ = ew * 0.8
    for su in (-fw_, fw_):
        ch_.append([B(ux * (r - 0.6) + tx * su, top + 0.3, uz * (r - 0.6) + tz * su), B(ux * (r - 0.6) + tx * su, roof_under_at(i0, r) - 0.2, uz * (r - 0.6) + tz * su)])
        ch_.append([B(ux * (r + 0.6) + tx * su, top + 0.3, uz * (r + 0.6) + tz * su), B(ux * (r + 0.6) + tx * su, roof_under_at(i0, r) - 0.2, uz * (r + 0.6) + tz * su)])
    hw_ = ew / 2 + 0.3
    box(wv_, wf_, [B(ux * (r + a_) + tx * b_, top + yy, uz * (r + a_) + tz * b_) for yy in (0.15, 0.4) for a_, b_ in ((-1.0, -hw_), (-1.0, hw_), (1.0, hw_), (1.0, -hw_))])
mesh_obj("speaker_clusters", "roof_detail", wv_, wf_, SPK_W, "estimated", SRC_BS + "; ledger bowl.speaker.* (by eye from JWNowpO44rw 02:00)")
mesh_obj("speaker_grilles", "roof_detail", gv_, gf_, SPK_G, "estimated", SRC_BS + "; ledger bowl.speaker.*")
tube_obj("speaker_chains", "roof_detail", ch_, 0.04, STEEL, "estimated", SRC_BS)
# VIP glazing (BS18, BS19): warm light behind the glass, mullions dividing the band into boxes
gl = bpy.data.objects["vip_glass"]; gm = principled("vip_glass_lit", srgb("#27302F"), 0.08, 0.0)
gp = gm.node_tree.nodes["Principled BSDF"]; gp.inputs["Emission Color"].default_value = (*srgb("#FFD9A0"), 1)
gp.inputs["Emission Strength"].default_value = V("bowl.vip.glow_day"); gp.label = f"night:{V('bowl.vip.glow_night')}"
gl.data.materials.clear(); gl.data.materials.append(gm)
yv0, yv1 = V("bowl.band.vip_glass_y0"), V("bowl.band.vip_glass_y1")
columns("vip_mullions", lambda i: at(i, V("bowl.tier_middle.t0")) - 0.08, yv0, lambda i: yv1, V("bowl.vip.mullion_spacing"), 0.06,
        SRC_BS + "; ledger bowl.vip.mullion_spacing (estimated, BS19)")
# floodlight lenses (BS28): white lens faces under the heads, lit at night
lens = principled("night_floodlight_lens", srgb("#F2F2EE"), 0.2); lp_ = lens.node_tree.nodes["Principled BSDF"]
lp_.inputs["Emission Color"].default_value = (1, 1, 1, 1); lp_.inputs["Emission Strength"].default_value = 0.0; lp_.label = "night:40"
fo = bpy.data.objects["floodlights"]; fo.data.materials.append(lens)
for p in fo.data.polygons:
    if p.normal.z < -0.5: p.material_index = 1
# pitch apron (BS41, BS47): pale paved strip in front of the lowest rows, with a low kerb at the grass edge
APW = V("bowl.apron.width"); av, af = [], []
for i in range(N):
    ux, uz = dirs[i]; r0_ = rIn[i] - APW
    av += [B(ux * r0_, 0.09, uz * r0_), B(ux * rIn[i], 0.09, uz * rIn[i]), B(ux * r0_, 0.2, uz * r0_), B(ux * (r0_ + 0.25), 0.2, uz * (r0_ + 0.25))]
for i in range(N):
    a, b_ = 4 * i, 4 * ((i + 1) % N); af += [(a, b_, b_ + 1, a + 1), (a, a + 2, b_ + 2, b_), (a + 2, a + 3, b_ + 3, b_ + 2)]
mesh_obj("pitch_apron", "pitch", av, af, principled("apron_paving", srgb("#D1CEC5"), 0.85), "estimated", SRC_BS + "; ledger bowl.apron.width (BS41, BS47)")
# corner flags (BS40; Law 1: at least 1.5 m, not pointed)
fl_v, fl_f, poles_ = [], [], []
for sx in (-1, 1):
    for sz in (-1, 1):
        x, z = rot(sx * hw, sz * hl); poles_.append([B(x, YM, z), B(x, YM + V("bowl.corner_flag.h"), z)])
        b0 = len(fl_v); top_ = YM + V("bowl.corner_flag.h")
        fl_v += [B(x, top_, z), B(x + 0.45, top_ - 0.05, z), B(x + 0.45, top_ - 0.4, z), B(x, top_ - 0.35, z)]; fl_f.append((b0, b0 + 1, b0 + 2, b0 + 3))
tube_obj("corner_flag_poles", "pitch", poles_, 0.02, principled("flag_pole", srgb("#F4F3ED"), 0.4), "derived (Laws of the Game)", SRC_BS)
mesh_obj("corner_flags", "pitch", fl_v, fl_f, principled("corner_flag_yellow", srgb("#F0D84A"), 0.7), "estimated", SRC_BS + " (BS40, render only)")
# dugouts (BS44, render only, kept estimated): two generic shelters on the east touchline either side of halfway
# (east, so they stay clear of the C12 camera on the west touchline)
dv_, df_ = [], []
DL, DW, DH = V("bowl.dugout.length"), V("bowl.dugout.depth"), V("bowl.dugout.h")
for sg in (-1, 1):
    zc = sg * (V("bowl.dugout.offset_halfway") + DL / 2); xo = hw + V("bowl.dugout.from_touchline")
    box(dv_, df_, [B(*rot(xo + a_, zc + b_), y) for y in (YM, YM + DH) for a_, b_ in ((0, -DL / 2), (DW, -DL / 2), (DW, DL / 2), (0, DL / 2))])
mesh_obj("dugouts", "pitch", dv_, df_, principled("dugout_shell", srgb("#B7B9B8"), 0.4, 0.2), "estimated", SRC_BS + "; ledger bowl.dugout.* (BS44, render only)")
print("speakers:", nsp, "x", ne, "elements")


# ---------------------------------------------------------------- F. interior tour (detail sheet 05, IT01-IT13)
SRC_IT = "detail sheet 05_interior_tour.md (frames JWNowpO44rw 000945.200, 002144.300, 000735.433, 000154.067, 002320.200, 000131.700)"
t0m, t1m, y0m, y1m = (V(f"bowl.tier_middle.{k}") for k in ("t0", "t1", "y0", "y1"))
t0l, t1l, y1l = V("bowl.tier_lower.t0"), V("bowl.tier_lower.t1"), V("bowl.tier_lower.y1")
t0u_, y0u_ = V("bowl.tier_upper.t0"), V("bowl.tier_upper.y0")


def ring_strip(name, coll_name, r_fn, ya, yb, material, claim, src):
    v, f = [], []
    for i in range(N):
        ux, uz = dirs[i]; r = r_fn(i); v += [B(ux * r, ya, uz * r), B(ux * r, yb, uz * r)]
    for i in range(N):
        a, b_ = 2 * i, 2 * ((i + 1) % N); f.append((a, b_, b_ + 1, a + 1))
    return mesh_obj(name, coll_name, v, f, material, claim, src)


# IT13 concourse at the top of the lower tier (002144.300): open, grey floor, the existing white columns at its front,
# a dark back wall (the BS18 glazing reads as the open concourse in the tour frames; sheet 05 wins), dark ducts above
CONC_FLOOR = principled("concourse_floor", srgb(L["bowl.concourse.floor_hex"]["value"]), 0.8)
CONC_BACK = principled("concourse_back", srgb(L["bowl.concourse.back_hex"]["value"]), 0.9)
vg = bpy.data.objects.get("vip_glass")
if vg: vg.hide_render = True; vg["claim"] = "hidden: the tour frames show an open concourse here (IT13)"
r_cb = lambda i: at(i, t0m) + CD  # concourse back wall, under the middle tier
bw_v, bw_f = [], []
for i in range(N):
    ux, uz = dirs[i]; r = r_cb(i); bw_v += [B(ux * r, y1l, uz * r), B(ux * r, mid_under(i, r) + 0.6, uz * r)]
for i in range(N):
    a, b_ = 2 * i, 2 * ((i + 1) % N); bw_f.append((a, b_, b_ + 1, a + 1))
mesh_obj("concourse_back_wall", "bowl_detail", bw_v, bw_f, CONC_BACK, "estimated (IT13)", SRC_IT)
fl_v, fl_f = [], []
for i in range(N):
    ux, uz = dirs[i]; ra, rb = at(i, t1l), r_cb(i)
    fl_v += [B(ux * ra, y1l + 0.02, uz * ra), B(ux * rb, y1l + 0.02, uz * rb)]
for i in range(N):
    a, b_ = 2 * i, 2 * ((i + 1) % N); fl_f.append((a, b_, b_ + 1, a + 1))
mesh_obj("concourse_floor", "bowl_detail", fl_v, fl_f, CONC_FLOOR, "estimated (IT13)", SRC_IT)
DUCT = principled("concourse_duct", srgb("#2E3133"), 0.5, 0.3)
ducts = [[B(dirs[i % N][0] * at(i % N, t1l + (t0m - t1l) * fr_), y0m - dy, dirs[i % N][1] * at(i % N, t1l + (t0m - t1l) * fr_)) for i in range(N + 1)]
         for fr_, dy in ((0.9, 1.6), (1.3, 3.0))]
tube_obj("concourse_ducts", "bowl_detail", ducts, 0.35, DUCT, "estimated (IT13, services as simple dark ducts)", SRC_IT)

# IT04 glazed box band between the middle and upper tiers (000945.200, 000735.433): dark glass on band_middle, white
# columns, bowl.boxband.bays_per_aisle bays per upper-tier aisle block
BOX_GLASS = principled("boxband_glass", srgb("#1C2328"), 0.08, 0.0)
bm_o = bpy.data.objects.get("band_middle")
if bm_o: bm_o.data.materials.clear(); bm_o.data.materials.append(BOX_GLASS); bm_o["claim"] = "estimated (IT04 glazed box band)"
r_bm = lambda i: at(i, t1m) - 0.15
ring_strip("boxband_sill", "bowl_detail", r_bm, y1m, y1m + 0.35, WHITE_P, "estimated (IT04)", SRC_IT)
ring_strip("boxband_head", "bowl_detail", r_bm, V("bowl.band.upper_front_y1") - 0.45, V("bowl.band.upper_front_y1"), WHITE_P, "estimated (IT04)", SRC_IT)
ring_bm = [(dirs[i][0] * r_bm(i), dirs[i][1] * r_bm(i)) for i in range(N)]
circ_bm = sum(math.dist(ring_bm[i], ring_bm[(i + 1) % N]) for i in range(N))
n_bays = int(V("bowl.boxband.bays_per_aisle")) * n_ais
columns("boxband_columns", r_bm, y1m, lambda i: V("bowl.band.upper_front_y1"), circ_bm / n_bays, 0.22, SRC_IT + " (IT04)")

# IT03 portals (upper tier: one per aisle; middle tier: every bowl.portals.middle_every aisles) with blank sign panels
PORTAL = principled("portal_void", srgb("#141516"), 0.9); PANEL = principled("sign_panel_blank", srgb(L["bowl.portals.panel_hex"]["value"]), 0.5)
pv, pf, sv_, sf_, rv, rf = [], [], [], [], [], []
pw, ph = V("bowl.portals.width") / 2, V("bowl.portals.height")
def portal(a, t_mouth, y_floor, panel_below):
    i0 = int(round(a / (2 * math.pi) * N)) % N; ux, uz = dirs[i0]; tx, tz = -uz, ux; r = at(i0, t_mouth)
    def bx(lst_v, lst_f, w, y0_, y1_, r0_, r1_):
        cs = []
        for yy in (y0_, y1_):
            for rr_, ss in ((r0_, -w), (r0_, w), (r1_, w), (r1_, -w)): cs.append(B(ux * rr_ + tx * ss, yy, uz * rr_ + tz * ss))
        box(lst_v, lst_f, cs)
    bx(pv, pf, pw, y_floor, y_floor + ph, r - 0.05, r + 2.5)                         # dark mouth
    bx(rv, rf, pw + 0.35, y_floor + ph, y_floor + ph + 0.35, r - 0.15, r + 0.2)      # white head
    for sg in (-1, 1):                                                                # white jambs
        cs = []
        for yy in (y_floor, y_floor + ph):
            for rr_, ss in ((r - 0.15, sg * pw), (r - 0.15, sg * (pw + 0.35)), (r + 0.2, sg * (pw + 0.35)), (r + 0.2, sg * pw)):
                cs.append(B(ux * rr_ + tx * ss, yy, uz * rr_ + tz * ss))
        box(rv, rf, cs)
    if panel_below:  # blank sign panel on the tier front under the portal (no text)
        bx(sv_, sf_, pw + 0.6, y_floor - 1.35, y_floor - 0.25, r - 0.25, r - 0.15)
for a in ais_th:
    portal(a, t0u_ + 0.015, y0u_ + 0.3, True)
for k, a in enumerate(ais_th):
    if k % int(V("bowl.portals.middle_every")) == 0: portal(a, t1m - 0.03, y1m - ph - 0.6, False)
mesh_obj("portals", "bowl_detail", pv, pf, PORTAL, "estimated (IT03 portals, generic openings; no signage or egress meaning)", SRC_IT)
mesh_obj("portal_frames", "bowl_detail", rv, rf, WHITE_P, "estimated (IT03)", SRC_IT)
mesh_obj("portal_panels", "bowl_detail", sv_, sf_, PANEL, "estimated (IT03 blank panels; the frames' sign text is not copied)", SRC_IT)

# IT06 tier-front rails (aisle rails exist above), IT08 glass balustrade on the upper tier front (002320.200)
fr_rails = [[B(dirs[i % N][0] * (at(i % N, t0_) + 0.2), y0_ + 1.0, dirs[i % N][1] * (at(i % N, t0_) + 0.2)) for i in range(N + 1)]
            for t0_, y0_ in ((t0m, y0m), (t0u_, y0u_))]
tube_obj("tier_front_rails", "bowl_detail", fr_rails, 0.03, RAIL, "estimated (IT06)", SRC_IT)
GLASS_B = bpy.data.materials.new("balustrade_glass")
try: GLASS_B.use_nodes = True
except Exception: pass
pb = GLASS_B.node_tree.nodes["Principled BSDF"]; pb.inputs["Base Color"].default_value = (0.85, 0.92, 0.92, 1)
pb.inputs["Roughness"].default_value = 0.05
for nm_ in ("Transmission Weight", "Transmission"):
    if nm_ in pb.inputs: pb.inputs[nm_].default_value = 0.9; break
GLASS_B.diffuse_color = (0.8, 0.9, 0.9, 0.3)
ring_strip("upper_balustrade", "bowl_detail", lambda i: at(i, t0u_) + 0.1, y0u_, y0u_ + V("bowl.balustrade.h"), GLASS_B, "estimated (IT08)", SRC_IT)

# IT07 LED ribbon boards on the lower and middle tier fronts: emissive, off by day, matchday only (label "matchday:")
LED = bpy.data.materials.new("led_ribbon")
try: LED.use_nodes = True
except Exception: pass
lp = LED.node_tree.nodes["Principled BSDF"]; lp.inputs["Base Color"].default_value = (0.02, 0.02, 0.025, 1); lp.inputs["Roughness"].default_value = 0.3
lp.inputs["Emission Color"].default_value = (*srgb("#1FA0E0"), 1); lp.inputs["Emission Strength"].default_value = 0.0
lp.label = "matchday:%s" % L["bowl.led_ribbon.strength"]["value"]
LED.diffuse_color = (0.02, 0.02, 0.025, 1)
lh = V("bowl.led_ribbon.h")
ring_strip("led_ribbon_lower", "bowl_detail", lambda i: at(i, t1l) - 0.12, y1l + 0.25, y1l + 0.25 + lh, LED, "Visualization (IT07, matchday only)", SRC_IT)
ring_strip("led_ribbon_middle", "bowl_detail", lambda i: at(i, t0m) - 0.12, y0m - lh - 0.1, y0m - 0.1, LED, "Visualization (IT07, matchday only)", SRC_IT)

# IT10 roof underside lattice: diagonal members between neighbouring primaries (000154.067); light grey steel
diag = []
for k in range(KR):
    a_, b_ = prim[k], prim[(k + 1) % KR]
    for q in range(0, len(a_) - 4, 4): diag += [[a_[q], b_[q + 2]], [b_[q + 2], a_[q + 4]]]
tube_obj("roof_lattice_diagonals", "roof_detail", diag, 0.14, STEEL, "estimated (IT10)", SRC_IT)
print("interior pass: aisles", n_ais, "upper portals", n_ais, "middle portals", len(range(0, n_ais, int(V("bowl.portals.middle_every")))),
      "box bays", n_bays, "floodlights per bay", V("bowl.floodlights.per_bay"))

bpy.ops.wm.save_as_mainfile(filepath=str(ROOT / "blender/out/talanta_detail.blend"))
print("saved talanta_detail.blend")
