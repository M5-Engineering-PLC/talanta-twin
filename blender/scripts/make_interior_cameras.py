"""Interior pass cameras C30-C35 (detail sheet 05), matched by eye to the tour frames, written to
blender/data/interior_cameras.json in the app manifest's camera format (the app manifest is the lead's; these stay
in blender/data until the lead copies them). Each pose is set in bowl terms (direction round the bowl, tier
fraction, height above the pad) and converted with the rings in blender/out/bowl_rings.json.
Anchors: the tier breaks, the concourse and box band, the roof edge, and the pitch edge (C30). No pitch lines are
visible in five of the six frames, so these are by-eye matches, not solved cameras.
Run: python3 blender/scripts/make_interior_cameras.py
"""
import json, math
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
G = json.loads((ROOT / "blender/out/bowl_rings.json").read_text()); N, PAD = G["N"], G["pad"]
import csv
LG = {r["name"]: r for r in csv.DictReader(open(ROOT / "gis/parameter_ledger.csv"))}
T0U = float(LG.get("bowl.tier_upper.t0_blockout", LG["bowl.tier_upper.t0"])["value"])  # seat count pass 01 moved the upper front


def roof_ring(theta_deg, dr, h):
    """App-frame point dr m outside the roof inner ring (opening edge) at direction theta, h m above the pad."""
    th = math.radians(theta_deg) % (2 * math.pi); i = int(round(th / (2 * math.pi) * N)) % N
    r = G["rRi"][i] + dr; return [round(math.cos(th) * r, 2), round(h + PAD, 2), round(math.sin(th) * r, 2)]


def ring(theta_deg, t, h, dr=0.0):
    """App-frame point at direction theta (deg from east towards south), tier fraction t, h m above the pad."""
    th = math.radians(theta_deg) % (2 * math.pi); i = int(round(th / (2 * math.pi) * N)) % N
    r = G["rIn"][i] + (G["rBack"][i] - G["rIn"][i]) * t + dr
    return [round(math.cos(th) * r, 2), round(h + PAD, 2), round(math.sin(th) * r, 2)]


CAMS = [  # id, frame, purpose, position, target, focal mm, roll deg
    ("C30", "000945.200", "pitch level near the west touchline, across to the east stand",   # pass 2: 1.6 m eye height,
     [-30.0, PAD + 1.6, 6.0], [80.0, PAD + 1.6 - 110.0 * math.tan(math.radians(7.6)), 6.0], 26, 0.0),  # horizon at y 237/720
    ("C31", "002144.300", "west concourse at the top of the lower tier, along the concourse, bowl on the left",
     ring(150, 0.415, 12.5 + 1.6), ring(115, 0.40, 12.5 + 1.0), 24, 0.0),   # pass 2: out of the VIP lounge arc (west centre)
    ("C32", "000735.433", "east concourse by a column, across the bowl to the west stand",
     ring(5, 0.53, 12.5 + 1.6), ring(178, 0.55, 22.0), 24, 0.0),   # pass 2: under the middle-tier soffit (t 0.45-0.62)
    ("C33", "000154.067", "east upper tier back, looking up at the catwalk ring and the roof lattice",
     ring(10, 0.9, 42.5 + 1.6), roof_ring(32, 4.0, 47.0), 30, -12.0),
    ("C34", "002320.200", "north end, upper tier front walkway behind the glass balustrade, across the bowl",
     ring(265, T0U + 0.015, 33.0 + 1.6), ring(195, 0.6, 33.0), 22, 0.0),   # 0.715 before seat count pass 01
    ("C35", "000131.700", "east upper gallery behind the top row, along the gallery, bowl on the right",
     ring(0, 1.0, 44.3 + 1.6, dr=0.5), ring(40, 0.98, 41.0), 22, 0.0),   # pass 2: near the rail, off the colonnade
]
out = {"note": "Interior pass cameras (detail sheet 05). Render viewpoints for review only; not real camera locations (AGENTS.md rule 8).",
       "cameras": [{"id": c, "name": f"Interior {fr}", "purpose": f"match tour frame JWNowpO44rw {fr}: {pur}; internal only",
                    "frame": f"research/frames/JWNowpO44rw/JWNowpO44rw_{fr}.jpg", "position": pos, "target": tgt, "up": [0, 1, 0],
                    "projection": "perspective", "focal_length_mm": f, "roll_deg": roll, "dof": False,
                    "exposure_ev": 1.0, "exposure_note": "the tour frames are hand-held with auto exposure",
                    "sun": {"date": "2026-01-15", "time_eat": "12:30", "kind": "neutral daylight"}, "variants": [], "seed": 30 + k}
                   for k, (c, fr, pur, pos, tgt, f, roll) in enumerate(CAMS)]}
(ROOT / "blender/data/interior_cameras.json").write_text(json.dumps(out, indent=1) + "\n")
print("\n".join(f"{c['id']} {c['position']} -> {c['target']} {c['focal_length_mm']} mm" for c in out["cameras"]))
