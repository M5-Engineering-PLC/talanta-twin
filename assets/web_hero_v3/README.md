# web_hero_v3 bundle (internal, private)

Status 2026-11-01: T1 done (base bundle from the 0730_gpu set). T2 done: the time-of-day sets 0730, 1030, 1805 and 2000 are in lightmaps/ and lightmaps_phone/. The painted images of the four GLBs were repaired on 2026-11-01 (see Repair): desktop 151.5 MB, phone tier 1 38.21 MB.

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
| models/talanta_hero.glb | 35,180,644 |
| models/talanta_site.glb | 89,633,388 |
| ground/ (62 files) | 8,282,082 |
| env/ (4 files) | 18,386,938 |
| desktop bundle (manifest.json, 68 files) | 151,483,052 (budget 250,000,000) |
| models_phone/talanta_hero_phone.glb | 8,558,496 |
| models_phone/talanta_site_phone.glb | 20,131,348 |
| phone tier 1 (manifest_phone.json) | 38,214,475 (budget 40,000,000) |

## Time-of-day sets (T2)

    node blender/web_hero/node/post_glb.mjs tod=<HHMM> base=assets/web_hero_v2_bake_<HHMM>/lightmaps/<HHMM>_gpu bundle=web_hero_v3 ref=assets/web_hero_v2_bake_0730/lightmaps/0730_gpu [phone]
    node blender/web_hero/node/post_glb.mjs reindex bundle=web_hero_v3

| Time | lightmaps/ (desktop, UASTC) | lightmaps_phone/ (ETC1S) |
|---|---|---|
| 0730 | 62,419,463 | 3,584,386 |
| 1030 | 56,455,008 | 3,369,446 |
| 1805 | 62,034,356 | 3,610,393 |
| 2000 | 60,573,493 | 3,667,764 |

The bytes are the 40 light maps of each set; manifest.json tod_bytes (241,513,551) and manifest_phone.json tod_bytes (14,263,005) also count the four tod.json files. The 1030 and 1805 tod.json have no panorama yet.

## Repair (2026-11-01)

The T1 GLBs carried a 1x1 KTX2 placeholder named "Image" (313 bytes) in place of painted images. WebGPU rejects a 1x1 block-compressed texture and loses the device.

- Cause: the file images of the 0730_gpu talanta_web_baked.blend are all unpacked and point at the Kaggle extraction folder (//../../../../tmp/talanta/pack/talanta_render_pack/...). That folder was not there at export, so the glTF exporter wrote a 1x1 placeholder for each painted image. post_glb.mjs dedup then merged the three tree materials that held the same placeholder.
- Lost: shield (shield_paint@stadium_ornament.001), island_tree_02_leaves_diff_1k (canopy_tint_1.001), and the materials canopy_bark.001 (jacaranda_tree_trunk_diff_1k, 140 primitives) and canopy_tint_4.001 (jacaranda_tree_leaves_diff_1k, 2 primitives), which had been merged into canopy_tint_1.001.
- Fix: blender/web_hero/node/repair_images.mjs bundle=web_hero_v3 ref=web_hero_v2_1, on the GLB bytes. The four images are encoded from the repo sources (blender/textures/shield.png, blender/assets/foliage/...) with the post_glb.mjs ETC1S settings; they are byte-identical to the web_hero_v2_1 images. The two materials are re-created from web_hero_v2_1, and their primitives are matched by mesh name, primitive index and index count (the slot order agrees with the blend). No re-export, no rebake: every accessor, node, light map and AO map is unchanged, and the T2 sets are untouched.
- Guards: post_glb.mjs stops if an embedded image (or a tod light map) has a side that is not a multiple of 4; export_web.py stops if a painted material's image file is missing.

| Image | Size | talanta_hero.glb | talanta_site.glb | talanta_hero_phone.glb | talanta_site_phone.glb |
|---|---|---|---|---|---|
| shield | 512x1024, 23,280 B | yes | | yes | |
| island_tree_02_leaves_diff_1k | 1024x1024, 80,956 B | | yes | | yes |
| jacaranda_tree_trunk_diff_1k | 1024x1024, 230,572 B | | yes | | yes |
| jacaranda_tree_leaves_diff_1k | 1024x1024, 125,770 B | | yes | | yes |

## Notes

- manifest.json lists no panoramas ("panoramas": []). The Kaggle runs did not write panorama_log_<HHMM>.json (the script failed after it saved the images; fixed in c798e62), and post_glb.mjs reads only the logs of 0730 and 1730. The panorama files are in env/ and in the "files" list with their sha256.
- Geometry, UVs, AO and albedo are the same at every time. Only the light maps, the light scale and the panorama change.

## Labels

- Estimated geometry and colours (parameter ledger).
- Traffic and people are Visualization.
- No reference frame is used as a texture.
- No exits, camera positions or control rooms are added.
