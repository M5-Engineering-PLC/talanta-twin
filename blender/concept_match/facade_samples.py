"""Replica plan acceptance (2026-10-20): shield, fascia and louvre colour samples, render against frame.

Each shield (or shield half, split by the white spine) is a connected red area (r - g > 35, r > 1.6 g, r - b > 15,
at least 150 px, taller than wide), inside the stadium mask when one is given (the murram beds are red-brown too). Per image, over all shields:
- red: median of the red pixels; black: median of the dark low-chroma pixels inside the shield's box (the lobes);
- louvre: median of the facade beside each shield (one shield width left and right, middle 40 % of its height,
  red and black pixels left out): louvre fins and the lattice;
- fascia: median of the band from 7 % to 2 % of the shield height above the shield top, over the shield width.
Prints both sets and the largest channel difference (acceptance: 12 levels in the same light).
Run (gis venv): ~/.venvs/gis/bin/python blender/concept_match/facade_samples.py <render png> <frame jpg> [w h] [mask png]
"""
import json, sys
import numpy as np
from PIL import Image
from scipy import ndimage


def samples(path, size, mask=None):
    a = np.asarray(Image.open(path).convert("RGB").resize(size)).astype(int); r, g, b = a[..., 0], a[..., 1], a[..., 2]
    red = (r - g > 35) & (r > 1.6 * g) & (r - b > 15); lum = a.mean(-1); ch = a.max(-1) - a.min(-1)
    if mask is not None: red &= mask
    red = ndimage.binary_closing(red, iterations=2); lab, n = ndimage.label(red)
    R, K, L, F = [], [], [], []; ns = 0
    for j, sl in enumerate(ndimage.find_objects(lab), 1):
        m = lab[sl] == j
        if m.sum() < 150: continue
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop; h, w = y1 - y0, x1 - x0
        if h < 1.3 * w: continue  # a shield is taller than wide
        ns += 1; R.append(a[sl][m])
        box = a[y0:y1, x0:x1]; dark = (box.mean(-1) < 70) & ((box.max(-1) - box.min(-1)) < 30); K.append(box[dark])
        ym0, ym1 = y0 + int(0.3 * h), y0 + int(0.7 * h)
        for xa, xb in ((max(x0 - w, 0), x0), (x1, min(x1 + w, a.shape[1]))):
            reg = a[ym0:ym1, xa:xb]; ok = ~(((reg[..., 0] - reg[..., 1]) > 60) | (reg.mean(-1) < 70)); L.append(reg[ok])
        fa, fb = max(y0 - int(0.07 * h), 0), max(y0 - int(0.02 * h), 1); F.append(a[fa:fb, x0:x1].reshape(-1, 3))
    med = lambda xs: np.median(np.concatenate(xs), 0).round().astype(int).tolist() if xs and sum(len(x) for x in xs) else None
    return {"shields": ns, "red": med(R), "black": med(K), "louvre": med(L), "fascia": med(F)}


if __name__ == "__main__":
    size = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (1280, 720)
    mk = ndimage.binary_dilation(np.asarray(Image.open(sys.argv[5]).convert("L").resize(size)) > 127, iterations=10) if len(sys.argv) > 5 else None
    s_r, s_f = samples(sys.argv[1], size, mk), samples(sys.argv[2], size, mk)
    diff = {k: (max(abs(x - y) for x, y in zip(s_r[k], s_f[k])) if s_r[k] and s_f[k] else None) for k in ("red", "black", "louvre", "fascia")}
    print(json.dumps({"render": s_r, "frame": s_f, "max_channel_diff": diff}))
