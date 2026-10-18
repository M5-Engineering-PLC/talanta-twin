"""Tier-section pass (cloud session 2026-10-18): fit each tier's tread and riser to the image rows of every seat row
in two square-on views of a long-side stand, from opposite sides and different heights.

Views (JWNowpO44rw, internal reference only): 000747.000 from the east upper tier, looking at the west stand
(camera high), and 002348.000 from the west VIP rows, looking at the east stand (camera low). Both stands are taken
to share one section. Row counts (hand counts at native resolution, rows.json) are fixed. For each tier, the dark
seat-back minima down one block-centre column give one image row per seat row.

Section, from the front row ring of the far stand (R horizontal, Y above the pad): lower tier from (0, Y0L) with
n_L rows of tread d_L and riser r_L; middle tier from the lower top + (dRm, dYm) with n_M rows (d_M, r_M); upper tier
from the middle top + (dRu, dYu) with n_U rows (d_U, r_U). Each seat back sits 0.6 tread behind and 0.8 m above its
nosing. Camera: horizontal distance to the far front ring = 2 rIn + Rc (Rc = depth into its own stand), height hc,
focal f (px), pitch tau. Image row = 360 - f tan(atan2(Y - hc, X) - tau). The measured plan depth (front ring to
back ring, blender/out/bowl_rings.json) is a soft limit on the upper tier's back (+-1.5 m).
Run: ~/.venvs/gis/bin/python gis/scripts/tier_section/tier_fit.py
"""
import json, math
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.optimize import least_squares
from scipy.signal import find_peaks

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / "rows.json").read_text())
G = json.loads((ROOT / "blender/out/bowl_rings.json").read_text())
i_e = int(round(math.radians(G["bearing"]) / (2 * math.pi) * G["N"])) % G["N"]
RIN, DEPTH = G["rIn"][i_e], G["rBack"][i_e] - G["rIn"][i_e]
TIERS = ["lower", "middle", "upper"]
N = {t: CFG["rows"][t]["n"] for t in TIERS}
TREAD, RISER = (0.7, 0.9), (0.3, 0.6)  # plausibility ranges (lead)


def rows_in(frame, x0, x1, y_top, y_front, n):
    """Image rows of the n seat-back minima between y_top (back row) and y_front (front row), back to front.
    Spurious splits (closer than 0.6 x the local spacing) are merged and single gaps (over 1.6 x) are filled."""
    im = np.asarray(Image.open(ROOT / f"research/frames/JWNowpO44rw/JWNowpO44rw_{frame}.jpg").convert("L")).astype(float)
    y0, y1 = int(y_top) - 2, int(y_front) + 3
    p = im[y0:y1, x0:x1].mean(1); yy = np.linspace(y0, y1 - 1, (y1 - y0) * 10); pp = np.interp(yy, np.arange(y0, y1), p)
    pk, _ = find_peaks(-pp, distance=15, prominence=1.0); v = list(yy[pk])
    v = [a for a in v if y_top - 1.5 <= a <= y_front + 1.5]
    for _ in range(3):
        if len(v) < 3: break
        d = np.diff(v); med = np.median(d); out = [v[0]]
        for k, a in enumerate(v[1:]):
            g = a - out[-1]
            if g < 0.6 * med: out[-1] = (out[-1] + a) / 2
            elif g > 1.6 * med:
                m_ = int(round(g / med)); out += [out[-1] + g * j / m_ for j in range(1, m_)] + [a]
            else: out.append(a)
        v = out
    return np.array(v)


VIEWS = CFG["views"]


def project(R, Y, cam):
    Rc, hc, f, tau = cam
    X = 2 * RIN + Rc - R  # the camera stands Rc into its own stand, across the pitch from the far front ring
    return 360 - f * np.tan(np.arctan2(Y - hc, X) - tau)


# Parameters: tread and riser per tier, the middle front offset from the lower top (dRm, dYm) and the upper front
# offset from the middle top (dRu, dYu); the lower front is the pitch wall at bowl.tier_lower.y0 (1.2 m). Camera B
# (002348.000) stands in the VIP rows: k_B rows below the lower top (0.5-4), eye 1.6 m above that tread. Camera A
# (000747.000) stands k_A rows into the upper tier (1-12), eye 1.6 m. One focal length f for both views (same tour
# camera), one pitch per view.
NAMES = ["tread_lower", "riser_lower", "tread_middle", "riser_middle", "tread_upper", "riser_upper", "dR_middle", "dY_middle",
         "dR_upper", "dY_upper", "k_A", "k_B", "f", "tau_A", "tau_B"]
X0 = [0.8, 0.45, 0.8, 0.5, 0.8, 0.45, 3.5, 5.0, 1.0, 3.0, 5.0, 2.0, 950, -0.15, 0.05]
LO = [0.3, 0.15, 0.3, 0.15, 0.3, 0.15, 0.5, 1.0, -8.0, 0.5, 1.0, 0.5, 300, -0.7, -0.4]
HI = [1.6, 1.0, 1.6, 1.0, 1.6, 1.0, 8.0, 12.0, 8.0, 10.0, 12.0, 4.0, 1800, 0.3, 0.5]
Y0L = float({r.split(",")[0]: r.split(",")[1] for r in (ROOT / "gis/parameter_ledger.csv").read_text().splitlines()}["bowl.tier_lower.y0"])


def tiers_of(x):
    dL, rL, dM, rM, dU, rU, dRm, dYm, dRu, dYu = x[:10]
    out, R, Y = {}, 0.0, Y0L
    for t, d, r, dR, dY in (("lower", dL, rL, 0, 0), ("middle", dM, rM, dRm, dYm), ("upper", dU, rU, dRu, dYu)):
        R, Y = R + dR, Y + dY; out[t] = (R, Y, d, r); R, Y = R + N[t] * d, Y + N[t] * r
    out["back"] = (R, Y)
    return out


def row_pts(tr, t):
    R, Y, d, r = tr[t]; k = np.arange(N[t]); return R + (k + 0.6) * d, Y + k * r + 0.8


def cameras(x):
    tr = tiers_of(x); kA, kB, f, tA, tB = x[10:15]
    R, Y, d, r = tr["upper"]; camA = (R + kA * d, Y + kA * r + 1.6, f, tA)
    R, Y, d, r = tr["lower"]; top = N["lower"]; camB = (R + (top - kB) * d, Y + (top - kB) * r + 1.6, f, tB)
    return {"000747.000": camA, "002348.000": camB}


def features(yrows):
    """Back row, front row, median spacing in the back and front thirds (px), from rows ordered back to front."""
    d = np.diff(yrows); k = max(2, len(d) // 3)
    return np.array([yrows[0], yrows[-1], np.median(d[:k]), np.median(d[-k:])])


def residuals(x, meas):
    tr = tiers_of(x); cs = cameras(x); res = []
    for v in VIEWS:
        for t in TIERS:
            R, Y = row_pts(tr, t); yp = project(R, Y, cs[v["frame"]])[::-1]
            fm = meas[v["frame"]][t]; fp = features(yp)
            res.append((fp - fm) * np.array([1, 1, 4, 4]))  # spacings weighted up: they are averages over many rows
    res.append([(tr["back"][0] - DEPTH) / 1.5 * 2.0])  # soft plan limit (+-1.5 m), px-equivalent
    return np.concatenate(res)


def measure(jitter=0.0, rng=None, col_shift=0):
    meas = {}
    for v in VIEWS:
        meas[v["frame"]] = {}
        for t in TIERS:
            w = v["tiers"][t]
            m = rows_in(v["frame"], w["x0"] + col_shift, w["x1"] + col_shift, w["y_top"], w["y_front"], N[t])
            fm = np.array([w["y_top"], w["y_front"], *features(m)[2:]], float)  # edges as read by hand
            if jitter: fm = fm + rng.normal(0, jitter, 4) * np.array([1, 1, 0.15, 0.15])
            meas[v["frame"]][t] = fm
    return meas


def fit(meas, x0=None):
    return least_squares(residuals, np.array(x0 or X0, float), bounds=(np.array(LO), np.array(HI)), args=(meas,), loss="soft_l1", f_scale=1.0, max_nfev=5000)


if __name__ == "__main__":
    meas = measure()
    for v in VIEWS:
        for t in TIERS: print(v["frame"], t, "back/front rows and spacings (px):", np.round(meas[v["frame"]][t], 2))
    # several starts; keep the best
    starts = [X0, [0.8, 0.4, 0.8, 0.5, 0.8, 0.4, 3, 6, 0, 3, 3, 1, 800, -0.2, 0.0], [0.8, 0.5, 0.8, 0.55, 0.8, 0.5, 4, 4, 2, 2, 8, 3, 1200, -0.1, 0.1]]
    fits = [fit(meas, s) for s in starts]; r = min(fits, key=lambda q: q.cost); x = r.x
    best = dict(zip(NAMES, map(float, x)))
    at_bound = [n for n, v, lo, hi in zip(NAMES, x, LO, HI) if min(v - lo, hi - v) < 1e-3 * (hi - lo)]
    print("costs", [round(q.cost, 1) for q in fits], "rms px %.2f" % np.sqrt(np.mean(r.fun[:-1] ** 2)), "at bound:", at_bound)
    print({k: round(v, 3) for k, v in best.items()})
    rng = np.random.default_rng(7); boots = []
    for b in range(30):
        rb = fit(measure(0.7, rng, int(rng.integers(-8, 9))), list(x)); boots.append(rb.x)
    boots = np.array(boots); p05, p95 = np.percentile(boots, 5, 0), np.percentile(boots, 95, 0)
    tr = tiers_of(x); tiers = {}
    for t in TIERS:
        R, Y, d, rr = tr[t]; i = TIERS.index(t)
        ok = TREAD[0] <= d <= TREAD[1] and RISER[0] <= rr <= RISER[1]
        tiers[t] = {"rows": N[t], "front_R": R, "front_Y": Y, "depth": N[t] * d, "rise": N[t] * rr, "tread": d, "riser": rr,
                    "tread_p05_p95": [float(p05[2 * i]), float(p95[2 * i])], "riser_p05_p95": [float(p05[2 * i + 1]), float(p95[2 * i + 1])], "plausible": bool(ok)}
        print("%-6s rows %2d tread %.2f [%.2f-%.2f] riser %.2f [%.2f-%.2f] depth %.1f rise %.1f front (R %.1f, Y %.1f) %s" % (
            t, N[t], d, p05[2 * i], p95[2 * i], rr, p05[2 * i + 1], p95[2 * i + 1], N[t] * d, N[t] * rr, R, Y, "ok" if ok else "REJECT"))
    print("upper back (R %.1f, Y %.1f); plan depth %.1f; cameras" % (*tr["back"], DEPTH), {k: tuple(round(c, 2) for c in v) for k, v in cameras(x).items()})
    out = {"rows": N, "fit": best, "at_bound": at_bound, "rms_px": float(np.sqrt(np.mean(r.fun[:-1] ** 2))), "costs": [float(q.cost) for q in fits],
           "p05": dict(zip(NAMES, map(float, p05))), "p95": dict(zip(NAMES, map(float, p95))), "tiers": tiers,
           "back": list(map(float, tr["back"])), "plan_depth": DEPTH, "rIn": RIN, "cameras": {k: list(map(float, v)) for k, v in cameras(x).items()},
           "measurements": {f: {t: list(map(float, m)) for t, m in d.items()} for f, d in meas.items()}}
    (HERE / "tier_fit_result.json").write_text(json.dumps(out, indent=1) + "\n")
