# Follow-up 01: the suggestions after pass E (internal)

Follow-up to the replica plan of 2026-10-20, after pass E. These are the four suggestions from the pass E report. No 4K, no H, no W.
Internal only: the sheets hold reference frames and landing mockups.

## 1. Shield in overcast: a drone camera grade, not a paint sheen

**Sheen tested and rejected.** D01 and F16 check renders (960 x 540, 32 samples, `facade_samples.py`), with the shield paint changed only for the test:

| Variant | D01 red / black (max diff) | F16 red / black (max diff) |
|---|---|---|
| paint as in pass A | 38 / 24 | 12 / 13 |
| Sheen 0.5, roughness 0.5 | 28 / 7 | 34 / 21 |
| Sheen 1.0, roughness 0.3 | 36 / 22 | 7 / 8 (one shield found only) |
| Coat 0.3, roughness 0.4 | 29 / 17 | 24 / 7 |

Every variant that greys the red in D01 adds about as much veil in sunlit F16. The paint stays as matched in F16.

**What the samples show.** In D01 the render's blacks are crushed: (13, 10, 13) against the frame's (34, 24, 37). The red has no blue left: (109, 0, 6) against (91, 19, 44). The louvre already matched. This is the drone camera and the air at drone distance (lifted, blue blacks, softer reds), not the paint.

**Fix: `display_grade` on the `overcast_drone` preset** (`blender/sky_hdri.py`).
- `render_cycles.py` applies it to the saved 8-bit image, in display values: `out = gain * (lum + sat * (c - lum)) * (1 - veil) + veil * veil_rgb`.
- Values: veil 0.094, veil_rgb (0.863, 0.693, 1.25), saturation 0.684, gain 0.964.
- They were fitted to the D01 red, black and louvre samples (largest error 4 levels).
- The render log records the grade. Only presets that carry `display_grade` change; today that is `overcast_drone` only.

**D02 exposure.** The 000714.767 day is much darker than 000645.000 (louvre 109 against 142). D02 gets a camera offset in `app/cameras/manifest.json`: `exposure_ev` -1.1, tested at -0.7 and -1.1 in check renders.

## 2. Lens distortion: tested, not the cause

The test added a radial term k1 to the hull projection of `refine_drone_cams.py` (scratch test, not committed) and refit on the frame silhouette:
- **D01:** the best k1 is about 0 (0.038 alone, -0.0006 with the pose). The hull IoU goes from 0.905 to 0.907.
- **D02:** k1 0.10 with the pose refit takes the hull IoU from 0.824 to 0.868, still far from 0.95.

The remaining misfit (overlays in `ground_fix_01`) is the bowl plan or profile, or the frame silhouette cut, not the lens. The cameras are not changed.

## 3. L06 dusk: the facade glows

- **Uplights** at dusk: `dusk_energy` 90 kW per lamp (was 30 kW). `blender/context/landing_look.py`.
- **Warm light behind the louvres:** an emission (strength 2, warm 1.0/0.62/0.30) on the light backing `facade_void_pbr`.
  - It has a new `dusk:` label: on only with a preset that turns the fixtures on before night. It is off at night and by day (`render_cycles.py`).
  - It is labelled Visualization.
  - Check renders: 2 reads, 6 burns the facade out (`L06_glow_check_2_top_6_bottom.jpg`).
- **`sunset_landing` preset:** sun to sky 2.0 (was 5.0) and exposure -1.4 EV (was -1.8). The low sun no longer drowns the lights.

`step_FE.blend` is rebuilt from `step_FD` with the new `landing_look.py`. L07 is not affected: no fixtures by day, so it was not re-rendered.

## 4. Haze change of pass D: checked in C19 and C20

The scene is `step_FE`. Both cameras were check-rendered twice: once as now, once with the pre-pass-D band haze put back in the compositor (scratch pre-script, 8 nodes). The images are in `haze_ab/`, old on top, new below.
- **C19 (morning_golden):** the far land reads greener and the Ngong Hills clearer. There is no band seam.
- **C20 (evening_golden):** nearly the same; the middle distance is a little clearer.

No regression, so the change stays.

## Renders (1080p, 128 samples, look layer on, `step_FE`)

| Render | Camera | State, light | Time |
|---|---|---|---|
| D01_overcast_drone_hero.png | D01, refined | asbuilt, overcast_drone + display grade | 5.9 min |
| D02_overcast_drone_hero.png | D02, solved, -1.1 EV | asbuilt, overcast_drone + display grade | 6.2 min |
| D03_overcast_drone_hero.png | D03, refined | asbuilt, overcast_drone + display grade (first D03 under the grey sky) | 7.5 min |
| L06_sunset_landing_hero.png | L06 | finished, sunset_landing (dusk lights) | 8.7 min |

## Acceptance

**Colour samples** (`facade_samples.py`, in the stadium mask; target 12 levels):

| Camera | Red | Black | Louvre | Fascia |
|---|---|---|---|---|
| D01 render | (92, 23, 40) | (29, 25, 40) | (138, 135, 150) | (211, 209, 224) |
| D01 frame | (91, 19, 44) | (34, 24, 37) | (142, 142, 149) | (153, 152, 162) |
| **D01 max difference** | **4, pass** (was 38) | **5, pass** (was 24) | **7, pass** (was 10) | 62, fail |
| D02 render | (65, 21, 35) | (23, 19, 33) | (103, 100, 116) | (186, 183, 198) |
| D02 frame | (51, 9, 20) | (30, 13, 17) | (109, 108, 109) | (81, 78, 80) |
| **D02 max difference** | 15, fail (was 63) | 16, fail (was 20) | **8, pass** (was 42) | 118, fail |

- F16 is unchanged: the paint is unchanged, and `neutral` has no display grade (red 12, black 13 in the check render, as in pass C).

**D03 roof band** (rows 140-180, x 420-820 of 1280, as in pass B):

| | Median colour | High-pass contrast (9 px) |
|---|---|---|
| Frame 000617.567 | (228, 232, 237) | 2.66 % |
| roof_fix_01 (procedural sky) | (180, 200, 222) | 3.00 % |
| followup_01 | (208, 205, 220) | 2.61 % |

The roof's worst channel is now 27 levels off the frame (was 48). It is no longer blue.

**L06:** the facade glows warm all round with the lattice readable, as in mockup 06 (`sheets/004`). The glow is design intent, labelled Visualization.

**Silhouette IoU:** unchanged: D01 0.913, D02 0.913, D03 0.960 (same cameras and bowl).

## Gaps (honest list)

1. **The drone grade is global.**
   - It also mutes the ground: the laterite and murram in D01 read pink-grey, where the frame's are a strong red-brown (`sheets/001`).
   - Next step: raise the saturation of the ground materials under this preset, or fit the grade with ground samples too.
2. **The D02 frame is a different day.**
   - Its shields and blacks are warmer and darker than D01's. One grade fits D01; red and black miss by 15 and 16 in D02.
   - The D02 fascia sample lands on a dark gap, as before.
3. **Fascia samples** still land on the bright roof edge in the renders (all D cameras). They are not a clean fascia reading.
4. **The D01/D02 IoU stays at 0.91.** Not the lens (part 2): the bowl plan or profile at the right end of D01 and along the D02 roof line is next.
5. **L06:**
   - The sky is still less saturated than the mockup's orange clouds.
   - The far land is still olive under the low sun.
   - The backing glow is uniform; the mockup's concourse glazing and doors are not modelled (no exits rule).
6. **The H stills** use `sunset_artistic`, which also turns the fixtures on, so they would get the backing glow at the H preset's light. They are not rendered: no H in this order.
