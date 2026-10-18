"""Far land, ground cover and facades for the concept-match pass 2 (lead review of pass 1, 2026-10-18).

- The horizon.py terrain bands (3 to 8.5 km) repeat the terrain_far surface from the same GLO-30 raster, so the two
  z-fought into pale stripes. terrain_far keeps its faces inside 3 km; beyond that the bands carry the Sentinel-2
  colour (ground_far.jpg, same UV frame as terrain_far) so lookdev.py can haze each band on its own.
- The 10 m Sentinel-2 colour reads as a flat beige smear at grazing angles. A shared node group keeps its tone
  (the measured colour) and adds structure by tone class: dark pixels become broadleaf canopy, bright ones a
  roof and yard mosaic, the middle a suburb mix. Visualization: the mosaic is generic, not mapped roofs or trees.
- C19 bottom left: the car-park asphalt (site_regions2 blue) becomes murram, as in the as-built yard
  (JWNowpO44rw 001246.333), and the raw imagery round the site gets the same structured cover.
- The OSM/Overture buildings and suburb walls get storey window rows and per-building cream and grey tones.
Run from build_site_detail.py after the context builders and before materials_pbr.apply.
"""
import json, math
from pathlib import Path

import bpy

CLAIM = "Visualization: far-land structure from Sentinel-2 tone classes; roof, yard and canopy mosaic generic"
TRIM_M = 3000.0   # terrain_far faces beyond this go; horizon_band_1 starts at 2850 m (150 m overlap)
MURRAM = ((0.33, 0.13, 0.065), (0.42, 0.18, 0.09))   # linear, the Ground109 earth range in build_scene.py
FACADE_TONES = [(0.62, 0.58, 0.49), (0.55, 0.54, 0.51), (0.47, 0.47, 0.46), (0.64, 0.54, 0.40), (0.42, 0.44, 0.46)]


def _n(t, kind, **inputs):
    nd = t.nodes.new(kind)
    for k, v in inputs.items():
        if k.startswith("_"): setattr(nd, k[1:], v); continue
        sock = nd.inputs[int(k[1:])] if k[0] == "i" and k[1:].isdigit() else nd.inputs[k]
        if hasattr(v, "node"): t.links.new(v, sock)
        else: sock.default_value = v
    return nd


def _math(t, op, a, b=0.0, clamp=False):
    return _n(t, "ShaderNodeMath", _operation=op, _use_clamp=clamp, i0=a, i1=b).outputs[0]


def _mix(t, f, a, b):
    m = _n(t, "ShaderNodeMix", _data_type="RGBA", i0=f)
    for i, v in ((6, a), (7, b)):
        if hasattr(v, "node"): t.links.new(v, m.inputs[i])
        else: m.inputs[i].default_value = (*v, 1) if len(v) == 3 else v
    return m.outputs[2]


def _ramp(t, value, lo, hi):
    """Smooth 0..1 from lo to hi (hi < lo gives a falling ramp)."""
    return _n(t, "ShaderNodeMapRange", _interpolation_type="SMOOTHSTEP", Value=value, **{"From Min": lo, "From Max": hi}).outputs[0]


def _grade_group(site=False):
    """site=False: canopy and roof mosaic for the far land. site=True: grass and murram cover for the open ground
    round the site, where a flat roof mosaic without buildings would read as camouflage."""
    name = "site_ground_grade" if site else "far_land_grade"
    g = bpy.data.node_groups.get(name)
    if g: return g
    g = bpy.data.node_groups.new(name, "ShaderNodeTree")
    g.interface.new_socket(name="Color", in_out="INPUT", socket_type="NodeSocketColor")
    g.interface.new_socket(name="Keep", in_out="INPUT", socket_type="NodeSocketFloat")
    g.interface.new_socket(name="Color", in_out="OUTPUT", socket_type="NodeSocketColor")
    t = g.nodes; gi, go = t.new("NodeGroupInput"), t.new("NodeGroupOutput")
    src = gi.outputs["Color"]
    pos = t.new("ShaderNodeTexCoord").outputs["Object"]
    lum = _n(g, "ShaderNodeRGBToBW", Color=src).outputs[0]
    sat = _n(g, "ShaderNodeHueSaturation", Color=src, Saturation=1.25, Value=0.95).outputs[0]
    # canopy: three greens by a 70 m noise, shaded by a 9 m noise (crowns), brightness follows the imagery
    n70 = _n(g, "ShaderNodeTexNoise", Vector=pos, Scale=1 / 70, Detail=3.0).outputs["Fac"]
    n9 = _n(g, "ShaderNodeTexNoise", Vector=pos, Scale=1 / 9, Detail=2.0).outputs["Fac"]
    canopy = _mix(g, n70, (0.030, 0.055, 0.022), (0.060, 0.085, 0.032))
    canopy = _mix(g, _ramp(g, n9, 0.35, 0.65), _n(g, "ShaderNodeMix", _data_type="RGBA", _blend_type="MULTIPLY", i0=1.0, i6=canopy, i7=(0.55, 0.55, 0.55, 1)).outputs[2], canopy)
    # built: roof mosaic in 14 m cells (rust, terracotta, grey sheet, cream), trees between plots
    vor = _n(g, "ShaderNodeTexVoronoi", Vector=pos, Scale=1 / 14).outputs["Color"]
    vr = _n(g, "ShaderNodeSeparateColor", Color=vor).outputs
    roof = _mix(g, _ramp(g, vr[0], 0.45, 0.55), (0.24, 0.075, 0.045), (0.33, 0.13, 0.07))
    roof = _mix(g, _ramp(g, vr[1], 0.62, 0.70), roof, (0.20, 0.20, 0.20))
    roof = _mix(g, _ramp(g, vr[2], 0.80, 0.86), roof, (0.42, 0.37, 0.28))
    built = _mix(g, _ramp(g, _n(g, "ShaderNodeTexNoise", Vector=pos, Scale=1 / 22, Detail=2.0).outputs["Fac"], 0.56, 0.62), roof, canopy)
    if site:  # grass for the dark and middle tones, murram with grass patches for the bright ones
        canopy = _mix(g, _n(g, "ShaderNodeTexNoise", Vector=pos, Scale=1 / 8, Detail=4.0).outputs["Fac"], (0.045, 0.075, 0.025), (0.075, 0.10, 0.04))
        murram = _mix(g, _n(g, "ShaderNodeTexNoise", Vector=pos, Scale=1 / 5, Detail=4.0).outputs["Fac"], MURRAM[0], MURRAM[1])
        dry = _mix(g, _n(g, "ShaderNodeTexNoise", Vector=pos, Scale=1 / 12, Detail=3.0).outputs["Fac"], (0.14, 0.13, 0.06), (0.20, 0.17, 0.08))
        murram = _mix(g, _ramp(g, _n(g, "ShaderNodeTexNoise", Vector=pos, Scale=1 / 60, Detail=3.0).outputs["Fac"], 0.48, 0.58), murram, dry)
        built = _mix(g, _ramp(g, _n(g, "ShaderNodeTexNoise", Vector=pos, Scale=1 / 30, Detail=3.0).outputs["Fac"], 0.56, 0.64), murram, canopy)
    # tone classes from the imagery (linear luminance): dark = canopy, bright = built, middle = mixed suburb
    # thresholds favour canopy: the drone frames show heavy tree cover over the suburbs (environment notes)
    veg = _ramp(g, lum, 0.14, 0.08)
    bright = _ramp(g, lum, 0.22, 0.34)
    mid = _mix(g, _ramp(g, _n(g, "ShaderNodeTexNoise", Vector=pos, Scale=1 / 45, Detail=3.0).outputs["Fac"], 0.38, 0.48), built, canopy)
    structured = _mix(g, veg, _mix(g, bright, mid, built), canopy)
    # keep the measured tone: scale the mosaic to the imagery brightness, then blend with the graded imagery
    s_lum = _n(g, "ShaderNodeRGBToBW", Color=structured).outputs[0]
    gain = _math(g, "MINIMUM", _math(g, "DIVIDE", lum, _math(g, "MAXIMUM", s_lum, 0.01)), 1.6)
    gain = _math(g, "MAXIMUM", _math(g, "ADD", _math(g, "MULTIPLY", gain, 0.5), 0.5), 0.6)
    structured = _n(g, "ShaderNodeMix", _data_type="RGBA", _blend_type="MULTIPLY", i0=1.0, i6=structured,
                    i7=_n(g, "ShaderNodeCombineColor", Red=gain, Green=gain, Blue=gain).outputs[0]).outputs[2]
    out = _mix(g, gi.outputs["Keep"], structured, sat)
    g.links.new(out, go.inputs["Color"])
    g["claim"] = CLAIM
    return g


def _wrap_image(mat, keep, site=False):
    """Route every use of the material's ground image through far_land_grade."""
    t = mat.node_tree
    for img in [nd for nd in t.nodes if nd.type == "TEX_IMAGE" and nd.image and nd.image.name.startswith("ground_")]:
        links = list(img.outputs["Color"].links)
        if not links: continue
        grp = t.nodes.new("ShaderNodeGroup"); grp.node_tree = _grade_group(site); grp.label = grp.node_tree.name
        grp.inputs["Keep"].default_value = keep
        t.links.new(img.outputs["Color"], grp.inputs["Color"])
        for lk in links: t.links.new(grp.outputs["Color"], lk.to_socket)
    mat["far_land"] = CLAIM


def _band_material(root, ground):
    m = bpy.data.materials.new("far_land_band_mat"); m.use_nodes = True; t = m.node_tree
    p = t.nodes["Principled BSDF"]; p.inputs["Roughness"].default_value = 0.95
    img = t.nodes.new("ShaderNodeTexImage"); img.extension = "EXTEND"
    img.image = bpy.data.images.load(str(root / "app/public/data" / ground["file"]), check_existing=True)
    # terrain_far UV: u = (x - x0) / size, v = 1 + (y + z0) / size (build_scene.py terrain(), Blender x east, y north)
    s = ground["size"]
    mp = _n(t, "ShaderNodeMapping", _vector_type="POINT", Vector=t.nodes.new("ShaderNodeTexCoord").outputs["Object"],
            Location=(-ground["x0"] / s, 1 + ground["z0"] / s, 0), Scale=(1 / s, 1 / s, 1))
    t.links.new(mp.outputs[0], img.inputs["Vector"]); t.links.new(img.outputs["Color"], p.inputs["Base Color"])
    m["claim"] = "derived: Sentinel-2 colour (ground_far.jpg) on the GLO-30 bands; " + CLAIM
    return m


def _trim_far(scene, ground):
    """Drop terrain_far where the bands cover it. Keep a 150 m rim at the raster edge: the band grid (120 m)
    stops short of it, and without the rim the sky shows between the bands and terrain_horizon."""
    import bmesh
    ob = bpy.data.objects["terrain_far"]; bm = bmesh.new(); bm.from_mesh(ob.data)
    x0, y0 = ground["x0"] + 150, -(ground["z0"] + ground["size"]) + 150; x1, y1 = ground["x0"] + ground["size"] - 150, -ground["z0"] - 150
    def covered(c): return math.hypot(c.x, c.y) > TRIM_M and x0 < c.x < x1 and y0 < c.y < y1
    gone = [f for f in bm.faces if covered(f.calc_center_median())]
    bmesh.ops.delete(bm, geom=gone, context="FACES"); bm.to_mesh(ob.data); bm.free()
    return len(gone)


def _murram_car_park():
    """build_scene.py SR32 car-park asphalt is mixc(noise, #3A3C3A, #4A4C49); recolour that mix to murram."""
    srgb = lambda h: tuple(((int(h[i:i + 2], 16) / 255 + 0.055) / 1.055) ** 2.4 for i in (1, 3, 5))
    want = (srgb("#3A3C3A"), srgb("#4A4C49")); n = 0
    for nd in bpy.data.materials["terrain_site_mat"].node_tree.nodes:
        if nd.type == "MIX" and getattr(nd, "data_type", "") == "RGBA":
            got = (tuple(nd.inputs[6].default_value)[:3], tuple(nd.inputs[7].default_value)[:3])
            if all(abs(x - y) < 1e-4 for g_, w_ in zip(got, want) for x, y in zip(g_, w_)):
                nd.inputs[6].default_value = (*MURRAM[0], 1); nd.inputs[7].default_value = (*MURRAM[1], 1); n += 1
    return n


def _facades():
    """Storey window rows on walls (normal z < 0.5) and a per-building tone from a 30 m Voronoi cell."""
    names = ["buildings_mat"] + [m.name for m in bpy.data.materials if m.name.startswith("suburbs_wall_")]
    done = []
    for name in names:
        m = bpy.data.materials.get(name)
        if not m or not m.node_tree or m.get("far_land_facade"): continue
        t = m.node_tree; p = next(nd for nd in t.nodes if nd.type == "BSDF_PRINCIPLED")
        base = p.inputs["Base Color"].links[0].from_socket if p.inputs["Base Color"].is_linked else tuple(p.inputs["Base Color"].default_value)
        pos = t.nodes.new("ShaderNodeTexCoord").outputs["Object"]
        xyz = _n(t, "ShaderNodeSeparateXYZ", Vector=pos).outputs
        geo = t.nodes.new("ShaderNodeNewGeometry")
        nz = _n(t, "ShaderNodeSeparateXYZ", Vector=geo.outputs["Normal"]).outputs[2]
        wall = _math(t, "LESS_THAN", _math(t, "ABSOLUTE", nz), 0.5)
        cell = _n(t, "ShaderNodeSeparateColor", Color=_n(t, "ShaderNodeTexVoronoi", Vector=pos, Scale=1 / 30).outputs["Color"]).outputs[0]
        tone = FACADE_TONES[0]
        for k, c in enumerate(FACADE_TONES[1:], 1):
            tone = _mix(t, _math(t, "GREATER_THAN", cell, k / len(FACADE_TONES)), tone, c)
        if name == "buildings_mat":  # keep the vertex colour where it is not near white (roofs, coloured walls)
            pale = _ramp(t, _n(t, "ShaderNodeRGBToBW", Color=base).outputs[0], 0.45, 0.65)
            tone = _mix(t, _math(t, "MULTIPLY", pale, wall), base, tone)
        else:
            tone = _mix(t, 0.5, base, tone)
        floor = _math(t, "FRACT", _math(t, "DIVIDE", xyz[2], 3.2))
        row = _math(t, "MULTIPLY", _math(t, "GREATER_THAN", floor, 0.34), _math(t, "LESS_THAN", floor, 0.82))
        bay = _math(t, "LESS_THAN", _math(t, "FRACT", _math(t, "DIVIDE", _math(t, "ADD", xyz[0], xyz[1]), 2.1)), 0.66)
        glass = _math(t, "MULTIPLY", _math(t, "MULTIPLY", row, bay), wall)
        col = _mix(t, glass, tone, (0.07, 0.09, 0.10))
        t.links.new(col, p.inputs["Base Color"])
        m["far_land_facade"] = "Visualization: generic window rows and tones, not surveyed"; done.append(name)
    return done


def build(scene, root):
    root = Path(root).resolve()
    if bpy.data.node_groups.get("far_land_grade"): raise RuntimeError("far_land already applied")
    ground = json.loads((root / "app/public/data/manifest.json").read_text())["ground"]
    trimmed = _trim_far(scene, ground[1])
    band_mat = _band_material(root, ground[1])
    bands = [o for o in scene.objects if o.name.startswith("horizon_band_")]
    for o in bands: o.data.materials.clear(); o.data.materials.append(band_mat)
    _wrap_image(bpy.data.materials["terrain_site_mat"], 0.35, site=True)
    for name, keep in (("terrain_far_mat", 0.3), ("far_land_band_mat", 0.35), ("terrain_horizon_mat", 0.45)):
        _wrap_image(bpy.data.materials[name], keep)
    report = {"claim": CLAIM, "terrain_far_faces_trimmed": trimmed, "bands_retextured": len(bands),
              "car_park_mix_nodes_to_murram": _murram_car_park(), "facade_materials": _facades()}
    print("FAR_LAND_BUILD " + json.dumps(report), flush=True)
    return report


def detail_site_ground(root):
    """After materials_pbr: the open ground outside the site masks (murram and grass from the imagery classes)
    takes the CC0 Ground109 colour, roughness and normal at a stronger contrast than the paved masks, so no
    flat slab remains (lead review of pass 1, C19 bottom left). Call after materials_pbr.apply."""
    import materials_pbr as pbr
    m = bpy.data.materials["terrain_site_mat"]; t = m.node_tree
    if m.get("far_land_ground_detail"): return 0
    p = next(nd for nd in t.nodes if nd.type == "BSDF_PRINCIPLED")
    masks = pbr._terrain_masks(t); m1, m2 = masks["site_regions.png"], masks["site_regions2.png"]
    on = _math(t, "ADD", _math(t, "ADD", m1.outputs["Red"], m1.outputs["Green"]), _math(t, "ADD", m1.outputs["Blue"], m2.outputs["Blue"]))
    off = _math(t, "SUBTRACT", 1.0, on, clamp=True)
    geom = t.nodes.new("ShaderNodeNewGeometry"); repeat = pbr.SURFACES["Ground109"][0]
    pos = _n(t, "ShaderNodeVectorMath", _operation="MULTIPLY", i0=geom.outputs["Position"], i1=(1 / repeat,) * 3).outputs[0]
    g = t.nodes.new("ShaderNodeGroup"); g.node_tree = pbr._texture_group(Path(root), "Ground109")
    t.links.new(pos, g.inputs["Position"]); t.links.new(geom.outputs["Normal"], g.inputs["Normal"])
    bw = _n(t, "ShaderNodeRGBToBW", Color=g.outputs["Color"]).outputs[0]
    fine = _math(t, "ADD", 0.62, _math(t, "MULTIPLY", bw, 0.9))
    broad = _math(t, "ADD", 0.72, _math(t, "MULTIPLY", _n(t, "ShaderNodeTexNoise", Vector=geom.outputs["Position"], Scale=1 / 18, Detail=4.0).outputs["Fac"], 0.56))
    gain = _math(t, "ADD", 1.0, _math(t, "MULTIPLY", off, _math(t, "SUBTRACT", _math(t, "MULTIPLY", fine, broad), 1.0)))
    base = p.inputs["Base Color"].links[0].from_socket
    col = _n(t, "ShaderNodeMix", _data_type="RGBA", _blend_type="MULTIPLY", i0=1.0, i6=base,
             i7=_n(t, "ShaderNodeCombineColor", Red=gain, Green=gain, Blue=gain).outputs[0]).outputs[2]
    t.links.new(col, p.inputs["Base Color"])
    if p.inputs["Normal"].is_linked:
        nm = _n(t, "ShaderNodeMix", _data_type="VECTOR", i0=off); t.links.new(p.inputs["Normal"].links[0].from_socket, nm.inputs[4])
        t.links.new(g.outputs["Normal"], nm.inputs[5]); t.links.new(nm.outputs[1], p.inputs["Normal"])
    rl = p.inputs["Roughness"].links[0].from_socket if p.inputs["Roughness"].is_linked else p.inputs["Roughness"].default_value
    t.links.new(_n(t, "ShaderNodeMix", _data_type="FLOAT", i0=off, i2=rl, i3=g.outputs["Roughness"]).outputs[0], p.inputs["Roughness"])
    m["far_land_ground_detail"] = "estimated: CC0 Ground109 detail on the open ground outside the site masks"
    return 1
