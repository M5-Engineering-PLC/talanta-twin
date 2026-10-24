# Replica plan: drone frames and landing mockups, 2026-10-20

Author: lead session. Source: facade_fix_01 sheets 001 to 007 (c9ad652) and the lead review in facade_review_01_2026-10-20.md.

## Two targets, one model

- Target 1: the drone frames D01 (000645.000), D02 (000714.767), D03 (000617.567), F16 (001216.000) and F32 (001232.600). They show the as-built state: red murram earth, bare plazas, construction hoarding, overcast light.
- Target 2: the landing mockups 06 and 07. They show the finished state: lawns, planting, paving, people, cars, sunset and daylight.
- The two targets share one geometry. The frames set the geometry. The mockups set only the surface look and the lighting.
- So the scene gets two surface states on the same geometry: asbuilt (for the D and F cameras) and finished (for L06, L07 and the web bundle).

## Where we are (facade_fix_01)

| area | drone frames | mockups |
|---|---|---|
| Bowl silhouette and convex barrel | match | match |
| Ribs, 24 bays, 8 shields, positions | match | match (mockup ribs are wider; the frames win) |
| Shield colour | fail: pink-magenta against crimson | fail |
| Shield outline | fail: blunt oval against a pointed lens | fail |
| Spear blades | fail: spoon ovals against leaf blades | fail |
| Fascia band | fail: thin rim against a broad white band | fail |
| Louvre tone | fail: dark gaps, grey gradient | fail |
| Roof cushions | fail: almost flat; D03 frame shows strong pillows | fail: mockups show strong pillows |
| Base | match in shape; recess too light in overcast | mockups show a lit glazed concourse |
| Ground surface | fail: green lawns against red murram and bare earth | partial: too sparse, lollipop trees |
| Foreground south-west | fail: track and pitch where D02 shows a lawn in a road loop | fail: mockups show the same lawn and road loop |
| Context city | fail: pale uniform boxes | fail: L07 needs denser mid-rise and a taller CBD |
| Context trees | fail: lollipop crowns, navy jacaranda | fail |
| Far land | partial: flat green-grey | fail in L06: beige band, mockup is green with blue hills |
| Sky and light | fail: pale white overcast against heavy grey cloud | H preset has the HDRIs; not yet checked |
| People and cars | not wanted (frames are construction) | missing; Visualization only |

## Passes

1. Pass A, facade (facade_fix_02): shield colour and outline, spear blades, fascia band 2.5 m, louvre backing, jacaranda colour.
2. Pass B, roof cushions: count the cushion rows and bays from D03 000617.567 and 001221.500. Raise the bulge until the D03 render shows the same pillow shading.
3. Pass C, ground from the solved cameras: back-project the as-built outlines (roads, road loop, lawn, plazas, track, pitch, stand) from D01 to D03 onto the terrain. Fix the south-west foreground from this, not by eye. Build the asbuilt and finished surface states.
4. Pass D, context: tree crowns, city blocks, far land, overcast sky for the D cameras.
5. Pass E, landing look (finished state only): warm uplights, a warm glow in the ground-floor recess at dusk, people and parked cars labelled Visualization.
6. Then 4K H stills of L06 and L07. Then Munene approves. Then W.

## Acceptance

- D01 to D03, asbuilt state: the stadium silhouette overlaps the frame silhouette by 95 % or more (intersection over union). Shield, fascia and louvre colour samples are within 12 levels per channel of the frame in the same light.
- F16: the shield outline width fractions are within 0.05 of the frame (0.73 at 10 % from the top, 0.30 at 3 % from the bottom tip).
- L06 and L07, finished state: the side-by-side sheets show the same layout, roof read, shield read and context density as the mockups. No mockup pixel is used as a texture.

## Rules that stay

- Frames and mockups are internal reference only. Never use them as textures.
- No gates, exits, signs, CCTV or control rooms. People and crowds are labelled Visualization.
- New ledger rows only. Do not edit old rows.
- No 4K and no W until the lead accepts pass E.
