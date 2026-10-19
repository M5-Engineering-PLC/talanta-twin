"""Geometry pass 4: convex wall (bulge >= 0, locked by Munene 2026-10-19).

Refits only the wall bulge and the shoulder radii Rh, Rv. The crest stays at roof_top_y 54 m (yW = 54 - Rv); the
other profile values stay at the build values (foot inset 0.66, opening 50, sag 1.5, shield centre 27.92, ring kept).
Frames: the 8 frames of passes 2 and 3, plus three edge-on frames whose right limb shows the wall in profile
(001212.500, 001227.500, 001230.050). The edge-on frames have no mask: their silhouette term is the hand-read limb
(lines_edge.json) against the projected outline; J, F and the shield as in lines.json. They share one lens ("close").

Two anchors of the barrel against the measured roof outer ring rRo (W1b, seen from above):
  top     the build formula: the wall top (junction) on rRo, the bulge outside it
  widest  the widest ring of the barrel on rRo: the junction and the foot sit "bulge" inside it
Rule (fit2.acceptance): accept only if max(basin spread, leave-one-out spread) < 2 m and no value at a bound.
Run: ~/.venvs/gis/bin/python fit4_convex.py <work> <top|widest>
"""
import json, math, os, sys, time
import numpy as np
from scipy import ndimage as nd
import model as m
import fit2 as f2

HERE = os.path.dirname(os.path.abspath(__file__))
EDGE = {k: v for k, v in json.load(open(os.path.join(HERE, "lines_edge.json"))).items() if not k.startswith("_")}
BUILD = dict(openY=50.0, sag=1.5, dF=0.66, hs=27.92, dRi=0.0, yFoot=6.0)
CREST = 54.0
FIT_KEYS = ["bulge", "Rh", "Rv"]
FIT_LO = np.array([0.0, 0.5, 0.5]); FIT_HI = np.array([8.0, 20.0, 15.0])
STARTS = [[0.5, 3.0, 3.0], [2.5, 8.0, 6.0], [5.0, 12.0, 9.0]]
ANCHOR = sys.argv[2] if len(sys.argv) > 2 else "top"
TAG = f"pass4_{ANCHOR}"


def inset(p):  # how far the junction and the barrel ends sit inside rRo
    return max(p["bulge"], 0.0) if ANCHOR == "widest" else 0.0


# ---- model with the anchor (replaces model.shell and model.wall_r; same rows as model.shell)
def shell(p, nw=10, ns=10, nr=8):
    yW, Rh, Rv, openY, sag, bulge, yF = p["yW"], p["Rh"], p["Rv"], p["openY"], p["sag"], p["bulge"], p["yFoot"]
    rT = m.rRo - inset(p); r0 = rT - p["dF"]
    rows = []
    for k in range(nw + 1):
        f = k / nw; rows.append((r0 + (rT - r0) * f + bulge * math.sin(math.pi * f), np.full(m.N, yF + (yW - yF) * f)))
    for k in range(1, ns + 1):
        a = k / ns * math.pi / 2; rows.append((rT - Rh * (1 - math.cos(a)), np.full(m.N, yW + Rv * math.sin(a))))
    rc = rT - Rh; top = yW + Rv
    for k in range(1, nr + 1):
        t = k / nr; rows.append((rc + (m.rRi - rc) * t, np.full(m.N, top + (openY - top) * t - sag * math.sin(t * math.pi))))
    R = np.stack([r for r, _ in rows], 1); Y = np.stack([y for _, y in rows], 1)
    return np.stack([m.DX[:, None] * R, Y, m.DZ[:, None] * R], -1)


def wall_r(p, th, y):
    i = (np.round(th / (2 * np.pi) * m.N).astype(int)) % m.N
    rT = m.rRo[i] - inset(p); r0 = rT - p["dF"]
    f = np.clip((y - p["yFoot"]) / (p["yW"] - p["yFoot"]), 0, 1)
    return r0 + (rT - r0) * f + p["bulge"] * np.sin(np.pi * f)


m.shell, m.wall_r = shell, wall_r


def prof(x):
    p = dict(m.CUR); p.update(BUILD); p.update(dict(zip(FIT_KEYS, map(float, x)))); p["yW"] = CREST - p["Rv"]; return p


f2.KEYS, f2.LO, f2.HI, f2.prof = FIT_KEYS, FIT_LO, FIT_HI, prof
_res = f2._residuals


def _residuals(fr, p, cam, w_sil, w_line, w_sh):
    # the junction and foot rings follow the anchor: shift rRo used by fit2 for this call
    d = inset(p)
    if d:
        f2.RRO = RRO0 - d
        try: return _res(fr, p, cam, w_sil, w_line, w_sh)
        finally: f2.RRO = RRO0
    return _res(fr, p, cam, w_sil, w_line, w_sh)


RRO0 = f2.RRO.copy(); f2._residuals = _residuals


class EdgeFrame(f2.Frame):
    """Edge-on frame: hand-read limb (sky against the wall and roof edge) instead of a mask."""
    def __init__(self, f):
        self.f = f; L = EDGE[f]
        limb = np.array(L["limb"], float)
        t = np.linspace(0, 1, 30)[:, None]  # densify the limb polyline for the edge term
        pts = np.vstack([a + (b - a) * t for a, b in zip(limb[:-1], limb[1:])])
        self.edge = pts[np.linspace(0, len(pts) - 1, 220).astype(int)]
        self.dt = np.zeros((f2.H, f2.W))     # no outline-to-mask term: the rest of the outline is out of frame
        self.w_px, self.h_px, self.cropped_x = f2.W, f2.H, True
        self.oedge = None; self.oext = None
        self.J = np.array(L["J"], float); self.F = np.array(L["F"], float).reshape(-1, 2); self.S = np.array(L["S"], float)
        self.k = None


def init_edge_camera(fr, p):
    """Grid over the shield the frame faces, view offset, elevation, distance and focal length, then polish."""
    from scipy.optimize import least_squares
    cands = []
    for k in range(8):
        th0 = math.radians(-1.76 - 90 + 45 * k)
        for dth in (-20, -10, 0, 10, 20):
            th = th0 + math.radians(dth); rr = float(wall_r(p, np.array([th]), np.array([28.0]))[0])
            tgt = np.array([math.cos(th) * rr, 28.0, math.sin(th) * rr])
            for daz in (-40, -20, 0, 20, 40):
                for el in (2, 10, 18):
                    for d in (60, 110, 180):
                        for fpx in (700, 1100, 1600):
                            c = np.r_[tgt, math.degrees(th) + daz, el, d, fpx, 0.0, 0.0]
                            fr.k = f2.label_shields(fr, p, c)
                            cands.append((np.sum(np.minimum(f2.residuals(fr, p, c), 150) ** 2), c, fr.k))
    cands.sort(key=lambda t: t[0]); best = None
    lo = np.array([-150, -20, -150, -1e4, -10, 20, 300, -20]); hi = np.array([150, 90, 150, 1e4, 85, 3000, 4000, 20])
    for cost, c, k in cands[:12]:
        fr.k = k
        def fun(v, c=c): cc = c.copy(); cc[:8] = v; return f2.residuals(fr, p, cc)
        r = least_squares(fun, np.clip(c[:8], lo + 1e-6, hi - 1e-6), bounds=(lo, hi), loss="soft_l1", f_scale=10, max_nfev=300)
        cc = c.copy(); cc[:8] = r.x; fr.k = f2.label_shields(fr, p, cc)
        val = np.sum(np.minimum(f2.residuals(fr, p, cc), 150) ** 2)
        if best is None or val < best[0]: best = (val, cc, fr.k)
    fr.k = best[2]; return best[1], best[0]


_G = {}
def frames(drop=None):
    st = _G["st"]; out = []
    for f in f2.FRAMES:
        if f in f2.EXCLUDED or f == drop: continue
        fr = f2.Frame(_G["work"], f); fr.k = st["final2"]["k"][f]; out.append(fr)
    for f in EDGE:
        if f == drop: continue
        fr = EdgeFrame(f); fr.k = _G["cams"][f]["k"]; out.append(fr)
    return out


def _init(work, st, cams): _G.update(work=work, st=st, cams=cams); f2.WORK = work


_iou = f2.iou
f2.iou = lambda fr, p, cam: float("nan") if isinstance(fr, EdgeFrame) else _iou(fr, p, cam)


def cams0():
    c = {f: np.array(v) for f, v in _G["st"]["final2"]["cams"].items()}
    for f, v in _G["cams"].items(): c[f] = np.array(v["cam"])
    return c


def lens():
    L = dict(_G["st"]["lens"]); L.update({f: "close" for f in EDGE}); return L


def pack(x, c2, fl, r, frs):
    p = prof(x)
    return {"profile": {k: float(p[k]) for k in FIT_KEYS + ["yW"]}, "cams": {f: list(map(float, c)) for f, c in c2.items()},
            "focal": {k: list(map(float, v)) for k, v in fl.items()}, "cost_image": float(r.cost),
            "per_frame": f2.report(frs, p, c2), "k": {fr.f: fr.k for fr in frs}}


def ms_worker(x0):
    frs = frames(); x, c2, fl, r = f2.joint(frs, cams0(), lens(), np.array(x0), nfev=80)
    d = pack(x, c2, fl, r, frs); d["start"] = x0; return d


def loo_worker(a):
    drop, best = a; frs = frames(drop)
    x, c2, fl, r = f2.joint(frs, {f: np.array(c) for f, c in best["cams"].items()}, lens(),
                            np.array([best["profile"][k] for k in FIT_KEYS]), nfev=60 if drop else 100)
    d = pack(x, c2, fl, r, frs); d["drop"] = drop; return d


if __name__ == "__main__":
    from multiprocessing import Pool
    WORK = sys.argv[1]; t0 = time.time()
    st = json.load(open(f"{WORK}/fit2_state.json"))
    _init(WORK, st, {})
    p0 = prof(STARTS[1]); edge_cams = {}
    for f in EDGE:  # cameras of the edge-on frames from a grid on the middle start
        fr = EdgeFrame(f); c, cost = init_edge_camera(fr, p0)
        edge_cams[f] = {"cam": list(map(float, c)), "k": fr.k, "cost": float(cost)}
        print("edge camera", f, "shield k", fr.k, "cost %.0f" % cost, np.round(c, 1).tolist(), flush=True)
    _init(WORK, st, edge_cams)
    with Pool(3, _init, (WORK, st, edge_cams)) as pool:
        ms = pool.map(ms_worker, STARTS)
        for s in ms: print("start", s["start"], "cost %.0f" % s["cost_image"], {k: round(v, 2) for k, v in s["profile"].items()}, flush=True)
        bi = f2.basins(ms); best = min((ms[i] for i in bi), key=lambda s: s["cost_image"])
        drops = [None] + [f for f in f2.FRAMES if f not in f2.EXCLUDED] + list(EDGE)
        lo_ = pool.map(loo_worker, [(d, best) for d in drops])
    final = lo_[0]; loo = {d["drop"]: d["profile"] for d in lo_[1:]}
    for f, p in loo.items(): print("without", f, {k: round(v, 2) for k, v in p.items()}, flush=True)
    acc = f2.acceptance([ms[i]["profile"] for i in bi], list(loo.values()), keys=FIT_KEYS)
    for k, v in acc.items():
        print("%-6s basin %.2f loo %.2f -> %s (median %.2f)" % (k, v["basin_spread"], v["loo_spread"], "ACCEPT" if v["accepted"] else "reject", v["median"]), flush=True)
    st = json.load(open(f"{WORK}/fit2_state.json"))
    st[TAG] = {"anchor": ANCHOR, "fixed": BUILD, "crest": CREST, "starts": STARTS, "edge_cams": edge_cams, "multistart": ms,
               "basins": bi, "final": final, "loo": loo, "acceptance": acc, "excluded": f2.EXCLUDED, "seconds": round(time.time() - t0)}
    json.dump(st, open(f"{WORK}/fit2_state.json", "w"), indent=1)
    print("seconds", round(time.time() - t0))
