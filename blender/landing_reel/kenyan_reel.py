"""Internal test reel in a Kenyan style from the two 24-frame Cycles orbits (scroll_test_01 L07 daylight, scroll_test_02
L06 lit sunset). Internal review only, not the landing film.

Run from the repo root:  python3 blender/landing_reel/kenyan_reel.py <out.mp4>
Title card with the flag bands (black, red, green with white edging) and a shield motif, a band wipe, the daylight
orbit, a band wipe, the dusk orbit, an end card. Each orbit plays forwards and back (ping-pong) with a crossfade
between rendered frames (three output frames each at 24 fps), so no frame is invented by interpolation. The claim
"Visualization: people, vehicles and lighting are illustrative" is on screen for the whole reel.
"""
import subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(sys.argv[1])
W, H, FPS = 1920, 1080, 24
BLACK, RED, GREEN, WHITE, CREAM = (16, 16, 16), (187, 0, 0), (0, 106, 68), (255, 255, 255), (246, 239, 222)
CLAIM = "Visualization: people, vehicles and lighting are illustrative"


def font(size, bold=False):
    for n in (("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"), "DejaVuSans.ttf"):
        try: return ImageFont.truetype(n, size)
        except OSError: pass
    return ImageFont.load_default()


def bands(d, y, h, x0=0, x1=W):
    """Flag bands: black, red, green with white edging, total height h."""
    e = max(2, h // 14); b = (h - 2 * e) / 3
    ys = [y, y + b, y + b + e, y + 2 * b + e, y + 2 * b + 2 * e, y + h]
    for (a, z), c in zip(zip(ys, ys[1:]), (BLACK, WHITE, RED, WHITE, GREEN)): d.rectangle([x0, a, x1, z], fill=c)


def shield(d, cx, cy, s):
    """Shield motif: an upright ellipse, black rims, red body, a white band and a white centre (no national emblem)."""
    d.ellipse([cx - s * 0.42, cy - s, cx + s * 0.42, cy + s], fill=BLACK)
    d.ellipse([cx - s * 0.34, cy - s * 0.9, cx + s * 0.34, cy + s * 0.9], fill=RED)
    d.rectangle([cx - s * 0.05, cy - s * 0.86, cx + s * 0.05, cy + s * 0.86], fill=WHITE)
    d.ellipse([cx - s * 0.12, cy - s * 0.12, cx + s * 0.12, cy + s * 0.12], fill=WHITE)


def overlay(im, caption=None):
    d = ImageDraw.Draw(im)
    bands(d, H - 18, 18)
    if caption:
        f = font(34, True); d.rectangle([60, 60, 60 + d.textlength(caption, font=f) + 40, 120], fill=(16, 16, 16))
        d.text((80, 68), caption, font=f, fill=CREAM)
    f = font(24); t = CLAIM
    d.rectangle([60, H - 80, 60 + d.textlength(t, font=f) + 30, H - 40], fill=(16, 16, 16))
    d.text((75, H - 75), t, font=f, fill=CREAM)
    return im


def card(title, sub):
    im = Image.new("RGB", (W, H), CREAM); d = ImageDraw.Draw(im)
    bands(d, 0, 90); bands(d, H - 90, 90)
    shield(d, W // 2, 380, 150)
    ft, fs = font(84, True), font(36)
    d.text(((W - d.textlength(title, font=ft)) / 2, 580), title, font=ft, fill=BLACK)
    d.text(((W - d.textlength(sub, font=fs)) / 2, 700), sub, font=fs, fill=(60, 60, 60))
    f = font(24); d.text(((W - d.textlength(CLAIM, font=f)) / 2, H - 150), CLAIM, font=f, fill=(60, 60, 60))
    return im


def wipe(a, b, n=14):
    """Flag-band wipe from a to b: the bands sweep across, b is revealed behind them."""
    out = []
    for k in range(n):
        t = (k + 1) / n; x = int(-W * 0.3 + t * W * 1.6)
        im = b.copy(); im.paste(a.crop((x, 0, W, H)), (x, 0)) if x < W else None
        d = ImageDraw.Draw(im)
        for j, c in enumerate((BLACK, WHITE, RED, WHITE, GREEN)):
            off = j * 36 - 90; d.polygon([(x + off, 0), (x + off + 40, 0), (x + off + 40 - 200, H), (x + off - 200, H)], fill=c)
        out.append(im)
    return out


def orbit(folder, caption):
    fr = [Image.open(f).convert("RGB").resize((W, H), Image.LANCZOS) for f in sorted((ROOT / folder).glob("frame_*.png"))]
    seq = fr + fr[-2:0:-1]  # forwards and back
    out = []
    for i in range(len(seq)):
        a, b = seq[i], seq[(i + 1) % len(seq)]
        for k in range(3): out.append(overlay(Image.blend(a, b, k / 3), caption))
    return out


tmp = Path(tempfile.mkdtemp()); frames = []
title = card("Talanta Stadium", "Raila Odinga Talanta Stadium, Ngong Road, Nairobi  ·  digital twin test reel")
end = card("Explore in 3D", "Cycles renders from the twin model  ·  internal test")
day = orbit("blender/out/scroll_test_01", "Cityside · 10:30")
dusk = orbit("blender/out/scroll_test_02", "Hillside · 18:05, lit")
frames += [title] * int(2.5 * FPS) + wipe(title, day[0]) + day + wipe(day[-1], dusk[0]) + dusk + wipe(dusk[-1], end) + [end] * int(2 * FPS)
for i, im in enumerate(frames): im.save(tmp / f"f{i:05d}.png", compress_level=1)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(tmp / "f%05d.png"), "-c:v", "libx264",
                "-preset", "slow", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(OUT)], check=True)
for f in tmp.iterdir(): f.unlink()
print("reel", OUT, len(frames), "frames", round(len(frames) / FPS, 1), "s", OUT.stat().st_size, "bytes")
