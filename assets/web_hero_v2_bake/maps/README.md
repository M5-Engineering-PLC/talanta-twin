# maps/ (web_hero_v2 bake)

Baked maps of `blender/web_hero/bake_lightmaps.py` for the web_hero_v2 bundle (work order
engineering/cloud_web_hero_v2_2026-10-24.md, W2), on the pass K scene step_FK, finished state, look layer on, light
preset morning_golden (07:30 EAT), 128 light samples, 64 AO samples, 4 albedo samples. 8-bit sRGB PNG:
`<group>_light.png` = sRGB(light / light_scale), with `light_scale` per group in `stages.json`; `<group>_ao.png`
linear AO; `<group>_albedo.png` sRGB diffuse colour.

The bake runs in parts of less than 4 h; this branch is updated after each part (the commit message names the part).
`stages.json` lists every finished batch with its time and object signature; a rerun with the same scene skips the
batches already on disk. Restore in a new container (repo root):

    git fetch origin assets/web_hero_v2_bake
    mkdir -p blender/out/web_hero && git archive FETCH_HEAD maps | tar -x -C blender/out/web_hero/

Internal build data. No reference frame or photo is used as a texture. The record of the parts is
blender/web_hero/WEB_HERO_V2.md on the work branch.
