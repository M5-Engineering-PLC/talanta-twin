# Site measurements (work order W1b)

Date of form: 2026-10-16
Who measures: Munene or a team member, at a desktop with Google Earth Pro.
Status: batch 1 (site boundary, pitch zone, 2026-10-16), batch 2 (roof outer ring, north plaza, warm-up track), the roof inner ring and the bowl plinth (2026-10-17) recorded. The two training pitches are still open. Scale checks not possible on the newest image (see below).
Classification: internal. Gate, parking and access measurements must not appear in a public demo (AGENTS.md rule 8).

## Rules

1. Record numbers only. Do not save, export, screenshot or trace Google Earth imagery into this repository or the product. The Google Earth terms do not allow it.
2. Use the newest image that shows the finished roof. The roof was complete from about February 2026 in Sentinel-2 (`coverage_report.md`). An older image shows construction.
3. Write down the image date for every row. Google Earth Pro shows it in the status bar. Use the clock tool (View > Historical Imagery) to pick dates.
4. Measure each item 3 times, starting fresh each time. Do it on 2 different image dates where both show the finished state.
5. Use the Ruler tool. Line for straight distances, Path for curved edges. Set units to metres.
6. Record coordinates in decimal degrees (Tools > Options > Show Lat/Long > Decimal Degrees). We convert them to EPSG:32737.

## Imagery available (checked 2026-10-16)

- Newest Google Earth Pro image: **26 Dec 2025, Airbus**. The steel roof ring is up but the cladding is not finished (Sentinel-2 shows the ring complete from Feb 2026). Measure the outer edge of the roof structure on it and mark the rows "Dec 2025 frame". Repeat when a newer image appears.
- Zoom in to an eye altitude of 500 m or less before you measure. The screenshot of the boundary was at 4.27 km.

## Scale check first

The Laws of the Game fix these markings, so they test the imagery scale. Pitch length and width do not. They vary between stadiums.

| Check | Fixed value | Run 1 | Run 2 | Run 3 | Image date |
|---|---|---|---|---|---|
| Penalty area width along the goal line | 40.32 m | | | | |
| Penalty area depth | 16.50 m | | | | |
| Centre circle diameter | 18.30 m | | | | |
| Goal area width | 18.32 m | | | | |

If a check is off by more than 1 m, note it and continue. The lead uses the four checks to correct the scale.

**Status 2026-10-17: not possible: no pitch markings on the newest image (26 Dec 2025, Airbus).** This is not a failed check. Repeat when Google Earth Pro offers an image with the pitch marked.

## Pitch and bowl

Expected values come from the satellite and OSM work in `coverage_report.md`. They are there to catch mistakes, not to steer the reading.

| Item | How | Expected | Run 1 | Run 2 | Run 3 | Image date |
|---|---|---|---|---|---|---|
| Pitch length, goal line to goal line | Line along touchline | about 105 m | | | | |
| Pitch width, touchline to touchline | Line across halfway line | about 68 m | | | | |
| Grass area length, edge to edge | Line | about 130 m | | | | |
| Grass area width, edge to edge | Line | about 85 m | | | | |
| Roof outer edge, long axis | Line through pitch centre spot along the long axis | 256-274 m | 252.0 (min. rectangle of the 12-point roof-top polygon; 250.1 in EPSG:32737) | | | 2025-12-26 (Airbus), Dec 2025 frame |
| Roof outer edge, short axis | Line through the centre spot across | 204-234 m | 214.4 (214.5 in EPSG:32737) | | | 2025-12-26 (Airbus), Dec 2025 frame |
| Roof inner edge, long axis | Line | unknown | 130.0 (min. rectangle of the 21-point polygon "ROOF RING", EPSG:32737; bearing 179.6 deg). `measurements/roof_inner_w1b_2026-10-17.csv` | | | 2025-12-26 (Airbus) |
| Roof inner edge, short axis | Line | unknown | 88.1 (opening area 10,443 m2) | | | 2025-12-26 (Airbus) |
| Long-axis bearing | Ruler heading along the touchline | 176-180 degrees | 181 (roof-top polygon, 1 deg = 181 deg); pitch zone 1.76 deg | | | 2025-12-26 (Airbus) |
| Centre spot position | Lat, lon | -1.30602, 36.74965 | | | | |
| Roof outline, 16 points | Path round the outer roof edge. Read out the lat, lon of each vertex | | 12 points (corners cut): `measurements/roof_outer_w1b_2026-10-17.csv`, 47,041 m2 | | | 2025-12-26 (Airbus) |

## Heights from shadows

Height = shadow length x tan(sun elevation). The lead computes the sun elevation from the image date, time and position with pvlib. Google Earth Pro shows the date. It does not always show the time, so measure the shadow of a known object as a calibration.

| Object | Shadow length | Shadow bearing | Image date | Run |
|---|---|---|---|---|
| Calibration: a floodlight mast or building with a known height | | | | |
| Roof edge, west side, shadow on the pitch | | | | |
| Roof edge, east side, shadow on the ground outside | | | | |

## Site plan (internal)

| Item | How | Run 1 | Run 2 | Run 3 | Image date |
|---|---|---|---|---|---|
| Gate 1-8 centre positions | Lat, lon for each gate | | | | |
| Main plaza outline | Path, vertices as lat, lon | North forecourt plaza, 10 points: 8,268 m2, 102.5 x 93.5 m, long axis 89 deg. `measurements/north_plaza_w1b_2026-10-17.csv` | | | 2025-12-26 (Airbus) |
| Each parking area: outline and bay count | Path and count | | | | |
| Training pitch 1 and 2: length, width | Line | Not yet measured. (The KML shape named "Training pitch" is the warm-up track, below.) | | | |
| Warm-up track oval, east of the bowl | Polygon | 6 points: 12,738 m2, 166.7 x 87.8 m, long axis 179 deg. Standard 8-lane outer edge is 176.9 x 92.5 m, so use the standard shape, labelled estimated. `measurements/warmup_track_w1b_2026-10-17.csv` | | | 2025-12-26 (Airbus) |
| Mini-stadium: outline | Path | | | | |
| Access road widths, 5 samples | Line kerb to kerb, with location | | | | |
| Site boundary fence | Path | 8-point polygon: 33.87 ha, perimeter 2,349 m. Vertices in `measurements/site_boundary_w1b_2026-10-16.csv` | | | 2025-12-26 (Airbus) |

## Near-ring spot checks

Choose 10 buildings of different sizes within 1 km. For each: footprint length and width, and the lat, lon of one corner. The lead compares them with `derived/near_ring_buildings.gpkg`.

| # | Lat, lon of corner | Length | Width | Image date |
|---|---|---|---|---|
| 1 | | | | |

## Historical image dates

List every image date that Google Earth Pro offers for the site from 2023 on. We use them to check the Sentinel-2 timeline.

| Image date | What it shows (fields, earthworks, frame, roof, finished) |
|---|---|
| | |

## Batch 2 check (cloud session, 2026-10-17)

Recomputed in EPSG:32737 (UTM 37S) from the CSVs, to check the lead's local-projection numbers. Centroids are relative to the twin origin (-1.306037, 36.749597).

| Shape | Lead area | UTM area | Lead rectangle | UTM rectangle | Area centroid | Vertex mean (lead's method) | Twin today |
|---|---|---|---|---|---|---|---|
| Roof outer ring | 47,041 m2 | 46,761 m2 | 252.0 x 214.4 | 250.1 x 214.5 | 10 m E, 27 m N | 4 m W, 22 m N | bowl_outer 256 (N-S) x 203 (E-W) m |
| North plaza | 8,268 m2 | 8,219 m2 | 102.5 x 93.5 | 102.5 x 92.9 | 2 m E, 205 m N | 15 m W, 204 m N | eye plaza about 184 x 92 m, centre about 203 m N |
| Warm-up track | 12,738 m2 | 12,662 m2 | 166.7 x 87.8 | 165.8 x 87.2 | 169 m E, 117 m N | 171 m E, 122 m N | not modelled at this position |

- Areas agree within 0.6%. UTM scale (0.9996) and the projection account for the gap.
- The lead's centroids are vertex means. The points are unevenly spaced, so the area centroid is the better position. The roof-top centroid is still uncertain by about 20 m from relief displacement.
- The roof short axis (214 m) is 11 m wider than the twin bowl (203 m). The long axis (250 to 252 m) is 4 to 6 m shorter. Stage 00 puts both in the parameter ledger.
- The plaza position matches the twin. Its width is about half the twin's (102 m against 184 m). Stage 00 corrects it.

## Roof inner ring (2026-10-17)

21 points, area 10,443 m2, opening 130.0 x 88.1 m, long axis 179.6 deg. Area centroid 13 m E, 29 m N of the twin origin. The roof outer ring centroid is 10 m E, 27 m N. Both roof-level outlines are shifted by the same amount, which fits relief displacement on the oblique image, not a real offset. The roof is centred on the pitch, so subtract about 10 m E, 28 m N from roof-level positions.

Roof depth from the two rings: about 63 m on each side ((214.5 - 88.1) / 2) and 60 m at each end ((250.1 - 130.0) / 2). Plan area of the roof band: 36,300 m2.

## Bowl plinth, ground-level outline (2026-10-17)

KML name "STADIUM OUTLINE", 30 points. The points were clicked out of order and the ring crossed itself, so `measurements/bowl_plinth_w1b_2026-10-17.csv` reorders them by angle round the vertex mean (the clicked order is kept in a column). The reordered ring is valid.

| Value | Measured | Twin `bowl_outer` today |
|---|---|---|
| Area | 45,297 m2 | |
| Minimum rectangle | 253.0 x 202.8 m | 256 (N-S) x 203 (E-W) m |
| Area centroid from the twin origin | 2 m W, 2 m N | about 4 m E, 2 m N |
| North and south extent | 128.6 m N, 123.7 m S | 130.8 m N, 125.5 m S |
| West and east extent | 105.1 m W, 98.3 m E | 97.5 m W, 105.9 m E |

- The ground outline is centred on the pitch, with no relief shift. This confirms the shift of the two roof rings (about 10 m E, 28 m N) comes from the oblique view.
- The twin's bowl size is within 3 m of the measurement. The twin is about 7 m too far east.
- The roof outer ring (214.5 m) is about 12 m wider than the ground outline (202.8 m): the roof overhangs the facade by about 6 m on each side, or the oblique view widens it. Stage 01b checks this on the historian frames.
