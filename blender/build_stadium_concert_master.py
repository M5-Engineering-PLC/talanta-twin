import bpy
import bmesh
import math
import random
import subprocess
from pathlib import Path

print("================================================================")
print("  TALANTA STADIUM CONCERT MASTER - FULL STADIUM & PACKED SHOW   ")
print("================================================================")

bpy.ops.wm.read_factory_settings(use_empty=True)

scene = bpy.context.scene
scene.frame_start = 1
scene.frame_end = 120
scene.render.fps = 24

scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100

# EEVEE Engine
scene.render.engine = 'BLENDER_EEVEE'
if hasattr(scene, 'eevee'):
    scene.eevee.taa_render_samples = 32
    if hasattr(scene.eevee, 'use_raytracing'):
        scene.eevee.use_raytracing = True

# Atmospheric night world
world = bpy.data.worlds.new("ConcertNightWorld")
world.use_nodes = True
bg_node = world.node_tree.nodes.get("Background")
if bg_node:
    bg_node.inputs["Color"].default_value = (0.010, 0.012, 0.022, 1.0)
    bg_node.inputs["Strength"].default_value = 0.5
scene.world = world

# Collections
def get_or_create_col(name):
    col = bpy.data.collections.get(name)
    if not col:
        col = bpy.data.collections.new(name)
        scene.collection.children.link(col)
    return col

col_stadium = get_or_create_col("Stadium_Architecture")
col_stage = get_or_create_col("Concert_Stage")
col_lights = get_or_create_col("Concert_Lighting")
col_lasers = get_or_create_col("Concert_Lasers")
col_crowd = get_or_create_col("Concert_Crowd_Pitch")
col_camera = get_or_create_col("Concert_Camera")
col_archetypes = get_or_create_col("Archetypes_Offscreen")

# ==========================================
# 1. IMPORT ACTUAL TALANTA STADIUM GEOMETRY
# ==========================================
print("Importing Talanta Stadium architecture (blockout.glb)...")
blockout_path = 'E:/M5/grao/app/public/data/blockout.glb'
bpy.ops.import_scene.gltf(filepath=blockout_path)

# Materials for Stadium Architecture
def create_pbr_mat(name, color, roughness=0.5, metallic=0.0, emission=None, emit_strength=1.0):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.diffuse_color = color
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
        if emission:
            if "Emission Color" in bsdf.inputs:
                bsdf.inputs["Emission Color"].default_value = emission
                bsdf.inputs["Emission Strength"].default_value = emit_strength
            elif "Emission" in bsdf.inputs:
                bsdf.inputs["Emission"].default_value = emission
    return mat

mat_roof = create_pbr_mat("M_StadiumRoof", (0.18, 0.20, 0.24, 1.0), roughness=0.35, metallic=0.85)
mat_tiers = create_pbr_mat("M_StadiumTiers", (0.55, 0.12, 0.12, 1.0), roughness=0.6, metallic=0.1) # Kenyan crimson seats
mat_facade = create_pbr_mat("M_StadiumFacade", (0.75, 0.65, 0.45, 1.0), roughness=0.5, metallic=0.3)
mat_pitch_turf = create_pbr_mat("M_StadiumPitchTurf", (0.08, 0.22, 0.08, 1.0), roughness=0.9)
mat_concourse = create_pbr_mat("M_StadiumConcrete", (0.35, 0.36, 0.38, 1.0), roughness=0.7)

# Assign imported stadium objects to Stadium collection & materials
imported_objs = [o for o in bpy.data.objects if o.name in [
    'back_wall', 'band_lower', 'band_middle', 'base_band', 'base_columns', 'base_recess',
    'facade', 'facade_backing', 'lattice', 'lattice_rings', 'louvre_fins', 'north_plaza',
    'pitch', 'pitch_wall', 'pitch_zone', 'plinth', 'ring_beam', 'roof', 'roof_ribs',
    'shields', 'site_pad', 'soffit', 'spears', 'tier_lower', 'tier_middle', 'tier_upper',
    'training_field_sw', 'training_pitch_se', 'vip_glass', 'warmup_track'
]]

for o in imported_objs:
    col_stadium.objects.link(o)
    for c in list(o.users_collection):
        if c != col_stadium: c.objects.unlink(o)
    
    # Assign refined stadium materials
    if any(k in o.name for k in ['roof', 'ring_beam', 'lattice']):
        o.data.materials.clear()
        o.data.materials.append(mat_roof)
    elif any(k in o.name for k in ['tier_lower', 'tier_middle', 'tier_upper']):
        o.data.materials.clear()
        o.data.materials.append(mat_tiers)
    elif 'pitch' in o.name:
        o.data.materials.clear()
        o.data.materials.append(mat_pitch_turf)
    elif any(k in o.name for k in ['shields', 'spears', 'facade']):
        o.data.materials.clear()
        o.data.materials.append(mat_facade)
    else:
        o.data.materials.clear()
        o.data.materials.append(mat_concourse)

print(f"Assigned {len(imported_objs)} stadium architectural components.")

# Pitch elevation in Talanta model is Z = 6.20m
PITCH_Z = 6.20

# ==========================================
# 2. CONCERT STAGE ARCHITECTURE (MEGA-STAGE)
# ==========================================
mat_stage = create_pbr_mat("M_StageDeck", (0.07, 0.07, 0.08, 1.0), roughness=0.5, metallic=0.2)
mat_catwalk = create_pbr_mat("M_CatwalkDeck", (0.12, 0.12, 0.14, 1.0), roughness=0.4, metallic=0.3)
mat_truss = create_pbr_mat("M_TrussSteel", (0.42, 0.44, 0.48, 1.0), roughness=0.25, metallic=0.9)
mat_speaker = create_pbr_mat("M_SpeakerCabinet", (0.04, 0.04, 0.05, 1.0), roughness=0.8, metallic=0.1)
mat_ground = create_pbr_mat("M_TurfProtectionDeck", (0.06, 0.07, 0.08, 1.0), roughness=0.85)
mat_barricade = create_pbr_mat("M_MojoBarricade", (0.55, 0.58, 0.62, 1.0), roughness=0.2, metallic=0.95)
mat_mic = create_pbr_mat("M_Microphone", (0.05, 0.05, 0.06, 1.0), roughness=0.3, metallic=0.8)

# Procedural LED Video Screen Material
mat_screen = bpy.data.materials.new(name="M_ConcertLEDScreen")
mat_screen.use_nodes = True
mat_screen.diffuse_color = (0.0, 0.85, 1.0, 1.0)
s_nodes = mat_screen.node_tree.nodes
s_links = mat_screen.node_tree.links
s_nodes.clear()
s_out = s_nodes.new('ShaderNodeOutputMaterial')
s_emit = s_nodes.new('ShaderNodeEmission')
s_emit.inputs['Strength'].default_value = 10.0
s_coord = s_nodes.new('ShaderNodeTexCoord')
s_wave = s_nodes.new('ShaderNodeTexWave')
s_wave.wave_type = 'BANDS'
s_wave.inputs['Scale'].default_value = 1.4
s_wave.inputs['Distortion'].default_value = 5.0
s_ramp = s_nodes.new('ShaderNodeValToRGB')
s_ramp.color_ramp.elements[0].position = 0.0
s_ramp.color_ramp.elements[0].color = (0.08, 0.0, 0.25, 1.0) # Deep violet
s_ramp.color_ramp.elements[1].position = 1.0
s_ramp.color_ramp.elements[1].color = (0.0, 0.9, 1.0, 1.0)   # Cyan
el_mid1 = s_ramp.color_ramp.elements.new(0.42)
el_mid1.color = (1.0, 0.05, 0.70, 1.0) # Neon magenta
el_mid2 = s_ramp.color_ramp.elements.new(0.82)
el_mid2.color = (1.0, 0.95, 0.35, 1.0) # Electric gold
s_links.new(s_coord.outputs['Generated'], s_wave.inputs['Vector'])
s_links.new(s_wave.outputs['Color'], s_ramp.inputs['Fac'])
s_links.new(s_ramp.outputs['Color'], s_emit.inputs['Color'])
s_links.new(s_emit.outputs['Emission'], s_out.inputs['Surface'])

def make_box_obj(name, size_xyz, loc_xyz, mat, col):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= size_xyz[0]
        v.co.y *= size_xyz[1]
        v.co.z *= size_xyz[2]
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if mat: me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    o.location = loc_xyz
    col.objects.link(o)
    return o

# Protective Pitch Turf Decking ($65m wide x 85m long)
make_box_obj("Turf_Protection_Deck", (66.0, 86.0, 0.12), (0, 8.0, PITCH_Z + 0.06), mat_ground, col_stage)

# Mega-Stage Main Deck ($38m wide x 16m deep, 1.6m high)
STAGE_Y = 32.0
STAGE_DECK_Z = PITCH_Z + 1.6
make_box_obj("Stage_MainDeck", (38.0, 16.0, 1.6), (0, STAGE_Y, PITCH_Z + 0.8), mat_stage, col_stage)

# Catwalk Thrust (Extends 22m down the center pitch into crowd)
make_box_obj("Stage_CatwalkThrust", (3.6, 22.0, 1.3), (0, 13.0, PITCH_Z + 0.65), mat_catwalk, col_stage)

# Catwalk Performance Diamond / T-Head Stage
make_box_obj("Stage_Catwalk_T_Head", (8.5, 4.2, 1.3), (0, 2.0, PITCH_Z + 0.65), mat_catwalk, col_stage)

# DJ Riser & Console (Center Stage)
make_box_obj("Stage_DJRiser", (6.0, 3.2, 0.8), (0, STAGE_Y + 1.0, STAGE_DECK_Z + 0.4), mat_stage, col_stage)
make_box_obj("DJ_Booth_Console", (3.2, 1.0, 0.9), (0, STAGE_Y + 0.5, STAGE_DECK_Z + 1.25), mat_speaker, col_stage)

# Giant Stadium LED Backwall ($36m wide x 14m high)
make_box_obj("Stage_LED_Backwall", (36.0, 0.4, 14.0), (0, STAGE_Y + 8.2, STAGE_DECK_Z + 7.0), mat_screen, col_stage)

# Left & Right Stadium IMAG Screens ($9m wide x 12m high)
make_box_obj("LED_IMAG_Screen_Left",  (9.0, 0.4, 12.0), (-23.5, STAGE_Y + 2.0, STAGE_DECK_Z + 6.0), mat_screen, col_stage)
make_box_obj("LED_IMAG_Screen_Right", (9.0, 0.4, 12.0), (23.5,  STAGE_Y + 2.0, STAGE_DECK_Z + 6.0), mat_screen, col_stage)

# 3D Emissive Crown Sign: "TALANTA LIVE 2026"
font_data = bpy.data.curves.new(type='FONT', name='TalantaFontData')
font_data.body = "TALANTA LIVE"
font_data.size = 2.8
font_data.extrude = 0.2
mat_font = create_pbr_mat("M_TalantaSign", (1.0, 0.95, 0.8, 1.0), emission=(1.0, 0.85, 0.2, 1.0), emit_strength=20.0)
font_data.materials.append(mat_font)
sign_obj = bpy.data.objects.new("Stage_Sign_Talanta", font_data)
sign_obj.location = (-9.5, STAGE_Y + 8.0, STAGE_DECK_Z + 14.8)
sign_obj.rotation_euler = (math.radians(90), 0, 0)
col_stage.objects.link(sign_obj)

# Stadium Heavy-Duty Truss Towers
truss_coords = [
    # 4 Main Stage Towers (Reaching 20m high)
    (-19.0, STAGE_Y - 7.5, STAGE_DECK_Z + 10.0, 1.0, 1.0, 20.0),
    (19.0,  STAGE_Y - 7.5, STAGE_DECK_Z + 10.0, 1.0, 1.0, 20.0),
    (-19.0, STAGE_Y + 8.0, STAGE_DECK_Z + 11.0, 1.0, 1.0, 22.0),
    (19.0,  STAGE_Y + 8.0, STAGE_DECK_Z + 11.0, 1.0, 1.0, 22.0),
    # Top Crossbeams
    (0.0,   STAGE_Y - 7.5, STAGE_DECK_Z + 20.2, 39.0, 1.0, 1.0),
    (0.0,   STAGE_Y + 8.0, STAGE_DECK_Z + 22.2, 39.0, 1.0, 1.0),
    (-19.0, STAGE_Y + 0.2, STAGE_DECK_Z + 21.0, 1.0, 16.5, 1.0),
    (19.0,  STAGE_Y + 0.2, STAGE_DECK_Z + 21.0, 1.0, 16.5, 1.0),
    # Mid Lighting Rig Bar
    (0.0,   STAGE_Y - 7.5, STAGE_DECK_Z + 14.0, 39.0, 0.8, 0.8),
]
for idx, (tx, ty, tz, sx, sy, sz) in enumerate(truss_coords):
    make_box_obj(f"Truss_Frame_{idx:02d}", (sx, sy, sz), (tx, ty, tz), mat_truss, col_stage)

# Line-Array Speakers (J-Hangs flanking both sides, 8 per array)
for side_x in [-20.5, 20.5]:
    for spk_i in range(8):
        spk_z = STAGE_DECK_Z + 17.0 - spk_i * 1.05
        spk = make_box_obj(f"SpeakerArray_{'L' if side_x < 0 else 'R'}_{spk_i}", (1.8, 1.1, 0.7), (side_x, STAGE_Y - 6.5 + spk_i * 0.2, spk_z), mat_speaker, col_stage)
        spk.rotation_euler.x = math.radians(3 + spk_i * 4.0)

# Stage Foldback Wedge Monitors along stage edge
for mx in [-4.0, 4.0, -9.0, 9.0, -14.0, 14.0]:
    wedge = make_box_obj(f"Stage_Wedge_{mx}", (0.9, 0.55, 0.45), (mx, STAGE_Y - 7.2, STAGE_DECK_Z + 0.25), mat_speaker, col_stage)
    wedge.rotation_euler.x = math.radians(-25)

# Mojo Crowd Safety Barricades (Separating pitch crowd from catwalk & stage)
barricade_sections = [
    # Front of stage deck left & right
    ((-11.0, STAGE_Y - 8.2, PITCH_Z + 0.6), (14.5, 0.15, 1.2)),
    ((11.0,  STAGE_Y - 8.2, PITCH_Z + 0.6), (14.5, 0.15, 1.2)),
    # Catwalk flanks
    ((-2.4, 13.0, PITCH_Z + 0.6), (0.15, 20.0, 1.2)),
    ((2.4,  13.0, PITCH_Z + 0.6), (0.15, 20.0, 1.2)),
    # Catwalk T-head perimeter
    ((-4.8, 0.0, PITCH_Z + 0.6), (3.6, 0.15, 1.2)),
    ((4.8,  0.0, PITCH_Z + 0.6), (3.6, 0.15, 1.2)),
    ((0.0, -0.6, PITCH_Z + 0.6), (9.8, 0.15, 1.2)),
]
for b_idx, (b_loc, b_size) in enumerate(barricade_sections):
    make_box_obj(f"Mojo_Barricade_{b_idx:02d}", b_size, b_loc, mat_barricade, col_stage)

# ==========================================
# 3. STADIUM FLOODLIGHTS & CONCERT LASERS
# ==========================================
# 4 Stadium High-Mast Floodlights mounted on Upper Roof Rim (illuminates bowl & grandstands)
stadium_flood_coords = [
    (-85.0,  100.0, 52.0, math.radians(48), math.radians(-32), "StadiumFlood_NW"),
    (85.0,   100.0, 52.0, math.radians(48), math.radians(32),  "StadiumFlood_NE"),
    (-85.0, -100.0, 52.0, math.radians(52), math.radians(-32), "StadiumFlood_SW"),
    (85.0,  -100.0, 52.0, math.radians(52), math.radians(32),  "StadiumFlood_SE"),
]
for fx, fy, fz, rx, rz, fname in stadium_flood_coords:
    fl_data = bpy.data.lights.new(name=fname, type='SPOT')
    fl_data.energy = 85000.0
    fl_data.color = (0.85, 0.90, 1.0)
    fl_data.spot_size = math.radians(65)
    fl_data.spot_blend = 0.35
    fl_obj = bpy.data.objects.new(fname, fl_data)
    fl_obj.location = (fx, fy, fz)
    fl_obj.rotation_euler = (rx, 0, rz)
    col_lights.objects.link(fl_obj)

# Moving Concert Spotlights on Stage Truss
moving_lights = [
    ((-15.0, STAGE_Y - 7.5, STAGE_DECK_Z + 18.0), (1.0, 0.05, 0.75), math.radians(45), math.radians(-25), "Beam_Magenta_L"),
    ((15.0,  STAGE_Y - 7.5, STAGE_DECK_Z + 18.0), (0.0, 0.90, 1.0),  math.radians(45), math.radians(25),  "Beam_Cyan_R"),
    ((-7.5,  STAGE_Y - 7.5, STAGE_DECK_Z + 19.0), (0.95, 0.65, 0.0), math.radians(52), math.radians(-15), "Beam_Amber_L"),
    ((7.5,   STAGE_Y - 7.5, STAGE_DECK_Z + 19.0), (0.6, 0.1, 0.95),  math.radians(52), math.radians(15),  "Beam_Violet_R"),
    ((0.0,   STAGE_Y - 7.5, STAGE_DECK_Z + 19.0), (1.0, 0.95, 0.9),  math.radians(35), 0,                 "Beam_CenterKey"),
]
for (lx, ly, lz), lcol, rx, rz, lname in moving_lights:
    ld = bpy.data.lights.new(name=lname, type='SPOT')
    ld.energy = 28000.0
    ld.color = lcol
    ld.spot_size = math.radians(40)
    ld.spot_blend = 0.25
    lo = bpy.data.objects.new(lname, ld)
    lo.location = (lx, ly, lz)
    lo.rotation_euler = (rx, 0, rz)
    col_lights.objects.link(lo)

# High-Intensity Stadium Lasers (Shooting from Stage Truss up into Roof Canopy)
mat_laser_cyan = create_pbr_mat("M_LaserCyan", (0.0, 0.9, 1.0, 1.0), emission=(0.0, 0.95, 1.0, 1.0), emit_strength=50.0)
mat_laser_magenta = create_pbr_mat("M_LaserMagenta", (1.0, 0.05, 0.7, 1.0), emission=(1.0, 0.05, 0.7, 1.0), emit_strength=50.0)
mat_laser_green = create_pbr_mat("M_LaserGreen", (0.1, 1.0, 0.3, 1.0), emission=(0.1, 1.0, 0.3, 1.0), emit_strength=50.0)

laser_specs = [
    ((-18.0, STAGE_Y - 7.5, STAGE_DECK_Z + 20.0), math.radians(-25), math.radians(-40), mat_laser_cyan),
    ((18.0,  STAGE_Y - 7.5, STAGE_DECK_Z + 20.0), math.radians(-25), math.radians(40),  mat_laser_cyan),
    ((-10.0, STAGE_Y - 7.5, STAGE_DECK_Z + 20.0), math.radians(-20), math.radians(-20), mat_laser_magenta),
    ((10.0,  STAGE_Y - 7.5, STAGE_DECK_Z + 20.0), math.radians(-20), math.radians(20),  mat_laser_magenta),
    ((-3.0,  STAGE_Y - 7.5, STAGE_DECK_Z + 20.0), math.radians(-30), math.radians(-8),  mat_laser_green),
    ((3.0,   STAGE_Y - 7.5, STAGE_DECK_Z + 20.0), math.radians(-30), math.radians(8),   mat_laser_green),
]
for l_idx, (l_origin, l_rot_x, l_rot_z, l_mat) in enumerate(laser_specs):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.05, radius2=0.15, depth=90.0)
    me = bpy.data.meshes.new(f"LaserBeamMesh_{l_idx}")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(l_mat)
    laser_obj = bpy.data.objects.new(f"Laser_Beam_{l_idx:02d}", me)
    laser_obj.location = (l_origin[0], l_origin[1] - 40.0, l_origin[2] + 20.0)
    laser_obj.rotation_euler = (l_rot_x + math.radians(65), 0, l_rot_z)
    col_lasers.objects.link(laser_obj)

# ==========================================
# 4. IMPORT MIXAMO PROTOTYPES & DANCE ARCHETYPES
# ==========================================
print("Importing Mixamo prototypes...")
bpy.ops.import_scene.fbx(filepath='E:/M5/grao/blender/assets/people/Samba_Dancing.fbx')
arm_samba = bpy.data.objects['Armature']
surf_samba = bpy.data.objects['Alpha_Surface']
joints_samba = bpy.data.objects.get('Alpha_Joints')
arm_samba.name = "Proto_Armature_Samba"
surf_samba.name = "Proto_Surface_Samba"
if joints_samba: joints_samba.name = "Proto_Joints_Samba"
arm_samba.location = (500.0, 0, 0) # Offscreen

bpy.ops.import_scene.fbx(filepath='E:/M5/grao/blender/assets/people/Hip_Hop_Dancing.fbx')
arm_hiphop = [o for o in bpy.data.objects if o.name.startswith("Armature") and o != arm_samba][0]
surf_hiphop = [o for o in bpy.data.objects if o.name.startswith("Alpha_Surface") and o != surf_samba][0]
joints_hiphop = [o for o in bpy.data.objects if o.name.startswith("Alpha_Joints") and o != joints_samba]
joints_hiphop = joints_hiphop[0] if joints_hiphop else None
arm_hiphop.name = "Proto_Armature_HipHop"
surf_hiphop.name = "Proto_Surface_HipHop"
if joints_hiphop: joints_hiphop.name = "Proto_Joints_HipHop"
arm_hiphop.location = (520.0, 0, 0) # Offscreen

for o in [arm_samba, surf_samba, joints_samba, arm_hiphop, surf_hiphop, joints_hiphop]:
    if o:
        col_archetypes.objects.link(o)
        for c in list(o.users_collection):
            if c != col_archetypes: c.objects.unlink(o)

# Avatar Materials
avatar_mats = [
    create_pbr_mat("Avatar_ElectricCyan", (0.0, 0.85, 1.0, 1.0), roughness=0.35),
    create_pbr_mat("Avatar_HotMagenta",   (1.0, 0.12, 0.65, 1.0), roughness=0.35),
    create_pbr_mat("Avatar_NeonLime",     (0.25, 0.95, 0.2, 1.0), roughness=0.35),
    create_pbr_mat("Avatar_SunsetOrange", (1.0, 0.45, 0.05, 1.0), roughness=0.35),
    create_pbr_mat("Avatar_ElectricGold", (1.0, 0.88, 0.12, 1.0), roughness=0.35),
    create_pbr_mat("Avatar_PureWhite",    (0.96, 0.96, 0.98, 1.0), roughness=0.25),
    create_pbr_mat("Avatar_DeepViolet",   (0.55, 0.15, 0.95, 1.0), roughness=0.35),
    create_pbr_mat("Avatar_CrimsonRed",   (0.92, 0.08, 0.15, 1.0), roughness=0.35),
]

# Create 8 Master Crowd Archetypes
archetype_collections = []
configs = [
    ("Arch_HipHop_Cyan",    arm_hiphop, surf_hiphop, joints_hiphop, 0,   avatar_mats[0]),
    ("Arch_Samba_Magenta",  arm_samba,  surf_samba,  joints_samba,  0,   avatar_mats[1]),
    ("Arch_HipHop_Lime",    arm_hiphop, surf_hiphop, joints_hiphop, 32,  avatar_mats[2]),
    ("Arch_Samba_Orange",   arm_samba,  surf_samba,  joints_samba,  52,  avatar_mats[3]),
    ("Arch_HipHop_Gold",    arm_hiphop, surf_hiphop, joints_hiphop, 74,  avatar_mats[4]),
    ("Arch_Samba_White",    arm_samba,  surf_samba,  joints_samba,  96,  avatar_mats[5]),
    ("Arch_HipHop_Violet",  arm_hiphop, surf_hiphop, joints_hiphop, 118, avatar_mats[6]),
    ("Arch_Samba_Crimson",  arm_samba,  surf_samba,  joints_samba,  140, avatar_mats[7]),
]

for col_name, src_arm, src_surf, src_joints, offset, outfit_mat in configs:
    arch_col = bpy.data.collections.new(col_name)
    col_archetypes.children.link(arch_col)
    archetype_collections.append(arch_col)

    bpy.ops.object.select_all(action='DESELECT')
    src_arm.select_set(True)
    src_surf.select_set(True)
    if src_joints: src_joints.select_set(True)
    bpy.context.view_layer.objects.active = src_arm
    bpy.ops.object.duplicate(linked=False)
    dup_arm = bpy.context.active_object
    dup_arm.name = f"{col_name}_Armature"
    dup_arm.location = (0, 0, 0)
    dup_arm.scale = (0.01, 0.01, 0.01)

    if offset > 0 and dup_arm.animation_data and dup_arm.animation_data.action:
        act = dup_arm.animation_data.action.copy()
        dup_arm.animation_data.action = act
        if act.is_action_layered:
            cb = act.layers[0].strips[0].channelbags[0]
            for fc in cb.fcurves:
                for kp in fc.keyframe_points:
                    kp.co.x -= offset

    arch_col.objects.link(dup_arm)
    for c in list(dup_arm.users_collection):
        if c != arch_col: c.objects.unlink(dup_arm)

    for ch in list(dup_arm.children):
        arch_col.objects.link(ch)
        for c in list(ch.users_collection):
            if c != arch_col: c.objects.unlink(ch)
        if ch.data and hasattr(ch.data, 'materials') and len(ch.data.materials) > 0:
            ch.data.materials[0] = outfit_mat

# ==========================================
# 5. SPECIAL LEAD ARTIST ARCHETYPE (MC / SINGER)
# Holding Microphone & Raising/Pumping Arm Rhythmicaly
# ==========================================
col_lead_artist = bpy.data.collections.new("Arch_LeadArtist_Frontman")
col_archetypes.children.link(col_lead_artist)

bpy.ops.object.select_all(action='DESELECT')
arm_hiphop.select_set(True)
surf_hiphop.select_set(True)
if joints_hiphop: joints_hiphop.select_set(True)
bpy.context.view_layer.objects.active = arm_hiphop
bpy.ops.object.duplicate(linked=False)
lead_arm = bpy.context.active_object
lead_arm.name = "LeadArtist_Armature"
lead_arm.location = (0, 0, 0)
lead_arm.scale = (0.01, 0.01, 0.01)

# Custom Action for Lead Singer
act_lead = lead_arm.animation_data.action.copy()
act_lead.name = "Action_LeadSinger_Concert"
lead_arm.animation_data.action = act_lead

if act_lead.is_action_layered:
    cb = act_lead.layers[0].strips[0].channelbags[0]
    to_remove = [fc for fc in cb.fcurves if any(b in fc.data_path for b in ['LeftArm', 'LeftForeArm', 'RightArm', 'RightForeArm'])]
    for fc in to_remove:
        cb.fcurves.remove(fc)

bpy.context.view_layer.objects.active = lead_arm
bpy.ops.object.mode_set(mode='POSE')
r_arm = lead_arm.pose.bones.get('mixamorig:RightArm')
r_fore = lead_arm.pose.bones.get('mixamorig:RightForeArm')
l_arm = lead_arm.pose.bones.get('mixamorig:LeftArm')
l_fore = lead_arm.pose.bones.get('mixamorig:LeftForeArm')

for b in [r_arm, r_fore, l_arm, l_fore]:
    b.rotation_mode = 'XYZ'

# Pose Right Arm holding mic up to mouth
r_arm.rotation_euler = (math.radians(-65), math.radians(20), math.radians(-35))
r_fore.rotation_euler = (math.radians(95), math.radians(-10), math.radians(15))

# Animate Left Arm pumping up and down to crowd
pump_frames = [
    (1,   math.radians(-115), math.radians(45)),
    (15,  math.radians(-35),  math.radians(15)),
    (30,  math.radians(-120), math.radians(50)),
    (45,  math.radians(-35),  math.radians(15)),
    (60,  math.radians(-125), math.radians(55)),
    (75,  math.radians(-35),  math.radians(15)),
    (90,  math.radians(-120), math.radians(50)),
    (105, math.radians(-35),  math.radians(15)),
    (120, math.radians(-115), math.radians(45)),
]
for f, arm_pitch, fore_bend in pump_frames:
    l_arm.rotation_euler = (arm_pitch, math.radians(-15), math.radians(20))
    l_fore.rotation_euler = (fore_bend, 0, 0)
    l_arm.keyframe_insert(data_path="rotation_euler", frame=f)
    l_fore.keyframe_insert(data_path="rotation_euler", frame=f)
    r_arm.keyframe_insert(data_path="rotation_euler", frame=f)
    r_fore.keyframe_insert(data_path="rotation_euler", frame=f)

bpy.ops.object.mode_set(mode='OBJECT')

col_lead_artist.objects.link(lead_arm)
for c in list(lead_arm.users_collection):
    if c != col_lead_artist: c.objects.unlink(lead_arm)

for ch in list(lead_arm.children):
    col_lead_artist.objects.link(ch)
    for c in list(ch.users_collection):
        if c != col_lead_artist: c.objects.unlink(ch)
    if ch.data and hasattr(ch.data, 'materials') and len(ch.data.materials) > 0:
        ch.data.materials[0] = avatar_mats[1] # Hero Magenta Outfit

# Add 3D Microphone prop to Lead Artist
mic_obj = make_box_obj("LeadArtist_Microphone", (0.05, 0.05, 0.22), (0.22, 0.28, 1.48), mat_mic, col_lead_artist)
mic_obj.parent = lead_arm

# Instantiate Lead Artist on Catwalk T-Head (Commanding the Stadium Crowd!)
lead_instance = bpy.data.objects.new("Lead_Artist_Frontman", None)
lead_instance.instance_type = 'COLLECTION'
lead_instance.instance_collection = col_lead_artist
lead_instance.location = (0.0, 2.5, PITCH_Z + 1.3) # On catwalk T-head
lead_instance.rotation_euler = (0, 0, math.radians(180)) # Facing stadium crowd!
lead_instance.scale = (1.1, 1.1, 1.1)
col_stage.objects.link(lead_instance)

# Instantiate DJ on Main Stage Riser
dj_instance = bpy.data.objects.new("DJ_Performer_Stage", None)
dj_instance.instance_type = 'COLLECTION'
dj_instance.instance_collection = archetype_collections[0] # Cyan HipHop DJ
dj_instance.location = (0.0, STAGE_Y + 1.2, STAGE_DECK_Z + 0.8)
dj_instance.rotation_euler = (0, 0, 0)
dj_instance.scale = (1.1, 1.1, 1.1)
col_stage.objects.link(dj_instance)

# ==========================================
# 6. POPULATE 250+ PACKED DANCERS ON PITCH
# (Densely packing Golden Circle, Catwalk Wings & GA Floor)
# ==========================================
random.seed(2026)

crowd_positions = []

# Section A: Front of Catwalk T-Head (Golden Circle VIP Pit, Y: -12m to 1.5m)
while len(crowd_positions) < 90:
    px = random.uniform(-14.0, 14.0)
    py = random.uniform(-12.0, 1.0)
    too_close = False
    for ex, ey, _ in crowd_positions:
        if math.hypot(px - ex, py - ey) < 0.72:
            too_close = True
            break
    if not too_close:
        crowd_positions.append((px, py, PITCH_Z + 0.12))

# Section B: Left Wing Flanking Catwalk (X: -18m to -2.8m, Y: 1.5m to 23.5m)
while len(crowd_positions) < 170:
    px = random.uniform(-18.0, -2.8)
    py = random.uniform(1.5, 23.5)
    too_close = False
    for ex, ey, _ in crowd_positions:
        if math.hypot(px - ex, py - ey) < 0.72:
            too_close = True
            break
    if not too_close:
        crowd_positions.append((px, py, PITCH_Z + 0.12))

# Section C: Right Wing Flanking Catwalk (X: 2.8m to 18.0m, Y: 1.5m to 23.5m)
while len(crowd_positions) < 250:
    px = random.uniform(2.8, 18.0)
    py = random.uniform(1.5, 23.5)
    too_close = False
    for ex, ey, _ in crowd_positions:
        if math.hypot(px - ex, py - ey) < 0.72:
            too_close = True
            break
    if not too_close:
        crowd_positions.append((px, py, PITCH_Z + 0.12))

# Section D: General Admission Pitch Extension (Y: -24.0m to -12.0m)
while len(crowd_positions) < 300:
    px = random.uniform(-22.0, 22.0)
    py = random.uniform(-24.0, -12.0)
    too_close = False
    for ex, ey, _ in crowd_positions:
        if math.hypot(px - ex, py - ey) < 0.75:
            too_close = True
            break
    if not too_close:
        crowd_positions.append((px, py, PITCH_Z + 0.12))

for idx, (px, py, pz) in enumerate(crowd_positions):
    chosen_arch = archetype_collections[idx % len(archetype_collections)]
    dancer_inst = bpy.data.objects.new(f"Dancer_{idx:03d}_Pitch", None)
    dancer_inst.instance_type = 'COLLECTION'
    dancer_inst.instance_collection = chosen_arch
    dancer_inst.location = (px, py, pz)

    # Face the catwalk frontman (0, 2.5) or stage center (0, 32)
    target_y = 2.5 if py < 2.0 else 18.0
    angle_to_stage = math.atan2(target_y - py, 0.0 - px) - math.pi / 2
    angle_to_stage += random.uniform(-math.radians(16), math.radians(16))
    dancer_inst.rotation_euler = (0, 0, angle_to_stage)

    # Height variation
    scale_jitter = random.uniform(0.93, 1.07)
    dancer_inst.scale = (scale_jitter, scale_jitter, scale_jitter)

    col_crowd.objects.link(dancer_inst)

print(f"Instanced {len(crowd_positions)} realistic Mixamo dancers across stadium pitch!")

# ==========================================
# 7. CINEMATIC STADIUM CONCERT CAMERA
# High-angle grandstand crane push-in capturing full stadium scale
# ==========================================
cam_data = bpy.data.cameras.new("Stadium_Concert_Camera")
cam_data.lens = 22.0
cam_data.clip_end = 500.0
cam_obj = bpy.data.objects.new("Concert_Crane_Camera", cam_data)
scene.camera = cam_obj
col_camera.objects.link(cam_obj)

# Camera starts elevated in lower grandstands framing the entire stadium bowl, roof, and mega-stage,
# then sweeps forward and down toward the catwalk lead artist!
cam_kf = [
    (1,   (-4.5, -26.0, PITCH_Z + 14.5), (math.radians(72), 0, math.radians(-7))),
    (60,  (0.0,  -14.0, PITCH_Z + 9.5),  (math.radians(70), 0, math.radians(0))),
    (120, (2.8,   -4.5, PITCH_Z + 5.5),  (math.radians(68), 0, math.radians(10))),
]
for f, loc, rot in cam_kf:
    cam_obj.location = loc
    cam_obj.rotation_euler = rot
    cam_obj.keyframe_insert(data_path="location", frame=f)
    cam_obj.keyframe_insert(data_path="rotation_euler", frame=f)

# ==========================================
# 8. OUTPUTS: BLEND, GLB, PREVIEW IMAGE & VIDEO
# ==========================================
out_dir = Path("E:/M5/grao/blender/out")
out_dir.mkdir(parents=True, exist_ok=True)

blend_path = out_dir / "talanta_stadium_concert_master.blend"
glb_path = out_dir / "talanta_stadium_concert_master.glb"
preview_img = out_dir / "stadium_concert_master_preview.png"

bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
print(f" Saved Master Blend: {blend_path}")

# Render Frame 45 Preview in EEVEE
scene.frame_set(45)
scene.render.filepath = str(preview_img)
try:
    print("Rendering high-impact EEVEE beauty preview (Frame 45)...")
    bpy.ops.render.render(write_still=True)
    print(f" Rendered Beauty Preview: {preview_img}")
except Exception as e:
    print(f" Render note: {e}")

# Export Animated GLB
try:
    print("Exporting animated glTF stadium concert asset...")
    bpy.ops.export_scene.gltf(
        filepath=str(glb_path),
        export_format='GLB',
        export_animations=True,
        export_apply=False,
    )
    print(f" Exported GLB: {glb_path}")
except Exception as e:
    print(f" GLTF export note: {e}")

print("=== TALANTA STADIUM CONCERT MASTER BUILD COMPLETED ===")
