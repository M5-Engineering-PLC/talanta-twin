import bpy
import subprocess
import os
from pathlib import Path

scene = bpy.context.scene
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.light = 'STUDIO'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = 'BOTH'

scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.render.resolution_percentage = 100
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 120

frames_dir = Path("E:/M5/grao/blender/out/frames")
frames_dir.mkdir(parents=True, exist_ok=True)

scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(frames_dir / "frame_")

print("Starting 120-frame Workbench animation render to frames...")
bpy.ops.render.render(animation=True)
print("Finished rendering frames!")

mp4_path = "E:/M5/grao/blender/out/talanta_concert_dance_previz.mp4"
ffmpeg_cmd = [
    "C:/Users/hp/scoop/shims/ffmpeg.exe",
    "-y",
    "-framerate", "24",
    "-i", str(frames_dir / "frame_%04d.png"),
    "-c:v", "libx264",
    "-pix_fmt", "yuv420p",
    "-crf", "18",
    mp4_path
]

print("Encoding MP4 via ffmpeg...")
res = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
if res.returncode == 0:
    print(f" SUCCESS! MP4 Video ready at: {mp4_path}")
else:
    print(f" FFMPEG error: {res.stderr}")
