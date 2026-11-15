import bpy
import math
from pathlib import Path

blend_path = "E:/M5/grao/blender/out/talanta_stadium_concert_master.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

scene = bpy.context.scene
PITCH_Z = 6.20

# 1. Add High-Intensity Followspots directly illuminating the Catwalk Frontman
col_lights = bpy.data.collections.get("Concert_Lighting")
if not col_lights:
    col_lights = scene.collection

# Catwalk Followspot L & R
follow_l_data = bpy.data.lights.new(name="Followspot_Lead_L", type='SPOT')
follow_l_data.energy = 45000.0
follow_l_data.color = (1.0, 0.96, 0.90)
follow_l_data.spot_size = math.radians(45)
follow_l_obj = bpy.data.objects.new("Followspot_Lead_L", follow_l_data)
follow_l_obj.location = (-12.0, -8.0, PITCH_Z + 10.0)
follow_l_obj.rotation_euler = (math.radians(35), math.radians(-15), math.radians(-35))
col_lights.objects.link(follow_l_obj)

follow_r_data = bpy.data.lights.new(name="Followspot_Lead_R", type='SPOT')
follow_r_data.energy = 45000.0
follow_r_data.color = (1.0, 0.96, 0.90)
follow_r_data.spot_size = math.radians(45)
follow_r_obj = bpy.data.objects.new("Followspot_Lead_R", follow_r_data)
follow_r_obj.location = (12.0, -8.0, PITCH_Z + 10.0)
follow_r_obj.rotation_euler = (math.radians(35), math.radians(15), math.radians(35))
col_lights.objects.link(follow_r_obj)

# Front Crowd Wash Light (illuminating the sea of dancers in front of stage)
crowd_wash_data = bpy.data.lights.new(name="Crowd_Front_Wash", type='SPOT')
crowd_wash_data.energy = 55000.0
crowd_wash_data.color = (0.95, 0.85, 1.0) # Slight violet-white festival wash
crowd_wash_data.spot_size = math.radians(75)
crowd_wash_obj = bpy.data.objects.new("Crowd_Front_Wash", crowd_wash_data)
crowd_wash_obj.location = (0.0, 24.0, PITCH_Z + 14.0)
crowd_wash_obj.rotation_euler = (math.radians(42), 0, 0)
col_lights.objects.link(crowd_wash_obj)

# 2. Hero Stadium Concert Camera: Elevated Golden Circle vantage
cam = scene.camera
if not cam:
    cam_data = bpy.data.cameras.new("Stadium_Concert_Camera")
    cam = bpy.data.objects.new("Stadium_Concert_Camera", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

cam.data.lens = 20.0
cam.data.clip_end = 500.0

# Frame 45: Sweeping crane shot positioned right behind the front pit crowd,
# framing the lead artist frontman commanding the audience, with the towering stage,
# massive LED video walls, lasers, and curved stadium bowl behind!
cam.location = (-1.8, -7.5, PITCH_Z + 4.2)
cam.rotation_euler = (math.radians(73), 0, math.radians(-8))

scene.frame_set(45)
preview_path = "E:/M5/grao/blender/out/talanta_stadium_concert_hero_shot.png"
scene.render.filepath = preview_path
scene.render.engine = 'BLENDER_EEVEE'
if hasattr(scene, 'eevee'):
    scene.eevee.taa_render_samples = 32

print(f"Rendering Hero Stadium Concert Shot to {preview_path}...")
bpy.ops.render.render(write_still=True)
print("Hero render complete!")

# Save the updated blend file with these lights and camera
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print("Updated blend file saved successfully!")
