"""Test skin and wardrobe separation on the animated milestone crowd.

blender -b concert-textured-lead.blend --python-exit-code 1 --python
blender/render_concert_crowd_materials.py -- OUTPUT.png [--save-blend]
"""
import sys
from pathlib import Path

import bpy


def material(name, color, roughness, subsurface=0, fabric=False):
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*color, 1)
    principled = next(node for node in result.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
    principled.inputs['Base Color'].default_value = (*color, 1)
    principled.inputs['Roughness'].default_value = roughness
    principled.inputs['Subsurface Weight'].default_value = subsurface
    if fabric:
        tree = result.node_tree
        uv = tree.nodes.new('ShaderNodeTexCoord')
        grain = tree.nodes.new('ShaderNodeTexNoise')
        grain.inputs['Scale'].default_value = 155
        grain.inputs['Detail'].default_value = 2
        bump = tree.nodes.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value = .26
        bump.inputs['Distance'].default_value = .0008
        tree.links.new(uv.outputs['UV'], grain.inputs['Vector'])
        tree.links.new(grain.outputs['Fac'], bump.inputs['Height'])
        tree.links.new(bump.outputs['Normal'], principled.inputs['Normal'])
    return result


def region(name):
    bone = name.rsplit(':', 1)[-1].lower()
    if 'foot' in bone or 'toe' in bone:
        return 3
    if 'leg' in bone:
        return 2
    if any(part in bone for part in ('head', 'neck', 'forearm', 'hand', 'eye')):
        return 0
    return 1


# Use the exported skinned topology to keep material boundaries attached during the dance.
objects = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH' and
           len(obj.vertex_groups) and any(slot.material and slot.material.name.startswith('Avatar_') for slot in obj.material_slots)]
skin_colors = [(.116, .061, .035), (.20, .106, .067), (.35, .20, .127), (.083, .039, .023)]
tops = [(.105, .15, .21), (.23, .15, .095), (.14, .19, .11), (.38, .34, .28),
        (.23, .073, .091), (.089, .16, .16), (.14, .12, .19), (.29, .24, .18)]
skin = [material(f'Crowd skin {i}', color, .58, .12) for i, color in enumerate(skin_colors)]
shirts = [material(f'Crowd shirt {i}', color, .82, fabric=True) for i, color in enumerate(tops)]
trousers = [material('Crowd denim', (.045, .069, .106), .86, fabric=True), material('Crowd charcoal', (.055, .052, .047), .87, fabric=True),
            material('Crowd khaki', (.20, .16, .095), .85, fabric=True)]
shoes = material('Crowd footwear', (.037, .034, .032), .76)
processed = set()
for index, obj in enumerate(sorted(objects, key=lambda obj: obj.name)):
    geometry = obj.data
    if geometry in processed:
        continue
    processed.add(geometry)
    geometry.materials.clear()
    for value in [skin[index % len(skin)], shirts[index % len(shirts)], trousers[index % len(trousers)], shoes]:
        geometry.materials.append(value)
    regions = {group.index: region(group.name) for group in obj.vertex_groups}
    weights = [tuple((regions[group.group], group.weight) for group in vertex.groups if group.group in regions)
               for vertex in geometry.vertices]
    for polygon in geometry.polygons:
        scores = [0.0, 0.0, 0.0, 0.0]
        for vertex in polygon.vertices:
            for body_region, weight in weights[vertex]:
                scores[body_region] += weight
        polygon.material_index = max(range(len(scores)), key=scores.__getitem__) if any(scores) else 1

print(f'Assigned skin, shirts, trousers and shoes on {len(processed)} meshes ({len(objects)} objects)', flush=True)
if not processed:
    raise RuntimeError('No skinned crowd meshes matched the milestone scene')

scene = bpy.context.scene
scene.frame_set(68)
bpy.data.objects['Textured lead anchor'].rotation_euler.z = 0
scene.render.resolution_x = 960
scene.render.resolution_y = 540
scene.render.resolution_percentage = 100
scene.cycles.samples = 12
args = sys.argv[sys.argv.index('--') + 1:]
output = Path(args[0]).resolve()
scene.render.filepath = str(output)
if '--save-blend' in args[1:]:
    bpy.ops.wm.save_as_mainfile(filepath=str(output.with_suffix('.blend')), compress=True)
bpy.ops.render.render(write_still=True)
