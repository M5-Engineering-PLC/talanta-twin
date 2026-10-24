"""Pass J (engineering/cloud_handoff_2026-10-23.md, Step 2): real local buildings as plain masses, both states.

Reads blender/data/landmarks_pass_j.json and gis/derived/near_ring_buildings.gpkg. Each landmark is its gpkg
footprint (named footprint, or the nearest footprint of 100 m2 or more within 40 m of the map pin) extruded to the gpkg
height, with a flat roof and a parapet. The walls carry a storey rhythm (window rows every storey_m, window columns)
and, for the Enkang blocks, the vertical strips of the frames; colours by eye from the cited frames, never from photo or
map pixels. No names, logos or signage. The generic context masses that overlap a landmark footprint are removed:
the gpkg extrusions in `buildings` and `suburbs_buildings` (suburbs.py) and the step B blocks (`bg_*`, background_b.py).
The buildings exist today, so they show in both the asbuilt and the finished state.
Run from the repo root: TALANTA_SITE_BLEND=blender/out/step_FJ.blend ~/.venvs/bpy/bin/python blender/context/landmarks_pass_j.py
"""
import json, math, os, sqlite3, struct
from pathlib import Path
import numpy as np
import bpy, bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[2]
D = json.loads((ROOT / "blender/data/landmarks_pass_j.json").read_text())
ORIGIN = json.loads((ROOT / "app/public/data/manifest.json").read_text())["origin_utm"]
bpy.ops.wm.open_mainfile(filepath=os.environ.get("TALANTA_SITE_BLEND", str(ROOT / "blender/out/talanta_site.blend")))
scene = bpy.context.scene
col = bpy.data.collections.get("landmarks_pass_j") or bpy.data.collections.new("landmarks_pass_j")
if col.name not in scene.collection.children: scene.collection.children.link(col)
for o in list(col.objects): bpy.data.objects.remove(o)
report = {}


def rings(blob):
    """GeoPackage header, then WKB POLYGON (EPSG:32737) -> rings in the app frame (x east, z south)."""
    flags = blob[3]; off = 8 + {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}[(flags >> 1) & 7]
    e = "<" if blob[off] else ">"; kind, = struct.unpack_from(e + "I", blob, off + 1)
    if kind != 3: return None
    n_r, = struct.unpack_from(e + "I", blob, off + 5); off += 9; out = []
    for _ in range(n_r):
        n, = struct.unpack_from(e + "I", blob, off); off += 4
        xy = struct.unpack_from(e + "d" * (n * 2), blob, off); off += n * 16
        out.append([(x - ORIGIN[0], -(y - ORIGIN[1])) for x, y in zip(xy[::2], xy[1::2])][:-1])
    return out


def area(R): return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(R, R[1:] + R[:1]))) / 2


with sqlite3.connect(f"file:{ROOT / 'gis/derived/near_ring_buildings.gpkg'}?mode=ro", uri=True) as db:
    ROWS = {}
    for fid, geom, name, h, src in db.execute("SELECT fid, geom, name, height_m, height_src FROM near_ring_buildings"):
        R = rings(geom)
        if not R: continue
        P = R[0]; ROWS[fid] = dict(fid=fid, name=name, h=float(h), src=src, ring=P, area=area(P),
                                   c=(sum(p[0] for p in P) / len(P), sum(p[1] for p in P) / len(P)))


def pick(b):
    if b["fids"] != "pin": return [ROWS[f] for f in b["fids"]]
    px, pz = b["pin"]
    near = [r for r in ROWS.values() if math.dist(r["c"], (px, pz)) <= D["pin_radius_m"] and r["area"] >= D["min_area_m2"]]
    return [min(near, key=lambda r: math.dist(r["c"], (px, pz)))] if near else []


# ---------------------------------------------------------------- ground
dg = bpy.context.evaluated_depsgraph_get(); BVH = []
for tn in ("terrain_site", "terrain_far"):
    t = bpy.data.objects.get(tn)
    if not t: continue
    tm = t.evaluated_get(dg).to_mesh()
    BVH.append(BVHTree.FromPolygons([t.matrix_world @ v.co for v in tm.vertices], [p.vertices[:] for p in tm.polygons]))
    t.evaluated_get(dg).to_mesh_clear()


def ground(x, z):
    for b in BVH:
        hit = b.ray_cast(Vector((x, -z, 3000.0)), Vector((0, 0, -1)))
        if hit[0] is not None: return hit[0].z
    return 0.0


def srgb(h):
    h = h.lstrip("#"); return tuple(((int(h[i:i + 2], 16) / 255 + 0.055) / 1.055) ** 2.4 for i in (0, 2, 4))


def flat(name, hx, rough=0.85):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True
    p = m.node_tree.nodes["Principled BSDF"]; p.inputs["Base Color"].default_value = (*srgb(hx), 1)
    p.inputs["Roughness"].default_value = rough; m.diffuse_color = (*srgb(hx), 1)
    return m


def wall_material(name, pal, z0, storey):
    """Wall colour, window rows every storey (from z0), window columns along the facade; optional vertical strips.
    Facade coordinate u = |n_y| x + |n_x| y (world), so the columns run along each wall whatever its bearing."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree
    for n in list(nt.nodes):
        if n.type not in ("BSDF_PRINCIPLED", "OUTPUT_MATERIAL"): nt.nodes.remove(n)
    p = nt.nodes["Principled BSDF"]; p.inputs["Roughness"].default_value = 0.8
    N = lambda t, **kw: nt.nodes.new(t)
    L = nt.links.new
    geo = N("ShaderNodeNewGeometry"); pos = N("ShaderNodeSeparateXYZ"); nrm = N("ShaderNodeSeparateXYZ")
    L(geo.outputs["Position"], pos.inputs[0]); L(geo.outputs["Normal"], nrm.inputs[0])

    def math_(op, a, b=None, v=None):
        n = N("ShaderNodeMath"); n.operation = op
        if isinstance(a, float): n.inputs[0].default_value = a
        else: L(a, n.inputs[0])
        if b is not None:
            if isinstance(b, float): n.inputs[1].default_value = b
            else: L(b, n.inputs[1])
        return n.outputs[0]
    u = math_("ADD", math_("MULTIPLY", math_("ABSOLUTE", nrm.outputs["Y"]), pos.outputs["X"]),
              math_("MULTIPLY", math_("ABSOLUTE", nrm.outputs["X"]), pos.outputs["Y"]))
    zf = math_("FRACT", math_("DIVIDE", math_("SUBTRACT", pos.outputs["Z"], float(z0)), float(storey)))
    row = math_("MULTIPLY", math_("GREATER_THAN", zf, 0.38), math_("LESS_THAN", zf, 0.82))
    cf = math_("FRACT", math_("DIVIDE", u, 3.0))
    colm = math_("MULTIPLY", math_("GREATER_THAN", cf, 0.2), math_("LESS_THAN", cf, 0.8))
    win = math_("MULTIPLY", row, colm)
    wall = N("ShaderNodeRGB"); wall.outputs[0].default_value = (*srgb(pal["wall"]), 1); base = wall.outputs[0]
    if "strip" in pal:  # vertical strips (Enkang): a band of strip_frac every strip_pitch_m along the facade
        sf = math_("FRACT", math_("DIVIDE", u, float(pal["strip_pitch_m"])))
        strip = math_("LESS_THAN", sf, float(pal["strip_frac"]))
        sc = N("ShaderNodeRGB"); sc.outputs[0].default_value = (*srgb(pal["strip"]), 1)
        mx = N("ShaderNodeMix"); mx.data_type = "RGBA"; L(strip, mx.inputs["Factor"]); L(base, mx.inputs[6]); L(sc.outputs[0], mx.inputs[7])
        base = mx.outputs[2]
    wc = N("ShaderNodeRGB"); wc.outputs[0].default_value = (*srgb(pal["window"]), 1)
    mw = N("ShaderNodeMix"); mw.data_type = "RGBA"; L(win, mw.inputs["Factor"]); L(base, mw.inputs[6]); L(wc.outputs[0], mw.inputs[7])
    L(mw.outputs[2], p.inputs["Base Color"])
    rough = N("ShaderNodeMapRange"); L(win, rough.inputs[0]); rough.inputs[3].default_value = 0.85; rough.inputs[4].default_value = 0.2
    L(rough.outputs[0], p.inputs["Roughness"])
    m.diffuse_color = (*srgb(pal["wall"]), 1)
    return m


def resample_ring(R, step=2.0):
    out = []
    for a, b in zip(R, R[1:] + R[:1]):
        n = max(1, int(math.dist(a, b) / step)); out += [(a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n) for k in range(n)]
    return out


def mass(name, R, h, pal, claim):
    """Extruded footprint: walls from below the lowest ground to the roof, a flat roof, a 1 m parapet."""
    S = D["storey_m"]; gs = [ground(*p) for p in resample_ring(R)]; g0, g1 = min(gs), max(gs)
    top = g1 + h; bm = bmesh.new()
    signed = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(R, R[1:] + R[:1]))
    P = R if signed < 0 else R[::-1]  # counter-clockwise in Blender x, y (y = -z): outward wall normals
    lo, mid, hi = ([bm.verts.new((x, -z, zz)) for x, z in P] for zz in (g0 - 0.5, top, top + 1.0))
    n = len(P)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], mid[j], mid[i])).material_index = 0
        bm.faces.new((mid[i], mid[j], hi[j], hi[i])).material_index = 2  # parapet band, 1 m
    roof = bm.faces.new([bm.verts.new((x, -z, top)) for x, z in P]); roof.material_index = 1
    if roof.normal.z < 0: roof.normal_flip()
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(wall_material(name + "_wall", pal, g1, S))
    me.materials.append(flat(name + "_roof", pal["roof"], 0.7)); me.materials.append(flat(name + "_parapet", pal["parapet"], 0.8))
    o = bpy.data.objects.new(name, me); col.objects.link(o); o["claim"] = claim
    return o, g0, top


# ---------------------------------------------------------------- landmark masses
FOOT = []  # (name, ring, bbox) for the clearing below
for b in D["buildings"]:
    pal = D["palettes"][b["palette"]]; rows = pick(b); recs = []
    for k, r in enumerate(rows):
        claim = (f"{b['label']}: footprint {b['position_source']}; height {r['h']} m {b['height_source']}; colours {pal['source']}; "
                 f"confidence {b['confidence']}. Plain mass, no names or signage.")
        o, g0, top = mass(f"lm_{b['name']}" + (f"_{k}" if len(rows) > 1 else ""), r["ring"], r["h"], pal, claim)
        xs, zs = [p[0] for p in r["ring"]], [p[1] for p in r["ring"]]
        FOOT.append((o.name, r["ring"], (min(xs), max(xs), min(zs), max(zs)), r["fid"]))
        recs.append({"fid": r["fid"], "gpkg_name": r["name"], "centre": [round(r["c"][0]), round(r["c"][1])], "area_m2": round(r["area"]),
                     "height_m": r["h"], "height_src": r["src"], "storeys": max(1, round(r["h"] / D["storey_m"])),
                     "pin_distance_m": round(math.dist(r["c"], b["pin"]))})
    report[b["name"]] = recs or "no footprint found"


# ---------------------------------------------------------------- remove the generic masses on these footprints
def inside(p, ring):
    x, y = p; yes = False
    for (ax, ay), (bx, by) in zip(ring, ring[1:] + ring[:1]):
        if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax: yes = not yes
    return yes


def overlaps(x0, x1, z0, z1, pad=1.0):
    """An island's plan box overlaps a landmark: box corners or centre in the footprint, or footprint vertices in the box."""
    for _, R, (a, b, c, d), _ in FOOT:
        if x1 < a - pad or x0 > b + pad or z1 < c - pad or z0 > d + pad: continue
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        if inside((cx, cz), R) or any(inside(q, R) for q in ((x0, z0), (x1, z0), (x1, z1), (x0, z1))): return True
        if any(x0 - pad <= p[0] <= x1 + pad and z0 - pad <= p[1] <= z1 + pad for p in R): return True
    return False


removed = {}
for o in [o for o in scene.objects if o.type == "MESH" and (o.name in ("buildings", "suburbs_buildings") or o.name.startswith("bg_"))]:
    if o.name == "bg_town_lights": continue
    bm = bmesh.new(); bm.from_mesh(o.data); bm.faces.ensure_lookup_table(); M = o.matrix_world
    fid_layer = bm.faces.layers.int.get("building_fid")
    fids = {f[3] for f in FOOT}
    seen, dead = set(), []
    for f0 in bm.faces:  # connected islands: one building or block each
        if f0.index in seen: continue
        stack, isl = [f0], []
        seen.add(f0.index)
        while stack:
            f = stack.pop(); isl.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in seen: seen.add(g.index); stack.append(g)
        if fid_layer is not None and any(f[fid_layer] in fids for f in isl): dead += isl; continue
        pts = [M @ v.co for f in isl for v in f.verts]
        xs, zs = [p.x for p in pts], [-p.y for p in pts]
        if overlaps(min(xs), max(xs), min(zs), max(zs)): dead += isl
    if dead:
        bmesh.ops.delete(bm, geom=list(set(dead)), context="FACES"); bm.to_mesh(o.data); o.data.update()
        removed[o.name] = len(set(dead))
    bm.free()
report["removed_faces"] = removed
print("LANDMARKS_PASS_J " + json.dumps(report), flush=True)
(ROOT / "blender/out/landmarks_pass_j_report.json").write_text(json.dumps(report, indent=1))
bpy.ops.wm.save_mainfile()
