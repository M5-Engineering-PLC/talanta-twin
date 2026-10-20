# Stadium profile fit from the drone frames (work in progress)

Date: 2026-10-18. Status: software, not converged. Handed from the local lead to the cloud build chat.

## Goal

Fit the stadium side profile to the Kenyan Historian drone frames. The plan rings (plinth, roof outer, roof inner) are measured and stay fixed. The fit changes only the heights and the section shape that are now estimated by eye:

| Parameter | Meaning | Current value (ledger) |
|---|---|---|
| yW | wall top, where the shoulder starts | 51 m (roof_top_y 54 minus shoulder_r 3) |
| Rh, Rv | horizontal and vertical radius of the wall-to-roof shoulder | 3 m, 3 m |
| openY | height of the roof opening edge | 50 m (opening_y_blockout) |
| sag | roof sag between crest and opening | 1.5 m |
| dF | wall foot inset from the roof outer ring | about 0 to 1 m |
| bulge | outward bulge of the wall at mid height | 0 m |
| hs | shield centre height | 28.75 m |

All heights are above the site pad.

## Files

- model.py: the shell as points (port of profile() in blender/build_blockout.py), the cameras, and the projection.
- seg2.py: stadium and roof-opening masks for 9 frames, with a search box for each frame. Run `python3 seg2.py <outdir>`.
- solve_cams.py: one camera for each frame by differential evolution (look-at target, azimuth, elevation, distance, focal length in px, roll).
- fit_profile.py: alternates a profile fit over all frames with a camera re-polish.
- shield_pts.json: shield centres read from the frames by hand (about plus or minus 10 px, 1280 x 720). Partial shields at the frame edges are left out.

Frames: 000641.633, 000659.633, 001221.500, 001224.500, 001232.600, 001235.934, 001239.267, 001244.833, 001247.833.

## What was learned

1. The masks are usable. Light murram at the base leaks in on 001221.500 and 001224.500. A test that rejects warm colour (r minus b below 0.045) removes most of the leak.
2. Silhouette only: the cameras reached 71 to 96% overlap with the current profile. The profile fit then ran to Rh = 25 m (the bound), Rv = 8.5 m, yW = 46 m. Two cameras (001232.600, 001235.934) sat in wrong minima, so this result is not reliable.
3. Silhouette plus shield anchors (nearest match): the camera solve got worse (001659.633 went to 83 degrees elevation and 23 degrees roll). The profile moved to yW = 37 m, Rh = 4 to 8 m. The two runs disagree, so the profile is not determined yet.
4. The stadium and its 8 shields are close to symmetric under a 180 degree turn. This does not matter for the profile, but it gives each camera two equal minima.

## Recommended next steps

- Fix the focal length per lens. The frames come from a few lenses (the wide frames near 700 to 850 px, the tele frames near 2500 px). Solve the focal length once per clip, not per frame.
- Use explicit correspondences, not nearest match: give each shield in shield_pts.json its index k (0 to 7, angle -91.76 + 45 k degrees, x east, z south), and add the opening-ring corners and the visible wall-to-roof junction line.
- Start each camera from a coarse grid over azimuth and elevation, then polish. Keep the best of the two symmetric minima.
- Use a Blender silhouette render with the real blockout as a check of the final fit.
- Report the fitted values with a leave-one-frame-out spread. Write them to the ledger as derived only when the spread is under about 2 m.
