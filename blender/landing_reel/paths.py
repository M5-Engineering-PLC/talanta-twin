"""Camera poses of the walkthrough chapters (blender/landing_reel/chapters.json), in the app frame.

pose(chapter, i) -> (position, target) for frame i of the chapter; frames(chapter) is its frame count. Plain Python
(no bpy), so the paths can be checked outside Blender: python3 blender/landing_reel/paths.py prints the poses of
every 24th frame and the nearest distance to the stadium centre.
"""
import json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = json.loads((ROOT / "blender/landing_reel/chapters.json").read_text())
CAMS = {c["id"]: c for c in json.loads((ROOT / "app/cameras/manifest.json").read_text())["cameras"]}


def chapter(cid):
    return next(c for c in SPEC["chapters"] if c["id"] == cid)


def frames(ch):
    return int(round(ch["seconds"] * SPEC["fps"]))


def _ease(t, kind):
    if kind == "out": return 1 - (1 - t) ** 3
    if kind == "in_out": return t * t * (3 - 2 * t) if t < 1 else 1.0
    return t


def _polar(p, c):
    """(radius, azimuth from +x towards +z, height) of p about c."""
    dx, dz = p[0] - c[0], p[2] - c[2]
    return math.hypot(dx, dz), math.atan2(dz, dx), p[1] - c[1]


def _at(c, r, az, h):
    return [c[0] + r * math.cos(az), c[1] + h, c[2] + r * math.sin(az)]


def pose(ch, i):
    n = frames(ch)
    if "from" in ch:  # push from a camera: closer along the view line, lower, a small orbit about its target
        cam = CAMS[ch["from"]]; tgt = cam["target"]
        t = _ease(i / max(n - 1, 1), ch.get("ease"))
        r, az, h = _polar(cam["position"], tgt)
        k = 1 - ch["push"] * t
        return _at(tgt, r * k, az + math.radians(ch["orbit_deg"]) * t, h * k - ch["drop_m"] * t), list(tgt)
    cam = CAMS[ch["to"]]; tgt = cam["target"]  # orbit that ends on a camera
    m = n - ch.get("hold_frames", 0)
    t = _ease(min(i / max(m - 1, 1), 1.0), ch.get("ease"))
    r1, az1, h1 = _polar(cam["position"], tgt)
    r0, az0, h0 = ch["start_radius_m"], az1 - math.radians(ch["orbit_deg"]), ch["start_height_m"]
    if t >= 1.0: return list(cam["position"]), list(tgt)
    return _at(tgt, r0 + (r1 - r0) * t, az0 + (az1 - az0) * t, h0 + (h1 - h0) * t), list(tgt)


if __name__ == "__main__":
    for ch in SPEC["chapters"]:
        n = frames(ch); near = min(math.hypot(pose(ch, i)[0][0], pose(ch, i)[0][2]) for i in range(n))
        print(ch["id"], n, "frames, nearest horizontal distance to the pitch centre", round(near), "m")
        for i in list(range(0, n, 24)) + [n - 1]:
            p, t = pose(ch, i); print("  ", i, [round(x, 1) for x in p])
    end = pose(chapter("ch2_orbit"), frames(chapter("ch2_orbit")) - 1)[0]
    print("ch2 last frame equals L07:", end == CAMS["L07"]["position"])
