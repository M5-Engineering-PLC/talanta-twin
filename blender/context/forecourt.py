"""Footage-led forecourt with explicit estimates and unmodified W1b anchors."""
import json, math
from pathlib import Path

import bpy, bmesh
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
from mathutils.bvhtree import BVHTree

LIMIT = 70000


def _inside(p, ring):
    x, y = p[:2]; yes = False
    for a, b in zip(ring, ring[1:] + ring[:1]):
        if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]: yes = not yes
    return yes


def _material(name, hx):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    rgb = [int(hx[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    rgb = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]
    m.diffuse_color = (*rgb, 1)
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*rgb, 1); p.inputs['Roughness'].default_value = .86
    return m


def _object(name, verts, faces, material, item, collection):
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    me.materials.append(material)
    ob = bpy.data.objects.new(name, me); collection.objects.link(ob)
    for key in ('claim', 'source', 'state'): ob[key] = item[key]
    ob['element_id'] = item['id']; ob['evidence'] = 'software / Visualization'
    return ob


def _surface(name, ring, material, item, collection, height, lift):
    pts = [Vector((x, y, 0)) for x, y in ring]
    triangles = tessellate_polygon([pts])  # returns index triples
    verts, faces = [], []
    def triangle(a, b, c):
        # Subdivide long triangles to follow the terrain instead of bridging slopes.
        if max((a-b).length, (b-c).length, (c-a).length) > 8:
            ab, bc, ca = (a+b)/2, (b+c)/2, (c+a)/2
            for pts in ((a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)): triangle(*pts)
            return
        i = len(verts); points = [a, b, c]
        if (b-a).cross(c-a).z < 0: points.reverse()
        verts.extend((p.x, p.y, height(p.x, p.y) + lift) for p in points); faces.append((i, i+1, i+2))
    for tri in triangles: triangle(*(pts[i] for i in tri))
    return _object(name, verts, faces, material, item, collection)


def _strip(name, pts, width, material, item, collection, height, lift, thickness=0):
    verts, faces = [], []
    for a, b in zip(pts, pts[1:]):
        dx, dy = b[0]-a[0], b[1]-a[1]; length = math.hypot(dx, dy)
        if length < 1e-8: continue
        nx, ny = -dy/length*width/2, dx/length*width/2
        count = max(1, math.ceil(length/3))
        for k in range(count):
            pa = (a[0]+dx*k/count, a[1]+dy*k/count)
            pb = (a[0]+dx*(k+1)/count, a[1]+dy*(k+1)/count)
            ring = [(pa[0]-nx,pa[1]-ny),(pb[0]-nx,pb[1]-ny),(pb[0]+nx,pb[1]+ny),(pa[0]+nx,pa[1]+ny)]
            i = len(verts)
            verts.extend((x,y,height(x,y)+lift) for x,y in ring); faces.append((i,i+1,i+2,i+3))
            if thickness:
                verts.extend((x,y,height(x,y)+lift-thickness) for x,y in ring)
                for j in range(4): faces.append((i+j,i+4+j,i+4+(j+1)%4,i+(j+1)%4))
    return _object(name, verts, faces, material, item, collection)


def _column(name, xy, radius, z, h, material, item, collection, n=8):
    v = [(xy[0]+radius*math.cos(k*math.tau/n),xy[1]+radius*math.sin(k*math.tau/n),z+dz) for dz in (0,h) for k in range(n)]
    f = [tuple(reversed(range(n))),tuple(range(n,2*n))]
    f += [(k,(k+1)%n,(k+1)%n+n,k+n) for k in range(n)]
    return _object(name,v,f,material,item,collection)


def _preserve(scene, collection, names, domain):
    hidden, retained = [], []
    for name in names:
        ob = scene.objects.get(name)
        if ob is None: continue
        # Batched site scatter objects also contain items outside this module's domain.
        if name != 'north_plaza' and ob.type == 'MESH' and not ob.hide_render:
            copy = ob.copy(); copy.data = ob.data.copy(); copy.name = 'fc_retained_' + name
            collection.objects.link(copy)
            bm = bmesh.new(); bm.from_mesh(copy.data)
            selected = [v for v in bm.verts if _inside(ob.matrix_world @ v.co, domain)]
            bmesh.ops.delete(bm, geom=selected, context='VERTS'); bm.to_mesh(copy.data); bm.free()
            copy['claim'] = ob.get('claim', 'estimated: inherited site context')
            copy['source'] = 'existing scene object ' + name
            copy['retention_note'] = 'Original mesh and modifiers copied; only forecourt vertices removed.'
            retained.append(copy.name)
        ob.hide_render = True; ob.hide_viewport = True; hidden.append(name)
    return hidden, retained


def build(scene, root):
    """Build the finished forecourt and return software geometry and replacement counts."""
    root = Path(root).resolve()
    data = json.loads((root/'blender/data/forecourt_layout.json').read_text())
    if bpy.data.collections.get('forecourt_context'): raise RuntimeError('forecourt_context already exists. Call build once per scene.')
    elements = data['elements']
    for item in elements:
        if not all(item.get(k) for k in ('id','source','claim','state','kind')): raise ValueError('Forecourt element lacks provenance')
    collection = bpy.data.collections.new('forecourt_context'); scene.collection.children.link(collection)
    collection['claim'] = 'estimated finished design intent; W1b plaza outline retained; see per-object claim'
    collection['source'] = 'blender/data/forecourt_layout.json'; collection['evidence'] = data['evidence']
    collection['state'] = data['default_state']
    dg = bpy.context.evaluated_depsgraph_get()
    terrain = [(ob, BVHTree.FromObject(ob,dg)) for name in ('terrain_site','terrain_far') if (ob := scene.objects.get(name)) and ob.type == 'MESH']
    cache = {}
    def height(x,y):
        key = (round(x,4),round(y,4))
        if key not in cache:
            cache[key] = data['fallback_ground_z_m']
            for ob, tree in terrain:
                inv = ob.matrix_world.inverted(); origin = inv @ Vector((x,y,3000))
                down = (inv.to_3x3() @ Vector((0,0,-1))).normalized()
                hit = tree.ray_cast(origin,down)[0]
                if hit is not None: cache[key] = (ob.matrix_world @ hit).z; break
        return cache[key]
    mats = {k:_material('fc_'+k,v) for k,v in data['materials'].items()}
    domain = next(e['polygon'] for e in elements if e['kind']=='extent')
    hidden, retained = _preserve(scene,collection,data['replace_objects'],domain)
    base = next(e for e in elements if e['kind']=='extent')
    _surface('fc_base',domain,mats['grass'],base,collection,height,.11)
    order = {'extent':0,'lawn':1,'plaza':2,'surface':2,'path':3,'bed':4,'roundabout':4,'mast_cluster':5,'street_light':5,'bench_line':5,'palm':6}
    for item in sorted(elements,key=lambda e:order[e['kind']]):
        kind = item['kind']; name = 'fc_' + item['id']; ring = item.get('polygon')
        if kind == 'extent': continue
        if kind == 'roundabout':
            x,y = item['center']; r = item['radius_m']
            ring = [(x+r*math.cos(k*math.tau/48),y+r*math.sin(k*math.tau/48)) for k in range(48)]
        if ring:
            _surface(name,ring,mats[item['material']],item,collection,height,item['lift_m'])
            if item.get('kerb_width_m',0):
                _strip(name+'_kerb',ring+ring[:1],item['kerb_width_m'],mats['kerb'],item,collection,height,item['lift_m']+item['kerb_height_m'],item['kerb_height_m'])
            if kind in ('bed','roundabout'):
                x = sum(p[0] for p in ring)/len(ring); y = sum(p[1] for p in ring)/len(ring)
                for k in range(5):
                    xy = (x+(k-2)*.6,y+(.5 if k%2 else -.5))
                    ob = _column(name+f'_plant_{k}',xy,.65,height(*xy)+item['lift_m'],.4+(k%3)*.1,mats['planting'],item,collection)
                    ob['state'] = 'design_intent'; ob['claim'] = 'estimated low planting, design intent from ' + data['elements'][1]['finish_source']
        elif kind == 'path':
            pts = item['polyline']; w = item['width_m']
            _strip(name,pts,w,mats[item['material']],item,collection,height,item['lift_m'])
            if item['kerb_width_m']:
                for side in (-1,1):
                    # Kerbs follow each segment; joints overlap by the narrow kerb width.
                    for j,(a,b) in enumerate(zip(pts,pts[1:])):
                        dx,dy=b[0]-a[0],b[1]-a[1]; d=math.hypot(dx,dy)
                        offset = (-dy/d*w/2*side,dx/d*w/2*side)
                        edge = [(p[0]+offset[0],p[1]+offset[1]) for p in (a,b)]
                        _strip(name+f'_kerb_{side}_{j}',edge,item['kerb_width_m'],mats['kerb'],item,collection,height,item['lift_m']+item['kerb_height_m'],item['kerb_height_m'])
        elif kind == 'palm':
            ob = bpy.data.objects.new(item['id'],None); collection.objects.link(ob)
            x,y = item['position']; ob.location = (x,y,height(x,y)+.3)
            ob.empty_display_type = 'PLAIN_AXES'; ob.empty_display_size = .8
            for key in ('claim','source','state'): ob[key] = item[key]
            ob['height_m'] = item['height_m']; ob['element_id'] = item['id']
        elif kind in ('mast_cluster','street_light'):
            points = item['positions'] if kind=='mast_cluster' else [item['position']]
            for k,xy in enumerate(points):
                z = height(*xy)+.25
                _column(name+f'_{k}',xy,item['radius_m'],z,item['height_m'],mats['white'],item,collection)
                if kind=='street_light': _column(name+'_head',xy,.4,z+item['height_m'],.18,mats['white'],item,collection)
        elif kind == 'bench_line':
            a,b=item['polyline']; dx,dy=b[0]-a[0],b[1]-a[1]; d=math.hypot(dx,dy)
            for k in range(item['count']):
                t=(k+.5)/item['count']; x,y=a[0]+dx*t,a[1]+dy*t
                pts=[(x-dx/d*item['length_m']/2,y-dy/d*item['length_m']/2),(x+dx/d*item['length_m']/2,y+dy/d*item['length_m']/2)]
                _strip(name+f'_{k}',pts,item['width_m'],mats['bench'],item,collection,height,item['height_m']+.25,.12)
    added = 0
    for ob in collection.objects:
        if ob.type=='MESH' and ob.name not in retained:
            ob.data.calc_loop_triangles(); added += len(ob.data.loop_triangles)
    if added > LIMIT: raise RuntimeError(f'Forecourt triangle budget exceeded: {added} > {LIMIT}')
    report = dict(evidence='software / Visualization',elements=len(elements),palm_slots=sum(e['kind']=='palm' for e in elements),added_triangles=added,triangle_limit=LIMIT,hidden=hidden,retained=retained,terrain_mode='raycast' if terrain else 'flat smoke-test fallback')
    collection['report'] = json.dumps(report)
    print('FORECOURT_BUILD '+json.dumps(report),flush=True)
    return report
