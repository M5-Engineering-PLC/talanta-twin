"""Golden-hour light presets: a CC0 HDRI sky (blender/assets/hdri, CREDITS.md) plus the physical sun lamp.

One preset drives the stills (render_cycles.py), the bake and the panorama (web_hero/common.py) and the export
manifest. The HDRI is rotated about the vertical so its sun sits at the scene sun azimuth (NOAA position for the
preset date and time). Its sun disc is clipped out and given back to the sun lamp with the same colour and
irradiance, so shadows stay sharp and there is only one sun. The HDRI sun elevation is the photographer's, not
ours; only the azimuth is matched (both are logged). Artistic light: label renders "Visualization".
"""
import json, math
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "blender/data/hdri_sun.json"

PRESETS = {
    # Munene's decision (plan_concept_match_2026-10-17.md): morning golden hour for the bake, web twin and C19
    "morning_golden": {"date": "2026-01-15", "time_eat": "07:30", "kind": "morning golden",
                       "hdri": "blender/assets/hdri/kloppenheim_06_puresky_4k.hdr", "sky_strength": 1.0,
                       "sun_kelvin": 4300, "sun_to_sky": 5.0, "exposure_ev": -1.0},
    # evening golden hour for the C20 still only
    "evening_golden": {"date": "2026-01-15", "time_eat": "17:30", "kind": "evening golden",
                       "hdri": "blender/assets/hdri/wasteland_clouds_puresky_4k.hdr", "sky_strength": 1.0,
                       "sun_kelvin": 3800, "sun_to_sky": 5.0, "exposure_ev": -1.7},
    # landing stills L06 and L07 (Munene, 2026-10-19: mirror landing mockups 06 "Sunset" and 07 "Daylight"). At 18:05 the
    # sun stands about 8 deg up, inside the top of the L06 frame as in the mockup; site lamps and facade lights are on.
    "sunset_landing": {"date": "2026-01-15", "time_eat": "18:05", "kind": "evening golden",
                       "hdri": "blender/assets/hdri/wasteland_clouds_puresky_4k.hdr", "sky_strength": 1.0,
                       "sun_kelvin": 3300, "sun_to_sky": 5.0, "exposure_ev": -1.4, "fixtures": True},
    "daylight_landing": {"date": "2026-01-15", "time_eat": "10:30", "kind": "daylight",
                         "hdri": "blender/assets/hdri/wasteland_clouds_puresky_4k.hdr", "sky_strength": 1.0,
                         "sun_kelvin": 5600, "sun_to_sky": 5.0, "exposure_ev": -1.2},
}


def blackbody(k):
    """Linear RGB of a blackbody (Tanner Helland fit), normalised to its largest channel."""
    t = k / 100
    r = 255 if t <= 66 else 329.698727446 * (t - 60) ** -0.1332047592
    g = 99.4708025861 * math.log(t) - 161.1195681661 if t <= 66 else 288.1221695283 * (t - 60) ** -0.0755148492
    b = 255 if t >= 66 else 0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307
    lin = [((min(max(c, 0), 255) / 255 + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    return tuple(c / max(lin) for c in lin)


def hdri_sun(rel):
    """Sun of an equirectangular HDRI: direction, clip level, and the clipped excess as irradiance and colour.
    Cached in blender/data/hdri_sun.json (keyed by file name and size)."""
    path = ROOT / rel
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    key = f"{path.name}:{path.stat().st_size}"
    if key in cache: return cache[key]
    im = bpy.data.images.load(str(path), check_existing=True)
    w, h = im.size
    px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px); px = px.reshape(h, w, 4)[..., :3]  # row 0 = bottom
    lum = px @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    r, c = np.unravel_index(int(np.argmax(lum)), lum.shape)
    u, v = (c + 0.5) / w, (r + 0.5) / h
    alpha = -(u - 0.5) * 2 * math.pi            # Cycles: u = -atan2(y, x) / 2pi + 0.5
    elev = (v - 0.5) * math.pi                   #         v = atan2(z, hypot(x, y)) / pi + 0.5
    # clip level: the brightest sky outside 4 degrees of the sun
    vv = (np.arange(h) + 0.5) / h; uu = (np.arange(w) + 0.5) / w
    el_g = ((vv - 0.5) * math.pi)[:, None]; al_g = (-(uu - 0.5) * 2 * math.pi)[None, :]
    d = np.stack([np.cos(el_g) * np.cos(al_g), np.cos(el_g) * np.sin(al_g), np.sin(el_g) * np.ones_like(al_g)], -1)
    s = np.array([math.cos(elev) * math.cos(alpha), math.cos(elev) * math.sin(alpha), math.sin(elev)])
    near = (d @ s) > math.cos(math.radians(4))
    clip = float(np.percentile(lum[~near & (el_g.repeat(w, 1) > 0)], 99.9))
    # excess above the clip, integrated over solid angle, projected on the sun direction (irradiance, W/m2 units)
    dom = (2 * math.pi / w) * (math.pi / h) * np.cos(el_g)
    excess = np.clip(px - clip, 0, None) * near[..., None]
    E = (excess * (dom * np.clip(d @ s, 0, None))[..., None]).sum((0, 1))
    sky = np.minimum(px, clip) * (dom * np.clip(d[..., 2], 0, None))[..., None]
    E_sky = float((sky.sum((0, 1)) @ np.array([0.2126, 0.7152, 0.0722])))
    res = {"file": rel, "size": [w, h], "sun_alpha_deg": round(math.degrees(alpha), 3), "sun_elevation_deg": round(math.degrees(elev), 3),
           "clip": round(clip, 4), "sun_irradiance": round(float(E.max()), 4), "sky_horizontal_irradiance": round(E_sky, 4),
           "sun_color": [round(float(x / E.max()), 4) for x in E]}
    cache[key] = res; CACHE.parent.mkdir(parents=True, exist_ok=True); CACHE.write_text(json.dumps(cache, indent=1) + "\n")
    bpy.data.images.remove(im)
    return res


def apply(scene, preset_key, el, az, sun):
    """Set the world to the preset HDRI rotated to the scene sun (elevation el, azimuth az from north, clockwise),
    and the sun lamp to the clipped HDRI sun. Returns a log dict."""
    p = PRESETS[preset_key]; hs = hdri_sun(p["hdri"])
    w = scene.world; n, l = w.node_tree.nodes, w.node_tree.links
    bg = n["Background"]
    for lk in list(bg.inputs["Color"].links): l.remove(lk)
    tc = n.new("ShaderNodeTexCoord"); mp = n.new("ShaderNodeMapping"); mp.vector_type = "POINT"; mp.name = "hdri_rotation"
    env = n.new("ShaderNodeTexEnvironment"); env.name = "hdri"
    env.image = bpy.data.images.load(str(ROOT / p["hdri"]), check_existing=True)
    alpha_s = math.radians(90 - az)              # scene sun direction angle atan2(y north, x east)
    rot = math.radians(hs["sun_alpha_deg"]) - alpha_s
    mp.inputs["Rotation"].default_value = (0, 0, rot)
    cl = n.new("ShaderNodeVectorMath"); cl.operation = "MINIMUM"; cl.name = "hdri_clip"; cl.inputs[1].default_value = (hs["clip"],) * 3
    l.new(tc.outputs["Generated"], mp.inputs["Vector"]); l.new(mp.outputs["Vector"], env.inputs["Vector"])
    l.new(env.outputs["Color"], cl.inputs[0]); l.new(cl.outputs["Vector"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = p["sky_strength"]
    sun.data.energy = p["sun_to_sky"] * hs["sky_horizontal_irradiance"] * p["sky_strength"]
    sun.data.color = blackbody(p["sun_kelvin"])
    # the scene's procedural clouds and Nishita sky are replaced; the haze box stays (lookdev may hide it)
    return {"preset": preset_key, "hdri": p["hdri"], "rotation_deg": round(math.degrees(rot), 2),
            "hdri_sun_elevation_deg": hs["sun_elevation_deg"], "scene_sun_elevation_deg": round(el, 2),
            "sun_energy": round(sun.data.energy, 3), "sun_kelvin": p["sun_kelvin"], "sun_color": [round(c, 4) for c in sun.data.color]}


def horizon_rgb(scene, view_alpha_deg, half_width_deg=35, elev_deg=(0.5, 4.0)):
    """Mean clipped HDRI radiance just above the horizon around a world view direction (angle from east,
    counter-clockwise): the colour aerial perspective tends to (lookdev.py haze)."""
    n = scene.world.node_tree.nodes; env = n["hdri"]; im = env.image
    rot = n["hdri_rotation"].inputs["Rotation"].default_value[2]
    clip = n["hdri_clip"].inputs[1].default_value[0]
    w, h = im.size
    px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px); px = px.reshape(h, w, 4)[..., :3]
    r0, r1 = (int((0.5 + math.radians(e) / math.pi) * h) for e in elev_deg)
    a = np.radians(view_alpha_deg + np.linspace(-half_width_deg, half_width_deg, 64)) + rot
    cols = (((-a / (2 * math.pi) + 0.5) % 1.0) * w).astype(int)
    band = np.minimum(px[r0:r1 + 1][:, cols], clip)
    return [round(float(c), 4) for c in band.reshape(-1, 3).mean(0) * scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value]
