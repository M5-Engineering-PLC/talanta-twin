"""Stage a web hero bundle into the app for a local preview of hero mode (?hero).

Run from the repo root:  python3 blender/web_hero/stage_app_preview.py [bundle]   (default bundle: web_hero_v1)
Copies blender/out/web_hero/<bundle>/models/*.glb to app/public/models/ and the 2048 Radiance HDR of the 07:30
panorama to app/public/env/ and the ground tiles (ground/*.ktx2 and tiles.json, when the bundle has them) to
app/public/ground/, then writes app/public/models/manifest.json in the format app/src/hero/loadHero.js and
environment.js read (models, files, ground.index for groundTiles.js, environment.file / file_2048 under app/public/env/, tone_mapping, time).
The app loads panoramas with HDRLoader, so the 8K EXR is not staged; the 2048 HDR serves both entries.
Local preview only: the staged files are binaries and are never committed (list app/public/models/ and
app/public/env/ and app/public/ground/ in .git/info/exclude).
"""
import json, os, shutil, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUNDLE = sys.argv[1] if len(sys.argv) > 1 else "web_hero_v1"
B = ROOT / "blender/out/web_hero" / BUNDLE
MODELS, ENV, GROUND = ROOT / "app/public/models", ROOT / "app/public/env", ROOT / "app/public/ground"
MODELS.mkdir(parents=True, exist_ok=True); ENV.mkdir(parents=True, exist_ok=True)

m = json.loads((B / "manifest.json").read_text())
models = {}
for k, v in m["models"].items():
    name = os.path.basename(v["file"]); shutil.copy2(B / "models" / name, MODELS / name)
    models[k] = {**v, "file": f"app/public/models/{name}"}
pano = m["panoramas"][0]  # 07:30 morning_golden
hdr_name = os.path.basename(pano["file_2048"]); shutil.copy2(B / "env" / hdr_name, ENV / hdr_name)
hdr = f"app/public/env/{hdr_name}"
ground = []
if (B / "ground/tiles.json").exists():
    shutil.rmtree(GROUND, ignore_errors=True); shutil.copytree(B / "ground", GROUND)
    ground = sorted(f"app/public/ground/{f.name}" for f in GROUND.iterdir())

out = {"generated": m["generated"], "source": f"staged from blender/out/web_hero/{BUNDLE} (local preview only)",
       "frame": m["frame"], "time": {"date": m["sun"]["date"], "local": m["sun"]["local"]}, "sun": m["sun"],
       "files": [{"file": v["file"], "bytes": (ROOT / v["file"]).stat().st_size} for v in models.values()]
                + [{"file": f, "bytes": (ROOT / f).stat().st_size} for f in [hdr] + ground],
       "models": models, "lightmaps": m["lightmaps"], "environment": {**pano, "file": hdr, "file_2048": hdr},
       "tone_mapping": {"blender_view_transform": "AgX", "blender_exposure_ev": -1.0,
                        "three": "AgXToneMapping, toneMappingExposure = 2^-1 (approved morning look)"},
       "labels": m["labels"]}
if ground: out["ground"] = {"index": "app/public/ground/tiles.json"}
(MODELS / "manifest.json").write_text(json.dumps(out, indent=1) + "\n")
print("staged", BUNDLE, "->", MODELS.relative_to(ROOT), ENV.relative_to(ROOT), f"{len(ground)} ground files", sum(f["bytes"] for f in out["files"]), "bytes")
