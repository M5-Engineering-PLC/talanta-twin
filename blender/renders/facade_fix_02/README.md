# Facade fix 02: replica plan pass A (internal)

Pass A of the lead order of 2026-10-20 (`engineering/replica_plan_2026-10-20.md`, answers in the order). Internal only:
the sheets hold reference frames. Do not publish them. No 4K and no W.

## What changed

Code: commit a9dcc8f. Values: new rows in `gis/parameter_ledger.csv` (old rows untouched).

- **Shield paint, not the grade.** AgX and the look layer are unchanged.
  - Crop renders of F16 (32 samples, look layer on) showed what limited the old paint. At roughness 0.6, sky reflection added a blue-grey veil: pure black rendered (33, 46, 56), and pure red never went below G 38.
  - The paint is now matte: `bowl.shield.roughness` 0.85, `bowl.shield.specular` 0.1. Pure black then renders (7, 13, 19).
  - Albedos were tuned against the frame in the same crop: `bowl.shield.red` #a4122c and `bowl.shield.black` #1a1b1e.
  - Test results: #a40c2c rendered (170, 4, 59) and #a4162c rendered (171, 17, 59). #a4122c sits between them.
- **Shield outline: a pointed lens.**
  - `blender/shield_paint.py` draws the half-width as (1 - |v|^a)^b, with `bowl.shield.outline_a` 1.85 and `outline_b` 0.82.
  - The lobes, spine, leaves and boss follow the outline. Size and position are unchanged.
  - The drawn fractions are lower than the rendered ones because the shoulder foreshortens the shield top in F16. The exponents were tuned in renders, not on the drawing.
- **Spear blades:** long leaf blades, 6.5 m (`bowl.spear.blade_len`), pointed tip, widest at 62 % of their length. Maximum width is 2.2 x the shaft diameter (`bowl.spear.blade_width_ratio`).
- **Fascia:** the merged row `bowl.fin.fascia_h` 2.5 m gives a broad white band from the top V points to the roof edge. The bay is now 32.1 m on the fascia line (771 m round).
- **Louvres:** light grey backing behind the fins (`bowl.fin.backing_grey` 0.45) instead of a dark void. Fin depth and slope are unchanged.
- **Recess** under the ring beam: albedo 0.025, darker in overcast.
- **Jacaranda:** lighter lilac. Site trees use #A58CCB, suburbs #A890C8, canopy tint #B49AD8.

## Renders

- Rebuild: the STATUS.md chain plus the step F context steps, frozen as `blender/out/step_FA.blend`. It took 29 min (07:49 to 08:17); tree_rules runs twice and takes most of it.
- Every render: Cycles 1920 x 1080 hero, 128 samples, look layer on.
- The pass B rebuild ran on the same 4 cores, so the times are longer than usual.

| Render | Camera | Light | Time |
|---|---|---|---|
| F16_neutral_hero.png | F16, solved to 001216.000 | neutral 12:30 | 20.1 min |
| D02_overcast_hero.png | D02, exact drone camera | overcast 11:00 | 18.3 min |

## Acceptance

### F16 against 001216.000

From `blender/concept_match/shield_fractions.py`. Boxes: render 300,0,1000,1080; frame 450,0,1060,1080.

| | Render | Frame | Target | Result |
|---|---|---|---|---|
| Red width 10 % from top / mid-height | 0.680 | 0.734 | 0.73 +- 0.05 | on the limit (see gap 1) |
| Red width 3 % from bottom tip / mid-height | 0.301 | 0.300 | 0.30 +- 0.05 | pass |

From `blender/concept_match/facade_samples.py`, in the same light (sunlit facade):

| Sample | Render | Frame | Max channel difference | Result (12 levels) |
|---|---|---|---|---|
| Shield red, median | (169, 2, 55) | (164, 13, 57) | 11 | pass |
| Lobe black, median | (17, 27, 37) | (29, 29, 37) | 12 | pass |
| Louvre (fins and lattice beside the shield) | (158, 179, 197) | (167, 173, 180) | 17 | fail: blue cast |
| Fascia band above the shield | (216, 227, 241) | (183, 196, 205) | 36 | fail: brighter and bluer |

### D02 against 000714.767

Same tool, in the stadium mask of D02 (overcast in both, but the render's overcast is the blue procedural sky):

| Sample | Render | Frame | Max channel difference |
|---|---|---|---|
| Shield red | (124, 2, 50) | (51, 9, 20) | 73 |
| Lobe black | (8, 21, 33) | (30, 13, 17) | 22 |
| Louvre | (144, 170, 194) | (109, 108, 109) | 85 |
| Fascia band | (193, 210, 230) | (81, 78, 80) | 150 (the frame sample falls on the dark gap above the shield top at this distance; not a fascia reading) |

Fail. The frame is much darker and neutral grey; the render is brighter and blue. This is the light, not the paint
(the same paint passes in F16). The grey cloud sky and lower exposure for the D cameras are pass D.

## Sheets (sheets/, internal)

Made with `engineering/review_sheet.py`: render, frame, 50 % blend and edges, saved as JPG at quality 90.

## Gaps (honest list)

1. **Shield top fraction is on the limit.**
   - The crop tests on the facade_fix_01 scene gave 0.725 with these exponents.
   - The 2.5 m fascia row lowers the shield top, and the full render gives 0.680.
   - A pointier outline is being tested in crop renders for a new ledger row in a later pass.
2. **Louvre and fascia tone.**
   - In F16's neutral light both read bluer than the frame: louvre max difference 17, fascia 36.
   - The paint is near white. The blue comes from the procedural daylight sky and the look layer. The grey cloud sky for the D cameras is pass D.
3. **F16 camera.**
   - It was solved on the facade_fix_01 lattice (12.7 px rms).
   - With the 2.5 m fascia, the V points sit 1 m lower, so the shield top sits near the top of the render, while the frame shows the fascia band and roof edge above it.
   - Not re-solved here.
4. **Black lobes** are at the edge of the 12-level band (max difference 12, red and green channels).
5. **D02:** see the numbers above. The overcast sky is still the blue procedural one, so sample matches wait for pass D.
