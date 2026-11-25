"""Build a 10 m Cycles reference scene from the verified Rocketbox FBX files."""
import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prototype_skin import skin_variant
from prototype_kits import PALETTES, kit_variant


AVATARS = ("Female_Adult_01", "Male_Adult_01")


def texture(material, path, socket, *, normal=False, alpha=False, kit=None):
    tree = material.node_tree
    shader = next(node for node in tree.nodes if node.type == "BSDF_PRINCIPLED")
    image = bpy.data.images.load(str(path), check_existing=True)
    image.colorspace_settings.name = "Non-Color" if normal else "sRGB"
    node = tree.nodes.new("ShaderNodeTexImage")
    node.label = path.name
    if socket == "Base Color" and not alpha:
        image = skin_variant(image, material.name)
    if kit and material.name.endswith("_body") and socket == "Base Color":
        image = kit_variant(image, material.name, kit)
    node.image = image
    if normal:
        decoder = tree.nodes.new("ShaderNodeNormalMap")
        tree.links.new(node.outputs["Color"], decoder.inputs["Color"])
        tree.links.new(decoder.outputs["Normal"], shader.inputs[socket])
    else:
        tree.links.new(node.outputs["Color"], shader.inputs[socket])
    if alpha:
        tree.links.new(node.outputs["Alpha"], shader.inputs["Alpha"])


def import_avatar(stage, name, kit=None):
    source = stage / "Assets" / "Avatars" / "Adults" / name
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(source / "Export" / f"{name}.fbx"), use_anim=False)
    imported = set(bpy.data.objects) - before
    rig, = (obj for obj in imported if obj.type == "ARMATURE")
    mesh, = (obj for obj in imported if obj.type == "MESH")
    rig.name = name
    mesh.name = f"{name}_Mesh"
    for material in mesh.data.materials:
        material.use_nodes = True
        nodes = material.node_tree.nodes
        for node in list(nodes):
            if node.type not in {"BSDF_PRINCIPLED", "OUTPUT_MATERIAL"}:
                nodes.remove(node)
        shader = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
        shader.inputs["Roughness"].default_value = 0.58
        maps = source / "Textures"
        opacity = material.name.endswith("_opacity")
        texture(material, maps / f"{material.name}_color.tga", "Base Color", alpha=opacity, kit=kit)
        if not opacity:
            texture(material, maps / f"{material.name}_normal.tga", "Normal", normal=True)
    return rig, mesh


def face_camera(rig, mesh, x):
    bones = rig.data.bones
    foot = rig.matrix_world @ bones["Bip01 L Foot"].head_local
    toe = rig.matrix_world @ bones["Bip01 L Toe0"].head_local
    forward = toe - foot
    angle = -math.pi / 2 - math.atan2(forward.y, forward.x)
    rig.matrix_world = Matrix.Rotation(angle, 4, "Z") @ rig.matrix_world
    bpy.context.view_layer.update()
    bottom = min((mesh.matrix_world @ Vector(corner)).z for corner in mesh.bound_box)
    rig.location += Vector((x, 0, -bottom))
    bpy.context.view_layer.update()


def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


def create_scene(stage, kits=(None, None)):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    avatars = []
    for name, x, kit in zip(AVATARS, (-0.82, 0.82), kits):
        rig, mesh = import_avatar(stage, name, kit)
        face_camera(rig, mesh, x)
        avatars.append((rig, mesh))

    bpy.ops.mesh.primitive_plane_add(size=200)
    floor = bpy.context.object
    floor.name = "Neutral floor"
    material = bpy.data.materials.new("Neutral grey")
    material.diffuse_color = (0.18, 0.18, 0.18, 1)
    floor.data.materials.append(material)
    scene.world = bpy.data.worlds.new("Neutral ambient")
    scene.world.color = (0.18, 0.18, 0.18)

    for label, location, energy, size in [
        ("Key", (-3, -4, 5), 650, 4),
        ("Fill", (4, -3, 3), 400, 3),
        ("Rim", (0, 3, 5), 750, 4),
    ]:
        light = bpy.data.lights.new(label, "AREA")
        light.energy, light.size = energy, size
        obj = bpy.data.objects.new(label, light)
        scene.collection.objects.link(obj)
        obj.location = location
        aim(obj, (0, 0, 1))

    camera = bpy.data.objects.new("Review camera at 10 m", bpy.data.cameras.new("Review lens"))
    scene.collection.objects.link(camera)
    camera.location = (0, -10, 1.25)
    camera.data.lens = 90
    aim(camera, (0, 0, 0.91))
    scene.camera = camera
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 800
    scene.render.resolution_percentage = 100
    scene.view_settings.view_transform = "AgX"
    return scene, avatars


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--kits", nargs=2, choices=PALETTES)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    scene, _ = create_scene(args.stage, args.kits or (None, None))
    args.output.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(args.output / "rocketbox-10m-rest.png")
    bpy.ops.wm.save_as_mainfile(filepath=str(args.output / "rocketbox-10m-rest.blend"))
    bpy.ops.render.render(write_still=True)
