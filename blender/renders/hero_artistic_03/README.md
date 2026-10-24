# Hero artistic 03: 4K stills L06 and L07 on step_FJ (waiting for approval)

Work order: engineering/cloud_handoff_2026-10-23.md, Step 4. **STOP after these stills.** Munene must approve them
before the W re-bake (Step 5). The W re-bake has not started.

## Settings

| | |
|---|---|
| Scene | step_FJ: step_FE + pass I (`layout_pass_i.py`) + pass H people and crowns + pass J landmarks. Finished state, look layer on. |
| Preset | `hero_artistic`: 3840 x 2160, Cycles 128 samples adaptive (min 32, threshold 0.02), OpenImageDenoise, volumetric haze, glare and bloom, edge bevels |
| L06 | `sunset_artistic` (Belfast Sunset, CC0), dusk fixtures on |
| L07 | `daylight_artistic` (Kloofendal 48d, CC0), day |

## Fixes in this step

**1. Speckle on the far ridge (L06): found and removed at the cause.**
- More samples did not help: a 4K crop at 256 samples, adaptive minimum 128 and an indirect clamp still speckled.
- Root cause, from A/B crops: with compositing off, the ridge is clean; with a flat colour in place of its image, it
  still speckles. So the speckle comes from the look layer (`lookdev.py`), not the render.
  - `hero_artistic.finish()` turns the volumetric haze back on after the look layer is built.
  - In some samples a ray scatters inside the haze box. The Depth, Mist and Object Index passes then take the
    volume's values, so the per-band haze masks flip pixel by pixel.
- Fix (`hero_artistic.py`): the look layer reads Depth, Mist and Object Index from a second view layer,
  `passes_no_haze`. That layer leaves out the haze box's collection and renders at 16 samples. The image still comes
  from the main layer, haze included. The sample increase was dropped again.

**2. Hills at dusk.**
- With clean masks, the Ngong Hills band showed what the speckle had hidden: a flat, near-white wall. The cause is the
  fixed band haze (0.58 and 0.70) toward a far tint that the bright sunset haze colour makes near white.
- At dusk only (`hero_artistic.prepare()`):
  - band haze is lowered to 0.32 (`terrain_horizon_hills`) and 0.40 (`terrain_horizon_far`);
  - the far tint brightness drops from 0.95 to 0.48.
- The hills now read as a hazy blue-violet range, as in mockup 06. L07 keeps the day values.

**3. Warmer L06 sky (`sky_hdri.py`, `sunset_artistic`).**
- Camera rays see the sky graded warmer: saturation 1.55 and gain (1.12, 0.97, 0.80), so the clouds read orange as in
  mockup 06.
- Light rays keep the ungraded HDRI, so the light on the scene does not change.

## Renders

| Render | Time |
|---|---|
| L06_sunset_artistic_hero_artistic.png (and the `_labelled.jpg` copy) | 84.8 min |
| L07_daylight_artistic_hero_artistic.png (and the `_labelled.jpg` copy) | 54.9 min |

The labelled copies carry "Visualization: people, vehicles and lighting are illustrative". People, cars and the dusk
lights are not a crowd count, occupancy or safety study.

## What changed in the stills since hero_artistic_02

- **Pass I:**
  - The pass F layout is gone: no west road, railway, station, footbridge or car parks.
  - The south-west lawn (no markings) and the west forecourt lawn are back.
  - The east approach is broad pale paving with an island.
  - The NE track is terracotta again.
- **Pass J:** the Enkang blocks and the other landmarks stand in the city. They show mainly in L07; L06 looks the other
  way.
- **L06:** clean ridge, blue-violet hills and orange clouds.

## Gaps

1. The far land bands below the ridge are smoother than in hero_artistic_02: their old texture was partly the speckle.
2. The warm points on the far land are the dusk town lights (background_b.py). They are intended, but they are dense
   at 4K.
3. The backing glow is still uniform. The skies are CC0 HDRIs, not Nairobi skies.
4. L06 took 85 min against 64 min before: the pass layer and the larger scene.
