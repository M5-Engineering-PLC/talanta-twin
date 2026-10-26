# web_preview_g (unbaked, app testing only)

Unbaked preview export of the current scene (step_FX: the facade fix of 2026-10-20 plus steps L, T, B, R, F), made
for app testing only. Not a release, not web_hero_v2, and not a replacement for web_hero_v1.

- No lightmaps and no bake: plain glTF materials (base colour, roughness, metallic). Light the scene in the app.
- Level of detail and instancing as web_hero_v1 (export_web.py: LOD1 at 300 m, LOD2 at 1 km, EXT_mesh_gpu_instancing,
  meshopt). Needs KTX2Loader (shield paint, tree impostor atlas) and MeshoptDecoder.
- No ground tiles and no panoramas: the ground is the terrain_site mesh with the app's own ground_site.jpg (pale).
- Parts tagged internal_only (brand marks) are excluded.
- manifest.json lists every file with its size and sha256.
- Estimated geometry and colours (parameter ledger). Traffic and people are Visualization.
- Credits: see the main branch (CREDITS.md), including the CC-BY nganya model.

Built by blender/web_hero/stage_unbaked.py, export_web.py base=preview_g unbaked, node/post_glb.mjs base=preview_g
bundle=web_preview_g (branch m5/vibrant-ride-5er9ju).
