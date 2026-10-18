"""Estimated CC0 surface detail with metre-based projection and preserved palette."""
import ast, json, os
from pathlib import Path

import bpy

VERSION = 1
SOURCES = ('blender/build_scene.py', 'blender/build_site_detail.py',
           'blender/build_bowl_detail.py', 'blender/context/suburbs.py')
# Repeat widths are artistic estimates, not dimensions from the source footage.
SURFACES = {
    'PavingStones146': (2.4, 18.0), 'Asphalt031': (2.0, 30.0),
    'Ground109': (3.0, 24.0), 'Grass005': (3.0, 22.0),
    'RoofingTiles013A': (2.4, 12.0), 'CorrugatedSteel005': (2.0, 14.0),
    'Concrete034': (3.0, 20.0),
}
MAPPING = {}
for _set, _names in {
    'PavingStones146': 'paving paving_pbr footpath_paving apron_paving',
    'Asphalt031': 'roads_mat ngong_asphalt',
    'Ground109': 'earth earth_pbr service_murram planter_soil',
    'Grass005': 'grass grass_pbr runoff_grass',
    'Concrete034': 'concrete concrete_pbr concrete_light concrete_light_pbr concrete_shade concrete_shade_pbr tread_concrete kerb_concrete drain_channel median_concrete barrier_concrete planter_wall canopy_pale suburbs_concrete suburbs_wall_E8E3D6 suburbs_wall_E7D7B5 suburbs_wall_DCC394',
    'RoofingTiles013A': 'suburbs_roof_8E3B2A suburbs_roof_A2482F suburbs_roof_7A4B33',
    'CorrugatedSteel005': 'suburbs_roof_6E7680 suburbs_roof_3F5F4A canopy_roof',
}.items():
    MAPPING.update(dict.fromkeys(_names.split(), _set))
TERRAIN = 'terrain_site_mat'
UNCHANGED = '''white_shell white_shell_pbr membrane membrane_pbr facade_void facade_void_pbr
colonnade_louvre glass_pbr plinth_glass seat_green seat_red seat_green_pbr seat_red_pbr seat_plastic
spear_white spear_pbr rail_steel roof_steel_white cable_dark catwalk_grating floodlight_head
night_floodlight_lens pitch_turf training_grass track track_pbr track_surface road_paint marking_paint pitch_line line_paint
palm_trunk palm_frond jacaranda_leaf mast_white pole_grey night_lamp_warm night_flood flag_plain
bollard_grey jet_spray fence_palisade sign_frame sign_blank bay_paint opening_trim_dark
night_fascia_white night_fascia_cyan night_fascia_violet night_ring_white goal_white paint_white
speaker_white speaker_grille vip_glass_lit flag_pole corner_flag_yellow dugout_shell screen_black
buildings_mat haze terrain_far_mat terrain_horizon_mat suburbs_bark suburbs_window suburbs_tank_dark
st_0_round_leaf st_1_acacia_leaf sh_0_green_m sh_1_red_m'''.split()
UNCHANGED += ['suburbs_leaf_' + h for h in ('334C2A', '4B6234', '627242', '657466', '756486')]
UNCHANGED += ['tree_' + str(i) + '_' + s + '_leaf' for i, s in enumerate(('round', 'acacia', 'eucalyptus'))]


def _node(tree, kind, name=None):
    n = tree.nodes.new(kind)
    if name: n.name = name
    n['claim'] = 'estimated'
    return n


def _link(tree, value, socket):
    if hasattr(value, 'is_output'): tree.links.new(value, socket)
    else:
        if socket.type == 'RGBA':
            value = (*value[:3], 1) if hasattr(value, '__len__') else (value, value, value, 1)
        socket.default_value = value


def _math(t, op, a, b=0):
    n = _node(t, 'ShaderNodeMath'); n.operation = op
    _link(t, a, n.inputs[0]); _link(t, b, n.inputs[1])
    return n.outputs[0]


def _vec(t, op, a, b=(0, 0, 0)):
    n = _node(t, 'ShaderNodeVectorMath'); n.operation = op
    _link(t, a, n.inputs[0]); _link(t, b, n.inputs[1])
    return n.outputs['Vector']


def _xyz(t, vals):
    n = _node(t, 'ShaderNodeCombineXYZ')
    for value, socket in zip(vals, n.inputs): _link(t, value, socket)
    return n.outputs[0]


def _split(t, value):
    n = _node(t, 'ShaderNodeSeparateXYZ'); _link(t, value, n.inputs[0])
    return list(n.outputs)


def _mix(t, factor, a, b, op='MIX'):
    n = _node(t, 'ShaderNodeMixRGB'); n.blend_type = op
    for val, socket in zip((factor, a, b), n.inputs): _link(t, val, socket)
    return n.outputs[0]


def _image(root, name, kind):
    path = root / 'blender/assets/textures' / name / f'{name}_2K-JPG_{kind}.jpg'
    image_name = f'talanta_pbr:{name}:{kind}'
    im = bpy.data.images.get(image_name)
    if im is None:
        im = bpy.data.images.load(str(path), check_existing=False); im.name = image_name
        im.colorspace_settings.name = 'sRGB' if kind == 'Color' else 'Non-Color'
    base = Path(bpy.data.filepath).parent if bpy.data.filepath else root
    im.filepath = '//' + Path(os.path.relpath(path, base)).as_posix()
    im['claim'] = 'estimated'
    im['repository_path'] = path.relative_to(root).as_posix()
    return im


def _texture_group(root, name):
    key = 'talanta_pbr:' + name
    if key in bpy.data.node_groups: return bpy.data.node_groups[key]
    t = bpy.data.node_groups.new(key, 'ShaderNodeTree'); t['claim'] = 'estimated'
    for label, direction, kind in [('Position', 'INPUT', 'NodeSocketVector'), ('Normal', 'INPUT', 'NodeSocketVector'),
                                    ('Color', 'OUTPUT', 'NodeSocketColor'), ('Roughness', 'OUTPUT', 'NodeSocketFloat'),
                                    ('Normal', 'OUTPUT', 'NodeSocketVector')]:
        t.interface.new_socket(name=label, in_out=direction, socket_type=kind)
    inp, out = _node(t, 'NodeGroupInput'), _node(t, 'NodeGroupOutput')
    pos, norm = _split(t, inp.outputs['Position']), _split(t, inp.outputs['Normal'])
    weights = [_math(t, 'POWER', _math(t, 'ABSOLUTE', n), 4) for n in norm]
    total = _math(t, 'ADD', _math(t, 'ADD', weights[0], weights[1]), weights[2])
    weights = [_math(t, 'DIVIDE', w, _math(t, 'MAXIMUM', total, 1e-8)) for w in weights]
    colors, roughs, normals = [], [], []
    for axis, (u, v) in enumerate(((1, 2), (0, 2), (0, 1))):
        uv = _xyz(t, (pos[u], pos[v], 0)); samples = {}
        for kind in ('Color', 'Roughness', 'NormalGL'):
            n = _node(t, 'ShaderNodeTexImage', f'{kind}_{axis}'); n.image = _image(root, name, kind)
            n.extension = 'REPEAT'; t.links.new(uv, n.inputs['Vector']); samples[kind] = n.outputs['Color']
        colors.append(_vec(t, 'MULTIPLY', samples['Color'], _xyz(t, (weights[axis],) * 3)))
        roughs.append(_math(t, 'MULTIPLY', samples['Roughness'], weights[axis]))
        decoded = _split(t, _vec(t, 'SUBTRACT', _vec(t, 'MULTIPLY', samples['NormalGL'], (2, 2, 2)), (1, 1, 1)))
        # NormalGL uses tangent axes. Rotate each sample into its projection plane.
        world = [None] * 3
        world[u], world[v] = _math(t, 'MULTIPLY', decoded[0], 0.35), _math(t, 'MULTIPLY', decoded[1], 0.35)
        world[axis] = _math(t, 'MULTIPLY', decoded[2], _math(t, 'SIGN', norm[axis]))
        normals.append(_vec(t, 'MULTIPLY', _xyz(t, world), _xyz(t, (weights[axis],) * 3)))
    t.links.new(_vec(t, 'ADD', _vec(t, 'ADD', colors[0], colors[1]), colors[2]), out.inputs['Color'])
    t.links.new(_math(t, 'ADD', _math(t, 'ADD', roughs[0], roughs[1]), roughs[2]), out.inputs['Roughness'])
    t.links.new(_vec(t, 'NORMALIZE', _vec(t, 'ADD', _vec(t, 'ADD', normals[0], normals[1]), normals[2])), out.inputs['Normal'])
    return t


def _sample(t, root, name, meters):
    repeat, macro = SURFACES[name]
    geom = _node(t, 'ShaderNodeNewGeometry', 'PBR_world_metres')
    pos = _vec(t, 'MULTIPLY', geom.outputs['Position'], (meters / repeat,) * 3)
    g = _node(t, 'ShaderNodeGroup', 'PBR_' + name); g.node_tree = _texture_group(root, name)
    t.links.new(pos, g.inputs['Position']); t.links.new(geom.outputs['Normal'], g.inputs['Normal'])
    bw = _node(t, 'ShaderNodeRGBToBW'); t.links.new(g.outputs['Color'], bw.inputs[0])
    # Neutralized albedo keeps the tuned hue and limits texture contrast.
    fine = _math(t, 'ADD', 0.9, _math(t, 'MULTIPLY', bw.outputs[0], 0.2))
    noise = _node(t, 'ShaderNodeTexNoise', 'PBR_macro_wear'); noise.inputs['Scale'].default_value = meters / macro
    noise.inputs['Detail'].default_value = 3; t.links.new(geom.outputs['Position'], noise.inputs['Vector'])
    broad = _math(t, 'ADD', 0.86, _math(t, 'MULTIPLY', noise.outputs['Fac'], 0.28))
    return _math(t, 'MULTIPLY', fine, broad), g.outputs['Roughness'], g.outputs['Normal']


def _input(socket):
    return socket.links[0].from_socket if socket.is_linked else tuple(socket.default_value) if socket.type == 'RGBA' else tuple(socket.default_value) if socket.type == 'VECTOR' else socket.default_value


def _terrain_masks(t):
    masks = {}
    for n in t.nodes:
        if n.type == 'SEPARATE_COLOR' and n.inputs['Color'].is_linked:
            src = n.inputs['Color'].links[0].from_node
            if src.type == 'TEX_IMAGE' and src.image:
                masks[Path(src.image.filepath).name] = n
    return masks


def _catalog(root):
    names = set(MAPPING) | set(UNCHANGED) | {TERRAIN}
    for path in SOURCES:
        for n in ast.walk(ast.parse((root / path).read_text())):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ('mat', 'principled', 'image_mat', 'attr_mat', 'nodes_mat', '_material'):
                if n.args and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str): names.add(n.args[0].value)
    return names


def apply(scene, root=None):
    """Apply estimated CC0 detail once and write the material inventory at the repository root."""
    root = Path(root).resolve() if root is not None else Path(__file__).resolve().parents[1]
    meters = scene.unit_settings.scale_length or 1.0
    # Fail before material edits if a required file is absent.
    for name in SURFACES:
        for kind in ('Color', 'Roughness', 'NormalGL'):
            path = root / 'blender/assets/textures' / name / f'{name}_2K-JPG_{kind}.jpg'
            if not path.is_file(): raise FileNotFoundError(f'Missing CC0 map: {path.relative_to(root)}')
    records = []
    names = _catalog(root) | {m.name for m in bpy.data.materials}
    for name in sorted(names):
        m = bpy.data.materials.get(name); texture = MAPPING.get(name)
        if m is not None and m.use_nodes and not m.get('materials_pbr_version'):
            emissive = any(n.type == 'EMISSION' or (n.type == 'BSDF_PRINCIPLED' and
                           (n.inputs.get('Emission Strength') and (n.inputs['Emission Strength'].is_linked or
                            (n.inputs['Emission Strength'].default_value > 0 and
                             (n.inputs['Emission Color'].is_linked or max(n.inputs['Emission Color'].default_value[:3]) > 0))))) for n in m.node_tree.nodes)
            if emissive: texture = None
        record = dict(material=name, claim='estimated', present=m is not None, action='unchanged', reason='Preserve existing surface or unknown material.')
        if texture or name == TERRAIN:
            record.update(action='textured' if m else 'planned', texture_set=texture or 'masked regions',
                          reason='Preserve palette and add CC0 surface detail.', projection='world-space triplanar, metres',
                          scale_claim='estimated', meters_per_blender_unit=meters)
            sets = [texture] if texture else ['Grass005', 'PavingStones146', 'Asphalt031']
            record['textures'] = {s: dict(repeat_m=SURFACES[s][0], macro_m=SURFACES[s][1],
                maps={k: f'blender/assets/textures/{s}/{s}_2K-JPG_{k}.jpg' for k in ('Color', 'Roughness', 'NormalGL')}) for s in sets}
            record['paving_module_m'] = 0.4 if 'PavingStones146' in sets else None
            if m is not None and m.get('materials_pbr_version') != VERSION:
                m.use_nodes = True; t = m.node_tree
                p = next((n for n in t.nodes if n.type == 'BSDF_PRINCIPLED'), None)
                if p is None: raise ValueError(f'{name}: Principled BSDF is missing')
                tint = _input(p.inputs['Base Color'])
                if name == TERRAIN:
                    masks = _terrain_masks(t)
                    if not {'site_regions.png', 'site_regions2.png'} <= masks.keys():
                        raise ValueError('terrain_site_mat: region masks are missing')
                    detail, rough, normal = 1.0, _input(p.inputs['Roughness']), _input(p.inputs['Normal'])
                    for s, factor in [('Grass005', masks['site_regions.png'].outputs['Red']),
                                      ('PavingStones146', masks['site_regions.png'].outputs['Green']),
                                      ('Asphalt031', masks['site_regions2.png'].outputs['Blue'])]:
                        d, r, n = _sample(t, root, s, meters)
                        detail, rough, normal = _mix(t, factor, detail, d), _mix(t, factor, rough, r), _mix(t, factor, normal, n)
                else:
                    detail, rough, normal = _sample(t, root, texture, meters)
                color = _mix(t, 1.0, tint, detail, 'MULTIPLY')
                t.links.new(color, p.inputs['Base Color']); t.links.new(rough, p.inputs['Roughness']); t.links.new(normal, p.inputs['Normal'])
                m['claim'] = 'estimated'; m['materials_pbr_version'] = VERSION
                m['materials_pbr_tint'] = list(p.inputs['Base Color'].default_value)
                m['materials_pbr_set'] = texture or 'masked regions'
            if m is not None: record['tint_linear'] = list(m.get('materials_pbr_tint', m.diffuse_color))
        records.append(record)
    report = dict(date='2026-10-18', source='blender/materials_pbr.py', project='Talanta Twin', status='software', claim='estimated',
                  version=VERSION, handoff='Apply after all builders and before save or bake.',
                  assumptions=['Texture repeat widths and macro variation are artistic estimates.',
                               'Paving repeat assumes about six 0.4 m modules per image.',
                               'Warm suburb roofs use tiles. Gray and green roofs use corrugated sheet.',
                               'Existing red earth and service murram colors remain the Ground109 tint.',
                               'Grass005 excludes the striped pitch and training turf.',
                               'World projection assumes fixed geometry during the bake.'],
                  materials=records)
    path = root / 'blender/data/materials_pbr_map.json'
    content = json.dumps(report, indent=2) + '\n'
    if not path.exists() or path.read_text() != content: path.write_text(content)
    return report
