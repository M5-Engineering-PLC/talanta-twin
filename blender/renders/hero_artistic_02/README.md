# Hero artistic 02: 4K stills of L06 and L07 (step 19, final scene)

Lead order of 2026-10-22: after passes F, G and H, render the 4K hero_artistic stills of L06 and L07, push them, and **STOP**. W waits for Munene's approval of these stills.

## Settings

| | |
|---|---|
| Scene | step_FH: step_FE, plus the pass F layout, plus the pass H people and crowns. Finished state, look layer on. |
| Preset | `hero_artistic` (`blender/hero_artistic.py`): 3840 x 2160, Cycles 128 samples adaptive, OpenImageDenoise, volumetric haze, glare and bloom, edge bevels |
| L06 | `sunset_artistic` sky (Belfast Sunset, CC0), dusk fixtures on: uplights, recess glow, backing glow |
| L07 | `daylight_artistic` sky (Kloofendal 48d, CC0), day |

**Stand-ins skipped:** the step H stand-ins (its own uplights, stick people and box cars) are not added this time, because the scene already carries the pass E uplights, the pass F cars and the pass H figures (change in `hero_artistic.py`).

**Labelling:** people, cars and the dusk lights are a Visualization. The labelled copy (`*_labelled.png`) carries that note in the corner. The unlabelled PNG is for review only.

## Renders

| Render | Time |
|---|---|
| L06_sunset_artistic_hero_artistic.png (and the labelled copy) | 64.2 min |
| L07_daylight_artistic_hero_artistic.png (and the labelled copy) | 37.1 min |

## Gaps

1. **Each landing camera shows only part of the pass F layout.**
   - **L07:** the west road, station, footbridge and far west car park are on the left.
   - **L06:** they are at the right edge, behind the bowl.
   - The north-west car park is out of both frames.
2. **Speckle in L06:** the far ridge under the low sun shows a fine speckle (the haze volume and the denoiser at 128 samples). More samples or a larger adaptive minimum would clear it.
3. **The L06 sky is still less saturated than the mockup's orange clouds**, and the far land is olive under the low sun (followup_01, gap 5).
4. **The backing glow is uniform.** The concourse glazing and doors are not modelled (no exits rule).
5. **The skies are CC0 HDRIs, not Nairobi skies.**
