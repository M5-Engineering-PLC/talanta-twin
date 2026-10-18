"""Seeded traffic Visualization from the shared, derived keep-left lane source."""
import json, math, random, struct
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

CLAIM = 'estimated vehicle mix and queues; derived lane placement; Visualization'


def build(scene, root):
    """Build static low-poly vehicles from shared lanes and return software counts."""
    root = Path(root).resolve()
    source = json.loads((root / 'blender/data/ngong_lanes.json').read_text())
    manifest = json.loads((root / 'app/public/data/manifest.json').read_text())
    meta = manifest['terrain'][0]
    raw = (root / 'app/public/data' / meta['file']).read_bytes()
    heights = struct.unpack('<' + 'f' * (len(raw) // 4), raw)
    dg = bpy.context.evaluated_depsgraph_get()
    surfaces = [(ob, BVHTree.FromObject(ob, dg)) for name in ('ngong_road', 'terrain_site', 'terrain_far') if (ob := bpy.data.objects.get(name))]
    collection = bpy.data.collections.new('traffic_visualization')
    scene.collection.children.link(collection)
    collection['claim'] = CLAIM
    rng = random.Random(704)
    verts, faces, slots = [], [], []
    paints = ['#EBE9DF', '#282A2D', '#B23C32', '#365B85', '#8D9A81', '#D0D3D5', '#693F88', '#E5B642']
    palette = paints + ['#233540', '#191B1D']
    materials = []
    for i, hx in enumerate(palette):
        mat = bpy.data.materials.new('traffic_plain_%02d' % i)
        rgb = tuple(int(hx[j:j + 2], 16) / 255 for j in (1, 3, 5))
        mat.diffuse_color = (*rgb, 1)
        materials.append(mat)

    def ground(x, z):
        for ob, bvh in surfaces:
            hit = bvh.ray_cast(ob.matrix_world.inverted() @ Vector((x, -z, 3000)), Vector((0, 0, -1)))[0]
            if hit is not None:
                return (ob.matrix_world @ hit).z + (.015 if ob.name == 'ngong_road' else .415)
        fc = (x - meta['x0']) / meta['dx'] - .5
        fr = (z - meta['z0']) / meta['dz'] - .5
        c = max(0, min(meta['nx'] - 2, math.floor(fc)))
        r = max(0, min(meta['nz'] - 2, math.floor(fr)))
        tx, tz = max(0, min(1, fc - c)), max(0, min(1, fr - r))
        at = lambda rr, cc: heights[rr * meta['nx'] + cc]
        return ((at(r, c) * (1 - tx) + at(r, c + 1) * tx) * (1 - tz)
                + (at(r + 1, c) * (1 - tx) + at(r + 1, c + 1) * tx) * tz
                - (x * x + z * z) / (2 * 6371000) + .415)

    def box(origin, tangent, center, size, material):
        start = len(verts)
        dx, dy = tangent
        for a, b, c in ((-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1), (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)):
            x, y, z = (center[0] + a * size[0] / 2, center[1] + b * size[1] / 2, center[2] + c * size[2] / 2)
            verts.append((origin[0] + dx * x - dy * y, origin[1] + dy * x + dx * y, origin[2] + z))
        for f in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            faces.append(tuple(start + j for j in f))
            slots.append(material)

    endpoints = [p for road in source['roads'][1:] for lane in road['lanes'] for p in (lane['app'][0], lane['app'][-1])]
    counts = dict(car=0, bus=0, nganya=0)
    minimum_gap = float('inf')
    for lane in source['roads'][0]['lanes']:
        points = lane['app'][1:-1]
        cumulative = [0]
        for a, b in zip(points, points[1:]): cumulative.append(cumulative[-1] + math.dist(a, b))
        junctions = [cumulative[i] for i, p in enumerate(points) if any(math.dist(p, q) < 25 for q in endpoints)]
        station = rng.uniform(20, 55)
        previous, previous_length = None, 0
        while station < cumulative[-1] - 20:
            i = 1
            while i < len(cumulative) - 1 and cumulative[i] < station: i += 1
            a, b = points[i - 1], points[i]
            span = cumulative[i] - cumulative[i - 1]
            t = (station - cumulative[i - 1]) / span
            x, z = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            pick = rng.random()
            kind = 'bus' if lane['leftLane'] and pick < .16 else 'nganya' if pick < (.45 if lane['leftLane'] else .08) else 'car'
            L, W, H = {'car': (4.5, 1.85, 1.5), 'bus': (11, 2.5, 3.2), 'nganya': (7, 2.25, 2.7)}[kind]
            if previous is not None: minimum_gap = min(minimum_gap, station - previous - (L + previous_length) / 2)
            if x * x + z * z < 1480 ** 2:
                origin, tangent = (x, -z, ground(x, z)), ((b[0] - a[0]) / span, -(b[1] - a[1]) / span)
                paint = 0 if kind == 'bus' else rng.randrange(len(paints))
                box(origin, tangent, (0, 0, H * .42 + .3), (L, W, H * .65), paint)
                box(origin, tangent, (-L * .06, 0, H * .82 + .3), (L * (.55 if kind == 'car' else .88), W * .86, H * .35), len(paints))
                if kind == 'bus': box(origin, tangent, (0, 0, H * .28), (L * 1.002, W * 1.002, .28), 2)
                for axle in (-L * .32, L * .32):
                    for side in (-1, 1): box(origin, tangent, (axle, side * W * .45, .36), (.68, .24, .68), len(paints) + 1)
                counts[kind] += 1
            previous, previous_length = station, L
            queue = any(0 < j - station < 90 for j in junctions)
            station += rng.uniform(15, 20) if queue else rng.uniform(35, 85)
    mesh = bpy.data.meshes.new('traffic_plain_mesh')
    mesh.from_pydata(verts, [], faces)
    for material in materials: mesh.materials.append(material)
    for poly, slot in zip(mesh.polygons, slots): poly.material_index = slot
    mesh.update()
    ob = bpy.data.objects.new('traffic_Visualization', mesh)
    collection.objects.link(ob)
    ob['claim'] = CLAIM
    triangles = len(faces) * 2
    assert minimum_gap >= 3, minimum_gap
    assert triangles < 60000, triangles
    report = dict(evidence='software; Visualization', seed=704, vehicles=sum(counts.values()), counts=counts, triangles=triangles, minimum_bumper_gap_m=round(minimum_gap, 3))
    collection['report'] = json.dumps(report)
    print('TRAFFIC_BUILD ' + json.dumps(report), flush=True)
    return report
