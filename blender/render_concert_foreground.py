"""Replace selected milestone dancers at their existing pitch positions.

blender -b crowd-fabrics.blend --python-exit-code 1 --python
blender/render_concert_foreground.py -- CONCERT_ASSET_DIR OUTPUT.png
"""
import math
import sys
from pathlib import Path

import bpy

asset_dir, output = (Path(value).resolve() for value in sys.argv[sys.argv.index('--') + 1:])
scene = bpy.context.scene
lead = bpy.data.objects['Textured lead anchor']
slots = [7, 15, 16, 23, 39, 41, 59, 71, 76, 87]
sources = [asset_dir / 'crowd/male.glb', asset_dir / 'performer/model.glb']

for index, slot in enumerate(slots):
    original = bpy.data.objects[f'Dancer_{slot:03d}_Pitch']
    placed_at = original.matrix_world.translation.copy()
    existing = set(scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(sources[index % len(sources)]))
    imported = [obj for obj in scene.objects if obj not in existing]

    anchor = bpy.data.objects.new(f'Textured crowd {slot:03d}', None)
    bpy.context.collection.objects.link(anchor)
    anchor.location = placed_at
    anchor.rotation_euler.z = math.atan2(lead.location.x - placed_at.x, placed_at.y - lead.location.y)
    anchor.scale = (.92 + index % 5 * .04,) * 3
    for obj in imported:
        if obj.parent is None:
            obj.parent = anchor
            obj.location.x = 0
        animation = obj.animation_data
        if not animation or not animation.action:
            continue
        action, action_slot = animation.action, animation.action_slot
        animation.action = None
        track = animation.nla_tracks.new()
        track.name = 'Crowd dance offset'
        strip = track.strips.new(action.name, 1 - (index * 7) % 29, action)
        strip.action_slot = action_slot
        strip.repeat = 4

    for obj in original.children_recursive:
        obj.hide_render = True
        obj.hide_viewport = True

scene.frame_set(68)
scene.render.filepath = str(output)
bpy.ops.wm.save_as_mainfile(filepath=str(output.with_suffix('.blend')), compress=True)
bpy.ops.render.render(write_still=True)
print(f'Loaded {len(slots)} textured dancers at existing milestone positions.')
