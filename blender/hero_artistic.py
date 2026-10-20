"""Step H (Munene, 2026-10-19): "hero_artistic" render preset. Artistic stills only; not used by the web bundle.

render_cycles.py calls prepare() before the look layer and finish() after it when quality is hero_artistic:
- 3840 x 2160, adaptive sampling, OpenImageDenoise, no simplify (textures at 100 %)
- facade uplights and a warm base glow round the plinth (dusk only), volumetric haze back on, sun glare and bloom
- edge bevels (shader bevel on the shell, facade and roof whites), deeper louvre fins
- parked cars in the GE car park (plain bodies, no sacco names or logos) and people on the plaza paving
People and vehicles are illustrative (Visualization); the image corner carries that label (stamp()).
The sky comes from the sunset_artistic and daylight_artistic presets in sky_hdri.py (CC0 HDRIs, fetch_hdri_h.sh).
"""
import json, math
from pathlib import Path
import numpy as np
import bpy, bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
CLAIM = "Visualization: hero_artistic still (step H); lights, people and cars are illustrative"
RES = (3840, 2160)
SET = {
    "samples": 128, "adaptive_threshold": 0.02, "adaptive_min": 32,
    "uplights": 96, "uplight_w": 1800.0, "uplight_k": 2900, "uplight_spot_deg": 38.0, "uplight_out_m": 2.5,
    "base_glow": 5.0, "base_glow_k": 3000,
    "haze_density": 1.6e-5, "haze_anisotropy": 0.72,
    "glare_mix": 0.09, "glare_threshold": 1.1, "streak_mix": 0.05,
    "bevel_m": 0.04, "lattice_bevel_max_m": 0.03, "fin_depth_scale": 1.35,  # lattice cap: facade spec 2026-10-20 (square rib edges)
    "cars": 0.62, "people": 1400,
}


def blackbody(k):
    import sky_hdri
    return sky_hdri.blackbody(k)


def _col(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(c)
    c["claim"] = CLAIM
    return c


def _mat(name, rgb, rough=0.5, emit=0.0, emit_rgb=None):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]; p.inputs["Base Color"].default_value = (*rgb, 1); p.inputs["Roughness"].default_value = rough
    if emit:
        p.inputs["Emission Color"].default_value = (*(emit_rgb or rgb), 1); p.inputs["Emission Strength"].default_value = emit
    m["claim"] = CLAIM
    return m


def _ground_bvh(scene):
    from mathutils.bvhtree import BVHTree
    terr = bpy.data.objects["terrain_site"]; dg = bpy.context.evaluated_depsgraph_get()
    tm = terr.evaluated_get(dg).to_mesh()
    bvh = BVHTree.FromPolygons([terr.matrix_world @ v.co for v in tm.vertices], [p.vertices[:] for p in tm.polygons])
    terr.evaluated_get(dg).to_mesh_clear()
    return lambda x, y: (bvh.ray_cast(Vector((x, y, 3000.0)), Vector((0, 0, -1)))[0] or Vector((0, 0, 0))).z


def _render(scene):
    r = scene.render; r.resolution_x, r.resolution_y = RES; r.resolution_percentage = 100
    r.use_simplify = False
    c = scene.cycles; c.samples = SET["samples"]; c.use_adaptive_sampling = True
    c.adaptive_threshold = SET["adaptive_threshold"]; c.adaptive_min_samples = SET["adaptive_min"]
    c.use_denoising = True; c.denoiser = "OPENIMAGEDENOISE"
    if hasattr(c, "texture_limit_render"): c.texture_limit_render = "OFF"
    if __import__("os").environ.get("TALANTA_ART_TEST"):  # quick pipeline check: tiny and noisy
        r.resolution_percentage = 12; c.samples = 4


def _uplights(scene, dusk):
    """Spot lights in the paving round the plinth, aimed up the facade; a warm emissive band on the glazed base."""
    if not dusk: return {"uplights": 0}
    RG = json.loads((ROOT / "blender/out/bowl_rings.json").read_text()); N = RG["N"]; pad = RG["pad"]
    col = _col("hero_uplights"); col_k = blackbody(SET["uplight_k"]); n = SET["uplights"]
    for k in range(n):
        i = int(round(k * N / n)) % N; ux, uz = RG["dirs"][i]; r = RG["rPl"][i] + SET["uplight_out_m"]
        ld = bpy.data.lights.new(f"uplight_{k:03d}", "SPOT"); ld.energy = SET["uplight_w"]; ld.color = col_k
        ld.spot_size = math.radians(SET["uplight_spot_deg"]); ld.spot_blend = 0.6; ld.shadow_soft_size = 0.15
        o = bpy.data.objects.new(f"uplight_{k:03d}", ld); col.objects.link(o)
        o.location = (ux * r, -uz * r, pad + 0.2)
        aim = Vector((ux * (r - 6.0), -uz * (r - 6.0), pad + 30.0)) - o.location
        o.rotation_euler = aim.to_track_quat("-Z", "Y").to_euler(); o["claim"] = CLAIM
    # base glow: a band just proud of the plinth face, 0.8 to 4.6 m (glazed base read, no openings modelled)
    glow = _mat("hero_base_glow", (0.05, 0.045, 0.04), 0.2, SET["base_glow"], blackbody(SET["base_glow_k"]))
    v, f = [], []
    for i in range(N):
        ux, uz = RG["dirs"][i]; r = RG["rPl"][i] + 0.06
        v += [(ux * r, -uz * r, pad + 0.8), (ux * r, -uz * r, pad + 4.6)]
    for i in range(N):
        j = (i + 1) % N; f.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
    me = bpy.data.meshes.new("hero_base_glow"); me.from_pydata(v, [], f); me.materials.append(glow); me.update()
    o = bpy.data.objects.new("hero_base_glow", me); col.objects.link(o); o["claim"] = CLAIM
    o.visible_shadow = False
    return {"uplights": n, "uplight_w": SET["uplight_w"]}


def _bevels_and_fins():
    """Shader bevel on the whites (rounded edges catch the light) and deeper louvre fins (scaled about the wall line)."""
    done = []
    for m in bpy.data.materials:
        if not m.node_tree or not any(k in m.name.lower() for k in ("white", "shell", "fascia", "roof", "lattice", "membrane", "rubis_canopy")): continue
        p = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if p is None or p.inputs["Normal"].is_linked: continue
        b = m.node_tree.nodes.new("ShaderNodeBevel"); b.inputs["Radius"].default_value = min(SET["bevel_m"], SET["lattice_bevel_max_m"]) if "lattice" in m.name.lower() else SET["bevel_m"]; b.samples = 6
        m.node_tree.links.new(b.outputs["Normal"], p.inputs["Normal"]); done.append(m.name)
    fins = bpy.data.objects.get("louvre_fins"); fin_note = None
    if fins is not None:
        # build_blockout.py writes each fin ring as (inner, outer) vertex pairs; push the inner edge in (it stays clear
        # of the backing: 0.7 m x 1.35 = 0.95 m < 1.4 m inset) and keep its height (the fin slope)
        me = fins.data; co = np.empty(len(me.vertices) * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 2, 3)
        co[:, 0, :2] = co[:, 1, :2] + (co[:, 0, :2] - co[:, 1, :2]) * SET["fin_depth_scale"]
        me.vertices.foreach_set("co", co.ravel()); me.update(); fin_note = f"fin depth 0.7 m x {SET['fin_depth_scale']}"
    return {"bevel_materials": len(done), "fins": fin_note}


def _cars(scene):
    """Parked cars on the GE car-park rows (site_layout_ge.json); plain painted bodies with a glass cabin."""
    D = json.loads((ROOT / "blender/data/site_layout_ge.json").read_text()); T = D["transform"]
    px2m = lambda p: ((p[0] - T["px0"]) / T["px_per_m"], (p[1] - T["py0"]) / T["px_per_m"])
    ground = _ground_bvh(scene); rng = np.random.default_rng(2026)
    paints = [(0.8, 0.8, 0.8), (0.55, 0.56, 0.58), (0.05, 0.05, 0.06), (0.62, 0.05, 0.04), (0.08, 0.16, 0.42), (0.85, 0.85, 0.82), (0.3, 0.3, 0.32)]
    pm = [_mat(f"hero_car_paint_{i}", c, 0.25) for i, c in enumerate(paints)]; glass = _mat("hero_car_glass", (0.02, 0.025, 0.03), 0.05)
    col = _col("hero_cars_Visualization"); n = 0
    for cp in D["car_parks"]:
        poly = [px2m(p) for p in cp["px"]]; a = math.radians(cp["row_bearing_deg"])
        u = (math.sin(a), -math.cos(a)); w = (-u[1], u[0])  # app frame: along the row, across the rows
        xs, zs = zip(*poly); cx, cz = sum(xs) / len(xs), sum(zs) / len(zs); R = max(math.dist((cx, cz), p) for p in poly)
        def inside(x, z):
            c = False
            for (x1, z1), (x2, z2) in zip(poly, poly[1:] + poly[:1]):
                if (z1 > z) != (z2 > z) and x < x1 + (z - z1) * (x2 - x1) / (z2 - z1): c = not c
            return c
        v, f, mi = [], [], []
        for row in np.arange(-R, R, cp["row_spacing_m"]):
            for side in (-1, 1):
                for t in np.arange(-R, R, 2.6):
                    if rng.random() > SET["cars"]: continue
                    o = row + side * 3.2
                    x, z = cx + u[0] * t + w[0] * o, cz + u[1] * t + w[1] * o
                    if not inside(x, z): continue
                    g = ground(x, -z) + 0.06; L, W = 4.4, 1.8
                    for (h0, h1, l, ww, m) in ((0.25, 0.95, L, W, int(rng.integers(len(pm)))), (0.95, 1.45, L * 0.55, W * 0.92, len(pm))):
                        b = len(v)
                        for hh in (h0, h1):
                            for sl, sw in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                                ax = w[0] * sl * l / 2 + u[0] * sw * ww / 2; az = w[1] * sl * l / 2 + u[1] * sw * ww / 2
                                v.append((x + ax, -(z + az), g + hh))
                        for q in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
                            f.append(tuple(b + k for k in q)); mi.append(m)
                    n += 1
        if not v: continue
        me = bpy.data.meshes.new("hero_parked_cars"); me.from_pydata(v, [], f)
        for m in pm + [glass]: me.materials.append(m)
        me.polygons.foreach_set("material_index", mi); me.update()
        bm = bmesh.new(); bm.from_mesh(me); bmesh.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new("hero_parked_cars_Visualization", me); col.objects.link(o); o["claim"] = CLAIM
    return {"parked_cars": n}


def _people(scene):
    """Figures on paving near the bowl: a ray from above must land on forecourt or apron paving."""
    dg = bpy.context.evaluated_depsgraph_get(); rng = np.random.default_rng(1963)
    RG = json.loads((ROOT / "blender/out/bowl_rings.json").read_text())
    cloth = [_mat(f"hero_person_{i}", c, 0.8) for i, c in enumerate(((0.6, 0.05, 0.04), (0.9, 0.9, 0.88), (0.05, 0.05, 0.06), (0.1, 0.25, 0.08), (0.75, 0.55, 0.1), (0.15, 0.2, 0.45)))]
    skin = _mat("hero_person_skin", (0.12, 0.07, 0.045), 0.6)
    v, f, mi = [], [], []; n = 0; tries = 0
    while n < SET["people"] and tries < SET["people"] * 12:
        tries += 1; i = int(rng.integers(RG["N"])); ux, uz = RG["dirs"][i]
        r = RG["rPl"][i] + rng.uniform(3, 70); x, y = ux * r, -uz * r
        hit, loc, _, _, ob, _ = scene.ray_cast(dg, Vector((x, y, 300.0)), Vector((0, 0, -1)), distance=600.0)
        if not hit or ob.type != "MESH" or not ob.material_slots: continue
        nm = (ob.material_slots[0].material.name if ob.material_slots[0].material else "").lower()
        if not any(k in nm for k in ("paving", "apron", "fc_paving", "ge_paving", "concrete")): continue
        h = rng.uniform(1.55, 1.85); bw = 0.22; g = loc.z
        for (z0, z1, rr, m) in ((g, g + h * 0.86, bw, int(rng.integers(len(cloth)))), (g + h * 0.86, g + h, bw * 0.55, len(cloth))):
            b = len(v)
            for zz in (z0, z1):
                for k in range(6):
                    a = 2 * math.pi * k / 6; v.append((x + rr * math.cos(a), y + rr * math.sin(a), zz))
            for k in range(6):
                k2 = (k + 1) % 6; f.append((b + k, b + k2, b + 6 + k2, b + 6 + k)); mi.append(m)
            f.append(tuple(b + 6 + k for k in range(6))); mi.append(m)
        n += 1
    if not v: return {"people": 0}
    me = bpy.data.meshes.new("hero_people_Visualization"); me.from_pydata(v, [], f)
    for m in cloth + [skin]: me.materials.append(m)
    me.polygons.foreach_set("material_index", mi); me.update()
    o = bpy.data.objects.new("hero_people_Visualization", me); _col("hero_people_Visualization").objects.link(o); o["claim"] = CLAIM
    return {"people": n}


def prepare(scene, dusk):
    """Scene changes before the look layer. Returns a log dict."""
    _render(scene)
    log = {"preset": "hero_artistic", "resolution": list(RES), "settings": SET}
    log.update(_uplights(scene, dusk)); log.update(_bevels_and_fins()); log.update(_cars(scene)); log.update(_people(scene))
    import lookdev  # stronger bloom and glare for the artistic set
    lookdev.STRENGTHS["glare"] = SET["glare_mix"]; lookdev.STRENGTHS["glare_threshold"] = SET["glare_threshold"]
    return log


def finish(scene):
    """After the look layer: volumetric haze back on (lookdev hides it) and a streak glare for the sun."""
    hz = bpy.data.objects.get("haze_volume")
    if hz is not None:
        hz.hide_render = False
        n = bpy.data.materials["haze"].node_tree.nodes["haze"]
        n.inputs["Density"].default_value = SET["haze_density"]; n.inputs["Anisotropy"].default_value = SET["haze_anisotropy"]
    scene.cycles.volume_bounces = 0; scene.cycles.volume_step_rate = 4.0
    tree = scene.compositing_node_group if hasattr(scene, "compositing_node_group") else scene.node_tree
    out = next((n for n in tree.nodes if n.type in ("GROUP_OUTPUT", "COMPOSITE")), None)
    if out is not None and out.inputs[0].is_linked:
        src = out.inputs[0].links[0].from_socket
        g = tree.nodes.new("CompositorNodeGlare")
        if "Type" in g.inputs:
            g.inputs["Type"].default_value = "Streaks"; g.inputs["Threshold"].default_value = 4.0
            if "Streaks" in g.inputs: g.inputs["Streaks"].default_value = 6
        else:
            g.glare_type = "STREAKS"; g.threshold = 4.0; g.streaks = 6
        tree.links.new(src, g.inputs["Image"])
        mix = tree.nodes.new("ShaderNodeMix") if hasattr(scene, "compositing_node_group") else tree.nodes.new("CompositorNodeMixRGB")
        if mix.bl_idname == "ShaderNodeMix":
            mix.data_type = "RGBA"; mix.inputs["Factor"].default_value = SET["streak_mix"]
            tree.links.new(src, mix.inputs["A"]); tree.links.new(g.outputs["Image"], mix.inputs["B"]); res = mix.outputs["Result"]
        else:
            mix.inputs[0].default_value = SET["streak_mix"]; tree.links.new(src, mix.inputs[1]); tree.links.new(g.outputs["Image"], mix.inputs[2]); res = mix.outputs[0]
        tree.links.new(res, out.inputs[0])


def stamp(path):
    """A labelled copy for sharing inside the team: 'Visualization' in the lower left corner."""
    from PIL import Image, ImageDraw, ImageFont
    im = Image.open(path).convert("RGB"); d = ImageDraw.Draw(im)
    try: font = ImageFont.truetype("DejaVuSans.ttf", 34)
    except OSError: font = ImageFont.load_default()
    d.text((40, im.height - 70), "Visualization: people, vehicles and lighting are illustrative", fill=(255, 255, 255), font=font)
    out = Path(path).with_name(Path(path).stem + "_labelled.jpg"); im.save(out, quality=92)
    return out
