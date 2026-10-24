"""Pass F sheet: a render from camera P01 against the dusk aerial photo (internal only: the photo is a reference, never
public). Writes <out>/sheets/P01_vs_photo_internal.jpg: photo and render side by side, then a 50 % overlay with the
photo's edges in cyan, so layout differences show.
Run: ~/.venvs/gis/bin/python blender/scripts/photo_sheet.py <render.png> <out_dir> [label]
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageChops

ROOT = Path(__file__).resolve().parents[2]
PHOTO = ROOT / "research/reference/dusk_aerial_finished_2026-10-17.jpg"
ren, out = Path(sys.argv[1]), Path(sys.argv[2]); label = sys.argv[3] if len(sys.argv) > 3 else ren.stem
p = Image.open(PHOTO).convert("RGB"); W, H = 960, round(960 * p.height / p.width)
p = p.resize((W, H), Image.LANCZOS); r = Image.open(ren).convert("RGB").resize((W, H), Image.LANCZOS)
edges = p.convert("L").filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 60 else 0)
ov = Image.blend(r, p, 0.5); cyan = Image.new("RGB", (W, H), (0, 230, 255)); ov.paste(cyan, (0, 0), edges)
redges = r.convert("L").filter(ImageFilter.FIND_EDGES).point(lambda v: 255 if v > 60 else 0)
ed = Image.new("RGB", (W, H), (0, 0, 0)); ed.paste(cyan, (0, 0), edges); ed.paste(Image.new("RGB", (W, H), (255, 80, 40)), (0, 0), redges)
sheet = Image.new("RGB", (2 * W, 2 * H + 60), (20, 20, 22)); d = ImageDraw.Draw(sheet)
for im, (x, y), t in ((p, (0, 30), "dusk photo 2026-10-17 (internal reference)"), (r, (W, 30), label),
                      (ov, (0, H + 60), "50 % overlay, photo edges cyan"), (ed, (W, H + 60), "edges: photo cyan, render orange")):
    sheet.paste(im, (x, y)); d.text((x + 8, y - 22), t, fill=(230, 230, 230))
(out / "sheets").mkdir(parents=True, exist_ok=True)
dst = out / "sheets" / f"{ren.stem.split('_')[0]}_vs_photo_internal.jpg"; sheet.save(dst, quality=88)
print(dst)
