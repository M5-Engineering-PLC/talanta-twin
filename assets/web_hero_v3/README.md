# web_hero_v3 bundle (internal, private)

Status 2026-10-29: T1 done and pushed (base bundle from the 0730_gpu set; desktop 151.0 MB, phone tier 1 37.75 MB). T2 (time-of-day sets) waits for the post_glb.mjs tod mode.

## Source sets

- Base: assets/web_hero_v2_bake_0730/lightmaps/0730_gpu (Kaggle GPU, 128 samples, preset morning_golden, 2026-01-15 07:30 EAT; scene blender/out/frozen_FL.blend, bake script 4cf04ca). The files in that folder are not changed.
- Ground tiles: the 07:30 tiles of web_hero_v2_1 (assets/web_hero_v2_1/ground, 62 files). No new tiles are rendered.
- Panoramas in env/:
  - talanta_pano_0730.exr and talanta_pano_0730_2048.hdr from the 0730_gpu set.
  - talanta_pano_2030.exr and talanta_pano_2030_2048.hdr from the 2000_gpu set. The 2000 set uses the manifest sun "night" (20:30 EAT), so the file names say 2030.
  - 1030 and 1805: they are added when the laptop puts them in the bake folders.
- Check before the build: the four GPU sets (0730, 1030, 1805, 2000) have the same 40 groups, the same objects in each group and the same 87 map files at the same sizes.

## Commands

From the repository root. The work folder blender/out/web_hero/v3_0730 holds symlinks to maps/, bake_log.json and talanta_web_baked.blend of the 0730_gpu set; export/ and web_hero_v3/ are written there.

    blender -b --factory-startup --python-exit-code 1 --python blender/web_hero/export_web.py -- base=v3_0730
    node blender/web_hero/node/post_glb.mjs base=v3_0730 bundle=web_hero_v3
    node blender/web_hero/node/post_glb.mjs base=v3_0730 bundle=web_hero_v3 phone

Before post_glb.mjs: web_hero_v3/ground/ is a copy of assets/web_hero_v2_1/ground/, and web_hero_v3/env/ holds the panoramas above. Times: export 514 s, post_glb desktop 3,369 s, phone 148 s (cloud CPU).

## Sizes

| Part | Bytes |
|---|---|
| models/talanta_hero.glb | 35,157,680 |
| models/talanta_site.glb | 89,195,500 |
| ground/ (62 files) | 8,282,082 |
| env/ (4 files) | 18,386,938 |
| desktop bundle (manifest.json, 68 files) | 151,022,200 (budget 250,000,000) |
| models_phone/talanta_hero_phone.glb | 8,535,532 |
| models_phone/talanta_site_phone.glb | 19,693,428 |
| phone tier 1 (manifest_phone.json) | 37,753,591 (budget 40,000,000) |

## Notes

- manifest.json lists no panoramas ("panoramas": []). The Kaggle runs did not write panorama_log_<HHMM>.json (the script failed after it saved the images; fixed in c798e62), and post_glb.mjs reads only the logs of 0730 and 1730. The panorama files are in env/ and in the "files" list with their sha256.
- Geometry, UVs, AO and albedo are the same at every time. Only the light maps, the light scale and the panorama change.

## Labels

- Estimated geometry and colours (parameter ledger).
- Traffic and people are Visualization.
- No reference frame is used as a texture.
- No exits, camera positions or control rooms are added.
