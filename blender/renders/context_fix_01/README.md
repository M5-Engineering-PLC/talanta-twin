# Context fix 01: replica plan pass D (internal)

Pass D of the lead order of 2026-10-20. Internal only: the sheets hold reference frames and landing mockups. No 4K and no W.

## What changed

Code: e8f37b6 (pass D part), plus the tuning commit with these renders.

- **Trees: irregular clustered crowns at all distances** (`blender/context/tree_crowns.py`).
  - Every ellipsoid crown of the forest scatter prototypes (`tree_protos`), the site tree copies (`st_*`) and the suburb trees is replaced, in place on the shared mesh, by a cluster of 6 to 14 lumpy sub-crowns. All their instances change.
  - The canopy.py variants (lobed crowns with leaf cards) are kept.
  - Clustered trees are also planted on the tree cells of the as-built trace, both states: the forest edges the drone frames show, 230 m or more from the bowl. Nearer, the tree class also caught dark lawn.
- **City: darker and varied** (`blender/context/context_fix.py`).
  - Suburb walls, OSM facades, the background_b blocks and the horizon towers are darkened to 0.68.
  - Each building gets a tone spread of +-22 % from a 60 m world noise.
- **L07: denser mid-rise and a taller cluster** (estimated, Visualization; finished state only).
  - 140 mid-rise blocks of 20 to 45 m and 1400 trees in the L07 view, 1.2 to 4.5 km out.
  - 22 towers of 60 to 140 m at 40 deg and 3.5 km, toward the Kileleshwa and Lavington apartment towers.
  - The CBD (75 deg) and Upper Hill (85 deg) lie outside the L07 frame, so the "taller CBD cluster" is placed where tall towers stand inside the frame. It is not labelled as the CBD.
- **Far land: green with blue-grey hills** (L06).
  - The Sentinel-2 dry-season tone of the far-land materials is turned toward dark green (Colour blend 0.95, x 0.6).
  - The hills and far layers get a blue-grey copy.
  - The haze on the middle distance bands is lighter (`lookdev.py` aerial_band_haze), and the outer bands blend fully into the blue far tint. This changes every render that uses an HDRI preset.
- **Overcast sky for the D cameras:** new preset `overcast_drone` in `blender/sky_hdri.py`.
  - CC0 HDRI Overcast Soil (Pure Sky) from Poly Haven. It is not committed; `blender/assets/fetch_hdri_h.sh` fetches it, and CREDITS.md lists it.
  - Weak soft sun (0.35 of the sky; 25 deg disc), exposure -0.2 EV.
  - A cool sky tint (0.86, 0.96, 1.16): the HDRI is warmer than the frames' grey deck.
  - The exposure and tint were tuned in D01 check renders against the louvre sample:

    | Setting | Louvre sample |
    |---|---|
    | -1.6 EV | (83, 80, 74) |
    | -0.6 EV | (125, 121, 112) |
    | -0.4 EV with tint | (128, 130, 129) |
    | Frame | (142, 142, 149) |

## Renders

- Scene: `step_FC` plus `tree_crowns.py` and `context_fix.py`, frozen as `blender/out/step_FD.blend`.
- Cycles 1920 x 1080 hero, 128 samples, look layer on.

| Render | Camera | State, light | Time |
|---|---|---|---|
| D01_overcast_drone_hero.png | D01, refined | asbuilt, overcast_drone | 7.0 min |
| D02_overcast_drone_hero.png | D02, solved | asbuilt, overcast_drone | 7.2 min |
| L06_sunset_landing_hero.png | L06 | finished, sunset_landing | 11.4 min |
| L07_daylight_landing_hero.png | L07 | finished, daylight_landing | 9.8 min |

**Re-renders:**
- D01 and D02 were rendered three times. The first set showed trace trees on dark lawn and a dark, warm sky. That was fixed by keeping only tree areas of 600 m² or more at 230 m or further, hiding the Google Earth eucalyptus row in asbuilt (the frames show it unplanted), and the exposure and tint above.
- The second set still showed the trace trees as crowns on poles. A commented-out scale line was the cause; the trees are now broad and touching.
- L06 was rendered before that last tree fix. Its trace trees, if any are in view, are the narrow ones.

## Acceptance

**D01 and D02 colour samples** (`facade_samples.py`, in the stadium mask; target 12 levels):

| Camera | Shield red | Lobe black | Louvre | Fascia |
|---|---|---|---|---|
| D01 render | (109, 0, 6) | (10, 10, 13) | (135, 137, 139) | (217, 220, 223) |
| D01 frame | (91, 19, 44) | (34, 24, 37) | (142, 142, 149) | (153, 152, 162) |
| D01 max difference | 38 | 24 | 10 (pass) | 68 |
| D02 max difference | 63 | 20 | 42 | 145 |

- The louvre now passes in D01 (it was 46 in pass C).
- **Shield red and black fail in overcast:**
  - The frames' overcast shields carry a blue sky sheen: (91, 19, 44) and (51, 9, 20).
  - The pass A paint is matte, with specular 0.1, tuned in sun in F16, where it passes.
  - One paint cannot match both without a sheen term. Not changed: the order fixed the paint in F16.
- **Fascia:** the sample above the shield top lands on the bright roof edge in the render and on darker parts in the frames. It is not a clean fascia reading in D views.
- **D02:** the frame day is darker and more contrasty than D01's. One sky preset matches D01, not both.

**Silhouette IoU** is unchanged from pass C: D01 0.913, D02 0.913, D03 0.960. Same cameras, same bowl.

**Landing sheets:** L06 and L07 against mockups 06 and 07 are in `sheets/`. By eye:
- L06: green forest, olive far land and blue-grey hills.
- L07: denser and darker mid-rise, with the taller cluster at the right.

## Gaps (honest list)

1. **L06 far land is olive-beige, not green.**
   - The middle bands read about (128, 116, 92) under the 3300 K sun, even with the land albedo turned to dark green and the haze lowered.
   - A thin pale haze strip remains under the hills.
2. **Overcast shields** read pure red and black against the frames' sheened crimson (see above).
3. **The trace trees are bright green clusters;** the frames' canopy is darker and finer.
4. **The ground of D01 and D02 is a 1 m cell mesh.**
   - Laterite plazas read paler than the frames' pink-beige.
   - Some murram reads grey where the trace classed it paved.
5. **The L07 taller cluster is not at the CBD,** which lies outside the frame (see above). Its blocks are generic boxes with the horizon window materials.
6. **The haze change in `lookdev.py` also affects the C19/C20 and H presets.** They were not re-rendered: no 4K and no H in this order.
