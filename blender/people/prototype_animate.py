"""Bake the two Quaternius prototype clips onto the Talanta review rigs."""
import argparse
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prototype_scene import create_scene
from retarget import retarget_actions

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("stage", type=Path)
parser.add_argument("animation", type=Path)
parser.add_argument("output", type=Path)
parser.add_argument("--stills", type=Path, help="Render one sample frame from each clip")
parser.add_argument("--sprint", action="store_true", help="Include the football locomotion clip")
parser.add_argument("--kits", nargs=2, choices=("kenya-white", "kenya-red", "spain-red"),
                    default=("kenya-white", "spain-red"))
args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])

scene, avatars = create_scene(args.stage, args.kits)
before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=str(args.animation))
source_objects = set(bpy.data.objects) - before
source, = (obj for obj in source_objects if obj.type == "ARMATURE")

clips = ("Idle_Loop", "Sitting_Idle_Loop")
if args.sprint:
    clips += ("Sprint_Loop",)
rig_actions = []
for rig, _ in avatars:
    actions = retarget_actions(source, rig, clips)
    data = rig.animation_data
    data.action = None
    for name, action in zip(clips, actions):
        track = data.nla_tracks.new()
        track.name = name
        track.strips.new(name, 0, action)
    data.use_nla = False
    data.action = actions[0]
    rig_actions.append((rig, dict(zip(clips, actions))))

for obj in source_objects:
    bpy.data.objects.remove(obj, do_unlink=True)
scene.frame_set(12)
used_images = {node.image for _, mesh in avatars for material in mesh.data.materials
               for node in material.node_tree.nodes if node.type == "TEX_IMAGE" and node.image}
for image in used_images:
    if not image.packed_file:
        image.pack()
args.output.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(args.output))

if args.stills:
    args.stills.mkdir(parents=True, exist_ok=True)
    for name in clips:
        for rig, actions in rig_actions:
            rig.animation_data.action = actions[name]
        first, last = rig_actions[0][1][name].frame_range
        scene.frame_set(round((first + last) / 2))
        scene.render.filepath = str(args.stills / f"{name}.png")
        bpy.ops.render.render(write_still=True)
