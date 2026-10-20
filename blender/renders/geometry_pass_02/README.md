# Geometry pass 2: opening ring, landmarks, multistart and leave-one-out

Fit: gis/scripts/profile_fit/fit2.py (state in gis/scripts/profile_fit/work/fit2_state.json, keys multistart2, final2,
loo2, spread2). Same terms as pass 1, with two additions:

- Opening ring re-measured: the visible opening edge is fitted as the measured roof inner ring minus a free inset dRi
  (bounds -4 to 14 m), since pass 1 showed the modelled ring lower and wider than the grey opening border.
- Landmarks: the left, right and top extremes of the opening outline on each frame (weight 2).

Cameras: one focal length and one k1 per lens, as in pass 1. 001232.600 is still excluded (no camera match).

## Acceptance

A parameter is accepted when the larger of two spreads is under 2 m:

- leave-one-frame-out (max - min over 8 runs, each started at the joint fit);
- the spread across the three multistart basins (starts at wall top 40, 46 and 51 m). Their costs are within 4 % of
  each other (442,906, 427,107 and 435,210), so the frames do not choose between them.

The leave-one-out alone is not a fair test this pass. Seven of the eight runs stay within 0.01 m of the start. The
basin spread is the real uncertainty. Values are the median over the basins.

| parameter | A (40) | B (46, best) | C (51) | median | basin spread | LOO spread | accepted | built (m) |
|---|---|---|---|---|---|---|---|---|
| wall top yW | 44.32 | 47.01 | 49.16 | 47.01 | 4.84 | 0.01 | no | 51.0 (kept) |
| shoulder Rh | 10.18 | 8.27 | 13.65 | 10.18 | 5.37 | 0.40 | no | 3.0 (kept) |
| shoulder Rv | 6.52 | 1.18 | 4.23 | 4.23 | 5.34 | 0.00 | no | 3.0 (kept) |
| opening height | 50.22 | 48.71 | 51.28 | 50.22 | 2.57 | 0.20 | no | 50.0 (kept) |
| opening ring inset dRi | 2.77 | 4.05 | 0.41 | 2.77 | 3.64 | 0.03 | no | 0 (ring kept) |
| roof sag | -2.66 | -0.24 | -2.73 | -2.66 | 2.49 | 6.19 | no | 1.5 (estimate) |
| foot inset dF | 0.66 | -0.12 | 0.81 | 0.66 | 0.94 | 0.09 | yes | 0.66 |
| wall bulge | -3.09 | -3.43 | -3.01 | -3.09 | 0.43 | 0.14 | yes | -3.09 |
| shield centre hs | 27.92 | 27.44 | 28.14 | 27.92 | 0.70 | 0.30 | yes | 27.92 |

Changes from pass 1:

- Accepted: shield centre (27.92 m, was rejected at 4.9 m spread), foot inset 0.66 m (was 0.74), wall bulge -3.09 m
  (was -2.89).
- Withdrawn: roof sag. It was accepted in pass 1 (-2.74 m, spread 1.6 m). In pass 2, leaving out 001239.267 moves it
  to +5.95 m, and basin B gives -0.24 m. The build reads the earlier estimate bowl.roof_sag (1.5 m, estimated) again.
  Two of the three basins agree on about -2.7 m, so a fourth frame of the roof between the crest and the opening would
  likely settle it.
- Opening ring: not settled. The inset runs from 0.4 to 4.05 m across the basins, so the ring from
  blender/out/bowl_rings.json stays. It is in the ledger as bowl.profile.fit_opening_inset (not read).

Rejected values are ledger rows bowl.profile.fit_* ("estimated (frame fit, spread X m, not accepted)").

Lenses (basin B): wide 1041 px (k1 -0.169), tele 2145 px (k1 -0.459). Basins A and C keep the pass 1 lenses (about
990 and 2360 px, k1 -0.08 and -0.20). Basin B buys its lower cost partly with a stronger lens distortion.

## Per frame (basin B, 8 frames)

| frame | mask IoU | outline median px | junction rms px |
|---|---|---|---|
| 000641.633 | 0.895 | 3.9 | 15.1 |
| 000659.633 | 0.958 | 3.3 | 7.3 |
| 001221.500 | 0.945 | 6.7 | 15.3 |
| 001224.500 | 0.950 | 7.4 | 13.4 |
| 001235.934 | 0.787 | 9.4 | 45.8 |
| 001239.267 | 0.926 | 6.1 | 18.9 |
| 001244.833 | 0.929 | 5.0 | 7.9 |
| 001247.833 | 0.872 | 12.5 | 57.5 |

## Roof ribs and shields (code, commit 34bc03d)

- The 60 underside primaries now sit at 2 pi k / 60 (were offset half a bay), so every other primary lies under one of
  the 30 topside cushion ribs (bowl.roof.cushion_bays). The hangers follow. build_bowl_detail.py raises an error if
  the primary count is not a multiple of the cushion bay count.
- Shield clamp (build_blockout.py near line 489): the fitted centre moves the whole shield, with its height kept,
  limited so the tip stays under the fascia line and the foot above the plinth. The old clamp cut the tip alone, which
  shrank the shield and moved its centre.

## Checks

- fit_overlay_8_frames.jpg: as in pass 1, with the opening drawn at the fitted inset.
- blender_silhouette_check.jpg: Workbench silhouette of the rebuilt blockout against the masks (green mask, magenta
  Blender):

  | cameras | 000641.633 | 001244.833 |
  |---|---|---|
  | pass 1 cameras on the pass 2 build | 0.878 | 0.906 |
  | pass 2 cameras (basin B) on the pass 2 build | 0.852 | 0.873 |
  | pass 1 (pass 1 build and cameras) | 0.877 | 0.905 |

  The check uses a pinhole camera and ignores k1. On the same cameras, the pass 2 build matches pass 1 or does a
  little better. The lower score with the basin B cameras comes from their stronger k1, not from the geometry.

## Renders

C19 (morning_golden) and C20 (evening_golden) at the check settings (960 x 540, 32 samples, lookdev on). Times are in
render_log.jsonl. Side-by-sides against the historian keep frames 000641.633 and 001244.833 (internal only).
Visualization.
