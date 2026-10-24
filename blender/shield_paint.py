"""Shield paint drawn from simple shapes (our own drawing, never a frame pixel), used by build_blockout.py.

Outline (pass A, 2026-10-20): a pointed lens, half-width w(v) = (1 - |v|^a)^b of the half shield width at height v
(-1 top tip, +1 bottom tip). a and b come from the ledger (bowl.shield.outline_a/_b), tuned in F16 renders so the
rendered red-field width at 10 % from the top and at 3 % from the bottom tip, as fractions of the mid-height red width,
match JWNowpO44rw 001216.000 (0.73, 0.30; blender/concept_match/shield_fractions.py). The drawn fractions are lower
than the rendered ones: the facade shoulder foreshortens the top of the shield in that view. The parts follow the outline: black crescent
lobes on the left and right edges (thickest at mid-height), a white spine, white leaves above and below a white boss.
No pale rim: the edge has the face colour (facade spec 2026-10-20 rule 8).
"""
import numpy as np


def srgb(hexv):
    h = hexv.lstrip("#"); return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def draw(w, h, red_hex, black_hex, a, b, lobe=0.4, lobe_h=0.56):
    """RGBA float image (rows top to bottom), sRGB-encoded values."""
    yy, xx = np.mgrid[0:h, 0:w]; u = (xx + 0.5) / w * 2 - 1; v = (yy + 0.5) / h * 2 - 1
    au, av = np.abs(u), np.abs(v)
    edge = np.clip(1 - av ** a, 0, 1) ** b
    outline = au <= edge
    white = [0.95, 0.95, 0.93, 1]
    img = np.zeros((h, w, 4)); img[outline] = [*srgb(red_hex), 1]
    thick = lobe * np.sqrt(np.clip(1 - (v / lobe_h) ** 2, 0, 1))  # crescent thickness, following the outline
    img[outline & (au >= edge - thick) & (thick > 0)] = [*srgb(black_hex), 1]
    img[outline & (au < 0.014) & (av < 0.97)] = white  # spine
    t = np.clip((av - 0.16) / 0.78, 0, 1)  # leaves above and below the boss, pointed at both ends, kept inside the lens
    scale = np.clip(edge / 0.82, 0, 1)
    lw = 0.085 * np.sin(np.pi * t) ** 0.7 * scale
    img[outline & (av > 0.16) & (av < 0.94) & (np.abs(au - 0.115 * scale) < lw)] = white
    img[(u / 0.18) ** 2 + (v / 0.13) ** 2 <= 1] = white  # boss
    return img
