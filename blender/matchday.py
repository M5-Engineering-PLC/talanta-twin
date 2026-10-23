"""Group 3 (detail sheet 04_people_life.md, PL-01 to PL-19, PL-39 to PL-43): matchday crowd, players, officials and
pitch-side staff, on the matchday cameras only (M01 day, M02 night; blender/data/matchday_cameras.json).

Everything here is Visualization (AGENTS.md rule 7): occupancy, clothing mix, props, kits and positions are build
estimates from the sheet, not a record of any match. Figures are anonymous low-poly shapes; no faces, numbers, names,
badges, sponsor marks or slogans. Stewards are generic figures in plain vests at loose, seeded spots; nothing here marks
a post, gate, exit or control position (rule 8). The Kenya flags are plain stripes; the shield and spears are left out.

render_cycles.py calls prepare() for an M camera before the look layer; the main build and the web bundle never hold
these objects. Write the cameras: python3 blender/matchday.py cameras
"""
import json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLAIM = "Visualization: matchday scene (group 3, detail sheet PL); crowd, players and staff are illustrative"
SRC = "engineering/detail_sheets/04_people_life.md (PL rows; colours and counts by eye, estimated)"
SET = {  # PL rows, the middle of each range
    "occupancy": {"lower": 0.90, "middle": 0.90, "upper": 0.85},            # PL-02 to PL-04, PL-10
    "block_jitter": 0.05,                                                    # PL-10: emptier and fuller blocks
    "cloth": {  # PL-01, PL-03, PL-04: (hex, weight)
        "lower": [("#B92332", 0.35), ("#222222", 0.25), ("#18733D", 0.20), ("#E8E4D8", 0.20)],
        "middle": [("#B92332", 0.40), ("#222222", 0.25), ("#18733D", 0.15), ("#E8E4D8", 0.20)],
        "upper": [("#B92332", 0.40), ("#222222", 0.30), ("#18733D", 0.10), ("#E8E4D8", 0.20)]},
    "legs": [("#222222", 0.45), ("#3A3F4A", 0.30), ("#5B5246", 0.15), ("#2F4766", 0.10)],
    "skin": [("#3B2417", 0.4), ("#4E3020", 0.35), ("#2C1A11", 0.25)],
    "scarf_every": 16, "flag_every": 32, "horn_every": 40,                   # PL-06, PL-07, PL-09
    "scarf_cols": ["#B92332", "#18733D", "#222222", "#F2F0E8"],
    "horn_cols": ["#E5B52C", "#B92332", "#18733D", "#222222"],
    "big_flag_m": (15.0, 10.0), "big_flag_dir_deg": 70.0,                    # PL-08: one block, across from M01
    "phone_every": 60, "phone_w": 6.0,                                       # PL-39, PL-42 (night only)
    "kits": {"home": ("#B92332", "#222222"), "away": ("#E8E4D8", "#18733D"),  # PL-11, PL-12 (shirt, shorts)
             "gk_home": ("#D8B629", "#222222"), "gk_away": ("#315E9B", "#222222"), "ref": ("#222222", "#222222")},
    "stewards_every_m": 40.0, "ball_kids": 5, "crew": 12,                    # PL-16, PL-18, PL-17/PL-19
    "seed": 2026,
}

# matchday cameras in bowl terms (direction deg from east towards south, tier fraction, height above the pad)
CAMS = [("M01", "Matchday bowl, day (Visualization)", "neutral", (225, 0.47, 22.7), (45, 0.22, 4.0), 22),
        ("M02", "Matchday bowl, night (Visualization)", "night", (225, 0.47, 22.7), (45, 0.22, 4.0), 22)]


def write_cameras():
    G = json.loads((ROOT / "blender/out/bowl_rings.json").read_text()); N, PAD = G["N"], G["pad"]
    SUNS = json.loads((ROOT / "app/cameras/manifest.json").read_text())["suns"]

    def ring(th_deg, t, h):
        th = math.radians(th_deg) % (2 * math.pi); i = int(round(th / (2 * math.pi) * N)) % N
        r = G["rIn"][i] + (G["rBack"][i] - G["rIn"][i]) * t
        return [round(math.cos(th) * r, 2), round(h + PAD, 2), round(math.sin(th) * r, 2)]
    out = {"note": "Matchday cameras (group 3). Render viewpoints for review only; not real camera locations (AGENTS.md rule 8). "
                   "Every still from them is a Visualization.",
           "cameras": [{"id": c, "name": nm, "purpose": "group 3 matchday crowd, players and staff (detail sheet PL); Visualization; internal only",
                        "position": ring(*p), "target": ring(*t), "up": [0, 1, 0], "projection": "perspective", "focal_length_mm": f,
                        "roll_deg": 0.0, "dof": False, "exposure_ev": 0.0, "sun": dict(SUNS[sun]), "variants": [], "seed": 40 + k}
                       for k, (c, nm, sun, p, t, f) in enumerate(CAMS)]}
    (ROOT / "blender/data/matchday_cameras.json").write_text(json.dumps(out, indent=1) + "\n")
    print("\n".join(f"{c['id']} {c['position']} -> {c['target']}" for c in out["cameras"]))


if __name__ == "__main__" and "cameras" in sys.argv:
    write_cameras(); raise SystemExit

import csv
import numpy as np
import bpy, bmesh
from mathutils import Matrix

L = {r["name"]: r for r in csv.DictReader(open(ROOT / "gis/parameter_ledger.csv"))}
V = lambda k: float(L[k + "_blockout"]["value"]) if k + "_blockout" in L else float(L[k]["value"])


def lin(h):
    return tuple(((int(h[i:i + 2], 16) / 255 + 0.055) / 1.055) ** 2.4 for i in (1, 3, 5))


def pick(rng, table, n):
    cols = np.array([lin(h) for h, _ in table]); w = np.array([w for _, w in table]); w = w / w.sum()
    return cols[rng.choice(len(table), size=n, p=w)]


def _coll():
    c = bpy.data.collections.get("matchday_Visualization") or bpy.data.collections.new("matchday_Visualization")
    if c.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(c)
    c["claim"] = CLAIM
    return c


def _attr_mat(name, attr, rough=0.75, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; m["claim"] = CLAIM
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]; a = nt.nodes.new("ShaderNodeAttribute")
    a.attribute_type = "INSTANCER"; a.attribute_name = attr
    nt.links.new(a.outputs["Color"], p.inputs["Base Color"]); p.inputs["Roughness"].default_value = rough
    if emit:
        nt.links.new(a.outputs["Color"], p.inputs["Emission Color"]); p.inputs["Emission Strength"].default_value = emit
    return m


def _flag_mat(name, axis):
    """Kenya stripes along the cloth's local axis (0..1): black, white, red, white, green; no shield (Visualization)."""
    m = bpy.data.materials.new(name); m.use_nodes = True; m["claim"] = CLAIM
    nt = m.node_tree; p = nt.nodes["Principled BSDF"]; p.inputs["Roughness"].default_value = 0.85
    tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ"); cr = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["UV"], sep.inputs[0]); nt.links.new(sep.outputs[axis], cr.inputs["Fac"])
    cr.color_ramp.interpolation = "CONSTANT"; els = cr.color_ramp.elements
    stops = [(0.0, "#111111"), (0.3, "#FFFFFF"), (0.367, "#BB0000"), (0.633, "#FFFFFF"), (0.7, "#006600")]
    els[0].position, els[0].color = stops[0][0], (*lin(stops[0][1]), 1); els[1].position, els[1].color = stops[1][0], (*lin(stops[1][1]), 1)
    for pos, hx in stops[2:]:
        e = els.new(pos); e.color = (*lin(hx), 1)
    nt.links.new(cr.outputs["Color"], p.inputs["Base Color"])
    return m


def _boxes(bm, parts):
    """parts: (cx, cy, cz, hx, hy, hz, tilt_x, material index)."""
    for cx, cy, cz, hx, hy, hz, tilt, mi in parts:
        g = bmesh.ops.create_cube(bm, size=1.0)
        for v in g["verts"]:
            v.co.x *= 2 * hx; v.co.y *= 2 * hy; v.co.z *= 2 * hz
            v.co = Matrix.Rotation(tilt, 3, "X") @ v.co; v.co.x += cx; v.co.y += cy; v.co.z += cz
        for fc in {f for v in g["verts"] for f in v.link_faces}: fc.material_index = mi


def _head(bm, z, r, mi):
    g = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=r)
    for v in g["verts"]: v.co.z += z
    for fc in {f for v in g["verts"] for f in v.link_faces}: fc.material_index = mi


def _proto(name, build, mats):
    bm = bmesh.new(); build(bm); me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    o = bpy.data.objects.new(name, me); pc = bpy.data.collections.get("matchday_protos") or bpy.data.collections.new("matchday_protos")
    if pc.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(pc)
    pc.hide_render = True; pc.hide_viewport = True; pc.objects.link(o)
    return o


def _scatter(name, proto, pos, rotz, attrs, scale=None):
    """Instance proto on points; point colour attributes reach the shader as INSTANCER attributes (as the seats do)."""
    pos = np.asarray(pos, np.float32).reshape(-1, 3)
    if not len(pos): return 0
    me = bpy.data.meshes.new(name + "_points"); me.vertices.add(len(pos)); me.vertices.foreach_set("co", pos.ravel())
    rot = np.zeros((len(pos), 3), np.float32); rot[:, 2] = rotz
    me.attributes.new("rot", "FLOAT_VECTOR", "POINT").data.foreach_set("vector", rot.ravel())
    sc = np.ones((len(pos), 3), np.float32) * (np.asarray(scale, np.float32)[:, None] if scale is not None else 1.0)
    me.attributes.new("scl", "FLOAT_VECTOR", "POINT").data.foreach_set("vector", sc.ravel())
    for k, c in attrs.items():
        c = np.asarray(c, np.float32); c = np.concatenate([c, np.ones((len(c), 1), np.float32)], axis=1)
        me.attributes.new(k, "FLOAT_COLOR", "POINT").data.foreach_set("color", c.ravel())
    o = bpy.data.objects.new(name, me); _coll().objects.link(o); o["claim"], o["sources"] = CLAIM, SRC
    gn = bpy.data.node_groups.new(name + "_scatter", "GeometryNodeTree")
    gn.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    gn.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    gi, go = gn.nodes.new("NodeGroupInput"), gn.nodes.new("NodeGroupOutput")
    oi = gn.nodes.new("GeometryNodeObjectInfo"); oi.inputs["Object"].default_value = proto
    iop = gn.nodes.new("GeometryNodeInstanceOnPoints")
    for nm, sock in (("rot", "Rotation"), ("scl", "Scale")):
        ra = gn.nodes.new("GeometryNodeInputNamedAttribute"); ra.data_type = "FLOAT_VECTOR"; ra.inputs["Name"].default_value = nm
        gn.links.new(ra.outputs["Attribute"], iop.inputs[sock])
    gn.links.new(gi.outputs[0], iop.inputs["Points"]); gn.links.new(oi.outputs["Geometry"], iop.inputs["Instance"])
    gn.links.new(iop.outputs["Instances"], go.inputs[0])
    o.modifiers.new("scatter", "NODES").node_group = gn
    return len(pos)


def _fans(rng, night, log):
    seats = bpy.data.objects["seats"].data; n = len(seats.vertices)
    P = np.zeros(n * 3, np.float32); seats.vertices.foreach_get("co", P); P = P.reshape(-1, 3)
    R = np.zeros(n * 3, np.float32); seats.attributes["rot"].data.foreach_get("vector", R); rz = R.reshape(-1, 3)[:, 2]
    PAD = json.loads((ROOT / "blender/out/bowl_rings.json").read_text())["pad"]
    h = P[:, 2] - PAD
    tier = np.where(h <= V("bowl.tier_lower.y1") + 0.5, "lower", np.where(h <= V("bowl.tier_middle.y1") + 0.5, "middle", "upper"))
    th = np.arctan2(-P[:, 1], P[:, 0]) % (2 * math.pi)  # app angle: east towards south
    block = (th / (2 * math.pi) * 27).astype(int)
    jit = rng.uniform(-SET["block_jitter"], SET["block_jitter"], 27)
    occ = np.array([SET["occupancy"][t] for t in tier]) + jit[block]
    keep = rng.random(n) < occ
    P, rz, tier = P[keep], rz[keep], tier[keep]; m = len(P)
    cloth = np.zeros((m, 3), np.float32)
    for t in ("lower", "middle", "upper"):
        s = tier == t; cloth[s] = pick(rng, SET["cloth"][t], int(s.sum()))
    legs, skin = pick(rng, SET["legs"], m), pick(rng, SET["skin"], m)
    ph = V("bowl.seat.pan_h")
    shirt, trous, skinm = _attr_mat("md_shirt", "clothcol"), _attr_mat("md_legs", "legcol"), _attr_mat("md_skin", "skincol", 0.6)
    fan = _proto("md_fan_proto", lambda bm: (_boxes(bm, [
        (0, -0.10, ph + 0.36, 0.19, 0.11, 0.28, -0.10, 0),           # torso, leaning back
        (-0.21, -0.02, ph + 0.30, 0.05, 0.06, 0.22, 0.35, 0), (0.21, -0.02, ph + 0.30, 0.05, 0.06, 0.22, 0.35, 0),  # arms
        (0, 0.14, ph + 0.07, 0.17, 0.22, 0.07, 0.0, 1),              # thighs
        (-0.09, 0.36, ph / 2, 0.06, 0.06, ph / 2, 0.0, 1), (0.09, 0.36, ph / 2, 0.06, 0.06, ph / 2, 0.0, 1)]),  # lower legs
        _head(bm, ph + 0.78, 0.11, 2)), [shirt, trous, skinm])
    log["fans"] = _scatter("md_fans", fan, P, rz, {"clothcol": cloth, "legcol": legs, "skincol": skin})
    log["seats_empty"] = int(n - m)
    # props held by some fans: in the fan's own frame, rotated with it
    fwd = np.stack([-np.sin(rz), np.cos(rz)], 1)  # local +Y in Blender XY
    def at_hand(sel, up, fw):
        q = P[sel].copy(); q[:, 0] += fwd[sel, 0] * fw; q[:, 1] += fwd[sel, 1] * fw; q[:, 2] += up; return q
    u = rng.random(m)
    s_scarf = u < 1 / SET["scarf_every"]; s_flag = (u >= 1 / SET["scarf_every"]) & (u < 1 / SET["scarf_every"] + 1 / SET["flag_every"])
    s_horn = (u >= 0.5) & (u < 0.5 + 1 / SET["horn_every"])
    scarf = _proto("md_scarf_proto", lambda bm: _boxes(bm, [(0, 0, 0, 0.70, 0.01, 0.09, 0, 0),
        (-0.24, -0.02, -0.28, 0.04, 0.04, 0.26, 0, 1), (0.24, -0.02, -0.28, 0.04, 0.04, 0.26, 0, 1)]),
        [_attr_mat("md_scarf", "propcol", 0.9), shirt])
    log["scarves"] = _scatter("md_scarves", scarf, at_hand(s_scarf, ph + 1.30, -0.05), rz[s_scarf],
                              {"propcol": pick(rng, [(c, 1) for c in SET["scarf_cols"]], int(s_scarf.sum())), "clothcol": cloth[s_scarf]})
    def flag_build(bm):
        _boxes(bm, [(0, 0, -0.15, 0.008, 0.008, 0.45, 0, 0)])
        g = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.0)
        uv = bm.loops.layers.uv.verify(); gx = [v.co.x for v in g["verts"]]; gy = [v.co.y for v in g["verts"]]
        for v in g["verts"]:  # cloth 0.45 x 0.30 m beside the pole top
            u_, w_ = (v.co.x - min(gx)) / (max(gx) - min(gx)), (v.co.y - min(gy)) / (max(gy) - min(gy))
            v.co.x, v.co.y, v.co.z = 0.008 + 0.45 * u_, 0.0, 0.30 * w_
        for fc in {f for v in g["verts"] for f in v.link_faces}:
            fc.material_index = 1
            for lp in fc.loops: lp[uv].uv = ((lp.vert.co.x - 0.008) / 0.45, 1 - lp.vert.co.z / 0.30)  # black stripe on top
    hand_flag = _proto("md_hand_flag_proto", flag_build, [_attr_mat("md_pole", "propcol", 0.6), _flag_mat("md_flag_small", "Y")])
    log["hand_flags"] = _scatter("md_hand_flags", hand_flag, at_hand(s_flag, ph + 1.20, 0.05), rz[s_flag],
                                 {"propcol": np.tile(lin("#D8D0C1"), (int(s_flag.sum()), 1))})
    horn = _proto("md_horn_proto", lambda bm: bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.015, radius2=0.06, depth=0.6,
                  matrix=Matrix.Translation((0, 0.3, 0)) @ Matrix.Rotation(-math.pi / 2, 4, "X")), [_attr_mat("md_horn", "propcol", 0.4)])
    log["horns"] = _scatter("md_horns", horn, at_hand(s_horn, ph + 0.95, 0.05), rz[s_horn],
                            {"propcol": pick(rng, [(c, 1) for c in SET["horn_cols"]], int(s_horn.sum()))})
    if night:  # PL-39, PL-42: sparse cool-white phone lights
        s_ph = rng.random(m) < 1 / SET["phone_every"]
        ph_o = _proto("md_phone_proto", lambda bm: _head(bm, 0.0, 0.04, 0), [_attr_mat("md_phone", "propcol", 0.3, SET["phone_w"])])
        log["phone_lights"] = _scatter("md_phones", ph_o, at_hand(s_ph, ph + 1.15, 0.15), rz[s_ph],
                                       {"propcol": pick(rng, [("#F3F4FF", 0.7), ("#BFD4FF", 0.3)], int(s_ph.sum()))})
    return P, tier


def _big_flag(log):
    """PL-08: one large plain-stripe Kenya flag held over a lower-tier block, following the rake."""
    G = json.loads((ROOT / "blender/out/bowl_rings.json").read_text()); N, PAD = G["N"], G["pad"]
    th0 = math.radians(SET["big_flag_dir_deg"]); i = int(round(th0 / (2 * math.pi) * N)) % N
    rin, rb = G["rIn"][i], G["rBack"][i]; t0, t1, y0, y1 = (V(f"bowl.tier_lower.{k}") for k in ("t0", "t1", "y0", "y1"))
    W, D = SET["big_flag_m"]; r_mid = rin + (rb - rin) * (t0 + t1) / 2
    dt_ = D / ((rb - rin) * math.hypot(1, (y1 - y0) / ((rb - rin) * (t1 - t0)))) ; tc = (t0 + t1) / 2
    bm = bmesh.new(); uv = bm.loops.layers.uv.verify(); nu, nv = 24, 12; vs = []
    for a in range(nv + 1):
        t = tc - dt_ / 2 + dt_ * a / nv; y = y0 + (y1 - y0) * (t - t0) / (t1 - t0) + 1.9
        r = rin + (rb - rin) * t
        for b in range(nu + 1):
            th = th0 + (b / nu - 0.5) * W / r_mid
            z = PAD + y + 0.25 * math.sin(b / nu * 3 * math.pi) * math.sin(a / nv * math.pi)
            vs.append(bm.verts.new((math.cos(th) * r, -math.sin(th) * r, z)))
    for a in range(nv):
        for b in range(nu):
            k = a * (nu + 1) + b; fc = bm.faces.new((vs[k], vs[k + 1], vs[k + nu + 2], vs[k + nu + 1]))
            for lp, (uu, vv) in zip(fc.loops, ((b, a), (b + 1, a), (b + 1, a + 1), (b, a + 1))): lp[uv].uv = (uu / nu, 1 - vv / nv)
    me = bpy.data.meshes.new("md_big_flag"); bm.to_mesh(me); bm.free(); me.materials.append(_flag_mat("md_flag_big", "Y"))
    o = bpy.data.objects.new("md_big_flag", me); _coll().objects.link(o); o["claim"], o["sources"] = CLAIM, SRC
    log["big_flag_m"] = [W, D]


def _pitch_people(rng, log):
    """PL-11 to PL-19: players in a loose match layout, officials, ball attendants, stewards and crew at the pitch edge."""
    G = json.loads((ROOT / "blender/out/bowl_rings.json").read_text()); PAD = G["pad"]
    b = math.radians(G["bearing"]); cb, sb = math.cos(b), math.sin(b)
    hl, hw = V("pitch.length") / 2, V("pitch.width") / 2; zg = PAD + 0.1
    to_bl = lambda x, z: ((x * cb - z * sb), -(x * sb + z * cb))  # pitch local (x across, z along) -> app -> Blender XY
    shirt, trous, skinm = (bpy.data.materials[n] for n in ("md_shirt", "md_legs", "md_skin"))
    std = _proto("md_standing_proto", lambda bm: (_boxes(bm, [
        (0, 0, 1.18, 0.20, 0.11, 0.27, 0, 0), (-0.24, 0, 1.12, 0.05, 0.05, 0.27, 0, 2), (0.24, 0, 1.12, 0.05, 0.05, 0.27, 0, 2),
        (0, 0, 0.84, 0.18, 0.11, 0.09, 0, 1), (-0.09, 0, 0.40, 0.065, 0.065, 0.40, 0, 2), (0.09, 0, 0.40, 0.065, 0.065, 0.40, 0, 2)]),
        _head(bm, 1.58, 0.11, 2)), [shirt, trous, skinm])
    ball = np.array([0.12 * hw, 0.18 * hl])
    # 4-4-2 shapes in (across, along) fractions; home defends -z, away defends +z; the block leans to the ball
    shape = [(-0.7, -0.55), (-0.25, -0.62), (0.25, -0.62), (0.7, -0.55), (-0.75, -0.15), (-0.25, -0.2), (0.25, -0.2), (0.75, -0.15),
             (-0.2, 0.15), (0.25, 0.2)]
    pos, face, sh, sc = [], [], [], []
    def person(x, z, kit, scale=1.0, look=None):
        lx, lz = (look if look is not None else ball) - np.array([x, z])
        X, Y = to_bl(x, z); dX, dY = to_bl(lx, lz)
        pos.append((X, Y, zg)); face.append(math.atan2(dY, dX) - math.pi / 2); sh.append(kit); sc.append(scale)
    for side, kit, gk, sgn in (("home", "home", "gk_home", 1), ("away", "away", "gk_away", -1)):
        for (u, v) in shape:
            x = u * hw + rng.normal(0, 2.5); z = sgn * v * hl + 0.35 * (ball[1] - sgn * v * hl) * 0.5 + rng.normal(0, 3)
            person(np.clip(x, -hw + 1, hw - 1), np.clip(z, -hl + 2, hl - 2), kit, rng.uniform(0.95, 1.05))
        person(rng.normal(0, 1.5), -sgn * (hl - 3.5), gk, 1.03)
    person(ball[0] - 6, ball[1] - 9, "ref"); person(-hw - 0.8, ball[1] - 4, "ref"); person(hw + 0.8, -ball[1] - 6, "ref")  # PL-14
    log["players"] = 22; log["officials"] = 3
    kits = {k: (lin(a), lin(c)) for k, (a, c) in SET["kits"].items()}
    kits["steward"] = (lin("#C6D72C"), lin("#252525")); kits["kid"] = (lin("#D8B629"), lin("#222222")); kits["crew"] = (lin("#252525"), lin("#9A9A96"))
    # PL-16 stewards: loose seeded spots round the run-off, facing the stands; no fixed posts
    per = 4 * (hl + hw + 8); ns = int(per / SET["stewards_every_m"])
    for k in range(ns):
        s = (k + rng.uniform(0.2, 0.8)) / ns * per; e = 6.5 + rng.uniform(-0.6, 0.6)
        sides = [(2 * (hw + e), lambda q: (-hw - e + q, -hl - e)), (2 * (hl + e), lambda q: (hw + e, -hl - e + q)),
                 (2 * (hw + e), lambda q: (hw + e - q, hl + e)), (2 * (hl + e), lambda q: (-hw - e, hl + e - q))]
        for ln, f_ in sides:
            if s <= ln: x, z = f_(s); break
            s -= ln
        person(x, z, "steward", 1.0, look=np.array([x * 3, z * 3]))
    for k in range(SET["ball_kids"]):  # PL-18
        a = rng.uniform(0, 2 * math.pi); x = np.clip(math.cos(a) * (hw + 9), -hw - 3, hw + 3); z = np.clip(math.sin(a) * (hl + 9), -hl - 3, hl + 3)
        person(x, z, "kid", 0.82)
    for g in range(3):  # PL-17, PL-19: small loose groups beside the field, east side away from the tunnel
        cz = rng.uniform(-0.6, 0.6) * hl
        for k in range(SET["crew"] // 3): person(hw + 4.5 + rng.uniform(0, 2), cz + rng.uniform(-2.5, 2.5), "crew", rng.uniform(0.95, 1.05))
    log["stewards"], log["ball_attendants"], log["crew"] = ns, SET["ball_kids"], SET["crew"] // 3 * 3
    cl = np.array([kits[k][0] for k in sh]); lg = np.array([kits[k][1] for k in sh]); sk = pick(rng, SET["skin"], len(sh))
    _scatter("md_pitch_people", std, pos, face, {"clothcol": cl, "legcol": lg, "skincol": sk}, scale=np.array(sc))
    bme = bmesh.new(); _head(bme, 0.0, 0.11, 0); me = bpy.data.meshes.new("md_ball"); bme.to_mesh(me); bme.free()
    m = bpy.data.materials.new("md_ball"); m.use_nodes = True; m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.9, 0.9, 0.88, 1)
    me.materials.append(m); X, Y = to_bl(*ball); o = bpy.data.objects.new("md_ball", me); o.location = (X + 0.6, Y + 0.4, zg + 0.11); _coll().objects.link(o)


def prepare(scene, night):
    """Add the matchday Visualization to the open scene; LED ribbons on ('matchday:' labels). Returns a log dict."""
    rng = np.random.default_rng(SET["seed"]); log = {"preset": "matchday", "claim": CLAIM, "night": bool(night)}
    _fans(rng, night, log); _big_flag(log); _pitch_people(rng, log)
    for mt in bpy.data.materials:
        if not mt.node_tree: continue
        for nd in mt.node_tree.nodes:
            if nd.label.startswith("matchday:"):
                v = float(nd.label.split(":")[1])
                if nd.type == "BSDF_PRINCIPLED": nd.inputs["Emission Strength"].default_value = v
                elif nd.type == "EMISSION": nd.inputs["Strength"].default_value = v
    return log


def stamp(path):
    """A labelled copy: 'Visualization' in the lower left corner (as hero_artistic.stamp)."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.open(path).convert("RGB"); d = ImageDraw.Draw(im)
    try: font = ImageFont.truetype("DejaVuSans.ttf", max(18, im.height // 32))
    except OSError: font = ImageFont.load_default()
    d.text((im.height // 27, im.height - im.height // 15), "Visualization: crowd, players and staff are illustrative, not a safety simulation",
           fill=(255, 255, 255), font=font)
    out = Path(path).with_name(Path(path).stem + "_labelled.jpg"); im.save(out, quality=92)
    return out
