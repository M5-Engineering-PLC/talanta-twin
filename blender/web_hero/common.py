"""Shared setup for the web hero track (bake, panorama, export).

The web app shows baked Blender results. Every step here loads blender/out/talanta_site.blend with the
exact C06 morning sun and sky that blender/render_cycles.py uses (2026-01-15, 07:35 EAT), by running
render_cycles.py up to its "end of scene setup" line. Internal build step; no frames are used as textures.
"""
import json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "blender/out/web_hero"
MAPS = OUT / "maps"
MARK = "# ---- end of scene setup"


def setup_morning(out_dir="blender/out/web_hero/_unused"):
    """Open talanta_site.blend and set the 07:35 morning sun and sky. Returns the render_cycles globals."""
    src = (ROOT / "blender/render_cycles.py").read_text()
    head = src.split(MARK)[0]
    argv = sys.argv
    sys.argv = [argv[0], out_dir, "C06", "morning", "check"]
    g = {"__file__": str(ROOT / "blender/render_cycles.py"), "__name__": "render_cycles_setup"}
    try:
        exec(compile(head, "render_cycles.py (setup)", "exec"), g)
    finally:
        sys.argv = argv
    import bpy
    # Volume haze is a camera effect, not surface light; keep it out of the bakes and the panorama.
    if "haze_volume" in bpy.data.objects:
        bpy.data.objects["haze_volume"].hide_render = True
    return g


def sun_vector_app(el_deg, az_deg):
    """Unit vector towards the sun in the app frame (x east, y up, z south)."""
    el, az = math.radians(el_deg), math.radians(az_deg)
    return [round(math.sin(az) * math.cos(el), 5), round(math.sin(el), 5), round(-math.cos(az) * math.cos(el), 5)]


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1) + "\n")
