# assets/web_hero_v2_bake_1030: P2 time-of-day bake set 10:30 (internal)

Lightmaps of the web_hero_v2 twin at 10:30 EAT on 2026-01-15 (sky preset daylight_artistic, the light of the L07 still), baked on the same geometry and UVs as web_hero_v2 (blender/web_hero/bake_lightmaps.py, TALANTA_BAKE_PRESET=daylight_artistic, TALANTA_BAKE_OUT=blender/out/web_hero/lightmaps/1030).
Scene: blender/out/frozen_FL.blend = frozen_FK.blend plus the stand detail of the seat re-check (seat model v2, aisle step nosings, rail posts and rail ends in bowl_detail; Munene 2026-10-26). The baked groups and their UVs are unchanged; the new stand parts export unbaked.
Layout as the 07:30 set (assets/web_hero_v2_bake), under lightmaps/1030/: maps/<group>_{light,ao,albedo}.png, maps/stages.json (light scale and time per batch), bake_log.json and talanta_web_baked.blend after the final run, env/ with the 10:30 panorama (8192 x 4096 EXR, 2048 HDR, near=800).
Encoding: light png = sRGB(light / light_scale); multiply by light_scale (stages.json, bake_log.json) for linear light on a white diffuse surface.
Labels: estimated geometry and colours (parameter ledger). Traffic is Visualization. No reference frame is used as a texture.
