# Landmark candidates

Date: 2026-10-23
Project: Talanta Twin
Status: internal frame review and camera projection
Source path: `research/video_index/MASTER_INDEX.csv`, `engineering/environment_from_drone_2026-10-17.md`, `gis/derived/near_ring_buildings.gpkg`, `app/cameras/manifest.json`, and the listed frames and renders
Handoff: choose three to five named landmarks for the near-ring model. The frame set does not identify the apartment blocks by name.

## Method and limits

Frame evidence means that a frame shows a building or a group of buildings. Camera projection means that the candidate point falls inside a hero camera view. Inference means a likely match based on position or appearance. A camera projection does not prove that the current render contains that building.

I inspected 13 allowed frames as images. I selected them by subject and view: city-side aerials, mid-rise blocks, and the nearby skyline. No frame from `oL3wsPsx4Jw` or `PWj9s_v3G6U` appears here. The frames stay internal.

The positions use the supplied site-frame coordinates. The heights come from the named GeoPackage features. The Junction Mall has two named footprints in the GeoPackage. Their combined approximate center is x 1,410 m, z -879 m, with heights from 11 to 17 m. The unnamed tower cluster has four features. They span x 488 to 619 m and z -1,510 to -1,488 m. Their heights range from 60 to 74 m.

I projected each feature center and its estimated height through the six named cameras. I used 1920 x 1080 pixels and the vertical field of view in the manifest. The listed pixel point is the center of the projected building. The height is the projected vertical span from ground to roof. These values ignore terrain, nearby occlusion, building footprint, and any difference between the estimated height and the real height. Only L07 and D02 contain candidate centers in the image bounds.

The frames show groups of apartment blocks. The images do not show a map position or a named building label for those blocks. The current renders show a generic city skyline in L07 and D02. They do not identify these candidates as modeled objects.

## Candidate record

| Name | Position and height from GeoPackage | Visible in which frames | Hero camera projection at 1920 x 1080 | What the frame buildings look like | Confidence that the frame shows this candidate |
|---|---|---|---|---|---|
| Enkang Apartments A | x 5 m, z -419 m, height 45.5 m | Not seen by name. Nearby block groups appear in `JWNowpO44rw_000619.700.jpg`, `JWNowpO44rw_000623.200.jpg`, and `JWNowpO44rw_000626.700.jpg`. | L07: x 806, y 447, height 102 px. D02: x 826, y 374, height 74 px. | Frame evidence: groups of about 8 to 15 storeys. White or cream faces include red or gray vertical panels. Roofs appear flat. The frames do not resolve balconies or the plan shape. The details are group-level only. | Low. Several nearby blocks share this height and look. No frame gives a position or name. |
| Enkang Apartments B | x -13 m, z -459 m, height 47 m | Not seen by name. Nearby block groups appear in `JWNowpO44rw_000619.700.jpg`, `JWNowpO44rw_000623.200.jpg`, and `JWNowpO44rw_000626.700.jpg`. | L07: x 755, y 439, height 102 px. D02: x 790, y 369, height 73 px. | Frame evidence: groups of about 8 to 15 storeys. White or cream faces include red or gray vertical panels. Roofs appear flat. The frames do not resolve balconies or the plan shape. The details are group-level only. | Low. Several nearby blocks share this height and look. No frame gives a position or name. |
| Enkang Apartments C | x -47 m, z -445 m, height 38 m | Not seen by name. Nearby block groups appear in `JWNowpO44rw_000619.700.jpg`, `JWNowpO44rw_000623.200.jpg`, and `JWNowpO44rw_000626.700.jpg`. | L07: x 683, y 453, height 84 px. D02: x 738, y 379, height 60 px. | Frame evidence: groups of about 8 to 15 storeys. White or cream faces include red or gray vertical panels. Roofs appear flat. The frames do not resolve balconies or the plan shape. The details are group-level only. | Low. Several nearby blocks share this height and look. No frame gives a position or name. |
| TSAVO Skywalk | x 223 m, z -976 m, height 41.5 m | Not seen by name. A general block view appears in `JWNowpO44rw_000706.800.jpg` and `JWNowpO44rw_000709.167.jpg`. | L07: x 991, y 376, height 57 px. D02: x 963, y 329, height 39 px. | Frame evidence: a cream apartment tower has a flat roof and a rectangular front. The image is too small to resolve balconies or the plan shape. It is not matched to TSAVO Skywalk. | Low. The frame does not give the tower position or name. |
| The Fedge | x 229 m, z -1,178 m, height 51 m | Not seen by name. A general block view appears in `JWNowpO44rw_000706.800.jpg` and `JWNowpO44rw_000709.167.jpg`. | L07: x 941, y 356, height 62 px. D02: x 930, y 316, height 42 px. | Frame evidence: a cream apartment tower has a flat roof and a rectangular front. The image is too small to resolve balconies or the plan shape. It is not matched to The Fedge. | Low. The frame does not give the tower position or name. |
| Rock park Apartments | x 413 m, z -1,289 m, height 66.5 m | Not seen by name. A general block view appears in `JWNowpO44rw_000706.800.jpg` and `JWNowpO44rw_000709.167.jpg`. | L07: x 1,115, y 340, height 74 px. D02: x 1,048, y 306, height 51 px. | Frame evidence: a cream and ochre tower with a flat roof stands near the right side of the stadium in the view. The frame does not resolve balconies or the plan shape. It is not matched to Rock park Apartments. | Low. The frame does not give the tower position or name. |
| Avana Residence | x 849 m, z -1,037 m, height 43.5 m | Not seen by name. Distant city blocks appear in `JWNowpO44rw_001242.050.jpg` and `JWNowpO44rw_001244.833.jpg`. | L07: x 1,708, y 361, height 53 px. D02: x 1,448, y 319, height 36 px. | Frame evidence: distant blocks appear white, gray, and cream, with flat roof lines. The frames do not resolve balconies or plan shape. They do not isolate this candidate. | Low. The candidate is within two views, but the distant blocks cannot be tied to its footprint. |
| Urban Oasis Apartments | x about 1,280 m, z about -1,350 m, height 73 to 83 m | Not seen by name. Distant city blocks appear in `JWNowpO44rw_001242.050.jpg` and `JWNowpO44rw_001244.833.jpg`. | L07: x 1,910, y 322, height 82 px, using 83 m. D02: x 1,580, y 295, height 55 px, using 83 m. | Frame evidence: distant tower groups sit above dense low roofs. Their colors are gray, white, and cream. The frames do not resolve balconies or plan shape. They do not isolate this candidate. | Low. The candidate is near the frame skyline, but the frame gives no location or name. |
| Tanga Heights | x about 1,390 m, z about -1,110 m, height 38 to 39.5 m | Not seen by name. Distant city blocks appear in `JWNowpO44rw_001242.050.jpg` and `JWNowpO44rw_001244.833.jpg`. | D02: x 1,767, y 315, height 29 px, using 39.5 m. Outside L07. | Frame evidence: distant blocks appear white, gray, and cream, with flat roof lines. The frames do not resolve balconies or plan shape. They do not isolate this candidate. | Low. The candidate has a small projected height and the frame gives no location or name. |
| West Height Apartments | x 1,679 m, z -995 m, height 41.6 m | Not seen. | Outside all six camera views. | No frame shows a building that can be linked to this candidate. | Low. No frame position or name matches the candidate. |
| Astoria Apartments | x 1,535 m, z -1,432 m, height 41.6 m | Not seen by name. Distant city blocks appear in `JWNowpO44rw_001242.050.jpg` and `JWNowpO44rw_001244.833.jpg`. | D02: x 1,679, y 305, height 26 px. Outside L07. | Frame evidence: distant blocks appear white, gray, and cream, with flat roof lines. The frames do not resolve balconies or plan shape. They do not isolate this candidate. | Low. The candidate has a small projected height and the frame gives no location or name. |
| The Junction Mall | Approximate combined center x 1,410 m, z -879 m, height 11 to 17 m. The GeoPackage has two named footprints. | Not seen. | Outside all six camera views. | No frame shows a low landmark that can be linked to this candidate. | Low. No frame position or name matches the candidate. |
| Unnamed towers in the requested area | x 488 to 619 m, z -1,510 to -1,488 m, height 60 to 74 m | Towers appear in the wider skyline in `JWNowpO44rw_001242.050.jpg` and `JWNowpO44rw_001244.833.jpg`. The exact four towers are not isolated. | L07: x 1,183, y 327, height 73 px, using x 550 m, z -1,500 m, and 74 m. D02: x 1,094, y 298, height 50 px, using the same point and height. | Frame evidence: multiple narrow towers rise above dense low roofs. Colors appear gray, white, and cream. The frames do not resolve balconies or plan shape. | Low. Tower groups are visible, but the four GeoPackage footprints cannot be matched to image shapes. |
| Rubis station at Dagoretti Corner | No matching named feature found in the supplied GeoPackage. | Not seen. The selected frames do not show an identifiable station. | No projection. The work order gives no site-frame position. | No station feature can be described from the selected frames. | Low. No frame shows a station that can be matched to Rubis. |

## Ranked shortlist for review

The ranking uses the projected pixel height, presence in L07 or D02, and the visible shape in the wider block frames. This is a shortlist of candidates to inspect. The frame identity remains unconfirmed for every entry.

1. Enkang Apartments A. It projects to 102 px in L07 and 74 px in D02. The adjacent towers in the frame group have a distinct white and red block form. Crop: `sheets/01_enkang_a.jpg`.
2. Enkang Apartments B. It projects to 102 px in L07 and 73 px in D02. Its position separates it from A in the projection. Crop: `sheets/02_enkang_b.jpg`.
3. Enkang Apartments C. It projects to 84 px in L07 and 60 px in D02. Its height estimate is lower than A and B. Crop: `sheets/03_enkang_c.jpg`.
4. Rock park Apartments. It projects to 74 px in L07 and 51 px in D02. The nearby frame view includes a tall cream and ochre block. Crop: `sheets/04_rock_park.jpg`.
5. The Fedge. It projects to 62 px in L07 and 42 px in D02. The nearby frame view includes apartment towers, but no exact match. Crop: `sheets/05_the_fedge.jpg`.

Each crop shows a general building group from the cited frame. The crop does not identify the named candidate.

## Evidence labels

- Frame evidence: the named frame visibly shows apartment blocks or towers. The frames do not establish a named building match.
- Camera projection: L07 and D02 place the listed candidate point inside the image. The other four cameras do not place these candidate centers inside their image bounds.
- Inference: the ranked shortlist favors candidates with the largest projected height and a similar frame view. This ranking does not confirm a building identity.

## Questions for the lead

- The frames show city-side apartment blocks, but their positions cannot be tied to the GeoPackage footprints. Should the shortlist remain a camera-projection shortlist until someone supplies a georeferenced reference view?
- The selected frames show several tower groups. The images do not confirm whether the four unnamed towers in the requested area are among them.

## Positions from Munene's map screenshots (lead, 2026-10-23)

Munene supplied two Google Maps satellite screenshots: `ref/gmaps_north_2026-10-23.webp` and `ref/gmaps_northeast_2026-10-23.webp`. They are internal reference for positions only. Do not use them as a texture or in a public page.

Method: the URL gives the centre of each map. The scale is 1.25 m per pixel, calibrated on The Junction Mall footprint in the GeoPackage. The stadium ring falls 22 m from the twin origin. Treat each position as plus or minus 25 m. A pin marks the label point, not the building centre.

The imagery shows the stadium under construction. Use it for the surroundings, not for the finished site layout.

| Map pin | x (m, east) | z (m, south) | Distance | Bearing | Match in the GeoPackage |
|---|---|---|---|---|---|
| Enkang - Ngong Road | -102 | -462 | 473 m | 347 | Enkang Apartments A, B, C (38 to 47 m) at x -47 to 5, z -459 to -419 |
| Ngando Flats | -275 | -424 | 505 m | 327 | not named in the GeoPackage |
| Liberty Centre | -100 | -653 | 660 m | 351 | not named |
| Denali Apartments | -200 | -796 | 821 m | 346 | Denali Apartments, 34 m |
| Racecourse Gardens Apartments | -468 | -825 | 948 m | 330 | not named |
| White Village Apartments | 174 | -909 | 925 m | 11 | not named |
| Alba Apartments | 255 | -890 | 926 m | 16 | probably the footprint named TSAVO Skywalk (41.5 m) at x 223, z -976 |
| Dagoretti Corner | 434 | -926 | 1,023 m | 25 | junction label |
| Kenya Meteorological Department | 1,084 | -632 | 1,255 m | 60 | low buildings |
| Century Cinemax | 1,356 | -972 | 1,669 m | 54 | part of The Junction |
| The Junction Mall | 1,471 | -897 | 1,723 m | 59 | The Junction Mall, 11 to 17 m |
| Jamhuri sports ground | 224 | -288 | 365 m | 38 | the field north-east of the stadium, south of Ngong Road |
| Jamhuri Sports Ground main gate | 490 | -19 | 490 m | 88 | the east side of the site |

Findings:
- Frame JWNowpO44rw_000706.800 shows a 12-storey cream and brown tower in front of long grey industrial sheds, with Ngong Road and the stadium behind it. The map shows the CFAO Mobility sheds between the Enkang pin and Ngong Road. So this tower is probably one of the Enkang blocks. Label: inference, medium confidence.
- The model's Rubis station is at x -382, z -182 (423 m, bearing 295), on Ngong Road west-north-west of the stadium. It is not at the Dagoretti Corner junction (1.0 km, bearing 25). The step R note records that Munene chose the north-west Rubis.
- The Junction Mall is outside all six hero cameras (Luna's projection). It shows only in the live twin when the viewer turns north-east.
