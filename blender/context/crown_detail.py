"""Pass H (lead order 2026-10-22): tree crowns that no longer read as soft blobs up close (D02, D03 foregrounds).

The clustered crowns of pass D (tree_crowns.py) are smooth lumpy spheres with a faint noise bump; within 150 m of the
camera they read as soft green blobs. Two changes:
- the leaf materials (forest, site and suburb trees; the jacaranda keeps its leaf texture) get a leaf-mass structure in
  object space: a coarse distorted noise (masses of about 0.6 m) sets the tone from 0.5 to 1.2 times the leaf colour, a
  fine noise adds leaf grain, and both drive a soft bump. (A Voronoi cell pattern was tried first: it read as a tortoise
  shell.)
- the crown meshes of the foreground trace trees, which the forest instances share, get their leaf vertices pushed in
  and out by a smooth noise (0.35 m, baked into the shared mesh), so the crown outlines break up; trunks stay straight.
  (Subdivision and Displace modifiers with a vertex group were tried first and took about 10 GB at render time.)
Crown size and tree positions do not change. Both states.
Run from the repo root: ~/.venvs/bpy/bin/python blender/context/crown_detail.py
"""
import json, os
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=os.environ.get("TALANTA_SITE_BLEND", str(ROOT / "blender/out/talanta_site.blend")))
done = []
for m in bpy.data.materials:
    n = m.name
    if not (n.startswith(("tree_", "st_", "suburbs_leaf")) and n.endswith(("_leaf",)) or n.startswith("suburbs_leaf")): continue
    if not m.use_nodes or m.get("crown_detail"): continue
    nt = m.node_tree; nd, lk = nt.nodes, nt.links; p = nd.get("Principled BSDF")
    if p is None or p.inputs["Base Color"].is_linked: continue
    base = tuple(p.inputs["Base Color"].default_value)
    tc = nd.new("ShaderNodeTexCoord")
    # leaf masses: a coarse noise (clumps of about 0.6 m) sets each clump's tone; a fine noise adds leaf grain
    big = nd.new("ShaderNodeTexNoise"); big.inputs["Scale"].default_value = 1.7; big.inputs["Detail"].default_value = 4.0
    big.inputs["Roughness"].default_value = 0.6; big.inputs["Distortion"].default_value = 0.6
    fine = nd.new("ShaderNodeTexNoise"); fine.inputs["Scale"].default_value = 9.0; fine.inputs["Detail"].default_value = 2.0
    lk.new(tc.outputs["Object"], big.inputs["Vector"]); lk.new(tc.outputs["Object"], fine.inputs["Vector"])
    tone = nd.new("ShaderNodeMapRange"); tone.inputs["From Min"].default_value = 0.3; tone.inputs["From Max"].default_value = 0.7
    tone.inputs["To Min"].default_value = 0.5; tone.inputs["To Max"].default_value = 1.2; lk.new(big.outputs["Fac"], tone.inputs["Value"])
    grain = nd.new("ShaderNodeMapRange"); grain.inputs["To Min"].default_value = 0.78; grain.inputs["To Max"].default_value = 1.08
    lk.new(fine.outputs["Fac"], grain.inputs["Value"])
    mul = nd.new("ShaderNodeMath"); mul.operation = "MULTIPLY"; lk.new(tone.outputs[0], mul.inputs[0]); lk.new(grain.outputs[0], mul.inputs[1])
    col = nd.new("ShaderNodeMix"); col.data_type = "RGBA"; col.blend_type = "MULTIPLY"; col.inputs["Factor"].default_value = 1.0
    col.inputs["A"].default_value = base
    cmb = nd.new("ShaderNodeCombineColor"); [lk.new(mul.outputs[0], cmb.inputs[i]) for i in range(3)]
    lk.new(cmb.outputs[0], col.inputs["B"]); lk.new(col.outputs["Result"], p.inputs["Base Color"])
    # bump from both noises: soft leaf masses with a grain, no hard cell edges
    hsum = nd.new("ShaderNodeMath"); hsum.operation = "MULTIPLY_ADD"; hsum.inputs[1].default_value = 0.25
    lk.new(fine.outputs["Fac"], hsum.inputs[0]); lk.new(big.outputs["Fac"], hsum.inputs[2])
    bump = nd.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.8; bump.inputs["Distance"].default_value = 0.3
    lk.new(hsum.outputs[0], bump.inputs["Height"])
    old = p.inputs["Normal"].links[0].from_socket if p.inputs["Normal"].is_linked else None
    if old: lk.new(old, bump.inputs["Normal"])
    lk.new(bump.outputs["Normal"], p.inputs["Normal"])
    m["crown_detail"] = "pass H: noise leaf masses (tone, grain, bump); estimated look"
    done.append(n)
# silhouettes: the crown meshes of the foreground trace trees (tree_crowns.py; shared with the forest instances, about
# 530 users each) get their leaf vertices pushed along the normal by a smooth noise (+-0.35 m, about 0.7 m features),
# baked into the shared mesh in local coordinates, so every crown of those types breaks its outline; trunks stay
# straight. (Subdivision and Displace modifiers with a vertex group were tried first: on the shared meshes they took
# about 10 GB at render.)
from mathutils import noise
nd_ = 0
for me in {o.data for o in bpy.data.objects if o.type == "MESH" and o.name.startswith("trace_tree_")}:
    if me.get("crown_rough"): continue
    leaf = {i for i, m in enumerate(me.materials) if m and m.name.endswith("_leaf")}
    vs = {v for p_ in me.polygons if p_.material_index in leaf for v in p_.vertices}
    if not vs: continue
    for i in vs:
        v = me.vertices[i]; v.co += v.normal * 0.35 * noise.noise(v.co / 0.7)
    me.update(); me["crown_rough"] = "pass H: baked noise offset on the leaf vertices"; nd_ += 1
print("CROWN_DETAIL " + json.dumps({"materials": done, "roughened_crown_meshes": nd_}), flush=True)
bpy.ops.wm.save_mainfile()
