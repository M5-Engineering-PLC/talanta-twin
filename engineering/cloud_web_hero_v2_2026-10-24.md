# Cloud work order: record fixes, W re-bake, web_hero_v2 (2026-10-24)

Date: 2026-10-24
Project: Talanta twin (M5)
From: the local lead session
To: the cloud Talanta build chat
Status: active work order. Munene approved the 4K stills in blender/renders/hero_artistic_04/ on 2026-10-24.
Branch: `wo/web-hero-v2`, from `main` at f1ecf9b

Read this file first. Then read AGENTS.md, BRANCHING.md and blender/STATUS.md.

## Branch rules from now on

- All work branches are merged into `main` and deleted. This includes `ccr-11a40cef-r87r85` and `lead/layout-audit-01`. Do not push to them again.
- Work only on `wo/web-hero-v2`. Do not make a new branch.
- Commit as Munene's git identity. Do not add AI attribution. Push after each item.
- The lead opens the pull request into `main` from the laptop when this order is done.
- Do not put large binaries on this branch. The bake maps and the bundle go to orphan branches (see W2 and W4). Check images on this branch are JPG, 1 MB or less each.

The AI image rule stays: research/reference/dusk_aerial_finished_2026-10-17.jpg is AI-generated. It is never evidence.

## Basis

Sol reviewed pass K read-only (dc559e7..3f672b2). The verdict was "approve now" for the 4K stills and the W re-bake. Sol found four follow-up items. W0 below holds the items that this order fixes.

## W0. Record fixes (no renders)

1. Ledger generator. gis/scripts/build_parameter_ledger.py overwrites gis/parameter_ledger.csv, but it does not contain the 17 records that pass K added (rows 466 to 482). Add these records to the generator. Then run the generator and make sure that the output is byte-identical to the committed CSV.
2. South plaza records. The ledger (gis/parameter_ledger.csv:472) gives about 110 x 135 m. blender/renders/pass_k_check_01/README.md gives 110 x 125 m. Measure the size from blender/data/plaza_south_k.json and correct the wrong record with a correction row. Do not edit old rows.
3. In the same README (line 111), the text says that the two centre estimates agree within the 25 m uncertainty. They are 33 m apart, so this is not true. Correct the text. Give the outline centre and the round-bed centre as two separate values. Keep the solved position. Do not move the plaza.
4. In blender/renders/matchday_01/README.md, add a note: do not use M02 in a presentation until the night-lighting gap is corrected.
5. In blender/renders/landing_pass_02/README.md, add a note: the F and H stills are superseded by hero_artistic_04.

## W1. Put passes I, J and K into the web export

The export and the bake do not include the new work now. blender/web_hero/export_web.py `SITE_COLS` and blender/web_hero/bake_lightmaps.py `GROUPS` only list the collections of steps L, F, R and B.

1. Add these collections to the bake groups and to `SITE_COLS`: `layout_pass_i`, `landmarks_pass_j`, `plaza_south_k`. Use the same `_own_meshes()` filter as `site_layout`. Give each a group name and an atlas size that suits its area.
2. Export `layout_cars_visualization` like `traffic_Visualization`. Keep the "Visualization" name in the export.
3. Make sure that no object from `layout_final` or `layout_final_cars_visualization` goes into the bake or the export. Add a check in export_web.py that stops the export if one does.
4. Build the scene as step_FK in the finished state, with the look layer on. The export must contain only objects that render in that state.
5. Make sure that the K4 grass material (`training_grass`, blender/grass_look.py) bakes to the albedo map. If its procedural variation does not survive the bake, write it as a gap.
6. Do not export security-sensitive detail: no exits, camera positions or control rooms (AGENTS.md rule 8). Objects marked `internal_only` stay out.
7. Run `bake_lightmaps.py ... test` (quarter-size atlases) and `uvonly` first. Write the group list, the atlas cover and the cost estimate in blender/web_hero/WEB_HERO_V2.md.

## W2. The bake, in parts of less than 4 h

The re-bake is costed at about 4.7 h CPU only if the web_hero_v1 stage maps still exist. The v1 bake maps exist only on the orphan branch `assets/web_hero_v1_bake` (43 maps recovered from the GLBs, lossy). A full bake from zero is about 11 h CPU (albedo 0.44 h, AO 3.60 h, light 6.95 h).

1. Find out what you can reuse. Write the result and the real cost estimate in WEB_HERO_V2.md before the first long run.
2. Split the bake into parts of less than 4 h each. The stages are saved in maps/stages.json and reused on restart.
3. The container can be lost between sessions. So after each part, push the finished maps and maps/stages.json to the orphan branch `assets/web_hero_v2_bake`. Make it like `assets/web_hero_v1_bake`. At the start of each session, restore the maps from that branch.
4. Record each part (groups, CPU time, result) in WEB_HERO_V2.md on `wo/web-hero-v2`.

## W3. Panoramas, ground tiles and export

1. `render_panorama.py` for 07:30 (`preset=morning_golden`) and 17:30, 8K, `near=800`.
2. `ground_tiles.py` (61 tiles).
3. `export_web.py`, then `node blender/web_hero/node/post_glb.mjs bundle=web_hero_v2`.
4. Do not change the files of `web_hero_v1`.

## W4. Bundle and check shots

1. Push the bundle (models/, ground/, env/, manifest.json with size and sha256 for each file) to the orphan branch `assets/web_hero_v2`.
2. Commit a copy of the manifest to `wo/web-hero-v2` as blender/web_hero/web_hero_v2_manifest.json.
3. Stage the bundle with `stage_app_preview.py` and take the hero screenshots with `node/shot_hero.mjs` from the L06 and L07 views. Put them next to the hero_artistic_04 stills in one internal sheet. Commit them as JPG, 1 MB or less each.
4. In WEB_HERO_V2.md, write the size of the bundle against the 250 MB limit, the load time in software GL, and the gaps.

Check that:
- The south plaza, the lens island, the landmark towers and the grass loop show in the web build.
- No west road, railway, station, footbridge or west car park shows.
- People and cars carry the "Visualization" label in the app.

## Stop

Stop after W4. Do not create a release. The laptop checks the manifest, runs `gh release create web_hero_v2 --prerelease`, switches the app (`app/tools/fetch_assets.mjs --bundle`) to web_hero_v2, and opens the pull request into `main`.

## Open questions that stay with the lead

- Ngando Flats, Racecourse Gardens and Liberty Centre keep their provisional footprints (4.5 m, 4.0 m and 11.5 m). Do not invent heights.
- A grass retune across the three skies is optional and is not part of this order.
