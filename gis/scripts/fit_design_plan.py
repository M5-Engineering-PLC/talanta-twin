"""Design plan of the bowl: concentric, symmetric superellipses fitted to the W1b traces.

The W1b plinth and roof rings are hand traces on an oblique image. They wobble by up to 6 m and
are not symmetric, so the shell built straight from them looks lumpy. The architects' plan is
symmetric about both pitch axes. This script fits one superellipse to each ring,
  r(phi) = (|cos phi / a|^n + |sin phi / b|^n)^(-1/n),  phi measured from the pitch cross axis,
centred on the pitch centre (twin origin) and aligned to pitch.bearing, by least squares on the
radial residual. The roof rings are relief-corrected first (roof.relief_shift_*). Writes
  gis/measurements/normalized/bowl_<ring>_design_2026-10-17.csv  (vertex, x_east, z_south)
  gis/measurements/normalized/bowl_design_plan_2026-10-17.json    (fit values, read by the ledger)
Run with ~/.venvs/gis/bin/python gis/scripts/fit_design_plan.py, then rebuild the ledger.
"""
import csv, json, math
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[2]
NORM = ROOT / "gis/measurements/normalized"
L = {r["name"]: r for r in csv.DictReader(open(ROOT / "gis/parameter_ledger.csv"))}
b = math.radians(float(L["pitch.bearing"]["value"]))
sx, sz = float(L["roof.relief_shift_x"]["value"]), float(L["roof.relief_shift_z"]["value"])
RINGS = [("plinth", "bowl_plinth_w1b_2026-10-17.csv", (0.0, 0.0)),
         ("roof_outer", "roof_outer_w1b_2026-10-17.csv", (sx, sz)),
         ("roof_inner", "roof_inner_w1b_2026-10-17.csv", (sx, sz))]


def se(phi, a, bb, n):
    return (np.abs(np.cos(phi) / a) ** n + np.abs(np.sin(phi) / bb) ** n) ** (-1 / n)


def densify(pts, step=1.0):
    out = []
    for (ax, az), (bx, bz) in zip(pts, pts[1:] + pts[:1]):
        k = max(1, int(math.hypot(bx - ax, bz - az) / step))
        out += [(ax + (bx - ax) * t / k, az + (bz - az) * t / k) for t in range(k)]
    return np.array(out)


res = {"method": "concentric superellipse about the pitch centre, axes on pitch.bearing, least squares on radius",
       "bearing_deg": math.degrees(b), "rings": {}}
for name, fn, (dx, dz) in RINGS:
    p = densify([(float(r["x_east"]) - dx, float(r["z_south"]) - dz) for r in csv.DictReader(open(NORM / fn))])
    rr, ph = np.hypot(p[:, 0], p[:, 1]), np.arctan2(p[:, 1], p[:, 0]) - b
    fit = least_squares(lambda q: rr - se(ph, *q), [100.0, 120.0, 3.0]).x
    d = rr - se(ph, *fit)
    a, bb, n = (round(float(v), 2) for v in fit)
    res["rings"][name] = {"a_cross": a, "b_long": bb, "n": n, "rms_m": round(float(np.sqrt(np.mean(d ** 2))), 2),
                          "max_m": round(float(np.abs(d).max()), 2), "source": fn}
    t = np.linspace(0, 2 * math.pi, 361)[:-1]; r = se(t, a, bb, n)
    with open(NORM / f"bowl_{name}_design_2026-10-17.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["vertex", "x_east", "z_south"])
        for k, (tt, q) in enumerate(zip(t, r)):
            w.writerow([k + 1, round(q * math.cos(tt + b), 3), round(q * math.sin(tt + b), 3)])
    print(name, res["rings"][name])
(NORM / "bowl_design_plan_2026-10-17.json").write_text(json.dumps(res, indent=1) + "\n")
