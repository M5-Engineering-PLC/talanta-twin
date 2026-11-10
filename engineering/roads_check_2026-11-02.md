# Roads check: shipped site GLB against the Google Earth records (2026-11-02)

Demo milestone work order, task 6. Report only: no geometry was edited. Internal only.

Checked file: `assets/web_hero_v3/models/talanta_site.glb` (89,633,388 bytes, the repaired T1 export). The road, plaza and path
meshes were read with gltf-transform (meshopt decoded), in world space (app frame: x east, z south, metres, origin at the
pitch centre).

## What "the Google Earth captures" are in this repository

There are no Google Earth images in `research/`, and there must not be: `gis/site_measurements.md` rule 1 forbids saving or
tracing Google Earth imagery into the repository. The Google Earth record is numeric:

| Record | What it holds | Accuracy stated |
|---|---|---|
| `blender/data/site_layout_ge.json` (step L, 2026-10-19) | a trace by eye of Munene's Google Earth Pro screenshot (image 26 Dec 2025, Airbus): the north-east road, the east hardstanding, two east buildings, the apron band | about ±10 m |
| `gis/measurements/*_w1b_*.csv` (W1b) | Google Earth Pro polygons clicked by Munene on the same image: site boundary, north plaza, bowl plinth, roof rings, pitch zone, warm-up track, two training pitches | a few metres (oblique image; roof rings about ±20 m) |

So every road below is compared with these numbers. Where neither record covers a road, the row says so and names the
source that placed it. Distances are measured on the mesh vertices; "match" means within the stated accuracy of the record.

## Roads and plazas

| Shipped mesh | Google Earth record | Result | Measured |
|---|---|---|---|
| `ge_road_north_east` (9 m road from the north plaza round the north end of the warm-up track, then south along the east side) | `site_layout_ge.json` roads[0], 496 m | **match** | centre line 0.1 m from the trace (median), half width 4.6 m (trace 9 m wide); 91 % of the trace length is covered |
| same road, x 252 to 255, z -30 to +10 | same trace | **missing, by decision** (about 40 m) | pass I cut the road where it meets the paved east approach (`blender/context/layout_pass_i.py`, audit fix 6, evidence D03) |
| Ngong Road (`ngong_road`, carriageways, median, barrier, service lanes) | W1b site boundary, north edge = "Ngong Rd verge" | **match** | the five north-edge boundary vertices lie 1.1, 1.8, 2.0, 2.1 and 4.3 m from the road surface |
| East hardstanding (`ge_east_hardstanding`, bay lines, islands) | `site_layout_ge.json` car_parks[0], 15,544 m² | **match** | every trace vertex is on the mesh (0.0 m); same bounding box x 294 to 456, z -183 to 76 |
| North plaza (`fc_plaza_edge`) | W1b `north_plaza` polygon | **match** | W1b vertices 0.1 to 6.3 m from the plaza edge; bounding box x -44 to 52 against -51 to 52, z -251 to -159 against -252 to -159 |
| Apron band round the bowl (`ge_apron_ring`) | `site_layout_ge.json` apron_ring (18 m band) with the W1b plinth | **match** | band radius 100 to 150 m against plinth radius 99 to 131 m, by bearing |
| South-west loop road (`sw_loop_road`) and its lawn (`sw_lawn`) | W1b `training_pitch_sw` (the bare-earth field the loop encloses) | **offset, about 13 m on the east side, and about 60 m short at the south** (estimated) | loop x -167 to -62, z 117 to 245; W1b field x -151 to -49, z 123 to 304. The north ends agree (6 m). The field's east edge is about 13 m east of the loop, and its south end runs about 60 m past the loop. The loop was traced from drone frame D02, not from Google Earth |
| East approach paving (`pi_east_approach`, island) | none (the trace shows the north-east road there) | **not in the Google Earth record** | placed from a D03 camera solve (±20 m), pass I |
| South plaza (`pk_south_plaza`, beds) | none | **not in the Google Earth record** | D02 camera solve (±25 m), pass K |
| North forecourt paths and lawns (`fc_path_*`, `fc_*_lawn`, `fc_facade_apron`) | north plaza outline only | **inside the W1b plaza and site; layout not in the Google Earth record** | drone frames JWNowpO44rw 04:45, 06:45, 06:59 (ledger `site.path.*`, `site.north_west.lawn`) |
| Finish plaza and paths round the bowl (`fp_plaza`, `fp_paths`, `fp_beds`) | none | **not in the Google Earth record** | step F: the landing mockups' look on unmeasured ground (`blender/context/finish_plaza.py`, "estimated ... not measured") |
| Rubis station forecourt (`rubis_forecourt`, x -410 to -351, z -195 to -158) | none (outside the W1b site) | **not in the Google Earth record** | `blender/context/rubis_station.py` |
| Context roads (`roads_final`) | none (outside the site) | **not in the Google Earth record** | OSM (`gis/derived/roads.gpkg`); OSM ways inside the W1b site were dropped on purpose (ledger `site.osm_footways_inside_w1b`) |

### Roads that the Google Earth notes name, checked against OSM

The W1b boundary note says: "N: Ngong Rd verge; E: west of Jamhuri Rd; S: Ngong Road Forest Sanctuary edge; W: track at
forest edge". Google Earth gives no line for the east and west roads, so the OSM line is the only position to check against:

| Road | Result | Measured |
|---|---|---|
| Ngong Road | **match** | OSM centre line 2.0 m (median) from the shipped road surface |
| Jamhuri Road (OSM "Jamuhuri Road", east of the site) | **partly missing / offset about 13 to 16 m** | only 14 to 38 % of the OSM line has a shipped road within 8 m; median 13 to 16 m |
| Jamhuri Park Road (east) | **partly missing / offset about 12 m** | 40 % within 8 m |
| West track at the forest edge (OSM "Memorial", service) | **missing** | 12 % within 8 m; median 59 m to the nearest shipped road |

## Shipped geometry whose only source is the AI dusk image

**None found.** Checked three ways:

1. **Objects:** no `lf_*` (pass F) object, and no west road, railway, station, footbridge, north-west car park, spine beds,
   south-west lot or road between the pitches, is in `talanta_site.glb`, `talanta_hero.glb` or `talanta_site_phone.glb`.
2. **Ledger:** every row of `gis/parameter_ledger.csv` that cites `research/reference/dusk_aerial_finished_2026-10-17.jpg`
   has a correction row "withdrawn 2026-10-23: source is an AI-generated image".
3. **Leftovers from pass F that do ship:**
   - The material `lf_murram_bed` (red murram) is used by `fp_beds` and the east-approach island. Its colour was first
     taken from the AI image. Pass I re-sourced it to drone frames JWNowpO44rw 06:45 (ledger `site.forecourt_paths.colour`).
   - The car figures `layout_cars_visualization` (pass F design, `lf_car_paint_*`, `lf_tyre` materials) are labelled
     Visualization. They stand only on the Google Earth east hardstanding (31 % of the vertices) and along Ngong Road (the
     rest). None stand where pass F put the withdrawn west road or car parks.

Close to this question but not the AI dusk image: the `fp_*` finish plaza, paths and beds round the bowl take their layout
from the landing mockups' look (step F), with no measurement. The mockups in `research/concepts/2026-10-17/` are also
generated images (their prompts are in the same folder). If the rule should cover them too, those meshes are the ones to
review.

## Method and limits

- Tools: gltf-transform with the meshopt decoder to read the GLB; numpy for distances. Scripts were scratch only and are not
  committed. Google Earth pixel positions convert with the `site_layout_ge.json` transform; W1b lon/lat convert about the app
  origin (36.749597 E, 1.306037 S).
- The Google Earth trace is a by-eye trace (±10 m). A "match" here cannot be better than that.
- The trace does not draw the east and west boundary roads. Those rows use OSM, which is not a Google Earth source.
- Roads were compared in plan only. Heights and widths of the context roads were not checked.
