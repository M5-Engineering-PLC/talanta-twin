"""Export the 10 m prototype's near-detail web meshes without changing the Cycles source."""
import argparse
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prototype_scene import AVATARS, create_scene
from prototype_kits import PALETTES


def reduce_mesh(mesh, triangle_budget):
    bpy.context.view_layer.objects.active = mesh
    mesh.data.calc_loop_triangles()
    triangles = len(mesh.data.loop_triangles)
    if triangles <= triangle_budget:
        return
    modifier = mesh.modifiers.new("Web near-detail reduction", "DECIMATE")
    modifier.ratio = triangle_budget / triangles
    mesh.modifiers.move(len(mesh.modifiers) - 1, 0)
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def prepare_textures(mesh):
    for material in mesh.data.materials:
        for node in material.node_tree.nodes:
            if node.type != "TEX_IMAGE" or not node.image:
                continue
            image = node.image
            width, height = image.size
            maximum = max(width, height)
            if maximum > 512:
                image.scale(round(512 * width / maximum), round(512 * height / maximum))
                image.pack()


def export_avatars(avatars, output, *, animated):
    output.mkdir(parents=True, exist_ok=True)
    for rig, mesh in avatars:
        bpy.ops.object.select_all(action="DESELECT")
        mesh.select_set(True)
        rig.select_set(True)
        reduce_mesh(mesh, 5900)
        prepare_textures(mesh)
        bpy.ops.export_scene.gltf(
            filepath=str(output / f"{rig.name}.glb"),
            export_format="GLB",
            use_selection=True,
            export_image_format="WEBP",
            export_animations=animated,
            export_animation_mode="NLA_TRACKS",
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--animated-blend", type=Path)
    parser.add_argument("--kits", nargs=2, choices=PALETTES)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    if args.animated_blend:
        bpy.ops.wm.open_mainfile(filepath=str(args.animated_blend))
        avatars = [(bpy.data.objects[name], bpy.data.objects[f"{name}_Mesh"]) for name in AVATARS]
    else:
        _, avatars = create_scene(args.stage, args.kits or (None, None))
    export_avatars(avatars, args.output, animated=bool(args.animated_blend))
