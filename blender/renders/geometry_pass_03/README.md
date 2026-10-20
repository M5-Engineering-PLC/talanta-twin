# Geometry pass 3: crest-prior height run (last height fit). Result: rule failed, build values kept

Reviewed plan: Luna and Sol. Fit: gis/scripts/profile_fit/fit2.py, `fit2.py <work> robust pass3 prior` (state in
gis/scripts/profile_fit/work/fit2_state.json, key pass3).

## What ran

- Objective: the pass 2 objective (silhouette, opening ring with free inset dRi, opening landmarks, junction, foot,
  labelled shields; one focal length and k1 per lens) plus a Gaussian crest prior ((yW + Rv - 54) / 2)^2. Its source
  is the narration at 10:27 ("the roof structure rises to roughly 54 m") plus the press figure (ledger
  bowl.profile.crest_prior; engineering/detail_sheets/06_interior_inventory.md).
- Units: the prior is in units of sigma, so the image residuals are counted in units of the 10 px robust scale. The
  soft_l1 loss is applied by hand to the image residuals only, and the prior stays outside it. Total = image cost
  + 0.5 x 10^2 x ((crest - 54) / 2)^2.
- Free: yW, Rh, Rv, opening height and dRi (and sag, dF, bulge, hs as before). The crest is not fixed.
- Same 8 frames (001232.600 still excluded), same lenses, 3 starts (wall top 40, 46 and 51 m; dRi 3, 5 and 1 m as in
  pass 2).
- Rule (fit2.acceptance, committed in 12ba527): accept only if max(basin spread, leave-one-out spread) < 2 m. Basins
  are the starts whose image-only cost is within 4 % of the best. Added in this pass: a parameter held at its bound
  in any run is not accepted. Its spread is zero only because it cannot move.

## Costs (image-only and prior penalty, reported separately)

| start (wall top, dRi) | image-only cost | prior penalty | crest (m) | in basin |
|---|---|---|---|---|
| 40, 3 | 405,789 | 627 | 46.91 | yes |
| 46, 5 | 400,674 (best) | 600 | 47.07 | yes |
| 51, 1 | 421,657 | 43 | 52.15 | no (+5.2 %) |
| all 8 frames from the best basin | 399,874 | 598 | 47.08 | |

## Result

| parameter | basin median | basin spread | leave-one-out spread | accepted | built (m) |
|---|---|---|---|---|---|
| wall top yW | 45.19 | 0.29 | 5.61 | no | 51.0 (kept) |
| shoulder Rh | 14.14 | 23.53 | 1.30 | no | 3.0 (kept) |
| shoulder Rv | 1.80 | 0.14 | 3.05 | no | 3.0 (kept) |
| crest yW + Rv | 46.99 | 0.15 | 2.66 | no | 54.0 (kept) |
| opening height | 47.91 | 1.19 | 4.67 | no | 50.0 (kept) |
| opening inset dRi | 6.50 | 0.04 | 2.39 | no | 0 (ring kept) |
| roof sag | 0.75 | 1.81 | 5.97 | no | 1.5 (kept) |
| foot inset dF | 0.31 | 0.06 | 3.39 | no | 0.66 (pass 2, kept) |
| wall bulge | -4.00 | 0.00 | 0.00 | no (held at its -4 m bound) | -3.09 (pass 2, kept) |
| shield centre hs | 24.81 | 0.36 | 3.65 | no | 27.92 (pass 2, kept) |

The spread rule fails for every parameter. As agreed, this was the last height-fit run. The build keeps its values,
and nothing is labelled "derived (prior-constrained, frames + narration)". The pass 3 values are in the ledger as
bowl.profile.fit3_* rows ("estimated (prior-constrained fit, spread X m, not accepted)", not read). There was no
rebuild, because the build is the same as geometry pass 2. Its silhouette check (0.878 / 0.906 with the pass 1
cameras) and its C19/C20 side-by-sides in blender/renders/geometry_pass_02/ still stand. No new renders were made.

## Why it fails

- The two basins now agree on the heights (spread under 0.3 m), but leave-one-out does not. Leaving out 000641.633
  drops the crest to 44.5 m and the wall top to 39.7 m. Leaving out 000659.633 gives 45.3 and 42.3 m. The other six
  drops stay within 0.3 m. Two wide frames carry the height.
- Height trades against focal length and camera distance. In the best basin the tele lens drifted to 1,280 px
  (passes 1 and 2: 2,145-2,364 px), with k1 -0.30, and the wide lens moved to k1 -0.40. A 2 m prior on one height
  barely registers against image costs that differ by 5,100-21,000 between solutions. The penalty for the crest
  sitting 7 m under the prior is only about 600.
- The fitted crest (about 47 m) disagrees with the narrated 54 m by 3.5 sd, even with the prior. Either the
  narrated figure is the top of a structure above the crest line used here (the 8 m shoulder, the opening ring),
  or the frames alone cannot fix the scale.

## Conflict with pass 2 (for the lead)

dF and hs passed the rule in pass 2 (spreads 0.94 and 0.70 m) and fail it here (leave-one-out 3.4 and 3.7 m), and
bulge now runs to its bound. They stay in the build at their pass 2 values, as instructed, but their "derived" status
rests on one objective only. A measured section (drawing or survey) is the way to settle the heights. More frame
fitting is not.

## Files

- fit_results.csv: per-start values and costs, spreads, decisions, built values, and per-frame results for the best
  basin (IoU 0.781 to 0.960).
- fit_overlay_8_frames.jpg: as in pass 2, for the pass 3 best-basin fit (internal: tour frames).
