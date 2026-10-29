# Cloud work order: web_hero_v3 bundle and the time-of-day sets (2026-10-29)

Date: 2026-10-29
Project: Talanta twin (M5)
From: the local lead session
To: the TALANTA cloud session
Branch: `wo/web-hero-v2`. Pull it first. Work only on this branch.

## Basis

The four Kaggle GPU light sets are in the branch:
- assets/web_hero_v2_bake_0730/lightmaps/0730_gpu
- assets/web_hero_v2_bake_1030/lightmaps/1030_gpu
- assets/web_hero_v2_bake_1805/lightmaps/1805_gpu
- assets/web_hero_v2_bake_2000/lightmaps/2000_gpu

Each folder holds maps/, bake_log.json, run_record.json and talanta_web_baked.blend (the frozen_FL scene with the maps). The 0730 and 2000 folders also hold the panorama in env/. The 1030 and 1805 panoramas are rendering on Kaggle now. The laptop adds them to the same folders.

The app will switch light maps by time of day (ENV-01). Geometry, UVs, AO and albedo are the same at every time. Only the light maps, the light scale and the panorama change.

## T1. The base bundle web_hero_v3 (start now)

1. Build the bundle from the 0730_gpu set with export_web.py and post_glb.mjs, desktop and phone, as for web_hero_v2_1. Use `base=` to point at that set. Do not edit the files in the bake set folders.
2. Reuse the 07:30 ground tiles of web_hero_v2_1 (ground_tiles.py reuse). Do not render new tiles.
3. Put the panoramas of 0730 and 2000 in the bundle env/. Add 1030 and 1805 when they are in the branch.
4. Write assets/web_hero_v3/README.md: source sets, commands, sizes, and the labels (Visualization for traffic and people).
5. Keep the phone tier 1 under 40 MB and the desktop bundle under 250 MB.
6. Commit as Munene, no AI attribution. Push after the bundle is committed.

## T2. The time-of-day sets (after the laptop pushes the post_glb.mjs tod mode)

The laptop adds a `tod=<HHMM>` mode to post_glb.mjs. It writes only the light maps of one time and a tod.json.

1. Run it for 0730, 1030, 1805 and 2000 against web_hero_v3, desktop and phone.
2. Commit the sets to assets/web_hero_v3/lightmaps/ and lightmaps_phone/. Push.
3. Report the size of each set.

## Rules

- No security-sensitive detail (exits, camera positions, control rooms).
- No reference frame as a texture.
- If a group list or a map size differs between the sets, stop and report. Do not re-bake.
