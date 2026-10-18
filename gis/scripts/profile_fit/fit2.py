"""Profile fit, second version (cloud session 2026-10-18): least squares on image distances, not mask IoU.

Terms per frame (pixels, 1280 x 720):
  sil    mask boundary points to the projected shell outline (convex hull), and outline vertices to the mask
         boundary (distance transform); points on the frame border are left out (frames crop the stadium)
  open   roof-opening mask boundary points to the projected opening ring
  J, F   hand-read wall-to-roof junction and wall foot points (lines.json) to the projected visible rings
  S      shield centres with explicit labels: the left-to-right shields of a frame are the adjacent shields
         k+1, k of the model (angle -91.76 + 45 k deg); k is chosen once per frame in the grid stage
Cameras start from a coarse grid over azimuth and elevation (the 180 deg symmetry gives two equal minima; the
better is kept), then a per-camera polish, then the joint fit: profile + one focal length per lens + 7 pose
values per frame. Leave-one-frame-out repeats the joint fit without each frame in turn.
Run: python3 fit2.py <workdir with the seg2.py masks> [grid|joint|loo|all]
"""
import json, math, os, sys, time
import numpy as np
from scipy import ndimage as nd
from scipy.optimize import least_squares
from scipy.spatial import ConvexHull
import model as m

HERE = os.path.dirname(os.path.abspath(__file__))
LINES = {k: v for k, v in json.load(open(os.path.join(HERE, "lines.json"))).items() if not k.startswith("_")}
FRAMES = list(LINES)
KEYS = ["yW", "Rh", "Rv", "openY", "sag", "dF", "bulge", "hs"]
LO = np.array([30, 1, 1, 35, -3, -4, -4, 18.0]); HI = np.array([60, 40, 20, 60, 6, 15, 6, 36.0])
START = np.array([51.0, 3.0, 3.0, 50.0, 1.5, 1.0, 0.0, 28.75])
PRESS_MAX = 56.0  # press: maximum height about 56 m (soft limit, +-2 m)
W, H = m.W, m.H
NS = 360  # ring sampling for the curve distances
ANG = 2 * np.pi * np.arange(NS) / NS


def interp_ring(r):  # model rings are sampled at N = 120; resample to NS
    x = np.r_[r, r[:1]]; t = np.linspace(0, 1, len(x)); return np.interp(np.linspace(0, 1, NS + 1)[:-1], t, x)


RRO, RRI = interp_ring(m.rRo), interp_ring(m.rRi)
DXS, DZS = np.cos(ANG), np.sin(ANG)


def prof(x):
    p = dict(m.CUR); p.update(dict(zip(KEYS, map(float, x)))); return p


def ring(r, y): return np.stack([DXS * r, np.full(NS, y), DZS * r], -1)


def project(P, cam):
    R, C, f = m.cam_matrix(cam); q = (P - C) @ R.T
    z = q[:, 2]; return np.stack([f * q[:, 0] / np.maximum(z, 1e-3) + W / 2, f * q[:, 1] / np.maximum(z, 1e-3) + H / 2], 1), z, C


def visible(P, C):  # outward-facing points of a ring (normal = radial direction)
    n = np.stack([P[:, 0], np.zeros(len(P)), P[:, 2]], 1); n /= np.linalg.norm(n, axis=1, keepdims=True)
    return ((C - P) * n).sum(1) > 0


def seg_dist(pts, poly, closed=True):
    """Distance from each point to a polyline (vectorised point-to-segment)."""
    a = poly; b = np.roll(poly, -1, 0) if closed else poly[1:]
    if not closed: a = poly[:-1]
    ab = b - a; L2 = np.maximum((ab ** 2).sum(1), 1e-9)
    t = np.clip(((pts[:, None, :] - a[None]) * ab[None]).sum(2) / L2[None], 0, 1)
    d = pts[:, None, :] - (a[None] + t[..., None] * ab[None]); return np.sqrt((d ** 2).sum(2)).min(1)


def runs(mask):  # split a visibility mask on the closed ring into runs of consecutive indices
    idx = np.nonzero(mask)[0]
    if len(idx) == 0: return []
    if mask.all(): return [np.r_[idx, idx[:1]]]
    k0 = int(np.nonzero(~mask)[0][0]); order = np.roll(np.arange(len(mask)), -k0); out, cur = [], []
    for i in order:
        if mask[i]: cur.append(i)
        elif cur: out.append(np.array(cur)); cur = []
    if cur: out.append(np.array(cur))
    return out


def curve_dist(pts, P, cam, need_visible=True):
    uv, z, C = project(P, cam)
    vis = visible(P, C) if need_visible else np.ones(len(P), bool)
    vis &= z > 1
    best = np.full(len(pts), 400.0)
    for r_ in runs(vis):
        if len(r_) > 1: best = np.minimum(best, seg_dist(pts, uv[r_], closed=False))
    return best


class Frame:
    def __init__(self, work, f):
        self.f = f; M = np.load(f"{work}/mask_{f}.npy")
        e = M ^ nd.binary_erosion(M, iterations=1)
        e[:3, :] = e[-3:, :] = e[:, :3] = e[:, -3:] = False      # frame border is not a stadium edge
        ys, xs = np.nonzero(e); rng = np.random.default_rng(1); k = rng.choice(len(xs), min(220, len(xs)), replace=False)
        self.edge = np.stack([xs[k], ys[k]], 1).astype(float)
        self.dt = nd.distance_transform_edt(~e)
        ys_, xs_ = np.nonzero(M); self.w_px = np.ptp(xs_) + 1; self.h_px = np.ptp(ys_) + 1
        self.cropped_x = xs_.min() < 4 or xs_.max() > W - 5
        try:
            O = np.load(f"{work}/open_{f}.npy")
            oe = O ^ nd.binary_erosion(O, iterations=1); ys, xs = np.nonzero(oe)
            k = rng.choice(len(xs), min(90, len(xs)), replace=False); self.oedge = np.stack([xs[k], ys[k]], 1).astype(float)
            if O.sum() < 6000: self.oedge = None
        except FileNotFoundError: self.oedge = None
        L = LINES[f]; self.J = np.array(L["J"], float); self.F = np.array(L["F"], float).reshape(-1, 2); self.S = np.array(L["S"], float)
        self.k = None  # shield label of the rightmost annotated shield


def shell_pts(p): return m.shell(p).reshape(-1, 3)


def shield_P(p, ks):
    th = np.radians(-1.76 - 90 + 45 * np.asarray(ks)); y = p["hs"]
    r = m.wall_r(p, th, y) + 2.6; return np.stack([np.cos(th) * r, np.full(len(ks), y), np.sin(th) * r], -1)


def n_res(fr): return 220 + 220 + 90 + len(fr.J) + len(fr.F) + len(fr.S)


def residuals(fr, p, cam, w_sil=1.0, w_line=3.0, w_sh=3.0):
    """Fixed length per frame (n_res); missing terms are zeros."""
    r = _residuals(fr, p, cam, w_sil, w_line, w_sh)
    return r if len(r) == n_res(fr) else np.r_[r, np.zeros(n_res(fr) - len(r))]


def _residuals(fr, p, cam, w_sil, w_line, w_sh):
    out = []
    uv, z, C = project(shell_pts(p), cam)
    if (z < 1).any(): return np.full(n_res(fr), 300.0)
    hull = uv[ConvexHull(uv).vertices]
    out.append(w_sil * pad(seg_dist(fr.edge, hull), 220))
    hv = np.linspace(0, 1, 120, endpoint=False); a = hull; b = np.roll(hull, -1, 0)
    dense = (a[:, None] + (b - a)[:, None] * hv[None, :, None]).reshape(-1, 2)
    inside = (dense[:, 0] > 3) & (dense[:, 0] < W - 4) & (dense[:, 1] > 3) & (dense[:, 1] < H - 4)
    dd = np.where(inside, fr.dt[np.clip(dense[:, 1].astype(int), 0, H - 1), np.clip(dense[:, 0].astype(int), 0, W - 1)], 0.0)
    out.append(w_sil * pad(dd[:: max(1, len(dd) // 220)][:220], 220))
    out.append(pad(0.7 * curve_dist(fr.oedge, ring(RRI, p["openY"]), cam, need_visible=False), 90) if fr.oedge is not None else np.zeros(90))
    rF = RRO - p["dF"]
    out.append(w_line * curve_dist(fr.J, ring(RRO, p["yW"]), cam))
    if len(fr.F): out.append(w_line * curve_dist(fr.F, ring(rF, p["yFoot"]), cam))
    if fr.k is not None and len(fr.S):
        ks = [(fr.k + len(fr.S) - 1 - i) % 8 for i in range(len(fr.S))]   # left to right: k+n-1 ... k
        su, sz, _ = project(shield_P(p, ks), cam)
        out.append(w_sh * np.linalg.norm(su - fr.S, axis=1))
    elif len(fr.S): out.append(np.zeros(len(fr.S)))
    return np.concatenate(out)


def pad(r, n):  # fixed residual length per frame for least_squares
    return np.r_[r, np.zeros(max(0, n - len(r)))][:n]


def label_shields(fr, p, cam):
    """Choose k so the annotated shields match adjacent visible model shields in left-to-right order."""
    best = (1e18, None)
    for k in range(8):
        ks = [(k + len(fr.S) - 1 - i) % 8 for i in range(len(fr.S))]
        P = shield_P(p, ks); su, sz, C = project(P, cam)
        nrm = np.stack([np.cos(np.radians(-91.76 + 45 * np.array(ks))), np.zeros(len(ks)), np.sin(np.radians(-91.76 + 45 * np.array(ks)))], -1)
        facing = (((C - P) * nrm).sum(1) / np.linalg.norm(C - P, axis=1) > 0.15).all()
        d = np.linalg.norm(su - fr.S, axis=1).sum() + (0 if facing else 5000)
        if d < best[0]: best = (d, k)
    return best[1]


def cam_from(az, el, f, fr, p):
    """Target at the bowl centre; distance so the projected shell height matches the mask height."""
    c = np.array([0, 28, 0, az, el, 3000.0, f, 0.0])
    uv, z, C = project(shell_pts(p), c)
    if fr.cropped_x: c[5] = 3000 * (np.ptp(uv[:, 1]) + 1) / fr.h_px
    else: c[5] = 3000 * (np.ptp(uv[:, 0]) + 1) / fr.w_px
    # centre the projected shell on the mask centre by shifting the look-at target (small-angle)
    uv, z, C = project(shell_pts(p), c)
    du = fr.edge.mean(0) - uv.mean(0); R, C, f_ = m.cam_matrix(c)
    shift = (R[0] * du[0] + R[1] * du[1]) * c[5] / f_
    c[0] += shift[0]; c[1] += shift[1]; c[2] += shift[2]; return c


def solve_camera(fr, p, f0, free_f=True, seeds=None, top=8, f_fixed=None):
    """seeds: list of (az, el, f) to scan around instead of the full grid (re-solve of frames in wrong minima)."""
    cands = []
    if f_fixed: free_f = False
    fl = (f_fixed,) if f_fixed else (700.0, 1000.0, 1500.0, 2500.0)
    grid = ([(az, el, f_) for az in range(0, 360, 10) for el in range(3, 75, 4) for f_ in fl]
            if seeds is None else [(a + da, max(3, e + de), f_ * sf) for a, e, f_ in seeds for da in range(-60, 61, 6)
                                   for de in (-8, -4, 0, 4, 8) for sf in ((1.0,) if f_fixed else (0.8, 1.0, 1.25))])
    for az, el, f0 in grid:
            c = cam_from(az, el, f0, fr, p)
            fr.k = label_shields(fr, p, c)
            cost = np.sum(np.minimum(residuals(fr, p, c), 150) ** 2)
            cands.append((cost, c, fr.k))
    cands.sort(key=lambda t: t[0]); best = None
    for cost, c, k in cands[:top]:
        fr.k = k
        idx = [0, 1, 2, 3, 4, 5, 6, 7] if free_f else [0, 1, 2, 3, 4, 5, 7]
        def fun(v):
            cc = c.copy(); cc[idx] = v; return residuals(fr, p, cc)
        lo = np.array([-150, -20, -150, -1e4, 2, 60, 300, -20])[idx]; hi = np.array([150, 90, 150, 1e4, 85, 3000, 4000, 20])[idx]
        r = least_squares(fun, np.clip(c[idx], lo + 1e-6, hi - 1e-6), bounds=(lo, hi), loss="soft_l1", f_scale=10, max_nfev=400)
        cc = c.copy(); cc[idx] = r.x; fr.k = label_shields(fr, p, cc)
        val = np.sum(np.minimum(residuals(fr, p, cc), 150) ** 2)
        if best is None or val < best[0]: best = (val, cc, fr.k)
    fr.k = best[2]; return best[1]


def joint(frames, cams, lens, x0, fixed_profile=False, nfev=60):
    """Profile + one focal length per lens + pose per frame."""
    lens_ids = sorted(set(lens[f.f] for f in frames))
    fvals = {L: np.mean([cams[f.f][6] for f in frames if lens[f.f] == L]) for L in lens_ids}
    v0 = list(x0) + [fvals[L] for L in lens_ids]
    for f in frames: v0 += list(np.delete(cams[f.f], 6))
    v0 = np.array(v0); n_p = len(KEYS); n_l = len(lens_ids)
    lo = list(LO) + [300] * n_l; hi = list(HI) + [4000] * n_l
    for _ in frames: lo += [-150, -20, -150, -1e4, 2, 60, -20]; hi += [150, 90, 150, 1e4, 85, 3000, 20]
    lo, hi = np.array(lo), np.array(hi)
    lens_index = [lens_ids.index(lens[f.f]) for f in frames]
    sizes = [n_res(f) for f in frames]

    def unpack(v):
        p = prof(v[:n_p]); out = []
        for i, f in enumerate(frames):
            c = v[n_p + n_l + 7 * i: n_p + n_l + 7 * i + 7]; out.append(np.insert(c, 6, v[n_p + lens_index[i]]))
        return p, out

    def fun(v):
        if fixed_profile: v = np.r_[x0, v[n_p:]]
        p, cs = unpack(v)
        res = [pad(residuals(f, p, c), n) for f, c, n in zip(frames, cs, sizes)]
        top = p["yW"] + p["Rv"]
        res.append([5.0 * max(0.0, top - (PRESS_MAX + 2.0))])
        return np.concatenate(res)

    r = least_squares(fun, np.clip(v0, lo + 1e-6, hi - 1e-6), bounds=(lo, hi), loss="soft_l1", f_scale=10, max_nfev=nfev, x_scale="jac")
    p, cs = unpack(r.x)
    return r.x[:n_p], {f.f: c for f, c in zip(frames, cs)}, {L: r.x[n_p + i] for i, L in enumerate(lens_ids)}, r


def report(frames, p, cams):
    out = {}
    for f in frames:
        res = residuals(f, p, cams[f.f], 1, 1, 1)
        J = curve_dist(f.J, ring(RRO, p["yW"]), cams[f.f])
        out[f.f] = {"k": f.k, "sil_median_px": round(float(np.median(res[:220])), 1), "J_rms_px": round(float(np.sqrt((J ** 2).mean())), 1),
                    "iou": round(iou(f, p, cams[f.f]), 3)}
    return out


def iou(fr, p, cam):
    s = m.sil(p, cam); M = np.load(f"{WORK}/mask_{fr.f}.npy")
    Md = M.reshape(H // m.SC, m.SC, W // m.SC, m.SC).mean((1, 3)) > 0.5
    if s is None: return 0.0
    return float((s & Md).sum() / max(1, (s | Md).sum()))


if __name__ == "__main__":
    WORK = sys.argv[1]; mode = sys.argv[2] if len(sys.argv) > 2 else "all"
    if mode == "overlay": mode = "none"
    frames = [Frame(WORK, f) for f in FRAMES]
    state_path = f"{WORK}/fit2_state.json"
    state = json.load(open(state_path)) if os.path.exists(state_path) else {}
    p0 = prof(START)
    if mode in ("grid", "all") or "cams" not in state:
        cams = {}
        for fr in frames:
            t = time.time()
            c = solve_camera(fr, p0, None); best = (np.sum(np.minimum(residuals(fr, p0, c), 150) ** 2), c, fr.k)
            cams[fr.f] = best[1]; fr.k = best[2]
            print(fr.f, "k", fr.k, "f %.0f" % best[1][6], "az %.0f el %.0f d %.0f roll %.1f" % tuple(best[1][[3, 4, 5, 7]]),
                  "cost %.0f" % best[0], "%.0f s" % (time.time() - t), flush=True)
        state["cams"] = {f: list(map(float, c)) for f, c in cams.items()}; state["k"] = {fr.f: fr.k for fr in frames}
        json.dump(state, open(state_path, "w"), indent=1)
    if mode == "regrid":   # python3 fit2.py <work> regrid <frame> [<frame> ...]: seeds from the other cameras
        good = [f for f in state["cams"] if f not in sys.argv[3:]]
        seeds = [tuple(np.array(state["cams"][f])[[3, 4, 6]]) for f in good]
        seeds += [((a + 180) % 360, e, f_) for a, e, f_ in seeds]   # and the symmetric twins
        for fr in frames:
            if fr.f not in sys.argv[3:]: continue
            t = time.time(); c = solve_camera(fr, p0, None, seeds=seeds, top=12)
            v = np.sum(np.minimum(residuals(fr, p0, c), 150) ** 2)
            print(fr.f, "k", fr.k, "f %.0f" % c[6], "az %.0f el %.0f d %.0f roll %.1f" % tuple(c[[3, 4, 5, 7]]), "cost %.0f (was %.0f)" % (v,
                  np.sum(np.minimum(residuals(Frame(WORK, fr.f) if False else fr, p0, np.array(state["cams"][fr.f])), 150) ** 2)), "%.0f s" % (time.time() - t), flush=True)
            state["cams"][fr.f] = list(map(float, c)); state["k"][fr.f] = fr.k
        json.dump(state, open(state_path, "w"), indent=1)
    cams = {f: np.array(c) for f, c in state["cams"].items()}
    for fr in frames: fr.k = state["k"][fr.f]
    lens = state.get("lens") or {f: ("tele" if cams[f][6] > 1600 else "wide") for f in FRAMES}
    state["lens"] = lens
    if mode in ("joint", "all"):
        t = time.time()
        x, cams2, fl, r = joint(frames, cams, lens, START, nfev=120)
        p = prof(x)
        state["joint"] = {"profile": dict(zip(KEYS, map(float, x))), "focal": {k: float(v) for k, v in fl.items()},
                          "cams": {f: list(map(float, c)) for f, c in cams2.items()}, "per_frame": report(frames, p, cams2),
                          "cost": float(r.cost), "seconds": round(time.time() - t)}
        json.dump(state, open(state_path, "w"), indent=1)
        print("joint", {k: round(v, 2) for k, v in state["joint"]["profile"].items()}, state["joint"]["focal"], round(time.time() - t), "s", flush=True)
        print(json.dumps(state["joint"]["per_frame"]), flush=True)
    if mode in ("loo", "all"):
        base = state["joint"]; x0 = np.array([base["profile"][k] for k in KEYS])
        cj = {f: np.array(c) for f, c in base["cams"].items()}; loo = {}
        for drop in FRAMES:
            t = time.time(); sub = [fr for fr in frames if fr.f != drop]
            x, _, _, _ = joint(sub, cj, lens, x0, nfev=80)
            loo[drop] = dict(zip(KEYS, map(float, x)))
            print("loo without", drop, {k: round(v, 2) for k, v in loo[drop].items()}, round(time.time() - t), "s", flush=True)
            state["loo"] = loo; json.dump(state, open(state_path, "w"), indent=1)
        spread = {k: float(np.ptp([loo[f][k] for f in loo])) for k in KEYS}
        state["spread"] = spread; json.dump(state, open(state_path, "w"), indent=1)
        print("spread (max - min over leave-one-out)", {k: round(v, 2) for k, v in spread.items()}, flush=True)


def overlay(work, frames, p, cams, tag):
    """Fitted outline (cyan), junction ring (magenta), crest (yellow), foot (orange), opening (green), model
    shields (red rings) and hand-read points (white dots) on every frame."""
    from PIL import Image, ImageDraw
    tiles = []
    for fr in frames:
        c = cams[fr.f]
        im = Image.open(m.ROOT + f"research/frames/JWNowpO44rw/JWNowpO44rw_{fr.f}.jpg").convert("RGB"); d = ImageDraw.Draw(im)
        uv, z, C = project(shell_pts(p), c); h = uv[ConvexHull(uv).vertices]
        d.line([tuple(q) for q in np.vstack([h, h[:1]])], fill=(0, 255, 255), width=3)
        crest = ring(RRO - p["Rh"], p["yW"] + p["Rv"])
        for P, col in ((ring(RRO, p["yW"]), (255, 0, 255)), (crest, (255, 255, 0)), (ring(RRO - p["dF"], p["yFoot"]), (255, 140, 0))):
            u, _, C_ = project(P, c); vis = visible(P, C_)
            for r_ in runs(vis): d.line([tuple(q) for q in u[r_]], fill=col, width=2)
        u, _, _ = project(ring(RRI, p["openY"]), c); d.line([tuple(q) for q in np.vstack([u, u[:1]])], fill=(0, 255, 0), width=2)
        if fr.k is not None and len(fr.S):
            ks = [(fr.k + len(fr.S) - 1 - i) % 8 for i in range(len(fr.S))]
            for q in project(shield_P(p, ks), c)[0]: d.ellipse((q[0] - 12, q[1] - 12, q[0] + 12, q[1] + 12), outline=(255, 0, 0), width=4)
        for q in np.vstack([fr.J, fr.F.reshape(-1, 2), fr.S]): d.ellipse((q[0] - 5, q[1] - 5, q[0] + 5, q[1] + 5), fill=(255, 255, 255))
        im = im.resize((640, 360)); ImageDraw.Draw(im).text((5, 5), f"{fr.f}  iou {iou(fr, p, c):.3f}", fill=(255, 255, 0)); tiles.append(im)
    sh = Image.new("RGB", (1920, 360 * ((len(tiles) + 2) // 3)))
    for k, t in enumerate(tiles): sh.paste(t, ((k % 3) * 640, (k // 3) * 360))
    sh.save(f"{work}/overlay_{tag}.jpg", quality=85)


if __name__ == "__main__" and "overlay" in sys.argv:
    st = json.load(open(f"{WORK}/fit2_state.json")); key = sys.argv[sys.argv.index("overlay") + 1]
    if key == "grid": p = prof(START); cams = {f: np.array(c) for f, c in st["cams"].items()}
    else: p = prof([st[key]["profile"][k] for k in KEYS]); cams = {f: np.array(c) for f, c in st[key]["cams"].items()}
    for fr in frames: fr.k = st["k"][fr.f]
    overlay(WORK, frames, p, cams, key)
