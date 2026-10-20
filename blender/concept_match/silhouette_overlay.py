"""Silhouette of the stadium from the landing cameras over landing mockups 06 and 07 (internal sheet).

Renders a flat mask of the bowl (shell, facade detail, plinth) from L06 and L07 with Workbench, then draws its outline
on the mockup at the mockup size (the landing cameras were solved on the full mockup frame, solve_cameras.py landing).
The mockups are a look and layout target only: they are read here, never used as a texture.
Run from the repo root:
  ~/.venvs/bpy/bin/python blender/concept_match/silhouette_overlay.py <mockup dir> <out dir> [blend]
Writes <out>/L0N_silhouette_mask.png and <out>/silhouette_overlay_L06_L07_internal.jpg, and prints the mask boxes
next to the solve targets.
"""
import json, sys
from pathlib import Path
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "blender/scripts")); sys.path.insert(0, str(ROOT / "blender/concept_match"))
from cameras import load_cameras

MOCK, OUT = Path(sys.argv[-3] if len(sys.argv) > 3 else sys.argv[-2]), ROOT / (sys.argv[-2] if len(sys.argv) > 3 else sys.argv[-1])
BLEND = sys.argv[-1] if len(sys.argv) > 3 else "blender/out/talanta_blockout.blend"
OUT.mkdir(parents=True, exist_ok=True)
VIEWS = {"L06": "06-hillside-landing-mockup.png", "L07": "07-cityside-landing-mockup.png"}
KEEP = {"shell", "facade_detail", "plinth", "shields"}

bpy.ops.wm.open_mainfile(filepath=str(ROOT / BLEND))
s = bpy.context.scene
_, cams = load_cameras(s, ROOT / "app/cameras/manifest.json")
for o in s.objects:
    if o.type in ("MESH", "CURVE"):
        names = {c.name for c in o.users_collection}
        o.hide_render = not (names & KEEP)
s.render.engine = "BLENDER_WORKBENCH"
sh = s.display.shading; sh.light = "FLAT"; sh.color_type = "SINGLE"; sh.single_color = (1, 1, 1)
sh.show_cavity = False; sh.show_shadows = False; sh.show_object_outline = False
s.view_settings.view_transform = "Standard"; s.view_settings.exposure = 0; s.view_settings.look = "None"
w = bpy.data.worlds.new("black"); s.world = w; w.color = (0, 0, 0)
s.render.resolution_x, s.render.resolution_y, s.render.resolution_percentage = 1672, 941, 100
s.render.film_transparent = False

from PIL import Image, ImageDraw, ImageFilter
targets = json.load(open(ROOT / "blender/data/landing_cameras.json")) if (ROOT / "blender/data/landing_cameras.json").exists() else {}
tiles, report = [], {}
for cid, mock in VIEWS.items():
    s.camera = cams[cid]
    path = OUT / f"{cid}_silhouette_mask.png"; s.render.filepath = str(path); bpy.ops.render.render(write_still=True)
    m = np.asarray(Image.open(path).convert("L")) > 128
    ys, xs = np.nonzero(m)
    box = [xs.min() / m.shape[1], ys.min() / m.shape[0], xs.max() / m.shape[1], ys.max() / m.shape[0]] if len(xs) else None
    report[cid] = {"mask_box": [round(v, 4) for v in box] if box else None}
    im = Image.open(MOCK / mock).convert("RGB").resize((1672, 941))
    edge = Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(5))
    im.paste((0, 255, 255), mask=edge)
    ImageDraw.Draw(im).text((12, 900), f"{cid}: model outline (cyan) over mockup {mock[:2]} - internal", fill=(255, 255, 0))
    tiles.append(im)
sheet = Image.new("RGB", (1672, 941 * len(tiles)))
for k, t in enumerate(tiles): sheet.paste(t, (0, 941 * k))
sheet.save(OUT / "silhouette_overlay_L06_L07_internal.jpg", quality=88)
print("SILHOUETTE", json.dumps(report))
