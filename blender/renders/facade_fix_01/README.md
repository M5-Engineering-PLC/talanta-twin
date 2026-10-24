# Facade fix 01 (internal)

The lead's facade fix of 2026-10-20 (Phase B, steps 9 and 10), built to `engineering/facade_spec_2026-10-20.md` and
the 2026-10-20 rows of `gis/parameter_ledger.csv`. Internal only: the sheets hold reference frames and the landing
mockups. Do not publish them. No 4K and no W were run. The 4K H render that was running was stopped when this order
arrived. Waiting for the lead's review.

## What changed (blender/build_blockout.py)

- **Lattice:**
  - 24 ribs per direction (`bowl.profile.lattice_members_704`).
  - Each rib is a flat strip with square edges: 0.45 m face, standing 0.25 m proud of the louvre faces.
  - The top V points sit under the fascia line at equal arc length round the fascia. The first is on the shield 0 axis. The bottom points sit directly below the top points, on the ring beam.
  - Each rib runs from a top V point to the bottom point one bay along, so the X crossings fall at mid-height between two V points.
  - The joints are sharp mitres. Each rib is clipped to its own bay by the vertical line through the V points at its ends and by the fascia and ring-beam lines. No round forks and no tube sweep.
  - The round `lattice_rings` tubes are removed.
  - The lattice has its own material, `white_shell_lattice`. `hero_artistic.py` caps its bevel at 0.03 m; the rest of the facade keeps 0.04 m.
- **Louvres:** the pitch is 0.65 m (from the ledger). The lowest fin sits on the ring beam, 0.05 m above it instead of 0.4 m. The first D01 render showed a dark band there, so that render was discarded and everything was rebuilt.
- **Shields:**
  - Centred on every third V line. The top is at the top V point and the foot at the bottom point.
  - Paint: red #ad2750 and black #1c1e22 with white stripes, roughness 0.6, metallic 0.
  - The pale rim is removed; the edge has the face colour.
  - The 21 m width is unchanged.
- **Spears:** the shaft radius is 0.37 m (from the ledger), white. They cross behind each shield, and the blade tips stop 0.6 m under the fascia line.
- **Base:**
  - A white ring beam 2.0 m high (`bowl.base.ring_beam_h`) under the lowest louvre. Its face is on the wall line at the foot, which overhangs the plinth by up to 5.6 m.
  - Under it, the set-back ground floor is in a dark material, with one white pier per bay under the bottom points (24 piers).
  - No gates, exits or signs.
  - New ledger row `bowl.base.recess_depth` (4.0 m, carried over from the 2026-10-17 row). The last `bowl.base.recess` row is now a description, not a number.
- **Measured bay:** 31.8 m along the fascia line (763.0 m round). The spec's 32.5 m is measured on the roof outer ring (780.4 m), which sits slightly further out.

## Renders

- Rebuild: STATUS.md order, then the context steps as for step F, frozen as `blender/out/step_FX.blend`.
- Every render: Cycles at 1920 x 1080, hero quality (128 samples, adaptive, OIDN), the same as the last landing checks, with the look layer on (`TALANTA_LOOKDEV=1`).

| Render | Camera | Light | Time |
|---|---|---|---|
| D01_overcast_hero.png | D01, exact drone camera (manifest = drone_cameras.json solved) | overcast 11:00, as the environment pass | 9.9 min |
| D02_overcast_hero.png | D02, exact | overcast | 11.1 min |
| D03_overcast_hero.png | D03, exact | overcast | 14.9 min |
| F16_neutral_hero.png | F16, solved to 001216.000 | neutral 12:30 (the solved facade is in sun) | 11.5 min |
| F32_overcast_hero.png | F32, solved to 001232.600 | overcast | 14.1 min |
| L06_sunset_landing_hero.png | L06 | sunset_landing 18:05 | 9.5 min |
| L07_daylight_landing_hero.png | L07 | daylight_landing 10:30 | 9.1 min |

### Wall-clock time

| Stage | Time |
|---|---|
| Code | about 1 h |
| Rebuild (first) | 24 min |
| Rebuild (after the fin fix) | 25 min |
| Renders | about 87 min (D01 to F16) |
| F32 re-solve and re-render | about 25 min |

Lost time:
- The first D01 render (12 min) was discarded after the fin fix.
- A D01 run was killed by a worker restart (about 38 min idle).

### Cameras F16 and F32 (blender/concept_match/solve_facade_cams.py, facade_cameras.json)

Method: pinhole fits to lattice landmarks read by eye from the frames (the top V points and the bottom points). Each
fit tries every shield and both directions round the bowl. The stadium is close to symmetric under a half turn, so
each fit has a twin.

**F16 (001216.000):**
- Shield 3, south-east side. V and bottom points fit at 12.7 px rms, with an 18.99 mm lens.
- The half-turn twin, shield 7, fits equally well. I picked shield 3 because the frame is sunlit, and under the 12:30 January sun only the south-east twin is in sun.
- The fit needs a wider lens than the drone's (about 24 mm). The model's curvature at this shield is not the frame's (see gaps).

**F32 (001232.600):**
- Shield 1, north-east side. V points fit at 25.5 px rms and the roof-opening edge at 19.8 px median, with a 29.3 mm lens.
- The frame looks across the bowl into the Ngong Road forest, so the camera is on the north-east side.
- A fit to the V points alone reached 3.3 px, but it left the camera height free and put the roof opening far too low. That render was discarded.

## Sheets (sheets/, internal)

- `engineering/review_sheet.py`: render, frame, 50 % blend, and Sobel edges (render grey, frame cyan). Saved as JPG at quality 90 to keep the repo light.
- One sheet for each render: D01–D03 against their drone frames, F16 and F32 against 001216.000 and 001232.600, and L06/L07 against landing mockups 06/07.

## Gaps (honest list)

1. **Shield colour fails the spec's same-light check.**
   - Median red pixel, F16 render: (180, 87, 134). Frame 001216.000: (166, 11, 58).
   - The render reads pink-magenta and much less saturated than the frame's crimson. D01 overcast gives (144, 63, 123).
   - The ledger paint is used as given. The likely cause is the AgX view transform plus the look layer, which compress saturated reds and add sky blue.
   - Not changed here: it needs the lead's decision (grade or paint value).
2. **Fascia band.** The frame shows a broad white fascia band above the V points. The model shows a thin rim, because `bowl.fin.fascia_h` is 1.5 m on a shoulder that curves away. Not in this order.
3. **Louvre tone.** The louvres read darker and greyer than the frame's near-white fins, because the dark backing shows between the fins. The pitch is the ledger's 0.65 m; fin depth and slope are unchanged.
4. **Ring beam.**
   - A hairline dark line remains between the beam and the lowest fin (the fin's shadow).
   - In overcast light the recess under the beam reads mid-grey, lighter than the frames' dark ground floor.
5. **Shield size and curvature.** The width (21 m) is unchanged. F16 needs 19 mm and leaves 12.7 px rms, so the facade curvature and bay layout at that shield differ from the frame by a few percent.
6. **Bay rhythm.** The bays are equal arc length on the fascia line. The spec's 24-bay count assumes that the end bays follow the 3-bay rhythm of the long side; not checked on an end view.
7. **Night shield lights.** The lights in `build_site_detail.py` still aim at the old evenly spaced shield angles, a few degrees off the new positions. Night only.
8. **Web bake groups.** `lattice_rings` is gone, but the web_hero bake groups still list it. W was not run.
9. **F32 far side.** The near facade, V points, shields and roof rim overlay the frame. The far roof rim and the roof opening sit about 40 to 60 px (of 720) lower in the render. Either the far half of the roof plan or crest height differs from the frame, or the drone lens distortion (not modelled) moves them.
10. **Ground-floor entrance.** The entrance canopy at the base in 001216.000 is not modelled, by the no-gates, no-exits rule.

## Conflicts (frames vs spec)

- Bay width: 31.8 m on the fascia line against the spec's 32.5 m on the roof outer ring. Both follow from 24 bays; they differ only in which ring is measured. No other conflict found.
