"""Estimated, seeded foliage replacements with shared meshes and export LOD links."""
import json, math, random, zlib
from collections import Counter
from pathlib import Path

import bpy
from mathutils import Vector

CLAIM = 'estimated: species mix and crown form from historian frames and concept 06; positions unchanged'
LIMIT = 1500000
SEED = 704
TINTS = ('#284A2D', '#3B6034', '#52703C', '#687951', '#796195')
VARIANTS = [('broadleaf_%02d' % i, 'broadleaf', i % 4) for i in range(7)] + [
    ('jacaranda', 'broadleaf', 4), ('eucalyptus_00', 'eucalyptus', 2),
    ('eucalyptus_01', 'eucalyptus', 3), ('palm_00', 'palm', 1), ('palm_01', 'palm', 2)]


def _material(root, tint):
    name = 'canopy_tint_%d' % tint
    if name in bpy.data.materials: return bpy.data.materials[name]
    m = bpy.data.materials.new(name); m.use_nodes = True; m['claim'] = CLAIM
    rgb = tuple(((int(TINTS[tint][i:i + 2], 16) / 255 + 0.055) / 1.055) ** 2.4 for i in (1, 3, 5))
    m.diffuse_color = (*rgb, 1)
    n, l = m.node_tree.nodes, m.node_tree.links; p = n.get('Principled BSDF')
    p.inputs['Roughness'].default_value = 0.84
    folder = 'jacaranda_tree' if tint == 4 else 'island_tree_02'
    path = root / 'blender/assets/foliage' / folder / (folder + '_leaves_diff_1k.jpg')
    tex = n.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(str(path), check_existing=True)
    mix = n.new('ShaderNodeMixRGB'); mix.blend_type = 'MULTIPLY'; mix.inputs[0].default_value = 0.7
    mix.inputs[2].default_value = (*rgb, 1); l.new(tex.outputs['Color'], mix.inputs[1])
    uv = n.new('ShaderNodeTexCoord'); xy = n.new('ShaderNodeSeparateXYZ')
    l.new(uv.outputs['UV'], xy.inputs[0])
    card = n.new('ShaderNodeMath'); card.operation = 'GREATER_THAN'; card.inputs[1].default_value = -0.5
    l.new(xy.outputs['X'], card.inputs[0])
    color = n.new('ShaderNodeMixRGB'); color.inputs[1].default_value = (*rgb, 1)
    l.new(card.outputs[0], color.inputs[0]); l.new(mix.outputs[0], color.inputs[2])
    l.new(color.outputs[0], p.inputs['Base Color'])
    # JPG atlases contain black backgrounds, not source alpha.
    sep = n.new('ShaderNodeSeparateColor'); l.new(tex.outputs['Color'], sep.inputs[0])
    a = n.new('ShaderNodeMath'); a.operation = 'MAXIMUM'
    b = n.new('ShaderNodeMath'); b.operation = 'MAXIMUM'
    l.new(sep.outputs[0], a.inputs[0]); l.new(sep.outputs[1], a.inputs[1])
    l.new(a.outputs[0], b.inputs[0]); l.new(sep.outputs[2], b.inputs[1])
    cut = n.new('ShaderNodeMath'); cut.operation = 'GREATER_THAN'; cut.inputs[1].default_value = 0.025
    l.new(b.outputs[0], cut.inputs[0])
    alpha = n.new('ShaderNodeMixRGB'); alpha.inputs[1].default_value = (1, 1, 1, 1)
    l.new(card.outputs[0], alpha.inputs[0]); l.new(cut.outputs[0], alpha.inputs[2])
    l.new(alpha.outputs[0], p.inputs['Alpha'])
    if hasattr(m, 'surface_render_method'): m.surface_render_method = 'DITHERED'
    elif hasattr(m, 'blend_method'): m.blend_method = 'HASHED'
    m.use_backface_culling = False
    return m


def _bark(root):
    m = bpy.data.materials.get('canopy_bark')
    if m: return m
    m = bpy.data.materials.new('canopy_bark'); m.use_nodes = True; m['claim'] = CLAIM
    p = m.node_tree.nodes.get('Principled BSDF'); p.inputs['Roughness'].default_value = 0.95
    tex = m.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(root / 'blender/assets/foliage/jacaranda_tree/jacaranda_tree_trunk_diff_1k.jpg'), check_existing=True)
    m.node_tree.links.new(tex.outputs['Color'], p.inputs['Base Color'])
    return m


def _geometry(kind, seed, detail):
    rng = random.Random(seed); verts, faces, mats, uvs = [], [], [], []
    def face(points, mat=0, uv=None):
        start = len(verts); verts.extend(points); faces.append(tuple(range(start, len(verts))))
        mats.append(mat); uvs.append(uv or [(-1, -1)] * len(points))
    def branch(a, b, radius, sides=4):
        a, b = Vector(a), Vector(b); axis = (b - a).normalized()
        u = axis.cross(Vector((0, 1, 0))).normalized(); v = axis.cross(u)
        rings = [[a + radius * (math.cos(j * math.tau / sides) * u + math.sin(j * math.tau / sides) * v) for j in range(sides)],
                 [b + radius * 0.45 * (math.cos(j * math.tau / sides) * u + math.sin(j * math.tau / sides) * v) for j in range(sides)]]
        for j in range(sides):
            k = (j + 1) % sides; face([rings[0][j], rings[0][k], rings[1][k], rings[1][j]], 1,
                                     [(j / sides, 0), (k / sides, 0), (k / sides, 1), (j / sides, 1)])
        face(list(reversed(rings[0])), 1); face(rings[1], 1)
    def lobe(c, r):
        # Unequal octahedra produce angular clusters rather than a smooth blob.
        points = [(1, 0, 0), (0, 1, 0), (-1, 0, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
        vs = [tuple(c[j] + p[j] * r[j] * rng.uniform(0.86, 1.14) for j in range(3)) for p in points]
        def triangle(a, b, d):
            if detail != 'high': face([a, b, d]); return
            center = Vector(c)
            def midpoint(x, y):
                p = ((Vector(x) + Vector(y)) / 2 - center)
                unit = Vector((p.x / r[0], p.y / r[1], p.z / r[2])).normalized()
                return center + Vector((unit.x * r[0], unit.y * r[1], unit.z * r[2])) * rng.uniform(0.92, 1.08)
            ab, bd, da = midpoint(a, b), midpoint(b, d), midpoint(d, a)
            for points in ((a, ab, da), (ab, b, bd), (da, bd, d), (ab, bd, da)): face(points)
        for j in range(4):
            triangle(vs[j], vs[(j + 1) % 4], vs[4])
            triangle(vs[(j + 1) % 4], vs[j], vs[5])
    def card(c, size, angle):
        u = Vector((math.cos(angle), math.sin(angle), 0)) * size
        v = Vector((-0.15 * math.sin(angle), 0.15 * math.cos(angle), 1)) * size
        c = Vector(c)
        face([c - u - v, c + u - v, c + u + v, c - u + v], 0,
             [(0, 0.49), (0.18, 0.49), (0.18, 1), (0, 1)])
    if kind == 'palm':
        branch((0, 0, 0), (0.02, 0, 0.91), 0.018, 5 if detail == 'high' else 3)
        count, steps = (14, 6) if detail == 'high' else ((10, 4) if detail == 'web' else (8, 2))
        for j in range(count):
            az = math.tau * j / count + rng.uniform(-0.12, 0.12)
            length = rng.uniform(0.28, 0.4); points = []
            for k in range(steps + 1):
                t = k / steps; rr = length * t; z = 0.91 + 0.26 * math.sin(math.pi * t) * length - 0.18 * t * t
                w = 0.033 * math.sin(math.pi * t) + 0.001
                points.append([(0.02 + math.cos(az) * rr + s * math.sin(az) * w,
                                math.sin(az) * rr - s * math.cos(az) * w, z) for s in (-1, 1)])
            for k in range(steps):
                face([points[k][0], points[k][1], points[k + 1][1], points[k + 1][0]], 0,
                     [(0, 0.49 + k / steps * 0.51), (0.18, 0.49 + k / steps * 0.51),
                      (0.18, 0.49 + (k + 1) / steps * 0.51), (0, 0.49 + (k + 1) / steps * 0.51)])
    else:
        euc = kind == 'eucalyptus'; count = 10 if detail == 'high' else (6 if detail == 'web' else 3)
        branch((0, 0, 0), (0.01, -0.01, 0.78 if euc else 0.61), 0.017 if euc else 0.025, 4 if detail != 'far' else 3)
        for j in range(count):
            az = j * 2.4 + rng.uniform(-0.4, 0.4)
            rr = rng.uniform(0.07, 0.13) if euc else rng.uniform(0.13, 0.25)
            z = 0.49 + 0.43 * j / max(count - 1, 1) if euc else rng.uniform(0.56, 0.82)
            c = (math.cos(az) * rr, math.sin(az) * rr, z)
            r = (0.105, 0.09, 0.13) if euc else (rng.uniform(0.15, 0.22), rng.uniform(0.14, 0.22), rng.uniform(0.13, 0.21))
            lobe(c, r)
            if detail != 'far' and j % 2 == 0: branch((0, 0, 0.38 if not euc else 0.55), c, 0.009, 3)
        for j in range(36 if detail == 'high' else (14 if detail == 'web' else 4)):
            az = rng.uniform(0, math.tau); rr = rng.uniform(0.07, 0.2) if euc else rng.uniform(0.14, 0.35)
            card((math.cos(az) * rr, math.sin(az) * rr, rng.uniform(0.55, 0.92)), 0.06 if euc else 0.09, az)
    low, high = min(v[2] for v in verts), max(v[2] for v in verts)
    verts = [(v[0] / (high - low), v[1] / (high - low), (v[2] - low) / (high - low)) for v in verts]
    return verts, faces, mats, uvs


def _prototype(collection, name, kind, seed, detail, leaf, bark):
    v, f, mats, uv = _geometry(kind, seed, detail)
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], f); me.update()
    if leaf.name == 'canopy_tint_4':
        uv = [[(0.16 + x / 0.18 * 0.83, 0.51 + (y - 0.49) / 0.51 * 0.49) if x >= 0 else (x, y) for x, y in coords] for coords in uv]
    me.materials.append(leaf); me.materials.append(bark); layer = me.uv_layers.new(name='UVMap')
    for poly, mat, coords in zip(me.polygons, mats, uv):
        poly.material_index = mat; poly.use_smooth = True
        for index, xy in zip(poly.loop_indices, coords): layer.data[index].uv = xy
    me.calc_loop_triangles(); me['triangles'] = len(me.loop_triangles); me['claim'] = CLAIM
    o = bpy.data.objects.new(name, me); collection.objects.link(o); o['claim'] = CLAIM
    return o


def _kind(name):
    name = name.lower()
    if 'palm' in name: return 'palm'
    if 'euc' in name: return 'eucalyptus'
    return 'broadleaf'


def _height(obj):
    zs = [v.co.z for v in obj.data.vertices]
    return max(zs) - min(zs), min(zs)


def _targets(scene):
    result = []
    for obj in sorted(scene.objects, key=lambda o: o.name):
        name = obj.name.lower()
        if not (name in ('trees', 'site_trees', 'palms') or name.startswith(('forest_belt', 'tree_instance', 'palm_instance'))): continue
        if obj.get('canopy_done'): continue
        nodes = [(m, n) for m in obj.modifiers if m.type == 'NODES' and m.node_group
                 for n in m.node_group.nodes if n.bl_idname == 'GeometryNodeCollectionInfo']
        if nodes:
            if len(nodes) != 1: raise RuntimeError('Ambiguous foliage collection on ' + obj.name)
            mod, node = nodes[0]; sources = sorted(node.inputs['Collection'].default_value.objects, key=lambda o: o.name)
            if obj.type != 'MESH' or 'proto' not in obj.data.attributes: raise RuntimeError('Missing point prototype attribute on ' + obj.name)
            result.append((obj, mod, node, sources))
        elif obj.instance_type == 'COLLECTION' and obj.instance_collection:
            sources = list(obj.instance_collection.objects)
            if len(sources) != 1 or sources[0].type != 'MESH': raise RuntimeError('Unsupported foliage collection on ' + obj.name)
            result.append((obj, None, None, sources))
        else:
            raise RuntimeError('Non-instance foliage: %s; replace its creation with a collection instance in its build script' % obj.name)
    return result


def build(scene, root):
    """Build foliage variants and swap known scatter instances without changing points."""
    root = Path(root).resolve(); targets = _targets(scene)
    existing = bpy.data.collections.get('canopy_variants')
    if existing:
        if targets: raise RuntimeError('New foliage appeared after canopy build; rebuild the scene before canopy integration')
        return json.loads(existing['report'])
    # Plan all choices before changing scatter data. Keep source heights per point.
    plans, records = [], []
    for obj, mod, node, sources in targets:
        if any(s.type != 'MESH' for s in sources): raise RuntimeError('Non-mesh foliage prototype on ' + obj.name)
        for s in sources:
            if _height(s)[0] <= 0: raise RuntimeError('Zero-height foliage prototype: ' + s.name)
        count = len(obj.data.vertices) if node else 1
        rng = random.Random(SEED + zlib.crc32(obj.name.encode()))
        cells = Counter((math.floor(v.co.x / 40), math.floor(v.co.y / 40)) for v in obj.data.vertices) if node else Counter()
        rows = []
        for i in range(count):
            source_index = obj.data.attributes['proto'].data[i].value if node else 0
            if not 0 <= source_index < len(sources): raise RuntimeError('Prototype index outside collection on ' + obj.name)
            source = sources[source_index]; kind = _kind(source.name)
            pos = obj.data.vertices[i].co if node else Vector((0, 0, 0))
            belt = obj.name == 'trees' and cells[(math.floor(pos.x / 40), math.floor(pos.y / 40))] >= 24
            if belt: kind = 'broadleaf' if rng.random() < 0.9 else 'eucalyptus'
            if kind == 'palm': variant = rng.choice((10, 11))
            elif kind == 'eucalyptus': variant = rng.choice((8, 9))
            else: variant = 7 if obj.name != 'trees' and rng.random() < 0.035 else rng.randrange(7)
            world = obj.matrix_world @ pos
            row = {'source': source_index, 'variant': variant, 'detail': 'far', 'distance': math.hypot(world.x, world.y)}
            rows.append(row); records.append(row)
        plans.append((obj, mod, node, sources, rows))
    triangles = {(i, d): sum(len(f) - 2 for f in _geometry(kind, SEED + i, d)[1])
                 for i, (_, kind, _) in enumerate(VARIANTS) for d in ('high', 'web', 'far')}
    total = sum(triangles[r['variant'], 'far'] for r in records)
    if total > LIMIT: raise RuntimeError('Canopy minimum instance budget %d exceeds %d; no scatter changed' % (total, LIMIT))
    for r in sorted(records, key=lambda r: r['distance']):
        extra = triangles[r['variant'], 'high'] - triangles[r['variant'], 'far']
        if total + extra <= LIMIT: r['detail'] = 'high'; total += extra
    library = bpy.data.collections.new('canopy_variants'); scene.collection.children.link(library)
    library.hide_render = True; library.hide_viewport = True; library['claim'] = CLAIM
    bark = _bark(root); variants = {}
    for i, (name, kind, tint) in enumerate(VARIANTS):
        leaf = _material(root, tint)
        for detail in ('high', 'web', 'far'):
            o = _prototype(library, 'canopy_' + name + '_' + detail, kind, SEED + i, detail, leaf, bark)
            variants[i, detail] = o
        assert triangles[i, 'web'] <= 300
        for detail in ('high', 'web', 'far'):
            o = variants[i, detail]; o['web_lod'] = variants[i, 'web'].name; o.data['web_lod'] = variants[i, 'web'].data.name
    used = Counter(); changed = {}
    for obj, mod, node, sources, rows in plans:
        bank = bpy.data.collections.new('canopy_bank_' + obj.name); library.children.link(bank); bank['claim'] = CLAIM
        keys = sorted({(r['source'], r['variant'], r['detail']) for r in rows})
        for j, (source_index, variant, detail) in enumerate(keys):
            height, base = _height(sources[source_index]); src = variants[variant, detail]
            o = bpy.data.objects.new('%s_%04d' % (bank.name, j), src.data.copy()); bank.objects.link(o)
            for v in o.data.vertices: v.co = (v.co.x * height, v.co.y * height, v.co.z * height + base)
            o['claim'] = CLAIM; o.data['claim'] = CLAIM
            low = bpy.data.objects.new(o.name + '_web', variants[variant, 'web'].data.copy()); library.objects.link(low)
            for v in low.data.vertices: v.co = (v.co.x * height, v.co.y * height, v.co.z * height + base)
            low['claim'] = CLAIM; low.data['claim'] = CLAIM
            o['web_lod'] = low.name; o.data['web_lod'] = low.data.name
        indices = {key: j for j, key in enumerate(keys)}
        if node:
            # Copy the group and mesh so another scatter cannot inherit this remap.
            obj.data = obj.data.copy(); mod.node_group = mod.node_group.copy()
            node = next(n for n in mod.node_group.nodes if n.bl_idname == 'GeometryNodeCollectionInfo')
            node.inputs['Collection'].default_value = bank
            for item, r in zip(obj.data.attributes['proto'].data, rows): item.value = indices[r['source'], r['variant'], r['detail']]
        else: obj.instance_collection = bank
        for r in rows: used[VARIANTS[r['variant']][0] + ':' + r['detail']] += 1
        obj['canopy_done'] = True; obj['canopy_position_claim'] = obj.get('claim', '')
        obj['claim'] = CLAIM; obj['web_lod'] = json.dumps({o.name: o['web_lod'] for o in bank.objects}, sort_keys=True)
        changed[obj.name] = len(rows)
    report = {'evidence': 'software', 'claim': CLAIM, 'instances': len(records), 'scatter_counts': changed,
              'instance_triangles': total, 'triangle_limit': LIMIT, 'usage': dict(used),
              'variant_triangles': {name: {d: triangles[i, d] for d in ('high', 'web', 'far')} for i, (name, _, _) in enumerate(VARIANTS)}}
    library['report'] = json.dumps(report, sort_keys=True)
    print('CANOPY_BUILD ' + json.dumps(report, sort_keys=True), flush=True)
    return report
