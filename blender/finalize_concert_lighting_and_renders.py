import bpy
import math
import shutil
from pathlib import Path

print("==================================================")
print("  POLISHING CONCERT LIGHTING & CINEMATIC CAMERA   ")
print("==================================================")

blend_path = "E:/M5/grao/blender/out/talanta_stadium_concert_master.blend"
glb_path = "E:/M5/grao/blender/out/talanta_stadium_concert_master.glb"
app_glb = "E:/M5/grao/app/public/data/talanta_stadium_concert_master.glb"
bpy.ops.wm.open_mainfile(filepath=blend_path)

scene = bpy.context.scene
PITCH_Z = 6.20

col_lights = bpy.data.collections.get("Concert_Lighting")
if not col_lights:
    col_lights = bpy.data.collections.new("Concert_Lighting")
    scene.collection.children.link(col_lights)

# 1. Catwalk Followspots (Crisp key lighting on frontman)
def add_spot(name, loc, rot, energy, color, size_deg, blend=0.3):
    old = bpy.data.objects.get(name)
    if old: bpy.data.objects.remove(old, do_unlink=True)
    sd = bpy.data.lights.new(name=name, type='SPOT')
    sd.energy = energy
    sd.color = color
    sd.spot_size = math.radians(size_deg)
    sd.spot_blend = blend
    so = bpy.data.objects.new(name, sd)
    so.location = loc
    so.rotation_euler = rot
    col_lights.objects.link(so)
    return so

# Left & Right Followspots for Frontman
add_spot("Followspot_Frontman_L", (-10.0, -8.0, PITCH_Z + 9.5), (math.radians(38), math.radians(-12), math.radians(-32)), 55000.0, (1.0, 0.95, 0.90), 42)
add_spot("Followspot_Frontman_R", ( 10.0, -8.0, PITCH_Z + 9.5), (math.radians(38), math.radians( 12), math.radians( 32)), 55000.0, (1.0, 0.95, 0.90), 42)

# Golden Circle Crowd Front Wash (illuminating audience faces & outfits)
add_spot("Crowd_GoldenCircle_Wash", (0.0, 24.0, PITCH_Z + 15.0), (math.radians(44), 0, 0), 65000.0, (0.92, 0.88, 1.0), 75)
add_spot("Crowd_Pit_Fill", (0.0, -18.0, PITCH_Z + 12.0), (math.radians(-35), 0, math.radians(180)), 40000.0, (0.85, 0.92, 1.0), 65)

# 2. Refined Cinematic Drone Camera Path
cam = scene.camera
if not cam:
    cam_data = bpy.data.cameras.new("Concert_Drone_Camera")
    cam = bpy.data.objects.new("Concert_Drone_Camera", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

cam.data.clip_end = 600.0
cam.animation_data_clear()

# 150 Frames Choreography:
# Frame 1: Low glide between dancing audience members in Golden Circle
# Frame 45: Pushing past glowing smartphone screens towards catwalk T-head
# Frame 75: Hero close-up on MC Frontman (three-quarter angle, looking up)
# Frame 115: Smooth crane pull-out revealing the stage and golden circle
# Frame 150: Majestic arena overview showing full stadium bowl, lasers, and packed floor
drone_keyframes = [
    # (frame, (X, Y, Z), (rot_X, rot_Y, rot_Z), lens)
    (1,   (-2.2, -10.5, PITCH_Z + 1.95), (math.radians(82),  0, math.radians(-8)),  22.0),
    (45,  (-1.4,  -5.2, PITCH_Z + 2.45), (math.radians(76),  0, math.radians(-6)),  26.0),
    (75,  (-0.9,  -1.8, PITCH_Z + 3.10), (math.radians(71),  0, math.radians(10)),  35.0), # Hero Frontman Close-up
    (115, (-0.2, -11.0, PITCH_Z + 6.80), (math.radians(72),  0, math.radians(0)),   24.0),
    (150, ( 0.0, -22.5, PITCH_Z + 12.2), (math.radians(70),  0, math.radians(0)),   19.0), # Epic Stadium Reveal (Safe from lattice)
]

for f, loc, rot, lens in drone_keyframes:
    cam.location = loc
    cam.rotation_euler = rot
    cam.data.lens = lens
    cam.keyframe_insert(data_path="location", frame=f)
    cam.keyframe_insert(data_path="rotation_euler", frame=f)
    cam.data.keyframe_insert(data_path="lens", frame=f)

# Save Master Blend
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print(f"Saved refined master blend: {blend_path}")

# Export Synchronized Animated GLB
try:
    print("Exporting updated GLB...")
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
        export_format='GLB',
        export_animations=True,
        export_apply=False,
    )
    print(f"Exported: {glb_path}")
    if Path(app_glb).parent.exists():
        shutil.copy2(glb_path, app_glb)
        print(f"Copied to app: {app_glb}")
except Exception as e:
    print(f"GLTF Export note: {e}")

# 3. Render 3 High-Impact Verification Beauty Frames
out_dir = Path("E:/M5/grao/blender/out")
artifact_dir = Path("C:/Users/hp/.gemini/antigravity/brain/afadf3b7-ab21-44d5-9df2-c128a411b3d0")

scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.engine = 'BLENDER_EEVEE'
if hasattr(scene, 'eevee'):
    scene.eevee.taa_render_samples = 32

verify_shots = [
    (75,  "concert_drone_frontman_hero.png", "Hero Drone close-up on MC Frontman & Stage"),
    (45,  "concert_crowd_spacing_verify.png", "Golden Circle Pit crowd pass-through with clear spacing & glowing phones"),
    (150, "concert_stadium_epic_reveal.png",  "High crane reveal of 60,000 capacity Talanta Stadium arena & lasers"),
]

for fnum, fname, label in verify_shots:
    scene.frame_set(fnum)
    dest_blend = out_dir / fname
    scene.render.filepath = str(dest_blend)
    print(f"\nRendering Frame {fnum}: {label}...")
    bpy.ops.render.render(write_still=True)
    dest_art = artifact_dir / fname
    shutil.copy2(str(dest_blend), str(dest_art))
    print(f" Rendered and copied: {dest_art}")

print("\n=== POLISHING AND VERIFICATION RENDERS COMPLETE ===")
