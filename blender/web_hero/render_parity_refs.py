"""P1 cloud (Cycles parity, 2026-10-25): the reference images for the app colour match, 1920 x 1080, no haze.

Run from the repo root (TALANTA_SITE_BLEND=$PWD/blender/out/frozen_FK.blend), one image per call:
  blender -b --factory-startup --python-exit-code 1 --python blender/web_hero/render_parity_refs.py -- <out_dir> <L06|L07> <bake|still>
  bake   ref_bake_<view>.png: the web export state, lit as the 07:30 bake (common.setup_morning: morning_golden, the
         finished state with the look layer's materials), only what export_web.py exports (no people, no trace_trees,
         no context_l07_visualization, no night or dusk fixtures, no brand marks), with the full look: the view
         transform and look and the view's exposure from blender/web_hero/look_v2.json (the exposure the app uses at
         that view) and the look layer's compositor without its haze;
  still  ref_still_<view>.png: the hero_artistic_04 set-up of that view at the still time (render_cycles.py
         hero_artistic: L07 daylight_artistic 10:30, L06 sunset_artistic 18:05 with fixtures, people and cars), at
         1920 x 1080, without haze.
"No haze": the haze volume and its pass layer are left out and the compositor's distance haze (mist haze, aerial haze
and band haze) is set to zero; glare, streaks, vignette, grain and dispersion stay. Internal reference only
(orphan branch assets/web_hero_v2_bake, parity/). People, cars and lights in ref_still are Visualization.
"""
import json, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARGV = sys.argv[sys.argv.index("--") + 1:]
OUT, VIEW, KIND = ROOT / ARGV[0], ARGV[1], ARGV[2]
OUT.mkdir(parents=True, exist_ok=True)
LOOK = json.loads((ROOT / "blender/web_hero/look_v2.json").read_text())
sys.path.insert(0, str(ROOT / "blender")); sys.path.insert(0, str(ROOT / "blender/web_hero"))
import lookdev
NO_HAZE = {"haze_day": 0.0, "haze_night": 0.0, "aerial_haze_max": 0.0}


def zero_haze():
    lookdev.STRENGTHS.update(NO_HAZE)
    lookdev.STRENGTHS["aerial_band_haze"] = {k: 0.0 for k in lookdev.STRENGTHS["aerial_band_haze"]}


def drop_haze_layer(s):
    """hero_artistic.finish() turns the haze volume back on and reads the data passes from a layer without it; here the
    volume stays off and the passes come from the main layer again."""
    hz = bpy.data.objects.get("haze_volume")
    if hz is not None: hz.hide_render = True
    pl = s.view_layers.get("passes_no_haze")
    tree = s.compositing_node_group if hasattr(s, "compositing_node_group") else s.node_tree
    if pl is not None and tree is not None:
        main_rl = next(n for n in tree.nodes if n.type == "R_LAYERS" and n.layer == s.view_layers[0].name)
        for n in [n for n in tree.nodes if n.type == "R_LAYERS" and n.layer == pl.name]:
            for o in n.outputs:
                for lk in list(o.links): tree.links.new(main_rl.outputs[o.name], lk.to_socket)
            tree.nodes.remove(n)
        s.view_layers.remove(pl)


import hero_artistic
zero_haze()
lookdev.STRENGTHS["glare"] = hero_artistic.SET["glare_mix"]; lookdev.STRENGTHS["glare_threshold"] = hero_artistic.SET["glare_threshold"]
hidden = []
if KIND == "still":
    _far = hero_artistic.set_far_values
    def _far_no_haze(strengths, dusk):  # prepare() sets the far band haze; keep it at zero here
        r = _far(strengths, dusk); zero_haze(); return r
    hero_artistic.set_far_values = _far_no_haze
    src = (ROOT / "blender/render_cycles.py").read_text()
    head = src.split("t0 = time.time(); bpy.ops.render.render(write_still=True)")[0]
    sys.argv = [sys.argv[0], str(OUT.relative_to(ROOT)), VIEW, LOOK["views"][VIEW]["preset"], "hero_artistic"]
    g = {"__file__": str(ROOT / "blender/render_cycles.py"), "__name__": "render_cycles_setup"}
    exec(compile(head, "render_cycles.py (setup)", "exec"), g)
    import bpy
    s = bpy.context.scene
else:
    from common import setup_morning
    g = setup_morning()
    import bpy
    s = bpy.context.scene
    s.camera = g["cams"][VIEW]
    for name in json.loads((ROOT / "blender/data/camera_hides.json").read_text()).get(VIEW, {}).get("hide", []):
        if name in bpy.data.objects: bpy.data.objects[name].hide_render = True
    # the web export state: what export_web.py leaves out does not appear (people, the trace trees, the L07 context
    # Visualization, fixtures and town lights of the dusk and night stills)
    for cn in ("people_figures_visualization", "people_protos", "trace_trees", "context_l07_visualization", "night_lights"):
        c_ = bpy.data.collections.get(cn)
        for o in (c_.all_objects if c_ else []):
            if not o.hide_render: o.hide_render = True; hidden.append(o.name)
    for o in bpy.data.objects:
        if not o.hide_render and (o.name.startswith(("dusk_", "bg_town_lights")) or (o.type == "LIGHT" and o.data.type != "SUN")):
            o.hide_render = True; hidden.append(o.name)
    vs = s.view_settings
    vs.view_transform, vs.look, vs.exposure = LOOK["view_transform"], LOOK["views"][VIEW]["look"], LOOK["views"][VIEW]["exposure_ev"]
    s.render.use_compositing = True
    c = s.cycles; c.samples = hero_artistic.SET["samples"]; c.adaptive_threshold = hero_artistic.SET["adaptive_threshold"]
    c.use_adaptive_sampling = True; c.use_denoising = True; c.denoiser = "OPENIMAGEDENOISE"
    hero_artistic.finish(s)  # the stills' streak glare
drop_haze_layer(s)
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 1920, 1080, 100
s.render.image_settings.file_format = "PNG"; s.render.image_settings.color_mode = "RGB"; s.render.image_settings.color_depth = "8"
if "dry" in ARGV: s.render.resolution_percentage = 20; s.cycles.samples = 8  # set-up check only
s.render.filepath = str(OUT / f"ref_{KIND}_{VIEW}.png")
t0 = time.time(); bpy.ops.render.render(write_still=True); sec = time.time() - t0
vs = s.view_settings
rec = {"file": Path(s.render.filepath).name, "view": VIEW, "kind": KIND, "seconds": round(sec, 1),
       "time_eat": g["st"]["time_eat"], "date": g["st"]["date"], "light": g.get("sun_key"),
       "view_transform": vs.view_transform, "look": vs.look, "exposure_ev": round(vs.exposure, 4),
       "samples": s.cycles.samples, "resolution": [1920, 1080], "haze": "none (volume off, compositor haze 0)",
       "compositor": bool(s.render.use_compositing), "camera": s.camera.name, "hidden_for_export_state": len(hidden),
       "claim": "Internal reference only. ref_still: people, vehicles and lighting are illustrative (Visualization)."}
with open(OUT / "parity_log.jsonl", "a") as f: f.write(json.dumps(rec) + "\n")
print("parity ref", json.dumps(rec), flush=True)
