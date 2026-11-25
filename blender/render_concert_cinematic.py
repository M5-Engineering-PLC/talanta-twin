"""Rebuild lighting and cinematic cameras from the concert milestone GLB.

Run with blender -b --python-exit-code 1 --python blender/render_concert_cinematic.py
-- MASTER.glb OUTPUT_DIR [--preview] [--animation] [--save-blend] [--shot flyover|front-pit|catwalk-reverse].
"""
import argparse
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def add_spot(name, location, target, color, energy, angle):
    data = bpy.data.lights.new(name, 'SPOT')
    data.color = color
    data.energy = energy
    data.spot_size = angle
    data.spot_blend = .5
    data.shadow_soft_size = .8
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    aim(obj, target)


def add_shot(name, keys):
    data = bpy.data.cameras.new(name)
    data.lens = 25
    data.clip_end = 800
    camera = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(camera)
    camera.rotation_mode = 'QUATERNION'
    previous = None
    for frame, location, target in keys:
        camera.location = location
        rotation = (Vector(target) - camera.location).to_track_quat('-Z', 'Y')
        if previous is not None and rotation.dot(previous) < 0:
            rotation.negate()
        camera.rotation_quaternion = rotation
        previous = rotation
        camera.keyframe_insert(data_path='location', frame=frame)
        camera.keyframe_insert(data_path='rotation_quaternion', frame=frame)
    return camera


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('master', type=Path)
parser.add_argument('output', type=Path)
parser.add_argument('--preview', action='store_true')
parser.add_argument('--save-blend', action='store_true', help='Save the prepared scene before rendering')
parser.add_argument('--animation', action='store_true', help='Render each shot as a numbered PNG sequence')
parser.add_argument('--shot', choices=['flyover', 'front-pit', 'catwalk-reverse'])
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
args.output.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(args.master.resolve()))
scene = bpy.context.scene
# glTF restores only the first global clip. The exported crowd actions target
# disjoint rig sets, so restore each object's own action and slot.
animated = []
for obj in scene.objects:
    animation = obj.animation_data
    if not animation or animation.action:
        continue
    track = next((track for track in reversed(animation.nla_tracks) if track.strips), None)
    if track:
        strip = track.strips[0]
        animation.action = strip.action
        animation.action_slot = strip.action_slot
        animated.append(obj)
print(f'Restored actions on {len(animated)} additional objects', flush=True)

def pose_sample(frame):
    scene.frame_set(frame)
    depsgraph = bpy.context.evaluated_depsgraph_get()
    return {
        obj.name: tuple(tuple(tuple(row) for row in bone.matrix) for bone in obj.evaluated_get(depsgraph).pose.bones)
        for obj in scene.objects if obj.type == 'ARMATURE' and obj.animation_data
    }

pose_a, pose_b = pose_sample(24), pose_sample(72)
moving = sum(pose_a[name] != pose_b[name] for name in pose_a)
print(f'Moving rigs between frames 24 and 72: {moving}/{len(pose_a)}', flush=True)

screen = bpy.data.materials.get('M_ConcertLEDScreen')
if screen:
    tree = screen.node_tree
    principled = next(node for node in tree.nodes if node.type == 'BSDF_PRINCIPLED')
    waves = tree.nodes.new('ShaderNodeTexWave')
    waves.bands_direction = 'X'
    waves.inputs['Scale'].default_value = 2.8
    waves.inputs['Distortion'].default_value = 5
    waves.inputs['Detail Scale'].default_value = 1.4
    waves.inputs['Phase Offset'].driver_add('default_value').driver.expression = 'frame * 0.08'
    ramp = tree.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (.013, .006, .07, 1)
    ramp.color_ramp.elements[1].color = (.17, .48, 1, 1)
    ramp.color_ramp.elements.new(.53).color = (.44, .025, .25, 1)
    tree.links.new(waves.outputs['Fac'], ramp.inputs['Fac'])
    tree.links.new(ramp.outputs['Color'], principled.inputs['Emission Color'])
    principled.inputs['Base Color'].default_value = (.025, .019, .05, 1)
    principled.inputs['Emission Strength'].default_value = 1.75

stage = bpy.data.objects['Stage_Catwalk_T_Head'].location
pitch = stage.z - 1.35

world = bpy.data.worlds.new('Concert night')
world.use_nodes = True
world.node_tree.nodes['Background'].inputs[0].default_value = (.026, .044, .1, 1)
world.node_tree.nodes['Background'].inputs[1].default_value = .3
scene.world = world

for side, color in [(-1, (.55, .19, 1)), (1, (.16, .59, 1))]:
    add_spot(f'Stage wash {side}', (side * 17, 26, pitch + 16), (side * 5, 0, pitch + 1), color, 12000, 1.1)
    add_spot(f'Bowl wash {side}', (side * 28, -16, pitch + 18), (side * 11, 7, pitch), color, 8000, 1.5)
add_spot('Frontman key', (-4, -6, pitch + 11), (0, stage.y, pitch + 2.4), (1, .68, .45), 3200, .58)

shots = {
    'flyover': [(1, (-55, -100, pitch + 135), (0, 6, pitch)), (72, (-14, -23, pitch + 64), (0, 6, pitch)), (120, (-8, -17, pitch + 21), (0, 11, pitch + 3))],
    'front-pit': [(1, (-4.5, -25, pitch + 9), (0, 10, pitch + 4)), (120, (2.8, -4.5, pitch + 4.8), (0, 6, pitch + 2.4))],
    'catwalk-reverse': [(1, (1, 10, pitch + 5), (0, -22, pitch + 3)), (120, (0, 6, pitch + 3.8), (0, -26, pitch + 3))],
}
cameras = {name: add_shot(name, keys) for name, keys in shots.items()}

scene.render.engine = 'CYCLES'
scene.cycles.samples = 8 if args.preview else 64
scene.cycles.use_denoising = True
scene.render.resolution_x = 640 if args.preview else 3840
scene.render.resolution_y = 360 if args.preview else 2160
scene.render.resolution_percentage = 100
scene.render.fps = 24
scene.frame_end = 120
scene.render.image_settings.file_format = 'PNG'

if args.save_blend:
    scene.camera = cameras[args.shot or 'front-pit']
    scene.frame_set(72)
    bpy.ops.wm.save_as_mainfile(filepath=str((args.output / 'concert-prepared.blend').resolve()))

for name in [args.shot] if args.shot else shots:
    scene.camera = cameras[name]
    if args.animation:
        frames = args.output / name
        frames.mkdir(exist_ok=True)
        scene.render.filepath = str((frames / 'frame_').resolve())
        bpy.ops.render.render(animation=True)
    else:
        scene.frame_set(72)
        scene.render.filepath = str((args.output / f'{name}.png').resolve())
        bpy.ops.render.render(write_still=True)
