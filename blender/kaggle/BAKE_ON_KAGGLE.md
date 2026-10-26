# P2 bakes on the Kaggle GPU (handoff to the local lead chat)

Date: 2026-10-26
From: the cloud build session, for Munene and the local lead chat
Decision: Munene, 2026-10-26: bake the P2 sets (10:30, 18:05, 20:00) on the Kaggle GPU. The cloud CPU bake of 10:30 continues until the GPU maps arrive; then it stops.
Order: engineering/lead_decision_2026-10-25_cycles_parity.md, P2.

## What is ready

- Render pack 2026-10-26 on branch assets/render_pack at c14cc71: 219,340,800 bytes in 3 parts (talanta_render_pack.tar.000 to .002), sha256 file, README; tested from an empty folder under strace (no file read outside the pack). Upload it as a new version of the private dataset talanta-render-pack. It holds:
  - blender/out/frozen_FL.blend: frozen_FK.blend plus the seat re-check stand detail (seat v2, aisle step nosings, rail posts and rail ends in bowl_detail). The bakes and chapters 1 and 2 use it.
  - blender/out/frozen_FL_interior.blend: frozen_FL.blend plus the concourse, the entry and the roof grid (interior_* collections). Chapters 3 and 4 use it.
  - the scripts of wo/web-hero-v2 at the pack date, with the GPU hook (TALANTA_PRE) in bake_lightmaps.py and render_panorama.py, and the P2 options TALANTA_BAKE_PRESET and TALANTA_BAKE_OUT.
- blender/kaggle/talanta_bake.ipynb: one bake set (or part of it) per run, then the panorama. Variables at the top: HHMM, PRESET (from HHMM), ONLY, SAMPLES, PANORAMA.
- blender/kaggle/compare_maps.py: compares two bakes of the same groups (GPU against CPU).
- blender/kaggle/talanta_chapter_render.ipynb: now finds frozen_FL.blend in the new pack (frozen_FK.blend in pack 7e19362); chapters 3 and 4 take frozen_FL_interior.blend, haze 0 and no lens shift.

## Cloud CPU bake of 10:30 (runs until the GPU maps arrive)

| Sub-run | Groups | Wall time | Branch commit |
|---|---|---|---|
| 1a | stadium_shell, stadium_fins, stadium_ornament, roof | 4,805 s (1.33 h) | b95cdc5 |
| 1b | sport, roads, site_built, forecourt | 2,704 s (0.75 h) | 66727ab |
| 2a | site_layout, station, layout_pass_i, plaza_south, trace_sw, landmarks | running (container restart at 10:26 UTC cost about 0.5 h) | |

The maps of sub-run 1a (assets/web_hero_v2_bake_1030, lightmaps/1030/maps/) are the CPU side of the GPU test comparison.

## Steps

1. Upload the new pack as a dataset version (keep it private).
2. GPU test: talanta_bake.ipynb with HHMM "1030" and ONLY "stadium_shell,stadium_fins,stadium_ornament,roof" (the default). This is the cloud CPU sub-run 1a. On the cloud CPU the same batches took albedo 134 s, AO 853 s and light 3,240 s (07:30 set; 1.2 h).
3. Compare: download the output; fetch the CPU maps of sub-run 1a from branch assets/web_hero_v2_bake_1030 (lightmaps/1030/maps/); run
   `python3 blender/kaggle/compare_maps.py <gpu>/lightmaps/1030/maps <cpu>/lightmaps/1030/maps`.
   Pass: light maps within 3 % mean difference and 2 % in mean level (noise only), AO and albedo within 2 of 255.
4. If the test passes and the GPU speed fits the budget: full runs, ONLY "" and PANORAMA True:
   - 1030 (daylight_artistic), then 1805 (sunset_artistic, dusk fixtures on), then 2000 (manifest sun "night": 20:30 EAT, venue lights on; the night fixtures are real Cycles lights: 100 night_* spot lights and 48 dusk uplights, no positions invented).
   - Each run: one Blender process; less than 4 h. If the GPU test shows that a full set takes more than 3.5 h, run the 07:30 parts instead (ONLY per part, the groups in blender/web_hero/WEB_HERO_V2.md, "Parts"), then one run with ONLY "" to write bake_log.json, the baked blend and the panorama.
5. After each set: stop the cloud CPU bake of that time if it still runs (tell the cloud session), and push the set to the orphan branch assets/web_hero_v2_bake_<HHMM> with this layout: lightmaps/<HHMM>/maps/*.png, maps/stages.json, bake_log.json, talanta_web_baked.blend, env/ (panorama) and run_record.json. The cloud session has already pushed the CPU sub-runs of 10:30 to assets/web_hero_v2_bake_1030; a GPU set replaces those files.
6. Stop and report the hours after each set (P2 rule).

## Budget (Kaggle, 30 GPU h a week; Munene's limit 20 h for the week)

| Item | GPU h |
|---|---|
| used: GPU test 2026-10-25, C1, C2 | about 1.0 |
| C1 and C2 again on the new pack (the seats changed) | 0.7 |
| C3 to C6 (on hold until the bakes and the pack are done) | 9.8 |
| bake GPU test | about 0.3 |
| three bake sets with panoramas | about 3 (estimate: the 13 times render speed-up of the T4s; to measure in the test) |
| repeats of rejected frames, at most | 4.0 |
| total | about 18.8 (21.8 if the bake speed-up is only 5 times) |

## Rules

- The dataset, the notebooks and their output stay private. Stop the session after each run.
- The maps are internal until the lead approves the set. Traffic is Visualization.
- Do not add fixtures near exits or control rooms (AGENTS.md rule 8).
