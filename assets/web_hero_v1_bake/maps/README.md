# maps/ (recovered 2026-10-20)

The original baked maps (`maps/*.png`, 8-bit sRGB, written by `blender/web_hero/bake_lightmaps.py`) were never pushed and were lost when the build container was reclaimed. No copy survived.

These PNGs were decoded from the KTX2 textures inside the `web_hero_v1` GLBs (branch `assets/web_hero_v1`, `models/`) with `extract_v1_maps.mjs` and the three.js Basis transcoder. They are lossy:
- Lightmaps and AO were stored as UASTC with RDO. Albedo was stored as ETC1S.
- The suburbs maps were stored at 3072 px; the bake was 4096 px.
- Only the maps the GLBs carry are here: every `*_light`, plus the AO and albedo maps that the export used. The ground, forecourt and site_built AO and albedo bakes were not exported and are gone.

The encoding matches the original PNGs (sRGB, light divided by `light_scale` from `stages.json`), so `export_web.py` can use them in place of the bakes.
