# web_hero_v1 bundle

Environment pass for the web twin (cloud session 2026-10-19). The binaries are not in git (AGENTS.md rule 1 and the
lead's instruction). They live in `blender/out/web_hero/web_hero_v1/` on the build machine and are meant to ship as
the GitHub prerelease `web_hero_v1`. `web_hero_v1_manifest.json` (this folder) lists every file with its size and
sha256, so an upload can be checked against it.

Release status: not uploaded. This session has no tool that can create a GitHub release or upload assets.
A person with release access uploads the folder, or grants that access to an agent.

## Contents (148.95 MB of 250 MB)

| file | MB | what |
|---|---|---|
| models/talanta_hero.glb | 32.65 | stadium, bowl, roof, pitch, seats (63,107 instanced) and VIP chairs; lightmaps |
| models/talanta_site.glb | 74.08 | site, forecourt, suburbs (roof and wall colours, windows as geometry), canopy (31,976 instanced trees through web_lod, crossed-quad impostors beyond 300 m), traffic (Visualization); lightmaps |
| ground/L0_*.ktx2, ground/L1_*.ktx2 | 8.8 (61 tiles) | 07:30 ground colour, 0.25 m/px within 640 m (5 x 5) and 0.5 m/px to 1,536 m (6 x 6), 1024 px each |
| ground/tiles.json | | x0, z0 (west and north edges, app frame), size, level, m_per_px per tile |
| env/talanta_pano_0730.exr, env/talanta_pano_1730.exr | 12.13, 12.39 | 8192 x 4096 equirect, half-float DWAB, everything beyond 800 m only |
| env/talanta_pano_*_2048.hdr | 4.36, 4.57 | 2048 px Radiance HDR versions |

Codecs: geometry EXT_meshopt_compression (16-bit positions); lightmaps (light, AO) KTX2 UASTC + RDO + zstd;
colour (albedo, shield paint, impostor atlas, ground tiles) KTX2 ETC1S. The 4096 suburbs lightmaps are resampled
to 3072, because the Basis encoder limit is 12.6 Mpix per image.

## How it was made

1. `bake_lightmaps.py 128`: all groups at 07:30 (albedo 4, AO 64, light 128 samples). Times per batch are in
   `blender/out/web_hero/maps/stages.json`. Stage totals: albedo 0.44 h, AO 3.60 h, light 6.95 h.
2. `export_web.py`, then `node/post_glb.mjs bundle=web_hero_v1`.
3. `ground_tiles.py blender/out/web_hero/ground_png 16`: 61 orthographic tiles, 7,168 s.
4. `render_panorama.py 128 8192 preset=morning_golden|evening_golden near=800 out=blender/out/web_hero/web_hero_v1/env`:
   1,334 s and 1,380 s.
5. `node/post_glb.mjs bundle=web_hero_v1 skip_models`: ground tiles to KTX2, tiles.json and the manifest.

## For the app

- Lightmaps: move each baked material's emissiveMap to lightMap (texCoord in extras.talanta_lightmap), set emissive
  to black and lightMapIntensity to extras.talanta_lightmap.intensity. A KTX2Loader is required.
- LOD: nodes share extras.lod_group; extras.lod and extras.lod_switch_m give the levels (0, 300, 1000 m).
- Ground tiles are unlit colour with the 07:30 light and shadow baked in. Draw level 0 over level 1. Under buildings
  and the stadium they are dark (ground in full shadow), and the GLB geometry covers them.
- The panoramas show only what lies beyond 800 m in plan, seen from 150 m above the pitch centre. Below about 10.6 deg
  under the horizon they show the bare sky dome, which the GLBs cover.
- Labels: traffic is Visualization. No people are included. No reference frame is used as a texture.
