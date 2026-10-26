"""Interior for walkthrough chapters 3 and 4 (engineering/interior_plan_2026-10-26.md), on top of frozen_FK.blend.

Run from the repo root:
  blender -b --factory-startup --python-exit-code 1 --python blender/build_interior.py -- <part> [<part> ...]
  parts: concourse (part 1: the inner and outer concourse, their lights, the chapter 3 entry)
         stand (part 2: the seat model, aisle step nosings, rail posts and rail ends)
         roof (part 3: the secondary steel grid under the roof membrane)
The first part opens blender/out/frozen_FK.blend; later parts open blender/out/frozen_FK_interior.blend. The result is
saved as blender/out/frozen_FK_interior.blend. frozen_FK.blend is not changed (the twin export and the bakes use it).
All new objects go in interior_* collections, which export_web.py does not read. Old objects that the interior replaces
are hidden here only (hide_render), with a claim.

Rule 8: no exits, exit signs, signs with text, turnstiles, gates, CCTV, control or security rooms, the player tunnel or
back-of-house rooms. The concourse is generic where no frame shows it. Every dimension is estimated (by eye from the
frames in the plan, or typical practice); the facts table is in the plan.
"""
import csv, json, math, sys, time
from pathlib import Path
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PARTS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else ["concourse"]
L = {r["name"]: r for r in csv.DictReader(open(ROOT / "gis/parameter_ledger.csv"))}
V = lambda k: float(L[k + "_blockout"]["value"]) if k + "_blockout" in L else float(L[k]["value"])
G = json.loads((ROOT / "blender/out/bowl_rings.json").read_text())
N, PAD = G["N"], G["pad"]
rIn, rBack = np.array(G["rIn"]), np.array(G["rBack"])
TH = 2 * math.pi * np.arange(N) / N  # bowl_rings dirs are at uniform angles from east (app x) towards south (app z)
OUT = ROOT / "blender/out/frozen_FK_interior.blend"
SRC = ROOT / "blender/out/frozen_FK.blend"
bpy.ops.wm.open_mainfile(filepath=str(OUT if OUT.exists() and "concourse" not in PARTS else SRC))
scene = bpy.context.scene
B = lambda x, y, z: (x, -z, y + PAD)  # app frame (pad-relative height) -> Blender
LOG = {"parts": PARTS, "objects": {}}


def rof(arr, th):
    """Radius of a ring array at angle th (periodic linear interpolation)."""
    return float(np.interp(th % (2 * math.pi), np.append(TH, 2 * math.pi), np.append(arr, arr[0])))


def coll(name):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name); scene.collection.children.link(c)
    return c


def srgb(h):
    return tuple(((int(h[i:i + 2], 16) / 255 + 0.055) / 1.055) ** 2.4 for i in (1, 3, 5))


def mat(name, hexc, rough=0.6, metal=0.0, joints=None, emission=None, bump=None):
    """Principled material. joints=(joint hex, u size m, v size m, joint m): a UV brick pattern in metres (panel or
    tile joints). emission=(strength, hex). bump=wave scale for a corrugated roller shutter (UV v in metres)."""
    m = bpy.data.materials.get(name)
    if m: return m
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*srgb(hexc), 1); p.inputs["Roughness"].default_value = rough
    p.inputs["Metallic"].default_value = metal; m.diffuse_color = (*srgb(hexc), 1)
    if joints:
        jh, su, sv, jw = joints
        uv = nt.nodes.new("ShaderNodeUVMap"); mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (1 / su, 1 / sv, 1)
        br = nt.nodes.new("ShaderNodeTexBrick")
        br.inputs["Color1"].default_value = (*srgb(hexc), 1); br.inputs["Color2"].default_value = (*srgb(hexc), 1)
        br.inputs["Mortar"].default_value = (*srgb(jh), 1); br.inputs["Scale"].default_value = 1.0
        br.inputs["Mortar Size"].default_value = jw / max(su, sv); br.inputs["Brick Width"].default_value = 1.0
        br.inputs["Row Height"].default_value = 1.0; br.offset = 0.0; br.squash = 1.0
        nt.links.new(uv.outputs["UV"], mp.inputs["Vector"]); nt.links.new(mp.outputs["Vector"], br.inputs["Vector"])
        nt.links.new(br.outputs["Color"], p.inputs["Base Color"])
        bm = nt.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = 0.3; bm.inputs["Distance"].default_value = 0.002
        nt.links.new(br.outputs["Fac"], bm.inputs["Height"]); nt.links.new(bm.outputs["Normal"], p.inputs["Normal"])
    if bump:
        uv = nt.nodes.new("ShaderNodeUVMap"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); mth = nt.nodes.new("ShaderNodeMath")
        mth.operation = "SINE"; mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; mul.inputs[1].default_value = bump
        nt.links.new(uv.outputs["UV"], sep.inputs["Vector"]); nt.links.new(sep.outputs["Y"], mul.inputs[0]); nt.links.new(mul.outputs[0], mth.inputs[0])
        bm = nt.nodes.new("ShaderNodeBump"); bm.inputs["Strength"].default_value = 0.6; bm.inputs["Distance"].default_value = 0.01
        nt.links.new(mth.outputs[0], bm.inputs["Height"]); nt.links.new(bm.outputs["Normal"], p.inputs["Normal"])
    if emission:
        p.inputs["Emission Color"].default_value = (*srgb(emission[1]), 1); p.inputs["Emission Strength"].default_value = emission[0]
    return m


def mesh_obj(name, cname, verts, faces, material, claim, uvs=None, smooth=False):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces)
    if uvs is not None:
        lay = me.uv_layers.new(name="UVMap")
        for lp in me.loops: lay.data[lp.index].uv = uvs[lp.vertex_index]
    me.validate(); me.update()
    if smooth:
        for p in me.polygons: p.use_smooth = True
    mats = material if isinstance(material, list) else [material]
    o = bpy.data.objects.new(name, me); coll(cname).objects.link(o)
    for m in mats: o.data.materials.append(m)
    o["claim"] = claim; o["sources"] = "engineering/interior_plan_2026-10-26.md (facts table)"
    LOG["objects"][name] = len(faces)
    return o


def tube_obj(name, cname, paths, r, material, claim, res=2):
    cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = res; cu.use_fill_caps = True
    for pts in paths:
        sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
        for k, v in enumerate(pts): sp.points[k].co = (*v, 1)
    o = bpy.data.objects.new(name, cu); coll(cname).objects.link(o); o.data.materials.append(material)
    o["claim"] = claim; LOG["objects"][name] = len(paths)
    return o


class Ring:
    """A ring of radius r_fn(th), sampled by arc length (step metres) for placing things at metre spacing."""
    def __init__(self, r_fn, step=0.25):
        th = np.linspace(0, 2 * math.pi, 4 * N + 1); r = np.array([r_fn(t) for t in th])
        x, z = np.cos(th) * r, np.sin(th) * r
        s = np.concatenate([[0], np.cumsum(np.hypot(np.diff(x), np.diff(z)))])
        self.th, self.s, self.length, self.r_fn = th, s, s[-1], r_fn
    def theta(self, s):
        return float(np.interp(s % self.length, self.s, self.th))
    def s_of(self, th):
        return float(np.interp(th % (2 * math.pi), self.th, self.s))
    def frame(self, s, r_fn=None):
        """(point x, z), unit tangent (towards larger s), unit outward normal, at arc length s; on r_fn if given."""
        f = r_fn or self.r_fn; t0, t1 = self.theta(s - 0.2), self.theta(s + 0.2); t = self.theta(s)
        if t1 < t0: t1 += 2 * math.pi
        pa = np.array([math.cos(t0) * f(t0), math.sin(t0) * f(t0)]); pb = np.array([math.cos(t1) * f(t1), math.sin(t1) * f(t1)])
        tg = (pb - pa) / np.linalg.norm(pb - pa); nn = np.array([tg[1], -tg[0]])
        p = np.array([math.cos(t) * f(t), math.sin(t) * f(t)])
        if np.dot(nn, p) < 0: nn = -nn
        return p, tg, nn


def box_local(v, f, uv, p, tg, nn, t0, t1, n0, n1, y0, y1):
    """Append a box in a local frame (tangent t, outward normal n, height y), with UVs in metres."""
    b = len(v)
    pts = [(t0, n0, y0), (t1, n0, y0), (t1, n1, y0), (t0, n1, y0), (t0, n0, y1), (t1, n0, y1), (t1, n1, y1), (t0, n1, y1)]
    for (t, n, y) in pts:
        q = p + tg * t + nn * n; v.append(B(q[0], y, q[1]))
    # UVs by face orientation are approximated per vertex: (t + n, y) keeps metre scale on the side faces
    for (t, n, y) in pts: uv.append((t + n, y))
    f += [(b, b + 3, b + 2, b + 1), (b + 4, b + 5, b + 6, b + 7), (b, b + 1, b + 5, b + 4), (b + 1, b + 2, b + 6, b + 5),
          (b + 2, b + 3, b + 7, b + 6), (b + 3, b, b + 4, b + 7)]


def ring_wall(v, f, uv, ring, r_fn, y0, y1, gaps=(), step=0.5, flip=False):
    """Vertical wall strip on r_fn from y0 to y1, UV (arc m, height m), leaving out arc ranges in gaps [(s0, s1)]."""
    s = np.arange(0, ring.length + step / 2, step)
    keep = lambda a, b_: all(b_ <= g0 or a >= g1 for g0, g1 in gaps)
    for k in range(len(s) - 1):
        a, b_ = s[k], s[k + 1]
        if not keep(a, b_): continue
        ta, tb = ring.theta(a), ring.theta(b_)
        b0 = len(v)
        for (tt, ss) in ((ta, a), (tb, b_)):
            r = r_fn(tt); x, z = math.cos(tt) * r, math.sin(tt) * r
            v += [B(x, y0, z), B(x, y1, z)]; uv += [(ss, y0), (ss, y1)]
        f.append((b0, b0 + 1, b0 + 3, b0 + 2) if not flip else (b0, b0 + 2, b0 + 3, b0 + 1))


def ring_band(v, f, uv, ring, ra_fn, rb_fn, y_fn, step=1.0, gaps=(), flip=False):
    """Horizontal band between two rings at height y_fn(th) (floor or soffit), UV in metres (arc m, radial m)."""
    s = np.arange(0, ring.length + step / 2, step)
    keep = lambda a, b_: all(b_ <= g0 or a >= g1 for g0, g1 in gaps)
    for k in range(len(s) - 1):
        a, b_ = s[k], s[k + 1]
        if not keep(a, b_): continue
        b0 = len(v)
        for (tt, ss) in ((ring.theta(a), a), (ring.theta(b_), b_)):
            ra, rb = ra_fn(tt), rb_fn(tt); y = y_fn(tt)
            v += [B(math.cos(tt) * ra, y, math.sin(tt) * ra), B(math.cos(tt) * rb, y, math.sin(tt) * rb)]
            uv += [(ss, 0.0), (ss, rb - ra)]
        f.append((b0, b0 + 2, b0 + 3, b0 + 1) if not flip else (b0, b0 + 1, b0 + 3, b0 + 2))


# ---------------------------------------------------------------- bowl section values (ledger, estimated)
at = lambda th, t: rof(rIn, th) + (rof(rBack, th) - rof(rIn, th)) * t
t1l, yF = V("bowl.tier_lower.t1"), V("bowl.tier_lower.y1")  # top of the lower tier = concourse floor (IF74)
t0m, t1m, y0m, y1m = (V(f"bowl.tier_middle.{k}") for k in ("t0", "t1", "y0", "y1"))
CD = V("bowl.concourse.depth")
H_IN = 4.4    # inner concourse clear height to the soffit (estimated, 002144.300: about 2.5 person heights)
H_OUT = 4.6   # outer concourse height to the slat ceiling (estimated, 000404.000)
D_OUT = 11.0  # outer concourse depth behind the back wall (estimated, generic)
WALL_T = 0.4  # back wall thickness (estimated)
r_front = lambda th: at(th, t1l)            # concourse front edge (back of the lower tier)
r_wall = lambda th: at(th, t0m) + CD        # concourse back wall (existing line, IT13)
r_out = lambda th: r_wall(th) + WALL_T / 2 + D_OUT  # outer wall of the outer concourse


def mid_under(th, r):
    """Height (pad-relative) of the middle tier's underside over radius r, less a 0.6 m slab (as build_bowl_detail)."""
    t = (r - rof(rIn, th)) / (rof(rBack, th) - rof(rIn, th))
    return y0m + (y1m - y0m) * min(max((t - t0m) / (t1m - t0m), 0), 1) - 0.6


# lower-tier aisle angles: every bowl.aisle.spacing m along the front row (as build_bowl_detail)
front = Ring(lambda th: rof(rIn, th))
n_ais = int(round(front.length / V("bowl.aisle.spacing")))
AIS = [front.theta((k + 0.5) * front.length / n_ais) for k in range(n_ais)]
# chapter 3 entry: the aisle nearest 60 deg from east towards south (south-east side, about 120 deg from the west
# centre line, far from the tunnel and VIP placeholders on the west); entries at every 2nd aisle round the ring
TH_E = min(AIS, key=lambda a: abs((a - math.radians(60) + math.pi) % (2 * math.pi) - math.pi))
k_e = AIS.index(TH_E)
ENTRIES = [AIS[k] for k in range(n_ais) if (k - k_e) % 2 == 0]

# VIP stand (west): its lounge glazing stands at the concourse front over the VIP arc; keep the soffit out of it
vip = bpy.data.objects.get("vip_lounge_glazing")
VIP_TH = None
if vip:
    ang = [math.atan2(-(vip.matrix_world @ vv.co).y, (vip.matrix_world @ vv.co).x) % (2 * math.pi) for vv in vip.data.vertices]
    c0 = math.atan2(np.mean(np.sin(ang)), np.mean(np.cos(ang))) % (2 * math.pi)
    half = max(abs((a - c0 + math.pi) % (2 * math.pi) - math.pi) for a in ang) + math.radians(1.5)
    VIP_TH = (c0, half)
in_vip = lambda th: VIP_TH is not None and abs((th - VIP_TH[0] + math.pi) % (2 * math.pi) - math.pi) < VIP_TH[1]


def part_concourse():
    t0 = time.time()
    C_IN, C_OUT, C_LT, C_EN = "interior_concourse", "interior_outer_concourse", "interior_concourse_lights", "interior_entry"
    FLOOR = mat("int_floor_polished", "#8E9092", 0.22, joints=("#6E7072", 1.2, 1.2, 0.006))
    WALL = mat("int_wall_panel", "#E6E4DE", 0.55, joints=("#B9B7B1", 1.2, 2.4, 0.01))
    SOFFIT = mat("int_soffit_concrete", "#B4B4B0", 0.85)
    FASCIA = mat("int_fascia_concrete", "#C9CACB", 0.8)
    SLAT = mat("int_ceiling_slat", "#2B2D30", 0.5, 0.2)
    PLENUM = mat("int_plenum_dark", "#111214", 0.9)
    LED = mat("int_led_strip", "#FFFFFF", 0.4, emission=(18.0, "#FFF1DE"))
    DUCT = mat("int_duct", "#3A3D40", 0.45, 0.4)
    COLW = mat("int_column_white", "#E8E8E4", 0.45)
    SHUT = mat("int_shutter", "#A9ADB0", 0.4, 0.7, bump=2 * math.pi / 0.08)
    PANEL = bpy.data.materials.get("sign_panel_blank") or mat("int_panel_blank", L["bowl.portals.panel_hex"]["value"], 0.5)
    ring_w = Ring(r_wall)
    s_ent = [ring_w.s_of(a) for a in ENTRIES]
    EW, EH = 3.0, 3.2  # entry opening width and height (estimated)
    gaps = [(s - EW / 2, s + EW / 2) for s in s_ent]
    s_e = ring_w.s_of(TH_E)
    vip_gap = []
    if VIP_TH:
        sa, sb = ring_w.s_of(VIP_TH[0] - VIP_TH[1]), ring_w.s_of(VIP_TH[0] + VIP_TH[1])
        vip_gap = [(sa, sb)] if sa < sb else [(sa, ring_w.length + 1), (-1, sb)]

    # old objects that the interior replaces (interior blend only)
    for nm, why in (("concourse_back_wall", "replaced by int_back_wall (entries, pale panels)"),
                    ("concourse_ducts", "replaced by int_ducts under the new concourse soffit"),
                    ("concourse_floor", "replaced by int_floor_inner (polished, joints)")):
        o = bpy.data.objects.get(nm)
        if o: o.hide_render = True; o.hide_viewport = True; o["claim"] = "hidden in frozen_FK_interior.blend: " + why

    # inner concourse (open to the bowl, 002144.300): polished floor, soffit at H_IN, a pale fascia from the soffit up to
    # the middle tier underside at the front edge, exposed ducts and cable trays under the soffit
    v, f, uv = [], [], []
    ring_band(v, f, uv, ring_w, r_front, lambda th: r_wall(th) - WALL_T / 2, lambda th: yF + 0.02, step=1.0)
    mesh_obj("int_floor_inner", C_IN, v, f, FLOOR, "estimated (IT13, 002144.300; polished grey, IF72)", uv)
    v, f, uv = [], [], []
    ring_band(v, f, uv, ring_w, r_front, lambda th: r_wall(th) - WALL_T / 2, lambda th: yF + H_IN, step=1.0, gaps=vip_gap, flip=True)
    mesh_obj("int_soffit_inner", C_IN, v, f, SOFFIT, "estimated (002144.300: low concrete soffit)", uv)
    v, f, uv = [], [], []
    s = np.arange(0, ring_w.length + 0.5, 1.0)
    for k in range(len(s) - 1):
        a, b_ = s[k], s[k + 1]
        if any(not (b_ <= g0 or a >= g1) for g0, g1 in vip_gap): continue
        b0 = len(v)
        for ss in (a, b_):
            tt = ring_w.theta(ss); r = r_front(tt); x, z = math.cos(tt) * r, math.sin(tt) * r
            v += [B(x, yF + H_IN - 0.05, z), B(x, mid_under(tt, r) + 0.6, z)]; uv += [(ss, 0), (ss, mid_under(tt, r) + 0.6 - yF - H_IN)]
        f.append((b0, b0 + 2, b0 + 3, b0 + 1))
    mesh_obj("int_fascia_front", C_IN, v, f, FASCIA, "estimated (002144.300: the concrete edge over the concourse front)", uv)
    ducts, trays = [], []
    for fr, dy, rr in ((0.35, 0.45, 0.32), (0.7, 0.55, 0.25)):
        pts = []
        for ss in np.arange(0, ring_w.length + 2, 2.0):
            tt = ring_w.theta(ss)
            if in_vip(tt):
                if len(pts) > 1: ducts.append((pts, rr))
                pts = []; continue
            r = r_front(tt) + (r_wall(tt) - r_front(tt)) * fr; pts.append(B(math.cos(tt) * r, yF + H_IN - dy - rr, math.sin(tt) * r))
        if len(pts) > 1: ducts.append((pts, rr))
    for rr in (0.32, 0.25):
        tube_obj(f"int_ducts_{int(rr * 100)}", C_IN, [p for p, r_ in ducts if r_ == rr], rr, DUCT, "estimated (002144.300: exposed services, generic)", res=3)
    # linear fittings under the soffit (emission strips) at 0.5 of the depth
    v, f, uv = [], [], []
    for ss in np.arange(1.0, ring_w.length, 6.0):
        tt = ring_w.theta(ss)
        if in_vip(tt): continue
        p, tg, nn = ring_w.frame(ss, lambda th: r_front(th) + (r_wall(th) - r_front(th)) * 0.5)
        box_local(v, f, uv, p, tg, nn, -1.4, 1.4, -0.06, 0.06, yF + H_IN - 0.08, yF + H_IN - 0.02)
    mesh_obj("int_inner_fittings", C_LT, v, f, LED, "estimated (generic linear fittings)", uv)

    # back wall with the entries (pale panels on both faces, reveals at the openings)
    v, f, uv = [], [], []
    ring_wall(v, f, uv, ring_w, lambda th: r_wall(th) - WALL_T / 2, yF, yF + H_OUT + 0.7, gaps=gaps, flip=True)
    ring_wall(v, f, uv, ring_w, lambda th: r_wall(th) + WALL_T / 2, yF, yF + H_OUT + 0.7, gaps=gaps)
    for se in s_ent:  # lintel and reveals at each entry
        p, tg, nn = ring_w.frame(se)
        box_local(v, f, uv, p, tg, nn, -EW / 2, EW / 2, -WALL_T / 2, WALL_T / 2, yF + EH, yF + H_OUT + 0.7)
        for sgn in (-1, 1):
            box_local(v, f, uv, p, tg, nn, sgn * EW / 2 - (0.02 if sgn > 0 else 0), sgn * EW / 2 + (0.02 if sgn < 0 else 0),
                      -WALL_T / 2, WALL_T / 2, yF, yF + EH)
    mesh_obj("int_back_wall", C_IN, v, f, WALL, "estimated (IT13 back wall line; pale panels, IF52/IF72)", uv)
    # blank panels over the entries on the bowl side (no text)
    v, f, uv = [], [], []
    for se in s_ent:
        p, tg, nn = ring_w.frame(se)
        box_local(v, f, uv, p, tg, nn, -1.2, 1.2, -WALL_T / 2 - 0.04, -WALL_T / 2, yF + EH + 0.25, yF + EH + 0.75)
    mesh_obj("int_entry_panels", C_IN, v, f, PANEL, "estimated (blank panels, no text; IF16)", uv)

    # outer concourse (enclosed, 000404.000): polished floor, dark slat ceiling with LED lines, white round columns,
    # pale outer wall with closed kiosk shutters, a dark plenum above the slats, the ceiling closing the wall tops
    v, f, uv = [], [], []
    ring_band(v, f, uv, ring_w, lambda th: r_wall(th) + WALL_T / 2, r_out, lambda th: yF + 0.02, step=1.0)
    mesh_obj("int_floor_outer", C_OUT, v, f, FLOOR, "estimated (000404.000, IF72)", uv)
    v, f, uv = [], [], []
    ring_band(v, f, uv, ring_w, lambda th: r_wall(th) + WALL_T / 2, r_out, lambda th: yF + H_OUT + 0.65, step=2.0, flip=True)
    ring_band(v, f, uv, ring_w, r_front, lambda th: r_wall(th) - WALL_T / 2, lambda th: yF + H_IN + 0.02, step=2.0, gaps=vip_gap)
    mesh_obj("int_plenum", C_OUT, v, f, PLENUM, "estimated (dark void above the slats)", uv)
    v, f, uv = [], [], []
    ring_mid = Ring(lambda th: r_wall(th) + WALL_T / 2 + D_OUT / 2)
    for ss in np.arange(0.2, ring_mid.length, 0.40):
        p, tg, nn = ring_mid.frame(ss)
        box_local(v, f, uv, p, tg, nn, -0.05, 0.05, -D_OUT / 2, D_OUT / 2, yF + H_OUT, yF + H_OUT + 0.30)
    mesh_obj("int_ceiling_slats", C_OUT, v, f, SLAT, "estimated (000404.000, 002600.000: dark slats, IF72)", uv)
    v, f, uv = [], [], []
    for fr in (0.22, 0.5, 0.78):
        rr = lambda th, fr=fr: r_wall(th) + WALL_T / 2 + D_OUT * fr
        ring_l = Ring(rr)
        for ss in np.arange(0, ring_l.length, 1.0):
            p, tg, nn = ring_l.frame(ss + 0.5)
            box_local(v, f, uv, p, tg, nn, -0.5, 0.5, -0.04, 0.04, yF + H_OUT - 0.05, yF + H_OUT - 0.01)
    mesh_obj("int_led_lines", C_LT, v, f, LED, "estimated (000404.000: long linear LED lines under the slats)", uv)
    paths = []
    ring_c = Ring(lambda th: r_wall(th) + WALL_T / 2 + D_OUT * 0.62)
    for ss in np.arange(4.5, ring_c.length, 9.0):
        if min(abs(ss - ring_c.s_of(a)) for a in ENTRIES) < 2.5: continue  # keep the entry axes clear
        p, tg, nn = ring_c.frame(ss); paths.append([B(p[0], yF, p[1]), B(p[0], yF + H_OUT, p[1])])
    tube_obj("int_columns_outer", C_OUT, paths, 0.45, COLW, "estimated (000404.000: white round columns)", res=4)
    ring_o = Ring(r_out)
    v, f, uv = [], [], []
    k_gaps = [(ss - 3.0, ss + 3.0) for ss in np.arange(12.0, ring_o.length - 6, 24.0)]
    ring_wall(v, f, uv, ring_o, r_out, yF, yF + H_OUT + 0.7, gaps=k_gaps, flip=True)
    sv, sf, suv = [], [], []
    for g0, g1 in k_gaps:  # kiosk bays: a 0.3 m recess with a closed roller shutter (no text), a pale head panel above
        p, tg, nn = ring_o.frame((g0 + g1) / 2, r_out)
        box_local(v, f, uv, p, tg, nn, -3.0, 3.0, 0.0, 0.3, yF + 3.0, yF + H_OUT + 0.7)
        for sgn in (-1, 1):
            box_local(v, f, uv, p, tg, nn, sgn * 3.0 - 0.02, sgn * 3.0 + 0.02, 0.0, 0.3, yF, yF + 3.0)
        box_local(sv, sf, suv, p, tg, nn, -2.98, 2.98, 0.28, 0.32, yF, yF + 3.0)
    mesh_obj("int_outer_wall", C_OUT, v, f, WALL, "estimated (generic: pale panels; IF52)", uv)
    mesh_obj("int_kiosk_shutters", C_OUT, sv, sf, SHUT, "estimated (cyNgbyZv6BM 001002.000: closed roller shutter; generic kiosk fronts, no text)", suv)

    # the chapter 3 entry passage: a 5 m block behind the back wall with the opening through it, wall lights
    v, f, uv = [], [], []
    p, tg, nn = ring_w.frame(s_e)
    for sgn in (-1, 1):
        box_local(v, f, uv, p, tg, nn, sgn * EW / 2 if sgn > 0 else -EW / 2 - 2.0, EW / 2 + 2.0 if sgn > 0 else -EW / 2,
                  WALL_T / 2, WALL_T / 2 + 5.0, yF, yF + H_OUT + 0.7)
    box_local(v, f, uv, p, tg, nn, -EW / 2, EW / 2, WALL_T / 2, WALL_T / 2 + 5.0, yF + EH, yF + H_OUT + 0.7)
    mesh_obj("int_entry_block", C_EN, v, f, WALL, "estimated (generic entry passage, 3.0 m x 3.2 m x 5.4 m)", uv)
    v, f, uv = [], [], []
    for sgn in (-1, 1):
        box_local(v, f, uv, p, tg, nn, sgn * (EW / 2 - 0.03) - 0.02, sgn * (EW / 2 - 0.03) + 0.02, 0.0, WALL_T / 2 + 5.0, yF + 2.6, yF + 2.66)
    mesh_obj("int_entry_lights", C_LT, v, f, LED, "estimated (wall light lines in the passage)", uv)
    # Cycles area lights: the outer concourse LED lines and the inner fittings within 60 m of the entry, the passage
    lc = coll(C_LT); n_l = 0
    def area(name, xyz, size, size_y, rot_z, power, warm=(1.0, 0.95, 0.88)):
        nonlocal n_l
        ld = bpy.data.lights.new(name, "AREA"); ld.shape = "RECTANGLE"; ld.size, ld.size_y = size, size_y
        ld.energy = power; ld.color = warm
        o = bpy.data.objects.new(name, ld); o.location = xyz; o.rotation_euler = (0, 0, rot_z); lc.objects.link(o)
        o["claim"] = "estimated (lights for the LED lines)"; n_l += 1
    for fr in (0.22, 0.5, 0.78):
        rr = lambda th, fr=fr: r_wall(th) + WALL_T / 2 + D_OUT * fr
        ring_l = Ring(rr); s0 = ring_l.s_of(TH_E)
        for ds in np.arange(-60, 60.1, 3.0):
            pp, tg2, nn2 = ring_l.frame(s0 + ds)
            area(f"int_area_out_{fr}_{int(ds)}", B(pp[0], yF + H_OUT - 0.08, pp[1]), 0.08, 2.9, math.atan2(-tg2[1], tg2[0]) + math.pi / 2, 45.0)
    ring_f = Ring(lambda th: r_front(th) + (r_wall(th) - r_front(th)) * 0.5); s0 = ring_f.s_of(TH_E)
    for ss in np.arange(1.0, ring_f.length, 6.0):
        if abs(((ss - s0) + ring_f.length / 2) % ring_f.length - ring_f.length / 2) > 60: continue
        pp, tg2, nn2 = ring_f.frame(ss)
        area(f"int_area_in_{int(ss)}", B(pp[0], yF + H_IN - 0.1, pp[1]), 0.12, 2.8, math.atan2(-tg2[1], tg2[0]) + math.pi / 2, 40.0)
    for sgn in (-1, 1):
        q = p + tg * sgn * (EW / 2 - 0.1) + nn * (WALL_T / 2 + 2.5)
        area(f"int_area_entry_{sgn}", B(q[0], yF + 2.63, q[1]), 0.06, 5.0, math.atan2(-tg[1], tg[0]), 25.0)
    LOG["area_lights"] = n_l
    LOG["entry"] = {"theta_deg": round(math.degrees(TH_E), 2), "aisle": k_e, "of_aisles": n_ais, "entries": len(ENTRIES),
                    "wall_point_app_xz": [round(float(x), 2) for x in p], "normal_out": [round(float(x), 3) for x in nn],
                    "floor_y_pad": yF, "pad": PAD, "r_front": round(r_front(TH_E), 2), "r_wall": round(r_wall(TH_E), 2),
                    "r_out": round(r_out(TH_E), 2)}
    LOG["vip_arc_deg"] = [round(math.degrees(VIP_TH[0]), 1), round(math.degrees(VIP_TH[1]), 1)] if VIP_TH else None
    LOG["concourse_s"] = round(time.time() - t0, 1)


def seat_mesh(name):
    """Moulded seat shell (about 600 triangles), front towards +Y, origin on the tread: a lofted side profile across
    the width with a dished back and a rolled top edge, a solid offset for thickness, a steel pedestal and foot plate,
    a blank number plate on the back. Shape estimated (frames 002714.067, 002746.867); size from the ledger."""
    import bmesh
    from mathutils import Vector
    sw, ph = V("bowl.seat.width") / 2, V("bowl.seat.pan_h")
    prof = [(0.215, ph - 0.035), (0.225, ph - 0.005), (0.200, ph + 0.012), (0.120, ph + 0.004), (0.020, ph - 0.004),
            (-0.090, ph + 0.004), (-0.170, ph + 0.030), (-0.205, ph + 0.090), (-0.225, ph + 0.200), (-0.245, ph + 0.320),
            (-0.258, ph + 0.400), (-0.250, ph + 0.425), (-0.228, ph + 0.428)]  # (y, z) from the front lip to the top roll
    nx_ = 11
    bm = bmesh.new(); rows = []
    for j in range(nx_):
        u = -1 + 2 * j / (nx_ - 1); x = u * sw
        dish = 0.028 * u * u  # the back curves forwards at the sides
        rows.append([bm.verts.new((x * (0.94 if k < 6 else 1.0), y + (dish if k >= 6 else 0.4 * dish * (k / 6)), z - 0.012 * (1 - u * u) * (k < 6)))
                     for k, (y, z) in enumerate(prof)])
    for j in range(nx_ - 1):
        for k in range(len(prof) - 1):
            bm.faces.new((rows[j][k], rows[j + 1][k], rows[j + 1][k + 1], rows[j][k + 1]))
    shell = list(bm.faces)
    r = bmesh.ops.solidify(bm, geom=shell, thickness=0.012)
    for fc in bm.faces: fc.material_index = 0; fc.smooth = True
    def cube(cx, cy, cz, hx, hy, hz, mi):
        g = bmesh.ops.create_cube(bm, size=1.0)
        for v in g["verts"]: v.co = Vector((v.co.x * 2 * hx + cx, v.co.y * 2 * hy + cy, v.co.z * 2 * hz + cz))
        for fc in {fc for v in g["verts"] for fc in v.link_faces}: fc.material_index = mi; fc.smooth = False
    cube(0, -0.06, (ph - 0.03) / 2, 0.025, 0.035, (ph - 0.03) / 2, 2)   # pedestal
    cube(0, -0.06, 0.006, 0.07, 0.07, 0.006, 2)                         # foot plate
    cube(0, 0.0, ph - 0.03, 0.17, 0.02, 0.012, 2)                       # pan bracket
    cube(0, -0.262, ph + 0.33, 0.035, 0.004, 0.018, 1)                  # number plate (blank)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    return me


def part_stand():
    t0 = time.time()
    C_ST = "interior_stand"
    NOSE = mat("int_step_nosing", "#DCDDD8", 0.6)
    STEEL = bpy.data.materials.get("rail_steel") or mat("int_rail_steel", "#8C8E90", 0.35, 0.8)
    PLATE = mat("int_seat_plate", "#E9E9E6", 0.4)
    # 1. seat model: the seats object instances seat_proto, so its mesh is replaced (same origin and front)
    so = bpy.data.objects.get("seat_proto")
    if so:
        old = so.data; seatm = old.materials[0] if old.materials else None
        me = seat_mesh("seat_proto_v2")
        for m in (seatm, PLATE, STEEL): me.materials.append(m)
        old.name = "seat_proto_v1"; old.use_fake_user = True
        so.data = me; so["claim"] = "estimated seat shell v2 (interior part 2); seat_proto_v1 is the 36-triangle block seat"
        LOG["seat_triangles"] = sum(len(p.vertices) - 2 for p in me.polygons)
    # 2. aisle step nosings and 3. handrail posts and bent rail ends (as build_bowl_detail: aisles on the front-ring
    #    angles, rounded to the ring directions)
    dirs = G["dirs"]
    front_ = [(dirs[i][0] * rIn[i], dirs[i][1] * rIn[i]) for i in range(N)]
    arcf = np.concatenate([[0], np.cumsum([math.dist(front_[i], front_[(i + 1) % N]) for i in range(N)])])
    ais_th = [2 * math.pi * np.interp((k + 0.5) * arcf[-1] / n_ais, arcf, np.arange(N + 1)) / N for k in range(n_ais)]
    at_i = lambda i, t: rIn[i] + (rBack[i] - rIn[i]) * t
    w = V("bowl.aisle.width") / 2
    v, f, uv, posts, ends = [], [], [], [], []
    for tn in ("lower", "middle", "upper"):
        t0_, t1_, y0_, y1_, rows = (V(f"bowl.tier_{tn}.{k}") for k in ("t0", "t1", "y0", "y1", "rows")); rows = int(rows)
        for a in ais_th:
            i0 = int(round(a / (2 * math.pi) * N)) % N; ux, uz = dirs[i0]; tx, tz = -uz, ux
            p = np.array([0.0, 0.0]); tg = np.array([tx, tz]); nn = np.array([ux, uz])
            for k in range(rows):
                ta, tb = t0_ + (t1_ - t0_) * k / rows, t0_ + (t1_ - t0_) * (k + 1) / rows
                ya, yb = y0_ + (y1_ - y0_) * k / rows, y0_ + (y1_ - y0_) * (k + 1) / rows
                for rr, yy in ((at_i(i0, ta), ya), ((at_i(i0, ta) + at_i(i0, tb)) / 2, ya + (yb - ya) / 2)):
                    box_local(v, f, uv, p, tg, nn, -w, w, rr, rr + 0.06, yy, yy + 0.008)
                if k % 2 == 0:
                    rr = at_i(i0, ta) + 0.1; posts.append([B(ux * rr, ya, uz * rr), B(ux * rr, ya + 0.9, uz * rr)])
            if tn == "lower":  # bent end of the centre rail at the aisle head: on over the top step, down to the floor
                rt, yt = at_i(i0, t1_), y1_
                ends.append([B(ux * rt, yt + 0.9, uz * rt), B(ux * (rt + 0.5), yt + 0.9, uz * (rt + 0.5)),
                             B(ux * (rt + 0.75), yt + 0.75, uz * (rt + 0.75)), B(ux * (rt + 0.8), yt, uz * (rt + 0.8))])
    mesh_obj("int_step_nosings", C_ST, v, f, NOSE, "estimated (pale nosing on each aisle step; frame 000751.000)", uv)
    tube_obj("int_rail_posts", C_ST, posts, 0.022, STEEL, "estimated (posts every 2 rows under the aisle rails; 000751.000)")
    tube_obj("int_rail_ends", C_ST, ends, 0.03, STEEL, "estimated (bent rail end at the lower-tier aisle heads; 002144.300)", res=3)
    LOG["stand_s"] = round(time.time() - t0, 1)


def part_roof():
    """Part 3: the roof underside seen from the stands. The primaries, cables, struts, 9 purlin rings, the catwalk and
    the IT10 diagonals exist (build_bowl_detail section C). Added: a secondary steel grid hung under the membrane,
    3 secondary ribs between neighbouring primaries, 27 secondary rings and one diagonal in each cell, so the underside
    reads as the dense triangulated lattice of frames 000155.599, 000200.000 and IF22 (by eye; estimated)."""
    t0 = time.time()
    PROF, JF = G["prof"], G["j_facade"]; NP = len(PROF[0])
    def surf(theta, jf, down=0.0):
        fi = (theta / (2 * math.pi)) % 1 * N; i0 = int(fi) % N; i1 = (i0 + 1) % N; fi -= int(fi)
        j0 = min(int(jf), NP - 2); fj = jf - j0
        r = sum(PROF[i][j][0] * wi * wj for i, wi in ((i0, 1 - fi), (i1, fi)) for j, wj in ((j0, 1 - fj), (j0 + 1, fj)))
        y = sum(PROF[i][j][1] * wi * wj for i, wi in ((i0, 1 - fi), (i1, fi)) for j, wj in ((j0, 1 - fj), (j0 + 1, fj)))
        return B(math.cos(theta) * r, y - down, math.sin(theta) * r)
    STEEL = bpy.data.materials.get("roof_steel_white") or mat("int_roof_steel", "#E3E3DF", 0.4, 0.1)
    KR, dr = int(V("bowl.roofsteel.ribs")), V("bowl.roofsteel.drop")
    J0, J1 = JF + 1.0, NP - 1.3
    SUB, NRING = 4, 28           # secondary ribs: every quarter bay; secondary rings: 28 across the roof depth (estimated)
    DROP = 0.55                  # secondary grid below the membrane (estimated; the primaries hang 1.2 m)
    js = np.linspace(J0, J1, NRING)
    ribs, rings, diag = [], [], []
    for k in range(KR * SUB):
        if k % SUB == 0: continue  # the primaries are already there
        th = 2 * math.pi * k / (KR * SUB); ribs.append([surf(th, j, DROP) for j in js])
    for j in js:
        rings.append([surf(2 * math.pi * i / (KR * SUB * 2), j, DROP) for i in range(KR * SUB * 2 + 1)])
    for k in range(KR * SUB):
        ta, tb = 2 * math.pi * k / (KR * SUB), 2 * math.pi * (k + 1) / (KR * SUB)
        for q in range(NRING - 1):
            a_, b_ = (ta, tb) if (k + q) % 2 == 0 else (tb, ta)
            diag.append([surf(a_, js[q], DROP), surf(b_, js[q + 1], DROP)])
    tube_obj("int_roof_sub_ribs", "interior_roof_under", ribs, 0.07, STEEL, "estimated (secondary ribs; 000155.599, 000200.000, IF22)", res=1)
    tube_obj("int_roof_sub_rings", "interior_roof_under", rings, 0.06, STEEL, "estimated (secondary rings; IF22)", res=1)
    tube_obj("int_roof_sub_diagonals", "interior_roof_under", diag, 0.05, STEEL, "estimated (one diagonal per cell; IF22 triangular grid)", res=1)
    LOG["roof_s"] = round(time.time() - t0, 1)


if "concourse" in PARTS: part_concourse()
if "stand" in PARTS: part_stand()
if "roof" in PARTS: part_roof()
for c in [c for c in bpy.data.collections if c.name.startswith("interior_")]:
    c["claim"] = "interior for the walkthrough film (chapters 3 and 4); not in the web_hero_v2 twin export"
bpy.ops.wm.save_as_mainfile(filepath=str(OUT), compress=True)
_lp = ROOT / "blender/out/interior_build_log.json"  # one log for all parts: later parts update it
_prev = json.loads(_lp.read_text()) if _lp.exists() and "concourse" not in PARTS else {}
_prev.setdefault("objects", {}).update(LOG.pop("objects")); _prev["parts"] = sorted(set(_prev.get("parts", [])) | set(LOG.pop("parts")))
_prev.update(LOG); _lp.write_text(json.dumps(_prev, indent=1) + "\n")
print("interior", json.dumps(LOG))
