"""Web hero step 1: bake the approved 07:30 golden light (common.py) into lightmaps on a second UV set ("lightmap").

Run from the repo root:  ~/.venvs/bpy/bin/python blender/web_hero/bake_lightmaps.py [samples]
CPU Cycles. Three passes over every bake group in one call each:
  light   DIFFUSE, direct + indirect, no colour: the light arriving at a white surface (sun, sky, bounce)
  ao      ambient occlusion, 2 m distance
  albedo  DIFFUSE colour only, so procedural materials (terrain masks, turf stripes, track lanes) export
UV set from lightmap_uv.py (chart packing). Groups: stadium shell, louvre fins, stadium ornament and roof on 2048 px atlases; sport, roads, built site items and
24 ground tiles (terrain_site cut into 16 inner tiles of 350 m over the site and 8 outer tiles) on 1024 px.
Writes blender/out/web_hero/maps/<group>_{light,ao,albedo}.png, blender/out/web_hero/talanta_web_baked.blend
and blender/out/web_hero/bake_log.json (times, light scales). Lightmaps are 8-bit sRGB of light / scale.
Stage by stage: each pass bakes in batches of groups, and every batch is written to maps/ (plus the light scale
and time to maps/stages.json) as soon as it finishes. A rerun with the same scene skips the batches already on
disk (UV packing is deterministic), so a lost container costs one batch, not the bake. "fresh" ignores them.
Pass 2 of the concept match: materials_pbr surfaces, suburbs, canopy and traffic are in the scene and shade the
maps; the forecourt_context meshes (forecourt.py, which hides the old plaza and planters) are their own group.
"""
import json, math, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ROOT, OUT, MAPS, setup_morning, sun_vector_app, write_json
import lightmap_uv

SAMPLES = int(sys.argv[-1]) if sys.argv[-1].isdigit() else 128
TEST = "test" in sys.argv  # quarter-size atlases and few samples, for a quick pipeline check
g = setup_morning()
import bpy, bmesh
import numpy as np

s = bpy.context.scene
t_start = time.time()
GROUPS = {
    "stadium_shell": (2048, ["plinth", "base_recess", "base_band", "base_columns", "soffit", "facade_backing", "facade", "opening_trim"]),
    "stadium_fins": (2048, ["louvre_fins"]),
    "stadium_ornament": (2048, ["lattice", "lattice_rings", "shields", "spears"]),
    "roof": (2048, ["roof", "roof_ribs", "ring_beam"]),
    "sport": (1024, ["pitch_zone", "pitch", "pitch_apron", "warmup_track_ne", "warmup_track_ne_infield", "track_sw", "track_sw_infield", "training_pitch_se_turf"]),
    "roads": (2048, ["ngong_road", "ngong_barrier", "roads"]),
    "site_built": (1024, ["planters", "entrance_canopies", "sign_frames"]),
    # environment pass (web_hero_v1): suburbs buildings (roof and wall colours per material, windows as their own
    # faces) and the traffic Visualization; lightmaps only, the export keeps their material colours
    "suburbs": (4096, ["suburbs_buildings"]),
    "traffic": (2048, ["traffic_Visualization"]),
}
_fc = bpy.data.collections.get("forecourt_context")
if _fc:  # forecourt.py meshes (paths, kerbs, beds, plaza); empties and instancers stay out
    GROUPS["forecourt"] = (2048, sorted(o.name for o in _fc.all_objects if o.type == "MESH" and not o.hide_render
                                        and not o.modifiers and len(o.data.polygons)))
CLIP = 1500.0  # the site GLB stops here; the panorama carries everything beyond


def to_mesh(o):
    """Curve objects (bevelled tubes) become real meshes so they can carry a UV set."""
    if o.type == "MESH": return o
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
    n = bpy.data.objects.new(o.name, me)
    for c in o.users_collection: c.objects.link(n)
    n.matrix_world = o.matrix_world.copy()
    for k in o.keys(): n[k] = o[k]
    o.name += "_curve"; o.hide_render = True; o.hide_viewport = True
    n.name = n.name.replace(".001", "")
    return n


def clip_box(o, half):
    """Cut a mesh to the square |x|, |y| <= half (Blender frame)."""
    bm = bmesh.new(); bm.from_mesh(o.data); bm.transform(o.matrix_world)
    for co, no in (((half, 0, 0), (1, 0, 0)), ((-half, 0, 0), (-1, 0, 0)), ((0, half, 0), (0, 1, 0)), ((0, -half, 0), (0, -1, 0))):
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, plane_co=co, plane_no=no, clear_outer=True)
    bm.transform(o.matrix_world.inverted()); bm.to_mesh(o.data); bm.free()


# ---------------------------------------------------------------- prepare objects
groups = {}
for gname, (size, names) in GROUPS.items():
    obs = []
    for n in names:
        o = bpy.data.objects.get(n)
        if o is None or o.hide_render: print("skip", n); continue
        obs.append(to_mesh(o))
    groups[gname] = (size // 4 if TEST else size, obs)
clip_box(bpy.data.objects["roads"], CLIP)

# ground tiles: faces of terrain_site by centroid; inner 4 x 4 over +-700 m, then 8 outer tiles to +-1500 m
ter = bpy.data.objects["terrain_site"]
inner = [-700, -350, 0, 350, 700]; outer = [-CLIP - 10, -700, 700, CLIP + 10]
rects = [(inner[i], inner[i + 1], inner[j], inner[j + 1]) for i in range(4) for j in range(4)]
rects += [(outer[i], outer[i + 1], outer[j], outer[j + 1]) for i in range(3) for j in range(3) if not (i == 1 and j == 1)]
bm0 = bmesh.new(); bm0.from_mesh(ter.data)
cent = np.array([[*f.calc_center_median()[:2]] for f in bm0.faces]); bm0.free()
M = ter.matrix_world
for k, (x0, x1, y0, y1) in enumerate(rects):
    bm = bmesh.new(); bm.from_mesh(ter.data); bm.faces.ensure_lookup_table()
    keep = (cent[:, 0] >= x0) & (cent[:, 0] < x1) & (cent[:, 1] >= y0) & (cent[:, 1] < y1)
    bmesh.ops.delete(bm, geom=[f for f, kp in zip(bm.faces, keep) if not kp], context="FACES")
    me = bpy.data.meshes.new(f"ground_{k:02d}"); bm.to_mesh(me); bm.free()
    for m_ in ter.data.materials: me.materials.append(m_)
    o = bpy.data.objects.new(f"ground_{k:02d}", me); ter.users_collection[0].objects.link(o); o.matrix_world = M.copy()
    o["tile_rect_m"] = [x0, x1, y0, y1]; o["claim"] = ter.get("claim", ""); o["sources"] = ter.get("sources", "")
    groups[f"ground_{k:02d}"] = (256 if TEST else 1024, [o])
ter.hide_render = True; ter.hide_viewport = True

# ---------------------------------------------------------------- outward normals
# Many builders emit faces wound inward or downward (roof, plinth, crown, shields, lattice, spears, tracks).
# Cycles renders both sides, but a bake records the side the normal faces, so fix the copy baked here:
# closed solids get recalculated outside normals; open sheets get each face turned up (if flat) or away
# from the bowl axis (if vertical).
def orient_outward(o):
    bm = bmesh.new(); bm.from_mesh(o.data)
    closed = all(len(e.link_faces) == 2 for e in bm.edges)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    if not closed:
        R = o.matrix_world.to_3x3(); flip = []
        for f in bm.faces:
            n = R @ f.normal; c = o.matrix_world @ f.calc_center_median()
            bad = n.z < 0 if abs(n.z) > 0.5 else n.x * c.x + n.y * c.y < 0
            if bad: flip.append(f)
        bmesh.ops.reverse_faces(bm, faces=flip)
    bm.to_mesh(o.data); bm.free(); o.data.update()


for gname, (size, obs) in groups.items():
    if gname.startswith("ground_"): continue
    for o in obs: orient_outward(o)

# ---------------------------------------------------------------- UV sets: UV0 kept (or added), UV1 = "lightmap"
def ensure_uvs(o):
    if not o.data.uv_layers: o.data.uv_layers.new(name="UVMap")
    o.data.uv_layers[0].active_render = True
    if "lightmap" not in o.data.uv_layers: o.data.uv_layers.new(name="lightmap")
    o.data.uv_layers.active = o.data.uv_layers["lightmap"]


TUBES = {"spears", "lattice_rings", "roof_ribs", "ring_beam"}  # thin round members: unrolled, not boxed
uv_stats = {}
t_uv = time.time()
for gname, (size, obs) in groups.items():
    for o in obs: ensure_uvs(o)
    if gname.startswith("ground_"):
        o = obs[0]; x0, x1, y0, y1 = o["tile_rect_m"]
        vx = np.array([(M @ v.co)[:2] for v in o.data.vertices]); lo, hi = vx.min(0), vx.max(0)
        uv = o.data.uv_layers["lightmap"].data; li = np.zeros(len(o.data.loops), int); o.data.loops.foreach_get("vertex_index", li)
        q = (vx[li] - lo) / (hi - lo)
        uv.foreach_set("uv", (0.002 + q * 0.996).ravel())
        continue
    st = lightmap_uv.pack(obs, size, tube_names=TUBES); uv_stats[gname] = st
    print(f"uv {gname}: {st} at {time.time() - t_uv:.0f} s", flush=True)
print(f"uv sets: {time.time() - t_uv:.1f} s")
if "uvonly" in sys.argv:  # report how much of each atlas the UV set covers, then stop
    for gname, (size, obs) in groups.items():
        area = 0.0
        for o in obs:
            uv = np.empty(len(o.data.loops) * 2); o.data.uv_layers["lightmap"].data.foreach_get("uv", uv); uv = uv.reshape(-1, 2)
            for p_ in o.data.polygons:
                q = uv[p_.loop_start:p_.loop_start + p_.loop_total]
                area += 0.5 * abs(np.dot(q[:, 0], np.roll(q[:, 1], 1)) - np.dot(q[:, 1], np.roll(q[:, 0], 1)))
        print(f"coverage {gname}: {area:.2f} of the atlas, {sum(len(o.data.polygons) for o in obs)} faces", flush=True)
    sys.exit(0)

# ---------------------------------------------------------------- per-group material copies with a target image node
images = {}
for gname, (size, obs) in groups.items():
    for kind in ("light", "ao", "albedo"):
        images[gname, kind] = bpy.data.images.new(f"{gname}_{kind}", size, size, alpha=False, float_buffer=True)
    copies = {}
    for o in obs:
        for slot in o.material_slots:
            m = slot.material
            if m is None: continue
            if m not in copies:
                c = m.copy(); c.name = f"{m.name}@{gname}"; copies[m] = c
                nd = c.node_tree.nodes.new("ShaderNodeTexImage"); nd.name = "bake_target"
                uvn = c.node_tree.nodes.new("ShaderNodeUVMap"); uvn.uv_map = "lightmap"; uvn.name = "bake_uv"
                c.node_tree.links.new(uvn.outputs["UV"], nd.inputs["Vector"])
                c["bake_group"] = gname
            slot.material = copies[m]
all_obs = [o for _, obs in groups.values() for o in obs]


def target(kind):
    for gname, (size, obs) in groups.items():
        for o in obs:
            for slot in o.material_slots:
                if slot.material is None: continue
                nd = slot.material.node_tree.nodes["bake_target"]; nd.image = images[gname, kind]
                slot.material.node_tree.nodes.active = nd


bpy.ops.object.select_all(action="DESELECT")
for o in all_obs: o.select_set(True)
bpy.context.view_layer.objects.active = all_obs[0]
c = s.cycles; c.device = "CPU"; c.use_adaptive_sampling = False; c.use_denoising = False
s.render.bake.margin = 2; s.render.bake.margin_type = "EXTEND"; s.render.bake.target = "IMAGE_TEXTURES"
s.world.light_settings.distance = 2.0
# ---------------------------------------------------------------- encode and save (8-bit sRGB PNG)
def srgb(x):
    x = np.clip(x, 0, 1); return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055)


if TEST: MAPS = OUT / "test/maps"
MAPS.mkdir(parents=True, exist_ok=True)
STAGES = MAPS / "stages.json"
stages = json.loads(STAGES.read_text()) if STAGES.exists() and "fresh" not in sys.argv else {}
key = {"samples": SAMPLES, "test": TEST, "light": g["sun_key"]}
if stages.get("key") != key: stages = {"key": key, "done": {}}
# only=<g1,g2,...>: bake just these groups now (held groups wait for a later run); fresh=<g1,...>: rebake them
ARG = {a.split("=")[0]: a.split("=")[1].split(",") for a in sys.argv if a.startswith(("only=", "fresh="))}
for n in ARG.get("fresh", []):
    for tag in [t for t in stages["done"] if ":" in t and n in t.split(":")[1].split("+")]: del stages["done"][tag]
scales = {k: v["light_scale"] for k, v in stages["done"].items() if "light_scale" in v}


def save(gname, kind):
    im = images[gname, kind]
    w, h = im.size; px = np.empty(w * h * 4, np.float32); im.pixels.foreach_get(px); px = px.reshape(h, w, 4)[..., :3]
    rec = {}
    if kind == "light":
        lum = px.max(-1); v = lum[lum > 1e-4]
        sc = float(np.percentile(v, 99.7)) if v.size else 1.0; scales[gname] = rec["light_scale"] = round(sc, 4)
        enc = srgb(px / sc)
    elif kind == "ao": enc = np.repeat(px[..., :1], 3, -1)
    else: enc = srgb(px)
    out = bpy.data.images.new(f"{gname}_{kind}_8bit", w, h, alpha=False)
    rgba = np.concatenate([enc, np.ones((h, w, 1))], -1).astype(np.float32)
    out.colorspace_settings.name = "Non-Color"  # values written are already encoded
    out.pixels.foreach_set(rgba.ravel()); out.filepath_raw = str(MAPS / f"{gname}_{kind}.png"); out.file_format = "PNG"; out.save()
    im.filepath_raw = out.filepath_raw  # the baked blend references the saved maps, nothing packed
    return rec


BATCHES = [["stadium_shell", "stadium_fins"], ["stadium_ornament", "roof"], ["sport", "roads", "site_built", "forecourt"], ["suburbs", "traffic"],
           [f"ground_{k:02d}" for k in range(12)], [f"ground_{k:02d}" for k in range(12, 16)],  # inner tiles (+-700 m)
           [f"ground_{k:02d}" for k in range(16, 24)]]  # outer tiles: their own batch, as baked with only= (stage tags match)
BATCHES = [[n for n in b_ if n in groups] for b_ in BATCHES]
BATCHES = [b_ for b_ in BATCHES if b_] + [[n for n in groups if not any(n in b_ for b_ in BATCHES)]]
if "only" in ARG: BATCHES = [[n for n in b_ if n in ARG["only"]] for b_ in BATCHES]
SIG = {n: [groups[n][0], sorted(o.name for o in groups[n][1])] for n in groups}  # a batch is reused only for the same objects
times = {}
for kind, btype, filt, spp in (("albedo", "DIFFUSE", {"COLOR"}, 4), ("ao", "AO", set(), 4 if TEST else 64), ("light", "DIFFUSE", {"DIRECT", "INDIRECT"}, 4 if TEST else SAMPLES)):
    target(kind); c.samples = spp; times[kind] = 0.0
    for batch in BATCHES:
        if not batch: continue
        tag = f"{kind}:{'+'.join(batch)}"
        if tag in stages["done"] and stages["done"][tag].get("sig") == [SIG[n] for n in batch] \
                and all((MAPS / f"{n}_{kind}.png").exists() for n in batch):
            for n in batch: images[n, kind].filepath_raw = str(MAPS / f"{n}_{kind}.png")
            print(f"bake {tag}: on disk, skipped", flush=True); continue
        bpy.ops.object.select_all(action="DESELECT")
        sel = [o for n in batch for o in groups[n][1]]
        for o in sel: o.select_set(True)
        bpy.context.view_layer.objects.active = sel[0]
        t0 = time.time()
        if filt: bpy.ops.object.bake(type=btype, pass_filter=filt, use_clear=True, margin=2)
        else: bpy.ops.object.bake(type=btype, use_clear=True, margin=2)
        dt = round(time.time() - t0, 1); times[kind] += dt
        recs = {n: save(n, kind) for n in batch}
        stages["done"][tag] = {"seconds": dt, "samples": spp, "at": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()), "sig": [SIG[n] for n in batch]}
        for n, r_ in recs.items():
            if r_: stages["done"].setdefault(n, {}).update(r_)
        STAGES.write_text(json.dumps(stages, indent=1) + "\n")
        print(f"bake {tag}: {dt} s at {spp} samples, saved", flush=True)
    times[kind] = round(times[kind], 1)
    print(f"bake {kind}: {times[kind]} s at {spp} samples", flush=True)

print("light scales:", scales)

if "only" in ARG:
    print(json.dumps({"partial": ARG["only"], "bake_seconds": times})); sys.exit(0)
# the export step reads these: which group each object and material belongs to
for gname, (size, obs) in groups.items():
    for o in obs: o["bake_group"] = gname; o["bake_size"] = size
el, az = g["el"], g["az"]
log = {"date": g["st"]["date"], "time_eat": g["st"]["time_eat"], "light_preset": g["sun_key"], "sky": g.get("sky_log"), "sun_elevation_deg": round(el, 2), "sun_azimuth_deg": round(az, 2),
       "sun_dir_app": sun_vector_app(el, az), "sun_energy": g["sun"].data.energy, "sun_color": list(g["sun"].data.color),
       "samples": {"light": SAMPLES, "ao": 64, "albedo": 4}, "bake_seconds": times, "stages": stages["done"], "total_seconds": round(time.time() - t_start, 1),
       "groups": {gname: {"size": size, "objects": [o.name for o in obs], "light_scale": scales[gname], "uv": uv_stats.get(gname, "planar tile")} for gname, (size, obs) in groups.items()},
       "encoding": "light png = sRGB(light / light_scale); multiply by light_scale to get linear light on a white diffuse surface"}
if TEST: OUT = OUT / "test"
write_json(OUT / "bake_log.json", log)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "talanta_web_baked.blend"), compress=True)
print(json.dumps({"bake_seconds": times, "total_seconds": log["total_seconds"]}))
