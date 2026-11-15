import bpy
import math

print("==================================================")
print("  FINALIZE 100% COLLISION-FREE CROWD PLACEMENTS   ")
print("==================================================")

blend_path = "E:/M5/grao/blender/out/talanta_stadium_concert_master.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

scene = bpy.context.scene
PITCH_Z = 6.20

col_crowd = bpy.data.collections.get("Concert_Crowd_Pitch")
dancers = {o.name: o for o in col_crowd.objects if o.name.startswith("Dancer_")}

verified_open_slots = {
    "Dancer_022_Pitch": (-6.60, -1.90, PITCH_Z + 0.12),
    "Dancer_043_Pitch": (-2.40, -4.10, PITCH_Z + 0.12),
    "Dancer_049_Pitch": (5.00,  -6.00, PITCH_Z + 0.12),
    "Dancer_073_Pitch": (0.60,  -4.10, PITCH_Z + 0.12),
}

for name, loc in verified_open_slots.items():
    d = dancers.get(name)
    if d:
        d.location = loc
        angle = math.atan2(2.5 - loc[1], 0.0 - loc[0]) - math.pi / 2
        d.rotation_euler = (0, 0, angle)
        print(f"Set {name} to verified open slot {loc}")

# Comprehensive Audit of all 300 dancers
MIN_SAFE_DIST = 0.70
positions = [(d.name, d.location.x, d.location.y, d.location.z) for d in dancers.values()]

collisions = []
for i in range(len(positions)):
    n1, x1, y1, _ = positions[i]
    for j in range(i + 1, len(positions)):
        n2, x2, y2, _ = positions[j]
        d = math.hypot(x1 - x2, y1 - y2)
        if d < MIN_SAFE_DIST:
            collisions.append((n1, n2, d))

boundary_errors = []
for n, x, y, z in positions:
    # Inside Catwalk Thrust
    if abs(x) < 2.0 and (2.0 <= y <= 24.0):
        boundary_errors.append((n, f"Inside Catwalk Thrust ({x:.2f}, {y:.2f})"))
    # Inside Catwalk T-Head
    elif abs(x) < 4.4 and (-0.6 <= y <= 3.5):
        boundary_errors.append((n, f"Inside Catwalk T-Head ({x:.2f}, {y:.2f})"))
    # Inside Main Stage
    elif abs(x) < 19.5 and (23.5 <= y <= 41.0):
        boundary_errors.append((n, f"Inside Main Stage ({x:.2f}, {y:.2f})"))
    # Outside pitch
    elif abs(x) > 34.0 or abs(y) > 50.0:
        boundary_errors.append((n, f"Outside Pitch Bounds ({x:.2f}, {y:.2f})"))

print(f"\nAUDIT VERIFICATION SUMMARY:")
print(f"Total Avatars Checked: {len(positions)}")
print(f"Proximity Collisions (< {MIN_SAFE_DIST}m): {len(collisions)}")
print(f"Structural Boundary Errors: {len(boundary_errors)}")

if len(collisions) == 0 and len(boundary_errors) == 0:
    print("\n>>> ZERO DEFECTS VERIFIED: 100% CLEAN AND REALISTIC PLACEMENTS! <<<")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print("Saved verified master blend file.")
    
    # Render beauty frame
    scene.frame_set(45)
    preview_path = "E:/M5/grao/blender/out/talanta_stadium_concert_hero_shot.png"
    scene.render.filepath = preview_path
    scene.render.engine = 'BLENDER_EEVEE'
    if hasattr(scene, 'eevee'):
        scene.eevee.taa_render_samples = 32
    bpy.ops.render.render(write_still=True)
    print("Rendered beauty preview image.")
else:
    print(f"FAILED: Collisions: {collisions}, Boundary Errors: {boundary_errors}")
    raise RuntimeError("Audit failed verification checks.")
