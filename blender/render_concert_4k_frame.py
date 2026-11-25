"""Render the figure-facing-camera 4K look test from the textured lead checkpoint.

blender -b concert-textured-lead.blend --python-exit-code 1 --python
blender/render_concert_4k_frame.py -- OUTPUT.png
"""
import sys
from pathlib import Path

import bpy

output = Path(sys.argv[sys.argv.index('--') + 1]).resolve()
scene = bpy.context.scene
scene.frame_set(68)
bpy.data.objects['Textured lead anchor'].rotation_euler.z = 0
scene.render.resolution_x = 3840
scene.render.resolution_y = 2160
scene.render.resolution_percentage = 100
scene.render.fps = 24
scene.cycles.samples = 64
scene.cycles.use_denoising = True
scene.cycles.denoiser = 'OPENIMAGEDENOISE'
try:
    preferences = bpy.context.preferences.addons['cycles'].preferences
    preferences.compute_device_type = 'METAL'
    preferences.refresh_devices()
    metal_devices = [device for device in preferences.devices if device.type == 'METAL']
    if metal_devices:
        for device in preferences.devices:
            device.use = device.type == 'METAL'
        scene.cycles.device = 'GPU'
        print('Cycles Metal: ' + ', '.join(device.name for device in metal_devices), flush=True)
except (TypeError, RuntimeError) as error:
    print(f'Cycles Metal unavailable: {error}', flush=True)
scene.render.filepath = str(output)
print(f'Rendering {scene.render.resolution_x} × {scene.render.resolution_y} @ {scene.cycles.samples} samples on {scene.cycles.device}', flush=True)
bpy.ops.render.render(write_still=True)
