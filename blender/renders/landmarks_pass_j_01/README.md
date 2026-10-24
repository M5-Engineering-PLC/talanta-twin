# Landmarks pass J 01: real local buildings as plain masses

Work order: engineering/cloud_handoff_2026-10-23.md, Step 2. Internal only.

## Scene chain

`step_FJ` = `step_FI` + `people_figures.py` + `crown_detail.py` (as in pass H) + `blender/context/landmarks_pass_j.py`
(data: `blender/data/landmarks_pass_j.json`). The buildings exist today, so they show in both states.

## Method

- Footprint: the named gpkg footprint (`gis/derived/near_ring_buildings.gpkg`, EPSG:32737). Without a name, the nearest
  footprint of 100 m² or more within 40 m of Munene's map pin.
- Height: the gpkg height (Open Buildings 2023, or default_by_area where noted). Storeys = height / 3.2 m.
- Mass: the footprint extruded from below the lowest ground to the roof, a flat roof and a 1 m parapet.
- Walls: one shader per building gives window rows every storey and window columns every 3 m along each wall. The
  Enkang blocks add red-brown vertical strips (every 9 m, 20 %), from JWNowpO44rw_000706.800 and 000619.700. Colours
  are by eye; no photo or map pixels are used. No names, logos or signage.
- Clearing: the generic masses on these footprints are removed in both states. That is 310 faces of `buildings` (the
  gpkg extrusions), 2,276 of `suburbs_buildings` (suburbs.py roofs, parapets and tanks, matched by `building_fid`) and
  61 of `bg_midrise_near` (background_b.py blocks, whole blocks only).
- Ledger: 12 rows `context.landmark.*`, each with its position source, height source and confidence.

## Buildings

| Building | gpkg footprint | Centre x, z (m) | Height | Storeys | Pin distance | Confidence |
|---|---|---|---|---|---|---|
| Enkang Apartments A | fid 8630, named | 2, -423 | 45.5 m | 14 | 111 m | medium |
| Enkang Apartments B | fid 8635, named | -12, -457 | 47.0 m | 15 | 90 m | medium |
| Enkang Apartments C | fid 8625, named | -52, -444 | 38.0 m | 12 | 53 m | medium |
| Ngando Flats | fid 8575, unnamed | -275, -433 | 4.5 m | 1 | 9 m | low |
| Liberty Centre | fid 8408, unnamed | -102, -644 | 11.5 m | 4 | 9 m | low |
| Denali Apartments | fid 8290, named | -155, -719 | 34.0 m | 11 | 89 m | medium |
| Racecourse Gardens Apartments | fid 7113, unnamed | -472, -802 | 4.0 m (default) | 1 | 24 m | low |
| White Village Apartments | fid 7827, unnamed | 164, -893 | 23.5 m | 7 | 19 m | low |
| Alba Apartments (TSAVO Skywalk footprint) | fid 10428, named TSAVO Skywalk | 223, -976 | 41.5 m | 13 | 92 m | low |
| Kenya Meteorological Department | fid 9665, named | 1,095, -622 | 7.0 m | 2 | 15 m | medium |
| The Junction Mall and Century Cinemax | fids 9846, 14176, named | 1,357, -865; 1,442, -869 | 17.0 m; 11.0 m | 5; 3 | 55 m; 33 m | medium |

The Enkang pin marks the group label: all three named Enkang footprints are 53 to 111 m from it.

**Denali and Alba: decided, not open.** Within 40 m of each pin the gpkg holds only low buildings: 5 m or less near
the Denali pin, 15 m or less near the Alba pin. So a 34 m or 41.5 m block cannot stand at the pin, and the pin marks a
label. The named Denali footprint and the TSAVO Skywalk footprint (the handoff's probable Alba) are used. The Alba
identity stays unconfirmed in the ledger.

## Visibility (ray test from each camera, 9 points per mass)

- **L07:** Enkang A, B and C are in frame; only their top floors show above the bowl roof (2 or 3 of 9 points).
  Denali (7 of 9), Alba (5 of 9) and White Village (3 of 9) are visible. Ngando and Liberty are hidden.
- **D02:** the same pattern. The Junction Mall shows at the right edge (6 of 9). KMD and Racecourse Gardens are hidden.

`L07_check_crop_enkang.png` is a 4x crop of a 960 x 540 check render: the Enkang trio above the roof.

## Gaps

1. Ngando Flats (4.5 m) and Racecourse Gardens (4.0 m, default height) have no tall gpkg footprint within 40 m of their
   pins. Their masses are as low as the gpkg says. Real heights need a frame or a site visit.
2. The White Village footprint is 116 m² at 23.5 m. Three small tall fragments lie near the pin, so the real building is
   probably larger.
3. Enkang storeys follow the gpkg heights (14, 15, 12). Frame 000706.800 shows a 12-storey tower; the block in that
   frame is not tied to A, B or C.
4. There are no balconies, setbacks or lit windows. The masses are plain.
