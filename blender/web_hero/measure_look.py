"""P1 cloud (Cycles parity, 2026-10-25): the manifest "look" block, measured in Blender.

Run from the repo root once per still view (TALANTA_SITE_BLEND=$PWD/blender/out/frozen_FK.blend):
  blender -b --factory-startup --python-exit-code 1 --python blender/web_hero/measure_look.py -- L07
  blender -b --factory-startup --python-exit-code 1 --python blender/web_hero/measure_look.py -- L06
Each run sets up the hero_artistic_04 still of that view (render_cycles.py up to its render call, as
blender/scroll_test/render_scroll_frames.py does) and merges into blender/web_hero/look_v2.json:
  view_transform, look  the scene's view transform and look (lookdev.py);
  views.<view>          exposure_ev (preset plus camera), the still time, preset, look;
  curve                 33 display-encoded samples (sRGB, 0..1) of the view transform and look on a scene-linear grey
                        ramp 0.18 x 2^EV, EV -10 to +6.5, exposure 0 (the app applies exposure first). agx_base is the
                        same ramp with no look, for comparison with three.js AgXToneMapping;
  compositor            the colour values of the look layer (lookdev.py STRENGTHS after hero_artistic.prepare).
post_glb.mjs copies the block into the bundle manifest. Measurement only: nothing is rendered.
"""
import json, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VIEW = sys.argv[sys.argv.index("--") + 1]
PRESET = {"L07": "daylight_artistic", "L06": "sunset_artistic"}[VIEW]
EV_MIN, EV_MAX, N = -10.0, 6.5, 33
OUT = ROOT / "blender/web_hero/look_v2.json"

src = (ROOT / "blender/render_cycles.py").read_text()
head = src.split("t0 = time.time(); bpy.ops.render.render(write_still=True)")[0]
tmp = Path(tempfile.mkdtemp())
sys.argv = [sys.argv[0], str(tmp), VIEW, PRESET, "hero_artistic"]
g = {"__file__": str(ROOT / "blender/render_cycles.py"), "__name__": "render_cycles_setup"}
exec(compile(head, "render_cycles.py (setup)", "exec"), g)

import bpy
import numpy as np
from PIL import Image
import lookdev, hero_artistic, sky_hdri

s = bpy.context.scene
vs = s.view_settings
exposure, look = float(vs.exposure), vs.look


def ramp_8bit(look_name):
    """Cross-check: the ramp through Blender's own save_render (8-bit read-back), exposure 0, gamma 1."""
    saved = (vs.exposure, vs.gamma, vs.look, vs.use_curve_mapping)
    vs.exposure, vs.gamma, vs.look, vs.use_curve_mapping = 0.0, 1.0, look_name, False
    im = bpy.data.images.new("look_ramp", N, 1, float_buffer=True, alpha=False)
    px = np.ones((1, N, 4), np.float32); px[0, :, :3] = LIN[:, None]; im.pixels.foreach_set(px.ravel())
    st = s.render.image_settings
    keep = (st.file_format, st.color_depth, st.color_mode)
    st.file_format, st.color_mode, st.color_depth = "PNG", "RGB", "8"
    f = tmp / f"ramp_{look_name.replace(' ', '_')}.png"; im.save_render(str(f), scene=s)
    st.file_format, st.color_depth, st.color_mode = keep
    bpy.data.images.remove(im)
    vs.exposure, vs.gamma, vs.look, vs.use_curve_mapping = saved
    return np.asarray(Image.open(f).convert("RGB")).reshape(-1, 3)[:N].astype(np.float64) / 255.0


def ramp(look_name):
    """Display values (float) of the ramp through Blender's OCIO config: scene linear -> the scene's display and view
    transform, with look_name ("None": no look). Returns (grey samples, rgb samples, max difference to ramp_8bit)."""
    import PyOpenColorIO as OCIO
    cfg = OCIO.Config.CreateFromFile(str(Path(bpy.utils.resource_path("LOCAL")) / "datafiles/colormanagement/config.ocio"))
    dvt = OCIO.DisplayViewTransform(src=OCIO.ROLE_SCENE_LINEAR, display=s.display_settings.display_device, view=vs.view_transform)
    pipe = OCIO.LegacyViewingPipeline(); pipe.setDisplayViewTransform(dvt)
    if look_name != "None": pipe.setLooksOverrideEnabled(True); pipe.setLooksOverride(look_name)
    cpu = pipe.getProcessor(cfg).getDefaultCPUProcessor()
    out = []
    for v in LIN:
        out.append(list(cpu.applyRGB([float(v)] * 3)))
    out = np.clip(np.array(out), 0.0, 1.0)
    diff = float(np.abs(out - ramp_8bit(look_name)).max())
    return [round(float(v), 5) for v in out[:, 1]], [[round(float(c), 5) for c in r] for r in out], round(diff, 5)


LIN = 0.18 * 2.0 ** np.linspace(EV_MIN, EV_MAX, N)
samples, rgb, check = ramp(look)
base, _, check_base = ramp("None")
print("ocio vs save_render (8-bit) max difference", check, check_base, flush=True)
S = lookdev.STRENGTHS
block = json.loads(OUT.read_text()) if OUT.exists() else {}
views = block.get("views", {})
# the app reads one curve; the first view measured sets it, and a later view with another look carries its own curve
if block.get("look") == look or (VIEW == "L07" and not views): block.pop("look", None)
views[VIEW] = {"exposure_ev": round(exposure, 4), "time": sky_hdri.PRESETS[PRESET]["time_eat"],
               "date": sky_hdri.PRESETS[PRESET]["date"], "preset": PRESET, "look": look}
if block.get("look") not in (None, look):
    views[VIEW]["curve"] = {"ev_min": EV_MIN, "ev_max": EV_MAX, "samples": samples}
else:
    block.update(view_transform=vs.view_transform, look=look,
                 curve={"ev_min": EV_MIN, "ev_max": EV_MAX, "input": "scene-linear grey 0.18 x 2^EV, exposure 0",
                        "output": "display-encoded value (the scene display device), 0..1, float, through Blender's OCIO config (PyOpenColorIO)",
                        "check": f"max difference to Blender save_render 8-bit: {check} (look), {check_base} (no look)",
                        "samples": samples, "samples_rgb": rgb, "agx_base_samples": base})
block["views"] = views
block["compositor"] = {
    "contrast": 1.0,  # the contrast of the stills is the look itself ("AgX - High Contrast"), already in the curve
    "saturation": S["grade_saturation"], "warmth": list(S["grade_warm"]),
    "warmth_rise": list(S["grade_warm_rise"]), "warmth_fall": list(S["grade_warm_fall"]),
    "grain": S["grain"], "glare": S["glare"], "glare_threshold": S["glare_threshold"],
    "streak_glare": hero_artistic.SET["streak_mix"], "streak_threshold": 4.0,
    "vignette": S["vignette"], "dispersion": S["dispersion"],
    "order": "saturation and warm gain on scene-linear before the view transform (warmth fades in over display-equivalent "
             "luminance warmth_rise and out over warmth_fall); fog glow glare (glare, glare_threshold) and streaks; "
             "lens dispersion; vignette and grain last",
    "not_in_web": "volumetric haze and the mist-pass aerial haze of the stills (the references are rendered without haze)",
}
block["source"] = "blender/web_hero/measure_look.py (lookdev.py STRENGTHS after hero_artistic.prepare, render_cycles.py presets)"
OUT.write_text(json.dumps(block, indent=1) + "\n")
print("look", VIEW, json.dumps({"exposure_ev": exposure, "look": look, "transform": vs.view_transform, "ev_-0.2": samples[19]}))
