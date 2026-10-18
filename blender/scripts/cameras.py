"""Load the frozen critic cameras (app/cameras/manifest.json) into a Blender scene.

App frame (x east, y up, z south) -> Blender (X east, Y north, Z up) = (x, -z, y).
Usage inside Blender:  from cameras import load_cameras; cams = load_cameras(scene, manifest_path)
"""
import json, math
import bpy
from mathutils import Vector


def to_blender(p):
    return Vector((p[0], -p[2], p[1]))


def load_cameras(scene, path, collection_name="critic_cameras", extra=None):
    """extra: an optional JSON file with more cameras in the manifest format (interior pass C30-C35 in
    blender/data/interior_cameras.json, kept out of the app manifest); an optional "roll_deg" turns the camera
    about its view axis (hand-held frames)."""
    m = json.load(open(path))
    if extra is not None and __import__("os").path.exists(extra):
        m = dict(m); m["cameras"] = m["cameras"] + json.load(open(extra))["cameras"]
    col = bpy.data.collections.get(collection_name) or bpy.data.collections.new(collection_name)
    if col.name not in scene.collection.children:
        scene.collection.children.link(col)
    out = {}
    for c in m["cameras"]:
        data = bpy.data.cameras.new(c["id"])
        data.sensor_fit = "HORIZONTAL"
        data.sensor_width = m["sensor_width_mm"]
        if c["projection"] == "orthographic":
            data.type = "ORTHO"; data.ortho_scale = c["ortho_scale_m"]
        else:
            data.type = "PERSP"; data.lens = c["focal_length_mm"]
        data.clip_start, data.clip_end = 0.5, 60000
        data.dof.use_dof = m["exposure"]["dof"]
        data.dof.aperture_fstop = m["exposure"]["f_stop"]
        ob = bpy.data.objects.new(c["id"], data)
        col.objects.link(ob)
        pos, tgt = to_blender(c["position"]), to_blender(c["target"])
        ob.location = pos
        q = (tgt - pos).to_track_quat("-Z", "Y")
        if c.get("roll_deg"):
            from mathutils import Quaternion
            q = q @ Quaternion((0, 0, 1), math.radians(c["roll_deg"]))
        ob.rotation_euler = q.to_euler()
        ob["purpose"], ob["seed"], ob["sun"] = c["purpose"], c["seed"], json.dumps(c["sun"])
        if "exposure_ev" in c: ob["exposure_ev"] = c["exposure_ev"]  # per-camera offset (hand-held auto exposure)
        out[c["id"]] = ob
    return m, out


def apply_render_settings(scene, m, look_check=True):
    r = scene.render
    r.resolution_x, r.resolution_y = m["resolution"]
    r.resolution_percentage = int(100 * (m["look_check_scale"] if look_check else 1))
    scene.view_settings.view_transform = m["exposure"]["view_transform"]
    scene.view_settings.exposure = m["exposure"]["exposure_ev"]
