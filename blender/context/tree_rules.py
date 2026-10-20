"""Step T (Munene, 2026-10-19): trees only where they belong.

For every point of the tree and palm scatters, cast a ray down and read the material of the surface under it.
A tree on a plaza, road, median without planting, car-park aisle, the forecourt paving, a path, a pitch, a track
or a track infield is removed. Inside the W1b site boundary a tree also needs a reason to be there: a lawn or
planting bed under it, or a path or road within ALONG m (a row along the path). Outside the boundary (forest belt,
city) every tree on an allowed surface stays. Run after build_site_detail.py and canopy (it edits the scatter point meshes).
  ~/.venvs/bpy/bin/python blender/context/tree_rules.py [report]     (report: counts only, the blend is not saved)
The rule is by surface, not by position, so it follows any later change of the layout.
"""
import json, math, sys
from collections import Counter
from pathlib import Path
import bpy, bmesh
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
SCATTERS = ("trees", "palms", "site_trees", "fc_retained_site_trees", "fc_retained_palms")
# surfaces a tree may not stand on (material name prefixes); everything else keeps its trees
NO_TREE = ("fc_paving", "fc_murram", "fc_kerb", "apron_paving", "pitch_turf", "runoff_grass", "training_grass", "track_surface",
           "pitch_line", "line_paint", "concrete", "asphalt", "road", "lane", "kerb", "carpark", "car_park", "parking", "bay_",
           "median", "barrier", "footpath", "paving", "murram", "plaza", "pave", "drain", "service", "horizon_racecourse_track",
           "white_shell", "membrane", "track", "sport_", "pitch", "tread", "deck")


ALONG = 9.0
PATHS = ("fc_paving_band", "fc_murram", "roads_mat", "ge_asphalt", "footpath_paving", "fc_paving")
BED = ("fc_grass", "fc_planting", "fc_soil", "planter_soil", "ge_lawn", "sh_0_green", "sh_1_red")


def site_boundary():
    import csv
    return [(float(r["x_east"]), -float(r["z_south"])) for r in csv.DictReader(open(ROOT / "gis/measurements/normalized/site_boundary_w1b_2026-10-16.csv"))]


def inside(x, y, poly):
    c = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1): c = not c
    return c


def plan_paths():
    """Path centre lines of blender/data/site_plan.json (x east, z south) with their widths; many are painted into
    the site ground texture, not modelled, so the ray test alone misses the tree rows along them."""
    P = json.loads((ROOT / "blender/data/site_plan.json").read_text())
    return [(p["pts"], p.get("w", 6.0)) for p in P["paths"]]


def seg_dist(x, z, a, b):
    dx, dz = b[0] - a[0], b[1] - a[1]; L2 = dx * dx + dz * dz or 1e-9
    t = max(0.0, min(1.0, ((x - a[0]) * dx + (z - a[1]) * dz) / L2)); return math.hypot(x - a[0] - t * dx, z - a[1] - t * dz)


def near_plan_path(x, z):
    return any(seg_dist(x, z, a, b) <= w / 2 + ALONG for pts, w in PLAN for a, b in zip(pts[:-1], pts[1:]))


def surface_is_bad(name):
    n = name.lower()
    if any(n.startswith(k) or k in n for k in ("fc_grass", "fc_planting", "fc_soil")): return False
    if any(k in n for k in NO_TREE): return True
    return False


def main(report_only):
    import os
    bpy.ops.wm.open_mainfile(filepath=os.environ.get("TALANTA_SITE_BLEND", str(ROOT / "blender/out/talanta_site.blend")))
    s = bpy.context.scene
    scat = [s.objects[n] for n in SCATTERS if n in s.objects and not s.objects[n].hide_render]
    for o in scat: o.hide_viewport = True   # the ray must not hit the trees themselves
    for o in s.objects:
        if o.name in ("haze_volume",) or o.name.startswith("night_"): o.hide_viewport = True
    dg = bpy.context.evaluated_depsgraph_get()
    global SITE, PLAN; SITE = site_boundary(); PLAN = plan_paths()
    out = {}
    for o in scat:
        me = o.data; mw = o.matrix_world; bad = []; seen = Counter()
        for v in me.vertices:
            p = mw @ v.co
            hit, loc, nrm, idx, ob, _ = s.ray_cast(dg, Vector((p.x, p.y, p.z + 60.0)), Vector((0, 0, -1)), distance=200.0)
            if not hit: seen["(none)"] += 1; continue
            slot = ob.material_slots[ob.data.polygons[idx].material_index] if (ob.type == "MESH" and ob.material_slots and idx < len(ob.data.polygons)) else None
            mname = slot.material.name if slot and slot.material else ob.name
            seen[mname] += 1
            if surface_is_bad(mname): bad.append(v.index); continue
            if inside(p.x, p.y, SITE) and not any(k in mname for k in BED):
                near = near_plan_path(p.x, -p.y)
                for dx, dy in ([] if near else [(ALONG * math.cos(k * math.pi / 4), ALONG * math.sin(k * math.pi / 4)) for k in range(8)]):
                    h2 = s.ray_cast(dg, Vector((p.x + dx, p.y + dy, p.z + 60.0)), Vector((0, 0, -1)), distance=200.0)
                    if h2[0] and h2[4].type == "MESH" and h2[4].material_slots:
                        m2 = h2[4].material_slots[h2[4].data.polygons[h2[3]].material_index].material
                        if m2 and any(k in m2.name for k in PATHS): near = True; break
                if not near: bad.append(v.index); seen["(site, no bed or path)"] += 1
        out[o.name] = {"points": len(me.vertices), "removed": len(bad), "surfaces": dict(seen.most_common(25))}
        if not report_only and bad:
            bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
            bmesh.ops.delete(bm, geom=[bm.verts[i] for i in bad], context="VERTS"); bm.to_mesh(me); bm.free(); me.update()
        o["tree_rule"] = "step T: removed from paving, roads, paths, pitches and tracks by the surface under each point"
    for o in scat: o.hide_viewport = False
    print("TREE_RULES " + json.dumps(out, sort_keys=True), flush=True)
    if not report_only: bpy.ops.wm.save_mainfile()
    return out


if __name__ == "__main__":
    main("report" in sys.argv)
