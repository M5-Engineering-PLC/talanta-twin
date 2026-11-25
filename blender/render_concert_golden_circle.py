"""Render and verify the textured Golden Circle dancers from the prepared scene.

blender -b foreground.blend --python-exit-code 1 --python
blender/render_concert_golden_circle.py -- OUTPUT.png [--motion-preview]
"""
from pathlib import Path
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

scene = bpy.context.scene
scene.frame_set(68)
source = scene.camera
camera = source.copy()
camera.data = source.data.copy()
camera.name = 'Golden Circle close-up'
bpy.context.collection.objects.link(camera)
camera.location = (1.5, -13.5, 9)
target = Vector((-4.5, -3.5, 7.5))
camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
camera.data.lens = 34
scene.camera = camera
bpy.context.view_layer.update()

actors = [obj for obj in scene.objects if obj.name.startswith('Textured crowd ')]
assert len(actors) == 10
def pose(frame):
    scene.frame_set(frame)
    graph = bpy.context.evaluated_depsgraph_get()
    return [tuple(tuple(tuple(row) for row in bone.matrix) for child in actor.children_recursive if child.type == 'ARMATURE'
                  for bone in child.evaluated_get(graph).pose.bones) for actor in actors]
first, last = pose(44), pose(68)
motion = sum(a != b for a,b in zip(first,last))
assert motion == 10, motion
in_frame = [actor.name for actor in actors if (uv := world_to_camera_view(scene, camera, actor.matrix_world.translation + Vector((0, 0, 1.3)))).z > 0 and 0 < uv.x < 1 and 0 < uv.y < 1]
print(f'Dancers moving: {motion}; camera contains {len(in_frame)} actor anchors: {in_frame}', flush=True)
assert len(in_frame) >= 6
args = sys.argv[sys.argv.index('--') + 1:]
output = Path(args[0]).resolve()
if '--motion-preview' in args[1:]:
    output.mkdir(parents=True, exist_ok=True)
    camera.keyframe_insert(data_path='location', frame=44)
    camera.keyframe_insert(data_path='rotation_euler', frame=44)
    camera.location = (0.2, -11.8, 8.75)
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    camera.keyframe_insert(data_path='location', frame=91)
    camera.keyframe_insert(data_path='rotation_euler', frame=91)
    scene.render.engine = 'BLENDER_EEVEE'
    scene.eevee.taa_render_samples = 8
    scene.render.resolution_x = 480
    scene.render.resolution_y = 270
    scene.render.fps = 24
    scene.frame_start = 44
    scene.frame_end = 91
    scene.render.image_settings.file_format = 'JPEG'
    scene.render.filepath = str(output / 'golden-circle-')
    bpy.ops.render.render(animation=True)
else:
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)
