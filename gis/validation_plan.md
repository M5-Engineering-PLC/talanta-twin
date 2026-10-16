# Validation plan for the twin geometry

Date: 2026-10-16
Status: proposed. Pass marks are fixed now, before the results, so that nobody tunes them later.

The checks below do not depend on the lead's or Munene's judgement. Each one compares the model with an independent source or a physical fact.

| # | Check | Independent source | Pass mark | Runs after |
|---|---|---|---|---|
| V1 | Scale check of the imagery | Laws of the Game: penalty area 40.32 x 16.5 m, centre circle 18.30 m, goal area 18.32 m | All four within 0.5 m after the scale correction | W1b |
| V2 | Roof outline agreement | W1b ruler outline vs OSM vs Sentinel-2 vs the SfM point cloud (W3) | W1b and SfM within 1 m; Sentinel-2 inside its 5-95% range | W1b, W3 |
| V3 | Bowl centre and bearing | OSM + Sentinel-2 + W1b | Centre within 2 m; bearing within 1 deg | W1b |
| V4 | Seat count | Official capacity 60,000 (press, many sources) | Rows x seats per row in the model within 2% of 60,000 | W6 |
| V5 | Roof height by shadow | Sun elevation from pvlib for the image date and time, and the shadow length from W1b | Model roof edge within 1.5 m of the shadow result. Repeat on 2 image dates | W1b, W6 |
| V6 | Overlay on held-back frames | 20 reference frames that W6 never sees. Camera matched with fSpy | Silhouette overlap (IoU) of the bowl at least 0.90 on 16 of 20 frames | W6 |
| V7 | COLMAP quality | COLMAP's own report | At least 60% of images registered; mean reprojection error under 1 px | W3 |
| V8 | Near-ring footprints | 10 W1b spot-checks | 8 of 10 within 3 m | W1b |
| V9 | Construction timeline | Google Earth Pro historical image dates (W1b) | Each image's stage matches the Sentinel-2 stage for that month | W1b |
| V10 | Outside reviewer | The architect's office (Maj. Victor King'e, MoD), CRBC, Sports Kenya, or a licensed surveyor | They confirm 5 key dimensions: roof outline, pitch, roof height, tier count, bearing | Phase 0 end |

## Rules

- Hold back the V6 frames now: pick 20 frames from `labels_manual.csv` with keep=yes across the exterior, aerial and bowl classes, and list them in a new file `gis/heldout_frames.csv`. W6 must not use them.
- A failed check stays in the report. The item keeps the label "estimated" until it passes.
- V10 is the only check that needs a person outside M5. Ask early, because it takes the longest.
