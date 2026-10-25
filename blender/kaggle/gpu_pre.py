"""TALANTA_PRE hook for the Kaggle GPU render test (2026-10-25).

render_cycles.py runs this file on the set-up scene, after it sets the device to CPU and before the render.
It turns on every OptiX GPU, or every CUDA GPU when OptiX is not available, and sets the scene to GPU.
The globals bpy and s (the scene) come from render_cycles.py.
"""
prefs = bpy.context.preferences.addons["cycles"].preferences
chosen = None
for kind in ("OPTIX", "CUDA"):
    try:
        prefs.compute_device_type = kind
    except TypeError:
        continue
    prefs.get_devices()
    if any(d.type == kind for d in prefs.devices):
        chosen = kind
        break
if chosen is None:
    raise SystemExit("gpu_pre.py: no OptiX or CUDA device found")
for d in prefs.devices:
    d.use = d.type == chosen
s.cycles.device = "GPU"
print("gpu_pre.py:", chosen, [d.name for d in prefs.devices if d.use])
