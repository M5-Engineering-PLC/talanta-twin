# Review: Stage 02 C06 hero and C17, lead and Sol

Date: 2026-10-17
Reviewed: C06 pass 1 and pass 3, C17 (commit dc0ae2d)
Reviewers: the local lead session, and GPT-6.1 Sol (read-only, session 01a148b1-d214-7cc0-9d80-5e0cc5d4d8c1)
Status: sent to the cloud chat as the Stage 02b work order. Passes 4 to 6 followed (8da0ab5 to 98d0ec5).

## Verdict

- The direction is right. A Stage 01 redo is not necessary.
- Pass 3 scored 62/100. Sol gives materials, lighting, atmosphere and vegetation 2 each, not 3. The honest score is near 52/100.
- Expected score after Stage 02b: 72 to 78. An honest 85 needs the Stage 03 specialist builds.
- Plan change: run up to 4 Stage 02b passes, then start Stage 03. Judge gate G4 (85 on two passes) after Stage 03.
- Stop Stage 02b early if two passes in a row gain less than 3 points.

## Reference frames

Score each pass side by side with these frames. Do not use frames in gis/heldout_frames.csv.

| Subject | Frames (JWNowpO44rw) |
|---|---|
| Facade, shields, spears | 12:12, 12:16, 10:28 |
| Shield bulge | 00:16 |
| Roof, ground, context | 11:20, 12:40 |
| Proportions | 07:04 |

## Fixes, in order

1. Facade louvres and lattice. The real facade has dense, thin horizontal fins with dark openings behind them. Build fin geometry over a recessed dark backing (`louvre_pbr` in `blender/build_scene.py`). Make the lattice read more clearly (`curve_obj()` in `blender/build_blockout.py`).
2. Shields and spears.
   - Make the shields about 85 to 90% of the facade height, with the width to match. Label the size "estimated".
   - Use this pattern: a red field, black crescent lobes on the left and right, a white vertical spine, a white central boss, and broad white leaves above and below the boss. Remove the white pinstripes (`shield_png()`).
   - Give each shield a slight convex bulge.
   - Build two crossed white spears behind each shield. The script computed the spear paths but did not build them. Keep the blade tips below the roof edge.
3. Base. Replace the dark plinth loft with a light concrete band, white columns and a recessed shadow.
4. Light and camera. The lead approves morning light for C06. At 07:15 EAT the sun is 8.1 deg high at 111 deg azimuth, which is too low. Use 07:30 to 07:45 EAT for about 11 to 14 deg. Tilt the camera so that the Ngong Hills and a band of sky show.
5. Ground. Use separate regions: red murram soil (about #8B4A2B to #A0522D), light concrete paving, asphalt roads with markings, and grass only on the pitches.
6. Roof. Lower the raised ribs first. Then add faint radial seams and slight variation between panels.
7. Trees. Keep a wooded belt where frame 11:20 shows one. In other areas, use clumps with clearings and uneven crowns.
8. Sky, last. Use a low-resolution CC0 HDRI with clouds, or a cheap cloud background. Record the licence in the ledger. Do not use volume clouds.

## Render budget

Keep each pass below about 5 minutes on CPU. Use instanced trees, simple fin geometry and a low-resolution HDRI.

## C17 (blind-test camera)

Do this in Stage 03, with the landscape specialist build.

1. Match the stadium size and placement, the road convergence and the horizon.
2. Fix the foreground buildings (brown and red tile or iron-sheet roofs), the asphalt, the tall trees, the highway traffic and the cloud contrast.
3. Refine the facade.
4. For the G5 test, crop or mask the watermark on the real frame. Otherwise the logo shows which image is real.

C17 and the frames are internal only. Never use a frame as a texture.
