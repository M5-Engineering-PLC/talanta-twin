"""Shared setup for the web hero track (bake, panorama, export).

The web app shows baked Blender results. Every step here loads blender/out/talanta_site.blend (or TALANTA_SITE_BLEND,
for web_hero_v2 the frozen step_FK scene) in the finished state with the look layer on, and the
approved light of the concept match (Munene and lead, pass 1 review): the morning_golden preset of
blender/sky_hdri.py (2026-01-15, 07:30 EAT, kloppenheim_06 HDRI rotated to the NOAA sun, -1 EV), by running
render_cycles.py up to its "end of scene setup" line with camera C19. Internal build step; no frames are used as textures.
"""
import json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "blender/out/web_hero"
MAPS = OUT / "maps"
# P2 time-of-day bakes (2026-10-26): TALANTA_BAKE_OUT=blender/out/web_hero/lightmaps/<HHMM> puts the maps, stages.json,
# bake_log.json and the baked blend of one set there (same layout as the 07:30 set: maps/ and the two files);
# TALANTA_BAKE_PRESET picks the sky preset of blender/sky_hdri.py (default morning_golden, the 07:30 set).
import os as _os
BAKE_OUT = ROOT / _os.environ["TALANTA_BAKE_OUT"] if _os.environ.get("TALANTA_BAKE_OUT") else OUT
BAKE_PRESET = _os.environ.get("TALANTA_BAKE_PRESET", "morning_golden")
if _os.environ.get("TALANTA_BAKE_OUT"): MAPS = BAKE_OUT / "maps"
MARK = "# ---- end of scene setup"


def setup_morning(out_dir="blender/out/web_hero/_unused", preset="morning_golden"):
    """Open talanta_site.blend and set the approved golden sun and HDRI sky (morning_golden 07:30 by default,
    evening_golden 17:30). Returns the render_cycles globals."""
    src = (ROOT / "blender/render_cycles.py").read_text()
    head = src.split(MARK)[0]
    argv = sys.argv
    sys.argv = [argv[0], out_dir, "C19", preset, "check"]
    g = {"__file__": str(ROOT / "blender/render_cycles.py"), "__name__": "render_cycles_setup"}
    try:
        exec(compile(head, "render_cycles.py (setup)", "exec"), g)
    finally:
        sys.argv = argv
    import bpy
    # Volume haze is a camera effect, not surface light; keep it out of the bakes and the panorama.
    if "haze_volume" in bpy.data.objects:
        bpy.data.objects["haze_volume"].hide_render = True
    # web_hero_v2 (order 2026-10-24, W1.4): the bundle is the finished state with the look layer on. The state switch
    # hides the as-built-only objects; the look layer wraps the materials (dirt, colour variation, edge wear) and sets
    # the sun angle. Its grade (compositor, AgX look) is a camera effect: the compositor stays off and the view settings
    # stay as render_cycles.py set them, so bakes, panoramas and tiles keep the approved morning tone; the app tone-maps.
    s = bpy.context.scene
    sys.path.insert(0, str(ROOT / "blender"))
    import scene_state
    from lookdev import apply_lookdev
    scene_state.set_state(s, "finished")
    vs = s.view_settings; view = (vs.view_transform, vs.look, vs.exposure)
    apply_lookdev(s, "day")
    vs.view_transform, vs.look, vs.exposure = view
    s.render.use_compositing = False
    g["web_state"] = {"state": s["talanta_state"], "lookdev": s["talanta_lookdev"], "blend": str(Path(bpy.data.filepath).resolve().relative_to(ROOT))}
    # Brand marks and other internal-only parts (rubis_station.py) never reach the bake, panorama or export.
    for o in bpy.data.objects:
        if "internal_only" in o.keys(): o.hide_render = True; o.hide_viewport = True
    return g


def sun_vector_app(el_deg, az_deg):
    """Unit vector towards the sun in the app frame (x east, y up, z south)."""
    el, az = math.radians(el_deg), math.radians(az_deg)
    return [round(math.sin(az) * math.cos(el), 5), round(math.sin(el), 5), round(-math.cos(az) * math.cos(el), 5)]


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=1) + "\n")
