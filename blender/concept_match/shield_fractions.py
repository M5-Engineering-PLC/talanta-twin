"""Shield outline check (replica plan 2026-10-20, pass A): red-field width fractions of one shield in an image.

Red field = pixels clearly redder than green and blue (the white spine, leaves and boss inside it are bridged: the
width of a row is its leftmost to rightmost red pixel). The shield height runs from the first to the last row with
red pixels in the box. Prints the red width at 10 % from the top and at 3 % from the bottom tip as fractions of the
red width at mid-height, and the median red and black (lobe) colours.
Usage: python3 blender/concept_match/shield_fractions.py <image> x0,y0,x1,y1 [width height]
  box in pixels of a 1920 x 1080 frame (the image is resized to width x height first, default 1920 x 1080)
"""
import json, sys
import numpy as np
from PIL import Image


def measure(path, box, size=(1920, 1080)):
    a = np.asarray(Image.open(path).convert("RGB").resize(size)).astype(int)
    x0, y0, x1, y1 = box; a = a[y0:y1, x0:x1]
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    red = (r - g > 60) & (r - b > 25)
    rows = np.where(red.sum(1) >= 3)[0]
    top, bot = rows[0], rows[-1]; H = bot - top

    def width(fr):
        y = int(round(top + fr * H)); ws = []
        for yy in range(y - 2, y + 3):  # 5-row median against noise
            xs = np.where(red[yy])[0]
            if len(xs): ws.append(xs[-1] - xs[0] + 1)
        return float(np.median(ws)) if ws else 0.0
    mid = width(0.5)
    # black lobes: dark, low-saturation pixels between the red field's extent rows, inside the shield height
    band = a[top + H // 3: top + 2 * H // 3]
    lum = band.mean(-1); blk = band[(lum < 70) & (np.abs(band[..., 0] - band[..., 2]) < 25)]
    return {"top_px": int(top + y0), "bottom_px": int(bot + y0), "mid_width_px": mid,
            "f_top10": round(width(0.10) / mid, 3), "f_bottom3": round(width(0.97) / mid, 3),
            "red_median": np.median(a[red], 0).round().astype(int).tolist(),
            "black_median": np.median(blk, 0).round().astype(int).tolist() if len(blk) else None, "black_px": int(len(blk))}


if __name__ == "__main__":
    box = [int(v) for v in sys.argv[2].split(",")]
    size = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (1920, 1080)
    print(json.dumps(measure(sys.argv[1], box, size)))
