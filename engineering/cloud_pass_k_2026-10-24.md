# Cloud work order: pass K, fixes before the final 4K stills (2026-10-24)

Date: 2026-10-24
Project: Talanta twin (M5)
From: the local lead session
To: the cloud Talanta build chat
Status: active work order. Approved by Munene on 2026-10-24.
Branch: `lead/layout-audit-01`, from 4f48e8e (step_FJ)

Read this file first. The basis is a read-only review by Sol of commits 412a4bb to 4f48e8e and of the stills in blender/renders/hero_artistic_03/. The review verdict was "fix first". The W re-bake stays on hold.

The AI image rule from engineering/layout_audit_01/LEAD_REVIEW.md (revision 2) still applies. Never use research/reference/dusk_aerial_finished_2026-10-17.jpg as evidence.

## K1. Sourcing in the people script

File: blender/context/people_figures.py.

1. Remove every text that calls the dusk image a photo or uses it as a source (the docstring at lines 7 to 8, and the comments at lines 95 and 118).
2. State that the crowd density and the grouping are an artistic Visualization choice.
3. Remove the `lf_station_forecourt` branch from `walk_surface()`. The station does not exist in the model.
4. Do not change the crowd density in this pass.

## K2. South plaza in D02

The D02 frame (JWNowpO44rw_000714.767) shows a broad pale plaza south of the bowl, east of the south-west grass loop. It has a round bed in the centre and long axial beds. The model shows lawn and paths there. Sol's audit (layout_plan.json:south_plaza) gives the centre at about x 15, z 195, and the size at 80 to 100 m east to west by 100 to 130 m north to south.

1. Find out whether an object for this plaza exists in any state (for example, hidden by pass F or pass I). If one exists, show it in the finished state.
2. If none exists, build it in a new file blender/context/plaza_south_k.py, with the data in blender/data/plaza_south_k.json:
   - Fit the outline to D02 with the camera solve method of engineering/layout_audit_01/camera_estimates.json. Record the uncertainty (about 25 m).
   - Use the north plaza (forecourt_layout.json:plaza_edge, central_round_bed, axial_bed_north, axial_bed_south) as the pattern for paving, the round bed and the axial beds.
   - Join the plaza to the outer apron. Keep the south-west grass loop and its road as they are.
   - Set `state_only="finished"`.
3. Remove the lawn, paths and trees that overlap the plaza in the finished state only.
4. Add ledger rows. The label is "estimate from a camera solve". The paving finish and the planting are "inference".

## K3. Rounder east island

File: blender/data/layout_pass_i.json:east_approach.island, and the island code in blender/context/layout_pass_i.py.

1. Replace the four-corner diamond with a long pointed lens shape. Use at least 24 points.
2. Keep the two tips at [144,2] and [223,-1].
3. Make the maximum width 22 to 24 m, at about the middle of the island.
4. Keep the outer paved area as it is.
5. Separate the island kerb (0.25 m) and the planting from the camera-solve coordinates in the ledger. The kerb and the planting are "inference".

## K4. Grass that looks real

The south-west lawn and the training pitch look flat and too saturated in L07. The south-west lawn uses `training_grass` (blender/context/asbuilt_ground.py:164). A change to the `GRASS` fallback in pass I alone does not correct this.

1. In the `training_grass` material, decrease the saturation to match the other grass in the same render.
2. Add low-frequency colour and brightness variation (noise at a scale of about 8 to 20 m).
3. Add a small roughness and bump variation.
4. Keep the mowing stripes on the pitches only. Do not add markings to the south-west lawn.
5. Make sure that the other users of `training_grass` still look correct in D01 and D02.

## K5. Landmark buildings

### K5a. Wrong footprints for two buildings

The ledger gives Ngando Flats 4.5 m and Racecourse Gardens Apartments 4.0 m. These are apartment blocks, so the nearest-footprint rule in `pick()` found a small building next to the pin.

1. For these two pins, select the footprint of the apartment block within 80 m of the pin. Prefer the tallest footprint, then the largest area.
2. If no footprint within 80 m is taller than 12 m, keep the nearest footprint. Then write the case under "Questions for the lead" in the README.
3. Do the same check on every other landmark. Write the result in a table in the README.

### K5b. Enkang appearance

Frame evidence: JWNowpO44rw_000706.800 shows a 12-storey tower. It is cream and ochre, with brown or maroon vertical strips, a regular window grid and a darker roof parapet. JWNowpO44rw_000619.700 shows white and maroon towers in the same group.

1. Change `landmarks_pass_j.json:palettes.enkang` and `landmarks_pass_j.py:mass()` so that the upper floors show these features: the vertical strips, the window grid, the parapet and the roof plant.
2. Keep the positions and the heights from the gpkg (38, 45.5 and 47 m). Do not make the towers taller.

### K5c. Generic masses near the landmarks

The generic grey blocks behind the Enkang towers in L07 are as tall as the landmarks, or taller. So the landmarks do not stand out.

1. Find the generic masses (blender/context/suburbs.py, background_b.py) in the L07 view cone within 1,500 m of the bowl.
2. If a gpkg footprint is under a generic mass, use the gpkg height of that footprint.
3. If there is no gpkg footprint, limit the height to the median gpkg height of the buildings within 200 m.
4. Do not change the CBD and Upper Hill towers.
5. Add one ledger row that describes the rule and the number of masses changed.

## K6. Dusk values in the day preset

File: blender/hero_artistic.py, `prepare()` (lines 214 to 216).

1. Set the day values and the dusk values explicitly in both branches. A day call after a dusk call in the same process must give the day values.
2. Add a small test that runs without Blender (stub `lookdev.STRENGTHS`), calls dusk and then day, and makes sure that the day values come back.

## K7. Ledger text

File: gis/parameter_ledger.csv.

1. Row 454: replace "largest-area rule" with the rule that `pick()` really uses after K5a.
2. Rows 461 and 462: The Junction is visible in D02 (pass J README). Correct the "outside all hero cameras" text.
3. Add correction rows. Do not edit or delete the old rows.

## K8. L06 forecourt light check

The sunlit forecourt in the lower right of L06 is very bright, with a hard diagonal shadow edge. Sol thinks that it is the real cast shadow of the stadium under a low sun (sun angle 0.53 degrees in lookdev.py).

1. Render a 1080p crop of that area two times: look layer on, and look layer off.
2. If the two crops agree, change nothing. Write the result in the README.
3. If only the look-layer crop shows the hard edge or the bright patch, correct the look-layer mask. Then write the cause in the README.

## Renders

### Check renders (1080p, step_FK)

1. Render D02, D03, P01 and L07 at 1080p.
2. Make sheets: D02 against 000714.767, and D03 against 000617.567.
3. Make a crop sheet of the Enkang group in L07, beside JWNowpO44rw_000706.800.
4. Push the renders, the sheets and a README (blender/renders/pass_k_check_01/README.md) with the change list, the checks below and the gaps.

Checks:
- D02: a pale plaza with a round bed is south of the bowl. The south-west grass loop is still there.
- D03: the island is a long pointed lens, not a diamond.
- L07: the grass shows variation. The Enkang towers stand out from the generic blocks.
- No render shows a west road, railway, station, footbridge or car park on the west lawns.

### Final 4K stills

1. Render L06 and L07 at 4K with the `hero_artistic` preset on step_FK, into blender/renders/hero_artistic_04/.
2. Push the stills, the labelled copies and the README.
3. Stop. Munene must approve the stills before the W re-bake.

Expected cloud time: about 1 hour for the check renders and about 2.5 hours for the 4K pair.

## Rules that stay

- AGENTS.md applies in full.
- All changes apply to the finished state only, except the landmark and context masses, which are the same in both states.
- Frames and sheets are internal only.
- People, cars and lights are a Visualization. The labelled copies carry the note.
- Commit as Munene's git identity. Do not add AI attribution.
