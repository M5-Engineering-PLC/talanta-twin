# Hero artistic 04: 4K stills L06 and L07 on step_FK (waiting for approval)

Work order: engineering/cloud_pass_k_2026-10-24.md, "Final 4K stills". **STOP after these stills.** Munene must approve
them before the W re-bake. The W re-bake has not started.

## Settings

| | |
|---|---|
| Scene | step_FK (blender/renders/pass_k_check_01/README.md): step_FE + pass I, H and J steps with the pass K code + south plaza + grass retune. Finished state, look layer on. This branch also carries seat count pass 01 (61,039 places). |
| Preset | `hero_artistic` as in hero_artistic_03: 3840 x 2160, Cycles 128 samples adaptive (min 32, threshold 0.02), OpenImageDenoise, volumetric haze with the haze-free pass layer, glare and bloom, edge bevels |
| L06 | `sunset_artistic` (Belfast Sunset, CC0), dusk fixtures on; dusk far haze and tint set by `set_far_values` (K6) |
| L07 | `daylight_artistic` (Kloofendal 48d, CC0), day; day far haze and tint set explicitly (K6) |

## Renders

| Render | Time |
|---|---|
| L06_sunset_artistic_hero_artistic.png (and the `_labelled.jpg` copy) | 78.0 min |
| L07_daylight_artistic_hero_artistic.png (and the `_labelled.jpg` copy) | 46.5 min |

The labelled copies carry "Visualization: people, vehicles and lighting are illustrative". People, cars and the dusk
lights are not a crowd count, occupancy or safety study. Use only the labelled copies outside the team, and only once
Munene clears them.

## What changed since hero_artistic_03 (pass K)

- **South plaza (K2):** pale paving south of the bowl with the round bed and the two axial beds, from a D02 camera
  solve (+-25 m). It shows in the L07 foreground. The south-west grass loop and its road are unchanged.
- **Grass (K4):** the south-west lawn is no longer flat and over-saturated; soft 8-20 m patches, no markings.
- **Landmarks (K5):** the Enkang towers have the darker parapet and roof plant; 37 generic blocks in the L07 cone are
  one storey (median rule). The tall masses behind Enkang in L07 are real gpkg buildings at their gpkg heights.
- **East island (K3):** a pointed lens. It is not in either view (D03 shows it, pass_k_check_01).
- **L06:** the bright forecourt and its hard shadow edge at lower right are the stadium's cast shadow (K8: same with
  the look layer off). The far ridge stays clean and the hills hazy blue-violet, as in hero_artistic_03; the day/dusk fix
  (K6) does not change a single-preset run.

## Gaps

1. The south plaza has no people (people_figures.py runs before it; K1 keeps the density).
2. Under the brighter daylight_artistic sky the south-west lawn in L07 reads a little lighter and yellower than the
   lawns beside it; it was tuned under daylight_landing (pass_k_check_01).
3. As in hero_artistic_03: the dusk town lights are dense at 4K, the backing glow is uniform, and the skies are CC0
   HDRIs, not Nairobi skies.
4. The questions for the lead in pass_k_check_01/README.md (Ngando Flats, Racecourse Gardens, Liberty Centre, the K5c
   median cap, the south plaza position) are open.
