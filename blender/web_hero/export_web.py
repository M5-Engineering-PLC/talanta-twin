"""Web hero step 3a: stage the baked scene for the three.js app (Blender side of the GLB export).

Run from the repo root after bake_lightmaps.py:  ~/.venvs/bpy/bin/python blender/web_hero/export_web.py [test]
Then run post_glb.mjs (node), which adds instancing, lightmap textures (KTX2), meshopt and the manifest.

What this does, in blender/out/web_hero/talanta_web_baked.blend:
  materials  every material becomes a plain Principled BSDF the glTF exporter can write. Baked materials get
             base colour = their mean baked albedo (or white plus the albedo map for ground, sport and roads)
             and extras.talanta_bake_group, so post_glb.mjs can attach that group's maps.
  UVs        baked objects keep only the "lightmap" set (TEXCOORD_0); other objects export no UVs.
  LODs       LOD0 is the object; LOD1 (300 m) and LOD2 (1 km) are decimated copies named <name>__LOD1/2 for
             meshes over LOD_MIN_TRIS triangles. Small detail is dropped at LOD2 (extras.lod_max_m = 1000).
  instances  GN scatter sets (seats, trees, palms, shrubs, masts, lights, bollards, jets) are written as one
             low-poly proto mesh per kind plus world transforms in instances.bin; post_glb.mjs turns them into
             EXT_mesh_gpu_instancing nodes. Seats keep their colour per instance.
Coordinates: glTF y-up from Blender (x, y, z) -> (x, z, -y), which is the app frame (x east, y up, z south).
Only geometry and plain material values leave Blender; no reference frame or photo is used as a texture.
"""
import json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUT, write_json
import bpy, bmesh
import numpy as np

TEST = "test" in sys.argv
BASE = OUT / "test" if TEST else OUT
STAGE = BASE / "export"; STAGE.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(BASE / "talanta_web_baked.blend"))
s = bpy.context.scene
bake = json.loads((BASE / "bake_log.json").read_text())
ALBEDO_GROUPS = lambda g: g.startswith("ground_") or g in ("sport", "roads", "stadium_ornament")  # procedural or painted (shields): ship the albedo map
LOD_MIN_TRIS = 4000
LOD_RATIO = {1: 0.35, 2: 0.10}
CLIP = 1500.0
THIN_TUBE = 0.35  # m bevel radius; unbaked curves thinner than this export as 4-sided tubes

HERO_COLS = ["plinth", "shell", "facade_detail", "roof_detail", "bowl_detail", "tiers", "pitch", "sport"]
SITE_COLS = ["context", "site", "forecourt_context", "suburbs_context", "traffic_visualization"]
# far land and horizon layers live in the panorama (render_panorama.py near=800); terrain_site is replaced by the
# baked ground tiles
SKIP = {"terrain_far", "terrain_horizon", "terrain_horizon_hills", "terrain_horizon_far", "terrain_site", "haze_volume"}
DETAIL_COLS = {"bowl_detail", "roof_detail"}  # dropped beyond 1 km
DETAIL_NAMES = {"goals", "corner_flags", "corner_flag_poles", "dugouts", "pitch_markings", "training_pitch_lines",
                "parking_lines", "road_markings", "ngong_markings", "boundary_fence", "sign_frames"}
# instanced sets: instancer object -> (glb, low-poly recipe per LOD); recipes are applied to each proto mesh
# Recipes: a float is a decimation ratio (1.0 keeps the mesh), "web" is the canopy's own web_lod mesh (canopy.py, at
# most 300 triangles), "impostor" is two crossed quads textured from the impostor atlas (side views rendered here).
INSTANCERS = {
    "seats": ("hero", {0: "seat4", 1: "seat2"}), "vip_seats": ("hero", {0: 1.0}),
    "trees": ("site", {0: "web", 1: "impostor"}),
    "site_trees": ("site", {0: 0.33, 1: "impostor"}), "palms": ("site", {0: 0.2, 1: "impostor"}),
    "fc_retained_site_trees": ("site", {0: 0.33, 1: "impostor"}), "fc_retained_palms": ("site", {0: 0.2, 1: "impostor"}),
    "shrubs": ("site", {0: 0.25}), "fc_retained_shrubs": ("site", {0: 0.25}),
    "light_masts": ("site", {0: 1.0}), "path_lights": ("site", {0: 1.0}), "bollards": ("site", {0: 1.0}), "flag_masts": ("site", {0: 1.0}),
    "fc_retained_light_masts": ("site", {0: 1.0}), "fc_retained_path_lights": ("site", {0: 1.0}),
    "fc_retained_bollards": ("site", {0: 1.0}), "fc_retained_flag_masts": ("site", {0: 1.0}),
    "jets": ("site", {0: 1.0}), "track_masts": ("site", {0: 1.0}),
    "suburbs_trees": ("site", {0: 0.33, 1: "impostor"}), "suburbs_tanks": ("site", {0: 1.0}),
}
GN_PROTO = {"seats": "seat_proto", "vip_seats": "vip_seat_proto"}  # GN geometry instances report the instancer itself
PREFIX_SETS = {"suburbs_tree_": "suburbs_trees", "suburbs_tank_": "suburbs_tanks"}  # collection-instance empties
TREE_SETS = ("trees", "site_trees", "palms", "fc_retained_site_trees", "fc_retained_palms", "suburbs_trees")
INST_SWITCH = {"seats": [0, 300], **{k: [0, 300] for k in TREE_SETS}}  # LOD start distances (m)
INST_MAX = {"seats": 1000, "vip_seats": 1000, "shrubs": 1000, "fc_retained_shrubs": 1000, "path_lights": 1000, "bollards": 1000,
            "fc_retained_path_lights": 1000, "fc_retained_bollards": 1000, "jets": 1000}
IMPOSTOR_CELL = 128


def tris(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


# ---------------------------------------------------------------- materials
def mean_albedo(o, mat_index, img_px, size):
    """Mean baked albedo over the faces of one material slot, sampled at face centres in the lightmap set."""
    me = o.data; uvl = me.uv_layers["lightmap"].data
    acc = []; w = []
    for p in me.polygons:
        if p.material_index != mat_index: continue
        u = sum(uvl[i].uv[0] for i in p.loop_indices) / p.loop_total; v = sum(uvl[i].uv[1] for i in p.loop_indices) / p.loop_total
        x = min(size - 1, max(0, int(u * size))); y = min(size - 1, max(0, int(v * size)))
        acc.append(img_px[y, x]); w.append(p.area)
    if not acc: return None
    a = np.average(np.array(acc), axis=0, weights=np.maximum(np.array(w), 1e-6))
    return [float(c) for c in a]


def first_color(sock, depth=0):
    """A representative colour for a linked Base Color: the first unlinked colour found upstream."""
    if not sock.is_linked: return list(sock.default_value)[:3]
    if depth > 6: return None
    nd = sock.links[0].from_node
    if nd.type == "VALTORGB":
        els = nd.color_ramp.elements; return list(els[len(els) // 2].color)[:3]
    if nd.type == "RGB": return list(nd.outputs[0].default_value)[:3]
    for i in nd.inputs:
        if i.type == "RGBA":
            c = first_color(i, depth + 1)
            if c: return c
    return None


albedo_cache = {}
def albedo_px(gname):
    if gname not in albedo_cache:
        size = bake["groups"][gname]["size"]
        im = bpy.data.images.load(str(BASE / "maps" / f"{gname}_albedo.png")); im.colorspace_settings.name = "Non-Color"
        px = np.empty(size * size * 4, np.float32); im.pixels.foreach_get(px); px = px.reshape(size, size, 4)[..., :3]
        lin = np.where(px <= 0.04045, px / 12.92, ((px + 0.055) / 1.055) ** 2.4)
        albedo_cache[gname] = (lin, size)
    return albedo_cache[gname]


def principled_values(m):
    """(base colour, roughness, metallic, emission colour, emission strength, alpha) from a material."""
    bsdf = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if m.use_nodes else None
    if bsdf is None:
        return list(m.diffuse_color)[:3], 0.7, 0.0, [0, 0, 0], 0.0, 1.0
    gv = lambda k, d: (bsdf.inputs[k].default_value if not bsdf.inputs[k].is_linked else d)
    col = first_color(bsdf.inputs["Base Color"]) or [0.6, 0.6, 0.6]
    em = list(gv("Emission Color", (0, 0, 0, 1)))[:3]; es = float(gv("Emission Strength", 0.0))
    alpha = float(gv("Alpha", 1.0)); trans = float(gv("Transmission Weight", 0.0))
    if trans > 0.5: alpha = min(alpha, 0.35)
    return col, float(gv("Roughness", 0.7)), float(gv("Metallic", 0.0)), em, es, alpha


new_mats = {}
def export_material(m, o, slot_index):
    gname = m.get("bake_group")
    if gname and ALBEDO_GROUPS(gname):
        key = (m.name, "tex")
    elif gname:
        key = (m.name, o.name, slot_index)  # mean albedo can differ per object for a shared material
    else:
        key = (m.name,)
    if key in new_mats: return new_mats[key]
    img = own_image(m)
    col, rough, metal, em, es, alpha = principled_values(m)
    if img is not None: col = [1.0, 1.0, 1.0]
    elif gname and ALBEDO_GROUPS(gname): col = [1.0, 1.0, 1.0]
    elif gname:
        px, size = albedo_px(gname); a = mean_albedo(o, slot_index, px, size)
        if a: col = a
    base = m.name.split("@")[0]
    nm = bpy.data.materials.new(f"{base}" + (f"@{gname}" if gname else ""))
    nm.use_nodes = True; b = nm.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1.0); b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if es > 0 and max(em) > 0:
        b.inputs["Emission Color"].default_value = (*em, 1.0); b.inputs["Emission Strength"].default_value = es
    if alpha < 1.0:
        b.inputs["Alpha"].default_value = alpha
        try: nm.surface_render_method = "BLENDED"
        except AttributeError: nm.blend_method = "BLEND"
    if img is not None:  # painted: its own image on UV 0 with an alpha cut-out; the lightmap moves to UV 1
        tn = nm.node_tree.nodes.new("ShaderNodeTexImage"); tn.image = img
        nm.node_tree.links.new(tn.outputs["Color"], b.inputs["Base Color"]); nm.node_tree.links.new(tn.outputs["Alpha"], b.inputs["Alpha"])
        nm["talanta_alpha_mask"] = True
    if gname:
        nm["talanta_bake_group"] = gname; nm["talanta_albedo_map"] = bool(ALBEDO_GROUPS(gname)) and img is None
        nm["talanta_lightmap_texcoord"] = 1 if img is not None else 0
    nm.use_backface_culling = False  # source meshes are not consistently wound; draw both sides like Cycles
    new_mats[key] = nm
    return nm


# ---------------------------------------------------------------- objects to export
def realize(o):
    """Evaluated geometry (modifiers, curve bevels) as a fresh mesh object in world space."""
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    me.transform(o.matrix_world)
    n = bpy.data.objects.new(o.name + "__x", me); s.collection.objects.link(n)
    return n


def own_image(m):
    """The image a material paints with (shield design, generated by build_blockout.py), if any."""
    if m is None or not m.use_nodes: return None
    return next((n.image for n in m.node_tree.nodes if n.type == "TEX_IMAGE" and n.image and n.name != "bake_target"), None)


def keep_uvs(o, baked, painted):
    """Baked: lightmap only (TEXCOORD_0), or the painting UV first and the lightmap second for painted objects."""
    uvs = o.data.uv_layers
    keep = (["UVMap"] if painted else []) + (["lightmap"] if baked else [])
    for l in [l for l in uvs if l.name not in keep]: uvs.remove(l)
    if painted and baked and uvs[0].name != "UVMap": raise SystemExit(f"{o.name}: UV order")
    if uvs: uvs[0].active_render = True


def strip_props(o):
    for k in list(o.keys()): del o[k]


def decimated(o, ratio, name):
    m = o.modifiers.new("lod", "DECIMATE"); m.ratio = ratio; m.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(o.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    o.modifiers.remove(m)
    n = bpy.data.objects.new(name, me); s.collection.objects.link(n)
    return n


export = {"hero": [], "site": []}
lod_table = []
for glb, cols in (("hero", HERO_COLS), ("site", SITE_COLS)):
    for cname in cols:
        col = bpy.data.collections.get(cname)
        if col is None: continue
        for o in list(col.all_objects):
            if o.hide_render or o.name in SKIP or o.name in INSTANCERS or o.type not in ("MESH", "CURVE"): continue
            if any(m.type == "NODES" for m in o.modifiers) and o.type == "MESH" and not o.data.polygons: continue
            baked = "bake_group" in o.keys()
            if o.type == "CURVE" and o.data.bevel_depth < THIN_TUBE:
                o.data.bevel_resolution = 0  # 4-sided members: thin rails, purlins and cables read the same in the app
            src_mats = [sl.material for sl in o.material_slots]
            x = realize(o)
            if len(x.data.polygons) == 0: bpy.data.objects.remove(x); continue
            if glb == "site" and not baked:  # the site GLB stops at +-1500 m; the panorama carries the rest
                c = np.array([p.center[:2] for p in x.data.polygons])
                if np.abs(c).max() > CLIP:
                    bm = bmesh.new(); bm.from_mesh(x.data)
                    far = [f for f in bm.faces if max(abs(f.calc_center_median().x), abs(f.calc_center_median().y)) > CLIP]
                    bmesh.ops.delete(bm, geom=far, context="FACES"); bm.to_mesh(x.data); bm.free()
            painted = any(own_image(m) for m in src_mats)
            keep_uvs(x, baked, painted)
            for i, m in enumerate(src_mats):
                if m is not None and i < len(x.data.materials): x.data.materials[i] = export_material(m, o, i)
            strip_props(x)
            name = o.name; o.name = name + "__src"; x.name = name
            T = tris(x.data); detail = cname in DETAIL_COLS or name in DETAIL_NAMES
            x["lod_group"] = name; x["lod"] = 0; x["lod_switch_m"] = [0, 300, 1000] if T > LOD_MIN_TRIS else [0]
            if detail: x["lod_max_m"] = 1000
            if baked: x["talanta_bake_group"] = o["bake_group"]
            export[glb].append(x); row = {"name": name, "glb": glb, "lod0": T}
            if T > LOD_MIN_TRIS:
                for k in (1, 2):
                    if k == 2 and detail: continue
                    d = decimated(x, LOD_RATIO[k], f"{name}__LOD{k}")
                    d["lod_group"] = name; d["lod"] = k; d["lod_switch_m"] = x["lod_switch_m"]
                    if baked: d["talanta_bake_group"] = o["bake_group"]
                    export[glb].append(d); row[f"lod{k}"] = tris(d.data)
            lod_table.append(row)
print("objects staged:", {k: len(v) for k, v in export.items()}, flush=True)

# ---------------------------------------------------------------- impostors
ATLAS = {}  # proto mesh name -> (u0, v0, u1, v1) in the atlas


def impostor_atlas(mesh_names):
    """Side views (orthographic, alpha) of each proto mesh into one atlas, IMPOSTOR_CELL px per cell; morning sun from
    behind the camera, sky fill. Writes <stage>/impostor_atlas.png and fills ATLAS."""
    if not mesh_names: return
    n = len(mesh_names); cols = int(math.ceil(math.sqrt(n))); rows = int(math.ceil(n / cols)); C_ = IMPOSTOR_CELL
    W_, H_ = cols * C_, rows * C_
    sc = bpy.data.scenes.new("impostor"); sc.render.engine = "CYCLES"; sc.cycles.device = "CPU"; sc.cycles.samples = 16
    sc.cycles.use_denoising = True; sc.render.film_transparent = True; sc.render.resolution_x = sc.render.resolution_y = C_
    sc.render.image_settings.file_format = "PNG"; sc.render.image_settings.color_mode = "RGBA"
    sc.view_settings.view_transform = s.view_settings.view_transform; sc.view_settings.exposure = s.view_settings.exposure
    w = bpy.data.worlds.new("impostor_sky"); w.use_nodes = True; w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.65, 0.8, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.6; sc.world = w
    sun = bpy.data.objects.new("imp_sun", bpy.data.lights.new("imp_sun", "SUN")); sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(55), 0, math.radians(20)); sc.collection.objects.link(sun)
    cd = bpy.data.cameras.new("imp_cam"); cd.type = "ORTHO"; cam_ = bpy.data.objects.new("imp_cam", cd); sc.collection.objects.link(cam_); sc.camera = cam_
    atlas = np.zeros((H_, W_, 4), np.float32); tmp = STAGE / "_impostor_cell.png"
    for k, mn in enumerate(mesh_names):
        me = bpy.data.meshes[mn]; o = bpy.data.objects.new("_imp", me); sc.collection.objects.link(o)
        co = np.array([v.co[:] for v in me.vertices]); lo, hi = co.min(0), co.max(0); cx, cy = (lo[:2] + hi[:2]) / 2
        size = max(hi[0] - lo[0], hi[2] - lo[2], 0.5) * 1.04
        cd.ortho_scale = size; cam_.location = (cx, cy - 200.0, (lo[2] + hi[2]) / 2); cam_.rotation_euler = (math.radians(90), 0, 0)
        cd.clip_end = 400.0; sc.render.filepath = str(tmp)
        with bpy.context.temp_override(scene=sc): bpy.ops.render.render(write_still=True)
        im = bpy.data.images.load(str(tmp)); px = np.array(im.pixels[:], np.float32).reshape(C_, C_, 4); bpy.data.images.remove(im)
        r_, c_ = divmod(k, cols); atlas[(rows - 1 - r_) * C_:(rows - r_) * C_, c_ * C_:(c_ + 1) * C_] = px
        # quad UVs: the cell, trimmed to the mesh's own width/height inside the square view
        wv, hv = (hi[0] - lo[0]) * 1.0 / size, (hi[2] - lo[2]) / size
        u0 = (c_ + 0.5 - wv / 2) / cols; u1 = (c_ + 0.5 + wv / 2) / cols; v0 = (rows - 1 - r_ + 0.5 - hv / 2) / rows; v1 = (rows - 1 - r_ + 0.5 + hv / 2) / rows
        ATLAS[mn] = (u0, v0, u1, v1); sc.collection.objects.unlink(o); bpy.data.objects.remove(o)
    img = bpy.data.images.new("impostor_atlas", W_, H_, alpha=True); img.pixels.foreach_set(atlas.ravel())
    img.filepath_raw = str(STAGE / "impostor_atlas.png"); img.file_format = "PNG"; img.save()
    img.pack()  # the glTF exporter embeds it; post_glb.mjs turns it into KTX2 (ETC1S, alpha)
    mat = bpy.data.materials.new("impostor_atlas"); mat.use_nodes = True; b_ = mat.node_tree.nodes["Principled BSDF"]
    tn = mat.node_tree.nodes.new("ShaderNodeTexImage"); tn.image = img
    mat.node_tree.links.new(tn.outputs["Color"], b_.inputs["Base Color"]); mat.node_tree.links.new(tn.outputs["Alpha"], b_.inputs["Alpha"])
    b_.inputs["Roughness"].default_value = 0.9; mat["talanta_alpha_mask"] = True; mat["talanta_impostor"] = True; mat.use_backface_culling = False
    ATLAS["_material"] = mat; ATLAS["_size"] = [W_, H_]; ATLAS["_cells"] = n
    print("impostor atlas", n, "cells", W_, "x", H_, flush=True)


def impostor_mesh(me_src, name):
    """Two crossed vertical quads over the proto's bounding box, UV-mapped to its atlas cell."""
    co = np.array([v.co[:] for v in me_src.vertices]); lo, hi = co.min(0), co.max(0); c = (lo + hi) / 2
    hw_ = (hi[0] - lo[0]) / 2; u0, v0, u1, v1 = ATLAS[me_src.name]
    verts = [(c[0] - hw_, c[1], lo[2]), (c[0] + hw_, c[1], lo[2]), (c[0] + hw_, c[1], hi[2]), (c[0] - hw_, c[1], hi[2]),
             (c[0], c[1] - hw_, lo[2]), (c[0], c[1] + hw_, lo[2]), (c[0], c[1] + hw_, hi[2]), (c[0], c[1] - hw_, hi[2])]
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], [(0, 1, 2, 3), (4, 5, 6, 7)])
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li, (uu, vv) in zip(poly.loop_indices, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))): uv.data[li].uv = (uu, vv)
    me.materials.append(ATLAS["_material"]); me["talanta_impostor"] = True; me.update()
    return me


# ---------------------------------------------------------------- instance sets
def lowpoly(me_src, recipe, name):
    """Low-poly version of a proto mesh: a decimation ratio, the canopy's web mesh, crossed impostor quads, an
    8-triangle canopy, or 4/2-triangle seats."""
    co = np.array([v.co[:] for v in me_src.vertices]); lo, hi = co.min(0), co.max(0)
    if recipe == "web":
        web = bpy.data.meshes.get(me_src.get("web_lod", ""))
        if web is None: raise SystemExit(f"{me_src.name}: no web_lod mesh")
        me = web.copy(); me.name = name
        for l in list(me.uv_layers): me.uv_layers.remove(l)
        return me
    if recipe == "impostor":
        return impostor_mesh(me_src, name)
    me = bpy.data.meshes.new(name)
    if isinstance(recipe, float):
        if recipe >= 1.0:
            me = me_src.copy(); me.name = name
        else:
            tmp = bpy.data.objects.new("_tmp", me_src); s.collection.objects.link(tmp)
            d = decimated(tmp, recipe, name); me = d.data; bpy.data.objects.remove(d); bpy.data.objects.remove(tmp)
        for l in list(me.uv_layers): me.uv_layers.remove(l)
        me.validate(clean_customdata=False); return me
    if recipe == "octa":  # canopy only: the widest material (leaves / fronds), as an octahedron over its bbox
        mi = max(range(len(me_src.materials)), key=lambda i: sum(p.area for p in me_src.polygons if p.material_index == i))
        cv = np.array([me_src.vertices[v].co[:] for p in me_src.polygons if p.material_index == mi for v in p.vertices])
        l2, h2 = cv.min(0), cv.max(0); c = (l2 + h2) / 2; r = (h2 - l2) / 2
        v = [(c[0] + r[0], c[1], c[2]), (c[0] - r[0], c[1], c[2]), (c[0], c[1] + r[1], c[2]), (c[0], c[1] - r[1], c[2]),
             (c[0], c[1], h2[2]), (c[0], c[1], max(l2[2], 0.0) + 0.15 * (h2[2] - l2[2]))]
        f = [(0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)]
        me.from_pydata(v, [], f); me.materials.append(me_src.materials[mi])
    else:  # seats, facing +y (towards the pitch): seat pan, plus the backrest for seat4
        x0, x1 = lo[0], hi[0]
        v = [(x0, -0.18, 0.445), (x1, -0.18, 0.445), (x1, 0.22, 0.445), (x0, 0.22, 0.445),
             (x0, -0.20, 0.42), (x1, -0.20, 0.42), (x1, -0.24, 0.86), (x0, -0.24, 0.86)]
        f = [(0, 1, 2, 3), (4, 5, 6, 7)] if recipe == "seat4" else [(4, 5, 6, 7)]
        me.from_pydata(v, [], f); me.materials.append(me_src.materials[0])
    me.update(); return me


dg = bpy.context.evaluated_depsgraph_get()
inst = {}  # (set, proto mesh name) -> list of 4x4
for di in dg.object_instances:
    if not di.is_instance or di.parent is None: continue
    par = di.parent.original; pn = par.name
    if par.hide_render: continue  # the viewport depsgraph also lists the instances of render-hidden instancers
    pn = next((v for k, v in PREFIX_SETS.items() if pn.startswith(k)), pn)
    if pn not in INSTANCERS or di.object.type != "MESH": continue
    ob = di.object.original
    mn = bpy.data.objects[GN_PROTO.get(pn, "seat_proto")].data.name if ob.name == par.name else ob.data.name
    inst.setdefault((pn, mn), []).append(np.array(di.matrix_world))
impostor_atlas(sorted({mn for (sn, mn) in inst if "impostor" in INSTANCERS[sn][1].values()}))
seat_col = None
sp = bpy.data.objects["seats"].data
if "seatcol" in sp.attributes:
    seat_col = np.empty(len(sp.vertices) * 4, np.float32); sp.attributes["seatcol"].data.foreach_get("color", seat_col); seat_col = seat_col.reshape(-1, 4)
    seat_pos = np.empty(len(sp.vertices) * 3); sp.vertices.foreach_get("co", seat_pos); seat_pos = seat_pos.reshape(-1, 3) @ np.array(bpy.data.objects["seats"].matrix_world)[:3, :3].T + np.array(bpy.data.objects["seats"].matrix_world)[:3, 3]

C = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)  # Blender -> glTF


def mat_to_trs(M):
    t = M[:3, 3]; R = M[:3, :3]; sc = np.linalg.norm(R, axis=0); R = R / sc
    Rg = C @ R @ C.T; tg = C @ t; sg = np.array([sc[0], sc[2], sc[1]])
    # rotation matrix -> quaternion (x, y, z, w)
    tr = np.trace(Rg)
    if tr > 0:
        S = math.sqrt(tr + 1.0) * 2; w = 0.25 * S; x = (Rg[2, 1] - Rg[1, 2]) / S; y = (Rg[0, 2] - Rg[2, 0]) / S; z = (Rg[1, 0] - Rg[0, 1]) / S
    elif Rg[0, 0] > Rg[1, 1] and Rg[0, 0] > Rg[2, 2]:
        S = math.sqrt(1.0 + Rg[0, 0] - Rg[1, 1] - Rg[2, 2]) * 2; w = (Rg[2, 1] - Rg[1, 2]) / S; x = 0.25 * S; y = (Rg[0, 1] + Rg[1, 0]) / S; z = (Rg[0, 2] + Rg[2, 0]) / S
    elif Rg[1, 1] > Rg[2, 2]:
        S = math.sqrt(1.0 + Rg[1, 1] - Rg[0, 0] - Rg[2, 2]) * 2; w = (Rg[0, 2] - Rg[2, 0]) / S; x = (Rg[0, 1] + Rg[1, 0]) / S; y = 0.25 * S; z = (Rg[1, 2] + Rg[2, 1]) / S
    else:
        S = math.sqrt(1.0 + Rg[2, 2] - Rg[0, 0] - Rg[1, 1]) * 2; w = (Rg[1, 0] - Rg[0, 1]) / S; x = (Rg[0, 2] + Rg[2, 0]) / S; y = (Rg[1, 2] + Rg[2, 1]) / S; z = 0.25 * S
    return tg, [x, y, z, w], sg


blob = bytearray(); sets = []
for (setname, meshname), Ms in sorted(inst.items()):
    glb, recipes = INSTANCERS[setname]
    Ms = np.array(Ms)
    keep = np.ones(len(Ms), bool)
    if glb == "site": keep = (np.abs(Ms[:, 0, 3]) <= CLIP) & (np.abs(Ms[:, 1, 3]) <= CLIP)
    Ms = Ms[keep]
    if not len(Ms): continue
    T, Q, S_ = zip(*[mat_to_trs(M) for M in Ms])
    arrs = {"TRANSLATION": np.array(T, np.float32), "ROTATION": np.array(Q, np.float32), "SCALE": np.array(S_, np.float32)}
    if setname == "seats" and seat_col is not None:
        # match instances to points by position (instances keep point order, checked here)
        d = np.abs(Ms[:, :3, 3] - seat_pos[:len(Ms)]).max()
        if d > 1e-3: raise SystemExit(f"seat instances are not in point order ({d:.3f} m)")
        arrs["_COLOR_0"] = seat_col[:len(Ms), :3].astype(np.float32)
    src = bpy.data.meshes[meshname]
    entry = {"set": setname, "proto": meshname, "glb": glb, "count": int(len(Ms)), "attributes": {}, "lods": []}
    for k, a in arrs.items():
        entry["attributes"][k] = {"offset": len(blob), "count": int(a.shape[0]), "components": int(a.shape[1])}
        blob += a.tobytes()
    for lod, recipe in sorted(recipes.items()):
        me = lowpoly(src, recipe, f"proto__{setname}__{meshname}__LOD{lod}")
        mats = [export_material(m, None, i) if m else None for i, m in enumerate(me.materials)]
        for i, m in enumerate(mats):
            if m: me.materials[i] = m
        po = bpy.data.objects.new(me.name, me); s.collection.objects.link(po)
        po["proto_of"] = setname; po["lod"] = lod
        export[glb].append(po)
        entry["lods"].append({"lod": lod, "node": po.name, "tris": tris(me),
                              "switch_m": INST_SWITCH.get(setname, [0])[lod] if lod < len(INST_SWITCH.get(setname, [0])) else None})
    if setname in INST_MAX: entry["max_m"] = INST_MAX[setname]
    sets.append(entry)
    print("instances", setname, meshname, len(Ms), [l["tris"] for l in entry["lods"]], flush=True)
(STAGE / "instances.bin").write_bytes(bytes(blob))

# ---------------------------------------------------------------- write staged GLBs
for glb, obs in export.items():
    bpy.ops.object.select_all(action="DESELECT")
    for o in obs: o.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.export_scene.gltf(filepath=str(STAGE / f"{glb}_stage.glb"), export_format="GLB", use_selection=True,
                              export_extras=True, export_texcoords=True, export_normals=True, export_apply=False,
                              export_yup=True, export_materials="EXPORT", export_image_format="AUTO",
                              export_cameras=False, export_lights=False, export_animations=False,
                              export_attributes=False, export_gn_mesh=False, export_gpu_instances=False)
    print("wrote", glb, flush=True)
el, az = bake["sun_elevation_deg"], bake["sun_azimuth_deg"]
write_json(STAGE / "stage.json", {"instances": sets, "lod_table": lod_table, "bake": bake,
                                  "view": {"transform": s.view_settings.view_transform, "look": s.view_settings.look,
                                           "exposure": s.view_settings.exposure},
                                  "albedo_groups": [g for g in bake["groups"] if ALBEDO_GROUPS(g)]})
print(json.dumps({"lod0_tris_meshes": {g: sum(r["lod0"] for r in lod_table if r["glb"] == g) for g in export}}))
