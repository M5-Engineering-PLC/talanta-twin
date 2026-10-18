# Geometry pass 1: stadium side profile from the drone frames

Fit: gis/scripts/profile_fit/fit2.py (state in gis/scripts/profile_fit/work/fit2_state.json). Plan rings (plinth, roof outer, roof inner) fixed as measured.
Terms: silhouette chamfer both ways, roof-opening edge, hand-read wall-to-roof junction and wall foot lines (lines.json), labelled shields
(k, angle -91.76 + 45 k deg). Cameras: coarse grid over azimuth and elevation with pre-alignment, seeded re-solves, then a joint fit
with one focal length and one radial term k1 per lens: wide 964 px (k1 -0.072),
tele 2364 px (k1 -0.199; 001221.500 and 001224.500). Press maximum 56 m as a soft limit.
Masks: seg2.py with hand-placed base-leak exclusions on 001221.500 and 001224.500.

## Profile (heights above the site pad)

Accepted when the leave-one-frame-out spread (max - min over 8 runs) is under 2 m.

| parameter | fit, 8 frames (m) | spread (m) | accepted | built (m) |
|---|---|---|---|---|
| wall top yW | 46.37 | 2.86 | no | 51.0 (kept) |
| shoulder Rh | 10.16 | 5.12 | no | 3.0 (kept) |
| shoulder Rv | 4.65 | 3.46 | no | 3.0 (kept) |
| crest (yW + Rv) | 51.01 | 4.40 | no | 54.0 (kept) |
| opening height | 51.09 | 4.07 | no | 50.0 (kept) |
| roof sag | -2.74 | 1.60 | yes | -2.74 |
| foot inset dF | 0.74 | 0.99 | yes | 0.74 |
| wall bulge | -2.89 | 1.62 | yes | -2.89 |
| shield centre hs | 27.47 | 4.91 | no | 28.75 (kept) |

The heights are not determined yet: three start profiles (wall top 38, 44, 51 m) end at the same cost with the wall top between
45.7 and 49.6 m, and the crest moves 4.4 m when the two side views (001244.833, 001247.833) are left out. The rejected values are in
the ledger as bowl.profile.fit_* (not read by the build); the build keeps roof_top_y 54, shoulder_r 3, opening_y 50, shield centre 28.75.
Accepted: foot inset 0.74 m, wall bulge -2.89 m (the wall bows in at mid height), roof sag -2.74 m (the roof rises toward the opening).

## Per frame (8-frame fit)

| frame | mask IoU | outline median px | junction rms px |
|---|---|---|---|
| 000641.633 | 0.892 | 4.4 | 15.6 |
| 000659.633 | 0.963 | 1.9 | 6.2 |
| 001221.500 | 0.946 | 5.8 | 28.9 |
| 001224.500 | 0.953 | 7.6 | 23.6 |
| 001235.934 | 0.782 | 9.7 | 39.7 |
| 001239.267 | 0.928 | 6.1 | 22.5 |
| 001244.833 | 0.934 | 4.2 | 9.5 |
| 001247.833 | 0.872 | 10.9 | 43.4 |
| 001232.600 | 0.81 (best camera) | | 150 to 180 (excluded) |

001232.600 is left out: in every start (grid, seeded, three profiles, k1 down to -0.25) its camera sits at the 2 deg elevation bound with
the junction 150-180 px off. Likely stronger lens distortion or a crop than the one-term model covers.

## Checks

- fit_overlay_9_frames.jpg: outline (cyan), junction (magenta), crest (yellow), foot (orange), opening (green), model shields (red) and hand points (white).
- blender_silhouette_check.jpg: Workbench silhouette of the rebuilt blockout from the solved cameras of 000641.633 and 001244.833: IoU 0.877
  and 0.905. The roof line runs a little high, as expected from the kept 54 m crest against the fitted 51 m.
- Open issue: the modelled opening ring sits lower and wider than the visible opening on 001221.500, 001224.500 and 001239.267; the
  measured inner roof ring likely traces the outer edge of the grey opening border.

## Cushion roof

30 cushion bays between topside ribs (derived: projected rib lines for 30, 40 and 60 against 001221.500 and 001224.500 both match 30;
the 60 underside primaries carry a top rib on every other one), 8 cushion rows (estimated, 001232.600, 001235.934), bulge 0.45 m (estimated).

## Renders

C19 and C20 at the check settings (960 x 540, 32 samples, lookdev on): C19 186 s, C20 176 s (render_log.jsonl). Side by sides against the
historian keep frames 000641.633 and 001244.833 (internal only). Visualization.
