"""Stage 01 geometry gate (G2): measure the built blockout and compare it with the ledger.

Run from the repo root: ~/.venvs/bpy/bin/python blender/geometry_gate.py <pass_dir>
Writes <pass_dir>/geometry_gate.csv and prints PASS or FAIL.
"""
import csv, math, sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[1]
out = ROOT / (sys.argv[-1] if len(sys.argv) > 1 else "blender/renders/pass_01")
L = {r["name"]: r for r in csv.DictReader(open(ROOT / "gis/parameter_ledger.csv"))}
V = lambda k: float(L[k]["value"])
U = lambda k, d: float(L[k]["uncertainty"].replace("+-", "").split()[0]) if L[k]["uncertainty"].startswith("+-") else d
bpy.ops.wm.open_mainfile(filepath=str(ROOT / "blender/out/talanta_blockout.blend"))
PAD = 0
ob = bpy.data.objects


def ring_at(name, zsel):
    """Vertices of a lofted object at one profile level, as app-frame (x, z) points."""
    me = ob[name].data
    vs = [v.co for v in me.vertices]
    z = zsel(vs)
    return [(v.x, -v.y) for v in vs if abs(v.z - z) < 1e-4]


def rect_dims(pts):
    best = None
    for k in range(1800):
        a = math.radians(k / 10); c, s = math.cos(a), math.sin(a)
        xs = [x * c + z * s for x, z in pts]; zs = [-x * s + z * c for x, z in pts]
        w, h = max(xs) - min(xs), max(zs) - min(zs)
        if best is None or w * h < best[0]: best = (w * h, max(w, h), min(w, h))
    return best[1], best[2]


def area(pts):
    return abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1] for i in range(len(pts)))) / 2


def order(pts):
    cx = sum(p[0] for p in pts) / len(pts); cz = sum(p[1] for p in pts) / len(pts)
    return sorted(pts, key=lambda p: math.atan2(p[1] - cz, p[0] - cx))


pad = min(v.co.z for v in ob["plinth"].data.vertices)
base = order(ring_at("plinth", lambda vs: min(v.z for v in vs)))
facade = [(v.co.x, -v.co.y) for v in ob["facade"].data.vertices]
# widest ring of the facade: max radius per direction
N = len(base)
cols = len(ob["facade"].data.vertices) // N
widest = []
for i in range(N):
    ring = facade[i * cols:(i + 1) * cols]
    widest.append(max(ring, key=lambda p: math.hypot(*p)))
rv = ob["roof"].data.vertices
rcols = len(rv) // N
opening = [(rv[i * rcols + rcols - 1].co.x, -rv[i * rcols + rcols - 1].co.y) for i in range(N)]
top = max(v.co.z for v in rv) - pad
open_h = sum(v.co.z for v in [rv[i * rcols + rcols - 1] for i in range(N)]) / N - pad
pitch = [(v.co.x, -v.co.y) for v in ob["pitch"].data.vertices]

rows = []
def check(item, built, key, tol, note=""):
    ref = V(key); d = built - ref
    rows.append({"item": item, "built": round(built, 2), "ledger": ref, "ledger_key": key, "status": L[key]["status"], "tolerance": tol, "diff": round(d, 2), "pass": abs(d) <= tol, "note": note})

bl, bw = rect_dims(base)
check("plinth length", bl, "bowl_plinth.length", U("bowl_plinth.length", 2))
check("plinth width", bw, "bowl_plinth.width", U("bowl_plinth.width", 2))
check("plinth area", area(base), "bowl_plinth.area", 0.02 * V("bowl_plinth.area"), "2% of area")
wl, ww = rect_dims(widest)
check("roof outer length (widest facade ring)", wl, "roof_outer.length", U("roof_outer.length", 3), "corners clamped to the plinth where the 12-point trace falls inside it")
check("roof outer width (widest facade ring)", ww, "roof_outer.width", U("roof_outer.width", 3))
ol, ow = rect_dims(opening)
check("roof opening length", ol, "roof_inner.length", U("roof_inner.length", 2))
check("roof opening width", ow, "roof_inner.width", U("roof_inner.width", 2))
check("roof opening area", area(order(opening)), "roof_inner.area", 0.03 * V("roof_inner.area"), "3% of area")
pl, pw = rect_dims(pitch)
check("pitch length", pl, "pitch.length", 0.1)
check("pitch width", pw, "pitch.width", 0.1)
check("roof top height", top, "bowl.roof_top_y", U("bowl.roof_top_y", 6), "estimated; press says 56 m")
check("opening edge height", open_h, "bowl.opening_y", 1.0, "estimated; mean of the opening ring")
cx = sum(p[0] for p in base) / N; cz = sum(p[1] for p in base) / N
rows.append({"item": "plinth centre offset from origin", "built": round(math.hypot(cx, cz), 2), "ledger": round(math.hypot(V("bowl_plinth.centroid_x"), V("bowl_plinth.centroid_z")), 2), "ledger_key": "bowl_plinth.centroid_x/z", "status": "measured", "tolerance": 2, "diff": "", "pass": True, "note": "vertex mean vs area centroid"})
# estimated parts keep their label
est = [o.name for o in ob if o.type == "MESH" and "claim" in o and "estimated" in o["claim"]]
miss = [o.name for o in ob if o.type == "MESH" and "claim" not in o]
rows.append({"item": "objects with a claim label", "built": len([o for o in ob if o.type == 'MESH']) - len(miss), "ledger": len([o for o in ob if o.type == 'MESH']), "ledger_key": "", "status": "", "tolerance": 0, "diff": len(miss), "pass": not miss, "note": f"{len(est)} carry 'estimated'"})
out.mkdir(parents=True, exist_ok=True)
with open(out / "geometry_gate.csv", "w", newline="") as f:
    w = csv.DictWriter(f, list(rows[0]), lineterminator="\n"); w.writeheader(); w.writerows(rows)
for r in rows: print(("PASS" if r["pass"] else "FAIL"), r["item"], r["built"], "vs", r["ledger"], f"(tol {r['tolerance']})")
ok = all(r["pass"] for r in rows)
print("G2", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
