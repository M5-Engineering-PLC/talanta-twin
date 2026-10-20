"""Estimated suburban context. References inform geometry and never become textures."""
import json, math, random, sqlite3, struct
from collections import defaultdict
from pathlib import Path

import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

CLAIM = "estimated: roof form and colour by eye from lead renders and frame 07:04; footprints Overture/OSM"
LIMIT = 400000
SEED = 704


def _material(name, hx):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    try: m.use_nodes = True
    except AttributeError: pass
    def linear(v): return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
    rgb = tuple(linear(int(hx[i:i + 2], 16) / 255) for i in (1, 3, 5))
    m.diffuse_color = (*rgb, 1)
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*rgb, 1)
    p.inputs['Roughness'].default_value = 0.83
    return m


def _rings(blob):
    # GeoPackage header precedes ordinary WKB. This source uses EPSG:32737 polygons.
    flags = blob[3]; off = 8 + {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[(flags >> 1) & 7]
    endian = '<' if blob[off] else '>'; kind, = struct.unpack_from(endian + 'I', blob, off + 1)
    if kind != 3: raise ValueError(f'Expected 2D POLYGON, received WKB {kind}')
    count, = struct.unpack_from(endian + 'I', blob, off + 5); off += 9; rings = []
    for _ in range(count):
        n, = struct.unpack_from(endian + 'I', blob, off); off += 4
        xy = struct.unpack_from(endian + 'd' * (n * 2), blob, off); off += n * 16
        rings.append(list(zip(xy[::2], xy[1::2]))[:-1])
    return rings


def _inside(p, ring):
    x, y = p; yes = False
    for a, b in zip(ring, ring[1:] + ring[:1]):
        if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]: yes = not yes
    return yes


def _distance(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / max(dx * dx + dy * dy, 1e-12)))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def _footprints(root, origin):
    path = root / 'gis/derived/near_ring_buildings.gpkg'
    with sqlite3.connect(f'file:{path}?mode=ro', uri=True) as db:
        records = db.execute('SELECT fid, id, geom, height_m, height_src FROM near_ring_buildings ORDER BY fid').fetchall()
    rows, grid = {}, defaultdict(list)
    for fid, ident, geom, h, src in records:
        rings = [[(x - origin[0], y - origin[1]) for x, y in r] for r in _rings(geom)]
        pts = rings[0]; xs, ys = zip(*pts); bounds = min(xs), min(ys), max(xs), max(ys)
        rows[fid] = dict(fid=fid, id=ident, rings=rings, height_m=h, height_src=src, bounds=bounds)
        for x in range(math.floor((bounds[0] - 1) / 50), math.floor((bounds[2] + 1) / 50) + 1):
            for y in range(math.floor((bounds[1] - 1) / 50), math.floor((bounds[3] + 1) / 50) + 1): grid[x, y].append(fid)
    return rows, grid


def _match(p, rows, grid):
    candidates = grid.get((math.floor(p[0] / 50), math.floor(p[1] / 50)), [])
    for fid in candidates:
        r = rows[fid]['rings']
        if _inside(p, r[0]) and not any(_inside(p, hole) for hole in r[1:]): return rows[fid]
    return None


def _clip(poly, axis, mid, sign):
    out = []
    for a, b in zip(poly, poly[1:] + poly[:1]):
        da = sign * (a[0] * axis[0] + a[1] * axis[1] - mid)
        db = sign * (b[0] * axis[0] + b[1] * axis[1] - mid)
        if da >= -1e-8: out.append(a)
        if (da > 1e-8 and db < -1e-8) or (da < -1e-8 and db > 1e-8):
            t = da / (da - db); out.append(tuple(a[k] + t * (b[k] - a[k]) for k in range(3)))
    return out


class _Batch:
    def __init__(self): self.v, self.f, self.mi, self.fid, self.height, self.src = [], [], [], [], [], []
    def face(self, points, material, row):
        if len(points) < 3: return
        i = len(self.v); self.v.extend(points); self.f.append(tuple(range(i, len(self.v))))
        self.mi.append(material); self.fid.append(row['fid']); self.height.append(row['height_m'])
        self.src.append({'open_buildings_2023': 0, 'osm_floors': 1, 'default_by_area': 2}[row['height_src']])
    def object(self, name, collection, materials):
        me = bpy.data.meshes.new(name); me.from_pydata(self.v, [], self.f); me.update()
        for m in materials: me.materials.append(m)
        me.polygons.foreach_set('material_index', self.mi)
        for key, typ, field, vals in (('building_fid', 'INT', 'value', self.fid), ('height_m', 'FLOAT', 'value', self.height), ('height_src', 'INT', 'value', self.src)):
            me.attributes.new(key, typ, 'FACE').data.foreach_set(field, vals)
        ob = bpy.data.objects.new(name, me); collection.objects.link(ob); ob['claim'] = CLAIM
        ob['height_src_codes'] = '0=open_buildings_2023, 1=osm_floors, 2=default_by_area'
        return ob
    def triangles(self): return sum(len(f) - 2 for f in self.f)


def _cube(batch, center, size, mi, row):
    x, y, z = center; sx, sy, sz = (q / 2 for q in size)
    v = [(x + a * sx, y + b * sy, z + c * sz) for c in (-1, 1) for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
        batch.face([v[i] for i in f], mi, row)


def _tree_collection(kind, mats, rng):
    collection = bpy.data.collections.new('suburbs_proto_' + kind)
    bm = bmesh.new()
    trunk = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True, segments=6, radius1=0.34, radius2=0.16, depth=8)
    for v in trunk['verts']: v.co.z += 4
    crowns = {'broad': [(0, 0, 11, 5.6, 0.8), (-3, 1, 9, 4.4, 0.8), (3, -1, 10, 4.5, 0.9)],
              'jacaranda': [(0, 0, 9, 5.5, 0.62), (-3, -1, 8, 4.0, 0.7), (3, 2, 8.5, 4.0, 0.6)],
              'eucalyptus': [(0, 0, 16, 3.6, 1.7), (2, 0, 12, 3, 1.3), (-2, 1, 14, 3, 1.4)]}[kind]
    for i, (x, y, z, radius, stretch) in enumerate(crowns):
        g = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=radius)
        for v in g['verts']:
            v.co *= rng.uniform(0.86, 1.14); v.co.z *= stretch; v.co += Vector((x, y, z))
        for f in {f for v in g['verts'] for f in v.link_faces}: f.material_index = 1 + i % (len(mats) - 1)
    me = bpy.data.meshes.new('suburbs_' + kind); bm.to_mesh(me); bm.free()
    for m in mats: me.materials.append(m)
    for p in me.polygons: p.use_smooth = True
    ob = bpy.data.objects.new('suburbs_' + kind, me); collection.objects.link(ob); ob['claim'] = CLAIM
    me.calc_loop_triangles()
    return collection, len(me.loop_triangles)


def build(scene, root):
    """Add seeded roofs and suburban canopy, and return the software geometry counts."""
    root = Path(root).resolve()
    if bpy.data.collections.get('suburbs_context'): raise RuntimeError('suburbs_context already exists. Call build once per loaded scene.')
    original = bpy.data.objects.get('buildings')
    if not original or original.type != 'MESH': raise RuntimeError('The source buildings mesh is missing.')
    if original.matrix_world != __import__('mathutils').Matrix.Identity(4): raise RuntimeError('Expected buildings in the scene coordinate frame.')
    manifest = json.loads((root / 'app/public/data/manifest.json').read_text())
    rows, grid = _footprints(root, manifest['origin_utm'])
    rng = random.Random(SEED)
    collection = bpy.data.collections.new('suburbs_context'); scene.collection.children.link(collection)
    roof_hex = ['#8E3B2A', '#A2482F', '#7A4B33', '#6E7680', '#3F5F4A']
    materials = [_material('suburbs_roof_' + h[1:], h) for h in roof_hex]
    wall_mats = [_material('suburbs_wall_' + h[1:], h) for h in ('#E8E3D6', '#E7D7B5', '#DCC394')]
    materials += wall_mats + [_material('suburbs_concrete', '#9B978C'), _material('suburbs_window', '#34454B')]
    batch = _Batch(); source = original.data
    # The exporter writes each building as roof triangles followed by wall triangles.
    groups, tops, sides = [], [], []
    for p in source.polygons:
        if p.normal.z > 0.7:
            if sides: groups.append((tops, sides)); tops, sides = [], []
            tops.append(p.index)
        else: sides.append(p.index)
    if tops: groups.append((tops, sides))
    remove, wall_assign, matched, low, midrise, original_tops = set(), {}, {}, 0, 0, 0
    for tops, sides in groups:
        p = source.polygons[tops[0]]
        pts = [source.vertices[i].co for i in p.vertices]
        probe = (sum(v.x for v in pts) / len(pts), sum(v.y for v in pts) / len(pts))
        row = _match(probe, rows, grid)
        if row is None:
            if math.hypot(*probe) <= 1500: raise RuntimeError(f'No footprint for near building at {probe}')
            continue
        ring = row['rings'][0]
        # Area centroid, rather than a triangle center, determines the 1.5 km ring.
        area2 = cx = cy = 0
        for a, b in zip(ring, ring[1:] + ring[:1]):
            cross = a[0] * b[1] - b[0] * a[1]; area2 += cross; cx += (a[0] + b[0]) * cross; cy += (a[1] + b[1]) * cross
        if abs(area2) < 1e-8: continue
        if math.hypot(cx / (3 * area2), cy / (3 * area2)) > 1500: continue
        mi = rng.choices(range(5), weights=(32, 23, 27, 12, 6))[0]; wall = rng.randrange(3)
        for pi in sides: wall_assign[pi] = len(source.materials) + wall
        ztop = pts[0].z; floors = max(1, int(math.floor(row['height_m'] / 3.2 + 0.5)))
        matched[row['fid']] = dict(id=row['id'], height_m=row['height_m'], height_src=row['height_src'], eave_z=ztop, floors_estimated=floors)
        if floors <= 3:
            low += 1; remove.update(tops); original_tops += len(tops)
            # Pick the footprint's longest edge as the ridge direction.
            a, b = max(zip(ring, ring[1:] + ring[:1]), key=lambda ab: math.dist(*ab))
            length = math.dist(a, b); axis = (-(b[1] - a[1]) / length, (b[0] - a[0]) / length)
            roofpts = [source.vertices[i].co for pi in tops for i in source.polygons[pi].vertices]
            vals = [v.x * axis[0] + v.y * axis[1] for v in roofpts]
            lo, hi = min(vals), max(vals); center = (lo + hi) / 2; half = max((hi - lo) / 2, 0.1)
            rise = min(4.5, max(0.8, half * rng.uniform(0.35, 0.55)))
            def raised(v): return (v[0], v[1], v[2] + max(0, 1 - abs(v[0] * axis[0] + v[1] * axis[1] - center) / half) * rise)
            for pi in tops:
                triangle = [tuple(source.vertices[i].co) for i in source.polygons[pi].vertices]
                for sign in (-1, 1): batch.face([raised(v) for v in _clip(triangle, axis, center, sign)], mi, row)
            # Close the gables and stepped outlines without filling footprint courtyards.
            for pi in sides:
                upper = [tuple(source.vertices[i].co) for i in source.polygons[pi].vertices if abs(source.vertices[i].co.z - ztop) < 0.01]
                if len(upper) != 2: continue
                # Follow the wall triangle winding for the gable's outward normal.
                a, b = upper
                if (Vector(b) - Vector(a)).cross(Vector((0, 0, 1))).dot(source.polygons[pi].normal) < 0: a, b = b, a
                chain = [a, b]
                va = a[0] * axis[0] + a[1] * axis[1] - center; vb = b[0] * axis[0] + b[1] * axis[1] - center
                if va * vb < 0:
                    t = va / (va - vb); chain.insert(1, tuple(a[k] + t * (b[k] - a[k]) for k in range(3)))
                for a, b in zip(chain, chain[1:]):
                    if max(raised(a)[2], raised(b)[2]) > ztop + 0.01: batch.face([a, b, raised(b), raised(a)], 5 + wall, row)
        else:
            midrise += 1
            for pi in tops: wall_assign[pi] = len(source.materials) + 3
            # Parapets and window rows follow the original footprint walls.
            for pi in sides:
                upper = [tuple(source.vertices[i].co) for i in source.polygons[pi].vertices if abs(source.vertices[i].co.z - ztop) < 0.01]
                if len(upper) != 2: continue
                a, b = upper; length = math.dist(a, b)
                if length < 0.5: continue
                t = ((b[0] - a[0]) / length, (b[1] - a[1]) / length)
                n = source.polygons[pi].normal
                batch.face([a, b, (b[0], b[1], ztop + 0.75), (a[0], a[1], ztop + 0.75)], 5 + wall, row)
                batch.face([(a[0], a[1], ztop + 0.75), (b[0], b[1], ztop + 0.75), (b[0] - n.x * .22, b[1] - n.y * .22, ztop + .75), (a[0] - n.x * .22, a[1] - n.y * .22, ztop + .75)], 8, row)
                cols = min(8, int(length / 3.2)); levels = min(26, floors)
                for level in range(levels):
                    z = ztop - row['height_m'] + (level + .55) * row['height_m'] / floors
                    for col in range(cols):
                        d = (col + .5) * length / cols; x = a[0] + d * t[0] + n.x * .035; y = a[1] + d * t[1] + n.y * .035
                        batch.face([(x - t[0] * .65, y - t[1] * .65, z - .7), (x + t[0] * .65, y + t[1] * .65, z - .7), (x + t[0] * .65, y + t[1] * .65, z + .7), (x - t[0] * .65, y - t[1] * .65, z + .7)], 9, row)
            # Repeated tanks share one collection. Locations use a source roof triangle.
            c = sum((v for v in pts), Vector()) / len(pts)
            matched[row['fid']]['tank_location'] = [c.x, c.y, ztop + 0.3]
    if not low: raise RuntimeError('No low buildings matched the source mesh.')
    # Copy before editing. Other objects that share this mesh keep their original geometry.
    replacement = source.copy()
    for m in wall_mats + [materials[8]]: replacement.materials.append(m)
    for pi, mi in wall_assign.items(): replacement.polygons[pi].material_index = mi
    bm = bmesh.new(); bm.from_mesh(replacement); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in remove], context='FACES')
    bm.to_mesh(replacement); bm.free(); original.data = replacement
    original['claim'] = CLAIM; original['height_source_note'] = 'Original wall coordinates unchanged. Source heights and height_src retained in suburbs_buildings metadata.'
    roofs = batch.object('suburbs_buildings', collection, materials)
    roofs['building_sources'] = json.dumps(matched, separators=(',', ':'))
    roofs['roof_height_note'] = 'Source height defines the eave. Pitched roof rise and parapets are added estimates.'
    added = batch.triangles()
    # One shared tank collection for every mid-rise block.
    tank_col = bpy.data.collections.new('suburbs_proto_tank'); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True, segments=10, radius1=.8, radius2=.8, depth=1.6)
    for v in bm.verts: v.co.z += .8
    me = bpy.data.meshes.new('suburbs_tank'); bm.to_mesh(me); bm.free(); me.materials.append(_material('suburbs_tank_dark', '#30302D'))
    tank = bpy.data.objects.new('suburbs_tank', me); tank_col.objects.link(tank); tank['claim'] = CLAIM
    me.calc_loop_triangles(); tank_tris = len(me.loop_triangles)
    def instance(name, proto, loc, scale=1):
        ob = bpy.data.objects.new(name, None); collection.objects.link(ob)
        ob.instance_type = 'COLLECTION'; ob.instance_collection = proto; ob.location = loc
        ob.scale = (scale,) * 3; ob.rotation_euler.z = rng.uniform(0, math.tau); ob['claim'] = CLAIM
        return ob
    for fid, row in matched.items():
        if 'tank_location' in row:
            ob = instance(f'suburbs_tank_{fid}', tank_col, row['tank_location']); ob['building_fid'] = fid
            added += tank_tris
    bark = _material('suburbs_bark', '#685843')
    greens = [_material('suburbs_leaf_' + h[1:], h) for h in ('#334C2A', '#4B6234', '#627242', '#657466', '#756486')]
    prototypes = [_tree_collection('broad', [bark, greens[0], greens[1]], rng), _tree_collection('jacaranda', [bark, greens[1], greens[4]], rng), _tree_collection('eucalyptus', [bark, greens[3], greens[0]], rng)]
    dg = bpy.context.evaluated_depsgraph_get()
    terrain = [(ob, BVHTree.FromObject(ob, dg)) for name in ('terrain_site', 'terrain_far') if (ob := bpy.data.objects.get(name))]
    if not terrain: raise RuntimeError('Terrain is missing.')
    # Ray tests exclude all existing road surfaces, including rebuilt Ngong Road.
    road_bvh = [(ob, BVHTree.FromObject(ob, dg)) for name in ('roads', 'ngong_road') if (ob := bpy.data.objects.get(name))]
    mid = json.loads((root / 'blender/data/site_plan.json').read_text())['ngong']['mid']
    road = [(x, -z) for x, z in mid]
    occupied = defaultdict(list); trees = 0; species = [0, 0, 0]
    for attempt in range(45000):
        if trees >= 2500: break
        x, y = rng.uniform(-1490, 1490), rng.uniform(-1490, 1490)
        if x*x + y*y > 1490**2: continue
        # Ngong Road runs broadly east-west. Its interpolated north side is Lavington.
        seg = next(((a, b) for a, b in zip(road, road[1:]) if min(a[0], b[0]) <= x <= max(a[0], b[0])), None)
        if not seg: continue
        a, b = seg; ry = a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0])
        if y < ry + 34: continue
        p = (x, y)
        candidates = grid.get((math.floor(x / 50), math.floor(y / 50)), [])
        if any(_inside(p, rows[fid]['rings'][0]) or any(_distance(p, a, b) < 3.0 for a, b in zip(rows[fid]['rings'][0], rows[fid]['rings'][0][1:] + rows[fid]['rings'][0][:1])) for fid in candidates): continue
        cell = math.floor(x / 12), math.floor(y / 12)
        if any(math.dist(p, q) < 10 for ix in range(cell[0]-1, cell[0]+2) for iy in range(cell[1]-1, cell[1]+2) for q in occupied[ix, iy]): continue
        ray = Vector((x, y, 3000)); down = Vector((0, 0, -1))
        if any(bvh.ray_cast(ob.matrix_world.inverted() @ ray, down)[0] is not None for ob, bvh in road_bvh): continue
        ground = None
        for ob, bvh in terrain:
            hit = bvh.ray_cast(ob.matrix_world.inverted() @ ray, down)[0]
            if hit is not None: ground = (ob.matrix_world @ hit).z; break
        if ground is None: continue
        k = rng.choices(range(3), weights=(72, 16, 12))[0]; proto, tris = prototypes[k]
        if added + tris > LIMIT: break
        ob = instance(f'suburbs_tree_{trees:04d}', proto, (x, y, ground), rng.uniform(.82, 1.4))
        ob['species'] = ('broad-crown', 'jacaranda', 'eucalyptus')[k]
        ob['placement'] = 'estimated: mature canopy between houses north of Ngong Road'
        occupied[cell].append(p); added += tris; trees += 1; species[k] += 1
    if added > LIMIT: raise RuntimeError(f'Suburbs exceed triangle budget: {added}')
    report = dict(evidence='software / artistic visualization', seed=SEED, low_buildings=low, midrise_buildings=midrise, trees=trees, species=species, added_triangles=added, roof_detail_triangles=batch.triangles(), tank_triangles=midrise*tank_tris, removed_flat_roof_triangles=original_tops, triangle_limit=LIMIT)
    collection['claim'] = CLAIM; collection['report'] = json.dumps(report)
    print('SUBURBS_BUILD ' + json.dumps(report), flush=True)
    return report
