"""Gate G1: can this cloud session render? CPU Cycles, 960x540, 64 samples, denoiser.
Run: ~/.venvs/bpy/bin/python blender/scripts/g1_render_test.py <outdir>"""
import bpy, sys, time, os, json, platform
out = sys.argv[-1] if len(sys.argv) > 1 else 'blender/renders/g1'
os.makedirs(out, exist_ok=True)

def setup(scene):
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 64
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 960, 540, 100
    scene.render.image_settings.file_format = 'PNG'

def render(name):
    s = bpy.context.scene; setup(s)
    s.render.filepath = os.path.join(out, name + '.png')
    tris = sum(len(o.data.loop_triangles) for o in s.objects if o.type == 'MESH' and (o.data.calc_loop_triangles() or True))
    t0 = time.time(); bpy.ops.render.render(write_still=True); dt = time.time() - t0
    return {'frame': name, 'triangles': tris, 'seconds': round(dt, 1)}

res = []
bpy.ops.wm.read_factory_settings(use_empty=False)
res.append(render('default_scene'))

# 200k-triangle test: ground, sun + sky, ring of subdivided spheres and boxes
bpy.ops.wm.read_factory_settings(use_empty=True)
s = bpy.context.scene
bpy.ops.mesh.primitive_plane_add(size=400)
import math
for i in range(24):
    a = i / 24 * math.tau
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, radius=6, ring_count=32, location=(math.cos(a) * 60, math.sin(a) * 45, 6))
    bpy.ops.mesh.primitive_cube_add(size=8, location=(math.cos(a) * 90, math.sin(a) * 70, 4))
    m = bpy.context.object.modifiers.new('sub', 'SUBSURF'); m.levels = m.render_levels = 2
for o in list(s.objects): 
    if o.type == 'MESH':
        bpy.context.view_layer.objects.active = o
        for mod in list(o.modifiers): bpy.ops.object.modifier_apply(modifier=mod.name)
mat = bpy.data.materials.new('white'); mat.use_nodes = True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.8, 0.78, 0.74, 1)
for o in s.objects: o.data.materials.append(mat)
# top up to ~200k triangles with one dense sphere
tri = lambda: sum(len(o.data.loop_triangles) for o in s.objects if o.type == 'MESH' and (o.data.calc_loop_triangles() or True))
need = 200000 - tri()
seg = max(16, int(math.sqrt(need / 2)))
bpy.ops.mesh.primitive_uv_sphere_add(segments=seg * 2, ring_count=seg, radius=15, location=(0, 0, 15))
bpy.context.object.data.materials.append(mat)
bpy.ops.object.light_add(type='SUN', rotation=(math.radians(70), 0, math.radians(40))); bpy.context.object.data.energy = 4
w = bpy.data.worlds.new('sky'); s.world = w; w.use_nodes = True
sky = w.node_tree.nodes.new('ShaderNodeTexSky'); w.node_tree.links.new(sky.outputs[0], w.node_tree.nodes['Background'].inputs[0])
bpy.ops.object.camera_add(location=(170, -150, 70)); cam = bpy.context.object; s.camera = cam
c = cam.constraints.new('TRACK_TO'); e = bpy.data.objects.new('t', None); s.collection.objects.link(e); c.target = e
res.append(render('test_200k'))

info = {'blender': bpy.app.version_string, 'cpus': os.cpu_count(), 'ram_gb': round(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / 2**30, 1),
        'cpu': platform.processor() or open('/proc/cpuinfo').read().split('model name')[1].split('\n')[0].strip(': '), 'renders': res}
json.dump(info, open(os.path.join(out, 'g1_times.json'), 'w'), indent=1)
print(json.dumps(info, indent=1))
