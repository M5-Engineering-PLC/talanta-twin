# Site measurements (work order W1b)

Date of form: 2026-10-16
Who measures: Munene or a team member, at a desktop with Google Earth Pro.
Status: form ready, no measurements yet.
Classification: internal. Gate, parking and access measurements must not appear in a public demo (AGENTS.md rule 8).

## Rules

1. Record numbers only. Do not save, export, screenshot or trace Google Earth imagery into this repository or the product. The Google Earth terms do not allow it.
2. Use the newest image that shows the finished roof. The roof was complete from about February 2026 in Sentinel-2 (`coverage_report.md`). An older image shows construction.
3. Write down the image date for every row. Google Earth Pro shows it in the status bar. Use the clock tool (View > Historical Imagery) to pick dates.
4. Measure each item 3 times, starting fresh each time. Do it on 2 different image dates where both show the finished state.
5. Use the Ruler tool. Line for straight distances, Path for curved edges. Set units to metres.
6. Record coordinates in decimal degrees (Tools > Options > Show Lat/Long > Decimal Degrees). We convert them to EPSG:32737.

## Scale check first

The Laws of the Game fix these markings, so they test the imagery scale. Pitch length and width do not. They vary between stadiums.

| Check | Fixed value | Run 1 | Run 2 | Run 3 | Image date |
|---|---|---|---|---|---|
| Penalty area width along the goal line | 40.32 m | | | | |
| Penalty area depth | 16.50 m | | | | |
| Centre circle diameter | 18.30 m | | | | |
| Goal area width | 18.32 m | | | | |

If a check is off by more than 1 m, note it and continue. The lead uses the four checks to correct the scale.

## Pitch and bowl

Expected values come from the satellite and OSM work in `coverage_report.md`. They are there to catch mistakes, not to steer the reading.

| Item | How | Expected | Run 1 | Run 2 | Run 3 | Image date |
|---|---|---|---|---|---|---|
| Pitch length, goal line to goal line | Line along touchline | about 105 m | | | | |
| Pitch width, touchline to touchline | Line across halfway line | about 68 m | | | | |
| Grass area length, edge to edge | Line | about 130 m | | | | |
| Grass area width, edge to edge | Line | about 85 m | | | | |
| Roof outer edge, long axis | Line through pitch centre spot along the long axis | 256-274 m | | | | |
| Roof outer edge, short axis | Line through the centre spot across | 204-234 m | | | | |
| Roof inner edge, long axis | Line | unknown | | | | |
| Roof inner edge, short axis | Line | unknown | | | | |
| Long-axis bearing | Ruler heading along the touchline | 176-180 degrees | | | | |
| Centre spot position | Lat, lon | -1.30602, 36.74965 | | | | |
| Roof outline, 16 points | Path round the outer roof edge. Read out the lat, lon of each vertex | | | | | |

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
| Main plaza outline | Path, vertices as lat, lon | | | | |
| Each parking area: outline and bay count | Path and count | | | | |
| Training pitch 1 and 2: length, width | Line | | | | |
| Mini-stadium: outline | Path | | | | |
| Access road widths, 5 samples | Line kerb to kerb, with location | | | | |
| Site boundary fence | Path | | | | |

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
