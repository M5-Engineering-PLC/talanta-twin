"""Render a textured lead look test from the local prepared concert scene.

blender -b concert-prepared.blend --python-exit-code 1 --python
blender/render_concert_closeup.py -- app/public/concert/performer/model.glb OUTPUT_DIR
"""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

performer_file, output = (Path(value).resolve() for value in sys.argv[sys.argv.index('--') + 1:])
output.mkdir(parents=True, exist_ok=True)
scene = bpy.context.scene
legacy = bpy.data.objects['Lead_Artist_Frontman']
existing = set(scene.objects)
bpy.ops.import_scene.gltf(filepath=str(performer_file))
imported = [obj for obj in scene.objects if obj not in existing]
roots = [obj for obj in imported if obj.parent is None]
anchor = bpy.data.objects.new('Textured lead anchor', None)
bpy.context.collection.objects.link(anchor)
anchor.location = legacy.matrix_world.translation
anchor.rotation_euler.z = math.pi
for obj in roots:
    obj.parent = anchor
    obj.location.x = 0
for obj in legacy.children_recursive:
    obj.hide_render = True
    obj.hide_viewport = True

scene.frame_set(68)
look_at = anchor.location + Vector((0, 0, 1.3))
light = bpy.data.lights.new('Lead close-up softbox', 'AREA')
light.energy = 800
light.shape = 'DISK'
light.size = 3.5
light.color = (1, .75, .61)
key = bpy.data.objects.new(light.name, light)
bpy.context.collection.objects.link(key)
key.location = look_at + Vector((1.5, -4.5, 4))
key.rotation_euler = (look_at - key.location).to_track_quat('-Z', 'Y').to_euler()

camera_data = bpy.data.cameras.new('Performer close-up')
camera_data.lens = 42
camera = bpy.data.objects.new(camera_data.name, camera_data)
bpy.context.collection.objects.link(camera)
camera.location = look_at + Vector((2.1, -5.7, 1.05))
camera.rotation_euler = (look_at - camera.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera = camera
scene.render.resolution_x = 960
scene.render.resolution_y = 540
scene.cycles.samples = 16
scene.render.filepath = str(output / 'performer-closeup.png')
bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(output / 'concert-textured-lead.blend'))
