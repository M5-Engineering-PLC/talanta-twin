# Ground fix 01: replica plan pass C (internal)

Pass C of the lead order of 2026-10-20. Internal only: the sheets hold reference frames. No 4K and no W.

## Method: the ground traced from the solved cameras

Code is in commit e8f37b6 (pass C part). The steps:

1. **Cameras.** `blender/concept_match/refine_drone_cams.py` refines a solved drone camera on the stadium silhouette.
   - The bowl is near convex, so its silhouette is the hull of its projected rings (IoU 0.98 or better against the rendered mask).
   - The fit adjusts position, yaw, pitch, roll and focal length by chamfer distance to the frame silhouette.
   - D01 moved 14.5 m and D03 7.4 m (manifest notes say so).
   - D02 is kept as solved: its refit did not improve the acceptance IoU (0.904 against 0.911).
2. **Trace.** `blender/concept_match/asbuilt_trace.py` builds the label map:
   - Each frame (D01 000645.000, D02 000714.767, D03 000617.567) is split into classes by hue and brightness: grass, murram, laterite (bare plazas and paths), paved, trees, white roofs.
   - A 1 m plan grid on the terrain is projected into each frame through its camera, without the stadium mask.
   - Each cell takes the class of the frame that sees it with the smallest ground footprint (at most 2.5 m per pixel).
   - A 5 x 5 majority filter removes noise.
   - The result is `blender/data/asbuilt_classes.png` (labels only, no frame pixels), with `.json` holding outlines, coverage and the south-west fit.
3. **Change list.** `plan_classes.py` renders the old layout from above into the same classes. `asbuilt_trace.py` lists every area of 400 m² or more where the two disagree (table below).
4. **Build.** `blender/context/asbuilt_ground.py`, the last step of the chain, makes three collections:
   - `asbuilt_ground`: the traced classes as one mesh of 1 m cells on the terrain. It uses our own materials (patchy grass, murram, laterite, asphalt) and leaves the public roads to the context roads.
   - `trace_sw_finished`: the finished look of the traced south-west.
   - `trace_structures`: the stand.
5. **State switch.** `blender/scene_state.py` with `TALANTA_STATE=asbuilt|finished` in `render_cycles.py`.
   - **asbuilt:** the traced ground, and no planted dressing (beds, shrubs, flowers, palms, young trees, car park markings, the finished track and pitch surfaces).
   - **finished:** the scene as built.
   - Both states keep the masts, lamp poles, fence, buildings, bowl and context.

## Changes (the frames win)

**South-west foreground, both states (fixed from the trace, not by eye):**
- `track_sw`, its infield and `training_field_sw` are removed.
- **Lawn pitch:** 104 x 75 m, centred at x -114, z 181 (app metres), turned 9.5 deg from north-south, with pitch lines in the finished state.
- **Loop road:** 8 m wide round the lawn, corner radius 18 m (by eye from D02).
- **Stand with the white roof** west of the loop: 77 m long, centre x -202, z 130, facing the pitch.
  - About a dozen rows of red seats under a white roof on a back row of columns.
  - Plain masses: no gates, exits or signs.
- The old track ran 70 m further south.

**Surface changes, as-built state** (every disagreement of 400 m² or more; bearing from the bowl centre, clockwise from north):

| Where | Old layout | Frames | Area m² |
|---|---|---|---|
| 347 deg, 141 m (north plaza) | paved | laterite | 18 655 |
| 83 deg, 145 m (east apron) | grass | paved | 17 658 |
| 256 deg, 190 m (west, car park) | grass | paved | 14 736 |
| 116 deg, 240 m (south-east fields) | grass | murram | 12 928 |
| 178 deg, 184 m (south plaza with circle bed) | grass | laterite | 11 767 |
| 166 deg, 272 m (south road) | grass | paved | 7 866 |
| 89 deg, 234 m (east shield-shaped plaza) | grass | laterite | 6 326 |
| 170 deg, 246 m (south forest edge) | grass | trees | 5 260 |
| 75 deg, 254 m | grass | murram | 4 560 |
| 357 deg, 318 m (Ngong Road verge) | white | paved | 4 339 |
| 54 deg, 251 m | grass | laterite | 3 883 |
| 301 deg, 193 m | grass | paved | 3 421 |
| 12 deg, 277 m | grass | murram | 3 331 |
| 320 deg, 166 m | grass | murram | 2 893 |
| 163 deg, 188 m | grass | murram | 2 737 |
| 122 deg, 214 m | grass | laterite | 2 564 |
| 33 deg, 247 m | grass | murram | 2 518 |
| 322 deg, 197 m | grass | laterite | 2 241 |
| 344 deg, 251 m | grass | paved | 2 153 |
| 66 deg, 206 m | grass | murram | 1 976 |
| 208 deg, 177 m | grass | paved | 1 922 |
| 98 deg, 289 m | grass | trees | 1 574 |
| 200 deg, 254 m | grass | trees | 1 297 |
| 64 deg, 304 m | grass | paved | 1 202 |
| 189 deg, 278 m | grass | paved | 1 127 |
| 68 deg, 324 m | paved | laterite | 1 112 |
| 223 deg, 230 m | grass | laterite | 1 066 |
| 213 deg, 269 m | grass | paved | 1 045 |
| 351 deg, 282 m | white | paved | 980 |
| 218 deg, 232 m | murram | grass | 713 |

The full list (43 areas) is `changes` in `blender/data/asbuilt_classes.json`. The plan sheet `sheets/000_plan_trace_vs_layout.png` shows the trace beside the old layout.

## Renders (asbuilt state)

- Scene: full rebuild with `asbuilt_ground` appended, frozen as `blender/out/step_FC.blend` (09:05 to 09:35).
- Cycles 1920 x 1080 hero, 128 samples, look layer on.
- The overcast light is the old procedural sky; the grey cloud sky is pass D.
- F16 is re-rendered to check the new shield outline row (`bowl.shield.outline_a` 2.1).

| Render | Camera | Light | Time |
|---|---|---|---|
| D01_overcast_hero.png | D01, refined drone camera | overcast 11:00 (procedural) | 15.0 min (beside the pass D scene builds) |
| D02_overcast_hero.png | D02, solved drone camera | overcast | 8.1 min |
| D03_overcast_hero.png | D03, refined drone camera | overcast | 10.4 min |
| F16_neutral_hero.png | F16 | neutral 12:30 | 13.2 min |

- A worker restart at about 10:05 killed the D02 render; the rest ran from 17:09.
- The first D01 (old ground colours) was stopped after 5 min, when the D02 check showed orange laterite. The colours were retuned to the frame class medians (`class_median_srgb` in the json) and D01 restarted.

## Acceptance

**Stadium silhouette IoU** (target 0.95):
- Tools: `drone_masks.py` (flat bowl mask from the camera) and `silhouette_iou.py`.
- The frame silhouette is cut by a colour model of the same frame, in a +-15 px band.

| Camera | Before (facade_fix_01 cameras) | Now | Result |
|---|---|---|---|
| D01 | 0.869 | 0.913 | fail |
| D02 | 0.911 | 0.913 (camera kept) | fail |
| D03 | 0.939 | 0.960 | pass |

**F16 shield fractions**, with the new `bowl.shield.outline_a` 2.1 row:

| | Render | Frame | Result |
|---|---|---|---|
| 10 % from the top | 0.733 | 0.734 | pass |
| 3 % from the bottom tip | 0.321 | 0.300 | pass |

**F16 colour samples** (same light):

| Sample | Render | Frame | Max difference | Result |
|---|---|---|---|---|
| Red | (169, 2, 56) | (164, 13, 57) | 11 | pass |
| Black | (16, 26, 37) | (29, 29, 37) | 13 | 1 over the limit |
| Louvre | | | 17 | fail |
| Fascia | | | 36 | fail |

**D cameras, shield / fascia / louvre samples** (`facade_samples.py`, in the stadium mask):

| Camera | Red | Black | Louvre | Fascia |
|---|---|---|---|---|
| D01 | 44 | 24 | 46 | 68 |
| D02 | 74 | 22 | 85 | 150 (frame sample on the dark gap) |
| D03 | — | — | — | — |

- All three fail: the render is bright and blue, the frames grey and darker. Same cause as in passes A and B, the old procedural overcast sky. Pass D re-renders D01 and D02 under the grey cloud HDRI.
- D03: the frame's shields are too small and dark for the red rule (no shield found), so there are no D03 samples.

## Gaps (honest list)

1. **Light.** The D renders here use the old blue procedural overcast:
   - Murram reads blue-grey and the north plaza's laterite near white.
   - The colour acceptance fails for D01-D03.
   - The grey cloud sky is pass D.
2. **IoU in D01 and D02 is 0.91.**
   - The overlays (`silhouette_iou.py <dir> <out>`) show the remaining misfit at the right end of D01 and along the roof line in D02.
   - The D02 refit made it worse, so D02 keeps its solve.
   - The bowl plan or the lens distortion of the drone (not modelled) may account for the rest.
3. **Trace limits.**
   - Hue classes misread shaded or wet ground, and the 5 x 5 filter rounds corners.
   - The far cells (more than 2.5 m per pixel), and the ground behind the stadium in all three frames, are unknown and keep the terrain grass.
   - The as-built ground is a 1 m cell mesh, so its edges step at 1 m. That is invisible from the drones, but not for close views.
4. **Finished state outside the south-west keeps the mockup layout.** The frames show the plazas (north and south circle-bed plazas, east shield-shaped plaza) as bare construction. The finished layout there is the mockup design; only the south-west was rebuilt in both states, as ordered.
5. **The NE warm-up track** is kept in both states. D03 shows it as a dirt oval under construction, and the as-built ground covers it in the asbuilt state.
6. **Stand:** its rows and roof depth are estimated from the white-roof cells, and the depth is capped at 18 m.
