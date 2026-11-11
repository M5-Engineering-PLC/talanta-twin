"""Run with Blender Python after staging the two Rocketbox source folders."""
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prototype_scene import create_scene

stage = Path(sys.argv[sys.argv.index("--") + 1])
scene, avatars = create_scene(stage)
assert len(avatars) == 2
assert scene.render.engine == "CYCLES"
scene.frame_set(1)
for (rig, mesh), expected_x in zip(avatars, (-0.82, 0.82)):
    evaluated = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    xs = [(evaluated.matrix_world @ v.co).x for v in evaluated.data.vertices]
    assert abs((max(xs) + min(xs)) / 2 - expected_x) < 0.1
    assert rig.type == "ARMATURE" and len(rig.data.bones) >= 70
    assert mesh.parent == rig
    assert abs((scene.camera.location - mesh.matrix_world.translation).xy.length - 10) < 0.15
    mesh.data.calc_loop_triangles()
    assert len(mesh.data.loop_triangles) in (8732, 7440)
    assert len(mesh.data.uv_layers) > 0
    assert len(mesh.data.materials) == 3
    for material in mesh.data.materials:
        images = [node.image for node in material.node_tree.nodes if node.type == "TEX_IMAGE"]
        assert images and all(image and image.size[0] > 0 for image in images)
print("Two textured Rocketbox rigs are framed at 10 m")
