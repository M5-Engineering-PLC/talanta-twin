"""Build estimated far scenery for the Talanta stills."""
import json
import math
from pathlib import Path

import bpy


CLAIM_RACECOURSE = "estimated outline: mapped location from gis/scripts/export_web.py and JWNowpO44rw frames"
CLAIM_TERRAIN = "derived: Copernicus GLO-30 DSM, 2011-2015; limited to raster bounds"
CLAIM_RIDGE = "estimated: Ngong Hills position about 20 km southwest, from environment notes"
CLAIM_CITY = "CBD label from gis/scripts/export_web.py; Upper Hill placement and tower heights estimated"


def _material(name, color, roughness=0.92):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    return mat


def _mesh(scene, name, verts, faces, material, claim):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.materials.append(material)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    scene.collection.objects.link(obj)
    obj["claim"] = claim
    return obj


def _ellipse_mesh(scene, name, center, rx, ry, material, claim, segments=96):
    verts = [(center[0] + rx * math.cos(i * math.tau / segments),
              center[1] + ry * math.sin(i * math.tau / segments), 0.4)
             for i in range(segments)]
    return _mesh(scene, name, verts, [tuple(range(segments))], material, claim)


def _ring_mesh(scene, center, outer, inner, material, claim, segments=128):
    verts = []
    for rx, ry in (outer, inner):
        verts.extend((center[0] + rx * math.cos(i * math.tau / segments),
                      center[1] + ry * math.sin(i * math.tau / segments), 0.55)
                     for i in range(segments))
    faces = [(i, (i + 1) % segments, segments + (i + 1) % segments, segments + i)
             for i in range(segments)]
    return _mesh(scene, "racecourse_track", verts, faces, material, claim)


def _tree_slot(scene, name, x, y, radius, material):
    verts = [(x, y, 0.8), (x, y, 11.5)]
    faces = []
    segments = 9
    for z, scale in ((7.0, 0.72), (9.4, 1.0), (11.5, 0.35)):
        for i in range(segments):
            a = math.tau * i / segments
            verts.append((x + math.cos(a) * radius * scale,
                          y + math.sin(a) * radius * scale * 0.78, z))
    for layer in range(2):
        a0 = 2 + layer * segments
        b0 = a0 + segments
        for i in range(segments):
            faces.append((a0 + i, a0 + (i + 1) % segments,
                          b0 + (i + 1) % segments, b0 + i))
    faces.extend((1, 2 + i, 2 + (i + 1) % segments) for i in range(segments))
    faces.extend((1, 2 + 2 * segments + i, 2 + 2 * segments + (i + 1) % segments)
                 for i in range(segments))
    obj = _mesh(scene, name, verts, faces, material, CLAIM_RACECOURSE)
    obj["role"] = "tree_slot"
    return obj


def _height_sample(image, bounds, min_m, max_m, x, y):
    ix = max(0, min(image.size[0] - 1, int((x - bounds[0]) / (bounds[2] - bounds[0]) * image.size[0])))
    iy = max(0, min(image.size[1] - 1, int((bounds[3] - y) / (bounds[3] - bounds[1]) * image.size[1])))
    value = image.pixels[(iy * image.size[0] + ix) * 4]
    return min_m + value * (max_m - min_m) - 1809.6


def _terrain_band(scene, name, image, metadata, origin, radius_low, radius_high, material):
    bounds = metadata["bounds"]
    step = 4
    nx = image.size[0] // step
    ny = image.size[1] // step
    dx = (bounds[2] - bounds[0]) / (nx - 1)
    dy = (bounds[3] - bounds[1]) / (ny - 1)
    verts, faces, lookup = [], [], {}
    for j in range(ny):
        north = bounds[3] - j * dy
        y = north - origin[1]
        for i in range(nx):
            east = bounds[0] + i * dx
            x = east - origin[0]
            radius = math.hypot(x, y)
            if radius_low <= radius <= radius_high:
                lookup[i, j] = len(verts)
                verts.append((x, y, _height_sample(image, bounds, metadata["min_m"], metadata["max_m"], east, north)))
    for (i, j), a in lookup.items():
        for b, c in (((i + 1, j), (i + 1, j + 1)), ((i + 1, j + 1), (i, j + 1))):
            if b in lookup and c in lookup:
                faces.append((a, lookup[b], lookup[c]))
        if (i + 1, j) in lookup and (i, j + 1) in lookup:
            faces.append((a, lookup[i + 1, j], lookup[i, j + 1]))
    if not faces:
        return None
    return _mesh(scene, name, verts, faces, material, CLAIM_TERRAIN)


def _tower(scene, name, x, y, height, width, material):
    z0, z1 = 1.0, height + 1.0
    x0, x1 = x - width / 2, x + width / 2
    y0, y1 = y - width / 2, y + width / 2
    verts = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
             (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    obj = _mesh(scene, name, verts, faces, material, CLAIM_CITY)
    obj["estimated_height_m"] = height
    return obj


def _triangles(obj):
    if obj.type != "MESH":
        return 0
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


def build(scene, root):
    """Add racecourse, terrain bands, a ridge silhouette, and city towers."""
    root = Path(root).resolve()
    if bpy.data.collections.get("horizon_context"):
        raise RuntimeError("horizon_context already exists. Call build once per loaded scene.")
    collection = bpy.data.collections.new("horizon_context")
    scene.collection.children.link(collection)
    made = []

    # The outline is an estimate because the available OSM extracts contain no racecourse polygon.
    grass = _material("horizon_racecourse_grass", (0.34, 0.49, 0.24))
    track = _material("horizon_racecourse_track", (0.72, 0.69, 0.57))
    leaves = _material("horizon_racecourse_tree", (0.25, 0.36, 0.20))
    # The mapped racecourse label anchors the estimated oval west-southwest of the site.
    center = (-1730.0, -610.0)
    made.append(_ellipse_mesh(scene, "racecourse_infield", center, 410, 245, grass, CLAIM_RACECOURSE))
    made.append(_ring_mesh(scene, center, (470, 290), (410, 245), track, CLAIM_RACECOURSE))
    for i, (dx, dy, r) in enumerate(((-275, 110, 15), (-130, -40, 17), (65, 115, 14),
                                      (245, -75, 16), (360, 60, 13), (0, -175, 14))):
        made.append(_tree_slot(scene, f"tree_slot_{i + 1:02d}", center[0] + dx, center[1] + dy, r, leaves))

    terrain_json = root / "gis/derived/heightmap_glo30_far_12km_30m.json"
    terrain_png = terrain_json.with_suffix(".png")
    metadata = json.loads(terrain_json.read_text())
    manifest = json.loads((root / "app/public/data/manifest.json").read_text())
    origin = manifest["origin_utm"]
    image = bpy.data.images.load(str(terrain_png), check_existing=True)
    image.colorspace_settings.name = "Non-Color"
    terrain_colors = [_material(f"horizon_band_tint_{i}", (0.30 + 0.025 * i, 0.39 + 0.025 * i, 0.36 + 0.03 * i)) for i in range(1, 5)]
    # The raster is a 12 km square: 6 km on cardinal axes and 8.49 km at its corners.
    for i, (lo, hi) in enumerate(((3000, 4500), (4500, 6000), (6000, 7500), (7500, 8500)), 1):
        obj = _terrain_band(scene, f"horizon_band_{i}", image, metadata, origin, lo, hi, terrain_colors[i - 1])
        if obj:
            made.append(obj)
    bpy.data.images.remove(image)

    # The ridge is placed from the environment notes; its profile is a simple visualization.
    ridge_mat = _material("horizon_ngong_ridge", (0.36, 0.43, 0.45))
    ridge_verts = [(-17500, -13200, -5), (-15000, -14600, 0), (-13000, -14900, -8),
                   (-10800, -14000, 0), (-8800, -12800, -12), (-8800, -12800, 450),
                   (-10800, -14000, 720), (-13000, -14900, 1060), (-15000, -14600, 850),
                   (-16800, -13700, 680), (-17500, -13200, 450)]
    made.append(_mesh(scene, "ngong_hills_ridge", ridge_verts,
                      [(0, 1, 9, 10), (1, 2, 8, 9), (2, 3, 7, 8), (3, 4, 5, 6, 7)],
                      ridge_mat, CLAIM_RIDGE))

    tower_mat = _material("horizon_city_pale", (0.63, 0.62, 0.56), 0.88)
    towers = []
    for district, cx, cy, n in (("CBD", 8020, 2180, 12), ("Upper_Hill", 6900, 650, 9)):
        for i in range(n):
            col, row = i % 4, i // 4
            x = cx + (col - 1.5) * 210 + (row % 2) * 68
            y = cy + (row - 1) * 180
            height = 32 + ((i * 17 + 19) % 37)
            towers.append(_tower(scene, f"city_tower_{district}_{i + 1:02d}", x, y,
                                  height, 45 + (i % 3) * 12, tower_mat))
    made.extend(towers)

    for obj in made:
        for child in list(obj.users_collection):
            child.objects.unlink(obj)
        collection.objects.link(obj)
    counts = {
        "racecourse_triangles": sum(_triangles(o) for o in made if o.name.startswith("racecourse_") or o.name.startswith("tree_slot_")),
        "terrain_triangles": sum(_triangles(o) for o in made if o.name.startswith("horizon_band_")),
        "ridge_triangles": _triangles(bpy.data.objects["ngong_hills_ridge"]),
        "city_triangles": sum(_triangles(o) for o in towers),
    }
    counts["total_triangles"] = sum(counts.values())
    counts["triangle_limit"] = 300000
    collection["claim"] = "Mixed: see each object's claim property"
    collection["triangle_report"] = json.dumps(counts, separators=(",", ":"))
    print("HORIZON_TRIANGLES " + json.dumps(counts, sort_keys=True), flush=True)
    return counts
