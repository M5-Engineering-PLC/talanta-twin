"""Stage 02: CPU Cycles render of one critic camera from blender/out/talanta_site.blend (build_site_detail.py).

Sun state comes from app/cameras/manifest.json (date, EAT time) via a NOAA solar position.
Run from the repo root:
  ~/.venvs/bpy/bin/python blender/render_cycles.py <out_dir> <camera> [morning|golden|neutral|night|overcast] [preview|check|look|hero]
  preview = 8 samples at a quarter of full size, for framing checks only; check = 32 samples at look size
"""
import json, math, sys, time, datetime as dt
from pathlib import Path
import bpy
from mathutils import Euler, Vector

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "blender/scripts"))
from cameras import load_cameras, apply_render_settings
sys.path.insert(0, str(ROOT / "blender"))
import sky_hdri

out, cid = ROOT / sys.argv[-4], sys.argv[-3]
sun_key, quality = sys.argv[-2], sys.argv[-1]
out.mkdir(parents=True, exist_ok=True)


def sun_position(date, hhmm_eat, lat, lon):
    """NOAA solar position; returns (elevation_deg, azimuth_deg from north, clockwise)."""
    y, m, d = map(int, date.split("-")); hh, mm = map(int, hhmm_eat.split(":"))
    t = dt.datetime(y, m, d, hh, mm) - dt.timedelta(hours=3)
    jd = t.toordinal() + 1721424.5 + (t.hour + t.minute / 60) / 24
    jc = (jd - 2451545) / 36525
    L0 = (280.46646 + jc * (36000.76983 + jc * 0.0003032)) % 360
    M = 357.52911 + jc * (35999.05029 - 0.0001537 * jc)
    e = 0.016708634 - jc * (0.000042037 + 0.0000001267 * jc)
    C = math.sin(math.radians(M)) * (1.914602 - jc * (0.004817 + 0.000014 * jc)) + math.sin(math.radians(2 * M)) * (0.019993 - 0.000101 * jc) + math.sin(math.radians(3 * M)) * 0.000289
    lam = L0 + C - 0.00569 - 0.00478 * math.sin(math.radians(125.04 - 1934.136 * jc))
    eps = 23 + (26 + (21.448 - jc * (46.815 + jc * (0.00059 - jc * 0.001813))) / 60) / 60 + 0.00256 * math.cos(math.radians(125.04 - 1934.136 * jc))
    dec = math.degrees(math.asin(math.sin(math.radians(eps)) * math.sin(math.radians(lam))))
    yv = math.tan(math.radians(eps / 2)) ** 2
    eqt = 4 * math.degrees(yv * math.sin(2 * math.radians(L0)) - 2 * e * math.sin(math.radians(M)) + 4 * e * yv * math.sin(math.radians(M)) * math.cos(2 * math.radians(L0)) - 0.5 * yv * yv * math.sin(4 * math.radians(L0)) - 1.25 * e * e * math.sin(2 * math.radians(M)))
    tst = (t.hour * 60 + t.minute + eqt + 4 * lon) % 1440
    ha = tst / 4 - 180
    zen = math.degrees(math.acos(math.sin(math.radians(lat)) * math.sin(math.radians(dec)) + math.cos(math.radians(lat)) * math.cos(math.radians(dec)) * math.cos(math.radians(ha))))
    az = (math.degrees(math.acos(((math.sin(math.radians(lat)) * math.cos(math.radians(zen))) - math.sin(math.radians(dec))) / (math.cos(math.radians(lat)) * math.sin(math.radians(zen))))) + 180) % 360 if ha > 0 else (540 - math.degrees(math.acos(((math.sin(math.radians(lat)) * math.cos(math.radians(zen))) - math.sin(math.radians(dec))) / (math.cos(math.radians(lat)) * math.sin(math.radians(zen)))))) % 360
    return 90 - zen, az


bpy.ops.wm.open_mainfile(filepath=__import__("os").environ.get("TALANTA_SITE_BLEND", str(ROOT / "blender/out/talanta_site.blend")))  # a frozen copy per step
s = bpy.context.scene
# surface state (replica plan pass C): TALANTA_STATE=asbuilt for the drone and facade frames, finished (default) for
# the landing views; blender/scene_state.py
_state = __import__("os").environ.get("TALANTA_STATE")
if _state:
    sys.path.insert(0, str(ROOT / "blender")); import scene_state; scene_state.set_state(s, _state)
m, cams = load_cameras(s, ROOT / "app/cameras/manifest.json", extra=ROOT / "blender/data/interior_cameras.json")
apply_render_settings(s, m, look_check=(quality not in ("hero", "hero_artistic")))
s.camera = cams[cid]
# Objects a camera stands inside or right behind (blender/data/camera_hides.json, with a reason)
for name in json.loads((ROOT / "blender/data/camera_hides.json").read_text()).get(cid, {}).get("hide", []):
    if name in bpy.data.objects: bpy.data.objects[name].hide_render = True
# golden-hour presets (sky_hdri.py: HDRI sky + matched sun lamp) take precedence over the manifest suns
st = sky_hdri.PRESETS.get(sun_key) or m["suns"][sun_key]
lon, lat = m["frame"]["origin_lonlat"]
el, az = sun_position(st["date"], st["time_eat"], lat, lon)
sun = bpy.data.objects["sun"]
# Blender sun points down -Z; aim it from azimuth az (from north, clockwise) at elevation el.
sun.rotation_euler = Euler((math.radians(90 - el), 0, math.radians(180 - az)), "XYZ")
golden = el < 15 and st["kind"] != "overcast"
overcast = st["kind"] == "overcast"
sun.data.energy = 4.5 if not golden else 3.5
morning = st["kind"].startswith("morning")
sun.data.color = (1.0, 0.86, 0.70) if morning else (1.0, 0.76, 0.52) if golden else (1.0, 0.97, 0.92)
if morning: sun.data.energy = 4.0
s.view_settings.exposure = m["exposure"]["exposure_ev"] + m["exposure"].get("exposure_ev_by_sun", {}).get(sun_key, 0.0)
if golden: s.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.25
sky = s.world.node_tree.nodes["sky"]
sky.sun_elevation = math.radians(max(el, 0.5)); sky.sun_rotation = math.radians(90 - az)
bg = s.world.node_tree.nodes["Background"]
if overcast:  # cloud deck: weak diffuse sun, brighter flat sky, denser haze
    sun.data.energy = 0.6; sun.data.angle = math.radians(25); sky.sun_elevation = math.radians(60)
    bg.inputs["Strength"].default_value = 0.9
    bpy.data.materials["haze"].node_tree.nodes["haze"].inputs["Density"].default_value = 6e-5
night = st["kind"].startswith("night")
if night:  # sun below the horizon: no sun lamp, a faint sky; night fixtures on (build_site_detail.py, Visualization)
    sun.data.energy = 0.0; bg.inputs["Strength"].default_value = 1.0
    for lk in list(bg.inputs["Color"].links): s.world.node_tree.links.remove(lk)
    bg.inputs["Color"].default_value = (0.0015, 0.002, 0.0045, 1)  # moonless sky; no sunset band
if night or st.get("fixtures"):  # night fixtures on; a preset may switch them on at dusk (sky_hdri "fixtures")
    for mt in bpy.data.materials:
        if not mt.node_tree: continue
        for nd in mt.node_tree.nodes:
            if nd.label.startswith("night:") or (not night and nd.label.startswith("dusk:")):  # dusk: only before night
                v = float(nd.label.split(":")[1])
                if nd.type == "BSDF_PRINCIPLED": nd.inputs["Emission Strength"].default_value = v
                elif nd.type == "EMISSION": nd.inputs["Strength"].default_value = v
    for ob in bpy.data.objects:
        if ob.type == "LIGHT" and "night_energy" in ob: ob.data.energy = ob["night_energy"]
        if not night and ob.type == "LIGHT" and "dusk_energy" in ob: ob.data.energy = ob["dusk_energy"]  # dusk (pass E)
sky_log = None
if sun_key in sky_hdri.PRESETS:
    sky_log = sky_hdri.apply(s, sun_key, el, az, sun)
    s.view_settings.exposure = sky_hdri.PRESETS[sun_key].get("exposure_ev", s.view_settings.exposure)
    bpy.context.view_layer.update()  # camera matrices are stale until the view layer is evaluated
    fwd = s.camera.matrix_world.to_3x3() @ Vector((0, 0, -1))
    s["talanta_haze_rgb"] = sky_log["haze_rgb"] = sky_hdri.horizon_rgb(s, math.degrees(math.atan2(fwd.y, fwd.x)))
s.view_settings.exposure += s.camera.get("exposure_ev", 0.0)
c = s.cycles
c.device = "CPU"; c.samples = m["cycles"]["hero" if quality in ("hero", "hero_artistic") else "look_check"]["samples"]
if quality == "preview": c.samples = 8; s.render.resolution_percentage = 25
if quality == "check": c.samples = 32
c.use_adaptive_sampling = True; c.use_denoising = True; c.denoiser = "OPENIMAGEDENOISE"
c.max_bounces = 6; c.volume_bounces = 0; c.volume_step_rate = 4.0
s.render.engine = "CYCLES"; s.render.film_transparent = False
c.seed = cams[cid]["seed"]
s.render.image_settings.file_format = "PNG"
s.render.filepath = str(out / f"{cid}_{sun_key}_{quality}.png")
# ---- end of scene setup: blender/web_hero/*.py run this file up to this line for the same sun and sky
artistic = quality == "hero_artistic"  # step H: 4K artistic set (hero_artistic.py); always with the look layer
if artistic:
    import hero_artistic
    art_log = hero_artistic.prepare(s, bool(st.get("fixtures")))
# Opt-in photographic layer. Existing cloud commands retain the original path.
if __import__("os").environ.get("TALANTA_LOOKDEV") == "1" or artistic:
    sys.path.insert(0, str(ROOT / "blender"))
    from lookdev import apply_lookdev
    apply_lookdev(s, "night" if night else "day")
if artistic: hero_artistic.finish(s)
# test hooks (pass A paint tuning): TALANTA_PRE runs a Python file on the set-up scene; TALANTA_BORDER="x0,y0,x1,y1"
# renders only that part of the frame (fractions, top-left origin); TALANTA_SAMPLES overrides the sample count
_env = __import__("os").environ
if _env.get("TALANTA_PRE"): exec(compile(open(_env["TALANTA_PRE"]).read(), _env["TALANTA_PRE"], "exec"), {"bpy": bpy, "s": s, "ROOT": ROOT})
if _env.get("TALANTA_BORDER"):
    bx0, by0, bx1, by1 = map(float, _env["TALANTA_BORDER"].split(","))
    s.render.use_border = True; s.render.use_crop_to_border = False
    s.render.border_min_x, s.render.border_max_x, s.render.border_min_y, s.render.border_max_y = bx0, bx1, 1 - by1, 1 - by0
if _env.get("TALANTA_SAMPLES"): c.samples = int(_env["TALANTA_SAMPLES"])
t0 = time.time(); bpy.ops.render.render(write_still=True); sec = time.time() - t0
# display grade of a preset (sky_hdri "display_grade", e.g. the drone camera look of overcast_drone): applied to the
# saved 8-bit image, so the frame match holds in display values; the scene, paint and grade stay as they are
_dg = (sky_hdri.PRESETS.get(sun_key) or {}).get("display_grade")
if _dg:
    import numpy as np
    _im = bpy.data.images.load(s.render.filepath)
    _px = np.empty(len(_im.pixels), np.float32); _im.pixels.foreach_get(_px); _px = _px.reshape(-1, 4)
    _c = _px[:, :3]; _lum = (_c @ np.array([0.2126, 0.7152, 0.0722], np.float32))[:, None]
    _c = _dg["gain"] * (_lum + _dg["saturation"] * (_c - _lum)) * (1 - _dg["veil"]) + _dg["veil"] * np.array(_dg["veil_rgb"], np.float32)
    _px[:, :3] = np.clip(_c, 0, 1); _im.pixels.foreach_set(_px.ravel()); _im.save(); bpy.data.images.remove(_im)
rec = {"camera": cid, "sky": sky_log, "sun": st, "sun_elevation_deg": round(el, 2), "sun_azimuth_deg": round(az, 2), "quality": quality,
       "resolution": [s.render.resolution_x * s.render.resolution_percentage // 100, s.render.resolution_y * s.render.resolution_percentage // 100],
       "samples": c.samples, "seconds": round(sec, 1)}
if _dg: rec["display_grade"] = _dg
if artistic: rec["hero_artistic"] = art_log; rec["labelled_copy"] = hero_artistic.stamp(s.render.filepath).name
# image direction of cast shadows: a 100 m ground step away from the sun at the pitch centre (0 = right, ccw)
from bpy_extras.object_utils import world_to_camera_view
g0 = Vector((0, 0, m["frame"]["site_pad_y"])); g1 = g0 + 100 * Vector((-math.sin(math.radians(az)), -math.cos(math.radians(az)), 0))
p0, p1 = (world_to_camera_view(s, s.camera, g) for g in (g0, g1))
rec["shadow_image_deg"] = round(math.degrees(math.atan2((p1.y - p0.y) * s.render.resolution_y, (p1.x - p0.x) * s.render.resolution_x)), 1)
rec["state"] = s.get("talanta_state", "finished")
print(json.dumps(rec))
log = out / "render_log.jsonl"
with open(log, "a") as f: f.write(json.dumps(rec) + "\n")
