"""Side-by-side review sheet: a render next to reference frames, scaled to one height (internal only).

The sheet holds historian frames, so it is an internal review record (AGENTS.md rule 2): never a texture,
product build, pitch or public page.
Run: ~/.venvs/gis/bin/python blender/side_by_side.py <out.jpg> <render.png> <frame.jpg> [<frame.jpg> ...]
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw

out, paths = Path(sys.argv[1]), [Path(p) for p in sys.argv[2:]]
H = 540
ims = []
for p in paths:
    im = Image.open(p).convert("RGB"); ims.append(im.resize((round(im.width * H / im.height), H)))
sheet = Image.new("RGB", (sum(i.width for i in ims) + 8 * (len(ims) - 1), H + 26), (24, 24, 24))
d = ImageDraw.Draw(sheet); x = 0
for p, im in zip(paths, ims):
    sheet.paste(im, (x, 26)); d.text((x + 6, 7), ("render " if p.suffix == ".png" else "reference ") + p.name, fill=(230, 230, 230)); x += im.width + 8
sheet.save(out, quality=88)
print(out, sheet.size)
