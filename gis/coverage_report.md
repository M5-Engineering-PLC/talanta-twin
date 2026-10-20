# GIS coverage report (W1, with first passes of W2 and W4)

Date: 2026-10-16
Made by: the lead (Claude), from free open data only.
CRS: EPSG:32737 (WGS 84 / UTM 37S) for every output.

## Main findings

1. **The stadium is at 36.74965 E, 1.30602 S.** It is in Jamhuri Park, off Ngong Road, beside Ngong Road Forest. The Sentinel-2 roof centroid and the OSM stadium building agree within 1.5 m. The first guess (the Jamhuri Park Showground centroid) was 2 km east, and an earlier guess (the Kenya Railways golf course) was wrong. The box for all data is now 3 km x 3 km round the bowl.
2. **The roof outline is known to about 20-30 m, not yet to 1 m.**

   | Source | Long axis | Short axis | Bearing of long axis | Note |
   |---|---|---|---|---|
   | OSM building r20072298 (edited 2 Feb 2026) | 256 m | 204 m | 178-180 deg | Traced by an OSM mapper. Imagery and date not stated |
   | Sentinel-2, 7 scenes after roof completion, 3 thresholds | 274 m (5-95%: 262-328) | 234 m (222-250) | 177 deg (167-179) | 10 m pixels. Bright paving next to the roof enlarges it. Treat as an upper bound |

   The two sources agree on the centre and the bearing. They disagree on size by 18 m (long) and 30 m (short). W1b decides. Until then, use OSM for the blockout and label it "estimated".
3. **Inside the bowl:** OSM maps a grass area of 134 x 85 m (10,922 m2). That fits a 105 x 68 m pitch with about 14 m and 8 m of run-off. Sentinel-2 gives an opening of 9,300-11,100 m2. Neither source gives the pitch markings.
4. **Construction timeline from 58 clear Sentinel-2 scenes (Jan 2023 - Oct 2026)** (`derived/bowl_s2_timeline.png`, `derived/bowl_s2_contact_sheet.png`):
   - 2023: playing fields and a running track on the site.
   - April 2024: earthworks, matching the groundbreaking on 1 March 2024.
   - 2024-2025: frame of the bowl.
   - November 2025: a large part of the roof ring is in place (30% of the ring bright).
   - 11 February 2026: the roof ring is first over 80% bright.
   - August 2026 on: finished white roof and green pitch.
   
   The values for Feb 2024 (5%) come from cloud or bare soil, not the roof. Google Earth images dated before February 2026 show an unfinished roof. Do not measure the roof on them.
5. **Open Buildings 2.5D Temporal ends at 30 June 2023.** It shows the site before the stadium. It is good for the near ring, not for the bowl.

## First W1b measurement (2026-10-16)

Munene drew the site boundary in Google Earth Pro on the 26 Dec 2025 Airbus image: 8 vertices, **33.87 ha**, perimeter 2,349 m. It follows Ngong Road on the north, the line west of Jamhuri Road on the east, and the Ngong Road Forest Sanctuary edge on the south. It holds the bowl, the training pitches and the warm-up track, and its centroid is 26 m from the bowl centre. The press figure of "more than 45 ha" for Talanta Sports City may include land outside this line. Ask Sports Kenya, or use the Gazette notice, to settle it.

## Data downloaded (git-ignored, in `gis/raw/`)

Run the scripts in `gis/scripts/` to get the same files on another machine. Order: `fetch_sentinel2.py`, `fetch_open_buildings_temporal.py`, `fetch_dem.py`, `fetch_overture.py`, then `measure_bowl_s2.py` and `derive_near_ring.py`. Use `~/.venvs/gis/bin/python` (geopandas, rasterio, pyproj, pyarrow, scipy, matplotlib).

| Folder | Content | Source and licence | Size |
|---|---|---|---|
| `raw/sentinel2/` | 58 clear L2A scenes 2023-01-08 to 2026-10-01, bands B02 B03 B04 B08 at 10 m, plus `scenes.csv` (cloud score of all 335 scenes) | Copernicus Sentinel-2, AWS Earth Search COGs. Free; credit "Contains modified Copernicus Sentinel data 2023-2026" | 33 MB |
| `raw/open_buildings_temporal/` | 2016-2023 yearly rasters, 0.5 m: building count, height, presence | Google Open Buildings 2.5D Temporal v1. CC BY 4.0 | 270 MB |
| `raw/overture/` | Buildings, road segments, land use, infrastructure, land, water, places | Overture Maps 2026-09-23.0. OSM parts ODbL; Google and Microsoft footprints CC BY 4.0 / CDLA / ODbL | 14 MB |
| `raw/dem/` | GLO-30 DSM: 3 km at 10 m, 12 km at 30 m | Copernicus DEM GLO-30. Free; credit required | 0.8 MB |

## Derived files (committed, in `gis/derived/`)

| File | Content |
|---|---|
| `bowl_outline_s2.geojson` | Sentinel-2 ellipse fit of the roof (upper bound) |
| `bowl_s2_summary.json`, `bowl_s2_measurements.csv` | All fits, by scene and threshold, with the spread |
| `bowl_s2_timeline.csv`, `.png`, `bowl_s2_contact_sheet.png` | Construction timeline. Copernicus data, so the images may be shared with credit |
| `near_ring_buildings.gpkg` | 14,261 footprints without the bowl. Height source per building: Open Buildings 2023 for 7,567, OSM floors for 7, default by area for 6,687 |
| `roads.gpkg` | 1,609 road segments and 1 rail line, with class, name and surface |
| `heightmap_glo30_*.png` + `.json` | 16-bit heightmaps with bounds and min/max height for three.js |

## What could not be fetched from this environment

- OSM servers (Overpass, Geofabrik), STAC search APIs, Copernicus Data Space, Kenyan government sites, Wikipedia, StadiumDB and x.com. The agent proxy blocks them. Overture stands in for OSM.
- download.blender.org. Blender is installed as the PyPI `bpy` 5.2.2 module instead.
- Raw YouTube videos for W3.

## What this data cannot give

- Roof heights, tier rake and the facade at better than frame quality. They need W3 (structure from motion), the shadow method in W1b, or drawings.
- A roof outline to 1 m. It needs W1b or a 30-50 cm satellite image after February 2026.
- Gates, plazas and parking as built. OSM may lag. W1b covers them.

See `data_gap_matrix.csv` for each item and `validation_plan.md` for the checks.
