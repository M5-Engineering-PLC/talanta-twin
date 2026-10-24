# Pass K check renders (1080p, step_FK)

Work order: engineering/cloud_pass_k_2026-10-24.md (approved by Munene, 2026-10-24). Internal only: the sheets hold drone
frames. research/reference/dusk_aerial_finished_2026-10-17.jpg is AI-generated and is not used as evidence anywhere in
this pass. People, cars and lights are a Visualization, not a count, occupancy or safety study.

## Scene

`step_FK` = step_FE + the step_FJ steps run with the pass K code + two new steps:
`layout_pass_i.py` (K3), `people_figures.py` (K1), `crown_detail.py`, `landmarks_pass_j.py` (K5), `plaza_south_k.py` (K2),
`grass_k.py` (K4). This container had no scene files, so step_FE was rebuilt from scratch from this branch (about 40 min). A first build
lost `asbuilt_ground.py` and `tree_crowns.py` to a missing scipy in Blender's Python; Blender still exits 0 when a
`--python` script fails. Its renders were discarded. The chain now runs with `--python-exit-code 1`, and the final build
log has no traceback.
This branch also carries seat count pass 01 (upper tier overhang, vomitories; 61,039 places), which the lead's step_FJ did not.

## Change list

| Item | Change | Files |
|---|---|---|
| K1 | The people script no longer calls the dusk image a photo or a source. Density and grouping are stated as an artistic Visualization choice. The `lf_station_forecourt` branch is gone (the station is not in the model, so the crowd does not change). Density unchanged. | blender/context/people_figures.py |
| K2 | No south plaza object existed in any state (pass F, pass I and finish_plaza.py have none there), so it is built new. Outline, round bed and axial beds are fitted to D02 with the audit's camera solve (same code reproduces the audit's south_west_grass ring). Paving, kerbs and raised beds follow the north plaza pattern. The north edge runs on the outer edge of ge_apron_ring. Lawn, paths, beds, shrubs and trees under it are hidden or cut in the finished state only. The south-west loop and its road (sw_lawn, sw_loop_road) are kept: the west edge would stop 1 m outside the loop road, and on step_FK it already lies outside it (no clipping). | blender/context/plaza_south_k.py, blender/data/plaza_south_k.json |
| K3 | The east island is a long pointed lens (32 points, parabolic sides), tips [144,2] and [223,-1], 23 m wide at the middle. Outer paving unchanged. | blender/context/layout_pass_i.py island_ring(), blender/data/layout_pass_i.json |
| K4 | `training_grass` is less saturated (stripe pair #58763F / #5F7C46, was #4D8B38 / #568F40), with world-space patches at 8 to 20 m, a brightness variation, a fine grain, roughness 0.80 to 0.92 and a small bump. Stripes stay on the pitches (UV); the south-west lawn has no UV, so no stripes and no markings. | blender/grass_look.py, build_site_detail.py, blender/context/grass_k.py |
| K5a | pick() rule: nearest footprint (100 m2 or more, within 40 m of the pin); if it is lower than 12 m, the tallest footprint above 12 m within 80 m. No landmark changes footprint (table below). | blender/context/landmarks_pass_j.py, landmarks_pass_j.json |
| K5b | Enkang towers: cream-ochre walls, brown-maroon full-height strips every 8 m, the window grid, a darker 1.5 m parapet and roof plant (a core and two tanks). Positions and heights unchanged (38, 45.5, 47 m). | landmarks_pass_j.py mass(), roof_plant(); palettes.enkang |
| K5c | background_b.py blocks in the L07 view cone within 1,500 m: the gpkg height under a block, or the median gpkg height within 200 m. 37 blocks changed (all by the median, which is 4.0 to 4.5 m there; no block stood on a gpkg footprint). CBD, Upper Hill, Kilimani and Westlands are not touched. | landmarks_pass_j.py; landmarks_pass_j.json generic_cap |
| K6 | `hero_artistic.prepare()` sets the far haze and far tint explicitly for day and for dusk (`set_far_values`). Test: `python3 blender/test_hero_artistic_day_dusk.py` (no Blender; stubs `lookdev.STRENGTHS`; dusk then day gives the day values). It passes; on the old code it fails. | blender/hero_artistic.py, blender/test_hero_artistic_day_dusk.py |
| K7 | Correction rows for rows 454 (the rule pick() really uses), 461 and 462 (The Junction shows in D02). New rows for the south plaza, the lens island (camera solve vs. inference kept apart), the kerb and planting, the Enkang palette, the pick rule, the grass and the K5c cap. No old row edited or deleted. | gis/parameter_ledger.csv |

## K5a: footprint check on every landmark

Footprints of 100 m2 or more; heights from gis/derived/near_ring_buildings.gpkg.

| Landmark | Footprint used | Height | Tallest within 80 m of the pin | Result |
|---|---|---|---|---|
| Enkang A, B, C | named fids 8630, 8635, 8625 | 45.5, 47.0, 38.0 m | (named) | unchanged |
| Ngando Flats | nearest, fid 8575, 9 m from the pin | 4.5 m | fid 4247, 10.0 m | none above 12 m: kept; question below |
| Liberty Centre | nearest, fid 8408, 9 m | 11.5 m | fid 8415, 11.5 m | none above 12 m: kept; question below |
| Denali | named fid 8290 | 34.0 m | (named; nothing above 6 m near the pin) | unchanged |
| Racecourse Gardens | nearest, fid 7113 | 4.0 m (default_by_area) | fid 5997, 6.5 m | none above 12 m: kept; question below |
| White Village | nearest, fid 7827, 19 m | 23.5 m | fid 10427, 24.0 m (59 m away) | nearest is above 12 m: unchanged |
| Alba (TSAVO Skywalk) | named fid 10428 | 41.5 m | (named; 15 m near the pin) | unchanged |
| KMD | named fid 9665 | 7.0 m | (named) | unchanged |
| The Junction | named fids 9846, 14176 | 17.0, 11.0 m | (named) | unchanged |

## K8: L06 forecourt light check

`K8_L06_forecourt_look_on_vs_off.jpg`, from `k8_look_on/` and `k8_look_off/`: hero_artistic L06 (sunset_artistic, sun
9.2 deg elevation) at 1080p, lower-right quarter, rendered once with the look layer on and once with compositing off.
6.2 and 5.8 min.

| | look layer on | look layer off |
|---|---|---|
| sunlit forecourt, mean RGB | 167, 118, 59 | 161, 122, 83 |
| shadow, mean RGB | 62, 60, 38 | 56, 57, 40 |
| sunlit / shadow | 2.14 | 2.39 |
| largest step across the shadow edge (row 1000) | 22 levels | 25 levels |

The two crops agree: the bright patch and the hard diagonal edge are in the render without the look layer. They are the
stadium's cast shadow under the low sun (sun angle 0.53 deg, lookdev.py). The look layer only warms the grade (the blue
drops). Nothing was changed.

## Questions for the lead

- Ngando Flats (pin -275,-424) and Racecourse Gardens Apartments (pin -468,-825): the gpkg has no footprint above 12 m
  within 80 m of either pin (tallest 10.0 m and 6.5 m). Both stay on the nearest low footprint (4.5 m, 4.0 m). Is the
  pin right, or should a named footprint or a height from another source be used?
- Liberty Centre: the nearest footprint is 11.5 m (4 storeys), and nothing within 80 m is taller. Kept.
- K5c: the median gpkg height within 200 m is about 4 m round the L07 cone (mostly single-storey houses), so the rule
  lowers 37 generic mid-rise blocks to one storey. The Enkang towers now stand alone, but the city behind them reads
  much lower than before. Keep the rule, or cap at a higher percentile?
- The south plaza solve puts the round bed at (-16, 206), 33 m west of Sol's audit centre (15, 195), and the extent at
  about 110 x 125 m, a little above the audit's 80-100 x 100-130 m. Both are within the 25 m uncertainty.
