# W1b measurements, batch 2 (from Munene's Google Earth Pro saved places)

Date read: 2026-10-17
Source: Google Earth Pro 7.3.7, My Places > "TALANTA w1b" and My Places, drawn by Munene
Image: 26 Dec 2025 (Airbus), the newest image available. The roof is an open steel frame, and the pitch has no markings.
Method: the lead read the polygon vertices from myplaces.kml. The dimensions are from a local metric projection centred on -1.30602, 36.74965, and use the minimum-area bounding rectangle. These are numbers only. No imagery was saved.

Please save these as CSVs in gis/measurements/ (one file for each shape, vertices as lon, lat), add them to the parameter ledger, and update gis/site_measurements.md.

## Summary

| Shape | KML name | Points | Area | Bounding rectangle | Long-axis bearing | Centroid from pitch centre |
|---|---|---|---|---|---|---|
| Stadium outline, roof top (outer ring) | Polygon Measure ("Top stadium outline") | 12 | 47,041 m2 | 252.0 x 214.4 m | 1 deg | 4 m W, 22 m N |
| North forecourt plaza (shield-shaped, on the ground) | shield on ground | 10 | 8,268 m2 | 102.5 x 93.5 m | 89 deg | 15 m W, 205 m N |
| Warm-up track oval, east of the bowl (KML name says training pitch) | Training pitch | 6 | 12,738 m2 | 166.7 x 87.8 m | 179 deg | 171 m E, 123 m N |

## Checks against the expected values

- Roof outer ring: the short axis of 214.4 m is inside the expected range of 204 to 234 m. The long axis of 252.0 m is 4 m below the expected range of 256 to 274 m. The long-axis bearing of 1 degree agrees with the pitch zone (about 181 degrees).
- Roof outer ring: the centroid is 22 m north of the pitch centre. The image is oblique, so the top of the roof is displaced from its base (relief displacement). Treat the roof-top outline position as uncertain by about 20 m. Treat its size as more reliable than its position. Do not move the bowl to this centroid without a second check.
- Roof outer ring: the outline has only 12 points, and the form asked for 16. The curved corners are therefore slightly cut. The true area is probably a little larger.
- Warm-up track: Munene's screenshot shows that the shape named "Training pitch" traces the oval athletics track with the green infield, east of the bowl. Record it as the warm-up track outline, not as a training pitch. A standard 8-lane 400 m track measures about 176.9 x 92.5 m on its outer edge. The traced 166.7 x 87.8 m fits a track with fewer lanes, or a line along the inner edge. The shape has only 6 points, so the curved ends are cut. Use it for position and orientation. Use the standard track geometry for the shape, labelled "estimated".
- Plaza: this is the north forecourt shape that the twin calls the eye-shaped plaza. Use it to place and size the plaza and fountain in site.js. The current position is an estimate from frames.

## Still not measured

- Roof inner ring (the roof opening)
- Bowl plinth outline at ground level
- Training pitches: the rectangular field with a track south-west of the bowl, and the green rectangle south-east of the bowl
- Scale checks: these are not possible, because the newest image has no pitch markings.

## Vertices (lon, lat; the last point closes the ring)

Stadium outline, roof top
1,36.7488468,-1.3049392
2,36.7491486,-1.3046792
3,36.7501943,-1.3047020
4,36.7505274,-1.3049674
5,36.7506791,-1.3055540
6,36.7506124,-1.3064012
7,36.7502853,-1.3068426
8,36.7496137,-1.3069511
9,36.7490999,-1.3068479
10,36.7488099,-1.3065457
11,36.7487438,-1.3060502
12,36.7487559,-1.3053798
13,36.7488468,-1.3049392

North forecourt plaza
1,36.7491908,-1.3038274
2,36.7499402,-1.3037594
3,36.7500612,-1.3039886
4,36.7500672,-1.3043092
5,36.7499463,-1.3045995
6,36.7493177,-1.3045824
7,36.7491789,-1.3043231
8,36.7491547,-1.3042265
9,36.7491426,-1.3041299
10,36.7491607,-1.3040514
11,36.7491908,-1.3038274

Warm-up track oval
1,36.7507268,-1.3043810
2,36.7512239,-1.3042044
3,36.7514733,-1.3044273
4,36.7515290,-1.3051413
5,36.7514069,-1.3056990
6,36.7507579,-1.3056629
7,36.7507268,-1.3043810
