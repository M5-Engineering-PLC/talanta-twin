"""Interior pass sheets and metrics: render | tour frame for C30-C35 (blender/data/interior_cameras.json).
Per view: CIELAB mean and spread, edge density and highlight clipping for the whole frame and its top, middle and
bottom thirds, render against frame (same definitions as metrics.py). Frames are internal reference only.
Run: ~/.venvs/gis/bin/python blender/concept_match/interior_metrics.py <pass_dir>
"""
import csv, json, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, str(Path(__file__).resolve().parent))
from metrics import load, lab, edges, crop, W, H

ROOT = Path(__file__).resolve().parents[2]
BANDS = {"all": [0, 0, 1, 1], "top": [0, 0, 1, 1 / 3], "middle": [0, 1 / 3, 1, 2 / 3], "bottom": [0, 2 / 3, 1, 1]}


def main(pdir):
    pdir = ROOT / pdir; cams = json.loads((ROOT / "blender/data/interior_cameras.json").read_text())["cameras"]
    log = {json.loads(l)["camera"]: json.loads(l) for l in (pdir / "render_log.jsonl").read_text().splitlines()}
    rows = []
    for c in cams:
        rp = pdir / f"{c['id']}_overcast_check.png"
        if not rp.exists(): continue
        r, f = load(rp), load(ROOT / c["frame"]); rl, fl = lab(r), lab(f); re_, fe = edges(rl[..., 0]), edges(fl[..., 0])
        for n, b in BANDS.items():
            a, k = crop(rl, b).reshape(-1, 3), crop(fl, b).reshape(-1, 3)
            rows.append({"camera": c["id"], "metric": f"band:{n}",
                         "render": "L %.1f a %.1f b %.1f sdL %.1f edges %.3f" % (*a.mean(0), a[:, 0].std(), crop(re_, b).mean()),
                         "frame": "L %.1f a %.1f b %.1f sdL %.1f edges %.3f" % (*k.mean(0), k[:, 0].std(), crop(fe, b).mean()),
                         "difference": "dE76 %.1f dL %.1f dEdges %+.3f" % (np.linalg.norm(a.mean(0) - k.mean(0)), a[:, 0].mean() - k[:, 0].mean(), crop(re_, b).mean() - crop(fe, b).mean())})
        rc, fc = (r.max(-1) >= 250 / 255).mean(), (f.max(-1) >= 250 / 255).mean()
        rows.append({"camera": c["id"], "metric": "highlight clipping (share >= 250)", "render": "%.4f" % rc, "frame": "%.4f" % fc, "difference": "%+.4f" % (rc - fc)})
        rows.append({"camera": c["id"], "metric": "render time (s)", "render": "%.0f" % log.get(c["id"], {}).get("seconds", 0), "frame": "", "difference": ""})
        sheet = Image.new("RGB", (2 * W, H))
        for i, (img, label) in enumerate(((r, f"{c['id']} render (Visualization)"), (f, "tour frame " + Path(c["frame"]).stem.split("_")[1] + " (internal only)"))):
            t = Image.fromarray((img * 255).astype(np.uint8)); d = ImageDraw.Draw(t)
            d.rectangle([0, 0, 8 * len(label) + 12, 18], fill=(0, 0, 0)); d.text((6, 4), label, fill=(255, 255, 255)); sheet.paste(t, (i * W, 0))
        sheet.save(pdir / f"{c['id']}_side_by_side.jpg", quality=86)
    with open(pdir / "metrics.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, ["camera", "metric", "render", "frame", "difference"], lineterminator="\n"); w.writeheader(); w.writerows(rows)
    print(len(rows), "rows")


if __name__ == "__main__":
    main(sys.argv[1])
