"""Lightmap UV set for the web hero bake: deterministic chart packing, no Blender unwrap operators.

Blender's lightmap pack and smart project gave the stadium shell and the roads under 1% atlas coverage:
the louvre fins, lattice and roads are hundreds of metres long and under a metre wide. Here every object
is cut into small charts and each chart is laid flat:
  planar  faces grown from a seed face while within 35 degrees of its normal and within L_MAX of it,
          projected onto their mean plane (fins, walls, roof, roads, pitches)
  tube    faces grown by distance only, unrolled around the chart's long axis (spears, bevelled curves)
Charts are packed on shelves at one texel density per atlas (found by bisection), with a minimum of
MIN_PX texels across, so a 0.3 m fin still gets two rows of light. GAP_PX empty texels separate charts;
the bake's extend margin fills them so bilinear filtering does not pick up a neighbour.
"""
import math
from collections import deque
import numpy as np

L_MAX = 24.0   # m, longest chart side before scaling
COS_PLANAR = math.cos(math.radians(35))
MIN_PX = 2
GAP_PX = 2


def _mesh_arrays(o):
    me = o.data
    nv, nl, nf = len(me.vertices), len(me.loops), len(me.polygons)
    co = np.empty(nv * 3); me.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    M = np.array(o.matrix_world); co = co @ M[:3, :3].T + M[:3, 3]
    lv = np.empty(nl, int); me.loops.foreach_get("vertex_index", lv)
    le = np.empty(nl, int); me.loops.foreach_get("edge_index", le)
    ls = np.empty(nf, int); me.polygons.foreach_get("loop_start", ls)
    lt = np.empty(nf, int); me.polygons.foreach_get("loop_total", lt)
    lf = np.repeat(np.arange(nf), lt)
    # Newell normals and area-weighted centroids in world space
    p = co[lv]
    nxt = np.arange(nl) + 1; last = ls + lt - 1; nxt[last] = ls
    q = co[lv[nxt]]
    cr = np.cross(p, q); nrm = np.zeros((nf, 3)); np.add.at(nrm, lf, cr)
    area = 0.5 * np.linalg.norm(nrm, axis=1)
    nrm = nrm / np.maximum(2 * area, 1e-12)[:, None]
    cen = np.zeros((nf, 3)); np.add.at(cen, lf, p); cen /= lt[:, None]
    return co, lv, le, ls, lt, lf, nrm, area, cen


def _charts(nf, le, lf, nrm, cen, tube):
    """Region growing over shared edges. Returns a list of face-index arrays."""
    order = np.argsort(le, kind="stable"); e_s = le[order]; f_s = lf[order]
    adj = [[] for _ in range(nf)]
    starts = np.r_[0, np.nonzero(np.diff(e_s))[0] + 1, len(e_s)]
    for a, b in zip(starts[:-1], starts[1:]):
        fs = f_s[a:b]
        if len(fs) > 1:
            for i in fs:
                for j in fs:
                    if i != j: adj[i].append(j)
    done = np.zeros(nf, bool); out = []; r2 = (L_MAX / 2) ** 2
    nrm_l = nrm.tolist(); cen_l = cen.tolist()
    for seed in range(nf):
        if done[seed]: continue
        sn = nrm_l[seed]; sc = cen_l[seed]; flat_seed = (sn[0] ** 2 + sn[1] ** 2 + sn[2] ** 2) < 0.5
        done[seed] = True; chart = [seed]; dq = deque([seed])
        while dq:
            f = dq.popleft()
            for g in adj[f]:
                if done[g]: continue
                c = cen_l[g]
                if (c[0] - sc[0]) ** 2 + (c[1] - sc[1]) ** 2 + (c[2] - sc[2]) ** 2 > r2: continue
                if not tube and not flat_seed:
                    n = nrm_l[g]
                    if n[0] * sn[0] + n[1] * sn[1] + n[2] * sn[2] < COS_PLANAR: continue
                done[g] = True; chart.append(g); dq.append(g)
        out.append(np.array(chart))
    return out


def _flatten(chart, co, lv, ls, lt, nrm, area, cen, tube):
    """2D coordinates (metres) for every loop of the chart's faces. Returns (loop indices, uv, w, h)."""
    loops = np.concatenate([np.arange(ls[f], ls[f] + lt[f]) for f in chart])
    P = co[lv[loops]]
    if tube and len(P) > 2:
        m = P.mean(0); _, _, vt = np.linalg.svd(P - m, full_matrices=False); a = vt[0]
        b1 = vt[1]; b2 = np.cross(a, b1)
        d = P - m; u = d @ a
        rad = d - np.outer(u, a); R = max(float(np.linalg.norm(rad, axis=1).mean()), 1e-3)
        ang = np.arctan2(rad @ b2, rad @ b1)
        # unwrap each loop's angle against its own face's centroid angle so no face straddles the seam
        fl = np.repeat(chart, lt[chart]); dc = cen[fl] - m; dc -= np.outer(dc @ a, a)
        ac = np.arctan2(dc @ b2, dc @ b1)
        ang = ac + (ang - ac + np.pi) % (2 * np.pi) - np.pi
        uv = np.stack([u, ang * R], 1)
    else:
        n = (nrm[chart] * area[chart, None]).sum(0); ln = np.linalg.norm(n)
        n = n / ln if ln > 1e-9 else nrm[chart[0]]
        t = np.cross(n, [0, 0, 1.0]) if abs(n[2]) < 0.9 else np.cross(n, [1.0, 0, 0]); t /= np.linalg.norm(t)
        b = np.cross(n, t); uv = np.stack([P @ t, P @ b], 1)
        if len(uv) > 2:  # rotate to the principal axis for a tight box
            c0 = uv - uv.mean(0); _, _, vt = np.linalg.svd(c0, full_matrices=False); uv = c0 @ vt.T
    uv -= uv.min(0); w, h = uv.max(0)
    if h > w: uv = uv[:, ::-1]; w, h = h, w
    return loops, uv, float(w), float(h)


def _shelf(dims, size):
    """Shelf-pack (w, h) pixel rects, tallest first. Returns positions or None if it does not fit."""
    order = sorted(range(len(dims)), key=lambda i: (-dims[i][1], -dims[i][0]))
    pos = [None] * len(dims); x = y = GAP_PX; shelf_h = 0
    for i in order:
        w, h = dims[i]
        if w + 2 * GAP_PX > size: return None
        if x + w + GAP_PX > size: x = GAP_PX; y += shelf_h + GAP_PX; shelf_h = 0
        if y + h + GAP_PX > size: return None
        pos[i] = (x, y); x += w + GAP_PX; shelf_h = max(shelf_h, h)
    return pos


def pack(obs, size, tube_names=()):
    """Write the "lightmap" UV layer of every object in obs into one size x size atlas. Returns stats."""
    items = []  # (object, loops, uv in metres, w, h)
    for o in obs:
        co, lv, le, ls, lt, lf, nrm, area, cen = _mesh_arrays(o)
        tube = o.name in tube_names
        for ch in _charts(len(ls), le, lf, nrm, cen, tube):
            loops, uv, w, h = _flatten(ch, co, lv, ls, lt, nrm, area, cen, tube)
            items.append((o, loops, uv, w, h))

    def dims_at(d):
        return [(max(MIN_PX, math.ceil(w * d)), max(MIN_PX, math.ceil(h * d))) for _, _, _, w, h in items]

    lo, hi = 0.0, 1.0
    while _shelf(dims_at(hi), size) is not None: lo, hi = hi, hi * 2
    for _ in range(18):
        mid = 0.5 * (lo + hi)
        if _shelf(dims_at(mid), size) is not None: lo = mid
        else: hi = mid
    d = lo; dims = dims_at(d); pos = _shelf(dims, size)
    buf = {o.name: np.zeros((len(o.data.loops), 2)) for o in obs}
    used = 0
    for (o, loops, uv, w, h), (pw, ph), (x, y) in zip(items, dims, pos):
        sx = pw / w if w > 1e-9 else 0.0; sy = ph / h if h > 1e-9 else 0.0
        px = np.stack([x + uv[:, 0] * sx, y + uv[:, 1] * sy], 1)
        buf[o.name][loops] = px / size; used += pw * ph
    for o in obs:
        o.data.uv_layers["lightmap"].data.foreach_set("uv", buf[o.name].ravel())
    return {"charts": len(items), "texels_per_m": round(d, 3), "rect_fill": round(used / size ** 2, 3)}
