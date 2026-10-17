"""Stage 00: write app/cameras/manifest.json, the 16 frozen critic cameras C01-C16 (Astra review),
plus C17, the by-eye match of historian frame 07:04 for the G5 blind test (internal).

These are render viewpoints for review, not real camera locations (AGENTS.md rule 8).
Positions are in the app's local frame: x = east, y = up, z = south (metres, origin = W1b pitch
centre, y = 0 at the origin ground). The site pad is at y = site_pad_y. In Blender the same
point is (x, -z, y).
Run: ~/.venvs/gis/bin/python gis/scripts/build_camera_manifest.py
"""
import json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAN = json.loads((ROOT / "app/public/data/manifest.json").read_text())
PAD = MAN["features"]["site_pad_y"]
LAT, LON = MAN["origin_lonlat"][1], MAN["origin_lonlat"][0]


def pose(target, az, el, d):
    """Same convention as poseFrom() in main.js: az from north, clockwise; el above horizon."""
    a, e = math.radians(az), math.radians(el)
    tx, ty, tz = target
    return [round(tx + math.sin(a) * math.cos(e) * d, 2), round(ty + math.sin(e) * d, 2), round(tz - math.cos(a) * math.cos(e) * d, 2)], [tx, ty, tz]


NEUTRAL = {"date": "2026-01-15", "time_eat": "12:30", "kind": "neutral daylight"}
GOLDEN = {"date": "2026-01-15", "time_eat": "17:45", "kind": "golden hour"}
NIGHT = {"date": "2026-01-15", "time_eat": "20:30", "kind": "night, venue lights on"}
OVERCAST = {"date": "2026-01-15", "time_eat": "11:00", "kind": "overcast"}


def cam(cid, name, purpose, pos, target, lens=None, ortho=None, sun=NEUTRAL, variants=()):
    c = {"id": cid, "name": name, "purpose": purpose, "position": pos, "target": target, "up": [0, 1, 0]}
    if ortho:
        c["projection"] = "orthographic"; c["ortho_scale_m"] = ortho
    else:
        c["projection"] = "perspective"; c["focal_length_mm"] = lens
        c["vfov_deg"] = round(math.degrees(2 * math.atan(36 / 2 / lens * 9 / 16)), 3)
    c["sun"] = sun
    c["variants"] = list(variants)
    c["seed"] = int(cid[1:])
    return c


T0 = [0, PAD + 25, 0]
cams = []
for cid, nm, az in [("C01", "North elevation", 0), ("C02", "East elevation", 90), ("C03", "South elevation", 180), ("C04", "West elevation", 270)]:
    p, t = pose(T0, az, 0, 600)
    cams.append(cam(cid, nm, "geometry: silhouette and heights against the ledger", p, t, ortho=300))
p, t = pose([0, PAD, 0], 0, 89.999, 600)
cams.append(cam("C05", "Roof plan", "geometry: roof rings, plinth and pitch against the W1b shapes", p, t, ortho=480))
for cid, nm, az, var in [("C06", "Hero aerial, north-east", 40, ["golden", "night"]), ("C07", "Aerial, south-east", 135, []),
                         ("C08", "Aerial, south-west", 225, []), ("C09", "Aerial, north-west", 315, [])]:
    p, t = pose([-6, PAD + 16, 14], az, 14, 330)
    sun = GOLDEN if cid == "C06" else NEUTRAL
    purpose = "hero: dry golden-hour aerial looking south-west to the bowl and Ngong Hills" if cid == "C06" else "geometry and materials: elevated diagonal"
    cams.append(cam(cid, nm, purpose, p, t, lens=35, sun=sun, variants=var))
cams.append(cam("C10", "Across the bowl, long axis", "bowl: tiers, roof underside and opening, looking south", [0, PAD + 44, -112], [0, PAD + 8, 40], lens=24, variants=["golden", "night"]))
cams.append(cam("C11", "Across the bowl, short axis", "bowl: tiers and roof, looking east", [-86, PAD + 42, 0], [40, PAD + 10, 0], lens=24))
cams.append(cam("C12", "Seat section", "seats, rows and aisles of the west lower tier", [-32, PAD + 2.5, 6], [-70, PAD + 10, -4], lens=50))
cams.append(cam("C13", "Roof underside", "roof structure, membrane and ring beam from the pitch", [0, PAD + 2, 20], [-40, PAD + 45, -55], lens=24))
cams.append(cam("C14", "Facade and shield detail", "north shield, spears, lattice and louvres", [22, PAD + 20, -178], [-2, PAD + 26, -128], lens=50))
cams.append(cam("C15", "Forecourt and fountain", "north forecourt, plaza and fountain pool", [30, PAD + 17, -210], [0, PAD + 2, -160], lens=35, variants=["golden", "night"]))
p, t = pose([0, PAD + 25, 0], 28, 7, 950)
cams.append(cam("C16", "Approach and horizon", "approach from Ngong Road, skyline and Ngong Hills", p, t, lens=50))
# C17: composition of historian frame JWNowpO44rw 07:04, matched BY EYE (no camera solve; stage 01b found
# no identifiable ground-level W1b point). Drone over Ngong Road ENE of the stadium, about 100 m up,
# looking WSW; stadium 7.8 deg left of centre, horizon about 13.5 deg above centre, 24 mm on 36 mm.
# Internal: used for the G5 blind test only (AGENTS.md rule 2); the frame itself is never a texture.
cp = [756.3, -6.1 + 100, -601.1]
yaw, pitch = math.radians(231.5 + 7.8), math.radians(-13.5)
tgt = [round(cp[0] + math.sin(yaw) * math.cos(pitch) * 966, 2), round(cp[1] + math.sin(pitch) * 966, 2), round(cp[2] - math.cos(yaw) * math.cos(pitch) * 966, 2)]
cams.append(cam("C17", "07:04 match (by eye)", "G5 blind test: composition of JWNowpO44rw 07:04, overcast; internal only", cp, tgt, lens=24, sun=OVERCAST))

manifest = {
    "version": 1,
    "frozen": "2026-10-17",
    "note": "Render viewpoints for review only. Not real camera locations; do not publish as such (AGENTS.md rule 8).",
    "frame": {"x": "east", "y": "up", "z": "south", "units": "m", "origin_lonlat": [LON, LAT], "site_pad_y": PAD,
              "blender": "Blender (X, Y, Z) = (x, -z, y)"},
    "sensor_width_mm": 36,
    "resolution": [1920, 1080],
    "look_check_scale": 0.5,
    "exposure": {"view_transform": "AgX", "exposure_ev": 0.0, "exposure_ev_by_sun": {"golden": -1.0, "overcast": -1.3}, "f_stop": 8.0, "dof": False},
    "suns": {"neutral": NEUTRAL, "golden": GOLDEN, "night": NIGHT, "overcast": OVERCAST},
    "cycles": {"look_check": {"samples": 64, "adaptive": True, "denoiser": "OPENIMAGEDENOISE"},
               "hero": {"samples": 128, "adaptive": True, "denoiser": "OPENIMAGEDENOISE"}},
    "cameras": cams,
}
out = ROOT / "app/cameras/manifest.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(manifest, indent=1) + "\n")
print(out, len(cams), "cameras")
