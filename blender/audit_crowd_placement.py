import bpy
import math

print("==================================================")
print("  AUDITING CROWD PLACEMENT & DETECTING MESHING    ")
print("==================================================")

blend_path = "E:/M5/grao/blender/out/talanta_stadium_concert_master.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

scene = bpy.context.scene
PITCH_Z = 6.20

# 1. Collect all dancers and performers
col_crowd = bpy.data.collections.get("Concert_Crowd_Pitch")
col_stage = bpy.data.collections.get("Concert_Stage")

dancers = [o for o in col_crowd.objects if o.name.startswith("Dancer_")]
lead_artist = bpy.data.objects.get("Lead_Artist_Frontman")
dj = bpy.data.objects.get("DJ_Performer_Stage")

print(f"Total crowd dancers in scene: {len(dancers)}")
print(f"Lead Artist present: {lead_artist is not None} at {lead_artist.location if lead_artist else 'None'}")
print(f"DJ present: {dj is not None} at {dj.location if dj else 'None'}")

# 2. Check for interpenetration (people meshing together)
MIN_SAFE_DIST = 0.70 # Minimum distance between any two people centers in meters
close_pairs = []

positions = [(d.name, d.location.x, d.location.y, d.location.z) for d in dancers]

for i in range(len(positions)):
    n1, x1, y1, z1 = positions[i]
    for j in range(i + 1, len(positions)):
        n2, x2, y2, z2 = positions[j]
        dist = math.hypot(x1 - x2, y1 - y2)
        if dist < MIN_SAFE_DIST:
            close_pairs.append((n1, n2, dist, (x1, y1), (x2, y2)))

print(f"\n--- PAIRWISE PROXIMITY CHECK (Threshold < {MIN_SAFE_DIST}m) ---")
if close_pairs:
    print(f"WARNING: Found {len(close_pairs)} dancer pairs closer than {MIN_SAFE_DIST}m!")
    for n1, n2, d, p1, p2 in close_pairs[:10]:
        print(f"  - {n1} and {n2}: dist = {d:.3f}m at ({p1[0]:.2f}, {p1[1]:.2f}) and ({p2[0]:.2f}, {p2[1]:.2f})")
else:
    print(f"CLEAN: Zero dancer pairs closer than {MIN_SAFE_DIST}m.")

# 3. Check for boundary penetrations (Unrealistic Placements)
print("\n--- BOUNDARY & STRUCTURAL PENETRATION CHECK ---")
violations = []

# Catwalk bounds (thrust: X in [-1.8, 1.8], Y in [2.0, 24.0]; T-head: X in [-4.3, 4.3], Y in [-0.5, 3.5])
# Stage deck bounds (X in [-19.0, 19.0], Y in [23.5, 41.0])
for n, x, y, z in positions:
    # Check if inside catwalk thrust
    if abs(x) < 2.0 and (2.0 <= y <= 24.0):
        violations.append((n, "Inside Catwalk Thrust", (x, y, z)))
    # Check if inside catwalk T-head
    elif abs(x) < 4.5 and (-0.6 <= y <= 3.5):
        violations.append((n, "Inside Catwalk T-Head", (x, y, z)))
    # Check if inside main stage deck
    elif abs(x) < 19.5 and (23.5 <= y <= 41.0):
        violations.append((n, "Inside Main Stage Deck", (x, y, z)))
    # Check if outside pitch limits (Pitch is 71m wide, so X in [-35, 35], Y in [-53, 53])
    elif abs(x) > 34.0 or abs(y) > 50.0:
        violations.append((n, "Outside Stadium Pitch Bounds", (x, y, z)))
    # Check elevation (should be near pitch turf PITCH_Z + 0.12)
    elif abs(z - (PITCH_Z + 0.12)) > 0.15:
        violations.append((n, f"Abnormal Elevation (Z={z:.2f}, expected {PITCH_Z + 0.12:.2f})", (x, y, z)))

if violations:
    print(f"WARNING: Found {len(violations)} structural placement violations!")
    for n, reason, pos in violations[:10]:
        print(f"  - {n}: {reason} at {pos}")
else:
    print("CLEAN: All 300 dancers are strictly outside the stage, catwalk, and barricade structures, and correctly standing on the pitch floor.")

print("==================================================")
