"""Training grass look (pass K, K4, 2026-10-24): the node tree of the `training_grass` material.

Users: the training pitches (fan() in build_site_detail.py, UV in metres along the pitch axis, so they get the mowing
stripes) and the south-west lawn (sw_lawn in context/asbuilt_ground.py, no UV, so the stripe term stays constant and
the lawn has no markings). The pass K review found the material flat and too saturated in L07 next to the Grass005
grass. This tree:
- lowers the saturation to the Grass005 grass in the same render (L07: saturation 0.64 before, about 0.55 for the
  other lawns; colours below, tuned on L07 crops);
- adds low-frequency colour and brightness variation from world-space noise at about 8 to 20 m;
- adds a small roughness and bump variation;
- keeps the mowing stripes (UV x every stripe_w metres) on the pitches only.
build_site_detail.py builds the material with it; context/grass_k.py re-applies it on an existing scene (step_FK).
No frame pixels are used; colours are by eye against the other grass in the render.
"""
import bpy

STRIPE = ("#5A7B39", "#5F7F3E")   # stripe pair, was #4D8B38 / #568F40 (saturation 0.60 -> about 0.53)
PATCH = ("#527234", "#788545")    # low-frequency patches: darker green to a drier olive
CLAIM = "estimated: colour by eye against the Grass005 grass in the L07 render (pass K, K4); no frame pixels"


def srgb(h):
    h = h.lstrip("#"); return tuple(((int(h[i:i + 2], 16) / 255 + 0.055) / 1.055) ** 2.4 for i in (0, 2, 4))


def build(m, stripe_w=5.0):
    """Rebuild m's node tree in place (the material keeps its name and users)."""
    m.use_nodes = True; nt = m.node_tree; nt.nodes.clear(); n_, l_ = nt.nodes, nt.links
    out = n_.new("ShaderNodeOutputMaterial"); p = n_.new("ShaderNodeBsdfPrincipled"); p.name = "Principled BSDF"
    l_.new(p.outputs[0], out.inputs[0])
    # mowing stripes: UV x in metres (pitches); a mesh without UV reads (0, 0) and gets one stripe colour
    uv = n_.new("ShaderNodeUVMap"); sp = n_.new("ShaderNodeSeparateXYZ"); l_.new(uv.outputs["UV"], sp.inputs[0])
    dv = n_.new("ShaderNodeMath"); dv.operation = "DIVIDE"; dv.inputs[1].default_value = stripe_w; l_.new(sp.outputs["X"], dv.inputs[0])
    fl = n_.new("ShaderNodeMath"); fl.operation = "FLOOR"; l_.new(dv.outputs[0], fl.inputs[0])
    md = n_.new("ShaderNodeMath"); md.operation = "MODULO"; md.inputs[1].default_value = 2; l_.new(fl.outputs[0], md.inputs[0])
    st = n_.new("ShaderNodeMix"); st.data_type = "RGBA"; l_.new(md.outputs[0], st.inputs[0])
    st.inputs[6].default_value = (*srgb(STRIPE[0]), 1); st.inputs[7].default_value = (*srgb(STRIPE[1]), 1)
    # low-frequency patches in world space (metres): noise scale 0.07 gives features of about 8 to 20 m
    tc = n_.new("ShaderNodeTexCoord")
    big = n_.new("ShaderNodeTexNoise"); big.inputs["Scale"].default_value = 0.07; big.inputs["Detail"].default_value = 2.0
    big.inputs["Roughness"].default_value = 0.5; l_.new(tc.outputs["Object"], big.inputs["Vector"])
    ramp = n_.new("ShaderNodeValToRGB"); ramp.color_ramp.elements[0].position = 0.3; ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[0].color = (*srgb(PATCH[0]), 1); ramp.color_ramp.elements[1].color = (*srgb(PATCH[1]), 1)
    l_.new(big.outputs["Fac"], ramp.inputs["Fac"])
    mx = n_.new("ShaderNodeMix"); mx.data_type = "RGBA"; mx.inputs[0].default_value = 0.6
    l_.new(st.outputs[2], mx.inputs[6]); l_.new(ramp.outputs["Color"], mx.inputs[7])
    # brightness: +-25 % from a second, offset noise at about 12 m; fine grain at about 1 m (multiply, 15 %)
    lum = n_.new("ShaderNodeTexNoise"); lum.inputs["Scale"].default_value = 0.11; lum.inputs["Detail"].default_value = 1.0
    l_.new(tc.outputs["Object"], lum.inputs["Vector"])
    lr = n_.new("ShaderNodeMapRange"); lr.inputs[3].default_value = 0.75; lr.inputs[4].default_value = 1.25; l_.new(lum.outputs["Fac"], lr.inputs[0])
    br = n_.new("ShaderNodeMix"); br.data_type = "RGBA"; br.blend_type = "MULTIPLY"; br.inputs[0].default_value = 1.0
    l_.new(mx.outputs[2], br.inputs[6]); l_.new(lr.outputs[0], br.inputs[7])
    fine = n_.new("ShaderNodeTexNoise"); fine.inputs["Scale"].default_value = 1.0; fine.inputs["Detail"].default_value = 4.0
    l_.new(tc.outputs["Object"], fine.inputs["Vector"])
    gr = n_.new("ShaderNodeMix"); gr.data_type = "RGBA"; gr.blend_type = "MULTIPLY"; gr.inputs[0].default_value = 0.15
    l_.new(br.outputs[2], gr.inputs[6]); l_.new(fine.outputs["Color"], gr.inputs[7])
    l_.new(gr.outputs[2], p.inputs["Base Color"])
    # roughness 0.80 to 0.92 with the patches; a small bump from the fine noise
    rr = n_.new("ShaderNodeMapRange"); rr.inputs[3].default_value = 0.8; rr.inputs[4].default_value = 0.92; l_.new(big.outputs["Fac"], rr.inputs[0])
    l_.new(rr.outputs[0], p.inputs["Roughness"])
    bump = n_.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 0.15; bump.inputs["Distance"].default_value = 0.02
    l_.new(fine.outputs["Fac"], bump.inputs["Height"]); l_.new(bump.outputs["Normal"], p.inputs["Normal"])
    m.diffuse_color = (*srgb(STRIPE[0]), 1); m["claim"] = CLAIM; m["grass_look"] = "pass K (K4)"
    return m
