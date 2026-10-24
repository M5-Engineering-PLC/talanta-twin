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

## Check renders (1080p, step_FK)

Finished state, look layer on (`TALANTA_LOOKDEV=1`), Cycles hero quality (128 samples), 1920 x 1080.

| Render | Light | Time |
|---|---|---|
| D02_daylight_landing_hero.png | daylight_landing | 9.5 min |
| D03_daylight_landing_hero.png | daylight_landing | 13.4 min |
| L07_daylight_landing_hero.png | daylight_landing | 9.7 min |
| P01_sunset_landing_hero.png | sunset_landing | 17.3 min |

Sheets (`engineering/review_sheet.py`: render, frame, 50 % blend, edges; JPG quality 90), internal only:
- `sheets/001_D02_step_FK_finished_vs_JWNowpO44rw_000714.767_internal.jpg`
- `sheets/002_D03_step_FK_finished_vs_JWNowpO44rw_000617.567_internal.jpg`
- `sheets/003_L07_Enkang_crop_vs_JWNowpO44rw_000706.800_internal.jpg` (L07 crop round Enkang A-C, projected through the
  L07 camera, beside the frame)

There is no P01 sheet: its only reference is the AI-generated image, which proves nothing.

## Checks from the work order

| Check | Result |
|---|---|
| D02: a pale plaza with a round bed south of the bowl; the south-west grass loop still there | pass: pale paving from the apron, the round bed (murram ring, planted centre) and the two axial beds sit on the frame's bed and beds in the 50 % blend; the grass loop, its road and the small stand are unchanged |
| D03: the island is a long pointed lens, not a diamond | pass: pointed lens in the centre of the east approach; it lies on the frame's island in the blend |
| L07: the grass shows variation | pass after one retune: the south-west lawn rendered at saturation 0.64 and nearly flat before pass K; now 0.53 against about 0.56 for the lawns beside it, with soft 8-20 m patches (no markings) |
| L07: the Enkang towers stand out from the generic blocks | partly: the 37 generic blocks in the cone are now one storey, and the Enkang upper floors show the strips, window grid, parapet and roof plant above the stadium roof. The tall masses still behind them are real gpkg buildings at their gpkg heights (fid 8624, 31 m, beside Enkang C; The Fedge 51 m and Rock Park Apartments 66.5 m about 1.2 km out), which the K5c rule keeps. The stadium roof hides the towers' lower floors in L07 |
| No render shows a west road, railway, station, footbridge or car park on the west lawns | pass in D02, D03, L07 and P01 (P01's traffic is Ngong Road) |

## Gaps

- The south plaza has no people: people_figures.py runs before plaza_south_k.py, and K1 keeps the density as it is.
- The plaza outline and beds are a flat-plane camera solve from one view (+-25 m). A GE trace would fix them.
- Grass colour is tuned to L07 only; D02 and D03 read consistent by eye.
- Enkang facade detail is a material on a plain extrusion (no balconies or recesses); at L07 distance it reads.
- seats.json and the web blockout are not re-exported for pass K (no change to the bowl in this pass).

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
  lowers 37 generic mid-rise blocks to one storey. The generic city behind the Enkang towers reads much lower than
  before, while real gpkg towers (The Fedge, Rock Park Apartments) still stand behind them. Keep the rule, or cap at a
  higher percentile?
- The south plaza solve gives two centres. The round-bed centre is (-15.7, 206.1). The centre of the built paving outline
  is (-17.5, 195.2) (the solved eight-point outline alone: (-16.0, 191.0)). Both lie about 33 m west of Sol's audit
  centre (15, 195): the bed 32.6 m, the outline 32.5 m. That is more than the 25 m uncertainty, so the solve and the
  audit do not agree on the position. The solved position is kept (the plaza is not moved); a GE trace would settle it.
  Size, measured from blender/data/plaza_south_k.json: the solved outline spans 110 x 135 m (x -64.0 to 45.8, z 124.9 to
  260.4). The built paving spans 109 x 123 m (z from 136.6), because its north edge follows the outer edge of
  ge_apron_ring instead of the three solved north points. The audit gave 80-100 x 100-130 m.
  (Corrected 2026-10-24, web hero v2 order W0: this item first said 110 x 125 m and that both centres agree within the
  25 m uncertainty.)
