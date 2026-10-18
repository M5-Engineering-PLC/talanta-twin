"""Procedural photographic treatment for CPU Cycles. All effects are artistic simulation."""
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

STRENGTHS = {
    "roughness_coarse": 0.06,  # Maximum coarse roughness offset in either direction.
    "roughness_fine": 0.03,  # Maximum fine roughness offset in either direction.
    "noise_coarse_scale": 0.6,  # World-space noise frequency per meter.
    "noise_fine_scale": 18.0,  # Fine world-space noise frequency per meter.
    "color_variation": 0.10,  # Maximum color darkening from broad noise (panel-to-panel paint tone).
    "dirt": 0.15,  # Maximum AO dirt darkening in crevices; open faces stay clean (new stadium).
    "ao_distance": 0.6,  # Local crevice search distance in meters, one sample.
    "edge_highlight": 0.04,  # White coating highlight, without simulated damage.
    "rain_streaks": 0.05,  # Maximum darkening on fin and roof-edge crevices.
    "streak_scale": 3.0,  # Lateral streak frequency per meter.
    "streak_vertical_scale": 0.025,  # Low vertical frequency for gravity-aligned streaks.
    "haze_day": 0.12,  # Maximum distant daylight sky blend (lowered: 0.22 flattened the image).
    "haze_night": 0.055,  # Maximum distant night sky blend.
    "mist_start": 150.0,  # Clear foreground distance in meters.
    "mist_depth": 6000.0,  # Distance to full aerial perspective in meters.
    # Pass 1 aerial haze and golden grade, used when an HDRI preset set scene["talanta_haze_rgb"] (sky_hdri.py)
    "aerial_haze_max": 0.36,  # Haze blend at full mist depth (pass 2: 0.55 -> 0.36, the far land read as a beige smear).
    "aerial_mist_start": 200.0,  # Clear foreground distance in meters.
    "aerial_mist_depth": 20000.0,  # Linear mist depth; the Ngong Hills ridge (about 18 km) reaches about 0.5.
    "aerial_gamma": 0.7,  # Haze = max x mist^gamma: faster build-up over the first few kilometres.
    "aerial_blue": 0.25,  # Pull of the haze colour toward a cool blue-grey (0.58, 0.66, 0.78), keeping its brightness.
    # Pass 2: fixed haze per distance band (horizon.py terrain bands 3-8.5 km, then the terrain_horizon
    # layers: 6-12.5 km, 12.5-20 km with the Ngong Hills, beyond 20 km),
    # lightest near, strongest far, so the far land keeps its structure and tone variation.
    "aerial_band_haze": {"horizon_band_1": 0.12, "horizon_band_2": 0.18, "horizon_band_3": 0.26, "horizon_band_4": 0.36,
                         "terrain_horizon": 0.42, "terrain_horizon_hills": 0.58, "terrain_horizon_far": 0.70},
    "aerial_far_tint": (0.85, 0.95),  # terrain_horizon layers: blue pull and brightness of their haze colour (hills read blue, as in 06)
    "aerial_far_tint_weight": {"horizon_band_3": 0.35, "horizon_band_4": 0.7},  # the outer bands blend toward it (no seam)
    "grade_saturation": 1.12,  # Richer greens and warm earth; applied before the view transform.
    "grade_warm": (1.05, 1.0, 0.93),  # Warm gain on mid-tones and highlights.
    "grade_warm_rise": (0.03, 0.18),  # Display-equivalent luminance where the warm gain fades in.
    "grade_warm_fall": (0.55, 1.4),  # ...and fades out again, so the white roof stays neutral.
    "grade_look": "AgX - High Contrast",  # More contrast than the default Medium High Contrast.
    "glare": 0.035,  # Fog-glow blend with the original image.
    "glare_threshold": 2.0,  # Linear brightness threshold for highlights.
    "vignette": 0.055,  # Maximum smooth corner darkening.
    "distortion": 0.0,  # Off: with Fit the barrel zoomed C06 by about 5% and broke the frozen framing.
    "dispersion": 0.0005,  # Small chromatic lens dispersion.
    "grain": 0.03,  # Fine, centered multiplicative film grain amplitude.
    "sensor_width": 36.0,  # Physical camera sensor width in millimeters.
    "aerial_distance": 150.0,  # Target distance above which DOF is disabled, meters.
    "f_stop": 2.8,  # Close-camera aperture.
    "sun_angle": 0.53,  # Solar angular diameter in degrees.
}


def _math(tree, operation, a, b=0.0, clamp=False):
    node = tree.nodes.new("ShaderNodeMath")
    node.operation = operation
    node.use_clamp = clamp
    for socket, value in zip(node.inputs, (a, b)):
        if hasattr(value, "node"):
            tree.links.new(value, socket)
        else:
            socket.default_value = value
    return node.outputs[0]


def _mix(tree, blend, factor, a, b):
    node = tree.nodes.new("ShaderNodeMixRGB")
    node.blend_type = blend
    for socket, value in zip(node.inputs, (factor, a, b)):
        if hasattr(value, "node"):
            tree.links.new(value, socket)
        else:
            socket.default_value = value
    return node.outputs[0]


def _noise(tree, vector, scale):
    node = tree.nodes.new("ShaderNodeTexNoise")
    node.inputs["Scale"].default_value = scale
    node.inputs["Detail"].default_value = 1.0
    tree.links.new(vector, node.inputs["Vector"])
    return node.outputs[0]


def _material_group():
    tree = bpy.data.node_groups.new("Talanta photo surface", "ShaderNodeTree")
    for name, kind, direction in (
        ("Color", "NodeSocketColor", "INPUT"),
        ("Roughness", "NodeSocketFloat", "INPUT"),
        ("White metal", "NodeSocketFloat", "INPUT"),
        ("Rain mask", "NodeSocketFloat", "INPUT"),
        ("Color", "NodeSocketColor", "OUTPUT"),
        ("Roughness", "NodeSocketFloat", "OUTPUT"),
    ):
        tree.interface.new_socket(name=name, in_out=direction, socket_type=kind)
    src = tree.nodes.new("NodeGroupInput")
    dst = tree.nodes.new("NodeGroupOutput")
    geo = tree.nodes.new("ShaderNodeNewGeometry")
    coarse = _noise(tree, geo.outputs["Position"], STRENGTHS["noise_coarse_scale"])
    fine = _noise(tree, geo.outputs["Position"], STRENGTHS["noise_fine_scale"])
    rough = src.outputs["Roughness"]
    for noise, strength in ((coarse, "roughness_coarse"), (fine, "roughness_fine")):
        offset = _math(tree, "MULTIPLY", _math(tree, "SUBTRACT", noise, 0.5), 2 * STRENGTHS[strength])
        rough = _math(tree, "ADD", rough, offset)
    rough = _math(tree, "ADD", rough, 0, clamp=True)
    ao = tree.nodes.new("ShaderNodeAmbientOcclusion")
    ao.samples = 1
    ao.only_local = True
    ao.inputs["Distance"].default_value = STRENGTHS["ao_distance"]
    occlusion = _math(tree, "SUBTRACT", 1.0, ao.outputs["AO"], clamp=True)
    dirt = _math(tree, "MULTIPLY", occlusion, STRENGTHS["dirt"])
    broad = _math(tree, "MULTIPLY", coarse, STRENGTHS["color_variation"])
    dark = _math(tree, "ADD", dirt, broad)
    # Stretch world-space noise along Z. Restrict streaks to overhang materials
    # and local occlusion under fins/roof edges, rather than staining whole surfaces.
    stretch = tree.nodes.new("ShaderNodeVectorMath")
    stretch.operation = "MULTIPLY"
    stretch.inputs[1].default_value = (1.0, 1.0, STRENGTHS["streak_vertical_scale"])
    tree.links.new(geo.outputs["Position"], stretch.inputs[0])
    streak = _noise(tree, stretch.outputs["Vector"], STRENGTHS["streak_scale"])
    rain = _math(tree, "MULTIPLY", streak, occlusion)
    rain = _math(tree, "MULTIPLY", rain, src.outputs["Rain mask"])
    rain = _math(tree, "MULTIPLY", rain, STRENGTHS["rain_streaks"])
    color = _mix(tree, "MULTIPLY", 1.0, src.outputs["Color"], _math(tree, "SUBTRACT", 1.0, _math(tree, "ADD", dark, rain)))
    # Pointiness is a cheap mesh-curvature approximation, not evidence of wear.
    edge = _math(tree, "MULTIPLY", _math(tree, "SUBTRACT", geo.outputs["Pointiness"], 0.5), 2.0, clamp=True)
    edge = _math(tree, "MULTIPLY", edge, src.outputs["White metal"])
    edge = _math(tree, "MULTIPLY", edge, STRENGTHS["edge_highlight"])
    color = _mix(tree, "MIX", edge, color, (1.0, 1.0, 1.0, 1.0))
    tree.links.new(color, dst.inputs["Color"])
    tree.links.new(rough, dst.inputs["Roughness"])
    return tree


def _materials(scene):
    # Split shared coatings only where the object needs a restricted effect.
    variants = {}
    material_flags = {}
    for ob in scene.objects:
        name = ob.name.lower()
        edge = any(word in name for word in ("fin", "lattice", "spear"))
        rain = any(word in name for word in ("fin", "fascia", "shoulder", "roof"))
        for slot in ob.material_slots:
            mat = slot.material
            if mat is None or not mat.node_tree:
                continue
            # White coated metal can have zero metallic weight. Identify this
            # scene's coatings explicitly, never infer white from a textured BSDF.
            white = any(word in mat.name.lower() for word in ("white_shell", "spear", "louvre"))
            flags = (bool(edge and white), bool(rain and (white or "membrane" in mat.name.lower())))
            if any(flags):
                key = (mat, flags)
                if key not in variants:
                    variants[key] = mat.copy()
                    variants[key].name = mat.name + " photo"
                slot.material = variants[key]
            material_flags[slot.material] = flags
    group = _material_group()
    visited = set()

    def wrap(tree, flags):
        if tree in visited:
            return
        visited.add(tree)
        for node in list(tree.nodes):
            if node.type == "GROUP" and node.node_tree:
                wrap(node.node_tree, flags)
            if node.type != "BSDF_PRINCIPLED":
                continue
            layer = tree.nodes.new("ShaderNodeGroup")
            layer.node_tree = group
            layer.label = "Photo surface: subtle new coating"
            layer.inputs["White metal"].default_value = float(flags[0])
            layer.inputs["Rain mask"].default_value = float(flags[1])
            layer.location = (node.location.x - 220, node.location.y)
            for name in ("Base Color", "Roughness"):
                target = node.inputs[name]
                inlet = layer.inputs["Color" if name == "Base Color" else name]
                outlet = layer.outputs[inlet.name]
                if target.is_linked:
                    tree.links.new(target.links[0].from_socket, inlet)
                else:
                    inlet.default_value = target.default_value
                tree.links.new(outlet, target)
    for mat, flags in material_flags.items():
        wrap(mat.node_tree, flags)


def _cameras(scene):
    # Newly loaded camera locations need evaluation before world-space distances.
    for layer in scene.view_layers:
        layer.update()
    path = Path(__file__).resolve().parents[1] / "app/cameras/manifest.json"
    manifest = json.loads(path.read_text())
    targets = {c["id"]: Vector((c["target"][0], -c["target"][2], c["target"][1])) for c in manifest["cameras"]}
    for ob in scene.objects:
        if ob.type != "CAMERA":
            continue
        camera = ob.data
        camera.sensor_width = STRENGTHS["sensor_width"]
        target = targets.get(ob.name.split(".")[0])
        if camera.dof.focus_object:
            target = camera.dof.focus_object.matrix_world.translation
        if target is None:
            # Reuse an explicitly configured target distance for other cameras.
            distance = camera.dof.focus_distance
        else:
            distance = (target - ob.matrix_world.translation).length
        camera.dof.focus_distance = distance
        camera.dof.use_dof = camera.type == "PERSP" and 0 < distance <= STRENGTHS["aerial_distance"]
        camera.dof.aperture_fstop = STRENGTHS["f_stop"]


def _index_socket(render):
    return next(o.name for o in render.outputs if o.name in ("IndexOB", "Object Index", "Index OB"))


def _aerial_grade(scene, tree, render, source, layer):
    """Depth haze toward the HDRI horizon colour, then saturation and a warm mid-tone gain (Visualization)."""
    scene.world.mist_settings.start = STRENGTHS["aerial_mist_start"]
    scene.world.mist_settings.depth = STRENGTHS["aerial_mist_depth"]
    rgb = list(scene["talanta_haze_rgb"])
    lum = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]
    blue = (0.58, 0.66, 0.78); blue_l = 0.2126 * blue[0] + 0.7152 * blue[1] + 0.0722 * blue[2]
    k = STRENGTHS["aerial_blue"]
    tint = [(1 - k) * c + k * b * lum / blue_l for c, b in zip(rgb, blue)] + [1.0]
    land = _math(tree, "LESS_THAN", render.outputs["Depth"], 1e8)  # the sky is not hazed twice
    haze = _math(tree, "POWER", render.outputs["Mist"], STRENGTHS["aerial_gamma"])
    haze = _math(tree, "MULTIPLY", _math(tree, "MULTIPLY", haze, STRENGTHS["aerial_haze_max"]), land)
    bands = [(41 + i, bpy.data.objects[n], h) for i, (n, h) in enumerate(STRENGTHS["aerial_band_haze"].items()) if n in bpy.data.objects]
    if bands:
        inside, fixed, far = 0.0, 0.0, 0.0
        for index, ob, h in bands:
            ob.pass_index = index
            mask = tree.nodes.new("CompositorNodeIDMask")
            tree.links.new(render.outputs[_index_socket(render)], mask.inputs[0])
            if "Index" in mask.inputs: mask.inputs["Index"].default_value = index
            else: mask.index = index
            inside = _math(tree, "ADD", inside, mask.outputs[0]); fixed = _math(tree, "ADD", fixed, _math(tree, "MULTIPLY", mask.outputs[0], h))
            wt = 1.0 if ob.name.startswith("terrain_horizon") else STRENGTHS["aerial_far_tint_weight"].get(ob.name, 0.0)
            if wt: far = _math(tree, "ADD", far, _math(tree, "MULTIPLY", mask.outputs[0], wt))
        haze = _math(tree, "ADD", _math(tree, "MULTIPLY", haze, _math(tree, "SUBTRACT", 1.0, inside, clamp=True)), fixed)
        kb, kl = STRENGTHS["aerial_far_tint"]
        far_tint = [kl * ((1 - kb) * c + kb * b * lum / blue_l) for c, b in zip(rgb, blue)] + [1.0]
        tint = _mix(tree, "MIX", far, tint, far_tint)
    image = _mix(tree, "MIX", haze, source, tint)
    hs = tree.nodes.new("CompositorNodeHueSat")
    tree.links.new(image, hs.inputs["Image"])
    hs.inputs["Saturation"].default_value = STRENGTHS["grade_saturation"]
    image = hs.outputs["Image"]
    bw = tree.nodes.new("CompositorNodeRGBToBW")
    tree.links.new(image, bw.inputs[0])
    shown = _math(tree, "MULTIPLY", bw.outputs[0], 2 ** scene.view_settings.exposure)
    (a0, a1), (b0, b1) = STRENGTHS["grade_warm_rise"], STRENGTHS["grade_warm_fall"]
    rise = _math(tree, "MULTIPLY", _math(tree, "SUBTRACT", shown, a0), 1 / (a1 - a0), clamp=True)
    fall = _math(tree, "MULTIPLY", _math(tree, "SUBTRACT", b1, shown), 1 / (b1 - b0), clamp=True)
    warm = _mix(tree, "MULTIPLY", 1.0, image, (*STRENGTHS["grade_warm"], 1.0))
    keep_haze_cool = _math(tree, "SUBTRACT", 1.0, _math(tree, "MULTIPLY", haze, 1.5), clamp=True)
    return _mix(tree, "MIX", _math(tree, "MULTIPLY", _math(tree, "MULTIPLY", rise, fall), keep_haze_cool), image, warm)


def _compositor(scene, mode):
    modern = hasattr(scene, "compositing_node_group")
    if modern:
        tree = scene.compositing_node_group
        if tree is None:
            tree = bpy.data.node_groups.new("Talanta photo compositor", "CompositorNodeTree")
            tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
            scene.compositing_node_group = tree
        output = next((n for n in tree.nodes if n.type == "GROUP_OUTPUT" and n.is_active_output), None)
        if output is None:
            output = tree.nodes.new("NodeGroupOutput")
    else:
        scene.use_nodes = True
        tree = scene.node_tree
        output = next((n for n in tree.nodes if n.type == "COMPOSITE" and n.is_active_output), None)
        if output is None:
            output = tree.nodes.new("CompositorNodeComposite")
    layer = scene.view_layers[0]
    layer.use_pass_mist = True
    if mode == "day" and scene.get("talanta_haze_rgb") is not None:  # passes before the Render Layers node reads them
        layer.use_pass_z = True; layer.use_pass_object_index = True
    scene.world.mist_settings.start = STRENGTHS["mist_start"]
    scene.world.mist_settings.depth = STRENGTHS["mist_depth"]
    scene.world.mist_settings.falloff = "LINEAR"
    render = tree.nodes.new("CompositorNodeRLayers")
    render.layer = layer.name
    source = output.inputs[0].links[0].from_socket if output.inputs[0].is_linked else render.outputs["Image"]
    # Use the Nishita sky's elevation to tint daylight aerial perspective.
    sky = next((n for n in scene.world.node_tree.nodes if n.type == "TEX_SKY"), None)
    low_sun = sky is not None and sky.sun_elevation < math.radians(20)
    tint = (0.018, 0.027, 0.055, 1) if mode == "night" else (0.55, 0.62, 0.72, 1) if low_sun else (0.46, 0.62, 0.82, 1)
    aerial = mode == "day" and scene.get("talanta_haze_rgb") is not None
    if aerial:
        image = _aerial_grade(scene, tree, render, source, layer)
    else:
        haze = _math(tree, "MULTIPLY", render.outputs["Mist"], STRENGTHS["haze_" + mode])
        image = _mix(tree, "MIX", haze, source, tint)
    glare = tree.nodes.new("CompositorNodeGlare")
    if "Type" in glare.inputs:
        glare.inputs["Type"].default_value = "Fog Glow"
        glare.inputs["Quality"].default_value = "Low"
        glare.inputs["Threshold"].default_value = STRENGTHS["glare_threshold"]
    else:
        glare.glare_type = "FOG_GLOW"
        glare.quality = "LOW"
        glare.threshold = STRENGTHS["glare_threshold"]
        glare.size = 6
    tree.links.new(image, glare.inputs["Image"])
    image = _mix(tree, "MIX", STRENGTHS["glare"], image, glare.outputs["Image"])
    lens = tree.nodes.new("CompositorNodeLensdist")
    lens.inputs["Distortion"].default_value = STRENGTHS["distortion"]
    lens.inputs["Dispersion"].default_value = STRENGTHS["dispersion"]
    # No Fit: the frozen camera framing must stay identical with the layer on or off.
    if "Fit" in lens.inputs:
        lens.inputs["Fit"].default_value = False
    else:
        lens.use_fit = False
    tree.links.new(image, lens.inputs["Image"])
    image = lens.outputs["Image"]
    if modern:
        coords = tree.nodes.new("CompositorNodeImageCoordinates")
        tree.links.new(image, coords.inputs["Image"])
        vector = coords.outputs["Normalized"]
        distance = tree.nodes.new("ShaderNodeVectorMath")
        distance.operation = "DISTANCE"
        tree.links.new(vector, distance.inputs[0])
        distance.inputs[1].default_value = (0.5, 0.5, 0.0)
        radius = _math(tree, "MULTIPLY", distance.outputs["Value"], math.sqrt(2))
        vignette = _math(tree, "MULTIPLY", _math(tree, "POWER", radius, 2), STRENGTHS["vignette"])
        image = _mix(tree, "MULTIPLY", 1.0, image, _math(tree, "SUBTRACT", 1, vignette))
        width = scene.render.resolution_x * scene.render.resolution_percentage / 100
        grain = _noise(tree, vector, width)
    else:
        # Blender 4.x compositor uses procedural legacy textures for these masks.
        tex = bpy.data.textures.new("Talanta radial vignette", type="BLEND")
        tex.progression = "SPHERICAL"
        node = tree.nodes.new("CompositorNodeTexture")
        node.texture = tex
        image = _mix(tree, "MULTIPLY", STRENGTHS["vignette"], image, node.outputs["Value"])
        tex = bpy.data.textures.new("Talanta fine grain", type="NOISE")
        node = tree.nodes.new("CompositorNodeTexture")
        node.texture = tex
        grain = node.outputs["Value"]
    grain = _math(tree, "MULTIPLY", _math(tree, "SUBTRACT", grain, 0.5), 2 * STRENGTHS["grain"])
    image = _mix(tree, "MULTIPLY", 1.0, image, _math(tree, "ADD", 1, grain))
    tree.links.new(image, output.inputs[0])


def apply_lookdev(scene, mode):
    """Apply once per loaded scene. Mode is day or night. Keep exposure and lenses."""
    if mode not in ("day", "night"):
        raise ValueError("lookdev mode must be 'day' or 'night'")
    if scene.get("talanta_lookdev"):
        return
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = STRENGTHS["grade_look"] if scene.get("talanta_haze_rgb") is not None else "AgX - Medium High Contrast"
    _cameras(scene)
    _materials(scene)
    for ob in scene.objects:
        if ob.type == "LIGHT" and ob.data.type == "SUN":
            ob.data.angle = math.radians(STRENGTHS["sun_angle"])
        if ob.name == "haze_volume":
            ob.hide_render = True
    # Also disconnect a legacy world volume; the opt-in layer never scatters volumes.
    if scene.world and scene.world.node_tree:
        for node in scene.world.node_tree.nodes:
            if node.type == "OUTPUT_WORLD":
                for link in list(node.inputs["Volume"].links):
                    scene.world.node_tree.links.remove(link)
    _compositor(scene, mode)
    scene["talanta_lookdev"] = mode
