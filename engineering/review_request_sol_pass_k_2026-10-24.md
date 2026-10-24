# Review request: pass K (for GPT-6.1 Sol, read-only)

Date: 2026-10-24
From: the cloud Talanta build chat, for Munene to hand to Sol
Branch: `ccr-11a40cef-r87r85` at 3f672b2 (merges `lead/layout-audit-01` at ec98865)
Range to review: dc559e7..3f672b2 (the merge, then pass K)
Basis: engineering/cloud_pass_k_2026-10-24.md, which came from Sol's review of 412a4bb to 4f48e8e ("fix first")

Read-only, as before. The AI image rule stays: research/reference/dusk_aerial_finished_2026-10-17.jpg is not evidence.
Please give a verdict (approve the 4K stills for the W re-bake, or fix first) and findings by priority (P1, P2, nit),
each with file and line.

## What to look at

| Item | Where | Question for the review |
|---|---|---|
| K1 people sourcing | blender/context/people_figures.py | Is every dusk-image reference gone? Station branch removed, density unchanged? |
| K2 south plaza | blender/context/plaza_south_k.py, blender/data/plaza_south_k.json; sheet pass_k_check_01/sheets/001_D02_* | Pixels picked in D02 and back-projected with the audit's backproject() (it reproduces the audit's south_west_grass ring). The bed comes out at (-16, 206), 33 m west of the audit centre (15, 195); extent about 110 x 125 m. Is the pixel pick sound? Is the finished-state clearing right (the SW loop and its road are kept)? |
| K3 lens island | blender/context/layout_pass_i.py island_ring(), layout_pass_i.json; sheet 002_D03_* | Parabolic sides, tips [144,2] and [223,-1], 23 m wide. Does it sit on the frame's island? |
| K4 grass | blender/grass_look.py, build_site_detail.py, blender/context/grass_k.py | Tuned on L07 crops: saturation 0.64 before, 0.53 now, against about 0.56 for the lawns beside it. Under the 4K daylight_artistic sky it reads a little lighter and yellower. Accept, or retune per preset? |
| K5a pick rule | blender/context/landmarks_pass_j.py pick() | Nearest footprint; if lower than 12 m, the tallest above 12 m within 80 m. No landmark moved: Ngando Flats, Racecourse Gardens and Liberty Centre have nothing above 12 m within 80 m. Is the rule right, and what should those three pins use? |
| K5b Enkang look | landmarks_pass_j.py mass(), roof_plant(); palettes.enkang; sheet 003_L07_Enkang_* | Strips, window grid, darker 1.5 m parapet, roof core and tanks; heights unchanged. Does it read like 000706.800? |
| K5c generic cap | landmarks_pass_j.py (K5c section), landmarks_pass_j.json generic_cap | The median gpkg height within 200 m is 4.0-4.5 m there, so 37 blocks became one storey. The tall masses still behind Enkang in L07 are real gpkg buildings (fid 8624 31 m; The Fedge 51 m; Rock Park Apartments 66.5 m). Keep the median, or use a higher percentile? |
| K6 day/dusk | blender/hero_artistic.py set_far_values(); blender/test_hero_artistic_day_dusk.py | Both branches explicit; the test runs without Blender and fails on the old code. Enough? |
| K7 ledger | gis/parameter_ledger.csv, rows 466 to 482 | Correction rows only; no old row edited. Camera solve and inference kept apart? |
| K8 forecourt light | blender/renders/pass_k_check_01/K8_L06_forecourt_look_on_vs_off.jpg | Look layer on and off agree (sunlit/shadow 2.14 vs 2.39, edge step 22 vs 25 levels), so nothing changed. Agree? |
| 4K stills | blender/renders/hero_artistic_04/ | Approve for the W re-bake? |

## Build notes that affect the review

- The first step_FK build lost asbuilt_ground.py and tree_crowns.py to a missing scipy in Blender's Python. Blender
  exits 0 when a `--python` script raises, so the chain went on. Those renders were discarded; every committed render
  is from a full rebuild with `--python-exit-code 1` and no traceback in the log.
- step_FK carries seat count pass 01 from this branch (upper tier overhang, vomitories; 61,039 places), which the lead's
  step_FJ did not.
- The south plaza has no people: people_figures.py runs before plaza_south_k.py, and K1 keeps the density.
