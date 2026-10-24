"""Pass G (lead order 2026-10-22): small data files for the live twin's light shows and seated crowd.

Reads the built bowl (blender/out/step_FE.blend, or TALANTA_SITE_BLEND) and writes, in the app frame (the glTF frame
of the exported scene: x east, y up = Blender z, z south = -Blender y, metres, origin W1b pitch centre):
- app/public/data/facade_lines.json: the facade lattice ribs as centre-line polylines (24 rising + 24 falling members,
  read from the built lattice mesh), the fascia ring, the roof opening ring, the eight shields (centre, outward normal,
  width, height) and the floodlight heads on the catwalk ring near the opening (position and aim).
- app/public/data/seats.json: one record per seat place in the bowl build (regular and VIP seats), with the facing
  bearing, tier and row.
All values are estimated: they are the build's values (ledger rows bowl.*), not survey data.
Run from the repo root: ~/.venvs/bpy/bin/python blender/scripts/export_live_data.py
"""
import csv, json, math, os
from pathlib import Path
import numpy as np
import bpy

ROOT = Path(__file__).resolve().parents[2]
L = {r["name"]: r for r in csv.DictReader(open(ROOT / "gis/parameter_ledger.csv"))}
V = lambda k: float(L[k + "_blockout"]["value"]) if k + "_blockout" in L else float(L[k]["value"])
G = json.loads((ROOT / "blender/out/bowl_rings.json").read_text())
PAD = G["pad"]
bpy.ops.wm.open_mainfile(filepath=os.environ.get("TALANTA_SITE_BLEND", str(ROOT / "blender/out/step_FE.blend")))
FRAME = ("app frame = glTF frame of the exported scene: x east, y up (Blender z), z south (-Blender y), metres, "
         "origin W1b pitch centre; y is absolute height in the scene (the pitch pad is at y %.2f)" % PAD)


def app(p):
    return [round(float(p[0]), 2), round(float(p[2]), 2), round(float(-p[1]), 2)]


def verts(name):
    o = bpy.data.objects[name]; me = o.data
    a = np.zeros(len(me.vertices) * 3); me.vertices.foreach_get("co", a); a = a.reshape(-1, 3)
    M = np.array(o.matrix_world); return a @ M[:3, :3].T + M[:3, 3]


def islands(name):
    """Vertex arrays of the loose parts of a mesh object (world space)."""
    o = bpy.data.objects[name]; me = o.data; P = verts(name)
    parent = list(range(len(P)))
    def find(i):
        while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for e in me.edges:
        a, b = find(e.vertices[0]), find(e.vertices[1])
        if a != b: parent[a] = b
    groups = {}
    for i in range(len(P)): groups.setdefault(find(i), []).append(i)
    return [P[g] for g in groups.values()]


def ring_order(P):
    th = np.arctan2(-P[:, 1], P[:, 0]); return P[np.argsort(th)]  # app bearing order: angle 0 east, increasing to the south


# ---------------------------------------------------------------- facade lines
# lattice mesh layout (build_blockout.py rib()): per member 3 lines x 40 points x (front, back); centre line = line 1, front
LA = verts("lattice"); n = 40; per = 3 * n * 2
nm = len(LA) // per
ribs = [[app(LA[m * per + (1 * n + k) * 2]) for k in range(n)] for m in range(nm)]
rising = [r for i, r in enumerate(ribs) if i % 2 == 0]; falling = [r for i, r in enumerate(ribs) if i % 2 == 1]
fascia = [app(p) for p in ring_order(verts("night_fascia_points").reshape(-1, 8, 3).mean(axis=1))]
opening = [app(p) for p in ring_order(verts("night_opening_row").reshape(-1, 8, 3).mean(axis=1))]
shields = []
for S in islands("shields"):
    c = S.mean(axis=0); r = np.array([c[0], c[1], 0.0]); r /= np.linalg.norm(r)
    w = float(np.ptp(S @ np.array([-r[1], r[0], 0.0]))); h = float(np.ptp(S[:, 2]))
    shields.append({"center": app(c), "normal": [round(float(r[0]), 4), 0.0, round(float(-r[1]), 4)], "w": round(w, 2), "h": round(h, 2)})
shields.sort(key=lambda s: math.atan2(s["center"][2], s["center"][0]))
pitch_y = PAD
floods = []
for F in islands("floodlights"):
    c = F.mean(axis=0)
    aim = np.array([c[0] * 0.25, c[1] * 0.25, pitch_y]) - c  # head tilted down to the pitch: aim at a quarter radius (estimated)
    aim /= np.linalg.norm(aim)
    floods.append({"pos": app(c), "aim": [round(float(aim[0]), 4), round(float(aim[2]), 4), round(float(-aim[1]), 4)]})
floods.sort(key=lambda f: math.atan2(f["pos"][2], f["pos"][0]))
out = {"frame": FRAME,
       "claim": "estimated: the built bowl's geometry (ledger bowl.*), not survey data; floodlight aims are estimated (a quarter radius on the pitch)",
       "ribs_note": f"{len(rising)} rising + {len(falling)} falling lattice members, centre lines on the facade face, foot to top, 40 points each; rising first",
       "ribs": rising + falling, "fascia": fascia, "opening": opening, "shields": shields, "floodlights": floods}
D = ROOT / "app/public/data"; D.mkdir(parents=True, exist_ok=True)
(D / "facade_lines.json").write_text(json.dumps(out, separators=(",", ":")) + "\n")

# ---------------------------------------------------------------- seats
rows_y = {}
for tn in ("lower", "middle", "upper"):
    y0, y1, rows = V(f"bowl.tier_{tn}.y0"), V(f"bowl.tier_{tn}.y1"), int(V(f"bowl.tier_{tn}.rows"))
    rows_y[tn] = np.array([PAD + y0 + (y1 - y0) * k / rows for k in range(rows)])
ally = np.concatenate([rows_y[t] for t in rows_y]); allt = sum([[t] * len(rows_y[t]) for t in rows_y], [])
allr = sum([list(range(1, len(rows_y[t]) + 1)) for t in rows_y], [])
seats, miss = [], 0
for name, kind in (("seats", None), ("vip_seats", "vip")):
    me = bpy.data.objects[name].data; P = verts(name)
    rot = np.zeros(len(P) * 3); me.attributes["rot"].data.foreach_get("vector", rot); rot = rot.reshape(-1, 3)
    for p, rr in zip(P, rot):
        j = int(np.argmin(np.abs(ally - p[2])))
        if abs(ally[j] - p[2]) > 0.05: miss += 1
        # seat front is +Y of the prototype turned by rot.z: facing = (-sin, cos) in Blender x, y
        fx, fy = -math.sin(rr[2]), math.cos(rr[2])
        facing = math.degrees(math.atan2(fx, fy)) % 360  # compass bearing the seated person faces (0 north, 90 east)
        a = app(p)
        seats.append({"x": a[0], "y": a[1], "z": a[2], "facing_deg": round(facing, 1), "tier": kind or allt[j], "row": allr[j]})
(D / "seats.json").write_text(json.dumps(seats, separators=(",", ":")) + "\n")
cnt = {}
for s_ in seats: cnt[s_["tier"]] = cnt.get(s_["tier"], 0) + 1
print("EXPORT", json.dumps({"ribs": [len(rising), len(falling)], "fascia": len(fascia), "opening": len(opening), "shields": len(shields),
                            "floodlights": len(floods), "seats": len(seats), "by_tier": cnt, "row_mismatch": miss,
                            "kb": [round((D / f).stat().st_size / 1024) for f in ("facade_lines.json", "seats.json")]}))
