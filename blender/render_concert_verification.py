import bpy
import shutil
from pathlib import Path

print("==================================================")
print("  RENDERING CONCERT DIGITAL TWIN BEAUTY FRAMES   ")
print("==================================================")

blend_path = "E:/M5/grao/blender/out/talanta_stadium_concert_master.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

scene = bpy.context.scene
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.engine = 'BLENDER_EEVEE'
if hasattr(scene, 'eevee'):
    scene.eevee.taa_render_samples = 32

out_dir = Path("E:/M5/grao/blender/out")
artifact_dir = Path("C:/Users/hp/.gemini/antigravity/brain/afadf3b7-ab21-44d5-9df2-c128a411b3d0")

renders = [
    (85,  "concert_drone_frontman_hero.png", "Hero Drone close-up on MC frontman & glowing smartphones"),
    (25,  "concert_crowd_spacing_verify.png", "Low-angle Golden Circle crowd pass-through showing spacing & human skin"),
    (150, "concert_stadium_epic_reveal.png",  "High crane reveal of full 60k Talanta Stadium arena & lasers"),
]

for frame_num, fname, desc in renders:
    scene.frame_set(frame_num)
    render_file = out_dir / fname
    scene.render.filepath = str(render_file)
    print(f"\nRendering Frame {frame_num} ({desc})...")
    bpy.ops.render.render(write_still=True)
    print(f" Saved: {render_file}")
    
    # Copy to artifact dir for display
    art_file = artifact_dir / fname
    shutil.copy2(str(render_file), str(art_file))
    print(f" Copied to artifact: {art_file}")

print("\n=== ALL BEAUTY VERIFICATION RENDERS COMPLETED ===")
