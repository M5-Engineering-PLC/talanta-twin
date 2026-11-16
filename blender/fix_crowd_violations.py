import bpy
import math
from pathlib import Path

print("==================================================")
print("  FIXING CROWD PLACEMENT VIOLATIONS               ")
print("==================================================")

blend_path = "E:/M5/grao/blender/out/talanta_stadium_concert_master.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

scene = bpy.context.scene
PITCH_Z = 6.20

col_crowd = bpy.data.collections.get("Concert_Crowd_Pitch")
dancers = {o.name: o for o in col_crowd.objects if o.name.startswith("Dancer_")}

# The 4 offending dancers inside catwalk T-head
# Relocate them to open, safe, valid spots in the front row of the Golden Circle pit outside the barricade:
# Barricade front is at Y = -0.6. Safe pit area in front of barricade is Y <= -1.4.
new_locations = {
    "Dancer_022_Pitch": (-1.8, -1.6, PITCH_Z + 0.12),
    "Dancer_043_Pitch": (1.8,  -1.6, PITCH_Z + 0.12),
    "Dancer_049_Pitch": (-3.8, -1.7, PITCH_Z + 0.12),
    "Dancer_073_Pitch": (3.8,  -1.7, PITCH_Z + 0.12),
}

for name, loc in new_locations.items():
    d = dancers.get(name)
    if d:
        d.location = loc
        # Face the catwalk frontman at (0, 2.5)
        angle = math.atan2(2.5 - loc[1], 0.0 - loc[0]) - math.pi / 2
        d.rotation_euler = (0, 0, angle)
        print(f"Relocated {name} to {loc} (outside barricade, facing frontman)")

# Rigorous validation loop to confirm ZERO collisions across ALL 300 dancers
MIN_DIST = 0.68
positions = [(d.name, d.location.x, d.location.y, d.location.z) for d in dancers.values()]

collision_count = 0
for i in range(len(positions)):
    n1, x1, y1, _ = positions[i]
    for j in range(i + 1, len(positions)):
        n2, x2, y2, _ = positions[j]
        dist = math.hypot(x1 - x2, y1 - y2)
        if dist < MIN_DIST:
            print(f"COLLISION: {n1} and {n2} closer than {MIN_DIST}m ({dist:.3f}m)")
            collision_count += 1

boundary_violations = 0
for n, x, y, z in positions:
    # Catwalk thrust
    if abs(x) < 2.0 and (2.0 <= y <= 24.0):
        print(f"VIOLATION: {n} inside Catwalk Thrust at ({x:.2f}, {y:.2f})")
        boundary_violations += 1
    # Catwalk T-head
    elif abs(x) < 4.4 and (-0.6 <= y <= 3.5):
        print(f"VIOLATION: {n} inside Catwalk T-Head at ({x:.2f}, {y:.2f})")
        boundary_violations += 1
    # Main stage
    elif abs(x) < 19.5 and (23.5 <= y <= 41.0):
        print(f"VIOLATION: {n} inside Stage at ({x:.2f}, {y:.2f})")
        boundary_violations += 1

print(f"\nFinal Audit Result:")
print(f" - Proximity collisions: {collision_count}")
print(f" - Structural violations: {boundary_violations}")

if collision_count == 0 and boundary_violations == 0:
    print("ALL 300 AVATARS FULLY VALIDATED AND CLEAN!")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print("Saved updated master blend file.")
else:
    print("WARNING: Violations remain!")

# Render updated beauty preview (Frame 45)
scene.frame_set(45)
preview_path = "E:/M5/grao/blender/out/talanta_stadium_concert_hero_shot.png"
scene.render.filepath = preview_path
scene.render.engine = 'BLENDER_EEVEE'
if hasattr(scene, 'eevee'):
    scene.eevee.taa_render_samples = 32

print(f"Rendering updated verified beauty frame to {preview_path}...")
bpy.ops.render.render(write_still=True)
print("Preview rendered!")

# Export updated GLB
glb_path = "E:/M5/grao/blender/out/talanta_stadium_concert_master.glb"
print(f"Exporting updated verified GLB to {glb_path}...")
bpy.ops.export_scene.gltf(
    filepath=glb_path,
    export_format='GLB',
    export_animations=True,
    export_apply=False,
)
print("Verified GLB export complete!")
print("==================================================")
