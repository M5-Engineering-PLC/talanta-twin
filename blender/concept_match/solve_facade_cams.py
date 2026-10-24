"""Facade fix 2026-10-20: cameras matched to JWNowpO44rw 001216.000 (close, sunlit) and 001232.600 (aerial, shade).

Landmarks are read by eye from the frames (internal, about +-6 px at 1920 wide, +-4 px at 1280 wide): the top V points
of the lattice under the fascia and the bottom points on the ring beam. For 001232.600 the six V points lie on one curve and leave
the camera height free (a V-point-only fit put the roof opening far too low), so points on the outer edge of the
roof-opening trim are fitted too (nearest-point distance); the output gives the residual of each set. Their 3D positions come from the built model (blender/out/bowl_rings.json, the lattice bays of
build_blockout.py: equal arc length round the fascia line, the first on the shield 0 axis). For each frame the solver
tries every shield as the centre one and both directions round the bowl, and fits a pinhole camera (position, yaw,
pitch, roll, focal length) by least squares. The stadium is close to symmetric under a half turn, so two shields fit
about as well; the pick is stated per frame ("pick": by fit, light and background), and the output lists the best candidates.
Writes cameras F16 and F32 into blender/data/interior_cameras.json (the extra camera file render_cycles.py reads).
Run: ~/.venvs/gis/bin/python blender/concept_match/solve_facade_cams.py
"""
import csv, json, math
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[2]
R = json.loads((ROOT / "blender/out/bowl_rings.json").read_text())
N, PAD, PROF = R["N"], R["pad"], np.array(R["prof"])  # PROF[i][j] = (r, y)
NP, J_F = PROF.shape[1], R["j_fascia"]
L = {r["name"]: r for r in csv.DictReader(open(ROOT / "gis/parameter_ledger.csv"))}
V = lambda k: float(L[k + "_blockout"]["value"]) if k + "_blockout" in L else float(L[k]["value"])
K, NSH = int(V("bowl.profile.lattice_members_704")), int(V("bowl.shields.count"))
plinthH, ld = V("bowl.plinth_h"), V("bowl.lattice.section_d")
Y_LO, Y_TOP = plinthH, PROF[0][J_F][1]
TH0 = math.radians(-R["bearing"]) - math.pi / 2


def j_at(y):
    p = PROF[0]
    if y < p[2][1]: return 2 + (y - p[2][1]) / (p[3][1] - p[2][1])
    for j in range(2, R["j_facade"]):
        if p[j][1] <= y <= p[j + 1][1]: return j + (y - p[j][1]) / (p[j + 1][1] - p[j][1])
    return R["j_facade"]


def surf(th, jf, off=0.0):
    """App-frame point (x east, y up incl. the pad, z south), as build_blockout.surf."""
    fi = (th / (2 * math.pi)) % 1 * N; i0 = int(fi) % N; i1 = (i0 + 1) % N; fi -= int(fi)
    j0 = min(max(int(math.floor(jf)), 2), NP - 2); fj = jf - j0
    rp = lambda i: PROF[i][j0] * (1 - fj) + PROF[i][j0 + 1] * fj
    a, b = rp(i0), rp(i1); r = a[0] * (1 - fi) + b[0] * fi + off; y = a[1] * (1 - fi) + b[1] * fi
    return np.array([math.cos(th) * r, y + PAD, math.sin(th) * r])


_th = TH0 + np.linspace(0, 2 * math.pi, 4801)
_q = np.array([surf(t, j_at(Y_TOP)) for t in _th])
_cum = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(_q, axis=0), axis=1))]); _u = K * _cum / _cum[-1]
th_u = lambda u: TH0 + float(np.interp(u % K, _u, _th - TH0))
top = lambda u: surf(th_u(u), j_at(Y_TOP), ld)
bot = lambda u: surf(th_u(u), j_at(Y_LO), ld)
OPEN = np.array([[math.cos(2 * math.pi * i / N) * R["rRi"][i], PROF[i][-1][1] + PAD, math.sin(2 * math.pi * i / N) * R["rRi"][i]] for i in range(N)])

# frame landmarks (px): (kind, offset in bays from the centre shield, x, y)
FRAMES = {
    "F16": {"frame": "001216.000", "size": (1920, 1080), "near": (-125.0, 25.7 + PAD, 141.3), "near_from": "001212.500",
            "pts": [("top", -1, 178, 88), ("top", 0, 760, 42), ("top", 1, 1378, 85), ("top", 2, 1715, 168),
                    ("bot", -1, 235, 962), ("bot", 0, 770, 1000), ("bot", 1, 1330, 965)], "open": [],
            "pick": (3, -1, "best fit (shield 3 or its half-turn twin 7, 12.7 px); the frame is sunlit and under the 12:30 "
                            "January sun only the south-east twin (shield 3) is in sun; the drone position solved for "
                            "001212.500 pointed at shield 5, which fits worse (19 px)")},
    "F32": {"frame": "001232.600", "size": (1280, 720), "near": (-143.0, 21.2 + PAD, -75.8), "near_from": "001230.050",
            "pts": [("top", -3, 172, 462), ("top", -2, 290, 498), ("top", -1, 470, 545), ("top", 0, 718, 553),
                    ("top", 1, 932, 518), ("top", 2, 1040, 476)],
            "open": [(358, 285), (420, 262), (520, 240), (620, 224), (760, 228), (880, 240), (915, 258), (870, 290),
                     (760, 325), (650, 347), (520, 330), (420, 305)], "pick": (1, -1, "the frame looks across the bowl into the Ngong Road forest (south-west of the site), so the "
                                   "camera is on the north-east side; the half-turn twin (shield 5) would look at the city")},
}


def basis(yaw, pitch, roll):
    fwd = np.array([math.cos(pitch) * math.cos(yaw), math.sin(pitch), math.cos(pitch) * math.sin(yaw)])
    right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right); up = np.cross(right, fwd)
    cr, sr = math.cos(roll), math.sin(roll)
    return fwd, cr * right + sr * up, -sr * right + cr * up


def project(P, x, size):
    C, (yaw, pitch, roll, f) = x[:3], x[3:]
    fwd, right, up = basis(yaw, pitch, roll); d = P - C
    z = d @ fwd; return np.stack([size[0] / 2 + f * (d @ right) / z, size[1] / 2 - f * (d @ up) / z], -1), z


def solve(spec, shield, sgn):
    c = shield * (K // NSH)
    P = np.array([(top if kind == "top" else bot)(c + sgn * o) for kind, o, _, _ in spec["pts"]])
    uv = np.array([(x, y) for *_, x, y in spec["pts"]], float); W, H = spec["size"]
    op = np.array(spec["open"], float)
    centre = np.array(top(c)); nrm = centre[[0, 2]] / np.linalg.norm(centre[[0, 2]])

    def res(x):
        p, z = project(P, x, spec["size"]); r = list((p - uv).ravel())
        if len(op):
            q, zq = project(OPEN, x, spec["size"]); dd = np.linalg.norm(op[:, None] - q[None], axis=2).min(1); r += list(dd * 0.7)
        r += list(np.minimum(z - 5, 0) * 100) + [min(x[1] - PAD - 5, 0) * 100]  # in front of the camera; camera above ground
        return np.array(r)
    best = None
    for dist in (60, 150, 250, 400):
        for el in (0.1, 0.4, 0.7):
            for f0 in (0.55, 0.85, 1.4):
                C0 = np.array([centre[0] + nrm[0] * dist * math.cos(el), centre[1] + dist * math.sin(el), centre[2] + nrm[1] * dist * math.cos(el)])
                d = np.array([0, 25 + PAD, 0]) - C0; yaw = math.atan2(d[2], d[0]); pitch = math.atan2(d[1], math.hypot(d[0], d[2]))
                x0 = np.array([*C0, yaw, pitch, 0.0, f0 * W])
                try: r = least_squares(res, x0, max_nfev=800, loss="soft_l1" if len(op) else "linear", f_scale=10)
                except Exception: continue
                if best is None or r.cost < best.cost: best = r
    p, _ = project(P, best.x, spec["size"])
    rms = float(np.sqrt(((p - uv) ** 2).sum(1).mean()))
    if len(op):
        q, _ = project(OPEN, best.x, spec["size"]); spec.setdefault("_open_med", {})[(shield, sgn)] = float(np.median(np.linalg.norm(op[:, None] - q[None], axis=2).min(1)))
    return best, rms


out = {}
for cid, spec in FRAMES.items():
    cands = []
    for k in range(NSH):
        for sgn in (1, -1):
            r, rms = solve(spec, k, sgn); cands.append((rms, k, sgn, r.x)); print(cid, k, sgn, round(rms, 1), flush=True)
    cands.sort(key=lambda c: c[0])
    good = [c for c in cands if c[0] <= cands[0][0] * 1.5 + 2]
    pick = min(good, key=lambda c: np.linalg.norm(c[3][:3] - np.array(spec["near"])))
    if "pick" in spec: pick = next(c for c in cands if (c[1], c[2]) == spec["pick"][:2])
    rms, k, sgn, x = pick
    fwd, right, up = basis(*x[3:6]); W, H = spec["size"]
    out[cid] = {"frame": spec["frame"], "shield": k, "direction": sgn, "rms_px": round(rms, 2), "position": [round(float(v), 2) for v in x[:3]],
                "target": [round(float(v), 2) for v in x[:3] + fwd * 100], "roll_deg": round(math.degrees(x[5]), 3),
                "focal_px": round(float(x[6]), 1), "opening_median_px": round(spec.get("_open_med", {}).get((k, sgn), float("nan")), 1), "focal_length_mm": round(float(x[6]) * 36 / W, 2),
                "candidates": [{"shield": c[1], "dir": c[2], "rms_px": round(c[0], 2), "position": [round(float(v), 1) for v in c[3][:3]]} for c in cands[:6]],
                "picked_by": spec["pick"][2] if "pick" in spec else f"nearest to the solved drone position of {spec['near_from']} among fits within 1.5x of the best"}
    print(cid, json.dumps({k_: v for k_, v in out[cid].items() if k_ != "candidates"}), flush=True)
    for c in out[cid]["candidates"]: print("   ", c)

ic = ROOT / "blender/data/interior_cameras.json"; d = json.loads(ic.read_text())
d["cameras"] = [c for c in d["cameras"] if c["id"] not in FRAMES]
for cid, o in out.items():
    d["cameras"].append({"id": cid, "purpose": f"facade fix check against frame JWNowpO44rw {o['frame']} (camera solved from lattice landmarks, "
                         f"rms {o['rms_px']} px); internal only", "projection": "perspective", "focal_length_mm": o["focal_length_mm"],
                         "position": o["position"], "target": o["target"], "roll_deg": o["roll_deg"], "seed": 1,
                         "sun": {"date": "2026-01-15", "time_eat": "10:30", "kind": "daylight"}})
ic.write_text(json.dumps(d, indent=1) + "\n")
(ROOT / "blender/renders/facade_fix_01").mkdir(parents=True, exist_ok=True)
(ROOT / "blender/renders/facade_fix_01/facade_cameras.json").write_text(json.dumps(out, indent=1) + "\n")
