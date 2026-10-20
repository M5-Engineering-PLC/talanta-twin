"""Step B (Munene, 2026-10-19): background like for like with landing mockups 06 and 07, from data, not from images.

Runs on blender/out/talanta_site.blend after build_site_detail.py (and site_layout_ge.py, tree_rules.py):
1. Forest belt (E1): the Sentinel-2 NDVI belt cells of the "trees" scatter (40 m cells with 24 or more trees, as in
   canopy.py) get extra jittered trees, so the belt reads as one canopy, not scattered crowns.
2. Far land (E2): the horizon bands and terrain_far lose the beige cast: their colour is pulled toward a hazy
   green-grey (lookdev.py still hazes each band by distance).
3. City (E4, mockup 07): mid-rise blocks (8 to 20 storeys) north of Ngong Road on free terrain, with grey and red
   roofs (the roof colour mix of engineering/environment_from_drone_2026-10-17.md); more towers at the CBD and Upper
   Hill points of horizon.py and a Kilimani cluster. Positions and heights estimated (Visualization); Open Buildings
   and OSM footprints in the near ring are kept and never overlapped (a block is only placed where the ray hits
   terrain).
4. Town lights (mockup 06 at dusk): small warm lights scattered over the far land, off by day; render_cycles.py
   switches every "night:" node on for night and for presets with fixtures (sunset_landing).
No image cards and no pixels from the mockups (AGENTS.md rule 2).
Run from the repo root: ~/.venvs/bpy/bin/python blender/context/background_b.py
"""
import json, math, os, sys
from pathlib import Path
import numpy as np
import bpy, bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "blender/context"))
CLAIM = "Visualization: background masses and lights estimated (step B); footprints and heights not mapped"
rng = np.random.default_rng(1911)
bpy.ops.wm.open_mainfile(filepath=os.environ.get("TALANTA_SITE_BLEND", str(ROOT / "blender/out/talanta_site.blend")))
scene = bpy.context.scene
col = bpy.data.collections.get("background_b") or bpy.data.collections.new("background_b")
if col.name not in scene.collection.children: scene.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)
report = {}


def srgb(h):
    h = h.lstrip("#"); return tuple(((int(h[i:i + 2], 16) / 255 + 0.055) / 1.055) ** 2.4 for i in (0, 2, 4))


def mat(name, hx, rough=0.85):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]; p.inputs["Base Color"].default_value = (*srgb(hx), 1)
    p.inputs["Roughness"].default_value = rough; m.diffuse_color = (*srgb(hx), 1); m["claim"] = CLAIM
    return m


# ---- 1. forest belt: densify the belt cells of the trees scatter
tr = scene.objects.get("trees")
if tr is not None:
    me = tr.data; n0 = len(me.vertices)
    co = np.empty(n0 * 3, np.float32); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    cell = np.floor(co[:, :2] / 40).astype(int); _, inv, cnt = np.unique(cell, axis=0, return_inverse=True, return_counts=True)
    belt = np.nonzero(cnt[inv.ravel()] >= 24)[0]
    attrs = {a.name: a for a in me.attributes if a.domain == "POINT" and a.name != "position"}
    vals = {}
    for nm, a in attrs.items():
        if a.data_type == "INT": v = np.empty(n0, np.int32); a.data.foreach_get("value", v)
        elif a.data_type == "FLOAT_VECTOR": v = np.empty(n0 * 3, np.float32); a.data.foreach_get("vector", v); v = v.reshape(-1, 3)
        else: continue
        vals[nm] = v
    reps = 2; src = np.repeat(belt, reps)
    new = co[src] + np.c_[rng.uniform(-9, 9, (len(src), 2)), np.zeros(len(src))].astype(np.float32)
    me.vertices.add(len(src)); allco = np.vstack([co, new]); me.vertices.foreach_set("co", allco.ravel())
    for nm, v in vals.items():
        a = me.attributes[nm]; nv = np.concatenate([v, v[src]])
        if nm in ("tscale3", "sc3"): nv[n0:] *= rng.uniform(0.85, 1.15, (len(src), 1)).astype(np.float32)
        if a.data_type == "INT": a.data.foreach_set("value", nv.astype(np.int32).ravel())
        else: a.data.foreach_set("vector", nv.astype(np.float32).ravel())
    me.update(); report["forest_belt"] = {"belt_points": int(len(belt)), "added": int(len(src)), "total": int(n0 + len(src))}

# ---- 2. far land: pull the beige toward a hazy green-grey
GREEN_GREY = (0.085, 0.125, 0.065, 1)  # pass 3: greener, so the far land reads as canopy (mockup 06)
done = []
for o in scene.objects:
    if o.type != "MESH" or not (o.name.startswith(("terrain_horizon", "horizon_band", "terrain_far"))): continue
    for m in o.data.materials:
        if not m or not m.node_tree or m.get("step_b_tint") or m.name in done: continue
        p = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
        if p is None or not p.inputs["Base Color"].links: continue
        src_sock = p.inputs["Base Color"].links[0].from_socket
        mix = m.node_tree.nodes.new("ShaderNodeMixRGB"); mix.blend_type = "MIX"; mix.inputs[0].default_value = 0.88
        mix.inputs[2].default_value = GREEN_GREY; mix.label = "step B: far land green-grey"
        m.node_tree.links.new(src_sock, mix.inputs[1]); m.node_tree.links.new(mix.outputs[0], p.inputs["Base Color"])
        m["step_b_tint"] = True; done.append(m.name)
report["far_land_tinted"] = done

# ---- 3. city masses
dg = bpy.context.evaluated_depsgraph_get()
def ground_hit(x, y):
    """(z, ok): ok only when the first hit from above is terrain (no building, road or tree there)."""
    hit, loc, _, _, ob, _ = scene.ray_cast(dg, Vector((x, y, 4000.0)), Vector((0, 0, -1)), distance=8000.0)
    if not hit: return 0.0, False
    return loc.z, ob.name.startswith(("terrain", "horizon_band"))

WALLS = [mat("bg_wall_%d" % i, h) for i, h in enumerate(("#B8B0A0", "#A89F8E", "#9C978D", "#C4BBA8", "#8E8A82", "#B59A80"))]  # pass 2: darker, warmer
ROOFS = [mat("bg_roof_%d" % i, h, 0.7) for i, h in enumerate(("#8E8A84", "#6F6C68", "#9C4A32", "#A2573C", "#7B3A2A", "#5E6266"))]
WIN = mat("bg_window_band", "#3B4148", 0.25)


def blocks(name, pts):
    """pts: list of (x, y, z0, w, d, h, rot); boxes with a roof, walls and dark window bands every storey."""
    v, f, mi = [], [], []
    for x, y, z0, w, d, h, a in pts:
        c, s = math.cos(a), math.sin(a); wi = int(rng.integers(len(WALLS))); ri = len(WALLS) + int(rng.integers(len(ROOFS)))
        corners = [(x + c * dx - s * dy, y + s * dx + c * dy) for dx, dy in ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2))]
        floors = max(1, int(h / 3.2)); levels = [z0]
        for k in range(1, floors):  # wall band, window band per storey
            levels += [z0 + k * 3.2 - 1.3, z0 + k * 3.2]
        levels.append(z0 + h)
        base = len(v)
        for z in levels:
            for cx, cy in corners: v.append((cx, cy, z))
        for li in range(len(levels) - 1):
            for k in range(4):
                a0 = base + li * 4 + k; a1 = base + li * 4 + (k + 1) % 4
                f.append((a0, a1, a1 + 4, a0 + 4)); mi.append(wi if li % 2 == 0 else len(WALLS) + len(ROOFS))
        top = base + (len(levels) - 1) * 4; f.append((top, top + 1, top + 2, top + 3)); mi.append(ri)
    me = bpy.data.meshes.new(name); me.from_pydata(v, [], f); me.validate(); me.update()
    for m in WALLS + ROOFS + [WIN]: me.materials.append(m)
    me.polygons.foreach_set("material_index", mi)
    o = bpy.data.objects.new(name, me); col.objects.link(o); o["claim"] = CLAIM
    return o


def scatter_blocks(name, n, centre, radius, hmin, hmax, wmin, wmax, sector=None, near=0.0):
    pts, tries = [], 0
    while len(pts) < n and tries < n * 30:
        tries += 1
        r = radius * math.sqrt(rng.uniform((near / radius) ** 2 if near else 0, 1)); a = rng.uniform(0, 2 * math.pi)
        x, y = centre[0] + r * math.cos(a), centre[1] + r * math.sin(a)
        if sector and not sector(x, y): continue
        z, ok = ground_hit(x, y)
        if not ok: continue
        w = rng.uniform(wmin, wmax); h = float(np.clip(rng.lognormal(math.log((hmin + hmax) / 2), 0.35), hmin, hmax))
        pts.append((x, y, z - 0.5, w, w * rng.uniform(0.6, 1.4), h, rng.uniform(0, math.pi)))
    blocks(name, pts); return len(pts)

# Blender frame: x east, y north. Ngong Road runs about 280 m north of the pitch; the city is north of it.
north_of_road = lambda x, y: y > 330 + 0.36 * x   # the road runs ENE (bearing about 70 deg)
# pass 2 (L07 sheet): 4 to 12 storeys near Ngong Road, fewer and spread wider, so roofs and tree cover read between them
report["midrise_near"] = scatter_blocks("bg_midrise_near", 170, (300, 1500), 1500, 12, 38, 14, 28, north_of_road, 350)
report["midrise_far"] = scatter_blocks("bg_midrise_far", 360, (1200, 3200), 2800, 15, 48, 16, 34, north_of_road, 1100)
for nm, c, n, rad, hmin, hmax in (("bg_cbd", (8020, 2180), 70, 900, 50, 190), ("bg_upper_hill", (6900, 650), 34, 700, 40, 130),
                                   ("bg_kilimani", (4300, 1700), 60, 1100, 30, 95), ("bg_westlands", (6400, 5200), 45, 1000, 35, 140)):
    report[nm] = scatter_blocks(nm, n, c, rad, hmin, hmax, 22, 48)

# ---- 4. town lights (dusk), off by day
LIGHT = bpy.data.materials.get("bg_town_light") or bpy.data.materials.new("bg_town_light")
LIGHT.use_nodes = True; nt = LIGHT.node_tree; nt.nodes.clear()
em = nt.nodes.new("ShaderNodeEmission"); em.inputs["Color"].default_value = (*srgb("#FFC27A"), 1); em.inputs["Strength"].default_value = 0.0
em.label = "night:14"; out = nt.nodes.new("ShaderNodeOutputMaterial"); nt.links.new(em.outputs[0], out.inputs[0]); LIGHT["claim"] = CLAIM
v, f, nl = [], [], 0
for _ in range(9000):
    r = rng.uniform(1500, 16000); a = rng.uniform(0, 2 * math.pi)
    # clusters: denser in towns (Dagoretti, Karen, Ngong, Kawangware to the W and SW; the city to the N and E)
    if rng.random() > 0.35 + 0.65 * (0.5 + 0.5 * math.sin(3 * a + 1.1) * math.sin(5 * a)): continue
    x, y = r * math.cos(a), r * math.sin(a); z, ok = ground_hit(x, y)
    if not ok: continue
    s = 1.2 + r / 6000; base = len(v)
    v += [(x - s, y, z + 3), (x + s, y, z + 3), (x, y, z + 3 + 2 * s), (x, y - s, z + 3), (x, y + s, z + 3)]
    f += [(base, base + 1, base + 2), (base + 3, base + 4, base + 2)]; nl += 1
me = bpy.data.meshes.new("bg_town_lights"); me.from_pydata(v, [], f); me.update(); me.materials.append(LIGHT)
o = bpy.data.objects.new("bg_town_lights", me); col.objects.link(o); o["claim"] = CLAIM
o.visible_shadow = False; report["town_lights"] = nl

print("BACKGROUND_B " + json.dumps(report), flush=True)
bpy.ops.wm.save_mainfile()
